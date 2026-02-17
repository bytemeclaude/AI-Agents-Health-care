import time
from utils.logger import get_logger

logger = get_logger(__name__)

# Indian brand name → generic name mapping (top 50+ Indian drugs)
INDIAN_BRAND_TO_GENERIC: dict[str, str] = {
    # Analgesics / Antipyretics
    "crocin": "paracetamol",
    "crocin advance": "paracetamol",
    "dolo": "paracetamol",
    "dolo-650": "paracetamol",
    "calpol": "paracetamol",
    "metacin": "paracetamol",
    "pyrigesic": "paracetamol",
    "combiflam": "ibuprofen+paracetamol",
    "brufen": "ibuprofen",
    "ibugesic": "ibuprofen",
    "nurofen": "ibuprofen",
    "voveran": "diclofenac",
    "diclomol": "diclofenac+paracetamol",

    # Antacids / GI
    "gelusil": "antacid",
    "digene": "antacid",
    "eno": "antacid",
    "omez": "omeprazole",
    "omeprazole": "omeprazole",
    "pantocid": "pantoprazole",
    "pan-d": "pantoprazole+domperidone",
    "rabonik": "rabeprazole",
    "rantac": "ranitidine",
    "perinorm": "metoclopramide",
    "ondansetron": "ondansetron",
    "domstal": "domperidone",

    # Antibiotics
    "augmentin": "amoxicillin+clavulanate",
    "mox": "amoxicillin",
    "amoxil": "amoxicillin",
    "azithral": "azithromycin",
    "zithromax": "azithromycin",
    "azee": "azithromycin",
    "taxim": "cefixime",
    "cifran": "ciprofloxacin",
    "ciplox": "ciprofloxacin",
    "clavam": "amoxicillin+clavulanate",
    "doxycycline": "doxycycline",
    "metrogyl": "metronidazole",
    "flagyl": "metronidazole",

    # Antimalarials / Tropical
    "lariago": "chloroquine",
    "malarid": "chloroquine",
    "falcigo": "artesunate",
    "coartem": "artemether+lumefantrine",
    "p-alaxin": "artemether+lumefantrine",
    "primaquine": "primaquine",

    # Antihistamines / Allergy
    "allegra": "fexofenadine",
    "allegra-180": "fexofenadine",
    "cetirizine": "cetirizine",
    "cetzine": "cetirizine",
    "montair": "montelukast",
    "singulair": "montelukast",
    "atarax": "hydroxyzine",

    # Antidiabetics
    "glycomet": "metformin",
    "glucophage": "metformin",
    "metsmall": "metformin",
    "januvia": "sitagliptin",
    "galvus": "vildagliptin",
    "amaryl": "glimepiride",
    "glimy": "glimepiride",
    "insulin": "insulin",

    # Cardiovascular / BP
    "ecosprin": "aspirin",
    "dispirin": "aspirin",
    "cardace": "ramipril",
    "telma": "telmisartan",
    "arkamin": "clonidine",
    "metolar": "metoprolol",
    "atenolol": "atenolol",
    "amlodipine": "amlodipine",
    "stamlo": "amlodipine",
    "acitrom": "warfarin",
    "sorbitrate": "isosorbide dinitrate",
    "nitrocontin": "nitroglycerin",
    "atorvastatin": "atorvastatin",
    "rozavel": "rosuvastatin",

    # Thyroid
    "thyronorm": "levothyroxine",
    "eltroxin": "levothyroxine",
    "thyroxine": "levothyroxine",

    # Vitamins / Supplements
    "limcee": "vitamin c",
    "becosules": "vitamin b complex",
    "revital": "multivitamin",
    "shelcal": "calcium",
    "calcimax": "calcium+vitamin d",
    "tayo": "vitamin d",
    "supradyn": "multivitamin",

    # Respiratory
    "asthalin": "salbutamol",
    "budecort": "budesonide",
    "foracort": "budesonide+formoterol",
    "seroflo": "fluticasone+salmeterol",
    "deriphyllin": "theophylline+etofylline",
    "alex": "chlorpheniramine+dextromethorphan",
    "benadryl": "diphenhydramine",

    # NSAIDs / Topical
    "moov": "diclofenac+linseed oil (topical)",
    "volini": "diclofenac (topical)",

    # Cold / Cough
    "sinarest": "paracetamol+chlorpheniramine",
    "coldarin": "paracetamol+phenylephrine",
    "solvin": "bromhexine",
    "grilinctus": "dextromethorphan+chlorpheniramine",
}

# Drug interaction database — keyed by sorted tuple of normalized generic names
# Covers both generic and common Indian brand pairings
_INTERACTION_DB: dict[tuple[str, str], str] = {
    ("aspirin", "warfarin"):
        "CRITICAL: Aspirin (Ecosprin/Dispirin) + Warfarin (Acitrom) — significantly increases bleeding risk. Monitor PT/INR closely.",
    ("aspirin", "acitrom"):
        "CRITICAL: Ecosprin + Acitrom (Warfarin) — major bleeding risk. Requires specialist supervision.",
    ("ibuprofen", "aspirin"):
        "WARNING: Brufen/Combiflam (Ibuprofen) + Aspirin (Ecosprin) — ibuprofen blunts the cardioprotective effect of low-dose aspirin.",
    ("ibuprofen", "warfarin"):
        "WARNING: Ibuprofen + Warfarin (Acitrom) — increases bleeding risk and may raise INR.",
    ("diclofenac", "warfarin"):
        "WARNING: Voveran/Diclomol + Warfarin (Acitrom) — may raise INR and bleeding risk.",
    ("metformin", "alcohol"):
        "WARNING: Glycomet/Metformin + Alcohol — risk of lactic acidosis. Advise patient to avoid alcohol.",
    ("paracetamol", "alcohol"):
        "WARNING: Crocin/Dolo (Paracetamol) + Alcohol — hepatotoxicity risk. Max dose 2g/day if drinking.",
    ("lisinopril", "potassium"):
        "WARNING: Lisinopril + Potassium supplements — hyperkalemia risk. Monitor serum potassium.",
    ("ramipril", "potassium"):
        "WARNING: Cardace (Ramipril) + Potassium supplements — hyperkalemia risk.",
    ("azithromycin", "antacid"):
        "INFO: Azithral (Azithromycin) + Antacids (Gelusil/Digene) — separate by at least 2 hours to avoid reduced absorption.",
    ("levothyroxine", "calcium"):
        "WARNING: Thyronorm/Eltroxin + Shelcal/Calcimax (Calcium) — take 4 hours apart; calcium reduces levothyroxine absorption.",
    ("levothyroxine", "antacid"):
        "WARNING: Thyronorm + Antacids — separate by 4 hours; antacids reduce levothyroxine absorption.",
    ("metformin", "ciprofloxacin"):
        "WARNING: Glycomet (Metformin) + Ciplox/Cifran (Ciprofloxacin) — may cause hypoglycaemia. Monitor blood sugar.",
    ("chloroquine", "antacid"):
        "INFO: Lariago (Chloroquine) + Antacids — separate by 4 hours; antacids reduce chloroquine absorption.",
    ("metronidazole", "alcohol"):
        "CRITICAL: Metrogyl/Flagyl (Metronidazole) + Alcohol — disulfiram-like reaction (flushing, vomiting). Strictly avoid alcohol.",
    ("ciprofloxacin", "calcium"):
        "INFO: Ciprofloxacin + Calcium (Shelcal) — separate by 2 hours; calcium reduces ciprofloxacin absorption.",
    ("atorvastatin", "clarithromycin"):
        "WARNING: Atorvastatin + Clarithromycin — increased risk of myopathy/rhabdomyolysis.",
    ("glimepiride", "alcohol"):
        "WARNING: Amaryl/Glimy (Glimepiride) + Alcohol — may cause severe hypoglycaemia.",
    ("salbutamol", "metoprolol"):
        "WARNING: Asthalin (Salbutamol) + Metolar (Metoprolol) — beta-blocker may blunt salbutamol bronchodilation.",
    ("aspirin", "ibuprofen"):
        "WARNING: Ecosprin (Aspirin) + Brufen (Ibuprofen) — ibuprofen reduces aspirin's antiplatelet effect.",
}


def _normalize_drug_name(name: str) -> str:
    """Lowercase, strip whitespace, map Indian brand to generic if known."""
    normalized = name.lower().strip()
    return INDIAN_BRAND_TO_GENERIC.get(normalized, normalized)


class MedicalTools:

    @staticmethod
    def check_drug_interactions(medications: list[str]) -> list[str]:
        """
        Checks for dangerous drug interactions.
        Supports Indian brand names — maps to generics before checking.
        Returns a list of interaction warnings.
        """
        logger.info(f"Checking interactions for {len(medications)} medications")
        time.sleep(0.5)  # Simulate API latency (reduced from 1s)

        generics = [_normalize_drug_name(m) for m in medications]
        logger.info(f"Normalized to generics: {generics}")

        interactions: list[str] = []
        checked: set[tuple[str, str]] = set()

        for i, drug_a in enumerate(generics):
            for drug_b in generics[i + 1:]:
                key = tuple(sorted([drug_a, drug_b]))
                if key in checked:
                    continue
                checked.add(key)
                warning = _INTERACTION_DB.get(key)
                if warning:
                    interactions.append(warning)

        return interactions

    @staticmethod
    def search_medical_guidelines(symptom: str) -> str:
        """
        Returns triage protocol for a given symptom.
        Covers standard and India-specific tropical disease protocols.
        """
        logger.info(f"Searching guidelines for symptom")
        time.sleep(0.5)

        symptom = symptom.lower()

        if "chest pain" in symptom or "chest" in symptom:
            return "PROTOCOL: Chest pain → Immediate ECG, Troponin I/T. Rule out ACS. If radiation to left arm/jaw: RED."
        if "fever" in symptom or "bukhar" in symptom:
            return "PROTOCOL: Fever → Check temp. >40°C or altered sensorium: RED. >38°C with rigors/chills: check for Malaria/Dengue (India context). Stable >38°C: YELLOW."
        if "headache" in symptom:
            return "PROTOCOL: Headache → Sudden thunderclap onset: RED (rule out SAH). Stiff neck + fever: RED (meningitis). Tension/Migraine: GREEN."
        if "rash" in symptom or "spots" in symptom:
            return "PROTOCOL: Rash + fever in India → Rule out Dengue (petechiae), Chikungunya (polyarthralgia), Typhoid (rose spots). Send CBC+platelet count."
        if "joint" in symptom or "arthralgia" in symptom:
            return "PROTOCOL: Joint pain + fever → Chikungunya likely in endemic season. Check for rash. Analgesics (avoid Aspirin in Dengue)."
        if "vomit" in symptom or "nausea" in symptom:
            return "PROTOCOL: Vomiting → If projectile + headache: RED. With fever + jaundice: check for Hepatitis A/E (common in India). Ondansetron (Emeset) 4mg."
        if "diarrhea" in symptom or "loose" in symptom or "dast" in symptom:
            return "PROTOCOL: Diarrhea → Assess dehydration (skin turgor, BP). ORS (Electral/Pedialyte). If blood in stool: RED. Cholera risk in flood-prone areas."
        if "breathe" in symptom or "breath" in symptom or "saans" in symptom:
            return "PROTOCOL: Breathlessness → O2 sat <92%: RED. Stridor: RED. Mild wheeze with asthma Hx: Asthalin (Salbutamol) nebulisation, YELLOW."

        return "PROTOCOL: Generic triage. Assess ABCs (Airway, Breathing, Circulation). Vitals mandatory."
