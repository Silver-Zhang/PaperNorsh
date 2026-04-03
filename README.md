# PaperNosh 📄

> Your personal research paper delivery service.

PaperNosh is a personalized academic literature delivery platform for researchers. Stop manually searching large databases — define your research interests, keywords, preferred sources and delivery preferences, and let PaperNosh discover, rank, and deliver the papers that matter to you every day.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development (Docker Compose)](#local-development-docker-compose)
  - [Manual Setup](#manual-setup)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Configuration](#configuration)
- [Running Tests](#running-tests)
- [Roadmap](#roadmap)

---

## Features

- **Multi-source ingestion** — fetches papers from arXiv, OpenAlex, and Crossref via their public APIs
- **Personalized ranking** — transparent, explainable scoring based on keywords, authors, sources, and journals
- **Daily digest** — web dashboard and optional email newsletter, delivered at your preferred time
- **Paper interactions** — save, ignore, or mark papers as highly relevant; feedback loops into future rankings
- **Graceful AI summaries** — generates concise summaries via OpenAI when configured; falls back to abstract truncation
- **Cross-source deduplication** — DOI, arXiv ID, and title-hash deduplication prevents duplicate paper cards
- **Modular source architecture** — new sources can be added by implementing a single abstract base class

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11 |
| Database | PostgreSQL 16 |
| Task scheduler | APScheduler |
| Cache / Queue | Redis |
| Auth | JWT (email + password) |
| Email | aiosmtplib (SMTP) |
| Deployment | Docker Compose |

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                        Browser                           │
│                    Next.js Frontend                      │
│         (Landing, Auth, Dashboard, Settings)             │
└───────────────────────┬──────────────────────────────────┘
                        │ REST API (JSON)
                        ▼
┌──────────────────────────────────────────────────────────┐
│                   FastAPI Backend                        │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐  │
│  │  Auth/Users  │  │  Papers/Digest│  │  Preferences │  │
│  └──────────────┘  └───────────────┘  └──────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐   │
│  │              Background Tasks (APScheduler)       │   │
│  │  Daily pipeline: fetch → deduplicate → rank →     │   │
│  │  generate digest → send email                     │   │
│  └───────────────────────────────────────────────────┘   │
└──────┬──────────────────┬──────────────────┬─────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
  PostgreSQL           Redis            External APIs
  (primary DB)         (cache)        (arXiv, OpenAlex,
                                        Crossref)
```

### Data Pipeline

1. **Fetch** — APScheduler triggers hourly fetches from all configured sources using user keyword pools
2. **Normalize** — each source's response is mapped to a unified `RawPaper` schema
3. **Deduplicate** — papers are matched by DOI, arXiv ID, or MD5 hash of the normalized title
4. **Store** — new papers are persisted to PostgreSQL
5. **Rank** — at digest time, each paper is scored against each user's preferences
6. **Digest** — top-N papers are saved to `DailyDigest`, viewable on the web and optionally emailed

### Ranking Scoring (transparent, per-paper)

| Signal | Points |
|---|---|
| Keyword match in title | +10 per keyword |
| Keyword match in abstract | +5 per keyword |
| Exclude keyword match | −20 per keyword |
| Preferred author match | +15 per author |
| Preferred source match | +5 |
| Preferred journal match | +10 per journal |

Each paper card includes a score breakdown explaining why it was recommended.

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) v2+
- (For manual setup) Python 3.11+, Node.js 20+, PostgreSQL 16, Redis 7

### Local Development (Docker Compose)

```bash
# 1. Clone the repository
git clone https://github.com/Silver-Zhang/PaperNorsh.git
cd PaperNorsh

# 2. Create your .env file
cp .env.example .env
# Edit .env and set SECRET_KEY (and optionally SMTP / OpenAI credentials)

# 3. Start all services
docker compose up --build

# 4. The app is now running:
#    Frontend:  http://localhost:3000
#    Backend:   http://localhost:8000
#    API Docs:  http://localhost:8000/docs
```

### Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://papernosh:papernosh@localhost:5432/papernosh"
export SECRET_KEY="your-secret-key"
export REDIS_URL="redis://localhost:6379/0"

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start the dev server
npm run dev
```

---

## Project Structure

```
PaperNosh/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py               # Auth dependency injection
│   │   │   └── routes/
│   │   │       ├── auth.py           # Register, login, me
│   │   │       ├── users.py          # User profile
│   │   │       ├── preferences.py    # Research preferences CRUD
│   │   │       ├── papers.py         # Paper listing, interactions
│   │   │       └── digest.py         # Daily digest endpoints
│   │   ├── core/
│   │   │   ├── config.py             # Pydantic settings
│   │   │   ├── database.py           # SQLAlchemy engine & session
│   │   │   └── security.py           # JWT, password hashing
│   │   ├── models/                   # SQLAlchemy ORM models
│   │   ├── schemas/                  # Pydantic v2 request/response schemas
│   │   ├── services/
│   │   │   ├── sources/
│   │   │   │   ├── base.py           # Abstract PaperSource base class
│   │   │   │   ├── arxiv.py          # arXiv RSS/API integration
│   │   │   │   ├── openalex.py       # OpenAlex API integration
│   │   │   │   └── crossref.py       # Crossref API integration
│   │   │   ├── ranking.py            # Relevance scoring engine
│   │   │   ├── digest.py             # Digest generation service
│   │   │   └── email_service.py      # SMTP email delivery
│   │   ├── tasks/
│   │   │   ├── scheduler.py          # APScheduler setup
│   │   │   └── pipeline.py           # Fetch, dedup, score pipeline
│   │   └── main.py                   # FastAPI app entrypoint
│   ├── alembic/                      # Database migrations
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_ranking.py
│   │   └── test_sources.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                      # Next.js App Router pages
│   │   ├── components/               # Reusable UI components
│   │   ├── lib/                      # API client, auth context, utils
│   │   └── types/                    # TypeScript type definitions
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## API Reference

Full interactive docs available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

### Authentication

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Login and receive JWT token |
| GET | `/api/auth/me` | Get current user info |

### Preferences

| Method | Path | Description |
|---|---|---|
| GET | `/api/preferences` | Get current user's preferences |
| PUT | `/api/preferences` | Create or update preferences |

### Papers

| Method | Path | Description |
|---|---|---|
| GET | `/api/papers` | List papers (with filters) |
| GET | `/api/papers/{id}` | Get paper detail |
| POST | `/api/papers/{id}/interact` | Save / ignore / mark highly relevant |
| GET | `/api/papers/saved` | Get saved papers |
| GET | `/api/papers/ignored` | Get ignored papers |

### Digest

| Method | Path | Description |
|---|---|---|
| GET | `/api/digest/today` | Get today's digest |
| GET | `/api/digest/history` | List past digests |
| POST | `/api/digest/trigger` | Manually trigger digest generation |

### Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |

---

## Database Schema

```
users
  id UUID PK | email (unique) | hashed_password | full_name
  timezone | is_active | is_verified | created_at | updated_at

user_preferences
  id UUID PK | user_id FK(users) | keywords[] | exclude_keywords[]
  preferred_topics[] | follow_authors[] | preferred_sources[]
  preferred_journals[] | delivery_time | max_papers_per_digest
  created_at | updated_at

papers
  id UUID PK | title | authors JSON | abstract | source
  source_id | doi (unique nullable) | arxiv_id | url
  published_date | journal_name | venue | keywords JSON
  raw_metadata JSON | ai_summary | ai_summary_generated_at
  dedup_hash (unique) | created_at

paper_interactions
  id UUID PK | user_id FK(users) | paper_id FK(papers)
  action (saved/ignored/highly_relevant) | relevance_score
  created_at | updated_at
  UNIQUE(user_id, paper_id)

daily_digests
  id UUID PK | user_id FK(users) | date | status
  papers JSON | email_sent_at | created_at | updated_at
  UNIQUE(user_id, date)
```

---

## Configuration

All configuration is through environment variables. See `.env.example` for a full list.

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *(required)* | JWT signing secret — change in production |
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `SMTP_HOST` | *(optional)* | SMTP server for email digests |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | *(optional)* | SMTP username |
| `SMTP_PASSWORD` | *(optional)* | SMTP password |
| `FROM_EMAIL` | `noreply@papernosh.io` | Sender address |
| `OPENAI_API_KEY` | *(optional)* | Enables AI summaries; falls back to abstract truncation if absent |
| `ENVIRONMENT` | `development` | Set to `production` to enable production guards |

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v --cov=app
```

The test suite uses an in-memory SQLite database and mocked HTTP responses for all external API calls, so no network access or running services are required.

---

## Roadmap

### Next after MVP
- [ ] Semantic similarity ranking (embedding-based)
- [ ] Semantic Scholar data source
- [ ] Weekly digest option
- [ ] Browser extension for one-click save
- [ ] User-defined collections / reading lists
- [ ] Export to Zotero / BibTeX
- [ ] Paper citation graph exploration

### Non-goals (MVP scope)
- Social networking features
- Payment system
- Mobile app
- Heavy enterprise features

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Push and open a Pull Request

---

## License

MIT
