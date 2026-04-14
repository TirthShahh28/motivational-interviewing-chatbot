"""
Build Knowledge Base from AnnoMI Dataset
==========================================
Extracts high-quality therapist exchange pairs from AnnoMI and formats
them as retrieval documents organized by technique and situation.

Output: knowledge_base/annomi_examples/ — multiple .txt files
Run:    python scripts/build_annomi_knowledge_base.py
"""

import sys
import json
import pandas as pd
from pathlib import Path
from collections import defaultdict

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_DIR = Path(__file__).parent.parent
CSV_PATH    = PROJECT_DIR / "data" / "raw" / "annomi_full.csv"
OUTPUT_DIR  = PROJECT_DIR / "knowledge_base" / "annomi_examples"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 1. Load and filter ────────────────────────────────────────────────────
print("Loading AnnoMI dataset...")
df = pd.read_csv(CSV_PATH)
print(f"  Total rows: {len(df)}")

# Keep only high-quality, alcohol-related sessions
df_high = df[df['mi_quality'] == 'high'].copy()
print(f"  High-quality rows: {len(df_high)}")

# ── 2. Reconstruct client→therapist exchange pairs ────────────────────────
print("\nExtracting exchange pairs...")

pairs = []  # (client_msg, therapist_msg, technique, transcript_id)

transcripts = df_high.groupby('transcript_id')

for tid, group in transcripts:
    group = group.sort_values('utterance_id').reset_index(drop=True)

    for i in range(len(group) - 1):
        curr = group.iloc[i]
        nxt  = group.iloc[i + 1]

        # Pattern: client turn followed by therapist turn
        if curr['interlocutor'] == 'client' and nxt['interlocutor'] == 'therapist':
            client_text    = str(curr['utterance_text']).strip()
            therapist_text = str(nxt['utterance_text']).strip()
            technique      = str(nxt['main_therapist_behaviour']).strip()
            client_talk    = str(curr['client_talk_type']).strip() if pd.notna(curr['client_talk_type']) else 'unknown'

            # Filter out very short or NaN utterances
            if (len(client_text) < 15 or len(therapist_text) < 15 or
                client_text == 'nan' or therapist_text == 'nan'):
                continue

            pairs.append({
                'transcript_id': tid,
                'client_msg': client_text,
                'therapist_msg': therapist_text,
                'technique': technique,
                'client_talk_type': client_talk,
            })

print(f"  Extracted {len(pairs)} exchange pairs")

# Technique distribution
from collections import Counter
tech_counts = Counter(p['technique'] for p in pairs)
print(f"  Technique breakdown:")
for t, c in tech_counts.most_common():
    print(f"    {t:20s}: {c}")

# ── 3. Organize by technique and save as knowledge base files ─────────────
print("\nBuilding knowledge base files...")

TECHNIQUE_LABELS = {
    'reflection':      'Reflection (Empathic Listening)',
    'question':        'Open Question (Exploring)',
    'therapist_input': 'Therapist Input (Affirmation / Summary / Information)',
    'other':           'General MI Response',
}

# Group pairs by technique
by_technique = defaultdict(list)
for p in pairs:
    by_technique[p['technique']].append(p)

# Write one file per technique (cap at 80 examples each to avoid huge files)
MAX_PER_FILE = 80
files_written = []

for technique, examples in by_technique.items():
    if technique == 'nan' or not examples:
        continue

    label = TECHNIQUE_LABELS.get(technique, technique)
    filename = f"mi_examples_{technique}.txt"
    filepath = OUTPUT_DIR / filename

    # Sort by client message length (prefer medium-length, more informative ones)
    examples_sorted = sorted(examples, key=lambda x: abs(len(x['client_msg']) - 120))
    selected = examples_sorted[:MAX_PER_FILE]

    lines = [
        f"# MI Technique Examples: {label}",
        f"# Source: AnnoMI Dataset (High-Quality Sessions)",
        f"# These are real exchanges from expert Motivational Interviewing sessions.",
        "",
    ]

    for i, ex in enumerate(selected, 1):
        lines.append(f"--- Example {i} ---")
        lines.append(f"Client: {ex['client_msg']}")
        lines.append(f"Therapist ({label}): {ex['therapist_msg']}")
        lines.append("")

    filepath.write_text('\n'.join(lines), encoding='utf-8')
    files_written.append((filename, len(selected)))
    print(f"  Written: {filename} ({len(selected)} examples)")

# ── 4. Create special files for high-defensiveness / sustain talk ──────────
print("\nBuilding situation-specific files...")

# Sustain talk examples (client resisting change)
sustain_pairs = [p for p in pairs if 'sustain' in p['client_talk_type'].lower()]
if sustain_pairs:
    filepath = OUTPUT_DIR / "mi_examples_sustain_talk.txt"
    lines = [
        "# Handling Sustain Talk (Client Resisting Change)",
        "# Source: AnnoMI Dataset (High-Quality Sessions)",
        "# These examples show how expert MI therapists respond when clients",
        "# express resistance, ambivalence, or reasons NOT to change.",
        "",
    ]
    for i, ex in enumerate(sustain_pairs[:80], 1):
        lines.append(f"--- Example {i} ---")
        lines.append(f"Client (resisting): {ex['client_msg']}")
        lines.append(f"Therapist: {ex['therapist_msg']}")
        lines.append(f"Technique: {ex['technique']}")
        lines.append("")
    filepath.write_text('\n'.join(lines), encoding='utf-8')
    print(f"  Written: mi_examples_sustain_talk.txt ({min(len(sustain_pairs), 80)} examples)")

# Change talk examples (client showing motivation)
change_pairs = [p for p in pairs if 'change' in p['client_talk_type'].lower()]
if change_pairs:
    filepath = OUTPUT_DIR / "mi_examples_change_talk.txt"
    lines = [
        "# Reinforcing Change Talk (Client Showing Motivation)",
        "# Source: AnnoMI Dataset (High-Quality Sessions)",
        "# These examples show how expert MI therapists respond when clients",
        "# express desire, ability, reasons, or need to change.",
        "",
    ]
    for i, ex in enumerate(change_pairs[:80], 1):
        lines.append(f"--- Example {i} ---")
        lines.append(f"Client (motivated): {ex['client_msg']}")
        lines.append(f"Therapist: {ex['therapist_msg']}")
        lines.append(f"Technique: {ex['technique']}")
        lines.append("")
    filepath.write_text('\n'.join(lines), encoding='utf-8')
    print(f"  Written: mi_examples_change_talk.txt ({min(len(change_pairs), 80)} examples)")

# ── 5. Summary ─────────────────────────────────────────────────────────────
print(f"\nKnowledge base built at: {OUTPUT_DIR}")
total_examples = sum(c for _, c in files_written)
all_files = list(OUTPUT_DIR.glob('*.txt'))
total_size = sum(f.stat().st_size for f in all_files) / 1024
print(f"  Files: {len(all_files)}")
print(f"  Total examples: {total_examples + min(len(sustain_pairs),80) + min(len(change_pairs),80)}")
print(f"  Total size: {total_size:.1f} KB")
print(f"\nNext: run python scripts/build_rag_contexts.py to rebuild ChromaDB")
