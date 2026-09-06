import os
import re
import time
from datetime import datetime
from instagrapi import Client
import pandas as pd
import requests
import schedule
import streamlit as st

st.set_page_config(
    page_title="Insta Reel Bulk Studio", page_icon="⚡", layout="wide"
)

st.title("⚡ Instagram Reel Automation Studio")

# --- 1. FIXED INLINE LOGIN & SETTINGS (NO SLIDE MENU) ---
st.header("🔑 Instagram Login & Settings")

if "IG_USERNAME" in st.secrets and "IG_PASSWORD" in st.secrets:
    ig_username = st.secrets["IG_USERNAME"]
    ig_password = st.secrets["IG_PASSWORD"]
    st.success("✅ Logged in automatically via Streamlit Secrets!")
else:
    col_user, col_pass = st.columns(2)
    with col_user:
        ig_username = st.text_input("Instagram Username")
    with col_pass:
        ig_password = st.text_input("Instagram Password", type="password")

st.divider()

# --- HELPER FUNCTIONS ---
if "logs" not in st.session_state:
    st.session_state.logs = []


def add_log(slot, status, details):
    st.session_state.logs.append(
        {
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Slot/Mode": slot,
            "Status": status,
            "Details": details,
        }
    )


def get_instagram_client():
    if not ig_username or not ig_password:
        return None
    cl = Client()
    cl.login(ig_username, ig_password)
    return cl


def get_drive_folder_id(url):
    match = re.search(r"folders/([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
    return None


def download_drive_file(file_id, destination):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(
        URL, params={"id": file_id, "confirm": "t"}, stream=True
    )
    with open(destination, "wb") as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)


# --- NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(
    ["📁 Drive Bulk 8-Reels Auto", "📊 Analytics Dashboard", "📋 Activity Logs"]
)

# --- TAB 1: DRIVE BULK AUTOMATION ---
with tab1:
    st.header("📁 Bulk Drive Folder Auto Sync")
    st.caption("Drive Folder Link paste karein jahan saare Videos hain.")

    TIME_SLOTS = [
        "08:00",
        "10:30",
        "13:00",
        "15:30",
        "18:00",
        "20:00",
        "22:00",
        "23:30",
    ]

    drive_folder_url = st.text_input(
        "Google Drive Public Folder URL",
        placeholder="https://drive.google.com/drive/folders/...",
    )
    auto_caption = st.text_area(
        "Reels Caption & Hashtags",
        value="#reels #viral #trending #explore #foryou",
    )

    # Individual Drive Links option as fallback
    st.subheader("Or Set Individual 8 Links")
    drive_urls = []
    cols = st.columns(4)
    for i, slot in enumerate(TIME_SLOTS):
        col_idx = i % 4
        with cols[col_idx]:
            url = st.text_input(f"Slot {i+1} ({slot})", key=f"slot_url_{i}")
            drive_urls.append(url)

    def process_slot_upload(slot_index):
        url = drive_urls[slot_index]
        if not url:
            return

        file_id = None
        match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
        if match:
            file_id = match.group(1)

        if not file_id:
            add_log(f"Slot {slot_index+1}", "Failed", "Invalid Link")
            return

        local_file = f"slot_{slot_index+1}.mp4"
        try:
            download_drive_file(file_id, local_file)
            cl = get_instagram_client()
            media = cl.clip_upload(local_file, caption=auto_caption)
            add_log(
                f"Slot {slot_index+1}",
                "Success",
                f"Media ID: {media.pk}",
            )
        except Exception as e:
            add_log(f"Slot {slot_index+1}", "Failed", str(e))
        finally:
            if os.path.exists(local_file):
                os.remove(local_file)

    st.divider()
    start_auto = st.checkbox("🚀 Activate Daily 8-Reels Schedule Engine")

    if start_auto:
        if not ig_username or not ig_password:
            st.error("Please provide Instagram Username and Password!")
        else:
            st.info("Automation Running. Schedule active for 8 fixed slots...")
            schedule.clear()
            for idx, time_slot in enumerate(TIME_SLOTS):
                schedule.every().day.at(time_slot).do(
                    process_slot_upload, idx
                )

            while start_auto:
                schedule.run_pending()
                time.sleep(30)

# --- TAB 2: ANALYTICS DASHBOARD ---
with tab2:
    st.header("📊 Smart Performance Analytics")
    if st.button("🔄 Sync Instagram Data"):
        if not ig_username or not ig_password:
            st.error("Login details missing!")
        else:
            with st.spinner("Fetching profile analytics..."):
                try:
                    cl = get_instagram_client()
                    medias = cl.user_medias(cl.user_id, amount=10)
                    analytics_data = []

                    for m in medias:
                        if m.media_type == 2:
                            views = (
                                m.play_count
                                if hasattr(m, "play_count") and m.play_count
                                else 0
                            )
                            analytics_data.append(
                                {
                                    "Date": m.taken_at.strftime(
                                        "%Y-%m-%d %H:%M"
                                    ),
                                    "Views": views,
                                    "Likes": m.like_count,
                                    "Comments": m.comment_count,
                                }
                            )

                    if analytics_data:
                        df = pd.DataFrame(analytics_data)
                        st.dataframe(df, use_container_width=True)
                        st.bar_chart(df, x="Date", y="Views")
                    else:
                        st.warning("No Video Reels found.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# --- TAB 3: ACTIVITY LOGS ---
with tab3:
    st.header("📋 Execution Activity Logs")
    if st.session_state.logs:
        st.dataframe(
            pd.DataFrame(st.session_state.logs), use_container_width=True
        )
    else:
        st.info("No activity recorded yet.")
