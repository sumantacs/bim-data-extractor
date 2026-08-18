@echo off
REM ===================================
REM BIM Data Extractor - Quick Run
REM ===================================

REM Activate virtual environment
if not exist venv (
    echo [ERROR] Virtual environment not found.
    echo Please run setup_windows.bat first
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

REM Run the app
echo.
echo ===================================
echo  BIM Data Extractor is starting...
echo ===================================
echo.
echo The app will open in your default browser at:
echo http://localhost:8501
echo.
echo Keep this window open. Press Ctrl+C to stop the app.
echo.

streamlit run app.py

pause
