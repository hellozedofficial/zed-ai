@echo off
echo Starting Bedrock Chat Application...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found!
    echo Please run setup.bat first
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo .env file not found!
    echo Please copy .env.example to .env and add your AWS credentials
    exit /b 1
)

echo Starting Flask server...
echo.
python app.py
