"""
搜集模組 - Apify 搜集器
透過 Apify API (apify-client) 啟動 Actor 並搜集資料。
"""

import logging
from apify_client import ApifyClient
from datetime import datetime

from collectors.base_collector import BaseCollector
import config

logger = logging.getLogger(__name__)


class ApifyCollector(BaseCollector):
    """從 Apify Server (Actor) 搜集資料"""

    def __init__(self):
        super().__init__(name="Apify")
        # 只要有設定 Token 就初始化 Apify Client
        self.client = ApifyClient(config.APIFY_API_TOKEN) if config.APIFY_API_TOKEN else None

    def _fetch_data(self) -> list[dict]:
        """
        呼叫 Apify Actor 執行任務並獲取 dataset

        Returns:
            list[dict]: 抓取結果列表
        """
        all_articles = []

        if not self.client:
            logger.warning("[Apify] 未設定 APIFY_API_TOKEN，跳過搜集")
            return []

        actor_id = getattr(config, "APIFY_ACTOR_ID", "apify/google-search-scraper")
        
        for keyword in config.SEARCH_KEYWORDS:
            try:
                logger.info(f"[Apify] 正在利用 Actor ({actor_id}) 搜尋關鍵字：{keyword} ... (這可能需要數十秒)")
                
                # 注意：這裡的 run_input 是針對 "apify/google-search-scraper" 預設設計的
                # 若您後續在 .env 更改為其他 Actor (例如 Instagram 或 Twitter Scraper)
                # 您可能需要一併修改這裡傳遞的 parameters 以符合該 Actor 的規範
                run_input = {
                    "queries": f"{keyword} news",
                    "maxPagesPerQuery": 1,
                    "resultsPerPage": config.MAX_ARTICLES_PER_SOURCE,
                    "languageCode": "zh-TW"
                }

                # 呼叫 Actor 並等待它在 Apify Server 上執行完畢
                run = self.client.actor(actor_id).call(run_input=run_input)

                # 從 Apify Default Dataset 提取執行結果
                dataset_items = self.client.dataset(run["defaultDatasetId"]).iterate_items()
                
                count = 0
                for item in dataset_items:
                    try:
                        title = item.get("title", "無標題")
                        description = item.get("description", "")
                        url = item.get("url", "")
                        
                        article = {
                            "title": title,
                            "content": description[:500],
                            "source": f"Apify ({actor_id})",
                            "url": url,
                            "published_at": datetime.now().isoformat(),
                        }
                        all_articles.append(article)
                        count += 1
                    except Exception as e:
                        logger.warning(f"[Apify] 解析單筆結果時發生錯誤：{e}")
                        continue
                
                logger.info(f"[Apify] 關鍵字 '{keyword}' 從 Server 搜集到 {count} 篇內容")

            except Exception as e:
                logger.error(f"[Apify] 執行 Actor '{actor_id}' 時發生錯誤：{e}")
                continue

        # 去除重複文章（依照 URL）
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article["url"] not in seen_urls and article["url"]:
                seen_urls.add(article["url"])
                unique_articles.append(article)

        return unique_articles
