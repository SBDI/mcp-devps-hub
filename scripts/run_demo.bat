@echo off
REM Run the MCP DevOps Hub demo with server and client

REM Run the PowerShell script
powershell -ExecutionPolicy Bypass -File scripts\run_demo_windows.ps1

REM Pause to view any output from the PowerShell script
pause
