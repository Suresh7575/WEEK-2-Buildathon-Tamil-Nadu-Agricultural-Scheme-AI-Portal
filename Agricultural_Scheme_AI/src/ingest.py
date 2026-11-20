
import os
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from pypdf import PdfReader

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


# ==================================================
# 1. PATH CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=False)

PDF_FOLDER = BASE_DIR / "data" / "pdfs"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"
MANIFEST_PATH = VECTORSTORE_DIR / "ingested_pdfs.json"

PDF_FOLDER.mkdir(parents=True, exist_ok=True)
VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# 2. OPENAI EMBEDDINGS
# ==================================================

def get_embeddings():

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is missing. Check your .env file."
        )

    return OpenAIEmbeddings(
        model=os.getenv(
            "OPENAI_EMBEDDING_MODEL",
            "text-embedding-3-small"
        ),
        api_key=api_key
    )


# ==================================================
# 3. FILE HELPERS
# ==================================================

def normalize_filename(filename):

    filename = Path(str(filename)).name

    filename = re.sub(
        r"[^\w.\- ]",
        "_",
        filename
    )

    return filename.strip()


def calculate_file_hash(file_bytes):

    return hashlib.sha256(file_bytes).hexdigest()


def get_pdf_content(uploaded_file):

    """
    Supports:
    - FastAPI raw bytes
    - bytearray
    - Streamlit UploadedFile
    - File-like objects
    """

    if isinstance(uploaded_file, bytes):
        return uploaded_file

    if isinstance(uploaded_file, bytearray):
        return bytes(uploaded_file)

    if hasattr(uploaded_file, "getvalue"):
        return uploaded_file.getvalue()

    if hasattr(uploaded_file, "file"):
        file_object = uploaded_file.file
        if hasattr(file_object, "seek"):
            file_object.seek(0)
        return file_object.read()

    if hasattr(uploaded_file, "read"):
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        return uploaded_file.read()

    raise TypeError(
        "Unsupported upload format. Expected PDF bytes or an uploaded file."
    )


def get_upload_filename(uploaded_file, filename=None):

    if filename:
        return filename

    if hasattr(uploaded_file, "name"):
        return uploaded_file.name

    if hasattr(uploaded_file, "filename"):
        return uploaded_file.filename

    return "uploaded_document.pdf"


def get_relative_vectorstore_path():

    """
    Use a relative path for FAISS because absolute paths
    are failing in this Windows project environment.

    Run FastAPI from the project root directory.
    """

    return os.path.relpath(
        VECTORSTORE_DIR,
        Path.cwd()
    )


# ==================================================
# 4. MANIFEST MANAGEMENT
# ==================================================

def load_manifest():

    if not MANIFEST_PATH.exists():
        return {}

    try:
        with open(
            MANIFEST_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return {}


def save_manifest(manifest):

    with open(
        MANIFEST_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            manifest,
            file,
            indent=4,
            ensure_ascii=False
        )


# ==================================================
# 5. PDF INGESTION
# ==================================================

def add_pdf_to_index(uploaded_file, filename=None, *args, **kwargs):

    """
    Complete PDF ingestion process:

    1. Read uploaded PDF
    2. Validate filename and content
    3. Check duplicate PDF
    4. Save PDF
    5. Extract PDF text
    6. Split text into chunks
    7. Generate embeddings
    8. Add documents to FAISS
    9. Save FAISS index
    10. Update manifest
    """

    try:

        # ------------------------------------------
        # A. GET PDF CONTENT
        # ------------------------------------------

        file_bytes = get_pdf_content(uploaded_file)

        original_filename = get_upload_filename(
            uploaded_file,
            filename
        )

        original_filename = normalize_filename(
            original_filename
        )

        if not original_filename.lower().endswith(".pdf"):

            return {
                "success": False,
                "message": "Only PDF files are supported."
            }

        if not file_bytes:

            return {
                "success": False,
                "message": "The uploaded PDF is empty."
            }

        # ------------------------------------------
        # B. CHECK PDF HASH
        # ------------------------------------------

        file_hash = calculate_file_hash(file_bytes)

        manifest = load_manifest()

        if file_hash in manifest:

            return {
                "success": True,
                "message": (
                    f"{original_filename} is already indexed."
                ),
                "filename": original_filename,
                "duplicate": True
            }

        # ------------------------------------------
        # C. SAVE PDF
        # ------------------------------------------

        pdf_path = PDF_FOLDER / original_filename

        with open(pdf_path, "wb") as file:
            file.write(file_bytes)

        # ------------------------------------------
        # D. EXTRACT PDF TEXT
        # ------------------------------------------

        reader = PdfReader(str(pdf_path))

        documents = []

        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):

            page_text = page.extract_text() or ""

            if page_text.strip():

                documents.append(
                    Document(
                        page_content=page_text,
                        metadata={
                            "source": original_filename,
                            "page": page_number
                        }
                    )
                )

        if not documents:

            return {
                "success": False,
                "message": (
                    "No readable text found in this PDF. "
                    "Scanned PDFs may require OCR."
                )
            }

        # ------------------------------------------
        # E. SPLIT TEXT INTO CHUNKS
        # ------------------------------------------

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=[
                "\n\n",
                "\n",
                ".",
                " ",
                ""
            ]
        )

        chunks = splitter.split_documents(
            documents
        )

        if not chunks:

            return {
                "success": False,
                "message": "No text chunks were generated."
            }

        # ------------------------------------------
        # F. GENERATE EMBEDDINGS
        # ------------------------------------------

        embeddings = get_embeddings()

        # ------------------------------------------
        # G. LOAD OR CREATE FAISS INDEX
        # ------------------------------------------

        relative_path = get_relative_vectorstore_path()

        index_file = VECTORSTORE_DIR / "index.faiss"
        metadata_file = VECTORSTORE_DIR / "index.pkl"

        if index_file.exists() and metadata_file.exists():

            store = FAISS.load_local(
                relative_path,
                embeddings,
                allow_dangerous_deserialization=True
            )

            store.add_documents(chunks)

        else:

            store = FAISS.from_documents(
                chunks,
                embeddings
            )

        # ------------------------------------------
        # H. SAVE FAISS INDEX
        # ------------------------------------------

        store.save_local(
            relative_path
        )

        # ------------------------------------------
        # I. UPDATE MANIFEST
        # ------------------------------------------

        manifest[file_hash] = {
            "filename": original_filename,
            "file_hash": file_hash,
            "pages": len(reader.pages),
            "chunks": len(chunks),
            "uploaded_at": datetime.now().isoformat()
        }

        save_manifest(manifest)

        # ------------------------------------------
        # J. SUCCESS RESPONSE
        # ------------------------------------------

        return {
            "success": True,
            "message": (
                f"{original_filename} indexed successfully."
            ),
            "filename": original_filename,
            "pages": len(reader.pages),
            "chunks": len(chunks),
            "duplicate": False
        }

    except Exception as error:

        return {
            "success": False,
            "message": (
                f"PDF ingestion failed: {str(error)}"
            )
        }


# ==================================================
# 6. MULTIPLE PDF UPLOAD
# ==================================================

def add_multiple_pdfs(uploaded_files):

    results = []

    for uploaded_file in uploaded_files:

        result = add_pdf_to_index(
            uploaded_file
        )

        results.append(result)

    return results
