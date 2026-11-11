# Roadmap

Separado por sistema. Cada seção tem o que já foi feito e o que falta.

## Projeto principal (homelab + IA para o NOC)

- [x] Base de IA local: Ollama na GPU + Open WebUI
- [x] Serviços de NOC no laboratório: NetBox (IPAM), GLPI (chamados), Zabbix (monitoramento)
- [x] Integrações NetBox → Zabbix e Zabbix → GLPI
- [x] Publicação segura dos serviços (proxy na nuvem, sem portas abertas na rede local)
- [ ] **Fechar o monitoramento** do backbone (ver [Zabbix](#zabbix))
- [ ] **Agente de IA (OpenClaw) em VM isolada**, com snapshot antes de cada skill e tokens **somente leitura** ([guia](../servicos/openclaw/README.md))
  - [x] VM com firewall de saída fechado, usuário sem sudo, Docker rootless, gateway em loopback, token como SecretRef
  - [x] Modelo local (gemma4:12b, 32K) respondendo pela API nativa do Ollama
  - [x] Sandbox `all` (sem rede, raiz somente leitura, sem root), ferramentas de shell/arquivos/web negadas, `security audit` sem críticos
  - [x] Zabbix somente leitura: função com lista de permissões (11 métodos `.get`), MCP `zabbix-mcp` em modo leitura com 8 ferramentas expostas, firewall só VM → Zabbix
  - [x] Instruções do agente para o papel de N2 (PT-BR, só diagnóstico, sem comandos de CLI)
  - [x] NetBox somente leitura (MCP oficial, sem clientes e sem histórico)
  - [x] GLPI somente leitura (só chamados do grupo NOC)
  - [x] Teste com chamado real (Zabbix → GLPI → agente): alerta ICMP abriu o chamado #4 e o agente o encontrou
  - [x] Primeiro caso de uso N2: resumir problemas ativos do Zabbix e chamados abertos no GLPI — **via workflow do n8n** (03/11): só com instruções o modelo pulava etapas e errava dados; com a ferramenta `noc_resumo`, 1 chamada e dados exatos
  - [x] Nome do host nas respostas do Zabbix (validado em 03/11 com host de teste: nome + chamado do GLPI)
  - [x] Snapshot `integracoes-funcionando`
  - [x] Painel pela VPN sem túnel SSH (03/11): Caddy HTTPS na VM, gateway ainda em loopback, `trustedProxies` + `allowedOrigins`, 443 liberada só para o notebook
  - [x] **Canal Discord da equipe** (03/11): plugin oficial na mesma versão do núcleo, só o canal do agente, só cargo NOC, só com menção, DM desligada, token como SecretRef; 15 → 5 plugins carregados ([guia](../servicos/openclaw/README.md#canal-discord-da-equipe), [servidor](../servicos/discord/README.md))
  - [ ] Resumo em horário fixo no canal de resumo (agendamento do próprio agente + `noc_resumo`)
  - [ ] Regras do canal compartilhado (sem credenciais/community, alerta de impacto em equipamento de núcleo) — validar em sessão nova
  - [ ] Testar mensagem direta ao bot (deve ser ignorada)
  - [ ] Manter o plugin Discord na mesma versão do núcleo a cada atualização; revisar se o plugin `canvas` é necessário
  - [ ] Apagar snapshots antigos da VM (thin pool `local-lvm` superalocado), incluindo o de antes do MCP do n8n
  - [ ] Limpeza pós-MCP do n8n: drop-in com `NODE_EXTRA_CA_CERTS` e linha do `.bashrc` (o `run.sh` já define a CA) e regra de saída redundante no firewall da VM
  - [ ] Revisar os avisos do update 2026.10.10 (`openclaw update cleanup --dry-run`, busca de memória sem provider) sem rodar `doctor --fix`
- [x] ~~Acesso da equipe ao Open WebUI~~ — **Open WebUI dispensado (30/10)**: o agente OpenClaw é a interface de IA; equipe acessará por canal de mensagens do agente
- [x] **n8n como orquestrador** (CT 108, [guia](../servicos/n8n/README.md)): consultas determinísticas expostas ao agente por MCP, tokens próprios fora da VM do agente
- [ ] Expandir o agente além da leitura (ações com aprovação humana, tokens de escrita mínimos e separados, registro de cada ação)
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
- [x] `intel-microcode` e fuso horário (America/Fortaleza)
- [x] Serviços de HA desativados (nó único)
- [x] TFA (TOTP) e chaves de recuperação no usuário administrador
- [x] Firewall do host: 8006/22 só para `redes-admin` (rede local automática do Proxmox contida na gerência)
- [x] Jobs de backup: diário (CTs 101, 104–106, 108 n8n + VM 107 OpenClaw) e semanal (Ollama) no HD, com retenção e repetir perdidos
- [x] Cópia semanal criptografada para o Google Drive (conta dedicada, `drive.file` + `crypt`)
- [x] Versão nova do `backup-offsite.sh` (envio único, CTs + VMs) instalada e validada: 23,8 GiB a ~16,7 MiB/s (29/10)
- [x] Teste de restauração a partir do Drive: CT 103 baixado, `zstd -t` ok, restaurado como 903 sem rede, Open WebUI subiu (30/10)
- [ ] Repetir o teste de restauração periodicamente (ex.: a cada 3 meses, alternando o CT)
- [x] Limpeza do HD antigo (backups e ISOs do servidor anterior)

## Segundo host Proxmox (POP) — planejado (10/11)

Host 24/7 (i7 10ª geração, 32 GB, RX 580) no POP principal do provedor; única carga fixa é uma VM com OBS (transmissão), o resto fica livre para o projeto.
- [x] Desenho de rede: host na DMZ do roteador de borda (/30, sem VLAN, IP direto na porta), guests numa faixa própria, WireGuard em container próprio com NAT para o proxy na Oracle
- [ ] Instalar com o novo endereçamento e firewall no mesmo padrão (DROP + `redes-admin`)
- [ ] WireGuard + regras de acesso no roteador de borda
- [ ] VM do OBS · backup (local + cópia criptografada no Drive)
- [ ] Definir quais serviços do projeto rodam neste host

## Rede dos containers (saída para a internet)

- Decisão: **só o Zabbix tem saída permanente** (ICMP/SNMP do backbone pelo NAT do IP público — os equipamentos só aceitam esse IP); os demais saem **apenas para atualizar** (apt, imagens Docker, modelos, npm/uv)
- [ ] Aplicar o padrão nos CTs 101–106 (`policy_out: DROP` + DNS/NTP/HTTP/HTTPS só quando atualizar; regras internas já existentes)
- [ ] Zabbix: saída própria para ICMP e SNMP (UDP 161 + portas específicas por equipamento)
- [ ] DNS dos CTs no MikroTik (gateway da VLAN) em vez de resolvedor externo

## Zabbix

- [x] Zabbix 7.0 LTS com PostgreSQL ajustado para pouca escrita, em SSD dedicado
- [x] Communities como macros secretas
- [x] Publicado no proxy (Access List, `/api_jsonrpc.php` bloqueado) com MFA
- [x] Porta e community SNMP por equipamento vindas do NetBox (config context)
- [x] Config context global aplicado a **todos** os devices com a tag `zabbix` (`zabbix-padrao-icmp`, 30/10)
- [x] Equipamentos já sincronizados com SNMP ok (local context em cada um)
- [ ] Restante do backbone (~20 equipamentos) com a tag `zabbix`
- [ ] Testar `bulk: 1` no equipamento atrás de NAT (manter `0` se der timeout)
- [x] ~~Template para o modelo NetEngine 8000~~ — template vem do config context (30/10)
- [ ] Role própria para a conta do sync (sair do Super admin)
- [ ] Avaliar SNMPv3 nos equipamentos principais

**Expansão para ~450 dispositivos do provedor (~50 SNMP, ~400 ICMP)** — cadastro pelo NetBox, entrada no Zabbix pelo sync
- [x] Template **padrão = ICMP Ping** para todo device com a tag `zabbix`; SNMP e templates específicos só por exceção no **contexto local** (`templates_config_context` + `overrule`, 30/10)
- [ ] Importação em massa por CSV no NetBox
- [ ] Dependências de triggers (equipamento atrás de POP/concentrador não alerta se o pai cair) e severidade por função, para não abrir dezenas de chamados no GLPI numa queda
- [x] CT 104 dimensionado (30/10): 4 núcleos, 6 GB, 80 GB; `StartPingers=5` e caches em `zabbix_server.d/90-escala.conf`; PostgreSQL `shared_buffers` 1 GB
- [ ] Decidir sobre a disponibilidade: o servidor é um PC com dual boot (no Windows = NOC sem monitoramento)
- [x] Inventário do host vindo do NetBox (coordenadas, site, fabricante, modelo, serial) + widget **Geomap** (03–04/11)
- [x] Coordenada **do site** herdada pelos devices (04/11)
- [ ] Coordenadas em todos os sites (POPs/torres) e cadastro dos devices (manual, em andamento)
- [ ] Topologia pai/filho não documentada → Network Map e dependências ficam para quando houver conexões no NetBox

**Novos serviços (depois)**
- [ ] Grafana (CT leve, plugin do Zabbix com usuário somente leitura, publicado no proxy) — **planejado (04/11)**
  - [x] Decidido: dashboards do NOC no Grafana — o Zabbix 7.0 não importa dashboard global pela interface (só no 8.0)
  - [ ] Validar o desenho (LXC leve: 2 vCPU, 1 GB, SSD de dados) dentro dos limites de RAM do host
  - [ ] Usuário de API próprio no Zabbix (lista de permissões só `.get`) + firewall
  - [ ] Instalação (apt) + plugin do Zabbix; dashboards Visão NOC, ICMP, backbone SNMP e por POP, com JSON versionado aqui
  - [ ] Backup e publicação no proxy com Access List
- [ ] Serviços pessoais (TeamSpeak/CS2) em VLAN separada, fora da documentação da empresa

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
- [x] **GLPI-Agent nos PCs do domínio** (10/11): GPO com script de inicialização assinado (política `RemoteSigned`), MSI com hash conferido e fonte interna primeiro, SSL validado no domínio público ([guia](../servicos/glpi/README.md#glpi-agent-nos-pcs-do-domínio))
- [ ] Conferir a chegada dos PCs no inventário
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
- [x] Reteste em 29/10 após recriar a macro global `{$GLPI.APP_TOKEN}` apagada por engano
- [ ] Revogar o token de API usado na configuração e limpar o arquivo de segredos temporário
- [ ] Migrar para a API nova do GLPI (OAuth) antes da remoção da legada

## Proxy (Oracle Cloud + NPM)

- [x] Instância ARM, IP reservado, firewall em duas camadas
- [x] Túnel WireGuard dedicado até o MikroTik; painel do NPM só pela VPN
- [x] Zabbix, NetBox e GLPI só para os IPs da empresa (Open WebUI público até 30/10 — host do proxy desativado)
- [ ] SSH pela VPN e remover a regra pública da porta 22

## IA (Ollama)

- [x] Ollama em LXC não privilegiado com a GPU
- [x] ~~Open WebUI publicado com HTTPS~~ → desativado em 30/10 (CT 103 parado, fora do backup e do proxy; apagar na Consolidação)
- [x] RAM do CT 102 conferida (30/10): 8 GB, modelo 100% na GPU, uso real ~2 GB

## n8n (orquestração do NOC)

- [x] CT 108 não privilegiado com Docker, Caddy `tls internal`, firewall IN/OUT fechado (03/11)
- [x] Saída para a internet só durante instalação/atualização (exceção 03/11: IXC e API do Discord, só 443, para a verificação de CTOs)
- [x] Tokens próprios somente leitura (Zabbix, NetBox com IP, GLPI com cliente de API + grupo NOC), escrita negada nos três
- [x] Workflow `noc_resumo` + `mcp_noc` (MCP Server Trigger com Bearer) ligados ao OpenClaw
- [x] Backup diário + cópia semanal no Drive
- [x] Checagem semanal de versão e avisos de segurança → Zabbix; script de atualização com snapshot
- [ ] Tokens diretos de Zabbix/NetBox/GLPI na VM do agente: **mantidos por enquanto** (detalhe de host); revisar na Consolidação
- [x] **Verificação de CTOs** (IXC → Postgres → Discord, [guia](../servicos/n8n/verificacao-ctos/README.md), 03/11): mapa cliente → CTO → PON, alerta de PON (≥ 5 e ≥ 30%) antes do de CTO (≥ 2 e ≥ 60%), mensagem única editada (novo → agravado → normalizado), testado em produção
- [ ] Verificação de CTOs: conferir publicação dos 4 fluxos; calibrar limites com alertas reais; título "normalizada"
- [ ] Ferramenta MCP `cto_alerta` para o agente responder sobre os alertas
- [ ] Relatórios de cadastro (fibra sem ONU, ONUs de clientes inativos ocupando porta, CTOs sem coordenada) · aviso de falha dos fluxos pelo Zabbix · limpeza periódica da tabela `quedas`
- [ ] Alertas de rádio
- [ ] Importar a CA do Caddy do n8n no notebook de administração
- [ ] Segunda ferramenta: detalhe de um host
- [ ] Fluxos de escrita com aprovação humana

## Consolidação (final do projeto)

Rodada de testes de segurança e de uso no dia a dia, antes de considerar o projeto concluído.

**Segurança**
- [ ] Varredura de portas de fora (4G) e de dentro (VLAN 1010): só o esperado aberto
- [ ] Revisão de firewall (Proxmox `.fw`, `DOCKER-USER`, Access Lists do NPM) contra a documentação
- [ ] Revisão de tokens e usuários de API: permissões mínimas, IP restrito, rotação dos antigos
- [ ] Teste do agente OpenClaw contra *prompt injection* (texto malicioso em chamado/descrição do NetBox) e tentativa de escrita
- [ ] Cabeçalhos HTTPS, TLS e MFA dos serviços publicados
- [ ] Atualizações pendentes e avisos de segurança (Proxmox, CTs, VM, Docker)
- [ ] Restauração completa simulada (servidor perdido, só Drive + Kaspersky)

**Uso no dia a dia**
- [ ] Rotina do NOC usando os sistemas por uma semana e anotar atritos
- [ ] Alertas: ruído, falsos positivos, chamados duplicados
- [ ] Acessos da equipe (canal do agente, Grafana) com contas próprias
- [ ] Documentação final revisada (README, roadmap, segundo cérebro)

## Próximo passo

1. **Zabbix em escala (~450 dispositivos):** dependências/severidades, filtro de interfaces no LLD e importação CSV no NetBox (ICMP padrão e dimensionamento do CT 104 concluídos em 30/10).
2. Política de saída dos containers (egress) — o Zabbix vai precisar alcançar as novas redes.
3. ~~Primeiro caso de uso N2~~ (feito via n8n, 03/11) · ~~canal Discord~~ (03/11); ~~alertas de fibra no Discord~~ (03/11, direto pelo n8n); próximo no agente: resumo em horário fixo no canal e a ferramenta `cto_alerta`.
4. Grafana; depois serviços pessoais em VLAN separada.
5. Consolidação: testes de segurança e de uso.
