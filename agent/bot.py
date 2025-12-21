from models.schemas import PatientProfile, TriageReport, UrgencyLevel
from tools.medical_tools import MedicalTools
from agent.brain import RiskClassifier
from agent.rag import RAGChain
import time

class TriageAgent:
    def __init__(self):
        self.system_prompt = "You are an advanced Medical Triage AI (v2.0)."
        self.tools = MedicalTools()
        
        # v2.0 Upgrades
        self.brain = RiskClassifier()
        self.rag = RAGChain()

    def _mock_llm_reasoning(self, patient: PatientProfile, context: dict) -> TriageReport:
        """
        Synthesizes RAG context + Brain Risk Score + Tool Outputs.
        """
        print("   [AGENT] Synthesizing Data...")
        time.sleep(1)
        
        reasons = []
        urgency = UrgencyLevel.GREEN
        actions = ["Monitor symptoms"]
        
        # 1. RAG Context Analysis
        rag_docs = context.get("rag_docs", [])
        reasons.append(f"Knowledge Retrieved: {rag_docs[0][:50]}...")
        
        if "RED" in str(rag_docs):
            urgency = UrgencyLevel.RED
            actions = ["Activate Emergency Protocol"]

        # 2. Risk Score Analysis (PyTorch)
        risk_score = context.get("risk_score", 0.0)
        reasons.append(f"AI Risk Score: {risk_score:.2f}")
        
        if risk_score > 0.7:
             urgency = UrgencyLevel.RED
             reasons.append("High Risk Score detected by Neural Net.")
        
        # 3. Drug Interactions
        interactions = context.get("interactions", [])
        if interactions:
             reasons.append(f"Drug Warnings: {len(interactions)} found.")

        return TriageReport(
            patient_id=patient.patient_id,
            urgency_level=urgency,
            reasoning=" | ".join(reasons),
            recommended_action=actions,
            flagged_interactions=interactions
        )

    def analyze(self, patient: PatientProfile) -> TriageReport:
        print(f"\n--- 🏥 Agent v2.0 Activated for Patient: {patient.patient_id} ---")
        
        # Step 1: Tool Use
        interactions = self.tools.check_drug_interactions(patient.current_medications)
        
        # Step 2: RAG Retrieval
        main_symptom = patient.symptoms[0] if patient.symptoms else "general"
        print(f"   [AGENT] Querying RAG for: '{main_symptom}'")
        rag_docs = self.rag.retrieve(main_symptom)
        
        # Step 3: Neural Probabilistic Modeling (Brain)
        print(f"   [AGENT] Running Risk Model on Vitals...")
        v = patient.vitals
        risk_score = 0.0
        if v:
            risk_score = self.brain.predict(
                patient.age, 
                v.heart_rate or 80, 
                v.temperature or 37, 
                v.oxygen_saturation or 98, 
                120 # Default BP Sys
            )
        
        context = {
            "interactions": interactions,
            "rag_docs": rag_docs,
            "risk_score": risk_score
        }
        
        # Step 4: Synthesis
        report = self._mock_llm_reasoning(patient, context)
        
        return report
