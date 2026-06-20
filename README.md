# ResumeRank — AI-Powered Resume Ranking

I built this because going through hundreds of PDF resumes manually takes forever. Drop in a bunch of resumes, type what you need like "react developer with typescript experience", and it shows you the best matches sorted by relevance. Saves hours of reading.

Try it live: https://resumerank.streamlit.app

## Why this exists

Hiring teams get hundreds of PDF resumes. Reading them one by one is painful. This tool indexes everything into a searchable database so you can find relevant candidates in seconds instead of spending hours going through every file.

## How it works

**Ingestion:**
- Upload a PDF resume
- Text is extracted using pypdf
- Resume gets classified into a category — backend, frontend, ai/ml, cloud, or general (tries keyword matching first to save API calls, falls back to Gemini only when needed)
- Text is split into overlapping chunks (500 chars each, 100 overlap)
- Each chunk is embedded using Gemini Embedding 2 (384 dimensions)
- Vectors + metadata go to Pinecone

**Search:**
- Type a query like "senior backend engineer"
- Query gets classified and embedded the same way
- Pinecone searches with a category filter, returns top 20 chunks
- Results are deduplicated — only the best chunk per resume (max 5 unique results)
- If fewer than 5 matches, an unfiltered fallback search fills the remaining slots
- Optionally, Gemini generates a readable summary comparing candidates
- Full pipeline trace is available in the UI if you want to debug what happened

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

- Python 3.9+
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

Open `.env` and add your keys:

```
GOOGLE_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
PINECONE_ENVIRONMENT=your_env_here
```

## Running

```bash
# Web UI
streamlit run app.py

# REST API (separate terminal)
python main_api.py
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/search` | Search resumes |
| POST | `/api/ingest` | Upload one PDF |
| POST | `/api/ingest-batch` | Upload multiple PDFs |
| DELETE | `/api/clear` | Delete all vectors |
| GET | `/` | Root info |

Example search:

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
├── config.py                 Config & env vars
├── query_engine.py           Search pipeline
├── ingest.py                 CLI batch ingestion
├── generate_test_resumes.py  Generate test PDFs
├── requirements.txt
├── .env.example
├── .streamlit/
│   └── config.toml           Theme config
├── data/resumes/             Uploaded PDFs
├── tests/
│   ├── test_parser.py
│   ├── test_chunker.py
│   ├── test_query_engine.py
│   ├── test_api.py
│   └── conftest.py
└── utils/
    ├── parser.py             PDF text extraction
    ├── chunker.py            Text chunking
    ├── ingest_single.py      Classify + embed + upsert
    └── pinecone_utils.py     Pinecone helpers
```

## Tests

```bash
pytest tests/ -v
pytest tests/ --cov=.
```

## Notes

- Category detection tries local keywords first to avoid burning through Gemini quota. Falls back to the LLM only when needed.
- If you hit Gemini's rate limit (429), search still works — just the LLM summary gets skipped.
- Vector IDs include timestamps so re-uploading the same file doesn't leave stale embeddings lying around.
- Chunk size and overlap can be tweaked in `utils/chunker.py` (defaults are 500 chars with 100 overlap).
- Theme is configured via `.streamlit/config.toml` with a lavender/white setup. No custom CSS needed.
