import pandas as pd
import numpy as np
import os
from scipy.spatial import KDTree


# ======================================================
# STEP 1: Clean SCATS site listing
# ======================================================
print("Step 1: Clean SCATS site listing")

scats_excel_path = "data/raw/SCATSSiteListingSpreadsheet_VicRoads.xlsx"
scats_clean_csv = "data/processed/SCATSSiteListingSpreadsheet_VicRoads_clean.csv"

if not os.path.exists(scats_excel_path):
    raise FileNotFoundError("SCATS site listing file is missing")

# Read Excel file
scats_df = pd.read_excel(
    scats_excel_path,
    sheet_name="SCATS Site Numbers",
    skiprows=9
)

# Standardize column names
scats_df.columns = (
    scats_df.columns.str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# Remove empty rows/columns and duplicates
scats_df = scats_df.dropna(how="all")
scats_df = scats_df.dropna(axis=1, how="all")
scats_df = scats_df.drop_duplicates()

os.makedirs("data/processed", exist_ok=True)
scats_df.to_csv(scats_clean_csv, index=False)


# ======================================================
# STEP 2: Load raw data
# ======================================================
print("Step 2: Load raw data")

traffic_file = "data/raw/Scats Data October 2006.xls"
aadt_file = "data/raw/Traffic_Count_Locations_with_LONG_LAT.csv"

if not os.path.exists(traffic_file):
    raise FileNotFoundError(f"Missing file: {traffic_file}")

if not os.path.exists(aadt_file):
    raise FileNotFoundError(f"Missing file: {aadt_file}")

# Load traffic data
traffic_raw = pd.read_excel(
    traffic_file,
    sheet_name="Data",
    header=1
)

traffic_raw.columns = (
    traffic_raw.columns.str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# Load AADT data
aadt_raw = pd.read_csv(aadt_file)
aadt_raw.columns = aadt_raw.columns.str.strip().str.lower()


# ======================================================
# STEP 3: Reshape data (wide -> long)
# ======================================================
print("Step 3: Reshape dataset")

id_cols = ["scats_number", "location", "nb_latitude", "nb_longitude", "date"]

# Select traffic columns (v00 - v95)
volume_cols = [
    col for col in traffic_raw.columns
    if col.startswith("v") and col[1:].isdigit()
]

# Convert to long format
traffic_long = pd.melt(
    traffic_raw[id_cols + volume_cols],
    id_vars=id_cols,
    value_vars=volume_cols,
    var_name="time_code",
    value_name="traffic_volume"
)

# Convert time index to HH:MM
def time_code_to_time(tc):
    idx = int(tc[1:])
    return f"{idx // 4:02d}:{(idx % 4) * 15:02d}:00"

# Create datetime column
traffic_long["datetime"] = pd.to_datetime(
    traffic_long["date"].astype(str).str[:10] + " " +
    traffic_long["time_code"].apply(time_code_to_time)
)

# Sort data
traffic_data = traffic_long.sort_values(
    ["scats_number", "datetime"]
).reset_index(drop=True)

print("Rows after Step 3:", len(traffic_data))


# ======================================================
# STEP 4: Data cleaning
# ======================================================
print("Step 4: Clean data")

# Remove invalid station
traffic_data = traffic_data[
    traffic_data["scats_number"] != 4335
].copy()

# Remove duplicates
traffic_data = traffic_data.drop_duplicates()

# Keep stations with enough data (>= 25 days)
days_count = traffic_data.groupby("scats_number")["datetime"].transform(
    lambda x: x.dt.date.nunique()
)
traffic_data = traffic_data[days_count >= 25].copy()

# Convert to numeric and fill missing values
traffic_data["traffic_volume"] = pd.to_numeric(
    traffic_data["traffic_volume"],
    errors="coerce"
)

traffic_data["traffic_volume"] = (
    traffic_data.groupby("scats_number")["traffic_volume"]
    .transform(lambda x: x.interpolate().bfill().ffill())
    .round()
    .astype(int)
)

print("Rows after Step 4:", len(traffic_data))


# ======================================================
# STEP 5: Feature engineering
# ======================================================
print("Step 5: Create features")

# Time features
traffic_data["hour"] = traffic_data["datetime"].dt.hour
traffic_data["day_of_week"] = traffic_data["datetime"].dt.dayofweek

# Weekend flag
traffic_data["is_weekend"] = (traffic_data["day_of_week"] >= 5).astype(int)

# Peak hour flag
weekday_peak = (
    (traffic_data["is_weekend"] == 0) &
    (traffic_data["hour"].between(7, 9) |
     traffic_data["hour"].between(15, 18))
)

weekend_peak = (
    (traffic_data["is_weekend"] == 1) &
    (traffic_data["hour"].between(11, 17))
)

traffic_data["is_peak"] = (weekday_peak | weekend_peak).astype(int)


# ======================================================
# STEP 6: Match nearest AADT location
# ======================================================
print("Step 6: Match AADT data")

aadt_raw = aadt_raw.reset_index(drop=True)

# Get one coordinate per station
station_coords = traffic_data.groupby("scats_number").agg({
    "nb_latitude": "first",
    "nb_longitude": "first"
}).reset_index()

# Build KDTree
aadt_points = aadt_raw[["x", "y"]].dropna().values
tree = KDTree(aadt_points)

# Find nearest AADT point
dist, idx = tree.query(
    station_coords[["nb_longitude", "nb_latitude"]].values
)

# Map road name
station_coords["road_name"] = aadt_raw.iloc[idx]["declared_r"].values

# Merge back
traffic_data = pd.merge(
    traffic_data,
    station_coords[["scats_number", "road_name"]],
    on="scats_number",
    how="left",
    validate="many_to_one"
)

# Fill missing values
traffic_data["road_name"] = (
    traffic_data["road_name"]
    .fillna("UNKNOWN")
    .astype("category")
)

print("Rows after Step 6:", len(traffic_data))


# ======================================================
# STEP 7: Save processed dataset
# ======================================================
print("Step 7: Save output")

final_cols = [
    "scats_number",
    "location",
    "road_name",
    "nb_latitude",
    "nb_longitude",
    "datetime",
    "hour",
    "day_of_week",
    "is_weekend",
    "is_peak",
    "traffic_volume"
]

# Final duplicate removal
final_data = traffic_data[final_cols].drop_duplicates()

final_data.to_csv(
    "data/processed/processed_traffic.csv",
    index=False
)

print("Final rows:", len(final_data))
print("Saved processed_traffic.csv successfully.")