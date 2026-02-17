"""
Language detection and translation utility for SwasthyaSahayak.
Supports Hindi, Hinglish, Tamil, Telugu → English.

Strategy:
  1. Apply Hinglish keyword map (offline, zero-latency)
  2. Detect language with langdetect (offline)
  3. Translate non-English text via deep-translator/Google (requires internet)
  4. Gracefully fall back to normalized text if translation fails
"""

from utils.logger import get_logger

logger = get_logger(__name__)

# Supported language codes and their display names
SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
}

# Hinglish / colloquial Hindi medical term → English mapping
# Used as primary offline fallback (no API needed)
HINGLISH_MEDICAL_MAP: dict[str, str] = {
    # Symptoms
    "bukhar": "fever",
    "bukhaar": "fever",
    "tap": "fever",
    "sar dard": "headache",
    "sardard": "headache",
    "sir dard": "headache",
    "sirdard": "headache",
    "seena dard": "chest pain",
    "seene mein dard": "chest pain",
    "pet dard": "stomach pain",
    "pet mein dard": "stomach pain",
    "petdard": "stomach pain",
    "gale mein dard": "sore throat",
    "gala dard": "sore throat",
    "pair dard": "leg pain",
    "pair mein dard": "leg pain",
    "kamar dard": "back pain",
    "kamar mein dard": "back pain",
    "haath dard": "arm pain",
    "kandha dard": "shoulder pain",
    "khasi": "cough",
    "khansi": "cough",
    "khaansi": "cough",
    "zukam": "cold",
    "jukam": "cold",
    "nazla": "cold runny nose",
    "naak beh rahi": "runny nose",
    "naak band": "blocked nose",
    "ulti": "vomiting",
    "vomiting": "vomiting",
    "ubkai": "nausea",
    "ji machalna": "nausea",
    "dast": "diarrhea",
    "loose motion": "diarrhea",
    "paitl": "diarrhea",
    "kabz": "constipation",
    "saans lene mein takleef": "difficulty breathing",
    "saans phoolna": "breathlessness",
    "saans": "breathing",
    "chakkar": "dizziness",
    "chakkar aana": "dizziness",
    "sir ghoomna": "dizziness",
    "aankhon mein dhundhlapan": "blurred vision",
    "aankhon mein jalan": "eye irritation",
    "aankhein lal": "red eyes",
    "thakan": "fatigue",
    "kamzori": "weakness",
    "behoshi": "loss of consciousness",
    "hosh kho dena": "loss of consciousness",
    "jhatak": "seizure",
    "mirgi": "epilepsy seizure",
    "khujli": "itching",
    "daane": "rash",
    "chakte": "rash",
    "sujan": "swelling",
    "sooja hua": "swollen",
    "dard": "pain",
    "bahut dard": "severe pain",
    "tez dard": "sharp pain",
    "jalan": "burning sensation",
    "paseena": "sweating",
    "kaanpna": "chills",
    "thand lagana": "chills",

    # Vitals / Body
    "nabz": "pulse",
    "dil ki dhadkan": "heart rate",
    "bp": "blood pressure",
    "sugar": "blood sugar",
    "oxygen": "oxygen saturation",
    "temperature": "temperature",
    "wajan": "weight",

    # Common conditions
    "malaria": "malaria",
    "dengue": "dengue",
    "typhoid": "typhoid",
    "tb": "tuberculosis",
    "tuberculosis": "tuberculosis",
    "khansi tb": "tuberculosis cough",
    "diabetes": "diabetes",
    "madhumeh": "diabetes",
    "bp ki bimari": "hypertension",
    "high bp": "high blood pressure",
    "low bp": "low blood pressure",
    "dil ki bimari": "heart disease",
    "heart attack": "heart attack",
    "stroke": "stroke",
    "asthma": "asthma",
    "dam": "asthma",
    "peele peshab": "yellow urine jaundice",
    "peeliya": "jaundice",
    "pagalpan": "mental confusion",

    # Common medications (Hinglish names)
    "crocin": "paracetamol (Crocin)",
    "dolo": "paracetamol (Dolo)",
    "combiflam": "ibuprofen+paracetamol (Combiflam)",
    "glycomet": "metformin (Glycomet)",
}


def _apply_hinglish_map(text: str) -> str:
    """Replace Hinglish medical terms with English equivalents (offline)."""
    result = text.lower().strip()
    # Sort by length descending to match longer phrases first
    for hinglish, english in sorted(HINGLISH_MEDICAL_MAP.items(), key=lambda x: -len(x[0])):
        result = result.replace(hinglish, english)
    return result


def detect_language(text: str) -> str:
    """
    Detect language code of input text.
    Returns ISO 639-1 code (e.g., 'hi', 'ta', 'en').
    Falls back to 'en' if detection fails.
    """
    try:
        from langdetect import detect, LangDetectException
        lang = detect(text)
        logger.info(f"Detected language: {SUPPORTED_LANGUAGES.get(lang, lang)}")
        return lang
    except ImportError:
        logger.warning("langdetect not installed — defaulting to English")
        return "en"
    except Exception as e:
        logger.warning(f"Language detection failed: {e} — defaulting to English")
        return "en"


def _translate_with_google(text: str, source_lang: str) -> str:
    """Translate text to English using deep-translator (requires internet)."""
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source=source_lang, target="en").translate(text)
        logger.info(f"Translated from {source_lang} to English via GoogleTranslator")
        return translated
    except ImportError:
        logger.warning("deep-translator not installed — using original text")
        return text
    except Exception as e:
        logger.warning(f"Translation API failed: {e} — using original text")
        return text


def translate_to_english(text: str) -> tuple[str, str]:
    """
    Translate a single text string to English.

    Returns:
        (translated_text, detected_language_code)

    Pipeline:
        1. Apply Hinglish keyword map (offline)
        2. Detect language
        3. If not English, attempt Google Translation
        4. Fall back to Hinglish-mapped text on failure
    """
    if not text or not text.strip():
        return text, "en"

    # Step 1: Offline Hinglish normalization
    hinglish_normalized = _apply_hinglish_map(text)

    # Step 2: Detect language on normalized text
    detected_lang = detect_language(hinglish_normalized)

    # Step 3: If already English (or detection says English), return as-is
    if detected_lang == "en":
        return hinglish_normalized, "en"

    # Step 4: Attempt online translation
    translated = _translate_with_google(hinglish_normalized, source_lang=detected_lang)
    return translated, detected_lang


def translate_symptoms(symptoms: list[str]) -> tuple[list[str], str]:
    """
    Translate a list of symptom strings to English.

    Returns:
        (translated_symptoms, primary_detected_language_code)
    """
    if not symptoms:
        return symptoms, "en"

    translated_symptoms: list[str] = []
    detected_langs: list[str] = []

    for symptom in symptoms:
        translated, lang = translate_to_english(symptom)
        translated_symptoms.append(translated)
        detected_langs.append(lang)

    # Use the most common detected language as the primary language
    primary_lang = max(set(detected_langs), key=detected_langs.count)

    if primary_lang != "en":
        lang_name = SUPPORTED_LANGUAGES.get(primary_lang, primary_lang)
        logger.info(f"Symptoms translated from {lang_name} to English for processing")

    return translated_symptoms, primary_lang
