"""Quick test: verify API key, Haiku response, and Sonnet scoring."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

from anthropic import Anthropic
client = Anthropic()

# Test 1: Haiku baseline generation
print("Test 1: Haiku baseline response...")
resp = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=300,
    system="You are a compassionate therapist specializing in Motivational Interviewing. Respond with 2-3 sentences.",
    messages=[
        {"role": "user", "content": "[Session begins. Client enters.]"},
        {"role": "assistant", "content": "Thanks for coming in today. What brings you here?"},
        {"role": "user", "content": "I dont even want to be here. My wife made me come. I dont have a drinking problem."},
    ],
)
haiku_response = resp.content[0].text
print(f"  Response: {haiku_response}")
print(f"  Tokens: input={resp.usage.input_tokens}, output={resp.usage.output_tokens}")
print()

# Test 2: Sonnet judge scoring
print("Test 2: Sonnet judge scoring...")
judge_prompt = (
    "Score this therapist response on 5 criteria (1-5 scale).\n\n"
    "Client (angry, high defensiveness): "
    "\"I dont even want to be here. My wife made me come. I dont have a drinking problem.\"\n\n"
    f"Therapist response: \"{haiku_response}\"\n\n"
    "Respond ONLY with valid JSON:\n"
    "{\n"
    '    "empathy": <1-5>,\n'
    '    "mi_technique_score": <1-5>,\n'
    '    "resistance_handling": <1-5>,\n'
    '    "autonomy_support": <1-5>,\n'
    '    "appropriateness": <1-5>,\n'
    '    "detected_technique": "<open_question|reflection|affirmation|summary|other>",\n'
    '    "overall_comment": "<1 sentence>"\n'
    "}"
)

resp2 = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=500,
    messages=[{"role": "user", "content": judge_prompt}],
)
print(f"  Scores: {resp2.content[0].text}")
print(f"  Tokens: input={resp2.usage.input_tokens}, output={resp2.usage.output_tokens}")
print()

# Test 3: Batch API access
print("Test 3: Batch API access...")
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

batch = client.messages.batches.create(
    requests=[
        Request(
            custom_id="test-001",
            params=MessageCreateParamsNonStreaming(
                model="claude-haiku-4-5-20251001",
                max_tokens=100,
                messages=[{"role": "user", "content": "Say hello in 5 words."}],
            ),
        )
    ]
)
print(f"  Batch ID: {batch.id}")
print(f"  Status: {batch.processing_status}")
print()

print("ALL 3 TESTS PASSED! Ready to run evaluation.")
print(f"  Haiku works (baseline generation)")
print(f"  Sonnet works (judge scoring)")
print(f"  Batch API works (50% discount)")
