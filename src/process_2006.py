import os
from pathlib import Path

from preprocessing.clean_scats_sites import clean_scats_sites
from preprocessing.clean_scats_traffic import clean_scats_traffic
from preprocessing.clean_traffic_locations import clean_aadt_locations
from preprocessing.merge_data import merge_datasets


SRC_ROOT = Path(__file__).resolve().parent
RAW_2006_DIR = SRC_ROOT / "data" / "2006_raw"
PROCESSED_DIR = SRC_ROOT / "data" / "processed"

def main():
    print("Start preprocessing pipeline...\n")

    # Raw data paths
    raw_sites_path = str(RAW_2006_DIR / "SCATSSiteListingSpreadsheet_VicRoads.xlsx")
    raw_traffic_path = str(RAW_2006_DIR / "Scats Data October 2006.xls")
    raw_aadt_path = str(RAW_2006_DIR / "Traffic_Count_Locations_with_LONG_LAT.csv")


    # Cleaned data output paths
    cleaned_sites_path = str(PROCESSED_DIR / "cleaned_sites.csv")
    cleaned_traffic_path = str(PROCESSED_DIR / "cleaned_traffic.csv")
    cleaned_aadt_path = str(PROCESSED_DIR / "cleaned_aadt.csv")


    # Final merged dataset
    master_output_path = str(PROCESSED_DIR / "master_dataset.csv")

    # Ensure output directory exists
    os.makedirs(PROCESSED_DIR, exist_ok=True)


    # Phase 1: Clean each dataset
    print("--- Phase 1: Cleaning data ---")

    print("Cleaning sites...")
    clean_scats_sites(
        input_path=raw_sites_path,
        output_path=cleaned_sites_path
    )

    print("Cleaning traffic...")
    clean_scats_traffic(
        input_path=raw_traffic_path,
        output_path=cleaned_traffic_path
    )

    print("Cleaning AADT...")
    clean_aadt_locations(
        input_path=raw_aadt_path,
        output_path=cleaned_aadt_path
    )
    print("Done cleaning.\n")


    # Phase 2: Merge datasets
    print("--- Phase 2: Merging data ---")
    
    merge_datasets(
        traffic_path=cleaned_traffic_path,
        sites_path=cleaned_sites_path,
        aadt_path=cleaned_aadt_path,
        output_path=master_output_path
    )
    print("Done merging.\n")


    # Finish
    print("All done!")
    print(f"Master dataset successfully saved to: {master_output_path}")

if __name__ == "__main__":
    main()
