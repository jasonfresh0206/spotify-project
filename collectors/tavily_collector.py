"""
搜集模組 - Tavily AI 搜集器
透過 Tavily API 搜集 Spotify 相關的最新網路文章、評論及新聞。
"""

import logging
import requests
from datetime import datetime

from collectors.base_collector import BaseCollector
import config

logger = logging.getLogger(__name__)


class TavilyCollector(BaseCollector):
    """從 Tavily Search API 搜集 Spotify 相關資訊"""

    # Tavily API Endpoint
    API_URL = "https://api.tavily.com/search"

    def __init__(self):
        super().__init__(name="Tavily")

    def _fetch_data(self) -> list[dict]:
        """
        透過 Tavily API 搜尋包含 Spotify 的最新資訊

        Returns:
            list[dict]: 搜尋結果列表
        """
        all_articles = []

        if not config.TAVILY_API_KEY:
            logger.warning("[Tavily] 尚未設定 TAVILY_API_KEY，略過搜尋")
            return []

        for keyword in config.SEARCH_KEYWORDS:
            try:
                # 組合 Tavily API Payload，要求抓取新聞類別，以及近幾天的資訊
                payload = {
                    "api_key": config.TAVILY_API_KEY,
                    "query": f"{keyword} 新聞 評論",
                    "search_depth": "advanced", # "basic" or "advanced"
                    "include_answer": False,
                    "include_images": False,
                    "include_raw_content": False,
                    "max_results": config.MAX_ARTICLES_PER_SOURCE,
                    "topic": "news" # 專注於即時新聞與話題
                }

                logger.info(f"[Tavily] 正在搜尋關鍵字：{keyword}")
                response = requests.post(self.API_URL, json=payload, timeout=20)
                
                if response.status_code == 401:
                    logger.error("[Tavily] API 金鑰無效，請確認 .env 設定")
                    continue
                    
                response.raise_for_status()
                data = response.json()
                
                results = data.get("results", [])

                for item in results:
                    try:
                        title = item.get("title", "無標題")
                        content = item.get("content", "")
                        url = item.get("url", "")
                        published_date = item.get("published_date", "")
                        
                        # 如果 API 沒給發布時間，預設給當前時間
                        if not published_date:
                            published_date = datetime.now().isoformat()

                        article = {
                            "title": title,
                            "content": content[:500],
                            "source": "Tavily Search",
                            "url": url,
                            "published_at": published_date,
                        }
                        all_articles.append(article)
                    except Exception as e:
                        logger.warning(f"[Tavily] 解析單篇搜尋結果時發生錯誤：{e}")
                        continue

                logger.info(f"[Tavily] 關鍵字 '{keyword}' 搜集到 {len(results)} 篇內容")

            except requests.exceptions.RequestException as e:
                logger.error(f"[Tavily] 搜尋關鍵字 '{keyword}' 時發生請求錯誤：{e}")
                continue

        # 去除重複文章（依照標題與 URL）
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article["url"] not in seen_urls and article["url"]:
                seen_urls.add(article["url"])
                unique_articles.append(article)

        return unique_articles
