# Job Search Assistant — A RAG-Powered Document Q&A Tool

A retrieval-augmented generation (RAG) system that lets you upload job-search documents (resumes, offer letters, JDs, HR policies) and ask natural-language questions about them — grounded entirely in your own files, not the model's general knowledge.

**Live app:** [job-search-rag-assistant.vercel.app](https://job-search-rag-assistant.vercel.app/)
**API docs:** [job-search-rag-backend.onrender.com/docs](https://job-search-rag-backend.onrender.com/docs)

**Why I built this:** While applying for jobs after graduating, I was juggling dozens of PDFs — offer letters, JDs, policy docs — and kept manually re-reading them to answer simple questions ("what's the notice period in this offer?", "does this JD ask for React?"). I built this to solve that problem directly, and to learn how production RAG pipelines are actually built end-to-end, from local prototype to live deployment.

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
│   (PDF)     │      │ (LangChain)  │      │ (Voyage AI)   │      │ (vector DB) │
└─────────────┘      └──────────────┘      └───────────────┘      └─────────────┘
                                                                          │
┌─────────────┐      ┌──────────────┐      ┌───────────────┐            │
│   Answer    │ ◀─── │  Claude API  │ ◀─── │   Retrieval   │ ◀──────────┘
│ + Sources   │      │ (generation) │      │ (top-k search)│
└─────────────┘      └──────────────┘      └───────────────┘
```

**Backend:** Python, FastAPI — containerized with Docker, deployed on Render
**Frontend:** React (Vite) — deployed on Vercel
**Embedding model:** Voyage AI (`voyage-3.5`) — Anthropic's recommended embeddings partner
**Vector database:** ChromaDB (persistent)
**LLM:** Claude (Anthropic API) for answer generation

---

## Key design decisions and tradeoffs

### Why Voyage AI for embeddings instead of a local model?
The first version of this project used `sentence-transformers` running locally inside the backend container. That worked fine on my laptop, but broke deployment: bundling PyTorch and a local embedding model pushed the container well past Render's free-tier 512MB memory limit, causing out-of-memory crashes on every deploy.

Switching to Voyage AI's embeddings API removed PyTorch from the container entirely, cutting memory usage dramatically and letting the app run comfortably within the free tier. This also reflects a legitimate production pattern: keeping a lightweight API server thin and offloading heavy ML inference to a dedicated service, rather than bundling multi-gigabyte ML libraries into every deploy. It's a deliberate separation of concerns — Voyage handles "understanding meaning" (embeddings), Claude handles "writing the answer" (generation) — two distinct pipeline stages that don't need to share a provider.

### Why chunk size 500 with 50-character overlap?
Embedding an entire document as one vector loses precision (too coarse — a question about one clause returns the whole document). Embedding every sentence separately loses context (too fine — related information gets split apart). 500 characters is large enough to hold a complete idea (e.g., one clause of a policy) while staying precise enough for accurate retrieval. The 50-character overlap prevents a sentence from being awkwardly cut in half at a chunk boundary, so no information is lost between chunks.

### Why top-k = 4 for retrieval?
Retrieving too few chunks risks missing the answer if it's split across multiple chunks. Retrieving too many floods the LLM's context with irrelevant text, increasing cost and risk of the model getting distracted by unrelated content. 3–5 is a common sweet spot for document Q&A at this scale.

### Why metadata tagging (doc_type)?
Each chunk is stored with a `doc_type` tag (resume, offer_letter, jd, policy, general) at ingestion time. This enables filtered retrieval — a user can ask a question scoped to just their offer letters, rather than searching indiscriminately across every uploaded document. This was the key differentiator from a generic single-document PDF chatbot.

### Why explicit grounding instructions in the prompt?
The prompt explicitly instructs the model to answer **only** using the retrieved context, and to say "I don't have that information" if the answer isn't present. Without this instruction, the model may fall back on its own general knowledge and produce a plausible-sounding but ungrounded answer — defeating the purpose of RAG.

---

## Deployment

- **Backend** is containerized with Docker and deployed on Render (free tier). CI happens implicitly through Render's GitHub integration — every push to `main` triggers an automatic rebuild and redeploy.
- **Frontend** is deployed on Vercel, connected to the same GitHub repo (`frontend/` subdirectory as the project root), with automatic redeploys on push.
- CORS is explicitly configured on the backend to allow requests only from the deployed frontend origin and local dev (`localhost:5173`).
- Note: the backend runs on Render's free tier, which spins down after 15 minutes of inactivity. The first request after idle time may take 30–50 seconds while the instance wakes up — this is expected free-tier behavior, not an application bug.

---

## What I'd improve at scale

- **Hybrid search:** combine vector similarity search with traditional keyword search (BM25) — vector search alone can miss exact-match queries (e.g., searching for a specific clause number or date)
- **Re-ranking:** add a re-ranking step after initial retrieval to reorder the top-k chunks by relevance before sending them to the LLM
- **Chunking strategy:** move from fixed-size chunking to semantic chunking (splitting on natural document structure — headers, paragraphs) for cleaner context boundaries
- **Streaming responses:** stream the LLM's answer token-by-token instead of waiting for the full response, for better perceived latency
- **Persistent multi-user storage:** currently ChromaDB runs as a single instance on the backend's filesystem; a production version would need per-user isolation and a hosted, persistent vector DB
- **CI test suite:** add automated tests (pytest) for the ingestion and retrieval pipeline, run via GitHub Actions on every push

---

## Running locally

**Backend:**
```bash
cd job-search-rag
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
# Add ANTHROPIC_API_KEY and VOYAGE_API_KEY to a .env file
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Backend runs on `http://127.0.0.1:8000`, frontend on `http://localhost:5173`.

**Docker (backend):**
```bash
docker build -t job-search-backend .
docker run -p 8000:8000 --env-file .env job-search-backend
```

---

## Tech stack

`Python` · `FastAPI` · `Docker` · `React` · `Vite` · `LangChain` · `ChromaDB` · `Voyage AI` · `Claude API` · `Render` · `Vercel`
