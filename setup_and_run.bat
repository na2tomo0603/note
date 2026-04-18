@echo off
chcp 65001 >nul
echo ========================================
echo  note.com 下書き自動投稿 セットアップ
echo ========================================
echo.

:: Python確認
python --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Python が見つかりません。
    echo https://www.python.org/downloads/ からインストールしてください。
    echo インストール時に「Add Python to PATH」にチェックを入れてください。
    pause
    exit /b 1
)
echo [OK] Python が見つかりました

:: Firefox確認
if exist "%ProgramFiles%\Mozilla Firefox\firefox.exe" (
    echo [OK] Firefox が見つかりました
    set FIREFOX_PATH=%ProgramFiles%\Mozilla Firefox\firefox.exe
) else if exist "%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe" (
    echo [OK] Firefox が見つかりました
    set FIREFOX_PATH=%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe
) else (
    echo [エラー] Firefox が見つかりません。
    echo https://www.mozilla.org/ja/firefox/ からインストールしてください。
    pause
    exit /b 1
)

:: geckodriver確認・ダウンロード
where geckodriver >nul 2>&1
if errorlevel 1 (
    echo [情報] geckodriver をダウンロードします...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/mozilla/geckodriver/releases/download/v0.35.0/geckodriver-v0.35.0-win64.zip' -OutFile 'geckodriver.zip'}"
    powershell -Command "& {Expand-Archive -Path 'geckodriver.zip' -DestinationPath '.' -Force}"
    del geckodriver.zip
    echo [OK] geckodriver をダウンロードしました
) else (
    echo [OK] geckodriver が見つかりました
)

:: noteclient インストール
echo.
echo [情報] noteclient をインストールします...
pip install noteclient -q
echo [OK] noteclient インストール完了

:: 実行
echo.
echo ========================================
echo  下書き投稿を開始します...
echo ========================================
echo.
python post_to_note.py

echo.
pause
