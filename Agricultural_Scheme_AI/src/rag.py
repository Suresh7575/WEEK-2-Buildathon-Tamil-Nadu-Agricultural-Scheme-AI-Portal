
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, AIMessage
from src.prompts import prompt


# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env", override=True)

# FAISS database location
VECTORSTORE_DIR = BASE_DIR / "vectorstore"


def load_vector_store():

    print("Loading FAISS vector database...")

    embeddings = OpenAIEmbeddings(
        model=os.getenv(
            "OPENAI_EMBEDDING_MODEL",
            "text-embedding-3-small"
        )
    )

    vector_store = FAISS.load_local(
        "vectorstore",
        embeddings,
        allow_dangerous_deserialization=True
    )

    print("FAISS database loaded successfully!")

    return vector_store


def retrieve_documents(question, k=3):

    vector_store = load_vector_store()

    results = vector_store.similarity_search(
        question,
        k=k
    )

    print(f"\nRelevant documents found: {len(results)}")

    return results


def answer_question(question):

    print("\nSearching agricultural scheme documents...")

    # Step 1: Retrieve relevant documents
    documents = retrieve_documents(question)

    # Step 2: Prepare context with source information
    context_parts = []

    for document in documents:

        source = Path(
            document.metadata.get("source", "Unknown source")
        ).name

        page = document.metadata.get("page_label", "Unknown")

        context_parts.append(
            f"Source: {source}\n"
            f"Page: {page}\n"
            f"Content: {document.page_content}"
        )

    context = "\n\n".join(context_parts)

    # Step 3: Load OpenAI chat model
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=float(
            os.getenv("OPENAI_TEMPERATURE", "0.2")
        )
    )

    # Step 4: Prepare prompt
    messages = prompt.format_messages(
        context=context,
        question=question
    )

    # Step 5: Generate answer
    print("\nGenerating answer using OpenAI LLM...")

    response = llm.invoke(messages)

    print("\n========== AGRICULTURAL SCHEME ANSWER ==========\n")

    print(response.content)

    print("\n================================================")

    return response.content



def answer_question_stream(question, chat_history):

    print("\nSearching agricultural scheme documents...")

    # Include previous conversation when searching for context
    previous_context = "\n".join(
        message.content for message in chat_history[-4:]
    )

    retrieval_query = previous_context + "\n" + question

    documents = retrieve_documents(retrieval_query)

    context_parts = []

    for document in documents:

        source = Path(
            document.metadata.get("source", "Unknown source")
        ).name

        page = document.metadata.get("page_label", "Unknown")

        context_parts.append(
            f"Source: {source}\n"
            f"Page: {page}\n"
            f"Content: {document.page_content}"
        )

    context = "\n\n".join(context_parts)

    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
        streaming=True
    )

    messages = prompt.format_messages(
        context=context,
        question=question,
        chat_history=chat_history
    )

    print("\nGenerating streaming answer...\n")
    print("========== AGRICULTURAL SCHEME ANSWER ==========\n")

    full_answer = ""

    for chunk in llm.stream(messages):

        if chunk.content:
            print(chunk.content, end="", flush=True)
            full_answer += chunk.content

    print("\n\n================================================")

    # Save current conversation for the next question
    chat_history.append(HumanMessage(content=question))
    chat_history.append(AIMessage(content=full_answer))

    return full_answer



if __name__ == "__main__":

    # Create an empty conversation history
    chat_history = []

    # First question
    question1 = "What subsidy is available for agricultural machinery?"

    print("\nUser Question 1:")
    print(question1)

    answer_question_stream(question1, chat_history)

    # Second question - uses previous conversation
    question2 = "What is the maximum amount for that category?"

    print("\nUser Question 2:")
    print(question2)

    answer_question_stream(question2, chat_history)

    print("\nSTEP 18B MEMORY TEST COMPLETED SUCCESSFULLY")
