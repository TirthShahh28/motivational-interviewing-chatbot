"""Quick test: 1 scenario through generate + score pipeline via CLI."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent

# Load first scenario
with open(PROJECT_DIR / "data" / "evaluation" / "eval_scenarios.jsonl", encoding="utf-8") as f:
    scenario = json.loads(f.readline())

print(f"Scenario: {scenario['id']}")
print(f"Source: {scenario['source']}")
print(f"Client: {scenario['client_message'][:100]}...")
print()

# Step 1: Generate therapist response
print("=" * 50)
print("STEP 1: Generating therapist response via CLI...")
print("=" * 50)

gen_prompt = (
    "You are a compassionate therapist specializing in Motivational Interviewing.\n"
    "Respond with 2-3 sentences as the therapist. No labels, no headers, just the therapist's words.\n\n"
)
for msg in scenario.get("conversation_history", []):
    role = "Therapist" if msg["role"] == "assistant" else "Client"
    gen_prompt += f"{role}: {msg['content']}\n"
gen_prompt += f"Client: {scenario['client_message']}\n"
gen_prompt += "\nTherapist:"

result = subprocess.run(
    ["claude.cmd", "--print"],
    input=gen_prompt,
    capture_output=True, text=True, timeout=120,
    encoding="utf-8", errors="replace",
)
therapist_response = result.stdout.strip()
print(f"\nTherapist response: {therapist_response}")
print()

# Step 2: Score the response
print("=" * 50)
print("STEP 2: Scoring response via CLI (Claude-as-judge)...")
print("=" * 50)

score_prompt = (
    "You are an expert MI evaluator. Score this therapist response.\n\n"
    f"Client ({scenario.get('client_emotion', 'unknown')}, "
    f"defensiveness:{scenario.get('client_defensiveness', 'unknown')}): "
    f"\"{scenario['client_message']}\"\n\n"
    f"Therapist response: \"{therapist_response}\"\n\n"
    "Score 1-5 on each criterion. Respond ONLY with JSON:\n"
    '{"empathy": <1-5>, "mi_technique_score": <1-5>, "resistance_handling": <1-5>, '
    '"autonomy_support": <1-5>, "appropriateness": <1-5>, '
    '"detected_technique": "<reflection|open_question|affirmation|summary|other>", '
    '"overall_comment": "<1 sentence>"}'
)

result2 = subprocess.run(
    ["claude.cmd", "--print"],
    input=score_prompt,
    capture_output=True, text=True, timeout=120,
    encoding="utf-8", errors="replace",
)
score_text = result2.stdout.strip()
print(f"\nRaw scores: {score_text}")

# Parse
try:
    if "```json" in score_text:
        score_text = score_text.split("```json")[1].split("```")[0]
    elif "```" in score_text:
        score_text = score_text.split("```")[1].split("```")[0]
    if not score_text.strip().startswith("{"):
        start = score_text.find("{")
        end = score_text.rfind("}")
        if start != -1 and end != -1:
            score_text = score_text[start:end + 1]
    scores = json.loads(score_text.strip())
    print(f"\nParsed scores:")
    for k, v in scores.items():
        print(f"  {k}: {v}")
    print(f"\nTEST PASSED! CLI pipeline works.")
except Exception as e:
    print(f"\nJSON parse failed: {e}")
    print(f"Raw output was: {result2.stdout[:300]}")
