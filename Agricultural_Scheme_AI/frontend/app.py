
import streamlit as st
import requests

st.set_page_config(
    page_title="Tamil Nadu Agricultural Scheme AI",
    page_icon="🌾",
    layout="centered"
)

API_URL = "http://127.0.0.1:8000/ask"

st.title("🌾 Tamil Nadu Agricultural Scheme AI")
st.write(
    "Ask questions about agricultural schemes "
    "using the uploaded government documents."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous conversation
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept a new question
question = st.chat_input(
    "Ask about agricultural schemes..."
)

if question:

    # Display and save the current question
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    # Send only previous messages as conversation history
    chat_history = st.session_state.messages[:-1]

    with st.chat_message("assistant"):

        with st.spinner("Searching agricultural documents..."):

            try:
                response = requests.post(
                    API_URL,
                    json={
                        "question": question,
                        "chat_history": chat_history
                    },
                    timeout=120
                )

                response.raise_for_status()

                answer = response.json()["answer"]

                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except requests.exceptions.ConnectionError:
                st.error(
                    "Cannot connect to FastAPI. "
                    "Please check whether the API is running."
                )

            except requests.exceptions.RequestException as error:
                st.error(f"API request failed: {error}")

            except (KeyError, ValueError):
                st.error("The API returned an invalid response.")
