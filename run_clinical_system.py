#!/usr/bin/env python3
"""
CLI entry point to execute the Multi-Agent Clinical LangGraph Backbone.
Demonstrates multi-model capability, pluggable specialist agents, and orchestrator consensus.
"""

import json
from clinical_agents.agents.specialists import (
    CardiologySpecialist,
    EndocrinologySpecialist,
    PulmonologySpecialist
)
from clinical_agents.agents.orchestrator import ClinicalOrchestrator
from clinical_agents.graph import build_clinical_graph
from clinical_agents.pipelines.ingestion import EHRDataPipeline


def main():
    print("=" * 70)
    print(" 🏥 MULTI-AGENT CLINICAL DIAGNOSTIC BACKBONE (LANGGRAPH)")
    print("=" * 70)

    # 1. Multi-Model Configuration: Assign models per agent
    # In production, these can be 'gpt-4o', 'claude-3-5-sonnet', 'gemini-1.5-pro', or 'ollama:llama3'
    specialists = [
        CardiologySpecialist(model_name="mock:cardio-reasoner"),
        EndocrinologySpecialist(model_name="mock:endo-expert"),
        PulmonologySpecialist(model_name="mock:pulmo-analyst")
    ]
    orchestrator = ClinicalOrchestrator(model_name="mock:lead-diagnostician")

    print(f"\n📋 Registered Specialists ({len(specialists)}):")
    for s in specialists:
        print(f"  - {s.name:25s} | Domain: {s.domain:15s} | Model: {s.model_name}")
    print(f"  - {orchestrator.name:25s} | Role: Lead Consensus    | Model: {orchestrator.model_name}\n")

    # 2. Build the LangGraph Workflow
    app = build_clinical_graph(specialists=specialists, orchestrator=orchestrator)

    # 3. Fetch a sample synthetic patient from our Synthea SQLite database
    pipeline = EHRDataPipeline()
    sample_ids = pipeline.get_sample_patient_ids(limit=1)
    if not sample_ids:
        print("❌ No patients found in synthea_data.db. Please generate data first!")
        return

    patient_id = sample_ids[0]
    chart = pipeline.fetch_patient_chart(patient_id)

    print(f"👤 Patient Selected: {chart.first_name} {chart.last_name} ({chart.gender}, Age {chart.age})")
    print(f"   ID: {chart.id}")
    print(f"   Active Conditions ({len(chart.active_conditions)}): {', '.join(chart.active_conditions[:3]) or 'None'}")
    print(f"   Medications ({len(chart.medications)}): {', '.join(chart.medications[:3]) or 'None'}")

    # 4. Define Chief Complaint (simulating clinical visit reason)
    chief_complaint = "Patient presents with persistent cough, mild wheezing, and episodes of shortness of breath upon exertion."
    print(f"\n🩺 Chief Complaint: \"{chief_complaint}\"")

    # 5. Execute LangGraph DAG
    print("\n⚡ Running Multi-Agent Graph...")
    initial_state = {
        "patient_id": patient_id,
        "chief_complaint": chief_complaint,
        "patient_chart": None,
        "specialist_assessments": {},
        "final_verdict": None,
        "audit_log": []
    }

    result = app.invoke(initial_state)

    # 6. Display Audit Log / Execution Path
    print("\n" + "-" * 70)
    print("🔍 EXECUTION AUDIT LOG:")
    for log_msg in result.get("audit_log", []):
        print(f"  {log_msg}")

    # 7. Display Specialist Confidence Table
    print("\n" + "-" * 70)
    print("📊 DOMAIN SPECIALIST CONFIDENCE SCORES:")
    assessments = result.get("specialist_assessments", {})
    for name, data in assessments.items():
        print(f"  * {data['domain']:15s} -> Confidence: {data['confidence']:.0%} | Severity: {data['severity']:8s} | Diagnosis: {data['primary_diagnosis']}")
        for ev in data.get("clinical_evidence", []):
            print(f"      └─ Evidence: {ev}")

    # 8. Display Orchestrator Final Consensus
    verdict = result.get("final_verdict")
    if verdict:
        print("\n" + "=" * 70)
        print(" 🎯 ORCHESTRATOR CONSENSUS & CARE PLAN")
        print("=" * 70)
        print(f"Overall Risk Level: {verdict['overall_risk_level']}")
        print(f"Primary Diagnoses:")
        for diag in verdict["primary_diagnoses"]:
            print(f"  • {diag}")
        print(f"\nReconciled Care Plan:")
        for item in verdict["reconciled_care_plan"]:
            print(f"  • {item}")
        if verdict.get("contraindications_and_warnings"):
            print(f"\n⚠️ Warnings:")
            for w in verdict["contraindications_and_warnings"]:
                print(f"  ! {w}")
        print(f"\nSummary:\n  {verdict['executive_summary']}")
        print("=" * 70)


if __name__ == "__main__":
    main()
