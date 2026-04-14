"""Run evaluation on 20 scenarios only — test run to check usage."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import subprocess
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
SCENARIOS_FILE = PROJECT_DIR / "data" / "evaluation" / "eval_scenarios_test10.jsonl"
OUTPUT_GEN = PROJECT_DIR / "data" / "evaluation" / "model_responses_claude_test10.jsonl"
OUTPUT_SCORES = PROJECT_DIR / "data" / "evaluation" / "results" / "scores_claude_test10.jsonl"

DELAY = 10  # seconds between calls

SYSTEM_PROMPT = """You are a compassionate, skilled therapist specializing in Motivational Interviewing (MI) for alcohol-related concerns.
Use OARS: Open questions, Affirmations, Reflections, Summaries.
Roll with resistance, never confront or lecture. Respect autonomy.
Respond with a single, thoughtful therapist response (2-4 sentences). Just the therapist's words, nothing else."""

JUDGE_PROMPT = """You are an expert MI evaluator. Score this therapist response.

Client ({emotion}, defensiveness:{defensiveness}): "{client_message}"

Therapist response: "{model_response}"

{reference_section}

Score 1-5 on each. Respond ONLY with JSON, no other text:
{{"empathy": <1-5>, "mi_technique_score": <1-5>, "resistance_handling": <1-5>, "autonomy_support": <1-5>, "appropriateness": <1-5>, "detected_technique": "<open_question|reflection|affirmation|summary|therapist_input|other>", "overall_comment": "<1 sentence>"}}"""


def call_cli(prompt, timeout=120):
    try:
        r = subprocess.run(
            ["claude.cmd", "--print"],
            input=prompt, capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", errors="replace",
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except:
        return None


def parse_scores(text):
    if not text:
        return None
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    text = text.strip()
    if not text.startswith("{"):
        s, e = text.find("{"), text.rfind("}")
        if s != -1 and e != -1:
            text = text[s:e+1]
    try:
        return json.loads(text)
    except:
        return None


def main():
    # Load scenarios
    scenarios = []
    with open(SCENARIOS_FILE, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                scenarios.append(json.loads(line))

    print(f"TEST RUN: {len(scenarios)} scenarios")
    print(f"Delay: {DELAY}s between calls")
    print(f"Estimated time: ~{len(scenarios) * (DELAY + 3) * 2 / 60:.0f} minutes")
    print()

    # Phase 1: Generate responses
    print("=" * 50)
    print("PHASE 1: Generating therapist responses")
    print("=" * 50)

    responses = []
    for i, s in enumerate(scenarios):
        prompt = SYSTEM_PROMPT + "\n\n"
        for msg in s.get("conversation_history", []):
            role = "Therapist" if msg["role"] == "assistant" else "Client"
            prompt += f"{role}: {msg['content']}\n"
        prompt += f"Client: {s['client_message']}\nTherapist:"

        resp = call_cli(prompt)
        if resp:
            responses.append({"scenario": s, "model_response": resp, "config": "claude"})
            print(f"  [{i+1}/{len(scenarios)}] OK - {s['id'][:40]}")
        else:
            print(f"  [{i+1}/{len(scenarios)}] FAILED - {s['id'][:40]}")

        if i < len(scenarios) - 1:
            time.sleep(DELAY)

    # Save responses
    OUTPUT_GEN.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_GEN, "w", encoding="utf-8") as f:
        for r in responses:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nGenerated: {len(responses)}/{len(scenarios)}")

    # Phase 2: Score responses
    print()
    print("=" * 50)
    print("PHASE 2: Scoring responses")
    print("=" * 50)

    results = []
    for i, item in enumerate(responses):
        s = item["scenario"]
        ref = ""
        if s.get("reference_response"):
            ref = f'Reference ({s.get("reference_technique","unknown")}): "{s["reference_response"]}"'

        prompt = JUDGE_PROMPT.format(
            emotion=s.get("client_emotion", "unknown"),
            defensiveness=s.get("client_defensiveness", "unknown"),
            client_message=s["client_message"][:500],
            model_response=item["model_response"],
            reference_section=ref,
        )

        raw = call_cli(prompt)
        scores = parse_scores(raw)

        if scores:
            results.append({
                "id": s["id"], "source": s["source"], "config": "claude",
                "client_emotion": s.get("client_emotion"),
                "client_defensiveness": s.get("client_defensiveness"),
                "scores": scores,
            })
            total = sum(scores.get(c, 0) for c in ["empathy", "mi_technique_score", "resistance_handling", "autonomy_support", "appropriateness"])
            print(f"  [{i+1}/{len(responses)}] {total}/25 - {s['id'][:40]}")
        else:
            print(f"  [{i+1}/{len(responses)}] PARSE FAILED - {s['id'][:40]}")

        if i < len(responses) - 1:
            time.sleep(DELAY)

    # Save scores
    OUTPUT_SCORES.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_SCORES, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Summary
    valid = [r for r in results if r["scores"].get("empathy", 0) > 0]
    if valid:
        criteria = ["empathy", "mi_technique_score", "resistance_handling", "autonomy_support", "appropriateness"]
        print(f"\n{'=' * 50}")
        print(f"  TEST RESULTS ({len(valid)} scenarios)")
        print(f"{'=' * 50}")
        for c in criteria:
            vals = [r["scores"].get(c, 0) for r in valid]
            avg = sum(vals) / len(vals) if vals else 0
            print(f"  {c:25s}: {avg:.2f} / 5.0")
        overall = sum(sum(r["scores"].get(c, 0) for c in criteria)/5 for r in valid) / len(valid)
        print(f"  {'OVERALL':25s}: {overall:.2f} / 5.0")
        print(f"{'=' * 50}")
    print(f"\nDone! Check your usage at claude.ai/settings")


if __name__ == "__main__":
    main()
