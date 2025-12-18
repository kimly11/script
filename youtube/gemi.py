import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import yt_dlp
# Import specific yt_dlp error types for better error handling
from yt_dlp.utils import DownloadError, ExtractorError

APP_TITLE = "Kimly Tool KH — Video Downloader"

def clean_profile_url(url: str) -> str:
    """Normalize TikTok profile link."""
    url = url.strip()
    if not url:
        return url
    # Keep only the part before '?'
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
        tk.Label(content, text="Enter TikTok Profile Link (for multiple videos)", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w")
        self.profile_entry = tk.Entry(content, width=90, font=("Segoe UI", 10))
        self.profile_entry.grid(row=1, column=0, columnspan=4, sticky="we", pady=(4, 10))
        self.profile_entry.insert(0, "https://www.tiktok.com/@khon_kimly")

        # Video input (Updated label for YouTube/General support)
        tk.Label(content, text="Enter Single Video Link (TikTok, YouTube, etc.)", font=("Segoe UI", 11, "bold")).grid(row=2, column=0, sticky="w")
        self.video_entry = tk.Entry(content, width=90, font=("Segoe UI", 10))
        self.video_entry.grid(row=3, column=0, columnspan=4, sticky="we", pady=(4, 10))
        # Example YouTube link for testing
        self.video_entry.insert(0, "") # User can insert any URL here

        # --- New: Cookies/Auth input ---
        tk.Label(content, text="Optional: Cookies File Path (to bypass 403 errors)", font=("Segoe UI", 11, "bold")).grid(row=4, column=0, sticky="w")
        cookie_row = tk.Frame(content)
        cookie_row.grid(row=5, column=0, columnspan=4, sticky="we", pady=(4, 10))
        self.cookies_entry = tk.Entry(cookie_row, width=80, font=("Segoe UI", 10))
        self.cookies_entry.pack(side="left", fill="x", expand=True)
        tk.Button(cookie_row, text="Browse .txt", command=self.choose_cookie_file).pack(side="left", padx=(8, 0))
        # -------------------------------

        # Folder chooser (Now row 6)
        folder_row = tk.Frame(content)
        folder_row.grid(row=6, column=0, columnspan=4, sticky="we", pady=(2, 12))
        self.folder_lbl = tk.Label(folder_row, text="No folder selected", font=("Segoe UI", 10))
        self.folder_lbl.pack(side="left")
        tk.Button(folder_row, text="Browse Folder", command=self.choose_folder).pack(side="left", padx=12)

        # Options (Now row 7)
        opt_row = tk.Frame(content)
        opt_row.grid(row=7, column=0, columnspan=4, sticky="w", pady=(0, 12))
        self.var_all = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_row, text="Download all (Profile)", variable=self.var_all, command=self.toggle_count).pack(side="left")
        tk.Label(opt_row, text="Download (count):").pack(side="left", padx=(18, 6))
        self.count_entry = tk.Entry(opt_row, width=8)
        self.count_entry.insert(0, "10")
        self.count_entry.pack(side="left")
        self.toggle_count()

        # Buttons (Now row 8)
        btn_row = tk.Frame(content)
        btn_row.grid(row=8, column=0, columnspan=4, sticky="w", pady=(0, 10))
        self.btn_download = tk.Button(btn_row, text="Download", width=12, command=self.start_download)
        self.btn_stop = tk.Button(btn_row, text="Stop", width=12, command=self.stop_download)
        self.btn_clear = tk.Button(btn_row, text="Clear", width=12, command=self.clear_log)
        self.lbl_completed = tk.Label(btn_row, text="Completed [0]", font=("Segoe UI", 10, "bold"))
        self.btn_download.pack(side="left", padx=(0, 8))
        self.btn_stop.pack(side="left", padx=8)
        self.btn_clear.pack(side="left", padx=8)
        self.lbl_completed.pack(side="left", padx=16)

        # Progress bar (Now row 9)
        self.progress = ttk.Progressbar(content, mode="determinate")
        self.progress.grid(row=9, column=0, columnspan=4, sticky="we", pady=(0, 12))

        # Log box (Now row 10)
        self.log = tk.Text(content, height=14, font=("Consolas", 10), bg="#0e0e0e", fg="#e6e6e6")
        self.log.grid(row=10, column=0, columnspan=4, sticky="nsew")
        content.grid_rowconfigure(10, weight=1) # Update row configure index
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
            
    def choose_cookie_file(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            self.cookies_entry.delete(0, tk.END)
            self.cookies_entry.insert(0, file_path)

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
            messagebox.showerror("Error", "Please enter a profile or single video link.")
            return
        if not self.download_folder:
            messagebox.showerror("Error", "Please choose a download folder.")
            return

        self.clear_log()
        self.stop_flag = False
        self.btn_download.config(state="disabled")

        if video_url:
            # Use the generic single downloader for YouTube, TikTok, or any supported single video URL
            threading.Thread(target=self._download_single_url, args=(video_url,), daemon=True).start()
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

    # --- Download one video (supports any yt-dlp URL like YouTube, TikTok, etc.) ---
    def _download_single_url(self, video_url: str):
        self.log_line(f"🔗 Single URL: {video_url}")
        self.progress["maximum"] = 1
        
        cookie_path = self.cookies_entry.get().strip()
        
        ydl_opts = {
            "outtmpl": os.path.join(self.download_folder, "%(uploader)s_%(id)s.%(ext)s"),
            "merge_output_format": "mp4",
            # FIX: Use a more general format selection to resolve "format not available" error on YouTube Shorts
            "format": "bestvideo+bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self._progress_hook],
            "noplaylist": True,
            # FIX: Add retries to stabilize downloads against 403 errors and network hiccups
            "retries": 5, 
            "fragment_retries": 5,
        }
        
        if cookie_path:
            if not os.path.exists(cookie_path):
                self.log_line(f"⚠️ Warning: Cookie file not found at {cookie_path}. Proceeding without authentication.")
            else:
                ydl_opts["cookiefile"] = cookie_path
                self.log_line("🔐 Using cookies for authentication...")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
        except (DownloadError, ExtractorError) as e:
            # Provide more specific error messages for yt-dlp failures
            self.log_line(f"❌ Download Error: {e.args[0]}")
            if "403" in str(e):
                 self.log_line("💡 HINT: Error 403 often means authentication is needed. Try using a valid cookie file.")
        except Exception as e:
            self.log_line(f"❌ An unexpected error occurred: {e}")
        finally:
            self.btn_download.config(state="normal")

    # --- Download full profile ---
    def _download_profile(self, profile_url: str, count: int | None):
        self.log_line(f"🔗 Profile: {profile_url}")
        
        cookie_path = self.cookies_entry.get().strip()
        
        ydl_opts = {
            "outtmpl": os.path.join(self.download_folder, "%(uploader)s_%(id)s.%(ext)s"),
            "merge_output_format": "mp4",
            "ignoreerrors": True,
            "continuedl": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self._progress_hook],
            # FIX: Add retries to stabilize downloads against 403 errors and network hiccups
            "retries": 5, 
            "fragment_retries": 5,
        }
        
        if cookie_path:
            if not os.path.exists(cookie_path):
                self.log_line(f"⚠️ Warning: Cookie file not found at {cookie_path}. Proceeding without authentication.")
            else:
                ydl_opts["cookiefile"] = cookie_path
                self.log_line("🔐 Using cookies for authentication...")
            
        if count is not None:
            ydl_opts["playlistend"] = count

        try:
            # Count videos first
            self.log_line("🔎 Analyzing profile for video count...")
            # We use a separate YDL instance for probing to avoid interference
            probe_opts = {"quiet": True, "extract_flat": "in_playlist"}
            if cookie_path and os.path.exists(cookie_path):
                 probe_opts["cookiefile"] = cookie_path

            with yt_dlp.YoutubeDL(probe_opts) as probe:
                info = probe.extract_info(profile_url, download=False)
                
            entries = info.get("entries") or []
            total = len(entries) if count is None else min(len(entries), count)
            
            if total == 0:
                self.log_line("⚠️ No videos found or profile is inaccessible (try using cookies).")
                self.btn_download.config(state="normal")
                return

            self.progress["maximum"] = total
            self.progress["value"] = 0
            self.log_line(f"Found {total} video(s). Starting download…")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([profile_url])

            if not self.stop_flag:
                self.log_line("✅ All done.")
        except (DownloadError, ExtractorError) as e:
            self.log_line(f"❌ Profile Download Error: {e.args[0]}")
            if "403" in str(e):
                 self.log_line("💡 HINT: Error 403 often means authentication is needed. Try using a valid cookie file.")
        except Exception as e:
            self.log_line(f"❌ An unexpected error occurred: {e}")
        finally:
            self.btn_download.config(state="normal")

    def _progress_hook(self, d):
        if self.stop_flag:
            # This is the standard way to stop yt-dlp from a hook
            raise KeyboardInterrupt("Stopped by user")

        if d.get("status") == "finished":
            self.completed += 1
            self.lbl_completed.config(text=f"Completed [{self.completed}]")
            
            # For single video download, the maximum is 1, so this will fill the bar
            self.progress["value"] = self.completed
            
            filename = d.get('filename','')
            # For playlist downloads, filenames often include a playlist index which we strip for a cleaner log
            if self.progress["maximum"] > 1:
                filename = re.sub(r'^\d+\-?\d*\s*','', filename)
                
            self.log_line(f"⬇️ Saved: {os.path.basename(filename)}")

if __name__ == "__main__":
    app = TikTokDownloader()
    app.mainloop()
