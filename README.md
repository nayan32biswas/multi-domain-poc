# Multi Domain POC

- `docker compose up server` Run the backend
- `cd frontend && npm run dev` Run the frontend

## Start For Production

- `docker compose up --build frontend-builder` Build frontend.
- `docker compose build server` Build the app image.
- `docker compose up -d server static_server`

## Project Creation

- `uv init multi-domain-poc`
- `cd multi-domain-poc`
- `npm create vite@latest multi-domain-poc -- --template react-ts`
- `mv multi-domain-poc frontend`
- `uv add fastapi uvicorn pydantic mongodb-odm pymongo`
- `uv add --optional dev ruff mypy`
- `export DB_URL="mongodb://root:password@localhost:27017/multi_domain?authSource=admin"`
- Generate secret key

```py
import secrets
secrets.token_hex(32)
```

- `uv run -m uvicorn app.main:app --reload`
