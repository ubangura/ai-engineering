import os
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import pandas as pd
import requests

# ---------------------------------------------------------------------
# Call API
# ---------------------------------------------------------------------

# Washington D.C.
latitude = 38.8951
longitude = -77.0364

today = datetime.now()
week_ago = today - timedelta(weeks=1)
start_date = week_ago.strftime("%Y-%m-%d")
end_date = today.strftime("%Y-%m-%d")

url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&start_date={start_date}&end_date={end_date}&daily=temperature_2m_max,temperature_2m_min"
response = requests.get(url)
data = response.json()

# ---------------------------------------------------------------------
# Process Data
# ---------------------------------------------------------------------

daily_data = data["daily"]

df = pd.DataFrame(
    {
        "date": daily_data["time"],
        "max_temp": daily_data["temperature_2m_max"],
        "min_temp": daily_data["temperature_2m_min"],
    }
)

df["avg_temp"] = round((df["max_temp"] + df["min_temp"]) / 2, 1)

df["date"] = pd.to_datetime(df["date"])

# ---------------------------------------------------------------------
# Visualize
# ---------------------------------------------------------------------

plt.figure(figsize=(10, 6))
plt.plot(df["date"], df["max_temp"], "r-o", label="Max")
plt.plot(df["date"], df["min_temp"], "b-o", label="Min")
plt.plot(df["date"], df["avg_temp"], "g--", label="Average")

plt.title("Washington D.C. Weather - Past 7 Days")
plt.xlabel("Date")
plt.ylabel("Temperature (°C)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()

if not os.path.exists("data"):
    os.makedirs("data")

plt.savefig("data/dc_7day_weather_chart.png")
df.to_csv("data/dc_7day_weather.csv", index=False)

print(f"Average temperature: {df['avg_temp'].mean():.1f}°C")
print("Files saved to 'data' directory")
