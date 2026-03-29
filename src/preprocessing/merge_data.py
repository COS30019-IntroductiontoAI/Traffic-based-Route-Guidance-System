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


    print("\n=== STAGE 2: MERGING DATASETS ===")


    # Step 1: Check input files
    for path in [traffic_path, sites_path, aadt_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Missing file: {path}. Please run preprocessing first."
            )

    print("Step 1: Loading cleaned datasets...")

    traffic_data = pd.read_csv(traffic_path)
    sites_data = pd.read_csv(sites_path)
    aadt_data = pd.read_csv(aadt_path)

    print(f"Traffic data shape: {traffic_data.shape}")
    print(f"Sites data shape: {sites_data.shape}")
    print(f"AADT data shape: {aadt_data.shape}")


    # Step 2: Merge Traffic and Sites
    print("Step 2: Merging traffic data with SCATS site metadata...")

    master_data = pd.merge(
        traffic_data,
        sites_data,
        on="scats_number",
        how="left",
        validate="many_to_one"
    )

    missing_sites = master_data["location_description"].isnull().sum()
    print(f"Rows without matching site metadata: {missing_sites}")


    # Step 3: Spatial matching with AADT
    print("Step 3: Performing spatial matching with AADT data...")

    # Extract one coordinate per SCATS station
    scats_coordinates = master_data.groupby("scats_number").agg({
        "nb_latitude": "first",
        "nb_longitude": "first"
    }).reset_index()

    # Prepare AADT coordinate points
    aadt_coordinates = aadt_data[[
        "aadt_longitude",
        "aadt_latitude"
    ]].values

    # Build KDTree for fast nearest neighbor search
    aadt_tree = KDTree(aadt_coordinates)

    # Find nearest AADT point for each SCATS station
    query_points = scats_coordinates[[
        "nb_longitude",
        "nb_latitude"
    ]].values

    distances, nearest_indices = aadt_tree.query(query_points)


    # Step 4: Retrieve matched AADT records
    print("Step 4: Matching AADT records...")

    matched_aadt = aadt_data.iloc[nearest_indices].reset_index(drop=True)

    # Attach SCATS identifier
    matched_aadt["scats_number"] = scats_coordinates["scats_number"].values

    # Store distance as a feature
    matched_aadt["distance_to_aadt"] = distances


    # Step 5: Merge AADT into master dataset
    print("Step 5: Merging AADT features into master dataset...")

    master_data = pd.merge(
        master_data,
        matched_aadt,
        on="scats_number",
        how="left",
        validate="many_to_one"
    )


    # Step 6: Final checks
    print("Step 6: Performing final checks...")

    missing_aadt = master_data["aadt_longitude"].isnull().sum()
    print(f"Rows without matching AADT data: {missing_aadt}")

    print(f"Final dataset shape: {master_data.shape}")


    # Step 7: Save output
    print("Step 7: Saving master dataset...")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    master_data.to_csv(output_path, index=False)

    print("Merging process completed successfully.")
    print(f"Output saved to: {output_path}")

    return master_data