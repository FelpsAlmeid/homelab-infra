# OpenClaw — agente de IA isolado (VM 107)

Agente [OpenClaw](https://openclaw.ai) (2026.10.x) usando o modelo local do Ollama, montado para atuar como apoio N2 do NOC com **acesso somente leitura**.

## Camadas de isolamento

| Camada | Controle |
|---|---|
| VM própria | Kernel separado dos containers; snapshot antes de cada mudança |
| Firewall do Proxmox | Entrada só SSH da gerência; **saída fechada** (`policy_out: DROP`), liberada destino a destino |
| Usuário | `openclaw` sem sudo |
| Sandbox | Docker **rootless** (containers sem root real e sem acesso ao loopback da VM) |
| Gateway | Só em `127.0.0.1:18789`; acesso por túnel SSH |
| Segredos | Token do gateway fora do `openclaw.json` (SecretRef `env` + `EnvironmentFile` 600) |
| Skills | Nenhuma da galeria pública sem revisão |

## Firewall da VM — [`vm.fw.example`](vm.fw.example)

## Instalação resumida

```bash
# como root na VM
adduser --disabled-password --gecos "" openclaw
apt install -y uidmap dbus-user-session systemd-container curl git ca-certificates
loginctl enable-linger openclaw
curl -fsSL https://get.docker.com | sh
systemctl disable --now docker.socket docker.service      # só o modo rootless
curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && apt install -y nodejs   # >= 24.22.1

# sessão do usuário (colar a linha abaixo sozinha)
machinectl shell openclaw@
dockerd-rootless-setuptool.sh install && systemctl --user enable --now docker
echo 'export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock' >> ~/.bashrc
npm config set prefix ~/.npm-global && echo 'export PATH=$HOME/.npm-global/bin:$PATH' >> ~/.bashrc
curl -fsSL https://openclaw.ai/install.sh -o /tmp/openclaw-install.sh && less /tmp/openclaw-install.sh && bash /tmp/openclaw-install.sh
# Quick start → One agent → provedor: Skip → sem canal → sem skills
```

## Modelo no Ollama de outro host

Ollama remoto exige o modelo declarado (sem descoberta automática). Use a **API nativa — sem `/v1`**, senão o *tool calling* quebra:

```json5
{
  models: { providers: { ollama: {
    baseUrl: "http://<ip-do-ollama>:11434", apiKey: "ollama-local", api: "ollama",
    timeoutSeconds: 300, maxTokens: 4096,
    models: [{ id: "gemma4:12b", reasoning: false, input: ["text"],
               contextTokens: 32768, params: { num_ctx: 32768, keep_alive: "15m" } }]
  } } },
  agents: { defaults: { model: { primary: "ollama/gemma4:12b" } } }
}
```
`params.num_ctx` vale só para as requisições do OpenClaw (o padrão do Ollama, usado por outros clientes, não muda).

## Gateway e segredo

```bash
chmod go-w ~ ~/.config ~/.config/systemd && chmod 700 ~/.config/systemd/user   # o install recusa pastas graváveis por outros
openclaw gateway install

# token fora do config
mkdir -p ~/.config/openclaw && chmod 700 ~/.config/openclaw
read -rsp "token: " T; printf 'OPENCLAW_GATEWAY_TOKEN=%s\n' "$T" > ~/.config/openclaw/gateway.env; unset T; chmod 600 ~/.config/openclaw/gateway.env
mkdir -p ~/.config/systemd/user/openclaw-gateway.service.d
printf '[Service]\nEnvironmentFile=%%h/.config/openclaw/gateway.env\n' > ~/.config/systemd/user/openclaw-gateway.service.d/secrets.conf
systemctl --user daemon-reload
set -a; . ~/.config/openclaw/gateway.env; set +a
openclaw secrets configure     # env · alias gateway · allowlist/id OPENCLAW_GATEWAY_TOKEN
openclaw secrets audit --check # clean
```

## Sandbox e política de ferramentas

Base: `docs/gateway/security/hardened-baseline.md` (sem copiar o bloco `gateway`, para não trazer o token em texto).

```json5
tools: {
  deny: ["group:automation","group:runtime","group:fs","group:web","browser","sessions_spawn","sessions_send"],
  sandbox: { tools: { deny: [/* mesma lista */] } },   // defesa em profundidade
  fs: { workspaceOnly: true }, exec: { security: "deny", ask: "always" },
  elevated: { enabled: false }, sessions: { visibility: "agent" }, agentToAgent: { enabled: false },
},
agents: { defaults: { sandbox: { mode: "all", scope: "session", workspaceAccess: "none" } } }
```

```bash
# o serviço do gateway não lê o .bashrc: apontar para o Docker rootless
printf '[Service]\nEnvironment=DOCKER_HOST=unix://%%t/docker.sock\n' > ~/.config/systemd/user/openclaw-gateway.service.d/docker.conf

# imagem do sandbox (o pacote npm não traz scripts/sandbox-setup.sh)
docker build -t openclaw-sandbox:bookworm-slim - <<'DOCKERFILE'
FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
  bash ca-certificates curl git jq python3 ripgrep && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --shell /bin/bash sandbox
USER sandbox
WORKDIR /home/sandbox
CMD ["sleep", "infinity"]
DOCKERFILE
```

Validação: container com `NetworkMode=none`, raiz somente leitura e usuário sem root; `openclaw security audit --deep` sem críticos.

> **O modelo descreve ferramentas que não tem.** Pedido de `cat /etc/machine-id`: a resposta inventou capacidades, mas o log mostrou `Unknown tool id: shell_execute` e nada foi executado. Valide sempre pela configuração e pelo log, nunca pela resposta do modelo.

## Integração com o Zabbix (somente leitura)

Três camadas independentes:

| Camada | Controle |
|---|---|
| Zabbix | Usuário sem frontend; função com API em **lista de permissões**: `host.get` `hostgroup.get` `hostinterface.get` `problem.get` `event.get` `trigger.get` `item.get` `history.get` `trend.get` `maintenance.get` `template.get` |
| MCP | [`zabbix-mcp`](https://github.com/mhajder/zabbix-mcp) com versão fixa, `READ_ONLY_MODE=true`, rate limit |
| OpenClaw | Só 8 ferramentas expostas e só `zabbix__*` liberado no sandbox |

```bash
# token fora do openclaw.json: .env privado + script de inicialização
mkdir -p ~/.config/zabbix-mcp && chmod 700 ~/.config/zabbix-mcp
read -rsp "Token Zabbix: " T; echo          # sozinho; colar o valor no prompt
cat > ~/.config/zabbix-mcp/.env <<EOF
ZABBIX_URL=http://<ip-zabbix>/api_jsonrpc.php
ZABBIX_TOKEN=$T
READ_ONLY_MODE=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_REQUESTS=60
EOF
unset T; chmod 600 ~/.config/zabbix-mcp/.env

cat > ~/.config/zabbix-mcp/run.sh <<'EOF'
#!/bin/sh
set -a; . /home/openclaw/.config/zabbix-mcp/.env; set +a
exec /home/openclaw/.local/bin/uvx zabbix-mcp@0.7.1
EOF
chmod 700 ~/.config/zabbix-mcp/run.sh      # o servidor não lê o .env do diretório de trabalho

openclaw mcp add zabbix --command /home/openclaw/.config/zabbix-mcp/run.sh --timeout 60
openclaw mcp tools zabbix --include problem_get,event_get,host_get,hostgroup_get,trigger_get,item_get,history_get,maintenance_get
```

```json5
tools: {
  alsoAllow: ["zabbix__*"],
  sandbox: { tools: { alsoAllow: ["zabbix__*"] } },   // sem isso o sandbox esconde as ferramentas do MCP
  toolSearch: false,   // modelos locais do Ollama usam busca de ferramentas por padrão; o gemma4:12b erra a chamada
}
```

Teste: *"Quais problemas estão ativos no Zabbix agora?"* → problemas reais retornados pelo `problem_get`.

## Instruções do agente

Papel de N2 do NOC em [`workspace/`](workspace/README.md) (SOUL/AGENTS/IDENTITY), com os testes de regressão.

## Painel web

O gateway escuta só em loopback; o acesso é por túnel SSH a partir da rede de administração:

```bash
ssh -L 18789:127.0.0.1:18789 <usuario>@<ip-da-vm>   # depois: http://127.0.0.1:18789/
```

O painel mostra as chamadas de ferramenta de cada resposta — útil para auditar o que o agente consultou. Não publicar no proxy: é a interface de administração do agente.

## Validação

Com o NAT do servidor removido por engano, o agente listou as três quedas reais por ICMP; após a correção, uma nova pergunta consultou o Zabbix de novo e confirmou a normalização.

## Próximos passos
- NetBox e GLPI somente leitura
