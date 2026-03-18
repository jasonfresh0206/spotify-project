"""
搜集模組 - DuckDuckGo 搜集器
透過 DuckDuckGo 免費搜尋引擎搜集 Spotify 相關的最新新聞。
這個模組完全不需要 API Key。
"""

import logging
from duckduckgo_search import DDGS
from datetime import datetime

from collectors.base_collector import BaseCollector
import config

logger = logging.getLogger(__name__)


class DuckDuckGoCollector(BaseCollector):
    """從 DuckDuckGo 搜集 Spotify 新聞 (免 API Key)"""

    def __init__(self):
        super().__init__(name="DuckDuckGo")

    def _fetch_data(self) -> list[dict]:
        """
        透過 duckduckgo_search 套件搜尋包含 Spotify 的最新新聞

        Returns:
            list[dict]: 搜尋結果列表
        """
        all_articles = []

        try:
            with DDGS() as ddgs:
                for keyword in config.SEARCH_KEYWORDS:
                    try:
                        logger.info(f"[DuckDuckGo] 正在搜尋新聞關鍵字：{keyword}")
                        
                        # 呼叫 DDGS 搜尋新聞
                        results = list(ddgs.news(
                            keywords=keyword,
                            max_results=config.MAX_ARTICLES_PER_SOURCE
                        ))

                        for item in results:
                            try:
                                title = item.get("title", "無標題")
                                content = item.get("body", "")
                                url = item.get("url", "")
                                published_date = item.get("date", "")
                                source_name = item.get("source", "DuckDuckGo")

                                if not published_date:
                                    published_date = datetime.now().isoformat()

                                article = {
                                    "title": title,
                                    "content": content[:500],
                                    "source": f"DDG News - {source_name}",
                                    "url": url,
                                    "published_at": published_date,
                                }
                                all_articles.append(article)
                            except Exception as e:
                                logger.warning(f"[DuckDuckGo] 解析單篇新聞時發生錯誤：{e}")
                                continue

                        logger.info(f"[DuckDuckGo] 關鍵字 '{keyword}' 搜集到 {len(results)} 篇新聞")

                    except Exception as e:
                        logger.error(f"[DuckDuckGo] 搜尋關鍵字 '{keyword}' 時發生錯誤：{e}")
                        continue

        except Exception as e:
            logger.error(f"[DuckDuckGo] 初始化搜尋引擎失敗：{e}")

        # 去除重複文章（依照 URL）
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article["url"] not in seen_urls and article["url"]:
                seen_urls.add(article["url"])
                unique_articles.append(article)

        return unique_articles
