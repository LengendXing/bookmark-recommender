# Bookmark Recommender

AI-powered bookmark recommendation system with semantic search.

## Tech Stack

- **Backend**: Python 3.12 + FastAPI + SQLAlchemy + Alembic
- **Frontend**: Vue 3 + Vite + TypeScript + Tailwind CSS
- **Storage**: SQLite (business data) + ChromaDB (vector search)
- **AI**: Claude API (web scraping + enrichment) + sentence-transformers (embedding)

## Quick Start

```bash
# Backend
cd backend
pip install -e .
cp ../.env.development .env
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Deploy with Docker

```bash
cp .env.example .env
docker compose up --build -d
```

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers
│   │   ├── core/         # Config, database, security, logging
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic (scraper, claude, embedding, ingest)
│   │   └── main.py       # App entry
│   ├── migrations/       # Alembic migrations
│   └── tests/
├── frontend/
│   └── src/
│       ├── api/          # API client
│       ├── components/   # Reusable components
│       ├── layouts/      # Page layouts
│       ├── pages/        # Route pages
│       ├── stores/       # Pinia stores
│       ├── i18n/         # Internationalization
│       └── styles/       # Tailwind + CSS
└── docker-compose.yml
```

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /api/auth/register | Register |
| POST | /api/auth/login | Login |
| GET | /api/bookmarks | List bookmarks |
| POST | /api/bookmarks/ingest | Ingest URL |
| POST | /api/recommend | Recommend by query |
| POST | /api/recommend/train | Trigger model training |

## License

MIT
