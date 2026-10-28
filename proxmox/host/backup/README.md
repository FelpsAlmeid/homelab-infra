# Backup do Proxmox

## Camadas

| Camada | O quê | Onde | Retenção |
|---|---|---|---|
| Diário (job do Proxmox, 02:30) | CTs 101, 103, 104, 105, 106 — modo snapshot | Disco separado do sistema (`hd-antigo`) | 7 diários · 4 semanais · 3 mensais |
| Semanal (job do Proxmox, dom 03:30) | CT 102 (Ollama, modelos re-baixáveis) | `hd-antigo` | 2 semanais |
| Fora do PC (timer, dom 05:00) | Dump mais recente de cada CT + `.tar` da configuração do host | Google Drive, remote `crypt` | 4 semanas |

- **Repetir perdidos** ligado nos jobs e `Persistent=true` no timer: o PC tem dualboot; se estiver no Windows no horário, roda quando o Proxmox subir.
- Bind mounts (`backup=0`, ex.: dados do Samba) **não** entram no `vzdump`.

## Google Drive sem expor a conta pessoal

- Conta **dedicada** aos backups, membro do grupo familiar do Google One: usa o espaço do plano, mas não enxerga os arquivos de ninguém.
- Arquivos em pasta compartilhada contam no espaço de **quem envia**, não do dono da pasta — por isso compartilhar uma pasta com outra conta não resolve.
- Remote com `scope=drive.file`: o token só vê o que o próprio rclone criou.
- Remote `crypt` por cima: conteúdo e nomes criptografados. **Senha e salt guardados fora do servidor** — sem eles, nada pode ser restaurado.

```bash
# conta dedicada (autorização via túnel: ssh -L 53682:127.0.0.1:53682 <usuario>@<host>)
rclone config create gdrive-vms drive scope=drive.file
rclone mkdir gdrive-vms:backup-homelab

# camada criptografada
P1=$(openssl rand -base64 32); P2=$(openssl rand -base64 32); echo "$P1"; echo "$P2"   # guardar no gerenciador de senhas
rclone config create gdrive-vms-crypt crypt remote=gdrive-vms:backup-homelab \
  filename_encryption=standard directory_name_encryption=true password="$P1" password2="$P2" --obscure
unset P1 P2; chmod 600 /root/.config/rclone/rclone.conf
```

## Cópia semanal

[`backup-offsite.sh`](backup-offsite.sh) · [`backup-offsite.service`](backup-offsite.service) · [`backup-offsite.timer`](backup-offsite.timer)

```bash
install -m 750 backup-offsite.sh /usr/local/sbin/
install -m 644 backup-offsite.service backup-offsite.timer /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now backup-offsite.timer
systemctl start backup-offsite.service && journalctl -u backup-offsite -f   # primeira execução
```

## Restaurar a partir do Drive

```bash
rclone lsf gdrive-vms-crypt:semanal/                       # semanas disponíveis
rclone copy gdrive-vms-crypt:semanal/<SEMANA>/ct-<ID>/ /mnt/hd-antigo/dump/ -P
pct restore <ID> /mnt/hd-antigo/dump/vzdump-lxc-<ID>-....tar.zst --storage <storage>
```
Em um servidor novo: instalar o rclone, recriar `gdrive-vms` (mesma conta) e `gdrive-vms-crypt` com **a mesma senha e salt**.

> Teste de restauração periódico: restaurar um CT com outro ID (`--unique 1`) e conferir o serviço.
