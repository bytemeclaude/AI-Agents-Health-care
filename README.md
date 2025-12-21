# Medical Triage System (Enterprise v2.0)

A high-performance, secure, and AI-powered Patient Triage System designed for healthcare providers.

## 🌟 Key Features
- **Intelligent Triage Engine**: Combines Neural Networks (PyTorch), RAG (Retrieval-Augmented Generation), and Heuristic Tools.
- **Enterprise Architecture**: REST API built with FastAPI, SQLite/Postgres support via SQLAlchemy.
- **Security & Compliance**: API Key Authentication, PII Masking in Logs, Audit Trails.
- **Scalability**: Docker-ready, asynchronous processing.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- `pip`

### Installation
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the API
Start the server:
```bash
python -m app.main
```
The API will be available at `http://localhost:8000`.

### API Documentation
Interactive Swagger UI is available at `http://localhost:8000/docs`.

## 🧪 Testing
Run the test suite:
```bash
pytest
```

## 🏗️ Architecture
- **API Layer**: `app/main.py` (FastAPI) - Entry point, Validation, Auth.
- **Data Layer**: `models/db_models.py` (SQLAlchemy) - Patient & Triage Records.
- **Logic Layer**:
  - `agent/bot.py`: Main Agent Orchestrator.
  - `agent/brain.py`: Neural Network for Vitals Risk Assessment.
  - `agent/rag.py`: Knowledge Base Retrieval.
  - `tools/medical_tools.py`: Drug Interactions & Protocol Search.

## 🔒 Security
- **Authentication**: Requires `X-API-Key` header.
- **Logging**: PII is scrubbed from application logs.
- **Data Persistence**: All triage events are audited in the database.
