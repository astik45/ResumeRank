import os
from dotenv import load_dotenv
from utils.ingest_single import ingest_resume

load_dotenv()

RESUME_FOLDER = "data/resumes"

for filename in os.listdir(RESUME_FOLDER):
    if filename.endswith(".pdf"):
        path = os.path.join(RESUME_FOLDER, filename)
        print(f"Processing {filename}...")
        try:
            category = ingest_resume(path, filename)
            print(f"Uploaded {filename} with category: {category}")
        except Exception as e:
            print(f"Error processing {filename}: {e}")