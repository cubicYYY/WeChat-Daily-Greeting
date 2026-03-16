"""Fetch weather from Open-Meteo (free, no API key required)."""

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

# West Lafayette, IN
WLAFAYETTE = (40.4259, -86.9081)
# Hangzhou, China
HANGZHOU = (30.2741, 120.1551)


def get_weather(lat: float, lon: float) -> str:
    """Return weather string like '晴 5℃ 最高12℃ 最低-1℃'."""
    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weather_code",
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
    high = round(data["daily"]["temperature_2m_max"][0])
    low = round(data["daily"]["temperature_2m_min"][0])
    desc = WMO_ZH.get(code, f"未知({code})")

    return f"{desc} {cur_temp}°C （最高{high}°C 最低{low}°C）"


def wlafayette_weather() -> str:
    return get_weather(*WLAFAYETTE)


def hangzhou_weather() -> str:
    return get_weather(*HANGZHOU)
