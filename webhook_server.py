"""
對話式 LINE 機器人 Webhook Server (Feature 1)
使用 Flask 接收 LINE 的訊息，並結合 Gemini 分析當天輿情回覆使用者。
執行方式： python webhook_server.py
"""

import os
import logging
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import config
from analyzers.sentiment_analyzer import SentimentAnalyzer

# 設定日誌
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 初始化 LINE API
line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)

# 初始化 Gemini 分析器
analyzer = SentimentAnalyzer()


@app.route("/callback", methods=['POST'])
def callback():
    """LINE 伺服器傳送 Webhook 事件的端點"""
    # 取得 X-Line-Signature 標頭值
    signature = request.headers.get('X-Line-Signature', '')
    
    # 取得請求內容
    body = request.get_data(as_text=True)
    logger.info(f"收到 Webhook 請求: {body}")
    
    # 處理 Webhook
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("驗證簽章無效！請檢查 .env 中的 LINE_CHANNEL_SECRET 是否正確設定。")
        abort(400)
        
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理使用者傳送的文字訊息"""
    user_msg = event.message.text
    logger.info(f">>> 收到來自使用者的訊息: {user_msg}")
    
    # 讀取最新報告 JSON
    report_data_str = "今日尚未產生任何舆情報告資料。"
    
    # 嘗試從 GitHub Pages 抓取線上最新的 JSON（雲端部署專用）
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
        logger.warning(f"無法從 GitHub 讀取報告 ({e})，改為嘗試讀取本地檔案。")
        # 降級備用方案：讀取本地
        report_file = os.path.join(os.path.dirname(__file__), "data", "reports", "latest_analysis.json")
        if os.path.exists(report_file):
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_data_str = f.read()
            except Exception as local_e:
                logger.error(f"讀取本地報告發生錯誤: {local_e}")

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
    try:
        response = analyzer.model.generate_content(prompt)
        reply_text = response.text
    except Exception as e:
        logger.error(f"Gemini API 請求失敗: {e}")
        reply_text = "抱歉，我的 AI 大腦暫時連線異常或受到限制，請稍候再試！😵"

    logger.info(f"<<< 回覆使用者: {reply_text.replace(chr(10), ' ')}")

    # 透過 LINE API 把回覆傳給使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    if not config.LINE_CHANNEL_SECRET:
        logger.warning("尚未設定 LINE_CHANNEL_SECRET，將無法驗證 Webhook！請前往 .env 設定。")
    if not config.LINE_CHANNEL_ACCESS_TOKEN:
        logger.warning("尚未設定 LINE_CHANNEL_ACCESS_TOKEN，將無法回覆訊息！請前往 .env 設定。")
        
    logger.info("=========================================")
    logger.info("啟動對話式 LINE 機器人伺服器...")
    logger.info("預設執行於 Port 5000，請使用 ngrok http 5000 對外開啟 Webhook！")
    logger.info("=========================================")
    
    # 在 local 測試通常啟動 5000 埠
    app.run(host='0.0.0.0', port=5000)
