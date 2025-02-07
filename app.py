import streamlit as st
import os
import json
import vertexai
from vertexai.preview.generative_models import GenerativeModel
import streamlit.components.v1 as components
from dotenv import load_dotenv
import requests
from flask import Flask, request, jsonify
import psycopg2
import pandas as pd  


# Load environment variables
load_dotenv()

# Streamlit page config
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

# Initialize Vertex AI
vertexai.init(project="sparkdatathon-2025-student-5", location="us-central1")
model = GenerativeModel("gemini-2.0-flash-exp")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""

# Dashboard Configuration
# Simpan token secara langsung di session state
SUP_URL = "https://dashboard.pulse.bliv.id"
DASHBOARD_ID = "883359f9-6bf3-468e-9d70-e391dcfa3542"
USERNAME = "pulse"
PASSWORD = "f6d72ad2-e454-11ef-9cd2-0242ac120002"

# Login ke Superset API
LOGIN_URL = f"{SUP_URL}/api/v1/security/login"
login_data = {
    "username": USERNAME,
    "password": PASSWORD,
    "provider": "db",
    "refresh": True
}

try:
    login_response = requests.post(LOGIN_URL, json=login_data, verify=False)
    login_response.raise_for_status()
    access_token = login_response.json().get("access_token")

    # Simpan token ke session_state agar bisa digunakan
    st.session_state["superset_token"] = access_token

except requests.exceptions.RequestException as e:
    print(f"❌ Error saat login: {e}")

def login_to_superset():
    """Login ke Superset API dan simpan token di session_state."""
    LOGIN_URL = f"{SUP_URL}/api/v1/security/login"
    login_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "provider": "db",
        "refresh": True
    }

    try:
        response = requests.post(LOGIN_URL, json=login_data, verify=False)
        response.raise_for_status()  # Pastikan tidak error

        token = response.json().get("access_token")
        
        if token:
            st.session_state["superset_token"] = token
        else:
            st.error("❌ Token tidak ditemukan dalam respons API.")

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error saat login Superset: {e}")

# Panggil fungsi login sebelum mengambil data dashboard
login_to_superset()

# Konfigurasi koneksi PostgreSQL
DB_HOST = "34.50.80.66"
DB_PORT = "5432"
DB_NAME = "pulse"
DB_USER = "pulse"
DB_PASSWORD = "uxeacaiheedeNgeebiveighetao9Eica"



# 4️⃣ Fungsi untuk mendapatkan skema database (schema tables)
def get_database_schema():
    """Mengambil informasi seluruh tabel dan kolom dari database PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        query = """
        SELECT table_name, column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public';
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        # Simpan schema dalam session_state agar tidak query ulang
        st.session_state["db_schema"] = df
        return df

    except Exception as e:
        st.error(f"❌ Error fetching database schema: {e}")
        return None



def get_hasilprediksi_data():
    """Ambil data dari tabel 'hasilprediksi' di PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        query = "SELECT * FROM hasilprediksi;"  # ✅ Ambil data dari tabel 'hasilprediksi'
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ Error fetching database data: {e}")
        return None

def is_sql_query(user_input):
    """Deteksi apakah input pengguna adalah pertanyaan SQL atau tidak."""
    sql_keywords = ["select", "count", "group by", "order by", "where", "table", "column", "data", "jumlah", "berapa", "hitung"]

    # Cek apakah input mengandung kata-kata terkait SQL
    return any(word in user_input.lower() for word in sql_keywords)

def generate_sql_query(user_input):
    """Mengubah teks natural menjadi query SQL, tetapi hanya mengizinkan SELECT, COUNT, FILTER, GROUP BY, ORDER BY, dan WHERE.
    MENOLAK query INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE.
    """
    if "db_schema" not in st.session_state or st.session_state["db_schema"] is None:
        return "❌ Database schema belum tersedia. Silakan jalankan `get_database_schema()` terlebih dahulu."

    schema_context = st.session_state["db_schema"].to_json(orient="records", indent=2)

    prompt = f"""
    Anda adalah AI yang mengubah teks natural menjadi SQL Query.
    **Pastikan query hanya menggunakan SELECT, COUNT, FILTER, GROUP BY, ORDER BY, dan WHERE.**
    Query yang diperbolehkan:
    - SELECT (mengambil data)
    - COUNT (menghitung jumlah data)
    - GROUP BY (mengelompokkan data)
    - ORDER BY (mengurutkan data)
    - WHERE (memfilter data)
    
    Berikut adalah skema tabel `hasilprediksi`:
    {schema_context}
    
    Contoh mapping input ke query:
    - "Berapa total attack?" ➝ `SELECT COUNT(*) FROM hasilprediksi WHERE marker = 'Attack';`
    - "Ada berapa natural?" ➝ `SELECT COUNT(*) FROM hasilprediksi WHERE marker = 'Natural';`
    
    Sekarang buat query SQL yang sesuai untuk permintaan ini:
    "{user_input}"
    
    **Hanya berikan query SQL tanpa format Markdown (tidak ada tanda ```sql atau ```).**
    """

    try:
        response = model.generate_content(prompt, stream=False)
        sql_query = response.text.strip()

        # Hapus tanda ```sql atau ``` yang mungkin muncul
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

        # Cegah query yang mengubah data
        forbidden_keywords = ["insert", "update", "delete", "drop", "alter", "truncate"]
        if any(keyword in sql_query.lower() for keyword in forbidden_keywords):
            return "❌ Query tidak diizinkan. Hanya query SELECT, COUNT, FILTER, GROUP BY, ORDER BY, dan WHERE yang dapat dieksekusi."

        return sql_query

    except Exception as e:
        return f"❌ Error processing SQL query: {str(e)}"



def execute_sql_query(sql_query):
    """Eksekusi SQL Query yang diberikan dan kembalikan hasil dalam format teks."""
    if not sql_query or sql_query.startswith("❌"):
        return "❌ Query tidak valid, eksekusi dibatalkan."

    forbidden_keywords = ["insert", "update", "delete", "drop", "alter", "truncate"]
    if any(keyword in sql_query.lower() for keyword in forbidden_keywords):
        return "❌ Query tidak diizinkan. Hanya query SELECT, COUNT, FILTER, GROUP BY, ORDER BY, dan WHERE yang dapat dieksekusi."

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )

        with conn.cursor() as cur:
            cur.execute(sql_query)

            # Ambil nama kolom
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        
        conn.close()

        # Konversi hasil ke format teks
        if not rows:
            return "✅ Query berhasil dijalankan, tetapi tidak ada data yang ditemukan."

        result_text = "\n".join([", ".join(map(str, row)) for row in rows])
        return f"{result_text}"

    except Exception as e:
        return f"❌ Error executing query: {str(e)}"




# Dashboard Embed Code (Perbaikan ukuran)
dashboard_html = f"""
<script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
<script src="https://unpkg.com/@superset-ui/embedded-sdk"></script>

<style>
    body, html {{
        margin: 0;
        padding: 0;
        width: 100%;
        height: 100%;
    }}
    #superset-container {{
        width: 100vw; 
        height: 100vh; 
        position: relative;
    }}
    iframe {{
        width: 100%;
        height: 100%;
        border: none;
    }}
</style>

<div id="superset-container"></div>

<script>
    const supersetUrl = "{SUP_URL}";
    const supersetApiUrl = supersetUrl + "/api/v1/security";
    const dashboardId = "{DASHBOARD_ID}";

    async function authenticateAndEmbedDashboard() {{
        console.log("🔄 Refresh Detected: Clearing old token...");
        localStorage.removeItem("superset_token");  // Hapus token lama saat refresh
        
        let access_token = null;

        try {{
            console.log("🔍 Authenticating...");
            
            // Lakukan login ulang untuk mendapatkan token baru
            const login_body = {{
                "username": "pulse",
                "password": "f6d72ad2-e454-11ef-9cd2-0242ac120002",
                "provider": "db",
                "refresh": true
            }};
            const login_headers = {{ headers: {{ "Content-Type": "application/json" }} }};

            let loginResponse = await axios.post(supersetApiUrl + "/login", login_body, login_headers);
            access_token = loginResponse.data["access_token"];
            localStorage.setItem("superset_token", access_token);

            console.log("✅ New Access Token:", access_token);

            // Kirim token ke parent (misalnya, Streamlit)
            if (access_token) {{
                console.log("📡 Sending token to Streamlit...");
                window.parent.postMessage({{ type: "TOKEN_UPDATE", token: access_token }}, "*");
            }}

            // **Dapatkan Guest Token untuk Embed Dashboard**
            const guest_token_body = {{
                "resources": [{{ "type": "dashboard", "id": dashboardId }}],
                "rls": [],
                "user": {{
                    "username": "report-viewer",
                    "first_name": "report-viewer",
                    "last_name": "report-viewer"
                }}
            }};

            const guest_token_headers = {{
                headers: {{
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + access_token
                }}
            }};

            let guestResponse = await axios.post(supersetApiUrl + "/guest_token/", guest_token_body, guest_token_headers);
            const guest_token = guestResponse.data["token"];
            console.log("✅ Guest Token received:", guest_token);

            // **Embed Dashboard**
            supersetEmbeddedSdk.embedDashboard({{
                id: dashboardId,
                supersetDomain: supersetUrl,
                mountPoint: document.getElementById("superset-container"),
                fetchGuestToken: async () => guest_token,
                dashboardUiConfig: {{
                    hideTitle: false,
                    filters: {{ expanded: false, visible: true }}
                }}
            }});

        }} catch (error) {{
            console.error("❌ Dashboard error:", error);
            if (error.response) {{
                console.log("Error Response Data:", error.response.data);
            }}
        }}
    }}

    // Menangani permintaan token dari parent (misal, Streamlit)
    window.addEventListener("message", (event) => {{
        if (event.data.type === "REQUEST_TOKEN") {{
            let stored_token = localStorage.getItem("superset_token");
            window.parent.postMessage({{ type: "TOKEN_UPDATE", token: stored_token }}, "*");
        }}
    }});

    // **Panggil fungsi autentikasi saat halaman dimuat**
    window.onload = authenticateAndEmbedDashboard;
</script>
"""

st.session_state["superset_token"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6dHJ1ZSwiaWF0IjoxNzM4ODQ4MDMyLCJqdGkiOiIyNWQ3MGM1Ny02OTM3LTRjY2EtOTE3NS1iNWFkZTJjZDFiMjIiLCJ0eXBlIjoiYWNjZXNzIiwic3ViIjo1LCJuYmYiOjE3Mzg4NDgwMzIsImNzcmYiOiJiMTIyYzFjYy0xMzIyLTQzZWItOWEyMy05YjBkODZmNjNmOTgiLCJleHAiOjE3Mzg4NDg5MzJ9.mz2b7hV5fGZgRj92EVBkeBwbR7amFlXs7bZD7erIOK0"



# Buat Flask app di dalam Streamlit
app = Flask(__name__)

@app.route("/store_token", methods=["POST"])
def store_token():
    """Menerima token dari JavaScript dan menyimpannya ke session_state Streamlit."""
    data = request.get_json()

    # Debugging untuk melihat data yang diterima
    print("🔍 Data token diterima:", data)

    if not data or "token" not in data:
        return jsonify({"error": "Token missing"}), 400

    st.session_state["superset_token"] = data["token"]
    print("✅ Token berhasil disimpan:", st.session_state["superset_token"])

    return jsonify({"message": "Token stored successfully"}), 200

# Define a detailed base prompt
BASE_PROMPT = """
{json.dumps(dashboard_data, indent=2)}
📌 **Nama Chatbot**: Sigma AI  
📌 **Peran**: Asisten AI yang ahli dalam keamanan siber, khususnya dalam mendeteksi dan mengurangi **False Data Injection Attacks (FDIA)** pada sistem **Industrial Internet of Things (IIoT)**.  
📌 **Tugas Utama**:  
1. **Menjawab pertanyaan teknis** tentang **FDIA, IIoT, dan keterkaitannya.  
2. **Menjelaskan fitur dan fungsi platform Sigma Boys** jika diminta.  
3. **Memahami dan menjelaskan fitur utama yang tersedia dalam sistem deteksi FDIA**, termasuk:  
   - **Interpretasi nilai asli vs. nilai transformasi** (misal, denormalisasi dst_port dari 0.0863 ke 5655).  
   - **Cara kerja normalisasi & transformasi data** dalam machine learning.  
   - **Analisis dan pemetaan kembali data ke bentuk aslinya**.  
4. **Menjelaskan grafik, chart, visualisasi data, serta pelaporan dashboard**.  
5. **Memberikan saran mitigasi & langkah yang diperlukan untuk mengurangi serangan FDIA**.  
6. **Menjawab pertanyaan umum yang tidak terkait dengan platform secara akurat dan sopan**.  
7. **Menggunakan bahasa fleksibel** (bisa formal, teknis, atau santai, tergantung gaya pengguna).  
8. **Menjaga kerahasiaan informasi penting** (misal, Google Application Credentials, akun, API, SDK, atau password).  
📊 **Kemampuan Membaca dan Menjelaskan Data Visualisasi**  
- Bisa menjelaskan **grafik anomali**, **heatmap serangan**, **tren FDIA dalam IIoT**, dan sebagainya.  
- Bisa membaca **dashboard monitoring**, menjelaskan **alert**, dan memberikan **saran mitigasi**.  
- Mampu membedakan **false positive vs. true positive** dalam deteksi serangan.  
🛡️ **Kemampuan Memberikan Mitigasi FDIA di IIoT**  
- Memberikan rekomendasi **firewall rules, IDS/IPS tuning, segmentasi jaringan**, dan **model machine learning** yang lebih akurat.  
- Memahami bagaimana **serangan FDIA bekerja di sistem IIoT**, termasuk dampaknya ke sensor, aktuator, dan pengambilan keputusan.  
- Dapat **menganalisis pola serangan berdasarkan log jaringan** dan mendeteksi **indikator kompromi (IoC)**.  
⚡ **Responsif & Fleksibel**  
- Bisa berbicara dengan gaya **formal, teknis, santai formal**, tergantung cara komunikasi pengguna.  
- Tidak terlalu sering menyebut **Sigma Boys** atau **Sigma AI**, kecuali jika diminta untuk memperkenalkan platform.  
- Tidak membagikan **informasi rahasia atau sensitif**.  
📌 Peran: Chatbot yang dapat menjelaskan 31 fitur utama dalam log jaringan, membantu analisis serangan FDIA, serta menafsirkan data transformasi dalam sistem deteksi anomali.
📌 Kemampuan Utama:
Memahami nilai asli vs. nilai transformasi dalam dataset deteksi FDIA.
Menjelaskan metode normalisasi (Min-Max Scaling, Z-Score) yang digunakan untuk mengubah data mentah menjadi bentuk yang bisa diproses oleh machine learning.
Mengembalikan nilai yang sudah dinormalisasi ke bentuk aslinya (denormalisasi).
Menjelaskan cara kerja setiap fitur dalam log jaringan dan bagaimana fitur tersebut digunakan untuk mendeteksi serangan.
📌 Penjelasan Fitur Utama dalam Log Jaringan:
dst_port (Port Tujuan) – Nomor port tujuan komunikasi jaringan.
src_port (Port Sumber) – Nomor port yang digunakan oleh pengirim paket.
dns_rcode (DNS Response Code) – Kode status dari permintaan DNS.
conn_state (Status Koneksi) – Status koneksi antara client dan server.
http_user_agent – Identitas perangkat atau aplikasi yang melakukan request HTTP.
ssl_version – Versi SSL/TLS yang digunakan dalam komunikasi aman.
http_status_code – Kode status HTTP dari server.
dns_query – Nama domain yang diminta dalam query DNS.
ssl_cipher – Algoritma enkripsi yang digunakan dalam SSL/TLS.
service – Jenis layanan yang terdeteksi dalam komunikasi jaringan.
proto (Protocol) – Protokol jaringan yang digunakan (TCP, UDP, ICMP).
dns_rejected – Apakah permintaan DNS ditolak oleh server.
Peran: Chatbot ini dapat membaca dan menjelaskan grafik, chart, heatmap, dan tren yang muncul di dashboard Sigma Boys untuk mendeteksi FDIA dalam IIoT.
📌 Kemampuan Utama:
Menganalisis heatmap serangan untuk melihat pola FDIA dalam waktu tertentu.
Membaca trend anomaly detection dan menjelaskan false positive vs. true positive.
Menjelaskan spike atau lonjakan data mencurigakan dalam grafik monitoring.
📌 Contoh Analisis Grafik:
❓ User: "Di dashboard ada grafik lonjakan di dns_query, artinya apa?"
✅ Chatbot: "Kalau ada lonjakan mendadak di dns_query, bisa jadi ada domain generation algorithm (DGA) attack dari malware yang mencoba berkomunikasi dengan C2 Server. Cek domain yang sering muncul di log DNS!"
Peran: Chatbot yang memberikan langkah mitigasi jika ditemukan serangan FDIA dalam sistem IIoT.
📌 Kemampuan Utama:
Menganalisis log jaringan untuk menemukan indikasi serangan.
Menyarankan aturan firewall dan IDS untuk memblokir serangan.
Memberikan strategi penerapan machine learning untuk mendeteksi FDIA lebih akurat.
Menjelaskan dampak FDIA terhadap sistem sensor dan kontrol IIoT.
📌 Contoh Respon Mitigasi:
❓ User: "Gimana cara mencegah FDIA di sensor tekanan industri?"
✅ Chatbot:
Gunakan validasi data berbasis ML – Latih model untuk mendeteksi anomali dalam pembacaan sensor.
Terapkan checksum & enkripsi – Pastikan data sensor dienkripsi agar tidak mudah dipalsukan.
Gunakan timestamping & nonce – Setiap data harus punya tanda waktu agar tidak bisa digunakan ulang oleh attacker.
eran: Chatbot yang dapat membantu menganalisis serangan berdasarkan log dan metadata jaringan.
📌 Kemampuan Utama:
Menggunakan fitur-fitur log jaringan yang tersedia untuk menganalisis pola serangan.
Menghubungkan aktivitas mencurigakan dengan teknik eksploitasi yang dikenal.
Menyarankan tools forensik jaringan seperti Zeek, Suricata, dan Wireshark.
📌 Contoh Investigasi:
❓ User: "Gue lihat ada lonjakan koneksi dari IP asing dengan conn_state aneh, itu tanda apa?"
✅ Chatbot:
Jika conn_state = S0, bisa jadi port scanning.
Jika conn_state = RSTO, mungkin ada upaya brute force yang gagal.
Jika http_request_body_len besar, mungkin ada upaya data exfiltration.
🚨 Rekomendasi:
Blokir IP mencurigakan di firewall.
Cek log lebih lanjut di SIEM atau packet capture.
Gunakan aturan IDS/IPS untuk mendeteksi pola serangan.
📌 Daftar 30 Fitur utama dalam Log Jaringan (FDIA Detection System) (**DAFTAR INI ADALAH FITUR UTAMA, TETAPI ADA KEMUNGKINAN ADA FITUR LAIN YANG BELUM DISEBUTKAN**)
1️⃣ HTTP (Hypertext Transfer Protocol)
http_response_body_len → Panjang (dalam byte) dari body HTTP response yang diterima oleh client.
http_resp_mime_types → Tipe MIME dari respons HTTP (misal: text/html, application/json, image/png).
http_request_body_len → Panjang (dalam byte) dari body HTTP request yang dikirim client.
http_user_agent → Identitas browser atau aplikasi yang melakukan request HTTP.
http_orig_mime_types → Tipe MIME dari request HTTP yang dikirim client.
http_trans_depth → Kedalaman transaksi HTTP dalam koneksi yang sama.
http_method → Metode HTTP yang digunakan (GET, POST, PUT, DELETE).
http_status_code → Kode status HTTP yang dikirim oleh server (200, 404, 500, dll.).
http_version → Versi HTTP yang digunakan (HTTP/1.1, HTTP/2).
http_uri → Alamat lengkap dari permintaan HTTP (misal: /login.php, /api/data).
2️⃣ SSL/TLS (Secure Socket Layer & Transport Layer Security)
ssl_issuer → Nama organisasi yang menerbitkan sertifikat SSL (Let's Encrypt, DigiCert).
ssl_subject → Nama entitas yang menggunakan sertifikat SSL (www.google.com).
ssl_cipher → Algoritma enkripsi yang digunakan dalam SSL/TLS (TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256).
ssl_version → Versi protokol SSL/TLS (TLS 1.2, TLS 1.3).
ssl_resumed → Apakah koneksi SSL/TLS menggunakan sesi sebelumnya (True/False).
ssl_established → Apakah koneksi SSL/TLS berhasil terjalin (True/False).
3️⃣ DNS (Domain Name System)
dns_rcode (DNS Response Code) → Kode status dari server DNS (0 = NoError, 3 = NXDomain, dll.).
dns_qclass (DNS Query Class) → Jenis permintaan DNS (1 = IN - Internet).
dns_qtype (DNS Query Type) → Jenis permintaan DNS (A, AAAA, MX, CNAME, TXT).
dns_rejected → Apakah permintaan DNS ditolak oleh server (True/False).
dns_RA (Recursion Available) → Apakah server DNS mendukung recursive queries (True/False).
dns_RD (Recursion Desired) → Apakah client meminta recursive DNS lookup (True/False).
dns_AA (Authoritative Answer) → Apakah server DNS memberikan jawaban authoritative (True/False).
dns_query → Nama domain yang diminta dalam query DNS (misal: www.facebook.com).
4️⃣ Jaringan & Koneksi
dst_port (Destination Port) → Port tujuan dari komunikasi jaringan (80, 443, 53, dll.).
src_port (Source Port) → Port asal dari komunikasi jaringan.
proto (Protocol) → Protokol jaringan yang digunakan (TCP, UDP, ICMP).
conn_state (Connection State) → Status koneksi antara client dan server (S0, S1, SF, dll.).
service → Jenis layanan jaringan yang terdeteksi (http, dns, ftp, dll.).
dst_ip_bytes → Jumlah byte yang dikirim ke IP tujuan.
**YANG TERPENTING BERIKAN JAWABAN YANG PASTI (TIDAK ADA KATA MUNGKIN, BISA JADI, KAYAKNYA, ATAUPUN KATA LAIN YANG RAGU-RAGU, HINDARI KATA-KATA ITU)**
**id di postgres hanya menunjukkan data unique saja tidak ada makna**
"""

def generate_response(user_input, database_data):
    """
    Gunakan data dari tabel 'hasilprediksi' untuk memberikan jawaban yang lebih akurat.
    """
    if database_data is None or database_data.empty:
        return "⚠️ Tidak ada data yang tersedia dalam tabel 'hasilprediksi'."

    # Pastikan data hanya mengandung informasi yang relevan untuk chatbot
    kolom_yang_diperlukan = ["id", "marker"]
    
    if not all(col in database_data.columns for col in kolom_yang_diperlukan):
        return "⚠️ Tabel hasilprediksi tidak memiliki struktur yang sesuai."

    database_context = database_data[kolom_yang_diperlukan].to_json(orient="records", indent=2)

    # Perbaikan Prompt untuk lebih kontekstual
    prompt = f"""
    Anda adalah chatbot AI yang membaca data prediksi dari tabel 'hasilprediksi' di PostgreSQL.
    Berikut adalah struktur tabel:
    - id (integer) → ID unik untuk setiap prediksi.
    - membaca kolom marker untuk mengidentifikasi attack dan natural

    Anda harus menjawab pertanyaan pengguna berdasarkan data berikut:

    {database_context}

    Pertanyaan pengguna: {user_input}

    **Berikan jawaban yang akurat berdasarkan data, dan jangan berasumsi jika data tidak ditemukan.**
    """

    try:
        response = model.generate_content(prompt, stream=True)
        return "".join(res.text for res in response)
    except Exception as e:
        return f"❌ Error processing response: {str(e)}"


# Handle send button click
def handle_send():
    """Menangani input pengguna, baik sebagai pertanyaan SQL atau pertanyaan umum."""
    user_text = st.session_state["input_text"]

    if user_text.strip():
        # **Pastikan skema database tersedia**
        if "db_schema" not in st.session_state:
            st.session_state["db_schema"] = get_database_schema()

        if st.session_state["db_schema"] is None:
            st.warning("⚠️ Tidak dapat mengambil skema database. Periksa koneksi PostgreSQL.")
            return  # ✅ Posisikan return di dalam fungsi

        # **Cek apakah input perlu diproses sebagai query SQL**
        if is_sql_query(user_text):
            # Buat query SQL
            sql_query = generate_sql_query(user_text)

            # Debug: tampilkan query sebelum dieksekusi
            st.write(f"🧐 Debug: Query yang akan dijalankan - '{sql_query}'")

            # **Cek apakah query valid sebelum dieksekusi**
            if sql_query.startswith("❌"):
                st.warning(sql_query)  # Tampilkan pesan error
                return  # ✅ Posisikan return di dalam fungsi

            # **Jalankan query SQL**
            ai_response = execute_sql_query(sql_query)
        else:
            # **Jika bukan SQL, gunakan model AI untuk menjawab pertanyaan**
            ai_response = model.generate_content(user_text).text.strip()

        # **Simpan hasil dalam chat history**
        st.session_state["chat_history"].append({"role": "user", "content": user_text})
        st.session_state["chat_history"].append({"role": "ai", "content": ai_response})

        # **Kosongkan input setelah mengirim**
        st.session_state["input_text"] = ""  

    else:
        st.warning("Input tidak boleh kosong. Silakan ketik sesuatu!")



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
st.markdown(
    """
    <h1 style='text-align: center;'>Sigma AI - FDIA Detection & Mitigation System</h1>
    """,
    unsafe_allow_html=True
)

# Display Dashboard (Full Width)
st.subheader("📊 Sigma Dashboard")

# Shortcut to Chatbot
st.markdown(
    """
    <a href="#13ef106a" class="shortcut-button">
        <img src="https://cdn-icons-png.flaticon.com/512/2593/2593635.png" alt="Bot Logo">
        Go to Chatbot
    </a>
    """,
    unsafe_allow_html=True
)

# Display Dashboard (Full Width)
components.html(dashboard_html, height=700)

# Display Chatbot Below
st.subheader("💬 Sigma Chatbot")

chat_container = st.container()

with chat_container:
    for chat in st.session_state["chat_history"]:
        if chat["role"] == "user":
            st.markdown(f"<div style='text-align:right;'><b>User:</b> {chat['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align:left;'><b>Sigma AI:</b> {chat['content']}</div>", unsafe_allow_html=True)

# Chat Input (Centered)
with st.form("chat_form", clear_on_submit=True):
    st.text_input(label="", placeholder="Type your message...", key="input_text")
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        st.form_submit_button("Send", on_click=handle_send)
    with col_btn2:
        st.form_submit_button("Clear", on_click=handle_clear)

# Button to Go to Dashboard (Under Sigma Chatbot)
st.markdown(
    """
    <a href="#8588f86d" class="shortcut-button">
        <img src="https://cdn-icons-png.flaticon.com/512/6821/6821002.png" alt="Dashboard Logo">
        Go to Dashboard
    </a>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
        .css-1v3fvcr {display: none;}  /* CSS untuk menyembunyikan badge 'Hosted with Streamlit' */
    </style>
    """, unsafe_allow_html=True
)
