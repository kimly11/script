import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import yt_dlp

APP_TITLE = "Kimly Tool KH — TikTok Profile Downloader"

def clean_profile_url(url: str) -> str:
    url = url.strip()
    if not url:
        return url
    # Keep only the part before '?'
    url = url.split("?")[0]
    # Normalize forms like tiktok.com/@user/
    m = re.search(r"(https?://)?(www\.)?tiktok\.com/@[^/]+/?", url, flags=re.I)
    if m:
        return m.group(0)
    # If user pasted just @username or username, build a URL
    u = url.lstrip("@")
    return f"https://www.tiktok.com/@{u}"

class TikTokProfileDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x560")
        self.minsize(880, 520)

        self.stop_flag = False
        self.completed = 0
        self.download_folder = ""

        # --- Header ---
        header = tk.Frame(self, bg="#0d6efd", height=48)
        header.pack(fill="x")
        tk.Label(header, text="Kimly Tool KH", fg="white", bg="#0d6efd",
                 font=("Segoe UI", 12, "bold"), padx=16).pack(side="left")

        # --- Content ---
        content = tk.Frame(self, padx=18, pady=18)
        content.pack(fill="both", expand=True)

        tk.Label(content, text="Enter Link Profile TikTok", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        self.url_entry = tk.Entry(content, width=90, font=("Segoe UI", 10))
        self.url_entry.grid(row=1, column=0, columnspan=4, sticky="we", pady=(6, 10))
        self.url_entry.insert(0, "past link profile")

        # Folder chooser
        folder_row = tk.Frame(content)
        folder_row.grid(row=2, column=0, columnspan=4, sticky="we", pady=(2, 10))
        self.folder_lbl = tk.Label(folder_row, text="No folder selected", font=("Segoe UI", 10))
        self.folder_lbl.pack(side="left")
        tk.Button(folder_row, text="Browse Folder", command=self.choose_folder).pack(side="left", padx=12)

        # Options
        opt_row = tk.Frame(content)
        opt_row.grid(row=3, column=0, columnspan=4, sticky="w", pady=(0, 12))
        self.var_all = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_row, text="Download all", variable=self.var_all, command=self.toggle_count).pack(side="left")
        tk.Label(opt_row, text="Download (count):").pack(side="left", padx=(18, 6))
        self.count_entry = tk.Entry(opt_row, width=8)
        self.count_entry.insert(0, "10")
        self.count_entry.pack(side="left")
        self.toggle_count()  # start disabled because "all" is checked

        # Buttons
        btn_row = tk.Frame(content)
        btn_row.grid(row=4, column=0, columnspan=4, sticky="w", pady=(0, 10))
        self.btn_download = tk.Button(btn_row, text="Download", width=12, command=self.start_download)
        self.btn_stop = tk.Button(btn_row, text="Stop", width=12, command=self.stop_download)
        self.btn_clear = tk.Button(btn_row, text="Clear", width=12, command=self.clear_log)
        self.lbl_completed = tk.Label(btn_row, text="Completed [0]", font=("Segoe UI", 10, "bold"))
        self.btn_download.pack(side="left", padx=(0, 8))
        self.btn_stop.pack(side="left", padx=8)
        self.btn_clear.pack(side="left", padx=8)
        self.lbl_completed.pack(side="left", padx=16)

        # Progress
        self.progress = ttk.Progressbar(content, mode="determinate")
        self.progress.grid(row=5, column=0, columnspan=4, sticky="we", pady=(0, 10))

        # Log box
        self.log = tk.Text(content, height=14, font=("Consolas", 10), bg="#0e0e0e", fg="#e6e6e6")
        self.log.grid(row=6, column=0, columnspan=4, sticky="nsew")
        content.grid_rowconfigure(6, weight=1)
        content.grid_columnconfigure(0, weight=1)

        # Footer
        footer = tk.Frame(self, bg="#0d6efd", height=44)
        footer.pack(fill="x", side="bottom")
        tk.Label(footer, text="KHMER 01", fg="white", bg="#0d6efd",
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=16)
        tk.Label(footer, text="Copyright © 2025 - All rights reserved",
                 fg="white", bg="#0d6efd", font=("Segoe UI", 10)).pack(side="right", padx=16)

    # --- UI helpers ---
    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_folder = folder
            self.folder_lbl.config(text=folder)

    def toggle_count(self):
        state = "disabled" if self.var_all.get() else "normal"
        self.count_entry.config(state=state)

    def log_line(self, s: str):
        self.log.insert("end", s + "\n")
        self.log.see("end")

    def clear_log(self):
        self.log.delete("1.0", "end")
        self.completed = 0
        self.lbl_completed.config(text=f"Completed [{self.completed}]")
        self.progress["value"] = 0

    def stop_download(self):
        self.stop_flag = True
        self.log_line("⛔ Stopping…")

    # --- Download logic ---
    def start_download(self):
        url = clean_profile_url(self.url_entry.get())
        if not url:
            messagebox.showerror("Error", "Please enter TikTok profile link.")
            return
        if not self.download_folder:
            messagebox.showerror("Error", "Please choose a download folder.")
            return

        # Count
        count = None
        if not self.var_all.get():
            try:
                c = int(self.count_entry.get())
                if c <= 0:
                    raise ValueError
                count = c
            except Exception:
                messagebox.showerror("Error", "Download count must be a positive number.")
                return

        self.clear_log()
        self.stop_flag = False
        self.btn_download.config(state="disabled")
        t = threading.Thread(target=self._download_thread, args=(url, count), daemon=True)
        t.start()

    def _download_thread(self, profile_url: str, count: int | None):
        self.log_line(f"🔗 Profile: {profile_url}")
        self.log_line("📥 Preparing…")

        # yt-dlp options:
        # - TikTok: yt-dlp retrieves the *no-watermark* play URLs automatically.
        # - Pass the profile URL directly; it's treated as a playlist of that user's posts.
        ydl_opts = {
            "outtmpl": os.path.join(self.download_folder, "%(uploader)s_%(id)s.%(ext)s"),
            "merge_output_format": "mp4",
            "ignoreerrors": True,
            "continuedl": True,
            "retries": 5,
            "fragment_retries": 5,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": False,
            "concurrent_fragment_downloads": 3,
            "progress_hooks": [self._progress_hook],
        }

        # Limit how many from the playlist
        if count is not None:
            ydl_opts["playlistend"] = count

        try:
            # First pass to know playlist length (for progress bar max)
            with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": "in_playlist"}) as probe:
                info = probe.extract_info(profile_url, download=False)
            entries = info.get("entries") or []
            total = len(entries) if count is None else min(len(entries), count)
            if total == 0:
                self.log_line("⚠️ No videos found.")
                self.btn_download.config(state="normal")
                return

            self.progress["maximum"] = total
            self.progress["value"] = 0
            self.log_line(f"Found {total} video(s). Starting download…")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([profile_url])

            if not self.stop_flag:
                self.log_line("✅ All done.")
        except Exception as e:
            self.log_line(f"❌ Error: {e}")
        finally:
            self.btn_download.config(state="normal")

    def _progress_hook(self, d):
        # Called for each fragment and at 'finished'
        if self.stop_flag:
            raise KeyboardInterrupt("Stopped by user")

        if d.get("status") == "finished":
            self.completed += 1
            self.lbl_completed.config(text=f"Completed [{self.completed}]")
            self.progress["value"] = self.completed
            self.log_line(f"⬇️ Saved: {os.path.basename(d.get('filename',''))}")
        elif d.get("status") == "downloading":
            # Optional: live per-file speed/ETA in the status bar
            eta = d.get("_eta_str") or ""
            speed = d.get("_speed_str") or ""
            total = d.get("_total_bytes_str") or d.get("_total_bytes_estimate_str") or ""
            downloaded = d.get("_downloaded_bytes_str") or ""
            self.log_line(f"… {downloaded}/{total} {speed} ETA {eta}")

if __name__ == "__main__":
    app = TikTokProfileDownloader()
    app.mainloop()
