"""
通知模組 - LINE Messaging API 推播
使用 LINE Messaging API 將每日輿情報告推播給指定使用者。
"""

import logging
import requests

import config

logger = logging.getLogger(__name__)


class LineNotifier:
    """使用 LINE Messaging API 發送推播訊息"""

    PUSH_API_URL = "https://api.line.me/v2/bot/message/push"

    def __init__(self):
        """初始化 LINE Messaging API"""
        self.channel_access_token = config.LINE_CHANNEL_ACCESS_TOKEN
        self.user_id = config.LINE_USER_ID

        if not self.channel_access_token:
            logger.warning("未設定 LINE_CHANNEL_ACCESS_TOKEN，推播功能將無法使用")
        if not self.user_id:
            logger.warning("未設定 LINE_USER_ID，推播功能將無法使用")

    def _format_message(self, analysis_result: dict) -> str:
        """
        將分析結果格式化為 LINE 推播訊息

        Args:
            analysis_result: LLM 分析結果

        Returns:
            str: 格式化後的推播訊息文字
        """
        sentiment = analysis_result.get("overall_sentiment", {})
        positive = sentiment.get("positive_ratio", 0)
        negative = sentiment.get("negative_ratio", 0)
        neutral = sentiment.get("neutral_ratio", 0)

        events = analysis_result.get("events", [])
        keywords = analysis_result.get("trending_keywords", [])
        summary = analysis_result.get("daily_summary", "無摘要")

        # 組合訊息
        lines = [
            "🎵 Spotify 每日輿情報告",
            "━━━━━━━━━━━━━━━━",
            "",
            "📊 今日情緒分佈：",
            f"  😊 正面：{positive:.0%}",
            f"  😐 中性：{neutral:.0%}",
            f"  😟 負面：{negative:.0%}",
            "",
        ]

        # 加入重大事件
        if events:
            lines.append("🔔 重大事件：")
            for event in events[:5]:  # 最多顯示 5 個事件
                severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    event.get("severity", "low"), "🟢"
                )
                lines.append(f"  {severity_icon} {event.get('title', '未知事件')}")
                if event.get("description"):
                    lines.append(f"     {event['description'][:50]}")
            lines.append("")

        # 加入熱門關鍵字
        if keywords:
            lines.append(f"🔑 熱門關鍵字：{' | '.join(keywords[:6])}")
            lines.append("")

        # 加入每日摘要
        lines.append("📝 今日摘要：")
        lines.append(f"  {summary}")
        lines.append("")
        
        report_url = analysis_result.get("report_url")
        if report_url:
            lines.append("🌐 檢視完整動態網頁報告：")
            lines.append(f"  {report_url}")
            lines.append("")
            
        lines.append("━━━━━━━━━━━━━━━━")

        return "\n".join(lines)

    def send(self, analysis_result: dict) -> bool:
        """
        發送分析結果到 LINE (使用大眾廣播模式)

        Args:
            analysis_result: LLM 分析結果

        Returns:
            bool: 發送是否成功
        """
        if not self.channel_access_token:
            logger.error("未設定 LINE_CHANNEL_ACCESS_TOKEN API 金鑰，無法發送廣播")
            return False

        try:
            message_text = self._format_message(analysis_result)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.channel_access_token}",
            }

            # 準備訊息陣列
            messages = [
                {
                    "type": "text",
                    "text": message_text,
                }
            ]

            # 若分析結果中含有懶人包圖片網址，將其作為首則訊息發送
            image_url = analysis_result.get("image_url")
            if image_url:
                messages.insert(0, {
                    "type": "image",
                    "originalContentUrl": image_url,
                    "previewImageUrl": image_url
                })

            # 廣播模式 (Broadcast) 不需要指定接收對象(to)，自動發給所有好友
            payload = {
                "messages": messages,
            }

            response = requests.post(
                "https://api.line.me/v2/bot/message/broadcast",
                headers=headers,
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                logger.info("✅ LINE 好友廣播推播發送成功！")
                return True
            else:
                logger.error(
                    f"LINE 廣播推播發送失敗，狀態碼：{response.status_code}，"
                    f"回應：{response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"LINE 廣播推播發送過程發生錯誤：{e}")
            return False

    def send_test(self) -> bool:
        """發送測試訊息，用來確認 LINE API 設定是否正確"""
        if not self.channel_access_token or not self.user_id:
            logger.error("LINE API 設定不完整，無法發送測試訊息")
            return False

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.channel_access_token}",
            }

            payload = {
                "to": self.user_id,
                "messages": [
                    {
                        "type": "text",
                        "text": "✅ Spotify 輿情監測系統 - 測試訊息\n\n恭喜！LINE 推播設定成功！\n系統將於每日早上 9:00 自動發送輿情報告。",
                    }
                ],
            }

            response = requests.post(
                self.PUSH_API_URL,
                headers=headers,
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                logger.info("LINE 測試訊息發送成功！")
                return True
            else:
                logger.error(f"LINE 測試訊息發送失敗：{response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"LINE 測試訊息發送錯誤：{e}")
            return False
