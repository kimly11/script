import yt_dlp
import os
import sys

# Parameters mimicking the app
video_url = "https://www.tiktok.com/@tiktok/video/7569958926309952788"
download_folder = "."

# Replicating linkvideo.py logic
if "/photo/" in video_url:
    print("ℹ️ Detected photo URL, applying fix…")
    video_url = video_url.replace("/photo/", "/video/")

print(f"🔗 Video: {video_url}")

ydl_opts = {
    # Using simplistic outtmpl for testing
    "outtmpl": os.path.join(download_folder, "%(uploader)s_%(id)s.%(ext)s"),
    "merge_output_format": "mp4",
    "quiet": False, # Changed to False to see output
    "no_warnings": False, # Changed to False
    # "progress_hooks": [self._progress_hook], # Skipped for headless
    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
}

print(f"Running with opts: {ydl_opts}")

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    print("✅ Video downloaded successfully.")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
