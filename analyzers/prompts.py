"""
分析模組 - LLM 提示詞管理
集中管理所有送給 Google Gemini 的提示詞（Prompt）。
輸出格式強制為 JSON，以利後續模組讀取。
"""

# 情緒分析與事件擷取的主要提示詞
SENTIMENT_AND_EVENTS_PROMPT = """你是一位專業的社群輿情分析師，專門分析 Spotify（音樂串流平台）的公眾討論與新聞。

請根據以下搜集到的文章資料，進行全面性分析，並以 **嚴格 JSON 格式** 回傳結果。

## 分析要求
1. **整體情緒分佈**：統計所有文章中正面、負面、中性的比例
2. **重大事件擷取**：找出值得關注的事件（如：App 當機、新功能上線、訂閱漲價、歌手音樂上下架等）
3. **熱門話題關鍵字**：找出討論中最常出現的關鍵字或主題
4. **每日摘要**：用 2-3 句話總結今天的 Spotify 輿情

## 輸入資料
{articles_json}

## 輸出格式（請嚴格遵守此 JSON 格式）
{{
    "overall_sentiment": {{
        "positive_ratio": 0.4,
        "negative_ratio": 0.3,
        "neutral_ratio": 0.3
    }},
    "events": [
        {{
            "title": "事件標題",
            "description": "事件描述",
            "severity": "high/medium/low",
            "sentiment": "positive/negative/neutral"
        }}
    ],
    "trending_keywords": ["關鍵字1", "關鍵字2", "關鍵字3"],
    "daily_summary": "今日 Spotify 輿情摘要...",
    "article_analyses": [
        {{
            "title": "文章標題",
            "sentiment": "positive/negative/neutral",
            "key_points": ["重點1", "重點2"]
        }}
    ]
}}

注意事項：
- 請只回傳 JSON，不要包含任何其他文字或 markdown 標記
- 比例數值請保留一位小數，且正面+負面+中性 = 1.0
- 若資料不足以判斷，severity 預設為 "low"
- 請使用繁體中文回覆所有文字內容
"""

# 當沒有搜集到任何資料時使用的提示詞
NO_DATA_RESPONSE = {
    "overall_sentiment": {
        "positive_ratio": 0.0,
        "negative_ratio": 0.0,
        "neutral_ratio": 0.0
    },
    "events": [],
    "trending_keywords": [],
    "daily_summary": "今日未搜集到任何 Spotify 相關討論或新聞。",
    "article_analyses": []
}
