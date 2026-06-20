from pinecone import Pinecone
from dotenv import load_dotenv
import os

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

def delete_all_vectors():
    try:
        index.delete(delete_all=True)
    except Exception as e:
        # Ignore namespace not found / empty index error
        print(f"Pinecone delete completed or index already empty: {e}")