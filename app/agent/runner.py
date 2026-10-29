import requests
import json
import os
import re

# Load .env so OLLAMA_MODEL env var is available
from dotenv import load_dotenv
load_dotenv()

try:
    from .prompt_builder import build_system_prompt
except (ImportError, ValueError):
    from prompt_builder import build_system_prompt

OLLAMA_URL      = "http://localhost:11434/api/chat"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

# ──────────────────────────────────────────────────────────────
# Model Selection
# Uses OLLAMA_MODEL env var if set, otherwise auto-detects.
# ──────────────────────────────────────────────────────────────
def get_best_ollama_model() -> str:
    env_override = os.getenv("OLLAMA_MODEL")
    if env_override:
        return env_override

    try:
        r = requests.get(OLLAMA_TAGS_URL, timeout=3)
        if r.status_code == 200:
            available = [m.get("name", "") for m in r.json().get("models", [])]
            # Prefer smaller model on CPU — faster responses
            for candidate in ["qwen2.5:3b", "qwen2.5:7b"]:
                for name in available:
                    if candidate in name:
                        return name
            if available:
                return available[0]
    except Exception:
        pass

    return "qwen2.5:3b"


# Ollama inference settings
OLLAMA_OPTIONS = {
    "num_ctx": 4096,    # memort
    "num_keep": -1,     # idel
    "temperature": 0.3  # lower = more focused / less random
}

# In-memory chat history per user session
SESSION_MEMORY = {}


# ──────────────────────────────────────────────────────────────
# 1. Backend Tool Functions
#    These are the real Python functions FitBuddy can trigger.
# ──────────────────────────────────────────────────────────────

def log_member_injury(member_id: int, injury_details: str):
    print(f"\n[BACKEND] Logged injury for member {member_id}: {injury_details}")
    return {"status": "success", "trainer_notified": True, "injury": injury_details}

def recommend_available_trainers(preferred_specialty: str = "General"):
    print(f"\n[BACKEND] Searching trainers for specialty: {preferred_specialty}")
    return [
        {"name": "Coach Ananya Verma",  "specialty": "Strength & Hypertrophy", "available_slots": 3},
        {"name": "Coach Kabir Malhotra","specialty": "HIIT & Conditioning",     "available_slots": 2}
    ]

# Map tool names (strings) → actual functions
TOOL_MAP = {
    "log_member_injury":           log_member_injury,
    "recommend_available_trainers": recommend_available_trainers
}


# ──────────────────────────────────────────────────────────────
# 2. Session Initialization
# ──────────────────────────────────────────────────────────────

def initialize_user_memory(user_name: str, user_role: str, user_context: str) -> list[dict]:
    """Builds the first system message for a new chat session."""
    raw_messages = build_system_prompt(user_name, user_role, user_context)
    full_text = "\n\n".join(m.get("content", "") for m in raw_messages if m.get("content"))
    return [{"role": "system", "content": full_text}]


# ──────────────────────────────────────────────────────────────
# 3. Health Check
# ──────────────────────────────────────────────────────────────

def check_ollama_status() -> bool:
    """Returns True if the local Ollama server is reachable."""
    try:
        r = requests.get(OLLAMA_TAGS_URL, timeout=3)
        return r.status_code == 200
    except Exception:
        return False


# ──────────────────────────────────────────────────────────────
# 4. Offline Fallback Engine
#    Used when Ollama is completely offline.
#    Returns pre-written smart replies word-by-word (simulates streaming).
# ──────────────────────────────────────────────────────────────

def _generate_fallback_response(user_message: str, user_name: str, user_role: str, user_context: str):
    msg_lower = user_message.lower()
    role = (user_role or "member").lower()

    if role == "trainer" and any(k in msg_lower for k in ["diagnos", "medic", "injury report", "prescription"]):
        reply = (
            f"Hey Coach {user_name}! I cannot provide medical advice or clinical records — that's outside my lane. "
            "Let's focus on workout programming instead.\n\nWhich client's training block should we review next? 💪"
        )
    elif role == "member" and any(k in msg_lower for k in ["pain", "tweaked", "sprain", "hurt", "injured", "sore back"]):
        log_member_injury(12611052, user_message)
        reply = (
            f"Hey {user_name}! Please stop heavy loading immediately. ⚠️ Apply ice for 15–20 minutes and rest the area. "
            "I've flagged this for your coach.\n\nDid the pain start during the setup or at the top of the movement? 🩹"
        )
    elif any(k in msg_lower for k in ["veg", "diet", "protein"]):
        reply = (
            f"Hey {user_name}! For high-protein Indian vegetarian meals: paneer bhurji, soya chunks pulao, "
            "sprouted moong chilla, and whey after your session are all great options.\n\n"
            "Want me to estimate your daily protein target based on your goal? 🎯"
        )
    elif any(k in msg_lower for k in ["warmup", "chest"]):
        reply = (
            f"Hey {user_name}! Prime your shoulders with band pull-aparts, scapular push-ups, and 2 light warm-up sets "
            "before your working weight.\n\nAre you going for flat bench strength or incline hypertrophy today? 🔥"
        )
    else:
        reply = (
            f"Hey {user_name}! FitBuddy here. Consistency and progressive overload are the keys to progress. "
            "Stay hydrated! 💪\n\nWhat exercise are you targeting next today?"
        )

    # Yield word-by-word to simulate streaming
    for word in reply.split(" "):
        yield word + " "


# ──────────────────────────────────────────────────────────────
# 5. Tool Call Parser
#    Extracts the JSON block from a model reply that contains
#    a [TOOL_CALL] tag. Returns (text_before, tool_json_or_None).
# ──────────────────────────────────────────────────────────────

def _split_tool_call(full_text: str):
    """
    Splits a model reply into:
      - The conversational text the user should see
      - The tool call JSON block (or None if no tool call)

    The model format from TOOLS.md is:
        <conversational text>
        [TOOL_CALL]
        { "tool_name": "...", "parameters": { ... } }
        [TOOL_CALL]
    """
    tag = "[TOOL_CALL]"
    idx = full_text.find(tag)
    if idx == -1:
        return full_text, None  # no tool call at all

    # Text before the first [TOOL_CALL] tag goes to the user
    user_text = full_text[:idx].strip()

    # Extract the JSON between the two [TOOL_CALL] tags
    after_first_tag = full_text[idx + len(tag):]
    end_idx = after_first_tag.find(tag)
    raw_json = after_first_tag[:end_idx].strip() if end_idx != -1 else after_first_tag.strip()

    # Strip inline comments (# ...) which are invalid JSON
    clean_json = re.sub(r"#.*$", "", raw_json, flags=re.MULTILINE).strip()

    try:
        tool_data = json.loads(clean_json)
    except json.JSONDecodeError:
        # JSON was malformed — treat the whole thing as regular text
        return full_text, None

    return user_text, tool_data


# ──────────────────────────────────────────────────────────────
# 6. Main Streaming Entry Point
# ──────────────────────────────────────────────────────────────

def stream_fitbuddy(user_message: str, user_name: str, user_role: str, user_context: str = ""):
    """
    Streams FitBuddy's reply token-by-token.

    Strategy:
    - Collect the FULL model response first (tokens arrive fast from local Ollama).
    - Split it into "user-visible text" and optional "tool call JSON".
    - Yield only the user-visible text to the browser.
    - Execute the tool silently in the background.
    - If a tool was called, make a second Ollama request for the natural follow-up reply.
    """
    session_key = f"{user_name}_{user_role}_{user_context}"
    ollama_online = check_ollama_status()

    if not ollama_online:
        print(f"[FitBuddy] Ollama is offline. Using fallback engine.")
        yield from _generate_fallback_response(user_message, user_name, user_role, user_context)
        return

    model_name = get_best_ollama_model()
    print(f"[FitBuddy] Streaming from model: '{model_name}'")

    try:
        # Initialize session history if this is a new user
        if session_key not in SESSION_MEMORY:
            SESSION_MEMORY[session_key] = initialize_user_memory(user_name, user_role, user_context)

        messages = SESSION_MEMORY[session_key]
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": True,
            "keep_alive": -1,
            "options": OLLAMA_OPTIONS
        }

        # ── Step 1: Collect the full raw response ─────────────────
        # We must collect everything before deciding what to show,
        # because the [TOOL_CALL] tag may appear anywhere in the text.
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120)
        response.raise_for_status()

        full_response = ""
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                token = chunk.get("message", {}).get("content", "")
                if token:
                    full_response += token

        # ── Step 2: Split into visible text + tool call ───────────
        user_visible_text, tool_data = _split_tool_call(full_response)

        # Save the full response to history (including the tool call,
        # so the model remembers it called a tool)
        messages.append({"role": "assistant", "content": full_response})

        # ── Step 3: Stream the user-visible part to the browser ───
        # Yield word-by-word so the frontend still feels like streaming
        if user_visible_text:
            for word in user_visible_text.split(" "):
                yield word + " "

        # ── Step 4: Execute the tool (if one was requested) ───────
        if tool_data:
            func_name = tool_data.get("tool_name")
            args      = tool_data.get("parameters", {})

            print(f"[FitBuddy] Executing tool: '{func_name}' with args: {args}")

            if func_name in TOOL_MAP:
                result = TOOL_MAP[func_name](**args)
            else:
                result = {"error": f"Tool '{func_name}' not found."}

            # Feed the tool result back to the model and get a natural reply
            messages.append({
                "role": "user",
                "content": f"Tool Output:\n{json.dumps(result)}\nNow reply naturally to the user."
            })

            follow_up_payload = {
                "model": model_name,
                "messages": messages,
                "stream": True,
                "keep_alive": -1,
                "options": OLLAMA_OPTIONS
            }

            follow_up_reply = ""
            with requests.post(OLLAMA_URL, json=follow_up_payload, stream=True, timeout=120) as stream_res:
                stream_res.raise_for_status()
                for line in stream_res.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            follow_up_reply += token
                            yield token

            messages.append({"role": "assistant", "content": follow_up_reply})

    except Exception as err:
        print(f"[FitBuddy] Ollama error: {err}. Switching to fallback.")
        yield from _generate_fallback_response(user_message, user_name, user_role, user_context)


# ──────────────────────────────────────────────────────────────
# Quick manual test — run: python runner.py
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Ollama online: {check_ollama_status()}")
    print(f"Selected model: {get_best_ollama_model()}")
    print("\n--- Live Test ---")
    for token in stream_fitbuddy("I tweaked my lower back on deadlifts today.", "Rohan Sharma", "member"):
        print(token, end="", flush=True)
    print("\n")