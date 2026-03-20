# from pinecone import Pinecone, ServerlessSpec
# from langchain_pinecone import PineconeVectorStore
# from app.config import PINECONE_API_KEY, PINECONE_INDEX_NAME


# def setup_pinecone_index(text_chunks, embedding):
#     pc = Pinecone(api_key=PINECONE_API_KEY)

#     if not pc.has_index(PINECONE_INDEX_NAME):
#         pc.create_index(
#             name=PINECONE_INDEX_NAME,
#             dimension=384,
#             metric="cosine",
#             spec=ServerlessSpec(cloud="aws", region="us-east-1")
#         )

#     # SAME as notebook (this is key)
#     docsearch = PineconeVectorStore.from_documents(
#         documents=text_chunks,
#         embedding=embedding,
#         index_name=PINECONE_INDEX_NAME
#     )

#     return docsearch

from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from app.config import PINECONE_API_KEY, PINECONE_INDEX_NAME
from app.embeddings import create_embeddings


def get_vectorstore():
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)

    # Check if index exists
    existing_indexes = [index.name for index in pc.list_indexes()]

    if PINECONE_INDEX_NAME not in existing_indexes:
        raise ValueError("Pinecone index not found. Run precompute_embeddings.py first.")

    # Load embeddings model
    embedding = create_embeddings()

    # Connect to existing index (NO re-embedding)
    vectorstore = PineconeVectorStore(
        index_name=PINECONE_INDEX_NAME,
        embedding=embedding
    )

    return vectorstore