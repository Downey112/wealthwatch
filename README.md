# WealthWatch

[![CI](https://github.com/Downey112/wealthwatch/actions/workflows/ci.yml/badge.svg)](https://github.com/Downey112/wealthwatch/actions/workflows/ci.yml)

A personal finance dashboard: record income and expenses, see monthly totals and net
savings, and view spending by category.

- **Frontend** - React 19 (Create React App), Chart.js, hosted on Azure Static Web Apps
- **Backend** - Python Azure Functions (v2 programming model)
- **Database** - Azure SQL in the cloud, SQLite on your machine
- **Auth** - Azure Static Web Apps built-in authentication (Microsoft sign-in)

> The original Azure deployment has been taken down, so there is no live demo. The app
> runs fully on a local machine with no cloud account.

## Project layout

```
frontend/   React app
backend/    Azure Functions API (function_app.py, db.py, tests/)
database/   schema.sql for Azure SQL / SQL Server
.github/    CI workflow and the (manual) Static Web Apps deploy workflow
```

## Run it locally

You need Node.js 20+, Python 3.11+ and
[Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local).

**1. Backend** (http://localhost:7071)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy local.settings.example.json local.settings.json   # macOS/Linux: cp
func start
```

With no `DB_SERVER` setting the API stores data in `backend/wealthwatch.db` (SQLite) and
creates the tables itself.

**2. Frontend** (http://localhost:3000)

```bash
cd frontend
npm install
npm start
```

The dev server proxies `/api` to the backend, and you are signed in as `dev@localhost`.

## Tests

```bash
cd backend  && python -m pytest tests
cd frontend && npm test -- --watchAll=false
```

## API

All routes are under `/api` and return JSON. Errors look like `{"error": "message"}`.

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/addtransaction` | Add a transaction. Body: `amount`, `type` (`income` or `expense`), `category`, `transaction_date` (`YYYY-MM-DD`), optional `description` |
| `GET` | `/gettransactions?year=&month=` | Transactions for a month, newest first. Without a period, the latest `limit` (default 50) |
| `GET` | `/getsummary?year=&month=` | Income, expense, net savings and expense totals by category. Defaults to the current month |
| `DELETE` | `/deletetransaction/{id}` | Delete one of your own transactions |

## Configuration

Backend settings (`backend/local.settings.json` locally, Function App settings in Azure):

| Setting | Purpose |
|---|---|
| `DB_SERVER`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Azure SQL / SQL Server connection. Leave `DB_SERVER` unset to use SQLite |
| `SQLITE_PATH` | Optional path for the SQLite file |
| `DEV_USER_EMAIL` | Local development only: the user to act as when a request carries no identity. Never set this in Azure |

Frontend: `REACT_APP_API_URL` overrides the API base URL (default `/api`). See
`frontend/.env.example`.

## Deploying to Azure

1. Create an Azure SQL database and run `database/schema.sql` against it.
2. Create a Python Function App, set the four `DB_*` settings and deploy `backend/`
   (`func azure functionapp publish <app-name>`).
3. Create a Static Web App from this repository with app location `frontend` and output
   location `build`, then **link the Function App as its backend** so `/api` is served
   through Static Web Apps.
4. Store the new deployment token as a repository secret, update the secret name in
   `.github/workflows/azure-static-web-apps-*.yml`, and restore that workflow's `push`
   trigger (it is manual-only while there is nothing to deploy to).

### Why the backend must be linked

The API trusts the identity headers that Static Web Apps adds to each request. That is
only safe when the Function App cannot be called directly. Linking it as the Static Web
App's backend restricts access to the Static Web App; `staticwebapp.config.json` then
requires a signed-in user for every `/api` route. Pointing the frontend straight at a
public Function App URL with `REACT_APP_API_URL` bypasses this and is not suitable for
real data.
