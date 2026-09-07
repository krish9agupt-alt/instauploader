import os
import re
import requests
from datetime import datetime
from instagrapi import Client
from PIL import Image

# Secrets se Credentials
IG_USERNAME = os.environ.get("IG_USERNAME")
IG_SESSIONID = os.environ.get("IG_SESSIONID")
LINKS_RAW = os.environ.get("REEL_LINKS")  # 3110 links separated by newline

TIME_SLOTS = ["08:00", "10:30", "13:00", "15:30", "18:00", "20:00", "22:00", "23:30"]

def get_instagram_client():
    cl = Client()
    cl.set_user_agent("Instagram 269.0.0.18.75 Android")
    if IG_SESSIONID:
        cl.login_by_sessionid(IG_SESSIONID)
    else:
        cl.login(IG_USERNAME, os.environ.get("IG_PASSWORD"))
    return cl

def download_drive_file(file_id, destination="video.mp4"):
    url = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(url, params={"id": file_id, "confirm": "t"}, stream=True)
    with open(destination, "wb") as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)

def run_upload():
    # File IDs parse karein
    raw_list = [line.strip() for line in LINKS_RAW.split("\n") if line.strip()]
    file_ids = []
    for item in raw_list:
        m = re.search(r"/d/([a-zA-Z0-9_-]+)", item)
        if m:
            file_ids.append(m.group(1))
        elif len(item) > 15:
            file_ids.append(item)

    if not file_ids:
        print("No video links found!")
        return

    # Track uploaded video index using a simple state file or logic
    tracking_file = "uploaded_count.txt"
    curr_index = 0
    if os.path.exists(tracking_file):
        with open(tracking_file, "r") as f:
            curr_index = int(f.read().strip())

    if curr_index >= len(file_ids):
        print("All 3,110 videos uploaded!")
        return

    selected_id = file_ids[curr_index]
    print(f"Uploading Video #{curr_index + 1} ID: {selected_id}")

    # Download & Thumbnail
    download_drive_file(selected_id, "temp.mp4")
    img = Image.new("RGB", (720, 1280), color=(0, 0, 0))
    img.save("thumb.jpg")

    # Caption
    caption = f"✨ Trending Reel #{curr_index + 1} ✨\n\nFollow for more! ❤️🔥\n\n#reels #viral #trending #explore"

    cl = get_instagram_client()
    media = cl.clip_upload("temp.mp4", caption=caption, thumbnail="thumb.jpg")
    print(f"✅ Success! Media ID: {media.pk}")

    # Update state index
    with open(tracking_file, "w") as f:
        f.write(str(curr_index + 1))

    # Clean up
    if os.path.exists("temp.mp4"): os.remove("temp.mp4")
    if os.path.exists("thumb.jpg"): os.remove("thumb.jpg")

if __name__ == "__main__":
    run_upload()

