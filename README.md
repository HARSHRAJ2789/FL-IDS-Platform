# 🛡️ FL-IDS Platform — Federated Learning Intrusion Detection SaaS

A **multi-tenant SaaS platform** where organizations join a private federated learning network to collaboratively train an AI intrusion detection model — without sharing any raw network data.

---

## 🏗️ Architecture

```
[Your Cloud Server — Railway/Render]
  FastAPI Backend API
  SQLite Database
  FL Round Orchestration (FedAvg)
  WebSocket real-time push
  Business Dashboard Portal
         ↑ HTTPS
  ┌──────┴──────┬──────────┬──────────┐
  ▼             ▼          ▼          ▼
[Client 1]  [Client 2] [Client 3] [Client 4]
 Hospital    Bank        ISP       Startup
 Agent       Agent      Agent      Agent
 scapy       scapy      scapy      scapy
 (live       (live      (live      (live
 packets)    packets)   packets)   packets)
```

---

## 🚀 Deploy to Railway (Recommended)

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Deploy from server/ directory
cd /Users/harsh/FL-IDS-Platform
railway up --service fl-ids-server
```

Or push to GitHub → connect repo in [railway.app](https://railway.app) → auto-deploys.

**Set these environment variables in Railway dashboard:**
```
SECRET_KEY = (generate a long random string)
DATABASE_URL = sqlite:////data/flds.db
WEIGHTS_DIR = /data/weights
```

---

## 🚀 Deploy to Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your repo → Render reads `render.yaml` automatically
4. Set `SECRET_KEY` environment variable
5. Deploy ✅

---

## 💻 Install Client Agent (on any machine)

After deploying the server, organizations install the agent with **one command:**

```bash
FLDS_API_KEY=their-api-key \
FLDS_SERVER_URL=https://your-server.railway.app \
curl -sSL https://your-server.railway.app/install.sh | bash
```

The agent:
- Captures live packets using `scapy`
- Trains local ML model every FL round
- Reports attacks to dashboard in real time
- Runs as a background service (auto-starts on boot)

---

## 🖥️ Dashboard Access

After deployment:
- **Login:** `https://your-server.railway.app/login`
- **Dashboard:** `https://your-server.railway.app/dashboard`

Features:
- Real-time threat alerts via WebSocket
- FL round metrics (accuracy, F1, AUC per round)
- Client agent status monitoring
- API key management

---

## 🔌 REST API

Full API docs auto-generated at: `https://your-server.railway.app/docs`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | None | Register organization |
| POST | `/auth/login` | None | Login → JWT token |
| GET | `/rounds/current` | API Key | Client polls for active round |
| GET | `/rounds/{id}/weights` | API Key | Download global weights |
| POST | `/rounds/{id}/submit` | API Key | Submit local weights |
| POST | `/alerts` | API Key | Report attack |
| GET | `/alerts` | JWT | Get org's alerts |
| GET | `/metrics/global` | JWT | All round metrics |
| GET | `/metrics/summary` | JWT | Dashboard summary stats |
| WS | `/ws/{org_id}` | JWT | Real-time push |

---

## 🐳 Local Development

```bash
cd /Users/harsh/FL-IDS-Platform
docker compose up --build

# Dashboard: http://localhost:80
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## 📁 Project Structure

```
FL-IDS-Platform/
├── server/               # FastAPI backend
│   ├── main.py
│   ├── models.py         # DB table definitions
│   ├── schemas.py        # Pydantic request/response
│   ├── routes/           # auth, rounds, alerts, metrics
│   ├── core/             # database, security, fedavg, websocket
│   ├── requirements.txt
│   └── Dockerfile
├── client/               # Agent installed on client machines
│   ├── agent.py          # Main loop
│   ├── feature_extractor.py  # scapy → 196 features
│   ├── trainer.py        # Local FL training
│   ├── detector.py       # Real-time attack detection
│   ├── config.py         # Configuration
│   └── install.sh        # One-line installer
├── dashboard/            # Web portal
│   ├── index.html        # Login + Register
│   └── portal.html       # Main business dashboard
├── docker-compose.yml    # Production stack
├── railway.toml          # Railway deployment
├── render.yaml           # Render deployment
├── nginx.conf            # Reverse proxy
└── .env.example          # Environment variables
```

---

## 💼 Business Model

| Plan | Clients | Features | Price |
|---|---|---|---|
| Starter | 1 | Basic dashboard, email alerts | ₹5,000/mo |
| Pro | 5 | Real-time dashboard, API access | ₹20,000/mo |
| Enterprise | Unlimited | Private FL rounds, SLA, custom | Custom |
