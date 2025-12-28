import requests
import os
import psycopg2
from datetime import datetime, timezone
from dotenv import load_dotenv


load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def fetch_carbon_data():
    """Fetches carbon intensity for the current day."""
    
    today_str = today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    print(f"Fetching data for date: {today_str}...")
    
    url = f"https://api.carbonintensity.org.uk/intensity/date/{today_str}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()['data']

def save_to_postgres(data):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    
    print(f"Processing {len(data)} records...")
    
    for entry in data:
        timestamp_str = entry['from']
        forecast = entry['intensity']['forecast']
        actual = entry['intensity']['actual'] 
        region_id = 'UK_NATIONAL' 
        
   
        query = """
        INSERT INTO raw_carbon_intensity (region_id, timestamp_utc, forecast_intensity, actual_intensity)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (region_id, timestamp_utc)
        DO UPDATE SET
            forecast_intensity = EXCLUDED.forecast_intensity,
            actual_intensity = EXCLUDED.actual_intensity;
        """
        
        cursor.execute(query, (region_id, timestamp_str, forecast, actual))
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Data successfully synced to DB.")

if __name__ == "__main__":
    try:
        raw_data = fetch_carbon_data()
        save_to_postgres(raw_data)
    except Exception as e:
        print(f"Pipeline failed: {e}")