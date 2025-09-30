import os
import uuid
import pdfplumber
from minio import Minio
import psycopg2
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from langchain_community.vectorstores import Qdrant
from langchain_core.documents import Document
from langchain.embeddings import SentenceTransformerEmbeddings

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path)

# Environment
QDRANT_URL = os.getenv("QDRANT_URL")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# Init clients
qdrant = QdrantClient(url=QDRANT_URL)
minio_client = Minio(
    MINIO_ENDPOINT.replace("http://","").replace("https://",""),
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)
pg_conn = psycopg2.connect(
    host=POSTGRES_HOST,
    database=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD
)
pg_cursor = pg_conn.cursor()

# Qdrant collection
COLLECTION_NAME = "cv-document-embeddings"
VECTOR_SIZE = 384
if COLLECTION_NAME not in [c.name for c in qdrant.get_collections().collections]:
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )

# Embedding model
embeddings = SentenceTransformerEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Qdrant(
    client=qdrant,
    collection_name=COLLECTION_NAME,
    embeddings=embeddings
)

def ingest_cv(file_path: str, candidate_name: str, email: str, role: str):
    # Upload to MinIO
    file_id = str(uuid.uuid4())
    object_name = f"{MINIO_BUCKET}/{file_id}.pdf"
    minio_client.fput_object(MINIO_BUCKET, object_name, file_path)
    # Insert candidate metadata in Postgres
    pg_cursor.execute(
        "INSERT INTO candidates (name, email, minio_path, role) VALUES (%s, %s, %s, %s) RETURNING id",
        (candidate_name, email, object_name, role)
    )
    candidate_id = pg_cursor.fetchone()[0]
    pg_conn.commit()
    # Extract text from PDF
    with pdfplumber.open(file_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    # Embed text
    doc = Document(
        page_content=text,
        metadata={
            "candidate_id": candidate_id,
            "name": candidate_name,
            "email": email,
            "role": role,
            "minio_path": object_name
        }
    )
    vectorstore.add_documents([doc])

    return {"candidate_id": candidate_id, "message": f"{candidate_name} ingested successfully!"}
