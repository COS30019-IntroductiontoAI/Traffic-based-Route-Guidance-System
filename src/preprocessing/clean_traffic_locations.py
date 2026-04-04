import pandas as pd
import os


def clean_aadt_locations(input_path: str, output_path: str):
    """
    Clean AADT location dataset without merging.
    This prepares the ground-truth road coordinates needed for KDTree spatial mapping later.
    """
    
    print("____________________________________________")
    print("\nSTEP 3: CLEANING AADT LOCATION DATA\n")

    # Fail fast if file is missing to prevent pipeline crashes
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    print("Reading AADT location data\n")
    df = pd.read_csv(input_path)

    # Standardize column names
    print("Standardizing column names\n")
    
    # Strip whitespace and lowercase to avoid annoying typos when referencing columns
    df.columns = df.columns.str.strip().str.lower()

    print("Column names standardized\n")

    # Rename coordinates
    print("Renaming coordinate columns\n")
    
    # Explicitly rename 'x' and 'y' to 'aadt_longitude' and 'aadt_latitude'.
    # This prevents naming conflicts and confusion with SCATS 'nb_latitude'/'nb_longitude' later.
    df = df.rename(columns={
        "x": "aadt_longitude",
        "y": "aadt_latitude"
    })

    print("Coordinate columns renamed\n")

    # Remove rows with missing coordinates
    print("Removing rows with missing coordinates\n")
    
    # The KDTree algorithm will throw an error if it encounters NaN coordinates.
    # We must drop any location that doesn't have exact spatial data.
    df = df.dropna(subset=["aadt_longitude", "aadt_latitude"])

    print(f"Remaining rows: {df.shape[0]}\n")

    # Remove duplicates
    print("Removing duplicate rows\n")
    
    # Remove exact duplicates to optimize and speed up KDTree nearest-neighbor queries
    df = df.drop_duplicates()

    print(f"Rows after removing duplicates: {df.shape[0]}\n")

    # Save
    print("Saving cleaned dataset\n")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"File saved to: {output_path}")
    print("Cleaning completed successfully\n")

    return df