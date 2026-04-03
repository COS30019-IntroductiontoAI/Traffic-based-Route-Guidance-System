import pandas as pd
import os
from scipy.spatial import KDTree


def merge_datasets(
    traffic_path: str,
    sites_path: str,
    aadt_path: str,
    output_path: str
):

    # Merge cleaned Traffic, SCATS Sites, and AADT datasets into a single master dataset.
    print("____________________________________________")
    print("\nSTEP 4: MERGING DATASETS\n")

    # Check input files
    for path in [traffic_path, sites_path, aadt_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Missing file: {path}. Please run preprocessing first."
            )

    print("Loading cleaned datasets\n")

    traffic_data = pd.read_csv(traffic_path)
    sites_data = pd.read_csv(sites_path)
    aadt_data = pd.read_csv(aadt_path)

    print(f"Traffic data shape: {traffic_data.shape}")
    print(f"Sites data shape: {sites_data.shape}")
    print(f"AADT data shape: {aadt_data.shape}\n")

    # Merge Traffic and Sites
    print("Merging traffic data with SCATS site metadata\n")

    master_data = pd.merge(
        traffic_data,
        sites_data,
        on="scats_number",
        how="left",
        validate="many_to_one"
    )

    missing_sites = master_data["location_description"].isnull().sum()
    print(f"Rows without matching site metadata: {missing_sites}\n")

    # Spatial matching with AADT
    print("Performing spatial matching with AADT data\n")

    scats_coordinates = master_data.groupby("scats_number").agg({
        "nb_latitude": "first",
        "nb_longitude": "first"
    }).reset_index()

    aadt_coordinates = aadt_data[[
        "aadt_longitude",
        "aadt_latitude"
    ]].values

    aadt_tree = KDTree(aadt_coordinates)

    query_points = scats_coordinates[[
        "nb_longitude",
        "nb_latitude"
    ]].values

    distances, nearest_indices = aadt_tree.query(query_points)

    print("Spatial matching completed\n")

    # Retrieve matched AADT records
    print("Retrieving matched AADT records\n")

    matched_aadt = aadt_data.iloc[nearest_indices].reset_index(drop=True)
    matched_aadt["scats_number"] = scats_coordinates["scats_number"].values
    matched_aadt["distance_to_aadt"] = distances

    print("AADT records matched successfully\n")

    # Merge AADT into master dataset
    print("Merging AADT features into master dataset\n")

    master_data = pd.merge(
        master_data,
        matched_aadt,
        on="scats_number",
        how="left",
        validate="many_to_one"
    )

    print("AADT features merged\n")

    # Final checks
    print("Running final checks\n")

    missing_aadt = master_data["aadt_longitude"].isnull().sum()
    print(f"Rows without matching AADT data: {missing_aadt}")
    print(f"Final dataset shape: {master_data.shape}\n")

    # Save output
    print("Saving master dataset\n")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    master_data.to_csv(output_path, index=False)

    print(f"File saved to: {output_path}")
    print("Merging completed successfully\n")

    return master_data