# Job Search Assistant — A RAG-Powered Document Q&A Tool

A retrieval-augmented generation (RAG) system that lets you upload job-search documents (resumes, offer letters, JDs, HR policies) and ask natural-language questions about them — grounded entirely in your own files, not the model's general knowledge.

**Why I built this:** While applying for jobs after graduating, I was juggling dozens of PDFs — offer letters, JDs, policy docs — and kept manually re-reading them to answer simple questions ("what's the notice period in this offer?", "does this JD ask for React?"). I built this to solve that problem directly, and to learn how production RAG pipelines are actually built.

---

## What it does

1. Upload a PDF and tag it (resume, offer letter, JD, HR policy, or general)
2. The system extracts the text, splits it into chunks, and embeds each chunk into a vector database
3. Ask a question in plain English
4. The system finds the most relevant chunks from your uploaded documents and asks an LLM to answer **using only that retrieved context**
5. The answer comes back along with the source document(s) it was pulled from

This is the core idea behind RAG: instead of hoping the model "knows" the answer, you retrieve the actual relevant text first, then ask the model to reason over it. This grounds the answer in real data and reduces hallucination.

---

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌───────────────┐      ┌─────────────┐
│   Upload    │ ───▶ │   Chunking   │ ───▶ │   Embedding   │ ───▶ │  ChromaDB   │
│   (PDF)     │      │ (LangChain)  │      │(MiniLM-L6-v2) │      │ (vector DB) │
└─────────────┘      └──────────────┘      └───────────────┘      └─────────────┘
                                                                          │
┌─────────────┐      ┌──────────────┐      ┌───────────────┐            │
│   Answer    │ ◀─── │  Claude API  │ ◀─── │   Retrieval   │ ◀──────────┘
│ + Sources   │      │ (generation) │      │ (top-k search)│
└─────────────┘      └──────────────┘      └───────────────┘
```

**Backend:** Python, FastAPI
**Frontend:** React (Vite)
**Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (runs locally, no API cost)
**Vector database:** ChromaDB (persistent, local)
**LLM:** Claude (Anthropic API) for answer generation

---

## Key design decisions and tradeoffs

### Why chunk size 500 with 50-character overlap?
Embedding an entire document as one vector loses precision (too coarse — a question about one clause returns the whole document). Embedding every sentence separately loses context (too fine — related information gets split apart). 500 characters is large enough to hold a complete idea (e.g., one clause of a policy) while staying precise enough for accurate retrieval. The 50-character overlap prevents a sentence from being awkwardly cut in half at a chunk boundary, so no information is lost between chunks.

### Why local embeddings instead of an embedding API?
Using `sentence-transformers` locally means embedding generation is free and has no rate limits — important for a project uploading multiple documents repeatedly during development and testing. The tradeoff is slightly lower embedding quality compared to larger hosted models (e.g., OpenAI's `text-embedding-3-large`), but for a document set of this size, the difference in retrieval accuracy is negligible.

### Why top-k = 4 for retrieval?
Retrieving too few chunks risks missing the answer if it's split across multiple chunks. Retrieving too many floods the LLM's context with irrelevant text, increasing cost and risk of the model getting distracted by unrelated content. 3–5 is a common sweet spot for document Q&A at this scale.

### Why metadata tagging (doc_type)?
Each chunk is stored with a `doc_type` tag (resume, offer_letter, jd, policy, general) at ingestion time. This enables filtered retrieval — a user can ask a question scoped to just their offer letters, rather than searching indiscriminately across every uploaded document. This was the key differentiator from a generic single-document PDF chatbot.

### Why explicit grounding instructions in the prompt?
The prompt explicitly instructs the model to answer **only** using the retrieved context, and to say "I don't have that information" if the answer isn't present. Without this instruction, the model may fall back on its own general knowledge and produce a plausible-sounding but ungrounded answer — defeating the purpose of RAG.

---

## What I'd improve at scale

- **Hybrid search:** combine vector similarity search with traditional keyword search (BM25) — vector search alone can miss exact-match queries (e.g., searching for a specific clause number or date)
- **Re-ranking:** add a re-ranking step after initial retrieval to reorder the top-k chunks by relevance before sending them to the LLM
- **Chunking strategy:** move from fixed-size chunking to semantic chunking (splitting on natural document structure — headers, paragraphs) for cleaner context boundaries
- **Streaming responses:** stream the LLM's answer token-by-token instead of waiting for the full response, for better perceived latency
- **Persistent multi-user storage:** currently ChromaDB runs as a local, single-user instance; a production version would need per-user isolation and a hosted vector DB (Pinecone, or ChromaDB in server mode)

---

## Running locally

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
# Add your ANTHROPIC_API_KEY to a .env file
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Backend runs on `http://127.0.0.1:8000`, frontend on `http://localhost:5173`.

---

## Tech stack

`Python` · `FastAPI` · `React` · `Vite` · `LangChain` · `ChromaDB` · `sentence-transformers` · `Claude API`
