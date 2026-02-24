import os
import json
import re
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd


# =========================
# Configuration
# =========================

# Set this to the directory that contains BOTH:
#   - the folder "260223_dme_predictions"
#   - the file "list_of_docs.xlsx"
ROOT_DIR = "/Users/annatymoshenko/Desktop/Docs/Data Analysis/label_check/"

PREDICTIONS_FOLDER_NAME = "260223_dme_predictions"
PRED_DIR = os.path.join(ROOT_DIR, PREDICTIONS_FOLDER_NAME)

EXCEL_FILENAME = "list_of_docs.xlsx"
EXCEL_PATH = os.path.join(ROOT_DIR, EXCEL_FILENAME)

OUTPUT_CSV_NAME = "merged_machine_vs_human_labels.csv"
OUTPUT_CSV_PATH = os.path.join(ROOT_DIR, OUTPUT_CSV_NAME)

CHANGELOG_NAME = "merged_machine_vs_human_labels_changelog.txt"
CHANGELOG_PATH = os.path.join(ROOT_DIR, CHANGELOG_NAME)


# =========================
# Helper functions
# =========================

def extract_doc_id_from_dirname(dirname: str) -> Optional[str]:
    """
    Extract leading numeric document ID from a subdirectory name.
    Examples:
        "22471894-2a6fe8..." -> "22471894"
        "22471894" -> "22471894"
    Returns None if no leading digits found.
    """
    m = re.match(r"^(\d+)", dirname)
    return m.group(1) if m else None


def load_prediction_from_subdir(subdir_path: str, subdir_name: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Attempt to load the metadata JSON from a subdirectory and extract required fields.

    Returns:
        (record, error_message)
        - record: dict with keys [doc_id_mc, label_id_mc, label_name_mc, label_confidence_temy] on success
        - error_message: None on success, otherwise a short description
    """
    # Extract doc_id_mc from subdirectory name
    doc_id_mc = extract_doc_id_from_dirname(subdir_name)
    if doc_id_mc is None:
        return None, f"Could not extract numeric ID from directory name '{subdir_name}'"

    # Locate JSON file
    json_candidates = [
        os.path.join(subdir_path, "metadata.json"),
        os.path.join(subdir_path, "metadata"),
    ]

    json_path = None
    for candidate in json_candidates:
        if os.path.isfile(candidate):
            json_path = candidate
            break

    if json_path is None:
        return None, f"Metadata JSON not found in '{subdir_path}'"

    # Load JSON
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        return None, f"Failed to read/parse JSON '{json_path}': {e}"

    # Extract required fields with strict checks
    try:
        doc_type = payload["documentType"]
        label_id_mc = str(doc_type["id"])
        label_name_mc = str(doc_type["name"])
        label_confidence_temy = float(payload["confidence"])
    except Exception as e:
        return None, f"Missing or invalid keys in JSON '{json_path}': {e}"

    record = {
        "doc_id_mc": str(doc_id_mc),
        "label_id_mc": label_id_mc,
        "label_name_mc": label_name_mc,
        "label_confidence_temy": label_confidence_temy,
    }
    return record, None


def parse_doc_id_from_url(url: Any) -> Optional[str]:
    """
    Parse the numeric document ID from a URL.
    The ID is defined as the numeric string immediately following '/view/'.

    Example:
        'https://.../view/22471894/tweet-us...' -> '22471894'
    """
    if not isinstance(url, str):
        return None
    m = re.search(r"/view/(\d+)", url)
    if m:
        return m.group(1)
    return None


# =========================
# Main processing
# =========================

def main():
    # --- Part 1: Machine predictions ---
    subfolder_records: List[Dict[str, Any]] = []
    failed_jsons: List[str] = []
    total_subfolders = 0

    if not os.path.isdir(PRED_DIR):
        raise FileNotFoundError(f"Predictions directory not found: {PRED_DIR}")

    # Iterate over immediate subdirectories in predictions folder
    for entry in os.scandir(PRED_DIR):
        if not entry.is_dir():
            continue

        total_subfolders += 1
        subdir_name = entry.name
        subdir_path = entry.path

        record, error = load_prediction_from_subdir(subdir_path, subdir_name)
        if error is not None:
            # Track failing JSON path for summary
            failed_jsons.append(f"{subdir_name}/metadata(.json): {error}")
            continue

        subfolder_records.append(record)

    # Build DataFrame for machine predictions
    df_mc = pd.DataFrame(subfolder_records, columns=[
        "doc_id_mc",
        "label_id_mc",
        "label_name_mc",
        "label_confidence_temy",
    ])

    # Basic type safety
    if not df_mc.empty:
        df_mc["doc_id_mc"] = df_mc["doc_id_mc"].astype("string")
        df_mc["label_id_mc"] = df_mc["label_id_mc"].astype("string")
        df_mc["label_name_mc"] = df_mc["label_name_mc"].astype("string")
        # leave confidence as float

    # --- Part 2: Human labels (Excel) ---
    if not os.path.isfile(EXCEL_PATH):
        raise FileNotFoundError(f"Excel file not found: {EXCEL_PATH}")

    # Assume no header; A: URL, B: label
    df_anna = pd.read_excel(
        EXCEL_PATH,
        header=None,
        usecols=[0, 1],
        names=["url", "doc_label_anna"],
        dtype={"url": "string", "doc_label_anna": "string"},
    )

    # Parse doc_id_anna from URL
    df_anna["doc_id_anna"] = df_anna["url"].apply(parse_doc_id_from_url).astype("string")

    # --- Part 3: Merge ---
    # Left join: machine predictions left, human labels right
    if df_mc.empty:
        merged = df_mc.copy()
        merged["doc_id_anna"] = pd.Series(dtype="string")
        merged["doc_label_anna"] = pd.Series(dtype="string")
    else:
        merged = df_mc.merge(
            df_anna[["doc_id_anna", "doc_label_anna"]],
            how="left",
            left_on="doc_id_mc",
            right_on="doc_id_anna",
        )

    # Enforce column order and exact names
    final_cols = [
        "doc_id_mc",
        "label_id_mc",
        "label_name_mc",
        "label_confidence_temy",
        "doc_id_anna",
        "doc_label_anna",
    ]
    merged_final = merged.reindex(columns=final_cols)

    # --- Write outputs (CSV + change log) ---
    # CSV
    merged_final.to_csv(OUTPUT_CSV_PATH, index=False)

    # Change log
    success_count = len(subfolder_records)
    fail_count = len(failed_jsons)

    # Some extra metrics for auditability
    total_human_rows = len(df_anna)
    matched_human_ids = merged_final["doc_id_anna"].notna().sum()

    with open(CHANGELOG_PATH, "w", encoding="utf-8") as logf:
        logf.write("Merge of machine predictions and human labels\n")
        logf.write(f"ROOT_DIR: {ROOT_DIR}\n")
        logf.write(f"Predictions directory: {PRED_DIR}\n")
        logf.write(f"Excel file: {EXCEL_PATH}\n")
        logf.write(f"Output CSV: {OUTPUT_CSV_PATH}\n\n")

        logf.write("=== Metrics ===\n")
        logf.write(f"Total sub-folders detected: {total_subfolders}\n")
        logf.write(f"Successfully processed sub-folders (JSON parsed): {success_count}\n")
        logf.write(f"Failed sub-folders (JSON issues): {fail_count}\n")
        logf.write(f"Total rows in human labels (Excel): {total_human_rows}\n")
        logf.write(f"Rows in merged output: {len(merged_final)}\n")
        logf.write(f"Rows with matched human doc_id_anna: {matched_human_ids}\n\n")

        if failed_jsons:
            logf.write("=== Failed JSONs ===\n")
            for item in failed_jsons:
                logf.write(f"{item}\n")

    # --- Part 4: Terminal summary ---
    print(f"Successfully processed {success_count} sub-folders, failed {fail_count}")
    if failed_jsons:
        print("Failed JSON files / sub-folders:")
        for item in failed_jsons:
            print(f"  - {item}")

    print("\nOutput CSV written to:")
    print(f"  {OUTPUT_CSV_PATH}")
    print("Change log written to:")
    print(f"  {CHANGELOG_PATH}")


if __name__ == "__main__":
    main()
    
