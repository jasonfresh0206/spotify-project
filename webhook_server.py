"""
對話式 LINE 機器人 Webhook Server (Feature 1)
使用 Flask 接收 LINE 的訊息，並結合 Gemini 分析當天輿情回覆使用者。
雲端部署版本：使用 line-bot-sdk v3 API。
"""

import os
import logging
from flask import Flask, request, abort

# 設定日誌
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ====== 從環境變數讀取設定 ======
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ====== 初始化 LINE SDK v3 ======
handler = None
configuration = None

try:
    from linebot.v3 import WebhookHandler
    from linebot.v3.exceptions import InvalidSignatureError
    from linebot.v3.messaging import (
        Configuration,
        ApiClient,
        MessagingApi,
        ReplyMessageRequest,
        TextMessage,
    )
    from linebot.v3.webhooks import MessageEvent, TextMessageContent

    if LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET:
        handler = WebhookHandler(LINE_CHANNEL_SECRET)
        configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
        logger.info("LINE SDK v3 初始化完成")
    else:
        logger.warning("未設定 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_CHANNEL_SECRET")
except Exception as e:
    logger.error(f"LINE SDK 初始化失敗: {e}")

# ====== 初始化 Gemini ======
gemini_model = None
try:
    if GEMINI_API_KEY:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-2.5-flash")
        logger.info("Gemini API 初始化完成")
    else:
        logger.warning("未設定 GEMINI_API_KEY")
except Exception as e:
    logger.error(f"Gemini 初始化失敗: {e}")


@app.route("/", methods=['GET'])
def health_check():
    """Render 健康檢查用的根路由"""
    return "Spotify Monitor Bot is alive! 🎵", 200


@app.route("/callback", methods=['POST'])
def callback():
    """LINE 伺服器傳送 Webhook 事件的端點"""
    if handler is None:
        logger.error("LINE SDK 未初始化，無法處理 Webhook")
        return 'LINE SDK not initialized', 500

    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    logger.info("收到 Webhook 請求")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("簽章驗證失敗！")
        abort(400)
    except Exception as e:
        logger.error(f"處理 Webhook 時發生錯誤: {e}")
        abort(400)

    return 'OK'


# ====== 訊息處理邏輯 ======
if handler is not None:
    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_message(event):
        """處理使用者傳送的文字訊息"""
        user_msg = event.message.text
        logger.info(f">>> 收到來自使用者的訊息: {user_msg}")

        # 讀取最新報告 JSON（從 GitHub Pages 抓取）
        report_data_str = "今日尚未產生任何舆情報告資料。"
        import requests
        github_json_url = "https://jasonfresh0206.github.io/spotify-project/data/reports/latest_analysis.json"

        try:
            req = requests.get(github_json_url, timeout=5)
            if req.status_code == 200:
                report_data_str = req.text
                logger.info("成功從 GitHub 讀取最新報告 JSON！")
            else:
                raise Exception(f"HTTP Status: {req.status_code}")
        except Exception as e:
            logger.warning(f"無法從 GitHub 讀取報告 ({e})")

        # 組合 Prompt 請求 Gemini 回答
        prompt = f"""
你是一個名為「Spotify Monitor AI」的專業輿情分析助教。
你的任務是基於以下最新的一份系統摘要報告，回答使用者的問題。
如果使用者問的問題與報告完全無關，請你友善地引導他們詢問關於今日 Spotify 輿情、關鍵字、重大事件等的內容。
如果是單純打招呼，可以禮貌地介紹自己的分析專業。

回答規則：
1. 請用繁體中文，語氣專業卻不失親切助理的感覺，可以適當使用 Emoji。
2. 在回答時請保持簡潔明瞭，文字不要太長，必須非常適合在手機 LINE 上閱讀（建議 150 字內）。
3. 如果使用者詢問特定事件細節，請從 [最新系統報告資料] 中尋找線索，如果沒有線索請老實說報告中沒有提到。

[最新系統報告資料 (JSON 格式)]
{report_data_str}

[使用者的問題]
{user_msg}
"""

        # 向 Gemini 請求回覆
        reply_text = "抱歉，我的 AI 大腦暫時連線異常，請稍候再試！😵"
        if gemini_model:
            try:
                response = gemini_model.generate_content(prompt)
                reply_text = response.text
            except Exception as e:
                logger.error(f"Gemini API 請求失敗: {e}")
        else:
            reply_text = "抱歉，AI 分析模組目前離線中，請稍候再試！"

        logger.info(f"<<< 回覆使用者: {reply_text.replace(chr(10), ' ')}")

        # 使用 v3 API 回覆訊息
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )


if __name__ == "__main__":
    logger.info("=========================================")
    logger.info("啟動對話式 LINE 機器人伺服器...")
    logger.info("=========================================")
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
