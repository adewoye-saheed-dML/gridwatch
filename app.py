import os
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv

# 1. Configuration
st.set_page_config(page_title="GridWatch Operator", page_icon="⚡", layout="wide")
load_dotenv()

# 2. Database Connection
@st.cache_resource
def get_db_engine():
    db_url = os.getenv("DATABASE_URL")
    return create_engine(db_url)

def fetch_forecast_data():
    engine = get_db_engine()
    query = """
        SELECT * FROM analytics.fct_green_windows 
        ORDER BY timestamp_utc ASC
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
        
    # FORCE DATA TYPES (Crucial for preventing math errors)
    df['forecast_intensity'] = pd.to_numeric(df['forecast_intensity'])
    df['avg_24h_intensity'] = pd.to_numeric(df['avg_24h_intensity'])
    
    return df

def calculate_kpis(df, load_kwh):
    # Get the row for "Right Now"
    latest = df.iloc[0]
    
    # Extract values and ensure they are floats
    current_intensity = float(latest['forecast_intensity'])
    avg_intensity = float(latest['avg_24h_intensity'])
    current_status = latest['window_status']
    
    # Calculate Savings
    savings_pct = ((avg_intensity - current_intensity) / avg_intensity) * 100
    
    # Find Best Window in next 24h
    next_24h = df.iloc[0:48]
    best_slot = next_24h.loc[next_24h['forecast_intensity'].idxmin()]
    
    # CO2 Math
    co2_now = (current_intensity * load_kwh) / 1000
    co2_best = (float(best_slot['forecast_intensity']) * load_kwh) / 1000
    co2_saved = co2_now - co2_best

    return {
        "status": current_status,
        "intensity": current_intensity,
        "savings_pct": savings_pct,
        "best_time": str(best_slot['timestamp_utc']),
        "best_intensity": float(best_slot['forecast_intensity']),
        "co2_now": co2_now,
        "co2_saved": co2_saved,
        "avg_intensity": avg_intensity
    }

def main():
    # Sidebar
    st.sidebar.title("Shift Parameters")
    load_kwh = st.sidebar.number_input("Projected Load (kWh)", min_value=0, value=1000, step=100)
    
    st.title("GridWatch: Shift Scheduler")
    st.markdown("### Heavy Industry Load Optimization")

    try:
        df = fetch_forecast_data()
        
        if df.empty:
            st.warning("System Status: Offline (No Data Available)")
            return

        kpis = calculate_kpis(df, load_kwh)
        
        # --- KPI Display ---
        c1, c2, c3, c4 = st.columns(4)
        
        # 1. Intensity
        c1.metric("Current Intensity", f"{kpis['intensity']:.0f} g/kWh", f"{kpis['savings_pct']:.1f}% vs Avg")
        
        # 2. Best Time (Slice string to HH:MM)
        time_str = kpis['best_time'][11:16]
        c2.metric("Optimal Window", time_str, f"{kpis['best_intensity']:.0f} g/kWh")
        
        # 3. Status
        c3.metric("Window Status", kpis['status'].replace('_', ' ').title())
        
        # 4. CO2 Impact
        c4.metric("Est. CO2 Output", f"{kpis['co2_now']:.1f} kg", f"-{kpis['co2_saved']:.1f} kg potential savings")

        st.divider()

        # --- Recommendation ---
        if kpis['status'] == 'super_green':
            st.success(f"**OPTIMAL WINDOW** | Intensity is {kpis['savings_pct']:.0f}% below average.")
        elif kpis['status'] == 'green':
            st.info("✅ **OPERATIONAL** | Intensity levels within acceptable range.")
        else:
            st.error(f"⛔ **HIGH INTENSITY** | Recommended hold until {time_str}.")

        # --- Chart ---
        st.subheader("48-Hour Carbon Intensity Forecast")
        
        df['chart_time'] = df['timestamp_utc'].astype(str)
        
        color_map = {'super_green': 'green', 'green': 'lightgreen', 'red': 'red'}
        
        fig = px.bar(
            df, 
            x='chart_time', 
            y='forecast_intensity',
            color='window_status',
            color_discrete_map=color_map,
            labels={'forecast_intensity': 'Intensity (g/kWh)', 'chart_time': 'Time (UTC)'}
        )
        
        # Add Reference Lines
        fig.add_hline(y=kpis['avg_intensity'], line_dash="dash", line_color="black", annotation_text="Daily Avg")
        fig.update_layout(showlegend=False)

        # UPDATED: Removed 'use_container_width' to fix the warning
        st.plotly_chart(fig)

        # --- Export ---
        with st.expander("Detailed Schedule"):
            # UPDATED: Removed 'use_container_width' to fix the warning
            st.dataframe(df)
            st.download_button(
                "Download CSV",
                df.to_csv(index=False).encode('utf-8'),
                "gridwatch_schedule.csv",
                "text/csv"
            )

    except Exception as e:
        st.error(f"System Error: {str(e)}")

if __name__ == "__main__":
    main()
