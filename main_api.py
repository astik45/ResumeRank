import os
import logging
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from config import config, logger
from utils.ingest_single import ingest_resume
from utils.pinecone_utils import delete_all_vectors
from query_engine import search_resumes

app = FastAPI(
    title=config.APP_NAME,
    description="AI-powered Resume Intelligence & Ranking System",
    version=config.APP_VERSION,
)

origins = [
    "http://localhost:3000",
    "http://localhost:8501",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchQuery(BaseModel):
    query: str
    top_k: Optional[int] = config.TOP_K_RESULTS


class SearchResult(BaseModel):
    filename: str
    score: float
    content: str


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int


class HealthResponse(BaseModel):
    status: str
    version: str


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    try:
        logger.info("Health check performed")
        return HealthResponse(
            status="healthy",
            version=config.APP_VERSION
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service unhealthy"
        )


@app.post("/api/search", response_model=SearchResponse)
async def search(query_obj: SearchQuery):
    try:
        if not query_obj.query or len(query_obj.query.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query cannot be empty"
            )

        logger.info(f"Searching for: {query_obj.query}")
        search_res = search_resumes(query_obj.query, top_k=query_obj.top_k)
        matches = search_res.get("matches", [])

        search_results = [
            SearchResult(
                filename=match.get("metadata", {}).get("source", "Unknown"),
                score=match.get("score", 0.0),
                content=match.get("metadata", {}).get("text", "")
            )
            for match in matches
        ]

        logger.info(f"Found {len(search_results)} results")
        return SearchResponse(
            query=query_obj.query,
            results=search_results,
            total_results=len(search_results)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


@app.post("/api/ingest")
async def ingest(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )

        os.makedirs(config.DATA_DIR, exist_ok=True)
        file_path = os.path.join(config.DATA_DIR, file.filename)

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"Ingesting resume: {file.filename}")
        ingest_resume(file_path)

        return {
            "status": "success",
            "filename": file.filename,
            "message": f"Resume {file.filename} ingested successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingest error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resume ingestion failed"
        )


@app.post("/api/ingest-batch")
async def ingest_batch(files: List[UploadFile] = File(...)):
    try:
        results = []
        os.makedirs(config.DATA_DIR, exist_ok=True)

        for file in files:
            try:
                if not file.filename.endswith(".pdf"):
                    results.append({
                        "filename": file.filename,
                        "status": "failed",
                        "error": "Only PDF files supported"
                    })
                    continue

                file_path = os.path.join(config.DATA_DIR, file.filename)
                content = await file.read()

                with open(file_path, "wb") as f:
                    f.write(content)

                logger.info(f"Batch ingesting: {file.filename}")
                ingest_resume(file_path)

                results.append({
                    "filename": file.filename,
                    "status": "success"
                })
            except Exception as e:
                logger.error(f"Failed to ingest {file.filename}: {str(e)}")
                results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": str(e)
                })

        return {
            "status": "completed",
            "total": len(files),
            "results": results
        }
    except Exception as e:
        logger.error(f"Batch ingest error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch ingestion failed"
        )


@app.delete("/api/clear")
async def clear_all():
    try:
        logger.warning("Clearing all indexed resumes")
        delete_all_vectors()
        return {
            "status": "success",
            "message": "All resumes cleared from index"
        }
    except Exception as e:
        logger.error(f"Clear error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear resumes"
        )


@app.get("/")
async def root():
    return {
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "docs": "/docs",
        "status": "running"
    }


if __name__ == "__main__":
    logger.info(f"Starting {config.APP_NAME} API server...")
    uvicorn.run(
        "main_api:app",
        host=config.API_HOST,
        port=config.API_PORT,
        log_level=config.LOG_LEVEL.lower(),
        reload=config.DEBUG_MODE
    )
