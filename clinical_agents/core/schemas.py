from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PatientChart(BaseModel):
    """Normalized Patient Electronic Health Record (EHR)."""
    id: str
    first_name: str
    last_name: str
    gender: str
    birthdate: str
    age: int
    active_conditions: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    observations: Dict[str, Any] = Field(default_factory=dict)
    allergies: List[str] = Field(default_factory=list)
    recent_encounters: List[str] = Field(default_factory=list)


class SpecialistAssessment(BaseModel):
    """Structured clinical diagnosis and confidence score from a domain specialist."""
    specialist_name: str
    domain: str
    has_condition: bool
    primary_diagnosis: str
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    severity: str = Field(description="Low, Moderate, High, or Critical")
    clinical_evidence: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)


class OrchestratorVerdict(BaseModel):
    """Final synthesized clinical assessment and reconciled treatment plan."""
    patient_id: str
    primary_diagnoses: List[str]
    overall_risk_level: str
    specialist_confidences: Dict[str, float]
    reconciled_care_plan: List[str]
    contraindications_and_warnings: List[str] = Field(default_factory=list)
    executive_summary: str
