import time
from utils.logger import get_logger

logger = get_logger(__name__)

class MedicalTools:
    
    @staticmethod
    def check_drug_interactions(medications: list[str]) -> list[str]:
        """
        Simulates checking for drug interactions.
        Returns a list of warnings.
        """
        logger.info(f"Checking interactions for {len(medications)} medications")
        time.sleep(1) # Simulate API latency
        
        interactions = []
        # Mock logic
        meds_lower = [m.lower() for m in medications]
        if "aspirin" in meds_lower and "warfarin" in meds_lower:
            interactions.append("CRITICAL: Aspirin and Warfarin increase bleeding risk.")
        if "lisinopril" in meds_lower and "potassium" in meds_lower:
            interactions.append("WARNING: Lisinopril and Potassium supplements can cause hyperkalemia.")
            
        return interactions

    @staticmethod
    def search_medical_guidelines(symptom: str) -> str:
        """
        Simulates searching medical databases for triage protocols.
        """
        logger.info(f"Searching guidelines for symptom")
        time.sleep(1) # Simulate Search
        
        symptom = symptom.lower()
        if "chest pain" in symptom:
            return "PROTOCOL: Chest pain -> Immediate ECG, Troponin I/T. Rule out ACS. Triage Level: RED."
        if "fever" in symptom:
            return "PROTOCOL: Fever -> Check temp. If > 40C or altered mental status: RED. If > 38C with no distress: GREEN/YELLOW."
        if "headache" in symptom:
            return "PROTOCOL: Headache -> Rule out meningitis/stroke. Sudden onset 'thunderclap': RED. Tension/Migraine: GREEN."
            
        return "PROTOCOL: Generic triage. Assess ABCs (Airway, Breathing, Circulation)."
