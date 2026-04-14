"""
Build RAG Contexts for V2+RAG Evaluation (Enhanced v2)
=======================================================
1. Builds ChromaDB from enriched knowledge_base/ (19 files, 335 KB)
2. Uses multi-query retrieval: semantic + state-aware + technique-aware
3. MMR (Maximal Marginal Relevance) for diverse, non-redundant chunks
4. Saves eval_scenarios_rag.jsonl with structured RAG context

Run:
    python scripts/build_rag_contexts.py
"""

import sys
import json
import shutil
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_DIR = Path(__file__).parent.parent
EVAL_SCENARIOS = PROJECT_DIR / "data" / "evaluation" / "eval_scenarios.jsonl"
OUTPUT_FILE    = PROJECT_DIR / "data" / "evaluation" / "eval_scenarios_rag.jsonl"
KNOWLEDGE_DIR  = PROJECT_DIR / "knowledge_base"
CHROMA_DIR     = PROJECT_DIR / "data" / "chroma_db"

# ── 1. Load scenarios ──────────────────────────────────────────────────────
print("Loading eval scenarios...")
scenarios = []
with open(EVAL_SCENARIOS, encoding='utf-8') as f:
    for line in f:
        if line.strip():
            scenarios.append(json.loads(line))
print(f"  Loaded {len(scenarios)} scenarios")

# ── 2. Build ChromaDB (always rebuild to pick up new files) ───────────────
print("\nInitializing RAG pipeline...")

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

print("  Loading embedding model (all-MiniLM-L6-v2)...")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# Always rebuild to include new knowledge base files
if CHROMA_DIR.exists():
    shutil.rmtree(CHROMA_DIR)
    print("  Cleared old ChromaDB")

print(f"  Building ChromaDB from {KNOWLEDGE_DIR}")
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Load all documents with source metadata
docs = []
for ext in ["*.md", "*.txt"]:
    for fpath in sorted(KNOWLEDGE_DIR.rglob(ext)):
        try:
            loader = TextLoader(str(fpath), encoding='utf-8')
            loaded = loader.load()
            # Add rich metadata
            category = fpath.parent.name if fpath.parent != KNOWLEDGE_DIR else "guidelines"
            for doc in loaded:
                doc.metadata['category'] = category
                doc.metadata['filename'] = fpath.name
            docs.extend(loaded)
        except Exception as e:
            print(f"  Warning: skipped {fpath.name}: {e}")

print(f"  Loaded {len(docs)} documents")

# Smart chunking: use example separators to keep exchanges intact
splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,        # slightly larger to keep full exchanges together
    chunk_overlap=80,      # more overlap for context continuity
    separators=[
        "\n---",           # example separators in our files
        "\n\n##",          # markdown headers
        "\n\n",            # paragraph breaks
        "\n",              # line breaks
        ". ",              # sentences
        " ",               # words
    ]
)
chunks = splitter.split_documents(docs)
print(f"  Split into {len(chunks)} chunks")

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=str(CHROMA_DIR)
)
print(f"  ChromaDB built and saved ({len(chunks)} chunks)")

# ── 3. Multi-strategy retrieval ───────────────────────────────────────────
print(f"\nRetrieving RAG contexts for {len(scenarios)} scenarios...")
print("  Strategy: 3 semantic queries + MMR diversity + 5 chunks per scenario")


def build_retrieval_queries(scenario: dict) -> list:
    """
    Build multiple retrieval queries to capture different aspects:
    1. Client message (semantic match to similar situations)
    2. State-aware query (emotion + defensiveness strategies)
    3. Technique-aware query (what MI technique fits)
    """
    queries = []

    client_msg = scenario['client_message']
    defensiveness = scenario.get('client_defensiveness', 'none')
    emotion = scenario.get('client_emotion', 'neutral')

    # Query 1: Direct semantic match — find similar client situations
    queries.append(f"Client: {client_msg}")

    # Query 2: State-aware — what strategies apply
    state_parts = []
    if defensiveness in ['high']:
        state_parts.append("handling high defensiveness denial resistance de-escalation amplified reflection")
    elif defensiveness in ['moderate']:
        state_parts.append("moderate resistance sustain talk double-sided reflection shifting focus")
    elif defensiveness in ['low', 'none']:
        state_parts.append("reinforcing change talk evoking motivation supporting change")

    if emotion in ['frustrated', 'angry']:
        state_parts.append("frustrated angry client validation de-escalation")
    elif emotion in ['sad', 'hopeless']:
        state_parts.append("sad hopeless client empathy building hope")
    elif emotion == 'anxious':
        state_parts.append("anxious worried client reassurance normalizing")
    elif emotion in ['contemplative', 'hopeful']:
        state_parts.append("contemplative client exploring ambivalence supporting change")

    if state_parts:
        queries.append(' '.join(state_parts))

    # Query 3: Technique exploration — what's the right MI move
    # Check for edge case indicators
    msg_lower = client_msg.lower()
    if any(w in msg_lower for w in ['kill', 'die', 'suicide', 'end it', 'hurt myself']):
        queries.append("crisis suicide self-harm safety protocol what to say")
    elif any(w in msg_lower for w in ['relapse', 'slipped', 'drank again', 'fell off']):
        queries.append("relapse sobriety compassionate response non-judgmental")
    elif any(w in msg_lower for w in ['not a problem', "don't have", 'everyone drinks', 'mind your own']):
        queries.append("denial minimization rolling with resistance avoid confrontation")
    elif any(w in msg_lower for w in ['want to change', 'ready', 'tired of', 'sick of']):
        queries.append("change talk motivation strengthening commitment preparation")
    else:
        queries.append(f"therapist reflection empathy response alcohol {emotion}")

    return queries


def retrieve_diverse(vectorstore, queries: list, k_total: int = 5) -> list:
    """
    Retrieve from multiple queries and deduplicate.
    Uses MMR for diversity within each query.
    Returns top k_total most relevant, non-redundant chunks.
    """
    all_docs = []
    seen_content = set()

    for query in queries:
        try:
            # MMR: fetch more, select diverse subset
            docs = vectorstore.max_marginal_relevance_search(
                query,
                k=3,
                fetch_k=10,
                lambda_mult=0.7  # balance relevance (1.0) vs diversity (0.0)
            )
            for doc in docs:
                # Deduplicate by content hash
                content_key = doc.page_content[:100].strip()
                if content_key not in seen_content:
                    seen_content.add(content_key)
                    all_docs.append(doc)
        except Exception:
            # Fallback to regular similarity search
            docs = vectorstore.similarity_search(query, k=3)
            for doc in docs:
                content_key = doc.page_content[:100].strip()
                if content_key not in seen_content:
                    seen_content.add(content_key)
                    all_docs.append(doc)

    return all_docs[:k_total]


enriched_scenarios = []
for i, scenario in enumerate(scenarios):
    queries = build_retrieval_queries(scenario)
    docs = retrieve_diverse(vectorstore, queries, k_total=5)

    rag_chunks = []
    for doc in docs:
        source = Path(doc.metadata.get('source', 'unknown')).name
        category = doc.metadata.get('category', 'unknown')
        rag_chunks.append({
            "source": source,
            "category": category,
            "content": doc.page_content.strip()
        })

    enriched = dict(scenario)
    enriched['rag_context'] = rag_chunks

    enriched_scenarios.append(enriched)

    if (i + 1) % 30 == 0:
        print(f"  [{i+1}/{len(scenarios)}] done")

print(f"  All {len(enriched_scenarios)} scenarios enriched")

# ── 4. Stats ──────────────────────────────────────────────────────────────
from collections import Counter
source_counts = Counter()
for s in enriched_scenarios:
    for c in s['rag_context']:
        source_counts[c['source']] += 1

print(f"\nRetrieval source distribution:")
for src, cnt in source_counts.most_common(10):
    print(f"  {src:45s}: {cnt}")

# ── 5. Save ───────────────────────────────────────────────────────────────
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for s in enriched_scenarios:
        f.write(json.dumps(s, ensure_ascii=False) + '\n')

print(f"\nSaved to: {OUTPUT_FILE}")
print(f"File size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
avg_chunks = sum(len(s['rag_context']) for s in enriched_scenarios) / len(enriched_scenarios)
print(f"Avg chunks per scenario: {avg_chunks:.1f}")

# Show diverse samples
print("\n" + "=" * 70)
print("SAMPLE RAG RETRIEVALS")
print("=" * 70)
for idx in [0, 80, 160]:
    s = enriched_scenarios[idx]
    print(f"\n{s['id']} | emotion={s.get('client_emotion','?')} | defense={s.get('client_defensiveness','?')}")
    print(f"  Client: {s['client_message'][:90]}...")
    for j, c in enumerate(s['rag_context']):
        print(f"  Chunk {j+1} [{c['source']}]: {c['content'][:100]}...")
