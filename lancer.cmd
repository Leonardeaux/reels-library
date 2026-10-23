@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m reels_library
) else (
  python -m reels_library
)
if errorlevel 1 pause
