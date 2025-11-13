# LumenPay Bot

Проект автоматизации продажи подписок для Telegram-каналов. Подробнее см. `docs/architecture-plan.md`.

## Quick Start

**See [DEPLOY.md](./DEPLOY.md) for complete server deployment instructions with Coolify.**

### Local Development

**Backend:**
```bash
poetry install
poetry run uvicorn backend.app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm ci
npm run dev
```

**Docker Compose (all services):**
```bash
docker compose up --build
```

---

## Deploy with Coolify (GitHub)

These instructions describe a minimal setup to deploy the project to Coolify using the GitHub repository as the source.

- Connect your GitHub repository to Coolify.
- Add three services in Coolify (or one stack depending on your plan): `backend`, `bot` and `frontend`.

Service settings (recommended):

- Backend
	- Build context: repository root
	- Dockerfile path: `backend/Dockerfile`
	- Port: `8000`
	- Environment variables: set `DATABASE_URL`, `SYNC_DATABASE_URL`, `REDIS_URL`, `ENVIRONMENT` and any secrets from `config/env.example`.

- Bot
	- Build context: repository root
	- Dockerfile path: `bot/Dockerfile`
	- Environment variables: `BACKEND_BASE_URL`, `BACKEND_API_PREFIX`, token secrets, etc.

- Frontend
	- Build context: `frontend`
	- Dockerfile path: `frontend/Dockerfile`
	- Port: `80`

Notes:

- The frontend image already includes an `nginx` config (`frontend/nginx.conf`) and serves the built `dist/` files. No runtime file mounts are required for Coolify.
- Coolify (or the external reverse proxy) should handle SSL termination; do not commit private certificates into the repo.
- Use Coolify's environment/secret UI to store production secrets.

CI:

- A GitHub Actions workflow is included at `.github/workflows/ci.yml` that runs backend tests and builds frontend on push/PR. This validates changes before deployment.

Local development:

- Backend (Poetry):

```bash
poetry install
poetry run uvicorn backend.app.main:app --reload
```

- Frontend:

```bash
cd frontend
npm ci
npm run dev
```

Running with Docker Compose (local):

```bash
docker compose up --build
```

