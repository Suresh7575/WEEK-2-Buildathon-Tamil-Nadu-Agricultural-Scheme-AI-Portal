"""PDF ingestion utilities for the Tamil Nadu Agricultural Scheme AI portal.

New PDFs are appended to the existing FAISS index. Existing vectors are not
rebuilt or deleted. A SHA-256 manifest prevents the same PDF being indexed twice.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

BASE_DIR = Path(__file__).resolve().parent.parent
PDF_FOLDER = BASE_DIR / "data" / "pdfs"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"
MANIFEST_PATH = VECTORSTORE_DIR / "ingested_pdfs.json"
load_dotenv(BASE_DIR / ".env", override=False)


def get_embeddings() -> OpenAIEmbeddings:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to the project .env file.")
    return OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        api_key=api_key,
    )


def _read_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {}
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_manifest(data: dict) -> None:
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
    temporary = MANIFEST_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(MANIFEST_PATH)


def _safe_filename(filename: str) -> str:
    name = Path(filename or "uploaded_scheme.pdf").name
    name = re.sub(r"[^A-Za-z0-9._() -]", "_", name).strip(" .")
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name or "uploaded_scheme.pdf"


def extract_pdf_documents(pdf_bytes: bytes, filename: str) -> list[Document]:
    if not pdf_bytes.startswith(b"%PDF"):
        raise ValueError("The uploaded file is not a valid PDF document.")
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception as exc:
        raise ValueError(f"Could not open PDF: {exc}") from exc

    documents: list[Document] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            documents.append(Document(
                page_content=text,
                metadata={"source": filename, "page": page_number, "page_label": str(page_number)},
            ))
    if not documents:
        raise ValueError("No selectable text was found. This may be a scanned PDF; OCR is not enabled yet.")
    return documents


def add_pdf_to_index(pdf_bytes: bytes, filename: str) -> dict:
    """Save and index one PDF, appending chunks to the existing FAISS index."""
    filename = _safe_filename(filename)
    digest = hashlib.sha256(pdf_bytes).hexdigest()
    manifest = _read_manifest()
    if digest in manifest:
        return {"filename": filename, "status": "already_indexed", "pages": manifest[digest].get("pages", 0), "chunks": manifest[digest].get("chunks", 0)}

    # The starter project already contains PDFs and a prebuilt FAISS index,
    # but may not have an ingestion manifest. Match uploaded bytes against
    # the existing PDF folder to avoid adding those same source files twice.
    PDF_FOLDER.mkdir(parents=True, exist_ok=True)
    for existing_pdf in PDF_FOLDER.glob("*.pdf"):
        try:
            if hashlib.sha256(existing_pdf.read_bytes()).hexdigest() == digest:
                return {"filename": existing_pdf.name, "status": "already_indexed", "pages": 0, "chunks": 0}
        except OSError:
            continue

    documents = extract_pdf_documents(pdf_bytes, filename)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(documents)
    if not chunks:
        raise ValueError("No searchable text chunks could be created from this PDF.")

    embeddings = get_embeddings()
    index_file = VECTORSTORE_DIR / "index.faiss"
    if index_file.exists():
        store = FAISS.load_local(
            str(VECTORSTORE_DIR), embeddings,
            allow_dangerous_deserialization=True,
        )
        store.add_documents(chunks)
    else:
        VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
        store = FAISS.from_documents(chunks, embeddings)

    # Persist the expanded index before marking this file as ingested.
    store.save_local(str(VECTORSTORE_DIR))
    PDF_FOLDER.mkdir(parents=True, exist_ok=True)
    destination = PDF_FOLDER / filename
    if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
        destination = PDF_FOLDER / f"{Path(filename).stem}_{digest[:8]}.pdf"
    destination.write_bytes(pdf_bytes)

    manifest[digest] = {"filename": destination.name, "pages": len(documents), "chunks": len(chunks)}
    _write_manifest(manifest)
    return {"filename": destination.name, "status": "indexed", "pages": len(documents), "chunks": len(chunks)}


def load_pdf_documents() -> list[Document]:
    """Load all PDFs in data/pdfs for a full initial index build."""
    documents: list[Document] = []
    PDF_FOLDER.mkdir(parents=True, exist_ok=True)
    for pdf_path in sorted(PDF_FOLDER.glob("*.pdf")):
        documents.extend(extract_pdf_documents(pdf_path.read_bytes(), pdf_path.name))
    if not documents:
        raise FileNotFoundError(f"No readable PDF files found in {PDF_FOLDER}")
    return documents


def split_documents(documents: Iterable[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    return splitter.split_documents(list(documents))


def create_vector_store(chunks: list[Document], embeddings=None) -> FAISS:
    if not chunks:
        raise ValueError("No text chunks available to index.")
    embeddings = embeddings or get_embeddings()
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
    store = FAISS.from_documents(chunks, embeddings)
    store.save_local(str(VECTORSTORE_DIR))
    return store


if __name__ == "__main__":
    pages = load_pdf_documents()
    chunks = split_documents(pages)
    create_vector_store(chunks)
    print(f"Indexed {len(pages)} pages into {len(chunks)} searchable chunks.")
