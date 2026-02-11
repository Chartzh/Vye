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
    page_title="Vye",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (UI CHAT KANAN-KIRI) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    
    /* USER CHAT (KANAN) */
    [data-testid="stChatMessage"][aria-label="user"] {
        flex-direction: row-reverse; /* Avatar di kanan */
        background-color: rgba(0, 100, 255, 0.1); /* Biru tipis */
        border-radius: 15px;
        text-align: right;
    }
    
    /* BOT CHAT (KIRI) */
    [data-testid="stChatMessage"][aria-label="assistant"] {
        background-color: rgba(255, 255, 255, 0.05); /* Abu transparan */
        border-radius: 15px;
    }

    /* Timestamp Link Styling */
    a.timestamp-link {
        color: #00d9ff !important;
        font-weight: bold;
        text-decoration: none;
        background: rgba(0, 217, 255, 0.1);
        padding: 2px 6px;
        border-radius: 4px;
        transition: all 0.2s;
    }
    a.timestamp-link:hover { background: rgba(0, 217, 255, 0.3); }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .vs-badge {
        font-size: 2rem; font-weight: 900; color: #ff4b4b; text-align: center;
        background: rgba(255, 75, 75, 0.1); border-radius: 50%; width: 60px; height: 60px;
        display: flex; align-items: center; justify-content: center; margin: 0 auto;
    }
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
# Update Prompt: Deteksi Sarkasme
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

# --- LINK GENERATOR (REGEX) ---
def make_timestamps_clickable(text, url):
    """Mengubah [MM:SS] jadi Link, tapi cek dulu url-nya valid"""
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
        
    # Regex support [MM:SS] dan [H:MM:SS]
    return re.sub(r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]', rep, text)

# --- SESSION STATE PERSISTENCE ---
# Inisialisasi variabel agar tidak hilang saat refresh/ganti tab
if "rag_msgs" not in st.session_state: st.session_state.rag_msgs = []
if "deep_data" not in st.session_state: st.session_state.deep_data = None
if "deep_analysis_result" not in st.session_state: st.session_state.deep_analysis_result = None # Simpan hasil analisa deep
if "competitor_result" not in st.session_state: st.session_state.competitor_result = None

# --- NAVIGASI ---
with st.sidebar:
    st.header("🧠 Vye Brain")
    app_mode = st.radio(
        "Pilih Mode:",
        ["🧠 Channel Brain", "📊 Deep Video Intelligence", "⚔️ Competitor Arena"],
    )
    st.markdown("---")

    if app_mode == "🧠 Channel Brain":
        selected_channel = st.selectbox("📚 Knowledge Base:", get_unique_channels())
        with st.expander("➕ Feed the Brain"):
            url = st.text_input("URL"); name = st.text_input("Name")
            if st.button("Ingest"):
                import ingest_channel
                c = ingest_channel.process_channel(url, name)
                if c: st.success(f"{c} added!"); time.sleep(1); st.rerun()

# --- MODE 1: CHANNEL BRAIN (RAG) ---
if app_mode == "🧠 Channel Brain":
    st.subheader(f"💬 Chat: {selected_channel}")

    for m in st.session_state.rag_msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if q := st.chat_input("Tanya sesuatu..."):
        st.session_state.rag_msgs.append({"role": "user", "content": q})
        with st.chat_message("user"): st.markdown(q)
        
        with st.chat_message("assistant"):
            with st.spinner("🧠 Mengakses memori..."):
                ctx = search_channel_brain(q, selected_channel)
                ctx_txt = "".join([f"Video: {c['video_title']}\nContent: {c['content']}\n\n" for c in ctx])
                hist = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.rag_msgs[-4:]])
                
                # UPDATE PROMPT SARKASME
                prompt = f"""
                Kamu adalah Vye. Jawab pertanyaan user berdasarkan DATA CONTEKAN.
                
                ATURAN PENTING:
                1. Gaya bahasa natural & luwes.
                2. JANGAN tulis timestamp di teks jawaban utama.
                3. HATI-HATI SARKASME: Jika di transkrip ada kalimat yang terdengar bercanda/mustahil (misal: "mau pindah ke Mars besok"), anggap itu sbg gurauan/sarkas, BUKAN fakta serius.
                
                RIWAYAT: {hist}
                CONTEKAN: {ctx_txt}
                PERTANYAAN: {q}
                """
                client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
                res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                
                st.markdown(res.text)
                st.session_state.rag_msgs.append({"role": "assistant", "content": res.text})
                
                if ctx:
                    with st.expander("📌 Sumber & Bukti"):
                        for c in ctx:
                            link = make_timestamps_clickable(c['content'], c['video_url'])
                            st.markdown(f"**📺 {c['video_title']}**")
                            st.markdown(f"<div style='font-size:0.9em;color:#ccc;border-left:2px solid #333;padding-left:10px;'>...{link}...</div>", unsafe_allow_html=True)

# --- MODE 2: DEEP VIDEO INTELLIGENCE (PERSISTENT) ---
elif app_mode == "📊 Deep Video Intelligence":
    st.header("📊 Deep Video Intelligence")
    st.caption("Analisis komprehensif: Strategi, Virality Score, dan Thumbnail Audit.")
    
    # Input URL (Default value dari session state kalau ada)
    default_url = st.session_state.deep_data['url'] if st.session_state.deep_data else ""
    url = st.text_input("🔗 YouTube URL", value=default_url, placeholder="https://youtube.com/watch?v=...")
    
    if st.button("🚀 Run Deep Analysis", type="primary"):
        if url:
            with st.spinner("Extracting data..."):
                trans, title, thumb = get_transcript_direct(url)
                if trans:
                    # Simpan ke session state biar gak ilang
                    st.session_state.deep_data = {"trans": trans, "title": title, "thumb": thumb, "url": url}
                    st.session_state.deep_analysis_result = None # Reset hasil analisa lama
                    st.rerun()
                else: st.error("Gagal ambil data video.")

    # Tampilkan Data jika ada di memory
    if st.session_state.deep_data:
        d = st.session_state.deep_data
        st.image(d['thumb'], width=400)
        st.subheader(d['title'])
        
        tab1, tab2, tab3 = st.tabs(["📑 Strategy Report", "👁️ Thumbnail Audit", "💬 Chat"])
        
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
        
        with tab1:
            # Tombol generate (Cek session state dulu)
            if st.session_state.deep_analysis_result:
                # Kalau sudah ada hasil, langsung tampilkan (biar gak generate ulang pas pindah tab)
                st.markdown(st.session_state.deep_analysis_result, unsafe_allow_html=True)
                if st.button("Regenerate Report"): # Opsi buat generate ulang
                    st.session_state.deep_analysis_result = None
                    st.rerun()
            else:
                if st.button("Generate Strategy Report"):
                    with st.spinner("Analyzing strategy..."):
                        prompt = STRATEGY_PROMPT + d['trans'][:30000]
                        res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                        
                        # PROSES LINK TIMESTAMP DI SINI
                        # Ubah teks biasa jadi link yang bisa diklik
                        final_html = make_timestamps_clickable(res.text, d['url'])
                        
                        # Simpan hasil yang sudah ada link-nya ke session state
                        st.session_state.deep_analysis_result = final_html
                        st.rerun()
        
        with tab2:
            if st.button("Audit Thumbnail"):
                with st.spinner("Scanning visuals..."):
                    img = load_image_from_url(d['thumb'])
                    if img:
                        res = client.models.generate_content(model="gemini-2.5-flash", contents=[img, THUMBNAIL_PROMPT])
                        st.markdown(res.text)
        
        with tab3:
            q = st.text_input("Tanya video ini:")
            if q:
                # Chat juga dikasih clickable timestamp
                prompt = f"Jawab berdasarkan transkrip ini:\n{d['trans'][:20000]}\n\nPertanyaan: {q}"
                res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                linked_res = make_timestamps_clickable(res.text, d['url'])
                st.markdown(linked_res, unsafe_allow_html=True)

# --- MODE 3: COMPETITOR ARENA (BATTLE MODE) ---
elif app_mode == "⚔️ Competitor Arena":
    st.header("⚔️ Competitor Arena")
    
    col1, col2 = st.columns(2)
    with col1: url_a = st.text_input("🔵 Video Kita (URL)")
    with col2: url_b = st.text_input("🔴 Video Kompetitor (URL)")
    
    # Gunakan session state untuk hasil battle juga
    if "battle_res" not in st.session_state: st.session_state.battle_res = None

    if st.button("⚔️ FIGHT!"):
        if url_a and url_b:
            with st.spinner("Analyzing both videos..."):
                ta, title_a, _ = get_transcript_direct(url_a)
                tb, title_b, _ = get_transcript_direct(url_b)
                
                if ta and tb:
                    prompt = f"""
                    Lakukan analisis perbandingan antara dua video ini.
                    
                    VIDEO A (KITA): {title_a}
                    TRANSKRIP A: {ta[:15000]}
                    
                    VIDEO B (KOMPETITOR): {title_b}
                    TRANSKRIP B: {tb[:15000]}
                    
                    TUGAS:
                    1. Siapa pemenangnya secara kualitas konten?
                    2. Apa kelebihan Video A dibanding B?
                    3. Apa kekurangan Video A dibanding B?
                    4. Berikan saran strategi agar Video A bisa mengalahkan B.
                    """
                    client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
                    res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                    
                    st.session_state.battle_res = f"### 🏆 Hasil: {title_a} vs {title_b}\n\n{res.text}"
                    st.rerun()

    if st.session_state.battle_res:
        st.markdown(st.session_state.battle_res)