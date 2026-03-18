"""
搜集模組 - 基底類別
定義所有資料搜集器的共同介面與重試機制。
"""

import time
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """所有資料搜集器的抽象基底類別"""

    def __init__(self, name: str, max_retries: int = 3, retry_delay: float = 2.0):
        """
        初始化搜集器

        Args:
            name: 搜集器名稱（用於日誌識別）
            max_retries: 最大重試次數
            retry_delay: 每次重試之間的等待秒數
        """
        self.name = name
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    @abstractmethod
    def _fetch_data(self) -> list[dict]:
        """
        實際抓取資料的方法（子類別必須實作）

        Returns:
            list[dict]: 抓取到的文章列表，每篇文章包含：
                - title (str): 標題
                - content (str): 內容摘要
                - source (str): 來源名稱
                - url (str): 原始連結
                - published_at (str): 發佈時間
        """
        pass

    def collect(self) -> list[dict]:
        """
        執行資料搜集（含重試機制）

        Returns:
            list[dict]: 搜集到的文章列表
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"[{self.name}] 開始搜集資料（第 {attempt} 次嘗試）")
                data = self._fetch_data()
                logger.info(f"[{self.name}] 成功搜集到 {len(data)} 筆資料")
                return data
            except Exception as e:
                logger.error(f"[{self.name}] 第 {attempt} 次搜集失敗：{e}")
                if attempt < self.max_retries:
                    logger.info(f"[{self.name}] 等待 {self.retry_delay} 秒後重試...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"[{self.name}] 已達最大重試次數，放棄搜集")
                    return []
