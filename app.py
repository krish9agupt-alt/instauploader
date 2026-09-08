import streamlit as st
import datetime
import random

# Instagram ke best engagement times (Subah, Dopehar, Shaam)
BEST_INSTA_TIMES = [
    datetime.time(9, 0),   # 9:00 AM
    datetime.time(12, 0),  # 12:00 PM
    datetime.time(15, 0),  # 3:00 PM
    datetime.time(18, 0),  # 6:00 PM
    datetime.time(20, 0),  # 8:00 PM
]

def generate_ai_caption_and_hashtags():
    """AI Caption aur Hashtags generate karne ka function"""
    captions = [
        "Wait for the end! 🤯", 
        "What do you think about this? 👇", 
        "Mind blown! 🔥", 
        "Tag someone who needs to see this! 🚀",
        "Absolutely amazing! 💯"
    ]
    hashtags_pool = ["#reels", "#viral", "#explorepage", "#trending", "#foryou", "#instagramreels", "#fyp"]
    
    caption = random.choice(captions)
    hashtags = " ".join(random.sample(hashtags_pool, 4)) # Koi bhi 4 random hashtags
    return f"{caption}\n\n{hashtags}"

# --- Main Logic ---

st.subheader("Bulk Google Drive Link Queue")
st.write("Neeche diye gaye box me ek sath 8 ya jitne chahein Google Drive links paste karein (har link ek nayi line me hona chahiye).")

# 1. Links Input Box
links_input = st.text_area("Paste Google Drive Links (One per line)", height=150)

# Links ko line ke hisaab se alag karna
links_list = [link.strip() for link in links_input.split('\n') if link.strip()]

scheduled_data = []

# 2. Dynamic Time Boxes (Agar links paste kiye gaye hain toh hi dikhenge)
if links_list:
    st.success(f"✅ {len(links_list)} Links detected! Set timings for each video below:")
    
    for i, link in enumerate(links_list):
        # Har video ke liye best time suggest karna loop ke hisaab se
        suggested_time = BEST_INSTA_TIMES[i % len(BEST_INSTA_TIMES)]
        
        with st.expander(f"⚙️ Video {i+1} Settings (Link: {link[:30]}...)", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                # Custom Time Box
                custom_time = st.time_input(f"Upload Time for Video {i+1}", value=suggested_time, key=f"time_{i}")
            
            with col2:
                # Generate Random AI Caption
                ai_caption = generate_ai_caption_and_hashtags()
                final_caption = st.text_area(f"AI Caption & Hashtags", value=ai_caption, key=f"cap_{i}")
            
            # Save data for the final upload loop
            scheduled_data.append({
                "video_number": i + 1,
                "link": link,
                "time": custom_time,
                "caption": final_caption
            })

# 3. One-by-One Processing & Uploading
if st.button("🚀 Start Batch Upload for All Links"):
    if not scheduled_data:
        st.error("Please paste at least one link first!")
    else:
        st.info("Starting upload process... Picking links one by one.")
        
        # Har ek link ko ek-ek karke process karein
        for data in scheduled_data:
            with st.spinner(f"Processing Video {data['video_number']}..."):
                # Yahan aapki downloading, thumbnail generation aur uploading API aayegi
                
                # Note: Random thumbnail ke liye aap `moviepy` library use karke 
                # video ke random frame (jaise t=2 sec) par image capture kar sakte hain.
                # Example: clip = VideoFileClip("video.mp4"); clip.save_frame("thumb.jpg", t=random.randint(1, 5))
                
                st.success(f"✅ Video {data['video_number']} Scheduled Successfully!")
                st.write(f"**Scheduled For:** {data['time']}")
                st.write(f"**Caption Used:** {data['caption']}")
                st.divider()
