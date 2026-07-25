from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from core.database import get_db
from models import Organization, GlobalMetric, ThreatAlert, Client
from schemas import GlobalMetricResponse, ClientResponse
from core.security import get_current_org
from typing import List

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/global", response_model=List[GlobalMetricResponse])
def get_global_metrics(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_org)):
    metrics = db.query(GlobalMetric).order_by(GlobalMetric.created_at).all()
    return metrics

@router.get("/summary")
def get_summary_metrics(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_org)):
    latest_metric = db.query(GlobalMetric).order_by(desc(GlobalMetric.created_at)).first()
    
    alert_count = db.query(ThreatAlert).filter(ThreatAlert.org_id == current_org.id).count()
    active_clients = db.query(Client).filter(Client.org_id == current_org.id, Client.is_active == True).count()
    
    return {
        "accuracy": latest_metric.accuracy if latest_metric else 0.0,
        "f1": latest_metric.f1 if latest_metric else 0.0,
        "auc": latest_metric.auc if latest_metric else 0.0,
        "total_alerts": alert_count,
        "active_clients": active_clients
    }

@router.get("/clients", response_model=List[ClientResponse])
def get_clients(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_org)):
    clients = db.query(Client).filter(Client.org_id == current_org.id).all()
    return clients
