import yt_dlp
import sys

print(f"Python version: {sys.version}")
try:
    print(f"yt-dlp version: {yt_dlp.version.__version__}")
except Exception as e:
    print(f"Could not get yt-dlp version: {e}")

url = "https://www.tiktok.com/@mereyke36/photo/7554233714369170706"
if "/photo/" in url:
    url = url.replace("/photo/", "/video/")
    print(f"Transformed URL: {url}")

ydl_opts = {
    'verbose': True,
    'quiet': False,
    'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'extractor_args': {
        'tiktok': {
            'device_id': ['12345678901234567890'],
            'app_info': ['1'],
        }
    }
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=False)
    print("\nSUCCESS: URL is supported.")
except Exception as e:
    print(f"\nFAILURE: {e}")
