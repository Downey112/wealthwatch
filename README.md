# WealthWatch

[![CI](https://github.com/Downey112/wealthwatch/actions/workflows/ci.yml/badge.svg)](https://github.com/Downey112/wealthwatch/actions/workflows/ci.yml)

A personal finance dashboard: record income and expenses, see monthly totals and net
savings, and view spending by category.

**Live: https://wealthwatch-six.vercel.app**

- **Frontend** - React 19 (Create React App), Chart.js, hosted on Vercel
- **Backend** - Python FastAPI, running as a Vercel serverless function
- **Database** - Supabase Postgres in the cloud, SQLite on your machine
- **Auth** - Supabase Auth (email and password); the API verifies each request's JWT

Everything runs on the free tiers of Vercel and Supabase, and fully on a local machine
with no cloud account.

## Project layout

```
frontend/   React app
backend/    FastAPI app (main.py, auth.py, db.py, tests/)
api/        Vercel entry point that serves backend/ as one function
supabase/   Supabase project config and database migrations
.github/    CI and the database keep-alive workflow
```

## Run it locally

You need Node.js 20+ and Python 3.11+.

**1. Backend** (http://localhost:8000, interactive docs at `/api/docs`)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env            # macOS/Linux: cp
uvicorn main:app --reload --port 8000 --env-file .env
```

With no `DATABASE_URL` the API stores data in `backend/wealthwatch.db` (SQLite) and
creates the tables itself.

**2. Frontend** (http://localhost:3000)

```bash
cd frontend
npm install
npm start
```

The dev server proxies `/api` to the backend, and with no Supabase settings you are
signed in as `dev@localhost`.

## Tests

```bash
cd backend  && python -m pytest tests
cd frontend && npm test -- --watchAll=false
```

## API

All routes are under `/api` and return JSON. Errors look like `{"error": "message"}`.
Every route except `/health` needs `Authorization: Bearer <Supabase access token>`.

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/addtransaction` | Add a transaction. Body: `amount`, `type` (`income` or `expense`), `category`, `transaction_date` (`YYYY-MM-DD`), optional `description` |
| `GET` | `/gettransactions?year=&month=` | Transactions for a month, newest first. Without a period, the latest `limit` (default 50) |
| `GET` | `/getsummary?year=&month=` | Income, expense, net savings and expense totals by category. Defaults to the current month |
| `DELETE` | `/deletetransaction/{id}` | Delete one of your own transactions |
| `GET` | `/health` | Checks the database connection. No sign-in needed |

## Configuration

Backend (`backend/.env` locally, Vercel environment variables in production):

| Setting | Purpose |
|---|---|
| `DATABASE_URL` or `POSTGRES_URL` | Postgres connection string. Use Supabase's **transaction pooler** string (port 6543). Leave both unset to use SQLite |
| `SUPABASE_URL` | `https://<project-ref>.supabase.co`. Access tokens are verified against this project's signing keys |
| `SUPABASE_JWT_SECRET` | Only for older Supabase projects that still sign tokens with the shared secret |
| `SQLITE_PATH` | Optional path for the SQLite file |
| `DEV_USER_EMAIL` | Local development only: the user to act as when a request carries no token. Ignored on Vercel |

Frontend (build-time, see `frontend/.env.example`):

| Setting | Purpose |
|---|---|
| `REACT_APP_SUPABASE_URL` | Same value as `SUPABASE_URL` |
| `REACT_APP_SUPABASE_ANON_KEY` | The project's anon / publishable key. Safe to ship in the browser |
| `REACT_APP_API_URL` | Optional API base URL (default `/api`) |

## Deploying

The live site uses Vercel's Supabase integration (`npx vercel integration add supabase`),
which creates the Supabase project and injects `POSTGRES_URL`, `SUPABASE_URL` and
`SUPABASE_ANON_KEY` into the Vercel project; the build passes the last two on to the
React app. With that route only the migration in `supabase/migrations/` has to be applied
by hand. To wire the two services up yourself instead:

1. **Supabase** - create a project, then from the repository root:
   ```bash
   npx supabase login
   npx supabase link --project-ref <project-ref>
   npx supabase db push          # creates the tables
   npx supabase config push      # applies the auth settings in supabase/config.toml
   ```
   Set `site_url` in `supabase/config.toml` to the live site's URL first.
2. **Vercel** - import the repository (or run `npx vercel` in it). `vercel.json` builds
   the frontend and routes `/api/*` to the Python function. Add the environment
   variables from the tables above, then deploy.
3. **Keep-alive** - Supabase pauses free projects after a week without activity. Set the
   `APP_URL` repository variable to the live URL and `.github/workflows/keepalive.yml`
   pings `/api/health` twice a week.

### How the data is protected

The browser only ever holds the Supabase anon key and the signed-in user's own access
token. The API checks that token's signature, expiry, audience and issuer on every
request and scopes every query to that user. The tables have row level security enabled
with no policies, so they cannot be read through Supabase's public REST API - only
through this API.
