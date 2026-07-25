from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class OrgCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class OrgLogin(BaseModel):
    email: EmailStr
    password: str

class OrgResponse(BaseModel):
    id: str
    name: str
    email: str
    api_key: str
    plan: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class ClientResponse(BaseModel):
    id: str
    hostname: str
    ip_address: str
    last_seen: datetime
    is_active: bool
    class Config:
        from_attributes = True

class AlertCreate(BaseModel):
    client_id: Optional[str] = None
    severity: str
    attack_type: str
    source_ip: str
    dest_ip: str
    details: str

class AlertResponse(BaseModel):
    id: str
    org_id: str
    client_id: Optional[str]
    severity: str
    attack_type: str
    source_ip: str
    dest_ip: str
    details: str
    timestamp: datetime
    is_acknowledged: bool
    class Config:
        from_attributes = True

class GlobalMetricResponse(BaseModel):
    id: str
    round_id: str
    accuracy: float
    f1: float
    loss: float
    auc: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    created_at: datetime
    class Config:
        from_attributes = True

class RoundResponse(BaseModel):
    id: str
    round_num: int
    status: str
    global_weights_path: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    min_clients: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
