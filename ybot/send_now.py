"""One-off script: immediately send a test template message."""

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from densho_bato.dispatchers import WeChatDispatcher
from dotenv import load_dotenv

from ybot.weather import get_aqi, get_weather, parse_cities

load_dotenv()

local_tz = ZoneInfo(
    os.environ.get("LOCAL_TIMEZONE", "America/Indiana/Indianapolis")
)
remote_tz = ZoneInfo(
    os.environ.get("REMOTE_TIMEZONE", "Asia/Shanghai")
)
cities = parse_cities(
    os.environ.get(
        "CITIES",
        "西拉法叶,40.4259,-86.9081;杭州,30.2741,120.1551",
    )
)

dispatcher = WeChatDispatcher(
    appid=os.environ["WECHAT_APPID"],
    secret=os.environ["WECHAT_SECRET"],
)

now_local = datetime.now(local_tz)
now_remote = datetime.now(remote_tz)

data: dict = {
    "local_time": {
        "value": now_local.strftime("%Y-%m-%d %H:%M:%S"),
    },
    "remote_time": {
        "value": now_remote.strftime("%Y-%m-%d %H:%M:%S"),
    },
    "plus_sentence": {
        "value": os.environ.get("PLUS_SENTENCE")
        or os.environ.get("DEFAULT_SENTENCE")
        or "Hi!"
    },
}

for i, city in enumerate(cities, 1):
    data[f"city{i}_name"] = {"value": city.name}
    data[f"city{i}_weather"] = {
        "value": get_weather(city.lat, city.lon),
    }
    data[f"city{i}_aqi"] = {
        "value": get_aqi(city.lat, city.lon),
    }

payload = {
    "user_id": os.environ["WECHAT_USER_ID"],
    "template_id": os.environ["WECHAT_TEMPLATE_ID"],
    "data": data,
}

dispatcher.send(payload)
print("Sent successfully!")
