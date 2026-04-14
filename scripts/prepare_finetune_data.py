"""
Convert synthetic JSONL conversations → fine-tuning format (ChatML).

Reads all JSONL files from data/synthetic/ and outputs:
  data/processed/finetune_train.jsonl   (90%)
  data/processed/finetune_eval.jsonl    (10%)

Automatically:
  - Filters out conversations exceeding MAX_TOKENS (2048)
  - Backs up previous versions before overwriting
  - Outputs ready-to-upload files (same names every time — no renaming needed)

Each output line is one conversation in ChatML format:
  {"messages": [
    {"role": "system",  "content": "..."},
    {"role": "user",    "content": "..."},
    {"role": "assistant","content": "..."},
    ...
  ]}

Run:
    python scripts/prepare_finetune_data.py
    python scripts/prepare_finetune_data.py --stats    # just show stats
"""

import json
import random
import shutil
import time
from pathlib import Path

SYNTHETIC_DIR = Path("data/synthetic")
OUTPUT_DIR    = Path("data/processed")
BACKUP_DIR    = Path("data/processed/backups")

# Max tokens per conversation for fine-tuning (must fit in GPU memory)
MAX_TOKENS = 2048

# Rough estimate: 1 token ≈ 4 characters for English text
CHARS_PER_TOKEN = 4

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


def load_all_conversations() -> list[dict]:
    """Load all conversations from all JSONL files in synthetic dir."""
    all_convos = []
    files = sorted(SYNTHETIC_DIR.glob("*.jsonl"))
    if not files:
        print(f"No JSONL files found in {SYNTHETIC_DIR}")
        return []
    for f in files:
        count = 0
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    all_convos.append(json.loads(line))
                    count += 1
        print(f"  Loaded {count:3d} conversations from {f.name}")
    return all_convos


def estimate_tokens(messages: list[dict]) -> int:
    """Estimate token count for a ChatML conversation.

    Uses character-based estimation with overhead for chat template tokens.
    Gemma 2 chat template adds ~10 tokens per message for role markers.
    """
    total_chars = sum(len(m["content"]) for m in messages)
    token_estimate = total_chars // CHARS_PER_TOKEN
    # Add overhead: ~10 tokens per message for chat template markers
    token_estimate += len(messages) * 10
    return token_estimate


def build_chatml(conversation: dict) -> dict | None:
    """Convert one conversation dict → ChatML messages format."""
    utterances = conversation.get("utterances", [])
    if not utterances:
        return None

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Group utterances by turn (therapist + client = one exchange)
    turns = {}
    for utt in utterances:
        t = utt["turn"]
        if t not in turns:
            turns[t] = {}
        turns[t][utt["speaker"]] = utt

    for turn_num in sorted(turns.keys()):
        turn = turns[turn_num]
        therapist_utt = turn.get("therapist")
        client_utt    = turn.get("client")

        if turn_num == 1 and therapist_utt:
            messages.append({
                "role": "user",
                "content": "[Session begins. Client enters.]"
            })
            messages.append({
                "role": "assistant",
                "content": therapist_utt["text"]
            })
            if client_utt:
                messages.append({
                    "role": "user",
                    "content": _client_text(client_utt)
                })
        else:
            if therapist_utt:
                messages.append({
                    "role": "assistant",
                    "content": therapist_utt["text"]
                })
            if client_utt:
                messages.append({
                    "role": "user",
                    "content": _client_text(client_utt)
                })

    # The last message should be a client utterance (user role)
    while messages and messages[-1]["role"] == "assistant":
        messages.pop()

    if len(messages) < 3:
        return None

    return {"messages": messages}


def _client_text(utt: dict) -> str:
    """Format client utterance, optionally including state labels as context."""
    text = utt["text"]
    parts = []
    if utt.get("client_emotion"):
        parts.append(f"emotion:{utt['client_emotion']}")
    if utt.get("client_defensiveness"):
        parts.append(f"defensiveness:{utt['client_defensiveness']}")
    if parts:
        text = f"{text}\n[{', '.join(parts)}]"
    return text


def split_train_eval(data: list, eval_ratio: float = 0.1, seed: int = 42):
    """Split data into train/eval sets."""
    random.seed(seed)
    shuffled = data.copy()
    random.shuffle(shuffled)
    split = max(1, int(len(shuffled) * eval_ratio))
    return shuffled[split:], shuffled[:split]


def write_jsonl(data: list[dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def backup_existing(train_path: Path, val_path: Path):
    """Backup existing processed files before overwriting."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    for p in [train_path, val_path]:
        if p.exists():
            backup = BACKUP_DIR / f"{p.stem}_{timestamp}{p.suffix}"
            shutil.copy2(p, backup)
            print(f"  Backed up: {p.name} -> backups/{backup.name}")


def print_stats(train: list, val: list, filtered_count: int = 0):
    all_data = train + val
    total_messages = sum(len(d["messages"]) for d in all_data)
    avg_messages    = total_messages / len(all_data) if all_data else 0

    token_counts = [estimate_tokens(d["messages"]) for d in all_data]
    min_tok = min(token_counts) if token_counts else 0
    max_tok = max(token_counts) if token_counts else 0
    avg_tok = sum(token_counts) / len(token_counts) if token_counts else 0

    print(f"\n{'='*50}")
    print(f"  DATASET STATISTICS")
    print(f"{'='*50}")
    print(f"  Total conversations : {len(all_data)}")
    print(f"  Train split         : {len(train)}")
    print(f"  Eval split          : {len(val)}")
    print(f"  Filtered (too long) : {filtered_count}")
    print(f"  Avg messages/convo  : {avg_messages:.1f}")
    print(f"  Token range         : {min_tok} - {max_tok} (avg {avg_tok:.0f})")
    print(f"  Max allowed tokens  : {MAX_TOKENS}")
    print(f"{'='*50}\n")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats", action="store_true", help="Show stats only")
    parser.add_argument("--no-state-labels", action="store_true",
                        help="Don't include emotion/defensiveness hints in client turns")
    parser.add_argument("--max-tokens", type=int, default=MAX_TOKENS,
                        help=f"Max tokens per conversation (default: {MAX_TOKENS})")
    args = parser.parse_args()

    max_tokens = args.max_tokens

    print(f"\nLoading conversations from {SYNTHETIC_DIR}/")
    conversations = load_all_conversations()
    print(f"\nTotal loaded: {len(conversations)} conversations")

    if not conversations:
        print("No data found. Run generate_synthetic_data.py first.")
        return

    # Convert to ChatML
    if args.no_state_labels:
        global _client_text
        _client_text = lambda utt: utt["text"]

    print("\nConverting to ChatML format...")
    converted = []
    skipped = 0
    filtered_too_long = 0

    for c in conversations:
        result = build_chatml(c)
        if result is None:
            skipped += 1
            continue

        # Filter by estimated token count
        est_tokens = estimate_tokens(result["messages"])
        if est_tokens > max_tokens:
            filtered_too_long += 1
            continue

        converted.append(result)

    print(f"Converted: {len(converted)} | Skipped (bad format): {skipped} | Filtered (>{max_tokens} tokens): {filtered_too_long}")

    if args.stats:
        train, val = split_train_eval(converted)
        print_stats(train, val, filtered_too_long)
        return

    # Split and write
    train, val = split_train_eval(converted)
    print_stats(train, val, filtered_too_long)

    train_path = OUTPUT_DIR / "finetune_train.jsonl"
    val_path   = OUTPUT_DIR / "finetune_eval.jsonl"

    # Backup existing files before overwriting
    backup_existing(train_path, val_path)

    write_jsonl(train, train_path)
    write_jsonl(val, val_path)

    print(f"  Written: {train_path}  ({len(train)} conversations)")
    print(f"  Written: {val_path}    ({len(val)} conversations)")
    print(f"\nNext step: Upload these to Google Colab or Google Drive")
    print(f"  data/processed/finetune_train.jsonl")
    print(f"  data/processed/finetune_eval.jsonl")


if __name__ == "__main__":
    main()
