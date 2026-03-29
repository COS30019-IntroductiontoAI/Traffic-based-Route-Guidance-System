"""
Shared test case filters for stratified test evaluation.
Defines 10 test scenarios used by both test_runner.py and test_stratified.py.
"""

import pandas as pd


# Comprehensive list of all 10 test cases with metadata
TEST_CASES = [
    {
        "id": "T01",
        "name": "T01-morning_peak_hour",
        "description": "Weekdays 7-9 AM (morning peak)",
    },
    {
        "id": "T02",
        "name": "T02-evening_peak_hour",
        "description": "Weekdays 4-6 PM (evening peak)",
    },
    {
        "id": "T03",
        "name": "T03-late_night_low_vol",
        "description": "11 PM to 2 AM (late night low volume)",
    },
    {
        "id": "T04",
        "name": "T04-weekday_vs_weekend",
        "description": "Weekends (all data)",
    },
    {
        "id": "T05",
        "name": "T05-mon_morning_vs_fri_afternoon",
        "description": "Monday morning / Friday afternoon",
    },
    {
        "id": "T06",
        "name": "T06-high_vol_intersection",
        "description": "Highest-traffic SCATS sensor",
    },
    {
        "id": "T07",
        "name": "T07-low_vol_intersection",
        "description": "Lowest-traffic SCATS sensor",
    },
    {
        "id": "T08",
        "name": "T08-full_mon",
        "description": "Full Mondays (all hours)",
    },
    {
        "id": "T09",
        "name": "T09-full_week",
        "description": "One full week of highest-volume SCATS sensor",
    },
    {
        "id": "T10",
        "name": "T10-transition_period",
        "description": "Early morning 6-8 AM (transition to peak)",
    },
]


def get_test_cases():
    """Return list of all test cases with metadata."""
    return TEST_CASES


def get_test_case_by_name(test_name: str) -> dict | None:
    """Find a test case by name or id."""
    for tc in TEST_CASES:
        if test_name in {tc["id"], tc["name"]}:
            return tc
    return None


def get_test_filter(test_name: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a filtered dataframe for the requested test scenario.
    
    Args:
        test_name: Test case id (T01-T10) or full name (e.g., "T01-morning_peak_hour")
        df: Input dataframe with columns: datetime, scats_number, location, hour, day_of_week, 
            is_weekend, actual, predicted_lstm, predicted_gru, predicted_lightgbm
    
    Returns:
        Filtered dataframe matching the test scenario criteria
    """
    if test_name in {"T01-morning_peak_hour", "T01"}:
        return df[(df["hour"] >= 7) & (df["hour"] <= 9) & (df["is_weekend"] == 0)]

    if test_name in {"T02-evening_peak_hour", "T02"}:
        return df[(df["hour"] >= 16) & (df["hour"] <= 18) & (df["is_weekend"] == 0)]

    if test_name in {"T03-late_night_low_vol", "T03"}:
        return df[(df["hour"] >= 23) | (df["hour"] <= 2)]

    if test_name in {"T04-weekday_vs_weekend", "T04"}:
        return df[df["is_weekend"] == 1]

    if test_name in {"T05-mon_morning_vs_fri_afternoon", "T05"}:
        monday_morning = (df["day_of_week"] == 0) & (df["hour"] < 12)
        friday_afternoon = (df["day_of_week"] == 4) & (df["hour"] >= 12)
        return df[monday_morning | friday_afternoon]

    if test_name in {"T06-high_vol_intersection", "T06"}:
        avg_vol = df.groupby("scats_number")["actual"].mean()
        top_scats = avg_vol.idxmax()
        print(f"TC06: Highest volume intersection -> SCATS {top_scats} (avg {avg_vol[top_scats]:.2f})")
        return df[df["scats_number"] == top_scats]

    if test_name in {"T07-low_vol_intersection", "T07"}:
        avg_vol = df.groupby("scats_number")["actual"].mean()
        low_scats = avg_vol.idxmin()
        print(f"TC07: Lowest volume intersection -> SCATS {low_scats} (avg {avg_vol[low_scats]:.2f})")
        return df[df["scats_number"] == low_scats]

    if test_name in {"T08-full_mon", "T08"}:
        return df[df["day_of_week"] == 0]

    if test_name in {"T09-full_week", "T09"}:
        top_scats = df.groupby("scats_number").size().idxmax()
        print(f"TC09: Full week intersection -> SCATS {top_scats}")
        return df[df["scats_number"] == top_scats]

    if test_name in {"T10-transition_period", "T10"}:
        return df[(df["hour"] >= 6) & (df["hour"] <= 8)]

    print(f"Warning: No filter defined for '{test_name}', using full dataset.")
    return df
