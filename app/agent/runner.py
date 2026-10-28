import requests
import json
import time
import os

try:
    from .prompt_builder import build_system_prompt
except (ImportError, ValueError):
    from prompt_builder import build_system_prompt

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

def get_best_ollama_model() -> str:
    """
    Auto-detects the best available model in Ollama.
    Prefers qwen2.5:3b on CPU for 3-4x faster response times, or respects OLLAMA_MODEL env var.
    """
    env_override = os.getenv("OLLAMA_MODEL")
    if env_override:
        return env_override

    try:
        r = requests.get(OLLAMA_TAGS_URL, timeout=3)
        if r.status_code == 200:
            available = [m.get("name", "") for m in r.json().get("models", [])]
            # Prefer 3b on CPU if available to prevent excessive swap latency
            for candidate in ["qwen2.5:3b", "qwen2.5:7b"]:
                for name in available:
                    if candidate in name:
                        return name
            if available:
                return available[0]
    except Exception:
        pass

    return "qwen2.5:3b"

# Sensible options for responsive local CPU/GPU execution without memory thrashing
OLLAMA_OPTIONS = {
    "num_ctx": 4096,     # Fits prompt and KV cache cleanly in RAM
    "num_keep": -1,      # Retain loaded model in memory
    "temperature": 0.3
}

SESSION_MEMORY = {}

# 1. Backend Tool Functions
def log_member_injury(member_id: int, injury_details: str):
    print(f"\n[BACKEND EXECUTED] Logged injury for {member_id}: {injury_details}")
    return {"status": "success", "trainer_notified": True, "injury": injury_details}

def recommend_available_trainers(preferred_specialty: str = "General"):
    print(f"\n[BACKEND EXECUTED] Searching for {preferred_specialty} trainers...")
    return [
        {"name": "Coach Ananya Verma", "specialty": "Strength & Hypertrophy", "available_slots": 3},
        {"name": "Coach Kabir Malhotra", "specialty": "HIIT & Conditioning", "available_slots": 2}
    ]

TOOL_MAP = {
    "log_member_injury": log_member_injury,
    "recommend_available_trainers": recommend_available_trainers
}

def initialize_user_memory(user_name: str, user_role: str, user_context: str) -> list[dict]:
    """
    Initializes user session with the structured system prompt.
    Does not run blocking pre-requests with unrealistic timeouts.
    """
    raw_messages = build_system_prompt(user_name, user_role, user_context)
    full_text = "\n\n".join(m.get("content", "") for m in raw_messages if m.get("content"))

    return [{
        "role": "system",
        "content": full_text
    }]

def check_ollama_status() -> bool:
    """Checks if Ollama daemon is reachable on port 11434."""
    try:
        r = requests.get(OLLAMA_TAGS_URL, timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def _generate_fallback_response(user_message: str, user_name: str, user_role: str, user_context: str):
    """
    Offline persona engine used ONLY when Ollama server is completely shut down.
    """
    msg_lower = user_message.lower()
    role = (user_role or "member").lower()

    if role == "trainer" and any(k in msg_lower for k in ["diagnos", "medic", "injury report", "prescription"]):
        reply = (
            f"Hey Coach {user_name}! I cannot provide medical advice or client clinical records—that's "
            "outside my lane! Let's keep our focus on workout programming and strength progressions instead.\n\n"
            "Which client's training block should we review next? 💪"
        )
    elif role == "member" and any(k in msg_lower for k in ["pain", "tweaked", "sprain", "hurt", "injured", "sore back"]):
        log_member_injury(12611052, user_message)
        reply = (
            f"Hey {user_name}! Please pause heavy loading immediately. ⚠️ I'm your fitness buddy, not a doctor! "
            "Apply ice or heat for 15-20 minutes, avoid spinal compression, and consult a physiotherapist if pain persists. "
            "I've logged this for your coach to review.\n\n"
            "Did the pain start during the setup or on the lockout? 🩹"
        )
    elif "veg" in msg_lower or "diet" in msg_lower or "protein" in msg_lower:
        reply = (
            f"Hey {user_name}! For high-protein Indian vegetarian meals, prioritize paneer bhurji, soya chunks pulao, "
            "sprouted moong chilla, and whey protein after your session!\n\n"
            "Would you like me to calculate your daily protein targets based on your goal? 🎯"
        )
    elif "warmup" in msg_lower or "chest" in msg_lower:
        reply = (
            f"Hey {user_name}! Prime your shoulders with band pull-aparts, scapular push-ups, and 2 light warmup sets "
            "before your working weight.\n\n"
            "Are you focusing on flat bench strength or incline hypertrophy today? 🔥"
        )
    else:
        reply = (
            f"Hey {user_name}! FitBuddy here. Consistency and progressive overload are key. Make sure to stay hydrated!\n\n"
            "What exercise are you targeting next today? 💪"
        )

    for word in reply.split(" "):
        yield word + " "

def stream_fitbuddy(user_message: str, user_name: str, user_role: str, user_context: str = ""):
    """
    Main entry point for conversational agent.
    Streams directly from Ollama when available, with resilient streaming & tool calling.
    """
    session_key = f"{user_name}_{user_role}_{user_context}"
    ollama_online = check_ollama_status()

    if not ollama_online:
        print(f"[FitBuddy Notice] Ollama is offline at {OLLAMA_URL}. Using offline fallback engine.")
        for chunk in _generate_fallback_response(user_message, user_name, user_role, user_context):
            yield chunk
        return

    # Ollama is online: proceed with real local LLM streaming
    model_name = get_best_ollama_model()
    print(f"[FitBuddy Agent] Streaming from Ollama model: '{model_name}'")

    try:
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

        # Generous timeout for CPU inference
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120)
        response.raise_for_status()

        text_buffer = ""
        is_potential_json = False
        is_tool_call = False

        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                content = chunk.get("message", {}).get("content", "")

                if content:
                    text_buffer += content
                    stripped = text_buffer.lstrip()

                    # Intercept JSON tool calls if emitted
                    if stripped.startswith("{") or stripped.startswith("[TOOL_CALL]"):
                        is_potential_json = True
                        if '"tool_name"' in stripped:
                            is_tool_call = True
                        continue
                    elif not is_potential_json:
                        yield content

        if is_potential_json and not is_tool_call:
            yield text_buffer

        messages.append({"role": "assistant", "content": text_buffer})

        # Tool Execution if the model produced a tool call
        if is_tool_call:
            try:
                import re
                json_str = text_buffer[text_buffer.find("{"):text_buffer.rfind("}")+1]
                clean_json = re.sub(r'#.*$', '', json_str, flags=re.MULTILINE)
                extracted_tool = json.loads(clean_json)

                func_name = extracted_tool.get("tool_name")
                args = extracted_tool.get("parameters", {})

                print(f"[FitBuddy Agent] Executing Tool: {func_name} with {args}")
                if func_name in TOOL_MAP:
                    result = TOOL_MAP[func_name](**args)
                else:
                    result = {"error": f"Tool {func_name} not found."}

                messages.append({
                    "role": "user",
                    "content": f"Tool Output:\n{json.dumps(result)}\nNow reply naturally to the user."
                })

                final_payload = {
                    "model": model_name,
                    "messages": messages,
                    "stream": True,
                    "keep_alive": -1,
                    "options": OLLAMA_OPTIONS
                }

                final_reply = ""
                with requests.post(OLLAMA_URL, json=final_payload, stream=True, timeout=120) as stream_res:
                    stream_res.raise_for_status()
                    for line in stream_res.iter_lines():
                        if line:
                            chunk = json.loads(line)
                            final_content = chunk.get("message", {}).get("content", "")
                            if final_content:
                                final_reply += final_content
                                yield final_content

                messages.append({"role": "assistant", "content": final_reply})
            except Exception as e:
                print(f"[FitBuddy Tool Error] {e}")

    except Exception as err:
        print(f"[Ollama Runtime Error] {err}. Switching to fallback.")
        for chunk in _generate_fallback_response(user_message, user_name, user_role, user_context):
            yield chunk

if __name__ == "__main__":
    print(f"Checking Ollama status: {check_ollama_status()}")
    print(f"Selected model: {get_best_ollama_model()}")
    print("\n--- Testing stream_fitbuddy Live ---")
    for token in stream_fitbuddy("Hello! I want a quick 3-exercise chest workout.", "Rohan Sharma", "member"):
        print(token, end="", flush=True)
    print("\n")