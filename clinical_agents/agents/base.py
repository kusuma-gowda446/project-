from abc import ABC, abstractmethod
from typing import Dict, Any, Callable
from clinical_agents.core.schemas import PatientChart, SpecialistAssessment
from clinical_agents.core.state import ClinicalState
from clinical_agents.core.models import get_chat_model


class BaseSpecialistAgent(ABC):
    """
    Abstract Base Class for all clinical domain specialists.
    Follows Open-Closed Principle: add new specialists without altering the graph backbone.
    """
    def __init__(self, name: str, domain: str, model_name: str = "mock"):
        self.name = name
        self.domain = domain
        self.model_name = model_name
        self.model = get_chat_model(model_name)

    @abstractmethod
    def evaluate(self, chart: PatientChart, chief_complaint: str) -> SpecialistAssessment:
        """
        Specialist logic: evaluates the patient EHR chart and chief complaint
        within this agent's medical domain.
        Returns a SpecialistAssessment with confidence score (0.0 to 1.0).
        """
        pass

    def as_node(self) -> Callable[[ClinicalState], Dict[str, Any]]:
        """
        Returns a LangGraph-compatible node function.
        Updates state['specialist_assessments'] with this specialist's evaluation.
        """
        def node_fn(state: ClinicalState) -> Dict[str, Any]:
            chart_dict = state.get("patient_chart")
            if not chart_dict:
                assessment = SpecialistAssessment(
                    specialist_name=self.name,
                    domain=self.domain,
                    has_condition=False,
                    primary_diagnosis="Patient chart unavailable",
                    confidence=0.0,
                    severity="Low",
                    clinical_evidence=["Missing patient EHR data"],
                    recommended_actions=[]
                )
            else:
                chart = PatientChart(**chart_dict)
                complaint = state.get("chief_complaint", "")
                assessment = self.evaluate(chart, complaint)

            log_entry = (
                f"[{self.name}] Assessed {self.domain}: "
                f"Diagnosis='{assessment.primary_diagnosis}', "
                f"Confidence={assessment.confidence:.2f}, "
                f"Severity={assessment.severity}"
            )
            return {
                "specialist_assessments": {self.name: assessment.model_dump()},
                "audit_log": [log_entry]
            }

        return node_fn
