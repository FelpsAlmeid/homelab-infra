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
- [ ] Migrar discos de Zabbix, NetBox e GLPI para SSD dedicado
- [x] Sincronização NetBox → Zabbix (hosts a partir do inventário, por tag)
- [ ] Reduzir permissões das contas de integração
- [x] Zabbix → GLPI (abertura e solução automática de chamados)
- [ ] Migrar a integração para a API nova do GLPI (OAuth)
- [ ] Agente de IA (OpenClaw) em VM isolada, com tokens somente leitura
- [ ] Coleta automática das configurações para este repositório
