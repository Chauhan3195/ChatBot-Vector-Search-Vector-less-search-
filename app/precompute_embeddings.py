# precompute_embeddings.py
from app.pdf_loader import load_pdf_files, filter_to_minmal_doc, split_extraced_docs
from app.embeddings import create_embeddings
from langchain_community.vectorstores import FAISS
import pickle

FAISS_INDEX_PATH = "faiss_index"
def build_index():
    # Load PDFs and split
    documents = load_pdf_files("data")
    if not documents:
        print(" No documents found. Skipping indexing.")
        return

    minimal_docs = filter_to_minmal_doc(documents)
    text_chunks = split_extraced_docs(minimal_docs)

    if not text_chunks:
        print(" No chunks generated. Skipping indexing.")
        return
    # Save chunks for BM25

    with open("chunks.pkl", "wb") as f:
        pickle.dump(text_chunks, f)

    print("Chunks saved successfully")

    # Embeddings
    embedding = create_embeddings()

    # Create FAISS vector store from documents
    vectorstore = FAISS.from_documents(text_chunks, embedding)

    # Save locally
    vectorstore.save_local("faiss_index")

    print("Embeddings precomputed and stored in FAISS!")

    if __name__ == "__main__":
        build_index()