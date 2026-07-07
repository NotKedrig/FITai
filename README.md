# FitAI

FitAI is a workout tracking platform with AI-powered set recommendations. Log workouts from a React Native mobile app, and get intelligent suggestions for weight and reps based on your session history, RPE, and fatigue signals.

The project is a monorepo with two main packages:

| Package | Description |
|---------|-------------|
| [`fitai-backend`](fitai-backend/) | FastAPI REST API, PostgreSQL, AI recommendation engine |
| [`fitai-mobile`](fitai-mobile/) | Expo / React Native client for iOS, Android, and web |

## Features

- **User authentication** — JWT-based register/login with secure password hashing
- **Workout tracking** — Start and end workouts, log sets with weight, reps, and RPE
- **Exercise library** — Browse global exercises or create custom ones
- **AI set recommendations** — After each working set, receive suggested weight and reps with an explanation
- **Rule-based fallback** — Deterministic progression logic when the AI provider is unavailable
- **Per-exercise stats** — Track estimated 1RM, volume, and session history
- **Observability** — Prometheus and Grafana included in the local Docker stack

## Tech Stack

**Backend**

- Python 3.11, FastAPI, Pydantic v2
- PostgreSQL 16 with async SQLAlchemy 2.0
- Alembic migrations, Redis
- AI providers: Google Gemini (default), OpenAI, Ollama

**Mobile**

- React Native 0.81, Expo 54
- React Navigation
- Secure token storage via `expo-secure-store`

**Infrastructure**

- Docker Compose (API, Postgres, Redis, Prometheus, Grafana)
- Railway deployment via [`railway.toml`](railway.toml)

## Architecture

```
fitai-mobile  ──HTTP──▶  fitai-backend (FastAPI)
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
               PostgreSQL   Redis    AI Provider
                              │
                    Rule engine fallback
```

The backend follows a layered design:

```
api/v1  →  services  →  repositories  →  models
                ↓
            ai/ (providers, context builder, prompt builder)
```

Business logic lives in services. Database access goes through repositories. Route handlers stay thin.

## Project Structure

```
FITai/
├── fitai-backend/
│   ├── app/
│   │   ├── api/v1/          # REST endpoints
│   │   ├── ai/              # AI provider abstraction
│   │   ├── core/            # Security, middleware
│   │   ├── db/              # Database session
│   │   ├── models/          # SQLAlchemy models
│   │   ├── repositories/    # Data access layer
│   │   ├── schemas/         # Pydantic request/response models
│   │   └── services/        # Business logic
│   ├── migrations/          # Alembic schema migrations
│   ├── scripts/             # Seed data, health checks, test flows
│   ├── tests/
│   └── docker-compose.yml
├── fitai-mobile/
│   └── src/
│       ├── api/             # HTTP client modules
│       ├── context/         # Auth and workout state
│       ├── navigation/
│       └── screens/
└── railway.toml
```

## Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose (recommended for backend)
- Python 3.11+ (for local backend development)
- Node.js 18+ and npm (for mobile)
- [Expo CLI](https://docs.expo.dev/) (installed via `npx expo`)
- An API key for your chosen AI provider (Gemini or OpenAI), or a local [Ollama](https://ollama.com/) instance

## Quick Start (Docker)

### 1. Configure environment

Create `fitai-backend/.env` with at least:

```env
DATABASE_URL=postgresql+asyncpg://fitai:fitai@db:5432/fitai
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
AI_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
```

### 2. Start the stack

```bash
cd fitai-backend
docker compose up -d
```

The API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs` (disabled in production).

### 3. Run migrations

```bash
docker compose exec api python run_alembic.py upgrade head
```

### 4. Seed exercises

```bash
docker compose exec api python scripts/seed_exercises.py
```

### 5. Run the mobile app

Update the API base URL in [`fitai-mobile/src/config/api.js`](fitai-mobile/src/config/api.js), then:

```bash
cd fitai-mobile
npm install
npx expo start
```

Use the Expo Go app or a dev client to open the app on your device or emulator.

## Local Development (without Docker)

### Backend

```bash
cd fitai-backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"

# Point DATABASE_URL at a running Postgres instance
alembic upgrade head
python scripts/seed_exercises.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Mobile

```bash
cd fitai-mobile
npm install
npx expo start
```

Point `BASE_URL` in `src/config/api.js` to your backend (e.g. `http://localhost:8000` or a tunnel URL when testing on a physical device).

## Environment Variables

### Backend (`fitai-backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | Async Postgres connection string |
| `SECRET_KEY` | Yes | — | JWT signing secret |
| `REDIS_URL` | No | — | Redis connection string |
| `ENVIRONMENT` | No | `development` | `development` or `production` |
| `ALLOWED_ORIGINS` | No | `*` | CORS origins (comma-separated) |
| `AI_PROVIDER` | No | `gemini` | `gemini`, `openai`, or `ollama` |
| `GEMINI_API_KEY` | If using Gemini | — | Google AI API key |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Gemini model name |
| `OPENAI_API_KEY` | If using OpenAI | — | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model name |
| `OLLAMA_BASE_URL` | If using Ollama | — | Ollama server URL |
| `OLLAMA_MODEL` | No | `llama3.2:3b` | Ollama model name |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | JWT expiry |

## API Overview

Base path: `/api/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/auth/register` | Create account |
| `POST` | `/auth/login` | Get JWT token |
| `GET` | `/users/me` | Current user profile |
| `GET` | `/users/me/stats` | Aggregate workout stats |
| `GET` | `/users/me/stats/{exercise_id}` | Stats for one exercise |
| `GET` | `/exercises` | List exercises (`?search=`) |
| `POST` | `/exercises` | Create custom exercise |
| `POST` | `/workouts` | Start a workout |
| `GET` | `/workouts` | List workouts |
| `POST` | `/workouts/{id}/end` | End a workout |
| `POST` | `/workouts/{id}/sets` | Log a set (returns AI recommendation) |
| `GET` | `/workouts/{id}/sets` | List sets for a workout |
| `DELETE` | `/sets/{id}` | Delete a set |

Authenticated endpoints require a Bearer token from `/auth/login`.

## How Recommendations Work

When you log a **working set** (not a warmup):

1. The service builds a `WorkoutContext` from your current session, recent history, and exercise metadata.
2. The configured AI provider generates a weight/reps suggestion with an explanation and confidence level.
3. If the AI call fails, a **rule engine** applies deterministic progression logic based on RPE, rep drops, volume, and fatigue signals.
4. The recommendation is stored alongside the set and returned in the API response.

Warmup sets are logged without generating a recommendation.

## AI Providers

Set `AI_PROVIDER` in your `.env`:

| Provider | Value | Notes |
|----------|-------|-------|
| Google Gemini | `gemini` | Default; requires `GEMINI_API_KEY` |
| OpenAI | `openai` | Requires `OPENAI_API_KEY` |
| Ollama | `ollama` | Local inference; set `OLLAMA_BASE_URL` |

## Testing

```bash
cd fitai-backend
pytest
```

Integration and end-to-end scripts live in [`fitai-backend/scripts/`](fitai-backend/scripts/). See [`fitai-backend/scripts/README.md`](fitai-backend/scripts/README.md) for migration and seeding notes.

## Deployment

The repo includes a [`railway.toml`](railway.toml) for deploying the backend to [Railway](https://railway.app/). On deploy, Alembic migrations run automatically before the server starts.

Set all required environment variables in your hosting provider. Use `ENVIRONMENT=production` to disable Swagger docs.

## Monitoring (local)

When running via Docker Compose:

| Service | URL |
|---------|-----|
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` |

## License

MIT
