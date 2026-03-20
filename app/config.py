# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "medical-chatboat")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")
PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CHUNK_SIZE = 1600
CHUNK_OVERLAP = 200

# ✅ ADD THIS
PDF_PATH = os.getenv("PDF_PATH")

