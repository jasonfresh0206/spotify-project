"""
通知模組 - Telegram Bot 推播
使用 Telegram Bot API 將每日輿情報告推播給指定聊天室。
"""

import logging
import requests

import config

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """使用 Telegram Bot API 發送推播訊息"""

    API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self):
        """初始化 Telegram Bot API"""
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID

        if not self.bot_token:
            logger.warning("未設定 TELEGRAM_BOT_TOKEN，Telegram 推播功能將無法使用")
        if not self.chat_id:
            logger.warning("未設定 TELEGRAM_CHAT_ID，Telegram 推播功能將無法使用")

    def _format_message(self, analysis_result: dict) -> str:
        """
        將分析結果格式化為 Telegram 推播訊息（支援 Markdown）

        Args:
            analysis_result: LLM 分析結果

        Returns:
            str: 格式化後的推播訊息
        """
        sentiment = analysis_result.get("overall_sentiment", {})
        positive = sentiment.get("positive_ratio", 0)
        negative = sentiment.get("negative_ratio", 0)
        neutral = sentiment.get("neutral_ratio", 0)

        events = analysis_result.get("events", [])
        keywords = analysis_result.get("trending_keywords", [])
        summary = analysis_result.get("daily_summary", "無摘要")

        lines = [
            "🎵 *Spotify 每日輿情報告*",
            "━━━━━━━━━━━━━━━━",
            "",
            "📊 *今日情緒分佈：*",
            f"  😊 正面：{positive:.0%}",
            f"  😐 中性：{neutral:.0%}",
            f"  😟 負面：{negative:.0%}",
            "",
        ]

        if events:
            lines.append("🔔 *重大事件：*")
            for event in events[:5]:
                severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    event.get("severity", "low"), "🟢"
                )
                lines.append(f"  {severity_icon} {event.get('title', '未知事件')}")
                if event.get("description"):
                    lines.append(f"     {event['description'][:50]}")
            lines.append("")

        if keywords:
            lines.append(f"🔑 *熱門關鍵字：*{' | '.join(keywords[:6])}")
            lines.append("")

        lines.append("📝 *今日摘要：*")
        lines.append(f"  {summary}")
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━")

        return "\n".join(lines)

    def send(self, analysis_result: dict) -> bool:
        """
        發送分析結果到 Telegram

        Args:
            analysis_result: LLM 分析結果

        Returns:
            bool: 發送是否成功
        """
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram Bot 設定不完整，無法發送推播")
            return False

        try:
            message_text = self._format_message(analysis_result)
            url = self.API_URL.format(token=self.bot_token)

            payload = {
                "chat_id": self.chat_id,
                "text": message_text,
                "parse_mode": "Markdown",
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info("Telegram 推播發送成功！")
                return True
            else:
                logger.error(
                    f"Telegram 推播發送失敗，狀態碼：{response.status_code}，"
                    f"回應：{response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Telegram 推播發送過程發生錯誤：{e}")
            return False

    def send_test(self) -> bool:
        """發送測試訊息，確認 Telegram Bot 設定是否正確"""
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram Bot 設定不完整，無法發送測試訊息")
            return False

        try:
            url = self.API_URL.format(token=self.bot_token)

            payload = {
                "chat_id": self.chat_id,
                "text": "✅ Spotify 輿情監測系統 \\- Telegram 測試訊息\n\n恭喜！Telegram 推播設定成功！\n系統將於每日早上 9:00 自動發送輿情報告。",
                "parse_mode": "Markdown",
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info("Telegram 測試訊息發送成功！")
                return True
            else:
                logger.error(f"Telegram 測試訊息發送失敗：{response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Telegram 測試訊息發送錯誤：{e}")
            return False
