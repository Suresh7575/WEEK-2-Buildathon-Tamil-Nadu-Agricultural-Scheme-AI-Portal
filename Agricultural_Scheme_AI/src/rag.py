
import os
import re
import pickle
from pathlib import Path

import faiss

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, AIMessage

from src.prompts import prompt


# ==================================================
# 1. CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=True)

VECTORSTORE_DIR = BASE_DIR / "vectorstore"


# ==================================================
# 2. OPENAI CONFIGURATION
# ==================================================

def get_api_key():

    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is missing. Check the project .env file."
        )

    return api_key


def get_embeddings():

    return OpenAIEmbeddings(
        model=os.getenv(
            "OPENAI_EMBEDDING_MODEL",
            "text-embedding-3-small"
        ),
        api_key=get_api_key(),
    )


def get_llm(temperature=None):

    if temperature is None:
        temperature = float(
            os.getenv("OPENAI_TEMPERATURE", "0.2")
        )

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=temperature,
        api_key=get_api_key(),
    )


# ==================================================
# 3. LOAD FAISS VECTOR DATABASE
# ==================================================

def load_vector_store():

    index_path = VECTORSTORE_DIR / "index.faiss"
    metadata_path = VECTORSTORE_DIR / "index.pkl"

    if not index_path.exists() or not metadata_path.exists():
        raise FileNotFoundError(
            f"FAISS files are missing from {VECTORSTORE_DIR}"
        )

    relative_index_path = os.path.relpath(
        index_path,
        Path.cwd()
    )

    index = faiss.read_index(relative_index_path)

    with open(metadata_path, "rb") as file:
        docstore, index_to_docstore_id = pickle.load(file)

    store = FAISS(
        embedding_function=get_embeddings(),
        index=index,
        docstore=docstore,
        index_to_docstore_id=index_to_docstore_id,
    )

    return store


# ==================================================
# 4. LANGUAGE DETECTION
# ==================================================

def is_tamil(text):

    return bool(
        re.search(r"[\u0B80-\u0BFF]", text)
    )


# ==================================================
# 5. TAMIL QUESTION TRANSLATION
# ==================================================

def translate_tamil_query(question):

    if not is_tamil(question):
        return question

    llm = get_llm(temperature=0)

    translation_prompt = f"""
Translate the following Tamil agricultural scheme question
into a clear English search query.

Rules:
- Preserve the exact meaning.
- Keep technical terms such as Tractor, Power Tiller,
  SC, ST, subsidy and scheme.
- Do not answer the question.
- Do not add information.
- Return only the English search query.

Tamil question:
{question}
"""

    response = llm.invoke(translation_prompt)

    translated_query = response.content

    if not isinstance(translated_query, str):
        translated_query = str(translated_query)

    return translated_query.strip()


# ==================================================
# 6. DOCUMENT RETRIEVAL
# ==================================================

def retrieve_documents(question, k=5):

    store = load_vector_store()

    # Use English translation as the primary search
    if is_tamil(question):

        translated_query = translate_tamil_query(question)

        if translated_query and translated_query.strip():
            primary_query = translated_query.strip()
        else:
            primary_query = question

    else:
        primary_query = question

    results = store.similarity_search(
        primary_query,
        k=k
    )

    retrieved_documents = []
    seen_documents = set()

    for document in results:

        source = document.metadata.get("source", "Unknown")

        page = document.metadata.get(
            "page_label",
            document.metadata.get("page", "Unknown")
        )

        content = document.page_content.strip()

        unique_key = (source, page, content)

        if unique_key not in seen_documents:
            seen_documents.add(unique_key)
            retrieved_documents.append(document)

    # Tamil search is used as fallback
    if is_tamil(question) and len(retrieved_documents) < k:

        tamil_results = store.similarity_search(
            question,
            k=k
        )

        for document in tamil_results:

            source = document.metadata.get("source", "Unknown")

            page = document.metadata.get(
                "page_label",
                document.metadata.get("page", "Unknown")
            )

            content = document.page_content.strip()

            unique_key = (source, page, content)

            if unique_key not in seen_documents:
                seen_documents.add(unique_key)
                retrieved_documents.append(document)

    return retrieved_documents[:k]


# ==================================================
# 7. FORMAT RETRIEVED CONTEXT
# ==================================================

def format_context(documents):

    context_parts = []

    for document in documents:

        source = Path(
            str(
                document.metadata.get(
                    "source",
                    "Unknown source"
                )
            )
        ).name

        page = document.metadata.get(
            "page_label",
            document.metadata.get("page", "Unknown")
        )

        context_parts.append(
            f"""
Source: {source}
Page: {page}

Content:
{document.page_content}
"""
        )

    return "\n\n----------------------\n\n".join(
        context_parts
    )


# ==================================================
# 8. GENERATE ANSWER
# ==================================================

def answer_question_stream(
    question,
    chat_history=None,
    language="English"
):

    chat_history = chat_history or []

    documents = retrieve_documents(
        question,
        k=5
    )

    context = format_context(documents)

    if not context.strip():

        if language.lower() in {"tamil", "தமிழ்"}:
            return (
                "மன்னிக்கவும், பதிவேற்றிய ஆவணங்களில் "
                "இந்தக் கேள்விக்குத் தொடர்புடைய தகவலை "
                "கண்டறிய முடியவில்லை."
            )

        return (
            "Sorry, I could not find relevant information "
            "for this question in the uploaded documents."
        )

    llm = get_llm()

    messages = prompt.format_messages(
        context=context,
        question=question,
        chat_history=chat_history,
        language=(
            "Tamil"
            if language.lower() in {"tamil", "தமிழ்"}
            else "English"
        ),
    )

    response = llm.invoke(messages)

    answer = response.content

    if not isinstance(answer, str):
        answer = "\n".join(
            str(part.get("text", part))
            if isinstance(part, dict)
            else str(part)
            for part in answer
        )

    chat_history.extend([
        HumanMessage(content=question),
        AIMessage(content=answer)
    ])

    return answer


# ==================================================
# 9. SIMPLE QUESTION FUNCTION
# ==================================================

def answer_question(question, language="English"):

    return answer_question_stream(
        question,
        chat_history=[],
        language=language
    )
