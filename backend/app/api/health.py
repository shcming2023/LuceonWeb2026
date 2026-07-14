from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.mineru_api import MineruApiClient

router = APIRouter()


@router.get("/system/health")
def system_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "ok", "gpu_required": False}


@router.get("/system/mineru-health")
def mineru_health():
    return MineruApiClient().health()
