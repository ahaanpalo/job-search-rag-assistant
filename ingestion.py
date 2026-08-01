from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
import uuid

# Load the embedding model once (reused across calls)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Set up persistent ChromaDB client (saves to disk in ./chroma_db)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("job_search_docs")

# Text splitter config
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)

def process_pdf(file_path: str, filename: str, doc_type: str = "general"):
    """
    Loads a PDF, splits it into chunks, embeds each chunk,
    and stores it in ChromaDB with metadata.
    """
    # Step 1: Load and extract text
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    full_text = "\n".join([page.page_content for page in pages])

    # Step 2: Split into chunks
    chunks = splitter.split_text(full_text)

    if not chunks:
        return {"chunks_stored": 0, "message": "No text extracted from PDF"}

    # Step 3: Embed each chunk
    embeddings = embedding_model.encode(chunks).tolist()

    # Step 4: Store in ChromaDB
    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [{"filename": filename, "doc_type": doc_type} for _ in chunks]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

    return {"chunks_stored": len(chunks), "filename": filename}