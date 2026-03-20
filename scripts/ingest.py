import hashlib
import os
import uuid

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import (
    PDF_PATH,
    PINECONE_API_KEY,
    PINECONE_CLOUD,
    PINECONE_INDEX_NAME,
    PINECONE_REGION,
)

# ✅ FIX: use embeddings from embeddings.py (NOT rag.py)
from app.embeddings import create_embeddings


load_dotenv()


def _stable_id(source: str, page: int | None, chunk_index: int, text: str) -> str:
    h = hashlib.sha256()
    h.update(source.encode("utf-8"))
    h.update(b"|")
    h.update(str(page).encode("utf-8"))
    h.update(b"|")
    h.update(str(chunk_index).encode("utf-8"))
    h.update(b"|")
    h.update(text.encode("utf-8", errors="ignore"))
    return h.hexdigest()[:32]


@retry(stop=stop_after_attempt(6), wait=wait_exponential(multiplier=1, min=1, max=30))
def _upsert(index, vectors):
    index.upsert(vectors=vectors)


def main():
    if not os.path.exists(PDF_PATH):
        raise SystemExit(
            f"PDF not found at '{PDF_PATH}'. Put your PDF there or update PDF_PATH in .env"
        )

    # ✅ Load PDF
    loader = PyPDFLoader(PDF_PATH)
    pages = loader.load()

    # ✅ Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
    docs = splitter.split_documents(pages)

    # ✅ Embeddings
    embeddings = create_embeddings()

    # ✅ Init Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)

    existing_indexes = [index.name for index in pc.list_indexes()]

    if PINECONE_INDEX_NAME not in existing_indexes:
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=384,  # matches MiniLM embeddings
            metric="cosine",
            spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
        )

    index = pc.Index(PINECONE_INDEX_NAME)

    batch_size = 64
    vectors = []

    run_id = str(uuid.uuid4())[:8]
    source = os.path.basename(PDF_PATH)

    # ✅ Process chunks
    for i, d in enumerate(tqdm(docs, desc="Embedding + Upserting")):
        text = (d.page_content or "").strip()
        if not text:
            continue

        md = d.metadata or {}
        page = md.get("page")

        if isinstance(page, float):
            page = int(page)
        if isinstance(page, str) and page.isdigit():
            page = int(page)

        # ✅ Create embedding
        vec = embeddings.embed_documents([text])[0]

        vid = _stable_id(source=source, page=page, chunk_index=i, text=text)

        vectors.append(
            {
                "id": vid,
                "values": vec,
                "metadata": {
                    "text": text,
                    "page": page,
                    "source": source,
                    "run_id": run_id,
                    "chunk_index": i,
                },
            }
        )

        #  Batch upsert
        if len(vectors) >= batch_size:
            _upsert(index, vectors)
            vectors = []

    #  Final upsert
    if vectors:
        _upsert(index, vectors)

    print(f" Done. Indexed {len(docs)} chunks into '{PINECONE_INDEX_NAME}'.")


if __name__ == "__main__":
    main()