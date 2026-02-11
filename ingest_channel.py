import streamlit as st
from google import genai # Library Baru
from google.genai import types
import yt_dlp
import os
import glob
import time
import random
from supabase import create_client

# --- SETUP ---
# Gunakan Client dari library google-genai
client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def get_channel_videos(channel_url, limit=30): 
    """Mengambil list URL video terbaru dari sebuah channel"""
    ydl_opts = {
        'extract_flat': True,
        'force_generic_extractor': True,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Tambahkan /videos untuk memastikan mengambil tab video
            info = ydl.extract_info(f"{channel_url}/videos", download=False)
            return [{"url": entry['url'], "title": entry['title']} for entry in info['entries'][:limit]]
        except Exception as e:
            st.error(f"Gagal mengambil list video: {e}")
            return []

def get_transcript(video_url):
    # Opsi "Factory Reset" - Biarkan yt-dlp mengatur dirinya sendiri
    ydl_opts = {
        'skip_download': True,      
        'writesubtitles': True,    
        'writeautomaticsub': True,  
        'subtitleslangs': ['id', 'en.*'], 
        'outtmpl': 'temp_rag_%(id)s',
        'quiet': True,              
        'no_warnings': True,
        'ignoreerrors': True,    
    }
    
    # Kita coba cek versi yt-dlp dulu biar yakin
    import yt_dlp.version
    st.sidebar.caption(f"yt-dlp ver: {yt_dlp.version.__version__}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Step 1: Tarik Info
            info = ydl.extract_info(video_url, download=True)
            
            # Kalau info kosong (kena blokir/error), langsung return None
            if not info:
                return None
                
            vid_id = info.get('id')
            
            # Step 2: Cari File Subtitle
            # Kita cari file apapun yang depannya temp_rag_{vid_id}
            sub_files = glob.glob(f"temp_rag_{vid_id}*")
            
            if not sub_files: 
                # Coba fallback: kadang yt-dlp nyimpen dengan nama beda dikit
                return None
            
            final_text = []
            
            # Step 3: Baca & Parsing (Logic Timestamp Kamu Tetap Dipakai)
            # Ambil file pertama yg ketemu
            with open(sub_files[0], 'r', encoding='utf-8') as f:
                lines = f.readlines()
                current_timestamp = ""
                
                for line in lines:
                    line = line.strip()
                    if "-->" in line:
                        time_part = line.split("-->")[0].strip()
                        try:
                            parts = time_part.split(":")
                            if len(parts) == 3:
                                minutes = int(parts[1]) + (int(parts[0]) * 60)
                                seconds = int(float(parts[2]))
                                current_timestamp = f"[{minutes:02d}:{seconds:02d}]"
                            elif len(parts) == 2:
                                minutes = int(parts[0])
                                seconds = int(float(parts[1]))
                                current_timestamp = f"[{minutes:02d}:{seconds:02d}]"
                        except:
                            continue
                    elif line and "WEBVTT" not in line and not line.isdigit():
                        if current_timestamp:
                            final_text.append(f"{current_timestamp} {line}")
                            current_timestamp = ""
            
            # Bersih-bersih
            for f in sub_files: 
                try: os.remove(f) 
                except: pass
                
            return "\n".join(final_text)
            
        except Exception as e:
            # Print error ke terminal biar kita tau kenapa, tapi jangan stop app
            print(f"❌ Error detail pada {video_url}: {e}")
            return None

def split_text_with_timestamp(text, chunk_size=1000):
    """
    Memotong teks tapi tetap menjaga info [00:00] di setiap awal chunk
    agar AI tahu kapan kalimat itu diucapkan.
    """
    chunks = []
    # Mencari pola timestamp [00:00] dalam teks
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        chunks.append(chunk)
    return chunks

def process_channel(channel_url, channel_name):
    st.info(f"🔍 Mencari video dari {channel_name}...")
    videos = get_channel_videos(channel_url)
    
    if not videos:
        st.error("Tidak ada video ditemukan. Pastikan URL channel benar.")
        return 0

    success_count = 0 
    progress_bar = st.progress(0)

    progress_bar = st.progress(0)
    for i, vid in enumerate(videos):
        st.write(f"📽️ Memproses ({i+1}/{len(videos)}): {vid['title']}")
        if i > 0:
            st.write("⏳ Cooling down 60 detik biar gak kena limit Gemini...")
            time.sleep(60) # Jeda pasti 60 detik biar aman 100%
        transcript = get_transcript(vid['url'])
        
        if transcript:
            chunks = split_text_with_timestamp(transcript)
            for chunk in chunks:
                try:
                    # Logika Embedding Baru (3072 Dimensi)
                    res = client.models.embed_content(
                        model="gemini-embedding-001",
                        contents=chunk,
                        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                    )
                    
                    embedding_vector = res.embeddings[0].values
                    
                    # Simpan ke Supabase
                    supabase.table("channel_knowledge").insert({
                        "channel_name": channel_name,
                        "video_title": vid['title'],
                        "video_url": vid['url'],
                        "content": chunk,
                        "embedding": embedding_vector
                    }).execute()
                    
                    # Delay kecil agar tidak spamming API
                    time.sleep(0.5) 
                except Exception as e:
                    st.error(f"Gagal memproses chunk: {e}")
            success_count += 1
        else:
            st.warning(f"⚠️ Skip {vid['title']} (Tidak ada transkrip)")
        
        progress_bar.progress((i + 1) / len(videos))
        time.sleep(2)
    
    return success_count

# --- UI INGEST ---
if __name__ == "__main__":
    st.title("🧠 Vye Ingestion Engine")
    st.caption("Status: Standalone Mode")

    target_url = st.text_input("Link Channel", placeholder="https://youtube.com/@GadgetIn")
    target_name = st.text_input("Nama Channel", placeholder="GadgetIn")

    if st.button("Mulai Belajar 🚀"):
        if target_url and target_name:
            process_channel(target_url, target_name)
            st.success("✅ Selesai! Data channel berhasil masuk ke Supabase.")
        else:
            st.warning("Isi link dan nama channel dulu bos!")