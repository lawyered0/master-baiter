# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "fastapi>=0.115.0",
#     "uvicorn>=0.32.0",
#     "sqlalchemy>=2.0.0",
#     "watchfiles>=1.0.0",
#     "websockets>=14.0",
# ]
# ///
"""Master-Baiter Dashboard — FastAPI server with live WebSocket updates.

Start with: uv run {baseDir}/server/main.py
Opens at: http://localhost:8147
"""

import asyncio
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure server package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from db import init_db
from ws import manager
from ingest import full_sync, watch_workspace
from routes.sessions import router as sessions_router
from routes.evidence import router as evidence_router
from routes.intel import router as intel_router
from routes.reports import router as reports_router
from routes.analytics import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB, run full sync, start file watcher."""
    init_db()
    full_sync()
    watcher_task = asyncio.create_task(watch_workspace(broadcast_fn=manager.broadcast))
    yield
    watcher_task.cancel()
    try:
        await watcher_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Master-Baiter Dashboard",
    description="Scam baiting session monitor, intel database, and report management",
    version="1.0.0",
    lifespan=lifespan,
)

# API routes
app.include_router(sessions_router)
app.include_router(evidence_router)
app.include_router(intel_router)
app.include_router(reports_router)
app.include_router(analytics_router)

# Static frontend files
FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def index():
    """Serve the dashboard SPA."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Master-Baiter Dashboard API", "docs": "/docs"}


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, receive any client messages
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "master-baiter-dashboard"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("MASTER_BAITER_PORT", "8147"))
    uvicorn.run(app, host="0.0.0.0", port=port)
