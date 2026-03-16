import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from densho_bato import Service
from densho_bato.dispatchers import WeChatDispatcher
from densho_bato.dispatchers.base import Dispatcher
from densho_bato.schedulers import Cron
from dotenv import load_dotenv

from ybot.weather import hangzhou_weather, wlafayette_weather

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

BEIJING = ZoneInfo("Asia/Shanghai")


class DynamicDispatcher(Dispatcher):
    """Wraps WeChatDispatcher, injecting dynamic timestamps and weather."""

    def __init__(self, inner: WeChatDispatcher) -> None:
        self._inner = inner

    def send(self, payload: dict) -> None:
        now_local = datetime.now()
        now_beijing = datetime.now(BEIJING)
        payload = {
            **payload,
            "data": {
                **payload["data"],
                "wlafayette_time": {"value": now_local.strftime("%Y-%m-%d %H:%M:%S")},
                "beijing_time": {"value": now_beijing.strftime("%Y-%m-%d %H:%M:%S")},
                "wlafayette_weather": {"value": wlafayette_weather()},
                "hangzhou_weather": {"value": hangzhou_weather()},
            },
        }
        self._inner.send(payload)


def main() -> None:
    appid = os.environ["WECHAT_APPID"]
    secret = os.environ["WECHAT_SECRET"]
    user_id = os.environ["WECHAT_USER_ID"]
    template_id = os.environ["WECHAT_TEMPLATE_ID"]

    dispatcher = DynamicDispatcher(WeChatDispatcher(appid=appid, secret=secret))
    scheduler = Cron("0 8 * * *", tz=BEIJING)

    payload = {
        "user_id": user_id,
        "template_id": template_id,
        "data": {"plus_sentence": {"value": "Hi!"}},
    }

    svc = Service()
    svc.add_job(scheduler, dispatcher, payload)

    logging.getLogger(__name__).info("ybot started — sending Hi! daily at 08:00 CST")
    svc.run_sync()


if __name__ == "__main__":
    main()
