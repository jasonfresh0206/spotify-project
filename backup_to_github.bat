@echo off
cd /d "C:\Users\User\spotify project"

:: Get today's date
set TODAY=%date:~0,10%

:: Git backup
git add .
git commit -m "Auto backup %TODAY%"
git push

echo Done!
