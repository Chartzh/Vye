import streamlit as st
from google import genai
from google.genai import types
import re
import time
import yt_dlp
import os
import glob
import requests
from PIL import Image
from io import BytesIO
from supabase import create_client

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Vye - AI Content Intelligence",
    page_icon="images/logo_favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (TEMA VYE FIXED) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');
    
    /* === GLOBAL STYLING === */
    * { font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, h5, h6 { font-family: 'Space Grotesk', sans-serif; font-weight: 700; }
    
    /* === FIX BACKGROUND (FULL GRADIENT TEMBUS BAWAH) === */
    .stApp { background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1729 100%) !important; }
    .main, .block-container, [data-testid="stHeader"] { background: transparent !important; }
    
    /* === EFEK MEMUDAR (FADE-OUT) DI KOLOM INPUT BAWAH === */
    [data-testid="stBottom"] { 
        /* Membuat gradien kabut dari transparan ke warna background paling bawah (#0f1729) */
        background: linear-gradient(180deg, transparent 0%, rgba(15, 23, 41, 0.85) 35%, rgba(15, 23, 41, 1) 100%) !important; 
        padding-top: 70px !important; /* Jarak efek kabut sebelum menyentuh kotak input */
        z-index: 99 !important;
    }
    [data-testid="stBottom"] > div { background: transparent !important; }
    
   /* === CHAT BUBBLE KANAN-KIRI === */
    .stChatMessage {
        background-color: transparent !important;
        border: none !important;
        margin-bottom: 1.5rem !important;
    }
    
    /* USER CHAT (KANAN) */
    div[data-testid="stChatMessage"]:has(.user-bubble) {
        display: flex !important;
        flex-direction: row-reverse !important;
    }
    div[data-testid="stChatMessage"]:has(.user-bubble) > div:nth-child(2) {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border-radius: 18px 18px 4px 18px !important;
        padding: 12px 18px !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
        
        margin-left: auto !important;  /* Ambil sisa ruang kosong di kiri, dorong kotak ke kanan */
        margin-right: 15px !important; /* Kasih jarak dikit biar gak nabrak muka avatar */
        
        width: fit-content !important;
        max-width: 75% !important;
        flex-grow: 0 !important;
    }
    
    div[data-testid="stChatMessage"]:has(.user-bubble) div[data-testid="stMarkdownContainer"] {
        padding: 0 !important; margin: 0 !important;
    }
    
    div[data-testid="stChatMessage"]:has(.user-bubble) p {
        margin: 0 !important; 
        font-family: 'Inter', sans-serif !important; 
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        line-height: 1.5 !important;
    }
    
    /* AI CHAT (KIRI) */
    div[data-testid="stChatMessage"]:has(.bot-bubble) {
        display: flex !important;
        flex-direction: row !important;
    }
    div[data-testid="stChatMessage"]:has(.bot-bubble) > div:nth-child(2) {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(102, 126, 234, 0.2) !important;
        border-radius: 18px 18px 18px 4px !important;
        padding: 12px 18px !important;
        color: #e2e8f0 !important;
        backdrop-filter: blur(10px) !important;
        
        margin-right: auto !important; /* Ambil sisa ruang kosong di kanan, dorong kotak ke kiri */
        margin-left: 15px !important;  /* Kasih jarak dari muka bot */
        
        width: fit-content !important;
        max-width: 85% !important;
        flex-grow: 0 !important;
    }
    
    div[data-testid="stChatMessage"]:has(.bot-bubble) div[data-testid="stMarkdownContainer"] {
        padding: 0 !important; margin: 0 !important;
    }
    
    div[data-testid="stChatMessage"]:has(.bot-bubble) p {
        margin: 0 0 10px 0 !important;
        line-height: 1.6 !important;
    }
    div[data-testid="stChatMessage"]:has(.bot-bubble) p:last-child {
        margin-bottom: 0 !important; 
    }
    
    /* === TIMESTAMP LINKS === */
    a.timestamp-link {
        color: #a78bfa !important; font-weight: 600 !important; text-decoration: none !important;
        background: rgba(167, 139, 250, 0.15) !important; padding: 3px 8px !important;
        border-radius: 6px !important; transition: all 0.3s ease !important;
        border: 1px solid rgba(167, 139, 250, 0.3) !important; display: inline-block !important;
    }
    a.timestamp-link:hover { background: rgba(167, 139, 250, 0.3) !important; transform: translateY(-2px) !important; }
    
    /* === SIDEBAR & UI LAINNYA === */
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 50%, #1e293b 100%) !important; border-right: 2px solid rgba(102, 126, 234, 0.3) !important; }
    [data-testid="stSidebar"] h1 { background: linear-gradient(135deg, #667eea 0%, #a78bfa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    [data-testid="stSidebar"] label { color: #cbd5e1 !important; font-weight: 500 !important; }
    .stButton > button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; color: white !important; border: none !important; border-radius: 10px !important; padding: 12px 24px !important; font-weight: 600 !important; transition: all 0.3s ease !important; }
    .stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important; }
    .stButton > button[kind="primary"] { background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%) !important; }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea, [data-testid="stChatInput"] { background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(102, 126, 234, 0.3) !important; border-radius: 10px !important; color: white !important; }
    .stTabs [data-baseweb="tab-list"] { background: rgba(255, 255, 255, 0.02); border-radius: 12px; padding: 4px; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white !important; }
    .streamlit-expanderHeader { background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(102, 126, 234, 0.2) !important; border-radius: 10px !important; color: #cbd5e1 !important; }
    .vs-badge { font-size: 2.5rem; font-weight: 900; background: linear-gradient(135deg, #ef4444 0%, #f59e0b 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; width: 80px; height: 80px; display: flex; align-items: center; justify-content: center; margin: 0 auto; border: 3px solid rgba(239, 68, 68, 0.3); border-radius: 50%; background-color: rgba(239, 68, 68, 0.1); animation: pulse 2s infinite; }
    @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
</style>
""", unsafe_allow_html=True)

# --- SETUP CLIENT ---
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except: return None

# --- PROMPTS ---
STRATEGY_PROMPT = """
Kamu adalah Expert YouTube Strategist yang teliti. Analisis transkrip ini.

⚠️ PENTING: DETEKSI SARKASME & KONTEKS
- Perhatikan nada bicara dan konteks percakapan.
- Bedakan antara pernyataan serius, fakta, atau SARKASME/CANDAAN.
- Jika ada pernyataan yang terdengar mustahil atau bernada menyindir (misal: "mau jadi presiden mars"), tandai itu sebagai gurauan, bukan fakta.

OUTPUT YANG DIMINTA:
## 📊 Executive Summary
Berikan 3 poin utama yang paling menonjol dari video ini.

## 🔥 Virality Score
Berikan skor 0-100 dengan breakdown alasan mengapa video ini berpotensi viral atau tidak.

## ✂️ Clip Ideas (Shorts/TikTok)
Identifikasi 3-5 momen terbaik.
WAJIB: Sertakan timestamp spesifik [MM:SS] di setiap ide agar bisa diklik.

## 💡 Content Gaps
Apa yang kurang dari video ini? Apa yang bisa ditambahkan agar lebih lengkap?

TRANSKRIP:
"""

THUMBNAIL_PROMPT = """
Analisis thumbnail ini sebagai Expert Desainer:
1. **CTR Score (0-10)**
2. **Visual Hierarchy**
3. **Emotional Trigger**
Berikan 3 saran perbaikan konkret.
"""

# --- FUNGSI HELPER ---
@st.cache_data(ttl=60)
def get_unique_channels():
    supabase = init_supabase()
    try:
        response = supabase.table("channel_knowledge").select("channel_name").execute()
        if response.data:
            unique_names = sorted(list(set([row['channel_name'] for row in response.data])))
            return ["Semua Channel"] + unique_names
        return ["Semua Channel"]
    except: return ["Semua Channel"]

def load_image_from_url(url):
    try:
        response = requests.get(url)
        return Image.open(BytesIO(response.content))
    except: return None

def get_transcript_direct(video_url):
    ydl_opts = {
        'skip_download': True, 'writesubtitles': True, 'writeautomaticsub': True,
        'subtitleslangs': ['id', 'en.*'], 'outtmpl': 'temp_single_%(id)s',
        'quiet': True, 'no_warnings': True, 'ignoreerrors': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            if not info: return None, None, None
            
            vid_id = info.get('id')
            title = info.get('title')
            thumb = info.get('thumbnail') 
            if info.get('thumbnails'): thumb = info['thumbnails'][-1]['url']
            
            sub_files = glob.glob(f"temp_single_{vid_id}*")
            if not sub_files: return None, title, thumb
            
            final_text = []
            with open(sub_files[0], 'r', encoding='utf-8') as f:
                lines = f.readlines()
                current_ts = ""
                for line in lines:
                    line = line.strip()
                    if "-->" in line:
                        t = line.split("-->")[0].strip()
                        try:
                            p = t.split(":")
                            if len(p)==3: mins = int(p[1]) + (int(p[0])*60); secs=int(float(p[2]))
                            elif len(p)==2: mins = int(p[0]); secs=int(float(p[1]))
                            current_ts = f"[{mins:02d}:{secs:02d}]"
                        except: continue
                    elif line and "WEBVTT" not in line and not line.isdigit():
                        if current_ts: final_text.append(f"{current_ts} {line}"); current_ts=""
            
            for f in sub_files: os.remove(f)
            return "\n".join(final_text), title, thumb
    except Exception as e: return None, None, None

def search_channel_brain(query, channel, match_count=6):
    client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    supabase = init_supabase()
    try:
        res = client.models.embed_content(
            model="gemini-embedding-001", contents=query,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )
        vec = res.embeddings[0].values
        rpc = 'match_documents_all' if channel == "Semua Channel" else 'match_documents'
        params = {'query_embedding': vec, 'match_threshold': 0.1, 'match_count': match_count}
        if channel != "Semua Channel": params['filter_channel'] = channel
        resp = supabase.rpc(rpc, params).execute()
        return resp.data if resp.data else []
    except: return []

def make_timestamps_clickable(text, url):
    if not url: return text
    def rep(m):
        ts = m.group(1)
        try:
            p = ts.split(":")
            if len(p)==3: total = (int(p[0])*3600) + (int(p[1])*60) + int(p[2])
            elif len(p)==2: total = (int(p[0])*60) + int(p[1])
            else: return m.group(0)
            return f'<a href="{url}&t={total}s" target="_blank" class="timestamp-link">⏱️ {ts}</a>'
        except: return m.group(0)
    return re.sub(r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]', rep, text)

# --- SESSION STATE PERSISTENCE ---
if "rag_msgs" not in st.session_state: st.session_state.rag_msgs = []
if "deep_data" not in st.session_state: st.session_state.deep_data = None
if "deep_analysis_result" not in st.session_state: st.session_state.deep_analysis_result = None 
if "competitor_result" not in st.session_state: st.session_state.competitor_result = None

# --- NAVIGASI ---
with st.sidebar:
    st.image("images/logo.png", use_container_width=True)
    
    st.markdown("---")
    app_mode = st.radio("Pilih Mode:", ["🧠 Channel Brain", "📊 Deep Video Intelligence", "⚔️ Competitor Arena"])
    st.markdown("---")

    if app_mode == "🧠 Channel Brain":
        selected_channel = st.selectbox("📚 Knowledge Base:", get_unique_channels())


# --- MODE 1: CHANNEL BRAIN (RAG) ---
if app_mode == "🧠 Channel Brain":
    st.markdown(f"### 💬 Chat dengan {selected_channel}")
    st.caption("Tanyakan apa saja tentang konten channel yang sudah diingat oleh Vye")

    # 1. LOOP HISTORI (SEKARANG BISA BACA SUMBER)
    for m in st.session_state.rag_msgs:
        with st.chat_message(m["role"]): 
            marker = "<div class='user-bubble'></div>" if m["role"] == "user" else "<div class='bot-bubble'></div>"
            st.markdown(marker + m["content"], unsafe_allow_html=True)
            
            # Tampilkan expander sumber jika ada di memori
            if m.get("sources"):
                with st.expander("📌 Sumber & Bukti"):
                    for c in m["sources"]:
                        link = make_timestamps_clickable(c['content'], c['video_url'])
                        st.markdown(f"**📺 {c['video_title']}**")
                        st.markdown(f"<div style='font-size:0.9em;color:#94a3b8;border-left:3px solid #667eea;padding-left:15px;margin:10px 0;'>...{link}...</div>", unsafe_allow_html=True)

    # 2. PROSES INPUT BARU
    if q := st.chat_input("Tanya sesuatu..."):
        st.session_state.rag_msgs.append({"role": "user", "content": q})
        with st.chat_message("user"): 
            st.markdown(f"<div class='user-bubble'></div>{q}", unsafe_allow_html=True)
        
        with st.chat_message("assistant"):
            with st.spinner("🧠 Mengakses memori..."):
                ctx = search_channel_brain(q, selected_channel)
                ctx_txt = "".join([f"Video: {c['video_title']}\nContent: {c['content']}\n\n" for c in ctx])
                hist = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.rag_msgs[-4:]])
                
                prompt = f"""
                Kamu adalah Vye. Jawab pertanyaan user berdasarkan DATA CONTEKAN.
                ATURAN PENTING:
                1. Gaya bahasa natural & luwes.
                2. JANGAN tulis timestamp di teks jawaban utama.
                3. HATI-HATI SARKASME.

                ATURAN KETAT:
                1. Jika jawaban TIDAK ADA di dalam DATA CONTEKAN, katakan: "Maaf, Bang David gak ada bahas spesifik soal itu di video-video yang gue inget sekarang."
                2. JANGAN PERNAH mengarang informasi dari pengetahuan umum kamu sendiri.
                
                RIWAYAT: {hist}
                CONTEKAN: {ctx_txt}
                PERTANYAAN: {q}
                """
                client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
                res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                
                # Tampilkan AI reply dengan MARKER
                st.markdown(f"<div class='bot-bubble'></div>{res.text}", unsafe_allow_html=True)
                
                # SIMPAN KE MEMORI (SEKARANG SUMBERNYA IKUT DISIMPAN)
                st.session_state.rag_msgs.append({
                    "role": "assistant", 
                    "content": res.text,
                    "sources": ctx  # <--- INI KUNCI UTAMANYA!
                })
                
                if ctx:
                    with st.expander("📌 Sumber & Bukti"):
                        for c in ctx:
                            link = make_timestamps_clickable(c['content'], c['video_url'])
                            st.markdown(f"**📺 {c['video_title']}**")
                            st.markdown(f"<div style='font-size:0.9em;color:#94a3b8;border-left:3px solid #667eea;padding-left:15px;margin:10px 0;'>...{link}...</div>", unsafe_allow_html=True)

# --- MODE 2 & 3 TETAP SAMA SEPERTI SEBELUMNYA ---
elif app_mode == "📊 Deep Video Intelligence":
    st.markdown("# 📊 Deep Video Intelligence")
    st.caption("Analisis komprehensif: Strategi, Virality Score, dan Thumbnail Audit.")
    
    default_url = st.session_state.deep_data['url'] if st.session_state.deep_data else ""
    url = st.text_input("🔗 YouTube URL", value=default_url, placeholder="https://youtube.com/watch?v=...")
    
    if st.button("🚀 Run Deep Analysis", type="primary"):
        if url:
            with st.spinner("Extracting data..."):
                trans, title, thumb = get_transcript_direct(url)
                if trans:
                    st.session_state.deep_data = {"trans": trans, "title": title, "thumb": thumb, "url": url}
                    st.session_state.deep_analysis_result = None 
                    st.rerun()
                else: st.error("Gagal ambil data video.")

    if st.session_state.deep_data:
        d = st.session_state.deep_data
        col1, col2 = st.columns([1, 2])
        with col1: st.image(d['thumb'], use_container_width=True)
        with col2:
            st.markdown(f"### {d['title']}")
            st.caption(f"🔗 [Buka Video]({d['url']})")
        
        st.markdown("---")
        tab1, tab2, tab3 = st.tabs(["📑 Strategy Report", "👁️ Thumbnail Audit", "💬 Chat"])
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
        
        with tab1:
            if st.session_state.deep_analysis_result:
                st.markdown(st.session_state.deep_analysis_result, unsafe_allow_html=True)
                if st.button("🔄 Regenerate Report"): 
                    st.session_state.deep_analysis_result = None
                    st.rerun()
            else:
                if st.button("✨ Generate Strategy Report"):
                    with st.spinner("Analyzing strategy..."):
                        prompt = STRATEGY_PROMPT + d['trans'][:30000]
                        res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                        final_html = make_timestamps_clickable(res.text, d['url'])
                        st.session_state.deep_analysis_result = final_html
                        st.rerun()
        
        with tab2:
            if st.button("🔍 Audit Thumbnail"):
                with st.spinner("Scanning visuals..."):
                    img = load_image_from_url(d['thumb'])
                    if img:
                        res = client.models.generate_content(model="gemini-2.5-flash", contents=[img, THUMBNAIL_PROMPT])
                        st.markdown(res.text)
        
        with tab3:
            st.markdown("#### 💬 Tanya tentang video ini")
            q = st.text_input("Ketik pertanyaan Anda:")
            if q:
                with st.spinner("🧠 Berpikir..."):
                    prompt = f"Jawab berdasarkan transkrip ini:\n{d['trans'][:20000]}\n\nPertanyaan: {q}"
                    res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                    linked_res = make_timestamps_clickable(res.text, d['url'])
                    st.markdown("---")
                    st.markdown(linked_res, unsafe_allow_html=True)

elif app_mode == "⚔️ Competitor Arena":
    st.markdown("# ⚔️ Competitor Arena")
    st.caption("Bandingkan dua video head-to-head dan dapatkan strategic insights")
    
    col1, col_vs, col2 = st.columns([5, 1, 5])
    with col1:
        st.markdown("#### 🔵 Video Kita")
        url_a = st.text_input("URL Video Kita", placeholder="https://youtube.com/watch?v=...", label_visibility="collapsed")
    with col_vs: st.markdown("<div class='vs-badge'>VS</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("#### 🔴 Video Kompetitor")
        url_b = st.text_input("URL Video Kompetitor", placeholder="https://youtube.com/watch?v=...", label_visibility="collapsed")
    
    if "battle_res" not in st.session_state: st.session_state.battle_res = None

    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("⚔️ START BATTLE!", type="primary", use_container_width=True):
            if url_a and url_b:
                with st.spinner("⚡ Analyzing both videos..."):
                    ta, title_a, _ = get_transcript_direct(url_a)
                    tb, title_b, _ = get_transcript_direct(url_b)
                    
                    if ta and tb:
                        prompt = f"""
                        Lakukan analisis perbandingan:
                        A: {title_a} ({ta[:15000]})
                        B: {title_b} ({tb[:15000]})
                        
                        TUGAS: Siapa pemenang, kelebihan, kekurangan, dan strategi.
                        """
                        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
                        res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                        st.session_state.battle_res = f"### 🏆 Hasil: {title_a} vs {title_b}\n\n{res.text}"
                        st.rerun()
                    else: st.error("Gagal mengambil data.")
            else: st.warning("Mohon isi kedua URL video!")

    if st.session_state.battle_res:
        st.markdown("---")
        st.markdown(st.session_state.battle_res)