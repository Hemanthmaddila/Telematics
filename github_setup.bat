@echo off
echo ================================================================
echo TELEMATICS INSURANCE PLATFORM - GITHUB SETUP SCRIPT
echo ================================================================
echo.
echo This script will help you publish your telematics platform to GitHub
echo.

:: Check if git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git is not installed or not in PATH
    echo Please install Git from https://git-scm.com/download/win
    pause
    exit /b 1
)

echo ✅ Git is installed
echo.

:: Get user input
set /p GITHUB_USERNAME="Enter your GitHub username: "
set /p REPO_NAME="Enter repository name (default: telematics-insurance-ml): "
if "%REPO_NAME%"=="" set REPO_NAME=telematics-insurance-ml

echo.
echo 📋 Configuration:
echo    GitHub Username: %GITHUB_USERNAME%
echo    Repository Name: %REPO_NAME%
echo    Repository URL: https://github.com/%GITHUB_USERNAME%/%REPO_NAME%
echo.

set /p CONFIRM="Continue with this configuration? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Setup cancelled
    pause
    exit /b 0
)

echo.
echo 🔧 Setting up Git repository...

:: Initialize git repository
echo Initializing Git repository...
git init
if %errorlevel% neq 0 (
    echo ERROR: Failed to initialize Git repository
    pause
    exit /b 1
)

:: Update files with actual GitHub username
echo Updating repository URLs...
powershell -Command "(Get-Content README.md) -replace '\[YourUsername\]', '%GITHUB_USERNAME%' | Set-Content README.md"
powershell -Command "(Get-Content setup.py) -replace '\[YourUsername\]', '%GITHUB_USERNAME%' | Set-Content setup.py"
powershell -Command "(Get-Content readme.txt) -replace 'YourGitHubUsername', '%GITHUB_USERNAME%' | Set-Content readme.txt"

:: Add all files
echo Adding files to Git...
git add .
if %errorlevel% neq 0 (
    echo ERROR: Failed to add files to Git
    pause
    exit /b 1
)

:: Create initial commit
echo Creating initial commit...
git commit -m "Initial commit: Production-grade telematics insurance platform with live AWS deployment"
if %errorlevel% neq 0 (
    echo ERROR: Failed to create commit
    pause
    exit /b 1
)

:: Set main branch
echo Setting main branch...
git branch -M main

:: Add remote origin
echo Adding GitHub remote...
git remote add origin https://github.com/%GITHUB_USERNAME%/%REPO_NAME%.git

echo.
echo ================================================================
echo 🚀 LOCAL GIT SETUP COMPLETE!
echo ================================================================
echo.
echo NEXT STEPS:
echo.
echo 1. Go to https://github.com and create a new repository:
echo    - Repository name: %REPO_NAME%
echo    - Description: Production-grade telematics platform for usage-based auto insurance with ML risk scoring - Live on AWS
echo    - Make it PUBLIC for portfolio showcase
echo    - DON'T initialize with README (you already have one)
echo.
echo 2. After creating the repository on GitHub, run this command:
echo    git push -u origin main
echo.
echo 3. Add repository topics on GitHub:
echo    machine-learning, insurance, telematics, aws, python, xgboost, kubernetes, microservices, production
echo.
echo 4. Set website URL in repository settings:
echo    http://telematics-alb-1568825282.us-east-2.elb.amazonaws.com
echo.
echo 5. Create a release (v1.0.0) to showcase your production system
echo.
echo Your repository URL will be:
echo https://github.com/%GITHUB_USERNAME%/%REPO_NAME%
echo.
echo Live system URL:
echo http://telematics-alb-1568825282.us-east-2.elb.amazonaws.com
echo.

pause
echo.
echo Would you like to create a release tag now? (y/n):
set /p CREATE_TAG=""
if /i "%CREATE_TAG%"=="y" (
    echo Creating release tag v1.0.0...
    git tag -a v1.0.0 -m "Release v1.0.0: Production telematics platform with live AWS deployment"
    echo ✅ Tag created! Don't forget to push it: git push origin v1.0.0
)

echo.
echo ================================================================
echo 🎉 SETUP COMPLETE!
echo ================================================================
echo.
echo Your telematics platform is ready for GitHub!
echo This showcases:
echo   ✅ Production-ready system deployed on AWS
echo   ✅ Advanced ML with XGBoost + SHAP explainability
echo   ✅ Microservices architecture with auto-scaling
echo   ✅ Real-time telematics data processing
echo   ✅ Professional software engineering practices
echo.
echo Remember to:
echo   - Create the repository on GitHub
echo   - Run: git push -u origin main
echo   - Add topics and website URL
echo   - Create a v1.0.0 release
echo.
pause
