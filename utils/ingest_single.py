import os
import time
from google.genai import Client
from google.genai import types
from dotenv import load_dotenv

from utils.parser import extract_text_from_pdf
from utils.chunker import chunk_text
from utils.pinecone_utils import index

load_dotenv()

client = Client(api_key=os.getenv("GOOGLE_API_KEY"))


def classify_text_locally(text):
    text_lower = text.lower()

    ai_ml_keywords = ["machine learning", "tensorflow", "pytorch", "nlp", "llm", "deep learning", "computer vision", "artificial intelligence", "data science"]
    import re
    words = set(re.findall(r'\b\w+\b', text_lower))
    if any(kw in text_lower for kw in ai_ml_keywords) or "ai" in words or "ml" in words:
        return "ai_ml"

    cloud_keywords = ["aws", "azure", "gcp", "docker", "kubernetes", "devops", "ci/cd", "terraform", "cloud"]
    if any(kw in text_lower for kw in cloud_keywords):
        return "cloud"

    frontend_keywords = ["react", "angular", "vue", "javascript", "typescript", "html", "css", "ui/ux", "frontend"]
    if any(kw in text_lower for kw in frontend_keywords):
        return "frontend"

    backend_keywords = ["python", "django", "fastapi", "node", "golang", "java", "database", "sql", "postgres", "mongodb", "backend", "apis"]
    if any(kw in text_lower for kw in backend_keywords):
        return "backend"

    return None


def classify_resume(text):
    local_cat = classify_text_locally(text)
    if local_cat:
        return local_cat

    try:
        prompt = (
            "You are an expert recruitment system. Analyze the following resume text and classify it into exactly one of these categories:\n"
            "- 'cloud' (if focus is on AWS, Azure, GCP, Docker, Kubernetes, DevOps, CI/CD)\n"
            "- 'frontend' (if focus is on React, Angular, Vue, Javascript, HTML, CSS, UI/UX)\n"
            "- 'backend' (if focus is on Python, Django, FastAPI, Node, Go, Java, databases, APIs)\n"
            "- 'ai_ml' (if focus is on Machine Learning, Data Science, AI, PyTorch, TensorFlow, NLP, LLMs)\n"
            "- 'general' (if none of the above fit particularly well)\n\n"
            "Respond with ONLY the category name in lowercase (e.g. backend, cloud, frontend, ai_ml, general)."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, f"Resume Text:\n{text[:8000]}"]
        )
        category = response.text.strip().lower()

        valid_categories = {"cloud", "frontend", "backend", "ai_ml", "general"}
        if category in valid_categories:
            return category
    except Exception as e:
        print(f"Error classifying resume via Gemini, falling back to keywords: {e}")

    return "general"


def ingest_resume(file_path, filename):
    text = extract_text_from_pdf(file_path)
    category = classify_resume(text)
    chunks = chunk_text(text)

    if not chunks:
        return category

    response = client.models.embed_content(
        model="models/gemini-embedding-2",
        contents=chunks,
        config=types.EmbedContentConfig(output_dimensionality=384)
    )
    embeddings = [e.values for e in response.embeddings]

    ts = int(time.time())
    vectors = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        vectors.append({
            "id": f"{filename}_{ts}_{i}",
            "values": embedding,
            "metadata": {
                "text": chunk,
                "category": category,
                "source": filename,
                "chunk_index": i
            }
        })

    batch_size = 100
    for start in range(0, len(vectors), batch_size):
        index.upsert(vectors=vectors[start:start + batch_size])

    return category
