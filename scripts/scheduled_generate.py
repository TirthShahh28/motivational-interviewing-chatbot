"""
Scheduled synthetic data generator — runs until 500 conversations exist.

This script:
  1. Counts existing conversations in data/synthetic/
  2. If under 500, generates a batch of 50 (medium, 10 turns each)
  3. After generation, runs prepare_finetune_data.py to rebuild train/eval splits
  4. Stops automatically once 500 conversations are reached

Usage (manual):
    python scripts/scheduled_generate.py

Designed to be called by a scheduler every 5 hours.
"""

import subprocess
import sys
from pathlib import Path

TARGET = 500
BATCH_SIZE = 50
SYNTHETIC_DIR = Path("data/synthetic")


def count_conversations() -> int:
    """Count total conversations across all synthetic JSONL files."""
    total = 0
    for f in SYNTHETIC_DIR.glob("*.jsonl"):
        with open(f, encoding="utf-8") as fh:
            total += sum(1 for line in fh if line.strip())
    return total


def main():
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)

    current = count_conversations()
    print(f"\n[STATUS] Current conversations: {current}/{TARGET}")

    if current >= TARGET:
        print(f"[DONE] Already at {current} conversations (target: {TARGET}). Nothing to do.")
        # Still rebuild train/eval in case it's stale
        print("\n[REBUILD] Rebuilding train/eval splits...")
        subprocess.run([sys.executable, "scripts/prepare_finetune_data.py"], check=True)
        return

    remaining = TARGET - current
    batch = min(BATCH_SIZE, remaining)
    print(f"[GENERATE] Generating {batch} conversations ({remaining} remaining to target)...\n")

    result = subprocess.run(
        [sys.executable, "scripts/generate_synthetic_data.py",
         "--batch", "medium", "--num", str(batch)],
        check=False,
    )

    if result.returncode != 0:
        print(f"[WARN] Generation exited with code {result.returncode}")

    new_count = count_conversations()
    print(f"\n[STATUS] Conversations after this run: {new_count}/{TARGET}")

    # Rebuild train/eval splits with ALL data
    print("\n[REBUILD] Rebuilding train/eval splits...")
    subprocess.run([sys.executable, "scripts/prepare_finetune_data.py"], check=True)

    if new_count >= TARGET:
        print(f"\n[COMPLETE] Target reached! {new_count} conversations ready.")
        print("   Upload data/processed/finetune_train.jsonl and finetune_eval.jsonl to Google Drive")
    else:
        print(f"\n[WAITING] {TARGET - new_count} more conversations needed. Next run in 5 hours.")


if __name__ == "__main__":
    main()
