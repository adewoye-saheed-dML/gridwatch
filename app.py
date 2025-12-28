import streamlit as st
import pandas as pd
import os
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Page Config
st.set_page_config(page_title="GridWatch Operator", page_icon="⚡", layout="centered")

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

@st.cache_resource
def get_engine():
    return create_engine(DB_URL)

def get_data():
    engine = get_engine()
    query = """
    SELECT * FROM analytics.fct_green_windows 
    ORDER BY timestamp_utc ASC
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df

st.title("⚡ GridWatch: Shift Scheduler")
st.markdown("### Heavy Industry Load Optimization")

try:
    df = get_data()
    
    if df.empty:
        st.warning("No data found.")
    else:
        # 1. Current Status
        latest_row = df.iloc[0] 
        current_status = latest_row['window_status']
        current_intensity = latest_row['forecast_intensity']
        avg_intensity = latest_row['avg_24h_intensity']
        
        # Calculate Savings %
        savings_pct = ((avg_intensity - current_intensity) / avg_intensity) * 100
        
        # 2. Find Best Upcoming Window (Next 12 hours)
        next_12h = df.iloc[0:24] 
        best_slot = next_12h.loc[next_12h['forecast_intensity'].idxmin()]
        # Convert to string to avoid Timestamp issues
        best_time = str(best_slot['timestamp_utc']) 
        best_val = best_slot['forecast_intensity']

        # --- KPI ROW ---
        c1, c2, c3 = st.columns(3)
        c1.metric("Current Intensity", f"{current_intensity} g/kWh", delta=f"{savings_pct:.1f}% vs Avg")
        # Display just the HH:MM part of the time
        c2.metric("Best Time (12h)", f"{best_time[11:16]}", f"{best_val} g/kWh")
        c3.metric("Window Status", current_status.replace('_', ' ').title())

        st.divider()

        # --- BIG RECOMMENDATION ---
        if current_status == 'super_green':
            st.success(f"🚀 **OPTIMAL WINDOW NOW** | Running now saves {savings_pct:.0f}% carbon vs average.")
        elif current_status == 'green':
            st.info(f"✅ **GOOD TO RUN** | Intensity is below daily average.")
        else:
            st.error(f"⛔ **HOLD OPERATIONS** | High intensity. Best time to resume is {best_time[11:16]}.")

        # --- CHART ---
        st.subheader("48-Hour Forecast")
        
        # FIX: Create a string column for the chart to prevent "Timestamp subtraction" error
        df['chart_time'] = df['timestamp_utc'].astype(str)

        color_map = {'super_green': 'green', 'green': 'lightgreen', 'red': 'red'}
        
        fig = px.bar(
            df, 
            x='chart_time',  # Use the string column here!
            y='forecast_intensity',
            color='window_status',
            color_discrete_map=color_map,
            title="Carbon Intensity Forecast",
        )
        # We remove the annotation for now to keep it simple and bug-free
        st.plotly_chart(fig)

except Exception as e:
    st.error(f"Error: {e}")
