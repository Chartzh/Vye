import streamlit as st
from google import genai
from google.genai import types
import yt_dlp
import os
import glob
import requests
from PIL import Image
from io import BytesIO
from fpdf import FPDF
import sqlite3
from datetime import datetime
import pandas as pd
import re
import time
import psycopg2
from supabase import create_client

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Vye - Vie for Attention",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Background */
    .main {
        background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%);
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #16213e 0%, #0f3460 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: #e8e8e8 !important;
    }
    
    /* Header Styling */
    h1, h2, h3 {
        color: #00d9ff !important;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    
    /* Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.2em;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* Primary Button */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
    }
    
    .stButton>button[kind="primary"]:hover {
        box-shadow: 0 6px 20px rgba(245, 87, 108, 0.6);
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 55px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        color: #b8b8b8;
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(0, 217, 255, 0.3);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-color: transparent;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* Input Fields */
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        color: #e8e8e8;
        padding: 12px;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #00d9ff;
        box-shadow: 0 0 0 1px #00d9ff;
    }
    
    /* Text Area */
    .stTextArea textarea {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        color: #e8e8e8;
    }
    
    /* Radio Buttons */
    .stRadio > div {
        background: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Select Box */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    /* Info Box */
    .stAlert {
        background: rgba(0, 217, 255, 0.1);
        border-left: 4px solid #00d9ff;
        border-radius: 8px;
    }
    
    /* VS Badge */
    .vs-badge {
        text-align: center;
        font-size: 4rem;
        font-weight: 900;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(245, 87, 108, 0.5);
        animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Card Styling */
    .video-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    
    /* Logo Style */
    .logo-text {
        font-size: 2.5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #00d9ff 0%, #667eea 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        letter-spacing: 2px;
    }
    
    .tagline {
        text-align: center;
        color: #b8b8b8;
        font-style: italic;
        font-size: 0.9rem;
        margin-top: -10px;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #00d9ff !important;
    }
    
    /* Chat Messages */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Divider */
    hr {
        border-color: rgba(255, 255, 255, 0.1);
    }
    
    /* Battle Columns */
    .battle-column {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        height: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP ---
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Config Error: {e}")
        return None

def save_to_db(title, url, summary, lang):
    supabase = init_supabase()
    if supabase:
        try:
            date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            short_summary = summary[:1000] + "..." if len(summary) > 1000 else summary
            
            # Kirim data via HTTP Request (JSON)
            data = {
                "date": date_now,
                "video_title": title,
                "video_url": url,
                "analysis_summary": short_summary,
                "language": lang
            }
            # Insert ke tabel 'history'
            supabase.table("history").insert(data).execute()
        except Exception as e:
            st.error(f"Gagal simpan ke Cloud: {e}")

def save_to_database(title, url, summary, lang, analysis_type):
    """Wrapper function to save analysis to database with analysis type"""
    save_to_db(title, url, summary, lang)

def load_history():
    supabase = init_supabase()
    if supabase:
        try:
            # Ambil data via HTTP Request
            response = supabase.table("history").select("*").order("id", desc=True).execute()
            data = response.data
            if data:
                return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Gagal load data: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=60) # Cache 1 menit biar gak berat loadingnya
def get_unique_channels():
    """Mengambil daftar nama channel yang unik dari database"""
    supabase = init_supabase()
    try:
        # Ambil kolom channel_name saja
        response = supabase.table("channel_knowledge").select("channel_name").execute()
        
        if response.data:
            # Pakai set() untuk menghapus duplikat, lalu urutkan
            unique_names = sorted(list(set([row['channel_name'] for row in response.data])))
            return ["Semua Channel"] + unique_names
        else:
            return ["Semua Channel"]
    except Exception as e:
        # Kalau error (misal tabel kosong), return default aja
        return ["Semua Channel"]

# --- PDF GENERATION ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0, 100, 200)
        self.cell(0, 10, 'VYE - Video Analysis Report', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 150, 255)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(3)
    
    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.set_text_color(0, 0, 0)
        # Clean text from emojis and special characters
        body = self.clean_text(body)
        self.multi_cell(0, 6, body)
        self.ln()
    
    def clean_text(self, text):
        """Remove emojis and non-ASCII characters"""
        # Remove emojis
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

def generate_pdf(video_title, analysis_text):
    """Generate PDF report"""
    try:
        pdf = PDF()
        pdf.add_page()
        
        # Add metadata
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 8, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1)
        pdf.ln(5)
        
        # Video Title
        pdf.chapter_title('Video Title:')
        pdf.chapter_body(video_title)
        
        # Analysis
        pdf.chapter_title('Strategic Analysis:')
        pdf.chapter_body(analysis_text)
        
        # Save
        filename = f"vye_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf.output(filename)
        return filename
    except Exception as e:
        st.error(f"PDF Generation Error: {str(e)}")
        return None
    
def search_channel_brain(query_text, channel_name, match_count=5):
    client_genai = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    supabase = init_supabase()
    
    try:
        # 1. Embedding DULUAN (Wajib)
        # Pastikan modelnya SAMA dengan saat ingest (ingest pake gemini-embedding-001 kan?)
        res = client_genai.models.embed_content(
            model="gemini-embedding-001",
            contents=query_text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )
        query_vector = res.embeddings[0].values
        
        # 2. Tentukan mau panggil RPC yang mana
        if channel_name == "Semua Channel":
            # Panggil fungsi SQL khusus tanpa filter
            # Parameter cuma butuh vektor, threshold, dan count
            response = supabase.rpc('match_documents_all', {
                'query_embedding': query_vector,
                'match_threshold': 0.1,
                'match_count': match_count
            }).execute()
        else:
            # Panggil fungsi SQL standar dengan filter channel
            response = supabase.rpc('match_documents', {
                'query_embedding': query_vector,
                'match_threshold': 0.1,
                'match_count': match_count,
                'filter_channel': channel_name 
            }).execute()
        
        return response.data if response.data else []

    except Exception as e:
        st.error(f"RAG Search Error: {e}")
        return []
    
# --- SIDEBAR & SETUP ---
with st.sidebar:
    st.markdown('<div class="logo-text">VYE</div>', unsafe_allow_html=True)
    st.markdown('<div class="tagline">Vie for Attention</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # API Key
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("🔑 Google API Key:", type="password")
        if not api_key: 
            st.warning("⚠️ API Key diperlukan untuk melanjutkan")
            st.stop()
    
    client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    
    st.markdown("---")
    
    # LANGUAGE SELECTOR (NEW FEATURE #2)
    st.markdown("### 🌐 Output Language")
    output_language = st.selectbox(
        "Select analysis language:",
        ["Indonesian", "English", "Javanese Style", "Formal Business"],
        help="AI will generate analysis in this language/style"
    )
    
    st.markdown("---")
    
    # MODE SELECTOR (UPDATED WITH NEW MODES)
    app_mode = st.radio(
        "🎯 Select Mode:", 
        ["📊 Single Analysis", "⚔️ Battle Mode", "⚖️ Prompt Battle", "🧠 Channel Brain","🗄️ History Database"],
        help="Pilih mode analisis sesuai kebutuhan"
    )
    
    st.markdown("---")
    with st.expander("➕ Tambah Channel Baru (Auto Ingest)"):
        st.caption("Masukkan link channel untuk dipelajari AI")
        ingest_url = st.text_input("Channel URL", placeholder="https://youtube.com/@...")
        ingest_name = st.text_input("Nama Label", placeholder="GadgetIn")
        
        if st.button("Mulai Belajar 🚀", key="btn_ingest"):
            if ingest_url and ingest_name:
                with st.spinner("Sedang memproses..."):
                    try:
                        import ingest_channel
                        jumlah_masuk = ingest_channel.process_channel(ingest_url, ingest_name)
                        
                        if jumlah_masuk > 0:
                            st.success(f"{jumlah_masuk} Video berhasil masuk Database.")
                        else:
                            st.error("❌ Gagal. Tidak ada video yang berhasil diproses.")
                            
                    except ImportError:
                        st.error("File ingest_channel.py tidak ditemukan.")
    
    # Info Box
    st.info(f"🔥 Active: **{app_mode}**")
    
    st.markdown("<br>" * 3, unsafe_allow_html=True)
    st.caption("Powered by Gemini AI")

# --- LANGUAGE PROMPTS MAPPER ---
LANGUAGE_INSTRUCTIONS = {
    "Indonesian": "Berikan semua analisis dalam Bahasa Indonesia yang profesional dan mudah dipahami.",
    "English": "Provide all analysis in professional, clear English.",
    "Javanese Style": "Berikan analisis dalam gaya bahasa Jawa yang halus namun tetap informatif. Gunakan beberapa istilah Jawa yang sopan.",
    "Formal Business": "Provide analysis in formal business language, suitable for corporate presentations and executive reports."
}

# --- PROMPTS ---
def get_strategy_prompt(language):
    """Generate strategy prompt with language instruction"""
    return f"""
{LANGUAGE_INSTRUCTIONS[language]}

Kamu adalah Expert YouTube Strategist. Analisis transkrip ini dengan detail:

## 📊 Executive Summary
Berikan 3 poin utama yang paling menonjol dari video ini.

## 🔥 Virality Score
Berikan skor 0-100 dengan breakdown alasan mengapa video ini berpotensi viral atau tidak.

## ✂️ Clip Ideas
Identifikasi 3-5 momen terbaik untuk dijadikan short clips dengan timestamp yang tepat.

## 📈 SEO Optimization
- Judul yang lebih clickable
- Deskripsi yang SEO-friendly
- 10-15 tags yang relevan

## 💡 Content Gaps
Apa yang bisa ditambahkan untuk membuat konten ini lebih komprehensif?

TRANSKRIP:
"""

THUMBNAIL_PROMPT = """
Bertindaklah sebagai Expert Thumbnail Designer & CTR Optimizer.

Analisis thumbnail ini berdasarkan:
1. **CTR Score (0-10)**: Seberapa clickable thumbnail ini?
2. **Visual Hierarchy**: Apakah elemen penting terlihat jelas?
3. **Color Psychology**: Apakah kombinasi warna efektif?
4. **Text Readability**: Apakah teks mudah dibaca?
5. **Emotional Trigger**: Apakah memicu curiosity/emotion?

Berikan saran konkret untuk meningkatkan CTR minimal 20%.
"""

def get_competitor_prompt(language):
    """Generate competitor prompt with language instruction"""
    return f"""
{LANGUAGE_INSTRUCTIONS[language]}

Kamu adalah Strategic Content Analyst. Lakukan analisis kompetitif mendalam.

## 🏆 The Winner
Pilih pemenang secara objektif berdasarkan:
- Content value & depth
- Storytelling quality
- Audience engagement potential
- Production quality

## ⚔️ Strengths & Weaknesses Matrix

### Video A (Your Video)
**💪 Kekuatan:**
- [List semua aspek yang unggul]

**⚠️ Kelemahan:**
- [List area yang perlu diperbaiki]

### Video B (Competitor)
**💪 Kekuatan:**
- [List semua aspek yang unggul]

**⚠️ Kelemahan:**
- [List area yang perlu diperbaiki]

## 🎯 Gap Analysis
Identifikasi topik/sudut pandang yang dibahas kompetitor tetapi terlewat di video Anda.

## 💡 Actionable Strategy
Berikan 5 langkah konkret untuk:
1. Menutup content gap
2. Meningkatkan kualitas konten
3. Mengalahkan kompetitor di niche yang sama

## 📊 Score Breakdown
Buat scoring untuk kedua video (skala 1-10):
- Content Depth: 
- Hook Quality:
- Pacing:
- Value Delivered:
- Production Quality:

DATA TRANSKRIP:
"""

# PROMPT BATTLE PERSONAS (NEW FEATURE #3)
def get_corporate_prompt(language):
    """Corporate Consultant Persona"""
    return f"""
{LANGUAGE_INSTRUCTIONS[language]}

You are a CORPORATE STRATEGY CONSULTANT specializing in business content optimization.

Analyze this video with a focus on:
- ROI potential and monetization opportunities
- Professional credibility and authority building
- B2B appeal and enterprise value
- Data-driven metrics and KPIs
- Formal presentation quality

Provide strategic recommendations suitable for board presentations.

TRANSCRIPT:
"""

def get_genz_prompt(language):
    """Gen-Z Viral Expert Persona"""
    return f"""
{LANGUAGE_INSTRUCTIONS[language]}

You are a VIRAL GEN-Z CONTENT STRATEGIST. You live and breathe TikTok, Reels, and Shorts.

Analyze this video focusing on:
- Hook strength in first 3 seconds
- Viral moment potential
- Meme-ability and shareability
- Gen-Z slang and relatability
- Short-form content adaptation
- Social media algorithm optimization

Give advice using modern internet language. Be energetic and trend-focused!

TRANSCRIPT:
"""

# --- FUNGSI HELPER ---
def get_transcript_data(video_url):
    """Extract transcript, title, and thumbnail from YouTube video"""
    # Bersihkan temp file lama
    for f in glob.glob("temp_subs*"):
        try: os.remove(f)
        except: pass

    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['id', 'en', 'id-ID', 'en-US'],
        'subtitlesformat': 'vtt',
        'outtmpl': 'temp_subs_%(id)s',
        'cookiefile': 'cookies.txt',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            title = info.get('title', 'Video YouTube')
            thumb_url = info.get('thumbnail', '')
            vid_id = info.get('id', '')
            
            downloaded_subs = glob.glob(f"temp_subs_{vid_id}*.vtt")
            
            full_text = ""
            if downloaded_subs:
                sub_file = downloaded_subs[0]
                text_content = []
                with open(sub_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    seen = set()
                    current_time = "00:00"
                    for line in lines:
                        line = line.strip()
                        if '-->' in line:
                            current_time = line.split('.')[0]
                            continue
                        if line and line != 'WEBVTT' and not line.isdigit() and line not in seen:
                            text_content.append(f"[{current_time}] {line}")
                            seen.add(line)
                full_text = "\n".join(text_content)
                os.remove(sub_file)
            
            return full_text, title, thumb_url

    except Exception as e:
        st.error(f"Extraction error: {str(e)}")
        return None, None, None

def load_image_from_url(url):
    """Load image from URL for AI analysis"""
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return img
    except: 
        return None

# --- MODE 1: SINGLE VIDEO ANALYSIS ---
if app_mode == "📊 Single Analysis":
    
    # Header
    st.markdown("# 🎬 Single Video Intelligence")
    st.markdown("Analisis mendalam untuk satu video YouTube")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Input URL
    url = st.text_input(
        "🔗 YouTube URL:", 
        placeholder="https://youtube.com/watch?v=...",
        help="Paste link video YouTube yang ingin dianalisis"
    )

    # Session State Setup
    if 'transcript' not in st.session_state: 
        st.session_state.transcript = None
    if 'video_title' not in st.session_state: 
        st.session_state.video_title = None
    if 'thumb_url' not in st.session_state: 
        st.session_state.thumb_url = None
    if 'chat_history' not in st.session_state: 
        st.session_state.chat_history = []
    if 'strategy_analysis' not in st.session_state:
        st.session_state.strategy_analysis = None
    if 'video_url' not in st.session_state:
        st.session_state.video_url = None

    # Analyze Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 ANALYZE VIDEO", type="primary"):
            if url:
                with st.spinner("🔍 Extracting video data..."):
                    transcript, title, thumb = get_transcript_data(url)
                    if transcript:
                        st.session_state.transcript = transcript
                        st.session_state.video_title = title
                        st.session_state.thumb_url = thumb
                        st.session_state.video_url = url
                        st.session_state.chat_history = []
                        st.session_state.strategy_analysis = None
                        st.success("✅ Data extracted successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to extract video data. Check the URL or subtitle availability.")
            else:
                st.warning("⚠️ Please enter a YouTube URL first")

    # Display Results
    if st.session_state.transcript:
        st.markdown("---")
        
        # Video Info Card
        col_img, col_info = st.columns([1, 2])
        with col_img:
            st.image(st.session_state.thumb_url, use_container_width=True)
        
        with col_info:
            st.markdown(f"### {st.session_state.video_title}")
            st.caption(f"📝 Transcript Length: {len(st.session_state.transcript):,} characters")
            st.caption(f"💬 Words: ~{len(st.session_state.transcript.split()):,}")
            st.caption(f"🌐 Output Language: **{output_language}**")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Analysis Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Strategy Report", 
            "👁️ Thumbnail Audit", 
            "💬 AI Chat", 
            "📝 Raw Transcript"
        ])
        
        with tab1:
            st.markdown("### 🎯 Content Strategy Analysis")
            st.markdown("Dapatkan insights strategis untuk meningkatkan performa video")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🔮 Generate Strategy Report", key="strategy_btn"):
                with st.spinner("🧠 Analyzing content strategy..."):
                    try:
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        response = model.generate_content(
                            get_strategy_prompt(output_language) + st.session_state.transcript[:30000]
                        )
                        st.session_state.strategy_analysis = response.text
                        st.markdown(response.text)
                        
                        # Save to database (NEW FEATURE #4)
                        save_to_database(
                            st.session_state.video_title,
                            st.session_state.video_url,
                            response.text[:500] + "...",  # Save summary
                            output_language,
                            "Single Analysis"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
            # PDF Download Button (NEW FEATURE #1)
            if st.session_state.strategy_analysis:
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("📥 Download PDF Report", key="pdf_btn"):
                        with st.spinner("📄 Generating PDF..."):
                            pdf_file = generate_pdf(
                                st.session_state.video_title,
                                st.session_state.strategy_analysis
                            )
                            if pdf_file:
                                with open(pdf_file, "rb") as f:
                                    st.download_button(
                                        label="⬇️ Download PDF",
                                        data=f,
                                        file_name=pdf_file,
                                        mime="application/pdf",
                                        use_container_width=True
                                    )
                                st.success("✅ PDF generated successfully!")
        
        with tab2:
            st.markdown("### 🎨 Thumbnail CTR Optimization")
            st.markdown("Analisis desain thumbnail untuk maksimalkan click-through rate")
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 1])
            with col1:
                st.image(st.session_state.thumb_url, use_container_width=True)
            
            with col2:
                if st.button("🔍 Audit Thumbnail", key="thumb_btn"):
                    with st.spinner("👁️ Analyzing visual elements..."):
                        try:
                            img = load_image_from_url(st.session_state.thumb_url)
                            if img:
                                model = genai.GenerativeModel('gemini-2.5-flash')
                                response = model.generate_content([THUMBNAIL_PROMPT, img])
                                st.markdown(response.text)
                            else:
                                st.error("❌ Failed to load thumbnail image")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

        with tab3:
            st.markdown("### 💬 Interactive AI Chat")
            st.markdown("Tanyakan apa saja tentang konten video ini")
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Display chat history
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            
            # Chat input
            if prompt := st.chat_input("Ask anything about this video..."):
                # User message
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # AI response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            model = genai.GenerativeModel('gemini-2.5-flash')
                            response = model.generate_content(
                                f"{LANGUAGE_INSTRUCTIONS[output_language]}\n\nContext:\n{st.session_state.transcript[:25000]}\n\nQuestion: {prompt}\n\nBerikan jawaban yang detail dan helpful."
                            )
                            st.markdown(response.text)
                            st.session_state.chat_history.append({
                                "role": "assistant", 
                                "content": response.text
                            })
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                    
        with tab4:
            st.markdown("### 📝 Full Transcript")
            st.text_area(
                "Raw transcript with timestamps", 
                st.session_state.transcript, 
                height=500,
                help="Transcript lengkap dengan timestamp"
            )

# --- MODE 2: COMPETITOR BATTLE ---
elif app_mode == "⚔️ Battle Mode":
    
    # Header
    st.markdown("# ⚔️ Competitive Battle Arena")
    st.markdown("Compare your video head-to-head with competitors")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Input URLs
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 🔵 Your Video")
        url_a = st.text_input(
            "Your YouTube URL:", 
            placeholder="https://youtube.com/watch?v=...",
            key="url_a"
        )
    
    with col_b:
        st.markdown("### 🔴 Competitor Video")
        url_b = st.text_input(
            "Competitor YouTube URL:", 
            placeholder="https://youtube.com/watch?v=...",
            key="url_b"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Battle Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("⚔️ START BATTLE", type="primary", key="battle_btn"):
            if url_a and url_b:
                status = st.status("🔄 Preparing battle arena...", expanded=True)
                
                # Extract Video A
                status.write("📥 Extracting Video A data...")
                trans_a, title_a, thumb_a = get_transcript_data(url_a)
                
                # Extract Video B
                status.write("📥 Extracting Video B data...")
                trans_b, title_b, thumb_b = get_transcript_data(url_b)
                
                if trans_a and trans_b:
                    status.write("🧠 Sending data to AI analyst...")
                    
                    st.markdown("---")
                    
                    # VS Visualization
                    col1, col2, col3 = st.columns([2, 1, 2])
                    
                    with col1:
                        st.markdown('<div class="video-card">', unsafe_allow_html=True)
                        if thumb_a: 
                            st.image(thumb_a, use_container_width=True)
                        st.markdown(f"**{title_a}**")
                        st.caption(f"📝 {len(trans_a):,} chars")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown('<div class="vs-badge">VS</div>', unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown('<div class="video-card">', unsafe_allow_html=True)
                        if thumb_b: 
                            st.image(thumb_b, use_container_width=True)
                        st.markdown(f"**{title_b}**")
                        st.caption(f"📝 {len(trans_b):,} chars")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # AI Analysis
                    input_prompt = f"""
                    {get_competitor_prompt(output_language)}
                    
                    === VIDEO A (YOUR VIDEO) ===
                    TITLE: {title_a}
                    TRANSCRIPT: {trans_a[:20000]} 
                    
                    === VIDEO B (COMPETITOR) ===
                    TITLE: {title_b}
                    TRANSCRIPT: {trans_b[:20000]}
                    """
                    
                    try:
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        response = model.generate_content(input_prompt)
                        
                        status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
                        
                        st.markdown("---")
                        st.markdown("## 📊 Battle Analysis Report")
                        st.markdown(response.text)
                        
                        # Save to database
                        save_to_database(
                            f"{title_a} VS {title_b}",
                            f"{url_a} | {url_b}",
                            response.text[:500] + "...",
                            output_language,
                            "Battle Mode"
                        )
                        
                    except Exception as e:
                        status.update(label="❌ AI Error", state="error")
                        st.error(f"Error: {str(e)}")
                else:
                    status.update(label="❌ Extraction Failed", state="error")
                    st.error("Failed to extract transcript from one or both videos. Check URLs and subtitle availability.")
            else:
                st.warning("⚠️ Please enter both YouTube URLs to start the battle!")

# --- MODE 3: PROMPT BATTLE (NEW FEATURE #3) ---
elif app_mode == "⚖️ Prompt Battle":
    
    st.markdown("# ⚖️ Prompt Battle: A/B Testing Mode")
    st.markdown("Compare two different AI persona analyses side-by-side")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Input URL
    battle_url = st.text_input(
        "🔗 YouTube URL:", 
        placeholder="https://youtube.com/watch?v=...",
        help="Enter one video URL to analyze with two different AI perspectives",
        key="battle_url"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Battle Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("⚡ START PROMPT BATTLE", type="primary", key="prompt_battle_btn"):
            if battle_url:
                with st.spinner("🔍 Extracting video data..."):
                    transcript, title, thumb = get_transcript_data(battle_url)
                    
                    if transcript:
                        st.markdown("---")
                        
                        # Video Info
                        col_img, col_info = st.columns([1, 3])
                        with col_img:
                            if thumb:
                                st.image(thumb, use_container_width=True)
                        with col_info:
                            st.markdown(f"### {title}")
                            st.caption(f"📝 {len(transcript):,} characters | 💬 ~{len(transcript.split()):,} words")
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("## 🤖 Dual AI Persona Analysis")
                        st.markdown("---")
                        
                        # Two columns for parallel analysis
                        col_corporate, col_genz = st.columns(2)
                        
                        # LEFT: Corporate Consultant
                        with col_corporate:
                            st.markdown('<div class="battle-column">', unsafe_allow_html=True)
                            st.markdown("### 💼 Corporate Consultant")
                            st.caption("Formal, ROI-focused, Enterprise perspective")
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            with st.spinner("🤵 Corporate analysis in progress..."):
                                try:
                                    model = genai.GenerativeModel('gemini-2.5-flash')
                                    corporate_response = model.generate_content(
                                        get_corporate_prompt(output_language) + transcript[:25000]
                                    )
                                    st.markdown(corporate_response.text)
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # RIGHT: Gen-Z Expert
                        with col_genz:
                            st.markdown('<div class="battle-column">', unsafe_allow_html=True)
                            st.markdown("### 🔥 Viral Gen-Z Expert")
                            st.caption("Trendy, Hook-focused, Social media optimized")
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            with st.spinner("😎 Gen-Z analysis in progress..."):
                                try:
                                    model = genai.GenerativeModel('gemini-2.5-flash')
                                    genz_response = model.generate_content(
                                        get_genz_prompt(output_language) + transcript[:25000]
                                    )
                                    st.markdown(genz_response.text)
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Save to database
                        save_to_database(
                            title,
                            battle_url,
                            "Prompt Battle: Corporate vs Gen-Z analysis completed",
                            output_language,
                            "Prompt Battle"
                        )
                        
                    else:
                        st.error("❌ Failed to extract video data. Check the URL or subtitle availability.")
            else:
                st.warning("⚠️ Please enter a YouTube URL first")

# --- MODE 4: HISTORY DATABASE (NEW FEATURE #4) ---
elif app_mode == "🗄️ History Database":
    
    st.markdown("# 🗄️ Analysis History Database")
    st.markdown("View and export all your previous analysis results")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Load history
    df = load_history()
    
    if not df.empty:
        st.markdown(f"### 📊 Total Records: {len(df)}")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Display dataframe
        st.dataframe(
            df,
            use_container_width=True,
            height=500,
            column_config={
                "id": "ID",
                "date": "Date",
                "video_title": "Video Title",
                "video_url": "URL",
                "summary": "Summary",
                "language": "Language",
                "mode": "Mode"
            }
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Export to CSV
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Export to CSV",
                data=csv,
                file_name=f"vye_history_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Statistics
        st.markdown("---")
        st.markdown("### 📈 Quick Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Analyses", len(df))
        
        with col2:
            if 'language' in df.columns:
                most_common_lang = df['language'].mode()[0] if not df['language'].mode().empty else "N/A"
                st.metric("Most Used Language", most_common_lang)
        
        with col3:
            if 'mode' in df.columns:
                most_common_mode = df['mode'].mode()[0] if not df['mode'].mode().empty else "N/A"
                st.metric("Most Used Mode", most_common_mode)
        
        with col4:
            if 'date' in df.columns:
                latest_date = df['date'].max()
                st.metric("Latest Analysis", latest_date[:10] if latest_date else "N/A")
        
        # Language distribution
        if 'language' in df.columns:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 🌐 Language Distribution")
            lang_counts = df['language'].value_counts()
            st.bar_chart(lang_counts)
        
        # Clear history option
        st.markdown("<br>" * 2, unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🗑️ Clear All History", key="clear_history"):
            if st.button("⚠️ Confirm Delete", key="confirm_clear"):
                try:
                    conn = sqlite3.connect('vye_history.db')
                    c = conn.cursor()
                    c.execute("DELETE FROM analysis_history")
                    conn.commit()
                    conn.close()
                    st.success("✅ History cleared successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    else:
        st.info("📭 No analysis history found yet. Start analyzing videos to build your database!")

# --- MODE 5: CHANNEL BRAIN (RAG MODE) ---
elif app_mode == "🧠 Channel Brain":
    st.header("🧠 Channel Brain (RAG Mode)")
    st.markdown("Tanya apa saja berdasarkan database video yang sudah dipelajari.")
    
    if "rag_chat_history" not in st.session_state:
        st.session_state.rag_chat_history = []

    dynamic_options = get_unique_channels()
    selected_channel = st.selectbox("Pilih Channel:", dynamic_options)

    # Tampilkan History Visual
    for message in st.session_state.rag_chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if query := st.chat_input(f"Tanya soal {selected_channel}..."):
        st.session_state.rag_chat_history.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
            
        with st.chat_message("assistant"):
            with st.spinner("Membongkar arsip video dan mengingat percakapan..."):
                # 1. Retrieval: Cari potongan transkrip relevan
                context_chunks = search_channel_brain(query, selected_channel)
                
                # 2. Memory: Ambil 5 pesan terakhir sebagai memori jangka pendek
                # Ini agar AI tahu apa yang sedang dibicarakan sebelumnya
                history_memory = "\n".join([
                    f"{m['role'].upper()}: {m['content']}" 
                    for m in st.session_state.rag_chat_history[-5:-1]
                ])
                
                if context_chunks:
                    context_text = "\n\n".join([f"Dikutip dari video '{c['video_title']}':\n{c['content']}" for c in context_chunks])
                    
                    client_genai = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
                    
                    # PROMPT DENGAN MEMORI 
                    prompt = f"""
                    Kamu adalah asisten ahli yang menjawab berdasarkan database video YouTube.
                    Gunakan DATA CONTEKAN di bawah untuk menjawab pertanyaan user.
                    Gunakan RIWAYAT PERCAKAPAN untuk memahami konteks.
                    
                    INSTRUKSI GAYA BAHASA:
                    1. Jawablah dengan gaya narasi yang mengalir dan natural (seperti manusia berbicara).
                    2. JANGAN menyertakan timestamp [menit:detik] di dalam teks jawaban utama agar mudah dibaca.
                    3. Rangkum poin-poin penting menjadi paragraf yang utuh.

                    RIWAYAT PERCAKAPAN SEBELUMNYA:
                    {history_memory}
                    
                    DATA CONTEKAN DARI VIDEO:
                    {context_text}
                    
                    PERTANYAAN TERBARU USER:
                    {query}
                    
                    Jawaban:
                    """
                    
                    try:
                        response = client_genai.models.generate_content(
                            model="gemini-2.5-flash", 
                            contents=prompt
                        )
                        full_response = response.text
                        st.markdown(full_response)
                        
                        st.session_state.rag_chat_history.append({"role": "assistant", "content": full_response})
                        
                        with st.expander("📌 Sumber Video Terkait"):
                            for c in context_chunks:
                                st.write(f"- [{c['video_title']}]({c['video_url']}) (Skor: {round(c['similarity'], 2)})")
                    except Exception as e:
                        st.error(f"Gagal generate jawaban: {e}")
                else:
                    st.warning("Maaf, saya tidak menemukan informasi yang relevan di database video.")

# --- FOOTER ---
st.markdown("<br>" * 3, unsafe_allow_html=True)
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>Made with ⚡ by Vye | Powered by Gemini AI</div>", 
    unsafe_allow_html=True
)