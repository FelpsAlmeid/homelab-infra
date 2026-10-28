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

## Próximos passos
- Sandbox em todas as sessões e execução em `deny`/`allowlist`
- Integração com o Zabbix por MCP em modo somente leitura; depois NetBox e GLPI
