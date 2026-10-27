# Zabbix 7.0 LTS em LXC

Monitoramento SNMP de ~20 equipamentos de rede, com o banco ajustado para **pouca escrita** (um Zabbix anterior travou o host quando dividia o SSD do sistema).

| Item | Valor |
|---|---|
| Container | LXC não privilegiado, Debian 13, 2 vCPU / 4 GB |
| Versões | Zabbix 7.0 LTS · PostgreSQL 17 · nginx · php8.4-fpm |
| Disco | SSD dedicado `ssd-dados` (LVM-Thin) — [migração](../../proxmox/host/ssd-dados.md) |

## Por que 7.0 e não 8.0
Na data da instalação, o repositório do 8.0 para Debian 13 só oferecia uma *release candidate* (e o pacote do repositório ativava o canal *unstable*). Ficou o 7.0 LTS, versão final com suporte longo.

## Instalação resumida
```bash
# repositório oficial 7.0 para Debian 13 (veja zabbix.com/download)
apt install -y postgresql zabbix-server-pgsql zabbix-frontend-php php8.4-pgsql \
  zabbix-nginx-conf zabbix-sql-scripts zabbix-agent2

runuser -u postgres -- createuser --pwprompt zabbix
runuser -u postgres -- createdb -O zabbix zabbix
zcat /usr/share/zabbix-sql-scripts/postgresql/server.sql.gz | runuser -u zabbix -- psql zabbix
# no 7.0 o schema fica em /usr/share/zabbix-sql-scripts/ (não em /usr/share/zabbix/sql-scripts/)
```
- `DBPassword` em `/etc/zabbix/zabbix_server.conf` (permissão `600 root:root`)
- [`90-zabbix-lowwrite.conf`](90-zabbix-lowwrite.conf) em `/etc/postgresql/17/main/conf.d/`
- nginx: `listen 80;` e `server_name` em `/etc/zabbix/nginx.conf`; remover o site padrão

## Configuração
- Housekeeping: histórico 7 dias, trends 365 dias
- Itens com intervalos de 1–5 min e pré-processamento *Discard unchanged with heartbeat*
- Communities SNMP em **macros globais do tipo "Secret text"** (`{$SNMP_COMMUNITY}`) — nunca em arquivos
- Templates oficiais já vêm no banco (inclusive os MikroTik *by SNMP*); modelo fora da lista → `Mikrotik by SNMP`
- Firewall do Proxmox: SSH, ping e 80 só para `redes-admin` ([modelo](../../proxmox/firewall/ct.fw.example)); a coleta SNMP é de saída

## Acesso e MFA
- Publicado no proxy com Access List (só IPs da empresa) e `/api_jsonrpc.php` negado ([NPM](../../oracle/npm/advanced/README.md))
- MFA TOTP no grupo dos administradores; robôs de integração não são afetados (API/sem frontend)
- `{$ZABBIX.URL}` com a URL HTTPS pública (link do evento nos chamados)

### Recuperar o acesso se perder o TOTP
O segredo fica na tabela `mfa_totp_secret`; apagando a linha do usuário, o próximo login mostra um QR novo:
```sql
-- su - postgres -c "psql -d zabbix"
SELECT u.userid, u.username, t.status FROM users u JOIN mfa_totp_secret t ON t.userid = u.userid;
DELETE FROM mfa_totp_secret WHERE userid = (SELECT userid FROM users WHERE username = '<usuario>');  -- esperar DELETE 1
```
Ao recadastrar, guarde a chave em texto (abaixo do QR) no gerenciador de senhas.

## Integrações
- Hosts sincronizados a partir do NetBox ([netbox-zabbix-sync](../netbox-zabbix-sync/README.md))
- Problemas abrindo/solucionando chamados no GLPI ([zabbix-glpi](../zabbix-glpi/README.md))
