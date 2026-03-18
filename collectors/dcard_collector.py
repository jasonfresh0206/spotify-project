"""
搜集模組 - Dcard 搜集器
透過 Dcard 公開 API 搜尋與 Spotify 相關的討論文章。
"""

import logging
import requests
from datetime import datetime, timedelta

from collectors.base_collector import BaseCollector
import config

logger = logging.getLogger(__name__)


class DcardCollector(BaseCollector):
    """從 Dcard 搜集 Spotify 相關討論"""

    # Dcard 公開搜尋 API
    SEARCH_URL = "https://www.dcard.tw/service/api/v2/search/posts"
    POST_URL = "https://www.dcard.tw/f/{}/p/{}"

    def __init__(self):
        super().__init__(name="Dcard")

    def _fetch_data(self) -> list[dict]:
        """
        從 Dcard 公開 API 搜尋包含 Spotify 關鍵字的文章

        Returns:
            list[dict]: Dcard 文章列表
        """
        all_articles = []

        for keyword in config.SEARCH_KEYWORDS:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                params = {
                    "query": keyword,
                    "limit": config.MAX_ARTICLES_PER_SOURCE,
                }

                response = requests.get(
                    self.SEARCH_URL,
                    headers=headers,
                    params=params,
                    timeout=15
                )
                response.raise_for_status()
                posts = response.json()

                # 過濾出最近 24 小時內的文章
                cutoff_time = datetime.now() - timedelta(hours=24)

                for post in posts:
                    try:
                        # 解析發佈時間
                        created_at = post.get("createdAt", "")
                        if created_at:
                            # Dcard 時間格式：2024-01-01T12:00:00.000Z
                            post_time = datetime.fromisoformat(
                                created_at.replace("Z", "+00:00")
                            )
                            # 轉換為 naive datetime 進行比較
                            post_time_naive = post_time.replace(tzinfo=None)
                            if post_time_naive < cutoff_time:
                                continue

                        forum_name = post.get("forumName", "")
                        post_id = post.get("id", "")

                        article = {
                            "title": post.get("title", "無標題"),
                            "content": post.get("excerpt", "")[:500],
                            "source": f"Dcard - {forum_name}",
                            "url": self.POST_URL.format(forum_name, post_id) if forum_name and post_id else "",
                            "published_at": created_at,
                            "likes": post.get("likeCount", 0),
                            "comments": post.get("commentCount", 0),
                        }
                        all_articles.append(article)
                    except Exception as e:
                        logger.warning(f"[Dcard] 解析單篇文章時發生錯誤：{e}")
                        continue

                logger.info(f"[Dcard] 關鍵字 '{keyword}' 搜集到 {len(posts)} 篇文章")

            except requests.exceptions.RequestException as e:
                logger.error(f"[Dcard] 搜尋關鍵字 '{keyword}' 時發生請求錯誤：{e}")
                continue

        # 去除重複文章（依照標題）
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            if article["title"] not in seen_titles:
                seen_titles.add(article["title"])
                unique_articles.append(article)

        return unique_articles
