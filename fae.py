import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import os, random, shutil, subprocess, threading

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
    if len(h) == 3:  # short form #rgb
        h = "".join(ch * 2 for ch in h)
    return "0x" + h.upper()

class TikTokVideoCreator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FFmpeg TikTok Video Creator")
        self.geometry("980x620")

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

        # ===== Logo Overlay =====
        ttk.Label(self, text="Logo Overlay:").grid(row=4, column=0, sticky="w", padx=8, pady=6)
        self.logo_path_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.logo_path_var).grid(row=4, column=3, sticky="ew", padx=8)
        ttk.Button(self, text="Browse", command=self._choose_logo).grid(row=4, column=4, sticky="w", padx=(0,8))
        
        # Logo position and size
        logo_pos_frame = ttk.Frame(self)
        logo_pos_frame.grid(row=5, column=0, columnspan=5, sticky="w", padx=8, pady=6)
        
        ttk.Label(logo_pos_frame, text="Position:").grid(row=0, column=0, sticky="w")
        self.logo_x = tk.IntVar(value=20)
        ttk.Entry(logo_pos_frame, textvariable=self.logo_x, width=6).grid(row=0, column=1, sticky="w", padx=(6, 0))
        ttk.Label(logo_pos_frame, text="X").grid(row=0, column=2, sticky="w", padx=(2, 6))
        
        self.logo_y = tk.IntVar(value=20)
        ttk.Entry(logo_pos_frame, textvariable=self.logo_y, width=6).grid(row=0, column=3, sticky="w")
        ttk.Label(logo_pos_frame, text="Y").grid(row=0, column=4, sticky="w", padx=(2, 6))
        
        ttk.Label(logo_pos_frame, text="Size:").grid(row=0, column=5, sticky="w")
        self.logo_size = tk.IntVar(value=100)
        ttk.Entry(logo_pos_frame, textvariable=self.logo_size, width=6).grid(row=0, column=6, sticky="w", padx=(6, 0))
        ttk.Label(logo_pos_frame, text="px").grid(row=0, column=7, sticky="w", padx=(2, 6))
        
        self.logo_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(logo_pos_frame, text="Enable Logo", variable=self.logo_enabled).grid(row=0, column=8, sticky="w", padx=(10, 0))

        # ===== Render / Overlay / Border =====
        row6 = 6
        ttk.Label(self, text="Render:").grid(row=row6, column=0, sticky="w", padx=8, pady=6)
        self.render_var = tk.StringVar(value="CPU")
        ttk.Combobox(self, textvariable=self.render_var, values=["CPU", "GPU"], width=8, state="readonly")\
            .grid(row=row6, column=1, sticky="w")

        overlay_frame = ttk.Frame(self)
        overlay_frame.grid(row=row6, column=2, columnspan=2, sticky="w")
        ttk.Label(overlay_frame, text="Video Size W").grid(row=0, column=0, sticky="w")
        self.overlay_w = tk.IntVar(value=TIKTOK_W)
        ttk.Entry(overlay_frame, textvariable=self.overlay_w, width=6).grid(row=0, column=1, sticky="w", padx=(6, 10))
        ttk.Label(overlay_frame, text="H").grid(row=0, column=2, sticky="w")
        self.overlay_h = tk.IntVar(value=TIKTOK_H)
        ttk.Entry(overlay_frame, textvariable=self.overlay_h, width=6).grid(row=0, column=3, sticky="w", padx=(6, 0))

        self.set_border_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="Set Border Video", variable=self.set_border_var)\
            .grid(row=7, column=0, sticky="w", padx=8)
        ttk.Label(self, text="Size").grid(row=7, column=1, sticky="w")
        self.border_size = tk.IntVar(value=5)
        ttk.Entry(self, textvariable=self.border_size, width=6).grid(row=7, column=1, sticky="w", padx=(40, 0))
        ttk.Label(self, text="Color").grid(row=7, column=2, sticky="w")
        self.border_color = tk.StringVar(value="#0000FF")
        ttk.Button(self, text="Pick", command=self._pick_color).grid(row=7, column=3, sticky="w")

        # ===== Create Button =====
        self.create_btn = ttk.Button(self, text="Create TikTok Videos", command=self._run_batch)
        self.create_btn.grid(row=8, column=0, columnspan=5, pady=14)

        # ===== Layout stretch =====
        self.columnconfigure(3, weight=1)
        self.rowconfigure(2, weight=1)

        self._update_bg_hint()

    # ---------- UI helpers ----------
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

    def _build_ffmpeg_cmd(self, in_video: str, bg_img: str, out_path: str):
        # Both background and video will have the same TikTok dimensions
        w = TIKTOK_W
        h = TIKTOK_H

        # Background branch: scale to TikTok portrait exactly
        bg_branch = f"[1]scale={w}:{h}[bg]"

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
            video_branch = f"[0]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2[v]"

        # Logo branch (if enabled)
        logo_filter = ""
        if self.logo_enabled.get() and self.logo_path_var.get() and os.path.isfile(self.logo_path_var.get()):
            logo_size = max(10, min(self.logo_size.get(), 300))  # Limit logo size
            logo_x = max(0, min(self.logo_x.get(), TIKTOK_W - logo_size))
            logo_y = max(0, min(self.logo_y.get(), TIKTOK_H - logo_size))
            logo_filter = f";[2]scale={logo_size}:-1:force_original_aspect_ratio=decrease[logo]"
            # Add logo overlay to the combine filter
            combine = f"[bg][v]overlay=0:0:shortest=1[tmp];[tmp][logo]overlay={logo_x}:{logo_y}:format=yuv420p[outv]"
        else:
            combine = "[bg][v]overlay=0:0:shortest=1,format=yuv420p[outv]"

        filter_complex = f"{bg_branch};{video_branch}{logo_filter};{combine}"

        # Encoder selection
        if self.render_var.get().upper() == "GPU":
            vcodec = ["-c:v", "h264_nvenc", "-preset", "p5", "-b:v", "5M"]
        else:
            vcodec = ["-c:v", "libx264", "-crf", "20", "-preset", "veryfast"]

        # Build command
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", in_video,
            "-loop", "1", "-i", bg_img,
        ]
        
        # Add logo input if enabled
        if self.logo_enabled.get() and self.logo_path_var.get() and os.path.isfile(self.logo_path_var.get()):
            cmd.extend(["-i", self.logo_path_var.get()])
            
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", "0:a?",
            *vcodec,
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            out_path
        ])
        
        return cmd

    def _process_one(self, video_path: str, out_dir: str):
        # Select background
        if self.bg_mode.get() == "choose":
            bg_img = self.bg_path_var.get()
            if not os.path.isfile(bg_img):
                raise RuntimeError("Invalid background image path.")
        else:
            bg_img = self._pick_random_background()
            if not bg_img:
                raise RuntimeError("No image found in the selected background folder.")

        base = os.path.splitext(os.path.basename(video_path))[0]
        out_path = os.path.join(out_dir, base + "_tiktok.mp4")

        cmd = self._build_ffmpeg_cmd(video_path, bg_img, out_path)
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

        # Check if logo is enabled but not selected
        if self.logo_enabled.get() and (not self.logo_path_var.get() or not os.path.isfile(self.logo_path_var.get())):
            messagebox.showerror("Logo Error", "Logo is enabled but no valid logo file is selected.")
            return

        # Disable button while running
        self.create_btn.config(state="disabled")
        for child in self.tree.get_children():
            self.tree.set(child, "status", "Queued")

        def worker():
            try:
                files = [f for f in os.listdir(in_dir) if f.lower().endswith(VIDEO_EXTS)]
                total = len(files)
                if total == 0:
                    messagebox.showwarning("No Videos", "No video files found in the selected folder.")
                    return
                for idx, fname in enumerate(sorted(files), start=1):
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