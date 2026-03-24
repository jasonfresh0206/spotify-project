"""
報告模組 - 圖文懶人包自動生成 (Feature 5)
使用 Pillow 將分析結果繪製為高質感的 1080x1080 圖文懶人包，直接適合在社群媒體發布或透過 LINE 觀看。
"""

import os
import logging
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

logger = logging.getLogger(__name__)

class ImageGenerator:
    """自動生成輿情報告懶人包圖檔"""

    def __init__(self):
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "reports")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 嘗試載入字體 (為 Windows 與通用環境做回退處理)
        try:
            self.font_title_lg = ImageFont.truetype("msjhbd.ttc", 72)  # 微軟正黑粗體
            self.font_title = ImageFont.truetype("msjhbd.ttc", 56)     
            self.font_heading = ImageFont.truetype("msjhbd.ttc", 40)
            self.font_body = ImageFont.truetype("msjh.ttc", 32)
            self.font_small = ImageFont.truetype("msjh.ttc", 24)
        except Exception:
            try:
                # 備用方案 2：Arial
                self.font_title_lg = ImageFont.truetype("arialbd.ttf", 72)
                self.font_title = ImageFont.truetype("arialbd.ttf", 56)
                self.font_heading = ImageFont.truetype("arialbd.ttf", 40)
                self.font_body = ImageFont.truetype("arial.ttf", 32)
                self.font_small = ImageFont.truetype("arial.ttf", 24)
            except Exception:
                # 最後回退方案
                self.font_title_lg = ImageFont.load_default()
                self.font_title = ImageFont.load_default()
                self.font_heading = ImageFont.load_default()
                self.font_body = ImageFont.load_default()
                self.font_small = ImageFont.load_default()

    def generate(self, analysis_result: dict, date_str: str = None) -> str:
        """
        傳入 JSON 分析結果，繪製成圖片並回傳檔案絕對路徑
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
        width, height = 1080, 1080
        # 基礎顏色：極深綠底 (符合 Pro Max 設計語彙)
        img = Image.new('RGBA', (width, height), color=(7, 10, 9, 255))
        
        # 建立發光特效圖層
        overlay = Image.new('RGBA', (width, height), color=(0,0,0,0))
        draw_ov = ImageDraw.Draw(overlay)
        
        # 在右上角與左下角繪製微光
        draw_ov.ellipse([(-200, -200), (600, 400)], fill=(30, 215, 96, 20))
        draw_ov.ellipse([(600, 600), (1400, 1400)], fill=(88, 166, 255, 10))
        
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)
        
        # 繪製大型標題
        draw.text((80, 80), "Spotify", fill=(30, 215, 96, 255), font=self.font_title_lg)
        draw.text((80, 160), "Premium Pulse", fill=(255, 255, 255, 255), font=self.font_title)
        draw.text((80, 240), f"每日輿情報告整理 | {date_str}", fill=(139, 153, 166, 255), font=self.font_small)

        # 繪製分隔線
        draw.line([(80, 290), (1000, 290)], fill=(255, 255, 255, 30), width=2)

        # 取出情緒資料
        sentiment = analysis_result.get("overall_sentiment", {})
        pos = sentiment.get("positive_ratio", 0) * 100
        neu = sentiment.get("neutral_ratio", 0) * 100
        neg = sentiment.get("negative_ratio", 0) * 100

        # === 區塊 1：情緒分佈條 ===
        draw.text((80, 330), "品牌情緒分佈", fill=(255, 255, 255, 255), font=self.font_heading)
        
        # 正向
        draw.text((80, 410), "正向", fill=(30, 215, 96, 255), font=self.font_body)
        draw.rounded_rectangle([(180, 415), (180 + 700, 445)], radius=15, fill=(255,255,255,20))
        draw.rounded_rectangle([(180, 415), (180 + 700 * (pos/100 if pos > 0 else 0), 445)], radius=15, fill=(30, 215, 96, 255))
        draw.text((910, 410), f"{pos:.0f}%", fill=(255,255,255,255), font=self.font_body)

        # 中性
        draw.text((80, 480), "中性", fill=(88, 166, 255, 255), font=self.font_body)
        draw.rounded_rectangle([(180, 485), (180 + 700, 515)], radius=15, fill=(255,255,255,20))
        draw.rounded_rectangle([(180, 485), (180 + 700 * (neu/100 if neu > 0 else 0), 515)], radius=15, fill=(88, 166, 255, 255))
        draw.text((910, 480), f"{neu:.0f}%", fill=(255,255,255,255), font=self.font_body)

        # 負向
        draw.text((80, 550), "負向", fill=(255, 75, 75, 255), font=self.font_body)
        draw.rounded_rectangle([(180, 555), (180 + 700, 585)], radius=15, fill=(255,255,255,20))
        draw.rounded_rectangle([(180, 555), (180 + 700 * (neg/100 if neg > 0 else 0), 585)], radius=15, fill=(255, 75, 75, 255))
        draw.text((910, 550), f"{neg:.0f}%", fill=(255,255,255,255), font=self.font_body)

        # === 區塊 2：重大事件 ===
        events = analysis_result.get("events", [])
        if events:
            draw.text((80, 650), "本日重大關注事件", fill=(255, 255, 255, 255), font=self.font_heading)
            y_offset = 720
            for ev in events[:3]:  # 最多顯示三筆以免超出畫面
                # 裝飾點
                draw.ellipse([(80, y_offset+12), (95, y_offset+27)], fill=(242, 201, 76, 255))
                
                title = ev.get("title", "")
                if len(title) > 20:
                    title = title[:19] + "..."
                    
                draw.text((120, y_offset), title, fill=(255, 255, 255, 255), font=self.font_body)
                
                # 嚴重程度標籤
                sev = ev.get("severity", "low").upper()
                sev_color = {"HIGH": (255,75,75,255), "MEDIUM": (242,201,76,255), "LOW": (30,215,96,255)}.get(sev, (242,201,76,255))
                
                draw.rounded_rectangle([(750, y_offset), (940, y_offset+38)], radius=18, fill=(255,255,255,20), outline=sev_color, width=2)
                # 微調文字置中
                draw.text((775, y_offset+4), f"{sev} ALERT", fill=sev_color, font=self.font_small)
                
                y_offset += 75
        
        # Footer
        draw.text((80, 980), "Powered by Spotify Monitor AI | UI UX Pro Max", fill=(139, 153, 166, 255), font=self.font_small)

        # 轉換為 RGB 並存檔
        rgb_img = img.convert('RGB')
        filename = f"infographic_{datetime.now().strftime('%Y%m%d')}.jpg"
        filepath = os.path.join(self.output_dir, filename)
        rgb_img.save(filepath, quality=92)
        
        logger.info(f"圖文懶人包已成功產生：{filepath}")
        return filepath
