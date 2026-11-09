@echo off
rem Abre o Katharos no PowerShell como administrador.
rem Acha o Python que ja existe no PC e so instala um se nao houver nenhum.
rem Uso: clique duas vezes, ou "KATHAROS.bat raiox", "KATHAROS.bat turbo --modo extremo"...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0programa\katharos.ps1" %*
