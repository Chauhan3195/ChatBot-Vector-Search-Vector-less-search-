from langchain_community.vectorstores import FAISS
from app.config import PINECONE_API_KEY, PINECONE_INDEX_NAME
from app.embeddings import create_embeddings
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Point directly to faiss_index inside project root
FAISS_INDEX_PATH = os.path.join(BASE_DIR, "faiss_index")
print("Loading FAISS from:", FAISS_INDEX_PATH)
def get_vectorstore():
    # Initialize Pinecone

    # Load embeddings model
    embedding = create_embeddings()
    index_file = os.path.join(FAISS_INDEX_PATH, "index.faiss")
        # Check if index exists
    if not os.path.exists(index_file):
        print("FAISS index not found at:", index_file)
        return None
       
        return None
    # Load existing FAISS index from local storage
    vectorstore = FAISS.load_local(
        FAISS_INDEX_PATH,
        embedding,
        allow_dangerous_deserialization=True
    )

    return vectorstore


   

