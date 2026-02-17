from utils.logger import get_logger

logger = get_logger(__name__)


class RAGChain:
    def __init__(self):
        logger.info("Initializing Medical Knowledge Base (Indian + Global Protocols)...")
        self.documents = [
            # ── Standard Emergency Protocols ──────────────────────────────────────
            "Chest Pain Protocol: Immediate ECG and Troponin I/T. Consider ACS if radiation to left arm or jaw. Diaphoresis + chest pain = RED Priority. Administer Ecosprin 325mg (Aspirin) if no contraindication.",
            "Fever Protocol: Temperature >40°C or immunocompromised patient = RED. Temperature >38°C with rigors, chills, or altered sensorium = YELLOW. Stable low-grade fever = GREEN. Use Paracetamol (Crocin/Dolo-650) 500-1000mg for symptomatic relief.",
            "Headache Protocol: Sudden thunderclap onset is RED (Subarachnoid Hemorrhage risk). Fever + stiff neck = RED (Meningitis). Progressive worsening over days = YELLOW. Tension-type or known Migraine = GREEN.",
            "Shortness of Breath: O2 saturation <92% = RED. Stridor or cyanosis = RED. Mild wheeze with known asthma history = YELLOW (give Salbutamol/Asthalin nebulisation). Exertional dyspnoea without distress = YELLOW.",
            "Altered Consciousness / Seizure: Any loss of consciousness = RED. Post-ictal confusion after known epilepsy = YELLOW. Syncope without trauma = YELLOW. GCS <14 = RED. Check blood glucose immediately (rule out hypoglycaemia).",

            # ── Drug Interaction Protocols ─────────────────────────────────────────
            "Drug Interaction — Warfarin (Acitrom) + Aspirin (Ecosprin): CRITICAL. Significantly increases bleeding risk. Monitor PT/INR. Common Indian combination requiring specialist oversight.",
            "Drug Interaction — Paracetamol (Crocin/Dolo) + Alcohol: WARNING. Hepatotoxicity risk. Limit Paracetamol to 2g/day if patient consumes alcohol. Avoid in liver disease.",
            "Drug Interaction — Metronidazole (Metrogyl/Flagyl) + Alcohol: CRITICAL. Causes disulfiram-like reaction — severe flushing, vomiting, palpitations. Strictly avoid alcohol during and 48h after treatment.",
            "Drug Interaction — Metformin (Glycomet) + Alcohol: WARNING. Increases lactic acidosis risk. Counsel patient to avoid alcohol.",
            "Drug Interaction — Levothyroxine (Thyronorm/Eltroxin) + Calcium (Shelcal): WARNING. Calcium reduces levothyroxine absorption by up to 40%. Take Thyronorm on empty stomach 4 hours before Shelcal.",
            "Drug Interaction — Azithromycin (Azithral) + Antacids (Gelusil/Digene/ENO): INFO. Antacids reduce azithromycin absorption. Separate by at least 2 hours.",
            "Drug Interaction — Ibuprofen (Brufen/Combiflam) + Aspirin (Ecosprin): WARNING. Ibuprofen blunts cardioprotective effect of low-dose aspirin. Avoid combination in cardiac patients.",

            # ── Tropical Disease Protocols (India-Specific) ───────────────────────
            "Malaria Protocol (India): Suspect Malaria if: fever with rigors and chills, especially in monsoon season (June–October) or after travel to endemic areas (Odisha, Jharkhand, Chhattisgarh, NE India). Cyclical fever pattern (every 48–72h). Confirm with Rapid Diagnostic Test (RDT) or peripheral smear. Treatment: Chloroquine (Lariago) for P. vivax. Artemether+Lumefantrine (Coartem/P-Alaxin) for P. falciparum. P. falciparum with altered sensorium = RED (Cerebral Malaria).",
            "Dengue Fever Protocol (India): Suspect Dengue if: high fever (>38.5°C) + severe headache + retro-orbital pain + myalgia + skin rash (petechiae/maculopapular). Dengue season: post-monsoon (July–November). RED flags requiring hospitalisation: abdominal pain, persistent vomiting, bleeding (gums/nose), rapid breathing, restlessness, platelet count <20,000. Do NOT give Aspirin or Ibuprofen (risk of bleeding). Use Paracetamol (Crocin/Dolo) only. Severe Dengue (DSS/DHF) = RED.",
            "Chikungunya Protocol (India): Suspect Chikungunya if: acute fever + severe polyarthralgia (joint pain, especially hands, wrists, ankles) + rash. Common in south India (Karnataka, Tamil Nadu, Kerala). Joint pain may persist for months (chronic phase). Treatment is supportive. NSAIDs (avoid Aspirin) for joint pain. No specific antiviral. Not typically life-threatening — GREEN/YELLOW unless secondary complications.",
            "Typhoid (Enteric Fever) Protocol (India): Suspect Typhoid if: stepwise rising fever over 1 week, relative bradycardia, rose spots on abdomen, constipation or diarrhoea. Confirm with Widal test (note false positives common in India) or blood culture (gold standard). Treatment: Azithromycin (Azithral) or Cefixime (Taxim) for uncomplicated cases. Complications (intestinal perforation, haemorrhage) = RED. Safe water and sanitation counselling mandatory.",
            "Leptospirosis Protocol (India): Suspect Leptospirosis in: farmers, fisherfolk, post-flood exposure. Features: fever + headache + myalgia + conjunctival suffusion. Severe (Weil's disease): jaundice + renal failure + bleeding = RED. Treatment: Doxycycline or Amoxicillin for mild cases. IV Penicillin G or Ceftriaxone for severe.",
            "Japanese Encephalitis (JE) Protocol (India): Endemic in UP, Bihar, Assam, Odisha. Fever + headache + vomiting → altered sensorium + seizures + neck rigidity = RED. Primarily in children. Report to district health officer. Supportive care only — no specific antiviral.",
            "Scrub Typhus Protocol (India): Fever + eschar (painless black scab at mite bite site) + lymphadenopathy. Common in Himalayas, Tamil Nadu, Assam. Confirm with Weil-Felix test or ELISA. Treatment: Doxycycline 100mg twice daily for 7 days. If untreated: myocarditis, meningitis — YELLOW to RED.",
            "Heat Stroke Protocol (India): Core temp >40°C + hot dry skin + confusion/coma. Common in North India (May–June). RED emergency. Immediate cooling: ice packs to axilla/groin, cool IV fluids. Heatstroke ≠ heat exhaustion (heat exhaustion: still sweating, conscious, GREEN/YELLOW).",

            # ── India-Specific Drug & Condition References ────────────────────────
            "Indian Pharmacopoeia — Common OTC Analgesics: Paracetamol (Crocin 500mg, Dolo-650, Calpol) — first-line for fever and mild pain. Ibuprofen (Brufen 400mg, Ibugesic) — mild-moderate pain, anti-inflammatory. Combiflam (Ibuprofen 400mg + Paracetamol 325mg) — combination for musculoskeletal pain. Voveran (Diclofenac 50mg) — stronger NSAID, avoid in peptic ulcer and renal disease.",
            "Indian Pharmacopoeia — GI Medications: Antacids: Gelusil, Digene, ENO (sodium bicarbonate). PPIs: Omez (Omeprazole), Pantocid (Pantoprazole), Pan-D (Pantoprazole + Domperidone). Anti-emetics: Perinorm (Metoclopramide), Domstal (Domperidone), Emeset (Ondansetron). ORS: Electral — standard ORS for rehydration in diarrhoea.",
            "Indian Pharmacopoeia — Common Antibiotics: Augmentin/Clavam (Amoxicillin + Clavulanate) — first-line for respiratory, dental, skin infections. Azithral (Azithromycin) — atypical pneumonia, enteric fever. Taxim (Cefixime) — UTI, enteric fever. Cifran/Ciplox (Ciprofloxacin) — UTI, GI infections. Metrogyl/Flagyl (Metronidazole) — anaerobic infections, amoebiasis. AVOID self-medication with antibiotics — antimicrobial resistance is a major concern in India.",
            "Diabetes Management in India: Metformin (Glycomet 500/850mg) — first-line for Type 2 DM. Common brands: Glycomet, Metsmall, Glucophage. Glimepiride (Amaryl, Glimy) — sulphonylurea, risk of hypoglycaemia. Check blood sugar (normal fasting: 70-100 mg/dL, post-prandial <140 mg/dL). Hypoglycaemia (<70 mg/dL) symptoms: sweating, tremor, confusion — give 15g fast-acting carbs (sugar/glucose). Severe hypoglycaemia with loss of consciousness = RED.",
            "Hypertension in India: First-line agents: Amlodipine (Stamlo 5mg), Telmisartan (Telma 40mg), Ramipril (Cardace 5mg), Atenolol. Target BP: <130/80 mmHg for most patients, <140/90 for elderly. Hypertensive urgency (BP >180/120, no end-organ damage) = YELLOW — oral antihypertensives. Hypertensive emergency (BP >180/120 + chest pain / altered sensorium / vision loss) = RED.",
            "Respiratory Infections in India: Community-acquired pneumonia (CAP): fever + productive cough + breathlessness + crepitations on auscultation. Mild CAP: Augmentin (Amoxicillin-Clavulanate) + Azithral outpatient. Severe CAP (O2 sat <94%, RR>30, confusion): RED — hospitalise. TB: suspect if cough >2 weeks + fever + night sweats + weight loss. Refer to DOTS centre. COVID-19: fever + cough + anosmia — isolate, test, supportive care.",
        ]
        logger.info(f"Knowledge Base Indexed ({len(self.documents)} documents).")

    def retrieve(self, query: str, n_results: int = 2) -> list[str]:
        """
        Retrieves most relevant documents for a query using Jaccard similarity.
        Tries Rust hyper-speed core first, falls back to Python.
        Returns up to n_results documents with score > 0.
        """
        try:
            import medical_agent_core
            print("   [RAG] Using Hyper-Speed (Rust) Search")
            scored_docs = medical_agent_core.fast_jaccard_search(query, self.documents)
            results = [doc for score, doc in scored_docs[:n_results] if score > 0]

        except ImportError:
            print("   [RAG] Using Standard (Python) Search")
            query_words = set(query.lower().split())
            scored_docs = []

            for doc in self.documents:
                doc_words = set(doc.lower().split())
                intersection = query_words.intersection(doc_words)
                if not intersection:
                    score = 0.0
                else:
                    score = len(intersection) / len(query_words.union(doc_words))
                scored_docs.append((score, doc))

            scored_docs.sort(key=lambda x: x[0], reverse=True)
            results = [doc for score, doc in scored_docs[:n_results] if score > 0]

        return results or [self.documents[0]]
