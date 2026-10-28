# Roadmap

Separado por sistema. Cada seção tem o que já foi feito e o que falta.

## Projeto principal (homelab + IA para o NOC)

- [x] Base de IA local: Ollama na GPU + Open WebUI
- [x] Serviços de NOC no laboratório: NetBox (IPAM), GLPI (chamados), Zabbix (monitoramento)
- [x] Integrações NetBox → Zabbix e Zabbix → GLPI
- [x] Publicação segura dos serviços (proxy na nuvem, sem portas abertas na rede local)
- [ ] **Fechar o monitoramento** do backbone (ver [Zabbix](#zabbix))
- [ ] **Agente de IA (OpenClaw) em VM isolada**, com snapshot antes de cada skill e tokens **somente leitura**
  - [ ] Primeiro caso de uso N2: resumir problemas ativos do Zabbix e chamados abertos no GLPI
- [ ] Acesso da equipe do NOC ao Open WebUI (contas sem admin, modelo padrão e *system prompt* em PT-BR, grupos/permissões)
- [ ] Coleta automática das configurações para este repositório

## Proxmox (host)

- [x] VLANs (gerência e serviços), IPv6 desativado, root sem acesso remoto
- [x] RTX 3060 com driver assinado (Secure Boot ativo)
- [x] Firewall do Proxmox em todos os containers (política DROP)
- [x] Storage `ssd-dados` (LVM-Thin) e migração de Zabbix, NetBox e GLPI ([como](../proxmox/host/ssd-dados.md))
- [x] Repositório `no-subscription` (enterprise desativado)
- Atualizações: **manuais, sob demanda** (correções de segurança/bugs), com backup antes e `dkms status` antes de reiniciar quando houver kernel novo
- [x] Remover os discos antigos (`unused0`) dos CTs 104–106
- [x] Ordem de boot: NetBox/GLPI `order=1`, Zabbix `order=2,up=60` (validar no próximo reboot)
- [ ] `intel-microcode` e fuso horário
- [x] Serviços de HA desativados (nó único)
- [ ] TFA (TOTP) no usuário administrador
- [x] Firewall do host: 8006/22 só para `redes-admin` (rede local automática do Proxmox contida na gerência)
- [x] Jobs de backup: diário (5 CTs) e semanal (Ollama) no HD, com retenção e repetir perdidos
- [x] Cópia semanal criptografada para o Google Drive (conta dedicada, `drive.file` + `crypt`)
- [ ] Instalar a versão nova do `backup-offsite.sh` (envio único) e validar uma execução completa
- [ ] Teste de restauração a partir do Drive
- [x] Limpeza do HD antigo (backups e ISOs do servidor anterior)

## Zabbix

- [x] Zabbix 7.0 LTS com PostgreSQL ajustado para pouca escrita, em SSD dedicado
- [x] Communities como macros secretas
- [x] Publicado no proxy (Access List, `/api_jsonrpc.php` bloqueado) com MFA
- [x] Porta e community SNMP por equipamento vindas do NetBox (config context)
- [ ] Config context global aplicado a **todos** os devices com a tag `zabbix`
- [x] Equipamentos já sincronizados com SNMP ok (local context em cada um)
- [ ] Restante do backbone (~20 equipamentos) com a tag `zabbix`
- [ ] Testar `bulk: 1` no equipamento atrás de NAT (manter `0` se der timeout)
- [ ] Template para o modelo NetEngine 8000 (se for monitorado)
- [ ] Role própria para a conta do sync (sair do Super admin)
- [ ] Avaliar SNMPv3 nos equipamentos principais

## NetBox

- [x] Restaurado do servidor antigo, convertido para não privilegiado
- [x] Custom fields e tag para a integração; token v2 restrito por IP
- [x] Config context global + local context por equipamento
- [x] Publicado no proxy (Access List) com tokens só da rede interna
- [ ] Permissões por objeto para a conta `zabbix-sync` (sair do superuser)
- [ ] Cadastrar o serial dos devices (alimenta `{$HW_SERIAL}` no Zabbix)

## GLPI

- [x] Restaurado do servidor antigo, firewall `DOCKER-USER` e cron em modo CLI
- [x] Publicado no proxy (Access List, APIs bloqueadas) com 2FA
- [ ] HTTPS interno (tokens ainda em HTTP dentro da VLAN)
- [ ] Avaliar `cron_limit` 5 → 10
- [ ] Trocar as senhas do MariaDB

## Integrações

**NetBox → Zabbix** ([netbox-zabbix-sync](../servicos/netbox-zabbix-sync/README.md))
- [x] Hosts criados a partir do inventário (tag, grupo `site/role`, template do tipo)
- [x] `usermacro_sync = "full"` e patch do bug da macro secreta
- [ ] Reaplicar o patch a cada atualização — ou atualizar quando corrigido no projeto (abrir issue)

**Zabbix → GLPI** ([zabbix-glpi](../servicos/zabbix-glpi/README.md))
- [x] Abertura, acompanhamento e solução automática de chamados (validado de novo após a migração e o proxy)
- [ ] Revogar o token de API usado na configuração e limpar o arquivo de segredos temporário
- [ ] Migrar para a API nova do GLPI (OAuth) antes da remoção da legada

## Proxy (Oracle Cloud + NPM)

- [x] Instância ARM, IP reservado, firewall em duas camadas
- [x] Túnel WireGuard dedicado até o MikroTik; painel do NPM só pela VPN
- [x] Open WebUI público com HTTPS; Zabbix, NetBox e GLPI só para os IPs da empresa
- [ ] SSH pela VPN e remover a regra pública da porta 22

## IA (Ollama + Open WebUI)

- [x] Ollama em LXC não privilegiado com a GPU
- [x] Open WebUI publicado com HTTPS
- [ ] Modelo padrão e *system prompt* para o NOC
- [ ] Contas da equipe e grupos de permissão

## Próximo passo

1. **Fechar o monitoramento** (seções Zabbix e Proxmox).
2. **Agente OpenClaw** em VM isolada, com tokens somente leitura.
