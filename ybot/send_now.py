"""One-off script: immediately send a test template message."""

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from densho_bato.dispatchers import WeChatDispatcher
from dotenv import load_dotenv

from ybot.weather import hangzhou_weather, wlafayette_weather

load_dotenv()

now_local = datetime.now()
now_beijing = datetime.now(ZoneInfo("Asia/Shanghai"))

dispatcher = WeChatDispatcher(
    appid=os.environ["WECHAT_APPID"],
    secret=os.environ["WECHAT_SECRET"],
)

payload = {
    "user_id": os.environ["WECHAT_USER_ID"],
    "template_id": os.environ["WECHAT_TEMPLATE_ID"],
    "data": {
        "wlafayette_time": {"value": now_local.strftime("%Y-%m-%d %H:%M:%S")},
        "beijing_time": {"value": now_beijing.strftime("%Y-%m-%d %H:%M:%S")},
        "wlafayette_weather": {"value": wlafayette_weather()},
        "hangzhou_weather": {"value": hangzhou_weather()},
        "plus_sentence": {"value": "Hi!"},
    },
}

dispatcher.send(payload)
print("Sent successfully!")
