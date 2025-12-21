# Medical Triage Agent (v2.0)

An intelligent AI Agent built from scratch to assist healthcare professionals in patient triage.

## 🧠 Intelligence Architecture
- **Neural Brain**: A PyTorch-based neural network (`agent/brain.py`) that predicts risk scores from patient vitals.
- **RAG Knowledge Base**: A robust retrieval system (`agent/rag.py`) that queries medical protocols.
- **Agentic Core**: A central logic unit (`agent/bot.py`) that synthesizes tools, knowledge, and probabilistic risk to enable decision-making.

## 🚀 Usage
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the agent:
   ```bash
   python main.py
   ```

## 🛠️ Tech Stack
- **Languages**: Python
- **ML/AI**: PyTorch, SentenceTransformers
- **Data**: Pydantic, TOONs (Token-Oriented Object Notation)
