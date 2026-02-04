import streamlit as st
import google.generativeai as genai
import yt_dlp
import os
import glob
import requests
from PIL import Image
from io import BytesIO

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
</style>
""", unsafe_allow_html=True)

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
    
    genai.configure(api_key=api_key)
    
    st.markdown("---")
    
    # MODE SELECTOR
    app_mode = st.radio(
        "🎯 Select Mode:", 
        ["📊 Single Analysis", "⚔️ Battle Mode"],
        help="Pilih mode analisis sesuai kebutuhan"
    )
    
    st.markdown("---")
    
    # Info Box
    st.info(f"🔥 Active: **{app_mode}**")
    
    st.markdown("<br>" * 3, unsafe_allow_html=True)
    st.caption("Powered by Gemini AI")

# --- PROMPTS ---

STRATEGY_PROMPT = """
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

COMPETITOR_PROMPT = """
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
                        st.session_state.chat_history = []
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
                            STRATEGY_PROMPT + st.session_state.transcript[:30000]
                        )
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
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
                                f"Context:\n{st.session_state.transcript[:25000]}\n\nQuestion: {prompt}\n\nBerikan jawaban yang detail dan helpful."
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
                    {COMPETITOR_PROMPT}
                    
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
                        
                    except Exception as e:
                        status.update(label="❌ AI Error", state="error")
                        st.error(f"Error: {str(e)}")
                else:
                    status.update(label="❌ Extraction Failed", state="error")
                    st.error("Failed to extract transcript from one or both videos. Check URLs and subtitle availability.")
            else:
                st.warning("⚠️ Please enter both YouTube URLs to start the battle!")

# --- FOOTER ---
st.markdown("<br>" * 3, unsafe_allow_html=True)
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>Made with ⚡ by Vye | Powered by Gemini AI</div>", 
    unsafe_allow_html=True
)