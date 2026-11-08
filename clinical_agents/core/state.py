import operator
from typing import TypedDict, Annotated, Optional, Dict, Any, List


class ClinicalState(TypedDict):
    """
    Central state shared across the LangGraph backbone.
    Parallel specialist agents update specialist_assessments concurrently.
    """
    patient_id: str
    chief_complaint: str
    patient_chart: Optional[Dict[str, Any]]
    
    # Annotated with operator.ior to merge parallel dictionary outputs from specialists
    specialist_assessments: Annotated[Dict[str, Dict[str, Any]], operator.ior]
    
    final_verdict: Optional[Dict[str, Any]]
    audit_log: Annotated[List[str], operator.add]
