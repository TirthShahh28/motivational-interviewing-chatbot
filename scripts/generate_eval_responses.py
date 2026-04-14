"""
Generate Model Responses for Evaluation (CLI Edition)
=====================================================
Takes eval scenarios and generates therapist responses using different model configs.

Configs:
  - claude: Claude baseline — uses Claude CLI (Max subscription, no API cost)
  - base:   Base Gemma 2 2B IT (no fine-tuning) — runs on Colab
  - v1:     Fine-tuned v1 (95 examples) — runs on Colab
  - v2:     Fine-tuned v2 (363 examples) — runs on Colab
  - v2_rag: Fine-tuned v2 + RAG knowledge retrieval — runs locally

Run:
    python scripts/generate_eval_responses.py --config claude
    python scripts/generate_eval_responses.py --config claude --start 50   # resume from scenario 50
    python scripts/generate_eval_responses.py --config claude --delay 15   # 15s between calls

Input:  data/evaluation/eval_scenarios.jsonl
Output: data/evaluation/model_responses_claude.jsonl
"""

import json
import os
import sys
import subprocess
import time
import argparse
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_DIR = Path(__file__).parent.parent
SCENARIOS_FILE = PROJECT_DIR / "data" / "evaluation" / "eval_scenarios.jsonl"
OUTPUT_DIR = PROJECT_DIR / "data" / "evaluation"

SYSTEM_PROMPT = """You are a compassionate, skilled therapist specializing in Motivational Interviewing (MI) for alcohol-related concerns.

Your approach:
- Use OARS: Open questions, Affirmations, Reflections, Summaries
- Meet the client where they are — never confront or lecture
- Roll with resistance, don't fight it
- Evoke the client's own motivation for change
- Respect autonomy — the client decides if and when they change
- Reflect emotions and defensiveness back with empathy

Respond with a single, thoughtful therapist response (2-4 sentences). Do NOT include any labels, headers, or metadata — just the therapist's words."""


def load_scenarios() -> list[dict]:
    scenarios = []
    with open(SCENARIOS_FILE, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                scenarios.append(json.loads(line))
    return scenarios


def load_existing_responses(config_name: str) -> dict:
    """Load already-generated responses to support resuming."""
    output_file = OUTPUT_DIR / f"model_responses_{config_name}.jsonl"
    existing = {}
    if output_file.exists():
        with open(output_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    existing[item["scenario"]["id"]] = item
    return existing


def call_claude_cli(prompt: str, timeout: int = 120) -> str:
    """Call Claude CLI in non-interactive mode and return the response."""
    try:
        result = subprocess.run(
            ["claude.cmd", "--print"] if sys.platform == "win32" else ["claude", "--print"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"[CLI ERROR: {result.stderr.strip()[:200]}]"
    except subprocess.TimeoutExpired:
        return "[CLI TIMEOUT]"
    except Exception as e:
        return f"[CLI EXCEPTION: {str(e)[:200]}]"


def build_generation_prompt(scenario: dict) -> str:
    """Build a prompt for Claude CLI to generate a therapist response."""
    parts = [SYSTEM_PROMPT, "\n\n## Conversation so far:\n"]

    for msg in scenario.get("conversation_history", []):
        role = "Therapist" if msg["role"] == "assistant" else "Client"
        parts.append(f"{role}: {msg['content']}")

    parts.append(f"\nClient: {scenario['client_message']}")
    parts.append("\nNow respond as the therapist. Only output the therapist's response, nothing else:")

    return "\n".join(parts)


def generate_claude_responses(scenarios: list[dict], start: int = 0, delay: int = 10):
    """Generate responses using Claude CLI."""
    output_file = OUTPUT_DIR / f"model_responses_claude.jsonl"

    # Load existing to support resuming
    existing = load_existing_responses("claude")
    if existing:
        print(f"  Found {len(existing)} existing responses (will skip those)")

    total = len(scenarios)
    generated = 0
    skipped = 0
    failed = 0

    # Open in append mode
    with open(output_file, "a", encoding="utf-8") as f:
        for i, scenario in enumerate(scenarios):
            if i < start:
                continue

            # Skip if already generated
            if scenario["id"] in existing:
                skipped += 1
                continue

            prompt = build_generation_prompt(scenario)
            response = call_claude_cli(prompt)

            if response.startswith("[CLI"):
                print(f"  [{i+1}/{total}] FAILED: {scenario['id']} - {response[:80]}")
                failed += 1
                # Still save it so we can identify failures
                result = {
                    "scenario": scenario,
                    "model_response": response,
                    "config": "claude",
                }
            else:
                result = {
                    "scenario": scenario,
                    "model_response": response,
                    "config": "claude",
                }
                generated += 1

            f.write(json.dumps(result, ensure_ascii=False) + "\n")
            f.flush()  # Write immediately so progress is saved

            if (generated + failed) % 5 == 0:
                elapsed_per = delay + 2  # rough estimate
                remaining = total - i - 1 - skipped
                eta_min = (remaining * elapsed_per) / 60
                print(f"  [{i+1}/{total}] Generated: {generated} | Skipped: {skipped} | Failed: {failed} | ETA: {eta_min:.0f}min")

            # Delay between calls to avoid rate limits
            if i < total - 1:
                time.sleep(delay)

    print(f"\nDone!")
    print(f"  Generated: {generated}")
    print(f"  Skipped (already done): {skipped}")
    print(f"  Failed: {failed}")
    print(f"  Output: {output_file}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True,
                        choices=["claude", "base", "v1", "v2", "v2_rag"],
                        help="Model config to generate responses for")
    parser.add_argument("--start", type=int, default=0,
                        help="Start from scenario index (for resuming)")
    parser.add_argument("--delay", type=int, default=10,
                        help="Seconds between CLI calls (default: 10)")
    args = parser.parse_args()

    scenarios = load_scenarios()
    print(f"Loaded {len(scenarios)} evaluation scenarios")

    if args.config == "claude":
        print(f"\nGenerating Claude baseline responses via CLI...")
        print(f"  Delay: {args.delay}s between calls")
        print(f"  Start: scenario {args.start}")
        est_min = (len(scenarios) * (args.delay + 2)) / 60
        print(f"  Estimated time: ~{est_min:.0f} minutes\n")
        generate_claude_responses(scenarios, start=args.start, delay=args.delay)

    elif args.config in ("base", "v1", "v2"):
        print(f"\nGemma model responses must be generated on Colab (needs GPU).")
        print(f"Steps:")
        print(f"  1. Upload eval_scenarios.jsonl to Google Drive -> mi-therapy-capstone/data/")
        print(f"  2. Use the eval response generation cells in the Colab notebook")
        print(f"  3. Download model_responses_{args.config}.jsonl back to data/evaluation/")

    elif args.config == "v2_rag":
        print(f"\nv2+RAG responses need both the RAG pipeline and the fine-tuned model.")


if __name__ == "__main__":
    main()
