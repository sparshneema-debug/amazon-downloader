import streamlit as st
import re
import json
import os
import subprocess
import zipfile
from io import BytesIO

# --- Page Configuration ---
st.set_page_config(page_title="Amazon Video Downloader", page_icon="🎬", layout="centered")

st.title("🎬 Amazon ASIN Video Downloader")
st.markdown("""
Paste the raw data (ASIN followed by the JSON array) into the box below. 
The app will extract the videos, rename them, and bundle them into a ZIP file for you.
""")

# --- Input Area ---
raw_data = st.text_area("Paste Raw Data Here:", height=250, placeholder="B0797KV92C [{...}]")

if st.button("🚀 Start Downloading"):
    if not raw_data.strip():
        st.warning("Please paste some data first!")
    else:
        # 1. Extract ASIN (10-character alphanumeric)
        asin_match = re.search(r'[A-Z0-9]{10}', raw_data)
        asin = asin_match.group(0) if asin_match else "DOWNLOADED_VIDEO"
        
        # 2. Extract JSON array (stuff inside [ ])
        json_str_match = re.search(r'\[.*\]', raw_data.replace('\n', ''))
        
        if json_str_match:
            try:
                video_list = json.loads(json_str_match.group(0))
                num_videos = len(video_list)
                st.info(f"Detected ASIN: **{asin}** | Found **{num_videos}** videos.")
                
                # Setup Download Directory
                download_dir = "temp_videos"
                if not os.path.exists(download_dir):
                    os.makedirs(download_dir)
                
                downloaded_paths = []
                progress_bar = st.progress(0)
                status_text = st.empty()

                # 3. Process each video
                for index, video in enumerate(video_list, start=1):
                    video_url = video.get('url')
                    if not video_url:
                        continue
                    
                    # Formatting filename: ASIN.1.mp4, ASIN.2.mp4...
                    file_name = f"{asin}.{index}.mp4"
                    save_path = os.path.join(download_dir, file_name)
                    
                    status_text.text(f"Downloading {file_name}...")
                    
                    # Run yt-dlp command
                    # -o specifies output path, -q for quiet mode
                    try:
                        subprocess.run(['yt-dlp', '-q', '-o', save_path, video_url], check=True)
                        downloaded_paths.append(save_path)
                    except Exception as e:
                        st.error(f"Failed to download video {index}: {e}")
                    
                    # Update Progress
                    progress_bar.progress(index / num_videos)

                # 4. Create ZIP in memory
                if downloaded_paths:
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w") as zf:
                        for file_path in downloaded_paths:
                            zf.write(file_path, os.path.basename(file_path))
                            # Clean up file after adding to zip
                            os.remove(file_path)
                    
                    status_text.text("✅ All videos processed!")
                    st.success(f"Successfully processed {len(downloaded_paths)} videos.")
                    
                    # 5. Download Button
                    st.download_button(
                        label="📥 Download ZIP Package",
                        data=zip_buffer.getvalue(),
                        file_name=f"{asin}_videos.zip",
                        mime="application/zip"
                    )
                
                # Cleanup directory
                if os.path.exists(download_dir):
                    os.rmdir(download_dir)

            except json.JSONDecodeError:
                st.error("Error: The JSON format in your text is invalid.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
        else:
            st.error("Could not find a valid list of videos in the text provided.")

# --- Footer ---
st.divider()
st.caption("Note: This tool uses yt-dlp and ffmpeg to merge HLS streams into high-quality MP4s.")
