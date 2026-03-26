from app.vectorstore import get_vectorstore
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

from langchain.chains import  create_history_aware_retriever ,create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate , MessagesPlaceholder
from app.bm25_retriever import BM25Retriever, HybridRetriever
import pickle
# Load env variables
load_dotenv()

def load_chunks():
    
    if not os.path.exists("chunks.pkl"):
        print("chunks.pkl not found")
        return None

    with open("chunks.pkl", "rb") as f:
        return pickle.load(f)


def get_rag_chain():
    try:    
            print("Initializing Hybrid RAG...")
            # Load vectorstore (FAISS / Pinecone)
            vectorstore = get_vectorstore()
            if vectorstore is None:
                print(" Vectorstore not available.")
                return None

            # Load precomputed chunks (NO PDF reprocessing)
            documents = load_chunks()

            if not documents:
                print(" No documents found. RAG cannot be initialized.")
                return None

            # BM25 retriever
            bm25_retriever = BM25Retriever(documents)

            #  Hybrid retriever (vector + keyword)
            retriever = HybridRetriever(
                vectorstore=vectorstore,
                bm25_retriever=bm25_retriever
            )

            # Groq LLM
            llm = ChatGroq(
                model="llama-3.1-8b-instant",
                groq_api_key=os.getenv("GROQ_API_KEY"),
                temperature=0
            )

            # system_prompt = (
            #     "Answer ONLY using the provided context.\n"
            #     "Do NOT use any external or prior knowledge.\n"
            #     "If the answer is not explicitly present in the context, respond exactly with:\n"
            #     "\"I don't have enough information to answer this question .Do you have any other query ?\"\n\n"
            #     "Context:\n{context}"
            # )
            system_prompt=(
                "You are a helpful AI assistant.\n\n"
                "1. If the user message is a greeting (e.g., hi, hello, hey, good morning, thanks, bye):\n"
                "- Respond in a friendly and polite tone.\n"
                "- Do NOT use the context.\n"
                "- You may ask a short follow-up question like 'How can I help you?'\n\n"

                "2. If the user asks for 'short':\n"
                "- Answer in EXACTLY one to two sentence.\n"        
                "- No explanation.\n\n"

                "3. If the user asks for 'brief' or 'summary' or 'concise':\n"
                "- Answer in 4 to 5 entences.\n"
                "- Maximum 50 words.\n"
                "- Do not add extra explanation.\n\n"

                "4. For all other questions:\n"
                "- Answer ONLY using the provided context.\n"
                "- Do NOT use any external or prior knowledge.\n"
                "- If the answer is not explicitly present in the context, respond exactly with:\n"
                "\"I don't have enough information to answer this question .Do you have any other query ?\"\n\n"

                    "Context:\n{context}"
                    )
            contextualize_q_prompt = ChatPromptTemplate.from_messages([
                ("system", 
                "Given the chat history and the latest user question, "
                "rewrite the question so it is standalone and clear. "
                "Do NOT answer the question."
                ),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}")
            ])
            history_aware_retriever = create_history_aware_retriever(
                llm,
                retriever,
                contextualize_q_prompt
            )
            # prompt = ChatPromptTemplate.from_messages([
            #     ("system", system_prompt),
            #     ("human", "{input}")
            # ])
            prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),   
            ("human", "{input}")
            ])

            qa_chain = create_stuff_documents_chain(llm, prompt)
            # rag_chain = create_retrieval_chain(retriever, qa_chain)
            qa_chain = create_stuff_documents_chain(llm, prompt)

            rag_chain  = create_retrieval_chain(
                history_aware_retriever,   
                qa_chain
            )

            print("RAG Ready")

            return rag_chain
    except Exception as e:
        print("Error initializing RAG:", str(e))
        return None 