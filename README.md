# 💰 WealthWatch — Cloud-Native Personal Finance Dashboard

![Deploy WealthWatch to Azure](https://github.com/Downey112/wealthwatch/actions/workflows/azure-deploy.yml/badge.svg)
![Azure](https://img.shields.io/badge/Azure-Static%20Web%20Apps-0078D4?logo=microsoftazure)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

> A full-stack, cloud-native personal finance tracker built and deployed on Microsoft Azure. Track income and expenses, visualize spending trends, and manage your finances — all synced to the cloud in real time.

🌐 **Live Demo:** [https://lemon-cliff-0776cbb00.7.azurestaticapps.net](https://lemon-cliff-0776cbb00.7.azurestaticapps.net)

---

## 📸 Screenshots

> _Add screenshots here after the full app is running_

---

## 🏗️ Cloud Architecture
┌─────────────────────────────────────────────────────┐
│                   User's Browser                     │
│              React SPA + Chart.js (Vite)             │
└──────────────────────┬──────────────────────────────┘
│ HTTPS
▼
┌─────────────────────────────────────────────────────┐
│         Azure Static Web Apps (Free Tier)            │
│     Global CDN · GitHub Actions CI/CD · Auth         │
└──────────────────────┬──────────────────────────────┘
│ REST /api/*
▼
┌─────────────────────────────────────────────────────┐
│      Azure Functions - Consumption Plan (Free)       │
│  GET /transactions · POST /transactions              │
│  DELETE /transactions · GET /summary                 │
└──────────────────────┬──────────────────────────────┘
│ pyodbc / SQL
▼
┌─────────────────────────────────────────────────────┐
│        Azure SQL Database (Free Tier)                │
│     users · transactions · categories                │
└─────────────────────────────────────────────────────┘
---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 19 + Vite | SPA framework |
| **Charts** | Chart.js + react-chartjs-2 | Data visualization |
| **Backend** | Azure Functions (Python 3.11) | Serverless REST API |
| **Database** | Azure SQL Database | Relational data storage |
| **Hosting** | Azure Static Web Apps | Frontend CDN hosting |
| **CI/CD** | GitHub Actions | Automated deployment |
| **IaC** | Azure CLI | Infrastructure provisioning |
| **Version Control** | Git + GitHub | Source control |

---

## ✨ Features

- 📊 **Dashboard** — Monthly income vs expenses bar chart + category breakdown pie chart
- ➕ **Add Transactions** — Log income or expenses with category, amount, date and notes
- 📋 **Transaction History** — Full sortable table with delete functionality
- 💹 **Summary Cards** — Total income, total expenses, and net balance at a glance
- ☁️ **Cloud Synced** — All data persisted in Azure SQL Database
- 🚀 **Auto-Deploy** — Every `git push` to `main` triggers a full CI/CD pipeline

---

## 🚀 CI/CD Pipeline

Every push to `main` automatically:

1. ✅ Checks out the repository
2. ✅ Sets up Node.js 20 and installs dependencies
3. ✅ Builds the React app with Vite
4. ✅ Deploys the `dist/` folder to Azure Static Web Apps globally
git push origin main
│
▼
GitHub Actions triggers
│
├── Build & Deploy Frontend ──▶ Azure Static Web Apps
└── Build & Deploy API ────────▶ Azure Functions

---

## 🗄️ Database Schema

```sql
users (id, github_username, display_name, created_at)
categories (id, name)
transactions (id, user_id, amount, type, category, note, transaction_date, created_at)
```

---

## 🏃 Running Locally

### Prerequisites
- Node.js 20+
- Python 3.11+
- Azure Functions Core Tools
- Azure CLI

### Frontend
```bash
cd frontend
npm install
npm run dev
# Runs at http://localhost:5173
```

### Backend API
```bash
cd api
pip install -r requirements.txt
# Create local.settings.json with your SQL_CONNECTION_STRING
func start
# Runs at http://localhost:7071
```

---

## ☁️ Azure Resources

| Resource | Service | Tier |
|---|---|---|
| `wealthwatch-app` | Azure Static Web Apps | Free |
| `wealthwatch-api-luqman` | Azure Functions | Consumption (Free) |
| `wealthwatch-db` | Azure SQL Database | Free Tier |
| `wealthwatch-sqlserver` | Azure SQL Server | — |
| `wealthwatchstorageluqman` | Azure Blob Storage | Standard LRS |

---

## 📚 What I Learned

- Designing and provisioning cloud infrastructure using **Azure CLI**
- Building **serverless REST APIs** with Azure Functions and Python
- Connecting Python functions to **Azure SQL Database** using pyodbc
- Setting up **GitHub Actions CI/CD pipelines** for automated deployment
- Managing **GitHub Secrets** for secure credential handling
- Deploying React SPAs to **Azure Static Web Apps** with global CDN
- Using **GitHub Projects** for Kanban-based project management

---

## 👨‍💻 Author

**Downey** — Computer Science Student at UiTM  
[![GitHub](https://img.shields.io/badge/GitHub-Downey112-181717?logo=github)](https://github.com/Downey112)

---

## 📄 License

This project is licensed under the MIT License.