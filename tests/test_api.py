from fastapi.testclient import TestClient
from app.main import app, get_db, get_api_key
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.db_models import Base

# Setup In-Memory Test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_get_api_key():
    return "test-key"

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_api_key] = override_get_api_key

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "version": "2.0"}

def test_triage_flow():
    payload = {
        "patient_id": "PT-TEST-002",
        "age": 30,
        "gender": "Female",
        "symptoms": ["Headache"],
        "vitals": {
            "heart_rate": 70,
            "blood_pressure": "120/80",
            "temperature": 36.5,
            "oxygen_saturation": 99
        },
        "current_medications": [],
        "medical_history": []
    }

    response = client.post("/triage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "PT-TEST-002"
    assert data["urgency_level"] in ["GREEN", "YELLOW", "RED"]
