# GLPI em Docker (LXC não privilegiado)

- `url_base` ajustada após a migração (Configurar → Geral, ou tabela `glpi_configs`), com dump do banco antes.
- Cache com datas erradas vindo do servidor antigo: apagar o conteúdo de `files/_cache` e reiniciar o `glpi-app`.
- Tarefas automáticas em modo **CLI** (o modo "GLPI" só roda quando alguém acessa a interface).
- Firewall interno na `DOCKER-USER`: [`firewall-docker-glpi.sh`](firewall-docker-glpi.sh) + [`glpi-docker-firewall.service`](glpi-docker-firewall.service).

## GLPI-Agent nos PCs do domínio

Distribuição pelo Active Directory (10/11/2026):
- **GPO com script de inicialização** (roda como SYSTEM), vinculada ao domínio; o script fica no SYSVOL.
- Política de execução do domínio em **`RemoteSigned`** → o script precisa estar **assinado** com um certificado de Assinatura de Código da CA interna. Qualquer edição invalida a assinatura: salvar em UTF-8 com BOM e assinar de novo.
- MSI baixado de um **compartilhamento interno primeiro** (GitHub como alternativa) e conferido por **SHA-256**.
- Configuração do agente (`agent.cfg`, sem BOM) só é regravada — e o serviço só reinicia — quando algo mudou.
- Servidor apontando para a **raiz** do domínio publicado (GLPI 10+ aceita o inventário nativo ali), com **validação SSL ativa**.
- Logs no PC: `C:\Windows\Temp\glpi-agent-install.log` e `glpi-agent-msi.log`.
