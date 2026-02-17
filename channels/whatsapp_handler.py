"""
SwasthyaSahayak — WhatsApp Conversation State Machine.

Manages multi-turn patient intake conversations over WhatsApp.
Each phone number gets its own session that expires after 30 minutes of inactivity.

Conversation flow:
  1. User sends first message → Welcome + ask for symptoms
  2. Bot collects: symptoms → age → gender → medications → vitals
  3. Runs TriageAgent.analyze()
  4. Sends formatted WhatsApp report back to user
"""

import re
import uuid
from datetime import datetime, timedelta
from enum import Enum

from models.schemas import PatientProfile, Vitals
from agent.bot import TriageAgent
from utils.toons import to_toon
from utils.logger import get_logger

logger = get_logger(__name__)

SESSION_TTL_MINUTES = 30

# Trigger words that restart the conversation
RESTART_TRIGGERS = {"restart", "reset", "start", "hi", "hello", "namaste", "hlo",
                    "hey", "ola", "namaskar", "shuru", "dobara"}


class ConversationState(Enum):
    AWAITING_SYMPTOMS   = "AWAITING_SYMPTOMS"
    AWAITING_AGE        = "AWAITING_AGE"
    AWAITING_GENDER     = "AWAITING_GENDER"
    AWAITING_MEDICATIONS = "AWAITING_MEDICATIONS"
    AWAITING_VITALS     = "AWAITING_VITALS"
    COMPLETE            = "COMPLETE"


# In-memory session store keyed by phone number.
# Replace with Redis for horizontal scaling in production.
_sessions: dict[str, dict] = {}

_agent: TriageAgent | None = None


def _get_agent() -> TriageAgent:
    """Singleton TriageAgent — loaded once, reused across sessions."""
    global _agent
    if _agent is None:
        _agent = TriageAgent()
    return _agent


def _purge_expired_sessions() -> None:
    """Remove sessions that have been idle beyond SESSION_TTL_MINUTES."""
    cutoff = datetime.utcnow() - timedelta(minutes=SESSION_TTL_MINUTES)
    expired = [phone for phone, s in _sessions.items() if s["updated_at"] < cutoff]
    for phone in expired:
        del _sessions[phone]
    if expired:
        logger.info(f"Purged {len(expired)} expired WhatsApp session(s).")


def _get_or_create_session(phone_number: str) -> dict:
    """Return existing session or create a fresh one for the phone number."""
    _purge_expired_sessions()
    if phone_number not in _sessions:
        _sessions[phone_number] = {
            "state":       ConversationState.AWAITING_SYMPTOMS,
            "patient_id":  f"WA-{uuid.uuid4().hex[:8].upper()}",
            "phone":       phone_number,
            "symptoms":    [],
            "age":         None,
            "gender":      None,
            "medications": [],
            "vitals_raw":  None,
            "created_at":  datetime.utcnow(),
            "updated_at":  datetime.utcnow(),
        }
        logger.info(f"New WhatsApp session: {_sessions[phone_number]['patient_id']}")
    _sessions[phone_number]["updated_at"] = datetime.utcnow()
    return _sessions[phone_number]


def _clear_session(phone_number: str) -> None:
    """Delete session after triage is complete or on restart."""
    _sessions.pop(phone_number, None)


def _parse_vitals_from_text(text: str) -> Vitals | None:
    """
    Best-effort vitals extraction from free-form text.
    Handles inputs like: '90bpm, 130/85, 38.5c, 97%'
    Returns None if no valid vitals found.
    """
    t = text.lower()
    hr = bp = temp = o2 = None

    hr_match = re.search(r'(\d{2,3})\s*(bpm|pulse|hr|heart|nabz)', t)
    if hr_match:
        val = int(hr_match.group(1))
        if 30 <= val <= 250:
            hr = val

    bp_match = re.search(r'(\d{2,3})\s*/\s*(\d{2,3})', t)
    if bp_match:
        bp = f"{bp_match.group(1)}/{bp_match.group(2)}"

    temp_match = re.search(r'(\d{2}\.?\d?)\s*(c|celsius|°c|degree)?', t)
    if temp_match:
        val = float(temp_match.group(1))
        if 35.0 <= val <= 42.5:
            temp = val

    o2_match = re.search(r'(\d{2,3})\s*(%|percent|o2|spo2|oxygen|saturation)', t)
    if o2_match:
        val = int(o2_match.group(1))
        if 50 <= val <= 100:
            o2 = val

    if any(v is not None for v in [hr, bp, temp, o2]):
        return Vitals(heart_rate=hr, blood_pressure=bp, temperature=temp, oxygen_saturation=o2)
    return None


def _format_whatsapp_report(report) -> str:
    """Format a TriageReport as a WhatsApp-friendly string with emoji and bold."""
    urgency_emoji = {
        "RED":    "🔴",
        "YELLOW": "🟡",
        "GREEN":  "🟢",
    }.get(report.urgency_level.value, "⚪")

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━",
        "🏥 *SwasthyaSahayak Report*",
        "━━━━━━━━━━━━━━━━━━━━━",
        f"Patient ID: {report.patient_id}",
        f"Urgency: {urgency_emoji} *{report.urgency_level.value}*",
        "",
        "*Clinical Assessment:*",
    ]

    for i, reason in enumerate(report.reasoning.split(" | "), 1):
        lines.append(f"  {i}. {reason}")

    lines += ["", "*Recommended Action:*"]
    for action in report.recommended_action:
        lines.append(f"  • {action}")

    if report.flagged_interactions:
        lines += ["", "⚠️ *Drug Interaction Alerts:*"]
        for alert in report.flagged_interactions:
            lines.append(f"  ⚠ {alert}")

    lines += [
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        "_This is AI-assisted triage only. Please consult a qualified doctor for diagnosis and treatment._",
        "",
        "_Type *restart* to begin a new assessment._",
    ]
    return "\n".join(lines)


WELCOME_MESSAGE = (
    "🏥 *SwasthyaSahayak* — AI Medical Triage\n"
    "━━━━━━━━━━━━━━━━━━━━━\n"
    "Namaste! I am your AI health assistant.\n\n"
    "Please describe your symptoms. You can type in:\n"
    "🇮🇳 Hindi / Hinglish  |  🇮🇳 Tamil / Telugu  |  🌐 English\n\n"
    "_Example (English):_ Fever, chest pain, difficulty breathing\n"
    "_Example (Hinglish):_ Tez bukhar, seena dard, saans ki takleef\n\n"
    "Type *restart* at any time to start over."
)


def process_message(phone_number: str, message_text: str) -> str:
    """
    Process one incoming WhatsApp message and return the bot's reply.

    Args:
        phone_number: The sender's phone number (e.g. 'whatsapp:+919876543210')
        message_text: The text content of the message (already transcribed if voice)

    Returns:
        The reply string to send back to the user.
    """
    session = _get_or_create_session(phone_number)
    text = message_text.strip()

    # Allow restart from any state
    if text.lower() in RESTART_TRIGGERS:
        _clear_session(phone_number)
        return WELCOME_MESSAGE

    state = session["state"]

    # ── AWAITING_SYMPTOMS ────────────────────────────────────────────────────
    if state == ConversationState.AWAITING_SYMPTOMS:
        # Treat entire message as symptom list (comma or newline separated)
        symptoms = [s.strip() for s in re.split(r"[,\n]+", text) if s.strip()]
        if not symptoms:
            return "Please describe at least one symptom so I can help you."
        session["symptoms"] = symptoms
        session["state"] = ConversationState.AWAITING_AGE
        count = len(symptoms)
        return (
            f"Thank you — *{count} symptom{'s' if count > 1 else ''}* noted.\n\n"
            "How old is the patient?\n"
            "_Please reply with age in years (e.g. *45*)_"
        )

    # ── AWAITING_AGE ─────────────────────────────────────────────────────────
    elif state == ConversationState.AWAITING_AGE:
        digits = re.sub(r"[^\d]", "", text)
        if not digits or not (0 < int(digits) < 120):
            return "Please enter a valid age in years.\n_Example: *35*_"
        session["age"] = int(digits)
        session["state"] = ConversationState.AWAITING_GENDER
        return (
            "What is the patient's gender?\n\n"
            "Reply: *Male* / *Female* / *Other*\n"
            "_( M / F / O also accepted )_"
        )

    # ── AWAITING_GENDER ───────────────────────────────────────────────────────
    elif state == ConversationState.AWAITING_GENDER:
        t = text.lower().strip()
        if t in ("male", "m", "man", "purush", "ladka", "boy"):
            session["gender"] = "Male"
        elif t in ("female", "f", "woman", "mahila", "aurat", "ladki", "girl"):
            session["gender"] = "Female"
        else:
            session["gender"] = "Other"
        session["state"] = ConversationState.AWAITING_MEDICATIONS
        return (
            "Is the patient currently taking any medications?\n\n"
            "Please list them separated by commas, or type *None*.\n"
            "_Indian brand names accepted: Crocin, Glycomet, Ecosprin, Thyronorm, etc._"
        )

    # ── AWAITING_MEDICATIONS ─────────────────────────────────────────────────
    elif state == ConversationState.AWAITING_MEDICATIONS:
        t = text.lower().strip()
        if t in ("none", "no", "nahi", "nahin", "nahi hai", "koi nahi", "nil", "nothing", "n/a"):
            session["medications"] = []
        else:
            session["medications"] = [m.strip() for m in re.split(r"[,\n]+", text) if m.strip()]
        session["state"] = ConversationState.AWAITING_VITALS
        return (
            "Do you have any current vitals? _(Type *Skip* if not available)_\n\n"
            "You can share any or all of:\n"
            "  • Heart rate — e.g. *90 bpm*\n"
            "  • Blood pressure — e.g. *130/85*\n"
            "  • Temperature — e.g. *38.5°C*\n"
            "  • O2 saturation — e.g. *97%*\n\n"
            "_Example: 90bpm, 130/85, 38.5, 97%_"
        )

    # ── AWAITING_VITALS → run analysis ───────────────────────────────────────
    elif state == ConversationState.AWAITING_VITALS:
        t = text.lower().strip()
        vitals = None
        if t not in ("skip", "no", "nahi", "none", "n/a", "nil", "don't know", "pata nahi"):
            session["vitals_raw"] = text
            vitals = _parse_vitals_from_text(text)

        session["state"] = ConversationState.COMPLETE

        patient = PatientProfile(
            patient_id=session["patient_id"],
            age=session["age"],
            gender=session["gender"],
            symptoms=session["symptoms"],
            vitals=vitals,
            current_medications=session["medications"],
            medical_history=[],
        )

        logger.info(f"Running triage for WhatsApp session {session['patient_id']}")
        try:
            report = _get_agent().analyze(patient)
        except Exception as e:
            logger.error(f"Triage analysis failed for {session['patient_id']}: {e}")
            _clear_session(phone_number)
            return (
                "⚠️ I encountered an error during analysis.\n"
                "Please try again or visit your nearest doctor.\n\n"
                "_Type *restart* to begin again._"
            )

        reply = _format_whatsapp_report(report)
        _clear_session(phone_number)
        return reply

    # Fallback — should not normally reach here
    else:
        _clear_session(phone_number)
        return WELCOME_MESSAGE
