#!/usr/bin/env python3
"""
Limpa e reorganiza o servidor Discord do NOC (uso único, com bot TEMPORÁRIO).

Uso:
  py discord_setup_noc.py ID_DO_SERVIDOR             # simulação: só mostra o plano
  py discord_setup_noc.py ID_DO_SERVIDOR --aplicar   # executa

- O token do bot temporário é pedido na tela (não fica em arquivo nem no histórico).
- Membros NÃO são removidos. Canais e cargos antigos são apagados
  (exceto @everyone, cargos gerenciados por bots/boost e os cargos da estrutura nova).
- Depois de usar: remover o bot temporário do servidor e apagar o aplicativo no Developer Portal.
"""
import getpass
import json
import sys
import time
import urllib.error
import urllib.request

API = "https://discord.com/api/v10"

# ---------- permissões (bits da API do Discord) ----------
VIEW = 1 << 10
SEND = 1 << 11
EMBED = 1 << 14
ATTACH = 1 << 15
HISTORY = 1 << 16
MENTION_ALL = 1 << 17
REACT = 1 << 6
PUBLIC_THREADS = 1 << 35
SEND_IN_THREADS = 1 << 38

HUMANO_LEITURA = VIEW | HISTORY | REACT
HUMANO_CONVERSA = HUMANO_LEITURA | SEND | EMBED | ATTACH | PUBLIC_THREADS | SEND_IN_THREADS
HUMANO_ALERTA = HUMANO_LEITURA | PUBLIC_THREADS | SEND_IN_THREADS   # comenta em thread, não no canal
BOT_AGENTE = VIEW | HISTORY | SEND | EMBED | SEND_IN_THREADS

# ---------- estrutura desejada ----------
CARGOS = ["NOC", "Suporte", "Bot-Agente"]   # Bot-Agente: será dado ao bot do OpenClaw depois

# regra: (cargo, allow, deny); "@everyone" = id do servidor
ESTRUTURA = [
    ("NOC", [
        ("agente-noc",   "Perguntas ao agente OpenClaw (mencione o bot)",
         [("@everyone", 0, VIEW), ("NOC", HUMANO_CONVERSA, 0), ("Bot-Agente", BOT_AGENTE, MENTION_ALL)]),
        ("resumo-turno", "Resumo automático do NOC (só o bot publica)",
         [("@everyone", 0, VIEW), ("NOC", HUMANO_ALERTA, SEND), ("Bot-Agente", BOT_AGENTE, MENTION_ALL)]),
        ("avisos-noc",   "Comunicados da equipe do NOC",
         [("@everyone", 0, VIEW), ("NOC", HUMANO_CONVERSA, 0), ("Bot-Agente", 0, VIEW)]),
    ]),
    ("Alertas", [
        ("alertas-fibra", "Notificações automáticas do n8n — fibra (comentar em thread)",
         [("@everyone", 0, VIEW), ("NOC", HUMANO_ALERTA, SEND), ("Suporte", HUMANO_ALERTA, SEND), ("Bot-Agente", 0, VIEW)]),
        ("alertas-radio", "Notificações automáticas do n8n — rádio (comentar em thread)",
         [("@everyone", 0, VIEW), ("NOC", HUMANO_ALERTA, SEND), ("Suporte", HUMANO_ALERTA, SEND), ("Bot-Agente", 0, VIEW)]),
    ]),
    ("Geral", [
        ("geral", "Conversa geral NOC + Suporte",
         [("@everyone", 0, VIEW), ("NOC", HUMANO_CONVERSA, 0), ("Suporte", HUMANO_CONVERSA, 0), ("Bot-Agente", 0, VIEW)]),
    ]),
]

# permissões das categorias = união: esconde de @everyone e mostra para quem usa algum canal dela
CATEGORIA_PERM = {
    "NOC":     [("@everyone", 0, VIEW), ("NOC", VIEW, 0), ("Bot-Agente", VIEW, 0)],
    "Alertas": [("@everyone", 0, VIEW), ("NOC", VIEW, 0), ("Suporte", VIEW, 0)],
    "Geral":   [("@everyone", 0, VIEW), ("NOC", VIEW, 0), ("Suporte", VIEW, 0)],
}

TIPOS = {0: "texto", 2: "voz", 4: "categoria", 5: "anúncios", 13: "palco", 15: "fórum", 16: "mídia"}


class Discord:
    def __init__(self, token):
        self.h = {
            "Authorization": f"Bot {token}",
            "User-Agent": "DiscordBot (setup-noc, 1.0)",
            "Content-Type": "application/json",
            "X-Audit-Log-Reason": "Reorganizacao do servidor NOC",
        }

    def req(self, metodo, caminho, corpo=None):
        dados = json.dumps(corpo).encode() if corpo is not None else None
        while True:
            r = urllib.request.Request(API + caminho, data=dados, headers=self.h, method=metodo)
            try:
                with urllib.request.urlopen(r, timeout=30) as resp:
                    txt = resp.read()
                    return json.loads(txt) if txt else None
            except urllib.error.HTTPError as e:
                txt = e.read().decode(errors="replace")
                if e.code == 429:                      # limite de requisições: espera e repete
                    espera = json.loads(txt).get("retry_after", 2)
                    time.sleep(float(espera) + 0.5)
                    continue
                raise RuntimeError(f"{metodo} {caminho} -> HTTP {e.code}: {txt}") from None


def main():
    if len(sys.argv) < 2 or not sys.argv[1].isdigit():
        print(__doc__)
        sys.exit(1)
    gid = sys.argv[1]
    aplicar = "--aplicar" in sys.argv[2:]

    d = Discord(getpass.getpass("Token do bot TEMPORÁRIO (não aparece na tela): ").strip())

    guild = d.req("GET", f"/guilds/{gid}")
    eu = d.req("GET", "/users/@me")
    membro = d.req("GET", f"/guilds/{gid}/members/{eu['id']}")
    canais = d.req("GET", f"/guilds/{gid}/channels")
    cargos = d.req("GET", f"/guilds/{gid}/roles")

    pos_por_id = {c["id"]: c["position"] for c in cargos}
    topo_bot = max((pos_por_id.get(r, 0) for r in membro["roles"]), default=0)
    sistema = {guild.get("rules_channel_id"), guild.get("public_updates_channel_id")} - {None}

    print(f"\nServidor: {guild['name']}  (bot: {eu['username']}, posição do cargo do bot: {topo_bot})")
    print("Modo:", "APLICAR" if aplicar else "SIMULAÇÃO (nada será alterado)")

    # ---- canais a apagar
    print(f"\nCanais atuais ({len(canais)}) — todos serão apagados:")
    for c in sorted(canais, key=lambda c: (c.get("parent_id") or "", c["position"])):
        aviso = "  [canal de regras/novidades da Comunidade: pode falhar]" if c["id"] in sistema else ""
        print(f"  - {TIPOS.get(c['type'], c['type']):10} #{c['name']}{aviso}")

    # ---- cargos
    por_nome = {c["name"]: c for c in cargos}
    apagar, bloqueados = [], []
    print(f"\nCargos atuais ({len(cargos)}):")
    for c in sorted(cargos, key=lambda c: -c["position"]):
        if c["id"] == gid:
            acao = "mantém (@everyone)"
        elif c.get("managed"):
            acao = "mantém (gerenciado por bot/boost)"
        elif c["name"] in CARGOS:
            acao = "mantém e reutiliza"
        elif c["position"] >= topo_bot:
            acao = "NÃO dá para apagar (acima do cargo do bot) — suba o cargo do bot ou apague à mão"
            bloqueados.append(c)
        else:
            acao = "apaga"
            apagar.append(c)
        print(f"  - {c['name']:25} {acao}")

    print("\nEstrutura nova:")
    print("  Cargos:", ", ".join(f"{n} ({'existe' if n in por_nome else 'criar'})" for n in CARGOS))
    for cat, filhos in ESTRUTURA:
        print(f"  [{cat}]")
        for nome, tema, _ in filhos:
            print(f"     #{nome:15} {tema}")

    if apagar:
        print("\nATENÇÃO: membros perdem os cargos apagados; depois atribua NOC/Suporte a cada pessoa.")
    if not aplicar:
        print("\nSimulação concluída. Para executar: acrescente --aplicar")
        return
    if input("\nDigite APLICAR para confirmar: ").strip() != "APLICAR":
        print("Cancelado.")
        return

    erros = []
    for c in canais:
        try:
            d.req("DELETE", f"/channels/{c['id']}")
            print(f"  apagado #{c['name']}")
        except RuntimeError as e:
            erros.append(str(e))
    for c in apagar:
        try:
            d.req("DELETE", f"/guilds/{gid}/roles/{c['id']}")
            print(f"  cargo apagado: {c['name']}")
        except RuntimeError as e:
            erros.append(str(e))

    ids = {"@everyone": gid}
    for nome in CARGOS:
        if nome in por_nome:
            ids[nome] = por_nome[nome]["id"]
        else:
            r = d.req("POST", f"/guilds/{gid}/roles",
                      {"name": nome, "permissions": "0", "hoist": nome != "Bot-Agente", "mentionable": nome != "Bot-Agente"})
            ids[nome] = r["id"]
            print(f"  cargo criado: {nome}")

    def overwrites(regras):
        return [{"id": ids[n], "type": 0, "allow": str(a), "deny": str(dn)} for n, a, dn in regras]

    for cat, filhos in ESTRUTURA:
        c = d.req("POST", f"/guilds/{gid}/channels",
                  {"name": cat, "type": 4, "permission_overwrites": overwrites(CATEGORIA_PERM[cat])})
        print(f"  categoria criada: {cat}")
        for nome, tema, regras in filhos:
            d.req("POST", f"/guilds/{gid}/channels",
                  {"name": nome, "type": 0, "topic": tema, "parent_id": c["id"],
                   "permission_overwrites": overwrites(regras)})
            print(f"     canal criado: #{nome}")

    print("\nConcluído." if not erros else "\nConcluído com erros:")
    for e in erros:
        print("  -", e)
    print("Próximo: atribuir NOC/Suporte às pessoas, remover o bot temporário e apagar o aplicativo dele.")


if __name__ == "__main__":
    main()
