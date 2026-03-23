@echo off
cd /d "C:\Users\User\spotify project"

:: Get today's date
set TODAY=%date:~0,10%

:: Copy reports to Obsidian Vault
if not exist "C:\Users\User\Documents\Obsidian Vault\.obsidian\spotify-reports" mkdir "C:\Users\User\Documents\Obsidian Vault\.obsidian\spotify-reports"
xcopy "C:\Users\User\spotify project\data\reports\*.*" "C:\Users\User\Documents\Obsidian Vault\.obsidian\spotify-reports\" /Y /D

:: Git backup
git add .
git commit -m "Auto backup %TODAY%"
git push

echo Done!
