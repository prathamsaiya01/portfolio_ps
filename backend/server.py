from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.cors import CORSMiddleware

from backend.config import get_cors_origins
from backend.database import close_database_connection, get_database
from backend.routes.candidates import router as candidates_router
from backend.routes.approval import router as approval_router
from backend.routes.github import router as github_router
from backend.routes.github_webhook import router as github_webhook_router
from backend.routes.health import router as health_router
from backend.routes.projects import router as projects_router
from backend.routes.portfolio import router as portfolio_router

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")

app = FastAPI(title="Portfolio Automator API")
api_router = APIRouter(prefix="/api")

# Preserve existing runtime behavior while allowing lazy DB access.
db = get_database()


class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusCheckCreate(BaseModel):
    client_name: str


@api_router.get("/")
async def root():
    return {"message": "Hello World"}


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    mongo_db = get_database()
    if mongo_db is None:
        raise RuntimeError("MongoDB is not configured")

    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()

    await mongo_db.status_checks.insert_one(doc)
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    mongo_db = get_database()
    if mongo_db is None:
        return []

    status_checks = await mongo_db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check.get("timestamp"), str):
            check["timestamp"] = datetime.fromisoformat(check["timestamp"])
    return status_checks


@api_router.get("/download/portfolio")
async def download_portfolio():
    file_path = ROOT_DIR / "portfolio-website.zip"
    if file_path.exists():
        return FileResponse(
            path=str(file_path),
            filename="portfolio-website.zip",
            media_type="application/zip",
        )
    return {"error": "File not found"}


app.include_router(health_router)
app.include_router(api_router)
app.include_router(github_router)
app.include_router(github_webhook_router)
app.include_router(projects_router)
app.include_router(candidates_router)
app.include_router(approval_router)
app.include_router(portfolio_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=get_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    close_database_connection()
