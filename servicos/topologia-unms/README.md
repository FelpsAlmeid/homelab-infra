# Levantamento de topologia pelo UNMS

Gera a planilha de revisão do campo `uplink` (pai de cada equipamento) no NetBox, usado depois nas dependências de triggers do Zabbix.

- **Somente leitura**: só `GET /devices` e `GET /data-links` na API do UNMS (v2.1)
- Vínculos: *data links* do UNMS (ethernet/wireless) + `attributes.apDevice` (estação → AP)
- Topologia em árvore (um uplink por equipamento); o UNMS não conhece o POP/BNG, então cada **ramo** recebe uma raiz informada à mão
- Devices em site de cliente (`endpoint`) ficam fora; switch sem IP fica na árvore e é marcado (o script de dependências atravessa até o ancestral monitorado)

## Uso

```bash
mkdir -p /root/topologia && cd /root/topologia
curl -fsSLO https://raw.githubusercontent.com/FelpsAlmeid/homelab-infra/main/servicos/topologia-unms/topologia_unms.py
export UNMS_URL=https://<unms>/nms/api/v2.1
read -rs UNMS_TOKEN && export UNMS_TOKEN     # colar o token (usuário Guest) e Enter
python3 topologia_unms.py coletar           # unms-devices.json, unms-data-links.json
python3 topologia_unms.py ramos             # ramos.csv
nano manter.txt                             # (opcional) regex dos padrões de nome de infraestrutura (o resto sai)
nano ignorar.txt                            # (opcional) regex de nomes a descartar: bancada, teste
nano pops.txt                                # sites de entrada (POP ou que recebem de POP fora do UNMS): "SITE" ou "SITE;POP de origem"
nano sites-pai.txt                           # "SITE;SITE PAI" para cada site de sites-sem-ramo.csv
nano raizes.txt                             # (opcional) nome ou IP de entrada de ramo que não passa por POP
python3 topologia_unms.py arvore            # topologia-revisao.csv
```

| Coluna | Uso |
|---|---|
| `ramo`, `nivel` | Ramo (a partir de qual raiz) e distância até ela |
| `uplink_sugerido`, `uplink_ip` | Pai calculado |
| `origem_vinculo` | `data-link wireless`, `data-link ethernet` ou `apDevice` |
| `observacao` | Raiz (informar o uplink no POP/BNG), sem ramo, sem IP |
| `uplink_confirmado` | Preenchido na revisão |

Os JSON e CSV gerados têm IPs e nomes internos: **não versionar**.
