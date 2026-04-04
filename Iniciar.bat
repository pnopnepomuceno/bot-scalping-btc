@echo off
cd C:\Users\PaulinhoNOliveira\BotScalping

echo Iniciando Bot Scalping...
start "Bot Scalping" cmd /k "py bot_scalping.py"

timeout /t 3 /nobreak > nul

echo Iniciando Dashboard...
start "Dashboard" cmd /k "py dashboard.py"

echo.
echo ✅ Bot e Dashboard iniciados!
echo Acesse: http://localhost:5000
pause