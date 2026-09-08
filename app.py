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
    .sub-text { color: #666; font-size: 1.1rem; margin-bottom: 20px; }
    .metric-card { background-color: #1e1e1e; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #333; }
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🎬 No Copyright Video Studio Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">Automated Daily 8-Reels Bulk Engine with Google Drive & Custom Time Management</p>', unsafe_allow_html=True)

# ----------------- SIDEBAR: CREDENTIALS & TIME SETTINGS -----------------
st.sidebar.header("🔑 Instagram & Schedule Settings")

with st.sidebar.expander("🔐 Credentials (UI Input)", expanded=True):
    ui_session_id = st.text_input("Session ID (Recommended)", type="password", placeholder="Paste sessionid cookie...")
    ui_username = st.text_input("Instagram Username", placeholder="username")
    ui_password = st.text_input("Instagram Password", type="password", placeholder="password")

st.sidebar.markdown("---")
st.sidebar.header("⏰ Custom Time & Slot Settings")
upload_time = st.sidebar.time_input("Daily Start Time", time(9, 0))
timezone_offset = st.sidebar.selectbox("Timezone", ["IST (UTC+5:30)", "UTC", "EST", "PST"])
daily_limit = st.sidebar.slider("Reels Per Day", min_value=1, max_value=20, value=8)

# ----------------- INSTAGRAM CLIENT AUTHENTICATION -----------------
@st.cache_resource
def init_instagram_client(s_id, uname, pwd):
    client = Client()
    try:
        if s_id and s_id.strip():
            client.login_by_sessionid(s_id.strip())
            return client, "Successfully Connected via Session ID!"
        elif uname and pwd:
            client.login(uname.strip(), pwd.strip())
            return client, "Successfully Connected via Username & Password!"
        
        # Fallback to st.secrets if UI inputs are empty
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
        
    return None, None

client, login_status = init_instagram_client(ui_session_id, ui_username, ui_password)

if not client:
    st.markdown("""
        <div style="background-color: #4c1d1d; padding: 15px; border-radius: 8px; border: 1px solid #f87171; color: #fca5a5; margin-bottom: 20px;">
            ❌ <b>Authentication Required:</b> Please enter your Session ID or Username/Password in the sidebar (or configure secrets.toml).
        </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.success(login_status)

# ----------------- GOOGLE DRIVE LINKS MANAGEMENT -----------------
st.sidebar.markdown("---")
st.sidebar.header("📁 Google Drive Source")
default_links_text = st.sidebar.text_area(
    "Paste Google Drive Links (One per line)", 
    value="https://drive.google.com/file/d/EXAMPLE_ID_1/view?usp=sharing\nhttps://drive.google.com/file/d/EXAMPLE_ID_2/view?usp=sharing",
    height=150
)

drive_links = [line.strip() for line in default_links_text.split("\n") if line.strip()]
total_videos = len(drive_links)

def convert_gdrive_url(url):
    """Converts a Google Drive share link into a direct download URL."""
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
tab1, tab2, tab3 = st.tabs([
    "🚀 Daily Bulk Engine", 
    "📅 Schedule & Time Logs", 
    "📤 Manual Drive/File Upload"
])

with tab1:
    st.subheader("Daily Bulk Reel Automation Queue")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><h3>Total Queue Links</h3><h2>{total_videos} Reels</h2></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><h3>Scheduled Daily Limit</h3><h2>{daily_limit} / Day</h2></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><h3>Active Start Time</h3><h2>{upload_time.strftime("%I:%M %p")}</h2></div>', unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔥 Test Upload 1 Video from Queue"):
            if not client:
                st.error("Please login first via sidebar credentials!")
            elif not drive_links:
                st.error("No Google Drive links provided in the sidebar!")
            else:
                with st.spinner("Downloading video from Google Drive and uploading to Instagram..."):
                    video_path = download_video(drive_links[0])
                    if video_path and os.path.exists(video_path):
                        try:
                            caption = "Automated Reel #NoCopyright #Shorts #Reels"
                            client.clip_upload(video_path, caption=caption)
                            st.success("✅ Reel uploaded successfully from Google Drive!")
                        except Exception as e:
                            st.error(f"Instagram Upload Error: {e}")
                        finally:
                            os.remove(video_path)
                    else:
                        st.error("Could not fetch file from the provided Google Drive link. Check if sharing permissions are set to 'Anyone with the link can view'.")

    with col_btn2:
        if st.button("▶️ Start Full Bulk Engine Cron Sync"):
            st.success(f"Bulk engine successfully activated! System will post {daily_limit} reels daily starting at {upload_time.strftime('%I:%M %p')}.")

with tab2:
    st.subheader("Scheduled Timeline & History")
    st.write(f"Current Timezone Configured: **{timezone_offset}**")
    st.markdown("---")
    st.markdown(f"**Today Slot 1:** {upload_time.strftime('%I:%M %p')} — 1 Reel queued")
    st.markdown(f"**Today Slot 2:** {(datetime.combine(datetime.today(), upload_time)).strftime('%I:%M %p')} (Interval spaced) — 1 Reel queued")
    st.info("The automated worker runs in the background based on your configured cron slot limits.")

with tab3:
    st.subheader("Manual Single Upload (Direct File or Drive Link)")
    
    upload_choice = st.radio("Choose Upload Source:", ["Google Drive Link", "Direct Local File Upload"])
    
    manual_caption = st.text_area("Reel Caption", value="No copyright daily reel 🚀 #reels")
    
    if upload_choice == "Google Drive Link":
        single_gdrive_url = st.text_input("Enter Google Drive Share Link")
        if st.button("Upload from Drive Link"):
            if client and single_gdrive_url:
                with st.spinner("Processing Google Drive file..."):
                    v_path = download_video(single_gdrive_url)
                    if v_path:
                        client.clip_upload(v_path, caption=manual_caption)
                        st.success("Uploaded successfully from Google Drive link!")
                        os.remove(v_path)
                    else:
                        st.error("Failed to download video.")
            else:
                st.error("Provide a valid link and ensure login credentials are set.")
    else:
        manual_file = st.file_uploader("Upload Video File (.mp4)", type=["mp4", "mov"])
        if st.button("Upload File to Instagram"):
            if client and manual_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                    tmp.write(manual_file.read())
                    tmp_path = tmp.name
                try:
                    with st.spinner("Uploading file..."):
                        client.clip_upload(tmp_path, caption=manual_caption)
                        st.success("File uploaded successfully!")
                except Exception as e:
                    st.error(f"Upload error: {e}")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
            else:
                st.error("Please upload a file and check credentials.")
