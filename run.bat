@echo off
REM ============================================================================
REM Ollama CLI Chatbot Client - Windows Launcher Script
REM ============================================================================

setlocal enabledelayedexpansion

cd /d "%~dp0"

REM Check for virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo [INFO] Virtual environment not found. Setting up .venv...
    where py >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        py -m venv .venv
    ) else (
        where python >nul 2>nul
        if %ERRORLEVEL% equ 0 (
            python -m venv .venv
        ) else (
            echo [ERROR] Python 3 was not found in PATH or via py launcher.
            echo Please install Python 3.10+ and add it to your PATH.
            pause
            exit /b 1
        )
    )
    
    call .venv\Scripts\activate.bat
    echo [INFO] Installing required dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

REM Run client with interactive model selector by default
python -m cli_chat.main -s %*
