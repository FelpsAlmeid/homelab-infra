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
  - [ ] Primeiro caso de uso N2: resumir problemas ativos do Zabbix e chamados abertos no GLPI
  - [ ] Mostrar o nome do host nas respostas do Zabbix — regra aplicada no AGENTS.md; **validar no próximo problema ativo**
  - [x] Snapshot `integracoes-funcionando`
- [x] ~~Acesso da equipe ao Open WebUI~~ — **Open WebUI dispensado (30/10)**: o agente OpenClaw é a interface de IA; equipe acessará por canal de mensagens do agente
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
- [x] Jobs de backup: diário (5 CTs + VM 107 OpenClaw) e semanal (Ollama) no HD, com retenção e repetir perdidos
- [x] Cópia semanal criptografada para o Google Drive (conta dedicada, `drive.file` + `crypt`)
- [x] Versão nova do `backup-offsite.sh` (envio único, CTs + VMs) instalada e validada: 23,8 GiB a ~16,7 MiB/s (29/10)
- [x] Teste de restauração a partir do Drive: CT 103 baixado, `zstd -t` ok, restaurado como 903 sem rede, Open WebUI subiu (30/10)
- [ ] Repetir o teste de restauração periodicamente (ex.: a cada 3 meses, alternando o CT)
- [x] Limpeza do HD antigo (backups e ISOs do servidor anterior)

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
- [ ] Config context global aplicado a **todos** os devices com a tag `zabbix`
- [x] Equipamentos já sincronizados com SNMP ok (local context em cada um)
- [ ] Restante do backbone (~20 equipamentos) com a tag `zabbix`
- [ ] Testar `bulk: 1` no equipamento atrás de NAT (manter `0` se der timeout)
- [ ] Template para o modelo NetEngine 8000 (se for monitorado)
- [ ] Role própria para a conta do sync (sair do Super admin)
- [ ] Avaliar SNMPv3 nos equipamentos principais

**Expansão para ~450 dispositivos do provedor (~50 SNMP, ~400 ICMP)** — cadastro pelo NetBox, entrada no Zabbix pelo sync
- [ ] Template **padrão = ICMP Ping** para todo device com a tag `zabbix`; SNMP e templates específicos só por exceção, informados no NetBox (tipo/contexto local)
- [ ] Importação em massa por CSV no NetBox
- [ ] Dependências de triggers (equipamento atrás de POP/concentrador não alerta se o pai cair) e severidade por função, para não abrir dezenas de chamados no GLPI numa queda
- [ ] Dimensionar o CT 104 (`StartPingers`, pollers SNMP assíncronos, CPU/RAM/disco, retenção do histórico)
- [ ] Decidir sobre a disponibilidade: o servidor é um PC com dual boot (no Windows = NOC sem monitoramento)

**Novos serviços (depois)**
- [ ] Grafana (CT leve, plugin do Zabbix com usuário somente leitura, publicado no proxy)
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
- [ ] Ajustar a RAM do CT 102 conforme o `ollama ps` (100% GPU → 8 GB)

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

1. **Zabbix em escala (~450 dispositivos):** contexto global com ICMP padrão, dependências/severidades, dimensionamento do CT 104 e importação CSV no NetBox.
2. Política de saída dos containers (egress) — o Zabbix vai precisar alcançar as novas redes.
3. Primeiro caso de uso N2 e validação do nome do host nas respostas (com os alertas reais).
4. Grafana; depois serviços pessoais em VLAN separada.
5. Consolidação: testes de segurança e de uso.
