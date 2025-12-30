import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import yt_dlp

APP_TITLE = "Kimly Tool KH — TikTok Downloader"

def clean_profile_url(url: str) -> str:
    url = url.strip()
    if not url:
        return url
    url = url.split("?")[0]
    m = re.search(r"(https?://)?(www\.)?tiktok\.com/@[^/]+/?", url, flags=re.I)
    if m:
        return m.group(0)
    u = url.lstrip("@")
    return f"https://www.tiktok.com/@{u}"

class TikTokDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x600")
        self.minsize(880, 560)

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

        # Profile input
        tk.Label(content, text="Enter TikTok Profile Link", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w")
        self.profile_entry = tk.Entry(content, width=90, font=("Segoe UI", 10))
        self.profile_entry.grid(row=1, column=0, columnspan=4, sticky="we", pady=(4, 10))
        self.profile_entry.insert(0, "https://www.tiktok.com/@khon_kimly")

        # Video input
        tk.Label(content, text="Enter TikTok Video Link", font=("Segoe UI", 11, "bold")).grid(row=2, column=0, sticky="w")
        self.video_entry = tk.Entry(content, width=90, font=("Segoe UI", 10))
        self.video_entry.grid(row=3, column=0, columnspan=4, sticky="we", pady=(4, 10))

        # Folder chooser
        folder_row = tk.Frame(content)
        folder_row.grid(row=4, column=0, columnspan=4, sticky="we", pady=(2, 12))
        self.folder_lbl = tk.Label(folder_row, text="No folder selected", font=("Segoe UI", 10))
        self.folder_lbl.pack(side="left")
        tk.Button(folder_row, text="Browse Folder", command=self.choose_folder).pack(side="left", padx=12)

        # Options
        opt_row = tk.Frame(content)
        opt_row.grid(row=5, column=0, columnspan=4, sticky="w", pady=(0, 12))
        self.var_all = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_row, text="Download all (Profile)", variable=self.var_all, command=self.toggle_count).pack(side="left")
        tk.Label(opt_row, text="Download (count):").pack(side="left", padx=(18, 6))
        self.count_entry = tk.Entry(opt_row, width=8)
        self.count_entry.insert(0, "10")
        self.count_entry.pack(side="left")
        self.toggle_count()

        # Buttons
        btn_row = tk.Frame(content)
        btn_row.grid(row=6, column=0, columnspan=4, sticky="w", pady=(0, 10))
        self.btn_download = tk.Button(btn_row, text="Download", width=12, command=self.start_download)
        self.btn_stop = tk.Button(btn_row, text="Stop", width=12, command=self.stop_download)
        self.btn_clear = tk.Button(btn_row, text="Clear", width=12, command=self.clear_log)
        self.lbl_completed = tk.Label(btn_row, text="Completed [0]", font=("Segoe UI", 10, "bold"))
        self.btn_download.pack(side="left", padx=(0, 8))
        self.btn_stop.pack(side="left", padx=8)
        self.btn_clear.pack(side="left", padx=8)
        self.lbl_completed.pack(side="left", padx=16)

        # Progress bar
        self.progress = ttk.Progressbar(content, mode="determinate")
        self.progress.grid(row=7, column=0, columnspan=4, sticky="we", pady=(0, 12))

        # Log box
        self.log = tk.Text(content, height=14, font=("Consolas", 10), bg="#0e0e0e", fg="#e6e6e6")
        self.log.grid(row=8, column=0, columnspan=4, sticky="nsew")
        content.grid_rowconfigure(8, weight=1)
        content.grid_columnconfigure(0, weight=1)

        # Footer
        footer = tk.Frame(self, bg="#0d6efd", height=44)
        footer.pack(fill="x", side="bottom")
        tk.Label(footer, text="KHMER 01", fg="white", bg="#0d6efd",
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=16)
        tk.Label(footer, text="Copyright © 2025 - All rights reserved",
                 fg="white", bg="#0d6efd", font=("Segoe UI", 10)).pack(side="right", padx=16)

    # --- Helpers ---
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

    # --- Main download entry ---
    def start_download(self):
        profile_url = clean_profile_url(self.profile_entry.get().strip())
        video_url = self.video_entry.get().strip()

        if not profile_url and not video_url:
            messagebox.showerror("Error", "Please enter a TikTok profile or video link.")
            return
        if not self.download_folder:
            messagebox.showerror("Error", "Please choose a download folder.")
            return

        self.clear_log()
        self.stop_flag = False
        self.btn_download.config(state="disabled")

        if video_url:
            threading.Thread(target=self._download_single, args=(video_url,), daemon=True).start()
        else:
            count = None
            if not self.var_all.get():
                try:
                    c = int(self.count_entry.get())
                    if c <= 0:
                        raise ValueError
                    count = c
                except Exception:
                    messagebox.showerror("Error", "Download count must be a positive number.")
                    self.btn_download.config(state="normal")
                    return
            threading.Thread(target=self._download_profile, args=(profile_url, count), daemon=True).start()

    # --- Download one video ---
    def _download_single(self, video_url: str):
        self.log_line(f"🔗 Video: {video_url}")
        ydl_opts = {
            "outtmpl": os.path.join(self.download_folder, "%(uploader)s_%(id)s.%(ext)s"),
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self._progress_hook],
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            self.log_line("✅ Video downloaded successfully.")
        except Exception as e:
            self.log_line(f"❌ Error: {e}")
        finally:
            self.btn_download.config(state="normal")

    # --- Download full profile ---
    def _download_profile(self, profile_url: str, count: int | None):
        self.log_line(f"🔗 Profile: {profile_url}")

        # Correct options for TikTok profiles
        ydl_opts = {
            "outtmpl": os.path.join(self.download_folder, "%(uploader)s_%(id)s.%(ext)s"),
            "merge_output_format": "mp4",
            "ignoreerrors": True,
            "continuedl": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self._progress_hook],
        }

        try:
            # Extract videos without flattening
            with yt_dlp.YoutubeDL({"quiet": True}) as probe:
                info = probe.extract_info(profile_url, download=False)
            entries = info.get("entries") or []
            if count is not None:
                entries = entries[:count]
            total = len(entries)
            if total == 0:
                self.log_line("⚠️ No videos found.")
                self.btn_download.config(state="normal")
                return

            self.progress["maximum"] = total
            self.progress["value"] = 0
            self.log_line(f"Found {total} video(s). Starting download…")

            # Download each video individually to respect count
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                for entry in entries:
                    if self.stop_flag:
                        break
                    video_url = entry.get("url")
                    if video_url:
                        ydl.download([video_url])

            if not self.stop_flag:
                self.log_line("✅ All done.")
        except Exception as e:
            self.log_line(f"❌ Error: {e}")
        finally:
            self.btn_download.config(state="normal")

    def _progress_hook(self, d):
        if self.stop_flag:
            return  # stop gracefully
        if d.get("status") == "finished":
            self.completed += 1
            self.lbl_completed.config(text=f"Completed [{self.completed}]")
            self.progress["value"] = self.completed
            self.log_line(f"⬇️ Saved: {os.path.basename(d.get('filename',''))}")

if __name__ == "__main__":
    app = TikTokDownloader()
    app.mainloop()
