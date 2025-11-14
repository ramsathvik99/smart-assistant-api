import os
import re
import time
import json
import threading
import datetime
import requests
import pyautogui
import webbrowser
import wikipedia
import concurrent.futures
from deep_translator import GoogleTranslator
from PyDictionary import PyDictionary
from tts import speak
import urllib.parse 
import feedparser
import platform
from pathlib import Path
from config import CONFIG
import datetime
import winsound
import simpleaudio as sa
import base64
import io
from tts import speak

from memory_manager import (
    add_note_db, get_notes_with_ids_db,
    delete_note_db, clear_notes_db, update_note_db,
    pin_note_db, unpin_note_db, mark_note_done_db,
    search_notes_db, get_pinned_notes_db, get_done_notes_db
)

from tts import speak
import threading

try:
    import pyautogui  # Desktop screenshots
except:
    pyautogui = None

try:
    from plyer import screenshot as plyer_screenshot  # Mobile screenshots
except:
    plyer_screenshot = None

# ---------------------- 🕒 CORE SKILLS ---------------------- #

def tell_time():
    """Tell the current system time."""
    current_time = time.strftime("%I:%M %p")
    speak(f"The current time is {current_time}.")


def tell_date():
    """Tell the current date."""
    today = datetime.datetime.now().strftime("%A, %B %d, %Y")
    speak(f"Today is {today}.")



# ---------------------- 🔔 Alarm Sound (embedded WAV) ---------------------- #
def set_timer(text):
    """Simple timer that supports seconds, minutes, hours."""
    text = text.lower()

    # Extract values
    seconds = 0

    if "hour" in text:
        h = int(re.search(r"(\d+)\s*hour", text).group(1))
        seconds += h * 3600

    if "minute" in text:
        m = int(re.search(r"(\d+)\s*minute", text).group(1))
        seconds += m * 60

    if "second" in text:
        s = int(re.search(r"(\d+)\s*second", text).group(1))
        seconds += s

    if seconds <= 0:
        speak("I couldn't understand the timer duration.")
        return

    speak("Timer set.")

    def alert():
        winsound.Beep(1800, 700)   # simple sound
        speak("Your timer is done.")

    threading.Timer(seconds, alert).start()


# ---------------------- HELPERS ---------------------- #
def natural_time_to_seconds(text):
    """Extracts seconds/minutes/hours from user speech."""
    text = text.lower()
    seconds = 0

    h = re.search(r"(\d+)\s*hour", text)
    m = re.search(r"(\d+)\s*minute", text)
    s = re.search(r"(\d+)\s*second", text)

    if h: seconds += int(h.group(1)) * 3600
    if m: seconds += int(m.group(1)) * 60
    if s: seconds += int(s.group(1))

    return seconds


def alarm_beep():
    """Soft alarm sound."""
    winsound.Beep(1800, 800)
    winsound.Beep(1800, 800)
    winsound.Beep(1800, 800)


# ---------------------- ALARM ---------------------- #
def set_alarm(text):
    text = text.lower().strip()

    # --- CASE 1: Natural language duration (10 seconds, 2 minutes) ---
    duration = natural_time_to_seconds(text)
    if duration > 0:
        speak(f"Alarm set for {duration} seconds from now.")
        threading.Timer(duration, lambda: (alarm_beep(), speak("Your alarm is ringing!"))).start()
        return

    # --- CASE 2: Clock time alarm (7:30 AM) ---
    match = re.match(r"(\d{1,2}):(\d{2})(\s*[ap]m)?", text)
    if not match:
        speak("I didn't understand the alarm time.")
        return

    hour = int(match.group(1))
    minute = int(match.group(2))
    ampm = match.group(3)

    # Handle AM/PM
    if ampm:
        ampm = ampm.strip()
        if "pm" in ampm and hour != 12: hour += 12
        if "am" in ampm and hour == 12: hour = 0

    now = datetime.datetime.now()
    alarm = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if alarm < now:
        alarm += datetime.timedelta(days=1)

    delay = (alarm - now).total_seconds()

    speak(f"Alarm set for {alarm.strftime('%I:%M %p')}.")
    threading.Timer(delay, lambda: (alarm_beep(), speak("Wake up! Your alarm is ringing!"))).start()


#--------------Math Solver------------------#
def solve_math(text):
    try:
        text = text.lower()

        # Remove unnecessary words
        for w in ["what is", "calculate", "equals", "the result of", "result of", "answer"]:
            text = text.replace(w, "")

        # Convert words to symbols
        text = text.replace("plus", "+")
        text = text.replace("add", "+")
        text = text.replace("minus", "-")
        text = text.replace("subtract", "-")
        text = text.replace("times", "*")
        text = text.replace("multiplied by", "*")
        text = text.replace("multiply", "*")
        text = text.replace("divide", "/")
        text = text.replace("divided by", "/")
        text = text.replace("by", "*")  # "10 by 2"

        # Convert x or × to *
        text = re.sub(r'(?<=\d)\s*[xX×]\s*(?=\d)', '*', text)

        # Keep only valid math characters
        expr = re.sub(r'[^0-9+\-*/(). ]', '', text).strip()

        # If nothing to solve
        if not expr:
            speak("Sorry, I couldn't calculate that.")
            return None

        result = eval(expr)
        speak(f"The result is {result}.")
        return result

    except Exception as e:
        print("[Math Error]", e)
        speak("Sorry, I couldn’t calculate that.")
        return None


#---------------------- 🔄 currency & unit conversion ---------------------- #
def convert_currency(amount, src, dest):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{src.upper()}"
        data = requests.get(url, timeout=5).json()

        rate = data["rates"].get(dest.upper())
        if not rate:
            speak("I couldn't find the currency you mentioned.")
            return

        result = round(amount * rate, 2)
        speak(f"{amount} {src.upper()} equals {result} {dest.upper()}.")
    except:
        speak("Currency conversion failed.")


def convert_units(value, unit_from, unit_to):
    unit_from = unit_from.lower().rstrip("s")
    unit_to = unit_to.lower().rstrip("s")

    # Normalize British spellings
    unit_from = unit_from.replace("metre", "meter")
    unit_to = unit_to.replace("metre", "meter")

    unit_from = unit_from.replace("kilometre", "km")
    unit_to = unit_to.replace("kilometre", "km")

    unit_from = unit_from.replace("kilometer", "km")
    unit_to = unit_to.replace("kilometer", "km")

    unit_from = unit_from.replace("meter", "m")
    unit_to = unit_to.replace("meter", "m")

    unit_from = unit_from.replace("centimeter", "cm")
    unit_to = unit_to.replace("centimeter", "cm")

    unit_from = unit_from.replace("millimeter", "mm")
    unit_to = unit_to.replace("millimeter", "mm")


    # Normalize plurals
    if unit_from.endswith("s"): unit_from = unit_from[:-1]
    if unit_to.endswith("s"): unit_to = unit_to[:-1]

    # Master conversion table (base units)
    unit_map = {
        # Length
        "km": 1000, 
        "m": 1,
        "cm": 0.01,
        "mm": 0.001,
        "inch": 0.0254,
        "ft": 0.3048,
        "yard": 0.9144,
        "mile": 1609.34,

        # Weight
        "kg": 1,
        "g": 0.001,
        "mg": 0.000001,
        "lb": 0.453592,
        "oz": 0.0283495,

        # Volume
        "liter": 1,
        "cup": 0.236588,
        "ml": 0.001,

        # Temperature handled separately
    }

    # Temperature conversion
    if unit_from in ["c", "celsius"] and unit_to in ["f", "fahrenheit"]:
        result = round((value * 9/5) + 32, 2)
        speak(f"{value}°C equals {result}°F.")
        return

    if unit_from in ["f", "fahrenheit"] and unit_to in ["c", "celsius"]:
        result = round((value - 32) * 5/9, 2)
        speak(f"{value}°F equals {result}°C.")
        return

    # Standard conversion
    if unit_from not in unit_map or unit_to not in unit_map:
        speak("Sorry, I cannot convert those units yet.")
        return

    # Convert to base, then to target
    base_value = value * unit_map[unit_from]
    result = round(base_value / unit_map[unit_to], 4)

    speak(f"{value} {unit_from} equals {result} {unit_to}.")


# ---------------------- 💻 SYSTEM UTILITIES ---------------------- #
def get_device_screenshot_folder():
    system = platform.system()

    # WINDOWS default screenshot folder
    if system == "Windows":
        win_path = Path.home() / "Pictures" / "Screenshots"
        if win_path.exists():
            return win_path
        return Path.home() / "Pictures"

    # MAC screenshots saved on Desktop
    elif system == "Darwin":
        return Path.home() / "Desktop"

    # LINUX screenshots normally in Pictures
    elif system == "Linux":
        pics = Path.home() / "Pictures" / "Screenshots"
        return pics if pics.exists() else Path.home() / "Pictures"

    # ANDROID screenshot folder
    elif ("ANDROID_ARGUMENT" in os.environ) or ("android" in platform.platform().lower()):
        android_path = Path("/sdcard/Pictures/Screenshots")
        if android_path.exists():
            return android_path
        return Path("/sdcard/DCIM/Screenshots")

    # UNKNOWN DEVICE fallback
    return Path.cwd() / "Screenshots"

#---------------------- SCREENSHOT ---------------------- #
def take_screenshot():
    folder = get_device_screenshot_folder()
    folder.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"screenshot_{timestamp}.png"
    filepath = folder / filename

    try:
        # DESKTOP
        if pyautogui:
            img = pyautogui.screenshot()
            img.save(str(filepath))

        # MOBILE
        elif plyer_screenshot:
            plyer_screenshot(filename=str(filepath))

        else:
            speak("Screenshot not supported on this device.")
            return False

        speak(f"Screenshot saved in your device's screenshot folder as {filename}.")
        print(f"[SAVED] {filepath}")
        return True

    except Exception as e:
        speak("Sorry, I couldn't take the screenshot.")
        print("[Screenshot Error]", e)
        return False
    

def lock_system():
    """Lock the Windows system."""
    speak("Locking the system now.")
    os.system("rundll32.exe user32.dll,LockWorkStation")


# ---------------------- 🌦️ WEB & INFO SKILLS ---------------------- #
def get_weather(location):
    """Fetch live weather for any Indian city or state using OpenWeather API."""
    api_key = "d29b7232620736a06c781aaea43a14c5" 

    if not api_key or api_key == "YOUR_OPENWEATHER_API_KEY":
        speak("Weather service is not configured. Please set your API key.")
        return

    # 🔹 Known Indian states with representative coordinates
    STATES = {
        "andhra pradesh": (15.9129, 79.74), "ap": (15.9129, 79.74),
        "telangana": (17.1232, 79.2088), "ts": (17.1232, 79.2088),
        "tamil nadu": (11.1271, 78.6569), "karnataka": (15.3173, 75.7139),
        "maharashtra": (19.7515, 75.7139), "kerala": (10.8505, 76.2711),
        "gujarat": (22.2587, 71.1924), "west bengal": (22.9868, 87.8550),
        "uttar pradesh": (26.8467, 80.9462), "rajasthan": (27.0238, 74.2179),
        "bihar": (25.0961, 85.3131), "punjab": (31.1471, 75.3412),
        "haryana": (29.0588, 76.0856), "madhya pradesh": (22.9734, 78.6569),
        "odisha": (20.9517, 85.0985), "jharkhand": (23.6102, 85.2799),
        "assam": (26.2006, 92.9376), "chhattisgarh": (21.2787, 81.8661),
        "himachal pradesh": (31.1048, 77.1734), "delhi": (28.6139, 77.2090),
        "jammu and kashmir": (33.7782, 76.5762),
    }

    location = location.strip().lower()
    if not location:
        speak("Please tell me a city or state name.")
        return

    try:
        # 🗺️ Determine whether the input is a state or a city
        if location in STATES:
            lat, lon = STATES[location]
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
            place = location.title()
        else:
            place = location.title()
            url = f"https://api.openweathermap.org/data/2.5/weather?q={place},IN&appid={api_key}&units=metric"

        # 🌐 Fetch live data
        response = requests.get(url, timeout=10).json()

        if response.get("cod") != 200:
            speak(f"I couldn't find the weather for {place}. Please try another location.")
            return

        # 🌡️ Extract useful info
        temp = response["main"].get("temp")
        feels_like = response["main"].get("feels_like")
        desc = response["weather"][0].get("description", "").capitalize()
        humidity = response["main"].get("humidity")

        # 🗣️ Speak the result
        speak(
            f"The weather in {place} is {desc}. "
            f"The temperature is {temp} degrees Celsius, feels like {feels_like}. "
            f"The humidity is {humidity} percent."
        )

    except requests.Timeout:
        speak("The weather service is taking too long to respond. Please try again later.")
    except Exception as e:
        print("[Weather Error]", e)
        speak("Sorry, I couldn't fetch the weather right now.")


#----------------------- News Fetcher ---------------------- #
def get_news(location=None):
    # Clean and prepare location
    if location:
        location = re.sub(r"[^a-zA-Z\s]", "", location).strip()
    else:
        location = "India"  # default

    # ✅ Encode spaces (e.g., "Andhra Pradesh" -> "Andhra%20Pradesh")
    query = urllib.parse.quote_plus(location)

    # 📰 Google News RSS URL (with encoded query)
    rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

    speak(f"Fetching the latest news for {location}...")
    try:
        # Parse the RSS feed
        feed = feedparser.parse(rss_url)

        if not feed.entries:
            speak(f"Sorry, I couldn’t find any current news for {location}.")
            return

        speak(f"Here are the top headlines for {location}:")
        for i, entry in enumerate(feed.entries[:5], start=1):
            headline = entry.title
            speak(f"Headline {i}: {headline}")
            time.sleep(0.4)

    except Exception as e:
        print("[News Error]", e)
        speak("Sorry, I couldn’t fetch the news right now.")

# ---------------------- AI QUERYING ---------------------- #
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

def ask_ai(query):

    # ---------------------- GROQ (Primary) ---------------------- #
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }

        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Nova, a smart assistant. "
                        "Always give short, clear answers. "
                        "Limit answers to MAXIMUM 2 sentences. "
                        "No long paragraphs. No deep history unless asked."
                    )
                },
                {"role": "user", "content": query}
            ],
            "max_tokens": 70,
            "temperature": 0.4
        }

        r = requests.post(url, json=payload, headers=headers, timeout=10)

        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()

        print("⚠ GROQ Error:", r.text)

    except Exception as e:
        print("❌ GROQ Failed:", e)

    # ---------------------- DEEPSEEK (Backup) ---------------------- #
    try:
        url = "https://api.deepseek.com/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Give short, direct answers. "
                        "Maximum 2 sentences only."
                    )
                },
                {"role": "user", "content": query}
            ],
            "max_tokens": 70,
            "temperature": 0.4
        }

        r = requests.post(url, json=payload, headers=headers, timeout=10)

        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()

        print("⚠ DEEPSEEK Error:", r.text)

    except Exception as e:
        print("❌ DEEPSEEK Failed:", e)


    # ---------------------- DUCKDUCKGO (Last fallback) ---------------------- #
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1
        }

        r = requests.get(url, params=params, timeout=5)
        data = r.json()

        if data.get("AbstractText"):
            return data["AbstractText"]

        topics = data.get("RelatedTopics", [])
        for t in topics:
            if isinstance(t, dict) and "Text" in t:
                return t["Text"]

    except Exception as e:
        print("⚠ DuckDuckGo Error:", e)

    return "I couldn't find a short answer for that."


# ---------------------- 🌐 TRANSLATION & DICTIONARY ---------------------- #
def translate_text(text, dest_lang=None):
    """Translate text into the specified language and speak appropriately."""
    try:
        # Normalize and parse
        command = text.lower().strip().replace("translate", "").strip()
        parts = command.split(" to ")

        if len(parts) == 2:
            phrase = parts[0].strip()
            lang_name = parts[1].strip().lower()
        else:
            phrase = command.strip()
            lang_name = "french"  # default fallback

        # ✅ Language mapping
        lang_map = {
            "french": "fr", "spanish": "es", "hindi": "hi", "telugu": "te",
            "tamil": "ta", "german": "de", "italian": "it", "japanese": "ja",
            "chinese": "zh-cn", "korean": "ko", "russian": "ru", "arabic": "ar",
            "english": "en", "bengali": "bn", "marathi": "mr", "urdu": "ur",
            "gujarati": "gu", "punjabi": "pa", "malayalam": "ml"
        }

        # Match full or short language names
        match = None
        for name in lang_map:
            if lang_name.startswith(name):
                match = name
                break

        if not match and len(lang_name) <= 3:
            for name, code in lang_map.items():
                if lang_name in [code, name[:2]]:
                    match = name
                    break

        if not match:
            speak("I didn’t recognize that language. Please try again.")
            return

        lang_code = lang_map[match]
        full_lang = match.capitalize()

        # 🧠 Perform translation using Deep Translator
        translated_text = GoogleTranslator(source='auto', target=lang_code).translate(phrase)

        # 🗣️ Speak result
        speak(f"In {full_lang}, '{phrase}' means:", lang_hint='en')
        speak(translated_text, lang_hint=lang_code)

        return translated_text

    except Exception as e:
        print(f"[Translate Error]: {e}")
        speak("Sorry, I couldn’t translate that right now.")
        return None

#---------------------- DICTIONARY ---------------------- #
def define_word(word):
    """Fetch and speak the definition of a word using Free Dictionary API."""
    # 🧹 Clean up the word
    word = word.lower().strip()
    word = re.sub(r'\b(what|is|the|meaning|of|a|an|define)\b', '', word).strip()

    if not word:
        speak("Please tell me which word you'd like me to define.")
        return

    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url, timeout=8)

        if response.status_code != 200:
            speak(f"Sorry, I couldn't find a definition for {word}.")
            return

        data = response.json()

        # ✅ Extract the first valid meaning
        meaning = data[0]["meanings"][0]
        part_of_speech = meaning.get("partOfSpeech", "word")
        definition = meaning["definitions"][0].get("definition", "No definition found")

        speak(f"The meaning of {word} as a {part_of_speech} is: {definition}")

        # 🗣 Optional example usage
        example = meaning["definitions"][0].get("example")
        if example:
            speak(f"For example, {example}")

    except Exception as e:
        print("[Define Error]", e)
        speak("Sorry, I couldn’t fetch the meaning right now.")


# ---------------------- 📝 ADVANCED NOTES (PostgreSQL) ---------------------- #

from memory_manager import (
    add_note_db, get_notes_with_ids_db,
    delete_note_db, clear_notes_db, update_note_db
)

def add_note(text):
    user_id = CONFIG["CURRENT_USER_ID"]
    if not text.strip():
        speak("Tell me what to write down.")
        return

    add_note_db(user_id, text)
    speak("Note saved.")


def read_notes():
    user_id = CONFIG["CURRENT_USER_ID"]
    notes = get_notes_with_ids_db(user_id)

    if not notes:
        speak("You do not have any notes yet.")
        return

    speak("Here are your notes:")
    for i, row in enumerate(notes, start=1):
        speak(f"Note {i}: {row['note']}")


def delete_note(number):
    user_id = CONFIG["CURRENT_USER_ID"]
    notes = get_notes_with_ids_db(user_id)

    if number <= 0 or number > len(notes):
        speak("That note number doesn't exist.")
        return

    note_id = notes[number - 1]["id"]
    delete_note_db(user_id, note_id)
    speak("Note deleted.")


def delete_note_by_text(keyword):
    user_id = CONFIG["CURRENT_USER_ID"]
    notes = get_notes_with_ids_db(user_id)

    keyword = keyword.lower()
    for row in notes:
        if keyword in row["note"].lower():
            delete_note_db(user_id, row["id"])
            speak("I deleted that note.")
            return

    speak("I couldn't find any note matching that.")


def update_note(number, new_text):
    user_id = CONFIG["CURRENT_USER_ID"]
    notes = get_notes_with_ids_db(user_id)

    if number <= 0 or number > len(notes):
        speak("That note number doesn't exist.")
        return

    note_id = notes[number - 1]["id"]
    update_note_db(user_id, note_id, new_text)
    speak("Note updated.")


def clear_all_notes():
    user_id = CONFIG["CURRENT_USER_ID"]
    clear_notes_db(user_id)
    speak("All notes cleared.")

def pin_note(number):
    user_id = CONFIG["CURRENT_USER_ID"]
    notes = get_notes_with_ids_db(user_id)

    if number <= 0 or number > len(notes):
        speak("That note number doesn't exist.")
        return

    note_id = notes[number - 1]["id"]
    pin_note_db(user_id, note_id)
    speak("I pinned that note.")

def unpin_note(number):
    user_id = CONFIG["CURRENT_USER_ID"]
    notes = get_notes_with_ids_db(user_id)

    if number <= 0 or number > len(notes):
        speak("That note number doesn't exist.")
        return

    note_id = notes[number - 1]["id"]
    unpin_note_db(user_id, note_id)
    speak("I unpinned that note.")

def mark_note_done(number):
    user_id = CONFIG["CURRENT_USER_ID"]
    notes = get_notes_with_ids_db(user_id)

    if number <= 0 or number > len(notes):
        speak("That note number doesn't exist.")
        return
    
    note_id = notes[number - 1]["id"]
    mark_note_done_db(user_id, note_id)
    speak("Marked that note as done.")

def search_notes(keyword):
    user_id = CONFIG["CURRENT_USER_ID"]
    results = search_notes_db(user_id, keyword)

    if not results:
        speak(f"No notes found containing {keyword}.")
        return

    speak(f"I found {len(results)} notes containing {keyword}:")
    for idx, row in enumerate(results, start=1):
        speak(f"Match {idx}: {row['note']}")

def show_pinned_notes():
    user_id = CONFIG["CURRENT_USER_ID"]
    notes = get_pinned_notes_db(user_id)

    if not notes:
        speak("You have no pinned notes.")
        return

    speak("Here are your pinned notes:")
    for i, row in enumerate(notes, start=1):
        speak(f"Pinned {i}: {row['note']}")

def show_done_notes():
    user_id = CONFIG["CURRENT_USER_ID"]
    notes = get_done_notes_db(user_id)

    if not notes:
        speak("You have no completed notes.")
        return

    speak("Here are your completed notes:")
    for i, row in enumerate(notes, start=1):
        speak(f"Done {i}: {row['note']}")

# ---------------------- ⏰ REMINDERS ---------------------- #

def set_reminder(task, minutes):
    speak(f"Okay, I will remind you to {task} in {minutes} minutes.")
    timer = threading.Timer(minutes * 60, lambda: speak(f"Reminder: {task}"))
    timer.start()


# ----------------------Music---------------------------#
from youtubesearchpython import VideosSearch
import webbrowser

def play_music(query):
    search = VideosSearch(query, limit=1)
    result = search.result()

    if not result["result"]:
        speak("I couldn't find that song.")
        return

    url = result["result"][0]["link"]
    speak(f"Playing {query} on YouTube.")
    webbrowser.open(url)
