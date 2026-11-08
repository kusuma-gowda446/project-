#!/usr/bin/env python3
"""
Interactive script to inspect and query the synthetic EHR database (synthea_data.db)
"""
import sqlite3
import pandas as pd

def main():
    db_file = "synthea_data.db"
    conn = sqlite3.connect(db_file)

    print("=" * 60)
    print(" 🏥 SYNTHETIC EHR DATABASE INSPECTOR (synthea_data.db)")
    print("=" * 60)

    # 1. Sample of patients
    print("\n[1] SAMPLE PATIENT PROFILES:")
    patients_df = pd.read_sql_query("""
        SELECT Id, FIRST, LAST, GENDER, BIRTHDATE, CITY, STATE 
        FROM patients 
        LIMIT 5;
    """, conn)
    print(patients_df.to_string(index=False))

    # 2. Diagnosed conditions
    print("\n[2] TOP 10 DIAGNOSED CONDITIONS:")
    conds_df = pd.read_sql_query("""
        SELECT DESCRIPTION, COUNT(*) AS Cases
        FROM conditions
        GROUP BY DESCRIPTION
        ORDER BY Cases DESC
        LIMIT 10;
    """, conn)
    print(conds_df.to_string(index=False))

    # 3. Patient with conditions and medications
    print("\n[3] EXAMPLE PATIENT WITH MEDS & CONDITIONS:")
    pt_detail = pd.read_sql_query("""
        SELECT p.FIRST || ' ' || p.LAST AS Patient, 
               c.DESCRIPTION AS Condition, 
               m.DESCRIPTION AS Medication
        FROM patients p
        JOIN conditions c ON p.Id = c.PATIENT
        JOIN medications m ON p.Id = m.PATIENT
        LIMIT 5;
    """, conn)
    print(pt_detail.to_string(index=False))

    conn.close()
    print("\n" + "=" * 60)
    print("✅ Database connection successful! You can now query any table.")
    print("=" * 60)

if __name__ == "__main__":
    main()
