#!/usr/bin/env python3
"""
Synthea Pipeline: Automation, Ingestion & Analysis
Automates synthetic health record generation, loads datasets into Pandas/SQLite,
and generates summary analytics.
"""

import argparse
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
import pandas as pd


JAR_FILE = "synthea-with-dependencies.jar"


def run_generator(
    jar_path: str = JAR_FILE,
    population: int = 100,
    state: str = None,
    city: str = None,
    gender: str = None,
    age_range: str = None,
    seed: int = None,
    export_csv: bool = True,
    export_fhir: bool = True,
    output_dir: str = "./output",
) -> bool:
    """Executes the Synthea JAR with specified parameters."""
    if not os.path.exists(jar_path):
        print(f"Error: JAR file not found at {jar_path}")
        return False

    cmd = ["java", "-jar", jar_path, "-p", str(population)]

    if seed is not None:
        cmd.extend(["-s", str(seed)])

    if gender:
        cmd.extend(["-g", gender.upper()])

    if age_range:
        cmd.extend(["-a", age_range])

    cmd.append(f"--exporter.csv.export={str(export_csv).lower()}")
    cmd.append(f"--exporter.fhir.export={str(export_fhir).lower()}")
    cmd.append(f"--exporter.baseDirectory={output_dir}")

    if state:
        cmd.append(state)
        if city:
            cmd.append(city)

    print(f"🚀 Running Synthea command:\n  {' '.join(cmd)}\n")
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Generation complete!\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Generation failed with exit code {e.returncode}")
        return False


def load_csv_data(csv_dir: str = "./output/csv") -> dict[str, pd.DataFrame]:
    """Loads all generated CSV files into a dictionary of Pandas DataFrames."""
    csv_path = Path(csv_dir)
    if not csv_path.exists():
        print(f"Directory not found: {csv_dir}")
        return {}

    data = {}
    csv_files = list(csv_path.glob("*.csv"))
    print(f"📁 Loading {len(csv_files)} tables from {csv_dir}...")
    for file in sorted(csv_files):
        table_name = file.stem
        try:
            data[table_name] = pd.read_csv(file)
            print(f"  - {table_name:20s}: {len(data[table_name]):>6} records")
        except Exception as e:
            print(f"  - {table_name:20s}: Failed to read ({e})")
    return data


def analyze_records(data: dict[str, pd.DataFrame]):
    """Performs demographic, clinical, and financial analytics on the loaded data."""
    print("\n" + "=" * 60)
    print(" 📊 SYNTHETIC HEALTH DATA SUMMARY ANALYSIS")
    print("=" * 60)

    # 1. Demographics
    if "patients" in data:
        pts = data["patients"]
        print("\n--- 1. Patient Demographics ---")
        print(f"Total Patients: {len(pts)}")
        if "GENDER" in pts.columns:
            gender_counts = pts["GENDER"].value_counts().to_dict()
            print(f"Gender Distribution: {gender_counts}")

        if "RACE" in pts.columns:
            race_counts = pts["RACE"].value_counts().head(5).to_dict()
            print(f"Top Races: {race_counts}")

        if "HEALTHCARE_EXPENSES" in pts.columns:
            avg_expenses = pts["HEALTHCARE_EXPENSES"].mean()
            median_income = pts["INCOME"].median() if "INCOME" in pts.columns else 0
            print(f"Mean Lifetime Healthcare Expenses: ${avg_expenses:,.2f}")
            print(f"Median Annual Income:               ${median_income:,.2f}")

    # 2. Conditions
    if "conditions" in data:
        conds = data["conditions"]
        print("\n--- 2. Top Diagnosed Conditions ---")
        top_conds = conds["DESCRIPTION"].value_counts().head(5)
        for desc, cnt in top_conds.items():
            print(f"  * {desc}: {cnt}")

    # 3. Medications
    if "medications" in data:
        meds = data["medications"]
        print("\n--- 3. Top Prescribed Medications ---")
        top_meds = meds["DESCRIPTION"].value_counts().head(5)
        for desc, cnt in top_meds.items():
            print(f"  * {desc}: {cnt}")

    # 4. Encounters
    if "encounters" in data:
        encs = data["encounters"]
        print("\n--- 4. Encounter Classes ---")
        enc_counts = encs["ENCOUNTERCLASS"].value_counts().to_dict()
        for enc_class, cnt in enc_counts.items():
            print(f"  * {enc_class}: {cnt}")

    print("\n" + "=" * 60 + "\n")


def export_to_sqlite(data: dict[str, pd.DataFrame], db_path: str = "synthea_data.db"):
    """Saves all tables into a local SQLite database for easy SQL querying."""
    if not data:
        print("No data available to export to SQLite.")
        return

    print(f"💾 Saving tables to SQLite database: {db_path} ...")
    conn = sqlite3.connect(db_path)
    for table_name, df in data.items():
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
    print(f"✅ Exported {len(data)} tables to {db_path}. You can query it with SQL!\n")


def main():
    parser = argparse.ArgumentParser(description="Synthea Automation, Analytics & SQL Pipeline")
    parser.add_argument("--generate", action="store_true", help="Trigger Synthea to generate new data")
    parser.add_argument("-p", "--population", type=int, default=100, help="Number of patients to generate")
    parser.add_argument("--state", type=str, default=None, help="State name (e.g., California, Massachusetts)")
    parser.add_argument("--city", type=str, default=None, help="City name")
    parser.add_argument("-g", "--gender", type=str, choices=["M", "F"], help="Filter by gender")
    parser.add_argument("-a", "--age-range", type=str, help="Filter by age range (e.g. 18-65)")
    parser.add_argument("-s", "--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="./output", help="Base output directory")
    parser.add_argument("--csv-dir", type=str, default="./output/csv", help="CSV directory to analyze")
    parser.add_argument("--sqlite", action="store_true", help="Export datasets to local SQLite database")
    parser.add_argument("--db-path", type=str, default="synthea_data.db", help="SQLite database output path")

    args = parser.parse_args()

    # Step 1: Generate if requested
    if args.generate:
        success = run_generator(
            population=args.population,
            state=args.state,
            city=args.city,
            gender=args.gender,
            age_range=args.age_range,
            seed=args.seed,
            output_dir=args.output_dir,
        )
        if not success:
            sys.exit(1)

    # Step 2: Load and Analyze
    csv_dir = os.path.join(args.output_dir, "csv") if args.generate else args.csv_dir
    data = load_csv_data(csv_dir)
    if data:
        analyze_records(data)

        # Step 3: SQLite export
        if args.sqlite:
            export_to_sqlite(data, args.db_path)
    else:
        print("Tip: If you haven't generated data yet, run with --generate")


if __name__ == "__main__":
    main()
