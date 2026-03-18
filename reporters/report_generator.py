"""
報告模組 - HTML 報告生成器
將 LLM 分析結果渲染成精美的 HTML 報告頁面。
"""

import os
import logging
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

import config

logger = logging.getLogger(__name__)


class ReportGenerator:
    """將分析結果生成 HTML 每日報告"""

    def __init__(self):
        """初始化模板引擎"""
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template = self.env.get_template("report.html")

        # 確保報告輸出目錄存在
        os.makedirs(config.REPORT_OUTPUT_DIR, exist_ok=True)
        logger.info(f"報告輸出目錄：{config.REPORT_OUTPUT_DIR}")

    def generate(self, analysis_result: dict) -> str:
        """
        生成 HTML 報告

        Args:
            analysis_result: LLM 分析結果

        Returns:
            str: 生成的報告檔案路徑
        """
        try:
            report_date = datetime.now().strftime("%Y 年 %m 月 %d 日")
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            output_path = os.path.join(config.REPORT_OUTPUT_DIR, filename)

            # 渲染 HTML 模板
            html_content = self.template.render(
                report_date=report_date,
                sentiment=analysis_result.get("overall_sentiment", {}),
                events=analysis_result.get("events", []),
                keywords=analysis_result.get("trending_keywords", []),
                daily_summary=analysis_result.get("daily_summary", "無摘要"),
                article_analyses=analysis_result.get("article_analyses", []),
            )

            # 寫入檔案
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            logger.info(f"HTML 報告已生成：{output_path}")
            return output_path

        except Exception as e:
            logger.error(f"報告生成失敗：{e}")
            return ""
