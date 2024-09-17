@echo off
chcp 65001
setlocal enabledelayedexpansion

echo Folder FlashSketch 起動スクリプト

REM 仮想環境のアクティベート
call venv\Scripts\activate

REM アプリケーションの実行
python main.py

pause