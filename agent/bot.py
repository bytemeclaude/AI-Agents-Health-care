from models.schemas import PatientProfile, TriageReport, UrgencyLevel
from tools.medical_tools import MedicalTools
from agent.brain import RiskClassifier
from agent.rag import RAGChain
from utils.logger import get_logger
from utils.language_handler import translate_symptoms, SUPPORTED_LANGUAGES
import time
import hashlib

logger = get_logger(__name__)


def _parse_systolic_bp(bp_string: str | None) -> int:
    """
    Parses systolic blood pressure from a string like '160/95' or '160'.
    Returns 120 as a safe default if parsing fails.
    """
    if not bp_string:
        return 120
    try:
        systolic_str = bp_string.split("/")[0].strip()
        return int(systolic_str)
    except (ValueError, IndexError):
        logger.warning(f"Could not parse BP value '{bp_string}', using default 120")
        return 120


class TriageAgent:
    def __init__(self):
        self.system_prompt = "You are an advanced Medical Triage AI (v2.0) — SwasthyaSahayak."
        self.tools = MedicalTools()
        self.brain = RiskClassifier()
        self.rag = RAGChain()

    def _mock_llm_reasoning(self, patient: PatientProfile, context: dict, detected_lang: str) -> TriageReport:
        """
        Synthesizes RAG context + Brain Risk Score + Tool Outputs into a TriageReport.
        """
        logger.info("Synthesizing triage data...")
        time.sleep(0.5)

        reasons = []
        urgency = UrgencyLevel.GREEN
        actions = ["Monitor symptoms at home. Rest and adequate hydration."]

        # 1. RAG Context Analysis
        rag_docs = context.get("rag_docs", [])
        if rag_docs:
            reasons.append(f"Protocol Match: {rag_docs[0][:80]}...")
            # Check all retrieved docs for RED flags
            combined_rag = " ".join(rag_docs)
            if "RED" in combined_rag:
                urgency = UrgencyLevel.RED
                actions = ["Activate Emergency Protocol — immediate physician assessment required."]
            elif "YELLOW" in combined_rag and urgency != UrgencyLevel.RED:
                urgency = UrgencyLevel.YELLOW
                actions = ["Urgent consultation with doctor within 2–4 hours. Do not delay."]

        # 2. Risk Score Analysis (Neural Net)
        risk_score = context.get("risk_score", 0.0)
        reasons.append(f"AI Vitals Risk Score: {risk_score:.2f}/1.00")

        if risk_score > 0.7:
            urgency = UrgencyLevel.RED
            reasons.append("Neural model flagged HIGH RISK based on vitals (high HR / low O2 detected).")
            actions = ["Activate Emergency Protocol — immediate physician assessment required."]
        elif risk_score > 0.4 and urgency == UrgencyLevel.GREEN:
            urgency = UrgencyLevel.YELLOW
            reasons.append("Neural model flagged MODERATE RISK — vitals warrant monitoring.")
            actions = ["Urgent consultation with doctor within 2–4 hours."]

        # 3. Drug Interactions
        interactions = context.get("interactions", [])
        if interactions:
            reasons.append(f"Drug Interaction Alert: {len(interactions)} warning(s) found.")
            if urgency == UrgencyLevel.GREEN:
                urgency = UrgencyLevel.YELLOW
                actions = ["Consult doctor about current medications before taking any new drugs."]

        # 4. Language note in report
        if detected_lang and detected_lang != "en":
            lang_name = SUPPORTED_LANGUAGES.get(detected_lang, detected_lang)
            reasons.append(f"Patient input language: {lang_name} (auto-translated to English for processing).")

        return TriageReport(
            patient_id=patient.patient_id,
            urgency_level=urgency,
            reasoning=" | ".join(reasons),
            recommended_action=actions,
            flagged_interactions=interactions,
        )

    def analyze(self, patient: PatientProfile) -> TriageReport:
        # Hash patient ID before logging — never log raw PII
        pid_hash = hashlib.sha256(patient.patient_id.encode()).hexdigest()[:8]
        logger.info(f"SwasthyaSahayak v2.0 — Patient hash: {pid_hash}")

        # Step 1: Multilingual symptom translation
        logger.info("Step 1/4: Language detection & translation")
        translated_symptoms, detected_lang = translate_symptoms(patient.symptoms)
        if detected_lang != "en":
            lang_name = SUPPORTED_LANGUAGES.get(detected_lang, detected_lang)
            logger.info(f"Translated {len(patient.symptoms)} symptom(s) from {lang_name} to English")

        # Step 2: Drug interaction check (uses Indian brand name → generic mapping)
        logger.info("Step 2/4: Checking drug interactions (Indian pharmacopoeia)")
        interactions = self.tools.check_drug_interactions(patient.current_medications)

        # Step 3: RAG retrieval on translated symptoms
        logger.info("Step 3/4: RAG retrieval from medical knowledge base")
        main_symptom = translated_symptoms[0] if translated_symptoms else "general"
        rag_docs = self.rag.retrieve(main_symptom)

        # Step 4: Neural risk scoring on vitals
        logger.info("Step 4/4: Running neural risk classifier on vitals")
        v = patient.vitals
        risk_score = 0.0
        if v:
            bp_systolic = _parse_systolic_bp(v.blood_pressure)
            risk_score = self.brain.predict(
                age=patient.age,
                hr=v.heart_rate or 80,
                temp=v.temperature or 37.0,
                o2=v.oxygen_saturation or 98,
                bp_sys=bp_systolic,
            )

        context = {
            "interactions": interactions,
            "rag_docs": rag_docs,
            "risk_score": risk_score,
        }

        # Step 5: Synthesis
        report = self._mock_llm_reasoning(patient, context, detected_lang)
        return report
