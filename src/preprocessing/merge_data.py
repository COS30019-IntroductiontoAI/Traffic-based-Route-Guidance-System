import pandas as pd
import os
from scipy.spatial import KDTree


def merge_datasets(
    traffic_path: str,
    sites_path: str,
    aadt_path: str,
    output_path: str
):
    """
    Merge cleaned Traffic, SCATS Sites, and AADT datasets.
    Key logic: Uses KDTree for nearest-neighbor spatial matching to snap 
    noisy SCATS coordinates onto accurate AADT road network coordinates.
    """

    print("____________________________________________")
    print("\nSTEP 4: MERGING DATASETS\n")

    # Check input files
    # Fail fast: Ensure all prerequisites from previous pipeline steps exist.
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

    # Strict merge: 'validate="many_to_one"' ensures that if sites_data accidentally 
    # contains duplicate SCATS numbers, Pandas will throw an error instead of silently 
    # multiplying our time-series traffic rows.
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

    # Performance optimization: Group by scats_number to get just the unique 39 intersection coordinates.
    # Querying the KDTree millions of times (for every row in master_data) would be massively inefficient.
    scats_coordinates = master_data.groupby("scats_number").agg({
        "nb_latitude": "first",
        "nb_longitude": "first"
    }).reset_index()

    aadt_coordinates = aadt_data[[
        "aadt_longitude",
        "aadt_latitude"
    ]].values

    # Build KDTree using ground-truth AADT coordinates for fast spatial lookups O(log N)
    aadt_tree = KDTree(aadt_coordinates)

    query_points = scats_coordinates[[
        "nb_longitude",
        "nb_latitude"
    ]].values

    # Find the nearest AADT node for every SCATS intersection
    distances, nearest_indices = aadt_tree.query(query_points)

    print("Spatial matching completed\n")

    # Retrieve matched AADT records
    print("Retrieving matched AADT records\n")

    # Map the KDTree output back to our SCATS intersections
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

    # Overwrite original SCATS coordinates with exact AADT spatial points
    print("Correcting SCATS coordinates using AADT matched points\n")
    
    #UI FIX: Raw SCATS coordinates are noisy and often fall in off-road terrain. 
    # We overwrite them with AADT coordinates to successfully pull the nodes onto the actual road network.
    master_data["nb_latitude"] = master_data["aadt_latitude"]
    master_data["nb_longitude"] = master_data["aadt_longitude"]
    
    # Drop redundant AADT coordinate columns to clean up dataset
    # We no longer need them since they have become the primary nb_latitude/longitude
    master_data = master_data.drop(columns=["aadt_latitude", "aadt_longitude"])

    # Final checks
    print("Running final checks\n")

    missing_aadt = master_data["distance_to_aadt"].isnull().sum()
    print(f"Rows without matching AADT data: {missing_aadt}")
    print(f"Final dataset shape: {master_data.shape}\n")

    # Save output
    print("Saving master dataset\n")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    master_data.to_csv(output_path, index=False)

    print(f"File saved to: {output_path}")
    print("Merging completed successfully\n")

    return master_data