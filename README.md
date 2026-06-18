<div align="center">

# 🎙️ Sarvam Talent Discovery Engine

**Multilingual AI-powered hiring platform for Indian companies**

*Candidates speak in any Indian language. AI evaluates. HR decides.*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Sarvam AI](https://img.shields.io/badge/Sarvam_AI-Powered-FF6B35?style=for-the-badge)](https://sarvam.ai)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br/>

```
A Hindi speaker and a Tamil speaker walk into the same job interview.
The AI evaluates them on equal footing.
```

</div>

---

## ✨ What Makes This Different

| Traditional Hiring | Sarvam Talent Discovery |
|---|---|
| English-only screening | 🌍 Any Indian language |
| Manual resume review | 🤖 AI competency scoring |
| Gut-feel shortlisting | 📊 Weighted, explainable scores |
| Static job forms | 🎙️ Conversational voice interviews |
| HR listens to every call | ⚡ AI-generated audio summaries |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────┐    ┌──────────────────────────────────┐
│   Candidate Portal (port 5173)  │    │   HR Dashboard   (port 5174)     │
│   React + Vite                  │    │   React + Vite                   │
└──────────────┬──────────────────┘    └──────────────┬───────────────────┘
               │                                       │
               └──────────────────┬────────────────────┘
                                  │  REST API
                                  ▼
              ┌───────────────────────────────────────┐
              │        FastAPI Backend  :8000          │
              │                                       │
              │  /auth   /jobs   /candidates           │
              │  /screening  /evaluations              │
              │  /dashboard  /analytics                │
              └────┬──────────────────┬───────────────┘
                   │                  │
          ┌────────▼──────┐  ┌────────▼────────────────┐
          │  PostgreSQL   │  │   Sarvam AI APIs         │
          │  :5432        │  │   • Speech-to-Text       │
          │               │  │   • Text-to-Speech       │
          │  5 tables     │  │   • STT + Translate      │
          └───────────────┘  │   • Translate            │
                             └─────────────────────────┘
          ┌───────────────┐
          │  Redis  :6379 │  ← Background task queue (Celery)
          └───────────────┘
```

---

## 🎯 The Candidate Journey

```
 APPLY         SCREEN              AI EVALUATES           HR DECIDES
   │               │                    │                      │
   ▼               ▼                    ▼                      ▼
┌─────┐    ┌───────────────┐    ┌──────────────────┐    ┌──────────┐
│Form │───▶│ Voice Intro   │───▶│ Competency Score │───▶│ Kanban   │
│     │    │ (any language)│    │ • Technical      │    │ Pipeline │
│     │    │               │    │ • Problem Solving│    │          │
│     │    │ Follow-up Q&A │    │ • Ownership      │    │ Shortlist│
│     │    │ (AI questions)│    │ • Curiosity      │    │ Offer    │
└─────┘    └───────────────┘    │ • Shipping Speed │    │ Reject   │
                                │ • Multilingual   │    └──────────┘
                                └──────────────────┘
```

---

## 🗂️ Project Structure

<details>
<summary><b>📁 Click to expand full directory tree</b></summary>

```
sarvam-talent-discovery/
│
├── 🐍 backend/                    FastAPI Python application
│   ├── main.py                    App entrypoint + route registration
│   ├── config.py                  Settings (reads from .env)
│   ├── requirements.txt           Python dependencies
│   ├── .env.example               ← Copy this to .env and fill in secrets
│   │
│   ├── core/                      Shared internals
│   │   ├── models.py              SQLAlchemy ORM table definitions
│   │   ├── schemas.py             Pydantic request/response models
│   │   ├── database.py            DB engine + session factory
│   │   └── security.py            bcrypt + JWT tokens
│   │
│   ├── api/routes/                HTTP route handlers (34 endpoints)
│   │   ├── auth.py                /auth — register, login, me
│   │   ├── jobs.py                /jobs — CRUD job postings
│   │   ├── candidates.py          /candidates — apply, list, status
│   │   ├── screening.py           /screening — voice session lifecycle
│   │   ├── evaluations.py         /evaluations — competency scores
│   │   ├── dashboard.py           /dashboard — HR pipeline view
│   │   └── analytics.py           /analytics — funnel + drop-off
│   │
│   └── services/                  Business logic layer
│       ├── sarvam/
│       │   └── sarvam_client.py   Sarvam AI wrapper (STT/TTS/Translate)
│       ├── storage/               S3 audio + resume uploads [Phase 2]
│       ├── pipeline/              AI evaluation orchestrator [Phase 2]
│       └── background/            Celery async tasks [Phase 2]
│
├── ⚛️  frontend/                   Candidate-facing portal [Phase 3]
├── 📊 dashboard/                  HR dashboard UI [Phase 3]
│
├── 🤖 ai/
│   ├── prompts/                   LLM prompt templates [Phase 4]
│   ├── notebooks/                 Experiments & analysis
│   └── evals/                     Prompt evaluation scripts
│
├── 🐳 docker-compose.yml           Postgres + Redis services
└── 🏗️  infra/                      Infrastructure config
```

</details>

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker Desktop
- Git

### 1. Clone & Setup

```bash
git clone https://github.com/karthikj5453/sarvam_talent_discovery.git
cd sarvam-talent-discovery
```

### 2. Configure Environment

```bash
cd backend
cp .env.example .env
# Edit .env with your credentials (see Environment Variables below)
```

### 3. Start Infrastructure

```bash
# From project root
docker compose up -d postgres redis
```

### 4. Install Dependencies & Run

```powershell
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload
```

### 5. Explore the API

```
http://localhost:8000/docs  ← Interactive Swagger UI
http://localhost:8000/redoc ← ReDoc documentation
```

---

## 🔑 Environment Variables

<details>
<summary><b>📋 Full .env reference</b></summary>

```env
# ─── Database ─────────────────────────────────────────────────
DATABASE_URL=postgresql://postgres:password@localhost:5432/sarvam_talent

# ─── Redis ────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379

# ─── Sarvam AI ── Get your key at sarvam.ai ──────────────────
SARVAM_API_KEY=sk_your_key_here
SARVAM_BASE_URL=https://api.sarvam.ai

# ─── JWT ──────────────────────────────────────────────────────
# Generate: openssl rand -hex 32
SECRET_KEY=change_me_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ─── AWS S3 (audio + resume storage) ─────────────────────────
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_BUCKET_NAME=sarvam-talent-audio
AWS_REGION=ap-south-1

# ─── App ──────────────────────────────────────────────────────
APP_ENV=development
DEBUG=true
CORS_ORIGINS=["http://localhost:5173","http://localhost:5174"]
```

</details>

---

## 📡 API Reference

<details>
<summary><b>🔐 Authentication</b></summary>

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/auth/register` | Create HR account | ❌ |
| `POST` | `/auth/login` | Get JWT token | ❌ |
| `GET`  | `/auth/me` | Current user info | ✅ |

```bash
# Login example
curl -X POST http://localhost:8000/auth/login \
  -d "username=hr@company.com&password=secret"

# Use token in subsequent requests
curl -H "Authorization: Bearer <token>" http://localhost:8000/jobs/
```

</details>

<details>
<summary><b>💼 Jobs</b></summary>

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET`    | `/jobs/` | List all active jobs | ✅ |
| `POST`   | `/jobs/` | Create a job posting | ✅ |
| `GET`    | `/jobs/{id}` | Get job details | ✅ |
| `PATCH`  | `/jobs/{id}` | Update job | ✅ |
| `DELETE` | `/jobs/{id}` | Soft-delete job | ✅ |

```json
// POST /jobs/ body example
{
  "title": "ML Engineer",
  "department": "AI",
  "location": "Bangalore",
  "required_skills": ["Python", "LangGraph", "RAG"],
  "competency_weights": {
    "technical_depth": 0.30,
    "first_principles": 0.25,
    "shipping_velocity": 0.20,
    "ownership_signals": 0.10,
    "curiosity_depth": 0.10,
    "multilingual_fluency": 0.05
  }
}
```

</details>

<details>
<summary><b>👤 Candidates</b></summary>

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET`   | `/candidates/` | List candidates (filterable) | ✅ |
| `POST`  | `/candidates/public/apply` | Candidate applies (public) | ❌ |
| `GET`   | `/candidates/{id}` | Candidate + latest score | ✅ |
| `PATCH` | `/candidates/{id}/status` | Move pipeline stage | ✅ |

**Pipeline stages:** `applied → screened → shortlisted → interviewing → offered → rejected`

</details>

<details>
<summary><b>🎙️ Screening</b></summary>

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/screening/start` | Begin a screening session | ❌ |
| `GET`  | `/screening/{session_id}` | Get session state | ❌ |
| `POST` | `/screening/upload-resume` | Record resume URL | ❌ |
| `POST` | `/screening/upload-intro` | Save intro transcript | ❌ |
| `POST` | `/screening/upload-answer` | Save answer transcript | ❌ |
| `POST` | `/screening/complete` | Finalize + trigger evaluation | ❌ |

</details>

<details>
<summary><b>📊 Dashboard & Analytics</b></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard/pipeline` | Candidate counts per stage |
| `GET` | `/dashboard/candidates` | Candidates with scores |
| `GET` | `/dashboard/jobs/{id}/top-candidates` | Top-N ranked candidates |
| `GET` | `/analytics/funnel` | Funnel view (all stages) |
| `GET` | `/analytics/drop-off` | Drop-off rates between stages |
| `POST`| `/analytics/event` | Record a tracking event |

</details>

---

## 🧠 Competency Framework

Every candidate is scored across **6 dimensions** (0–10 each), weighted per job:

| Dimension | What It Measures |
|---|---|
| 🔬 **Technical Depth** | Depth of technical knowledge demonstrated |
| 🧩 **First Principles** | Ability to reason from fundamentals |
| 🚀 **Shipping Velocity** | Track record of delivering working software |
| 🏆 **Ownership Signals** | Evidence of taking initiative and accountability |
| 🔍 **Curiosity Depth** | Genuine intellectual curiosity and learning drive |
| 🗣️ **Multilingual Fluency** | Communication clarity across languages |

**Weighted total score formula:**
```
total = Σ (score_i × weight_i)   where Σ weights = 1.0
```

---

## 🌐 Supported Indian Languages (Sarvam AI)

| Code | Language | TTS Speaker |
|------|----------|-------------|
| `hi-IN` | Hindi | Meera |
| `ta-IN` | Tamil | Arjun |
| `te-IN` | Telugu | Pavithra |
| `kn-IN` | Kannada | Maitreyi |
| `ml-IN` | Malayalam | Laleh |
| `bn-IN` | Bengali | Riya |
| `gu-IN` | Gujarati | Manisha |
| `mr-IN` | Marathi | Sachin |
| `pa-IN` | Punjabi | Amol |
| `en-IN` | English (India) | Meera |

---

## 🗓️ Roadmap

- [x] **Phase 1** — Backend API (all 34 endpoints with real DB logic)
- [x] **Phase 1** — Sarvam AI client (STT, TTS, Translate)
- [x] **Phase 1** — Auth, Docker Compose, .gitignore
- [x] **Phase 2a** — Sarvam STT wired into screening routes (auto-transcribe on upload)
- [x] **Phase 2b** — S3 + local-fallback storage service for audio + resumes
- [x] **Phase 2c** — LLM evaluation pipeline (Gemini scoring + heuristic fallback)
- [x] **Phase 2d** — Celery background task worker (ASYNC_EVAL=true to enable)
- [x] **Phase 2e** — Resume PDF text extraction (PyMuPDF → feeds AI evaluator)
- [x] **Phase 3** — Candidate portal UI (React + Vite, port 5173)
- [x] **Phase 3** — HR dashboard UI (React + Vite, port 5174)
- [x] **Phase 4** — LLM prompt engineering (competency scorer + follow-up Q generator)
- [x] **Phase 4** — GitHub Actions CI/CD (pytest + frontend build checks)
- [x] **Phase 4** — Production Docker (multi-stage Dockerfile + docker-compose prod profile)
- [ ] **Phase 5** — Production deployment (cloud hosting, domain, SSL)
- [ ] **Phase 5** — HR notification emails (SendGrid/SMTP on shortlisting)

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **API Framework** | FastAPI 0.111 |
| **ORM** | SQLAlchemy 2.0 |
| **Database** | PostgreSQL 16 (JSONB for flexible fields) |
| **Auth** | JWT (python-jose) + bcrypt (passlib) |
| **HTTP Client** | httpx (async) |
| **AI APIs** | Sarvam AI (STT, TTS, Translate) |
| **Storage** | AWS S3 (boto3) |
| **Queue** | Celery + Redis |
| **PDF Parsing** | PyMuPDF |
| **Validation** | Pydantic v2 |
| **Testing** | pytest |
| **Containers** | Docker + Docker Compose |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Copy `.env.example` → `.env` and fill in credentials
4. Run `docker compose up -d` to start DB + Redis
5. Make your changes and run tests: `pytest backend/tests/`
6. Push and open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ using [Sarvam AI](https://sarvam.ai) • [FastAPI](https://fastapi.tiangolo.com) • [PostgreSQL](https://postgresql.org)

*Breaking language barriers in Indian hiring, one voice at a time.*

</div>
