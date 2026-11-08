from typing import List
from clinical_agents.core.schemas import PatientChart, SpecialistAssessment
from clinical_agents.agents.base import BaseSpecialistAgent


class CardiologySpecialist(BaseSpecialistAgent):
    """Specialist agent focused on Cardiovascular Health."""
    def __init__(self, model_name: str = "mock"):
        super().__init__(name="CardiologySpecialist", domain="Cardiology", model_name=model_name)

    def evaluate(self, chart: PatientChart, chief_complaint: str) -> SpecialistAssessment:
        evidence: List[str] = []
        confidence = 0.1
        has_condition = False
        diagnosis = "No active cardiac disease detected"
        severity = "Low"
        actions: List[str] = []

        # 1. Condition search
        cardiac_keywords = ["hypertension", "coronary", "myocardial", "heart failure", "atrial fibrillation"]
        matched_conditions = [
            c for c in chart.active_conditions
            if any(k in c.lower() for k in cardiac_keywords)
        ]
        if matched_conditions:
            has_condition = True
            confidence += 0.45
            evidence.append(f"Recorded conditions: {', '.join(matched_conditions)}")
            diagnosis = matched_conditions[0]
            severity = "Moderate"

        # 2. Chief complaint symptoms
        symptoms = ["chest pain", "palpitations", "shortness of breath", "dizziness"]
        if any(s in chief_complaint.lower() for s in symptoms):
            confidence += 0.25
            evidence.append(f"Chief complaint reports relevant cardiac symptoms: '{chief_complaint}'")
            if severity == "Moderate":
                severity = "High"

        # 3. Medications check
        cardiac_meds = ["lisinopril", "amlodipine", "metoprolol", "atorvastatin", "simvastatin", "hydrochlorothiazide"]
        matched_meds = [
            m for m in chart.medications
            if any(k in m.lower() for k in cardiac_meds)
        ]
        if matched_meds:
            confidence += 0.15
            evidence.append(f"Cardiovascular medications: {', '.join(matched_meds)}")

        # 4. Vitals check
        for desc, val in chart.observations.items():
            if "systolic blood pressure" in desc.lower():
                evidence.append(f"Vitals: {desc} = {val}")

        confidence = min(0.98, max(0.05, confidence))
        if has_condition or confidence > 0.5:
            actions.append("Order 12-lead ECG and comprehensive lipid panel")
            actions.append("Schedule 6-month blood pressure review")

        return SpecialistAssessment(
            specialist_name=self.name,
            domain=self.domain,
            has_condition=has_condition or confidence > 0.5,
            primary_diagnosis=diagnosis,
            confidence=round(confidence, 2),
            severity=severity,
            clinical_evidence=evidence if evidence else ["Normal baseline cardiovascular status"],
            recommended_actions=actions
        )


class EndocrinologySpecialist(BaseSpecialistAgent):
    """Specialist agent focused on Metabolic and Endocrine disorders."""
    def __init__(self, model_name: str = "mock"):
        super().__init__(name="EndocrinologySpecialist", domain="Endocrinology", model_name=model_name)

    def evaluate(self, chart: PatientChart, chief_complaint: str) -> SpecialistAssessment:
        evidence: List[str] = []
        confidence = 0.1
        has_condition = False
        diagnosis = "Normal endocrine profile"
        severity = "Low"
        actions: List[str] = []

        # 1. Diabetes / Thyroid conditions
        endocrine_keywords = ["diabetes", "prediabetes", "hyperglycemia", "hypothyroidism", "hyperthyroidism"]
        matched_conds = [
            c for c in chart.active_conditions
            if any(k in c.lower() for k in endocrine_keywords)
        ]
        if matched_conds:
            has_condition = True
            confidence += 0.5
            diagnosis = matched_conds[0]
            severity = "Moderate"
            evidence.append(f"Prior endocrine history: {', '.join(matched_conds)}")

        # 2. Symptoms
        symptoms = ["fatigue", "excessive thirst", "frequent urination", "weight loss", "weight gain"]
        if any(s in chief_complaint.lower() for s in symptoms):
            confidence += 0.2
            evidence.append(f"Symptom correlation: '{chief_complaint}'")

        # 3. Medications
        endo_meds = ["metformin", "insulin", "glipizide", "levothyroxine", "semaglutide"]
        matched_meds = [m for m in chart.medications if any(k in m.lower() for k in endo_meds)]
        if matched_meds:
            confidence += 0.2
            evidence.append(f"Endocrine prescriptions: {', '.join(matched_meds)}")

        confidence = min(0.98, max(0.05, confidence))
        if has_condition or confidence > 0.5:
            actions.append("Order HbA1c and Fasting Plasma Glucose test")
            actions.append("Refer to diabetic nutritional counseling")

        return SpecialistAssessment(
            specialist_name=self.name,
            domain=self.domain,
            has_condition=has_condition or confidence > 0.5,
            primary_diagnosis=diagnosis,
            confidence=round(confidence, 2),
            severity=severity,
            clinical_evidence=evidence if evidence else ["No overt endocrine markers flagged"],
            recommended_actions=actions
        )


class PulmonologySpecialist(BaseSpecialistAgent):
    """Specialist agent focused on Respiratory and Pulmonary diseases."""
    def __init__(self, model_name: str = "mock"):
        super().__init__(name="PulmonologySpecialist", domain="Pulmonology", model_name=model_name)

    def evaluate(self, chart: PatientChart, chief_complaint: str) -> SpecialistAssessment:
        evidence: List[str] = []
        confidence = 0.1
        has_condition = False
        diagnosis = "Clear respiratory status"
        severity = "Low"
        actions: List[str] = []

        pulm_keywords = ["asthma", "copd", "bronchitis", "pneumonia", "respiratory", "apnea"]
        matched_conds = [
            c for c in chart.active_conditions
            if any(k in c.lower() for k in pulm_keywords)
        ]
        if matched_conds:
            has_condition = True
            confidence += 0.5
            diagnosis = matched_conds[0]
            severity = "Moderate"
            evidence.append(f"Documented respiratory conditions: {', '.join(matched_conds)}")

        symptoms = ["cough", "wheezing", "dyspnea", "shortness of breath", "sputum"]
        if any(s in chief_complaint.lower() for s in symptoms):
            confidence += 0.25
            evidence.append(f"Respiratory symptoms noted in complaint: '{chief_complaint}'")

        pulm_meds = ["albuterol", "fluticasone", "montelukast", "budesonide", "ipratropium"]
        matched_meds = [m for m in chart.medications if any(k in m.lower() for k in pulm_meds)]
        if matched_meds:
            confidence += 0.2
            evidence.append(f"Inhalers / respiratory therapy: {', '.join(matched_meds)}")

        confidence = min(0.98, max(0.05, confidence))
        if has_condition or confidence > 0.5:
            actions.append("Perform Spirometry / Pulmonary Function Test (PFT)")
            actions.append("Review inhaler administration technique")

        return SpecialistAssessment(
            specialist_name=self.name,
            domain=self.domain,
            has_condition=has_condition or confidence > 0.5,
            primary_diagnosis=diagnosis,
            confidence=round(confidence, 2),
            severity=severity,
            clinical_evidence=evidence if evidence else ["Lungs clear, no active pulmonary diagnosis"],
            recommended_actions=actions
        )
