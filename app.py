import os
import tempfile
import requests
import streamlit as st
from instagrapi import Client
from datetime import datetime, time

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="Instagram Reels Auto-Uploader Studio Pro",
    page_icon="🚀",
    layout="wide"
)

# ----------------- CUSTOM STYLING -----------------
st.markdown("""
    <style>
    .main-header { font-size: 2.3rem; font-weight: bold; color: #FF4B4B; margin-bottom: 0px; }
    .sub-text { color: #aaa; font-size: 1.1rem; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🎬 No Copyright Video Studio Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">Bulk Batch Uploader: Paste 8+ Google Drive Links or Upload Files with Custom Timing</p>', unsafe_allow_html=True)

# ----------------- SIDEBAR: CREDENTIALS -----------------
st.sidebar.header("🔑 Instagram Credentials")
ui_session_id = st.sidebar.text_input("Session ID (Recommended)", type="password", placeholder="Paste sessionid cookie...")
ui_username = st.sidebar.text_input("Instagram Username")
ui_password = st.sidebar.text_input("Instagram Password", type="password")

# ----------------- INSTAGRAM CLIENT AUTHENTICATION -----------------
@st.cache_resource
def init_instagram_client(s_id, uname, pwd):
    client = Client()
    try:
        if s_id and s_id.strip():
            client.login_by_sessionid(s_id.strip())
            return client, "Connected via Session ID!"
        elif uname and pwd:
            client.login(uname.strip(), pwd.strip())
            return client, "Connected via Username & Password!"
        
        # Fallback to st.secrets
        if "instagram" in st.secrets:
            sec_s_id = st.secrets["instagram"].get("SESSION_ID")
            sec_uname = st.secrets["instagram"].get("USERNAME")
            sec_pwd = st.secrets["instagram"].get("PASSWORD")
            if sec_s_id:
                client.login_by_sessionid(sec_s_id)
                return client, "Connected via Secrets Session ID!"
            elif sec_uname and sec_pwd:
                client.login(sec_uname, sec_pwd)
                return client, "Connected via Secrets Credentials!"
                
        if "SESSION_ID" in st.secrets:
            client.login_by_sessionid(st.secrets["SESSION_ID"])
            return client, "Connected via Secrets SESSION_ID!"
            
    except Exception as e:
        return None, f"Login Error: {str(e)}"
        
    return None, "Not Logged In"

client, login_status = init_instagram_client(ui_session_id, ui_username, ui_password)

if not client:
    st.sidebar.warning(f"⚠️ {login_status} Please enter your details above.")
else:
    st.sidebar.success(f"✅ {login_status}")

# ----------------- HELPERS -----------------
def convert_gdrive_url(url):
    if "drive.google.com" in url and "/file/d/" in url:
        try:
            file_id = url.split("/file/d/")[1].split("/")[0]
            return f"https://drive.google.com/uc?export=download&id={file_id}"
        except Exception:
            pass
    return url

def download_video(url):
    direct_url = convert_gdrive_url(url)
    try:
        response = requests.get(direct_url, stream=True, timeout=30)
        if response.status_code == 200:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp.write(chunk)
            tmp.close()
            return tmp.name
    except Exception as e:
        st.error(f"Download failed: {e}")
    return None

# ----------------- MAIN UI TABS -----------------
tab1, tab2 = st.tabs(["📦 Bulk Google Drive Links Box", "📤 Direct Multi-File Uploader"])

with tab1:
    st.subheader("Bulk Google Drive Link Queue")
    st.write("Neeche diye gaye box me ek sath 8 ya jitne chahein Google Drive links paste karein (har link ek nayi line me hona chahiye).")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        start_time = st.time_input("Custom Schedule Start Time", time(8, 0))
    with col_t2:
        caption_template = st.text_input("Default Caption", value="No Copyright Reel 🚀 #shorts #reels")

    links_input = st.text_area(
        "Paste 8+ Google Drive Links (One per line)",
        height=220,
        placeholder="https://drive.google.com/file/d/ID_1/view?usp=sharing\nhttps://drive.google.com/file/d/ID_2/view?usp=sharing"
    )

    if st.button("🚀 Start Batch Upload for All Links"):
        if not client:
            st.error("Please login first via sidebar credentials!")
        else:
            links = [l.strip() for l in links_input.split("\n") if l.strip()]
            if not links:
                st.warning("Please paste at least one Google Drive link!")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                total = len(links)
                
                for idx, link in enumerate(links):
                    status_text.text(f"Processing Reel {idx+1} of {total}...")
                    v_path = download_video(link)
                    if v_path and os.path.exists(v_path):
                        try:
                            caption = f"{caption_template} #{idx+1}"
                            client.clip_upload(v_path, caption=caption)
                            st.success(f"✅ Reel #{idx+1} uploaded successfully and marked as Complete!")
                        except Exception as e:
                            st.error(f"❌ Failed Reel #{idx+1}: {e}")
                        finally:
                            os.remove(v_path)
                    else:
                        st.error(f"❌ Could not download Reel #{idx+1} from link.")
                    progress_bar.progress((idx + 1) / total)
                
                status_text.text("🎉 All scheduled reels processed successfully!")

with tab2:
    st.subheader("Direct Multi-File Video Upload Box")
    st.write("Apne computer se ek sath multiple video files (.mp4) select karke upload karein.")
    
    uploaded_files = st.file_uploader("Choose Video Files", type=["mp4", "mov"], accept_multiple_files=True)
    manual_caption = st.text_input("Caption for Uploaded Files", value="Daily Reel 🚀 #reels")
    
    if st.button("🚀 Upload All Selected Files"):
        if not client:
            st.error("Please login first via sidebar credentials!")
        elif not uploaded_files:
            st.warning("Please select at least one video file!")
        else:
            total_files = len(uploaded_files)
            p_bar = st.progress(0)
            s_text = st.empty()
            
            for idx, uploaded_file in enumerate(uploaded_files):
                s_text.text(f"Uploading file {idx+1} of {total_files}...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                try:
                    client.clip_upload(tmp_path, caption=f"{manual_caption} #{idx+1}")
                    st.success(f"✅ File #{idx+1} ({uploaded_file.name}) uploaded successfully!")
                except Exception as e:
                    st.error(f"❌ Error uploading #{idx+1}: {e}")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                p_bar.progress((idx + 1) / total_files)
            s_text.text("🎉 All file uploads completed!")
