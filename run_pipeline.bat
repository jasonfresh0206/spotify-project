@echo off
cd /d "C:\Users\User\spotify project"

:: Execute the full pipeline directly
python main.py --run-now

:: Wait for 5 seconds before closing the window (optional, just to see if any immediate crash happens)
timeout /t 5 >nul
