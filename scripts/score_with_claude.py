"""
Score Model Responses with Claude-as-Judge (CLI Edition)
========================================================
Takes model-generated responses and scores them on 5 MI criteria using Claude CLI.
No API key or credits needed — uses your Max subscription.

Run:
    python scripts/score_with_claude.py --config claude
    python scripts/score_with_claude.py --config v2
    python scripts/score_with_claude.py --config v2 --delay 15        # 15s between calls
    python scripts/score_with_claude.py --compare                      # compare all scored configs

Input:  data/evaluation/model_responses_{config}.jsonl
Output: data/evaluation/results/scores_{config}.jsonl
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
RESPONSES_DIR = PROJECT_DIR / "data" / "evaluation"
RESULTS_DIR = PROJECT_DIR / "data" / "evaluation" / "results"

JUDGE_PROMPT = """You are an expert Motivational Interviewing (MI) evaluator. Score a therapist's response to a client in an alcohol-related counseling session.

## Context
Client's emotional state: {emotion}
Client's defensiveness level: {defensiveness}

## Conversation History
{history}

## Client's Message
"{client_message}"

## Therapist's Response (to evaluate)
"{model_response}"

{reference_section}

## Scoring (1-5 each)

1. Empathy: Does it validate feelings, not dismiss them?
2. MI Technique: Does it correctly use OARS (Open questions, Affirmations, Reflections, Summaries)?
3. Resistance Handling: Does it roll with resistance or confront/lecture?
4. Autonomy Support: Does it respect client's right to choose?
5. Contextual Appropriateness: Is it fitting for this client's emotion/defensiveness level?

Also identify the MI technique used: open_question, reflection, affirmation, summary, therapist_input, or other.

Respond ONLY with valid JSON, no other text:
{{"empathy": <1-5>, "mi_technique_score": <1-5>, "resistance_handling": <1-5>, "autonomy_support": <1-5>, "appropriateness": <1-5>, "detected_technique": "<technique>", "overall_comment": "<1 sentence>"}}"""


def format_history(history: list[dict]) -> str:
    if not history:
        return "No prior conversation."
    formatted = []
    for msg in history[-6:]:
        role = "Therapist" if msg["role"] == "assistant" else "Client"
        formatted.append(f"{role}: {msg['content']}")
    return "\n".join(formatted)


def call_claude_cli(prompt: str, timeout: int = 120) -> str:
    """Call Claude CLI in non-interactive mode."""
    try:
        result = subprocess.run(
            ["claude.cmd", "--print", "--model", "claude-sonnet-4-20250514"] if sys.platform == "win32" else ["claude", "--print", "--model", "claude-sonnet-4-20250514"],
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


def parse_scores(response_text: str) -> dict:
    """Parse JSON scores from Claude's response."""
    text = response_text.strip()

    # Handle markdown code blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    # Try to find JSON object in the response
    text = text.strip()
    if not text.startswith("{"):
        # Find first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end + 1]

    try:
        scores = json.loads(text)
        # Validate required fields
        required = ["empathy", "mi_technique_score", "resistance_handling",
                     "autonomy_support", "appropriateness"]
        for field in required:
            if field not in scores:
                scores[field] = 0
        return scores
    except json.JSONDecodeError:
        return {
            "empathy": 0, "mi_technique_score": 0,
            "resistance_handling": 0, "autonomy_support": 0,
            "appropriateness": 0, "detected_technique": "parse_error",
            "overall_comment": f"JSON parse failed: {response_text[:150]}",
        }


def load_responses(config_name: str) -> list[dict]:
    responses_file = RESPONSES_DIR / f"model_responses_{config_name}.jsonl"
    if not responses_file.exists():
        print(f"No responses file: {responses_file}")
        return []
    responses = []
    with open(responses_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                responses.append(json.loads(line))
    return responses


def load_existing_scores(config_name: str) -> dict:
    """Load already-scored results to support resuming."""
    score_file = RESULTS_DIR / f"scores_{config_name}.jsonl"
    existing = {}
    if score_file.exists():
        with open(score_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    existing[item["id"]] = item
    return existing


def score_config(config_name: str, delay: int = 10):
    """Score all responses for a given model config using Claude CLI."""
    responses = load_responses(config_name)
    if not responses:
        print(f"No responses found for config: {config_name}")
        return []

    # Load existing scores for resuming
    existing = load_existing_scores(config_name)
    if existing:
        print(f"  Found {len(existing)} existing scores (will skip those)")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = RESULTS_DIR / f"scores_{config_name}.jsonl"

    total = len(responses)
    scored = 0
    skipped = 0
    failed = 0

    with open(output_file, "a", encoding="utf-8") as f:
        for i, item in enumerate(responses):
            scenario = item["scenario"]
            model_response = item["model_response"]

            # Skip already scored
            if scenario["id"] in existing:
                skipped += 1
                continue

            # Skip failed generations
            if model_response.startswith("[CLI") or model_response == "[GENERATION FAILED]":
                skipped += 1
                continue

            # Build judge prompt
            history_str = format_history(scenario.get("conversation_history", []))

            reference_section = ""
            if scenario.get("reference_response"):
                ref_technique = scenario.get("reference_technique", "unknown")
                reference_section = (
                    f"## Reference (Real Therapist Response)\n"
                    f"A real therapist responded with ({ref_technique}):\n"
                    f'"{scenario["reference_response"]}"\n'
                    f"The model doesn't need to match this exactly."
                )

            prompt = JUDGE_PROMPT.format(
                emotion=scenario.get("client_emotion", "unknown"),
                defensiveness=scenario.get("client_defensiveness", "unknown"),
                history=history_str,
                client_message=scenario["client_message"],
                model_response=model_response,
                reference_section=reference_section,
            )

            # Call Claude CLI
            response_text = call_claude_cli(prompt)

            if response_text.startswith("[CLI"):
                print(f"  [{i+1}/{total}] CLI FAILED: {scenario['id']}")
                failed += 1
                continue

            scores = parse_scores(response_text)

            result = {
                "id": scenario["id"],
                "source": scenario["source"],
                "config": config_name,
                "client_emotion": scenario.get("client_emotion"),
                "client_defensiveness": scenario.get("client_defensiveness"),
                "client_talk_type": scenario.get("client_talk_type"),
                "model_response": model_response,
                "reference_response": scenario.get("reference_response"),
                "reference_technique": scenario.get("reference_technique"),
                "scores": scores,
            }

            f.write(json.dumps(result, ensure_ascii=False) + "\n")
            f.flush()
            scored += 1

            if scored % 5 == 0:
                remaining = total - i - 1 - skipped
                eta_min = (remaining * (delay + 3)) / 60
                # Calculate running average
                print(f"  [{i+1}/{total}] Scored: {scored} | Skipped: {skipped} | Failed: {failed} | ETA: {eta_min:.0f}min")

            time.sleep(delay)

    print(f"\nScoring complete for '{config_name}'!")
    print(f"  Scored: {scored}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed: {failed}")

    # Load all scores and print summary
    all_scores = load_existing_scores(config_name)
    if all_scores:
        print_summary(list(all_scores.values()), config_name)

    return list(all_scores.values())


def print_summary(results: list[dict], config_name: str):
    """Print scoring summary."""
    valid = [r for r in results if r["scores"].get("empathy", 0) > 0]

    if not valid:
        print(f"\nNo valid scores for {config_name}")
        return

    criteria = ["empathy", "mi_technique_score", "resistance_handling",
                "autonomy_support", "appropriateness"]

    print(f"\n{'=' * 60}")
    print(f"  SCORES: {config_name} ({len(valid)} scenarios)")
    print(f"{'=' * 60}")

    for c in criteria:
        scores_list = [r["scores"][c] for r in valid]
        avg = sum(scores_list) / len(scores_list)
        print(f"  {c:25s}: {avg:.2f} / 5.0")

    # Overall
    all_scores = []
    for r in valid:
        total = sum(r["scores"][c] for c in criteria)
        all_scores.append(total / 5)
    overall = sum(all_scores) / len(all_scores)
    print(f"  {'OVERALL':25s}: {overall:.2f} / 5.0")

    # Technique distribution
    techniques = [r["scores"].get("detected_technique", "unknown") for r in valid]
    tech_counts = {}
    for t in techniques:
        tech_counts[t] = tech_counts.get(t, 0) + 1
    print(f"\n  Technique distribution:")
    for t, count in sorted(tech_counts.items(), key=lambda x: -x[1]):
        print(f"    {t:20s}: {count} ({100*count/len(valid):.0f}%)")

    # AnnoMI technique match
    annomi_results = [r for r in valid if r.get("reference_technique")]
    if annomi_results:
        matches = sum(
            1 for r in annomi_results
            if r["scores"].get("detected_technique") == r["reference_technique"]
        )
        print(f"\n  AnnoMI technique match: {matches}/{len(annomi_results)} "
              f"({100*matches/len(annomi_results):.0f}%)")

    # By defensiveness level
    print(f"\n  Scores by defensiveness:")
    for level in ["high", "moderate", "low", "none"]:
        subset = [r for r in valid if r.get("client_defensiveness") == level]
        if subset:
            avg = sum(
                sum(r["scores"][c] for c in criteria) / 5
                for r in subset
            ) / len(subset)
            print(f"    {level:10s}: {avg:.2f} / 5.0  (n={len(subset)})")

    # By source
    print(f"\n  Scores by data source:")
    for source in ["annomi", "synthetic_eval", "edge_case"]:
        subset = [r for r in valid if r.get("source") == source]
        if subset:
            avg = sum(
                sum(r["scores"][c] for c in criteria) / 5
                for r in subset
            ) / len(subset)
            print(f"    {source:15s}: {avg:.2f} / 5.0  (n={len(subset)})")

    print(f"{'=' * 60}")


def compare_all_configs():
    """Load all saved scores and print comparison table."""
    configs = ["claude", "base", "v1", "v2", "v2_rag"]
    all_results = {}

    for config in configs:
        score_file = RESULTS_DIR / f"scores_{config}.jsonl"
        if score_file.exists():
            results = []
            with open(score_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        results.append(json.loads(line))
            valid = [r for r in results if r["scores"].get("empathy", 0) > 0]
            if valid:
                all_results[config] = valid

    if len(all_results) < 2:
        print("Need at least 2 scored configs to compare.")
        print(f"Found: {list(all_results.keys())}")
        return

    criteria = ["empathy", "mi_technique_score", "resistance_handling",
                "autonomy_support", "appropriateness"]

    print(f"\n{'=' * 70}")
    print(f"  CROSS-CONFIG COMPARISON")
    print(f"{'=' * 70}")

    header = f"  {'Criterion':25s}" + "".join(f" {c:>8s}" for c in all_results.keys())
    print(header)
    print("  " + "-" * (25 + 9 * len(all_results)))

    for crit in criteria:
        row = f"  {crit:25s}"
        for config, results in all_results.items():
            avg = sum(r["scores"][crit] for r in results) / len(results)
            row += f" {avg:8.2f}"
        print(row)

    row = f"  {'OVERALL':25s}"
    for config, results in all_results.items():
        avg = sum(
            sum(r["scores"][c] for c in criteria) / 5
            for r in results
        ) / len(results)
        row += f" {avg:8.2f}"
    print("  " + "-" * (25 + 9 * len(all_results)))
    print(row)

    print(f"{'=' * 70}")


def main():
    parser = argparse.ArgumentParser(description="Score model responses with Claude-as-judge (CLI)")
    parser.add_argument("--config", type=str,
                        help="Config to score: claude, base, v1, v2, v2_rag")
    parser.add_argument("--delay", type=int, default=10,
                        help="Seconds between CLI calls (default: 10)")
    parser.add_argument("--compare", action="store_true",
                        help="Compare all scored configs")
    args = parser.parse_args()

    if args.compare:
        compare_all_configs()
        return

    if not args.config:
        parser.print_help()
        return

    score_config(args.config, delay=args.delay)


if __name__ == "__main__":
    main()
