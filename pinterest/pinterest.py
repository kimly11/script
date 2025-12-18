import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import signal

process = None


def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_label.config(text=folder)


def start_download():
    global process

    url = url_text.get("1.0", tk.END).strip()
    folder = folder_label.cget("text")

    if not url:
        messagebox.showerror("Error", "Please enter Pinterest profile URL")
        return

    if folder == "No folder selected":
        messagebox.showerror("Error", "Please select a save folder")
        return

    cmd = [
        "gallery-dl",
        "--dest", folder,
        url
    ]

    log_box.delete(1.0, tk.END)

    def run():
        global process
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in process.stdout:
                log_box.insert(tk.END, line)
                log_box.see(tk.END)

            process.wait()
            messagebox.showinfo("Done", "Download completed!")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    threading.Thread(target=run, daemon=True).start()


def stop_download():
    global process
    if process:
        process.terminate()
        log_box.insert(tk.END, "\nDownload stopped.\n")


def clear_log():
    log_box.delete(1.0, tk.END)


# ================= GUI =================
root = tk.Tk()
root.title("Pinterest Profile Downloader")
root.geometry("700x500")

tk.Label(root, text="Pinterest Profile URL:", font=("Arial", 11)).pack(anchor="w", padx=10)

url_text = scrolledtext.ScrolledText(root, height=4)
url_text.pack(fill="x", padx=10)

frame = tk.Frame(root)
frame.pack(fill="x", padx=10, pady=5)

tk.Button(frame, text="Select Save Folder", command=select_folder).pack(side="left")

folder_label = tk.Label(frame, text="No folder selected", fg="gray")
folder_label.pack(side="left", padx=10)

frame3 = tk.Frame(root)
frame3.pack(pady=10)

tk.Button(frame3, text="Start Download", bg="green", fg="white", command=start_download).pack(side="left", padx=5)
tk.Button(frame3, text="Stop", bg="red", fg="white", command=stop_download).pack(side="left", padx=5)
tk.Button(frame3, text="Clear", bg="orange", command=clear_log).pack(side="left", padx=5)

log_box = scrolledtext.ScrolledText(root, height=18)
log_box.pack(fill="both", expand=True, padx=10, pady=10)

root.mainloop()
