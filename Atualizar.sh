#!/bin/bash
# ═══════════════════════════════════════════════════
#  atualizar.sh — Atualiza bot e dashboard na VPS
#  Uso: bash atualizar.sh
# ═══════════════════════════════════════════════════
 
set -e
DIR=~/BotScalping
GREEN='\033[0;32m'; AMBER='\033[0;33m'; NC='\033[0m'
info(){ echo -e "${GREEN}[OK]${NC} $1"; }
warn(){ echo -e "${AMBER}[!]${NC} $1"; }
 
cd $DIR
 
info "Baixando atualizações do GitHub..."
git pull
 
info "Ativando ambiente virtual..."
source venv/bin/activate
 
info "Atualizando dependências..."
pip install -r requirements.txt -q
 
info "Reiniciando bot(s) e dashboard..."
pm2 restart all --update-env
 
sleep 3
pm2 status
 
echo ""
info "Atualização concluída!"
echo -e "Dashboard: ${AMBER}http://$(hostname -I | awk '{print $1}'):5000${NC}"