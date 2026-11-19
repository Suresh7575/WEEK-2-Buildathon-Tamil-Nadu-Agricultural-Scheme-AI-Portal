# Tamil Nadu Agricultural Scheme AI Portal

A farmer-friendly, English–Tamil question-answer portal for Tamil Nadu agricultural scheme documents. It uses FastAPI, Streamlit, OpenAI embeddings/chat, PDF text extraction, and a persistent FAISS vector index.

## Improvements included

### 1. English–Tamil bilingual experience
- Select English or தமிழ் in the sidebar.
- Farmer-facing labels, upload instructions, helper text, quick questions, and important notices are translated.
- Answers follow the selected language: simple English or clear, natural Tamil.
- The assistant is instructed to use only retrieved document content, avoid inventing scheme rules or subsidy amounts, cite source document/page in its answer, and explain when the uploaded documents do not contain the answer.

### 2. Upload PDFs and automatically make them searchable
- Upload one or multiple PDF files in the sidebar.
- The FastAPI `/upload` endpoint validates the file, extracts text page by page, creates searchable chunks, generates embeddings, and adds the chunks to the existing FAISS index.
- The existing FAISS index is loaded and extended; it is not rebuilt for every new upload.
- A SHA-256 manifest prevents identical PDFs from being indexed twice.
- Uploaded PDFs are saved under `data/pdfs/`.
- Text-based PDFs are supported. Scanned PDFs require OCR; OCR is not included in this version.

## Project structure

```text
Agricultural_Scheme_AI/
├── backend/
│   └── main.py              # FastAPI /ask, /upload and /health endpoints
├── data/
│   └── pdfs/                # Uploaded scheme PDFs
├── frontend/
│   ├── app.py               # Default Streamlit entry point
│   └── Customapp.py         # Bilingual farmer-facing UI
├── src/
│   ├── ingest.py            # PDF extraction, chunking and incremental FAISS updates
│   ├── prompts.py           # Bilingual, farmer-friendly RAG instructions
│   └── rag.py               # Retrieval and answer generation
├── vectorstore/             # Persistent FAISS index and upload manifest
├── .env.example
├── requirements.txt
├── run_backend.bat
└── run_frontend.bat
```

## Windows setup

1. Install Python 3.10 or newer.
2. Open Command Prompt in this project folder.
3. Create and activate a virtual environment:

   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   ```

4. Install dependencies:

   ```cmd
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. Copy `.env.example` to `.env` and set your OpenAI API key. Never share or commit `.env`.
6. Start the backend in the first Command Prompt:

   ```cmd
   run_backend.bat
   ```

7. Start the frontend in a second Command Prompt:

   ```cmd
   run_frontend.bat
   ```

8. Open the Streamlit URL shown in the terminal (normally `http://localhost:8501`).

## Troubleshooting an HTTP 500 from `/ask`

If Streamlit displays an HTTP 500 error, FastAPI is reachable but the `/ask` operation failed. Open `http://127.0.0.1:8000/health` in a browser and check these fields:

- `index_available` should be `true`.
- `openai_api_key_configured` should be `true` (the key itself is never returned).
- `embedding_model` must match the model used to create the supplied FAISS index.

Keep the FastAPI Command Prompt open. The full traceback is logged there. The Streamlit interface also displays the API error response so you can identify whether the issue is a missing API key, invalid key, unavailable model, embedding/index mismatch, or another backend exception. After changing `.env`, stop and restart `run_backend.bat`.

## Upload workflow

1. Choose English or தமிழ்.
2. In the left sidebar, select one or more PDF files.
3. Select **Upload and index PDFs** (or the Tamil equivalent).
4. Wait for each file's result. Newly indexed documents are immediately available to the question-answer feature.
5. Ask a question in English or Tamil. The response follows the selected language.

## API endpoints

- `GET /` — API status.
- `GET /health` — backend health and whether the FAISS index exists.
- `POST /ask` — JSON fields: `question`, `chat_history`, `language` (`English` or `தமிழ்`).
- `POST /upload` — multipart form field `files`, one or more PDF files; adds new content to FAISS.

## Existing index and compatibility

The supplied `vectorstore/index.faiss` and `vectorstore/index.pkl` are retained in the project package. The application loads them using the embedding model named by `OPENAI_EMBEDDING_MODEL`; use the same embedding model that was used to create the existing index. Changing embedding models requires rebuilding the index from the source PDFs.

## Important limitations

- The current PDF parser extracts selectable text. Image-only/scanned PDFs need OCR before their contents can be searched.
- OpenAI API access is required for embeddings and chat responses in this version.
- The uploaded PDFs and FAISS index are stored locally on the machine running the app.
- Always verify eligibility, benefit amounts, application windows and procedures with the relevant official government department. The AI is an information aid, not an official government service.
