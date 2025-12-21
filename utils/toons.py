from models.schemas import TriageReport

def to_toon(report: TriageReport) -> str:
    """
    Converts a TriageReport into TOONs (Token-Oriented Object Notation) format.
    TOONs emphasizes indentation and minimal syntax for LLM readability.
    """
    # Placeholder for Rust optimization in future
    # try:
    #     import medical_agent_core
    #     return medical_agent_core.fast_toon_format(report.json())
    # except ImportError:
    #     pass
    
    toon_str = f"""
TriageReport
    patient_id: {report.patient_id}
    urgency: {report.urgency_level.value}
    reasoning: {report.reasoning}
    actions:
"""
    for action in report.recommended_action:
        toon_str += f"        - {action}\n"
        
    if report.flagged_interactions:
        toon_str += "    alerts:\n"
        for alert in report.flagged_interactions:
            toon_str += f"        - {alert}\n"
            
    return toon_str.strip()
