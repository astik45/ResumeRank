# ResumeRank — AI-Powered Resume Ranking

AI-powered resume ranking tool. Upload PDFs, type what you're looking for (like "react developer with typescript experience"), and it finds the best matching candidates ranked by relevance. Built with Gemini + Pinecone vector search.

## Why this exists

Hiring teams get hundreds of PDF resumes. Going through them manually takes hours. This tool indexes everything into a searchable database so you can find relevant candidates in seconds instead of reading through every file.

## How it works

**Ingestion:**
- You upload a PDF resume
- Text is extracted (pypdf)
- Resume gets classified into a category — backend, frontend, ai_ml, cloud, or general (uses keyword matching first to save API calls, falls back to Gemini LLM)
- Text is split into overlapping chunks (500 chars each, 100 overlap)
- Each chunk is embedded using `gemini-embedding-2` (384 dimensions)
- Vectors + metadata go to Pinecone

**Search:**
- You type a query like "senior backend engineer"
- Query is classified the same way (local keywords > Gemini LLM > general fallback)
- Query is embedded with the same model
- Pinecone searches with a category filter, returns top 20 chunks
- Results are deduplicated — only the best chunk per resume file (max 5 unique sources)
- If fewer than 5 results, an unfiltered fallback search fills remaining slots
- Optionally, Gemini generates a readable summary comparing candidates
- Full pipeline trace is available for debugging in the UI

## Tech stack

| Component | What |
|-----------|------|
| Frontend | Streamlit (port 8501) |
| API | FastAPI + Uvicorn (port 8000) |
| LLM | Gemini 2.5 Flash |
| Embeddings | Gemini Embedding 2 (384d) |
| Vector DB | Pinecone (serverless) |
| PDF parser | pypdf |
| Config | python-dotenv |

## Requirements

- Python 3.9 or newer
- Google Gemini API key
- Pinecone API key (free tier works)

## Setup

```bash
git clone <repo-url>
cd resume-rag
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` with your keys:

```
GOOGLE_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
PINECONE_ENVIRONMENT=your_env_here
```

### Deploy on Streamlit Cloud

1. Push this repo to GitHub
2. Go to https://share.streamlit.io → New app → select this repo, **Main file = `app.py`**
3. In **Settings → Secrets**, add:
   ```toml
   GOOGLE_API_KEY = "your_key_here"
   PINECONE_API_KEY = "your_key_here"
   PINECONE_ENVIRONMENT = "your_env_here"
   PINECONE_INDEX_NAME = "resume-qa"
   ```
4. Deploy — done. No `.env` file needed on the cloud (Streamlit injects secrets as env vars).

## Running

```bash
# Web UI
streamlit run app.py

# REST API (separate terminal)
python main_api.py
```

| URL | What |
|-----|------|
| http://localhost:8501 | Streamlit UI |
| http://localhost:8000/docs | API docs (Swagger) |
| http://localhost:8000/redoc | API docs (Redoc) |

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Service health check |
| POST | `/api/search` | Search resumes |
| POST | `/api/ingest` | Upload single PDF |
| POST | `/api/ingest-batch` | Upload multiple PDFs |
| DELETE | `/api/clear` | Delete all indexed vectors |
| GET | `/` | Root info |

Example search request:

```json
POST /api/search
{
  "query": "machine learning engineer with NLP experience",
  "top_k": 5
}
```

## Project structure

```
resume-rag/
├── app.py                    Streamlit frontend
├── main_api.py               FastAPI backend
├── config.py                 Configuration & env loading
├── query_engine.py           Search pipeline — classify, embed, search, dedupe, generate
├── ingest.py                 CLI batch ingestion
├── generate_test_resumes.py  Generate sample PDFs for testing
├── requirements.txt
├── .env.example              Environment variable template
├── .streamlit/
│   ├── config.toml           Streamlit theme config
│   └── secrets.toml.example  Secrets template for Streamlit Cloud
├── data/resumes/             Uploaded PDFs stored here
├── tests/
│   ├── test_parser.py
│   ├── test_chunker.py
│   ├── test_query_engine.py
│   ├── test_api.py
│   └── conftest.py
└── utils/
    ├── parser.py             Extract text from PDF
    ├── chunker.py            Split text into overlapping chunks
    ├── ingest_single.py      Classify + chunk + embed + upsert pipeline
    └── pinecone_utils.py     Pinecone client & helpers
```

## Tests

```bash
pytest tests/ -v
pytest tests/ --cov=.
```

## Notes

- Local keyword classification runs first to avoid unnecessary Gemini API calls (saves quota)
- If Gemini rate limit is hit (429), search results still work — only the LLM summary is skipped
- Timestamp-based vector IDs prevent stale embeddings when re-uploading the same file
- Change chunk size or overlap in `utils/chunker.py` if needed (defaults: 500/100)
- Theme is configured via `.streamlit/config.toml` (lavender/white) — no custom CSS needed
