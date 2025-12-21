from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum

class UrgencyLevel(str, Enum):
    GREEN = "GREEN"    # Non-urgent
    YELLOW = "YELLOW"  # Urgent
    RED = "RED"        # Emergent

class Vitals(BaseModel):
    heart_rate: Optional[int] = Field(None, description="Beats per minute")
    blood_pressure: Optional[str] = Field(None, description="Systolic/Diastolic e.g. '120/80'")
    temperature: Optional[float] = Field(None, description="Celsius")
    oxygen_saturation: Optional[int] = Field(None, description="Percentage")

class PatientProfile(BaseModel):
    patient_id: str
    age: int
    gender: str
    symptoms: List[str] = Field(..., description="List of reported symptoms")
    vitals: Optional[Vitals] = None
    current_medications: List[str] = Field(default_factory=list)
    medical_history: List[str] = Field(default_factory=list)

class TriageReport(BaseModel):
    patient_id: str
    urgency_level: UrgencyLevel
    reasoning: str = Field(..., description="Detailed medical reasoning for the urgency level")
    recommended_action: List[str] = Field(..., description="Step by step recommendations for the care team")
    flagged_interactions: List[str] = Field(default_factory=list, description="Any dangerous drug interactions found")
