@echo off
echo Installing requests...
pip install requests -q
echo OK

echo.
echo Running post_to_note.py ...
python post_to_note.py

echo.
if exist error.log (
    echo --- error.log ---
    type error.log
)
pause
