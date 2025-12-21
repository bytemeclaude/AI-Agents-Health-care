from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class PatientDB(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, unique=True, index=True)
    age = Column(Integer)
    gender = Column(String)
    medical_history = Column(JSON) # List of strings
    created_at = Column(DateTime, default=datetime.utcnow)

    triage_records = relationship("TriageRecordDB", back_populates="patient")

class TriageRecordDB(Base):
    __tablename__ = "triage_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_db_id = Column(Integer, ForeignKey("patients.id"))

    # Input snapshot
    symptoms = Column(JSON)
    vitals = Column(JSON) # Store as JSON object
    medications = Column(JSON)

    # Output
    urgency_level = Column(String)
    risk_score = Column(Float, nullable=True)
    reasoning = Column(Text)
    recommended_actions = Column(JSON)
    flagged_interactions = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("PatientDB", back_populates="triage_records")
