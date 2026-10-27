# Sincronização NetBox → Zabbix

O NetBox é a fonte da verdade: os equipamentos marcados com a tag `zabbix` viram hosts no Zabbix automaticamente, com grupo e template definidos pelo próprio NetBox.

Ferramenta: [netbox-zabbix-sync](https://github.com/TheNetworkGuy/netbox-zabbix-sync) (4.1.0), em virtualenv no container do Zabbix, rodando por um systemd timer a cada 15 minutos.

## Fluxo

```mermaid
flowchart LR
    NB["NetBox<br/>tag zabbix + Active + IP primário"] -->|a cada 15 min| S[netbox-zabbix-sync]
    S -->|cria/atualiza host<br/>grupo site/role<br/>template do tipo| Z[Zabbix]
    S -->|grava zabbix_hostid| NB
```

## Preparação no NetBox

| Objeto | Campo | Uso |
|---|---|---|
| Device | `zabbix_hostid` (Integer) | ID do host no Zabbix, gravado pela ferramenta |
| Device type | `zabbix_template` (Text, padrão `Mikrotik by SNMP`) | Template aplicado aos dispositivos daquele tipo |
| Tag | `zabbix` | Seleciona o que é monitorado |

## Configuração (resumo de `config.py`)

- Filtro: tag `zabbix`, status ativo, com IP primário
- Grupos de hosts: `site/role` (ex.: `POP Centro/Concentrador`)
- Template: campo `zabbix_template` do tipo de dispositivo
- Interface SNMP definida por **config context** no NetBox (veja abaixo); community pela macro `{$SNMP_COMMUNITY}`
- `usermacro_sync = "full"`: macros do host vêm do NetBox (inclusive secretas)
- Tokens em `/etc/netbox-zabbix-sync/sync.env` (permissão 600), carregado pelo systemd

## Porta e community por equipamento (config context)

Nem todos os equipamentos usam a porta 161 nem a mesma community. Editar a interface no Zabbix não adianta (o sync sobrescreve), então tudo fica no NetBox:

| Camada no NetBox | Arquivo | Uso |
|---|---|---|
| Config context global (tag `zabbix`, peso 1000) | [`zabbix-snmp-padrao.json`](config-context/zabbix-snmp-padrao.json) | Interface SNMP v2, porta 161, community `{$SNMP_COMMUNITY}` (global) |
| *Local config context* do device | [`device-local.example.json`](config-context/device-local.example.json) | Só as exceções: `interface_port` e/ou macro `{$SNMP_COMMUNITY}` secreta |

O NetBox mescla as duas camadas (o local prevalece). No Zabbix a interface continua com `{$SNMP_COMMUNITY}`; o valor vem da macro do host (prioridade: host → template → global).

Detalhes da versão 4.1.0 (lidos no código):
- `interface_port` só é lido se `interface_type` existir no context — por isso o global declara a interface completa.
- Com `interface_type: 2` o bloco `snmp` com `version` é obrigatório.
- `usermacro_sync`: `True` sincroniza; `"full"` também força o reenvio (a API do Zabbix não devolve o valor de macros secretas, então só o `full` propaga uma troca de community).
- Com o sync de macros ligado, **macros criadas à mão no host são substituídas** pelas do NetBox. Migre as exceções para o NetBox antes de ligar.
- O mapeamento padrão (`device_usermacro_map`) também cria `{$DEV_ROLE}`, `{$NB_ID}`, `{$NB_URL}` e `{$HW_SERIAL}` (este só se o device tiver serial).

Acesso ao NetBox restrito à equipe do NOC — por isso a community pode ficar no *local config context* (visível a quem vê o device e no changelog).

### Bug do 4.1.0: macro secreta gravada como `********`

`sanatize_log_output()` (em `modules/tools.py`) mascara os segredos para o log, mas usa `data.copy()` (cópia **rasa**): os dicionários das macros são os mesmos enviados ao Zabbix, que recebe `********` como valor. A função é chamada mesmo com log em `info`. Afeta também os `details` de interface (SNMPv3).

Correção local ([patch](patches/sanatize-deepcopy.patch)):
```bash
F=/opt/netbox-zabbix-sync/lib/python3.13/site-packages/netbox_zabbix_sync/modules/tools.py
cp $F $F.bak
sed -i 's/^    sanitized_data = data.copy()$/    import copy\n    sanitized_data = copy.deepcopy(data)/' $F
/opt/netbox-zabbix-sync/bin/python -c "import netbox_zabbix_sync.modules.tools as t; d={'macros':[{'type':'1','value':'x'}]}; t.sanatize_log_output(d); print(d)"
# esperado: value 'x' intacto
```
> Reaplicar após qualquer `pip install -U netbox-zabbix-sync`.

## systemd

[`netbox-zabbix-sync.service`](netbox-zabbix-sync.service) roda como usuário dinâmico sem privilégios e com sistema de arquivos somente leitura; [`netbox-zabbix-sync.timer`](netbox-zabbix-sync.timer) agenda a cada 15 minutos.

## Segurança das contas de integração

- **Token v2 do NetBox restrito por IP** ao container do Zabbix. Atenção: com o servidor web dual-stack, o NetBox vê o cliente como `::ffff:<ipv4>` — a lista de IPs permitidos precisa ter **também** `::ffff:<ipv4>/128`, senão a API devolve 403.
- A API do NetBox só aceita o container do Zabbix (firewall do Proxmox) e a rede de administração.
- Próximo passo: reduzir as permissões (NetBox: permissões por objeto; Zabbix: role própria limitada aos grupos sincronizados).

## Operação

- Novo equipamento: Active + IP primário → conferir `zabbix_template` do **tipo** → tag `zabbix`.
- Remover: mudar o status para Decommissioning/Inventory **antes** de tirar a tag; senão o host fica órfão no Zabbix.
- O NetBox manda: template, grupos, interface e macros editados à mão no Zabbix são sobrescritos. Porta/community diferente → *local config context* do device.
- **Nunca** crie uma segunda interface SNMP à mão: o sync para com `Multiple interfaces of the same type ... manual intervention required` e deixa de atualizar o host.
- Conferir o valor real de uma macro secreta (o Zabbix só esconde na interface):
  ```bash
  su - postgres -c "psql -d zabbix -c \"SELECT h.host, m.macro, m.type, m.value FROM hostmacro m JOIN hosts h ON h.hostid=m.hostid WHERE m.macro LIKE '%SNMP_COMMUNITY%';\""
  ```
  Evite `$` dentro de comandos com várias camadas de shell (`pct exec` → `su -c`): o `$SNMP_COMMUNITY` vira variável vazia.
