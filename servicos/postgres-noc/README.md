# Postgres central do NOC (CT 115)

Banco `noc` único para as integrações (hoje: [atendimento Opa Suite](../n8n/opa-suite/README.md)), separado do n8n. O n8n escreve; o Grafana só lê.

- **Por que um CT próprio, e não mais um container no Compose do n8n:** isolamento, backup independente e um ponto único de entrada para os sistemas.
- **Exceção que continua:** o Postgres da [verificação de CTOs](../n8n/verificacao-ctos/README.md) segue dentro do Compose do n8n.

| Item | Valor |
|---|---|
| ID / hostname | 115 / `postgres-noc` |
| Tipo | LXC **não privilegiado**, Debian 13, **sem Docker** (Postgres nativo do Debian, `apt install postgresql`) |
| Recursos | 2 vCPU · 2 GB · 16 GB em `ssd-dados` · `onboot=1` |
| Rede | VLAN de serviços (`10.0.10.16`), IPv6 desativado, firewall do Proxmox ligado |
| Acesso | `pct exec 115`, sem SSH |

## Criação

```bash
TPL=$(pveam list local 2>/dev/null | awk '/debian-13-standard.*amd64/ {print $1}' | sort -V | tail -n1)
GW=$(pct config 108 | grep -oP 'gw=\K[^,]+')
MASK=$(pct config 108 | grep -oP 'ip=10\.0\.10\.10/\K[0-9]+')
pct create 115 "$TPL" --hostname postgres-noc --unprivileged 1 \
  --cores 2 --memory 2048 --swap 512 --rootfs ssd-dados:16 \
  --net0 name=eth0,bridge=vmbr0,tag=1010,ip=10.0.10.16/$MASK,gw=$GW,firewall=1 \
  --ostype debian --timezone host --onboot 1 --start 1
pct exec 115 -- bash -c 'apt update && apt install -y postgresql'
```

### Rede do Postgres

- `postgresql.conf`: `listen_addresses = '*'`.
- `pg_hba.conf`: uma linha por cliente, `/32` e `scram-sha-256`:

```
host    noc    noc           <ip-n8n>/32       scram-sha-256
host    noc    grafana_ro    <ip-grafana>/32   scram-sha-256
```

### Usuários

O template mínimo do Debian **não tem `sudo`**, então os comandos usam `su - postgres -c "psql …"`. Duas regras para lidar com senhas e arquivos:

- **Senha fora da linha de comando.** Arquivo `.sql` escrito com heredoc de delimitador entre aspas (`<< 'EOF'`), para o bash não interpretar caracteres da senha. Apagar o arquivo nos dois lados depois.
- **Arquivo em `/tmp`, com `chmod 644`.** O usuário `postgres` não lê `/root`.

```sql
-- escrita (n8n)
CREATE DATABASE noc;
CREATE USER noc WITH ENCRYPTED PASSWORD '<senha>';
GRANT ALL PRIVILEGES ON DATABASE noc TO noc;
-- depois do schema (tabelas criadas pelo postgres):
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO noc;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO noc;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO noc;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO noc;

-- leitura (Grafana)
CREATE USER grafana_ro WITH ENCRYPTED PASSWORD '<senha>';
GRANT CONNECT ON DATABASE noc TO grafana_ro;
GRANT USAGE ON SCHEMA public TO grafana_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafana_ro;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT ON TABLES TO grafana_ro;
ALTER DEFAULT PRIVILEGES FOR ROLE noc      IN SCHEMA public GRANT SELECT ON TABLES TO grafana_ro;
```

## Firewall

[`ct.fw.example`](ct.fw.example): entrada 5432 só do n8n e do Grafana; **nenhuma saída**.

As duas pontas também precisam de regra:
- **n8n:** saída para `<ip-postgres>:5432` no `.fw` do CT 108 ([exemplo](../n8n/ct.fw.example)).
- **Grafana:** a mesma saída no CT 114, quando o travamento de saída for aplicado.

## Pendências

- Entrar nos jobs de backup do host (vzdump diário) e na cópia semanal criptografada.
- Avaliar migrar o banco da verificação de CTOs para cá.
- Cadastrar no NetBox/Zabbix (ICMP + TCP 5432).
