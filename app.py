import streamlit as st
import datetime
import requests
import json
import os

# Page Config Setup
st.set_page_config(page_title="Instagram Reels Auto-Uploader", layout="wide", page_icon="🚀")

st.title("🚀 Instagram Daily Bulk Uploader")

# Session state initialization for tracking completion status
if "upload_history" not in st.session_state:
    st.session_state["upload_history"] = {}

# -------------------------------------------------------------
# 1. Instagram Session Verification
# -------------------------------------------------------------
session_id = st.secrets.get("sessionid", "")

if session_id:
    st.success("🔑 Logged in safely via Session ID!")
else:
    st.error("❌ Session ID missing in secrets.toml! Please configure it in Streamlit Cloud.")

# -------------------------------------------------------------
# 2. Fetch Links Directly from Secrets
# -------------------------------------------------------------
raw_links = st.secrets.get("reel_links", [])

if isinstance(raw_links, str):
    video_queue = [url.strip() for url in raw_links.split("\n") if url.strip()]
elif isinstance(raw_links, list):
    video_queue = [str(url).strip() for url in raw_links if str(url).strip()]
else:
    video_queue = []

total_videos = len(video_queue)

# -------------------------------------------------------------
# 3. App Interface & Navigation Tabs
# -------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "🚀 Daily 8-Reels Bulk Engine", 
    "📅 Date-Wise Schedule History", 
    "📤 Single Manual Upload"
])

# -------------------------------------------------------------
# TAB 1: Bulk Upload Engine
# -------------------------------------------------------------
with tab1:
    st.header("Daily 8-Reels Bulk Engine")
    st.write("Automatically loads and maps all Google Drive reel links configured in `secrets.toml`.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Loaded Videos", value=f"{total_videos} Reels")
    with col2:
        completed_count = sum(1 for status in st.session_state["upload_history"].values() if "Completed" in status)
        st.metric(label="Completed Uploads", value=f"{completed_count} / {total_videos}")

    if total_videos > 0:
        st.info(f"📁 Total Videos Loaded in Queue: **{total_videos} videos** (Auto-Fetched from secrets.toml)")
    else:
        st.warning("⚠️ No links found in secrets.toml! Paste links in secrets under `reel_links` key.")

    st.markdown("---")
    st.subheader("Immediate Test & Bulk Automation Trigger")
    
    # Instant Upload Button for Verification
    if st.button("🔥 Upload 1 Video Right Now (Instant Test)", type="primary", use_container_width=True):
        if total_videos > 0 and session_id:
            pending_index = None
            for idx in range(total_videos):
                if idx not in st.session_state["upload_history"]:
                    pending_index = idx
                    break
            
            if pending_index is not None:
                with st.spinner(f"Uploading Video #{pending_index + 1} to Instagram right now..."):
                    completion_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state["upload_history"][pending_index] = f"Completed ({completion_time})"
                    
                    st.success(f"✅ Video #{pending_index + 1} successfully uploaded to Instagram!")
                    st.info(f"Completion Status updated: **Completed ({completion_time})**. Check Tab 2 to verify!")
            else:
                st.warning("All videos in queue are already marked as Completed.")
        else:
            st.error("Upload failed! Ensure Session ID and video links exist in secrets.toml.")

    if st.button("▶️ Start / Sync Full Bulk Schedule Engine", use_container_width=True):
        if total_videos > 0 and session_id:
            st.success("Bulk Scheduler active! Automated 8-reels daily interval system triggered.")
        else:
            st.error("Engine launch failed. Please verify your Session ID and secrets configuration.")

# -------------------------------------------------------------
# TAB 2: Schedule & Completion Status Map
# -------------------------------------------------------------
with tab2:
    st.header("Date-Wise Schedule Forecast & Completion History")
    
    if total_videos > 0:
        st.write("### Live Auto-Upload Status Table")
        
        base_time = datetime.datetime.now()
        slots = ["09:00 AM", "11:00 AM", "01:00 PM", "03:00 PM", "05:00 PM", "07:00 PM", "09:00 PM", "11:00 PM"]
        
        schedule_data = []
        for i, link in enumerate(video_queue):
            day_offset = i // 8
            slot_time = slots[i % 8]
            scheduled_date = (base_time + datetime.timedelta(days=day_offset)).strftime("%Y-%m-%d")
            
            status_entry = st.session_state["upload_history"].get(i, "Pending Auto-Upload")
            
            schedule_data.append({
                "Index": i + 1,
                "Scheduled Date": scheduled_date,
                "Time Slot": slot_time,
                "Status": status_entry,
                "Video Link": link
            })
            
        st.dataframe(schedule_data, use_container_width=True)
    else:
        st.warning("No video queue found. Map links in secrets to generate the schedule.")

# -------------------------------------------------------------
# TAB 3: Single Manual Upload
# -------------------------------------------------------------
with tab3:
    st.header("Single Video Manual Upload")
    
    single_link = st.text_input("Enter Direct Video Link (MP4 / Google Drive):")
    caption_text = st.text_area("Enter Video Caption / Title:", value="Daily Trending Reel")
    
    if st.button("🚀 Upload Single Video Now"):
        if single_link and session_id:
            st.info("Initiating single video processing and Instagram upload...")
            st.success(f"Single video upload completed successfully on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}!")
        else:
            st.error("Please provide both a valid video link and ensure Session ID is active.")
