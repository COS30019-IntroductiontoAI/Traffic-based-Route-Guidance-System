"""Process 2014 raw SCATS files into the standardized processed schema."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)

SRC_ROOT = Path(__file__).resolve().parent
DATA_DIR = SRC_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

PATH_2014_FOLDER = DATA_DIR / "2014_raw"
PATH_2006 = PROCESSED_DIR / "2006_processed.csv"
PATH_LOOKUP = DATA_DIR / "detector_direction_lookup.csv"
PATH_OUTPUT = PROCESSED_DIR / "2014_processed.csv"


def extract_dir_from_location(location: str) -> str | None:
    """Extract compass direction token from a location string.

    Args:
        location: Location text containing optional compass direction token.

    Returns:
        Extracted direction token or None if unavailable.
    """
    valid_dirs = {"N", "S", "E", "W", "NE", "NW", "SE", "SW"}
    for part in str(location).split():
        if part in valid_dirs:
            return part
    return None


def load_lookup_table(path_lookup: Path) -> pd.DataFrame:
    """Load detector-to-direction lookup table.

    Args:
        path_lookup: Lookup CSV path.

    Returns:
        Normalized lookup dataframe.

    Raises:
        FileNotFoundError: If file does not exist.
        pd.errors.EmptyDataError: If file is empty.
        pd.errors.ParserError: If CSV parsing fails.
        KeyError: If required columns are missing.
    """
    lookup_df = pd.read_csv(path_lookup)
    required = {"scats_number", "nb_detector", "direction"}
    missing = required.difference(set(lookup_df.columns))
    if missing:
        raise KeyError(f"Lookup table is missing required columns: {sorted(missing)}")

    lookup_df = lookup_df.copy()
    lookup_df["scats_number"] = pd.to_numeric(lookup_df["scats_number"], errors="coerce")
    lookup_df["nb_detector"] = pd.to_numeric(lookup_df["nb_detector"], errors="coerce")
    lookup_df = lookup_df.dropna(subset=["scats_number", "nb_detector", "direction"])
    lookup_df["scats_number"] = lookup_df["scats_number"].astype(int)
    lookup_df["nb_detector"] = lookup_df["nb_detector"].astype(int)
    return lookup_df


def detect_longitude_column(df_columns: pd.Index) -> str:
    """Detect longitude column name from known schema variants.

    Args:
        df_columns: Input dataframe columns.

    Returns:
        Chosen longitude column name.

    Raises:
        KeyError: If no longitude-like column can be found.
    """
    for candidate in ["nb_longtitude", "nb_longitude", "nb_long", "longitude", "longtitude"]:
        if candidate in df_columns:
            return candidate

    lon_like = [column for column in df_columns if "lon" in str(column).lower()]
    if lon_like:
        return lon_like[0]
    raise KeyError("No longitude column found in 2006 processed data.")


def load_boroondara_scats(path_2006: Path) -> set[int]:
    """Load Boroondara SCATS ids dynamically from 2006 processed data.

    Args:
        path_2006: 2006 processed CSV path.

    Returns:
        Set of SCATS ids present in the 2006 Boroondara dataset.

    Raises:
        FileNotFoundError: If input file is missing.
        pd.errors.EmptyDataError: If file is empty.
        pd.errors.ParserError: If CSV parsing fails.
        KeyError: If scats_number column is missing.
        ValueError: If no SCATS ids can be derived.
    """
    scats_df = pd.read_csv(path_2006, usecols=["scats_number"])
    scats_series = pd.to_numeric(scats_df["scats_number"], errors="coerce").dropna().astype(int)
    scats_set = set(scats_series.tolist())
    if not scats_set:
        raise ValueError("No SCATS ids were found in 2006 processed data.")
    return scats_set


def load_scats_metadata(path_2006: Path) -> pd.DataFrame:
    """Load 2006 metadata columns needed to map direction to location records.

    Args:
        path_2006: 2006 processed CSV path.

    Returns:
        Metadata dataframe keyed by scats_number and location direction.
    """
    df_2006 = pd.read_csv(path_2006)
    longitude_column = detect_longitude_column(df_2006.columns)
    df_2006 = df_2006.rename(columns={longitude_column: "nb_longtitude"})

    required = {"scats_number", "location", "road_name", "nb_latitude", "nb_longtitude"}
    missing = required.difference(set(df_2006.columns))
    if missing:
        raise KeyError(f"2006 metadata is missing required columns: {sorted(missing)}")

    scats_meta = (
        df_2006.drop_duplicates(subset=["scats_number", "location"])
        [["scats_number", "location", "road_name", "nb_latitude", "nb_longtitude"]]
        .copy()
    )
    scats_meta["location_dir"] = scats_meta["location"].apply(extract_dir_from_location)
    scats_meta = scats_meta.dropna(subset=["location_dir"])
    return scats_meta


def normalize_raw_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize key raw-column names to a canonical schema.

    Args:
        df: Raw daily dataframe.

    Returns:
        Dataframe with canonical key columns.
    """
    col_map: dict[str, str] = {}
    for column in df.columns:
        column_upper = column.upper()
        if column_upper in {"NB_SCATS_SITE", "SCATS_SITE", "SITE"}:
            col_map[column] = "NB_SCATS_SITE"
        if column_upper in {"NB_DETECTOR", "DETECTOR"}:
            col_map[column] = "NB_DETECTOR"
        if column_upper in {"QT_INTERVAL_COUNT", "INTERVAL", "DATETIME"}:
            col_map[column] = "QT_INTERVAL_COUNT"
        if column_upper in {"CT_ALARM_24HOUR", "ALARM"}:
            col_map[column] = "CT_ALARM_24HOUR"
    return df.rename(columns=col_map)


def parse_date_from_filename(file_path: Path) -> pd.Timestamp | None:
    """Parse date token from VSDATA_YYYYMMDD.csv filename.

    Args:
        file_path: Daily raw-file path.

    Returns:
        Parsed timestamp or None when pattern does not match.
    """
    try:
        date_token = file_path.name.split("_")[1].split(".")[0]
        return pd.to_datetime(date_token, format="%Y%m%d")
    except (IndexError, ValueError):
        return None


def process_one_file(
    file_path: Path,
    boroondara_scats: set[int],
    date_from_filename: pd.Timestamp | None,
) -> pd.DataFrame | None:
    """Process one 2014 raw daily file into detector-level 15-minute records.

    Args:
        file_path: Raw daily CSV path.
        boroondara_scats: SCATS ids allowed in output.
        date_from_filename: Optional base date extracted from filename.

    Returns:
        Processed daily dataframe or None when no usable rows remain.

    Raises:
        FileNotFoundError: If file does not exist.
        pd.errors.EmptyDataError: If file is empty.
        pd.errors.ParserError: If CSV parsing fails.
        KeyError: If required columns are missing.
    """
    df = pd.read_csv(file_path, low_memory=False)
    df = normalize_raw_columns(df)

    required = {"NB_SCATS_SITE", "NB_DETECTOR", "QT_INTERVAL_COUNT"}
    missing = required.difference(set(df.columns))
    if missing:
        raise KeyError(f"File {file_path.name} is missing required columns: {sorted(missing)}")

    df = df.copy()
    df["NB_SCATS_SITE"] = pd.to_numeric(df["NB_SCATS_SITE"], errors="coerce")
    df = df[df["NB_SCATS_SITE"].isin(boroondara_scats)].copy()
    if df.empty:
        return None

    v_cols = [
        column
        for column in df.columns
        if column.upper().startswith("V") and column[1:].isdigit() and 0 <= int(column[1:]) <= 95
    ]
    if not v_cols:
        return None

    for column in v_cols:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        df[column] = df[column].replace(-1022, np.nan)
        df[column] = df[column].where(df[column] >= 0, np.nan)

    if "CT_ALARM_24HOUR" in df.columns:
        df["CT_ALARM_24HOUR"] = pd.to_numeric(df["CT_ALARM_24HOUR"], errors="coerce")
        df = df[df["CT_ALARM_24HOUR"] < 96]
    if df.empty:
        return None

    if date_from_filename is not None:
        df["base_date"] = pd.Timestamp(date_from_filename)
    else:
        df["base_date"] = pd.to_datetime(df["QT_INTERVAL_COUNT"], dayfirst=True, errors="coerce").dt.normalize()
    df = df.dropna(subset=["base_date"])
    if df.empty:
        return None

    id_cols = ["NB_SCATS_SITE", "NB_DETECTOR", "base_date"]
    df_long = df[id_cols + v_cols].melt(
        id_vars=id_cols,
        value_vars=v_cols,
        var_name="v_col",
        value_name="traffic_volume",
    )

    df_long["interval_index"] = df_long["v_col"].str[1:].astype(int)
    df_long["datetime"] = df_long["base_date"] + pd.to_timedelta(df_long["interval_index"] * 15, unit="min")

    df_long = df_long.dropna(subset=["traffic_volume"])
    df_long = df_long[df_long["traffic_volume"] >= 0]
    if df_long.empty:
        return None

    df_long["hour"] = df_long["datetime"].dt.hour
    df_long["day_of_week"] = df_long["datetime"].dt.dayofweek
    df_long["is_weekend"] = df_long["day_of_week"].isin([5, 6]).astype(int)
    df_long["is_peak"] = df_long["hour"].isin([7, 8, 9, 16, 17, 18]).astype(int)

    df_long = df_long[
        [
            "NB_SCATS_SITE",
            "NB_DETECTOR",
            "datetime",
            "hour",
            "day_of_week",
            "is_weekend",
            "is_peak",
            "traffic_volume",
        ]
    ]
    df_long = df_long.rename(columns={"NB_SCATS_SITE": "scats_number", "NB_DETECTOR": "nb_detector"})
    df_long["scats_number"] = df_long["scats_number"].astype(int)
    df_long["nb_detector"] = pd.to_numeric(df_long["nb_detector"], errors="coerce").astype("Int64")
    df_long = df_long.dropna(subset=["nb_detector"]).copy()
    df_long["nb_detector"] = df_long["nb_detector"].astype(int)
    return df_long


def build_processed_2014_dataframe(
    raw_folder: Path,
    path_2006: Path,
    path_lookup: Path,
) -> pd.DataFrame:
    """Build the processed 2014 dataset aligned with 2006 schema.

    Args:
        raw_folder: Directory containing VSDATA_*.csv daily files.
        path_2006: 2006 processed CSV for metadata and dynamic SCATS filtering.
        path_lookup: Detector direction lookup CSV.

    Returns:
        Processed 2014 dataframe.

    Raises:
        FileNotFoundError: If required files/folders are missing.
        ValueError: If no usable data can be produced.
        KeyError: If required columns are missing.
        pd.errors.EmptyDataError: If a required CSV is empty.
        pd.errors.ParserError: If CSV parsing fails.
    """
    LOGGER.info("Loading detector direction lookup table from %s", path_lookup)
    lookup_table = load_lookup_table(path_lookup)
    LOGGER.info("Lookup table loaded: %d detector mappings", len(lookup_table))

    LOGGER.info("Loading 2006 metadata and dynamic SCATS filter from %s", path_2006)
    boroondara_scats = load_boroondara_scats(path_2006)
    scats_meta = load_scats_metadata(path_2006)
    LOGGER.info("Loaded %d dynamic SCATS ids from 2006", len(boroondara_scats))

    if not raw_folder.exists():
        raise FileNotFoundError(f"Raw 2014 folder not found: {raw_folder}")

    daily_files = sorted(raw_folder.glob("VSDATA_*.csv"))
    if not daily_files:
        raise FileNotFoundError(f"No VSDATA_*.csv files found in {raw_folder}")

    LOGGER.info("Processing %d daily raw files", len(daily_files))
    all_days: list[pd.DataFrame] = []

    for index, file_path in enumerate(daily_files, start=1):
        parsed_date = parse_date_from_filename(file_path)
        try:
            day_df = process_one_file(file_path, boroondara_scats, parsed_date)
        except pd.errors.EmptyDataError:
            LOGGER.warning("[%d/%d] %s skipped because file is empty", index, len(daily_files), file_path.name)
            continue
        except pd.errors.ParserError as exc:
            LOGGER.warning("[%d/%d] %s skipped due to parse error: %s", index, len(daily_files), file_path.name, exc)
            continue

        if day_df is None or day_df.empty:
            LOGGER.info("[%d/%d] %s skipped (no matching rows)", index, len(daily_files), file_path.name)
            continue

        all_days.append(day_df)
        LOGGER.info("[%d/%d] %s -> %d rows", index, len(daily_files), file_path.name, len(day_df))

    if not all_days:
        raise ValueError("No usable 2014 rows were extracted after filtering and cleaning.")

    df_combined = pd.concat(all_days, ignore_index=True)
    LOGGER.info("Combined detector rows: %d", len(df_combined))

    df_merged = df_combined.merge(
        lookup_table[["scats_number", "nb_detector", "direction"]],
        on=["scats_number", "nb_detector"],
        how="inner",
    )
    if df_merged.empty:
        raise ValueError("Detector-to-direction merge produced no rows.")

    df_direction = (
        df_merged.groupby(
            ["scats_number", "direction", "datetime", "hour", "day_of_week", "is_weekend", "is_peak"],
            observed=False,
        )["traffic_volume"]
        .sum(min_count=1)
        .reset_index()
    )

    df_final = df_direction.merge(
        scats_meta,
        left_on=["scats_number", "direction"],
        right_on=["scats_number", "location_dir"],
        how="inner",
    )
    if df_final.empty:
        raise ValueError("Direction-to-location metadata merge produced no rows.")

    df_final = df_final.drop(columns=["location_dir", "direction"])
    final_cols = [
        "scats_number",
        "location",
        "road_name",
        "nb_latitude",
        "nb_longtitude",
        "datetime",
        "hour",
        "day_of_week",
        "is_weekend",
        "is_peak",
        "traffic_volume",
    ]
    df_final = df_final[final_cols]
    df_final = df_final.sort_values(["scats_number", "datetime"]).reset_index(drop=True)
    return df_final


def save_processed_dataframe(df: pd.DataFrame, output_path: Path) -> Path:
    """Save processed 2014 dataframe to disk.

    Args:
        df: Processed dataframe.
        output_path: Output CSV path.

    Returns:
        Saved output path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df = df.copy()
    output_df["datetime"] = output_df["datetime"].dt.strftime("%d/%m/%Y %H:%M:%S")
    output_df.to_csv(output_path, index=False)
    return output_path


def main() -> int:
    """CLI entrypoint for 2014 processing pipeline.

    Returns:
        Process exit code.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    parser = argparse.ArgumentParser(description="Process 2014 raw SCATS data.")
    parser.add_argument("--raw-folder", default=str(PATH_2014_FOLDER), help="Folder containing VSDATA_*.csv files")
    parser.add_argument("--path-2006", default=str(PATH_2006), help="Path to 2006 processed CSV")
    parser.add_argument("--lookup", default=str(PATH_LOOKUP), help="Path to detector direction lookup CSV")
    parser.add_argument("--output", default=str(PATH_OUTPUT), help="Output path for processed 2014 CSV")
    args = parser.parse_args()

    try:
        processed_df = build_processed_2014_dataframe(
            raw_folder=Path(args.raw_folder),
            path_2006=Path(args.path_2006),
            path_lookup=Path(args.lookup),
        )
        output_path = save_processed_dataframe(processed_df, Path(args.output))
    except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError, KeyError, ValueError, OSError) as exc:
        LOGGER.error("2014 processing failed: %s", exc)
        return 1

    LOGGER.info("Saved processed 2014 dataset to %s", output_path)
    LOGGER.info("Total rows: %d", len(processed_df))
    LOGGER.info("Sites: %d", processed_df["scats_number"].nunique())
    LOGGER.info("Locations: %d", processed_df["location"].nunique())
    LOGGER.info("Date range: %s -> %s", processed_df["datetime"].min(), processed_df["datetime"].max())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
