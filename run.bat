@echo off
cd /d "%~dp0"

echo === YouTube to note ===
echo.

echo Updating to latest version...
git pull origin HEAD 2>nul
echo.

echo Installing packages...
py -m pip install playwright pillow youtube-transcript-api requests -q
py -m playwright install chromium
echo Done.
echo.

set /p URL="Paste YouTube URL and press Enter: "
echo.

echo Step 1: Fetching transcript...
py youtube_to_note.py "%URL%"
if errorlevel 1 goto error

echo.
echo Step 2: Posting to note.com...
py post_to_note.py
if errorlevel 1 goto error

echo.
echo Done!
goto end

:error
echo Error occurred.
if exist error.log type error.log

:end
pause
