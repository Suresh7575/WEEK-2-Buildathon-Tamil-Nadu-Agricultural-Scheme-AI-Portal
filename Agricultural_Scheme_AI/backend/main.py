import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field, field_validator
from langchain_core.messages import HumanMessage, AIMessage

# --------------------------------------------------
# 1. LOAD ENVIRONMENT VARIABLES
# --------------------------------------------------

# main.py is inside backend/; the .env file is in the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env before importing modules that initialize OpenAI clients.
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)

logger = logging.getLogger("uvicorn.error")

# --------------------------------------------------
# 2. IMPORT PROJECT MODULES
# --------------------------------------------------

from src.rag import answer_question_stream, VECTORSTORE_DIR
from src.ingest import add_pdf_to_index

# --------------------------------------------------
# 3. FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="Tamil Nadu Agricultural Scheme AI",
    description=(
        "Bilingual, document-grounded AI assistant "
        "for Tamil Nadu farmers."
    ),
    version="2.1.0",
)

# --------------------------------------------------
# 4. CONFIGURATION
# --------------------------------------------------

MAX_UPLOAD_SIZE = 30 * 1024 * 1024  # 30 MB

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# --------------------------------------------------
# 5. REQUEST MODELS
# --------------------------------------------------

class ChatMessage(BaseModel):
    role: str
    content: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, value):
        if value not in {"user", "assistant"}:
            raise ValueError(
                "Role must be either 'user' or 'assistant'."
            )
        return value


class QuestionRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=4000
    )

    chat_history: list[ChatMessage] = Field(
        default_factory=list
    )

    language: str = Field(default="English")

    @field_validator("question")
    @classmethod
    def validate_question(cls, value):
        if not value.strip():
            raise ValueError("Question cannot be empty.")
        return value.strip()

    @field_validator("language")
    @classmethod
    def validate_language(cls, value):
        if value.lower() not in {"english", "tamil"}:
            raise ValueError(
                "Language must be English or Tamil."
            )

        return value.capitalize()


# --------------------------------------------------
# 6. HOME ENDPOINT
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Tamil Nadu Agricultural Scheme API is running",
        "version": "2.1.0",
        "documentation": "/docs",
        "health_check": "/health",
    }


# --------------------------------------------------
# 7. HEALTH CHECK ENDPOINT
# --------------------------------------------------

@app.get("/health")
def health():

    index_file = VECTORSTORE_DIR / "index.faiss"
    metadata_file = VECTORSTORE_DIR / "index.pkl"

    api_key = os.getenv(
        "OPENAI_API_KEY", ""
    ).strip()

    return {
        "status": "ok",
        "index_available": (
            index_file.exists()
            and metadata_file.exists()
        ),
        "openai_api_key_configured": bool(api_key),
        "chat_model": os.getenv(
            "OPENAI_MODEL",
            "gpt-4o-mini"
        ),
        "embedding_model": os.getenv(
            "OPENAI_EMBEDDING_MODEL",
            "text-embedding-3-small"
        ),
    }


# --------------------------------------------------
# 8. CONVERT CHAT HISTORY
# --------------------------------------------------

def convert_chat_history(chat_history):

    history = []

    for message in chat_history:

        if message.role == "user":
            history.append(
                HumanMessage(content=message.content)
            )

        elif message.role == "assistant":
            history.append(
                AIMessage(content=message.content)
            )

    return history


# --------------------------------------------------
# 9. ASK QUESTION ENDPOINT
# --------------------------------------------------

@app.post("/ask")
def ask_question(request: QuestionRequest):

    # Check whether the API key is configured.
    api_key = os.getenv(
        "OPENAI_API_KEY", ""
    ).strip()

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "OpenAI API key is missing.",
                "solution": (
                    "Configure OPENAI_API_KEY in your .env file "
                    "and restart FastAPI."
                ),
            },
        )

    try:

        logger.info(
            "Received question. Language: %s",
            request.language
        )

        history = convert_chat_history(
            request.chat_history
        )

        answer = answer_question_stream(
            request.question,
            chat_history=history,
            language=request.language
        )

        if not answer:
            raise ValueError(
                "The AI model returned an empty response."
            )

        return {
            "status": "success",
            "question": request.question,
            "answer": answer,
            "language": request.language,
        }

    except FileNotFoundError as exc:

        logger.exception("FAISS index or document file not found")

        raise HTTPException(
            status_code=409,
            detail=str(exc)
        ) from exc

    except Exception as exc:

        logger.exception(
            "The /ask endpoint failed"
        )

        error_type = type(exc).__name__

        if error_type == "AuthenticationError":
            message = (
                "OpenAI authentication failed. "
                "Check whether OPENAI_API_KEY is valid."
            )

        elif error_type == "RateLimitError":
            message = (
                "OpenAI API rate limit or quota exceeded. "
                "Check your API usage and billing."
            )

        else:
            message = "The AI request failed."

        raise HTTPException(
            status_code=500,
            detail={
                "message": message,
                "error_type": error_type,
                "reason": str(exc),
            }
        ) from exc


# --------------------------------------------------
# 10. PDF UPLOAD ENDPOINT
# --------------------------------------------------

@app.post("/upload")
async def upload_pdfs(
    files: list[UploadFile] = File(...)
):

    if not files:
        raise HTTPException(
            status_code=400,
            detail="Choose at least one PDF file."
        )

    results = []

    for uploaded in files:

        filename = uploaded.filename or "Unknown"

        try:

            # Validate file extension
            if not filename.lower().endswith(".pdf"):

                results.append({
                    "filename": filename,
                    "status": "error",
                    "message": "Only PDF files are accepted."
                })

                continue

            # Read PDF content
            content = await uploaded.read()

            # Validate file size
            if len(content) > MAX_UPLOAD_SIZE:

                results.append({
                    "filename": filename,
                    "status": "error",
                    "message": "File exceeds the 30 MB upload limit."
                })

                continue

            if not content:

                results.append({
                    "filename": filename,
                    "status": "error",
                    "message": "The uploaded PDF is empty."
                })

                continue

            # Validate PDF signature
            if not content.startswith(b"%PDF-"):

                results.append({
                    "filename": filename,
                    "status": "error",
                    "message": "The uploaded file is not a valid PDF."
                })

                continue

            # Add PDF to existing FAISS index
            result = add_pdf_to_index(
                content,
                filename
            )

            results.append(result)

        except Exception as exc:

            logger.exception(
                "PDF upload failed: %s",
                filename
            )

            results.append({
                "filename": filename,
                "status": "error",
                "message": str(exc)
            })

        finally:

            await uploaded.close()

    successful = [
        item for item in results
        if item.get("status") in {
            "indexed",
            "already_indexed"
        }
    ]

    return {
        "status": "completed",
        "total_files": len(files),
        "indexed_count": len(successful),
        "results": results,
    }


# --------------------------------------------------
# 11. APPLICATION STARTUP
# --------------------------------------------------

@app.on_event("startup")
def startup_event():

    api_key = os.getenv(
        "OPENAI_API_KEY", ""
    ).strip()

    logger.info(
        "Tamil Nadu Agricultural Scheme AI API starting..."
    )

    logger.info(
        "OpenAI API key configured: %s",
        bool(api_key)
    )

    logger.info(
        "FAISS index available: %s",
        (
            (VECTORSTORE_DIR / "index.faiss").exists()
            and (VECTORSTORE_DIR / "index.pkl").exists()
        )
    )

    logger.info(
        "Chat model: %s",
        os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    )

    logger.info(
        "Embedding model: %s",
        os.getenv(
            "OPENAI_EMBEDDING_MODEL",
            "text-embedding-3-small"
        )
    )