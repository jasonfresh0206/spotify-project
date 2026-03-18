"""
分析模組 - 情緒分析器
使用 Google Gemini API 對搜集到的文章進行情緒分析與事件擷取。
"""

import json
import logging

import google.generativeai as genai

import config
from analyzers.prompts import SENTIMENT_AND_EVENTS_PROMPT, NO_DATA_RESPONSE

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """使用 Google Gemini 進行 Spotify 輿情分析"""

    def __init__(self):
        """初始化 Gemini API"""
        if not config.GEMINI_API_KEY:
            logger.warning("未設定 GEMINI_API_KEY，分析功能將無法使用")
            self.model = None
            return

        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        logger.info("Gemini API 初始化完成")

    def analyze(self, articles: list[dict]) -> dict:
        """
        分析搜集到的文章

        Args:
            articles: 搜集到的文章列表

        Returns:
            dict: 分析結果，包含情緒分佈、事件、關鍵字等
        """
        if not articles:
            logger.warning("沒有文章可供分析，回傳空結果")
            return NO_DATA_RESPONSE

        if not self.model:
            logger.error("Gemini API 未初始化，無法進行分析")
            return NO_DATA_RESPONSE

        try:
            # 準備文章資料（只傳送標題與內容摘要，節省 Token）
            articles_for_analysis = []
            for article in articles:
                articles_for_analysis.append({
                    "title": article.get("title", ""),
                    "content": article.get("content", "")[:300],
                    "source": article.get("source", ""),
                })

            articles_json = json.dumps(articles_for_analysis, ensure_ascii=False, indent=2)

            # 組合提示詞
            prompt = SENTIMENT_AND_EVENTS_PROMPT.format(articles_json=articles_json)

            logger.info(f"正在將 {len(articles)} 篇文章送交 Gemini 分析...")

            # 呼叫 Gemini API
            response = self.model.generate_content(prompt)

            # 解析回傳的 JSON
            response_text = response.text.strip()

            # 移除可能的 markdown 程式碼區塊標記
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            result = json.loads(response_text)
            logger.info("Gemini 分析完成")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Gemini 回傳的 JSON 格式解析失敗：{e}")
            logger.error(f"原始回傳內容：{response_text[:500]}")
            return NO_DATA_RESPONSE
        except Exception as e:
            logger.error(f"Gemini 分析過程發生錯誤：{e}")
            return NO_DATA_RESPONSE
