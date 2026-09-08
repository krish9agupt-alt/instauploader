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
    .slot-card { background-color: #1e1e1e; padding: 15px; border-radius: 8px; border: 1px solid #333; margin-bottom: 12px; }
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🎬 No Copyright Video Studio Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">8 Daily Reels Queue with Individual Google Drive Links, Custom Timing, and Completion Status</p>', unsafe_allow_html=True)

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

# ----------------- GOOGLE DRIVE HELPERS -----------------
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

# ----------------- SESSION STATE FOR 8 SLOTS -----------------
if "slot_status" not in st.session_state:
    st.session_state.slot_status = ["Pending"] * 8

# ----------------- MAIN UI TABS -----------------
tab1, tab2 = st.tabs(["🎯 8 Daily Reels Slots & Schedule", "📊 Bulk Progress Dashboard"])

with tab1:
    st.subheader("Configure & Upload 8 Individual Reels")
    st.write("Enter the Google Drive link and pick a custom schedule time for each reel slot.")
    st.markdown("---")

    # Render 8 rows dynamically
    for i in range(8):
        with st.container():
            st.markdown(f"<div class='slot-card'><b>Reel Slot #{i+1}</b>", unsafe_allow_html=True)
            cols = st.columns([3, 1.2, 1.2, 1])
            
            with cols[0]:
                link_val = st.text_input(
                    f"Google Drive Link #{i+1}", 
                    key=f"link_{i}", 
                    placeholder=f"Paste GDrive link for Reel {i+1}",
                    label_visibility="collapsed"
                )
            with cols[1]:
                default_hour = 8 + (i * 2) if (8 + (i * 2)) < 24 else 23
                st.time_input(f"Time #{i+1}", time(default_hour, 0), key=f"time_{i}", label_visibility="collapsed")
            with cols[2]:
                status = st.session_state.slot_status[i]
                if status == "Complete":
                    st.markdown("<p style='color: #4ade80; font-weight: bold; margin-top: 5px;'>✅ Complete</p>", unsafe_allow_html=True)
                elif status == "Uploading...":
                    st.markdown("<p style='color: #facc15; font-weight: bold; margin-top: 5px;'>⏳ Uploading...</p>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color: #94a3b8; margin-top: 5px;'>📌 Pending</p>", unsafe_allow_html=True)
            with cols[3]:
                if st.button(f"Upload #{i+1}", key=f"btn_{i}"):
                    if not client:
                        st.error("Please login via sidebar first!")
                    elif not link_val:
                        st.warning("Please enter a link first!")
                    else:
                        st.session_state.slot_status[i] = "Uploading..."
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # Process Upload for any slot triggered
    for i in range(8):
        if st.session_state.slot_status[i] == "Uploading...":
            link_to_process = st.session_state.get(f"link_{i}", "")
            with st.spinner(f"Downloading and publishing Reel #{i+1} to Instagram..."):
                video_path = download_video(link_to_process)
                if video_path and os.path.exists(video_path):
                    try:
                        caption = f"No Copyright Daily Reel #{i+1} 🚀 #shorts #reels #viral"
                        client.clip_upload(video_path, caption=caption)
                        st.session_state.slot_status[i] = "Complete"
                        st.success(f"Reel #{i+1} uploaded successfully!")
                    except Exception as e:
                        st.error(f"Instagram Upload Error: {e}")
                        st.session_state.slot_status[i] = "Pending"
                    finally:
                        os.remove(video_path)
                else:
                    st.error(f"Could not fetch file for Slot #{i+1}. Ensure sharing is set to 'Anyone with the link can view'.")
                    st.session_state.slot_status[i] = "Pending"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Process & Upload All Pending Slots"):
        for i in range(8):
            if st.session_state.slot_status[i] == "Pending" and st.session_state.get(f"link_{i}", ""):
                st.session_state.slot_status[i] = "Uploading..."
        st.rerun()

with tab2:
    st.subheader("Daily Status Overview")
    completed_count = sum(1 for s in st.session_state.slot_status if s == "Complete")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Total Completed Today", f"{completed_count} / 8 Reels")
    with col_m2:
        st.metric("Pending Slots", f"{8 - completed_count} Reels")
        
    st.markdown("---")
    if st.button("🔄 Reset All Status to Pending"):
        st.session_state.slot_status = ["Pending"] * 8
        st.rerun()
