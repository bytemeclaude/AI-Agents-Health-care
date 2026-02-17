"""
SwasthyaSahayak — Medical Triage Web UI (Phase 2)

Tabs:
  1. Patient Form   — structured intake form (text, multilingual)
  2. Voice Input    — upload audio file → Whisper STT → triage
  3. WhatsApp Setup — instructions for connecting WhatsApp channel

Run from the project root:
    streamlit run ui/streamlit_app.py
"""

import sys
import os
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from models.schemas import PatientProfile, Vitals, UrgencyLevel
from agent.bot import TriageAgent

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SwasthyaSahayak — AI Medical Triage",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .urgency-red    { background:#ffe0e0; border-left:6px solid #d32f2f; padding:16px; border-radius:6px; }
    .urgency-yellow { background:#fff8e1; border-left:6px solid #f9a825; padding:16px; border-radius:6px; }
    .urgency-green  { background:#e8f5e9; border-left:6px solid #2e7d32; padding:16px; border-radius:6px; }
    .alert-box      { background:#fff3e0; border-left:4px solid #e65100; padding:12px; border-radius:4px; margin:6px 0; }
    .info-box       { background:#e3f2fd; border-left:4px solid #1565c0; padding:12px; border-radius:4px; margin:6px 0; }
    .step-box       { background:#f3e5f5; border-left:4px solid #6a1b9a; padding:10px; border-radius:4px; margin:4px 0; }
    code            { background:#f5f5f5; padding:2px 6px; border-radius:3px; font-size:0.9em; }
</style>
""", unsafe_allow_html=True)

# ── Singleton Agent ───────────────────────────────────────────────────────────
@st.cache_resource
def load_agent():
    return TriageAgent()

agent = load_agent()

# ── Sample Patients ───────────────────────────────────────────────────────────
SAMPLE_PATIENTS = {
    "— Select a demo patient —": None,
    "55M — Chest Pain + Drug Interaction (English)": {
        "patient_id": "PT-DEMO-001", "age": 55, "gender": "Male",
        "symptoms": "Crushing chest pain\nShortness of breath",
        "hr": 110, "bp": "160/95", "temp": 37.2, "o2": 94,
        "meds": "Aspirin, Warfarin, Atorvastatin",
        "history": "Hypertension, High Cholesterol",
    },
    "28F — Dengue Suspect (Hindi/Hinglish)": {
        "patient_id": "PT-DEMO-002", "age": 28, "gender": "Female",
        "symptoms": "Tez bukhar\nSeena dard\nAankhon mein dard\nDaane body par",
        "hr": 98, "bp": "100/70", "temp": 39.5, "o2": 97,
        "meds": "Crocin, Combiflam",
        "history": "None",
    },
    "45M — Malaria Suspect (Hinglish, monsoon travel)": {
        "patient_id": "PT-DEMO-003", "age": 45, "gender": "Male",
        "symptoms": "Tez bukhar with kaanpna\nThakan aur chakkar\nSir dard",
        "hr": 105, "bp": "110/75", "temp": 40.1, "o2": 95,
        "meds": "None",
        "history": "Travel to Odisha last week",
    },
    "70F — Diabetic, multiple drug interactions": {
        "patient_id": "PT-DEMO-004", "age": 70, "gender": "Female",
        "symptoms": "Chakkar aana\nKamzori\nPaseena\nHands kaanpna",
        "hr": 92, "bp": "130/85", "temp": 36.8, "o2": 98,
        "meds": "Glycomet, Glimepiride, Thyronorm, Shelcal",
        "history": "Type 2 Diabetes, Hypothyroidism",
    },
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏥 SwasthyaSahayak")
    st.caption("AI Medical Triage — India | v2.0")
    st.divider()
    st.markdown("**Supported Languages**")
    st.markdown("🇮🇳 Hindi / Hinglish\n\n🇮🇳 Tamil | Telugu\n\n🌐 English")
    st.divider()
    st.markdown("**Urgency Levels**")
    st.markdown("🔴 **RED** — Emergency\n\n🟡 **YELLOW** — Urgent\n\n🟢 **GREEN** — Non-urgent")
    st.divider()
    st.markdown("**Channels**")
    st.markdown("🖥️ Web UI (this page)\n\n📱 WhatsApp (see Setup tab)\n\n🎤 Voice Input (Tab 2)")
    st.divider()
    st.caption("⚠️ For triage support only. Not a substitute for professional medical diagnosis.")


# ── Header ────────────────────────────────────────────────────────────────────
st.title("🏥 SwasthyaSahayak — AI Medical Triage")
st.markdown("*Democratizing primary healthcare triage across India*")
st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_form, tab_voice, tab_whatsapp = st.tabs([
    "📋 Patient Form",
    "🎤 Voice Input",
    "📱 WhatsApp Setup",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Patient Form
# ═══════════════════════════════════════════════════════════════════════════════
with tab_form:
    sample_choice = st.selectbox("Quick Demo — Load a Sample Patient", list(SAMPLE_PATIENTS.keys()))
    sample = SAMPLE_PATIENTS.get(sample_choice)

    st.subheader("Patient Intake")
    c1, c2, c3 = st.columns(3)
    with c1:
        patient_id = st.text_input("Patient ID", value=sample["patient_id"] if sample else "PT-NEW-001")
        age = st.number_input("Age (years)", min_value=0, max_value=120,
                              value=int(sample["age"]) if sample else 30)
    with c2:
        gender_opts = ["Male", "Female", "Other"]
        gender = st.selectbox("Gender", gender_opts,
                              index=gender_opts.index(sample["gender"]) if sample else 0)
    with c3:
        st.markdown("**Input Language**")
        st.caption("Symptoms can be in Hindi, Hinglish, Tamil, Telugu, or English — auto-detected.")

    st.divider()
    st.subheader("Symptoms")
    st.caption("One symptom per line. Type in Hindi, Hinglish, or English.")
    symptoms_raw = st.text_area(
        "Symptoms",
        value=sample["symptoms"] if sample else "",
        height=130,
        placeholder="Crushing chest pain\nShortness of breath\n\nOR in Hinglish:\nSeena dard\nSaans phoolna",
    )

    st.subheader("Vitals *(optional)*")
    v1, v2, v3, v4 = st.columns(4)
    with v1:
        heart_rate = st.number_input("Heart Rate (bpm)", 0, 300,
                                     value=int(sample["hr"]) if sample else 80)
    with v2:
        blood_pressure = st.text_input("Blood Pressure", value=sample["bp"] if sample else "120/80",
                                       placeholder="120/80")
    with v3:
        temperature = st.number_input("Temperature (°C)", 30.0, 45.0,
                                      value=float(sample["temp"]) if sample else 37.0, step=0.1)
    with v4:
        oxygen_sat = st.number_input("O2 Saturation (%)", 50, 100,
                                     value=int(sample["o2"]) if sample else 98)

    st.subheader("Medications")
    st.caption("Comma-separated. Indian brand names supported: Crocin, Dolo, Glycomet, Ecosprin, etc.")
    meds_raw = st.text_input("Current Medications", value=sample["meds"] if sample else "",
                             placeholder="Ecosprin, Glycomet, Thyronorm, Shelcal")

    st.subheader("Medical History")
    history_raw = st.text_input("Past Conditions (comma-separated)",
                                value=sample["history"] if sample else "",
                                placeholder="Hypertension, Diabetes, Asthma")

    st.divider()
    run_btn = st.button("▶ Run Triage Analysis", type="primary", use_container_width=True)

    if run_btn:
        symptoms_list = [s.strip() for s in symptoms_raw.splitlines() if s.strip()]
        if not symptoms_list:
            st.error("Please enter at least one symptom.")
            st.stop()

        patient = PatientProfile(
            patient_id=patient_id.strip(),
            age=int(age),
            gender=gender,
            symptoms=symptoms_list,
            vitals=Vitals(
                heart_rate=int(heart_rate) or None,
                blood_pressure=blood_pressure.strip() or None,
                temperature=float(temperature) or None,
                oxygen_saturation=int(oxygen_sat) or None,
            ),
            current_medications=[m.strip() for m in meds_raw.split(",") if m.strip()],
            medical_history=[h.strip() for h in history_raw.split(",") if h.strip()],
        )

        with st.spinner("Analysing patient data..."):
            try:
                report = agent.analyze(patient)
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                st.stop()

        _display_report(report, heart_rate, oxygen_sat)


# ═══════════════════════════════════════════════════════════════════════════════
# Shared report display helper (defined after tab_form to avoid forward ref)
# ═══════════════════════════════════════════════════════════════════════════════
def _display_report(report, hr_val=None, o2_val=None):
    """Render a TriageReport with colour-coded banner and structured sections."""
    st.divider()
    st.subheader("Triage Report")
    urgency = report.urgency_level

    if urgency == UrgencyLevel.RED:
        st.markdown(
            '<div class="urgency-red"><h2>🔴 RED — EMERGENCY</h2>'
            '<p>Immediate medical attention required. Do not wait.</p></div>',
            unsafe_allow_html=True,
        )
    elif urgency == UrgencyLevel.YELLOW:
        st.markdown(
            '<div class="urgency-yellow"><h2>🟡 YELLOW — URGENT</h2>'
            '<p>Consult a doctor within 2–4 hours. Monitor closely.</p></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="urgency-green"><h2>🟢 GREEN — NON-URGENT</h2>'
            '<p>Home monitoring appropriate. See a doctor if symptoms worsen.</p></div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Patient ID", report.patient_id)
    m2.metric("Urgency",    urgency.value)
    if hr_val:  m3.metric("Heart Rate",  f"{hr_val} bpm")
    if o2_val:  m4.metric("O2 Sat",      f"{o2_val}%")

    st.subheader("Clinical Reasoning")
    for i, reason in enumerate(report.reasoning.split(" | "), 1):
        if reason.strip():
            st.markdown(f"**{i}.** {reason}")

    st.subheader("Recommended Actions")
    for action in report.recommended_action:
        st.success(f"✅ {action}")

    if report.flagged_interactions:
        st.subheader("⚠️ Drug Interaction Alerts")
        for alert in report.flagged_interactions:
            st.markdown(f'<div class="alert-box">⚠️ {alert}</div>', unsafe_allow_html=True)
    else:
        st.info("✅ No dangerous drug interactions detected.")

    with st.expander("View TOON Report (for Doctor)"):
        from utils.toons import to_toon
        st.code(to_toon(report), language="yaml")


# Monkey-patch the function into scope for run_btn callback (Streamlit limitation)
import types
_display_report_fn = _display_report


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Voice Input
# ═══════════════════════════════════════════════════════════════════════════════
with tab_voice:
    st.subheader("🎤 Voice Input — Describe Symptoms by Audio")
    st.markdown(
        "Upload a voice recording describing your symptoms. "
        "SwasthyaSahayak will transcribe it (supports Hindi, Tamil, Telugu, English) "
        "and run a triage analysis."
    )

    st.markdown(
        '<div class="info-box">'
        "💡 <b>Tip:</b> Simply say your symptoms naturally — "
        "e.g. <i>\"Mujhe tez bukhar hai, seena dard ho raha hai aur saans lene mein takleef hai\"</i>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    audio_file = st.file_uploader(
        "Upload Audio File",
        type=["ogg", "mp3", "wav", "m4a", "webm", "amr"],
        help="WhatsApp voice notes (.ogg), MP3, WAV, M4A, WebM supported.",
    )

    # Voice patient metadata
    st.subheader("Patient Info")
    vc1, vc2, vc3 = st.columns(3)
    with vc1:
        v_patient_id = st.text_input("Patient ID", value="PT-VOICE-001", key="v_pid")
        v_age        = st.number_input("Age", 0, 120, value=35, key="v_age")
    with vc2:
        v_gender     = st.selectbox("Gender", ["Male", "Female", "Other"], key="v_gender")
    with vc3:
        st.caption("Vitals and medications can be added after transcription.")

    v_meds = st.text_input(
        "Current Medications (optional)",
        placeholder="Crocin, Glycomet, ...",
        key="v_meds",
    )

    transcribe_btn = st.button("🔊 Transcribe & Analyse", type="primary",
                               disabled=(audio_file is None), use_container_width=True)

    if audio_file is not None:
        st.audio(audio_file)

    if transcribe_btn and audio_file is not None:
        suffix_map = {
            "audio/ogg":  ".ogg", "audio/mpeg": ".mp3", "audio/wav": ".wav",
            "audio/mp4":  ".m4a", "audio/webm": ".webm", "audio/amr": ".amr",
        }
        file_ext = "." + audio_file.name.rsplit(".", 1)[-1] if "." in audio_file.name else ".ogg"

        with st.spinner("Transcribing audio with Whisper STT..."):
            try:
                from channels.voice_handler import transcribe_audio_bytes
                result = transcribe_audio_bytes(audio_file.read(), suffix=file_ext)
                transcript  = result["text"]
                lang_name   = result["language_name"]
                duration_s  = result.get("duration_s", 0)
            except RuntimeError as e:
                st.error(str(e))
                st.info(
                    "**To enable Voice Input:** `pip install openai-whisper`\n\n"
                    "Also install ffmpeg: https://ffmpeg.org/download.html"
                )
                st.stop()
            except Exception as e:
                st.error(f"Transcription failed: {e}")
                st.stop()

        st.success(f"✅ Transcribed ({lang_name}, {duration_s:.1f}s)")
        st.markdown("**Transcribed Text:**")
        st.info(f'"{transcript}"')

        # Parse symptoms from transcript (newline/comma split)
        import re
        symptoms_from_voice = [s.strip() for s in re.split(r"[,।\n]+", transcript) if s.strip()]
        if not symptoms_from_voice:
            symptoms_from_voice = [transcript]

        st.markdown(f"**Detected {len(symptoms_from_voice)} symptom(s):** {', '.join(symptoms_from_voice)}")

        with st.spinner("Running triage analysis..."):
            patient = PatientProfile(
                patient_id=v_patient_id.strip(),
                age=int(v_age),
                gender=v_gender,
                symptoms=symptoms_from_voice,
                vitals=None,
                current_medications=[m.strip() for m in v_meds.split(",") if m.strip()],
                medical_history=[],
            )
            try:
                report = agent.analyze(patient)
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                st.stop()

        _display_report_fn(report)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — WhatsApp Setup
# ═══════════════════════════════════════════════════════════════════════════════
with tab_whatsapp:
    st.subheader("📱 WhatsApp Channel Setup")
    st.markdown(
        "Connect SwasthyaSahayak to WhatsApp so patients can receive AI triage "
        "directly on their phones — no app download required."
    )

    st.markdown(
        '<div class="info-box">'
        "📌 <b>Requirements:</b> A <a href='https://www.twilio.com' target='_blank'>Twilio account</a> "
        "(free sandbox available for testing) and a server with a public HTTPS URL."
        "</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### Step-by-Step Setup")

    steps = [
        ("1. Install dependencies",
         "```bash\npip install twilio openai-whisper\n```\n"
         "Also install **ffmpeg** for voice note support:\n"
         "- Windows: `winget install ffmpeg`\n"
         "- Ubuntu: `sudo apt install ffmpeg`\n"
         "- macOS: `brew install ffmpeg`"),

        ("2. Set environment variables",
         "Create a `.env` file in the project root:\n"
         "```\nTWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n"
         "TWILIO_AUTH_TOKEN=your_auth_token_here\n"
         "TWILIO_WHATSAPP_FROM=whatsapp:+14155238886\n```\n"
         "Find your credentials at: **console.twilio.com → Account Info**"),

        ("3. Start the WhatsApp webhook server",
         "```bash\nuvicorn app.whatsapp_webhook:app --host 0.0.0.0 --port 8001\n```"),

        ("4. Expose locally with ngrok (for testing)",
         "```bash\nngrok http 8001\n```\n"
         "Copy the HTTPS URL — e.g. `https://abc123.ngrok.io`"),

        ("5. Configure Twilio Sandbox",
         "Go to **Twilio Console → Messaging → Try it out → Send a WhatsApp message**\n\n"
         "Under *Sandbox Settings*, set:\n"
         "- **When a message comes in:** `https://abc123.ngrok.io/whatsapp/incoming`\n"
         "- **Method:** `POST`\n\n"
         "Save settings."),

        ("6. Activate the sandbox",
         "From your WhatsApp, send:\n"
         "```\njoin <your-sandbox-keyword>\n```\n"
         "to the Twilio sandbox number shown in the console.\n\n"
         "Then send any message to begin your first triage session!"),
    ]

    for title, content in steps:
        with st.expander(title, expanded=False):
            st.markdown(content)

    st.divider()
    st.markdown("### Conversation Flow Preview")

    col_user, col_bot = st.columns(2)
    with col_user:
        st.markdown("**👤 Patient (WhatsApp)**")
        conversation_user = [
            "Namaste",
            "Tez bukhar, seena dard, saans lene mein takleef",
            "45",
            "Male",
            "Crocin, Combiflam",
            "90bpm, 38.5°C, 97%",
        ]
        for msg in conversation_user:
            st.markdown(f'> 💬 *"{msg}"*')
            st.markdown("")

    with col_bot:
        st.markdown("**🤖 SwasthyaSahayak (Bot)**")
        conversation_bot = [
            "Welcome to SwasthyaSahayak 🏥 — describe your symptoms in Hindi, Hinglish, or English.",
            "Got it — 3 symptoms noted.\n\nHow old is the patient?",
            "What is the patient's gender? (Male / Female / Other)",
            "Any current medications? List them or type None.",
            "Any vitals available? (HR, BP, Temp, O2) — or type Skip.",
            "🔴 *RED — EMERGENCY*\nImmediate attention needed.\n⚠️ Drug alert: Combiflam + Aspirin interaction detected.",
        ]
        for msg in conversation_bot:
            st.info(msg)

    st.divider()
    st.markdown("### Health Check")
    st.markdown(
        "Once running, verify your webhook server at:\n"
        "```\nGET http://localhost:8001/whatsapp/health\n```"
    )

    col_env1, col_env2 = st.columns(2)
    with col_env1:
        sid_set = bool(os.getenv("TWILIO_ACCOUNT_SID", ""))
        token_set = bool(os.getenv("TWILIO_AUTH_TOKEN", ""))
        st.markdown("**Current Environment Status:**")
        st.markdown(f"{'✅' if sid_set else '❌'} `TWILIO_ACCOUNT_SID` — {'set' if sid_set else 'not set'}")
        st.markdown(f"{'✅' if token_set else '❌'} `TWILIO_AUTH_TOKEN` — {'set' if token_set else 'not set'}")
        st.markdown(f"📞 `TWILIO_WHATSAPP_FROM` — `{os.getenv('TWILIO_WHATSAPP_FROM', 'not set')}`")

    with col_env2:
        try:
            from channels.voice_handler import _load_whisper_model
            st.markdown("**Voice (Whisper) Status:**")
            st.markdown("✅ `openai-whisper` — installed")
        except Exception:
            st.markdown("**Voice (Whisper) Status:**")
            st.markdown("❌ `openai-whisper` — not installed (`pip install openai-whisper`)")


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "SwasthyaSahayak v2.0 — KiranaSync Health | "
    "Phase 1 ✅ + Phase 2 ✅ | "
    "For testing only. Not a substitute for professional medical advice. "
    "DPDP Act compliant — no patient data stored by this UI."
)
