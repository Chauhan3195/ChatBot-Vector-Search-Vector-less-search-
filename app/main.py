from fastapi import FastAPI , UploadFile, File , Request , BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse , JSONResponse
from pydantic import BaseModel
from app.rag import get_rag_chain
import os
import logging 
import shutil
from app.cache import get_cached_response, set_cached_response
from app.precompute_embeddings import build_index
from typing import List

# Make a folder for logs
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    filename="logs/app_errors.log",   # log file path
    level=logging.ERROR,              # log only errors and above
    format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
    force=True
)

application = FastAPI()

@application.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Logs full traceback including function name
    logging.error(f"Unhandled exception in path {request.url.path}: {exc}", exc_info=True)
    
    # Optional: return clean error to frontend
    return JSONResponse(
        status_code=500,
        content={"message": "An internal error occurred. Check logs for details."}
    )

# chat_history = []

application.mount("/static", StaticFiles(directory="app/static"), name="static")

UPLOAD_DIR = "data"

os.makedirs(UPLOAD_DIR, exist_ok=True)

#added


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_DIR = os.path.join(BASE_DIR, "..", "data")
UPLOAD_DIR = os.path.abspath(UPLOAD_DIR)

os.makedirs(UPLOAD_DIR, exist_ok=True)

print("UPLOAD DIR:", UPLOAD_DIR)  # debug

#### end of added


@application.post("/upload")
async def upload_file(files: List[UploadFile] = File(...)):
    try:
        saved_files = []

        for file in files:
            file_path = os.path.join(UPLOAD_DIR, file.filename)

            # optional: avoid overwrite
            if os.path.exists(file_path):
                base, ext = os.path.splitext(file.filename)
                file_path = os.path.join(UPLOAD_DIR, f"{base}_new{ext}")

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            print(f"File {file.filename} saved at {file_path}")
            saved_files.append(file.filename)

        # Build index ONCE after all uploads
        build_index()

        #  Reinitialize RAG
        global rag_chain
        rag_chain = get_rag_chain()

        return {"message": f"{len(saved_files)} files uploaded successfully", "files": saved_files}

    except Exception as e:
        return {"message": f"Upload failed: {str(e)}"}

rag_chain = None

@application.on_event("startup")
def startup_event():
    global rag_chain
    if rag_chain is None:
        rag_chain = get_rag_chain()


class ChatRequest(BaseModel):
    message: str

@application.get("/")
def home():
    return FileResponse("app/templates/index.html")

chat_history = []
@application.post("/chat")
async def chat(request: ChatRequest):
    global chat_history
    try:
        query = request.message.strip()
        cached_response = get_cached_response(query)
        if cached_response:
            return {"answer": format_text(cached_response)}
        
        if rag_chain is None:
            return {"answer": "RAG system not initialized. Please upload documents first."}

        print("cache missing now Calling LLM")   
         
        # result = await rag_chain.ainvoke({"input": query})
        result = await rag_chain.ainvoke({
            "input": query,
            "chat_history": chat_history  
        })

        raw_answer = result.get("answer", str(result))

            # Update history
        chat_history.append(("human", query))
        chat_history.append(("ai", raw_answer))


        formatted_answer = format_text(raw_answer)  

        set_cached_response(query, formatted_answer)

        return {"answer": formatted_answer}

    except Exception as e:
        return {"answer": f"Error: {str(e)}"}


def format_text(text: str) -> str:
    paragraphs = text.split("\n")
    return "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())

@application.get("/files")
async def list_files():
    return {"files": os.listdir(UPLOAD_DIR)}

@application.delete("/delete/{filename}")
async def delete_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)

    if os.path.exists(file_path):
        os.remove(file_path)

        # rebuild index after delete
        build_index()

        global rag_chain
        rag_chain = get_rag_chain()

    return {"message": "Deleted"}