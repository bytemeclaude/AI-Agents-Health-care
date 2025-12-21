import sys
from models.schemas import PatientProfile, Vitals
from agent.bot import TriageAgent
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.json import JSON

console = Console()

def main():
    agent = TriageAgent()
    
    # 1. Create a Mock Patient Scenario (Step 1 & 2)
    # Scenario: 55yo Male with Chest Pain and Drug Interaction risk
    patient = PatientProfile(
        patient_id="PT-2024-001",
        age=55,
        gender="Male",
        symptoms=["Crushing chest pain", "Shortness of breath"],
        vitals=Vitals(
            heart_rate=110,
            blood_pressure="160/95",
            temperature=37.2,
            oxygen_saturation=94
        ),
        current_medications=["Aspirin", "Warfarin", "Atorvastatin"],
        medical_history=["Hypertension", "High Cholesterol"]
    )
    
    console.print(Panel(f"[bold blue]New Patient Intake:[/bold blue] {patient.patient_id}", subtitle="Step 1: Intake"))
    console.print(f"Symptoms: {patient.symptoms}")
    console.print(f"Meds: {patient.current_medications}")

    # 2. Run Agent (Steps 3, 4, 6)
    report = agent.analyze(patient)
    
    # 3. Output Results (Step 8: TOONs Format)
    from utils.toons import to_toon
    
    console.print(Panel(to_toon(report), title="Final Assessment (TOONs Format)", border_style="bold magenta"))

if __name__ == "__main__":
    main()
