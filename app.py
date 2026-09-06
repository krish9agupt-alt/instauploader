import os
import re
import time
from datetime import datetime, timedelta
from instagrapi import Client
from PIL import Image
import pandas as pd
import requests
import schedule
import streamlit as st

st.set_page_config(
    page_title="Insta Reel Studio Pro", page_icon="⚡", layout="wide"
)

st.title("⚡ Instagram Reel Studio Pro (Fixed Session State)")

# --- 1. SESSION MANAGEMENT ---
st.header("🔑 Instagram Connection")

if "IG_USERNAME" in st.secrets and "IG_SESSIONID" in st.secrets:
    ig_username = st.secrets["IG_USERNAME"]
    ig_sessionid = st.secrets["IG_SESSIONID"]
    ig_password = None
    st.success("✅ Logged in safely via Session ID!")
else:
    col_user, col_pass = st.columns(2)
    with col_user:
        ig_username = st.text_input("Instagram Username")
    with col_pass:
        ig_password = st.text_input("Instagram Password / Session ID", type="password")
    ig_sessionid = None

st.divider()

if "logs" not in st.session_state:
    st.session_state.logs = []

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = set()

if "last_media_pk" not in st.session_state:
    st.session_state.last_media_pk = None

if "file_queue" not in st.session_state:
    st.session_state.file_queue = []


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
    img = Image.new("RGB", (720, 1280), color=(0, 0, 0))
    img.save(output_path)
    return output_path


def generate_auto_metadata(title):
    if not title:
        title = "Trending Reel"

    clean_title = title.strip()
    hashtags = f"#{clean_title.replace(' ', '')} #reels #viral #trending #explore #foryou #instagramreels"
    description = f"✨ {clean_title} ✨\n\nHope you like this video! Don't forget to Like, Comment, Share & Follow! ❤️🔥\n\n{hashtags}"

    return description


def download_drive_file(file_id, destination):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params={"id": file_id, "confirm": "t"}, stream=True)
    with open(destination, "wb") as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)


# --- NAVIGATION TABS ---
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📲 Auto Single Upload",
        "🚀 Daily 8-Reels Bulk Engine",
        "📅 Date-Wise Schedule History",
        "📋 Activity Logs",
    ]
)

TIME_SLOTS = ["08:00", "10:30", "13:00", "15:30", "18:00", "20:00", "22:00", "23:30"]

# --- TAB 1: INSTANT SINGLE UPLOAD ---
with tab1:
    st.header("📲 Single Upload (Auto Reel Linking)")

    single_file = st.file_uploader("Select MP4/MOV Video File", type=["mp4", "mov"])
    reel_title = st.text_input("📌 Input Video Title / Topic", placeholder="e.g. Chhath Puja Special")

    if reel_title:
        auto_desc = generate_auto_metadata(reel_title)
        st.info(f"🤖 **Auto Caption & Hashtags Preview:**\n\n{auto_desc}")

    target_reel_id = st.text_input("🔗 Link to Specific Reel (Optional)", placeholder="Leave blank to auto-link to previous uploaded reel")

    if st.button("🚀 Upload Single Reel Now", use_container_width=True):
        if not single_file:
            st.error("Pehle video file select karein!")
        else:
            temp_path = f"temp_{single_file.name}"
            thumb_path = f"thumb_{single_file.name}.jpg"
            with open(temp_path, "wb") as f:
                f.write(single_file.getbuffer())

            caption_final = generate_auto_metadata(reel_title)

            try:
                with st.spinner("Uploading..."):
                    generate_dummy_thumbnail(thumb_path)
                    cl = get_instagram_client()

                    media = cl.clip_upload(temp_path, caption=caption_final, thumbnail=thumb_path)

                    link_target_pk = None
                    if target_reel_id:
                        link_target_pk = cl.media_pk_from_url(target_reel_id) if "instagram.com" in target_reel_id else target_reel_id
                    elif st.session_state.last_media_pk:
                        link_target_pk = st.session_state.last_media_pk

                    linked_status = ""
                    if link_target_pk:
                        try:
                            cl.media_link_reel(media.pk, link_target_pk)
                            linked_status = f" (Auto-Linked to Reel: {link_target_pk})"
                        except Exception as l_err:
                            linked_status = f" (Link failed: {str(l_err)})"

                    st.session_state.last_media_pk = media.pk
                    st.balloons()
                    st.success(f"🎉 Reel Uploaded! Media ID: {media.pk}{linked_status}")
                    add_log("Single Auto Upload", "Success", f"Media ID: {media.pk}{linked_status}")

            except Exception as e:
                st.error(f"Error aaya: {str(e)}")
                add_log("Single Upload", "Failed", str(e))
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)


# --- TAB 2: BULK AUTO ENGINE ---
with tab2:
    st.header("🚀 Daily 8-Reels Bulk Engine")

    bulk_title = st.text_input("📌 Default Bulk Base Title / Theme", value="Daily Trending Reel")

    st.subheader("Paste All Video Drive Links / IDs (Sequence wise starting from Folder 1)")
    manual_links_input = st.text_area(
        "Paste Direct Video Share Links / IDs (1 per line):",
        height=220,
        placeholder="https://drive.google.com/file/d/1FGhEH4oWDneVunuD8pe...\nhttps://drive.google.com/file/d/2ABhEH4oWDneVunuD8pe...",
    )

    raw_list = [line.strip() for line in manual_links_input.split("\n") if line.strip()]
    if raw_list:
        temp_queue = []
        for item in raw_list:
            m = re.search(r"/d/([a-zA-Z0-9_-]+)", item)
            if m:
                temp_queue.append(m.group(1))
            elif len(item) > 15:
                temp_queue.append(item)
        st.session_state.file_queue = temp_queue

    st.info(f"📂 Total Videos Loaded in Queue: **{len(st.session_state.file_queue)}** videos.")

    def process_bulk_slot_upload(slot_index):
        if not st.session_state.file_queue:
            add_log(f"Slot {slot_index+1}", "Skipped", "Queue empty")
            return

        available_ids = [fid for fid in st.session_state.file_queue if fid not in st.session_state.uploaded_files]
        if not available_ids:
            add_log(f"Slot {slot_index+1}", "Skipped", "All queue videos uploaded!")
            return

        selected_id = available_ids[0]

        local_file = f"bulk_slot_{slot_index+1}.mp4"
        thumb_file = f"thumb_bulk_{slot_index+1}.jpg"

        auto_cap = generate_auto_metadata(f"{bulk_title} #{slot_index+1}")

        try:
            download_drive_file(selected_id, local_file)
            generate_dummy_thumbnail(thumb_file)

            cl = get_instagram_client()
            media = cl.clip_upload(local_file, caption=auto_cap, thumbnail=thumb_file)

            linked_info = ""
            if st.session_state.last_media_pk:
                try:
                    cl.media_link_reel(media.pk, st.session_state.last_media_pk)
                    linked_info = f" | Linked to Previous ({st.session_state.last_media_pk})"
                except Exception as link_e:
                    linked_info = f" | Link Error: {str(link_e)}"

            st.session_state.last_media_pk = media.pk
            st.session_state.uploaded_files.add(selected_id)

            add_log(f"Slot {slot_index+1} ({TIME_SLOTS[slot_index]})", "Success", f"Media ID: {media.pk}{linked_info}")

        except Exception as e:
            add_log(f"Slot {slot_index+1}", "Failed", str(e))
        finally:
            if os.path.exists(local_file):
                os.remove(local_file)
            if os.path.exists(thumb_file):
                os.remove(thumb_file)

    st.divider()
    start_auto = st.checkbox("🚀 Activate Daily 8-Reels Automation Engine")

    if start_auto:
        st.success("Automation Active! Daily 8-reels upload scheduler running...")
        schedule.clear()
        for idx, time_slot in enumerate(TIME_SLOTS):
            schedule.every().day.at(time_slot).do(process_bulk_slot_upload, idx)

        while start_auto:
            schedule.run_pending()
            time.sleep(30)


# --- TAB 3: DATE-WISE SCHEDULE HISTORY ---
with tab3:
    st.header("📅 Date-Wise Automatic Schedule Forecast")

    if not st.session_state.file_queue:
        st.warning("Pehle Tab 2 me videos ke links paste karein taaki schedule mapping calculate ho sake.")
    else:
        total_videos = len(st.session_state.file_queue)
        days_required = (total_videos + 7) // 8
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=days_required - 1)

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Videos Queue", f"{total_videos} Videos")
        c2.metric("Total Active Schedule Days", f"{days_required} Days")
        c3.metric("Schedule Valid Until", end_date.strftime("%d %b %Y"))

        st.subheader("📋 Date-Wise Execution Schedule History")

        schedule_data = []
        curr_date = start_date
        slot_idx = 0

        for i, fid in enumerate(st.session_state.file_queue):
            slot_time = TIME_SLOTS[slot_idx]

            schedule_data.append(
                {
                    "Video #": i + 1,
                    "Schedule Date": curr_date.strftime("%d-%m-%Y (%A)"),
                    "Slot Time": slot_time,
                    "Drive File ID": fid,
                    "Status": "Uploaded" if fid in st.session_state.uploaded_files else "Pending Auto-Upload",
                }
            )

            slot_idx += 1
            if slot_idx >= 8:
                slot_idx = 0
                curr_date += timedelta(days=1)

        df_sched = pd.DataFrame(schedule_data)
        st.dataframe(df_sched, use_container_width=True)


# --- TAB 4: ACTIVITY LOGS ---
with tab4:
    st.header("📋 Execution Activity Logs")
    if st.session_state.logs:
        st.dataframe(pd.DataFrame(st.session_state.logs), use_container_width=True)
    else:
        st.info("No activity recorded yet.")
