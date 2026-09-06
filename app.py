import time
from datetime import datetime
from instagrapi import Client
import os
import re
import requests
import schedule
import streamlit as st

st.set_page_config(
    page_title="Daily Auto Reel Uploader", page_icon="🤖", layout="centered"
)

st.title("🤖 Daily Automatic Instagram Reel Uploader")
st.write("Google Drive link aur daily execution time set karein.")

# Sidebar Credentials
st.sidebar.header("🔑 Instagram Credentials")
ig_username = st.sidebar.text_input("Instagram Username")
ig_password = st.sidebar.text_input("Instagram Password", type="password")

# Inputs
drive_url = st.text_input(
    "Google Drive File Link",
    placeholder="https://drive.google.com/file/d/.../view",
)
caption = st.text_area(
    "Caption / Hashtags", placeholder="Write your reel caption here..."
)
schedule_time = st.time_input("Daily Auto Upload Time")


def get_drive_file_id(url):
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
    match_id = re.search(r"id=([a-zA-Z0-9_-]+)", url)
    if match_id:
        return match_id.group(1)
    return None


def download_video(file_id, destination):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(
        URL, params={"id": file_id, "confirm": "t"}, stream=True
    )
    with open(destination, "wb") as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)


def run_upload():
    if not ig_username or not ig_password or not drive_url:
        st.error("Missing Credentials or Drive Link!")
        return

    file_id = get_drive_file_id(drive_url)
    if not file_id:
        st.error("Invalid Drive URL!")
        return

    local_file = "auto_reel.mp4"
    try:
        st.write(
            f"[{datetime.now().strftime('%H:%M:%S')}] Downloading video from Drive..."
        )
        download_video(file_id, local_file)

        st.write(
            f"[{datetime.now().strftime('%H:%M:%S')}] Logging in to Instagram..."
        )
        cl = Client()
        cl.login(ig_username, ig_password)

        st.write(
            f"[{datetime.now().strftime('%H:%M:%S')}] Uploading Reel..."
        )
        media = cl.clip_upload(local_file, caption=caption)
        st.success(
            f"🎉 Reel Uploaded Automatically! Media ID: {media.pk}"
        )
    except Exception as e:
        st.error(f"Error: {str(e)}")
    finally:
        if os.path.exists(local_file):
            os.remove(local_file)


col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 Upload Immediately"):
        run_upload()

with col2:
    start_scheduler = st.checkbox("⏰ Enable Daily Automation")

if start_scheduler:
    time_str = schedule_time.strftime("%H:%M")
    st.info(
        f"Automation active. Waiting to post daily at **{time_str}**..."
    )
    schedule.clear()
    schedule.every().day.at(time_str).do(run_upload)

    # Simple loop to keep task pending within Streamlit session
    while start_scheduler:
        schedule.run_pending()
        time.sleep(30)
