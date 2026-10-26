#!/usr/bin/env bash
# Restringe o acesso ao GLPI publicado pelo Docker.
# Portas publicadas pelo Docker não passam pela cadeia INPUT, por isso o filtro fica na DOCKER-USER,
# usando o IP interno do container (o DNAT já ocorreu quando o pacote chega aqui).
# Idempotente: remove as regras deste script antes de reaplicar.
set -euo pipefail

CONTAINER_IP="172.18.0.10"   # IP do glpi-app na rede do compose
CONTAINER_PORT="80"
ALLOWED=("10.0.0.0/24" "10.0.212.0/24")   # gerência + VPN de administração
TAG="glpi-fw"

# Remove regras anteriores marcadas com o comentário do script
while iptables -S DOCKER-USER | grep -q -- "--comment ${TAG}"; do
  rule=$(iptables -S DOCKER-USER | grep -- "--comment ${TAG}" | head -n1 | sed 's/^-A /-D /')
  eval "iptables ${rule}"
done

# DROP no fim, ACCEPTs inseridos antes dele
iptables -I DOCKER-USER -p tcp -d "${CONTAINER_IP}" --dport "${CONTAINER_PORT}" \
  -m comment --comment "${TAG}" -j DROP
for net in "${ALLOWED[@]}"; do
  iptables -I DOCKER-USER -p tcp -s "${net}" -d "${CONTAINER_IP}" --dport "${CONTAINER_PORT}" \
    -m comment --comment "${TAG}" -j ACCEPT
done

iptables -S DOCKER-USER | grep -- "--comment ${TAG}"
