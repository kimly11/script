"""
FB Account GUI (SAFE DEMO)
- Provides a UI matching the screenshot layout and controls
- Import emails from .txt/.csv (supports email, email:password, email,password)
- Populate table with columns: No, Name, User ID, Password, Cookies, Phone Number, Email, DOB
- Export to TXT/CSV/XLSX
- Start button will LAUNCH Chrome or LDPlayer instances (no signup automation)
- Includes simple password generator & random DOB filler for demo
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv, random, subprocess, os
from pathlib import Path
import datetime

# -------------- Configure platform-specific executables here --------------
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # adjust if needed or set "chrome"
LDPLAYER_EXE = r"C:\LDPlayer\dnplayer.exe"      # adjust to your LDPlayer installation
DNCONSOLE_EXE = r"C:\LDPlayer\dnconsole.exe"    # optional, if you use dnconsole to target indices
# -------------------------------------------------------------------------

def simple_password(length=10):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&*"
    return "".join(random.choice(chars) for _ in range(length))

def random_dob(start_year=1970, end_year=2000):
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    # choose valid day
    day = random.randint(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}"

class SafeFBGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Create Account Facebook - SAFE DEMO")
        self.geometry("1100x650")
        self.resizable(True, True)

        self.data = []  # list of dicts for rows

        self._build_top_controls()
        self._build_table()
        self._build_bottom_buttons()
        self._build_statusbar()

        self.running = False

    def _build_top_controls(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)

        # Number of Browsers
        ttk.Label(top, text="Select Number of Browsers :").grid(row=0, column=0, sticky="w")
        self.num_browsers = ttk.Combobox(top, values=[1,2,3,4,5,6,7,8], width=6, state="readonly")
        self.num_browsers.current(3)  # default 4 to match screenshot
        self.num_browsers.grid(row=0, column=1, padx=6)

        # Number of Loops
        ttk.Label(top, text="Number of Loops :").grid(row=0, column=2, sticky="w", padx=(12,0))
        self.num_loops = ttk.Combobox(top, values=[1,2,3,5,10,20], width=6, state="readonly")
        self.num_loops.current(0)
        self.num_loops.grid(row=0, column=3, padx=6)

        # Manual password / random
        ttk.Label(top, text="Password Mode:").grid(row=0, column=4, sticky="w", padx=(12,0))
        self.pass_mode = tk.StringVar(value="random")
        tk.Radiobutton(top, text="Random Password", variable=self.pass_mode, value="random").grid(row=0, column=5, sticky="w")
        tk.Radiobutton(top, text="Manual: Input", variable=self.pass_mode, value="manual").grid(row=0, column=6, sticky="w")
        self.manual_pass_entry = ttk.Entry(top, width=18)
        self.manual_pass_entry.grid(row=0, column=7, padx=6)
        self.manual_pass_entry.insert(0, "Beringin@333")

        # Language radio
        lang_frame = ttk.LabelFrame(self, text="Select Language")
        lang_frame.pack(fill="x", padx=8, pady=6)
        self.lang = tk.StringVar(value="Khmer (English)")
        langs = ["English","Khmer","Thai","Khmer (English)"]
        col = 0
        for l in langs:
            tk.Radiobutton(lang_frame, text=l, variable=self.lang, value=l).grid(row=0, column=col, padx=8, sticky="w")
            col += 1

        # Browser Mode radio
        browser_frame = ttk.LabelFrame(self, text="Browser Mode")
        browser_frame.pack(fill="x", padx=8, pady=6)
        self.browser_mode_var = tk.StringVar(value="Chrome")
        tk.Radiobutton(browser_frame, text="Chrome", variable=self.browser_mode_var, value="Chrome").pack(side="left", padx=8)
        tk.Radiobutton(browser_frame, text="Hide", variable=self.browser_mode_var, value="Hide").pack(side="left", padx=8)
        # (Note: hide is just UI flair here)

        # Registration Mode, Country, Fix Phone, Prefix, Digits
        reg_frame = ttk.Frame(self)
        reg_frame.pack(fill="x", padx=8, pady=6)

        ttk.Label(reg_frame, text="Registration Mode :").grid(row=0, column=0, sticky="w")
        self.reg_mode = tk.StringVar(value="Phone")
        tk.Radiobutton(reg_frame, text="Phone", variable=self.reg_mode, value="Phone").grid(row=0, column=1)
        tk.Radiobutton(reg_frame, text="Email", variable=self.reg_mode, value="Email").grid(row=0, column=2)

        ttk.Label(reg_frame, text="Country:").grid(row=0, column=3, sticky="w", padx=(12,0))
        self.country = ttk.Combobox(reg_frame, values=["Khmer","Thailand","Philippines","USA"], width=15, state="readonly")
        self.country.set("Khmer")
        self.country.grid(row=0, column=4, padx=6)

        self.fix_phone_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(reg_frame, text="Fix Phone", variable=self.fix_phone_var).grid(row=0, column=5, padx=6)

        ttk.Label(reg_frame, text="Prefix:").grid(row=0, column=6, padx=(6,0))
        self.prefix_entry = ttk.Entry(reg_frame, width=8)
        self.prefix_entry.grid(row=0, column=7, padx=4)
        ttk.Label(reg_frame, text="Digits:").grid(row=0, column=8, padx=(6,0))
        self.digits_spin = tk.Spinbox(reg_frame, from_=4, to=12, width=4)
        self.digits_spin.grid(row=0, column=9, padx=4)

        # Email domains
        domain_frame = ttk.Frame(self)
        domain_frame.pack(fill="x", padx=8, pady=(6,0))
        ttk.Label(domain_frame, text="Email Domains:").pack(side="left")
        self.dom_hot = tk.BooleanVar(); ttk.Checkbutton(domain_frame, text="Hotmail", variable=self.dom_hot).pack(side="left", padx=4)
        self.dom_gmail = tk.BooleanVar(); ttk.Checkbutton(domain_frame, text="Gmail", variable=self.dom_gmail).pack(side="left", padx=4)
        self.dom_yahoo = tk.BooleanVar(); ttk.Checkbutton(domain_frame, text="Yahoo", variable=self.dom_yahoo).pack(side="left", padx=4)
        self.dom_yandex = tk.BooleanVar(); ttk.Checkbutton(domain_frame, text="Yandex", variable=self.dom_yandex).pack(side="left", padx=4)
        ttk.Label(domain_frame, text="If no email domain selected, a random domain will be used").pack(side="left", padx=12)

    def _build_table(self):
        cols = ("No","Name","User ID","Password","Cookies","Phone Number","Email","Date Of Birth")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        for c in cols:
            self.tree.heading(c, text=c)
            # set widths similar to screenshot feel
        self.tree.column("No", width=40, anchor="center")
        self.tree.column("Name", width=160)
        self.tree.column("User ID", width=120)
        self.tree.column("Password", width=120)
        self.tree.column("Cookies", width=120)
        self.tree.column("Phone Number", width=120)
        self.tree.column("Email", width=240)
        self.tree.column("Date Of Birth", width=110, anchor="center")

        # vertical scrollbar
        vs = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vs.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(8,0), pady=8)
        vs.pack(side="left", fill="y", pady=8)

    def _build_bottom_buttons(self):
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=8, pady=(0,8))

        # Buttons: Start, Stop, Select All, Import, Export TXT, Export Excel, Export CSV, Clear
        self.start_btn = tk.Button(btn_frame, text="Start", bg="#0022cc", fg="white", width=10, command=self.on_start)
        self.start_btn.pack(side="left", padx=6)
        self.stop_btn = tk.Button(btn_frame, text="Stop", bg="#d80000", fg="white", width=10, command=self.on_stop)
        self.stop_btn.pack(side="left", padx=6)
        self.select_all_btn = tk.Button(btn_frame, text="Select All", bg="#1e90ff", fg="white", width=10, command=self.select_all)
        self.select_all_btn.pack(side="left", padx=6)
        self.import_btn = tk.Button(btn_frame, text="Import", bg="#1e90ff", fg="white", width=10, command=self.import_file)
        self.import_btn.pack(side="left", padx=6)
        self.export_txt_btn = tk.Button(btn_frame, text="Export TXT", bg="#ffbe00", fg="white", width=10, command=self.export_txt)
        self.export_txt_btn.pack(side="left", padx=6)
        self.export_xlsx_btn = tk.Button(btn_frame, text="Export Excel", bg="#2c9b2c", fg="white", width=12, command=self.export_xlsx)
        self.export_xlsx_btn.pack(side="left", padx=6)
        self.export_csv_btn = tk.Button(btn_frame, text="Export CSV", bg="#8b2ccf", fg="white", width=10, command=self.export_csv)
        self.export_csv_btn.pack(side="left", padx=6)
        self.clear_btn = tk.Button(btn_frame, text="Clear", bg="#ff0000", fg="white", width=10, command=self.clear_table)
        self.clear_btn.pack(side="left", padx=6)

        # Extra utilities: fill password/dob for selected rows
        util_frame = ttk.Frame(self)
        util_frame.pack(fill="x", padx=8, pady=(0,8))
        tk.Button(util_frame, text="Fill Passwords (selected)", command=self.fill_passwords).pack(side="left", padx=6)
        tk.Button(util_frame, text="Fill DOB (selected)", command=self.fill_dobs).pack(side="left", padx=6)

    def _build_statusbar(self):
        self.status_var = tk.StringVar(value="Status: Loop: 1 / 1 | Successful: 0")
        status_label = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w")
        status_label.pack(side="bottom", fill="x")

    # ---------- Table & Data helpers ----------
    def refresh_table(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        for idx, row in enumerate(self.data, start=1):
            vals = (idx,
                    row.get("name",""),
                    row.get("user_id",""),
                    row.get("password",""),
                    row.get("cookies",""),
                    row.get("phone",""),
                    row.get("email",""),
                    row.get("dob",""))
            self.tree.insert("", "end", values=vals)

    def import_file(self):
        p = filedialog.askopenfilename(title="Select email file", filetypes=[("Text / CSV","*.txt *.csv"),("All","*.*")])
        if not p:
            return
        loaded = []
        try:
            if p.lower().endswith(".csv"):
                with open(p, newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if not row: continue
                        email = row[0].strip()
                        pwd = row[1].strip() if len(row) > 1 else ""
                        if email:
                            loaded.append((email, pwd))
            else:
                with open(p, encoding="utf-8") as f:
                    for line in f:
                        s = line.strip()
                        if not s: continue
                        if ":" in s:
                            email, pwd = s.split(":",1)
                        elif "," in s:
                            email, pwd = s.split(",",1)
                        else:
                            email, pwd = s, ""
                        loaded.append((email.strip(), pwd.strip()))
        except Exception as e:
            messagebox.showerror("Import Error", str(e))
            return

        # append to self.data with placeholders
        for email, pwd in loaded:
            entry = {"name": "", "user_id": "", "password": pwd or "—", "cookies": "", "phone": "", "email": email, "dob": ""}
            self.data.append(entry)
        self.refresh_table()
        self.status_var.set(f"Status: Loaded {len(loaded)} emails. Total rows: {len(self.data)}")

    def clear_table(self):
        if not self.data:
            return
        if not messagebox.askyesno("Clear", "Clear all rows?"):
            return
        self.data.clear()
        self.refresh_table()
        self.status_var.set("Status: Cleared.")

    def select_all(self):
        # select all items in the treeview UI
        for iid in self.tree.get_children():
            self.tree.selection_add(iid)

    def export_txt(self):
        p = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text","*.txt")])
        if not p: return
        try:
            with open(p, "w", encoding="utf-8") as f:
                for row in self.data:
                    f.write(f"{row.get('email','')}\t{row.get('password','')}\t{row.get('phone','')}\n")
            messagebox.showinfo("Export", f"Exported to {p}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def export_csv(self):
        p = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not p: return
        try:
            with open(p, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Name","User ID","Password","Cookies","Phone Number","Email","Date Of Birth"])
                for row in self.data:
                    writer.writerow([row.get("name",""), row.get("user_id",""), row.get("password",""),
                                     row.get("cookies",""), row.get("phone",""), row.get("email",""), row.get("dob","")])
            messagebox.showinfo("Export", f"Exported to {p}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def export_xlsx(self):
        try:
            import pandas as pd
        except Exception:
            messagebox.showerror("Missing dependency", "Please install pandas (pip install pandas openpyxl) to export Excel.")
            return
        p = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")])
        if not p: return
        df = pd.DataFrame([
            {"Name":r.get("name",""), "User ID":r.get("user_id",""), "Password":r.get("password",""),
             "Cookies":r.get("cookies",""), "Phone Number":r.get("phone",""), "Email":r.get("email",""), "Date Of Birth":r.get("dob","")}
            for r in self.data
        ])
        try:
            df.to_excel(p, index=False)
            messagebox.showinfo("Export", f"Exported to {p}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    # Utilities to fill selected rows
    def fill_passwords(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Fill Passwords", "Select rows to fill.")
            return
        manual = self.pass_mode.get() == "manual"
        for iid in sel:
            vals = list(self.tree.item(iid, "values"))
            # vals order: No,Name,User ID,Password,Cookies,Phone,Email,DOB
            if manual:
                pwd = self.manual_pass_entry.get().strip() or "password123"
            else:
                pwd = simple_password(10)
            vals[3] = pwd
            # update object in self.data using No field
            try:
                idx = int(vals[0]) - 1
                self.data[idx]["password"] = pwd
            except:
                pass
            self.tree.item(iid, values=vals)
        self.status_var.set("Status: Passwords filled for selected rows.")

    def fill_dobs(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Fill DOB", "Select rows to fill.")
            return
        for iid in sel:
            vals = list(self.tree.item(iid, "values"))
            dob = random_dob(1970,2000)
            vals[7] = dob
            try:
                idx = int(vals[0]) - 1
                self.data[idx]["dob"] = dob
            except:
                pass
            self.tree.item(iid, values=vals)
        self.status_var.set("Status: DOB filled for selected rows.")

    # ---------- Start / Stop behavior (SAFE) ----------
    def on_start(self):
        # This will only launch Chrome or LDPlayer instances (no web automation).
        if self.running:
            messagebox.showinfo("Already running", "Process already running.")
            return
        try:
            n = int(self.num_browsers.get())
        except Exception:
            n = 1
        mode = self.browser_mode_var.get()
        loops = int(self.num_loops.get())

        if mode == "Chrome":
            self._launch_chrome(n)
        elif mode == "Hide":
            # "Hide" is not launching; we just simulate behavior
            messagebox.showinfo("Hide mode", "Hide mode selected — no applications will be launched.")
            self._simulate_progress(n, loops)
        else:
            # Default: try LDPlayer
            self._launch_ldplayer(n)

        # After launch, simulate row status updates to show demo "progress"
        self._simulate_progress(n, loops)

    def on_stop(self):
        # In this safe demo we can't forcibly stop external apps; just stop simulated progress
        if not self.running:
            self.status_var.set("Status: Idle")
            return
        self.running = False
        self.status_var.set("Status: Stopped by user")

    def _launch_chrome(self, n):
        exe = CHROME_PATH if os.path.exists(CHROME_PATH) else "chrome"
        launched = 0
        for i in range(n):
            try:
                subprocess.Popen([exe])
                launched += 1
                self._append_status_row(f"Chrome window #{i+1} launched")
            except FileNotFoundError:
                messagebox.showerror("Chrome not found", f"Chrome not found at {CHROME_PATH}.")
                break
            except Exception as e:
                self._append_status_row(f"Chrome launch error: {e}")
        self.status_var.set(f"Status: Launched {launched} Chrome instance(s).")

    def _launch_ldplayer(self, n):
        # If dnconsole exists and user installed, you may launch by index; fallback to dnplayer
        use_console = os.path.exists(DNCONSOLE_EXE)
        if use_console:
            for idx in range(n):
                cmd = [DNCONSOLE_EXE, "launch", "--index", str(idx)]
                try:
                    subprocess.Popen(cmd)
                    self._append_status_row(f"dnconsole: asked to launch index {idx}")
                except Exception as e:
                    self._append_status_row(f"dnconsole launch error idx {idx}: {e}")
        else:
            if not os.path.exists(LDPLAYER_EXE):
                messagebox.showerror("LDPlayer not found", f"Could not find LDPlayer at:\n{LDPLAYER_EXE}")
                return
            for i in range(n):
                try:
                    subprocess.Popen([LDPLAYER_EXE])
                    self._append_status_row(f"LDPlayer launch call #{i+1} sent (dnplayer).")
                except Exception as e:
                    self._append_status_row(f"LDPlayer launch error: {e}")
        self.status_var.set(f"Status: Launched {n} LDPlayer call(s).")

    def _append_status_row(self, text):
        # append a log-like row at the end if table shorter than index
        self.tree.insert("", "end", values=("-", "-", "-", "-", "-", "-", "-", text))

    def _simulate_progress(self, num_instances:int, loops:int):
        # This is a SAFE visual simulation to mimic activity on rows. It DOES NOT touch the internet.
        if not self.data:
            # if no rows, create demo rows equal to num_instances
            for i in range(num_instances):
                demo = {"name": f"Demo{i+1}", "user_id": f"user_demo{i+1}", "password": simple_password(10),
                        "cookies":"", "phone":"", "email":f"demo{i+1}@example.com", "dob": random_dob()}
                self.data.append(demo)
            self.refresh_table()

        self.running = True
        total_success = 0
        total_loops = loops
        for loop_index in range(1, total_loops+1):
            if not self.running:
                break
            # iterate rows and pretend to "process"
            for idx in range(len(self.data)):
                if not self.running:
                    break
                # update status cell by rewriting the row values
                item_id = self.tree.get_children()[idx]
                rowvals = list(self.tree.item(item_id, "values"))
                rowvals[3] = rowvals[3] or simple_password(10)  # ensure password displayed
                rowvals[4] = rowvals[4]  # cookies cell placeholder
                # set status text into DOB field temporarily for demo (since table columns fixed)
                status_text = f"Loop {loop_index}/{total_loops} - instance { (idx % num_instances) + 1 } queued"
                rowvals[7] = status_text
                self.tree.item(item_id, values=rowvals)
                # fake "success" for some rows randomly
                if random.random() < 0.15:
                    total_success += 1
                    # mark as success
                    rowvals[7] = "Successful (demo only)"
                    self.data[idx]["dob"] = rowvals[7]
                    self.tree.item(item_id, values=rowvals)

            self.status_var.set(f"Status: Loop: {loop_index} / {total_loops} | Successful: {total_success}")
            self.update()
            # small delay to show progress (non-blocking UI):
            self.after(600)
            self.update()

        self.running = False
        self.status_var.set(f"Status: Done. Loops: {total_loops} | Successful (demo): {total_success}")

if __name__ == "__main__":
    app = SafeFBGui()
    app.mainloop()
