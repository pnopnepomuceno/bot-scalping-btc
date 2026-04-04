@echo off
REM ──────────────────────────────────────────────────────────
REM instalar.bat — Instalação do Bot de Scalping no Windows
REM Duplo clique para executar
REM ──────────────────────────────────────────────────────────

echo ======================================
echo  Bot de Scalping BTC/USDT - Windows
echo ======================================
echo.

python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo ERRO: Python nao encontrado.
    echo Instale em https://www.python.org e marque "Add to PATH"
    pause
    exit /b 1
)

echo Criando ambiente virtual...
python -m venv venv
call venv\Scripts\activate

echo Instalando dependencias...
pip install python-binance anthropic pandas requests python-dotenv -q

IF NOT EXIST ".env" (
    copy .env.example .env
    echo.
    echo Arquivo .env criado! Abra e coloque suas chaves de API.
    notepad .env
) ELSE (
    echo Arquivo .env ja existe.
)

echo.
echo ======================================
echo  Instalacao concluida!
echo ======================================
echo.
echo Para iniciar o bot:
echo   venv\Scripts\activate
echo   python bot_scalping.py
echo.
pause
