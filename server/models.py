import datetime
import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    api_key = Column(String, unique=True, index=True)
    plan = Column(String, default="starter") # starter/pro/enterprise
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    clients = relationship("Client", back_populates="organization")
    alerts = relationship("ThreatAlert", back_populates="organization")

class Client(Base):
    __tablename__ = "clients"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id"))
    hostname = Column(String)
    ip_address = Column(String)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)

    organization = relationship("Organization", back_populates="clients")
    weights = relationship("ClientWeight", back_populates="client")

class FLRound(Base):
    __tablename__ = "fl_rounds"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    round_num = Column(Integer, unique=True, index=True)
    status = Column(String, default="pending") # pending/active/aggregating/complete
    global_weights_path = Column(String, nullable=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    min_clients = Column(Integer, default=2)

    client_weights = relationship("ClientWeight", back_populates="fl_round")
    metrics = relationship("GlobalMetric", back_populates="fl_round")

class ClientWeight(Base):
    __tablename__ = "client_weights"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    round_id = Column(String, ForeignKey("fl_rounds.id"))
    client_id = Column(String, ForeignKey("clients.id"))
    org_id = Column(String, ForeignKey("organizations.id"))
    n_samples = Column(Integer)
    weights_path = Column(String)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

    fl_round = relationship("FLRound", back_populates="client_weights")
    client = relationship("Client", back_populates="weights")

class GlobalMetric(Base):
    __tablename__ = "global_metrics"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    round_id = Column(String, ForeignKey("fl_rounds.id"))
    accuracy = Column(Float)
    f1 = Column(Float)
    loss = Column(Float)
    auc = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    fl_round = relationship("FLRound", back_populates="metrics")

class ThreatAlert(Base):
    __tablename__ = "threat_alerts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("organizations.id"))
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)
    severity = Column(String) # low/medium/high/critical
    attack_type = Column(String)
    source_ip = Column(String)
    dest_ip = Column(String)
    details = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    is_acknowledged = Column(Boolean, default=False)

    organization = relationship("Organization", back_populates="alerts")
