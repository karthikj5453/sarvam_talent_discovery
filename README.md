<div align="center">

# 🎙️ Sarvam Talent Discovery Engine (Enterprise Edition)

**Multilingual AI-powered hiring platform for Indian companies**

*Candidates speak in any Indian language. AI evaluates. HR decides.*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
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
| English-only screening | 🌍 **Any Indian language** supported |
| Generic LeetCode questions | 🐙 **GitHub Hyper-Personalization** via AI |
| Browser tabs unguarded | 🕵️ **Anti-Cheat Proctoring Engine** |
| HR listens to every call | ⚡ **AI-generated audio summaries** |
| Web forms for application | 💬 **WhatsApp Application Flow** |

---

## 🚀 Enterprise Features

We’ve pushed the platform beyond a simple prototype, integrating advanced features required by modern enterprise HR teams:

### 1. 🕵️ Anti-Cheat & Proctoring Engine
To maintain interview integrity, the platform actively monitors the candidate's environment:
- **Tab Tracking:** Utilizes the `visibilitychange` API to track if a candidate leaves the interview tab (e.g., to use ChatGPT).
- **Copy-Paste Detection:** For technical roles, pasting large blocks of code into the Monaco Sandbox flags an alert.
- **HR Visibility:** Recruiters see a bold red "Proctoring Alert" on the dashboard if cheating thresholds are crossed.

### 2. 🐙 GitHub Hyper-Personalization
Candidates can submit their GitHub URL. At runtime, the backend fetches their public repositories and injects them into the **Gemini 2.0 Flash** prompt. The AI then dynamically generates follow-up questions about the code they have *actually written*.

### 3. 💻 Engineering Sandbox
When an Engineering/Developer role is selected, the platform seamlessly displays an integrated **Monaco Code Editor**, allowing candidates to write and explain code in real-time while the AI assesses them.

### 4. 🧠 Emotional Intelligence (EQ) Scoring
Using sentiment analysis applied to the candidate's voice transcript, the AI generates an "EQ Score" to measure candidate confidence and emotional intelligence during the interview.

### 5. 📑 1-Click PDF Dossiers
HR can instantly export a candidate's full profile into a beautiful PDF dossier (powered by `jsPDF` and `html2canvas`), complete with the Executive Summary, Competency Radar Charts, and Q&A transcripts.

### 6. 💬 WhatsApp Integration Ready
Includes a pre-built webhook router (`/api/routes/whatsapp.py`) ready to connect with Twilio or Meta WhatsApp APIs, allowing candidates to apply directly via WhatsApp messages.

### 7. 🌓 Professional Theme Engine
System-wide Light and Dark mode toggle ensuring accessibility compliance for enterprise environments.

---

## 🏗️ System Architecture

```mermaid
graph TD
    CP[Candidate Portal :5173] --> API[FastAPI Backend :8000]
    HR[HR Dashboard :5174] --> API
    API --> DB[(PostgreSQL :5432)]
    API --> Redis[(Redis :6379)]
    Redis --> Worker[Celery Background Task]
    API --> Sarvam[Sarvam AI APIs]
    API --> Gemini[Google Gemini 2.0]
    API --> GitHub[GitHub API]
```

---

## 🎯 The Candidate Pipeline Workflow

```
 APPLY           SCREEN                  AI EVALUATES                HR DECIDES
   │                │                         │                           │
   ▼                ▼                         ▼                           ▼
┌──────┐    ┌───────────────┐         ┌──────────────────┐         ┌──────────┐
│ Form │───▶│ Voice Intro   │────────▶│ Competency Score │────────▶│ Kanban   │
│  or  │    │ (any language)│         │ • Technical      │         │ Pipeline │
│  WA  │    │               │         │ • Problem Solving│         │          │
└──────┘    │ Follow-up Q&A │         │ • Ownership      │         │ Shortlist│
            │ (AI + GitHub) │         │ • Curiosity      │         │ Offer    │
            └───────────────┘         │ • EQ Score       │         │ Reject   │
                                      └──────────────────┘         └──────────┘
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
│   ├── core/                      Shared internals (Models, Schemas, DB)
│   ├── api/routes/                HTTP route handlers (Auth, Jobs, Candidates)
│   │   ├── screening.py           Orchestrates voice sessions
│   │   └── whatsapp.py            WhatsApp Webhook endpoint
│   └── services/                  Business logic layer
│       ├── sarvam/                Sarvam AI wrappers
│       ├── llm/                   Gemini context and generation
│       └── background/            Celery async tasks
│
├── ⚛️  frontend/                   React Candidate Portal (Port 5173)
├── 📊 dashboard/                  React HR Dashboard (Port 5174)
├── 🤖 ai/                         Notebooks and Prompt Evals
├── 🐋 docker-compose.yml           Production infrastructure
└── 🌐 nginx/                      Reverse proxy configuration
```

</details>

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker Desktop
- API Keys: Sarvam AI & Google Gemini

### 1. Clone & Setup

```bash
git clone https://github.com/karthikj5453/sarvam_talent_discovery.git
cd sarvam-talent-discovery
```

### 2. Configure Environment

```bash
cd backend
cp .env.example .env
# Insert your SARVAM_API_KEY and GEMINI_API_KEY
```

### 3. Start Infrastructure (Production Profile)

```bash
# Start Postgres, Redis, Backend, Celery, Nginx, and both Frontends
docker compose --profile prod up -d --build
```

### 4. Explore the Ecosystem

- **Candidate Portal:** `http://localhost:5173/`
- **HR Dashboard:** `http://localhost:5174/`
- **Swagger API Docs:** `http://localhost:8000/docs`

---

## 🔑 Environment Variables

<details>
<summary><b>📋 Full .env reference</b></summary>

```env
# ─── Database & Cache
DATABASE_URL=postgresql://postgres:password@localhost:5432/sarvam_talent
REDIS_URL=redis://localhost:6379

# ─── AI Providers
SARVAM_API_KEY=sk_your_key_here
GEMINI_API_KEY=your_gemini_key

# ─── Security
SECRET_KEY=change_me_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ─── App Configuration
APP_ENV=development
ASYNC_EVAL=false # Set true to use Celery for async evaluations
```

</details>

---

## 🧠 Competency Framework & Scoring

Every candidate is scored across **7 dimensions** (0–10 each), weighted dynamically per job requirement:

| Dimension | What It Measures |
|---|---|
| 🔬 **Technical Depth** | Depth of technical knowledge demonstrated |
| 🧩 **First Principles** | Ability to reason from fundamentals |
| 🚀 **Shipping Velocity** | Track record of delivering working software |
| 🏆 **Ownership Signals** | Evidence of taking initiative and accountability |
| 🔍 **Curiosity Depth** | Genuine intellectual curiosity and learning drive |
| 🗣️ **Multilingual Fluency** | Communication clarity across languages |
| ❤️ **Emotional Intelligence** | Sentiment, confidence, and empathy (EQ Score) |

---

## 🌐 Supported Indian Languages (Powered by Sarvam AI)

| Code | Language | TTS Speaker | Code | Language | TTS Speaker |
|------|----------|-------------|------|----------|-------------|
| `hi-IN` | Hindi | Meera | `bn-IN` | Bengali | Riya |
| `ta-IN` | Tamil | Arjun | `gu-IN` | Gujarati | Manisha |
| `te-IN` | Telugu | Pavithra | `mr-IN` | Marathi | Sachin |
| `kn-IN` | Kannada | Maitreyi | `pa-IN` | Punjabi | Amol |
| `ml-IN` | Malayalam | Laleh | `en-IN` | English (India) | Meera |

---

## ⚙️ CI/CD Pipelines & Workflows

The project utilizes GitHub Actions for Continuous Integration.
- **Backend Checks:** Linting (`flake8`), unit tests (`pytest`), and DB schema validation.
- **Frontend Checks:** `npm run build` validation for both the Candidate Portal and HR Dashboard.
- **Docker Validation:** Ensures `docker-compose --profile prod build` completes successfully before merging.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **API Framework** | FastAPI 0.111 |
| **Frontend** | React + Vite + Recharts + Monaco Editor |
| **ORM** | SQLAlchemy 2.0 |
| **Database** | PostgreSQL 16 (JSONB for flexible fields) |
| **Auth** | JWT (python-jose) + bcrypt (passlib) |
| **AI Generation** | Google Gemini 2.0 Flash |
| **AI Speech** | Sarvam AI (STT, TTS, Translate) |
| **Queue** | Celery + Redis |
| **PDF Parsing** | PyMuPDF |
| **Containers** | Docker + Docker Compose + Nginx |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ using [Sarvam AI](https://sarvam.ai) • [FastAPI](https://fastapi.tiangolo.com) • [Google Gemini](https://ai.google.dev/)

*Breaking language barriers in Indian hiring, one voice at a time.*

</div>
