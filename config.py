
"""
全域設定模組
從 .env 檔案讀取所有環境變數，並集中管理系統設定。
"""

import os
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()


# ====== Google Gemini 設定 ======
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ====== Tavily API 設定 ======
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# ====== Apify API 設定 ======
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")
APIFY_ACTOR_ID = os.getenv("APIFY_ACTOR_ID", "apify/google-search-scraper")

# ====== LINE Messaging API 設定 ======
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")

# ====== Telegram Bot 設定 ======
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ====== 搜集設定 ======
# 搜尋關鍵字
SEARCH_KEYWORDS = ["Spotify", "spotify"]
# 每個資料來源最多抓取的文章數量
MAX_ARTICLES_PER_SOURCE = 30

# ====== 排程設定 ======
# 每日執行時間（24 小時制）
SCHEDULE_HOUR = 9
SCHEDULE_MINUTE = 0
SCHEDULE_TIMEZONE = "Asia/Taipei"

# ====== 報告設定 ======
REPORT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data", "reports")

# ====== 日誌設定 ======
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.path.join(os.path.dirname(__file__), "data", "app.log")
