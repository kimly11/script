from curl_cffi import requests

url = "https://www.tiktok.com/@tiktok/video/7586198416506506517"

try:
    print(f"Fetching {url}...")
    # Impersonate Chrome 120
    r = requests.get(url, impersonate="chrome120", timeout=10)
    print(f"Status Code: {r.status_code}")
    print(f"Title in HTML: {'<title>' in r.text}")
    
    if "verify" in r.text.lower() or "captcha" in r.text.lower():
        print("DETECTED: Verify/Captcha challenge found in response.")
    else:
        print("No obvious captcha text found.")

    # Print a snippet
    print(r.text[:500])

except Exception as e:
    print(f"Error: {e}")
