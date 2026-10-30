# Lições aprendidas

Problemas reais encontrados na montagem e como foram resolvidos.

| Contexto | Sintoma | Causa | Solução |
|---|---|---|---|
| Firewall do Proxmox | `invalid format - not a valid IP or CIDR: 10.0.0.1/24` | IP do gateway usado como rede | Usar o endereço de rede: `10.0.0.0/24` |
| Firewall do Proxmox | Regra ACCEPT nunca casava | Porta de **origem** preenchida | Só porta de destino |
| Usuário PAM | `change password failed: user does not exist` | Usuário criado só na GUI | Criar também no Linux (`useradd`) |
| Driver NVIDIA | Módulo não carrega com Secure Boot | Módulo sem assinatura | Chave MOK do DKMS + registro presencial no boot |
| Shell | `bash: <GW>: No such file or directory` | `<` e `>` são redirecionamento | Substituir marcadores pelos valores reais |
| Ollama em LXC | `requires zstd for extraction` | Template mínimo | `apt install zstd` |
| Ollama em LXC | `Unable to detect NVIDIA GPU` no instalador | Sem `lspci` | Ignorar: a GPU é detectada pelo serviço |
| Oracle Cloud | Sub-rede fora do CIDR da VCN | VCN padrão `10.0.0.0/16` colidia com a rede local | VCN/sub-rede `10.0.20.0/24` |
| Oracle Cloud | Portas fechadas mesmo com Security List aberta | Regras do iptables inseridas **depois** do REJECT | Inserir antes do REJECT |
| VS Code Remote-SSH | Falha de conexão | `IdentityFile` apontando para a chave **pública** | Usar a chave privada + `IdentitiesOnly yes` |
| WireGuard | Sem handshake; pacotes chegando a cada ~6 s | Chave pública copiada da interface errada | Conferir a chave da interface certa |
| Docker + NPM | Container falhava no boot | Porta publicada no IP do túnel antes do `wg0` existir | Docker com `After=wg-quick@wg0.service` |
| Restore de LXC | `Cannot mknod: Operation not permitted` | Arquivos de dispositivo em CT não privilegiado | `--ignore-unpack-errors 1` |
| Restore de LXC | Container herdou `apparmor unconfined` e privilégios | Configuração do servidor antigo | Restaurar como não privilegiado e remover `lxc.*` |
| GLPI em Docker | Acessível só em `127.0.0.1` | Regras `DOCKER-USER` do proxy antigo | Liberar as redes de administração |
| NetBox em Docker | `netbox-housekeeping` reiniciando (127) | Serviço legado removido nas versões novas | Desativar via `profiles: ["disabled"]` |
| Zabbix | Host travando | Escrita contínua do banco no SSD do sistema | Banco em disco dedicado |
| `pct create` | `volume 'local:vztmpl/...' does not exist` | Template salvo em outro storage | `pveam list <storage>` e usar o volid correto |
| `pct create` | Disco criado mesmo com erro | O disco é formatado antes de validar o template | Apagar o disco órfão antes de tentar de novo |
| Zabbix 8.0 | Instalaria uma *release candidate* | Pacote do repositório ativa o canal unstable | Usar o 7.0 LTS |
| Zabbix 7.0 | Schema não importado | Caminho mudou para `/usr/share/zabbix-sql-scripts/` | Caminho correto |
| Containers restaurados | Acesso aberto para toda a rede | Firewall do Proxmox não estava habilitado nos CTs | `/etc/pve/firewall/<ID>.fw` com política DROP |
| NetBox 4.5+ (token v2) | `403 Source IP ::ffff:x.x.x.x is not permitted` | IPs permitidos só em IPv4; o NetBox vê o cliente como IPv4 mapeado em IPv6 | Acrescentar `::ffff:<ip>/128` |
| netbox-zabbix-sync | Sincronização pularia todos os hosts | Usuário do Zabbix sem visão de templates/grupos | Role com permissão suficiente (Super admin no início) |
| netbox-zabbix-sync | Host com community/porta diferente perde o ajuste | A ferramenta sobrescreve a interface (e, com `usermacro_sync`, as macros) a cada execução | Porta e community no *local config context* do device no NetBox |
| netbox-zabbix-sync | `Multiple interfaces of the same type ... manual intervention required` | Segunda interface SNMP criada à mão no host | Deixar uma única interface SNMP |
| netbox-zabbix-sync 4.1.0 | Macro secreta chega ao Zabbix com valor `********` | `sanatize_log_output` mascara o log com cópia **rasa** e altera os dados enviados | Patch com `copy.deepcopy` (reaplicar após atualizar) |
| netbox-zabbix-sync | `interface_port` do config context ignorado; interface volta para 161 | A porta só é lida junto com `interface_type`, e o config context global não estava sendo aplicado ao device | `interface_type: 2` também no local context; conferir *Dados renderizados* |
| SNMP Huawei | Timeout com ping ok | Community diferente da macro | Ajustar a community |
| GLPI 11 | "Adicionar cliente da API" não aparece | Clientes de API pertencem à REST **legada**, desativada por padrão | Habilitar a REST API legada |
| Zabbix → GLPI | Media type oficial deixava sessões abertas | Não chamava `killSession` | Webhook adaptado com `killSession` em `finally` |
| Zabbix → GLPI | Robô deixaria de receber alertas de grupos novos | Permissão por grupo não cobre grupos criados depois | Papel tipo Super admin sem interface e sem API |
| Zabbix | Problema iniciado em manutenção nunca abriria chamado | Condição "não suprimido" é avaliada só na criação | Usar só "pausar operações de problemas suprimidos" |
| Firewall do Proxmox | `no such ipset` no `pve-firewall compile` — e mesmo assim imprime OK | Nome do IPSet na regra diferente do criado (hífen × sublinhado); a regra inválida é **descartada em silêncio** | Usar o nome exato; sempre ler a saída do `compile`, não só o OK |
| Nginx Proxy Manager | Serviço com Access List abria de qualquer IP | `.conf` gerado com `satisfy all` mas sem `allow`/`deny` (lista não regenerada) | Salvar a lista de novo e reaplicar no host; conferir com `grep allow` no `.conf` |
| NetBox atrás do proxy | Formulários com listas de seleção vazias | `location /api/ { deny all; }` — a interface usa a API pela sessão | Não bloquear `/api/` no NetBox; proteger por Access List + tokens com IP |
| Discos no Proxmox | `sdX` diferente depois de instalar outro disco | Nomes do kernel não são fixos | Usar `/dev/disk/by-id/...` em qualquer comando destrutivo |
| Ordem de boot | Sync falha com `No route to host` após reiniciar | Zabbix sobe antes do NetBox | `--startup order=` (NetBox/GLPI antes do Zabbix) |
| Zabbix MFA | Sem acesso após apagar o TOTP do app | Segredo continua no banco | `DELETE FROM mfa_totp_secret` do usuário → QR novo no login |
| Zabbix | Todos os equipamentos "Unavailable by ICMP ping" de uma vez | NAT do IP público do servidor removido; equipamentos só respondem a esse IP | Manter NAT para o Zabbix (dependência documentada) |
| Zabbix API | Função "somente leitura" liberava tudo menos leitura | Métodos na **Lista de negação** em vez da **Lista de permissões** | Lista de permissões; testar com `user.get` (deve negar) |
| Shell | `read -rsp "<token>" T` → "Not authorized" | O texto do `-p` é só o prompt; o `read` engoliu a linha seguinte colada | Rodar o `read` sozinho e colar o valor no prompt |
| zabbix-mcp | `Missing required Zabbix URL` com `.env` na pasta | O `.env` não é lido do diretório de trabalho | Script que carrega o `.env` e faz `exec` do servidor |
| OpenClaw + modelo local | Agente diz que "não tem ferramenta"; log `Unknown tool id: tool_search` | Busca de ferramentas automática para Ollama; modelo pequeno erra a chamada | `tools.toolSearch: false` e poucas ferramentas expostas |
| OpenClaw | Modelo descreve ferramentas de shell que não tem | Alucinação sobre as próprias capacidades | Validar por config e log, nunca pela resposta |
| NetBox (token) | "Item 2 na lista não validou" em IPs permitidos | Espaço depois da vírgula | `10.0.10.9/32,::ffff:10.0.10.9/128` sem espaço |
| NetBox + agente | Permissão sem clientes, mas histórico liberado | O histórico de mudanças copia dados de qualquer objeto | Não liberar `Object change` nem o `get_changelogs` |
| Firewall do Proxmox | VM sem acesso, `compile` com "unable to parse rule parameters: ]" | Caractere colado no fim da regra | Ler todas as linhas do `compile`, não só o OK |
| GLPI API | `ERROR_NOT_ALLOWED_IP` com a rede ok | Falta cliente de API ativo para o IP de origem | Cliente de API com a faixa do IP |
| `.env` lido pelo shell | `Syntax error: "(" unexpected` | Regex com parênteses sem aspas | Valor entre aspas simples |
| npm | "14 vulnerabilidades" ao instalar | Contagem inclui dependências de desenvolvimento | `npm audit --omit=dev`; `npm ci --ignore-scripts` |
| Shell | `Permission denied` ao "abrir" arquivo | Digitar o caminho tenta **executar** o arquivo | `nano <arquivo>` ou `code <arquivo>` |
| Zabbix → GLPI | `Parameter "glpi_app_token" is an unresolved macro` | Macro global `{$GLPI.APP_TOKEN}` apagada ao editar as macros SNMP | Recriar como texto secreto; `zabbix_server -R config_cache_reload`; conferir as duas `{$GLPI.*}` após editar macros globais |
| GLPI API (agente) | "No tickets found" com chamado aberto | Usuário da API fora do grupo NOC; o perfil só mostra chamados do grupo | Incluir o usuário no grupo; testar com um chamado real, não com lista vazia |
