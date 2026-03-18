"""One-off script: immediately send a test template message."""

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from densho_bato.dispatchers import WeChatDispatcher
from dotenv import load_dotenv

from ybot.weather import get_aqi, get_weather, parse_cities

load_dotenv()

local_tz = ZoneInfo(os.environ.get("LOCAL_TIMEZONE") or "America/Indiana/Indianapolis")
remote_tz = ZoneInfo(os.environ.get("REMOTE_TIMEZONE") or "Asia/Shanghai")
cities = parse_cities(
    os.environ.get("CITIES") or "西拉法叶,40.4259,-86.9081;杭州,30.2741,120.1551"
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

print("=== DEBUG: Payload ===")
print(json.dumps(payload, ensure_ascii=False, indent=2))

# Call wechatpy directly to capture the response
result = dispatcher._client.message.send_template(
    user_id=payload["user_id"],
    template_id=payload["template_id"],
    data=payload["data"],
)
print("=== DEBUG: WeChat API Response ===")
print(result)
print("Sent successfully!")
