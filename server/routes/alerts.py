from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from core.database import get_db
from models import ThreatAlert, Organization
from schemas import AlertCreate, AlertResponse
from core.security import get_current_org
from core.websocket_manager import manager
from typing import List

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.post("", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate, 
    db: Session = Depends(get_db), 
    current_org: Organization = Depends(get_current_org)
):
    new_alert = ThreatAlert(
        org_id=current_org.id,
        client_id=alert.client_id,
        severity=alert.severity,
        attack_type=alert.attack_type,
        source_ip=alert.source_ip,
        dest_ip=alert.dest_ip,
        details=alert.details
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    
    # Broadcast to websocket
    alert_dict = {
        "id": new_alert.id,
        "severity": new_alert.severity,
        "attack_type": new_alert.attack_type,
        "source_ip": new_alert.source_ip,
        "dest_ip": new_alert.dest_ip,
        "timestamp": new_alert.timestamp.isoformat()
    }
    await manager.broadcast_to_org(current_org.id, {"type": "new_alert", "data": alert_dict})
    
    return new_alert

@router.get("", response_model=List[AlertResponse])
def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db), 
    current_org: Organization = Depends(get_current_org)
):
    alerts = db.query(ThreatAlert).filter(ThreatAlert.org_id == current_org.id)\
               .order_by(desc(ThreatAlert.timestamp)).offset(skip).limit(limit).all()
    return alerts

@router.patch("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(
    alert_id: str, 
    db: Session = Depends(get_db), 
    current_org: Organization = Depends(get_current_org)
):
    alert = db.query(ThreatAlert).filter(ThreatAlert.id == alert_id, ThreatAlert.org_id == current_org.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    alert.is_acknowledged = True
    db.commit()
    db.refresh(alert)
    return alert
