"""Fetch weather and AQI from Open-Meteo (free, no API key required)."""

from dataclasses import dataclass
from datetime import datetime

import requests

WMO_ZH = {
    0: "晴",
    1: "大部晴",
    2: "多云",
    3: "阴",
    45: "雾",
    48: "雾凇",
    51: "小毛毛雨",
    53: "毛毛雨",
    55: "大毛毛雨",
    56: "冻毛毛雨",
    57: "大冻毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "小冻雨",
    67: "大冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "小阵雨",
    81: "阵雨",
    82: "大阵雨",
    85: "小阵雪",
    86: "大阵雪",
    95: "雷暴",
    96: "雷暴+冰雹",
    99: "强雷暴+冰雹",
}

# US EPA AQI categories
AQI_LEVEL_ZH = {
    (0, 50): "优",
    (51, 100): "良",
    (101, 150): "轻度污染",
    (151, 200): "中度污染",
    (201, 300): "重度污染",
    (301, 500): "危险",
}


WEEKDAY_ZH = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def format_datetime(dt: datetime) -> str:
    """Format datetime as '2026-03-19 08:01:06 星期四'."""
    return f"{dt.strftime('%Y-%m-%d %H:%M:%S')} {WEEKDAY_ZH[dt.weekday()]}"


@dataclass
class City:
    name: str
    lat: float
    lon: float


def parse_cities(raw: str) -> list[City]:
    """Parse 'name,lat,lon;name,lat,lon' into a list of City."""
    cities = []
    for entry in raw.split(";"):
        name, lat, lon = entry.strip().split(",")
        cities.append(City(name=name.strip(), lat=float(lat), lon=float(lon)))
    return cities


def get_weather(lat: float, lon: float) -> str:
    """Return weather string like '晴 5°C （最高12°C 最低-1°C）'."""
    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "auto",
            "forecast_days": 1,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    code = data["current"]["weather_code"]
    cur_temp = round(data["current"]["temperature_2m"])
    humidity = round(data["current"]["relative_humidity_2m"])
    high = round(data["daily"]["temperature_2m_max"][0])
    low = round(data["daily"]["temperature_2m_min"][0])
    desc = WMO_ZH.get(code, f"未知({code})")

    return f"{desc} {cur_temp}°C 湿度{humidity}%（最高{high}°C 最低{low}°C）"


def _aqi_label(aqi: int) -> str:
    for (lo, hi), label in AQI_LEVEL_ZH.items():
        if lo <= aqi <= hi:
            return label
    return "未知"


def get_aqi(lat: float, lon: float) -> str:
    """Return AQI string like 'AQI 42 （优）'."""
    resp = requests.get(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "us_aqi",
        },
        timeout=10,
    )
    resp.raise_for_status()
    aqi = round(resp.json()["current"]["us_aqi"])
    return f"AQI {aqi} （{_aqi_label(aqi)}）"
