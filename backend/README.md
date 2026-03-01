## Backend (FastAPI)

This directory contains a small FastAPI backend that provides:

- OAuth redirect flows for YouTube, Facebook, Instagram, Twitter (X), and TikTok.
- A generic SQLAlchemy schema for users and OAuth connections.
- REST endpoints to list and disconnect integrations used by the Next.js `connections` UI.

### Quick start

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r backend/requirements.txt
```

3. Run the app:

```bash
uvicorn backend.main:app --reload
```

By default, the app uses a local SQLite database at `./app.db`. You can override this via the
`DATABASE_URL` environment variable (e.g. PostgreSQL, MySQL, etc.).

### Key environment variables

- `DATABASE_URL` - SQLAlchemy URL (default: `sqlite:///./app.db`).
- `FRONTEND_BASE_URL` - Base URL of the Next.js app (default: `http://localhost:3000`).
- `TASKS_MODE` - `inline` for local or `cloud_tasks` for Cloud Run workers.
- `GCP_PROJECT_ID`, `GCP_LOCATION` - Cloud Tasks project and region.
- Queue names:
  - `CLOUD_TASKS_QUEUE_INGEST`
  - `CLOUD_TASKS_QUEUE_STATS`
  - `CLOUD_TASKS_QUEUE_VECTOR`
  - `CLOUD_TASKS_QUEUE_OVERVIEW`
  - `CLOUD_TASKS_QUEUE_PREMIUM`
  - `CLOUD_TASKS_QUEUE_CONTENT_FEATURES`
- Worker base URLs:
  - `WORKER_INGEST_BASE_URL`
  - `WORKER_STATS_BASE_URL`
  - `WORKER_VECTOR_BASE_URL`
  - `WORKER_DEEP_ANALYSIS_BASE_URL`
- Worker auth settings:
  - `WORKER_AUTH_MODE` (`oidc` recommended for production)
  - `WORKER_INVOKER_SERVICE_ACCOUNT`
  - `WORKER_INGEST_AUDIENCE`, `WORKER_STATS_AUDIENCE`, `WORKER_VECTOR_AUDIENCE`, `WORKER_DEEP_ANALYSIS_AUDIENCE`
- Client credentials and redirect paths for each provider:
  - `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REDIRECT_PATH`
  - `FACEBOOK_CLIENT_ID`, `FACEBOOK_CLIENT_SECRET`, `FACEBOOK_REDIRECT_PATH`
  - `INSTAGRAM_CLIENT_ID`, `INSTAGRAM_CLIENT_SECRET`, `INSTAGRAM_REDIRECT_PATH`
  - `TWITTER_CLIENT_ID`, `TWITTER_CLIENT_SECRET`, `TWITTER_REDIRECT_PATH`
  - `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_REDIRECT_PATH`

Configure each OAuth app on the provider side so that its redirect URL matches the
corresponding callback route, for example:

```text
https://your-backend-domain.com/oauth/youtube/callback
```
