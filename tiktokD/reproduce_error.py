import yt_dlp
import traceback

def test_tiktok(url):
    ydl_opts = {
        "quiet": False,
        "no_warnings": False,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "extractor_args": {"tiktok": {"impersonate": [""]}},
    }
    
    print(f"Testing URL: {url}")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            print("Successfully extracted info!")
            print(f"Title: {info.get('title')}")
    except Exception as e:
        print(f"Error: {e}")
        # traceback.print_exc()

if __name__ == "__main__":
    url = "https://www.tiktok.com/@na.jelly07/video/7555001157899390216"
    print("--- Test 1: Original Options ---")
    test_tiktok(url)
    
    print("\n--- Test 2: With Impersonate chrome ---")
    ydl_opts_2 = {
        "quiet": False,
        "impersonate": "chrome",
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts_2) as ydl:
             info = ydl.extract_info(url, download=False)
             print("Successfully extracted info with impersonate chrome!")
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- Test 3: With Impersonate chrome-110 ---")
    ydl_opts_3 = {
        "quiet": False,
        "impersonate": "chrome-110",
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts_3) as ydl:
             info = ydl.extract_info(url, download=False)
             print("Successfully extracted info with impersonate chrome-110!")
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- Test 4: With Mobile User Agent ---")
    ydl_opts_mobile = {
        "quiet": False,
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts_mobile) as ydl:
             info = ydl.extract_info(url, download=False)
             print("Successfully extracted info with Mobile UA!")
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- Test 5: Without User Agent / Impersonate (Default) ---")
    try:
        with yt_dlp.YoutubeDL({"quiet": False}) as ydl:
             info = ydl.extract_info(url, download=False)
             print("Successfully extracted info with default!")
    except Exception as e:
        print(f"Error: {e}")
