import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import pyautogui
import cv2
import numpy as np
from PIL import Image

pyautogui.FAILSAFE = True

class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Clicker with Condition Actions")

        self.conditions = {}  # {cond_name: {"img_path": str, "template": np.array, "action": str}}

        self.running = False
        self.thread = None

        self.neutral_x = tk.IntVar(value=500)
        self.neutral_y = tk.IntVar(value=500)

        self.create_widgets()

    def create_widgets(self):
        # Neutral position inputs
        pos_frame = tk.LabelFrame(self.root, text="Neutral Mouse Position")
        pos_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(pos_frame, text="X:").pack(side="left")
        tk.Entry(pos_frame, textvariable=self.neutral_x, width=5).pack(side="left", padx=5)
        tk.Label(pos_frame, text="Y:").pack(side="left")
        tk.Entry(pos_frame, textvariable=self.neutral_y, width=5).pack(side="left", padx=5)

        # Conditions Frame
        self.conds_frame = tk.LabelFrame(self.root, text="Conditions")
        self.conds_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.add_condition_button = tk.Button(self.root, text="Add Condition", command=self.add_condition)
        self.add_condition_button.pack(pady=5)

        # Start/Stop buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.start_btn = tk.Button(btn_frame, text="Start", command=self.start)
        self.start_btn.pack(side="left", padx=10)

        self.stop_btn = tk.Button(btn_frame, text="Stop", state="disabled", command=self.stop)
        self.stop_btn.pack(side="left", padx=10)

    def add_condition(self):
        cond_frame = tk.Frame(self.conds_frame, bd=1, relief="sunken", pady=5)
        cond_frame.pack(fill="x", pady=3)

        cond_name_var = tk.StringVar()
        cond_img_path_var = tk.StringVar()
        action_var = tk.StringVar(value="Click")

        # Condition name
        tk.Label(cond_frame, text="Condition Name:").pack(side="left")
        cond_name_entry = tk.Entry(cond_frame, textvariable=cond_name_var, width=15)
        cond_name_entry.pack(side="left", padx=5)

        # Load image button
        def load_image():
            path = filedialog.askopenfilename(title="Select Condition Image",
                                              filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
            if path:
                cond_img_path_var.set(path)
                # Load image for template matching
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    messagebox.showerror("Error", "Failed to load image.")
                    return
                self.conditions[cond_name_var.get()] = {"img_path": path, "template": img, "action": action_var.get()}
                img_label.config(text=path.split("/")[-1])

        load_img_btn = tk.Button(cond_frame, text="Load Image", command=load_image)
        load_img_btn.pack(side="left", padx=5)

        img_label = tk.Label(cond_frame, text="No image loaded", width=20, anchor="w")
        img_label.pack(side="left", padx=5)

        # Action dropdown
        tk.Label(cond_frame, text="Action:").pack(side="left", padx=5)
        action_menu = tk.OptionMenu(cond_frame, action_var, "Click", "Double Click", "Right Click", "Press Enter")
        action_menu.pack(side="left")

        # Save condition name and action changes live
        def update_condition_name(*args):
            name = cond_name_var.get()
            if name:
                if name not in self.conditions:
                    self.conditions[name] = {"img_path": cond_img_path_var.get(), "template": None, "action": action_var.get()}
                else:
                    self.conditions[name]["action"] = action_var.get()

        cond_name_var.trace_add("write", update_condition_name)
        action_var.trace_add("write", update_condition_name)

    def start(self):
        if self.running:
            return
        if not self.conditions:
            messagebox.showwarning("Warning", "Add at least one condition.")
            return
        # Load templates for all conditions
        for cond, data in self.conditions.items():
            if data["template"] is None and data["img_path"]:
                img = cv2.imread(data["img_path"], cv2.IMREAD_GRAYSCALE)
                if img is None:
                    messagebox.showerror("Error", f"Failed to load image for {cond}")
                    return
                self.conditions[cond]["template"] = img

        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.thread = threading.Thread(target=self.run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def run_loop(self):
        neutral_pos = (self.neutral_x.get(), self.neutral_y.get())
        threshold = 0.8  # Template match threshold

        while self.running:
            screenshot = pyautogui.screenshot()
            screen_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)

            for cond_name, data in self.conditions.items():
                template = data["template"]
                if template is None:
                    continue

                res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

                if max_val >= threshold:
                    x, y = max_loc
                    w, h = template.shape[::-1]
                    click_pos = (x + w // 2, y + h // 2)

                    # Perform action
                    if data["action"] == "Click":
                        pyautogui.click(click_pos)
                    elif data["action"] == "Double Click":
                        pyautogui.doubleClick(click_pos)
                    elif data["action"] == "Right Click":
                        pyautogui.rightClick(click_pos)
                    elif data["action"] == "Press Enter":
                        pyautogui.click(click_pos)
                        pyautogui.press("enter")

                    # Move back to neutral
                    pyautogui.moveTo(neutral_pos)

                    print(f"Action '{data['action']}' performed on {cond_name} at {click_pos}")
                    time.sleep(0.5)  # Wait a bit before next scan

            time.sleep(10)


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()
