@echo off
cd /d %~dp0
start "" http://127.0.0.1:5000
if exist ".venv313\Scripts\python.exe" (
    ".venv313\Scripts\python.exe" app.py
) else (
    uv run app.py
)
pause
