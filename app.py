import os
import re
import time
from datetime import datetime
from instagrapi import Client
import pandas as pd
import requests
import schedule
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Ultimate Insta Reel Studio",
    page_icon="🔥",
    layout="wide"
)

st.title("🔥 All-in-One Instagram Reel Automation & Analytics Studio")

# --- 1. LOGIN & SECRETS MANAGEMENT ---
if "IG_USERNAME" in st.secrets and "IG_PASSWORD" in st.secrets:
    ig_username = st.secrets["IG_USERNAME"]
    ig_password = st.secrets["IG_PASSWORD"]
    st.sidebar.success("✅ Logged in via Streamlit Secrets")
else:
    st.sidebar.header("🔑 Instagram Login")
    ig_username = st.sidebar.text_input("Username")
    ig_password = st.sidebar.text_input("Password", type="password")

# Session state for logs
if "logs" not in st.session_state:
    st.session_state.logs = []

# --- HELPER FUNCTIONS ---
def get_drive_file_id(url):
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
    match_id = re.search(r"id=([a-zA-Z0-9_-]+)", url)
    if match_id:
        return match_id.group(1)
    return None

def download_drive_video(file_id, destination):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params={"id": file_id, "confirm": "t"}, stream=True)
    with open(destination, "wb") as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)

def add_log(slot, status, details):
    st.session_state.logs.append({
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Slot/Mode": slot,
        "Status": status,
        "Details": details
    })

def get_instagram_client():
    if not ig_username or not ig_password:
        return None
    cl = Client()
    cl.login(ig_username, ig_password)
    return cl

# --- 2. AUTO HASHTAG GENERATOR ---
st.subheader("🏷️ Auto Hashtag Generator")
col_topic, col_gen = st.columns([3, 1])
with col_topic:
    topic = st.text_input("Enter Video Topic / Niche", placeholder="e.g. Fitness, Tech, Gaming, Motivation")
with col_gen:
    st.write(" ")
    st.write(" ")
    generate_tags = st.button("Generate Hashtags")

generated_hashtags = ""
if generate_tags and topic:
    clean_topic = topic.lower().replace(" ", "")
    base_tags = f"#{clean_topic} #{clean_topic}reels #{clean_topic}life #viral #trending #reelsindia #explore #foryou #instareels #foryoupage"
    st.code(base_tags, language="text")
    generated_hashtags = base_tags

# --- NAVIGATION TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🚀 Direct Upload", 
    "⏰ Daily 8-Slot Auto", 
    "📊 Smart Analytics", 
    "📋 Upload Logs"
])

# --- TAB 1: INSTANT DIRECT UPLOAD ---
with tab1:
    st.header("Direct File Upload")
    direct_file = st.file_uploader("Upload MP4/MOV Video from Device", type=["mp4", "mov"])
    direct_caption = st.text_area("Caption & Hashtags", value=generated_hashtags, key="direct_cap")

    if st.button("⚡ Upload Instant Reel"):
        if not direct_file:
            st.error("Please select a video file first!")
        elif not ig_username or not ig_password:
            st.error("Instagram credentials missing!")
        else:
            file_path = f"temp_{direct_file.name}"
            with open(file_path, "wb") as f:
                f.write(direct_file.getbuffer())

            try:
                st.info("Logging into Instagram...")
                cl = get_instagram_client()
                
                st.info("Uploading Reel...")
                media = cl.clip_upload(file_path, caption=direct_caption)
                st.success(f"🎉 Reel Uploaded! Media ID: {media.pk}")
                add_log("Instant Upload", "Success", f"Media ID: {media.pk}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
                add_log("Instant Upload", "Failed", str(e))
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)

# --- TAB 2: DAILY 8-SLOT AUTOMATION ---
with tab2:
    st.header("Daily 8-Slots Algorithm Auto Scheduler")
    TIME_SLOTS = ["08:00", "10:30", "13:00", "15:30", "18:00", "20:00", "22:00", "23:30"]
    auto_caption = st.text_area("Default Automation Caption", value=generated_hashtags, key="auto_cap")

    drive_urls = []
    for i, slot in enumerate(TIME_SLOTS, 1):
        url = st.text_input(f"Slot {i} ({slot}) - Google Drive Link", key=f"drive_slot_{i}")
        drive_urls.append(url)

    def upload_slot_video(slot_index):
        url = drive_urls[slot_index]
        if not url:
            return

        file_id = get_drive_file_id(url)
        if not file_id:
            add_log(f"Slot {slot_index+1}", "Failed", "Invalid Drive URL")
            return

        local_file = f"slot_{slot_index+1}_reel.mp4"
        try:
            download_drive_video(file_id, local_file)
            cl = get_instagram_client()
            media = cl.clip_upload(local_file, caption=auto_caption)
            add_log(f"Slot {slot_index+1}", "Success", f"Media ID: {media.pk}")
        except Exception as e:
            add_log(f"Slot {slot_index+1}", "Failed", str(e))
        finally:
            if os.path.exists(local_file):
                os.remove(local_file)

    start_auto = st.checkbox("🚀 Activate 8-Slot Daily Scheduler")
    if start_auto:
        if not ig_username or not ig_password:
            st.error("Add Instagram Credentials First!")
        else:
            st.info("Automation Active! System waiting for scheduled time slots...")
            schedule.clear()
            for idx, time_slot in enumerate(TIME_SLOTS):
                schedule.every().day.at(time_slot).do(upload_slot_video, idx)

            while start_auto:
                schedule.run_pending()
                time.sleep(30)

# --- TAB 3: SMART REELS ANALYTICS ---
with tab3:
    st.header("📊 Smart Reels Analytics & Performance")
    
    if st.button("🔄 Sync Latest Analytics Data"):
        if not ig_username or not ig_password:
            st.error("Instagram credentials missing!")
        else:
            with st.spinner("Fetching Instagram Reels analytics..."):
                try:
                    cl = get_instagram_client()
                    user_id = cl.user_id
                    medias = cl.user_medias(user_id, amount=10)

                    analytics_data = []
                    total_views = 0
                    total_likes = 0
                    total_comments = 0

                    for m in medias:
                        if m.media_type == 2:  # Video/Reel
                            views = m.play_count if hasattr(m, 'play_count') and m.play_count else 0
                            likes = m.like_count
                            comments = m.comment_count
                            engagement = round(((likes + comments) / views * 100), 2) if views > 0 else 0

                            total_views += views
                            total_likes += likes
                            total_comments += comments

                            analytics_data.append({
                                "Posted Date": m.taken_at.strftime("%Y-%m-%d %H:%M"),
                                "Caption": (m.caption_text[:25] + "...") if m.caption_text else "No Caption",
                                "Views 👁️": views,
                                "Likes ❤️": likes,
                                "Comments 💬": comments,
                                "Engagement Rate": f"{engagement}%"
                            })

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Tracked Reels", len(analytics_data))
                    c2.metric("Total Views", f"{total_views:,}")
                    c3.metric("Total Likes", f"{total_likes:,}")
                    c4.metric("Total Comments", f"{total_comments:,}")

                    st.divider()

                    if analytics_data:
                        df_analytics = pd.DataFrame(analytics_data)
                        st.subheader("📋 Recent Performance Breakdown")
                        st.dataframe(df_analytics, use_container_width=True)

                        st.subheader("📈 Views Comparison")
                        st.bar_chart(df_analytics, x="Posted Date", y="Views 👁️")
                    else:
                        st.warning("No Video/Reel media found.")

                except Exception as e:
                    st.error(f"Failed to fetch analytics: {str(e)}")

# --- TAB 4: UPLOAD LOGS ---
with tab4:
    st.header("📋 Activity Logs Report")
    if st.session_state.logs:
        df_logs = pd.DataFrame(st.session_state.logs)
        st.dataframe(df_logs, use_container_width=True)
    else:
        st.info("No activity logs recorded yet.")
