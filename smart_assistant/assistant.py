import re
from config import CONFIG
from sst import listen
from tts import speak

from chatbrain import generate_reply
from responses import chat_reply

from memory_manager import (
    get_or_create_user,
    add_history,
    get_chat_history,
)

from actions import open_website, open_app, system_action, search_web

from skills import (
    tell_time, tell_date, solve_math, take_screenshot, lock_system,
    get_weather, get_news, translate_text, define_word,
    add_note, read_notes, set_reminder,
    delete_note, delete_note_by_text, clear_all_notes, update_note,
    pin_note, unpin_note, mark_note_done,
    search_notes, show_pinned_notes, show_done_notes,
    set_timer, set_alarm,
    convert_currency, convert_units,
    play_music,ask_ai
)


# ======================================================
# COMMAND HANDLER
# ======================================================
def parse_and_execute(text):
    text = text.lower().strip()

    # ---------------- APPS / WEBSITES ----------------
    if "open youtube" in text:
        open_website("https://youtube.com", "YouTube")
        return True

    if "open google" in text:
        open_website("https://google.com", "Google")
        return True

    if text.startswith("open ") and "folder" not in text:
        name = text.replace("open app", "").replace("open", "").strip()
        if not name:
            speak("Please tell me which app to open.")
            return True
        open_app(name)
        return True

    # ---------------- SYSTEM ----------------
    if "shutdown" in text:
        system_action("shutdown"); return True
    if "restart" in text:
        system_action("restart"); return True
    if "lock" in text:
        system_action("lock"); return True

    # ---------------- SCREENSHOT ----------------
    if "screenshot" in text or "screen shot" in text:
        take_screenshot(); return True

    # ---------------- WEATHER ----------------
    if "weather" in text:
        city = text
        for p in [
            "what is the weather in", "weather in", "weather at",
            "weather for", "what's the weather in"
        ]:
            city = city.replace(p, "")
        city = city.strip()
        if not city:
            speak("Tell me a location.")
            return True
        get_weather(city)
        return True

    # ---------------- NEWS ----------------
    if "news" in text:
        cleaned = text
        for p in [
            "tell me the", "what is the", "latest", "breaking", "show me",
            "today's", "headlines", "news in", "news from", "news about"
        ]:
            cleaned = cleaned.replace(p, "")

        location = cleaned.replace("news", "").strip()
        if not location:
            location = "India"
        get_news(location); return True

    # ---------------- DICTIONARY ----------------
    if "meaning of" in text or "define" in text:
        word = (
            text.replace("meaning of", "")
            .replace("define", "")
            .strip()
        )
        if not word:
            speak("Tell me a word to define.")
        else:
            define_word(word)
        return True

    # ---------------- TRANSLATE ----------------
    if "translate" in text:
        translate_text(text)
        return True

    # ---------------- NOTES ----------------
    if "add note" in text or "write note" in text:
        note = text.replace("add note", "").replace("write note", "").strip()
        add_note(note); return True

    if "read notes" in text or "show notes" in text:
        read_notes(); return True

    if "delete note" in text:
        num = re.search(r"\d+", text)
        if num:
            delete_note(int(num.group()))
        else:
            keyword = text.replace("delete note", "").strip()
            delete_note_by_text(keyword)
        return True

    if "clear all notes" in text:
        clear_all_notes(); return True

    if "update note" in text:
        m = re.search(r"update note (\d+) to (.+)", text)
        if m:
            update_note(int(m.group(1)), m.group(2))
        else:
            speak("Say: update note 2 to buy milk.")
        return True

    # ----- pin / unpin -----
    if "pin note" in text:
        n = re.search(r"\d+", text)
        if n: pin_note(int(n.group()))
        return True

    if "unpin note" in text:
        n = re.search(r"\d+", text)
        if n: unpin_note(int(n.group()))
        return True

    # ----- mark done -----
    if "mark note" in text and "done" in text:
        n = re.search(r"\d+", text)
        if n: mark_note_done(int(n.group()))
        return True

    # ----- search notes -----
    if "search notes for" in text:
        word = text.replace("search notes for", "").strip()
        search_notes(word); return True

    # ----- show pinned / completed -----
    if "show pinned notes" in text:
        show_pinned_notes(); return True

    if "show completed notes" in text or "show done notes" in text:
        show_done_notes(); return True

    # ---------------- REMINDERS ----------------
    if text.startswith("remind me"):
        m = re.search(r"remind me to (.+) in (\d+) minutes", text)
        if m:
            set_reminder(m.group(1), int(m.group(2)))
        else:
            speak("Say: remind me to call mom in 5 minutes.")
        return True

    # ---------------- TIMERS ----------------
    if "timer" in text:
        set_timer(text)   # pass full text instead of number
        return True


    # ---------------- ALARMS ----------------
    if "alarm" in text:
        set_alarm(text)   # pass full text
        return True

    # ---------------- UNIT CONVERSION ----------------
    if "convert" in text and all(sym not in text for sym in ["$", "₹", "rs", "usd", "inr", "dollar", "rupee"]):
        m = re.search(r"convert (\d+(?:\.\d+)?) (\w+) to (\w+)", text)
        if m:
            convert_units(float(m.group(1)), m.group(2), m.group(3))
            return True

    # ---------------- CURRENCY ----------------
    if "convert" in text and " to " in text:
        t = text.lower()

        # Normalize currency keywords
        t = t.replace("dollars", "usd")
        t = t.replace("dollar", "usd")
        t = t.replace("$", "usd ")

        t = t.replace("rupees", "inr")
        t = t.replace("rupee", "inr")
        t = t.replace("rs", "inr ")
        t = t.replace("₹", "inr ")

        # Pattern 1: convert 100 usd to inr
        m = re.search(r"convert\s+(\d+(?:\.\d+)?)\s+(\w+)\s+to\s+(\w+)", t)

        # Pattern 2: convert usd 100 to inr   (like $1 becomes usd 1)
        if not m:
            m = re.search(r"convert\s+(\w+)\s+(\d+(?:\.\d+)?)\s+to\s+(\w+)", t)

        if m:
            # Figure out which part is number and which is currency
            a, b, c = m.group(1), m.group(2), m.group(3)

            if a.replace(".", "").isdigit():
                amount = float(a)
                src = b
            else:
                amount = float(b)
                src = a

            dest = c

            convert_currency(amount, src, dest)
            return True

    # ---------------- PLAY MUSIC ----------------
    if text.startswith("play "):
        play_music(text.replace("play", "").strip())
        return True

    # ---------------- MATH ----------------
    if any(op in text for op in ["+", "-", "*", "/", "plus", "minus", "times", "divide","x", "×", "by"]):
        solve_math(text); return True

    # ---------------- TIME & DATE ----------------
    if "time" in text:
        tell_time(); return True

    if "date" in text or "today" in text:
        tell_date(); return True

    # ---------------- SEARCH ----------------
    if text.startswith("search"):
        search_web(text); return True
  
    return False


# ======================================================
# MAIN
# ======================================================
def main():
    speak("Hello! Please enter your username.")

    username = input("Enter Username: ").strip()
    while not username:
        username = input("Enter Username: ").strip()

    # Ask for password in a loop until the correct one is entered
    while True:
        speak("Now please enter your password.")
        password = input("Enter Password: ").strip()
        while not password:
            password = input("Enter Password: ").strip()

        user_id, status = get_or_create_user(username, password)

        if status == "WRONG_PASSWORD":
            speak("Incorrect password. Please try again.")
        else:
            break   # Correct password → exit loop

    # Assign the authenticated user ID
    CONFIG["CURRENT_USER_ID"] = user_id

    if status == "NEW_USER":
        speak(f"Welcome {username}! Your account has been created.")
    else:
        speak(f"Welcome back {username}!")

    speak("How can I help you today?")


    while True:
        try:
            user_text = listen()
        except Exception as e:
            print("[Listening Error]", e)
            speak("Sorry, I didn't catch that.")
            continue

        if not user_text:
            continue

        if any(e in user_text.lower() for e in ["exit", "quit", "stop", "bye"]):
            speak("Goodbye! Have a great day!")
            break
        add_history(user_id, "user", user_text)

        # Try commands
        if parse_and_execute(user_text):
            continue

        # Small talk
        handled_st = chat_reply(user_text)
        if handled_st:
            add_history(user_id, "assistant", "(memory/smalltalk)")
            continue

        # AI fallback AFTER small talk
        reply = ask_ai(user_text)
        if reply:
            speak(reply)
            continue

        # AI fallback
        chats = get_chat_history(user_id)
        reply = generate_reply(user_text, chats)
        speak(reply)

        CONFIG["LAST_ASSISTANT_MSG"] = reply
        add_history(user_id, "assistant", reply)


if __name__ == "__main__":
    main()
