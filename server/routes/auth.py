from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database import get_db
from models import Organization
from schemas import OrgCreate, OrgLogin, OrgResponse, Token
from core.security import hash_password, verify_password, generate_api_key, create_jwt_token, get_current_org

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=OrgResponse)
def register(org_data: OrgCreate, db: Session = Depends(get_db)):
    if db.query(Organization).filter(Organization.email == org_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_org = Organization(
        name=org_data.name,
        email=org_data.email,
        password_hash=hash_password(org_data.password),
        api_key=generate_api_key()
    )
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return new_org

@router.post("/login", response_model=Token)
def login(org_data: OrgLogin, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.email == org_data.email).first()
    if not org or not verify_password(org_data.password, org.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(org.id)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/rotate-key")
def rotate_key(current_org: Organization = Depends(get_current_org), db: Session = Depends(get_db)):
    new_key = generate_api_key()
    current_org.api_key = new_key
    db.commit()
    return {"api_key": new_key}

@router.get("/me", response_model=OrgResponse)
def get_me(current_org: Organization = Depends(get_current_org)):
    return current_org
