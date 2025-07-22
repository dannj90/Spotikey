# Spotikey 🎵

Spotikey is a lightweight Windows app that allows you to quickly "like" the currently playing Spotify track using a customizable global hotkey.  
It also features a system tray icon, notifications, and an integrated Spotify authorization process.

---

## **Features**
- **Hotkey support**: Default `Ctrl + Alt + L` to "like" the current track.
- **Spotify OAuth2** authentication with refresh token handling.
- **System tray integration** (with minimize-to-tray).
- **Customizable settings** (hotkeys, notifications, run on startup).
- **Update checker**: Automatically checks for the latest version hosted on GitHub.
- **Help window**: Step-by-step instructions for Spotify API setup.

---

## **Requirements**
- **Windows 10/11**
- **Spotify Premium account** (to use the Web API)
- **Python 3.9+** (for development) or the **standalone .exe** (for end users)

---

## **Installation**
1. Download the latest release `.exe` from the [Releases page](https://github.com/dannj90/Spotikey/releases).
2. Run `Spotikey.exe`.
3. Authorize the app with your **Spotify Developer Dashboard** credentials (see **Help (?)** in the app).

---

## **Building from Source**
If you want to build the `.exe` yourself:
```bash
pip install -r requirements.txt
pyinstaller --onefile --windowed --icon=spotikey.ico spotikey.py
