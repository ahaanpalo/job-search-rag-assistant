from sentence_transformers import SentenceTransformer
import chromadb
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

# Reuse the same embedding model and ChromaDB collection as ingestion.py
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("job_search_docs")

claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def ask_question(question: str, doc_type_filter: str = None, top_k: int = 4):
    """
    Embeds the question, retrieves the most relevant chunks from ChromaDB,
    sends them to Claude, and returns an answer with sources.
    """
    # Step 1: Embed the question
    query_embedding = embedding_model.encode([question]).tolist()

    # Step 2: Search ChromaDB (optionally filtered by doc_type)
    query_args = {
        "query_embeddings": query_embedding,
        "n_results": top_k
    }
    if doc_type_filter:
        query_args["where"] = {"doc_type": doc_type_filter}

    results = collection.query(**query_args)

    retrieved_chunks = results["documents"][0]
    metadatas = results["metadatas"][0]

    if not retrieved_chunks:
        return {"answer": "No relevant documents found.", "sources": []}

    # Step 3: Build context from retrieved chunks
    context = "\n\n".join(retrieved_chunks)

    # Step 4: Send to Claude
    prompt = f"""Answer the question using ONLY the context below.
If the answer isn't in the context, say "I don't have that information."

Context:
{context}

Question: {question}
"""

    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    answer_text = response.content[0].text

    # Step 5: Return answer + sources
    sources = [
        {"filename": m["filename"], "doc_type": m["doc_type"]}
        for m in metadatas
    ]

    return {"answer": answer_text, "sources": sources}