import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import pyautogui
import cv2
import numpy as np
from PIL import Image
import random
import os
import pytesseract
import requests


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pyautogui.FAILSAFE = True  # move mouse to upper-left to abort

class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Human-like Auto Clicker")

        # conditions: {name: {"img_path":..., "template":..., "action":...}}
        self.conditions = {}

        # control variables
        self.running = False
        self.thread = None
        self.neutral_x = tk.IntVar(value=500)
        self.neutral_y = tk.IntVar(value=500)
        self.move_min = tk.DoubleVar(value=0.4)   # seconds
        self.move_max = tk.DoubleVar(value=1.0)
        self.jitter_px = tk.IntVar(value=4)       # pixel jitter
        self.action_delay_min = tk.DoubleVar(value=0.2)
        self.action_delay_max = tk.DoubleVar(value=0.6)
        self.cooldown = tk.DoubleVar(value=1.0)   # per-condition cooldown
        self.threshold = tk.DoubleVar(value=0.82) # template match threshold

        self.last_triggered = {}  # condition_name -> last timestamp

        self.create_widgets()

    def create_widgets(self):
        # Neutral position inputs
        pos_frame = tk.LabelFrame(self.root, text="Neutral Mouse Position")
        pos_frame.pack(padx=10, pady=5, fill="x")
        tk.Label(pos_frame, text="X:").pack(side="left")
        tk.Entry(pos_frame, textvariable=self.neutral_x, width=6).pack(side="left", padx=5)
        tk.Label(pos_frame, text="Y:").pack(side="left")
        tk.Entry(pos_frame, textvariable=self.neutral_y, width=6).pack(side="left", padx=5)
        tk.Button(pos_frame, text="Pick Current Mouse", command=self.pick_mouse_pos).pack(side="left", padx=8)

        # Humanization settings
        human_frame = tk.LabelFrame(self.root, text="Humanization (movement & timing)")
        human_frame.pack(padx=10, pady=5, fill="x")
        tk.Label(human_frame, text="Move time (min - max sec):").grid(row=0, column=0, sticky="w")
        tk.Entry(human_frame, textvariable=self.move_min, width=6).grid(row=0, column=1, padx=3)
        tk.Entry(human_frame, textvariable=self.move_max, width=6).grid(row=0, column=2, padx=3)
        tk.Label(human_frame, text="Jitter px:").grid(row=0, column=3, padx=(10,0))
        tk.Entry(human_frame, textvariable=self.jitter_px, width=6).grid(row=0, column=4, padx=3)

        tk.Label(human_frame, text="Action delay (min - max sec):").grid(row=1, column=0, sticky="w", pady=4)
        tk.Entry(human_frame, textvariable=self.action_delay_min, width=6).grid(row=1, column=1)
        tk.Entry(human_frame, textvariable=self.action_delay_max, width=6).grid(row=1, column=2)

        tk.Label(human_frame, text="Per-condition cooldown (sec):").grid(row=1, column=3, sticky="w", padx=(10,0))
        tk.Entry(human_frame, textvariable=self.cooldown, width=6).grid(row=1, column=4)

        tk.Label(human_frame, text="Template threshold (0-1):").grid(row=2, column=0, sticky="w", pady=4)
        tk.Entry(human_frame, textvariable=self.threshold, width=6).grid(row=2, column=1)

        # Conditions Frame
        self.conds_frame = tk.LabelFrame(self.root, text="Conditions (add in the order you want them clicked)")
        self.conds_frame.pack(padx=10, pady=5, fill="both", expand=True)

        add_row = tk.Frame(self.root)
        add_row.pack(fill="x", padx=10)
        tk.Button(add_row, text="Add Condition", command=self.add_condition).pack(side="left")
        tk.Label(add_row, text="  (name first, then Load Image)").pack(side="left")

        # Start/Stop
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=8)
        self.start_btn = tk.Button(btn_frame, text="Start", command=self.start)
        self.start_btn.pack(side="left", padx=8)
        self.stop_btn = tk.Button(btn_frame, text="Stop", state="disabled", command=self.stop)
        self.stop_btn.pack(side="left", padx=8)

    def pick_mouse_pos(self):
        x, y = pyautogui.position()
        self.neutral_x.set(x)
        self.neutral_y.set(y)
        messagebox.showinfo("Neutral Position Set", f"Neutral set to: ({x}, {y})")

    def add_condition(self):
        cond_frame = tk.Frame(self.conds_frame, bd=1, relief="sunken", pady=5)
        cond_frame.pack(fill="x", pady=3, padx=3)

        cond_name_var = tk.StringVar()
        cond_img_path_var = tk.StringVar()
        action_var = tk.StringVar(value="Click")

        # Condition name
        tk.Label(cond_frame, text="Name:").pack(side="left")
        cond_name_entry = tk.Entry(cond_frame, textvariable=cond_name_var, width=14)
        cond_name_entry.pack(side="left", padx=6)

        def load_image():
            name = cond_name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Enter a condition name before loading an image.")
                return
            # prevent duplicate names
            if name in self.conditions and self.conditions[name].get("img_path"):
                if not messagebox.askyesno("Overwrite?", f"Condition '{name}' already exists. Overwrite?"):
                    return

            path = filedialog.askopenfilename(title="Select Condition Image",
                                              filetypes=[("PNG/JPG", "*.png;*.jpg;*.jpeg"), ("All files", "*.*")])
            if path:
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    messagebox.showerror("Error", "Failed to load image (unsupported or corrupt).")
                    return
                cond_img_path_var.set(path)
                self.conditions[name] = {"img_path": path, "template": img, "action": action_var.get()}
                img_label.config(text=os.path.basename(path))
                cond_name_entry.config(state="disabled")  # lock the name
                # store last_triggered
                self.last_triggered[name] = 0.0

        load_img_btn = tk.Button(cond_frame, text="Load Image", command=load_image)
        load_img_btn.pack(side="left", padx=6)

        img_label = tk.Label(cond_frame, text="No image", width=20, anchor="w")
        img_label.pack(side="left", padx=6)

        # Action dropdown
        tk.Label(cond_frame, text="Action:").pack(side="left", padx=5)
        action_menu = tk.OptionMenu(cond_frame, action_var, "Click", "Double Click", "Right Click", "Press Enter")
        action_menu.pack(side="left")

        # update action when changed
        def action_changed(*_):
            name = cond_name_var.get().strip()
            if name in self.conditions:
                self.conditions[name]["action"] = action_var.get()
        action_var.trace_add("write", action_changed)

    def start(self):
        if self.running:
            return
        if not self.conditions:
            messagebox.showwarning("Warning", "Add at least one condition.")
            return

        # verify templates loaded
        for name, data in list(self.conditions.items()):
            if data.get("template") is None:
                if data.get("img_path"):
                    img = cv2.imread(data["img_path"], cv2.IMREAD_GRAYSCALE)
                    if img is None:
                        messagebox.showerror("Error", f"Failed to load image for '{name}'")
                        return
                    self.conditions[name]["template"] = img
                else:
                    messagebox.showerror("Error", f"Condition '{name}' has no image.")
                    return

        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.thread = threading.Thread(target=self.run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def human_move_to(self, x, y):
        """
        Move mouse to (x,y) with human-like duration + jitter.
        """
        jitter = self.jitter_px.get()
        jx = random.randint(-jitter, jitter)
        jy = random.randint(-jitter, jitter)
        tx = x + jx
        ty = y + jy

        # choose a random duration in the configured range
        dmin = max(0.01, float(self.move_min.get()))
        dmax = max(dmin, float(self.move_max.get()))
        dur = random.uniform(dmin, dmax)

        # try to use pyautogui tween if available
        tween = getattr(pyautogui, "easeInOutQuad", None)
        if tween:
            pyautogui.moveTo(tx, ty, duration=dur, tween=tween)
        else:
            pyautogui.moveTo(tx, ty, duration=dur)

    def perform_action(self, click_pos, action):
        x, y = click_pos
        if action == "Click":
            pyautogui.click(x, y)
        elif action == "Double Click":
            pyautogui.doubleClick(x, y)
        elif action == "Right Click":
            pyautogui.rightClick(x, y)
        elif action == "Press Enter":
            pyautogui.click(x, y)
            time.sleep(random.uniform(0.05, 0.18))
            pyautogui.press("enter")
        else:
            # default to click
            pyautogui.click(x, y)

    def run_loop(self):
        neutral_pos = (int(self.neutral_x.get()), int(self.neutral_y.get()))
        threshold = float(self.threshold.get())

        # Main loop: detect, queue found conditions (in insertion order), then click one-by-one
        while self.running:
            try:
                screenshot = pyautogui.screenshot()
                screen_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
            except Exception as e:
                print("Screenshot error:", e)
                time.sleep(0.5)
                continue

            found_queue = []
            now = time.time()

            # iterate in insertion order (order of adding conditions)
            for cond_name, data in self.conditions.items():
                template = data.get("template")
                if template is None:
                    continue
                # per-condition cooldown check
                last_t = self.last_triggered.get(cond_name, 0.0)
                if (now - last_t) < float(self.cooldown.get()):
                    continue

                res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                if max_val >= threshold:
                    x, y = max_loc
                    h, w = template.shape[:2]
                    click_pos = (x + w // 2, y + h // 2)
                    found_queue.append((cond_name, click_pos, data["action"]))
                    # mark last_triggered now to avoid double-adding in same cycle
                    self.last_triggered[cond_name] = now

            # process each found condition one-by-one (human-like)
            if found_queue:
                for cond_name, click_pos, action in found_queue:
                    if not self.running:
                        break
                    # move like a human
                    try:
                        self.human_move_to(*click_pos)
                        # tiny random pause before click
                        time.sleep(random.uniform(0.05, 0.18))
                        self.perform_action(click_pos, action)
                        # random delay after action
                        time.sleep(random.uniform(float(self.action_delay_min.get()),
                                                  float(self.action_delay_max.get())))
                        # move back to neutral slowly
                        self.human_move_to(*neutral_pos)
                    except pyautogui.FailSafeException:
                        self.running = False
                        print("Fail-safe triggered; stopping.")
                        break
                    except Exception as e:
                        print("Error performing action:", e)
                    # small pause before looking for next condition
                    time.sleep(0.08)

            # short sleep to avoid full CPU usage
            time.sleep(5)

        print("AutoClicker stopped.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()
def send_telegram_photo(self, image_path, caption="Screenshot"):
    token = "YOUR_TELEGRAM_BOT_TOKEN"
    chat_id = "YOUR_CHAT_ID"
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(image_path, "rb") as img_file:
        resp = requests.post(url, data={"chat_id": chat_id, "caption": caption}, files={"photo": img_file})
    if resp.status_code != 200:
        print("Telegram send failed:", resp.text)
#/...../ 
def send_telegram_photo(self, image_path, caption="Screenshot"):
    token = "YOUR_TELEGRAM_BOT_TOKEN"
    chat_id = "YOUR_CHAT_ID"
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(image_path, "rb") as img_file:
        resp = requests.post(url, data={"chat_id": chat_id, "caption": caption}, files={"photo": img_file})
    if resp.status_code != 200:
        print("Telegram send failed:", resp.text)
