#!/usr/bin/env python3
"""
Personaliza os nomes dos canais/categorias do servidor do NOC (bot TEMPORÁRIO).

Uso:
  py discord_renomear_noc.py ID_DO_SERVIDOR             # simulação
  py discord_renomear_noc.py ID_DO_SERVIDOR --aplicar   # executa

Só renomeia: permissões, mensagens e IDs dos canais não mudam
(o OpenClaw e o n8n usam o ID do canal, não o nome).
"""
import getpass
import json
import sys
import time
import urllib.error
import urllib.request

API = "https://discord.com/api/v10"

NOVOS_NOMES = {
    # categorias
    "NOC": "NOC",
    "Alertas": "ALERTAS",
    "Geral": "GERAL",
    # canais
    "agente-noc": "「🤖」-agente-noc",
    "resumo-turno": "「📋」-resumo-turno",
    "avisos-noc": "「📢」-avisos-noc",
    "alertas-fibra": "「💡」-alertas-fibra",
    "alertas-radio": "「📡」-alertas-radio",
    "geral": "「💬」-geral",
}


def req(h, metodo, caminho, corpo=None):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    while True:
        r = urllib.request.Request(API + caminho, data=dados, headers=h, method=metodo)
        try:
            with urllib.request.urlopen(r, timeout=30) as resp:
                txt = resp.read()
                return json.loads(txt) if txt else None
        except urllib.error.HTTPError as e:
            txt = e.read().decode(errors="replace")
            if e.code == 429:
                time.sleep(float(json.loads(txt).get("retry_after", 2)) + 0.5)
                continue
            raise RuntimeError(f"{metodo} {caminho} -> HTTP {e.code}: {txt}") from None


def main():
    if len(sys.argv) < 2 or not sys.argv[1].isdigit():
        print(__doc__)
        sys.exit(1)
    gid, aplicar = sys.argv[1], "--aplicar" in sys.argv[2:]
    token = getpass.getpass("Token do bot TEMPORÁRIO (não aparece na tela): ").strip()
    h = {"Authorization": f"Bot {token}", "User-Agent": "DiscordBot (setup-noc, 1.0)",
         "Content-Type": "application/json", "X-Audit-Log-Reason": "Personalizacao dos canais NOC"}

    canais = req(h, "GET", f"/guilds/{gid}/channels")
    plano = [(c, NOVOS_NOMES[c["name"]]) for c in canais
             if c["name"] in NOVOS_NOMES and NOVOS_NOMES[c["name"]] != c["name"]]

    print("Modo:", "APLICAR" if aplicar else "SIMULAÇÃO (nada será alterado)")
    for c, novo in plano:
        print(f"  {c['name']:15} -> {novo}")
    if not plano:
        print("  Nada a renomear (já personalizado?).")
        return
    if not aplicar:
        print("\nPara executar: acrescente --aplicar")
        return

    for c, novo in plano:
        req(h, "PATCH", f"/channels/{c['id']}", {"name": novo})
        print(f"  ok: {novo}")
    print("\nConcluído. Próximo: remover o bot temporário e apagar o aplicativo dele.")


if __name__ == "__main__":
    main()
