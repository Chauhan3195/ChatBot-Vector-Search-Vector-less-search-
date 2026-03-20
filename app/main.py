# from fastapi import FastAPI
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse
# from app.rag import get_rag_chain

# # FastAPI instance
# application = FastAPI()

# # Mount static files
# application.mount("/static", StaticFiles(directory="app/static"), name="static")

# # Initialize your RAG chain once at startup
# rag_chain = get_rag_chain()

# # Request model
# from pydantic import BaseModel
# class ChatRequest(BaseModel):
#     message: str

# # Homepage route
# @application.get("/")
# def home():
#     return FileResponse("app/templates/index.html")

# # API route to get chatbot response
# # @application.post("/chat")
# # def chat(request: ChatRequest):
# #     response = rag_chain.invoke({"input": request.message})
# #     return {"answer": response}

# # @application.post("/chat")
# # async def chat(request: ChatRequest):
# #     try:
# #         # Async call to the chain
# #         result = await rag_chain.ainvoke({"input": request.message})
        
# #         # Extract text safely
# #         if isinstance(result, dict):
# #             answer = result.get("output_text") or result.get("text") or str(result)
# #         else:
# #             answer = str(result)

# #         return {"answer": answer}
    
# #     except Exception as e:
# #         return {"answer": f"Error: {str(e)}"}

# # @application.post("/chat")
# # async def chat(request: ChatRequest):
# #     try:
# #         # Async call to the chain
# #         result = await rag_chain.ainvoke({"input": request.message})
        
# #         # Extract only the 'answer' field
# #         if isinstance(result, dict):
# #             answer = result.get("answer", "Sorry, no answer returned.")
# #         else:
# #             answer = str(result)

# #         return {"answer": answer}
    
# #     except Exception as e:
# #         return {"answer": f"Error: {str(e)}"}

# @application.post("/chat")
# async def chat(request: ChatRequest):
#     try:
#         # Async call to the RAG chain
#         result = await rag_chain.ainvoke({"input": request.message})

#         # Extract raw answer
#         if isinstance(result, dict):
#             raw_answer = result.get("answer") or result.get("output_text") or str(result)
#         else:
#             raw_answer = str(result)

#         # Format the text nicely
#         formatted_answer = format_text(raw_answer)

#         return {"answer": formatted_answer}
    
#     except Exception as e:
#         return {"answer": f"Error: {str(e)}"}


# def format_text(text: str) -> str:
#     """
#     Adds newlines and HTML-friendly formatting for long responses.
#     """
#     import re

#     # Split by double newlines or sentences for readability
#     paragraphs = re.split(r'\n\n|(?<=[.!?]) ', text)

#     # Wrap each paragraph in <p> for HTML
#     html_paragraphs = [f"<p>{p.strip()}</p>" for p in paragraphs if p.strip()]

#     # Return combined HTML
#     return "".join(html_paragraphs)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.rag import get_rag_chain

application = FastAPI()

application.mount("/static", StaticFiles(directory="app/static"), name="static")

rag_chain = None

@application.on_event("startup")
def startup_event():
    global rag_chain
    rag_chain = get_rag_chain()

class ChatRequest(BaseModel):
    message: str

@application.get("/")
def home():
    return FileResponse("app/templates/index.html")

@application.post("/chat")
async def chat(request: ChatRequest):
    try:
        result = await rag_chain.ainvoke({"input": request.message})

        raw_answer = result.get("answer", str(result))

        return {"answer": format_text(raw_answer)}

    except Exception as e:
        return {"answer": f"Error: {str(e)}"}


def format_text(text: str) -> str:
    paragraphs = text.split("\n")
    return "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())