@echo off
chcp 65001 >nul
echo ==========================================
echo  YouTube to note 自動投稿ツール
echo ==========================================
echo.
set /p URL="YouTube URLを貼り付けてEnter: "
echo.
echo 処理中...
python youtube_to_note.py "%URL%"
echo.
echo note.com に投稿します...
python post_to_note.py
echo.
pause
