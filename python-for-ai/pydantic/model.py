from pydantic import BaseModel


class WeatherResponse(BaseModel):
    city: str
    temperature_fahrenheit: float
    humidity: int
    description: str


api_response = {
    "city": "Washington D.C.",
    "temperature_fahrenheit": 85.0,
    "humidity": 75,
    "description": "Partly cloudy",
}

weather = WeatherResponse.model_validate(api_response)

print(f"Weather in {weather.city}: {weather.temperature_fahrenheit}°F")
print(f"Humidity: {weather.humidity}%")
print(f"Conditions: {weather.description}")

print(weather.model_dump_json())
