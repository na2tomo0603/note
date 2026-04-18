@echo off
chcp 65001 >nul
echo ==========================================
echo  YouTube to note 全自動投稿ツール
echo ==========================================
echo.

echo [準備] 必要パッケージをインストール中...
pip install playwright pillow youtube-transcript-api requests -q
playwright install chromium --quiet
echo 完了
echo.

set /p URL="YouTube URLを貼り付けてEnter: "
echo.

echo [1/3] 字幕取得 + 記事生成 + サムネ作成中...
python "%~dp0youtube_to_note.py" "%URL%"
if errorlevel 1 goto error

echo.
echo [2/3] note.com に投稿中...
python "%~dp0post_to_note.py"
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
