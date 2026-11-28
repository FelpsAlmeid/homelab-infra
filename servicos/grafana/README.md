# Grafana (CT 114)

Grafana OSS 13 (repositório apt oficial) num LXC leve, com fontes de dados **somente leitura**:

| Fonte | Plugin | Usuário |
|---|---|---|
| Zabbix (CT 104) | `alexanderzobnin-zabbix-app` | Usuário de API próprio, role com lista de permissões só `.get` |
| Postgres `noc` ([CT 115](../postgres-noc/README.md)) | `grafana-postgresql-datasource` (nativo) | `grafana_ro`, só `SELECT` |

Configuração por variáveis em `/etc/default/grafana-server` (o `grafana.ini` fica intacto). Os dashboards do NOC (visão geral, topologia e imagens para as TVs) ainda **não foram exportados** para cá.

## Dashboards ([`dashboards/`](dashboards))

### Atendimento ao Cliente — Opa Suite

[`atendimento-opa-suite.json`](dashboards/atendimento-opa-suite.json) é o painel executivo para a diretoria, com dados do [fluxo Opa Suite → n8n → Postgres](../n8n/opa-suite/README.md).

| Seção | Conteúdo |
|---|---|
| Cabeçalho | Logo, título e **"dados atualizados há X min"** (verde até 10, amarelo até 30, vermelho depois) |
| Resumo do período | Atendimentos · resolvidos pelo bot (%) · tempo mediano da equipe · CSAT (notas 4 e 5) · fora do horário · em aberto agora (em atendimento / na fila) |
| Tendência e canais | Barras diárias empilhadas por canal (cores da marca) + rosca de participação |
| Desempenho por setor | Tabela com volume, % do total, tempo mediano (`1h24` / `1d 19h`), nota, CSAT colorido e fora do horário |
| Quando o cliente procura | Mapa de calor dia da semana × hora, para dimensionar a escala |
| Equipe e motivos | Top 10 da equipe humana e top 10 motivos |
| Operação (recolhida) | Atendimentos em aberto, do mais antigo ao mais novo, com "aberto há" colorido |

Decisões de leitura:
- **Variação vs período anterior.** Cada indicador devolve dois pontos, o período anterior de mesmo tamanho e o atual, e o *percent change* nativo do stat compara os dois. A cor segue o que é bom para cada indicador:
  - **Tempo:** invertida (seta verde = mais rápido).
  - **Volume e fora do horário:** neutra.
  - **Bot e CSAT:** verde = subiu.
- **Mediana, não média.** Na equipe, a média era ~5× a mediana (653 × 124 min), puxada por conversas abertas por dias.
- **O bot fica fora** do tempo da equipe e do ranking. O setor do agente virtual tem ~42% do volume e ~20 min de mediana.
- **Dia local.** As barras diárias agrupam por `date_trunc('day', … AT TIME ZONE 'America/Fortaleza')`; o `$__timeGroup` agrupa em UTC e "virava" o dia às 21h.
- **Filtro de setor** em quase tudo. A rosca de bot (%) considera todos os setores, de propósito.

### Ao importar

- Escolher o data source Postgres `noc` em `DS_POSTGRESQL-NOC`. O JSON usa o id novo do plugin, `grafana-postgresql-datasource`: com o id antigo (`postgres`), o import não liga os painéis ao data source.
- **Logo:** o painel de texto não exibe imagem `data:` (sanitização do Grafana). O arquivo fica servido pelo próprio Grafana, e atualizações do pacote não apagam arquivos que não são dele:

```bash
pct exec 114 -- mkdir -p /usr/share/grafana/public/img/conecta
pct push 114 /tmp/<logo>.png /usr/share/grafana/public/img/conecta/conecta-fibra-logo-600.png --perms 644
```

- A comparação com o período anterior só aparece quando o banco tem o dobro do período carregado (ver o backfill em [`opa-suite`](../n8n/opa-suite/README.md)).

## Acesso da diretoria

- Contas nominais com papel **Viewer**, ou um time com leitura só na pasta do painel.
- Publicação externa pelo proxy (NPM + Access List) ainda pendente.
