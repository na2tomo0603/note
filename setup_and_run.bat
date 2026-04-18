@echo off
echo Installing noteclient...
pip install noteclient -q
if errorlevel 1 (
    echo ERROR: pip install failed
    pause
    exit /b 1
)
echo noteclient installed OK

echo.
echo Running post_to_note.py ...
python post_to_note.py

echo.
if exist error.log (
    echo --- error.log ---
    type error.log
)
pause
