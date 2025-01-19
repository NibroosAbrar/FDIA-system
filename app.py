import streamlit as st
import os
import json
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(layout="wide")

project_id = os.getenv("project.id")
project_region = os.getenv("region")

# Tulis kredensial dari st.secrets ke file sementara
with open("google_credentials.json", "w") as f:
    f.write(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"])

# Set environment variable ke file sementara
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_credentials.json"

# Tes apakah environment variable berhasil di-set
print("GOOGLE_APPLICATION_CREDENTIALS:", os.environ["GOOGLE_APPLICATION_CREDENTIALS"])

# Authentication
vertexai.init(project="sparkdatathon-2025-student-5", location="us-central1")

# Initialize the model
model = GenerativeModel("gemini-1.0-pro")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""
    
# Define a detailed base prompt
BASE_PROMPT = """
Anda adalah asisten AI yang sangat cerdas yang terintegrasi ke dalam platform bernama Sigma Boys.
Platform ini mencakup dasbor untuk memantau dan mengurangi serangan False Data Injection Attacks (FDIA) dalam sistem Industrial Internet of Things (IIoT).
Tugas utama Anda adalah:

1. Membantu pengguna dengan pertanyaan teknis tentang FDIA, IIoT, platform Vertex AI, Google Cloud, dan Platform Bliv, yang merupakan produk dari PT. BangunIndo.
2. Menjelaskan fitur dan fungsi platform jika diminta.
3. Menjelaskan grafik, chart, visualisasi data, rangkuman data, pelaporan dashboard, saran mitigasi, tindakan yang diperlukan untuk mitigasi FDIA, dan sebagainya yang berkaitan dengan FDIA dan Industrial Internet of Things (IIoT) jika diminta
4. Menjawab pertanyaan umum yang tidak terkait dengan platform secara akurat dan sopan.
5. Menggunakan bahasa yang fleksibel, bisa santai, bisa formal, bisa informal, dan bisa gaul juga tergantung pengguna
6. Jangan dikit-dikit menjelaskan Sigma Boys kecuali jika memang diminta ataupun (berkaitan dan relevan)
Selalu sesuaikan nada dan kedalaman penjelasan berdasarkan pertanyaan pengguna. 
Jika Anda tidak tahu jawabannya, sarankan langkah selanjutnya atau sumber daya eksternal yang mungkin berguna.
"""

# Function to generate a response
def generate_response(user_input):
    # Combine the base prompt with the user's input
    prompt = BASE_PROMPT + "\nUser: " + user_input
    try:
        # Generate content using the Gemini model
        response = model.generate_content(prompt, stream=True)
        return "".join(res.text for res in response)
    except Exception as e:
        # Fallback response in case of an error
        return "I'm sorry, I couldn't process your request. Please try again later."

# Handle send button click
def handle_send():
    user_text = st.session_state["input_text"]  # Get text from input widget
    if user_text.strip():
        # Add user message to chat history
        st.session_state["chat_history"].append({"role": "user", "content": user_text})
        
        # Generate AI response
        ai_response = generate_response(user_text)
        
        # Add AI response to chat history
        st.session_state["chat_history"].append({"role": "ai", "content": ai_response})
        
        # Clear input text
        st.session_state["input_text"] = ""
    else:
        st.warning("Input cannot be empty. Please type something!")

# Handle clear button click
def handle_clear():
    st.session_state["chat_history"] = []
    st.session_state["input_text"] = ""

# CSS (Copied from Project 1)
st.markdown(
    """
    <style>
    html, body, .stApp {
        margin: 0;
        padding: 0;
        height: 100%;
        width: 100%;
        overflow: hidden; /* Remove scrollbars */
    }

    .stTextInput div[data-testid="stMarkdownContainer"] {
        display: none;
    }

    .shortcut-button {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 10px;
        margin: 20px 0;
        background-color: #f0f0f0;
        color: black;
        text-decoration: none;
        font-size: 18px;
        font-weight: bold;
        border-radius: 8px;
        width: fit-content;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        transition: background-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
    }

    .shortcut-button:hover {
        background-color: #007BFF;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
    }

    .shortcut-button img {
        margin-right: 10px;
        width: 24px;
        height: 24px;
    }

    .centered-title {
        text-align: center;
        margin-bottom: 10px;
    }

    .centered-subtitle {
        text-align: center;
        margin-top: 5px;
    }

    .chat-message {
        margin: 10px 0;
        padding: 10px;
        border-radius: 5px;
        max-width: 80%;
        font-family: Arial, sans-serif;
    }

    .user-message {
        text-align: right;
        margin-left: auto;
    }

    .ai-message {
        text-align: left;
        margin-right: auto;
    }

    .stButton > button {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# MAIN
st.markdown('<h1 class="centered-title">Sigma Boys - Spark</h1>', unsafe_allow_html=True)
st.markdown('<h3 class="centered-subtitle">Detection and Mitigation System for FDIA in IIoT</h3>', unsafe_allow_html=True)

# Shortcut to Chatbot
st.markdown(
    """
    <a href="#chatbot-sigma-boys" class="shortcut-button">
        <img src="https://cdn-icons-png.flaticon.com/512/2593/2593635.png" alt="Bot Logo">
        Go to Chatbot
    </a>
    """,
    unsafe_allow_html=True
)

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

# Link to return to Dashboard
st.markdown(
    """
    <a href="#dashboard" class="shortcut-button">
        <img src="https://cdn-icons-png.flaticon.com/512/6821/6821002.png" alt="Dashboard Logo">
        Go to Dashboard
    </a>
    """,
    unsafe_allow_html=True
)

chat_container = st.container()

with chat_container:
    for chat in st.session_state["chat_history"]:
        if chat["role"] == "user":
            st.markdown(
                f"""
                <div class="chat-message user-message">{chat["content"]}</div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="chat-message ai-message">{chat["content"]}</div>
                """,
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
