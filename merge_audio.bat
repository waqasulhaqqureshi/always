@echo off
setlocal enabledelayedexpansion
title Mitti De Baway - One-Click ElevenLabs Audio Merger

echo ========================================================================
echo   MITTI DE BAWAY - ONE-CLICK ELEVENLABS AUDIO + VIDEO MERGER
echo ========================================================================
echo.

cd /d "%~dp0"

where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg not detected on system PATH.
    echo If Python cannot locate FFmpeg automatically, install it via PowerShell:
    echo     winget install Gyan.FFmpeg
    echo.
)

set PYTHON_CMD=
where python >nul 2>&1 && set PYTHON_CMD=python
if "%PYTHON_CMD%"=="" (
    where py >nul 2>&1 && set PYTHON_CMD=py -3
)
if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python 3 is not installed or not on PATH.
    echo Download Python from https://www.python.org/downloads/ and check "Add Python to PATH".
    pause
    exit /b 1
)

%PYTHON_CMD% merge_elevenlabs_audio.py
if errorlevel 1 (
    echo.
    echo [FAILED] Please fix the issue above and double-click merge_audio.bat again.
    pause
    exit /b 1
)

echo.
echo Your finished video is ready: FINAL_YOUTUBE_VIDEO.mp4
pause
