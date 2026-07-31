# ============================================================
# KAGGLE DATASET BULK ANALYSIS
# ============================================================
# This script runs the MedAgent Analysis Agent against 500 real
# CBC lab records from a Kaggle dataset, to validate the
# reference range coverage at scale.
#
# It does NOT use the Extraction Agent - the Kaggle data is
# already structured (CSV), so extraction is not needed.
# This tests ONLY the Analysis Agent's rule-based abnormality
# detection against a large, realistic dataset.
#
# Output:
#   - Summary statistics printed to terminal
#   - Full results CSV saved to outputs/kaggle_analysis_results.csv
#   - Summary CSV saved to outputs/kaggle_analysis_summary.csv
#
# Run: python analyse_kaggle_dataset.py
# ============================================================

import pandas as pd
import sys
import os
from collections import Counter

# Add project root to path so we can import from data/
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data.reference_ranges import flag_abnormal


# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------
INPUT_CSV = "data/kaggle_dataset/kaggle_lab_data.csv"
OUTPUT_DIR = "outputs"
RESULTS_CSV = os.path.join(OUTPUT_DIR, "kaggle_analysis_results.csv")
SUMMARY_CSV = os.path.join(OUTPUT_DIR, "kaggle_analysis_summary.csv")

# Kaggle uses abbreviated column names. Map them to the names
# our reference_ranges.py dictionary uses.
COLUMN_MAPPING = {
    "WBC":  "wbc",
    "RBC":  "rbc",
    "HGB":  "haemoglobin",
    "HCT":  "haematocrit",
    "MCV":  "mcv",
    "MCH":  "mch",
    "MCHC": "mchc",
    "PLT":  "platelets",
}

# Columns to skip entirely (IDs and tests not in our range dict)
SKIP_COLUMNS = {
    "ID", "LYMp", "MIDp", "NEUTp", "LYMn", "MIDn", "NEUTn",
    "RDWSD", "RDWCV", "MPV", "PDW", "PCT", "PLCR"
}


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def main():
    print("=" * 70)
    print("MEDAGENT — KAGGLE DATASET BULK ANALYSIS")
    print("=" * 70)

    # Make sure the output folder exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load the CSV
    print(f"\nLoading dataset: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} rows with {len(df.columns)} columns")

    # Print columns we WILL test vs SKIP
    print(f"\nTests being analysed ({len(COLUMN_MAPPING)}):")
    for kaggle_col, ref_name in COLUMN_MAPPING.items():
        print(f"  {kaggle_col} → {ref_name}")

    print(f"\nColumns skipped ({len(SKIP_COLUMNS)}): {', '.join(sorted(SKIP_COLUMNS))}")

    # ------------------------------------------------------------
    # ANALYSE EACH ROW
    # ------------------------------------------------------------
    print("\n" + "-" * 70)
    print("Running Analysis Agent on every row...")
    print("-" * 70)

    all_results = []
    status_counter = Counter()
    test_counter = Counter()
    abnormal_by_test = Counter()

    for idx, row in df.iterrows():
        row_id = row["ID"]

        # For each test column, check its abnormality status
        for kaggle_col, ref_name in COLUMN_MAPPING.items():
            value = row[kaggle_col]

            # Skip missing values
            if pd.isna(value):
                continue

            # Call our Analysis Agent's checker function
            status, ref = flag_abnormal(ref_name, value)

            all_results.append({
                "row_id": row_id,
                "test": ref_name,
                "kaggle_column": kaggle_col,
                "value": value,
                "status": status,
                "reference_range": (
                    f"{ref['min']}-{ref['max']}" if ref else ""
                ),
                "unit": ref["unit"] if ref else "",
            })

            # Track statistics
            status_counter[status] += 1
            test_counter[ref_name] += 1
            if status in ("HIGH", "LOW"):
                abnormal_by_test[ref_name] += 1

    # ------------------------------------------------------------
    # PRINT SUMMARY
    # ------------------------------------------------------------
    total_checks = len(all_results)

    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)

    print(f"\nTotal rows in dataset: {len(df)}")
    print(f"Total test values analysed: {total_checks}")
    print(f"Tests per row (average): {total_checks / len(df):.1f}")

    print(f"\n--- Distribution of Results ---")
    for status in ["NORMAL", "HIGH", "LOW", "UNKNOWN"]:
        count = status_counter.get(status, 0)
        pct = (count / total_checks * 100) if total_checks else 0
        print(f"  {status:8}: {count:5} ({pct:5.1f}%)")

    total_abnormal = status_counter["HIGH"] + status_counter["LOW"]
    total_normal = status_counter["NORMAL"]
    abnormal_pct = (total_abnormal / total_checks * 100) if total_checks else 0
    print(f"\n  Total abnormal (HIGH or LOW): {total_abnormal} ({abnormal_pct:.1f}%)")

    print(f"\n--- Abnormality Rate Per Test ---")
    for test in sorted(COLUMN_MAPPING.values()):
        total = test_counter[test]
        abnormal = abnormal_by_test[test]
        pct = (abnormal / total * 100) if total else 0
        print(f"  {test:15}: {abnormal:4} abnormal / {total:4} tested ({pct:5.1f}%)")

    # ------------------------------------------------------------
    # SAVE RESULTS TO CSV
    # ------------------------------------------------------------
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(RESULTS_CSV, index=False)
    print(f"\n✅ Full results saved to: {RESULTS_CSV}")
    print(f"   ({len(results_df)} rows)")

    # Save summary CSV
    summary_data = []
    for test in sorted(COLUMN_MAPPING.values()):
        total = test_counter[test]
        abnormal = abnormal_by_test[test]
        normal = total - abnormal
        summary_data.append({
            "test": test,
            "total_tested": total,
            "normal": normal,
            "abnormal": abnormal,
            "abnormal_percent": round((abnormal / total * 100), 2) if total else 0,
        })

    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(SUMMARY_CSV, index=False)
    print(f"✅ Summary table saved to: {SUMMARY_CSV}")

    print("\n" + "=" * 70)
    print("Analysis complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()