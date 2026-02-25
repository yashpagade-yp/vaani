"""
weather.py — Live Weather Tool
================================
Gives Vaani the ability to check live weather for any city.

Uses Open-Meteo API — completely free, no API key required.
Uses Open-Meteo Geocoding API to resolve city names to coordinates.

Example usage by LLM:
    User: "What's the weather in Mumbai?"
    LLM calls: get_weather(city="Mumbai")
    Tool returns: "Mumbai: 32°C, partly cloudy, humidity 78%, wind 12 km/h"
    LLM speaks: "It's 32 degrees in Mumbai right now, partly cloudy..."
"""

import httpx
from pipecat.processors.frameworks.rtvi import FunctionCallParams

from core.logger import logger


# ── WMO Weather Code Descriptions ─────────────────────────────────────────────
# Open-Meteo returns WMO codes — map them to human-readable descriptions
WMO_CODES = {
    0: "clear sky",
    1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "icy fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
    61: "light rain", 63: "moderate rain", 65: "heavy rain",
    71: "light snow", 73: "moderate snow", 75: "heavy snow",
    77: "snow grains",
    80: "light showers", 81: "moderate showers", 82: "violent showers",
    85: "snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "thunderstorm with heavy hail",
}


# ── Tool Schema ────────────────────────────────────────────────────────────────
GET_WEATHER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": (
            "Get the current live weather for any city in the world. "
            "Returns temperature, weather condition, humidity, and wind speed. "
            "Use this whenever the user asks about weather, temperature, or climate."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name (e.g., 'Mumbai', 'New York', 'London')"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit. Default is celsius.",
                    "default": "celsius"
                }
            },
            "required": ["city"]
        }
    }
}


# ── Tool Handler ───────────────────────────────────────────────────────────────
async def get_weather_handler(params: FunctionCallParams) -> None:
    """Handle a get_weather tool call from the LLM."""
    args = params.arguments
    city = args.get("city", "").strip()
    unit = args.get("unit", "celsius")

    logger.info("Tool: get_weather | city='{}' unit={}", city, unit)

    try:
        async with httpx.AsyncClient(timeout=10.0) as http:
            # Step 1: Geocoding — convert city name to lat/lon
            geo_resp = await http.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "language": "en", "format": "json"}
            )
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()

            results = geo_data.get("results", [])
            if not results:
                await params.result_callback(f"Could not find weather data for '{city}'. Please check the city name.")
                return

            location = results[0]
            lat = location["latitude"]
            lon = location["longitude"]
            location_name = location.get("name", city)
            country = location.get("country", "")

            # Step 2: Fetch current weather
            temp_unit = "celsius" if unit == "celsius" else "fahrenheit"
            weather_resp = await http.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,apparent_temperature",
                    "temperature_unit": temp_unit,
                    "wind_speed_unit": "kmh",
                    "timezone": "auto",
                }
            )
            weather_resp.raise_for_status()
            weather_data = weather_resp.json()

            current = weather_data.get("current", {})
            temp = current.get("temperature_2m", "N/A")
            feels_like = current.get("apparent_temperature", "N/A")
            humidity = current.get("relative_humidity_2m", "N/A")
            wind = current.get("wind_speed_10m", "N/A")
            wmo_code = current.get("weather_code", 0)
            condition = WMO_CODES.get(wmo_code, "unknown conditions")
            unit_symbol = "°C" if unit == "celsius" else "°F"

            result = (
                f"{location_name}, {country}: {temp}{unit_symbol} (feels like {feels_like}{unit_symbol}), "
                f"{condition}, humidity {humidity}%, wind {wind} km/h"
            )
            logger.info("Tool: get_weather completed | result='{}'", result)

    except httpx.TimeoutException:
        result = f"Weather request timed out for '{city}'. Please try again."
        logger.warning("Tool: get_weather timeout | city='{}'", city)
    except Exception as e:
        result = f"Could not get weather for '{city}': {str(e)}"
        logger.error("Tool: get_weather error | city='{}' error={}", city, str(e))

    await params.result_callback(result)
