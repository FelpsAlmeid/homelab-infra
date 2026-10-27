# Roadmap

- [x] Host Proxmox com VLANs, hardening e IPv6 desativado
- [x] RTX 3060 com driver assinado (Secure Boot ativo)
- [x] Samba em LXC com bind mount
- [x] Ollama na GPU + Open WebUI
- [x] Proxy público na Oracle Cloud com HTTPS
- [x] Túnel WireGuard dedicado até o MikroTik
- [x] Painel do proxy acessível só pela VPN
- [x] NetBox e GLPI restaurados e endurecidos
- [x] Zabbix 7.0 LTS (PostgreSQL, retenção curta, descarte de valores repetidos)
- [x] Firewall do Proxmox em todos os containers
- [x] Migrar discos de Zabbix, NetBox e GLPI para SSD dedicado
- [x] Sincronização NetBox → Zabbix (hosts a partir do inventário, por tag)
- [ ] Reduzir permissões das contas de integração
- [x] Zabbix → GLPI (abertura e solução automática de chamados)
- [x] Zabbix, NetBox e GLPI publicados no proxy (Access List da empresa, APIs bloqueadas, MFA)
- [x] Porta e community SNMP por equipamento definidas no NetBox (config context)
- [ ] Todo o backbone (~20 equipamentos) sincronizado do NetBox para o Zabbix
- [ ] Revogar tokens usados na configuração e HTTPS interno no GLPI
- [ ] Migrar a integração para a API nova do GLPI (OAuth)
- [ ] Agente de IA (OpenClaw) em VM isolada, com tokens somente leitura
- [ ] Coleta automática das configurações para este repositório
- [ ] Avaliar SNMPv3 nos equipamentos principais

## Próximo passo

1. **Fechar o monitoramento:** config context global aplicado a todos, exceções de porta/community no NetBox, restante do backbone com a tag `zabbix`.
2. **Agente OpenClaw** em VM isolada, com tokens somente leitura, começando por resumir problemas do Zabbix e chamados do GLPI.
