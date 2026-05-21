@echo off
REM TOM V2.0 - Bootstrap batch -> PowerShell installer
REM Use the one-liner instead: iwr -useb .../install.ps1 | iex
echo.
echo   TOM V2.0 needs PowerShell to install on Windows.
echo   Please run this command in PowerShell:
echo.
echo   iwr -useb https://raw.githubusercontent.com/theturbos/tom-job-hunter/main/install.ps1 ^| iex
echo.
pause
