# GLPI em Docker (LXC não privilegiado)

- `url_base` ajustada após a migração (Configurar → Geral, ou tabela `glpi_configs`), com dump do banco antes.
- Cache com datas erradas vindo do servidor antigo: apagar o conteúdo de `files/_cache` e reiniciar o `glpi-app`.
- Tarefas automáticas em modo **CLI** (o modo "GLPI" só roda quando alguém acessa a interface).
- Firewall interno na `DOCKER-USER`: [`firewall-docker-glpi.sh`](firewall-docker-glpi.sh) + [`glpi-docker-firewall.service`](glpi-docker-firewall.service).
