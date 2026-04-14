"""
Synthetic MI Conversation Generator
====================================
Generates labeled motivational interviewing conversations for fine-tuning.

Uses Claude Code CLI (`claude -p`) with your Max subscription — no API cost.

Generates realistic therapist-client dialogues with per-utterance labels for:
  - client emotion (neutral, frustrated, anxious, sad, angry, hopeful, contemplative, hopeless)
  - client defensiveness (none, low, moderate, high)
  - therapist MI technique (open_question, affirmation, reflection, summary, therapist_input, other)
  - client talk type (change, sustain, neutral)

Output format: JSONL (one conversation per line)

Usage:
    python scripts/generate_synthetic_data.py --batch short --num 50
    python scripts/generate_synthetic_data.py --batch medium --num 50
    python scripts/generate_synthetic_data.py --batch long --num 50
    python scripts/generate_synthetic_data.py --batch mixed --num 50
    python scripts/generate_synthetic_data.py --num 1 --turns 10 --dry-run
"""

import argparse
import json
import random
import subprocess
import sys
import time
from pathlib import Path

# ============== CLIENT PROFILES (25 diverse profiles) ==============

CLIENT_PROFILES = [
    # --- HIGH DEFENSIVENESS STARTERS ---
    {
        "name": "young professional with DUI",
        "context": "A 28-year-old marketing professional who drinks heavily at social events and after work. Recently got a DUI. Feels embarrassed but insists it was a one-time mistake.",
        "arc": "high -> moderate (by end)",
        "gender": "female",
    },
    {
        "name": "college binge drinker",
        "context": "A 21-year-old college senior who binge drinks every weekend. Friends staged an intervention but the student sees it as normal college behavior.",
        "arc": "high -> high (resistant throughout)",
        "gender": "male",
    },
    {
        "name": "high-functioning executive",
        "context": "A 45-year-old CEO who drinks a bottle of scotch nightly but maintains stellar work performance. Believes they have everything under control. Partner disagrees.",
        "arc": "high -> moderate (cracks in denial)",
        "gender": "male",
    },
    {
        "name": "court-mandated angry client",
        "context": "A 38-year-old mandated by court to attend counseling after a second DUI. Furious about being forced to be here. Sees the system as unfair.",
        "arc": "high -> moderate (anger softens slightly)",
        "gender": "male",
    },
    {
        "name": "peer-pressured teenager",
        "context": "An 18-year-old referred by school counselor after being caught drinking at a school event. Feels singled out since 'literally everyone drinks'.",
        "arc": "high -> moderate (begins reflecting)",
        "gender": "female",
    },
    {
        "name": "defensive construction worker",
        "context": "A 42-year-old construction worker who drinks a six-pack every night. Referred by his doctor after abnormal liver tests. Thinks the doctor is overreacting.",
        "arc": "high -> moderate (health scare sinks in)",
        "gender": "male",
    },
    {
        "name": "socialite in denial",
        "context": "A 33-year-old social media influencer whose entire social life revolves around drinking. Multiple friends have expressed concern. Insists it's just her lifestyle.",
        "arc": "high -> high (maintains denial with charm)",
        "gender": "female",
    },
    {
        "name": "military veteran",
        "context": "A 36-year-old veteran who started heavy drinking after deployment. Views drinking as normal military culture. Wife threatened divorce.",
        "arc": "high -> moderate (family motivation emerges)",
        "gender": "male",
    },
    # --- MODERATE DEFENSIVENESS STARTERS ---
    {
        "name": "stressed single parent",
        "context": "A 40-year-old single parent who has been drinking a bottle of wine nightly to cope with the stress of raising two kids alone. Knows it's too much but feels trapped.",
        "arc": "moderate -> low (opening up)",
        "gender": "female",
    },
    {
        "name": "grieving widow",
        "context": "A 55-year-old who lost their spouse 8 months ago and has been drinking to numb the pain. Isolated from friends and family.",
        "arc": "moderate -> low (emotional breakthrough)",
        "gender": "female",
    },
    {
        "name": "nurse with burnout",
        "context": "A 32-year-old ER nurse who started drinking heavily during the pandemic. Feels guilty but says it's the only way to decompress after traumatic shifts.",
        "arc": "moderate -> low (acknowledges impact on work)",
        "gender": "female",
    },
    {
        "name": "recently divorced man",
        "context": "A 48-year-old who has been drinking heavily since his divorce 4 months ago. Alternates between anger at his ex and sadness about losing his family.",
        "arc": "moderate -> low (grief beneath the anger)",
        "gender": "male",
    },
    {
        "name": "college athlete",
        "context": "A 20-year-old star athlete whose performance has been slipping due to partying. Coach gave an ultimatum. Torn between team loyalty and social life.",
        "arc": "moderate -> low (values clarification)",
        "gender": "male",
    },
    {
        "name": "immigrant dealing with isolation",
        "context": "A 29-year-old who moved to a new country alone and started drinking to cope with loneliness and cultural adjustment. Has no local support system.",
        "arc": "moderate -> none (finds hope in connection)",
        "gender": "female",
    },
    {
        "name": "teacher hiding a problem",
        "context": "A 37-year-old middle school teacher who drinks every evening and occasionally comes to work hungover. A colleague noticed and expressed concern privately.",
        "arc": "moderate -> moderate (ambivalent throughout)",
        "gender": "male",
    },
    # --- LOW DEFENSIVENESS STARTERS ---
    {
        "name": "retired lonely person",
        "context": "A 65-year-old retiree who started drinking more since retirement due to loneliness and loss of purpose. Doctor flagged liver concerns at last checkup.",
        "arc": "low -> none (ready for change)",
        "gender": "male",
    },
    {
        "name": "relapsed after 3 years sober",
        "context": "A 50-year-old who was sober for 3 years but relapsed after a sudden job loss. Feels deep shame and hopelessness. Has been to AA before.",
        "arc": "low -> none (reconnecting with motivation)",
        "gender": "male",
    },
    {
        "name": "socially anxious drinker",
        "context": "A 26-year-old software engineer with severe social anxiety who uses alcohol as liquid courage at every social event. Knows it's a crutch but terrified of life without it.",
        "arc": "low -> none (exploring alternatives)",
        "gender": "female",
    },
    {
        "name": "new mother struggling",
        "context": "A 31-year-old new mother who has been drinking wine nightly since the baby was born to cope with postpartum stress. Partner is supportive but worried.",
        "arc": "low -> none (baby as motivation)",
        "gender": "female",
    },
    {
        "name": "grad student overwhelmed",
        "context": "A 24-year-old PhD student who has been drinking to manage thesis stress and imposter syndrome. Advisor noticed declining work quality.",
        "arc": "low -> none (academic goals as anchor)",
        "gender": "male",
    },
    {
        "name": "bartender questioning lifestyle",
        "context": "A 27-year-old bartender who drinks after every shift. Recently realized they can't remember the last sober day. Starting to question if this is normal.",
        "arc": "low -> none (growing awareness)",
        "gender": "male",
    },
    {
        "name": "artist with creative block",
        "context": "A 34-year-old artist who believes alcohol fuels creativity. Has been drinking daily for years. Recently noticed the art has gotten worse, not better.",
        "arc": "low -> none (reframing the myth)",
        "gender": "female",
    },
    # --- SPECIAL ARCS ---
    {
        "name": "teenager caught by parents",
        "context": "A 16-year-old whose parents found empty bottles hidden in their room. Brought to counseling against their will. Scared but trying to act tough.",
        "arc": "high -> low (facade crumbles, fear emerges)",
        "gender": "male",
    },
    {
        "name": "elderly person in chronic pain",
        "context": "A 72-year-old with chronic pain who has been mixing alcohol with pain medication. Family is terrified. Doesn't want to burden anyone.",
        "arc": "low -> none (accepting help)",
        "gender": "female",
    },
    {
        "name": "person with dual diagnosis",
        "context": "A 39-year-old diagnosed with depression who self-medicates with alcohol. Has tried therapy before and dropped out. Skeptical but willing to give it one more try.",
        "arc": "moderate -> low (therapy trust rebuilding)",
        "gender": "male",
    },
]

# ============== EMOTION TRAJECTORIES (15 diverse paths) ==============

EMOTION_TRAJECTORIES = [
    # Anger-dominant arcs
    ["angry", "angry", "frustrated", "contemplative", "contemplative"],
    ["angry", "frustrated", "frustrated", "anxious", "hopeful"],
    ["angry", "angry", "angry", "frustrated", "neutral"],
    # Sadness-dominant arcs
    ["sad", "sad", "hopeless", "sad", "hopeful"],
    ["sad", "hopeless", "hopeless", "contemplative", "hopeful"],
    ["sad", "sad", "anxious", "contemplative", "hopeful"],
    # Anxiety-dominant arcs
    ["anxious", "anxious", "frustrated", "contemplative", "hopeful"],
    ["anxious", "anxious", "sad", "contemplative", "hopeful"],
    ["anxious", "neutral", "anxious", "contemplative", "contemplative"],
    # Frustration-dominant arcs
    ["frustrated", "frustrated", "angry", "anxious", "contemplative"],
    ["frustrated", "neutral", "frustrated", "contemplative", "hopeful"],
    # Neutral/contemplative arcs (less emotional clients)
    ["neutral", "neutral", "contemplative", "contemplative", "hopeful"],
    ["neutral", "anxious", "anxious", "contemplative", "hopeful"],
    # Complex/mixed arcs
    ["hopeful", "anxious", "frustrated", "sad", "hopeful"],  # setback then recovery
    ["contemplative", "anxious", "sad", "contemplative", "hopeful"],  # deep dive
]

# ============== REFERRAL CONTEXTS (how client arrived) ==============

REFERRAL_CONTEXTS = [
    "Self-referred after a wake-up call moment.",
    "Referred by primary care physician after routine screening.",
    "Mandated by court following an alcohol-related offense.",
    "Encouraged by spouse/partner who threatened to leave.",
    "Brought by a concerned family member.",
    "Referred by employer after a workplace incident.",
    "Walked in after seeing information online.",
    "Referred by another therapist or counselor.",
    "Came in after a friend's intervention.",
    "Referred by school counselor or academic advisor.",
    "Showed up after being discharged from the ER.",
    "Came in after a health scare (abnormal lab results).",
]

# ============== SESSION CONTEXTS (where/when) ==============

SESSION_CONTEXTS = [
    "First-ever counseling session. The client has never spoken to anyone professionally about their drinking.",
    "Second session. Client was hesitant last time but came back, which is a positive sign.",
    "Follow-up session after a difficult week. Client had a setback.",
    "First session at a new clinic. Client has seen counselors before without success.",
    "Walk-in session at a community health center. Client is not sure what to expect.",
    "Telehealth session. Client is at home and slightly more comfortable than they'd be in person.",
    "Session at a college wellness center between classes. Client is rushed but showed up.",
    "Session at a VA clinic. Client is used to clinical settings but not therapy.",
    "First session after completing a detox program. Client is fragile but motivated.",
    "Check-in session. Client has been making progress but hit a rough patch.",
]

# ============== THERAPIST STYLES (subtle variation) ==============

THERAPIST_STYLES = [
    "The therapist has a warm, gentle approach. They speak softly and use lots of reflections. They are patient and never rush.",
    "The therapist is direct but compassionate. They ask clear questions and give honest reflections without sugarcoating.",
    "The therapist uses humor appropriately to build rapport. They are casual in tone but clinically skilled.",
    "The therapist is very structured and methodical. They use MI techniques deliberately and clearly.",
    "The therapist is deeply empathetic and emotional. They are not afraid of silence and sitting with pain.",
    "The therapist is experienced and calm. They've seen everything and nothing shocks them. This puts the client at ease.",
]

# ============== PROMPT TEMPLATE ==============

GENERATION_PROMPT = """You are an expert in Motivational Interviewing (MI) and clinical psychology. Generate a realistic MI counseling conversation about alcohol use.

## Client Profile
{client_profile}

## Session Context
{session_context}

## Referral
{referral_context}

## Therapist Style
{therapist_style}

## Conversation Requirements
- Generate exactly {num_turns} back-and-forth exchanges (therapist then client)
- The client's defensiveness should follow this arc: {defensiveness_arc}
- The emotional trajectory should roughly follow: {emotion_trajectory}
- The therapist MUST use proper MI techniques (OARS: Open questions, Affirmations, Reflections, Summaries)
- Make the dialogue feel natural and realistic, not scripted
- Include realistic speech patterns: hesitations ("um", "like", "I don't know"), incomplete thoughts, self-corrections, emotional outbursts, long pauses indicated by "..."
- The client should use language appropriate for their age, background, and emotional state
- Vary sentence length — some responses should be very short (1-5 words), others longer
- NOT every therapist turn needs to be a question — sometimes just reflect or affirm
- The conversation should feel like it could be a real recording transcription

## Output Format
Return a JSON array where each element is one utterance with these exact fields:

[
  {{
    "turn": 1,
    "speaker": "therapist",
    "text": "the utterance text",
    "mi_technique": "reflection|open_question|closed_question|affirmation|summary|therapist_input|other",
    "client_emotion": null,
    "client_defensiveness": null,
    "client_talk_type": null
  }},
  {{
    "turn": 1,
    "speaker": "client",
    "text": "the utterance text",
    "mi_technique": null,
    "client_emotion": "neutral|frustrated|anxious|sad|angry|hopeful|contemplative|hopeless",
    "client_defensiveness": "none|low|moderate|high",
    "client_talk_type": "change|sustain|neutral"
  }}
]

## Label Definitions

**client_emotion**: The primary emotion the client is expressing in this utterance.
- neutral: Calm, matter-of-fact, no strong emotion
- frustrated: Exasperated, feeling stuck or unheard
- anxious: Worried, fearful, uncertain
- sad: Grief, regret, low mood
- angry: Hostile, irritated, blaming
- hopeful: Interested in change, seeing possibility
- contemplative: Thoughtful, weighing options, introspective
- hopeless: Defeated, believing nothing will help

**client_defensiveness**:
- none: Open, receptive, willing to explore
- low: Slight hesitation or "yeah but" responses
- moderate: Clear minimization, rationalization, or deflection
- high: Strong denial, hostility, or refusal to engage

**client_talk_type** (from MI theory):
- change: Language favoring change ("I want to...", "Maybe I should...", "I'm worried about...")
- sustain: Language favoring status quo ("I don't have a problem", "It's not that bad", "I can handle it")
- neutral: Neither change nor sustain talk ("Okay", "I see", factual responses)

**mi_technique** (for therapist only):
- open_question: Cannot be answered yes/no, invites exploration
- closed_question: Yes/no or short factual answer expected
- reflection: Mirrors back what the client said (simple or complex)
- affirmation: Recognizes client's strengths, efforts, or values
- summary: Collects and presents back multiple points from the conversation
- therapist_input: Sharing information, psychoeducation, or advice (with permission)
- other: Greetings, transitions, small talk, logistics

Return ONLY the JSON array, no other text."""


# ============== BATCH CONFIGURATIONS ==============

BATCH_CONFIGS = {
    "short": {"turns": 6, "description": "Quick interactions, intake screenings (~800 tokens)"},
    "medium": {"turns": 10, "description": "Core sessions, fits in 2048 tokens"},
    "long": {"turns": 14, "description": "Longer sessions, near 2048 token limit"},
    "mixed": {"turns": None, "description": "Random mix of 6-12 turns (all fit 2048 tokens)"},
}


def build_prompt(profile: dict, emotions: list[str], num_turns: int) -> str:
    """Build a fully randomized generation prompt."""
    referral = random.choice(REFERRAL_CONTEXTS)
    session = random.choice(SESSION_CONTEXTS)
    style = random.choice(THERAPIST_STYLES)

    return GENERATION_PROMPT.format(
        client_profile=f"{profile['name'].title()} ({profile['gender']}, {profile['arc'].split(' ->')[0]} defensiveness): {profile['context']}",
        session_context=session,
        referral_context=referral,
        therapist_style=style,
        num_turns=num_turns,
        defensiveness_arc=profile["arc"],
        emotion_trajectory=" -> ".join(emotions),
    )


def _find_claude_cmd() -> str:
    """Find the claude executable path."""
    import shutil
    path = shutil.which("claude")
    if path:
        return path
    raise FileNotFoundError("'claude' CLI not found")


CLAUDE_CMD = None


def call_claude_cli(prompt: str, model: str = "sonnet") -> str | None:
    """Call Claude Code CLI in print mode and return the text response."""
    global CLAUDE_CMD
    if CLAUDE_CMD is None:
        CLAUDE_CMD = _find_claude_cmd()

    cmd = [
        CLAUDE_CMD,
        "-p",
        "--output-format", "json",
        "--model", model,
        "--max-turns", "1",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input=prompt,
            timeout=180,  # longer timeout for long conversations
        )

        if result.returncode != 0:
            print(f"  [ERROR] CLI returned {result.returncode}: {result.stderr[:200]}")
            return None

        output = json.loads(result.stdout)
        return output.get("result", "")

    except subprocess.TimeoutExpired:
        print("  [ERROR] Claude CLI timed out (180s)")
        return None
    except json.JSONDecodeError as e:
        print(f"  [ERROR] Failed to parse CLI output: {e}")
        return result.stdout if result.stdout else None


def fix_encoding(text: str) -> str:
    """Fix common mojibake from UTF-8 double-encoding."""
    # Em-dash: UTF-8 bytes 0xE2 0x80 0x94 decoded as Windows-1252
    text = text.replace("\u00e2\u20ac\u201d", "\u2014")  # em-dash
    text = text.replace("\u00e2\u20ac\u201c", "\u2013")  # en-dash
    text = text.replace("\u00e2\u20ac\u2122", "\u2019")  # right single quote
    text = text.replace("\u00e2\u20ac\u0153", "\u201c")  # left double quote
    text = text.replace("\u00e2\u20ac\u009d", "\u201d")  # right double quote
    return text


def parse_conversation_json(response_text: str) -> list[dict] | None:
    """Extract and parse the JSON conversation from Claude's response."""
    text = fix_encoding(response_text.strip())

    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    try:
        return json.loads(text.strip())
    except json.JSONDecodeError as e:
        print(f"  [WARN] JSON parse failed: {e}")
        print(f"  Preview: {text[:200]}...")
        return None


def validate_conversation(conversation: dict) -> list[str]:
    """Validate a generated conversation for quality."""
    issues = []
    utterances = conversation.get("utterances", [])

    if len(utterances) < 4:
        issues.append(f"Too few utterances: {len(utterances)}")

    valid_emotions = {"neutral", "frustrated", "anxious", "sad", "angry", "hopeful", "contemplative", "hopeless"}
    valid_defensiveness = {"none", "low", "moderate", "high"}
    valid_talk_types = {"change", "sustain", "neutral"}
    valid_techniques = {"open_question", "closed_question", "reflection", "affirmation", "summary", "therapist_input", "other"}

    for i, utt in enumerate(utterances):
        if utt.get("speaker") == "client":
            if utt.get("client_emotion") not in valid_emotions:
                issues.append(f"Utterance {i}: invalid emotion '{utt.get('client_emotion')}'")
            if utt.get("client_defensiveness") not in valid_defensiveness:
                issues.append(f"Utterance {i}: invalid defensiveness '{utt.get('client_defensiveness')}'")
            if utt.get("client_talk_type") not in valid_talk_types:
                issues.append(f"Utterance {i}: invalid talk_type '{utt.get('client_talk_type')}'")
        elif utt.get("speaker") == "therapist":
            if utt.get("mi_technique") not in valid_techniques:
                issues.append(f"Utterance {i}: invalid technique '{utt.get('mi_technique')}'")

    return issues


def get_turns_for_batch(batch_type: str) -> int:
    """Get the number of turns for a batch type."""
    if batch_type == "mixed":
        return random.choice([6, 8, 10, 12])
    return BATCH_CONFIGS[batch_type]["turns"]


def compute_unique_combos():
    """Print how many unique scenario combinations are possible."""
    combos = (
        len(CLIENT_PROFILES)
        * len(EMOTION_TRAJECTORIES)
        * len(REFERRAL_CONTEXTS)
        * len(SESSION_CONTEXTS)
        * len(THERAPIST_STYLES)
    )
    print(f"Unique scenario combinations: {combos:,}")
    print(f"  {len(CLIENT_PROFILES)} profiles x {len(EMOTION_TRAJECTORIES)} emotions x "
          f"{len(REFERRAL_CONTEXTS)} referrals x {len(SESSION_CONTEXTS)} sessions x "
          f"{len(THERAPIST_STYLES)} styles")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic MI conversations using Claude Code CLI")
    parser.add_argument("--num", type=int, default=50, help="Number of conversations to generate")
    parser.add_argument("--batch", type=str, default="medium", choices=["short", "medium", "long", "mixed"],
                        help="Batch type: short(8), medium(15), long(25), mixed(random)")
    parser.add_argument("--turns", type=int, default=None, help="Override turns per conversation")
    parser.add_argument("--model", type=str, default="sonnet", choices=["sonnet", "opus", "haiku"],
                        help="Claude model to use")
    parser.add_argument("--output", type=str, default=None, help="Output file path (auto-generated if not set)")
    parser.add_argument("--dry-run", action="store_true", help="Preview one prompt without calling CLI")
    parser.add_argument("--stats", action="store_true", help="Show diversity statistics and exit")
    args = parser.parse_args()

    if args.stats:
        compute_unique_combos()
        return

    # Verify claude CLI
    try:
        global CLAUDE_CMD
        CLAUDE_CMD = _find_claude_cmd()
        print(f"Claude CLI: {CLAUDE_CMD}")
    except FileNotFoundError:
        print("ERROR: 'claude' CLI not found. Make sure Claude Code is installed.")
        sys.exit(1)

    # Auto-generate output path
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"data/synthetic/batch_{args.batch}_{timestamp}.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    batch_desc = BATCH_CONFIGS[args.batch]["description"]
    print(f"Batch: {args.batch} ({batch_desc})")
    print(f"Conversations: {args.num} | Model: {args.model}")
    print(f"Output: {output_path}")
    print(f"Cost: $0 (using Claude Code Max subscription)")
    compute_unique_combos()
    print()

    generated = 0
    failed = 0
    total_utterances = 0

    with open(output_path, "a", encoding="utf-8") as f:
        for i in range(args.num):
            profile = random.choice(CLIENT_PROFILES)
            emotions = random.choice(EMOTION_TRAJECTORIES)
            num_turns = args.turns if args.turns else get_turns_for_batch(args.batch)

            print(f"[{i+1}/{args.num}] {profile['name']} | {profile['arc']} | {num_turns} turns")

            prompt = build_prompt(profile, emotions, num_turns)

            if args.dry_run:
                print("=" * 60)
                print(prompt)
                print("=" * 60)
                return

            response_text = call_claude_cli(prompt, model=args.model)
            if response_text is None:
                failed += 1
                continue

            utterances = parse_conversation_json(response_text)
            if utterances is None:
                failed += 1
                continue

            conversation = {
                "id": f"synthetic_{int(time.time())}_{random.randint(1000, 9999)}",
                "source": f"synthetic_claude_{args.model}",
                "batch_type": args.batch,
                "client_profile": profile["name"],
                "client_context": profile["context"],
                "client_gender": profile["gender"],
                "defensiveness_arc": profile["arc"],
                "emotion_trajectory": emotions,
                "num_turns": num_turns,
                "utterances": utterances,
            }

            issues = validate_conversation(conversation)
            if issues:
                print(f"  [WARN] {issues[:3]}")

            f.write(json.dumps(conversation, ensure_ascii=False) + "\n")
            f.flush()
            generated += 1
            total_utterances += len(utterances)
            print(f"  OK — {len(utterances)} utterances (total: {total_utterances})")

            if i < args.num - 1:
                time.sleep(0.5)  # minimal delay between CLI calls

    print()
    print("=" * 50)
    print(f"DONE! Generated: {generated} | Failed: {failed}")
    print(f"Total utterances: {total_utterances}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
