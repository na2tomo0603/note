@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================
echo  YouTube to note 全自動投稿ツール
echo ==========================================
echo.

echo [準備] 必要パッケージをインストール中...
py -m pip install playwright pillow youtube-transcript-api requests -q 2>nul
if errorlevel 1 python -m pip install playwright pillow youtube-transcript-api requests -q
py -m playwright install chromium --quiet 2>nul
if errorlevel 1 python -m playwright install chromium --quiet
echo 完了
echo.

set /p URL="YouTube URLを貼り付けてEnter: "
echo.

echo [1/3] 字幕取得 + 記事生成 + サムネ作成中...
py youtube_to_note.py "%URL%" 2>nul
if errorlevel 1 python youtube_to_note.py "%URL%"
if errorlevel 1 goto error

echo.
echo [2/3] note.com に投稿中...
py post_to_note.py 2>nul
if errorlevel 1 python post_to_note.py
if errorlevel 1 goto error

echo.
echo [3/3] 完了！
goto end

:error
echo.
echo エラーが発生しました。
if exist error.log type error.log

:end
pause
