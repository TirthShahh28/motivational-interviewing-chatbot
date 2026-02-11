# Emotion-Aware Conversational Chatbot for Alcohol Dialogues

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An intelligent conversational agent that uses real-time state inference to detect user emotion and defensiveness, providing empathetic, autonomy-respecting responses grounded in Motivational Interviewing (MI) principles.

---

## 🌿 Branch Strategy

| Branch         | Purpose                                       | Status            |
| -------------- | --------------------------------------------- | ----------------- |
| `main`         | Capstone presentation version (Streamlit MVP) | ✅ Stable         |
| `capstone-mvp` | Backup of simple MVP                          | ✅ Frozen         |
| `production`   | Full-stack production-grade version           | 🚧 In Development |

### Which branch should you use?

- **For capstone demo**: Use `main` branch
- **For portfolio showcase**: Use `production` branch (FastAPI + PostgreSQL + Redis + Airflow)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit UI (app.py)                  │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│               Conversation Manager                          │
│  (Orchestrates the full pipeline)                           │
└──────┬──────────────┬──────────────┬──────────────┬─────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Safety     │ │    State     │ │     RAG      │ │   Response   │
│   Guard      │ │  Inference   │ │   Pipeline   │ │  Generator   │
│              │ │              │ │              │ │              │
│ • Crisis     │ │ • Emotion    │ │ • ChromaDB   │ │ • Adaptive   │
│   detection  │ │   detection  │ │ • Semantic   │ │   prompts    │
│ • Medical    │ │ • Defensive- │ │   search     │ │ • MI-based   │
│   boundaries │ │   ness level │ │ • Knowledge  │ │   responses  │
│ • Logging    │ │ • JSON output│ │   retrieval  │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

## Quick Start

### Prerequisites

1. **Python 3.10+** installed
2. **Ollama** installed (for local LLM)

### Step 1: Set Up Environment

```bash
# Navigate to project
cd capstone-chatbot

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Set Up Ollama (Local LLM)

```bash
# Install Ollama from https://ollama.com/

# Pull Llama 3 model
ollama pull llama3

# Verify it's running
ollama run llama3 "Hello, how are you?"
```

### Step 3: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env if needed (defaults should work)
```

### Step 4: Run the Application

```bash
# Start the Streamlit app
streamlit run app.py
```

Open your browser to `http://localhost:8501`

## Project Structure

```
capstone-chatbot/
├── app.py                    # Streamlit UI
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── src/
│   ├── __init__.py
│   ├── config.py            # Configuration settings
│   ├── state_inference.py   # Emotion/defensiveness detection
│   ├── rag_pipeline.py      # Knowledge retrieval (RAG)
│   ├── response_generator.py # Adaptive response generation
│   ├── safety_layer.py      # Safety checks and logging
│   └── conversation_manager.py # Main orchestrator
├── knowledge_base/          # SME-provided guidelines
│   ├── mi_principles.md
│   ├── handling_resistance.md
│   ├── emotional_responses.md
│   └── harm_reduction.md
├── data/
│   └── chroma_db/          # Vector database (auto-created)
└── logs/                    # Conversation logs
```

## How It Works

### 1. State Inference

When a user sends a message, the system analyzes it for:

- **Emotional state**: neutral, frustrated, anxious, sad, angry, hopeful, contemplative
- **Defensiveness level**: none, low, moderate, high

### 2. Knowledge Retrieval

Based on the user's message AND inferred state, the system retrieves relevant guidelines from the knowledge base using semantic search.

### 3. Adaptive Response

The response generator creates replies that:

- Match the appropriate MI technique for the defensiveness level
- Acknowledge the emotional state
- Incorporate relevant expert knowledge
- Maintain empathy and support autonomy

### 4. Safety Layer

Every message is checked for:

- Crisis indicators (self-harm, suicidal ideation) → Provides resources
- Medical advice requests → Redirects to professionals
- Inappropriate bot output → Blocks and regenerates

## Configuration Options

Edit `src/config.py` to customize:

| Setting                | Default | Description                     |
| ---------------------- | ------- | ------------------------------- |
| `OLLAMA_MODEL`         | llama3  | Which Ollama model to use       |
| `CONTEXT_WINDOW_TURNS` | 5       | Conversation history to include |
| `TOP_K_RESULTS`        | 3       | RAG documents to retrieve       |
| `CHUNK_SIZE`           | 500     | Knowledge base chunk size       |

## Using OpenAI Instead of Ollama

1. Add to `.env`:

```
OPENAI_API_KEY=your_key_here
```

2. Update `requirements.txt`:

```
langchain-openai>=0.0.5
```

3. In `app.py`, change:

```python
create_conversation_manager(use_ollama=False)
```

## Adding to Knowledge Base

1. Add `.md` or `.txt` files to `knowledge_base/`
2. Delete `data/chroma_db/` folder
3. Restart the app (it will re-index automatically)

## Evaluation

The `logs/` folder contains:

- Session logs (JSONL format)
- Flagged interactions for expert review

Each log entry includes:

- User message
- Bot response
- Inferred state
- Safety level
- Retrieved knowledge

## Development Roadmap

- [x] Core conversation pipeline
- [x] State inference module
- [x] RAG with ChromaDB
- [x] Safety guardrails
- [x] Streamlit UI
- [ ] More comprehensive knowledge base (needs SME input)
- [ ] Evaluation metrics
- [ ] Response latency optimization
- [ ] Docker deployment

## License

Academic use only - Capstone Project
