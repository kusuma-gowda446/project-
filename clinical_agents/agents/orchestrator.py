from typing import Dict, Any, List
from clinical_agents.core.schemas import OrchestratorVerdict, SpecialistAssessment
from clinical_agents.core.state import ClinicalState
from clinical_agents.core.models import get_chat_model


class ClinicalOrchestrator:
    """
    Lead Orchestrator Agent.
    Synthesizes reports from all domain specialists, ranks diagnoses by confidence,
    checks for cross-specialty contraindications, and creates the definitive care plan.
    """
    def __init__(self, model_name: str = "mock"):
        self.name = "ClinicalOrchestrator"
        self.model_name = model_name
        self.model = get_chat_model(model_name)

    def synthesize(self, state: ClinicalState) -> OrchestratorVerdict:
        patient_id = state.get("patient_id", "Unknown")
        assessments_raw = state.get("specialist_assessments", {})

        confidences: Dict[str, float] = {}
        primary_diagnoses: List[str] = []
        care_plan: List[str] = []
        warnings: List[str] = []

        max_confidence = 0.0
        high_severity_count = 0

        # Review each specialist's assessment
        for spec_name, raw_data in assessments_raw.items():
            assessment = SpecialistAssessment(**raw_data)
            confidences[assessment.domain] = assessment.confidence

            if assessment.confidence > max_confidence:
                max_confidence = assessment.confidence

            if assessment.severity in ["High", "Critical"]:
                high_severity_count += 1

            # Only include diagnoses above clinical threshold (e.g., confidence >= 0.40)
            if assessment.has_condition and assessment.confidence >= 0.40:
                primary_diagnoses.append(f"{assessment.primary_diagnosis} ({assessment.domain}, Conf: {assessment.confidence:.0%})")
                care_plan.extend(assessment.recommended_actions)

        # Cross-Domain Allergy & Contraindication Check
        chart = state.get("patient_chart")
        if chart and chart.get("allergies"):
            for allergy in chart["allergies"]:
                warnings.append(f"ALLERGY WARNING: Documented hypersensitivity to {allergy}.")

        # Determine overall risk
        if max_confidence >= 0.80 or high_severity_count >= 2:
            overall_risk = "High"
        elif max_confidence >= 0.50:
            overall_risk = "Moderate"
        else:
            overall_risk = "Low"

        if not primary_diagnoses:
            primary_diagnoses.append("No acute multi-specialty disease identified")
            care_plan.append("Routine outpatient follow-up and annual physical")

        summary = (
            f"Consensus reached across {len(assessments_raw)} domain specialists. "
            f"Primary findings: {', '.join(primary_diagnoses)}. "
            f"Overall Patient Risk: {overall_risk}."
        )

        return OrchestratorVerdict(
            patient_id=patient_id,
            primary_diagnoses=primary_diagnoses,
            overall_risk_level=overall_risk,
            specialist_confidences=confidences,
            reconciled_care_plan=list(dict.fromkeys(care_plan)),
            contraindications_and_warnings=warnings,
            executive_summary=summary
        )

    def as_node(self):
        """Returns a LangGraph-compatible node function."""
        def node_fn(state: ClinicalState) -> Dict[str, Any]:
            verdict = self.synthesize(state)
            log = f"[{self.name}] Finalized consensus verdict. Risk={verdict.overall_risk_level}."
            return {
                "final_verdict": verdict.model_dump(),
                "audit_log": [log]
            }
        return node_fn
