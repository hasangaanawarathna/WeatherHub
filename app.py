from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import requests
from flask import Flask, jsonify, render_template, request


app = Flask(__name__)

API_KEY = "YOUR_API_KEY"
CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def request_openweather(url: str, city: str) -> dict[str, Any]:
    """Fetch data from OpenWeatherMap and normalize common errors."""
    params = {"q": city, "appid": API_KEY, "units": "metric"}

    try:
        response = requests.get(url, params=params, timeout=10)
        payload = response.json()
    except requests.RequestException as exc:
        raise ValueError("Unable to reach OpenWeatherMap. Please try again.") from exc
    except ValueError as exc:
        raise ValueError("OpenWeatherMap returned an unexpected response.") from exc

    if response.status_code != 200:
        message = payload.get("message", "Unable to load weather data.")
        normalized = message.strip().lower()

        if normalized == "city not found":
            raise ValueError("Invalid city name. Please check the spelling and try again.")
        if response.status_code == 401:
            raise ValueError("Invalid OpenWeatherMap API key. Update API_KEY in app.py.")

        raise ValueError(message.capitalize())

    return payload


def detect_theme(weather_main: str, weather_id: int | None) -> str:
    """Map the weather condition to a visual theme."""
    main = weather_main.lower()

    if weather_id is not None:
        if 600 <= weather_id < 700:
            return "snowy"
        if 200 <= weather_id < 600:
            return "rainy"

    if main == "clear":
        return "sunny"
    if main == "clouds":
        return "cloudy"
    if main in {"rain", "drizzle", "thunderstorm"}:
        return "rainy"
    if main == "snow":
        return "snowy"

    return "cloudy"


def format_local_datetime(dt_value: int, timezone_offset: int) -> str:
    """Convert a Unix timestamp into the city's local time string."""
    local_time = datetime.fromtimestamp(dt_value + timezone_offset, tz=timezone.utc)
    return local_time.strftime("%A, %B %d, %Y %I:%M %p")


def build_forecast_items(forecast_payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Group 3-hour forecast data into daily cards."""
    grouped_days: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for item in forecast_payload.get("list", []):
        grouped_days[item["dt_txt"].split(" ")[0]].append(item)

    forecast_cards: list[dict[str, Any]] = []

    for day_key in sorted(grouped_days.keys())[:5]:
        items = grouped_days[day_key]
        representative = min(
            items,
            key=lambda entry: abs(
                datetime.strptime(entry["dt_txt"], "%Y-%m-%d %H:%M:%S").hour - 12
            ),
        )
        temperatures = [entry["main"]["temp"] for entry in items]
        weather = representative["weather"][0]

        forecast_cards.append(
            {
                "day": datetime.strptime(day_key, "%Y-%m-%d").strftime("%a, %b %d"),
                "min_temp": round(min(temperatures)),
                "max_temp": round(max(temperatures)),
                "description": weather["description"].title(),
                "condition": weather["main"].title(),
                "icon": f"https://openweathermap.org/img/wn/{weather['icon']}@2x.png",
            }
        )

    return forecast_cards


def build_weather_payload(city: str) -> dict[str, Any]:
    """Fetch current conditions and a 5-day forecast for a city."""
    city_name = city.strip()
    if not city_name:
        raise ValueError("Please enter a city name.")

    current = request_openweather(CURRENT_WEATHER_URL, city_name)
    forecast = request_openweather(FORECAST_URL, city_name)

    weather = current["weather"][0]
    timezone_offset = int(current.get("timezone", 0))
    theme = detect_theme(weather["main"], weather.get("id"))

    return {
        "city": f"{current['name']}, {current['sys']['country']}",
        "temperature": round(current["main"]["temp"]),
        "feels_like": round(current["main"]["feels_like"]),
        "humidity": current["main"]["humidity"],
        "wind_speed": round(current["wind"]["speed"], 1),
        "condition": weather["main"].title(),
        "description": weather["description"].title(),
        "icon": f"https://openweathermap.org/img/wn/{weather['icon']}@2x.png",
        "local_time": format_local_datetime(int(current["dt"]), timezone_offset),
        "theme": theme,
        "forecast": build_forecast_items(forecast),
    }


@app.get("/")
def index() -> str:
    """Render the main weather dashboard."""
    return render_template("index.html")


@app.get("/api/weather")
def api_weather() -> tuple[Any, int]:
    """Return weather data as JSON for the frontend."""
    city = request.args.get("city", "")

    try:
        payload = build_weather_payload(city)
        return jsonify({"success": True, "data": payload}), 200
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


if __name__ == "__main__":
    app.run(debug=True)