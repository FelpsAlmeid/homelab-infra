# Arquitetura

## Endereçamento

| Rede | Faixa | Uso |
|---|---|---|
| VLAN 1050 — gerência | `10.0.0.0/28` (host `10.0.0.2`, gw `10.0.0.1`) | Interface de gerência do Proxmox |
| VLAN 1010 — serviços | `10.0.10.0/24` (gw `10.0.10.1`) | Containers e VMs |
| VPN de administração | `10.0.212.0/24` | Notebook e acessos administrativos |
| Túnel do proxy | `10.0.213.0/30` | Oracle (`.1`) ↔ MikroTik (`.2`) |
| VCN da Oracle | `10.0.20.0/24` | Sub-rede da instância na nuvem (reservada) |

## Containers

| ID | Serviço | Tipo | Disco | Observação |
|---|---|---|---|---|
| 101 | Samba | LXC não privilegiado | bind mount de uma partição do HD | Compartilhamento de arquivos |
| 102 | Ollama | LXC não privilegiado + GPU | NVMe | API interna, sem autenticação → firewall restrito |
| 103 | Open WebUI | LXC não privilegiado | NVMe | Interface de chat, publicada via proxy |
| 104 | Zabbix | LXC | SSD dedicado | Banco isolado do disco do sistema |
| 105 | NetBox | LXC não privilegiado (Docker) | SSD dedicado | IPAM / inventário |
| 106 | GLPI | LXC não privilegiado (Docker) | SSD dedicado | Chamados |

## Decisões

- **Bridge VLAN-aware única (`vmbr0`)** com a tag definida em cada placa de rede dos guests: uma porta trunk no switch atende todas as VLANs.
- **LXC em vez de VM** sempre que possível: menos overhead; VM só para o que executa código não confiável (o agente de IA).
- **GPU compartilhada por LXC** (driver no host, só userspace no container) em vez de passthrough para uma VM: o host mantém a saída de vídeo e vários containers podem usar a GPU.
- **Proxy na nuvem + túnel iniciado pelo roteador:** nenhuma porta aberta na rede local; funciona mesmo atrás de CGNAT.
- **Túnel dedicado para o proxy**, separado da VPN de administração: o proxy é exposto à internet e não pode ter acesso administrativo.
- **Banco do monitoramento em disco dedicado:** escrita contínua do Zabbix chegou a travar o host quando dividia o SSD do sistema.
