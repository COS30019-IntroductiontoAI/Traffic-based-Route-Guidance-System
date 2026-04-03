import pandas as pd
import os


def clean_aadt_locations(input_path: str, output_path: str):

    # Clean AADT location dataset without merging.
    print("____________________________________________")
    print("\nSTEP 3: CLEANING AADT LOCATION DATA\n")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    print("Reading AADT location data\n")
    df = pd.read_csv(input_path)

    # Standardize column names
    print("Standardizing column names\n")
    df.columns = df.columns.str.strip().str.lower()

    print("Column names standardized\n")

    # Rename coordinates
    print("Renaming coordinate columns\n")
    df = df.rename(columns={
        "x": "aadt_longitude",
        "y": "aadt_latitude"
    })

    print("Coordinate columns renamed\n")

    # Remove rows with missing coordinates
    print("Removing rows with missing coordinates\n")
    df = df.dropna(subset=["aadt_longitude", "aadt_latitude"])

    print(f"Remaining rows: {df.shape[0]}\n")

    # Remove duplicates
    print("Removing duplicate rows\n")
    df = df.drop_duplicates()

    print(f"Rows after removing duplicates: {df.shape[0]}\n")

    # Save
    print("Saving cleaned dataset\n")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"File saved to: {output_path}")
    print("Cleaning completed successfully\n")

    return df