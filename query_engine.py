import os
from google.genai import Client
from google.genai import types
from dotenv import load_dotenv
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


def classify_query(query):
    local_cat = classify_text_locally(query)
    if local_cat:
        return local_cat, "Local Keyword Match (Skipped Gemini API to save quota)", f"Match found locally: '{local_cat}'"

    classification_prompt = (
        "You are an expert recruitment system. Classify the user's search query into exactly one of these categories:\n"
        "- 'cloud' (if focus is on AWS, Azure, GCP, Docker, Kubernetes, DevOps, CI/CD)\n"
        "- 'frontend' (if focus is on React, Angular, Vue, Javascript, HTML, CSS, UI/UX)\n"
        "- 'backend' (if focus is on Python, Django, FastAPI, Node, Go, Java, databases, APIs)\n"
        "- 'ai_ml' (if focus is on Machine Learning, Data Science, AI, PyTorch, TensorFlow, NLP, LLMs)\n"
        "- 'general' (if none of the above fit particularly well)\n\n"
        "Respond with ONLY the category name in lowercase (e.g. backend, cloud, frontend, ai_ml, general)."
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[classification_prompt, f"Query: {query}"]
        )
        category = response.text.strip().lower()

        valid_categories = {"cloud", "frontend", "backend", "ai_ml", "general"}
        if category in valid_categories:
            return category, classification_prompt, response.text
        raw_resp = response.text
    except Exception as e:
        raw_resp = f"Error: {e}"

    return "general", classification_prompt, f"{raw_resp} (Fallback applied: general)"


def _dedupe_by_source(matches, max_results=5):
    seen_sources = set()
    unique = []
    for m in matches:
        source = m.get("metadata", {}).get("source", "")
        if source not in seen_sources:
            seen_sources.add(source)
            unique.append(m)
            if len(unique) >= max_results:
                break
    return unique


def search_resumes(query, generate_summary=True, top_k=5):
    category, class_prompt, class_raw = classify_query(query)

    response_embed = client.models.embed_content(
        model="models/gemini-embedding-2",
        contents=query,
        config=types.EmbedContentConfig(output_dimensionality=384)
    )
    query_embedding = response_embed.embeddings[0].values

    pinecone_results = index.query(
        vector=query_embedding,
        top_k=20,
        filter={"category": category},
        include_metadata=True
    )
    filtered_matches = pinecone_results.get("matches", [])

    matches = _dedupe_by_source(filtered_matches, max_results=top_k)

    if len(matches) < top_k:
        already_seen = {m.get("metadata", {}).get("source", "") for m in matches}
        fallback_results = index.query(
            vector=query_embedding,
            top_k=20,
            include_metadata=True
        )
        for m in fallback_results.get("matches", []):
            source = m.get("metadata", {}).get("source", "")
            if source not in already_seen:
                already_seen.add(source)
                matches.append(m)
                if len(matches) >= top_k:
                    break

    system_instruction = (
        "You are an expert HR assistant and technical recruiter. "
        "Your job is to read the candidate resume chunks provided and generate a concise, readable summary "
        "answering the search query. Highlight key skills, experiences, or project matches, and direct the recruiter to the best candidates. "
        "If no candidates are found or the context is empty, explain that no matching profiles were found in the database. "
        "Do not make up any information. Use bullet points and clean structure."
    )

    generation_prompt = f"User Search Query: {query}\n\nCandidate Resume Context:\n"
    if not matches:
        generation_prompt += "\nNo candidate profiles found matching this category.\n"
    else:
        for i, m in enumerate(matches):
            meta = m.get("metadata", {})
            generation_prompt += f"\n[Candidate {i+1} | Source: {meta.get('source')} | Category: {meta.get('category')} | Score: {round(m.get('score', 0), 3)}]\n"
            generation_prompt += f"{meta.get('text')}\n"

    answer = ""
    raw_gen_response = ""
    if generate_summary:
        try:
            response_gen = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=generation_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3
                )
            )
            answer = response_gen.text
            raw_gen_response = response_gen.text
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                answer = (
                    "⚠️ **AI Summary Rate Limit Hit (Google Gemini API Quota Exceeded).**\n\n"
                    "The free-tier limit for Gemini API requests (20 requests per day or minute) has been exceeded. "
                    "**However, the Semantic Search and Ranking Engine still worked!** "
                    "Below, you can find the matching candidate profiles ranked by their matching scores directly from the Pinecone vector database."
                )
            else:
                answer = f"Error generating answer via Gemini: {e}"
            raw_gen_response = f"Error: {e}"
    else:
        answer = (
            "ℹ️ **AI summary generation is turned off.** "
            "Below are the semantically matched candidates ranked from the Pinecone database."
        )
        raw_gen_response = "Summary generation was bypassed by the user to conserve API quota."

    trace = {
        "classification": {
            "prompt": class_prompt,
            "raw_response": class_raw,
            "category": category
        },
        "embedding": {
            "model": "models/gemini-embedding-2",
            "dimensions": 384,
            "vector_sample": query_embedding[:10]
        },
        "search": {
            "filter": {"category": category},
            "filtered_chunks_retrieved": len(filtered_matches),
            "unique_sources_after_dedup": len({m.get("metadata", {}).get("source", "") for m in matches}),
            "fallback_used": len(matches) > len(_dedupe_by_source(filtered_matches, max_results=top_k)),
            "raw_matches": [
                {
                    "id": m.get("id"),
                    "score": m.get("score"),
                    "source": m.get("metadata", {}).get("source", ""),
                    "metadata": m.get("metadata")
                } for m in matches
            ]
        },
        "generation": {
            "system_instruction": system_instruction,
            "prompt": generation_prompt,
            "raw_response": raw_gen_response
        }
    }

    return {
        "answer": answer,
        "category": category,
        "matches": matches,
        "trace": trace
    }
