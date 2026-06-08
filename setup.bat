@echo off
REM Audio Overview Studio — Windows setup script
REM Run once: setup.bat

echo.
echo ==========================================
echo   Audio Overview Studio — Setup
echo ==========================================
echo.

REM --- .env ---
if not exist ".env" (
    copy .env.example .env > nul
    echo [OK] Created .env from .env.example
    echo      Open .env and add your API keys, or use the TTS Setup panel in the app.
) else (
    echo [OK] .env already exists — skipping
)

REM --- Python venv ---
echo.
echo Setting up Python backend...
cd backend

if not exist ".venv" (
    python -m venv .venv
    echo [OK] Created Python virtual environment
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
echo [OK] Python dependencies installed

REM --- Kokoro (local TTS, optional but recommended) ---
echo.
echo Installing Kokoro TTS (local, no API key needed)...
pip install "kokoro[en]" "misaki[en]" -q
if %errorlevel% == 0 (
    echo [OK] Kokoro installed
) else (
    echo [SKIP] Kokoro install failed - you can use OpenAI or ElevenLabs TTS instead
)

cd ..

REM --- Node / frontend ---
echo.
echo Setting up frontend...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Install it from https://nodejs.org (LTS version)
    pause
    exit /b 1
)

cd frontend
call npm install -q
echo [OK] Frontend dependencies installed
cd ..

echo.
echo ==========================================
echo   Setup complete!
echo ==========================================
echo.
echo Next steps:
echo   1. Edit .env and add your API key(s)  -- OR --
echo      enter them in the app's TTS Setup panel
echo   2. Start the app: python launch.py
echo   3. Open http://localhost:5173
echo   4. Click TTS Setup to configure your voice engine
echo.
pause
