import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import yt_dlp

APP_TITLE = "Kimly Tool KH — YouTube Downloader"

class YouTubeDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x600")
        self.minsize(880, 560)

        self.stop_flag = False
        self.completed = 0
        self.download_folder = ""

        # Header
        header = tk.Frame(self, bg="#dc3545", height=48)
        header.pack(fill="x")
        tk.Label(header, text="Kimly Tool KH", fg="white", bg="#dc3545",
                 font=("Segoe UI", 12, "bold"), padx=16).pack(side="left")

        # Content
        content = tk.Frame(self, padx=18, pady=18)
        content.pack(fill="both", expand=True)

        # YouTube URL
        tk.Label(content, text="Enter YouTube Video or Playlist Link", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w")
        self.url_entry = tk.Entry(content, width=90, font=("Segoe UI", 10))
        self.url_entry.grid(row=1, column=0, columnspan=4, sticky="we", pady=(4, 10))
        self.url_entry.insert(0, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        # Folder chooser
        folder_row = tk.Frame(content)
        folder_row.grid(row=2, column=0, columnspan=4, sticky="we", pady=(2, 12))
        self.folder_lbl = tk.Label(folder_row, text="No folder selected", font=("Segoe UI", 10))
        self.folder_lbl.pack(side="left")
        tk.Button(folder_row, text="Browse Folder", command=self.choose_folder).pack(side="left", padx=12)

        # Format options
        tk.Label(content, text="Select Format:", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky="w")
        self.format_var = tk.StringVar(value="mp4")
        ttk.Combobox(content, textvariable=self.format_var, values=["mp4", "mp3"], width=10, state="readonly").grid(row=3, column=1, sticky="w", padx=5)

        # Resolution selector
        tk.Label(content, text="Select Quality:", font=("Segoe UI", 10, "bold")).grid(row=3, column=2, sticky="w", padx=(20, 5))
        self.res_var = tk.StringVar(value="best")
        ttk.Combobox(content, textvariable=self.res_var, values=["best", "1080p", "720p", "480p", "360p", "240p", "144p"], width=10, state="readonly").grid(row=3, column=3, sticky="w")

        # Buttons
        btn_row = tk.Frame(content)
        btn_row.grid(row=4, column=0, columnspan=4, sticky="w", pady=(10, 10))
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
        self.progress.grid(row=5, column=0, columnspan=4, sticky="we", pady=(0, 12))

        # Log box
        self.log = tk.Text(content, height=14, font=("Consolas", 10), bg="#0e0e0e", fg="#e6e6e6")
        self.log.grid(row=6, column=0, columnspan=4, sticky="nsew")
        content.grid_rowconfigure(6, weight=1)
        content.grid_columnconfigure(0, weight=1)

        # Footer
        footer = tk.Frame(self, bg="#dc3545", height=44)
        footer.pack(fill="x", side="bottom")
        tk.Label(footer, text="YouTube Downloader by Kimly Tool KH", fg="white", bg="#dc3545",
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=16)
        tk.Label(footer, text="© 2025 All rights reserved",
                 fg="white", bg="#dc3545", font=("Segoe UI", 10)).pack(side="right", padx=16)

    # --- Helpers ---
    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_folder = folder
            self.folder_lbl.config(text=folder)

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

    # --- Start Download ---
    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube link.")
            return
        if not self.download_folder:
            messagebox.showerror("Error", "Please choose a download folder.")
            return

        self.clear_log()
        self.stop_flag = False
        self.btn_download.config(state="disabled")

        threading.Thread(target=self._download_video, args=(url,), daemon=True).start()

    # --- Download Logic ---
    def _download_video(self, url: str):
        fmt = self.format_var.get()
        res = self.res_var.get()
        outtmpl = os.path.join(self.download_folder, "%(title)s.%(ext)s")

        # Quality filter
        res_map = {
            "1080p": "bestvideo[height<=1080]+bestaudio/best",
            "720p": "bestvideo[height<=720]+bestaudio/best",
            "480p": "bestvideo[height<=480]+bestaudio/best",
            "360p": "bestvideo[height<=360]+bestaudio/best",
            "240p": "bestvideo[height<=240]+bestaudio/best",
            "144p": "bestvideo[height<=144]+bestaudio/best",
            "best": "bv*+ba/b"
        }
        video_format = res_map.get(res, "bv*+ba/b")

        if fmt == "mp3":
            ydl_opts = {
                "outtmpl": outtmpl,
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "progress_hooks": [self._progress_hook],
                "quiet": True,
                "no_warnings": True,
            }
        else:
            ydl_opts = {
                "outtmpl": outtmpl,
                "format": video_format,
                "merge_output_format": "mp4",
                "postprocessors": [{
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                }],
                "progress_hooks": [self._progress_hook],
                "quiet": True,
                "no_warnings": True,
            }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                total_videos = len(info["entries"]) if "entries" in info else 1
                self.progress["maximum"] = total_videos
                ydl.download([url])

            self.log_line("✅ Download complete!")
        except Exception as e:
            self.log_line(f"❌ Error: {e}")
        finally:
            self.btn_download.config(state="normal")

    def _progress_hook(self, d):
        if self.stop_flag:
            raise KeyboardInterrupt("Stopped by user")

        if d.get("status") == "finished":
            self.completed += 1
            self.lbl_completed.config(text=f"Completed [{self.completed}]")
            self.progress["value"] = self.completed
            self.log_line(f"⬇️ Saved: {os.path.basename(d.get('filename', ''))}")

if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()
