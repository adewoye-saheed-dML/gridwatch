# GridWatch: Heavy Industry Load Optimization

[![Live Application](https://img.shields.io/badge/Live-App-brightgreen)](https://gridwatch-app.streamlit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

GridWatch is an end-to-end analytics engineering platform designed to optimize energy consumption for heavy industry operations. By ingesting and analyzing real-time carbon intensity data from the UK National Grid, the system identifies optimal production windows to minimize Scope 2 carbon emissions.

## Project Overview

Industrial operations such as smelting, manufacturing, and large-scale computing consume significant amounts of electricity. GridWatch provides a data-driven approach to scheduling these loads by tracking grid carbon intensity. The system establishes a dynamic baseline using a 24-hour moving average and categorizes upcoming time slots as favorable or unfavorable for energy-intensive tasks.

## Problem Statement

Heavy industries often operate continuously or on rigid schedules, ignoring the fluctuations in the carbon intensity of the electricity grid. Running high-load machinery during peak fossil-fuel usage times results in:

- **Higher Carbon Footprint**: Increased Scope 2 emissions
- **Inefficiency**: Missed opportunities to utilize renewable energy surges
- **Regulatory Risk**: Difficulty meeting increasingly strict ESG reporting standards

## Solution Approach

GridWatch solves this by creating a real-time decision support system:

- Extracts live carbon intensity forecasts from the National Grid ESO API
- Calculates a dynamic 24-hour rolling average to normalize against daily seasonalities
- Visualizes "Go/No-Go" windows in a dashboard, allowing operators to quantify the CO2 savings of shifting production

## Architecture

The project implements a standard ELT (Extract, Load, Transform) pipeline:

```graph LR

    A[UK National Grid API] -->|Extract (Python)| B(Ingestion Script)
    B -->|Load| C[(Supabase PostgreSQL)]
    C -->|Transform (dbt)| D[Analytics Tables]
    D -->|Serve| E[Streamlit Dashboard]
    F[GitHub Actions] -->|Orchestrate| B
    
```

**Pipeline Components:**

1. **Ingestion**: A Python script fetches the latest forecast and actual intensity data
2. **Storage**: Data is upserted into a PostgreSQL database (Supabase) to ensure idempotency
3. **Transformation**: dbt (data build tool) processes the raw data, calculating rolling averages and assigning operational status signals
4. **Serving**: A Streamlit dashboard consumes the transformed data to provide actionable insights
5. **Orchestration**: GitHub Actions schedules the ingestion process to run hourly

## Tech Stack

- **Language**: Python 3.9+
- **Data Warehouse**: PostgreSQL (Supabase)
- **Transformation**: dbt Core (dbt-postgres adapter)
- **Visualization**: Streamlit, Plotly Express
- **Orchestration**: GitHub Actions (Cron)
- **Libraries**: pandas, SQLAlchemy, requests, python-dotenv

## Data Sources

**Carbon Intensity API**: Provided by National Grid ESO

- **Endpoint**: `https://api.carbonintensity.org.uk/intensity/date/{YYYY-MM-DD}`
- **Metrics**: Forecast Intensity (gCO2/kWh), Actual Intensity, Timestamp (UTC)

## Key Features

- **Automated Ingestion Pipeline**: Fetches live data and handles duplicate records using ON CONFLICT logic to maintain data integrity

- **Dynamic Baseline Analysis**: Uses SQL window functions to calculate a 24-hour rolling average of carbon intensity, adapting recommendations to daily grid fluctuations

- **Operational Status Indicators**:
  - 🟢 **Super Green**: Intensity is >15% below the 24-hour average
  - 🟢 **Green**: Intensity is below the 24-hour average
  - 🔴 **Red**: Intensity is above the 24-hour average

- **Shift Planning Dashboard**: An interactive interface that allows operators to input projected load (kWh) and calculates specific CO2 (kg) output and potential savings

## Setup & Installation

### Prerequisites

- Python 3.9 or higher
- PostgreSQL database (e.g., local Postgres or Supabase)
- dbt CLI installed
- Git

### Installation Steps

1. **Clone the Repository**

```
git clone https://github.com/adewoye-saheed-dML/gridwatch.git
cd gridwatch
```

2. **Configure Environment**

Create a `.env` file in the root directory:

```
touch .env
```

Add your database connection string:

```
DATABASE_URL="postgresql://user:password@host:port/database"
```

3. **Install Dependencies**

```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## How to Run

1. **Initialize Database**

The ingestion script expects a table named `raw_carbon_intensity`. Run the SQL found in the `ingest.py` logic or let the script handle the initial insert if permissions allow.

2. **Ingest Data**

```
python ingest.py
```

3. **Transform Data (dbt)**

```
cd transform
dbt deps
dbt run
cd ..
```

4. **Launch Dashboard**

```
streamlit run app.py
```

## Project Structure

```text

gridwatch/
├── .github/workflows/
│   └── hourly_sync.yml       # CI/CD: Hourly ingestion cron job
├── transform/                # dbt Project
│   ├── models/
│   │   ├── source.yml        # Source definitions
│   │   └── fct_green_windows.sql # Core logic model
│   └── dbt_project.yml       # dbt configuration
├── app.py                    # Streamlit Dashboard application
├── ingest.py                 # Python API extraction script
├── requirements.txt          # Python dependencies
└── README.md                 # Project Documentation

```

## Usage Example

**Scenario**: A shift manager at a steel plant needs to schedule a 4-hour smelting operation consuming 1000 kWh.

1. **Input**: The manager enters "1000" into the "Projected Load (kWh)" sidebar
2. **Analysis**: The dashboard shows current intensity is 200 g/kWh, but a "Super Green" window starts in 3 hours at 150 g/kWh
3. **Result**: The manager waits 3 hours, saving approximately 50 kg of CO2 (calculated dynamically by the app)

## Business Impact

- **Cost Reduction**: Often correlates with lower electricity spot prices during high renewable generation
- **ESG Compliance**: Provides concrete data for sustainability reporting
- **Brand Value**: Demonstrates commitment to green manufacturing practices

## Future Improvements

- **Price Integration**: Add electricity pricing data to optimize for both Cost and Carbon
- **Alerting System**: Email or Slack notifications when a "Super Green" window opens
- **Historical Reporting**: A retrospective view of actual carbon saved vs. potential

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.
---
