@echo off
echo Installing required packages...
pip install youtube-transcript-api playwright anthropic -q
playwright install chromium
echo.
echo Running youtube_to_note.py ...
python youtube_to_note.py %1
echo.
pause
