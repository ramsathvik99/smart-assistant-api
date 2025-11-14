import os
import time
import pyttsx3
import tempfile
from gtts import gTTS
from playsound import playsound
from config import CONFIG


# ----------------------------
# English TTS (pyttsx3)
# ----------------------------
def tts_pyttsx3(text):
    """Casual, human-like voice tuning."""
    if not text or not text.strip():
        return

    try:
        engine = pyttsx3.init()

        # 🔹 Choose best casual-sounding voice (female preferred)
        voices = engine.getProperty("voices")
        selected = voices[0].id

        for v in voices:
            lname = v.name.lower()
            if "zira" in lname or "female" in lname or "eva" in lname:
                selected = v.id
                break

        engine.setProperty("voice", selected)

        # 🔹 Casual human speaking speed (perfect balance)
        engine.setProperty("rate", 150)

        # 🔹 Comfortable relaxed volume
        engine.setProperty("volume", 1.0)

        # 🔹 Add light natural pauses (helps natural flow)
        text = text.replace(",", ", ...")
        text = text.replace(". ", ". ... ")

        engine.say(text)
        engine.runAndWait()
        engine.stop()

    except Exception as e:
        print("[TTS Error]", e)


# ----------------------------
# Multi-language (gTTS)
# ----------------------------
def tts_gtts(text, lang):
    if not text or not text.strip():
        return
    try:
        temp_file = os.path.join(
            tempfile.gettempdir(),
            f"nova_tts_{int(time.time()*1000)}.mp3"
        )

        tts = gTTS(text=text, lang=lang)
        tts.save(temp_file)
        playsound(temp_file)

        try:
            os.remove(temp_file)
        except:
            pass

    except Exception as e:
        print("[gTTS Error]:", e)


# ----------------------------
# MAIN SPEAK FUNCTION
# ----------------------------
def speak(text, lang_hint='en'):
    """Speak text in English or other languages."""
    try:
        print(f"{CONFIG['ASSISTANT_NAME']}: {text}")

        if lang_hint == 'en':
            tts_pyttsx3(text)
        else:
            tts_gtts(text, lang_hint)

        time.sleep(0.2)

    except Exception as e:
        print("[Speak Error]:", e)
