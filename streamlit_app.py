import streamlit as st
import re
import json
import os
import subprocess
import zipfile
from io import BytesIO

st.set_page_config(page_title="Amazon Video Downloader", page_icon="🎬", layout="centered")

st.title("🎬 Amazon ASIN Video Downloader")
st.markdown("Paste your data below. This version is extra-safe against formatting errors.")

raw_data = st.text_area("Paste Raw Data Here:", height=250, placeholder="B088GG1XJC {{...}}")

if st.button("🚀 Start Downloading"):
    if not raw_data.strip():
        st.warning("Please paste some data first!")
    else:
        # 1. Extract ASIN
        asin_match = re.search(r'[A-Z0-9]{10}', raw_data)
        asin = asin_match.group(0) if asin_match else "DOWNLOADED_VIDEO"
        
        # 2. Extract the JSON content even if it has extra brackets {{ }}
        # This regex looks for anything between the first { or [ and the last } or ]
        json_match = re.search(r'([\[\{].*[\]\}])', raw_data.replace('\n', ''), re.DOTALL)
        
        if json_match:
            data_str = json_match.group(0)
            
            # Clean up double brackets {{ }} which often cause crashes
            if data_str.startswith('{{'):
                data_str = data_str[1:-1]
            
            try:
                video_list = json.loads(data_str)
                
                # If the JSON is a single object, wrap it in a list
                if isinstance(video_list, dict):
                    video_list = [video_list]
                
                st.info(f"Detected ASIN: **{asin}** | Found **{len(video_list)}** videos.")
                
                download_dir = "downloads_folder"
                os.makedirs(download_dir, exist_ok=True)
                
                downloaded_paths = []
                progress_bar = st.progress(0)
                status_text = st.empty()

                for index, video in enumerate(video_list, start=1):
                    video_url = video.get('url')
                    if not video_url: continue
                    
                    file_name = f"{asin}.{index}.mp4"
                    save_path = os.path.join(download_dir, file_name)
                    
                    status_text.text(f"Downloading {file_name}...")
                    
                    # Run yt-dlp
                    result = subprocess.run(['yt-dlp', '-o', save_path, video_url], capture_output=True)
                    
                    if os.path.exists(save_path):
                        downloaded_paths.append(save_path)
                    
                    progress_bar.progress(index / len(video_list))

                if downloaded_paths:
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w") as zf:
                        for file_path in downloaded_paths:
                            zf.write(file_path, os.path.basename(file_path))
                            os.remove(file_path)
                    
                    st.success("✅ Process Complete!")
                    st.download_button(
                        label="📥 Download ZIP Package",
                        data=zip_buffer.getvalue(),
                        file_name=f"{asin}_videos.zip",
                        mime="application/zip"
                    )
                else:
                    st.error("Downloads failed. Check if the links are still active.")

            except Exception as e:
                st.error(f"Data Error: We found the text but couldn't read it as a list. Error: {e}")
        else:
            st.error("No valid video data found. Try copying the entire block again.")

st.divider()
st.caption("Powered by yt-dlp & FFmpeg")
