# create_qdrant_collection.py

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
import json
import requests

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "cv-document-embeddings"
VECTOR_SIZE = 384

# Connect to Qdrant
qdrant = QdrantClient(url=QDRANT_URL)

# Delete collection if exists
existing_collections = [c.name for c in qdrant.get_collections().collections]
if COLLECTION_NAME in existing_collections:
    print(f"Deleting existing collection {COLLECTION_NAME}")
    qdrant.delete_collection(collection_name=COLLECTION_NAME)

# Create collection
qdrant.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
)
print(f"Collection '{COLLECTION_NAME}' created with {VECTOR_SIZE} dimensions")

payload_indexes = {
    "candidate_id": {"type": "integer"},
    "email": {"type": "keyword"},
    "role": {"type": "keyword"}
}

url = f"{QDRANT_URL}/collections/{COLLECTION_NAME}/indexes"
headers = {"Content-Type": "application/json"}
response = requests.put(url, data=json.dumps(payload_indexes), headers=headers)

if response.status_code == 200:
    print("Payload indexes created successfully")
else:
    print("Failed to create payload indexes")
    print(response.status_code, response.text)
