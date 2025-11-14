from flask import Flask, request, jsonify
from flask_cors import CORS
import secrets

# Import your backend logic
from config import CONFIG
from memory_manager import (
    get_or_create_user,
    add_history,
    get_chat_history
)
from chatbrain import generate_reply
from responses import chat_reply
from skills import *
from actions import *
from sst import listen
from tts import speak
from app_backend import parse_and_execute


app = Flask(__name__)
CORS(app)

TOKENS = {}   # token → user_id


# ---------------------------
# LOGIN
# ---------------------------
@app.post("/login")
def login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"success": False, "message": "Missing credentials"})

    user_id, status = get_or_create_user(username, password)

    if status == "WRONG_PASSWORD":
        return jsonify({"success": False, "message": "Incorrect password"})

    CONFIG["CURRENT_USER_ID"] = user_id

    # Generate login token
    token = secrets.token_hex(16)
    TOKENS[token] = user_id

    return jsonify({
        "success": True,
        "token": token,
        "status": status
    })


# ---------------------------
# PROCESS TEXT MESSAGE
# ---------------------------
@app.post("/message")
def message():
    data = request.json
    token = data.get("token")
    text = data.get("text", "").strip()

    if not token or token not in TOKENS:
        return jsonify({"reply": "Invalid or missing token"})

    if not text:
        return jsonify({"reply": "Empty message"})

    user_id = TOKENS[token]
    CONFIG["CURRENT_USER_ID"] = user_id

    # Save user input
    add_history(user_id, "user", text)

    # 1. Check commands
    if parse_and_execute(text):
        return jsonify({"reply": "Done!"})

    # 2. Small talk
    st = chat_reply(text)
    if st:
        speak(st)
        add_history(user_id, "assistant", st)
        return jsonify({"reply": st})

    # 3. AI fallback
    reply = None
    try:
        reply = ask_ai(text)  # if skills has it
    except:
        reply = None

    if not reply:
        chats = get_chat_history(user_id)
        reply = generate_reply(text, chats)

    speak(reply)
    add_history(user_id, "assistant", reply)

    return jsonify({"reply": reply})


# ---------------------------
# PROCESS VOICE INPUT
# ---------------------------
@app.post("/voice")
def voice():
    data = request.json
    token = data.get("token")

    if not token or token not in TOKENS:
        return jsonify({"reply": "Invalid or missing token"})

    user_id = TOKENS[token]
    CONFIG["CURRENT_USER_ID"] = user_id

    try:
        text = listen()
    except Exception:
        return jsonify({"reply": "Sorry, I couldn't hear you."})

    # reuse message processing
    return message()


# ---------------------------
# RUN ON RENDER
# ---------------------------
if __name__ == "__main__":
    # Render uses dynamic port and 0.0.0.0 as host
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
