@echo off
chcp 65001
setlocal enabledelayedexpansion

echo Folder FlashSketch インストールスクリプト

REM Pythonがインストールされているか確認
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Pythonがインストールされていません。
    echo https://www.python.org/downloads/ からPythonをインストールしてください。
    pause
    exit /b
)

REM 仮想環境の作成
echo 仮想環境を作成しています...
python -m venv venv
call venv\Scripts\activate

REM 必要なパッケージをインストール
echo 必要なパッケージをインストールしています...
pip install PyQt5 Pillow PyYAML

REM アプリケーションファイルのコピー
echo アプリケーションファイルをコピーしています...
copy main.py .
xcopy /E /I language language
if exist config.yaml copy config.yaml .

echo インストールが完了しました。
pause