"""
AnnoMI Dataset Preprocessor
============================
Converts the raw AnnoMI CSV into conversation-level JSONL format
matching our synthetic data schema. This becomes our evaluation benchmark.

Usage:
    python scripts/prepare_annomi.py
"""

import csv
import json
from pathlib import Path
from collections import defaultdict

RAW_PATH = Path("data/raw/annomi_full.csv")
OUTPUT_PATH = Path("data/evaluation/annomi_benchmark.jsonl")

# Map AnnoMI labels to our schema
TALK_TYPE_MAP = {
    "change": "change",
    "sustain": "sustain",
    "neutral": "neutral",
    "n/a": None,
}

TECHNIQUE_MAP = {
    "question": "open_question",  # AnnoMI doesn't distinguish open/closed consistently
    "reflection": "reflection",
    "therapist_input": "therapist_input",
    "other": "other",
    "n/a": None,
}


def load_annomi(path: Path) -> list[dict]:
    """Load raw AnnoMI CSV."""
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def group_by_transcript(rows: list[dict]) -> dict[str, list[dict]]:
    """Group utterances by transcript_id."""
    transcripts = defaultdict(list)
    for row in rows:
        transcripts[row["transcript_id"]].append(row)
    return dict(transcripts)


def convert_transcript(transcript_id: str, utterances: list[dict]) -> dict:
    """Convert a single AnnoMI transcript to our format."""
    # Sort by utterance_id
    utterances.sort(key=lambda x: int(x["utterance_id"]))

    meta = utterances[0]
    topic = meta["topic"]
    mi_quality = meta["mi_quality"]

    converted_utterances = []
    turn = 0

    for utt in utterances:
        speaker = "therapist" if utt["interlocutor"] == "therapist" else "client"

        if speaker == "therapist":
            turn += 1

        entry = {
            "turn": turn,
            "speaker": speaker,
            "text": utt["utterance_text"],
            "mi_technique": TECHNIQUE_MAP.get(utt.get("main_therapist_behaviour", "n/a")),
            "client_emotion": None,  # AnnoMI doesn't label emotions
            "client_defensiveness": None,  # AnnoMI doesn't label defensiveness
            "client_talk_type": TALK_TYPE_MAP.get(utt.get("client_talk_type", "n/a")),
        }

        converted_utterances.append(entry)

    return {
        "id": f"annomi_{transcript_id}",
        "source": "annomi",
        "mi_quality": mi_quality,
        "topic": topic,
        "video_title": meta.get("video_title", ""),
        "num_turns": turn,
        "utterances": converted_utterances,
    }


def print_stats(conversations: list[dict]):
    """Print dataset statistics."""
    total_utts = sum(len(c["utterances"]) for c in conversations)
    topics = defaultdict(int)
    qualities = defaultdict(int)

    for c in conversations:
        topics[c["topic"]] += 1
        qualities[c["mi_quality"]] += 1

    print(f"Conversations: {len(conversations)}")
    print(f"Total utterances: {total_utts}")
    print(f"Avg utterances/conversation: {total_utts / len(conversations):.1f}")
    print()
    print("MI Quality:")
    for q, count in sorted(qualities.items()):
        print(f"  {q}: {count}")
    print()
    print("Top topics:")
    for topic, count in sorted(topics.items(), key=lambda x: -x[1])[:10]:
        print(f"  {topic}: {count}")


def main():
    print("Loading AnnoMI dataset...")
    rows = load_annomi(RAW_PATH)
    print(f"Loaded {len(rows)} utterances")

    print("Grouping by transcript...")
    transcripts = group_by_transcript(rows)

    print("Converting to conversation format...")
    conversations = []
    for tid, utts in transcripts.items():
        conv = convert_transcript(tid, utts)
        conversations.append(conv)

    # Filter to alcohol-related only for our use case
    alcohol_convos = [c for c in conversations if "alcohol" in c["topic"].lower()]
    other_convos = [c for c in conversations if "alcohol" not in c["topic"].lower()]

    print()
    print("=" * 50)
    print("ALL CONVERSATIONS:")
    print_stats(conversations)

    print()
    print("=" * 50)
    print("ALCOHOL-RELATED ONLY:")
    print_stats(alcohol_convos) if alcohol_convos else print("None found")

    # Save all conversations (useful for general MI technique learning)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for conv in conversations:
            f.write(json.dumps(conv, ensure_ascii=False) + "\n")
    print(f"\nSaved all conversations to {OUTPUT_PATH}")

    # Save alcohol-only subset
    alcohol_path = OUTPUT_PATH.parent / "annomi_alcohol_only.jsonl"
    with open(alcohol_path, "w", encoding="utf-8") as f:
        for conv in alcohol_convos:
            f.write(json.dumps(conv, ensure_ascii=False) + "\n")
    print(f"Saved alcohol-only subset to {alcohol_path}")


if __name__ == "__main__":
    main()
