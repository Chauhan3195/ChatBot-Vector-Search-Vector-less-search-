# precompute_embeddings.py
from app.pdf_loader import load_pdf_files, filter_to_minmal_doc, split_extraced_docs
from app.embeddings import create_embeddings
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from app.config import PINECONE_API_KEY, PINECONE_INDEX_NAME
from app.config import PINECONE_CLOUD, PINECONE_REGION

# Load PDFs and split
documents = load_pdf_files("data")
minimal_docs = filter_to_minmal_doc(documents)
text_chunks = split_extraced_docs(minimal_docs)

# Embeddings
embedding = create_embeddings()

# Pinecone setup
pc = Pinecone(api_key=PINECONE_API_KEY)
if not pc.has_index(PINECONE_INDEX_NAME):
    pc.create_index(name=PINECONE_INDEX_NAME, dimension=384, metric="cosine", 
                           spec=ServerlessSpec(
                                    cloud=PINECONE_CLOUD,      # e.g. "aws"
                                    region=PINECONE_REGION,    # e.g. "us-east-1"
        ),)


# Push documents once
# vectorstore = PineconeVectorStore.from_documents(
#     documents=text_chunks,
#     embedding=embedding,
#     index_name=PINECONE_INDEX_NAME
# )
vectorstore = PineconeVectorStore(
    index_name=PINECONE_INDEX_NAME,
    embedding=embedding,
)

## added by m to cceta btcvahj es 
batch_size = 25  # if you still see 2MB error, reduce to 10
for i in range(0, len(text_chunks), batch_size):
    batch = text_chunks[i : i + batch_size]
    vectorstore.add_documents(batch)
#####################################
print("Embeddings precomputed and stored in Pinecone!")