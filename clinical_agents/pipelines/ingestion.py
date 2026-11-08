import sqlite3
from datetime import datetime
from typing import Optional
from clinical_agents.core.schemas import PatientChart


class EHRDataPipeline:
    """
    Ingestion pipeline that extracts raw records from SQLite or CSV
    and normalizes them into a typed PatientChart.
    """
    def __init__(self, db_path: str = "synthea_data.db"):
        self.db_path = db_path

    def fetch_patient_chart(self, patient_id: str) -> Optional[PatientChart]:
        """Fetches and normalizes a patient chart by patient ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1. Demographics
        pt_query = """
        SELECT Id, FIRST, LAST, GENDER, BIRTHDATE 
        FROM patients 
        WHERE Id = ?
        """
        pt_row = cursor.execute(pt_query, (patient_id,)).fetchone()
        if not pt_row:
            conn.close()
            return None

        pid, first, last, gender, bdate = pt_row
        try:
            birth_dt = datetime.strptime(bdate, "%Y-%m-%d")
            age = max(0, datetime.now().year - birth_dt.year)
        except Exception:
            age = 45

        # 2. Conditions
        conds = [
            row[0] for row in cursor.execute(
                "SELECT DESCRIPTION FROM conditions WHERE PATIENT = ? ORDER BY START DESC", (patient_id,)
            ).fetchall()
        ]

        # 3. Medications
        meds = [
            row[0] for row in cursor.execute(
                "SELECT DESCRIPTION FROM medications WHERE PATIENT = ? ORDER BY START DESC", (patient_id,)
            ).fetchall()
        ]

        # 4. Observations (Vitals / Lab Results)
        obs_rows = cursor.execute(
            "SELECT DESCRIPTION, VALUE, UNITS FROM observations WHERE PATIENT = ? ORDER BY DATE DESC", (patient_id,)
        ).fetchall()
        observations = {}
        for desc, val, units in obs_rows:
            if desc not in observations:
                observations[desc] = f"{val} {units}" if units else str(val)

        # 5. Allergies
        allergies = [
            row[0] for row in cursor.execute(
                "SELECT DESCRIPTION FROM allergies WHERE PATIENT = ?", (patient_id,)
            ).fetchall()
        ]

        # 6. Recent Encounters
        encounters = [
            row[0] for row in cursor.execute(
                "SELECT DESCRIPTION FROM encounters WHERE PATIENT = ? ORDER BY START DESC LIMIT 5", (patient_id,)
            ).fetchall()
        ]

        conn.close()

        return PatientChart(
            id=pid,
            first_name=first or "Unknown",
            last_name=last or "Unknown",
            gender=gender or "U",
            birthdate=bdate or "1980-01-01",
            age=age,
            active_conditions=list(dict.fromkeys(conds)),  # Deduplicate while preserving order
            medications=list(dict.fromkeys(meds)),
            observations=observations,
            allergies=allergies,
            recent_encounters=encounters
        )

    def get_sample_patient_ids(self, limit: int = 5) -> list[str]:
        """Utility to get patient IDs with active medical conditions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        rows = cursor.execute("""
            SELECT DISTINCT p.Id 
            FROM patients p
            JOIN conditions c ON p.Id = c.PATIENT
            JOIN medications m ON p.Id = m.PATIENT
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [r[0] for r in rows]
