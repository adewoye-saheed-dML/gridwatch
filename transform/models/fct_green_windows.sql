{{ config(
    materialized='view'
) }}

WITH source_data AS (
    SELECT * FROM {{ source('gridwatch', 'raw_carbon_intensity') }}
),

moving_average AS (
    SELECT
        region_id,
        timestamp_utc,
        forecast_intensity,
        actual_intensity,
        
        -- Window Function: Calculate 24-hour rolling average
        AVG(forecast_intensity) OVER (
            PARTITION BY region_id 
            ORDER BY timestamp_utc 
            ROWS BETWEEN 24 PRECEDING AND CURRENT ROW
        ) as avg_24h_intensity

    FROM source_data
)

SELECT
    region_id,
    timestamp_utc,
    forecast_intensity,
    avg_24h_intensity,
    
    -- Business Logic: Is this a good time to run?
    CASE 
        WHEN forecast_intensity < (avg_24h_intensity * 0.85) THEN 'super_green' 
        WHEN forecast_intensity < avg_24h_intensity THEN 'green'
        ELSE 'red'
    END as window_status

FROM moving_average
ORDER BY timestamp_utc DESC
