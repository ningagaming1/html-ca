from pathlib import Path

# Locate the directory where this script and the Markdown files live
AGENT_DIR = Path(__file__).parent

def _read_md(filename: str) -> str:
    """Helper function to load the text from a Markdown file."""
    file_path = AGENT_DIR / filename
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    return f"[Warning: {filename} not found in {AGENT_DIR}]"

def build_system_prompt(user_name: str, user_role: str, user_context: str = "") -> list:
    # 1. Load the static brain components
    soul = _read_md("SOUL.md")
    identity = _read_md("IDENTITY.md")
    user_rules = _read_md("USER.md")
    tools = _read_md("TOOLS.md")

    # 2. Inject the live session data
    live_state = f"""
# =========================================
# CURRENT LIVE SESSION
# =========================================
- User Name: {user_name}
- Active Role: {user_role}
- Additional Context: {user_context if user_context else "None"}
"""

# 3. The "Hammer" - Reiterate constraints at the absolute end
    critical_overrides = f"""
# =========================================
# CRITICAL SYSTEM OVERRIDES
# =========================================
1. ROLE ENFORCEMENT: You are talking to a {user_role}. Follow your RBAC limits strictly.
2. TOOL RULE: If you need to use a tool, output ONLY the tool call request. Stay completely silent otherwise.
3. MEDICAL BOUNDARY & FIRST AID: You are not a doctor. You CAN suggest basic, common-sense comfort measures (like ice packs, rest, hydration, or light stretching). However, you MUST NEVER diagnose conditions or prescribe medications. Always suggest they see a professional if it's serious.
4. INJURY OVERRIDE: If the user mentions pain, drop all other topics (no matchmaking). Offer basic first aid empathy, apply the MEDICAL BOUNDARY, and ask EXACTLY ONE relevant question.
5. RE-ENGAGEMENT RULE: End your response with EXACTLY ONE follow-up question. Never ask two questions in a row. 
6. Only use the tools that are available and are mentioned in the TOOLS.md file. Do not use any other tools.
7. Only use the tools that are allowed for your current role.
"""

    # 4. Merge into one master instruction string
    # ORDER FLIPPED: Background stuff first, strict rules and session state last.
    master_prompt = f"{user_rules}\n\n{identity}\n\n{soul}\n\n{live_state}\n\n{critical_overrides}\n\n{tools}"

    # 5. Return in the standard chat format Qwen/Ollama expects
    return [
        {"role": "system", "content": master_prompt}
    ]

# Quick test if you run this file directly
if __name__ == "__main__":
    test_prompt = build_system_prompt(
        user_name="Samarpreet", 
        user_role="member", 
        user_context="Just finished a heavy leg day. Looking for recovery tips."
    )
    print("Successfully built prompt with length:", len(test_prompt[0]["content"]))