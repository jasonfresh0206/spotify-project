@echo off
chcp 65001 >nul
echo ===================================================
echo   正在設定 Spotify 每日輿情報告自動排程 (Task Scheduler)
echo ===================================================
echo.

set "TASK_NAME=Spotify_Daily_Monitor"
set "SCRIPT_PATH=c:\Users\User\spotify project\run_pipeline.bat"
set "WORKING_DIR=c:\Users\User\spotify project"

:: 刪除舊的排程 (如果存在)
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

:: 建立新的排程 (每天早上 09:00 執行)
:: 注意：使用 /ru "%USERNAME%" 指定目前使用者權限執行
schtasks /create /tn "%TASK_NAME%" /tr "\"%SCRIPT_PATH%\"" /sc daily /st 09:00 /f

echo.
if %errorlevel% equ 0 (
    echo [成功] 排程設定完成！
    echo 系統將會在每天早上 09:00 自動啟動爬蟲與 AI，並推送報告給您！
    echo (注意：執行當下您的電腦必須保持開機與非休眠狀態)
) else (
    echo [失敗] 排程設定發生錯誤，請嘗試對著本檔案按右鍵選擇「以系統管理員身分執行」。
)
echo.
pause
