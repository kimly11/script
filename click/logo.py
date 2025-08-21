import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import os, random, subprocess, threading

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
VIDEO_EXTS = (".mp4", ".mov", ".avi", ".mkv")

TIKTOK_W, TIKTOK_H = 720, 1200

def ffmpeg_exists() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        return False

class TikTokVideoCreator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FFmpeg TikTok Video Creator")
        self.geometry("980x560")

        # ===== Background (Choose / Random) =====
        ttk.Label(self, text="Background:").grid(row=0, column=0, sticky="w", padx=8, pady=(10,6))
        self.bg_mode = tk.StringVar(value="choose")
        ttk.Radiobutton(self, text="Choose", value="choose", variable=self.bg_mode, command=self._update_bg_hint)\
            .grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(self, text="Random", value="random", variable=self.bg_mode, command=self._update_bg_hint)\
            .grid(row=0, column=2, sticky="w")
        self.bg_path_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.bg_path_var).grid(row=0, column=3, sticky="ew", padx=8)
        ttk.Button(self, text="Browse", command=self._choose_background).grid(row=0, column=4, sticky="w", padx=(0,8))

        # ===== Video Folder =====
        ttk.Label(self, text="Video Folder:").grid(row=1, column=0, sticky="w", padx=8)
        self.video_folder_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.video_folder_var).grid(row=1, column=3, sticky="ew", padx=8)
        ttk.Button(self, text="Browse", command=self._choose_video_folder).grid(row=1, column=4, sticky="w", padx=(0,8))

        # ===== File Table =====
        cols = ("no", "title", "size", "status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=13)
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
        self.tree.column("no", width=40, anchor="center")
        self.tree.column("title", width=560, anchor="w")
        self.tree.column("size", width=100, anchor="e")
        self.tree.column("status", width=150, anchor="w")
        self.tree.grid(row=2, column=0, columnspan=5, sticky="nsew", padx=8, pady=8)

        # ===== Output Folder =====
        ttk.Label(self, text="Output Folder:").grid(row=3, column=0, sticky="w", padx=8)
        self.output_folder_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.output_folder_var).grid(row=3, column=3, sticky="ew", padx=8)
        ttk.Button(self, text="Browse", command=self._choose_output_folder).grid(row=3, column=4, sticky="w", padx=(0,8))

        # ===== Render Selection =====
        ttk.Label(self, text="Render:").grid(row=4, column=0, sticky="w", padx=8, pady=6)
        self.render_var = tk.StringVar(value="CPU")
        ttk.Combobox(self, textvariable=self.render_var, values=["CPU", "GPU"], width=8, state="readonly")\
            .grid(row=4, column=1, sticky="w")

        # ===== Create Button =====
        self.create_btn = ttk.Button(self, text="Create TikTok Videos", command=self._run_batch)
        self.create_btn.grid(row=6, column=0, columnspan=5, pady=14)

        self.columnconfigure(3, weight=1)
        self.rowconfigure(2, weight=1)
        self._update_bg_hint()

    def _update_bg_hint(self):
        if not self.bg_path_var.get():
            if self.bg_mode.get() == "choose":
                self.bg_path_var.set("Select a background image file…")
            else:
                self.bg_path_var.set("Select a folder with background images…")

    def _choose_background(self):
        if self.bg_mode.get() == "choose":
            path = filedialog.askopenfilename(
                title="Choose Background Image",
                filetypes=[("Image Files", ";".join(f"*{e}" for e in IMAGE_EXTS))]
            )
        else:
            path = filedialog.askdirectory(title="Choose Backgrounds Folder (for Random)")
        if path:
            self.bg_path_var.set(path)

    def _choose_video_folder(self):
        folder = filedialog.askdirectory(title="Choose Video Folder")
        if folder:
            self.video_folder_var.set(folder)
            self._load_videos(folder)

    def _choose_output_folder(self):
        folder = filedialog.askdirectory(title="Choose Output Folder")
        if folder:
            self.output_folder_var.set(folder)

    def _load_videos(self, folder):
        self.tree.delete(*self.tree.get_children())
        files = [f for f in os.listdir(folder) if f.lower().endswith(VIDEO_EXTS)]
        for i, f in enumerate(sorted(files), start=1):
            size_mb = os.path.getsize(os.path.join(folder, f)) / (1200 * 900.0)
            self.tree.insert("", "end", iid=f, values=(i, f, f"{size_mb:.2f} MB", "Ready"))

    def _pick_random_background(self):
        folder = self.bg_path_var.get()
        if not os.path.isdir(folder):
            return None
        candidates = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(IMAGE_EXTS)]
        return random.choice(candidates) if candidates else None

    def _build_ffmpeg_cmd(self, in_video: str, bg_img: str, out_path: str):
        canvas_w, canvas_h = TIKTOK_W, TIKTOK_H
        max_video_h = int(canvas_h * 0.8)  # 1080

        # Background scaled and cropped
        bg_branch = f"[1]scale={canvas_w}:{canvas_h}:force_original_aspect_ratio=increase," \
                    f"crop={canvas_w}:{canvas_h}[bg]"

        # Video scaled to 720 width, max 1080 height, centered
        video_branch = f"[0]scale=w={canvas_w}:h={max_video_h}:force_original_aspect_ratio=decrease," \
                       f"pad={canvas_w}:{canvas_h}:(ow-iw)/2:(oh-ih)/2:color=0x00000000[v]"

        combine = "[bg][v]overlay=shortest=1[outv]"
        filter_complex = f"{bg_branch};{video_branch};{combine}"

        if self.render_var.get().upper() == "GPU":
            vcodec = ["-c:v", "h264_nvenc", "-preset", "p5", "-b:v", "5M"]
        else:
            vcodec = ["-c:v", "libx264", "-crf", "20", "-preset", "veryfast"]

        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", in_video,
            "-loop", "1", "-i", bg_img,
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", "0:a?",
            *vcodec,
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            out_path
        ]
        return cmd

    def _process_one(self, video_path: str, out_dir: str):
        if self.bg_mode.get() == "choose":
            bg_img = self.bg_path_var.get()
            if not os.path.isfile(bg_img):
                raise RuntimeError("Invalid background image path.")
        else:
            bg_img = self._pick_random_background()
            if not bg_img:
                raise RuntimeError("No image found in background folder.")

        base = os.path.splitext(os.path.basename(video_path))[0]
        out_path = os.path.join(out_dir, base + "_tiktok.mp4")

        cmd = self._build_ffmpeg_cmd(video_path, bg_img, out_path)
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "FFmpeg failed.")
        return out_path

    def _run_batch(self):
        if not ffmpeg_exists():
            messagebox.showerror("FFmpeg not found", "Please install FFmpeg and add it to PATH.")
            return

        in_dir = self.video_folder_var.get().strip()
        out_dir = self.output_folder_var.get().strip()

        if not os.path.isdir(in_dir):
            messagebox.showerror("Input Error", "Invalid video folder.")
            return
        if not os.path.isdir(out_dir):
            messagebox.showerror("Output Error", "Invalid output folder.")
            return

        self.create_btn.config(state="disabled")
        for child in self.tree.get_children():
            self.tree.set(child, "status", "Queued")

        def worker():
            try:
                files = [f for f in os.listdir(in_dir) if f.lower().endswith(VIDEO_EXTS)]
                if not files:
                    messagebox.showwarning("No Videos", "No video files found.")
                    return
                for fname in sorted(files):
                    path = os.path.join(in_dir, fname)
                    self.tree.set(fname, "status", "Processing…")
                    try:
                        out_file = self._process_one(path, out_dir)
                        self.tree.set(fname, "status", f"Done → {os.path.basename(out_file)}")
                    except Exception as e:
                        self.tree.set(fname, "status", f"Error: {e}")
                messagebox.showinfo("Completed", "All videos processed.")
            finally:
                self.create_btn.config(state="normal")

        threading.Thread(target=worker, daemon=True).start()

if __name__ == "__main__":
    app = TikTokVideoCreator()
    app.mainloop()
