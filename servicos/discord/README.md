# Servidor Discord do NOC

Estrutura do servidor da equipe, criada por script com um **bot temporário** (token só no notebook, apagado ao final). O bot do agente OpenClaw é outro, com permissões mínimas — ver [`servicos/openclaw/README.md`](../openclaw/README.md#canal-discord-da-equipe).

| Categoria | Canal | Quem vê | Uso |
|---|---|---|---|
| NOC | `「🤖」-agente-noc` | NOC + bot do agente | Perguntas ao agente (mencionando o bot) |
| | `「📋」-resumo-turno` | NOC + bot | Resumo automático; só o bot publica, equipe comenta em thread |
| | `「📢」-avisos-noc` | NOC | Comunicados (sem o bot) |
| ALERTAS | `「💡」-alertas-fibra` | NOC + Suporte | Notificações do n8n (fibra); comentários em thread |
| | `「📡」-alertas-radio` | NOC + Suporte | Notificações do n8n (rádio) |
| GERAL | `「💬」-geral` | NOC + Suporte | Conversa livre |

Cargos: `NOC`, `Suporte` e `Bot-Agente` (dado ao bot do OpenClaw). `@everyone` não vê nada; o bot do agente não vê alertas nem o geral e não pode mencionar `@everyone`.

## Uso dos scripts

Sem dependências externas (só Python 3). Os dois rodam em **simulação** por padrão.

```powershell
py discord_setup_noc.py ID_DO_SERVIDOR             # mostra o que existe e o plano
py discord_setup_noc.py ID_DO_SERVIDOR --aplicar   # apaga canais/cargos antigos e cria a estrutura
py discord_renomear_noc.py ID_DO_SERVIDOR --aplicar   # nomes no estilo 「emoji」-nome
```

1. Developer Portal: aplicativo **temporário** → Bot → Reset Token (sem intents)
2. Convite com `bot` + **Administrator** (temporário: precisa enxergar canais privados e apagar cargos); subir o cargo do bot para o topo
3. Rodar a simulação, conferir, aplicar (o token é pedido na tela, nunca em arquivo)
4. **Expulsar o bot e apagar o aplicativo** (invalida o token)

O OpenClaw e o n8n usam o **ID** do canal: renomear não quebra a integração.
