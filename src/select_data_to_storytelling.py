import pandas as pd
import os
import json

def generate_storytelling_data():
    print("Extracting storytelling data...")

    # Set up paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(base_dir, 'data', 'processed', '2006_processed.csv')
    output_dir = os.path.join(base_dir, 'data', 'storytelling_vis')

    os.makedirs(output_dir, exist_ok=True)

    # Load data
    print(f"Loading: {input_file}")
    df = pd.read_csv(input_file)

    # Handle date column
    if 'date' not in df.columns and 'datetime' in df.columns:
        df['date'] = pd.to_datetime(df['datetime']).dt.strftime('%Y-%m-%d')
    elif 'date' in df.columns:
        df['date'] = df['date'].astype(str)

    # 1. Hourly pattern with overall average
    print("[1/5] Processing hourly pattern...")
    chart1 = df.groupby('hour', as_index=False)['traffic_volume'].mean().round(1)
    chart1['overall_average'] = round(df['traffic_volume'].mean(), 1)
    
    with open(os.path.join(output_dir, '1_LineChart_Traffic_By_Hour.json'), 'w') as f:
        json.dump(chart1.to_dict(orient='records'), f, indent=4)

    # 2. Weekday vs Weekend
    print("[2/5] Processing weekday vs weekend...")
    weekday = df[df['is_weekend'] == 0].groupby('hour')['traffic_volume'].mean()
    weekend = df[df['is_weekend'] == 1].groupby('hour')['traffic_volume'].mean()

    chart2 = pd.DataFrame({
        'hour': range(24),
        'weekday_volume': weekday.reindex(range(24)).fillna(0).round(1),
        'weekend_volume': weekend.reindex(range(24)).fillna(0).round(1)
    })

    with open(os.path.join(output_dir, '2_BarChart_Weekday_Vs_Weekend.json'), 'w') as f:
        json.dump(chart2.to_dict(orient='records'), f, indent=4)

    # 3. Traffic hotspots
    print("[3/5] Processing hotspots...")
    chart3 = df.groupby(
        ['scats_number', 'nb_latitude', 'nb_longitude', 'location'],
        as_index=False
    )['traffic_volume'].mean().round(1)
    chart3 = chart3.sort_values(by='traffic_volume', ascending=False)

    with open(os.path.join(output_dir, '3_MapChart_Traffic_Hotspots_LatLng.json'), 'w') as f:
        json.dump(chart3.to_dict(orient='records'), f, indent=4)

    # 4. Volume distribution (Box plot)
    print("[4/5] Processing volume distribution...")
    def boxplot_stats(x):
        return pd.Series(
            [x.min(), x.quantile(0.25), x.median(), x.quantile(0.75), x.max()],
            index=['min', 'q1', 'median', 'q3', 'max']
        )

    chart4 = df.groupby('hour')['traffic_volume'].apply(boxplot_stats).unstack().reset_index().round(1)

    with open(os.path.join(output_dir, '4_BoxPlot_Volume_Distribution_By_Hour.json'), 'w') as f:
        json.dump(chart4.to_dict(orient='records'), f, indent=4)

    # 5. Day of Week traffic (Replaced Radar Chart)
    print("[5/5] Processing day of week traffic...")
    chart5 = df.groupby('day_of_week', as_index=False)['traffic_volume'].mean().round(1)
    
    # Map 0-6 to actual day names
    day_map = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
    chart5['day_name'] = chart5['day_of_week'].map(day_map)
    chart5 = chart5.sort_values('day_of_week')

    with open(os.path.join(output_dir, '5_BarChart_DayOfWeek_Traffic.json'), 'w') as f:
        json.dump(chart5.to_dict(orient='records'), f, indent=4)

    print(f"Done! 5 files saved to: {output_dir}")

if __name__ == "__main__":
    generate_storytelling_data()