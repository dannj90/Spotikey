# Spotikey 🎵

Spotikey is a lightweight Windows app that allows you to quickly "like" the currently playing Spotify track using a customisable global hotkey.  
It also features a system tray icon, notifications, and an integrated Spotify authorisation process.

---

## **Features**

1. Global Hotkey for Liking Songs
   
  - Default Ctrl + Alt + L hotkey to "Like" the currently playing track on Spotify.
  - Fully customisable hotkey in the app settings.

2. Spotify Integration
   
  - OAuth2 authentication with Spotify Developer API.
  - Automatic token refresh to keep the session active.
  - One-click “Authorise” window to enter Client ID and Secret.
  - Built-in Help screen explaining how to set up the Spotify Developer App.

3. Notifications
   
  - Windows toast notifications when a song is liked or if an error occurs.
  - Option to enable or disable notifications in settings.

4. System Tray Integration
   
  - Spotikey runs silently in the Windows system tray.
  - Right-click tray menu with:
        - Open Spotikey
        - Check for Updates
        - Exit

5. Update Checker
   
  - Automatic version check on startup via GitHub API.
  - “Check for Updates” button in settings and tray menu.
  - Visual version indicator if a newer version is available (click to download).

6. Settings & Customization
   
  - Change hotkeys directly in the app.
  - Enable/disable notifications.
  - Run on Startup option (adds/removes Windows Startup shortcut).
  - One-click “Save Settings” with confirmation message.

7. Logging & Debugging
   
  - Real-time log display in the main window (scrollable).
  - Persistent log file saved to %APPDATA%\Spotikey\spotikey.log.
  - One-click “Clear Log” button.

8. User Interface
   
  - Modern dark UI styled after Spotify (black background, green accents).
  - Spotikey logo displayed in the main window.
  - Version number displayed under the logo.
  - “?” Help button opens a step-by-step guide for setup.

9. First-Time Setup Guidance
    
  - Friendly message on first run:
      - “Welcome to Spotikey! Please Authorise your Spotify account. Use the ‘?’ button for instructions.”

10. Lightweight & Portable
    
  - Single .exe build (~30MB) – no installation required.
  - Low resource usage when minimized to tray.

---

## **Requirements**
- **Windows 10/11**
- **Spotify Premium account** (to use the Web API)
- **Python 3.9+** (for development) or the **standalone .exe** (for end users)

---

## **Installation**
1. Download the latest release `.exe` from the [Releases page](https://github.com/dannj90/Spotikey/releases).
2. Run `Spotikey.exe`.
3. Authorise the app with your **Spotify Developer Dashboard** credentials (see **Help (?)** in the app).

---
    
PLEASE NOTE - THIS IS MY FIRST EVER APP AND RELEASE, THEREFORE THIS APP IS NOT DIGITALLY SIGNED YET

---

## **Building from Source**
If you want to build the `.exe` yourself:
```bash
pip install -r requirements.txt
pyinstaller --onefile --windowed --icon=spotikey.ico spotikey.py
