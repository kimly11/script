import yt_dlp
import sys

# ID from the user's error message
video_id = "7569958926309952788"
url = f"https://www.tiktok.com/@tiktok/video/{video_id}"

print(f"Testing extraction for: {url}")

opts = {
    'quiet': False,
    'verbose': True,
    # Using the same UA as the main script to reproduce exactly
    # "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "impersonate": "chrome120",
}

try:
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.extract_info(url, download=False)
    print("SUCCESS: Extraction worked!")
except Exception as e:
    print(f"FAILURE: {e}")
    sys.exit(1)
