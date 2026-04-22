"""
Dataset Progress Tracker
========================
Shows how many conversations and utterances have been generated
across all batch files.

Usage:
    python scripts/check_progress.py
    python scripts/check_progress.py --target 1000
    python scripts/check_progress.py --detailed
"""

import argparse
import json
from pathlib import Path
from collections import Counter

SYNTHETIC_DIR = Path("data/synthetic")
TARGET_DEFAULT = 1000


def load_all_conversations() -> list[dict]:
    """Load all conversations from all JSONL files in synthetic dir."""
    conversations = []
    for file in sorted(SYNTHETIC_DIR.glob("*.jsonl")):
        with open(file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        conversations.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return conversations


def print_progress(conversations: list[dict], target: int, detailed: bool = False):
    """Print progress summary."""
    total_convos = len(conversations)
    total_utterances = sum(len(c.get("utterances", [])) for c in conversations)
    pct = (total_convos / target * 100) if target > 0 else 0

    # Progress bar
    bar_len = 40
    filled = int(bar_len * total_convos / target) if target > 0 else 0
    bar = "#" * filled + "-" * (bar_len - filled)

    print("=" * 55)
    print("  SYNTHETIC DATA GENERATION PROGRESS")
    print("=" * 55)
    print()
    print(f"  [{bar}] {pct:.1f}%")
    print()
    print(f"  Conversations:  {total_convos:>6} / {target}")
    print(f"  Utterances:     {total_utterances:>6}")
    print(f"  Remaining:      {max(0, target - total_convos):>6}")
    print()

    # Per-file breakdown
    print("  FILES:")
    print(f"  {'File':<45} {'Convos':>7} {'Utts':>7}")
    print("  " + "-" * 61)
    for file in sorted(SYNTHETIC_DIR.glob("*.jsonl")):
        with open(file, encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        file_convos = len(lines)
        file_utts = 0
        for line in lines:
            try:
                c = json.loads(line)
                file_utts += len(c.get("utterances", []))
            except json.JSONDecodeError:
                pass
        print(f"  {file.name:<45} {file_convos:>7} {file_utts:>7}")
    print()

    if not detailed or not conversations:
        return

    # Detailed stats
    print("  DIVERSITY BREAKDOWN:")
    print()

    # By batch type
    batch_types = Counter(c.get("batch_type", "unknown") for c in conversations)
    print(f"  Batch types:")
    for bt, count in batch_types.most_common():
        print(f"    {bt:<15} {count:>5} conversations")
    print()

    # By profile
    profiles = Counter(c.get("client_profile", "unknown") for c in conversations)
    print(f"  Client profiles (top 10):")
    for profile, count in profiles.most_common(10):
        print(f"    {profile:<40} {count:>5}")
    print()

    # By defensiveness arc
    arcs = Counter(c.get("defensiveness_arc", "unknown") for c in conversations)
    print(f"  Defensiveness arcs:")
    for arc, count in arcs.most_common():
        print(f"    {arc:<45} {count:>5}")
    print()

    # Label distribution across all utterances
    emotions = Counter()
    defensiveness = Counter()
    talk_types = Counter()
    techniques = Counter()

    for c in conversations:
        for utt in c.get("utterances", []):
            if utt.get("speaker") == "client":
                emotions[utt.get("client_emotion", "unknown")] += 1
                defensiveness[utt.get("client_defensiveness", "unknown")] += 1
                talk_types[utt.get("client_talk_type", "unknown")] += 1
            else:
                techniques[utt.get("mi_technique", "unknown")] += 1

    print(f"  Emotion distribution:")
    for emo, count in emotions.most_common():
        pct_e = count / sum(emotions.values()) * 100
        print(f"    {emo:<20} {count:>5} ({pct_e:.1f}%)")
    print()

    print(f"  Defensiveness distribution:")
    for d, count in defensiveness.most_common():
        pct_d = count / sum(defensiveness.values()) * 100
        print(f"    {d:<20} {count:>5} ({pct_d:.1f}%)")
    print()

    print(f"  Client talk types:")
    for tt, count in talk_types.most_common():
        pct_t = count / sum(talk_types.values()) * 100
        print(f"    {tt:<20} {count:>5} ({pct_t:.1f}%)")
    print()

    print(f"  Therapist MI techniques:")
    for tech, count in techniques.most_common():
        pct_tech = count / sum(techniques.values()) * 100
        print(f"    {tech:<20} {count:>5} ({pct_tech:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Check synthetic data generation progress")
    parser.add_argument("--target", type=int, default=TARGET_DEFAULT, help="Target number of conversations")
    parser.add_argument("--detailed", action="store_true", help="Show detailed diversity breakdown")
    args = parser.parse_args()

    if not SYNTHETIC_DIR.exists():
        print("No synthetic data directory found. Run generate_synthetic_data.py first.")
        return

    conversations = load_all_conversations()
    print_progress(conversations, args.target, args.detailed)


if __name__ == "__main__":
    main()
