#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  instalar_vps.sh — Setup completo do Bot Scalping na VPS Linux
#  Uso: bash instalar_vps.sh
# ═══════════════════════════════════════════════════════════════

set -e

REPO="https://github.com/pnopnepomuceno/bot-scalping-btc.git"
DIR="$HOME/BotScalping"
PYTHON="python3"

GREEN='\033[0;32m'
AMBER='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${AMBER}[!]${NC} $1"; }
error() { echo -e "${RED}[ERRO]${NC} $1"; exit 1; }

echo ""
echo "══════════════════════════════════════════"
echo "  Bot Scalping BTC — Setup VPS Linux"
echo "══════════════════════════════════════════"
echo ""

# ── 1. Sistema ────────────────────────────────────────────────
info "Atualizando sistema..."
sudo apt-get update -qq && sudo apt-get upgrade -y -qq

# ── 2. Python e dependências do sistema ───────────────────────
info "Instalando Python e Git..."
sudo apt-get install -y -qq python3 python3-pip python3-venv git curl ufw

# ── 3. Node.js e PM2 ─────────────────────────────────────────
if ! command -v pm2 &> /dev/null; then
    info "Instalando Node.js e PM2..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - -qq
    sudo apt-get install -y -qq nodejs
    sudo npm install -g pm2 -q
else
    info "PM2 já instalado: $(pm2 --version)"
fi

# ── 4. Clonar ou atualizar repositório ───────────────────────
if [ -d "$DIR/.git" ]; then
    info "Repositório já existe — atualizando..."
    cd "$DIR"
    git pull
else
    info "Clonando repositório..."
    git clone "$REPO" "$DIR"
    cd "$DIR"
fi

# ── 5. Ambiente virtual Python ────────────────────────────────
info "Criando ambiente virtual..."
$PYTHON -m venv venv
source venv/bin/activate

info "Instalando dependências Python..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# ── 6. Arquivo .env ───────────────────────────────────────────
if [ ! -f "$DIR/.env" ]; then
    warn "Arquivo .env não encontrado — criando template..."
    cat > "$DIR/.env" << 'ENVEOF'
# ─────────────────────────────────────────
# Bot Scalping — Variáveis de Ambiente
# Preencha com suas chaves reais
# ─────────────────────────────────────────
BINANCE_API_KEY=
BINANCE_API_SECRET=
ANTHROPIC_API_KEY=
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=
ENVEOF
    warn "IMPORTANTE: edite o .env com suas chaves antes de iniciar o bot!"
    warn "Comando: nano $DIR/.env"
else
    info ".env já existe — mantendo."
fi

# ── 7. PM2 — registrar processos ─────────────────────────────
info "Configurando PM2..."
cd "$DIR"

pm2 delete bot       2>/dev/null || true
pm2 delete dashboard 2>/dev/null || true

pm2 start bot_scalping.py \
    --name bot \
    --interpreter "$DIR/venv/bin/python3" \
    --cwd "$DIR" \
    --restart-delay 5000 \
    --max-restarts 10

pm2 start dashboard.py \
    --name dashboard \
    --interpreter "$DIR/venv/bin/python3" \
    --cwd "$DIR" \
    --restart-delay 5000 \
    --max-restarts 10

pm2 save

# Iniciar PM2 junto com o sistema
pm2 startup | tail -1 | sudo bash || warn "Execute manualmente: pm2 startup"

# ── 8. Firewall ───────────────────────────────────────────────
info "Configurando firewall (UFW)..."
sudo ufw allow 22/tcp   comment "SSH"    > /dev/null
sudo ufw allow 5000/tcp comment "Dashboard" > /dev/null
sudo ufw --force enable > /dev/null

# ── 9. Script de deploy automático ───────────────────────────
info "Criando script de atualização..."
cat > "$DIR/atualizar.sh" << 'DEPEOF'
#!/bin/bash
cd ~/BotScalping
git pull
source venv/bin/activate
pip install -r requirements.txt -q
pm2 restart bot
pm2 restart dashboard
echo "Bot atualizado e reiniciado!"
DEPEOF
chmod +x "$DIR/atualizar.sh"

# ── 10. Resumo final ──────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════"
echo -e "  ${GREEN}Setup concluído!${NC}"
echo "══════════════════════════════════════════"
echo ""
echo "Próximos passos:"
echo "  1. Edite as chaves:  nano ~/BotScalping/.env"
echo "  2. Reinicie o bot:   pm2 restart bot"
echo "  3. Veja os logs:     pm2 logs bot"
echo "  4. Dashboard:        http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Para atualizar o bot depois de um git push:"
echo "  bash ~/BotScalping/atualizar.sh"
echo ""
pm2 status