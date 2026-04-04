#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# instalar.sh — Instalação automática do Bot de Scalping
# Uso: chmod +x instalar.sh && ./instalar.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

echo "======================================"
echo " Bot de Scalping BTC/USDT - Instalação"
echo "======================================"
echo ""

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale em https://www.python.org"
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Cria ambiente virtual
echo ""
echo "📦 Criando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate

# Instala dependências
echo "📦 Instalando dependências..."
pip install --upgrade pip -q
pip install python-binance anthropic pandas requests python-dotenv -q

echo ""
echo "✅ Dependências instaladas!"

# Cria .env se não existir
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "📝 Arquivo .env criado. Edite-o com suas chaves de API:"
    echo "   nano .env"
else
    echo "⚠️  Arquivo .env já existe, mantendo o atual."
fi

echo ""
echo "======================================"
echo " Instalação concluída!"
echo "======================================"
echo ""
echo "Próximos passos:"
echo "  1. Edite o arquivo .env com suas chaves"
echo "  2. Teste em modo simulação: python3 bot_scalping.py"
echo "  3. Para modo real, edite bot_scalping.py: TESTNET = False"
echo ""
echo "Para rodar em segundo plano 24/7:"
echo "  nohup python3 bot_scalping.py > bot.log 2>&1 &"
echo "  tail -f bot.log   (para ver os logs)"
