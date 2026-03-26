from fastapi import FastAPI , UploadFile, File , Request , BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse , JSONResponse
from pydantic import BaseModel
from app.rag import get_rag_chain
import hashlib  ,json , os , logging , shutil 
from app.cache import get_cached_response, set_cached_response
from app.precompute_embeddings import build_index
from typing import List


# Make a folder for logs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "logs", "app.log")

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # also print to console
    ],
    force=True
)

logger = logging.getLogger("chatbot_app")

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

chat_history = []

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
# Keep a dictionary to store file hashes (you could also persist in a JSON/db)
# Store uploaded file hashes
HASH_FILE = "uploaded_hashes.json"

# Load existing hashes at startup
if os.path.exists(HASH_FILE):
    with open(HASH_FILE, "r") as f:
        uploaded_file_hashes = json.load(f)
else:
    uploaded_file_hashes = {}

def save_hashes():
    with open(HASH_FILE, "w") as f:
        json.dump(uploaded_file_hashes, f, indent=2)

def get_file_hash(file: UploadFile) -> str:
    """Compute SHA256 hash of uploaded file without reading entire content in memory."""
    hash_sha256 = hashlib.sha256()
    file.file.seek(0)  # Ensure reading from start
    for chunk in iter(lambda: file.file.read(4096), b""):
        hash_sha256.update(chunk)
    file.file.seek(0)  # Reset for saving later
    return hash_sha256.hexdigest()

def check_duplicate(file: UploadFile) -> bool:
    """Return True if file already uploaded (by content)."""
    file_hash = get_file_hash(file)
    return file_hash in uploaded_file_hashes.values()

def register_file(file: UploadFile):
    """Save file hash to dict and persist to disk."""
    file_hash = get_file_hash(file)
    uploaded_file_hashes[file.filename] = file_hash
    save_hashes()

@application.post("/upload")
async def upload_file(files: List[UploadFile] = File(...)):
    try:
        saved_files = []

        for file in files:
            if check_duplicate(file):
                return {"message": f"File '{file.filename}' already uploaded."}
            file_path = os.path.join(UPLOAD_DIR, file.filename)

            # optional: avoid overwrite
            # if os.path.exists(file_path):
            #     base, ext = os.path.splitext(file.filename)
            #     file_path = os.path.join(UPLOAD_DIR, f"{base}_new{ext}")

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Register hash
            register_file(file)
            
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


from fastapi import Request
import time

@application.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request start
    logger.info(f"Request start: {request.method} {request.url.path}")

    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url.path} - {e}", exc_info=True)
        raise e

    process_time = time.time() - start_time
    logger.info(f"Request end: {request.method} {request.url.path} - Status {response.status_code} - Time {process_time:.3f}s")

    return response