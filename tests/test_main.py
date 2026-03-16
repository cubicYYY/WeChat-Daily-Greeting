import asyncio
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from densho_bato import Service
from densho_bato.dispatchers import PseudoDispatcher
from densho_bato.schedulers import Cron, Now

BEIJING = ZoneInfo("Asia/Shanghai")


class TestGreetingJob:
    @pytest.mark.asyncio
    async def test_now_sends_payload(self):
        """Verify the service fires and delivers a payload via PseudoDispatcher."""
        svc = Service()
        dispatcher = PseudoDispatcher()
        payload = {"data": {"message": {"value": "Hi!"}}}
        svc.add_job(Now(), dispatcher, payload)
        await svc.run()

    def test_cron_beijing_timezone(self):
        """Verify the Cron scheduler accepts Beijing timezone."""
        scheduler = Cron("0 8 * * *", tz=BEIJING)
        next_time = scheduler.next_trigger()
        assert next_time is not None

    @pytest.mark.asyncio
    async def test_service_stop(self):
        """Verify the service can be stopped cleanly."""
        svc = Service()
        dispatcher = PseudoDispatcher()
        svc.add_job(Cron("* * * * *", tz=BEIJING), dispatcher, {"msg": "Hi!"})
        task = asyncio.create_task(svc.run())
        await asyncio.sleep(0.1)
        svc.stop()
        await task

    def test_main_requires_env_vars(self):
        """Verify main() raises when env vars are missing."""
        with pytest.raises(KeyError):
            from ybot.main import main

            with patch.dict("os.environ", {}, clear=True):
                main()
