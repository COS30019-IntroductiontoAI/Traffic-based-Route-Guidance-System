import os
from pathlib import Path

from src.preprocessing.clean_scats_sites import clean_scats_sites
from src.preprocessing.clean_scats_traffic import clean_scats_traffic
from src.preprocessing.clean_traffic_locations import clean_aadt_locations
from src.preprocessing.merge_data import merge_datasets

SRC_DIR = Path(__file__).resolve().parent
RAW_2006_DIR = SRC_DIR / "data" / "2006_raw"
PROCESSED_DIR = SRC_DIR / "data" / "processed"

def main():
    print("____________________________________________")
    print("\nSTARTING PREPROCESSING PIPELINE\n")

    raw_sites_path = str(RAW_2006_DIR / "SCATSSiteListingSpreadsheet_VicRoads.xlsx")
    raw_traffic_path = str(RAW_2006_DIR / "Scats Data October 2006.xls")
    raw_aadt_path = str(RAW_2006_DIR / "Traffic_Count_Locations_with_LONG_LAT.csv")

    cleaned_sites_path = str(PROCESSED_DIR / "cleaned_sites.csv")
    cleaned_traffic_path = str(PROCESSED_DIR / "cleaned_traffic.csv")
    cleaned_aadt_path = str(PROCESSED_DIR / "cleaned_aadt.csv")

    master_output_path = str(PROCESSED_DIR / "master_dataset.csv")

    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # Phase 1
    print("Cleaning raw datasets\n")

    print("Cleaning SCATS site data\n")
    clean_scats_sites(
        input_path=raw_sites_path,
        output_path=cleaned_sites_path
    )

    print("Cleaning SCATS traffic data\n")
    clean_scats_traffic(
        input_path=raw_traffic_path,
        output_path=cleaned_traffic_path
    )

    print("Cleaning AADT location data\n")
    clean_aadt_locations(
        input_path=raw_aadt_path,
        output_path=cleaned_aadt_path
    )

    print("Data cleaning completed\n")

    # Phase 2
    print("Merging datasets\n")
    
    merge_datasets(
        traffic_path=cleaned_traffic_path,
        sites_path=cleaned_sites_path,
        aadt_path=cleaned_aadt_path,
        output_path=master_output_path
    )

    print("Merging completed\n")

    print("Preprocessing pipeline finished successfully")
    print(f"Master dataset saved to: {master_output_path}\n")

if __name__ == "__main__":
    main()