import pandas as pd
import os

print("Step 1: Reading raw Excel file")

# Load the SCATS traffic dataset from the Excel file
input_file = "data/raw/Scats Data October 2006.xls"
traffic_data = pd.read_excel(input_file, sheet_name="Data", header=1)

# Standardize column names
# Remove extra spaces
traffic_data.columns = traffic_data.columns.str.strip()

# Convert column names to lowercase
traffic_data.columns = traffic_data.columns.str.lower()

# Replace spaces with underscores
traffic_data.columns = traffic_data.columns.str.replace(" ", "_")

print("Step 2: Reshaping dataset from wide format to long format")

# Columns that identify the location of each SCATS site
identifier_columns = [
    "scats_number",
    "location",
    "nb_latitude",
    "nb_longitude",
    "date"
]

# Find traffic volume columns (v00 to v95)
traffic_columns = []

for column in traffic_data.columns:
    column_name = str(column)

    if column_name.startswith("v"):
        number_part = column_name[1:]

        if number_part.isdigit():
            traffic_columns.append(column)

# Keep only the columns we need
traffic_subset = traffic_data[identifier_columns + traffic_columns]

# Convert the dataset from wide format to long format
traffic_long = pd.melt(
    traffic_subset,
    id_vars=identifier_columns,
    value_vars=traffic_columns,
    var_name="time_code",
    value_name="traffic_volume"
)

print("Converting time codes to actual time values")

# Function to convert time code (v00–v95) into HH:MM:SS
def convert_time_code(time_code):

    interval_number = int(time_code[1:])

    hour = interval_number // 4
    minute = (interval_number % 4) * 15

    time_string = f"{hour:02d}:{minute:02d}:00"

    return time_string


# Apply the conversion
traffic_long["time"] = traffic_long["time_code"].apply(convert_time_code)

# Combine date and time into a datetime column
date_column = traffic_long["date"].astype(str).str.slice(0, 10)
time_column = traffic_long["time"]

traffic_long["datetime"] = pd.to_datetime(date_column + " " + time_column)

# Sort the data by location and time
traffic_sorted = traffic_long.sort_values(["scats_number", "datetime"])
traffic_sorted = traffic_sorted.reset_index(drop=True)

print("Step 3: Cleaning and filtering dataset")

# Remove the pedestrian counting site
traffic_sorted = traffic_sorted[traffic_sorted["scats_number"] != 4335]

# Create a temporary column that only contains the date
traffic_sorted["date_only"] = traffic_sorted["datetime"].dt.date

# Count how many unique days each location has
days_per_location = traffic_sorted.groupby(
    ["scats_number", "location"]
)["date_only"].transform("nunique")

# Keep only locations with at least 25 days of data
traffic_sorted = traffic_sorted[days_per_location >= 25]

# Remove the temporary column
traffic_sorted = traffic_sorted.drop(columns=["date_only"])

# Remove duplicate rows if any exist
traffic_sorted = traffic_sorted.drop_duplicates()

print("Handling missing traffic values")

# Convert traffic volume column to numeric
traffic_sorted["traffic_volume"] = pd.to_numeric(
    traffic_sorted["traffic_volume"],
    errors="coerce"
)

# Fill missing values using linear interpolation
traffic_sorted["traffic_volume"] = traffic_sorted["traffic_volume"].interpolate(method="linear")

# Backward fill remaining missing values
traffic_sorted["traffic_volume"] = traffic_sorted["traffic_volume"].bfill()

# Forward fill remaining missing values
traffic_sorted["traffic_volume"] = traffic_sorted["traffic_volume"].ffill()

# Round values
traffic_sorted["traffic_volume"] = traffic_sorted["traffic_volume"].round()

# Convert to integer
traffic_sorted["traffic_volume"] = traffic_sorted["traffic_volume"].astype(int)

print("Step 4: Creating time-based features")

# Extract hour of the day
datetime_column = traffic_sorted["datetime"]
traffic_sorted["hour"] = datetime_column.dt.hour

# Extract day of week (0 = Monday, 6 = Sunday)
traffic_sorted["day_of_week"] = datetime_column.dt.dayofweek

# Create a weekend indicator
traffic_sorted["is_weekend"] = traffic_sorted["day_of_week"] >= 5
traffic_sorted["is_weekend"] = traffic_sorted["is_weekend"].astype(int)

# Create peak hours indicator (peak hours: 7-9 AM and 5-7 PM)
traffic_sorted["is_peak"] = ((traffic_sorted["hour"] >= 7) & (traffic_sorted["hour"] < 9)) | ((traffic_sorted["hour"] >= 17) & (traffic_sorted["hour"] < 19))
traffic_sorted["is_peak"] = traffic_sorted["is_peak"].astype(int)

# Create road_name column (using location as road name)
traffic_sorted["road_name"] = traffic_sorted["location"]

# Select the final columns for the processed dataset
final_columns = [
    "scats_number",
    "location",
    "nb_latitude",
    "nb_longitude",
    "datetime",
    "hour",
    "day_of_week",
    "is_weekend",
    "is_peak",
    "road_name",
    "traffic_volume"
]

processed_data = traffic_sorted[final_columns]

print("Step 5: Saving processed dataset")

output_directory = "../data"
output_file = output_directory + "/2006_processed.csv"

# Create folder if it does not exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Save the processed dataset
processed_data.to_csv(output_file, index=False)

print("Processing completed")
print("File saved to:", output_file)