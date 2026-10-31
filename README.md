# WealthWatch 💰📈

[![Live Demo](https://img.shields.io/badge/Live_Demo-Vercel-black?style=flat&logo=vercel&logoColor=white)](https://wealthwatch-six.vercel.app)
[![CI](https://github.com/Downey112/wealthwatch/actions/workflows/ci.yml/badge.svg)](https://github.com/Downey112/wealthwatch/actions/workflows/ci.yml)
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Database: Supabase Postgres](https://img.shields.io/badge/Database-Supabase_PostgreSQL-3ECF8E?style=flat&logo=supabase&logoColor=white)](https://supabase.com/)
[![Frontend: React 19](https://img.shields.io/badge/Frontend-React_19-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)

A modern, full-stack personal finance tracker and analytical dashboard: record income and expenses, see monthly totals and net savings, and view spending categorized by budget division.

🔗 **Live Application:** [wealthwatch-six.vercel.app](https://wealthwatch-six.vercel.app)

---

## 🏗️ Architecture & Tech Stack

* **Frontend:** React 19 (Vite), Chart.js data visualizations, hosted on Vercel.
* **Backend:** Python FastAPI, running as serverless functions on Vercel (`api/index.py`).
* **Database & Governance:** Supabase PostgreSQL in the cloud (with Row Level Security), SQLite fallback for offline local execution.
* **Authentication:** Supabase Auth (Email & Password) with cryptographically validated JWT bearer tokens on all sensitive API endpoints.
* **Infrastructure Reliability:** Scheduled GitHub Actions keep-alive workflow (`.github/workflows/keepalive.yml`) to prevent free-tier database sleep.

---

## 📁 Project Layout

```text
wealthwatch/
├── frontend/   # React 19 single-page application & Chart.js components
├── backend/    # FastAPI core application (main.py, auth.py, db.py, unit tests)
├── api/        # Vercel serverless entry point bridging backend/
├── supabase/   # Supabase configuration & SQL migration schemas
└── .github/    # CI test suites & database keep-alive cron workflow
```

---

## ⚙️ Run Locally

Prerequisites: Node.js 20+ and Python 3.11+.

### 1. Backend API (http://localhost:8000, Interactive Swagger docs at `/api/docs`)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env    # On Linux/macOS: cp .env.example .env
uvicorn main:app --reload --port 8000 --env-file .env
```
*With no `DATABASE_URL` configured, the API automatically initializes a local SQLite database at `backend/wealthwatch.db`.*

### 2. Frontend Client (http://localhost:3000)
```bash
cd frontend
npm install
npm start
```
*The local development server automatically proxies `/api` requests to port 8000.*

---

## 🧪 Automated Testing

```bash
# Run backend test suite (FastAPI TestClient + SQLite in-memory)
cd backend && python -m pytest tests

# Run frontend React tests (Vitest)
cd frontend && npm test
```

---

## 🔌 API Endpoint Reference

All routes are nested under `/api` and return standardized JSON payloads. Every endpoint (except `/health`) requires `Authorization: Bearer <token>`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/addtransaction` | Record transaction (`amount`, `type`, `category`, `transaction_date`, `description`). |
| `GET` | `/gettransactions?year=&month=` | Retrieve historical transactions with optional monthly filters. |
| `GET` | `/getsummary?year=&month=` | Aggregate monthly income, total expenses, net savings, and category breakdowns. |
| `DELETE` | `/deletetransaction/{id}` | Permanently delete a specified transaction owned by authenticated user. |
| `GET` | `/health` | Unauthenticated database liveness probe. |

---

## 🔒 Security & Data Protection

The client browser only holds the public Supabase anon key and the authenticated user's access token. The FastAPI backend verifies the cryptographic JWT signature, audience, and expiration before scoping queries strictly to the caller's UUID. Tables have Row Level Security enabled to prevent unauthorized REST exposure.

---

## 📄 License

Released under the [MIT License](LICENSE).
