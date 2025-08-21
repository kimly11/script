import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import os, random, subprocess, threading

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
VIDEO_EXTS = (".mp4", ".mov", ".avi", ".mkv")
TIKTOK_W, TIKTOK_H = 435, 735

def ffmpeg_exists() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        return False

def to_ffmpeg_color(hex_color: str) -> str:
    """Convert '#rrggbb' to '0xRRGGBB' for ffmpeg."""
    if not hex_color:
        return "0x000000"
    h = hex_color.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return "0x" + h.upper()

class TikTokVideoCreator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FFmpeg TikTok Video Creator")
        self.geometry("980x650")

        # ===== Background Mode =====
        ttk.Label(self, text="Background:").grid(row=0, column=0, sticky="w", padx=8, pady=(10,6))
        self.bg_mode = tk.StringVar(value="choose")
        ttk.Radiobutton(self, text="Choose", value="choose", variable=self.bg_mode, command=self._update_bg_hint)\
            .grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(self, text="Random", value="random", variable=self.bg_mode, command=self._update_bg_hint)\
            .grid(row=0, column=2, sticky="w")
        ttk.Radiobutton(self, text="White", value="white", variable=self.bg_mode, command=self._update_bg_hint)\
            .grid(row=0, column=3, sticky="w")
        self.bg_path_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.bg_path_var).grid(row=0, column=4, sticky="ew", padx=8)
        ttk.Button(self, text="Browse", command=self._choose_background).grid(row=0, column=5, sticky="w", padx=(0,8))

        # ===== Video Folder =====
        ttk.Label(self, text="Video Folder:").grid(row=1, column=0, sticky="w", padx=8)
        self.video_folder_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.video_folder_var).grid(row=1, column=4, sticky="ew", padx=8)
        ttk.Button(self, text="Browse", command=self._choose_video_folder).grid(row=1, column=5, sticky="w", padx=(0,8))

        # ===== File Table =====
        cols = ("no", "title", "size", "status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=13)
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
        self.tree.column("no", width=40, anchor="center")
        self.tree.column("title", width=560, anchor="w")
        self.tree.column("size", width=100, anchor="e")
        self.tree.column("status", width=150, anchor="w")
        self.tree.grid(row=2, column=0, columnspan=6, sticky="nsew", padx=8, pady=8)

        # ===== Output Folder =====
        ttk.Label(self, text="Output Folder:").grid(row=3, column=0, sticky="w", padx=8)
        self.output_folder_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.output_folder_var).grid(row=3, column=4, sticky="ew", padx=8)
        ttk.Button(self, text="Browse", command=self._choose_output_folder).grid(row=3, column=5, sticky="w", padx=(0,8))

        # ===== Render / Overlay / Border =====
        row4 = 4
        ttk.Label(self, text="Render:").grid(row=row4, column=0, sticky="w", padx=8, pady=6)
        self.render_var = tk.StringVar(value="CPU")
        ttk.Combobox(self, textvariable=self.render_var, values=["CPU", "GPU"], width=8, state="readonly")\
            .grid(row=row4, column=1, sticky="w")

        overlay_frame = ttk.Frame(self)
        overlay_frame.grid(row=row4, column=2, columnspan=2, sticky="w")
        ttk.Label(overlay_frame, text="Overlay Size W").grid(row=0, column=0, sticky="w")
        self.overlay_w = tk.IntVar(value=580)
        ttk.Entry(overlay_frame, textvariable=self.overlay_w, width=6).grid(row=0, column=1, sticky="w", padx=(6, 10))
        ttk.Label(overlay_frame, text="H").grid(row=0, column=2, sticky="w")
        self.overlay_h = tk.IntVar(value=700)
        ttk.Entry(overlay_frame, textvariable=self.overlay_h, width=6).grid(row=0, column=3, sticky="w", padx=(6, 0))

        self.set_border_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="Set Border Video", variable=self.set_border_var)\
            .grid(row=5, column=0, sticky="w", padx=8)
        ttk.Label(self, text="Size").grid(row=5, column=1, sticky="w")
        self.border_size = tk.IntVar(value=5)
        ttk.Entry(self, textvariable=self.border_size, width=6).grid(row=5, column=1, sticky="w", padx=(40, 0))
        ttk.Label(self, text="Color").grid(row=5, column=2, sticky="w")
        self.border_color = tk.StringVar(value="#0000FF")
        ttk.Button(self, text="Pick", command=self._pick_color).grid(row=5, column=3, sticky="w")

        # ===== Logo / Text Overlay =====
        row6 = 6
        ttk.Label(self, text="Logo:").grid(row=row6, column=0, sticky="w", padx=8)
        self.logo_path_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.logo_path_var).grid(row=row6, column=1, columnspan=3, sticky="ew", padx=8)
        ttk.Button(self, text="Browse", command=self._choose_logo).grid(row=row6, column=4, sticky="w")

        row7 = 7
        ttk.Label(self, text="Text Overlay:").grid(row=row7, column=0, sticky="w", padx=8)
        self.text_overlay_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.text_overlay_var).grid(row=row7, column=1, sticky="ew", padx=8)
        self.text_color = tk.StringVar(value="#FF0000")
        ttk.Button(self, text="Pick Color", command=self._pick_text_color).grid(row=row7, column=2, sticky="w")
        ttk.Label(self, text="Size").grid(row=row7, column=3, sticky="w")
        self.text_size = tk.IntVar(value=28)
        ttk.Entry(self, textvariable=self.text_size, width=6).grid(row=row7, column=4, sticky="w")

        # ===== Create Button =====
        self.create_btn = ttk.Button(self, text="Create TikTok Videos", command=self._run_batch)
        self.create_btn.grid(row=8, column=0, columnspan=6, pady=14)

        # ===== Layout stretch =====
        self.columnconfigure(4, weight=1)
        self.rowconfigure(2, weight=1)

        self._update_bg_hint()

    # ---------- UI helpers ----------
    def _update_bg_hint(self):
        if self.bg_mode.get() == "choose" and not self.bg_path_var.get():
            self.bg_path_var.set("Select a background image file…")
        elif self.bg_mode.get() == "random" and not self.bg_path_var.get():
            self.bg_path_var.set("Select a folder with background images…")
        elif self.bg_mode.get() == "white":
            self.bg_path_var.set("(no file needed)")

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

    def _choose_logo(self):
        path = filedialog.askopenfilename(
            title="Choose Logo Image",
            filetypes=[("Image Files", ";".join(f"*{e}" for e in IMAGE_EXTS))]
        )
        if path:
            self.logo_path_var.set(path)

    def _pick_color(self):
        color = colorchooser.askcolor(initialcolor=self.border_color.get())[1]
        if color:
            self.border_color.set(color)

    def _pick_text_color(self):
        color = colorchooser.askcolor(initialcolor=self.text_color.get())[1]
        if color:
            self.text_color.set(color)

    def _load_videos(self, folder):
        self.tree.delete(*self.tree.get_children())
        files = [f for f in os.listdir(folder) if f.lower().endswith(VIDEO_EXTS)]
        for i, f in enumerate(sorted(files), start=1):
            size_mb = os.path.getsize(os.path.join(folder, f)) / (1024 * 1024.0)
            self.tree.insert("", "end", iid=f, values=(i, f, f"{size_mb:.2f} MB", "Ready"))

    # ---------- Processing ----------
    def _pick_random_background(self):
        folder = self.bg_path_var.get()
        if not os.path.isdir(folder):
            return None
        candidates = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(IMAGE_EXTS)]
        return random.choice(candidates) if candidates else None

    def _build_ffmpeg_cmd(self, in_video: str, out_path: str):
        # Clamp overlay size
        w = max(2, min(self.overlay_w.get(), TIKTOK_W - 40))
        h = max(2, min(self.overlay_h.get(), TIKTOK_H - 40))

        # Background branch
        if self.bg_mode.get() == "white":
            bg_branch = f"color=white:size={TIKTOK_W}x{TIKTOK_H}:duration=999[bg]"
            inputs = ["-i", in_video]
        else:
            if self.bg_mode.get() == "choose":
                bg_img = self.bg_path_var.get()
                if not os.path.isfile(bg_img):
                    raise RuntimeError("Invalid background image path.")
            else:
                bg_img = self._pick_random_background()
                if not bg_img:
                    raise RuntimeError("No image found in the selected background folder.")

            bg_branch = f"[1]scale={TIKTOK_W}:{TIKTOK_H}:force_original_aspect_ratio=increase," \
                        f"crop={TIKTOK_W}:{TIKTOK_H}[bg]"
            inputs = ["-i", in_video, "-loop", "1", "-i", bg_img]

        # Video branch
        if self.set_border_var.get():
            bs = max(1, int(self.border_size.get()))
            inner_w = max(2, w - 2 * bs)
            inner_h = max(2, h - 2 * bs)
            color = to_ffmpeg_color(self.border_color.get())
            video_branch = (
                f"[0]scale={inner_w}:{inner_h}:force_original_aspect_ratio=decrease,"
                f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={color}[v]"
            )
        else:
            video_branch = f"[0]scale={w}:{h}:force_original_aspect_ratio=decrease[v]"

        # Combine video on background
        combine = "[bg][v]overlay=(W-w)/2:(H-h)/2:shortest=1"

        # Logo overlay
        if self.logo_path_var.get():
            inputs += ["-i", self.logo_path_var.get()]
            combine += f"[logo];[logo]scale=120:-1[lg];[bg][lg]overlay=W-w-20:20[tmp];[tmp][v]overlay=(W-w)/2:(H-h)/2:shortest=1"

        # Text overlay
        if self.text_overlay_var.get():
            color = self.text_color.get().lstrip("#")
            fontsize = self.text_size.get()
            combine += f",drawtext=text='{self.text_overlay_var.get()}':fontcolor=#{color}:fontsize={fontsize}:x=20:y=H-th-20"

        filter_complex = f"{video_branch};{bg_branch};{combine},format=yuv420p[outv]"

        # Encoder
        if self.render_var.get().upper() == "GPU":
            vcodec = ["-c:v", "h264_nvenc", "-preset", "p5", "-b:v", "5M"]
        else:
            vcodec = ["-c:v", "libx264", "-crf", "20", "-preset", "veryfast"]

        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", "0:a?",
            *vcodec,
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            out_path
        ]
        return cmd

    def _process_one(self, video_path: str, out_dir: str):
        base = os.path.splitext(os.path.basename(video_path))[0]
        out_path = os.path.join(out_dir, base + "_tiktok.mp4")

        cmd = self._build_ffmpeg_cmd(video_path, out_path)
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "FFmpeg failed.")
        return out_path

    def _run_batch(self):
        if not ffmpeg_exists():
            messagebox.showerror("FFmpeg not found", "Install FFmpeg and ensure it is on your PATH.")
            return
        in_dir = self.video_folder_var.get().strip()
        out_dir = self.output_folder_var.get().strip()
        if not os.path.isdir(in_dir):
            messagebox.showerror("Video Folder", "Please choose a valid Video Folder.")
            return
        if not os.path.isdir(out_dir):
            messagebox.showerror("Output Folder", "Please choose a valid Output Folder.")
            return

        self.create_btn.config(state="disabled")
        for child in self.tree.get_children():
            self.tree.set(child, "status", "Queued")

        def worker():
            try:
                files = [f for f in os.listdir(in_dir) if f.lower().endswith(VIDEO_EXTS)]
                if not files:
                    messagebox.showwarning("No Videos", "No video files found in the selected folder.")
                    return
                for fname in sorted(files):
                    path = os.path.join(in_dir, fname)
                    self.tree.set(fname, "status", "Processing…")
                    try:
                        out_file = self._process_one(path, out_dir)
                        self.tree.set(fname, "status", f"Done → {os.path.basename(out_file)}")
                    except Exception as e:
                        self.tree.set(fname, "status", f"Error: {e}")
                messagebox.showinfo("Finished", "All tasks completed.")
            finally:
                self.create_btn.config(state="normal")

        threading.Thread(target=worker, daemon=True).start()

if __name__ == "__main__":
    app = TikTokVideoCreator()
    app.mainloop()
