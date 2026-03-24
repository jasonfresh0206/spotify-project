from jinja2 import Environment, FileSystemLoader
import os

env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('report.html')

mock_data = {
    "report_date": "2026-03-23 每日輿情報告",
    "sentiment": {
        "positive_ratio": 0.50,
        "neutral_ratio": 0.30,
        "negative_ratio": 0.20
    },
    "events": [
        {"title": "AI-brain", "severity": "high", "description": "Spotify正研發AI技術，包括與ChatGPT的深度整合，預計推出進階語音點歌與自動混音功能。"},
        {"title": "Gift-box", "severity": "medium", "description": "為Premium訂閱用戶推出更具個人化的地區專屬音樂推薦。"},
        {"title": "BTS", "severity": "medium", "description": "防彈少年團的新專輯在Spotify上創下首日1.12億串流播放量的新紀錄。"}
    ],
    "keywords": ["ChatGPT", "AI", "高保真音質", "競爭", "Arirang", "Premium功能", "訂閱用戶", "藝人版稅", "空間音訊", "獨立音樂推薦"],
    "daily_summary": "今日 Spotify Premium 在社群上的討論度極高，主要聚焦於即將推出的 AI 輔助功能以及多項獨家內容。雖然高保真音質 (HiFi) 延遲推出的議題引發部分資深發燒友不滿（佔負面輿情大宗），但整體使用者對於 AI 新功能的期待感壓倒性地帶來了正面評價。",
    "article_analyses": [
        {"title": "Spotify 準備推出基於 ChatGPT 的全新 DJ 功能", "sentiment": "positive", "key_points": ["預計下個月於北美地區上線", "引發大量 Z 世代用戶討論"]},
        {"title": "音樂人抗議 Spotify 新版版稅分潤機制", "sentiment": "negative", "key_points": ["獨立音樂人收益恐受損", "工會揚言發起抵制"]}
    ]
}

html_content = template.render(**mock_data)

with open('preview_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("預覽網頁已生成！請在資料夾中雙擊打開 preview_dashboard.html")
