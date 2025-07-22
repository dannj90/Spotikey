import os
import sys
import json
import threading
import time
import webbrowser
import requests
import keyboard
import queue
import signal
import winshell
from flask import Flask, request
import tkinter as tk
from tkinter import messagebox, scrolledtext
from win10toast import ToastNotifier
import pystray
from PIL import Image, ImageDraw, ImageTk
from datetime import datetime

# === APP INFO ===
APP_NAME = "Spotikey"
APP_VERSION = "0.9.3.1"
GITHUB_REPO_URL = "https://github.com/dannj90/Spotikey"
GITHUB_API_URL = "https://api.github.com/repos/dannj90/Spotikey/releases/latest"

# === RESOURCE PATH ===
def resource_path(relative_path):
    """Get absolute path to resource (works for dev and PyInstaller)."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# === APPDATA FOLDER ===
APPDATA_DIR = os.path.join(os.getenv("APPDATA"), "Spotikey")
os.makedirs(APPDATA_DIR, exist_ok=True)

DATA_FILE = os.path.join(APPDATA_DIR, "spotikey_data.json")
LOG_FILE = os.path.join(APPDATA_DIR, "spotikey.log")
ICON_FILE = resource_path("spotikey.ico")
CERT_FILE = resource_path("cert.pem")
KEY_FILE = resource_path("key.pem")

# === DEFAULT DATA ===
DEFAULT_DATA = {
    "hotkey": "ctrl+alt+l",
    "notifications": True,
    "client_id": "",
    "client_secret": "",
    "token_info": {},
    "run_on_startup": False
}

# === GLOBALS ===
LOG_MESSAGES = []
tray_icon = None
main_window = None
current_hotkey = None
notifier = ToastNotifier()
gui_queue = queue.Queue()
TOKEN_INFO = {}
LATEST_VERSION = None

# === DATA HANDLING ===
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    save_data(DEFAULT_DATA)
    return DEFAULT_DATA.copy()

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def log_message(msg):
    print(msg)
    LOG_MESSAGES.append(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    if main_window and main_window.log_box:
        main_window.refresh_log()

def clear_log():
    open(LOG_FILE, "w").close()
    LOG_MESSAGES.clear()
    if main_window:
        main_window.refresh_log()
    log_message("🧹 Log cleared.")

def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f]
    return []

def notify(title, message):
    data = load_data()
    if data.get("notifications", True):
        try:
            notifier.show_toast(title, message, duration=3, threaded=True, icon_path=ICON_FILE)
        except Exception as e:
            print(f"[WARN] Notification failed: {e}")

# === UPDATE CHECKER ===
def check_for_update():
    """Check GitHub for the latest Spotikey release version."""
    try:
        response = requests.get(GITHUB_API_URL, timeout=5)
        if response.status_code == 200:
            latest = response.json().get("tag_name", "").lstrip("v")
            if latest and latest != APP_VERSION:
                return latest
        return None
    except Exception as e:
        print(f"[WARN] Update check failed: {e}")
        return None

def prompt_update(latest_version):
    """Prompt user with update info."""
    if messagebox.askyesno(APP_NAME, f"A new version of Spotikey is available (v{latest_version}).\nWould you like to download it now?"):
        webbrowser.open(GITHUB_REPO_URL + "/releases")

def manual_update_check():
    latest_version = check_for_update()
    if latest_version:
        if messagebox.askyesno(APP_NAME, f"A new version of Spotikey is available (v{latest_version}).\nWould you like to download it now?"):
            webbrowser.open(GITHUB_REPO_URL + "/releases")
    else:
        messagebox.showinfo(APP_NAME, "You are running the latest version of Spotikey.")

# === ICONS ===
def load_icon():
    try:
        return Image.open(ICON_FILE)
    except Exception as e:
        print(f"[WARN] Failed to load icon: {e}")
        image = Image.new("RGB", (64, 64), (29, 185, 84))
        draw = ImageDraw.Draw(image)
        draw.ellipse((8, 8, 56, 56), fill=(0, 0, 0))
        return image

def get_tk_logo():
    try:
        img = Image.open(ICON_FILE)
        img = img.resize((48, 48), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"[WARN] Failed to load Spotikey logo: {e}")
        return None

# === FLASK SERVER ===
app = Flask(__name__)
REDIRECT_URI = "https://127.0.0.1:8888/callback"
SCOPE = "user-library-modify user-read-currently-playing"

@app.route("/callback")
def callback():
    global TOKEN_INFO
    code = request.args.get("code")
    if not code:
        return "Error: No code returned!"
    data = load_data()
    TOKEN_INFO = exchange_code_for_token(code, data["client_id"], data["client_secret"])
    if TOKEN_INFO:
        data["token_info"] = TOKEN_INFO
        save_data(data)
        notify(APP_NAME, "Authentication successful!")
        return "Authentication successful! You can close this tab."
    return "Error: Could not exchange code for token."

def start_flask():
    app.run(host="127.0.0.1", port=8888, ssl_context=(CERT_FILE, KEY_FILE))

# === SPOTIFY AUTH ===
def exchange_code_for_token(code, client_id, client_secret):
    token_url = "https://accounts.spotify.com/api/token"
    response = requests.post(token_url, data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "client_secret": client_secret,
    })
    data = response.json()
    if "access_token" in data:
        data['expires_at'] = int(time.time()) + data.get('expires_in', 3600)
        return data
    return None

def refresh_token(refresh_token, client_id, client_secret):
    token_url = "https://accounts.spotify.com/api/token"
    response = requests.post(token_url, data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    })
    data = response.json()
    if 'access_token' in data:
        if 'refresh_token' not in data:
            data['refresh_token'] = refresh_token
        data['expires_at'] = int(time.time()) + data.get('expires_in', 3600)
        save_token_info(data)
        return data
    return None

def save_token_info(token_info):
    data = load_data()
    data["token_info"] = token_info
    save_data(data)

def authenticate_spotify():
    global TOKEN_INFO
    data = load_data()
    if not data["client_id"] or not data["client_secret"]:
        return False
    TOKEN_INFO = data.get("token_info", {})
    if TOKEN_INFO and TOKEN_INFO.get("expires_at", 0) > int(time.time()):
        log_message("✅ Existing token is still valid.")
        return True
    if TOKEN_INFO and "refresh_token" in TOKEN_INFO:
        refreshed = refresh_token(TOKEN_INFO["refresh_token"], data["client_id"], data["client_secret"])
        if refreshed:
            TOKEN_INFO = refreshed
            log_message("🔄 Token refreshed successfully.")
            return True
    log_message("🌐 No valid token found, starting login flow...")
    auth_url = (
        "https://accounts.spotify.com/authorize?"
        + f"client_id={data['client_id']}&response_type=code"
        + f"&redirect_uri={REDIRECT_URI}&scope={SCOPE}&show_dialog=true"
    )
    threading.Thread(target=start_flask, daemon=True).start()
    webbrowser.open(auth_url)
    while not TOKEN_INFO:
        time.sleep(1)
    save_token_info(TOKEN_INFO)
    notify(APP_NAME, "New token generated!")
    return True

def get_headers():
    data = load_data()
    if TOKEN_INFO.get("expires_at", 0) <= int(time.time()):
        refreshed = refresh_token(TOKEN_INFO.get("refresh_token"), data["client_id"], data["client_secret"])
        if refreshed:
            TOKEN_INFO.update(refreshed)
            save_token_info(TOKEN_INFO)
            log_message("🔄 Token refreshed successfully.")
        else:
            log_message("❌ Token expired and refresh failed. Please re-login.")
            notify(APP_NAME, "Token expired. Please re-login.")
            return None
    return {
        "Authorization": f"Bearer {TOKEN_INFO['access_token']}",
        "Content-Type": "application/json"
    }

# === SPOTIFY ACTION ===
def like_current_song():
    headers = get_headers()
    if not headers:
        return
    try:
        playback = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
        if playback.status_code == 200 and playback.json():
            track = playback.json()["item"]
            track_name = track["name"]
            response = requests.put(
                "https://api.spotify.com/v1/me/tracks",
                headers=headers,
                json={"ids": [track["id"]]}
            )
            if response.status_code in (200, 201):
                log_message(f"💚 Liked: {track_name}")
                notify(APP_NAME, f"💚 Liked: {track_name}")
            else:
                log_message(f"❌ Failed to like track: {track_name}")
        else:
            log_message("⚠ No track is currently playing.")
    except Exception as e:
        log_message(f"❌ Error: {e}")

# === RUN ON STARTUP ===
def set_run_on_startup(enable):
    shortcut_path = os.path.join(winshell.startup(), "Spotikey.lnk")
    if enable:
        winshell.CreateShortcut(
            Path=shortcut_path,
            Target=sys.executable,
            Icon=(ICON_FILE, 0),
            Description="Spotikey Auto Start"
        )
        log_message("🔄 Run on startup enabled.")
    else:
        try:
            os.remove(shortcut_path)
            log_message("⏹ Run on startup disabled.")
        except:
            pass

# === GUI ===
class SpotikeyMain(tk.Tk):
    def __init__(self):
        super().__init__()
        try:
            import ctypes
            APP_ID = "Spotikey.App"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except Exception as e:
            print(f"[WARN] Could not set taskbar AppUserModelID: {e}")

        icon_path = resource_path("spotikey.ico")
        try:
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"[WARN] Could not set window icon: {e}")

        try:
            icon_img = Image.open(icon_path).resize((32, 32), Image.LANCZOS)
            icon_photo = ImageTk.PhotoImage(icon_img)
            self.iconphoto(True, icon_photo)
        except Exception as e:
            print(f"[WARN] Could not set taskbar icon: {e}")

        self.title(APP_NAME)
        self.geometry("1000x400")
        self.minsize(1000, 400)
        self.configure(bg="#191414")
        self.logo_img = get_tk_logo()
        self.log_box = None
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.bind("<Unmap>", self.on_minimize)

    def on_minimize(self, event):
        if self.state() == 'iconic':
            self.hide_to_tray()

    def hide_to_tray(self):
        self.withdraw()
        log_message("🔽 Spotikey minimized to tray.")
        notify(APP_NAME, "Spotikey is still running in the system tray.")

    def show_window(self):
        self.deiconify()
        self.lift()
        self.refresh_log()

    def create_widgets(self):
        top_frame = tk.Frame(self, bg="#191414")
        top_frame.pack(fill="x", pady=(5, 0))

        if self.logo_img:
            tk.Label(self, image=self.logo_img, bg="#191414").pack(pady=5)

        help_button = tk.Button(
            top_frame,
            text="?",
            font=("Arial", 14, "bold"),
            bg="#1DB954",
            fg="white",
            width=2,
            relief="flat",
            command=self.open_help_window
        )
        help_button.pack(side="right", padx=10)

        # App version label
        tk.Label(self, text=f"{APP_NAME} v{APP_VERSION}", font=("Arial", 16, "bold"), bg="#191414", fg="#1DB954").pack(pady=5)

        # Update indicator
        if LATEST_VERSION:
            update_label = tk.Label(
                self,
                text=f"New version available (v{LATEST_VERSION}) – Click to download",
                font=("Arial", 10, "bold"),
                bg="#191414",
                fg="red",
                cursor="hand2"
            )
            update_label.pack(pady=(0, 10))
            update_label.bind("<Button-1>", lambda e: webbrowser.open(GITHUB_REPO_URL + "/releases"))

        self.log_box = scrolledtext.ScrolledText(self, wrap=tk.WORD, bg="#000000", fg="white", height=12)
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.refresh_log()

        data = load_data()
        settings_frame = tk.Frame(self, bg="#191414")
        settings_frame.pack(pady=10, fill="x")
        tk.Label(settings_frame, text="Hotkey:", bg="#191414", fg="white").pack(side="left", padx=5)
        self.hotkey_entry = tk.Entry(settings_frame, width=20)
        self.hotkey_entry.insert(0, data.get("hotkey", "ctrl+alt+l"))
        self.hotkey_entry.pack(side="left", padx=5)

        self.notifications_var = tk.BooleanVar(value=data.get("notifications", True))
        tk.Checkbutton(settings_frame, text="Enable Notifications", variable=self.notifications_var,
                       bg="#191414", fg="white", selectcolor="#191414").pack(side="left", padx=10)

        self.startup_var = tk.BooleanVar(value=data.get("run_on_startup", False))
        tk.Checkbutton(settings_frame, text="Run on Startup", variable=self.startup_var,
                       bg="#191414", fg="white", selectcolor="#191414").pack(side="left", padx=10)

        tk.Button(settings_frame, text="Save Settings", bg="#1DB954", fg="white",
                  font=("Arial", 10, "bold"), relief="flat",
                  activebackground="#1ed760", activeforeground="black",
                  command=self.save_settings).pack(side="left", padx=10)

        tk.Button(settings_frame, text="Authorise", bg="#1DB954", fg="white",
                  font=("Arial", 10, "bold"), relief="flat",
                  command=self.open_authorise_window).pack(side="left", padx=10)

        tk.Button(settings_frame, text="Clear Log", bg="#1DB954", fg="white",
                  font=("Arial", 10, "bold"), relief="flat",
                  command=clear_log).pack(side="left", padx=10)

        tk.Button(settings_frame, text="Check for Updates", bg="#1DB954", fg="white",
                  font=("Arial", 10, "bold"), relief="flat",
                  command=manual_update_check).pack(side="left", padx=10)

    def refresh_log(self):
        self.log_box.delete(1.0, tk.END)
        for msg in load_log():
            self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)

    def save_settings(self):
        data = load_data()
        data["hotkey"] = self.hotkey_entry.get()
        data["notifications"] = self.notifications_var.get()
        data["run_on_startup"] = self.startup_var.get()
        save_data(data)
        rebind_hotkey()
        set_run_on_startup(data["run_on_startup"])
        messagebox.showinfo(APP_NAME, "Settings saved!")

    def open_authorise_window(self):
        AuthoriseWindow(self)

    def open_help_window(self):
        HelpWindow(self)

# === AUTHORISE WINDOW ===
class AuthoriseWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Authorise Spotify")
        self.configure(bg="#191414")
        self.geometry("400x200")
        self.resizable(False, False)
        try:
            if os.path.exists(ICON_FILE):
                self.iconbitmap(ICON_FILE)
        except:
            pass

        data = load_data()
        tk.Label(self, text="Client ID:", bg="#191414", fg="white").pack(pady=(10, 0))
        self.client_id_entry = tk.Entry(self, width=40)
        self.client_id_entry.insert(0, data.get("client_id", ""))
        self.client_id_entry.pack(pady=5)

        tk.Label(self, text="Client Secret:", bg="#191414", fg="white").pack(pady=(10, 0))
        self.client_secret_entry = tk.Entry(self, width=40, show="*")
        self.client_secret_entry.insert(0, data.get("client_secret", ""))
        self.client_secret_entry.pack(pady=5)

        tk.Button(self, text="Save & Authorise", bg="#1DB954", fg="white", font=("Arial", 10, "bold"),
                  relief="flat", command=self.save_and_auth).pack(pady=10)

    def save_and_auth(self):
        data = load_data()
        data["client_id"] = self.client_id_entry.get()
        data["client_secret"] = self.client_secret_entry.get()
        save_data(data)
        self.destroy()
        authenticate_spotify()

# === HELP WINDOW ===
class HelpWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Spotikey Help")
        self.configure(bg="#191414")
        self.geometry("500x400")
        self.resizable(True, True)

        try:
            if os.path.exists(ICON_FILE):
                self.iconbitmap(ICON_FILE)
        except:
            pass

        tk.Label(
            self, text="How to Authorise your App",
            font=("Arial", 14, "bold"), bg="#191414", fg="#1DB954"
        ).pack(pady=10)

        help_text = (
            "1. Go to Spotify Developer Dashboard (https://developer.spotify.com/dashboard/).\n"
            "2. Click \"Create an App\".\n"
            "3. Give the app a name (e.g., Hotkey).\n"
            "4. Add a description so you remember what the app is for later.\n"
            "5. Set the Redirect URI to: https://127.0.0.1:8888/callback\n"
            "6. Select Web API as the app type.\n"
            "7. Read and agree to the Spotify Developer Terms of Service.\n"
            "8. Click Save.\n"
            "9. Copy the Client ID and Client Secret, then paste them into Spotikey’s Authorise window."
        )

        text_box = scrolledtext.ScrolledText(
            self, wrap=tk.WORD, bg="#000000", fg="white", font=("Arial", 11)
        )
        text_box.insert(tk.END, help_text)
        text_box.config(state="disabled")
        text_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Button(
            self, text="Close", bg="#1DB954", fg="white",
            font=("Arial", 10, "bold"), relief="flat",
            command=self.destroy
        ).pack(pady=10)

# === TRAY ===
def create_tray_icon():
    global tray_icon
    def open_gui(icon, item):
        if main_window:
            main_window.show_window()
        else:
            gui_queue.put(True)
    def exit_app(icon, item):
        log_message("🔴 Spotikey is shutting down...")
        icon.stop()
        os._exit(0)
    image = load_icon()
    menu = pystray.Menu(
        pystray.MenuItem('Open Spotikey', open_gui),
        pystray.MenuItem('Check for Updates', lambda icon, item: manual_update_check()),
        pystray.MenuItem('Exit', exit_app)
    )
    tray_icon = pystray.Icon(APP_NAME, image, APP_NAME, menu)
    tray_icon.run()

# === HOTKEY ===
def rebind_hotkey():
    global current_hotkey
    if current_hotkey:
        keyboard.remove_hotkey(current_hotkey)
    data = load_data()
    hotkey = data.get("hotkey", "ctrl+alt+l")
    current_hotkey = keyboard.add_hotkey(hotkey, like_current_song)
    log_message(f"Hotkey set to {hotkey}")

def start_hotkey_listener():
    keyboard.wait()

# === MAIN ===
def start_tray_mode():
    global main_window
    if 'main_window' not in globals() or main_window is None:
        main_window = None
    rebind_hotkey()
    threading.Thread(target=start_hotkey_listener, daemon=True).start()
    log_message(f"🎵 {APP_NAME} v{APP_VERSION} is running in tray.")
    icon_thread = threading.Thread(target=create_tray_icon, daemon=False)
    icon_thread.start()
    while True:
        try:
            gui_queue.get(timeout=1)
            if main_window:
                main_window.show_window()
            else:
                main_window = SpotikeyMain()
                main_window.mainloop()
        except queue.Empty:
            pass

def main():
    global LOG_MESSAGES, main_window, LATEST_VERSION
    signal.signal(signal.SIGINT, lambda sig, frame: os._exit(0))
    signal.signal(signal.SIGTERM, lambda sig, frame: os._exit(0))

    LOG_MESSAGES = load_log()
    data = load_data()

    # Check for updates at startup
    LATEST_VERSION = check_for_update()
    if LATEST_VERSION:
        prompt_update(LATEST_VERSION)

    token_valid = authenticate_spotify()
    if not data["client_id"] or not data["client_secret"] or not token_valid:
        messagebox.showinfo(APP_NAME, "Welcome to Spotikey! Please Authorise your Spotify account.\nUse the '?' button in the top right for instructions.")
        log_message("⚙ Please Authorise the app.")
        main_window = SpotikeyMain()
        main_window.mainloop()
        data = load_data()
        if data["client_id"] and data["client_secret"]:
            token_valid = authenticate_spotify()
            if token_valid:
                log_message("✅ First-time setup complete. Hiding Spotikey to tray...")
                start_tray_mode()
        return
    if authenticate_spotify():
        start_tray_mode()

if __name__ == "__main__":
    main()
