import pandas as pd
import os


def clean_aadt_locations(input_path: str, output_path: str):

    # Clean AADT location dataset without merging.

    print("Cleaning AADT location dataset...")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    df = pd.read_csv(input_path)

    # Standardize column names
    df.columns = df.columns.str.strip().str.lower()

    # Rename coordinates
    df = df.rename(columns={
        "x": "aadt_longitude",
        "y": "aadt_latitude"
    })

    # Remove rows with missing coordinates
    df = df.dropna(subset=["aadt_longitude", "aadt_latitude"])

    # Remove duplicates
    df = df.drop_duplicates()

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)

    print("AADT cleaning completed.")
    print(f"Saved to: {output_path}")

    return df