# Product Requirements Document (PRD): AI-Powered Medical Triage Agent for India

## 1. Executive Summary
**Project Name:** "SwasthyaSahayak" (proposed name) / KiranaSync Health Agent
**Vision:** To democratize access to primary healthcare triage in India by leveraging AI agents, widely accessible communication channels (WhatsApp), and local community touchpoints (Kirana stores/Pharmacies), drastically reducing time-to-care and costs.

## 2. Market Analysis (Indian Context)
### 2.1 Problem Statement
-   **Doctor-Patient Ratio:** Skewed (1:1456 vs WHO recomm. 1:1000). Rural areas are significantly underserved.
-   **Language Barrier:** Medical advice is often in English; patients speak regional languages (Hindi, Tamil, Telugu, etc.).
-   **Access:** High reliance on local pharmacists or "quacks" due to lack of immediate doctor availability.
-   **Cost:** High out-of-pocket expenditure.
-   **Digital Literacy:** High smartphone penetration but varying levels of app proficiency. Interface must be conversational.

### 2.2 Opportunity
-   **AI Agents:** Can handle L1 triage (symptom analysis) instantly, 24/7.
-   **Rust Core:** Existing efficient architecture enables deployment on low-cost edge devices or efficient cloud scaling.
-   **WhatsApp:** Ubiquitous platform for delivery.

## 3. User Personas
### 3.1 The "Rural Patient" (End User)
-   **Profile:** Smartphone user, comfortable with Voice/WhatsApp, vernacular language speaker.
-   **Goal:** Quick advice for symptoms ("Is this fever dangerous?").
-   **Pain Point:** Doesn't want to travel 20km for a minor issue.

### 3.2 The "Kirana Health Partner" (Intermediary)
-   **Profile:** Local shop owner/pharmacist. Trusted by the community.
-   **Goal:** Value-added service for customers.
-   **Role:** Uses the "Pro" dashboard to triage customers using a low-cost device.

### 3.3 The "Doctor" (Specialist)
-   **Profile:** Overwhelmed GP or Specialist.
-   **Goal:** Needs pre-screened patient data to save time.
-   **Requirement:** Structured "TOONS" reports, not raw chat logs.

## 4. Functional Requirements

### 4.1 AI & Agents
-   **Multilingual Triage Agent:**
    -   Must support Hindi, Hinglish, Tamil, Telugu, English.
    -   **Speech-to-Text (STT):** Allow voice inputs for symptoms.
-   **Medical Knowledge Base (RAG):**
    -   **Indian Pharmacopoeia:** Recognize Indian brand names (e.g., Crocin vs Tylenol).
    -   **Tropical Diseases:** Enhanced protocols for Malaria, Dengue, Chikungunya.
-   **Bot Orchestration:**
    -   **Triage Bot:** Collects vitals/symptoms.
    -   **Appointment Bot:** Books slots with nearestavailable doctor if Red/Yellow flag.

### 4.2 Interfaces
-   **WhatsApp Integration:** Primary channel for patients.
    -   Twilio/Meta API integration.
-   **Web/App Dashboard:** For "Kirana Health Partners" to manage multiple patient records.

### 4.3 Technical Core (Modifications to Current Project)
-   **Rust RAG extension:**
    -   Optimize for Indian-language tokenization.
    -   Add "Fuzzy Search" for misspelled drug names.
-   **Brain (Risk Model):**
    -   Retrain/Calibrate for Indian demographics (if data available) or use standard global baselines customized for tropical variances (e.g., higher baseline temps in summer?).

## 5. Non-Functional Requirements
### 5.1 Privacy & Security
-   **DPDP Act Compliance:** India's Digital Personal Data Protection Act.
-   **Data Localization:** All patient data must reside on Indian servers.
-   **Consent:** Explicit vernacular consent before triage.

### 5.2 Performance
-   **Low Latency:** Inference < 2s even on 4G networks.
-   **Offline Capability:** The Rust core should potentially run locally on the "Kirana Partner's" laptop/phone for sync-later scenarios.

## 6. Roadmap

### Phase 1: MVP (Months 1-2) ✅ COMPLETE
-   [x] Integrate Hindi/Hinglish support in `TriageAgent`. → `utils/language_handler.py` + `agent/bot.py`
-   [x] Update `MedicalTools` with top 50 common Indian drugs. → `tools/medical_tools.py` (80+ brand mappings, 20+ interactions)
-   [x] Replace CLI with a basic Streamlit/Gradio web UI for testing. → `ui/streamlit_app.py`

### Phase 2: Channel Expansion (Months 3-4) ✅ COMPLETE
-   [x] WhatsApp Business API integration. → `channels/whatsapp_handler.py` + `app/whatsapp_webhook.py` (Twilio)
-   [x] Voice Note analysis (Audio -> Text -> Agent). → `channels/voice_handler.py` (OpenAI Whisper STT)

### Phase 3: Ecosystem (Months 5+)
-   [ ] Doctor Dashboard and Booking system.
-   [ ] ABDM (Ayushman Bharat) Health ID integration.

## 7. Immediate Action Plan (Code Changes)
1.  **Modify `agent/bot.py`:** Add language handling logic.
2.  **Enhance `agent/rag.py`:** Add Indian medical specific documents to the `documents` list (simulated knowledge base).
3.  **Update `tools/medical_tools.py`:** Add Indian drug interaction variations.
