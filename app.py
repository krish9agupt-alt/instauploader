import os
import re
import time
from datetime import datetime
from instagrapi import Client
from PIL import Image
import pandas as pd
import requests
import schedule
import streamlit as st

st.set_page_config(
    page_title="Insta Reel Studio", page_icon="⚡", layout="wide"
)

st.title("⚡ Instagram Reel Uploader & Auto Scheduler")

# --- 1. INLINE LOGIN & SESSION MANAGEMENT ---
st.header("🔑 Instagram Login & Settings")

if "IG_USERNAME" in st.secrets and "IG_SESSIONID" in st.secrets:
    ig_username = st.secrets["IG_USERNAME"]
    ig_sessionid = st.secrets["IG_SESSIONID"]
    ig_password = None
    st.success("✅ Logged in safely via Session ID (Bypassed IP Block)!")
else:
    col_user, col_pass = st.columns(2)
    with col_user:
        ig_username = st.text_input("Instagram Username")
    with col_pass:
        ig_password = st.text_input(
            "Instagram Password (or Session ID)", type="password"
        )
    ig_sessionid = None

st.divider()

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
    cl = Client()
    cl.set_user_agent(
        "Instagram 269.0.0.18.75 Android (26/8.0.0; 480dpi; 1080x1920; Xiaomi; Redmi Note 5; vince; qcom; en_US; 314665270)"
    )

    if ig_sessionid:
        cl.login_by_sessionid(ig_sessionid)
    elif ig_username and ig_password:
        if len(ig_password) > 30 and "%" in ig_password:
            cl.login_by_sessionid(ig_password)
        else:
            cl.login(ig_username, ig_password)
    else:
        raise Exception("Login credentials missing!")

    return cl


def generate_dummy_thumbnail(output_path="thumb.jpg"):
    # Generate a simple blank thumbnail image to bypass MoviePy dependency
    img = Image.new("RGB", (720, 1280), color=(0, 0, 0))
    img.save(output_path)
    return output_path


def get_drive_file_id(url):
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
    match_id = re.search(r"id=([a-zA-Z0-9_-]+)", url)
    if match_id:
        return match_id.group(1)
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
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📲 Instant Single Upload",
        "⏰ Daily 8-Reels Auto",
        "📊 Analytics Dashboard",
        "📋 Activity Logs",
    ]
)

# --- TAB 1: INSTANT SINGLE UPLOAD ---
with tab1:
    st.header("📲 Upload Single Reel Immediately")
    single_file = st.file_uploader(
        "Select MP4/MOV Video File", type=["mp4", "mov"], key="single_file_input"
    )
    single_caption = st.text_area(
        "Caption & Hashtags",
        placeholder="Write caption for single video...",
        key="single_cap",
    )

    if st.button("🚀 Upload Single Reel Now", use_container_width=True):
        if not single_file:
            st.error("Pehle video file select karein!")
        else:
            temp_path = f"temp_{single_file.name}"
            thumb_path = f"thumb_{single_file.name}.jpg"
            with open(temp_path, "wb") as f:
                f.write(single_file.getbuffer())

            try:
                with st.spinner("Logging in & Uploading..."):
                    # Generate explicit thumbnail to skip MoviePy auto-generation
                    generate_dummy_thumbnail(thumb_path)

                    cl = get_instagram_client()
                    media = cl.clip_upload(
                        temp_path,
                        caption=single_caption,
                        thumbnail=thumb_path,
                    )
                    st.balloons()
                    st.success(
                        f"🎉 Single Reel Uploaded! Media ID: {media.pk}"
                    )
                    add_log(
                        "Single Upload",
                        "Success",
                        f"Media ID: {media.pk}",
                    )
            except Exception as e:
                st.error(f"Error aaya: {str(e)}")
                add_log("Single Upload", "Failed", str(e))
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)

# --- TAB 2: DAILY 8-SLOT AUTOMATION ---
with tab2:
    st.header("⏰ Daily 8-Slots Auto Scheduler (Google Drive)")

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

    auto_caption = st.text_area(
        "Common Captions for All 8 Reels",
        value="#reels #viral #trending #explore #foryou",
        key="auto_cap",
    )

    st.subheader("Google Drive Links for 8 Slots")
    drive_urls = []
    cols = st.columns(4)
    for i, slot in enumerate(TIME_SLOTS):
        col_idx = i % 4
        with cols[col_idx]:
            url = st.text_input(
                f"Slot {i+1} ({slot}) Drive URL", key=f"slot_url_{i}"
            )
            drive_urls.append(url)

    def process_slot_upload(slot_index):
        url = drive_urls[slot_index]
        if not url:
            return

        file_id = get_drive_file_id(url)
        if not file_id:
            add_log(f"Slot {slot_index+1}", "Failed", "Invalid Link")
            return

        local_file = f"slot_{slot_index+1}.mp4"
        thumb_file = f"thumb_slot_{slot_index+1}.jpg"
        try:
            download_drive_file(file_id, local_file)
            generate_dummy_thumbnail(thumb_file)

            cl = get_instagram_client()
            media = cl.clip_upload(
                local_file, caption=auto_caption, thumbnail=thumb_file
            )
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
            if os.path.exists(thumb_file):
                os.remove(thumb_file)

    st.divider()
    start_auto = st.checkbox("🚀 Activate Daily 8-Reels Schedule Engine")

    if start_auto:
        st.info("Automation Running. Schedule active for 8 fixed slots...")
        schedule.clear()
        for idx, time_slot in enumerate(TIME_SLOTS):
            schedule.every().day.at(time_slot).do(process_slot_upload, idx)

        while start_auto:
            schedule.run_pending()
            time.sleep(30)

# --- TAB 3: ANALYTICS DASHBOARD ---
with tab3:
    st.header("📊 Smart Performance Analytics")
    if st.button("🔄 Sync Instagram Data"):
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
                                "Date": m.taken_at.strftime("%Y-%m-%d %H:%M"),
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

# --- TAB 4: ACTIVITY LOGS ---
with tab4:
    st.header("📋 Execution Activity Logs")
    if st.session_state.logs:
        st.dataframe(
            pd.DataFrame(st.session_state.logs), use_container_width=True
        )
    else:
        st.info("No activity recorded yet.")
