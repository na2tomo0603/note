@echo off
echo Installing playwright...
pip install playwright -q
echo Installing chromium browser...
playwright install chromium
echo.
echo Running post_to_note.py ...
python post_to_note.py
echo.
if exist error.log (
    echo --- error.log ---
    type error.log
)
pause
