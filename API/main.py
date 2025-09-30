from fastapi import FastAPI, UploadFile, Form
from Ingestion.ingest import ingest_cv
from Retrieval.retriever import answer_question
import shutil
import os
os.environ["USE_TF"] = "0"

app = FastAPI(title="CV Analysis Ingestion API")

UPLOAD_FOLDER = "tmp_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/upload_cv/")
async def upload_cv(
    file: UploadFile,
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...)
):
    # Save uploaded file temporarily
    tmp_file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(tmp_file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    # Ingest CV
    result = ingest_cv(tmp_file_path, name, email, role)
    # Remove temp file
    os.remove(tmp_file_path)
    return result

@app.post("/ask/")
async def ask_question(question: str = Form(...)):
    answer = answer_question(question)
    return {"question": question, "answer": answer}
