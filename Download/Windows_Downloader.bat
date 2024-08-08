@echo off

:: List of URLs to download the files from
setlocal enabledelayedexpansion
set urls=(
    "https://raw.githubusercontent.com/Frank1o3/Python-Proxy/main/DOCKERFILE"
    "https://raw.githubusercontent.com/Frank1o3/Python-Proxy/main/app/Config.json"
    "https://raw.githubusercontent.com/Frank1o3/Python-Proxy/main/app/LRU.py"
    "https://raw.githubusercontent.com/Frank1o3/Python-Proxy/main/requirements.txt"
    "https://raw.githubusercontent.com/Frank1o3/Python-Proxy/main/app/HTTP_Proxy.py"
    "https://raw.githubusercontent.com/Frank1o3/Python-Proxy/main/Download/cleanup.bat"
    "https://raw.githubusercontent.com/Frank1o3/Python-Proxy/main/Download/proxy-service.bat"
)

set DIR_NAME=Proxy
set APP_DIR=%DIR_NAME%\app

:: Ensure the directories exist before downloading files
if not exist "%DIR_NAME%" (
    mkdir "%DIR_NAME%"
)

if not exist "%APP_DIR%" (
    mkdir "%APP_DIR%"
)

:: Download the files
for %%u in %urls% do (
    powershell -Command "Invoke-WebRequest -Uri %%~u -OutFile \"%DIR_NAME%\%%~nxu\""
)

:: Move specific files to the app directory
if exist "%DIR_NAME%\HTTP_Proxy.py" (
    move "%DIR_NAME%\HTTP_Proxy.py" "%APP_DIR%" >nul
)
if exist "%DIR_NAME%\LRU.py" (
    move "%DIR_NAME%\LRU.py" "%APP_DIR%" >nul
)
if exist "%DIR_NAME%\Config.json" (
    move "%DIR_NAME%\Config.json" "%APP_DIR%" >nul
)

timeout /t 1 >nul

:: Check if 'build-docker' argument is passed
if "%~1"=="build-docker" (
    docker build -t python-proxy -f "%DIR_NAME%\DOCKERFILE" .
    echo Docker container built successfully.
) else (
    echo Docker container not built. To build the container, run the script with the 'build-docker' argument.
)

:: Check if 'service-create' argument is passed
if "%~2"=="service-create" (
    move "%DIR_NAME%\proxy-service.bat" "C:\Windows\System32\" >nul
    move "%DIR_NAME%\cleanup.bat" "C:\Windows\System32\" >nul
    schtasks /create /tn "ProxyService" /tr "C:\Windows\System32\proxy-service.bat" /sc onstart /rl highest /f
    echo Service created and enabled to start on system boot.
) else (
    echo No service created. To create a service, run the script with the 'service-create' argument.
)

pause
