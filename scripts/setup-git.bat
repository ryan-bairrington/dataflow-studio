@echo off
REM DataFlow Studio - Git Setup Script
REM Run this after installing Git

echo =================================
echo DataFlow Studio - Git Setup
echo =================================
echo.

REM Check if git is available
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed or not in PATH.
    echo.
    echo Please install Git from: https://git-scm.com/download/win
    echo Or run: winget install Git.Git
    echo.
    echo After installing, you may need to:
    echo 1. Close and reopen this terminal
    echo 2. Or add Git to your PATH manually
    pause
    exit /b 1
)

echo Git found: 
git --version
echo.

REM Navigate to project directory
cd /d "%~dp0.."
echo Working in: %CD%
echo.

REM Check if already a git repo
if exist ".git" (
    echo This is already a Git repository.
    echo Current status:
    git status --short
    echo.
    pause
    exit /b 0
)

REM Initialize git repo
echo Initializing Git repository...
git init

REM Add all files
echo.
echo Adding files...
git add .

REM Initial commit
echo.
echo Creating initial commit...
git commit -m "Initial commit: DataFlow Studio MVP"

echo.
echo =================================
echo SUCCESS! Git repository initialized.
echo =================================
echo.
echo Next steps:
echo 1. Create a new repository on GitHub (https://github.com/new)
echo 2. Run these commands:
echo.
echo    git remote add origin https://github.com/YOUR_USERNAME/dataflow-studio.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo Or use GitHub Desktop to push the repository.
echo.
pause
