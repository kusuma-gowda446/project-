# Multi-Agent Clinical Decision Support System

A multi-agent AI system for medical diagnosis and clinical decision support built with **LangGraph** and synthetic health records (**Synthea**).

---

## 💡 How It Works

1. **Input Pipeline:** Loads a synthetic patient's medical history (conditions, medications, lab vitals, allergies) from a local SQLite database.
2. **Domain Specialist Agents:** Multiple AI agents (Cardiology, Endocrinology, Pulmonology) analyze the patient in parallel. Each specialist outputs:
   - A domain diagnosis
   - A **confidence score** (e.g., 85%)
   - Clinical evidence (vitals, symptoms)
3. **Lead Orchestrator:** Weighs all specialist reports, checks for allergy and drug conflicts, and produces the final diagnosis and care plan.

```text
[Patient EHR Record]
       │
       ├──► [Cardiology Agent]    ──► (Diagnosis + Confidence) ──┐
       ├──► [Endocrinology Agent] ──► (Diagnosis + Confidence) ──┼──► [Lead Orchestrator] ──► Final Diagnosis & Care Plan
       └──► [Pulmonology Agent]   ──► (Diagnosis + Confidence) ──┘
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Multi-Agent Diagnosis
```bash
python3 run_clinical_system.py
```

### 3. View Patient Records in Your Browser
```bash
python3 web_viewer.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser to inspect patients, conditions, and vitals visually.

---

## 📁 Key Project Files

* **`run_clinical_system.py`** — Main entry point to run the multi-agent diagnosis.
* **`clinical_agents/`** — Core package with domain agents, multi-model factory, and LangGraph workflow.
* **`synthea_data.db`** — SQLite database with 82,000+ synthetic medical records.
* **`output/csv/`** — Spreadsheets for patients, encounters, conditions, and medications.
* **`web_viewer.py`** — Local web app to explore patient tables.
* **`query_ehr.py`** — Simple helper script to inspect patient records in the terminal.
