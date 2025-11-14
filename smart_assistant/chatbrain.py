import requests
from config import CONFIG
from memory_manager import add_history, get_chat_history

# Try importing OpenAI client
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=CONFIG["OPENAI_API_KEY"], base_url=CONFIG["OPENAI_API_BASE"])
except:
    openai_client = None


# ---------------------------------------------------------
#                 OPENAI PRIMARY ENGINE
# ---------------------------------------------------------
def call_openai(messages):
    """Primary: use OpenAI for response."""
    if not openai_client or not CONFIG["OPENAI_API_KEY"]:
        return None

    try:
        response = openai_client.chat.completions.create(
            model=CONFIG["OPENAI_MODEL"],
            messages=messages,
            temperature=0.8,
            max_tokens=250
        )

        return response.choices[0].message.content

    except Exception as e:
        print("[OpenAI Error]", e)
        return None


# ---------------------------------------------------------
#               HUGGING FACE FALLBACK ENGINE
# ---------------------------------------------------------
def call_huggingface(prompt):
    """Fallback when OpenAI fails."""
    headers = {"Authorization": f"Bearer {CONFIG['HF_API_KEY']}"}

    url = f"https://router.huggingface.co/hf-inference/{CONFIG['HF_MODEL_ID']}"

    try:
        resp = requests.post(url, headers=headers, json={"inputs": prompt})
        data = resp.json()

        if resp.status_code != 200:
            print("[HF Error]", resp.status_code, resp.text)
            return None

        # Handle HF response formats
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]

        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"]

        return None

    except Exception as e:
        print("[HF Request Failed]", e)
        return None


# ---------------------------------------------------------
#                   MAIN REPLY GENERATOR
# ---------------------------------------------------------
def generate_reply(user_input, chat_history):
    """
    Generate AI reply using:
    ✓ Memory (PostgreSQL)
    ✓ OpenAI (primary)
    ✓ HuggingFace (fallback)
    """
    user_id = CONFIG["CURRENT_USER_ID"]

    # Build the message list
    messages = [
        {
            "role": "system",
            "content": (
                f"You are {CONFIG['ASSISTANT_NAME']}, a friendly personal AI assistant. "
                f"User ID: {user_id}. Use memory to respond naturally."
            )
        }
    ]

    # Add chat history from the database
    for m in chat_history:
        messages.append({"role": m["role"], "content": m["content"]})

    # Add the new user message
    messages.append({"role": "user", "content": user_input})

    # Save message (user)
    add_history(user_id, "user", user_input)

    # --- Try OpenAI ---
    reply = call_openai(messages)

    # --- If OpenAI fails → Try HuggingFace ---
    if not reply:
        combined_prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        reply = call_huggingface(combined_prompt)

    # --- If HF fails too → Final fallback ---
    if not reply:
        reply = "I'm sorry, I couldn't generate a response right now."

    # Save assistant reply
    add_history(user_id, "assistant", reply)

    return reply
