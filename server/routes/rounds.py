import os
import uuid
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from core.database import get_db
from models import FLRound, ClientWeight, Organization
from schemas import RoundResponse
from core.security import get_current_org
from core.fedavg import process_round_aggregation, WEIGHTS_DIR
from typing import List

router = APIRouter(prefix="/rounds", tags=["rounds"])

def check_and_aggregate(db: Session, round_id: str):
    fl_round = db.query(FLRound).filter(FLRound.id == round_id).first()
    if not fl_round or fl_round.status != "active":
        return
        
    client_weights_count = db.query(ClientWeight).filter(ClientWeight.round_id == round_id).count()
    if client_weights_count >= fl_round.min_clients:
        fl_round.status = "aggregating"
        db.commit()
        
        # Perform aggregation
        process_round_aggregation(db, fl_round)
        
        # Auto-start new round
        new_round = FLRound(
            round_num=fl_round.round_num + 1,
            status="active"
        )
        db.add(new_round)
        db.commit()

@router.get("/current")
def get_current_round(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_org)):
    active_round = db.query(FLRound).filter(FLRound.status == "active").order_by(desc(FLRound.round_num)).first()
    if not active_round:
        raise HTTPException(status_code=404, detail="No active round found")
        
    weights_url = None
    if active_round.round_num > 1:
        prev_round = db.query(FLRound).filter(FLRound.round_num == active_round.round_num - 1).first()
        if prev_round and prev_round.global_weights_path:
            weights_url = f"/rounds/{prev_round.id}/weights"
            
    return {
        "round_id": active_round.id,
        "round_num": active_round.round_num,
        "weights_url": weights_url
    }

@router.get("/{round_id}/weights")
def get_round_weights(round_id: str, db: Session = Depends(get_db)):
    fl_round = db.query(FLRound).filter(FLRound.id == round_id).first()
    if not fl_round or not fl_round.global_weights_path:
        raise HTTPException(status_code=404, detail="Weights not found")
        
    try:
        # Load .npy and convert to list for JSON serialization
        weights = np.load(fl_round.global_weights_path, allow_pickle=True)
        # Convert numpy arrays to lists
        weights_list = [w.tolist() if isinstance(w, np.ndarray) else w for w in weights]
        return weights_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{round_id}/submit")
async def submit_weights(
    round_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    n_samples: int = Form(...),
    client_id: str = Form("dummy_client"),
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_org)
):
    fl_round = db.query(FLRound).filter(FLRound.id == round_id).first()
    if not fl_round or fl_round.status != "active":
        raise HTTPException(status_code=400, detail="Round is not active")
        
    content = await file.read()
    filename = f"{uuid.uuid4()}.npy"
    file_path = os.path.join(WEIGHTS_DIR, filename)
    
    with open(file_path, "wb") as f:
        f.write(content)
        
    cw = ClientWeight(
        round_id=round_id,
        client_id=client_id, # Simplified for mockup
        org_id=current_org.id,
        n_samples=n_samples,
        weights_path=file_path
    )
    db.add(cw)
    db.commit()
    
    background_tasks.add_task(check_and_aggregate, db, round_id)
    return {"status": "success"}

@router.get("/", response_model=List[RoundResponse])
def list_rounds(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_org)):
    rounds = db.query(FLRound).order_by(desc(FLRound.round_num)).all()
    return rounds

@router.post("/start", response_model=RoundResponse)
def start_round(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_org)):
    active = db.query(FLRound).filter(FLRound.status == "active").first()
    if active:
        raise HTTPException(status_code=400, detail="A round is already active")
        
    latest = db.query(FLRound).order_by(desc(FLRound.round_num)).first()
    round_num = latest.round_num + 1 if latest else 1
    
    new_round = FLRound(round_num=round_num, status="active")
    db.add(new_round)
    db.commit()
    db.refresh(new_round)
    return new_round
