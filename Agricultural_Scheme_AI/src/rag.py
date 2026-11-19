import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, AIMessage
from src.prompts import prompt

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=False)
VECTORSTORE_DIR = BASE_DIR / "vectorstore"


def get_embeddings():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to the project .env file.")
    return OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        api_key=api_key,
    )


def load_vector_store():
    index_path = VECTORSTORE_DIR / "index.faiss"
    if not index_path.exists():
        raise FileNotFoundError("The FAISS index is missing. Upload a scheme PDF to create it.")
    return FAISS.load_local(
        str(VECTORSTORE_DIR), get_embeddings(),
        allow_dangerous_deserialization=True,
    )


def retrieve_documents(question, k=5):
    store = load_vector_store()
    return store.similarity_search(question, k=k)


def answer_question_stream(question, chat_history=None, language="English"):
    chat_history = chat_history or []
    previous_context = "\n".join(message.content for message in chat_history[-4:])
    retrieval_query = f"{previous_context}\n{question}".strip()
    documents = retrieve_documents(retrieval_query)

    context_parts = []
    for document in documents:
        source = Path(str(document.metadata.get("source", "Unknown source"))).name
        page = document.metadata.get("page_label", document.metadata.get("page", "Unknown"))
        context_parts.append(
            f"Source: {source}\nPage: {page}\nContent: {document.page_content}"
        )
    context = "\n\n---\n\n".join(context_parts)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is missing. Create a .env file in the project root "
            "and set OPENAI_API_KEY=your_actual_key. Then restart FastAPI."
        )

    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
        api_key=api_key,
    )
    messages = prompt.format_messages(
        context=context,
        question=question,
        chat_history=chat_history,
        language="Tamil" if language.lower() in {"tamil", "தமிழ்"} else "English",
    )
    response = llm.invoke(messages)
    answer = response.content
    if not isinstance(answer, str):
        # Some model/provider versions return structured content blocks.
        answer = "\n".join(
            str(part.get("text", part)) if isinstance(part, dict) else str(part)
            for part in answer
        )
    chat_history.extend([HumanMessage(content=question), AIMessage(content=answer)])
    return answer


def answer_question(question, language="English"):
    return answer_question_stream(question, [], language)
