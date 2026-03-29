import pandas as pd
import os


def clean_scats_sites(input_path: str, output_path: str):

    #Clean SCATS site listing dataset.

    print("Step 1: Cleaning SCATS Site Listing Data")


    # Step 1: Check input file
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print("Reading SCATS site listing file...")

    df = pd.read_excel(
        input_path,
        sheet_name="SCATS Site Numbers",
        skiprows=9
    )


    # Step 2: Basic inspection
    print("Inspecting dataset...")

    number_of_rows = df.shape[0]
    number_of_columns = df.shape[1]

    print(f"Number of rows: {number_of_rows}")
    print(f"Number of columns: {number_of_columns}")

    duplicate_rows = df.duplicated().sum()
    print(f"Number of duplicate rows: {duplicate_rows}")


    # Step 3: Standardize column names
    print("Standardizing column names...")

    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.lower()
    df.columns = df.columns.str.replace(" ", "_")


    # Step 4: Remove empty rows and columns
    print("Removing empty rows and columns...")

    # Remove rows where all values are missing
    df = df.dropna(how="all")

    # Remove columns where all values are missing
    df = df.dropna(axis=1, how="all")


    # Step 5: Remove duplicate rows
    print("Removing duplicate rows...")

    df = df.drop_duplicates()


    # Step 6: Create scats_number column
    print("Creating scats_number column for merging...")

    if "site_number" in df.columns:
        df["scats_number"] = df["site_number"]
    else:
        raise KeyError("Column 'site_number' not found in dataset")

    df = df.drop_duplicates(subset=["scats_number"], keep="first")


    # Step 7: Select relevant columns
    print("Selecting relevant columns...")

    columns_to_keep = [
        "site_number",          # original identifier (for validation)
        "scats_number",         # key used for merging
        "location_description"  # descriptive information
    ]

    existing_columns = [
        column for column in columns_to_keep if column in df.columns
    ]

    df = df[existing_columns]


    # Step 8: Final check
    print("Performing final checks...")

    missing_scats = df["scats_number"].isnull().sum()
    print(f"Missing scats_number values: {missing_scats}")


    # Step 9: Save cleaned dataset
    print("Saving cleaned SCATS site data...")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df.to_csv(output_path, index=False)

    print("Cleaning completed successfully.")
    print(f"Output saved to: {output_path}")

    return df