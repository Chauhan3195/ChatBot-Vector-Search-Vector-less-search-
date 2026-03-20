## Flask RAG Chatbot (PDF → Pinecone → OpenAI)

This project builds a web-based chatbot for a large PDF (e.g. *The GALE Encyclopedia of Medicine, 2nd ed.*) using:

- **PyPDF** for reading PDF text
- **Sentence-Transformers** (`sentence-transformers/all-MiniLM-L6-v2`) for embeddings
- **Pinecone (Serverless)** for vector search
- **OpenAI** for answer generation
- **Flask** for the web UI

## 1) Setup

Create a virtual environment and install dependencies:

```bash
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

If `sentence-transformers` fails on Windows, install CPU PyTorch first:

```bash
pip install -U torch --index-url https://download.pytorch.org/whl/cpu
pip install -U sentence-transformers
```

## 2) Configure environment

Copy `.env.example` to `.env` and fill values:

- `OPENAI_API_KEY`
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME`
- `PINECONE_CLOUD` and `PINECONE_REGION`
- `PDF_PATH`

## 3) Create Pinecone index (Serverless)

In the Pinecone console create an index with:

- **dimension**: 384
- **metric**: cosine
- **deployment**: serverless

## 4) Put your PDF

Place your PDF at the path in `PDF_PATH` (default: `data/gale.pdf`).

## 5) Ingest (build the vector index)

Run:

```bash
python scripts/ingest.py
```

## 6) Run the Flask web app

```bash
python app.py
```

Open `http://127.0.0.1:5000`.

## Notes

- The chatbot answers using retrieved chunks and includes citations like `(p. 123)`.
- If your PDF is scanned images (not selectable text), you will need OCR before ingestion.
