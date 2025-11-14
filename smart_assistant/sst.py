import speech_recognition as sr
from tts import speak
from config import CONFIG

# Initialize recognizer
recognizer = sr.Recognizer()
recognizer.energy_threshold = 250
recognizer.dynamic_energy_threshold = True


def listen():
    """Safe speech recognition that NEVER breaks the main loop."""
    try:
        with sr.Microphone() as source:
            print("\n🎤 Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.4)

            # Listen for audio
            audio = recognizer.listen(source, phrase_time_limit=6)

        print("🧠 Recognizing...")

        # Convert to text
        text = recognizer.recognize_google(audio, language=CONFIG["LANGUAGE"])
        print(f"You: {text}")
        return text.strip()

    # User spoke nothing
    except sr.UnknownValueError:
        return ""   # <-- return blank, DO NOT speak anything

    # Internet down or Google STT failed
    except sr.RequestError:
        speak("Speech service unavailable. Please type your command.")
        return input("You: ")

    # Any other error (alarm sound, noise, unexpected sound)
    except Exception as e:
        print("[SST Error]", e)
        return ""   # <-- This is the FIX that prevents crashing

def reset_microphone():
    """Flush microphone noise after alarm/timer to prevent lock."""
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
    except:
        pass
