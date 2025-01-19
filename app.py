import streamlit as st
import os
import json
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(layout="wide")

# Set project details
project_id = os.getenv("project.id")
project_region = os.getenv("region")

# Write Google credentials from Streamlit secrets to a temporary file
with open("google_credentials.json", "w") as f:
    f.write(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"])

# Set Google credentials environment variable
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_credentials.json"

# Initialize Vertex AI
vertexai.init(project="sparkdatathon-2025-student-5", location="us-central1")

# Load the generative model
model = GenerativeModel("gemini-1.0-pro")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""

# Define the base prompt for better contextual responses
BASE_PROMPT = """
You are a chatbot integrated into a web dashboard named Sigma Boys. 
The dashboard is designed to monitor and mitigate FDIA in IIoT systems. 
Assist users by providing technical information, guidance on using the dashboard, and answering IIoT-related questions. 
If unsure, provide a polite fallback response.
"""

# Handle user input and AI response
def handle_send():
    user_text = st.session_state["input_text"]  # Get text from the input widget
    if user_text.strip():
        # Add user message to chat history
        st.session_state["chat_history"].append({"role": "user", "content": user_text})
        
        # Generate AI response with keyword detection and fallback logic
        if "dashboard" in user_text.lower():
            ai_response = (
                "You can navigate the dashboard using the menu on the left. "
                "Features include FDIA detection, mitigation, and IIoT system monitoring."
            )
        elif "FDIA" in user_text.lower() or "IIoT" in user_text.lower():
            ai_response = (
                "FDIA stands for False Data Injection Attacks, which are cyberattacks targeting data integrity in IoT systems. "
                "Our system mitigates these attacks by using advanced algorithms and anomaly detection."
            )
        else:
            # Generate response using the Gemini model
            prompt = BASE_PROMPT + "\nUser: " + user_text
            try:
                response = model.generate_content(prompt, stream=True)
                ai_response = "".join(res.text for res in response)
            except Exception as e:
                ai_response = "I'm sorry, I couldn't process your request. Please try again later."
        
        # Add AI response to chat history
        st.session_state["chat_history"].append({"role": "ai", "content": ai_response})
        
        # Clear the input text
        st.session_state["input_text"] = ""
    else:
        st.warning("Input cannot be empty. Please type something!")

def handle_clear():
    st.session_state["chat_history"] = []
    st.session_state["input_text"] = ""

# CSS styling for the app
st.markdown(
    """
    <style>
    html, body, .stApp { margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; }
    .chat-message { margin: 10px 0; padding: 10px; border-radius: 5px; max-width: 80%; font-family: Arial, sans-serif; }
    .user-message { text-align: right; margin-left: auto; }
    .ai-message { text-align: left; margin-right: auto; }
    </style>
    """,
    unsafe_allow_html=True
)

# Main UI components
st.markdown('<h1 class="centered-title">Sigma Boys - Spark</h1>', unsafe_allow_html=True)
st.markdown('<h3 class="centered-subtitle">Detection and Mitigation System for FDIA in IIoT</h3>', unsafe_allow_html=True)

# Dashboard section
st.markdown("### Dashboard")
st.components.v1.html(
    """
    <iframe src="https://bliv.ai/embed/dashboard" 
            style="width:100%; height:500px; border:none;"></iframe>
    """,
    height=500,
)

# Chat section
st.markdown('<h2 id="chatbot">Chatbot - Sigma Boys</h2>', unsafe_allow_html=True)

chat_container = st.container()

with chat_container:
    for chat in st.session_state["chat_history"]:
        if chat["role"] == "user":
            st.markdown(
                f'<div class="chat-message user-message">{chat["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chat-message ai-message">{chat["content"]}</div>',
                unsafe_allow_html=True,
            )

# Input and action buttons
input_container = st.container()
with input_container:
    with st.form("chat_form", clear_on_submit=True):
        st.text_input(
            label="",
            placeholder="Type your message",
            key="input_text"
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            st.form_submit_button("Send", on_click=handle_send)
        with col2:
            st.form_submit_button("Clear", on_click=handle_clear)
