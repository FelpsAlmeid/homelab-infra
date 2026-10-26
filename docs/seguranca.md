# Segurança

## Princípios

1. **Fechado por padrão:** política de entrada `DROP` em todos os containers; cada porta é liberada para uma origem específica.
2. **Grupos de acesso separados:**
   - `redes-admin` — gerência + VPN de administração: SSH, interfaces web e APIs internas.
   - `proxy-oracle` — só o IP do túnel do proxy, e só na porta do serviço publicado.
3. **Menor privilégio:** containers não privilegiados; root bloqueado para acesso remoto ao host; administração por usuário próprio com `sudo`.
4. **Nada de segredos no repositório:** só arquivos `*.example`; `.gitignore` bloqueia `.env`, chaves e dumps; `gitleaks` roda antes de cada commit.

## Camadas

| Camada | Controle |
|---|---|
| Internet → nuvem | Security List da Oracle + iptables da instância (80/443 e a porta do WireGuard) |
| Nuvem → rede local | Túnel WireGuard dedicado; firewall do MikroTik libera só destino/porta publicados |
| Rede local → containers | Firewall do Proxmox (fora do container, não é contornado pelo Docker) |
| Painel do proxy | Escuta só em `127.0.0.1` e no IP do túnel; acesso pela VPN |
| Host | Secure Boot, root sem login remoto, IPv6 desativado, SSH só com chave |
| Aplicações | Cadastro público desativado; contas criadas pelo administrador |

## Docker e firewall

Portas publicadas pelo Docker **ignoram a cadeia INPUT** do iptables (e o UFW). Por isso:
- o filtro principal fica no **firewall do Proxmox**, fora do container;
- quando há filtro dentro do container, ele usa a cadeia `DOCKER-USER` com o IP interno do container (após o DNAT) — veja [`servicos/glpi/firewall-docker-glpi.sh`](../servicos/glpi/firewall-docker-glpi.sh).

## O que nunca entra aqui

Senhas, tokens de API, chaves privadas (SSH, WireGuard, MOK), communities SNMP, IPs públicos, dumps de banco e dados de clientes.
