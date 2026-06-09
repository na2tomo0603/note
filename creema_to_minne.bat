@echo off
cd /d "%~dp0"

echo === Creema → ミンネ 自動出品ツール ===
echo.

echo 最新版に更新中...
git pull origin HEAD 2>nul
echo.

echo パッケージをインストール中...
py -m pip install playwright requests beautifulsoup4 -q
py -m playwright install chromium
echo.

set /p CREEMA_URL="CreemaのURLを貼り付けてEnter: "
echo.

set /p MINNE_EMAIL="ミンネのメールアドレス: "
echo.

set /p MINNE_PASSWORD="ミンネのパスワード: "
echo.

echo 出品処理を開始します...
set MINNE_EMAIL=%MINNE_EMAIL%
set MINNE_PASSWORD=%MINNE_PASSWORD%
py creema_to_minne.py "%CREEMA_URL%"

if errorlevel 1 goto error

echo.
echo 完了！
goto end

:error
echo エラーが発生しました。
if exist error.log type error.log

:end
pause
