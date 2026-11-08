# Multi-Agent AI Differential Diagnosis & Clinical Decision Support System

An enterprise-grade, modular multi-agent clinical decision support system built on **LangGraph**, **Multi-Model Orchestration**, and **Synthetic EHR Data (Synthea)**.

---

## 🏥 Architecture Overview

The system models a clinical tumor board or multi-specialty medical team. Each domain specialist agent evaluates the patient's electronic health record (EHR) and chief complaint within their specific medical domain, computing **confidence scores (0%–100%)**, severity levels, and clinical evidence. A **Lead Clinical Orchestrator** then synthesizes all specialist findings, checks for cross-domain contraindications (e.g., drug interactions, allergies), and formulates a unified care plan.

```
                                  [START]
                                     │
                                     ▼
                      ┌──────────────────────────────┐
                      │    Input Ingestion Pipeline  │  <-- Extracts EHR from Synthea / SQLite
                      └──────────────┬───────────────┘
                                     │ (Parallel Fan-Out)
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│ Cardiology Agent    │   │ Endocrinology Agent │   │ Pulmonology Agent   │  <-- Pluggable
│ Model: Claude 3.5   │   │ Model: GPT-4o       │   │ Model: Gemini Pro   │      Specialists
│ Output: Conf (0-1)  │   │ Output: Conf (0-1)  │   │ Output: Conf (0-1)  │
└──────────┬──────────┘   └──────────┬──────────┘   └──────────┬──────────┘
           │                         │                         │
           └─────────────────────────┼─────────────────────────┘
                                     │ (Fan-In: Consensus Merge)
                                     ▼
                      ┌──────────────────────────────┐
                      │   Lead Clinical Orchestrator │  <-- Resolves Conflicts,
                      │   Model: GPT-4o / o1         │      Synthesizes Care Plan
                      └──────────────┬───────────────┘
                                     │
                                     ▼
                                   [END]
```

---

## 📂 Project Structure

```text
├── clinical_agents/              # Core Multi-Agent Package
│   ├── core/
│   │   ├── schemas.py            # Pydantic data contracts (PatientChart, SpecialistAssessment, Verdict)
│   │   ├── state.py              # LangGraph state with parallel dictionary merge reducers
│   │   └── models.py             # Multi-Model Registry & Factory (OpenAI, Anthropic, Gemini, Ollama)
│   ├── pipelines/
│   │   └── ingestion.py          # Input pipeline: extracts & normalizes patient EHR from SQLite
│   ├── agents/
│   │   ├── base.py               # Abstract Base Class for pluggable domain specialists
│   │   ├── specialists.py        # Domain agents (Cardiology, Endocrinology, Pulmonology)
│   │   └── orchestrator.py       # Consensus agent weighing confidences & care plans
│   └── graph.py                  # Dynamic LangGraph DAG compiler
├── output/                       # Generated Synthetic Medical Data
│   ├── csv/                      # 18 relational CSV tables (patients, encounters, conditions, etc.)
│   └── fhir/                     # HL7 FHIR R4 JSON bundles
├── run_clinical_system.py        # CLI entry point to run the LangGraph workflow
├── query_ehr.py                  # Terminal utility to query and inspect patient EHRs
├── web_viewer.py                 # Live interactive browser dashboard for EHR tables (port 8501)
├── synthea_pipeline.py           # Automated Synthea generation & SQLite ingestion pipeline
├── synthea_data.db               # SQLite database containing 82,000+ clinical records
├── requirements.txt              # Python package dependencies
└── README.md
```

---

## 🧪 Synthetic Healthcare Data (Synthea)

The project leverages **Synthea** (MITRE's open-source synthetic patient generator) to create 100% HIPAA-compliant longitudinal health records.

* **Database:** `synthea_data.db` (82,356 records across 18 tables)
* **Clinical Standards:**
  * **Conditions:** SNOMED-CT coded diagnoses
  * **Medications:** RxNorm coded active prescriptions & dosages
  * **Labs & Vitals:** LOINC coded observations (BP, Glucose, BMI, A1c)
  * **Encounters:** Ambulatory, wellness, inpatient, and emergency department records
  * **Interoperability:** HL7 FHIR R4 transaction bundles

---

## 🚀 Quick Start Guide

### 1. Clone & Install Dependencies

```bash
git clone git@github.com:kusuma-gowda446/project-.git
cd project-

# Create virtual environment & install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. View Data in Your Browser (Web Dashboard)

Launch the built-in visual viewer to inspect all 18 clinical tables:
```bash
python3 web_viewer.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

### 3. Run the Multi-Agent Clinical Workflow

Execute the LangGraph multi-agent diagnostic process:
```bash
python3 run_clinical_system.py
```

**Sample Execution Output:**
```text
======================================================================
 🏥 MULTI-AGENT CLINICAL DIAGNOSTIC BACKBONE (LANGGRAPH)
======================================================================

📋 Registered Specialists (3):
  - CardiologySpecialist      | Domain: Cardiology      | Model: mock:cardio-reasoner
  - EndocrinologySpecialist   | Domain: Endocrinology   | Model: mock:endo-expert
  - PulmonologySpecialist     | Domain: Pulmonology     | Model: mock:pulmo-analyst
  - ClinicalOrchestrator      | Role: Lead Consensus    | Model: mock:lead-diagnostician

👤 Patient Selected: Kyra Gerlach (F, Age 3)
🩺 Chief Complaint: "Patient presents with persistent cough, mild wheezing, and shortness of breath."

📊 DOMAIN SPECIALIST CONFIDENCE SCORES:
  * Cardiology      -> Confidence: 35% | Severity: Low  | Diagnosis: No active cardiac disease
  * Endocrinology   -> Confidence: 10% | Severity: Low  | Diagnosis: Normal endocrine profile
  * Pulmonology     -> Confidence: 35% | Severity: Low  | Diagnosis: Clear respiratory status

🎯 ORCHESTRATOR CONSENSUS & CARE PLAN:
  Overall Risk Level: Low
  ⚠️ Warnings: ALLERGY WARNING: Documented hypersensitivity to Ibuprofen.
```

### 4. Query the Synthetic EHR Database

```bash
python3 query_ehr.py
```

Or query directly in Python:
```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("synthea_data.db")
df = pd.read_sql("SELECT FIRST, LAST, GENDER, CITY FROM patients LIMIT 5", conn)
print(df)
conn.close()
```

---

## 🔌 Extensibility: Adding a New Specialist Agent

The architecture strictly follows the **Open-Closed Principle**. To add a new medical specialty (e.g., **Nephrology**), you only need to define a class subclassing `BaseSpecialistAgent` in `clinical_agents/agents/specialists.py`:

```python
from clinical_agents.agents.base import BaseSpecialistAgent
from clinical_agents.core.schemas import PatientChart, SpecialistAssessment

class NephrologySpecialist(BaseSpecialistAgent):
    def __init__(self, model_name: str = "claude-3-5-sonnet"):
        super().__init__(name="NephrologySpecialist", domain="Nephrology", model_name=model_name)

    def evaluate(self, chart: PatientChart, chief_complaint: str) -> SpecialistAssessment:
        # 1. Inspect eGFR, serum creatinine, microalbuminuria in chart.observations
        # 2. Check renal disease history in chart.active_conditions
        # 3. Calculate calibrated confidence score (0.0 to 1.0)
        return SpecialistAssessment(
            specialist_name=self.name,
            domain=self.domain,
            has_condition=True,
            primary_diagnosis="Chronic Kidney Disease Stage 3",
            confidence=0.88,
            severity="Moderate",
            clinical_evidence=["eGFR: 45 mL/min/1.73m2"],
            recommended_actions=["Order Renal Ultrasound", "Monitor serum potassium"]
        )
```

Then register it in `run_clinical_system.py`:
```python
specialists = [
    CardiologySpecialist(model_name="claude-3-5-sonnet"),
    EndocrinologySpecialist(model_name="gpt-4o"),
    PulmonologySpecialist(model_name="gemini-1.5-pro"),
    NephrologySpecialist(model_name="claude-3-5-sonnet"),  # <-- Added in 1 line
]
```
The LangGraph backbone automatically dynamically constructs the fan-out and fan-in DAG!

---

## 🔄 Generating New Patient Cohorts

To generate a new cohort (e.g. 200 patients in California aged 40–80):

```bash
python3 synthea_pipeline.py --generate -p 200 -a 40-80 --state California --sqlite
```
*(Requires `synthea-with-dependencies.jar` available locally)*

---

## 📄 License
This project is licensed under the Apache 2.0 License.
Synthetic patient health data generated using Synthea (MITRE Corporation).
