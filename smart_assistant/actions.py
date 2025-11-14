import os, time, webbrowser, subprocess
from tts import speak

# ------------------- WEBSITE ACTIONS ------------------- #
def open_website(url, name=None):
    """Open a website cleanly in the default browser (no CMD flash)."""
    site_name = name or url

    try:
        speak(f"Opening {site_name}.")
        # Opens in the default browser silently
        webbrowser.get().open_new_tab(url)
        time.sleep(0.5)
        speak(f"{site_name} is now open.")
    except Exception as e:
        print("[Website Error]", e)
        speak(f"Sorry, I couldn’t open {site_name}.")


def search_web(query):
    """Perform a Google search using the user's query."""
    query = query.replace("search for", "").replace("search", "").strip()

    if not query:
        speak("Please tell me what you want to search for.")
        return

    speak(f"Searching Google for {query}")
    webbrowser.open(f"https://www.google.com/search?q={query}")


# ------------------- FILE & APP HELPERS ------------------- #
def find_app_exe(app_name):
    """Try to find an .exe file containing the app name."""
    app_name = app_name.lower()
    search_dirs = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        os.path.expandvars(r"%LOCALAPPDATA%"),
        os.path.expandvars(r"%APPDATA%"),
    ]

    for base in search_dirs:
        for root, dirs, files in os.walk(base):
            for file in files:
                if file.lower().endswith(".exe") and app_name in file.lower():
                    return os.path.join(root, file)
    return None


# ------------------- APP OPENING ------------------- #
def open_app(app_name):
    """Open desktop, system, or Store applications by name (Windows)."""
    app_name = app_name.lower().strip()
    speak(f"Opening {app_name}.")

    # Normalize common names
    app_name = app_name.replace("vs code", "vscode").replace("visual studio code", "vscode")

    # Predefined apps
    app_paths = {
        "calculator": "calc.exe",
        "notepad": "notepad.exe",
        "paint": "mspaint.exe",
        "vscode": r"C:\Users\Ram Sathvik\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd",
        "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    }

    # Windows Settings URIs
    settings_links = {
        "settings": "ms-settings:",
        "wifi": "ms-settings:network-wifi",
        "bluetooth": "ms-settings:bluetooth",
        "display": "ms-settings:display",
        "sound": "ms-settings:sound",
        "privacy": "ms-settings:privacy",
        "update": "ms-settings:windowsupdate",
        "power": "ms-settings:powersleep",
        "apps": "ms-settings:appsfeatures"
    }

    try:
        # ✅ Handle Windows Settings (ms-settings)
        if app_name in settings_links:
            os.system(f"start {settings_links[app_name]}")
            speak(f"{app_name.capitalize()} settings opened successfully.")
            return

        # ✅ Handle WhatsApp (UWP app)
        if "whatsapp" in app_name:
            os.system("start shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App")
            speak("WhatsApp has been opened successfully.")
            return

        # ✅ Known app paths
        if app_name in app_paths:
            exe_path = app_paths[app_name]
            if os.path.exists(exe_path):
                subprocess.Popen(exe_path)
                speak(f"{app_name} has been opened successfully.")
                return
            else:
                speak(f"I found {app_name} in my list, but the file path seems missing.")
                return

        # ✅ Partial match (multi-word)
        for known in app_paths.keys():
            if known in app_name and os.path.exists(app_paths[known]):
                subprocess.Popen(app_paths[known])
                speak(f"{known} has been opened successfully.")
                return

        # ✅ Search system for .exe or Desktop items
        exe_path = find_app_exe(app_name) or find_on_desktop(app_name)
        if exe_path:
            os.startfile(exe_path)
            speak(f"I found {app_name} at {exe_path}. Opening it now.")
            return

        # ✅ Fallback open
        os.system(f'start "" "{app_name}"')
        speak(f"I tried opening {app_name}.")
    except Exception as e:
        print("[App Error]", e)
        speak(f"Could not open {app_name}. {e}")


# ------------------- SYSTEM ACTIONS ------------------- #
def system_action(action):
    """Perform basic system control actions."""
    action = action.lower()
    if action == "shutdown":
        speak("Shutting down your system. Goodbye.")
        os.system("shutdown /s /t 3")
    elif action == "restart":
        speak("Restarting your system.")
        os.system("shutdown /r /t 3")
    elif action == "lock":
        speak("Locking your computer now.")
        os.system("rundll32.exe user32.dll,LockWorkStation")
    else:
        speak("I’m not sure which system action you meant.")
