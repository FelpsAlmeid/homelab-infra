#!/usr/bin/env bash
# Cópia semanal, criptografada, dos backups do Proxmox para o Google Drive.
# - Envia o dump mais recente de cada CT (+ .log e .notes) e um .tar da configuração do host.
# - Destino: remote rclone "crypt" (nomes e conteúdo criptografados).
# - Mantém as últimas KEEP_WEEKS semanas no destino.
set -euo pipefail

DUMP_DIR="${DUMP_DIR:-/mnt/hd-antigo/dump}"
REMOTE="${REMOTE:-gdrive-vms-crypt:semanal}"
VMIDS="${VMIDS:-101 102 103 104 105 106}"
KEEP_WEEKS="${KEEP_WEEKS:-4}"
WEEK="$(date +%G-W%V)"
DEST="${REMOTE}/${WEEK}"

RCLONE=(rclone --transfers 4 --drive-chunk-size 64M --retries 5 --low-level-retries 20 --stats 5m --stats-one-line -v)

log() { echo "[backup-offsite] $*"; }

# 1. Não competir com um vzdump em andamento (espera até 2 h)
for _ in $(seq 1 120); do
  pgrep -x vzdump >/dev/null || break
  log "vzdump em andamento, aguardando..."
  sleep 60
done
if pgrep -x vzdump >/dev/null; then
  log "ERRO: vzdump ainda em execução após 2 h"; exit 1
fi

# 2. Monta a semana numa pasta de preparo com hardlinks (mesmo disco: não ocupa espaço extra)
#    e envia tudo numa única chamada do rclone (menos overhead por arquivo, uploads em paralelo)
STAGE="$DUMP_DIR/.offsite-stage/$WEEK"
rm -rf "$DUMP_DIR/.offsite-stage"
mkdir -p "$STAGE"
for id in $VMIDS; do
  last="$(ls -1t "$DUMP_DIR"/vzdump-lxc-"$id"-*.tar.zst 2>/dev/null | head -n1 || true)"
  if [[ -z "$last" ]]; then
    log "AVISO: nenhum dump encontrado para o CT $id"; continue
  fi
  base="${last%.tar.zst}"
  log "CT $id -> $(basename "$last")"
  mkdir -p "$STAGE/ct-$id"
  for f in "$last" "$base.log" "$last.notes"; do
    if [[ -f "$f" ]]; then ln -f "$f" "$STAGE/ct-$id/"; fi
  done
done

# 3. Configuração do host
mkdir -p "$STAGE/host"
tar -czf "$STAGE/host/host-config-$(hostname)-$(date +%F).tar.gz" --ignore-failed-read \
  /etc/pve /etc/network /etc/hosts /etc/hostname /etc/fstab \
  /etc/default/grub /etc/grub.d /etc/modprobe.d /etc/sysctl.d \
  /etc/apt/sources.list.d /etc/ssh/sshd_config /etc/systemd/system 2>/dev/null || true

log "Enviando $(du -sh "$STAGE" | cut -f1) para $DEST"
"${RCLONE[@]}" copy "$STAGE" "$DEST"
rm -rf "$DUMP_DIR/.offsite-stage"

# 4. Retenção: mantém as últimas KEEP_WEEKS semanas
mapfile -t weeks < <(rclone lsf --dirs-only "$REMOTE" | sed 's#/$##' | sort)
if (( ${#weeks[@]} > KEEP_WEEKS )); then
  for old in "${weeks[@]:0:${#weeks[@]}-KEEP_WEEKS}"; do
    log "Removendo semana antiga: $old"
    rclone purge "$REMOTE/$old"
  done
fi

log "Concluído: $DEST"
rclone size "$DEST"
