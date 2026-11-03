#!/bin/bash
# n8n-update.sh — atualiza o n8n do CT 108 para uma versão fixa, com snapshot
# e saída de internet aberta só durante o pull.
# Uso: n8n-update.sh 2.47.1
set -euo pipefail

CT=108
FW=/etc/pve/firewall/$CT.fw
V="${1:-}"
[[ "$V" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "Uso: $0 <versão X.Y.Z>"; exit 1; }

ATUAL=$(pct exec $CT -- docker inspect n8n --format '{{.Config.Image}}' | sed 's/.*://')
echo "n8n em uso: $ATUAL  ->  nova: $V"
read -rp "Confirmar a atualização? (s/N) " R; [[ "$R" == [sS] ]] || { echo "Cancelado."; exit 0; }

SNAP="antes_n8n_${V//./_}"
echo "== Snapshot $SNAP"
pct snapshot $CT "$SNAP" --description "Antes do n8n $V ($(date '+%d/%m/%Y %H:%M'))"

fechar_egress() {
  if grep -q '# TEMP atualizacao n8n' "$FW"; then
    sed -i '/# TEMP atualizacao n8n/d' "$FW"
    pve-firewall compile >/dev/null 2>&1 || true
    echo "== Saída temporária FECHADA"
  fi
}
trap fechar_egress EXIT

echo "== Abrindo saída temporária (80/443)"
cp "$FW" "/root/$CT.fw.bak-$(date +%Y%m%d-%H%M)"
sed -i '$a OUT ACCEPT -p tcp -dport 443 -log nolog # TEMP atualizacao n8n' "$FW"
sed -i '$a OUT ACCEPT -p tcp -dport 80 -log nolog # TEMP atualizacao n8n' "$FW"
pve-firewall compile >/dev/null
sleep 10

echo "== Pull e recriação dos containers"
pct exec $CT -- bash -c "set -e; cd /opt/n8n
  cp compose.yml compose.yml.bak-\$(date +%Y%m%d-%H%M)
  sed -i 's#\(docker.n8n.io/n8nio/n8n:\)[0-9.]*#\1$V#' compose.yml
  grep -n 'n8nio/n8n:' compose.yml
  docker compose pull
  docker compose up -d
  docker image prune -f >/dev/null"

fechar_egress
trap - EXIT

echo "== Aguardando o healthz"
for i in $(seq 1 24); do
  if pct exec $CT -- curl -sk -m 5 https://10.0.10.10/healthz | grep -q '"ok"'; then OK=1; break; fi
  sleep 5
done
if [[ "${OK:-0}" != 1 ]]; then
  echo "!! healthz não respondeu em 2 min. Veja: pct exec $CT -- bash -c 'cd /opt/n8n && docker compose logs --tail 80 n8n'"
  echo "!! Voltar atrás (migrações de banco não são reversíveis só trocando a tag):"
  echo "   pct shutdown $CT && pct rollback $CT $SNAP && pct start $CT"
  exit 1
fi

echo "== OK: n8n $(pct exec $CT -- docker exec n8n n8n --version 2>/dev/null) respondendo"
echo "   Teste o resumo pelo OpenClaw e, depois de alguns dias sem problema: pct delsnapshot $CT $SNAP"
/usr/local/sbin/n8n-check || true
