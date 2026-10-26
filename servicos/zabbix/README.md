# Zabbix (em andamento)

Planejado:
- LXC em **SSD dedicado** (a escrita contínua do banco já travou o host quando dividia o disco do sistema).
- **PostgreSQL**, retenção curta de histórico, *trends* longas e pré-processamento "descartar inalterados com heartbeat".
- Coleta SNMP v2c com a community em **macro global do tipo texto secreto**.
- Hosts sincronizados a partir do NetBox; problemas abrem chamados no GLPI.
