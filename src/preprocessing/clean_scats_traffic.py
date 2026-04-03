import pandas as pd
import os

def clean_scats_traffic(input_path: str, output_path: str):

    # Clean SCATS traffic dataset and prepare it for machine learning.

    print("____________________________________________")
    print("\nSTEP 2: CLEANING SCATS TRAFFIC DATA\n")

    # Step 1: Check input file
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print("Reading raw traffic data\n")
    traffic_raw = pd.read_excel(
        input_path,
        sheet_name="Data",
        header=1
    )

    # Step 2: Basic inspection
    print("Inspecting dataset\n")
    print(f"Number of rows: {traffic_raw.shape[0]}")
    print(f"Number of columns: {traffic_raw.shape[1]}")

    duplicate_count = traffic_raw.duplicated().sum()
    print(f"Duplicate rows in raw data: {duplicate_count}\n")

    # Step 3: Standardize column names
    print("Standardizing column names\n")
    traffic_raw.columns = traffic_raw.columns.str.strip().str.lower().str.replace(" ", "_")

    print("Column names have been standardized\n")

    # Step 4: Identify columns
    print("Identifying relevant columns\n")
    identifier_columns = [
        "scats_number", "location", "nb_latitude", "nb_longitude", "date"
    ]

    volume_columns = [col for col in traffic_raw.columns if col.startswith("v") and col[1:].isdigit()]

    print(f"Identifier columns: {identifier_columns}")
    print(f"Number of volume columns: {len(volume_columns)}\n")

    # Step 5: Remove irrelevant columns
    print("Removing unnecessary columns\n")
    columns_to_drop = [
        "cd_melway", "hf_vicroads_internal", "vr_internal_stat", "vr_internal_loc"
    ]
    existing_columns_to_drop = [col for col in columns_to_drop if col in traffic_raw.columns]

    traffic_raw = traffic_raw.drop(columns=existing_columns_to_drop)

    columns_to_keep = identifier_columns + volume_columns
    traffic_raw = traffic_raw[columns_to_keep]

    print(f"Columns kept: {len(columns_to_keep)}\n")

    # Step 6: Reshape data (wide -> long)
    print("Reshaping data to long format\n")
    traffic_long = pd.melt(
        traffic_raw,
        id_vars=identifier_columns,
        value_vars=volume_columns,
        var_name="time_code",
        value_name="traffic_volume"
    )

    print(f"Data reshaped. New number of rows: {traffic_long.shape[0]}\n")

    # Step 7: Convert time code to datetime
    print("Creating datetime column\n")
    
    traffic_long["date"] = pd.to_datetime(traffic_long["date"]).dt.normalize()

    def convert_time_code_to_timedelta(time_code):
        index = int(time_code[1:])
        hour = index // 4
        minute = (index % 4) * 15
        return pd.Timedelta(hours=hour, minutes=minute)

    traffic_long["datetime"] = traffic_long["date"] + traffic_long["time_code"].apply(convert_time_code_to_timedelta)
    traffic_long["date"] = traffic_long["date"].dt.date

    print("Datetime column created successfully\n")

    # Step 8: Sort data
    print("Sorting data\n")
    traffic_data = traffic_long.sort_values(
        by=["scats_number", "datetime"]
    ).reset_index(drop=True)

    print("Data sorted\n")

    # Step 9: Remove invalid and duplicate data
    # Exclude site 4335 (pedestrian counts) to prevent skewed vehicle predictions
    print("Removing invalid and duplicate records\n")
    traffic_data = traffic_data[traffic_data["scats_number"] != 4335].copy()
    traffic_data = traffic_data.drop_duplicates()

    print("Invalid site removed and duplicates handled\n")

    # Step 10: Filter insufficient data
    # Keep sites with >= 25 days of data (accommodates valid sites like 4262 with 26 days)
    print("Filtering SCATS sites with insufficient data\n")
    unique_days_per_site = traffic_data.groupby("scats_number")["datetime"].transform(
        lambda values: values.dt.date.nunique()
    )
    traffic_data = traffic_data[unique_days_per_site >= 25].copy()

    print("Filtering completed\n")

    # Step 11: Handle missing values
    print("Handling missing traffic volume values\n")
    traffic_data["traffic_volume"] = pd.to_numeric(traffic_data["traffic_volume"], errors="coerce")

    traffic_data["traffic_volume"] = traffic_data.groupby("scats_number")["traffic_volume"].transform(
        lambda values: values.interpolate().bfill().ffill()
    )

    traffic_data["traffic_volume"] = traffic_data["traffic_volume"].round().astype(int)

    print("Missing values handled\n")

    # Step 12: Create time-based features
    print("Creating time-based features\n")
    traffic_data["hour"] = traffic_data["datetime"].dt.hour
    traffic_data["day_of_week"] = traffic_data["datetime"].dt.dayofweek
    traffic_data["is_weekend"] = (traffic_data["day_of_week"] >= 5).astype(int)

    weekday_peak_condition = (
        (traffic_data["is_weekend"] == 0) & 
        (traffic_data["hour"].between(7, 9) | traffic_data["hour"].between(15, 18))
    )
    weekend_peak_condition = (
        (traffic_data["is_weekend"] == 1) & 
        traffic_data["hour"].between(11, 17)
    )
    traffic_data["is_peak"] = (weekday_peak_condition | weekend_peak_condition).astype(int)

    print("Time-based features created\n")

    # Step 13: Save main dataset
    print("Saving cleaned dataset\n")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    traffic_data.to_csv(output_path, index=False)
    
    print(f"File saved to: {output_path}")
    print("Cleaning process completed successfully\n")

    return traffic_data