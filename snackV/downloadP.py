import os
import re
import threading
import requests
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import yt_dlp

# Global flag for stopping
stop_flag = False


# ====== Scraper: Get all video links from a SnackVideo profile ======
def get_profile_videos(profile_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(profile_url, headers=headers)
        if r.status_code != 200:
            return []
        # Extract video URLs
        links = re.findall(r'https://www\.snackvideo\.com/@[A-Za-z0-9._-]+/video/\d+', r.text)
        return list(set(links))  # unique only
    except Exception as e:
        print("Scraper error:", e)
        return []


# ====== Downloader ======
def download_video(url, folder, log_box):
    ydl_opts = {
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        log_box.insert(tk.END, f"✅ Downloaded: {url}\n")
        log_box.see(tk.END)
    except Exception as e:
        log_box.insert(tk.END, f"❌ Error: {e}\n")
        log_box.see(tk.END)


def start_download(url, folder, log_box, all_videos=True, limit=None):
    global stop_flag
    stop_flag = False

    def run():
        nonlocal url, folder, log_box, all_videos, limit

        if all_videos:
            links = get_profile_videos(url)
            if not links:
                log_box.insert(tk.END, "❌ No videos found in profile.\n")
                return
            log_box.insert(tk.END, f"🔍 Found {len(links)} videos.\n")
            count = 0
            for link in links:
                if stop_flag:
                    log_box.insert(tk.END, "⏹ Download stopped by user.\n")
                    break
                if limit and count >= limit:
                    break
                download_video(link, folder, log_box)
                count += 1
        else:
            download_video(url, folder, log_box)

        log_box.insert(tk.END, "🎉 Completed!\n")

    threading.Thread(target=run, daemon=True).start()


# ====== GUI ======
def build_gui():
    global stop_flag
    root = tk.Tk()
    root.title("SnackVideo Downloader KH")
    root.geometry("800x550")
    root.configure(bg="white")

    save_path = tk.StringVar(value="")

    # Title
    tk.Label(root, text="SnackVideo Downloader", font=("Arial", 16, "bold"), bg="white").pack(pady=10)

    # Input URL
    tk.Label(root, text="Enter SnackVideo Link / Profile:", bg="white").pack()
    url_entry = tk.Entry(root, width=90)
    url_entry.pack(pady=5)

    # Folder select
    def browse_folder():
        folder = filedialog.askdirectory()
        if folder:
            save_path.set(folder)

    tk.Button(root, text="Browse Folder", command=browse_folder, bg="lightgray").pack()
    tk.Label(root, textvariable=save_path, bg="white", fg="blue").pack()

    # Options
    all_videos = tk.BooleanVar(value=True)
    tk.Checkbutton(root, text="Download all from profile", variable=all_videos, bg="white").pack()

    tk.Label(root, text="Download limit (optional):", bg="white").pack()
    limit_entry = tk.Entry(root, width=10)
    limit_entry.pack()

    # Log box
    log_box = scrolledtext.ScrolledText(root, width=95, height=18, bg="black", fg="white")
    log_box.pack(pady=10)

    # Buttons
    button_frame = tk.Frame(root, bg="white")
    button_frame.pack()

    def start():
        url = url_entry.get().strip()
        folder = save_path.get()
        if not url or not folder:
            messagebox.showerror("Error", "Please enter URL and select folder.")
            return
        try:
            limit = int(limit_entry.get()) if limit_entry.get().strip() else None
        except:
            limit = None
        log_box.insert(tk.END, f"🚀 Starting download...\n")
        start_download(url, folder, log_box, all_videos.get(), limit)

    def stop():
        global stop_flag
        stop_flag = True

    def clear():
        log_box.delete("1.0", tk.END)

    tk.Button(button_frame, text="Download", command=start, bg="lightgray", width=12).grid(row=0, column=0, padx=5)
    tk.Button(button_frame, text="Stop", command=stop, bg="lightgray", width=12).grid(row=0, column=1, padx=5)
    tk.Button(button_frame, text="Clear", command=clear, bg="lightgray", width=12).grid(row=0, column=2, padx=5)

    root.mainloop()


if __name__ == "__main__":
    build_gui()
