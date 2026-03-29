import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

SRC_ROOT = Path(__file__).resolve().parent
DATA_DIR = SRC_ROOT / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'

# Configuration paths - Update these four paths as needed
PATH_2014_FOLDER  = str(DATA_DIR / '2014_raw')
PATH_2006         = str(PROCESSED_DIR / '2006_processed.csv')
PATH_LOOKUP       = str(DATA_DIR / 'detector_direction_lookup.csv')
PATH_OUTPUT       = str(PROCESSED_DIR / '2014_processed.csv')

# List of 39 SCATS detector numbers in the Boroondara region
BOROONDARA_SCATS = [
    970, 2000, 2200, 2820, 2825, 2827, 2846,
    3001, 3002, 3120, 3122, 3126, 3127, 3180,
    3662, 3682, 3685, 3804, 3812, 4030, 4032,
    4034, 4035, 4040, 4043, 4051, 4057, 4063,
    4262, 4263, 4264, 4266, 4270, 4272, 4273,
    4321, 4324, 4812, 4821
]

print("Step 1: Loading detector direction lookup table")

# Load the lookup table that maps detectors to directions
lookup_table = pd.read_csv(PATH_LOOKUP)
lookup_table['scats_number'] = lookup_table['scats_number'].astype(int)
lookup_table['nb_detector']  = lookup_table['nb_detector'].astype(int)
print(f"Lookup table loaded: {len(lookup_table)} detector mappings")

print("Step 2: Loading location metadata from 2006 data")

# Load the 2006 processed data to extract location, road name, and coordinates
df_2006 = pd.read_csv(PATH_2006)

# Auto-detect longitude column name (handles both spellings)
lon_col = None
for candidate in ['nb_longtitude', 'nb_longitude', 'nb_long', 'longitude', 'longtitude']:
    if candidate in df_2006.columns:
        lon_col = candidate
        break
if lon_col is None:
    print("WARNING: Could not find longitude column. Available columns:")
    print(df_2006.columns.tolist())
    lon_col = df_2006.columns[df_2006.columns.str.contains('lon', case=False)][0]
    print(f"Using: {lon_col}")

# Standardize to 'nb_longtitude' for consistency
df_2006.rename(columns={lon_col: 'nb_longtitude'}, inplace=True)

scats_meta = (
    df_2006.drop_duplicates(subset=['scats_number', 'location'])
    [['scats_number', 'location', 'road_name', 'nb_latitude', 'nb_longtitude']]
    .copy()
)

def extract_dir_from_location(loc):
    valid_dirs = {'N','S','E','W','NE','NW','SE','SW'}
    for p in str(loc).split():
        if p in valid_dirs:
            return p
    return None

scats_meta['location_dir'] = scats_meta['location'].apply(extract_dir_from_location)
print(f"2006 metadata loaded: {scats_meta['scats_number'].nunique()} sites")

print("Step 3: Processing daily data files")

# Function to process a single daily CSV file and return processed data
def process_one_file(filepath, date_from_filename=None):
    try:
        df = pd.read_csv(filepath, low_memory=False)
    except Exception as e:
        print(f"  ERROR reading {os.path.basename(filepath)}: {e}")
        return None

    # Normalize column names
    col_map = {}
    for c in df.columns:
        cu = c.upper()
        if cu in ['NB_SCATS_SITE','SCATS_SITE','SITE']:       col_map[c] = 'NB_SCATS_SITE'
        if cu in ['NB_DETECTOR','DETECTOR']:                   col_map[c] = 'NB_DETECTOR'
        if cu in ['QT_INTERVAL_COUNT','INTERVAL','DATETIME']:  col_map[c] = 'QT_INTERVAL_COUNT'
        if cu in ['CT_ALARM_24HOUR','ALARM']:                  col_map[c] = 'CT_ALARM_24HOUR'
    df.rename(columns=col_map, inplace=True)

    # Filter Boroondara FIRST (saves memory on large Victoria files)
    df['NB_SCATS_SITE'] = pd.to_numeric(df['NB_SCATS_SITE'], errors='coerce')
    df = df[df['NB_SCATS_SITE'].isin(BOROONDARA_SCATS)].copy()
    if len(df) == 0:
        return None

    # V columns
    v_cols = [c for c in df.columns
              if c.upper().startswith('V') and c[1:].isdigit() and 0 <= int(c[1:]) <= 95]

    # Clean invalid values
    for col in v_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].replace(-1022, np.nan)
        df[col] = df[col].where(df[col] >= 0, np.nan)

    # Drop fully alarmed rows
    if 'CT_ALARM_24HOUR' in df.columns:
        df['CT_ALARM_24HOUR'] = pd.to_numeric(df['CT_ALARM_24HOUR'], errors='coerce')
        df = df[df['CT_ALARM_24HOUR'] < 96]
    if len(df) == 0:
        return None

    # Parse base date from QT_INTERVAL_COUNT (one row = one day in 2014 raw data)
    # Use the filename date if provided (most reliable), otherwise parse from data
    if date_from_filename:
        df['base_date'] = date_from_filename
    else:
        df['base_date'] = pd.to_datetime(df['QT_INTERVAL_COUNT'], dayfirst=True, errors='coerce').dt.normalize()
    df = df.dropna(subset=['base_date'])

    # Unpivot V00-V95 into 96 rows per (site, detector, date)
    # V00=00:00, V01=00:15, ..., V95=23:45
    id_cols = ['NB_SCATS_SITE', 'NB_DETECTOR', 'base_date']
    df_long = df[id_cols + v_cols].melt(
        id_vars=id_cols,
        value_vars=v_cols,
        var_name='v_col',
        value_name='traffic_volume'
    )

    # Compute exact 15-min datetime
    df_long['interval_index'] = df_long['v_col'].str[1:].astype(int)
    df_long['datetime'] = (
        df_long['base_date'] +
        pd.to_timedelta(df_long['interval_index'] * 15, unit='min')
    )

    # Drop invalid volumes
    df_long = df_long.dropna(subset=['traffic_volume'])
    df_long = df_long[df_long['traffic_volume'] >= 0]

    # Time features
    df_long['hour']        = df_long['datetime'].dt.hour
    df_long['day_of_week'] = df_long['datetime'].dt.dayofweek
    df_long['is_weekend']  = df_long['day_of_week'].isin([5,6]).astype(int)
    df_long['is_peak']     = df_long['hour'].isin([7,8,9,16,17,18]).astype(int)

    df_long = df_long[['NB_SCATS_SITE','NB_DETECTOR','datetime',
                        'hour','day_of_week','is_weekend','is_peak','traffic_volume']]
    df_long.rename(columns={'NB_SCATS_SITE':'scats_number','NB_DETECTOR':'nb_detector'}, inplace=True)
    df_long['scats_number'] = df_long['scats_number'].astype(int)
    df_long['nb_detector']  = df_long['nb_detector'].astype(int)

    return df_long

print("Step 4: Processing all daily files in the folder")

# Collect all daily VSDATA CSV files from the 2014 folder
daily_files = sorted(glob.glob(os.path.join(PATH_2014_FOLDER, 'VSDATA_*.csv')))

if len(daily_files) == 0:
    print(f"\nERROR: No VSDATA_*.csv files found in '{PATH_2014_FOLDER}'")
    exit()

print(f"\nFound {len(daily_files)} daily files. Processing...")

all_days = []
for i, fpath in enumerate(daily_files):
    fname = os.path.basename(fpath)
    # Extract date from filename: VSDATA_20141001.csv -> 2014-10-01
    try:
        date_str = fname.split('_')[1].split('.')[0]  # Extract '20141001'
        date_from_file = pd.to_datetime(date_str, format='%Y%m%d')
    except:
        date_from_file = None
    
    result = process_one_file(fpath, date_from_filename=date_from_file)
    if result is not None and len(result) > 0:
        all_days.append(result)
        print(f"  [{i+1}/{len(daily_files)}] {fname} -> {len(result)} rows")
    else:
        print(f"  [{i+1}/{len(daily_files)}] {fname} -> skipped (no data)")

if len(all_days) == 0:
    print("ERROR: No data extracted. Check SCATS numbers and file format.")
    exit()

df_combined = pd.concat(all_days, ignore_index=True)
print(f"\nCombined: {len(df_combined)} hourly rows from {len(all_days)} files")
print(f"Sites found: {sorted(df_combined['scats_number'].unique())}")

print("Step 5: Joining detector information with direction lookup")

# Merge the detector-level data with direction information from the lookup table
df_merged = df_combined.merge(
    lookup_table[['scats_number','nb_detector','direction']],
    on=['scats_number','nb_detector'],
    how='inner'
)
print(f"\nAfter detector->direction join: {len(df_merged)} rows")
print(f"Sites remaining: {df_merged['scats_number'].nunique()}")

print("Step 6: Aggregating traffic volumes by direction")

# Group traffic volumes by location and direction (sum detectors with same direction)
df_direction = (
    df_merged.groupby([
        'scats_number','direction','datetime',
        'hour','day_of_week','is_weekend','is_peak'
    ])['traffic_volume']
    .sum(min_count=1)
    .reset_index()
)

print("Step 7: Joining location metadata from 2006 data")

# Merge with the 2006 location metadata to get road name and coordinates
df_final = df_direction.merge(
    scats_meta,
    left_on=['scats_number','direction'],
    right_on=['scats_number','location_dir'],
    how='inner'
)
df_final.drop(columns=['location_dir','direction'], inplace=True)

# Reorder to match 2006 format exactly
final_cols = [
    'scats_number','location','road_name',
    'nb_latitude','nb_longtitude',
    'datetime','hour','day_of_week',
    'is_weekend','is_peak','traffic_volume'
]
df_final = df_final[final_cols]
df_final = df_final.sort_values(['scats_number','datetime']).reset_index(drop=True)

print("Step 8: Saving processed data to output file")

# Ensure the output directory exists
os.makedirs(os.path.dirname(PATH_OUTPUT) or '.', exist_ok=True)
df_final['datetime'] = df_final['datetime'].dt.strftime('%d/%m/%Y %H:%M:%S')
df_final.to_csv(PATH_OUTPUT, index=False)

print(f"\n{'='*55}")
print(f"DONE! Saved to: {PATH_OUTPUT}")
print(f"Total rows  : {len(df_final)}")
print(f"Sites       : {df_final['scats_number'].nunique()}/39")
print(f"Locations   : {df_final['location'].nunique()}")
print(f"Date range  : {df_final['datetime'].min()} -> {df_final['datetime'].max()}")
print(f"{'='*55}")
print(f"\nSample output:")
print(df_final.head(5).to_string(index=False))
