# from app.pdf_loader import load_pdf_files, filter_to_minmal_doc, split_extraced_docs
# from app.embeddings import create_embeddings
# from app.vectorstore import setup_pinecone_index
# from langchain_community.llms import Ollama
# from langchain_groq import ChatGroq
# import os

# from langchain.chains import create_retrieval_chain
# from langchain.chains.combine_documents import create_stuff_documents_chain
# from langchain_core.prompts import ChatPromptTemplate


# def get_rag_chain():
#     print("Initializing RAG...")

#     # SAME as your notebook
#     documents = load_pdf_files("data")
#     minimal_docs = filter_to_minmal_doc(documents)
#     text_chunks = split_extraced_docs(minimal_docs)

#     embedding = create_embeddings()

#     # IMPORTANT: pass chunks + embedding (same as notebook)
#     docsearch = setup_pinecone_index(text_chunks, embedding)

#     retriever = docsearch.as_retriever(search_kwargs={"k": 3})



#     llm = ChatGroq(
#         model="llama3-8b-8192",
#         groq_api_key=os.getenv("GROQ_API_KEY")
#     )

#     system_prompt = (
#         "You are a medical assistant. Use the context to answer. "
#         "If not found, say you don't know.\n\n{context}"
#     )

#     prompt = ChatPromptTemplate.from_messages([
#         ("system", system_prompt),
#         ("human", "{input}")
#     ])

#     qa_chain = create_stuff_documents_chain(llm, prompt)
#     rag_chain = create_retrieval_chain(retriever, qa_chain)

#     print("RAG Ready")

#     return rag_chain


from app.vectorstore import get_vectorstore
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Load env variables
load_dotenv()


def get_rag_chain():
    print("Initializing RAG...")

    # ✅ Use existing Pinecone index (NO PDF loading)
    docsearch = get_vectorstore()

    retriever = docsearch.as_retriever(search_kwargs={"k": 3})

    # Groq LLM
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        groq_api_key=os.getenv("GROQ_API_KEY"),
        temperature=0
    )

    system_prompt = (
        "Answer ONLY using the provided context.\n"
        "Do NOT use any external or prior knowledge.\n"
        "If the answer is not explicitly present in the context, respond exactly with:\n"
        "\"I don't have enough information to answer this question .Do you have any other query ?\"\n\n"
        "Context:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])

    qa_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, qa_chain)

    print("RAG Ready")

    return rag_chain