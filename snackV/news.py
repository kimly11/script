import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import yt_dlp

# Global stop flag
stop_flag = False

# Download single video
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
    except Exception as e:
        log_box.insert(tk.END, f"❌ Error: {e}\n")
    log_box.see(tk.END)

# Start download in thread
def start_download(url, folder, log_box):
    global stop_flag
    stop_flag = False

    def run():
        if stop_flag:
            log_box.insert(tk.END, "⏹ Download stopped.\n")
            return
        download_video(url, folder, log_box)
        log_box.insert(tk.END, "🎉 Completed!\n")

    threading.Thread(target=run, daemon=True).start()

# GUI
def build_gui():
    global stop_flag

    root = tk.Tk()
    root.title("SnackVideo Single Downloader")
    root.geometry("700x450")
    root.configure(bg="white")

    save_path = tk.StringVar()

    tk.Label(root, text="Enter SnackVideo Video URL:", bg="white").pack(pady=5)
    url_entry = tk.Entry(root, width=80)
    url_entry.pack(pady=5)

    def browse_folder():
        folder = filedialog.askdirectory()
        if folder:
            save_path.set(folder)

    tk.Button(root, text="Select Folder", command=browse_folder, bg="lightgray").pack()
    tk.Label(root, textvariable=save_path, bg="white", fg="blue").pack()

    # Log box
    log_box = scrolledtext.ScrolledText(root, width=85, height=15, bg="black", fg="white")
    log_box.pack(pady=10)

    # Buttons
    button_frame = tk.Frame(root, bg="white")
    button_frame.pack()

    def start():
        url = url_entry.get().strip()
        folder = save_path.get().strip()
        if not url or not folder:
            messagebox.showerror("Error", "Please enter URL and select folder.")
            return
        log_box.insert(tk.END, "🚀 Starting download...\n")
        start_download(url, folder, log_box)

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
