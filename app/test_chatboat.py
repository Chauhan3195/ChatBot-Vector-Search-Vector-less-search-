from app.rag import get_rag_chain

if __name__ == "__main__":
    question = "Could you please tell me about delhi?"

    # Step 1: Load chain
    rag_chain = get_rag_chain()

    # Step 2: Ask question
    response = rag_chain.invoke({"input": question})

    print(f"Q: {question}")
    print(f"A: {response['answer']}")