import requests
import json
from prompt_builder import build_system_prompt

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:7b"
MAX_CHUNK_CHARS = 3500  # Keeps every individual prompt chunk safely under 4k

# Sent automatically with every request so you NEVER have to change settings on a new device
OLLAMA_OPTIONS = {
    "num_ctx": 65536,   # Unlocks 64k token memory automatically via API (raise to 100000 if needed)
    "num_keep": -1,     # Forces Ollama to keep all system prompt chunks locked in RAM
    "temperature": 0.3
}

# Stores conversation history per user so the 10k prompt is only sent once per session
SESSION_MEMORY = {}

# 1. Mock Backend Functions
def log_member_injury(member_id: int, injury_details: str):
    print(f"\n[BACKEND EXECUTED] Logged injury for {member_id}: {injury_details}")
    return {"status": "success", "trainer_notified": True}

def recommend_available_trainers(preferred_specialty: str = "General"):
    print(f"\n[BACKEND EXECUTED] Searching for {preferred_specialty} trainers...")
    return [{"name": "Coach Sarah", "specialty": "Bodybuilding", "available_slots": 2}]

TOOL_MAP = {
    "log_member_injury": log_member_injury,
    "recommend_available_trainers": recommend_available_trainers
}


def split_into_chunks(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Splits a 10k+ prompt into <4k chunks on line breaks so Markdown/JSON never breaks."""
    if len(text) <= max_chars:
        return [text]

    chunks, current = [], ""
    for line in text.splitlines(keepends=True):
        if len(current) + len(line) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            while len(line) > max_chars:
                chunks.append(line[:max_chars])
                line = line[max_chars:]
        current += line

    if current.strip():
        chunks.append(current.strip())
    return chunks


def initialize_user_memory(user_name: str, user_role: str, user_context: str) -> list[dict]:
    """
    Splits the 10k system prompt into <4k chunks and sends them one by one 
    to load Ollama's KV memory cache on the first turn.
    """
    raw_messages = build_system_prompt(user_name, user_role, user_context)
    full_text = "\n\n".join(m.get("content", "") for m in raw_messages if m.get("content"))
    chunks = split_into_chunks(full_text, MAX_CHUNK_CHARS)

    messages = []
    for idx, chunk in enumerate(chunks, start=1):
        messages.append({
            "role": "system",
            "content": f"[System Memory Part {idx}/{len(chunks)}]\n{chunk}"
        })
        # Send each <4k chunk one by one into Ollama's memory cache
        res = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "stream": False,
                "keep_alive": -1,
                "options": {**OLLAMA_OPTIONS, "num_predict": 1}
            }
        )
        res.raise_for_status()

    return messages


def stream_fitbuddy(user_message: str, user_name: str, user_role: str, user_context: str = ""):
    session_key = f"{user_name}_{user_role}_{user_context}"

    try:
        # Only chunk and send the 10k prompt if this user isn't in memory yet
        if session_key not in SESSION_MEMORY:
            SESSION_MEMORY[session_key] = initialize_user_memory(user_name, user_role, user_context)

        messages = SESSION_MEMORY[session_key]
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "stream": True,
            "keep_alive": -1,
            "options": OLLAMA_OPTIONS
        }

        response = requests.post(OLLAMA_URL, json=payload, stream=True)
        response.raise_for_status()

        text_buffer = ""
        is_potential_json = False
        is_tool_call = False

        # Read the stream in real-time
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                content = chunk.get("message", {}).get("content", "")

                if content:
                    text_buffer += content
                    stripped = text_buffer.lstrip()

                    # Hold TTS if output begins with '{' until we confirm if it's a tool call
                    if stripped.startswith("{"):
                        is_potential_json = True
                        if '"tool_name"' in stripped:
                            is_tool_call = True
                        continue
                    elif not is_potential_json:
                        yield content

        if is_potential_json and not is_tool_call:
            yield text_buffer

        # Save model response in memory
        messages.append({"role": "assistant", "content": text_buffer})

        # === TOOL EXECUTION PHASE ===
        if is_tool_call:
            try:
                json_str = text_buffer[text_buffer.find("{"):text_buffer.rfind("}")+1]
                extracted_tool = json.loads(json_str)

                func_name = extracted_tool.get("tool_name")
                args = extracted_tool.get("parameters", {})

                if func_name in TOOL_MAP:
                    result = TOOL_MAP[func_name](**args)
                else:
                    result = {"error": f"Tool {func_name} not found."}

                messages.append({
                    "role": "user",
                    "content": f"Tool Output:\n{json.dumps(result)}\nNow reply naturally to the user."
                })

                final_payload = {
                    "model": MODEL_NAME,
                    "messages": messages,
                    "stream": True,
                    "keep_alive": -1,
                    "options": OLLAMA_OPTIONS
                }

                final_reply = ""
                with requests.post(OLLAMA_URL, json=final_payload, stream=True) as stream_res:
                    stream_res.raise_for_status()
                    for line in stream_res.iter_lines():
                        if line:
                            chunk = json.loads(line)
                            final_content = chunk.get("message", {}).get("content", "")
                            if final_content:
                                final_reply += final_content
                                yield final_content

                # Save final natural voice response in memory
                messages.append({"role": "assistant", "content": final_reply})

            except Exception as e:
                yield f"\n[Agent internal error parsing tool output: {e}]"

    except Exception as e:
        yield f"System Error: {e}"


if __name__ == "__main__":
    print("FitBuddy (Flexi) - Turn 1 (Loads chunks & answers):")
    print("-" * 40)
    for text_chunk in stream_fitbuddy(
        user_message="I tweaked my lower back on deadlifts today.",
        user_name="Samarpreet",
        user_role="member",
        user_context="member_id=12611052"
    ):
        print(text_chunk, end="", flush=True)
    print("\n")

    print("FitBuddy (Flexi) - Turn 2 (Remembers Turn 1 & system prompt automatically):")
    print("-" * 40)
    for text_chunk in stream_fitbuddy(
        user_message="Can you match me with a bodybuilding trainer who knows about the injury I just mentioned?",
        user_name="Samarpreet",
        user_role="member",
        user_context="member_id=12611052"
    ):
        print(text_chunk, end="", flush=True)
    print("\n")