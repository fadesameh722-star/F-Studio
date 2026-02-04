import streamlit as st
import os
import sys
import subprocess
import time
import shutil
from datetime import timedelta
import pandas as pd

# --- 1. إعدادات الصفحة (تم إزالة الاسم) ---
st.set_page_config(
    page_title="F Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)
# --- إخفاء العلامات المائية والقوائم ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            [data-testid="stToolbar"] {visibility: hidden !important;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. دوال النظام والتحقق ---
def check_requirements():
    """فحص وتثبيت المكتبات بصمت"""
    try:
        import yt_dlp
    except ImportError:
        st.warning("جاري تهيئة ملفات النظام...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "pandas"])
        st.rerun()

check_requirements()
import yt_dlp

def check_ffmpeg():
    return shutil.which("ffmpeg") is not None

# دالة التحديث التفاعلية (Real Logs)
def update_interactive(placeholder):
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "--no-cache-dir", "yt-dlp"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    logs = ""
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None: break
        if line:
            logs += line
            placeholder.code(logs, language="bash")
    return process.poll() == 0

# هوك لمتابعة التحميل الحقيقي
def progress_hook(d):
    if d['status'] == 'downloading':
        try:
            p = float(d.get('_percent_str', '0%').replace('%','')) / 100
            st.session_state.prog_val = p
            st.session_state.status_msg = f"⏳ {d.get('_percent_str')} | 🚀 {d.get('_speed_str')}"
        except: pass

# --- 3. الستايل ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    
    .f-logo {
        background: #000; width: 60px; height: 60px;
        border-radius: 12px; display: flex; justify-content: center; align-items: center;
        margin: 0 auto 15px auto;
    }
    .f-logo h1 { color: #fff; font-size: 2rem; margin: 0; }
    
    button[kind="primary"] { background: #000; color: #fff; border-radius: 8px; }
    button[kind="primary"]:hover { background: #333; }
    </style>
""", unsafe_allow_html=True)

# --- 4. القائمة الجانبية ---
with st.sidebar:
    if os.path.exists("ICON.ico"): st.image("ICON.ico", width=60)
    else: st.markdown('<div class="f-logo"><h1>F</h1></div>', unsafe_allow_html=True)
    
    st.write("### ⚙️ النظام")
    if st.button("🔄 تحديث المحرك (Live)", use_container_width=True):
        log_box = st.empty()
        if update_interactive(log_box):
            st.success("✅ تم التحديث")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ فشل التحديث")

    st.divider()
    threads = st.slider("🚀 السرعة (Threads)", 1, 16, 4)

# --- 5. التطبيق الرئيسي ---
st.title("F Studio")

if 'data' not in st.session_state: st.session_state.data = None
if 'mode' not in st.session_state: st.session_state.mode = None
if 'prog_val' not in st.session_state: st.session_state.prog_val = 0.0
if 'status_msg' not in st.session_state: st.session_state.status_msg = "..."

tab1, tab2 = st.tabs(["🎬 فيديو فردي", "📂 قوائم التشغيل"])

# ==================================================
# 1. فيديو فردي
# ==================================================
with tab1:
    c1, c2 = st.columns([4, 1])
    with c1: url = st.text_input("رابط الفيديو", key="s_url")
    with c2: 
        if st.button("بحث", key="s_btn", use_container_width=True):
            if url:
                with st.spinner("تحليل..."):
                    try:
                        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                            st.session_state.data = ydl.extract_info(url, download=False)
                            st.session_state.mode = 'single'
                    except: st.error("رابط خطأ")

    if st.session_state.data and st.session_state.mode == 'single':
        info = st.session_state.data
        st.divider()
        
        # --- (إصلاح خطأ الصورة) ---
        col_img, col_inf = st.columns([1, 2])
        with col_img:
            thumb = info.get('thumbnail')
            if thumb and isinstance(thumb, str) and thumb.startswith('http'):
                st.image(thumb, use_container_width=True)
            else:
                st.markdown("### 🎵 Audio/No Image")
        # ---------------------------

        with col_inf:
            st.subheader(info.get('title', 'Video'))
            st.caption(f"⏱ {timedelta(seconds=int(info.get('duration', 0)))}")
        
        # خيارات
        c1, c2 = st.columns(2)
        with c1: f_type = st.radio("النوع", ["Video", "Audio"], horizontal=True)
        with c2: 
            if "Audio" in f_type: qual = st.selectbox("نقاء الصوت", ["320", "192", "128"])
            else: qual = st.selectbox("الدقة", ["Best", "1080p", "720p"])

        # القص
        with st.expander("✂️ قص الفيديو"):
            do_trim = st.checkbox("تفعيل")
            dur = int(info.get('duration', 0))
            if do_trim: s, e = st.slider("المدة", 0, dur, (0, dur))
            else: s, e = 0, dur

        if st.button("🚀 تحميل", use_container_width=True):
            bar = st.progress(0)
            stat = st.empty()
            
            try:
                name = "".join([c for c in info.get('title', 'v') if c.isalnum() or c in (' ', '-', '_')]).strip()
                opts = {
                    'outtmpl': f"{name}.%(ext)s",
                    'quiet': True,
                    'concurrent_fragment_downloads': threads,
                    'progress_hooks': [progress_hook]
                }
                
                # إعدادات القص
                if do_trim and check_ffmpeg():
                    opts['download_ranges'] = lambda _, __: [{'start_time': s, 'end_time': e}]
                    opts['force_keyframes_at_cuts'] = True

                # الصيغة
                if "Audio" in f_type:
                    opts['format'] = 'bestaudio/best'
                    if check_ffmpeg(): opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]
                else:
                    if "1080p" in qual: opts['format'] = "bestvideo[height<=1080]+bestaudio/best"
                    elif "720p" in qual: opts['format'] = "bestvideo[height<=720]+bestaudio/best"
                    else: opts['format'] = "bestvideo+bestaudio/best"

                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([info['webpage_url']])
                
                bar.progress(100)
                stat.success("✅ تم التحميل!")
                
                # زر الحفظ
                final = None
                for f in os.listdir('.'):
                    if f.startswith(name):
                        final = f
                        break
                if final:
                    with open(final, "rb") as f:
                        st.download_button("💾 حفظ", f, file_name=final)

            except Exception as ex: st.error(str(ex))
            
            # تحديث الشريط (خدعة)
            if st.session_state.prog_val > 0:
                bar.progress(st.session_state.prog_val)
                stat.text(st.session_state.status_msg)

# ==================================================
# 2. القوائم (Fixes: Empty & Crash)
# ==================================================
with tab2:
    cp1, cp2 = st.columns([4, 1])
    with cp1: p_url = st.text_input("رابط القائمة", key="p_url")
    with cp2:
        if st.button("جلب", key="p_btn", use_container_width=True):
            if p_url:
                with st.spinner("جاري الحفر لاستخراج القائمة..."):
                    try:
                        # أفضل إعدادات للقوائم عشان متبقاش فاضية
                        opts = {
                            'extract_flat': 'in_playlist', 
                            'ignoreerrors': True,
                            'no_warnings': True
                        }
                        with yt_dlp.YoutubeDL(opts) as ydl:
                            st.session_state.data = ydl.extract_info(p_url, download=False)
                            st.session_state.mode = 'playlist'
                    except: st.error("رابط خطأ")

    if st.session_state.data and st.session_state.mode == 'playlist':
        pl = st.session_state.data
        raw_entries = list(pl.get('entries', []))
        # تنظيف القائمة من القيم الفارغة
        entries = [e for e in raw_entries if e is not None]
        
        if not entries:
            st.warning("⚠️ القائمة فارغة أو خاصة (Private).")
        else:
            st.success(f"تم العثور على {len(entries)} فيديو")
            
            # --- (حماية الجدول من الانهيار) ---
            titles = []
            urls = []
            for e in entries:
                titles.append(e.get('title', 'Unknown'))
                urls.append(e.get('url', ''))

            df = pd.DataFrame({
                "check": [True] * len(entries),
                "title": titles,
                "url": urls
            })
            # إجبار التحويل لـ Boolean
            df["check"] = df["check"].astype(bool)

            edited = st.data_editor(
                df,
                column_config={
                    "check": st.column_config.CheckboxColumn("تحميل", default=True),
                    "url": None
                },
                hide_index=True,
                use_container_width=True
            )
            # ----------------------------------

            path_in = st.text_input("مسار الحفظ (اختياري)", value=os.path.join(os.getcwd(), "Downloads"))
            
            if st.button("📥 تحميل المختار", type="primary"):
                selected = edited[edited["check"] == True]
                if selected.empty:
                    st.warning("اختر فيديو!")
                else:
                    folder = "".join([c for c in pl.get('title', 'PL') if c.isalnum() or c in (' ', '-', '_')]).strip()
                    save_path = os.path.join(path_in, folder)
                    os.makedirs(save_path, exist_ok=True)
                    
                    m_bar = st.progress(0)
                    stat = st.empty()
                    
                    total = len(selected)
                    for i, row in enumerate(selected.itertuples()):
                        lnk = row.url
                        if "http" not in lnk: lnk = f"https://www.youtube.com/watch?v={lnk}"
                        
                        stat.text(f"({i+1}/{total}) {row.title}")
                        try:
                            # إعدادات تحميل سريعة للقوائم
                            popts = {
                                'outtmpl': f"{save_path}/%(title)s.%(ext)s",
                                'quiet': True,
                                'format': "bestvideo[height<=720]+bestaudio/best",
                                'concurrent_fragment_downloads': threads
                            }
                            with yt_dlp.YoutubeDL(popts) as ydl:
                                ydl.download([lnk])
                        except: pass
                        m_bar.progress((i+1)/total)
                    
                    stat.success(f"✅ تم الحفظ في: {save_path}")
                    if sys.platform == 'win32':

                        st.button("📂 فتح المجلد", on_click=lambda: os.startfile(save_path))
