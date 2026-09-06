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
    page_title="Insta Reel Studio Pro", page_icon="⚡", layout="wide"
)

st.title("⚡ Instagram Reel Studio Pro (Multi-Folder Auto Fetch)")

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


def get_drive_id(url):
    match = re.search(r"/folders/([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1), "folder"
    match_file = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if match_file:
        return match_file.group(1), "file"
    match_id = re.search(r"id=([a-zA-Z0-9_-]+)", url)
    if match_id:
        return match_id.group(1), "file"
    return None, None


def extract_files_from_drive_folder(folder_url):
    """Scrapes/Extracts direct downloadable video file IDs from public Google Drive folders/sub-folders"""
    folder_id, link_type = get_drive_id(folder_url)
    if not folder_id:
        return []
    
    file_ids = []
    try:
        # Fetch web view to parse file IDs
        scrape_url = f"https://drive.google.com/embeddedfolderview?id={folder_id}"
        resp = requests.get(scrape_url)
        if resp.status_code == 200:
            found_ids = re.findall(r'id=([a-zA-Z0-9_-]{25,})', resp.text)
            for fid in found_ids:
                if fid != folder_id and fid not in file_ids:
                    file_ids.append(fid)
    except Exception as e:
        pass
    
    return file_ids


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
        "🚀 Main Folder 8-Reels Daily Engine",
        "📊 Analytics",
        "📋 Activity Logs",
    ]
)

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


# --- TAB 2: MAIN FOLDER DIRECT AUTO ENGINE ---
with tab2:
    st.header("🚀 Main Drive Folder Multi-Subfolder Auto Engine")
    st.markdown("Direct apna **Main Folder Link** paste karein. System andar ke sabhi 32 folders ke videos auto-extract karke daily 8 slots par upload karega.")

    TIME_SLOTS = ["08:00", "10:30", "13:00", "15:30", "18:00", "20:00", "22:00", "23:30"]

    bulk_title = st.text_input("📌 Default Bulk Base Title / Theme", value="Daily Trending Video")
    
    main_folder_url = st.text_input("📂 Main Google Drive Folder Link", value="https://drive.google.com/drive/folders/10eyQKQ7VzvePaVVXFdXzQyIB-ossDsfQ")

    detected_file_ids = []
    if main_folder_url:
        with st.spinner("Fetching all videos from main folder & 32 sub-folders..."):
            detected_file_ids = extract_files_from_drive_folder(main_folder_url)
            st.success(f"📁 Total Videos Auto-Detected from Subfolders: **{len(detected_file_ids)}** videos found!")

    def process_bulk_slot_upload(slot_index):
        if not detected_file_ids:
            add_log(f"Slot {slot_index+1}", "Skipped", "No videos detected in folder")
            return

        available_ids = [fid for fid in detected_file_ids if fid not in st.session_state.uploaded_files]
        if not available_ids:
            add_log(f"Slot {slot_index+1}", "Skipped", "All folder videos uploaded!")
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
    start_auto = st.checkbox("🚀 Activate Daily 8-Reels Bulk Engine")

    if start_auto:
        st.info("Automation Running. Schedule active for 8 fixed slots daily...")
        schedule.clear()
        for idx, time_slot in enumerate(TIME_SLOTS):
            schedule.every().day.at(time_slot).do(process_bulk_slot_upload, idx)

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
                        views = m.play_count if hasattr(m, "play_count") and m.play_count else 0
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
        st.dataframe(pd.DataFrame(st.session_state.logs), use_container_width=True)
    else:
        st.info("No activity recorded yet.")
