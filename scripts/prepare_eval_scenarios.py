"""
Prepare Evaluation Scenarios
============================
Extracts test scenarios from 3 sources:
  1. AnnoMI real conversations (29 alcohol-specific)
  2. Synthetic eval split (40 held-out conversations)
  3. Hand-crafted edge cases (20 boundary scenarios)

Each scenario = a conversation context + the client's last message.
The model must generate a therapist response, which Claude then scores.

Output: data/evaluation/eval_scenarios.jsonl
  Each line: {
    "id": "annomi_0_turn_12",
    "source": "annomi|synthetic_eval|edge_case",
    "conversation_history": [...],   # previous turns as ChatML messages
    "client_message": "...",         # the message the model must respond to
    "client_emotion": "...",         # if available
    "client_defensiveness": "...",   # if available
    "reference_response": "...",     # real therapist response (AnnoMI only)
    "reference_technique": "...",    # MI technique label (AnnoMI only)
  }

Run:
    python scripts/prepare_eval_scenarios.py
"""

import json
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
ANNOMI_FILE = PROJECT_DIR / "data" / "evaluation" / "annomi_alcohol_only.jsonl"
EVAL_FILE = PROJECT_DIR / "data" / "processed" / "finetune_eval.jsonl"
EDGE_CASE_FILE = PROJECT_DIR / "data" / "evaluation" / "edge_case_scenarios.jsonl"
OUTPUT_FILE = PROJECT_DIR / "data" / "evaluation" / "eval_scenarios.jsonl"

SYSTEM_PROMPT = """You are a compassionate, skilled therapist specializing in Motivational Interviewing (MI) for alcohol-related concerns.

Your approach:
- Use OARS: Open questions, Affirmations, Reflections, Summaries
- Meet the client where they are — never confront or lecture
- Roll with resistance, don't fight it
- Evoke the client's own motivation for change
- Respect autonomy — the client decides if and when they change
- Reflect emotions and defensiveness back with empathy
- Use summaries to collect change talk and reflect it back

You adapt your technique based on the client's emotional state and defensiveness level."""


def load_jsonl(path: Path) -> list[dict]:
    data = []
    if not path.exists():
        print(f"  ⚠️  File not found: {path}")
        return data
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def extract_annomi_scenarios(conversations: list[dict]) -> list[dict]:
    """
    From each AnnoMI conversation, extract scenarios at key moments:
    - After client shows defensiveness (sustain talk)
    - After client shows openness (change talk)
    - Mid-conversation turns

    For each, we capture the conversation up to that point + the client message,
    and store the real therapist's next response as reference.
    """
    scenarios = []

    for convo in conversations:
        convo_id = convo["id"]
        utterances = convo.get("utterances", [])

        # Group by turn
        turns = {}
        for utt in utterances:
            t = utt["turn"]
            if t not in turns:
                turns[t] = {}
            turns[t][utt["speaker"]] = utt

        sorted_turns = sorted(turns.keys())

        # Extract scenarios at interesting points
        # Pick turns where client has sustain/change talk and next turn has therapist
        for i, turn_num in enumerate(sorted_turns):
            turn = turns[turn_num]
            client_utt = turn.get("client")

            if not client_utt:
                continue

            # Check if there's a next turn with a therapist response (our reference)
            next_turn_num = sorted_turns[i + 1] if i + 1 < len(sorted_turns) else None
            if next_turn_num is None:
                continue

            next_turn = turns[next_turn_num]
            therapist_utt = next_turn.get("therapist")
            if not therapist_utt:
                continue

            # Only pick interesting turns (sustain or change talk)
            talk_type = client_utt.get("client_talk_type", "neutral")
            is_interesting = talk_type in ("sustain", "change")

            if not is_interesting:
                continue

            # Limit to max 3 scenarios per conversation to keep total manageable
            convo_scenarios_so_far = sum(1 for s in scenarios if s["id"].startswith(convo_id))
            if convo_scenarios_so_far >= 3:
                continue

            # Build conversation history up to this point
            history = []
            for prev_turn_num in sorted_turns:
                if prev_turn_num > turn_num:
                    break
                prev_turn = turns[prev_turn_num]

                prev_therapist = prev_turn.get("therapist")
                prev_client = prev_turn.get("client")

                if prev_turn_num == turn_num:
                    # For the current turn, include therapist (if any) but client is the prompt
                    if prev_therapist:
                        history.append({
                            "role": "assistant",
                            "content": prev_therapist["text"]
                        })
                    # Client message is separate — it's the prompt
                else:
                    if prev_therapist:
                        history.append({
                            "role": "assistant",
                            "content": prev_therapist["text"]
                        })
                    if prev_client:
                        history.append({
                            "role": "user",
                            "content": prev_client["text"]
                        })

            scenarios.append({
                "id": f"{convo_id}_turn_{turn_num}",
                "source": "annomi",
                "conversation_history": history,
                "client_message": client_utt["text"],
                "client_emotion": client_utt.get("client_emotion"),
                "client_defensiveness": client_utt.get("client_defensiveness"),
                "client_talk_type": talk_type,
                "reference_response": therapist_utt["text"],
                "reference_technique": therapist_utt.get("mi_technique"),
                "mi_quality": convo.get("mi_quality", "unknown"),
            })

    return scenarios


def extract_synthetic_eval_scenarios(conversations: list[dict]) -> list[dict]:
    """
    From synthetic eval conversations (already in ChatML format),
    extract the last client message as the test prompt.
    Also extract a mid-conversation prompt for variety.
    """
    scenarios = []

    for i, convo in enumerate(conversations):
        messages = convo.get("messages", [])
        if len(messages) < 4:
            continue

        # Find user messages (skip system prompt and first [Session begins])
        user_indices = [j for j, m in enumerate(messages) if m["role"] == "user"]

        if len(user_indices) < 2:
            continue

        # Scenario 1: Last client message
        last_user_idx = user_indices[-1]
        history = messages[:last_user_idx]
        client_msg = messages[last_user_idx]["content"]

        # Parse emotion/defensiveness from the [emotion:X, defensiveness:Y] tag
        emotion, defensiveness = _parse_state_tags(client_msg)
        clean_msg = _clean_client_message(client_msg)

        scenarios.append({
            "id": f"synthetic_eval_{i}_last",
            "source": "synthetic_eval",
            "conversation_history": history,
            "client_message": client_msg,
            "client_emotion": emotion,
            "client_defensiveness": defensiveness,
            "client_talk_type": None,
            "reference_response": None,
            "reference_technique": None,
        })

        # Scenario 2: Mid-conversation (pick a user message around the middle)
        mid_idx = user_indices[len(user_indices) // 2]
        if mid_idx + 1 < len(messages):
            mid_history = messages[:mid_idx]
            mid_msg = messages[mid_idx]["content"]
            mid_emotion, mid_def = _parse_state_tags(mid_msg)

            scenarios.append({
                "id": f"synthetic_eval_{i}_mid",
                "source": "synthetic_eval",
                "conversation_history": mid_history,
                "client_message": mid_msg,
                "client_emotion": mid_emotion,
                "client_defensiveness": mid_def,
                "client_talk_type": None,
                "reference_response": messages[mid_idx + 1]["content"] if messages[mid_idx + 1]["role"] == "assistant" else None,
                "reference_technique": None,
            })

    return scenarios


def _parse_state_tags(text: str) -> tuple:
    """Extract [emotion:X, defensiveness:Y] from client message."""
    emotion, defensiveness = None, None
    if "[" in text and "]" in text:
        tag = text[text.rfind("[") + 1:text.rfind("]")]
        for part in tag.split(","):
            part = part.strip()
            if part.startswith("emotion:"):
                emotion = part.split(":")[1].strip()
            elif part.startswith("defensiveness:"):
                defensiveness = part.split(":")[1].strip()
    return emotion, defensiveness


def _clean_client_message(text: str) -> str:
    """Remove state tags from message."""
    if "\n[" in text:
        return text[:text.rfind("\n[")].strip()
    return text


def load_edge_cases() -> list[dict]:
    """Load hand-crafted edge case scenarios."""
    data = load_jsonl(EDGE_CASE_FILE)
    if not data:
        print("  ⚠️  No edge cases found. Run this script after creating edge_case_scenarios.jsonl")
    return data


def main():
    print("=" * 50)
    print("  PREPARING EVALUATION SCENARIOS")
    print("=" * 50)

    all_scenarios = []

    # 1. AnnoMI real conversations
    print("\n1. Loading AnnoMI alcohol conversations...")
    annomi = load_jsonl(ANNOMI_FILE)
    annomi_scenarios = extract_annomi_scenarios(annomi)
    all_scenarios.extend(annomi_scenarios)
    print(f"   Extracted {len(annomi_scenarios)} scenarios from {len(annomi)} conversations")

    # 2. Synthetic eval split
    print("\n2. Loading synthetic eval conversations...")
    synthetic = load_jsonl(EVAL_FILE)
    synthetic_scenarios = extract_synthetic_eval_scenarios(synthetic)
    all_scenarios.extend(synthetic_scenarios)
    print(f"   Extracted {len(synthetic_scenarios)} scenarios from {len(synthetic)} conversations")

    # 3. Edge cases
    print("\n3. Loading edge case scenarios...")
    edge_cases = load_edge_cases()
    all_scenarios.extend(edge_cases)
    print(f"   Loaded {len(edge_cases)} edge case scenarios")

    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for scenario in all_scenarios:
            f.write(json.dumps(scenario, ensure_ascii=False) + "\n")

    print(f"\n{'=' * 50}")
    print(f"  TOTAL: {len(all_scenarios)} evaluation scenarios")
    print(f"  - AnnoMI:         {len(annomi_scenarios)}")
    print(f"  - Synthetic eval: {len(synthetic_scenarios)}")
    print(f"  - Edge cases:     {len(edge_cases)}")
    print(f"  Saved to: {OUTPUT_FILE}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
