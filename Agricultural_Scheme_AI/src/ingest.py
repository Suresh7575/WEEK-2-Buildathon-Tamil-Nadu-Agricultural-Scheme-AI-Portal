
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS	


# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# PDF directory
PDF_FOLDER = BASE_DIR / "data" / "pdfs"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"

# Load environment variables
load_dotenv(BASE_DIR / ".env", override=True)


def load_pdf_documents():

    documents = []

    pdf_files = list(PDF_FOLDER.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in: {PDF_FOLDER}"
        )

    print(f"Found {len(pdf_files)} PDF files.")

    for pdf_file in pdf_files:

        print(f"\nLoading: {pdf_file.name}")

        loader = PyPDFLoader(str(pdf_file))

        pages = loader.load()

        documents.extend(pages)

        print(f"Pages extracted: {len(pages)}")

    print("\nPDF ingestion completed.")

    print(f"Total pages: {len(documents)}")

    return documents


def split_documents(documents):

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )

    chunks = text_splitter.split_documents(documents)

    print("\nText splitting completed.")

    print(f"Total chunks created: {len(chunks)}")

    return chunks


def test_embeddings(chunks):

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Check your .env file."
        )

    model_name = os.getenv(
        "OPENAI_EMBEDDING_MODEL",
        "text-embedding-3-small"
    )

    print(f"\nEmbedding model: {model_name}")

    embeddings = OpenAIEmbeddings(
        model=model_name
    )

    # Test only two chunks to limit API usage
    sample_texts = [
        chunk.page_content
        for chunk in chunks[:2]
    ]

    if not sample_texts:
        raise ValueError("No text chunks available.")

    vectors = embeddings.embed_documents(sample_texts)

    print("\nEmbedding test successful!")

    print(f"Chunks tested: {len(vectors)}")

    print(f"Vector dimensions: {len(vectors[0])}")

    return embeddings

def create_vector_store(chunks, embeddings):

    print("\nCreating FAISS vector database...")

    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings
    )

    # Create folder if it does not exist
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    # Save FAISS database
    vector_store.save_local("vectorstore")

    print("\nFAISS database created successfully!")

    print(f"Total chunks stored: {len(chunks)}")

    print(f"Database location: {VECTORSTORE_DIR}")

    return vector_store

if __name__ == "__main__":

    # Step 1: Extract PDF text
    documents = load_pdf_documents()

    # Step 2: Split extracted text
    chunks = split_documents(documents)

    # Step 3: Show a sample chunk
    print("\nFirst chunk preview:")

    print(chunks[0].page_content[:300])

    print("\nFirst chunk metadata:")

    print(chunks[0].metadata)

    # Step 4: Test OpenAI embeddings
    # Step 4: Test OpenAI embeddings
    embeddings = test_embeddings(chunks)

    # Step 5: Create and save FAISS database
    vector_store = create_vector_store(chunks, embeddings)

    print("\nCOMPLETED SUCCESSFULLY")
