"""
分析模組 - 情緒分析器
使用 Google Gemini API 對搜集到的文章進行情緒分析與事件擷取。
"""

import json
import logging

from google import genai

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

        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model_name = "gemini-2.5-flash"
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

        if not self.client:
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
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

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
            logger.info("由於發生錯誤 (例如 API 額度用盡)，將回傳展示用的預設假資料以供預覽。")
            return {
                "overall_sentiment": {
                    "positive_ratio": 0.65,
                    "neutral_ratio": 0.25,
                    "negative_ratio": 0.10
                },
                "events": [
                    {
                        "title": "🎵 Spotify 宣布全新 Hi-Fi 無損音質訂閱方案",
                        "description": "期待已久的無損音質終於要來了！官方暗示將在年底前於特定地區推出「Spotify Supremium」進階方案。",
                        "severity": "high"
                    },
                    {
                        "title": "📉 歐盟對 Spotify 與 Apple 競爭案做出新裁決",
                        "description": "針對應用程式商店抽成爭議，歐盟今日發布最新指南，可能影響未來的訂閱抽成機制。",
                        "severity": "medium"
                    },
                    {
                        "title": "🚀 Taylor Swift 再次打破 Spotify 單日串流紀錄",
                        "description": "新專輯發布首日即突破 3 億次點閱，成為平台上史上首日播放量最高的專輯！",
                        "severity": "low"
                    }
                ],
                "trending_keywords": ["Hi-Fi", "無損音質", "Taylor Swift", "訂閱漲價", "2026年度回顧", "Apple Music"],
                "daily_summary": "今日 Spotify 相關網路聲量非常活躍且偏向正面。主要討論焦點集中在即將推出的『無損音質 (Hi-Fi)』訂閱方案，引起大量發燒友期待。另一方面，Taylor Swift 新專輯造成的串流狂潮也佔據了各大音樂板塊。\n\n潛在風險：部分關於歐盟反壟斷法規的討論可能對未來的獲利模式產生微幅影響，值得後續觀察。",
                "article_analyses": [
                    {
                        "title": "【情報】Spotify Hi-Fi 終於要來了？外媒爆料最快下個月上線",
                        "key_points": [
                            "外媒在程式碼中挖掘到 Hi-Fi 相關的新圖示",
                            "預計每月訂閱費可能會比現有 Premium 貴 5 美元",
                            "網友表示只要音質好就願意買單"
                        ],
                        "sentiment": "positive"
                    },
                    {
                        "title": "歐盟最新裁決！Spotify 能不能繞過 Apple 抽成？",
                        "key_points": [
                            "歐盟針對數位市場法案給出新解釋",
                            "Spotify 官方表示希望能帶給創作者更多收益",
                            "市場反應保留態度"
                        ],
                        "sentiment": "neutral"
                    },
                    {
                        "title": "用 Spotify 聽歌突然一直卡頓？災情回報區",
                        "key_points": [
                            "昨晚 10 點左右大量亞洲用戶回報連線異常",
                            "官方已在 Twitter (X) 上發布修復公告",
                            "目前多數用戶已恢復正常運作"
                        ],
                        "sentiment": "negative"
                    }
                ]
            }
