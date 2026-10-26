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
