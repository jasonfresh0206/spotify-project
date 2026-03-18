---
trigger: always_on
---

# Spotify 自動化輿情與資訊追蹤系統 - Workspace Rules

## 📌 專案背景與目標 (Project Context)
- **專案名稱**：Spotify 輿情與活動自動化追蹤系統
- **核心目標**：每日自動搜集 Spotify 相關的網路討論與新聞，透過 LLM 分析正負向情緒與重大事件，並彙整成網頁報告及 Line/Telegram 推播通知。

## 🏗️ 架構與工作流程 (Architecture & Workflow)
本專案嚴格遵循以下「5 大核心模組」，請在撰寫程式碼時保持高內聚、低耦合（模組化設計）：

1. **搜集 (Collection)**
   - **職責**：從社群平台（Twitter/Reddit/PTT/Dcard）、網路新聞、App 商店評論搜集資訊。
   - **規範**：所有爬蟲或 API 呼叫必須包含錯誤處理（Error Handling）與重試機制（Retry），避免因網路問題中斷。

2. **分析 (Analysis)**
   - **職責**：將原始文本交由 LLM 解析。
   - **規範**：
     - Prompt（提示詞）必須集中化管理（例如獨立的 `prompts.py` 或 `.json` 設定檔）。
     - 輸出結果必須強制結構化（如 JSON 格式），以便後續模組讀取。包含：`"sentiment"` (正/負評) 與 `"events"` (重大事件)。

3. **報告 (Report)**
   - **職責**：展示 LLM 的分析結果給最終使用者（Web 儀表板）。
   - **規範**：前後端分離，確保資料可透過 API（如 RESTful 或 GraphQL）供應給網頁前端繪製圖表及趨勢。

4. **通知 (Notification)**
   - **職責**：將緊急告警或每日總結推播至 Line 或 Telegram。
   - **規範**：定義清晰的訊息模板（Message Templates），避免推播過度冗長的未排版文字。

5. **排程 (Scheduler)**
   - **職責**：定時執行上述流程。
   - **規範**：建議使用 Cron Job、APScheduler 或 Celery 等排程套件。此模組作為系統的 Entry Point（進入點）調用其他 4 個模組。

## 💻 程式碼撰寫規範 (Coding Guidelines)
- **語言及註解**：請使用 [選擇你的主要程式語言，如 Python / Node.js] 進行開發，並一律使用繁體中文撰寫關鍵註解。
- **環境變數 (Env Vars)**：所有敏感資訊（包含 LLM API Key、Line/Telegram Token、資料庫密碼）**絕對不可**hardcode 在程式碼中，必須統一寫在 `.env` 檔案內。
- **日誌 (Logging)**：系統自動化運行，因此必須導入妥善的 Logging 機制（至少包含 INFO 與 ERROR 等級），以便後續排錯。

## 🤖 給 AI 助手（如 Cursor/Windsurf/Copilot）的指令
- 當被要求「新增功能」時，請先釐清該功能屬於上述 5 大模組中的哪一個，並放在對應的檔案目錄下。
- 若更動到 LLM 的分析邏輯，請務必確認 Prompt 輸出的資料格式依然符合後續「報表」與「通知」模組的要求。
