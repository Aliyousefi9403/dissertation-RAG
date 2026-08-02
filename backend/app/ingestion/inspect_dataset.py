from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "datasets"
    / "ML-EdgeIIoT-dataset.csv"
)


def inspect_dataset() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    # Read only a small sample first because the complete CSV is very large.
    sample = pd.read_csv(DATASET_PATH, nrows=5)

    print(f"Dataset: {DATASET_PATH}")
    print(f"Number of columns: {len(sample.columns)}")

    print("\nColumns:")
    for column in sample.columns:
        print(f"- {column}")

    print("\nFirst five rows:")
    print(sample.to_string())

    print("\nData types:")
    print(sample.dtypes.to_string())


if __name__ == "__main__":
    inspect_dataset()