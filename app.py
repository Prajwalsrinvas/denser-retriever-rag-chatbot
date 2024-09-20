import json

import requests
import streamlit as st
import streamlit_mermaid as stmd
from groq import Groq

# Set page config
st.set_page_config(page_icon="🤖", layout="wide", page_title="RAG chatbot 🤖")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "models" not in st.session_state:
    st.session_state.models = None
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = st.secrets.get("GROQ_API_KEY", "")


# Function to load models from JSON file
def load_models():
    try:
        with open("groq_models.json", "r") as f:
            data = json.load(f)
            st.session_state.models = [i["id"] for i in data["data"]]
    except FileNotFoundError:
        st.error("Models file not found. Please run fetch_groq_models.py first.")
    except json.JSONDecodeError:
        st.error("Error reading models file. Please check the file format.")


# Sidebar for model selection and API key input
st.sidebar.header("Select an LLM")
load_models()
selected_model = st.sidebar.selectbox(
    "Choose a model from the list of groq models:",
    st.session_state.models or ["No models available"],
)

# GROQ API Key input
if not st.session_state.groq_api_key:
    with st.sidebar.popover("Enter GROQ API Key"):
        api_key = st.text_input("GROQ API Key", type="password")
        if st.button("Save API Key"):
            st.session_state.groq_api_key = api_key
            st.success("API Key saved for this session")

# Initialize Groq client
client = Groq(api_key=st.session_state.groq_api_key)

# Initialize Denser Retriever client
DENSER_RETRIEVER_API_KEY = st.secrets["DENSER_RETRIEVER_API_KEY"]
RETRIEVER_ID = st.secrets["RETRIEVER_ID"]


# Function to call Denser Retriever API
def get_relevant_chunks(query):
    headers = {
        "Authorization": f"Bearer {DENSER_RETRIEVER_API_KEY}",
        "content-type": "application/json",
    }
    json_data = {
        "query": query,
        "id": RETRIEVER_ID,
        "k": 3,
    }
    response = requests.post(
        "https://retriever.denser.ai/api/retrievers/retrieve",
        headers=headers,
        json=json_data,
    )
    return response.json()["passages"]


# Main chat interface
st.header("RAG chatbot 🤖")

st.caption(
    "Ask me anything about the python [instructor](https://python.useinstructor.com/) LLM library"
)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get relevant chunks from Denser Retriever
    chunks = get_relevant_chunks(prompt)
    context = "\n".join([chunk["page_content"] for chunk in chunks])

    # Prepare messages for Groq API
    messages = [
        {
            "role": "system",
            "content": f"""
You are an AI chatbot specialized in the Python library "Instructor." Your role is to answer questions exclusively based on the provided documentation and context about this library.

Answer the user's question from the context given below:
{context}
""",
        },
        *st.session_state.messages,
    ]

    # Get response from Groq API
    try:
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            for response in client.chat.completions.create(
                model=selected_model,
                messages=messages,
                stream=True,
            ):
                if response.choices[0].delta.content:
                    full_response += response.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)

        # Add assistant's response to chat history
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response, "chunks": chunks}
        )

        with st.expander("*Show Retrieved Context*", icon="📚"):
            for index, chunk in enumerate(chunks, start=1):
                c1, c2 = st.columns(2, vertical_alignment="bottom")
                c1.info(f"Chunk {index}")
                c2.metric(label="Relevance Score", value=round(chunk["score"], 3))
                st.code(chunk["page_content"])
                if index < len(chunks):
                    st.divider()
    except Exception as e:
        st.error(f"Error: {str(e)}")

# How to use and How it works buttons
col1, col2 = st.sidebar.columns(2)

with col1:
    with st.popover("How to Use 🤔"):
        st.markdown(
            """
            1. Select an LLM model from the sidebar.
            2. Enter your GROQ API key if prompted.
            3. Type your question about the Instructor library in the chat input.
            4. View the AI's response and the retrieved context.
            5. Optionally, export the chat history or clear it.
            """
        )


with col2:
    with st.popover("How it Works 🔍"):
        st.markdown("### Workflow Diagram")
        mermaid_code = """
        graph TD
            A[User selects LLM model] --> B[User enters query]
            B --> C[Denser Retriever finds relevant chunks]
            C --> D[Query + chunks sent to Groq LLM]
            D --> E[LLM generates response]
            E --> F[Response displayed in chat]
        """
        stmd.st_mermaid(mermaid_code, height="400px")
# Export chat history

col3, col4 = st.sidebar.columns(2)
with col3:
    if col3.button("Export Chat History 📤"):
        chat_export = []
        for message in st.session_state.messages:
            export_message = {
                "role": message["role"],
                "content": message["content"],
            }
            if "chunks" in message:
                export_message["chunks"] = message["chunks"]
            chat_export.append(export_message)

        st.sidebar.download_button(
            label="Download JSON",
            data=json.dumps(chat_export, indent=2),
            file_name="chat_history.json",
            mime="application/json",
        )

with col4:
    # Clear chat history button (moved to the bottom of the sidebar)
    if col4.button("Clear Chat History 🗑️"):
        st.session_state.messages = []
        st.rerun()
