import streamlit as st

st.set_page_config(layout="wide")

# Inisialisasi session_state
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""

# Callback / Fungsi handle_send
def handle_send():
    user_text = st.session_state["input_text"]  # Ambil teks dari widget
    if user_text.strip():
        # Masukkan ke chat_history
        st.session_state["chat_history"].append({"role": "user", "content": user_text})
        st.session_state["chat_history"].append({"role": "ai", "content": f"This is a response to: {user_text}"})
        # Kosongkan input text
        st.session_state["input_text"] = ""
    else:
        # Jika input kosong, tambahkan pesan peringatan atau abaikan
        st.warning("Input cannot be empty. Please type something!")

def handle_clear():
    st.session_state["chat_history"] = []

# CSS untuk menyembunyikan "Press Enter to apply" dan menambahkan gaya untuk tombol
st.markdown(
    """
    <style>
    .stTextInput div[data-testid="stMarkdownContainer"] {
        display: none;
    }
    .shortcut-button {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 10px;
        margin: 20px 0;
        background-color: #f0f0f0; /* Background abu-abu */
        color: black; /* Warna teks hitam */
        text-decoration: none; /* Hilangkan garis bawah */
        font-size: 18px;
        font-weight: bold;
        border-radius: 8px;
        width: fit-content;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        transition: background-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
    }
    .shortcut-button:hover {
        background-color: #007BFF; /* Hover warna biru */
        color: white; /* Teks menjadi putih saat hover */
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
        text-decoration: none; /* Pastikan garis bawah tetap hilang saat hover */
    }
    .shortcut-button:visited, .shortcut-button:active {
        text-decoration: none; /* Pastikan garis bawah hilang untuk semua kondisi */
        color: black;
    }
    .shortcut-button img {
        margin-right: 10px;
        width: 24px;
        height: 24px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# MAIN
st.markdown(
    """
    <style>
    .centered-title {
        text-align: center;
        margin-bottom: 10px;
        padding-bottom: 0;
    }
       
    .centered-subtitle {
        text-align: center;
        margin-top: 5px;
        padding-top: 0;
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
        margin: 0 auto;
        display: block;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<h1 class="centered-title">Sigma Boys - Spark</h1>', unsafe_allow_html=True)
st.markdown('<h3 class="centered-subtitle">Detection and Mitigation System for FDIA in IIoT</h3>', unsafe_allow_html=True)

# # Shortcut ke Chatbot
# st.markdown('<a href="#chatbot-sigma-boys" style="text-decoration:none; font-size:18px; color:#007BFF;">Go to Chatbot</a>', unsafe_allow_html=True)

# Shortcut ke Chatbot dengan logo
st.markdown(
    """
    <a href="#chatbot-sigma-boys" class="shortcut-button">
        <img src="https://cdn-icons-png.flaticon.com/512/2593/2593635.png" alt="Bot Logo">
        Go to Chatbot
    </a>
    """,
    unsafe_allow_html=True
)


# Ruang untuk Dashboard Bliv
st.markdown("### Dashboard")
st.components.v1.html(
    """
    <iframe src="https://bliv.ai/embed/dashboard" 
            style="width:100%; height:500px; border:none;"></iframe>
    """,
    height=500,
)

# Chat Area
st.markdown('<h2 id="chatbot">Chatbot - Sigma Boys</h2>', unsafe_allow_html=True)

# Tambahkan tombol "Go to Dashboard" di bawah Chatbot - Sigma Boys
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

# Input Area
input_container = st.container()
with input_container:
    st.text_input(
        label="",
        placeholder="Type your message",
        key="input_text",
        on_change=handle_send,  # Panggil handle_send saat teks berubah
    )
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Send"):  # Tidak perlu memanggil handle_send lagi
            pass  # Fungsi sudah dipanggil melalui on_change
    with col2:
        if st.button("Clear"):
            handle_clear()
