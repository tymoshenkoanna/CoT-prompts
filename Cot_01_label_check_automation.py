"""
Machine vs Human document label comparison.

Inputs (under the main folder "label_check"):
- Directory: 260223_dme_predictions/ (100 sub-folders, each with one JSON "metadata")
- File:      list_of_docs.xlsx

Output:
- CSV: machine_vs_human_labels.csv
  Columns: doc_id_mc, label_id_mc, label_name_mc,
           label_confidence_temy, doc_id_anna, doc_label_anna

The script also prints:
- "Successfully processed X sub-folders, failed Y"
- For failures, the corresponding JSON filenames/paths.
"""

import json
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd


# --------------------------------------------------------------------
# Configuration (adjust BASE_DIR if your path is different)
# --------------------------------------------------------------------
BASE_DIR = Path(
    "/xxxx/xxxxxxxxx/xxxxxxxx/xxxxx/xxxxx_xxxxxx/
).expanduser()

PREDICTIONS_DIR = BASE_DIR / "260223_dme_predictions"
DOC_LIST_PATH = BASE_DIR / "list_of_docs.xlsx"
OUTPUT_CSV_PATH = BASE_DIR / "machine_vs_human_labels.csv"

# Fail fast if the key paths are missing
if not PREDICTIONS_DIR.is_dir():
    raise FileNotFoundError(f"Predictions directory not found: {PREDICTIONS_DIR}")

if not DOC_LIST_PATH.is_file():
    raise FileNotFoundError(f"Doc list file not found: {DOC_LIST_PATH}")


# --------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------
def extract_doc_id_from_subdir_name(subdir_name: str) -> str:
    """
    Extract the numeric document ID from a sub-directory name.

    Rule:
    - Take the part before the first '-' (if any)
    - Return that part as-is (expected to be the numeric ID)
      Example:
        "22471894-2a6f..." -> "22471894"
        "22471894"        -> "22471894"
    """
    leading_part = subdir_name.split("-", 1)[0]
    return leading_part


def parse_doc_id_from_url(url: str) -> str | None:
    """
    Parse the document ID from a URL.

    Rule:
    - The document ID is the numeric string immediately following '/view/' in the path.
      Example:
        "https://.../document/view/70337116/asa-journal..." -> "70337116"
    - Returns None if it cannot be parsed.
    """
    if not isinstance(url, str):
        return None

    try:
        parsed = urlparse(url)
    except Exception:
        return None

    path = parsed.path or ""
    marker = "/view/"
    if marker not in(path):
        return None

    after_marker = path.split(marker, 1)[1]
    # Take characters up to the next '/' if present
    doc_id_part = after_marker.split("/", 1)[0]
    # Keep only digits (defensive)
    digits_only = "".join(ch for ch in doc_id_part if ch.isdigit())
    return digits_only or None


# --------------------------------------------------------------------
# Part 1: Load machine predictions from JSON sub-folders
# --------------------------------------------------------------------
def load_machine_predictions(predictions_dir: Path) -> tuple[pd.DataFrame, list[str]]:
    """
    Iterate through sub-folders in predictions_dir, read metadata JSON,
    and return:
      - DataFrame with columns:
          doc_id_mc, label_id_mc, label_name_mc, label_confidence_temy
      - List of JSON file paths that failed to process
    """
    rows = []
    failed_json_paths: list[str] = []

    # Deterministic order
    subdirs = sorted(
        [p for p in predictions_dir.iterdir() if p.is_dir()],
        key=lambda p: p.name,
    )

    for subdir in subdirs:
        doc_id_mc = extract_doc_id_from_subdir_name(subdir.name)

        # Expect exactly one JSON file per sub-directory
        json_files = list(subdir.glob("*.json"))
        if len(json_files) != 1:
            # Either missing JSON or multiple JSONs -> treat as failure
            if not json_files:
                failed_json_paths.append(str(subdir / "metadata.json"))
            else:
                failed_json_paths.extend(str(jf) for jf in json_files)
            continue

        metadata_path = json_files[0]

        try:
            with metadata_path.open("r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            failed_json_paths.append(str(metadata_path))
            continue

        # Extract fields from JSON
        doc_type = metadata.get("documentType", {}) or {}
        label_id_mc = doc_type.get("id")
        label_name_mc = doc_type.get("name")
        label_confidence_temy = metadata.get("confidence")

        rows.append(
            {
                "doc_id_mc": doc_id_mc,
                "label_id_mc": label_id_mc,
                "label_name_mc": label_name_mc,
                "label_confidence_temy": label_confidence_temy,
            }
        )

    # Build DataFrame with explicit dtypes
    df = pd.DataFrame(rows)

    if not df.empty:
        df["doc_id_mc"] = df["doc_id_mc"].astype("string")
        df["label_id_mc"] = df["label_id_mc"].astype("string")
        df["label_name_mc"] = df["label_name_mc"].astype("string")
        # Use nullable float for confidence
        df["label_confidence_temy"] = pd.to_numeric(
            df["label_confidence_temy"], errors="coerce"
        ).astype("Float64")

    return df, failed_json_paths


# --------------------------------------------------------------------
# Part 2: Load human labels from Excel list_of_docs.xlsx
# --------------------------------------------------------------------
def load_human_labels(doc_list_path: Path) -> pd.DataFrame:
    """
    Read list_of_docs.xlsx and extract:
      - doc_id_anna: numeric ID from URL in column A
      - doc_label_anna: label from column B

    Assumptions:
      - Column A contains URLs (or a header row which will be filtered out)
      - Column B contains the human labels.
    """
    # Read first two columns only, with no header assumption.
    # Later we filter rows that look like actual URLs.
    raw = pd.read_excel(
        doc_list_path,
        header=None,
        usecols=[0, 1],
        dtype=str,
    )
    raw.columns = ["url", "doc_label_anna"]

    # Keep rows with a non-null URL that looks like an HTTP URL
    raw = raw.dropna(subset=["url"])
    raw = raw[raw["url"].str.contains("http", case=False, na=False)].copy()

    # Parse document ID from URL
    raw["doc_id_anna"] = raw["url"].apply(parse_doc_id_from_url)

    # Drop rows where we could not parse an ID
    df = raw.dropna(subset=["doc_id_anna"]).copy()

    df["doc_id_anna"] = df["doc_id_anna"].astype("string")
    df["doc_label_anna"] = df["doc_label_anna"].astype("string")

    # We no longer need the raw URL in the downstream join
    df = df[["doc_id_anna", "doc_label_anna"]]

    return df


# --------------------------------------------------------------------
# Part 3: Merge machine predictions (left) with human labels (right)
# --------------------------------------------------------------------
def merge_predictions_and_labels(
    machine_df: pd.DataFrame, human_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Left join:
      Left:  machine_df (machine predictions)
      Right: human_df   (human labels)

    Join key:
      doc_id_mc (left) <-> doc_id_anna (right)
    """
    merged = machine_df.merge(
        human_df,
        how="left",
        left_on="doc_id_mc",
        right_on="doc_id_anna",
    )

    # Reorder and limit to the exact required columns
    merged = merged[
        [
            "doc_id_mc",
            "label_id_mc",
            "label_name_mc",
            "label_confidence_temy",
            "doc_id_anna",
            "doc_label_anna",
        ]
    ]

    return merged


# --------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------
def main() -> None:
    # Part 1: Machine predictions
    machine_df, failed_json_paths = load_machine_predictions(PREDICTIONS_DIR)

    # Part 2: Human labels
    human_df = load_human_labels(DOC_LIST_PATH)

    # Part 3: Merge
    if machine_df.empty:
        print("No machine prediction rows were loaded. Nothing to merge.")
        return

    merged_df = merge_predictions_and_labels(machine_df, human_df)

    # Save to CSV
    OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(OUTPUT_CSV_PATH, index=False)

    # Part 4: Terminal summary
    processed_count = len(machine_df)
    failed_count = len(failed_json_paths)

    print(f"Successfully processed {processed_count} sub-folders, failed {failed_count}")
    print(f"Output written to: {OUTPUT_CSV_PATH}")

    if failed_json_paths:
        print("Failed to process the following JSON files:")
        for path_str in failed_json_paths:
            print(f"- {path_str}")


if __name__ == "__main__":
    main()
