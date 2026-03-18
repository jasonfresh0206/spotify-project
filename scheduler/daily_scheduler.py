"""
排程模組 - 每日定時排程器
使用 APScheduler 設定每日早上 9:00 自動執行完整的輿情監測流程。
"""

import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

import config

logger = logging.getLogger(__name__)


class DailyScheduler:
    """每日定時排程器"""

    def __init__(self, job_func):
        """
        初始化排程器

        Args:
            job_func: 要定時執行的函式（完整流程）
        """
        self.scheduler = BlockingScheduler()
        self.job_func = job_func

    def start(self):
        """啟動排程器，設定每日指定時間執行"""
        trigger = CronTrigger(
            hour=config.SCHEDULE_HOUR,
            minute=config.SCHEDULE_MINUTE,
            timezone=config.SCHEDULE_TIMEZONE,
        )

        self.scheduler.add_job(
            self.job_func,
            trigger=trigger,
            id="daily_spotify_monitor",
            name="Spotify 每日輿情監測",
            replace_existing=True,
        )

        logger.info(
            f"排程已設定：每日 {config.SCHEDULE_HOUR:02d}:{config.SCHEDULE_MINUTE:02d} "
            f"({config.SCHEDULE_TIMEZONE}) 自動執行"
        )
        logger.info("排程器啟動中... 按 Ctrl+C 停止")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("排程器已停止")
            self.scheduler.shutdown()
