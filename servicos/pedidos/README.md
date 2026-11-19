# CT 111 — pedidos (interação do público com as lives)

Serviço em Python (só biblioteca padrão + `python3-qrcode`) num LXC Debian do host do POP. Recebe **pedidos de música por QR Code** do público das lives e entrega ao overlay do OBS na [VM obs-lives](../obs-lives/README.md); também guarda a **retransmissão por link** e um **painel admin**. Em produção desde 17/11/2026 (v1); painel, página em tempo real e agentes por SSE em 18/11/2026 (v2–v4).

## Arquitetura

| Item | Valor |
|---|---|
| Processo | um serviço systemd (usuário próprio sem login, `ProtectSystem=strict`, `NoNewPrivileges`, `CAP_NET_BIND_SERVICE`) com duas portas |
| Porta 80 (HTTP) | página pública (só rede interna, acesso por IP, sem DNS) + rotas dos agentes |
| Porta 8443 (HTTPS) | painel admin, certificado autoassinado por IP |
| Dados | `estado.json` (fila, catálogo, retransmissão, regras) + SQLite (usuários, sessões, auditoria, histórico) |
| Config | arquivo `.env` 640 — o token dos agentes **nunca** vai para o repositório |

## Público (porta 80)

- Pedido com **primeiro nome**, fila de até 10, 1 pedido por pessoa a cada 10 min e limite por IP; sugestões de músicas fora da biblioteca
- **Tempo real por SSE** (`/api/ao-vivo`): tocando agora com timer e barra (a duração vem do overlay), fila com "seu pedido" destacado, tocaram há pouco, mais pedidas da semana (sem nomes); sem SSE cai para consulta a cada 15 s
- Catálogo sem repetidas (a mesma faixa em duas pastas de período chega duas vezes do overlay)
- Layout responsivo: 1 coluna no celular, 2 no PC

## Agentes (overlay de música e vigia de retransmissão)

- Só do IP da VM do OBS + **token no cabeçalho** (`X-Token`, `X-Agente`); token na URL desligado depois da migração
- Vigia recebe o link da retransmissão por SSE (`/api/agente/eventos`) e reage em 1–2 s; reconecta sozinho após restart do serviço
- Ordem de migração para tirar o token da URL: servidor novo → overlay → vigia → conferir → só então desligar o token na URL

## Painel admin (porta 8443)

1. IP de origem em lista fixa (2 IPs) + regra no firewall do Proxmox (ACCEPT para os 2 IPs acima de um DROP na 8443)
2. HTTPS (TLS 1.2+)
3. Usuário + senha (scrypt) + **TOTP obrigatório** (código não reutilizável)
4. Bloqueio: 5 erros no usuário ou 10 no IP → 15 min
5. Sessão em cookie `__Host-` (HttpOnly, Secure, SameSite=Strict), presa ao IP, 30 min ocioso / 12 h máx.
6. CSRF + verificação de Origin em todo POST; CSP restrita
7. Papéis **admin** e **visualizador** (só leitura, não vê o link da retransmissão nem usuários/auditoria); usuários locais, não do AD
8. Auditoria 365 dias; histórico de pedidos **180 dias** (LGPD, só primeiro nome)

Abas: Visão geral (com cartão "Conexões" dos agentes) · Música · Retransmissão · Relatórios (CSV) · Usuários · Auditoria.

## Roadmap do sistema de interação

- [x] F0 — HTTPS por IP, SQLite, migração
- [x] F1 — painel admin seguro (18/11)
- [x] F2 — página pública em tempo real (18/11)
- [x] F3 — agentes com token no cabeçalho + SSE (18/11)
- [ ] F4 — recados moderados (faixa no rodapé) e enquetes ao vivo
- [ ] F5 — backup do CT, alertas no Zabbix, métricas no Grafana
- [ ] Usuário visualizador do marketing + certificado no PC dele
- Backlog: sorteio com validação de contrato pela API do ERP (via n8n); palpites/placar para eventos

## Lições

- Fonte de navegador do OBS em "Arquivo local" não alcança IP privado → usar URL `file:///` e responder `Access-Control-Allow-Private-Network: true`
- Overlay com token vazio recebe 403 e a página pública fica parada → ao trocar o arquivo do overlay, repor o token
- `pct exec` roda com PATH sem `/usr/local/bin` (o utilitário de linha de comando só aparece dentro do `pct enter`)
