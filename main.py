"""
Spotify 輿情監測與 LINE/Telegram 每日推播系統 - 主程式進入點

使用方式：
    python main.py                  → 啟動每日排程（於 09:00 自動執行）
    python main.py --run-now        → 立即執行一次完整流程（測試用）
    python main.py --test-line      → 發送 LINE 測試訊息
    python main.py --test-telegram  → 發送 Telegram 測試訊息
"""

import sys
import os
import logging
from datetime import datetime

# 確保專案根目錄在 Python 搜尋路徑中
sys.path.insert(0, os.path.dirname(__file__))

import config
from collectors.dcard_collector import DcardCollector
from collectors.news_collector import NewsCollector
from collectors.tavily_collector import TavilyCollector
from collectors.duckduckgo_collector import DuckDuckGoCollector
from collectors.apify_collector import ApifyCollector
from analyzers.sentiment_analyzer import SentimentAnalyzer
from reporters.report_generator import ReportGenerator
from reporters.image_generator import ImageGenerator
from notifiers.line_notifier import LineNotifier
from notifiers.telegram_notifier import TelegramNotifier
from scheduler.daily_scheduler import DailyScheduler


def setup_logging():
    """設定日誌系統"""
    # 確保日誌目錄存在
    os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)

    # 設定格式
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # 設定處理器
    handlers = [
        logging.StreamHandler(sys.stdout),  # 輸出到終端機
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),  # 輸出到檔案
    ]

    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
    )


def run_pipeline():
    """
    執行完整的輿情監測流程：
    搜集 → 分析 → 生成報告 → LINE 推播
    """
    logger = logging.getLogger("pipeline")
    logger.info("=" * 60)
    logger.info("開始執行 Spotify 輿情監測流程")
    logger.info(f"執行時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # ====== 步驟一：搜集資料 ======
    logger.info("【步驟 1/4】搜集資料...")
    all_articles = []

    # Dcard 搜集
    dcard = DcardCollector()
    dcard_articles = dcard.collect()
    all_articles.extend(dcard_articles)

    # Google News 搜集
    news = NewsCollector()
    news_articles = news.collect()
    all_articles.extend(news_articles)

    # DuckDuckGo 搜集 (免費新聞源)
    ddg = DuckDuckGoCollector()
    ddg_articles = ddg.collect()
    all_articles.extend(ddg_articles)

    # Tavily 搜集
    if config.TAVILY_API_KEY:
        tavily = TavilyCollector()
        tavily_articles = tavily.collect()
        all_articles.extend(tavily_articles)
    else:
        logger.info("未設定 TAVILY_API_KEY，略過 Tavily 搜尋")

    # Apify 搜集
    if config.APIFY_API_TOKEN:
        apify_coll = ApifyCollector()
        apify_articles = apify_coll.collect()
        all_articles.extend(apify_articles)
    else:
        logger.info("未設定 APIFY_API_TOKEN，略過 Apify 搜尋")

    logger.info(f"總共搜集到 {len(all_articles)} 篇文章")

    if not all_articles:
        logger.warning("未搜集到任何文章，流程結束")
        return

    # ====== 步驟二：LLM 分析 ======
    logger.info("【步驟 2/4】進行 LLM 情緒分析...")
    analyzer = SentimentAnalyzer()
    analysis_result = analyzer.analyze(all_articles)

    # ====== 步驟三：生成報告 ======
    logger.info("【步驟 3/4】生成 HTML 報告與懶人包圖檔...")
    reporter = ReportGenerator()
    report_path = reporter.generate(analysis_result)
    
    img_gen = ImageGenerator()
    img_path = img_gen.generate(analysis_result)
    
    if report_path:
        logger.info(f"報告已生成：{report_path}")
        
        # ====== 先設定 GitHub Pages 連結 ======
        filename = os.path.basename(report_path)
        report_url = f"https://jasonfresh0206.github.io/spotify-project/data/reports/{filename}"
        analysis_result["report_url"] = report_url
        
        if img_path:
            img_filename = os.path.basename(img_path)
            img_url = f"https://jasonfresh0206.github.io/spotify-project/data/reports/{img_filename}"
            analysis_result["image_url"] = img_url

    # ====== 儲存最新 JSON 供 Webhook 對話機器人讀取（必須在 git push 之前）======
    import json
    latest_file = os.path.join(os.path.dirname(__file__), "data", "reports", "latest_analysis.json")
    try:
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        logger.info("已儲存最新分析報告 (latest_analysis.json) 供 Webhook 機器人使用")
    except Exception as e:
        logger.warning(f"儲存 JSON 失敗: {e}")

    # ====== 同步上傳至 GitHub（報告 + 圖片 + JSON 一起推送）======
    if report_path:
        import subprocess
        import time
        logger.info("正在上傳報告至 GitHub 以支援線上網頁與圖檔檢視...")
        try:
            subprocess.run(["git", "add", "data/reports/"], check=False)
            subprocess.run(["git", "commit", "-m", f"Auto deploy report {datetime.now().strftime('%Y-%m-%d')}"], check=False)
            subprocess.run(["git", "push"], check=False)
            logger.info("✅ 報告圖文已推送到 GitHub")
            
            # 等待 GitHub Pages 部署完成，確保 LINE 推播時圖片已可存取
            logger.info("等待 60 秒讓 GitHub Pages 部署圖片...")
            time.sleep(60)
        except Exception as e:
            logger.warning(f"上傳至 GitHub 失敗：{e}")

    # ====== 步驟四：推播通知 ======
    logger.info("【步驟 4/4】發送推播通知...")

    # LINE 推播
    line_success = False
    if config.LINE_CHANNEL_ACCESS_TOKEN and config.LINE_USER_ID:
        line_notifier = LineNotifier()
        line_success = line_notifier.send(analysis_result)
        if line_success:
            logger.info("✅ LINE 推播已發送")
        else:
            logger.warning("⚠️ LINE 推播發送失敗")
    else:
        logger.info("未設定 LINE API，略過 LINE 推播")

    # Telegram 推播
    tg_success = False
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        tg_notifier = TelegramNotifier()
        tg_success = tg_notifier.send(analysis_result)
        if tg_success:
            logger.info("✅ Telegram 推播已發送")
        else:
            logger.warning("⚠️ Telegram 推播發送失敗")
    else:
        logger.info("未設定 Telegram Bot，略過 Telegram 推播")

    if line_success or tg_success:
        logger.info("✅ 完整流程執行完成！推播已發送。")
    else:
        logger.warning("⚠️ 流程執行完成，但所有推播管道均未成功。請檢查 .env 設定。")

    logger.info("=" * 60)


def main():
    """主程式進入點"""
    setup_logging()
    logger = logging.getLogger("main")

    # 檢查命令列參數
    if "--test-line" in sys.argv:
        # 測試 LINE 推播
        logger.info("正在發送 LINE 測試訊息...")
        notifier = LineNotifier()
        success = notifier.send_test()
        if success:
            print("✅ LINE 測試訊息已成功發送！請查看您的 LINE。")
        else:
            print("❌ LINE 測試訊息發送失敗。請檢查 .env 中的 LINE 設定。")
        return

    if "--test-telegram" in sys.argv:
        # 測試 Telegram 推播
        logger.info("正在發送 Telegram 測試訊息...")
        tg = TelegramNotifier()
        success = tg.send_test()
        if success:
            print("✅ Telegram 測試訊息已成功發送！請查看您的 Telegram。")
        else:
            print("❌ Telegram 測試訊息發送失敗。請檢查 .env 中的 Telegram 設定。")
        return

    if "--run-now" in sys.argv:
        # 立即執行一次完整流程
        logger.info("手動觸發模式：立即執行一次完整流程")
        run_pipeline()
        return

    # 預設：啟動每日排程
    logger.info("🎵 Spotify 輿情監測系統啟動")
    logger.info(
        f"排程設定：每日 {config.SCHEDULE_HOUR:02d}:{config.SCHEDULE_MINUTE:02d} "
        f"({config.SCHEDULE_TIMEZONE}) 自動執行"
    )

    scheduler = DailyScheduler(job_func=run_pipeline)
    scheduler.start()


if __name__ == "__main__":
    main()
