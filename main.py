from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import os
from ingestion import process_pdf
from retrieval import ask_question

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://job-search-rag-assistant.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Job Search RAG API is running"}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), doc_type: str = Form("general")):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Process the PDF: chunk, embed, store in ChromaDB
    result = process_pdf(file_path, file.filename, doc_type)

    return {
        "filename": file.filename,
        "status": "uploaded and processed successfully",
        "chunks_stored": result["chunks_stored"]
    }

@app.post("/ask")
async def ask(question: str = Form(...), doc_type: str = Form(None)):
    result = ask_question(question, doc_type_filter=doc_type)
    return result