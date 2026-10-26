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
| netbox-zabbix-sync | Host com community diferente perde o ajuste | A ferramenta sobrescreve a interface a cada execução | Community por macro no host |
| SNMP Huawei | Timeout com ping ok | Community diferente da macro | Ajustar a community |

