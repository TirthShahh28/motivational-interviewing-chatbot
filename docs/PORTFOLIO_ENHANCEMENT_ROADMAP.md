# Portfolio Enhancement Roadmap

## Transforming Capstone into a Backend/Data Engineering Showcase

### 🎯 Goal

Turn the "Emotion-Aware Chatbot" into a **production-grade system** that demonstrates:

- Backend API design and microservices
- Database modeling and optimization
- Data pipeline engineering
- Software engineering best practices
- DevOps and observability

---

## Phase 1: Backend Foundation (Weeks 4-6)

**Time: ~4 hours/week | Impact: HIGH**

### 1.1 FastAPI Backend

Replace Streamlit as the main interface (keep it as a demo client).

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry
│   ├── config.py            # Settings with Pydantic
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── endpoints/
│   │   │   │   ├── chat.py      # POST /chat, WebSocket /ws/chat
│   │   │   │   ├── sessions.py  # CRUD for sessions
│   │   │   │   ├── analytics.py # GET /analytics/emotions
│   │   │   │   └── health.py    # Health checks
│   │   │   └── dependencies.py
│   ├── core/
│   │   ├── security.py      # JWT, API keys
│   │   ├── middleware.py    # Rate limiting, CORS, logging
│   │   └── exceptions.py    # Custom exception handlers
│   ├── domain/
│   │   ├── models.py        # Pydantic domain models
│   │   ├── schemas.py       # Request/Response schemas
│   │   └── enums.py         # EmotionState, DefensivenessLevel
│   ├── services/
│   │   ├── inference_service.py
│   │   ├── conversation_service.py
│   │   ├── rag_service.py
│   │   └── safety_service.py
│   ├── repositories/
│   │   ├── base.py          # Abstract repository
│   │   ├── conversation_repo.py
│   │   ├── session_repo.py
│   │   └── analytics_repo.py
│   └── infrastructure/
│       ├── database.py      # SQLAlchemy setup
│       ├── redis.py         # Redis client
│       └── ollama.py        # LLM client wrapper
├── migrations/              # Alembic migrations
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── Dockerfile
└── pyproject.toml
```

### 1.2 Database Schema (PostgreSQL)

```sql
-- Core Tables
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) UNIQUE,  -- For OAuth
    created_at TIMESTAMP DEFAULT NOW(),
    settings JSONB DEFAULT '{}'
);

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    -- State inference results (for analytics)
    emotion VARCHAR(50),
    defensiveness VARCHAR(50),
    confidence FLOAT,

    -- Performance metrics
    inference_time_ms INT,
    response_time_ms INT
);

-- Analytics Tables (Star Schema for BI)
CREATE TABLE fact_conversations (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID,
    message_count INT,
    avg_response_time_ms FLOAT,
    dominant_emotion VARCHAR(50),
    max_defensiveness VARCHAR(50),
    crisis_detected BOOLEAN,
    session_duration_seconds INT,
    created_date DATE
);

CREATE TABLE dim_emotions (
    emotion VARCHAR(50) PRIMARY KEY,
    category VARCHAR(50),  -- 'positive', 'negative', 'neutral'
    suggested_approach TEXT
);

-- Indexes for performance
CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_messages_created ON messages(created_at);
CREATE INDEX idx_fact_date ON fact_conversations(created_date);
```

### 1.3 API Endpoints Design

| Method | Endpoint                         | Description                | Auth    |
| ------ | -------------------------------- | -------------------------- | ------- |
| POST   | `/api/v1/chat`                   | Send message, get response | API Key |
| WS     | `/api/v1/ws/chat/{session_id}`   | Real-time streaming        | Token   |
| POST   | `/api/v1/sessions`               | Create new session         | API Key |
| GET    | `/api/v1/sessions/{id}`          | Get session details        | API Key |
| GET    | `/api/v1/sessions/{id}/messages` | Get conversation history   | API Key |
| GET    | `/api/v1/analytics/emotions`     | Emotion distribution       | Admin   |
| GET    | `/api/v1/analytics/sessions`     | Session metrics            | Admin   |
| GET    | `/api/v1/health`                 | Health check               | None    |
| GET    | `/api/v1/health/ready`           | Readiness (DB, LLM)        | None    |

### Interview Talking Points After Phase 1:

- "I designed a RESTful API with proper versioning and OpenAPI documentation"
- "I implemented the repository pattern to decouple business logic from data access"
- "I used dependency injection for testability and modularity"
- "The database schema follows normalization principles with strategic denormalization for analytics"

---

## Phase 2: Production Hardening (Weeks 7-9)

**Time: ~4 hours/week | Impact: HIGH**

### 2.1 Caching Strategy (Redis)

```python
# Cache layers:
# 1. Session state cache (fast access to current conversation)
# 2. RAG embedding cache (avoid recomputing embeddings)
# 3. Response cache (for common questions - with TTL)

CACHE_KEYS = {
    "session": "session:{session_id}:state",      # TTL: 1 hour
    "embeddings": "rag:embedding:{hash}",          # TTL: 24 hours
    "response": "response:{message_hash}",         # TTL: 5 minutes
    "rate_limit": "ratelimit:{api_key}:{window}", # TTL: 1 minute
}
```

### 2.2 Async Processing (Celery + Redis)

```python
# Offload heavy operations:
@celery_app.task
def process_conversation_analytics(session_id: str):
    """Run after session ends - aggregate metrics"""
    pass

@celery_app.task
def update_knowledge_base(document_path: str):
    """Re-index RAG when knowledge base updates"""
    pass

@celery_app.task
def generate_daily_report():
    """Scheduled task for analytics aggregation"""
    pass
```

### 2.3 Authentication & Authorization

```python
# Multi-tier auth:
# 1. API Keys for service-to-service
# 2. JWT for user sessions
# 3. OAuth2 for admin dashboard

class AuthLevel(Enum):
    PUBLIC = "public"      # Health checks
    API_KEY = "api_key"    # Chat endpoints
    USER = "user"          # Session management
    ADMIN = "admin"        # Analytics, configuration
```

### 2.4 Rate Limiting

```python
# Sliding window rate limiter
RATE_LIMITS = {
    "chat": "10/minute",      # Prevent abuse
    "sessions": "5/minute",    # Session creation
    "analytics": "100/hour",   # Heavy queries
}
```

### Interview Talking Points After Phase 2:

- "I implemented a multi-layer caching strategy that reduced average response time by 40%"
- "Used Celery for async processing of analytics to keep the main API responsive"
- "Implemented sliding window rate limiting to prevent abuse while maintaining good UX"
- "The auth system supports multiple authentication methods for different use cases"

---

## Phase 3: Data Engineering (Weeks 10-12)

**Time: ~4 hours/week | Impact: VERY HIGH for Data Engineer roles**

### 3.1 Data Pipeline (Apache Airflow)

```
pipelines/
├── dags/
│   ├── daily_analytics.py       # Daily conversation aggregation
│   ├── weekly_report.py         # Weekly insights generation
│   ├── emotion_trends.py        # Emotion pattern analysis
│   └── data_quality_checks.py   # Great Expectations validations
├── plugins/
│   └── operators/
│       └── postgres_analytics.py
└── docker-compose.airflow.yml
```

### 3.2 Analytics DAG Example

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'tirth',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'daily_conversation_analytics',
    default_args=default_args,
    schedule_interval='0 2 * * *',  # 2 AM daily
    catchup=False,
) as dag:

    extract = PythonOperator(
        task_id='extract_conversations',
        python_callable=extract_daily_conversations,
    )

    transform = PythonOperator(
        task_id='compute_metrics',
        python_callable=compute_conversation_metrics,
    )

    load = PythonOperator(
        task_id='load_to_warehouse',
        python_callable=load_fact_table,
    )

    quality = PythonOperator(
        task_id='data_quality_check',
        python_callable=run_great_expectations,
    )

    extract >> transform >> load >> quality
```

### 3.3 Analytics Metrics to Track

| Metric                    | Type        | Business Value                     |
| ------------------------- | ----------- | ---------------------------------- |
| Emotion distribution      | Aggregate   | Understand user mental states      |
| Avg session length        | Time series | Engagement tracking                |
| Defensiveness progression | Sequence    | Measure conversation effectiveness |
| Crisis detection rate     | Rate        | Safety monitoring                  |
| Response time p50/p95/p99 | Latency     | Performance SLA                    |
| RAG retrieval accuracy    | Quality     | Knowledge base effectiveness       |

### 3.4 Data Quality (Great Expectations)

```python
# Expectations for conversation data:
expectations = [
    expect_column_values_to_not_be_null("session_id"),
    expect_column_values_to_be_in_set("emotion", VALID_EMOTIONS),
    expect_column_values_to_be_between("confidence", 0, 1),
    expect_table_row_count_to_be_between(min_value=100),  # Per day
]
```

### Interview Talking Points After Phase 3:

- "I built an ETL pipeline with Airflow that processes conversation data nightly"
- "Implemented a star schema optimized for analytical queries"
- "Used Great Expectations to ensure data quality with automated validation"
- "The pipeline generates insights like emotion trends and conversation effectiveness"

---

## Phase 4: Observability & DevOps (Weeks 13-14)

**Time: ~3 hours/week | Impact: MEDIUM-HIGH**

### 4.1 Docker Compose Setup

```yaml
# docker-compose.yml
services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - ollama
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379

  postgres:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  ollama:
    image: ollama/ollama
    volumes:
      - ollama_models:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  celery_worker:
    build: ./backend
    command: celery -A app.core.celery worker
    depends_on:
      - redis
      - postgres

  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
```

### 4.2 Monitoring Stack

```
monitoring/
├── prometheus.yml         # Scrape configs
├── alerting_rules.yml     # Alert definitions
└── grafana/
    └── dashboards/
        ├── api_performance.json
        ├── conversation_metrics.json
        └── system_health.json
```

### 4.3 Key Metrics to Monitor

```python
# Custom Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

chat_requests = Counter('chat_requests_total', 'Total chat requests', ['status'])
response_latency = Histogram('response_latency_seconds', 'Response latency')
active_sessions = Gauge('active_sessions', 'Currently active sessions')
emotion_detected = Counter('emotion_detected_total', 'Emotions detected', ['emotion'])
```

### 4.4 CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run linters
        run: |
          pip install ruff black mypy
          ruff check .
          black --check .
          mypy backend/

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          pip install -r requirements-dev.txt
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - name: Build and push Docker image
        run: |
          docker build -t emotion-chatbot:${{ github.sha }} .

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: echo "Deploy to Kubernetes/ECS/etc"
```

### Interview Talking Points After Phase 4:

- "Set up a complete observability stack with Prometheus and Grafana"
- "Created custom metrics for business KPIs alongside system metrics"
- "Implemented a CI/CD pipeline with automated testing and coverage reporting"
- "The system is fully containerized and can be deployed with a single command"

---

## Phase 5: Polish & Documentation (Week 15)

**Time: ~4 hours | Impact: HIGH for interviews**

### 5.1 Required Documentation

1. **README.md** - Project overview, quick start, architecture diagram
2. **ARCHITECTURE.md** - Deep dive into system design decisions
3. **API.md** - API documentation (auto-generated from OpenAPI)
4. **CONTRIBUTING.md** - Development setup, code style
5. **ADRs/** - Architecture Decision Records

### 5.2 Architecture Decision Records (ADRs)

```markdown
# ADR-001: Choice of FastAPI over Django

## Status

Accepted

## Context

Need a Python web framework for the API layer.

## Decision

Use FastAPI instead of Django REST Framework.

## Rationale

- Native async support for LLM streaming
- Automatic OpenAPI documentation
- Better performance for I/O-bound operations
- Type hints with Pydantic validation

## Consequences

- Need to use SQLAlchemy instead of Django ORM
- Team needs to learn FastAPI patterns
```

### 5.3 Portfolio Presentation Materials

- [ ] Architecture diagram (draw.io/Excalidraw)
- [ ] Demo video (2-3 minutes)
- [ ] Performance benchmarks
- [ ] Code coverage badge
- [ ] Live demo link (if hosted)

---

## Technology Stack Summary

| Category       | Technology           | Purpose                                |
| -------------- | -------------------- | -------------------------------------- |
| **API**        | FastAPI              | REST API with async support            |
| **Database**   | PostgreSQL 16        | Primary data store                     |
| **Cache**      | Redis 7              | Caching, rate limiting, sessions       |
| **Queue**      | Celery + Redis       | Async task processing                  |
| **LLM**        | Ollama (gemma3)      | Local inference                        |
| **Vector DB**  | pgvector             | RAG embeddings (avoid ChromaDB issues) |
| **Pipeline**   | Apache Airflow       | ETL orchestration                      |
| **Containers** | Docker Compose       | Local development                      |
| **Monitoring** | Prometheus + Grafana | Observability                          |
| **CI/CD**      | GitHub Actions       | Automated pipeline                     |
| **Testing**    | pytest + coverage    | Test automation                        |

---

## Quick Wins (Can Do This Week!)

1. **Add `/health` endpoint** - 30 minutes
2. **Add basic pytest tests** - 1 hour
3. **Create Dockerfile** - 30 minutes
4. **Add pre-commit hooks** (black, ruff) - 30 minutes
5. **Write README with architecture diagram** - 1 hour

These alone will make your GitHub repo look more professional immediately.

---

## Interview Story Framework

When discussing this project, use the **STAR method**:

**Situation**: "I was building an AI chatbot for my capstone that needed to detect emotions and adjust responses accordingly."

**Task**: "I wanted to make it production-ready to showcase backend engineering skills, not just ML/AI."

**Action**: "I architected a microservices-based system with FastAPI, PostgreSQL, Redis for caching, and Airflow for data pipelines. I implemented proper API design, authentication, and monitoring."

**Result**: "The system can handle X concurrent users, has 80%+ test coverage, and includes a complete observability stack. The data pipeline processes conversation analytics nightly and generates insights about user emotional patterns."

---

## Files Changed vs Created Summary

- Keep: `src/` (core logic) - refactor into services
- Keep: `knowledge_base/` - RAG content
- New: `backend/` - FastAPI application
- New: `pipelines/` - Airflow DAGs
- New: `monitoring/` - Prometheus/Grafana configs
- New: `docker-compose.yml` - Full stack
- New: `tests/` - Comprehensive test suite
- New: `.github/workflows/` - CI/CD

---

_This roadmap turns a good AI project into an exceptional engineering showcase._
