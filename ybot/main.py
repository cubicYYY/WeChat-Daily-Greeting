import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from densho_bato import Service
from densho_bato.dispatchers import WeChatDispatcher
from densho_bato.dispatchers.base import Dispatcher
from densho_bato.schedulers import Cron
from dotenv import load_dotenv

from ybot.weather import get_aqi, get_weather, parse_cities

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

LOCAL_TZ = ZoneInfo(os.environ.get("LOCAL_TIMEZONE") or "America/Indiana/Indianapolis")
REMOTE_TZ = ZoneInfo(os.environ.get("REMOTE_TIMEZONE") or "Asia/Shanghai")
CITIES = parse_cities(
    os.environ.get("CITIES") or "西拉法叶,40.4259,-86.9081;杭州,30.2741,120.1551"
)


def _parse_schedule(raw: str) -> str:
    """Convert 'HH:MM' or cron expression to cron string."""
    raw = raw.strip()
    if ":" in raw and " " not in raw:
        h, m = raw.split(":")
        return f"{int(m)} {int(h)} * * *"
    return raw


SCHEDULE = _parse_schedule(os.environ.get("SEND_TIME") or "08:00")


class DynamicDispatcher(Dispatcher):
    """Wraps WeChatDispatcher, injecting dynamic data."""

    def __init__(self, inner: WeChatDispatcher) -> None:
        self._inner = inner

    def send(self, payload: dict) -> None:
        now_local = datetime.now(LOCAL_TZ)
        now_remote = datetime.now(REMOTE_TZ)
        data = {
            **payload["data"],
            "local_time": {
                "value": now_local.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "remote_time": {
                "value": now_remote.strftime("%Y-%m-%d %H:%M:%S"),
            },
        }
        for i, city in enumerate(CITIES, 1):
            data[f"city{i}_name"] = {"value": city.name}
            data[f"city{i}_weather"] = {
                "value": get_weather(city.lat, city.lon),
            }
            data[f"city{i}_aqi"] = {
                "value": get_aqi(city.lat, city.lon),
            }
        self._inner.send({**payload, "data": data})


def main() -> None:
    appid = os.environ["WECHAT_APPID"]
    secret = os.environ["WECHAT_SECRET"]
    user_id = os.environ["WECHAT_USER_ID"]
    template_id = os.environ["WECHAT_TEMPLATE_ID"]

    dispatcher = DynamicDispatcher(WeChatDispatcher(appid=appid, secret=secret))
    scheduler = Cron(SCHEDULE, tz=REMOTE_TZ)

    payload = {
        "user_id": user_id,
        "template_id": template_id,
        "data": {
            "plus_sentence": {
                "value": os.environ.get("PLUS_SENTENCE")
                or os.environ.get("DEFAULT_SENTENCE")
                or "Hi!"
            }
        },
    }

    svc = Service()
    svc.add_job(scheduler, dispatcher, payload)

    logging.getLogger(__name__).info("ybot started")
    svc.run_sync()


if __name__ == "__main__":
    main()
