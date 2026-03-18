"""
搜集模組 - Google News RSS 搜集器
透過 Google News RSS feed 搜集 Spotify 相關新聞。
"""

import logging
import feedparser
import requests
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

from collectors.base_collector import BaseCollector
import config

logger = logging.getLogger(__name__)


class NewsCollector(BaseCollector):
    """從 Google News RSS 搜集 Spotify 相關新聞"""

    # Google News RSS 搜尋 URL
    RSS_URL = "https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"

    def __init__(self):
        super().__init__(name="GoogleNews")

    def _fetch_data(self) -> list[dict]:
        """
        從 Google News RSS 搜集 Spotify 相關新聞

        Returns:
            list[dict]: 新聞文章列表
        """
        all_articles = []

        for keyword in config.SEARCH_KEYWORDS:
            try:
                rss_url = self.RSS_URL.format(query=keyword)
                logger.info(f"[GoogleNews] 正在抓取 RSS feed：{keyword}")

                # 使用 requests 抓取 RSS 內容（以支援 timeout 和重試）
                response = requests.get(rss_url, timeout=15)
                response.raise_for_status()

                feed = feedparser.parse(response.content)

                if feed.bozo:
                    logger.warning(f"[GoogleNews] RSS 解析警告：{feed.bozo_exception}")

                # 過濾最近 24 小時的新聞
                cutoff_time = datetime.now() - timedelta(hours=24)

                for entry in feed.entries[:config.MAX_ARTICLES_PER_SOURCE]:
                    try:
                        # 解析發佈時間
                        published_at = ""
                        if hasattr(entry, "published"):
                            try:
                                pub_date = parsedate_to_datetime(entry.published)
                                published_at = pub_date.isoformat()
                                # 只保留最近 24 小時的新聞
                                if pub_date.replace(tzinfo=None) < cutoff_time:
                                    continue
                            except Exception:
                                published_at = entry.published

                        # 從標題中提取來源（Google News 格式：標題 - 來源）
                        title = entry.get("title", "無標題")
                        source_name = "Google News"
                        if " - " in title:
                            parts = title.rsplit(" - ", 1)
                            title = parts[0]
                            source_name = parts[1] if len(parts) > 1 else source_name

                        article = {
                            "title": title,
                            "content": entry.get("summary", "")[:500],
                            "source": source_name,
                            "url": entry.get("link", ""),
                            "published_at": published_at,
                        }
                        all_articles.append(article)

                    except Exception as e:
                        logger.warning(f"[GoogleNews] 解析單篇新聞時發生錯誤：{e}")
                        continue

                logger.info(f"[GoogleNews] 關鍵字 '{keyword}' 搜集到 {len(feed.entries)} 篇新聞")

            except requests.exceptions.RequestException as e:
                logger.error(f"[GoogleNews] 抓取 RSS 時發生請求錯誤：{e}")
                continue

        # 去除重複新聞（依照標題）
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            if article["title"] not in seen_titles:
                seen_titles.add(article["title"])
                unique_articles.append(article)

        return unique_articles
