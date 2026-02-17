# Implementation Plan - Indian Market Adaptation

## Goal Description
Enhance the existing Medical Triage Agent to support the Indian healthcare context, including support for local languages (Hindi), Indian drug brand names, and tropical disease protocols.

## User Review Required
> [!IMPORTANT]
> **Language Support**: Currently, we are adding a `language` field but full translation integration (e.g., Google Translate API) is out of scope for this iteration. We will simulate Hindi support via keyword matching.

## Proposed Changes

### Models Layer
#### [MODIFY] [schemas.py](file:///c:/Users/Admin/OneDrive/Desktop/KiranaSync/AI-Agents-Health-care-main/models/schemas.py)
- Add `language` field to `PatientProfile` (default: "en").

### Knowledge Layer
#### [MODIFY] [rag.py](file:///c:/Users/Admin/OneDrive/Desktop/KiranaSync/AI-Agents-Health-care-main/agent/rag.py)
- Add Indian-specific medical protocols (Dengue, Malaria).
- Add Hindi keywords to existing protocols for basic multi-lingual retrieval matching.

### Tools Layer
#### [MODIFY] [medical_tools.py](file:///c:/Users/Admin/OneDrive/Desktop/KiranaSync/AI-Agents-Health-care-main/tools/medical_tools.py)
- Update `check_drug_interactions` to recognize Indian brand names (e.g., Crocin, Dolo).
- Update `search_medical_guidelines` to return Indian-context specific protocols.

### Agent Layer
#### [MODIFY] [bot.py](file:///c:/Users/Admin/OneDrive/Desktop/KiranaSync/AI-Agents-Health-care-main/agent/bot.py)
- Update `analyze` method to respect the patient's `language` preference in the final report generation (mocked for now).

### Tests
#### [NEW] [test_indian_context.py](file:///c:/Users/Admin/OneDrive/Desktop/KiranaSync/AI-Agents-Health-care-main/tests/test_indian_context.py)
- Test case for Indian specific diseases (Dengue).
- Test case for Indian drug brands.

## Verification Plan

### Automated Tests
Run the following commands:
```bash
# Run existing tests to ensure no regression
pytest tests/test_api.py

# Run new Indian context tests
pytest tests/test_indian_context.py
```

### Manual Verification
1.  Run `python main.py` and modify the mock patient to have "Dengue" symptoms.
2.  Verify the output contains relevant protocols.
