import time
import requests
from config import CONFIG
from tts import speak

# import memory functions
from memory_manager import (
    update_user_memory,
    delete_memory_key,
    load_user_memory
)

def get_random_joke():
    try:
        url = "https://v2.jokeapi.dev/joke/Any"
        data = requests.get(url, timeout=6).json()

        if data.get("type") == "single":
            return data["joke"]
        else:
            return f"{data.get('setup')} ... {data.get('delivery')}"

    except Exception:
        return "Sorry, I couldn’t fetch a joke right now."


def chat_reply(text):
    """Handles small talk, memory commands, clarifications"""
    user_id = CONFIG["CURRENT_USER_ID"]
    text_l = text.lower().strip()

    # ---------------- MEMORY: REMEMBER ----------------
    if text_l.startswith("remember"):
        fact = text_l.replace("remember", "").strip()
        if not fact:
            speak("What should I remember?")
            return True

        key = fact.split()[0]
        update_user_memory(user_id, key, fact)
        speak(f"Okay, I will remember that {fact}.")
        return True

    # ---------------- MEMORY: FORGET ------------------
    if text_l.startswith("forget"):
        key = text_l.replace("forget", "").strip()
        if not key:
            speak("What should I forget?")
            return True
        
        delete_memory_key(user_id, key)
        speak(f"Okay, I forgot {key}.")
        return True

    # ---------------- MEMORY: RECALL -------------------
    if "what do you remember" in text_l or "what did i say" in text_l:
        mem = load_user_memory(user_id)

        if not mem:
            speak("I don't have anything in memory yet.")
        else:
            speak("Here’s what I remember:")
            for value in mem.values():
                speak(value)
        return True


    # ----------- CLARIFICATION / REPEAT REQUESTS (SAFE VERSION) ------------- #

    clarification_exact = [
        "wait",
        "what?",
        "what",
        "repeat",
        "say again",
        "i don't understand",
        "i didnt understand",
        "can you repeat",
        "what did you say",
        "huh",
        "pardon"
    ]

    # triggers ONLY when user says these phrases ALONE (or very close)
    if text_l in clarification_exact:
        last = CONFIG.get("LAST_ASSISTANT_MSG")
        if last:
            speak(last)
        else:
            speak("I haven’t said anything recently to repeat.")
        return True

    # allow short forms WITH trailing punctuation
    if text_l.rstrip("?.!") in clarification_exact:
        last = CONFIG.get("LAST_ASSISTANT_MSG")
        if last:
            speak(last)
        else:
            speak("I haven’t said anything recently to repeat.")
        return True

    # ---------------- SMALL TALK -----------------------
    if "how are you" in text_l:
        speak("I’m doing great, thanks for asking!")
        return True

    if "what is your name" in text_l:
        speak(f"My name is Neural Omnie Virtual Assistant. or you can call me {CONFIG['ASSISTANT_NAME']} in short.")
        return True

    if "who created you" in text_l:
        speak("I was created by Ram Sathvik.")
        return True

    if "thank" in text_l:
        speak("You're welcome!")
        return True

    if "joke" in text_l:
        speak(get_random_joke())
        return True

    # ---------------- HUMAN-LIKE SMALL TALK -----------------------
    if "how was your day" in text_l:
        speak("My day has been great! Talking with you always makes it better.")
        return True

    if "what are you doing" in text_l:
        speak("Just hanging out here, ready to help you anytime!")
        return True

    if "are you there" in text_l:
        speak("Yep, I’m right here. What’s up?")
        return True

    if "do you like me" in text_l:
        speak("Of course! I enjoy talking with you.")
        return True

    if "i am bored" in text_l:
        speak("Want to hear a joke or try something fun?")
        return True

    if "i am sad" in text_l or "i feel sad" in text_l:
        speak("I'm here for you. Want to talk about it, or should I cheer you up?")
        return True

    if "tell me something" in text_l:
        speak("Did you know? Your brain processes information faster than any computer!")
        return True

    if "are you smart" in text_l:
        speak("I try my best! But you’re the real boss here.")
        return True

    if "do you sleep" in text_l:
        speak("Nope, I don’t sleep. I wait for you like a loyal digital friend.")
        return True

    if "i love you" in text_l:
        speak("Aww, that’s sweet! I care about you too.")
        return True

    if "good morning" in text_l:
        speak("Good morning! I hope your day starts amazingly well.")
        return True

    if "good night" in text_l:
        speak("Good night! Rest well and take care.")
        return True

    if "are you hungry" in text_l:
        speak("I don’t eat, but I love the idea of food!")
        return True

    if "what is your purpose" in text_l:
        speak("My purpose is to help you, learn from you, and make your tasks easier.")
        return True

    return False
