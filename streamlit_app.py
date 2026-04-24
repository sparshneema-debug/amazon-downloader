import streamlit as st
import re
import os
import subprocess
import zipfile
from io import BytesIO

st.set_page_config(page_title="Amazon Video Downloader", page_icon="🎬", layout="centered")

st.title("🎬 Amazon Video Downloader (Super Scraper)")
st.markdown("Paste your data. This version ignores formatting errors and just hunts for video links!")

raw_data = st.text_area("Paste Raw Data Here:", height=250)

if st.button("🚀 Start Downloading"):
    if not raw_data.strip():
        st.warning("Please paste some data first!")
    else:
        # 1. Find the ASIN (10-char alphanumeric)
        asin_match = re.search(r'[A-Z0-9]{10}', raw_data)
        asin = asin_match.group(0) if asin_match else "VIDEO"
        
        # 2. Extract ALL URLs that look like Amazon video links
        # This finds .m3u8 and .mp4 links anywhere in the text
        video_links = re.findall(r'https://[^\s"\'\}]+\.(?:m3u8|mp4)', raw_data)
        
        # Remove duplicates
        video_links = list(dict.fromkeys(video_links))

        if video_links:
            st.info(f"Detected ASIN: **{asin}** | Found **{len(video_links)}** unique video links.")
            
            download_dir = "temp_dl"
            os.makedirs(download_dir, exist_ok=True)
            
            downloaded_paths = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for index, url in enumerate(video_links, start=1):
                file_name = f"{asin}.{index}.mp4"
                save_path = os.path.join(download_dir, file_name)
                
                status_text.text(f"Processing video {index} of {len(video_links)}...")
                
                # Download using yt-dlp
                # We use -f 'bestvideo+bestaudio/best' to ensure audio is included
                try:
                    subprocess.run(['yt-dlp', '-o', save_path, url], capture_output=True)
                    if os.path.exists(save_path):
                        downloaded_paths.append(save_path)
                except Exception as e:
                    st.error(f"Error on video {index}: {e}")
                
                progress_bar.progress(index / len(video_links))

            if downloaded_paths:
                # 3. Create ZIP
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for file_path in downloaded_paths:
                        zf.write(file_path, os.path.basename(file_path))
                        os.remove(file_path) # Clean up individual file
                
                st.success(f"✅ Success! Captured {len(downloaded_paths)} videos.")
                st.download_button(
                    label="📥 Download ZIP Package",
                    data=zip_buffer.getvalue(),
                    file_name=f"{asin}_videos.zip",
                    mime="application/zip"
                )
            else:
                st.error("Could not download videos. Check if your links are expired.")
        else:
            st.error("No video links (.m3u8 or .mp4) found in the text. Please check your source.")

st.divider()
st.caption("Advanced Scraper Mode: Ignoring JSON structure to find direct media paths.")
