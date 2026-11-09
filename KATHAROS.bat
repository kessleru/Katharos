@echo off
rem Abre o Katharos como administrador. Se o PC nao tiver Python, instala pelo winget (python.org, oficial).
rem Uso: clique duas vezes, ou "KATHAROS.bat raiox", "KATHAROS.bat turbo --modo extremo"...
setlocal
net session >nul 2>&1
if %errorlevel% neq 0 (
  if "%~1"=="" (powershell -NoProfile -Command "Start-Process -Verb RunAs -FilePath '%~f0'") else (powershell -NoProfile -Command "Start-Process -Verb RunAs -FilePath '%~f0' -ArgumentList '%*'")
  exit /b
)
cd /d "%~dp0"
chcp 65001 >nul

set "PY="
rem o python.exe da pasta WindowsApps e o atalho da Microsoft Store: ele grava o registro numa copia virtual
for %%P in (py.exe python.exe) do if not defined PY for /f "delims=" %%W in ('where %%P 2^>nul') do if not defined PY (echo %%W| find /i "WindowsApps" >nul || set "PY=%%W")
if not defined PY if exist "%ProgramFiles%\Python312\python.exe" set "PY=%ProgramFiles%\Python312\python.exe"
if not defined PY if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"

if not defined PY (
  echo Python nao encontrado. Instalando o Python 3.12 oficial pelo winget...
  winget install --id Python.Python.3.12 --exact --scope machine --silent --accept-source-agreements --accept-package-agreements --disable-interactivity
  if exist "%ProgramFiles%\Python312\python.exe" (set "PY=%ProgramFiles%\Python312\python.exe") else (
    echo.
    echo Nao consegui instalar o Python. Baixe em https://www.python.org/downloads/ e marque "Add python.exe to PATH".
    pause
    exit /b 1
  )
)

"%PY%" "%~dp0katharos.py" %*
echo.
pause
