import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from core.database import create_tables, get_db, SessionLocal
from core.websocket_manager import manager
from models import FLRound
from routes import auth, rounds, alerts, metrics

app = FastAPI(title="FL-IDS Platform", version="1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(rounds.router)
app.include_router(alerts.router)
app.include_router(metrics.router)

# Mount static files if directory exists, else create it
STATIC_DIR = os.path.join(os.path.dirname(__file__), "dashboard")
os.makedirs(STATIC_DIR, exist_ok=True)

# Create dummy HTML files to serve
portal_html_path = os.path.join(STATIC_DIR, "portal.html")
index_html_path = os.path.join(STATIC_DIR, "index.html")

if not os.path.exists(portal_html_path):
    with open(portal_html_path, "w") as f:
        f.write("<html><body><h1>FL-IDS Dashboard Portal</h1></body></html>")

if not os.path.exists(index_html_path):
    with open(index_html_path, "w") as f:
        f.write("<html><body><h1>FL-IDS Login</h1></body></html>")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.on_event("startup")
def startup_event():
    create_tables()
    db = SessionLocal()
    # Create first FL round if none exists
    if not db.query(FLRound).first():
        first_round = FLRound(round_num=1, status="active")
        db.add(first_round)
        db.commit()
    db.close()

@app.get("/")
def read_root():
    return {"status": "ok", "version": "1.0"}

@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    return FileResponse(portal_html_path)

@app.get("/login", response_class=HTMLResponse)
def get_login():
    return FileResponse(index_html_path)

@app.websocket("/ws/{org_id}")
async def websocket_endpoint(websocket: WebSocket, org_id: str):
    await manager.connect(websocket, org_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, org_id)
