from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader, APIKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models.schemas import PatientProfile, TriageReport
from models.db_models import Base, PatientDB, TriageRecordDB
from agent.bot import TriageAgent
import os
import uvicorn

# 1. Database Setup
DATABASE_URL = "sqlite:///./medical_triage.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 2. Security Setup
API_KEY = os.getenv("API_KEY", "secure-health-key-123")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Could not validate credentials")

# 3. App Setup
app = FastAPI(
    title="Medical Triage AI API",
    version="2.0",
    description="Enterprise-grade AI Triage System"
)

# Initialize Agent
agent = TriageAgent()

@app.get("/")
def health_check():
    return {"status": "healthy", "version": "2.0"}

@app.post("/triage", response_model=TriageReport)
def run_triage(patient: PatientProfile, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    """
    Analyzes patient data and returns a triage report.
    Persists data to the database for audit trails.
    """
    # Run Analysis
    try:
        report = agent.analyze(patient)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Persist to DB
    # 1. Find or Create Patient
    db_patient = db.query(PatientDB).filter(PatientDB.patient_id == patient.patient_id).first()
    if not db_patient:
        db_patient = PatientDB(
            patient_id=patient.patient_id,
            age=patient.age,
            gender=patient.gender,
            medical_history=patient.medical_history
        )
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)

    # 2. Save Record
    db_record = TriageRecordDB(
        patient_db_id=db_patient.id,
        symptoms=patient.symptoms,
        vitals=patient.vitals.model_dump() if patient.vitals else {},
        medications=patient.current_medications,
        urgency_level=report.urgency_level.value,
        # risk_score logic is hidden in agent, simplified here or we need to extract it
        reasoning=report.reasoning,
        recommended_actions=report.recommended_action,
        flagged_interactions=report.flagged_interactions
    )
    db.add(db_record)
    db.commit()

    return report

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
