#!/usr/bin/env python3
"""Levantamento de topologia a partir do UNMS (Legacy) para preencher o `uplink` no NetBox.

Somente leitura: faz apenas GET em /devices e /data-links.

Uso:
  1) Coletar (salva o JSON bruto):
       export UNMS_URL=https://<unms>/nms/api/v2.1
       read -rs UNMS_TOKEN && export UNMS_TOKEN        # colar o token e Enter
       python3 topologia_unms.py coletar
  2) Ver os ramos (componentes) e escolher a raiz de cada um:
       python3 topologia_unms.py ramos                 # gera ramos.csv
       -> preencher raizes.txt (nome ou IP do device de entrada de cada ramo, um por linha)
       (opcional) manter.txt: só ficam os nomes que casam com algum regex (padrões de infraestrutura)
       (opcional) ignorar.txt: um regex de nome por linha a descartar (bancada, teste)
  3) Gerar a planilha de revisão:
       python3 topologia_unms.py arvore                # gera topologia-revisao.csv
"""
import csv, json, os, re, ssl, sys, urllib.request
from collections import defaultdict, deque

F_DEV, F_LNK = "unms-devices.json", "unms-data-links.json"


def get(path):
    url = os.environ["UNMS_URL"].rstrip("/") + path
    req = urllib.request.Request(url, headers={"x-auth-token": os.environ["UNMS_TOKEN"], "Accept": "application/json"})
    ctx = ssl.create_default_context()
    if os.environ.get("UNMS_INSECURE", "1") == "1":   # UNMS interno com certificado autoassinado
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
        return json.load(r)


def coletar():
    for path, f in (("/devices", F_DEV), ("/data-links", F_LNK)):
        data = get(path)
        with open(f, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
        print(f"{f}: {len(data)} registros")


def g(d, *keys):
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def carregar():
    devs = json.load(open(F_DEV, encoding="utf-8"))
    links = json.load(open(F_LNK, encoding="utf-8"))
    info = {}
    for d in devs:
        i = d.get("identification") or {}
        if not i.get("id"):
            continue
        info[i["id"]] = {
            "nome": i.get("displayName") or i.get("name") or i.get("hostname") or i["id"],
            "ip": (d.get("ipAddress") or i.get("ip") or "").split("/")[0],
            "modelo": i.get("model") or "",
            "tipo": i.get("type") or "",
            "site": g(i, "site", "name") or "",
            "site_tipo": g(i, "site", "type") or "",
            "site_pai": g(i, "site", "parent", "name") or "",
            "modo": g(d, "overview", "wirelessMode") or "",
            "status": i.get("status") or g(d, "overview", "status") or "",
        }
    viz = defaultdict(dict)   # id -> {vizinho: origem}

    def liga(a, b, origem):
        if a and b and a != b:
            viz[a].setdefault(b, origem)
            viz[b].setdefault(a, origem)

    for l in links:
        a = g(l, "from", "device", "identification", "id")
        b = g(l, "to", "device", "identification", "id")
        for lado, did in (("from", a), ("to", b)):          # device que só aparece no link
            if did and did not in info:
                i = g(l, lado, "device", "identification") or {}
                info[did] = {"nome": i.get("displayName") or i.get("name") or did, "ip": (i.get("ipAddress") or "").split("/")[0],
                             "modelo": i.get("model") or "", "tipo": i.get("type") or "",
                             "site": g(l, lado, "site", "identification", "name") or "",
                             "site_tipo": g(l, lado, "site", "identification", "type") or "", "site_pai": "", "modo": "", "status": ""}
        liga(a, b, f"data-link {l.get('type', '')}".strip())
    for d in devs:                                          # estação -> AP
        liga(g(d, "identification", "id"), g(d, "attributes", "apDevice", "id"), "apDevice")
    if os.environ.get("INCLUIR_CLIENTES") != "1":            # CPE de cliente (site do tipo endpoint) fica fora
        fora = {d for d, x in info.items() if x["site_tipo"] == "endpoint"}
        for d in fora:
            info.pop(d)
            viz.pop(d, None)
        for v in viz.values():
            for d in fora:
                v.pop(d, None)
        if fora:
            print(f"{len(fora)} devices em sites de cliente ignorados (INCLUIR_CLIENTES=1 para incluir)")
    pad = []
    if os.path.exists("ignorar.txt"):                        # um regex por linha (sem diferenciar maiúsculas)
        pad = [re.compile(l.strip(), re.I) for l in open("ignorar.txt", encoding="utf-8") if l.strip() and not l.startswith("#")]
    manter = []
    if os.path.exists("manter.txt"):                         # se existir, só fica quem casa com algum regex
        manter = [re.compile(l.strip(), re.I) for l in open("manter.txt", encoding="utf-8") if l.strip() and not l.startswith("#")]
    fora = {d for d, x in info.items() if any(p.search(x["nome"]) for p in pad)
            or (manter and not any(p.search(x["nome"]) for p in manter))}
    for d in fora:
        info.pop(d)
        viz.pop(d, None)
    for v in viz.values():
        for d in fora:
            v.pop(d, None)
    if fora:
        print(f"{len(fora)} devices ignorados por ignorar.txt/manter.txt")
    for did in info:
        viz.setdefault(did, {})
    return info, viz


def componentes(viz):
    vistos, comps = set(), []
    for n in sorted(viz):
        if n in vistos:
            continue
        fila, comp = deque([n]), []
        vistos.add(n)
        while fila:
            x = fila.popleft()
            comp.append(x)
            for y in viz[x]:
                if y not in vistos:
                    vistos.add(y)
                    fila.append(y)
        comps.append(comp)
    return comps


def ramos():
    info, viz = carregar()
    comps = sorted(componentes(viz), key=len, reverse=True)
    soltos = sum(1 for c in comps if len(c) == 1)
    print(f"{len(info)} devices · {len(comps) - soltos} ramos com vínculo · {soltos} soltos (sem data link)")
    nomes = defaultdict(int)
    for x in info.values():
        nomes[x["nome"].strip().lower()] += 1
    dup = sorted(n for n, q in nomes.items() if q > 1)
    if dup:
        print(f"Nomes repetidos ({len(dup)}): " + ", ".join(dup[:15]) + (" ..." if len(dup) > 15 else ""))
    with open("ramos.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["ramo", "qtd_devices", "sites", "devices (nome [ip])"])
        for n, c in enumerate(comps, 1):
            sites = sorted({info[x]["site"] for x in c if info[x]["site"]})
            w.writerow([n, len(c), " | ".join(sites), " | ".join(sorted(f"{info[x]['nome']} [{info[x]['ip']}]" for x in c))])
    print(f"{len(comps)} ramos -> ramos.csv")
    print("Preencha raizes.txt com o device de entrada de cada ramo (o que liga no POP/BNG), um por linha.")


def arvore():
    info, viz = carregar()
    por_nome = defaultdict(list)
    for did, x in info.items():
        por_nome[x["nome"].strip().lower()].append(did)
        if x["ip"]:
            por_nome[x["ip"]].append(did)
    raizes = []
    if os.path.exists("raizes.txt"):
        for linha in open("raizes.txt", encoding="utf-8"):
            nome = linha.strip()
            if not nome or nome.startswith("#"):
                continue
            ids = por_nome.get(nome.lower(), [])
            if len(ids) != 1:
                print(f"AVISO raiz '{nome}': {'não encontrada' if not ids else 'nome duplicado'}")
                continue
            raizes.append(ids[0])
    pai, prof, origem, ramo = {}, {}, {}, {}
    for n, r in enumerate(raizes, 1):
        if r in prof:
            print(f"AVISO raiz '{info[r]['nome']}' já está no ramo de outra raiz")
            continue
        prof[r], ramo[r], fila = 0, n, deque([r])
        while fila:
            x = fila.popleft()
            for y, o in sorted(viz[x].items()):
                if y not in prof:
                    pai[y], prof[y], origem[y], ramo[y] = x, prof[x] + 1, o, n
                    fila.append(y)
    ciclos = sum(1 for a in prof for b in viz[a] if b in prof and a < b) - len(pai)
    sem_raiz = [d for d in info if d not in prof]
    with open("topologia-revisao.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["ramo", "nivel", "device", "ip", "modelo", "tipo", "modo_radio", "site_unms", "site_pai_unms",
                    "uplink_sugerido", "uplink_ip", "origem_vinculo", "observacao", "uplink_confirmado"])
        ordem = sorted(prof, key=lambda d: (ramo[d], prof[d], info[d]["site"], info[d]["nome"]))
        for d in ordem + sorted(sem_raiz, key=lambda d: (info[d]["site"], info[d]["nome"])):
            x, p = info[d], pai.get(d)
            obs = []
            if d in raizes:
                obs.append("RAIZ DO RAMO - informar o uplink no POP/BNG")
            if d not in prof:
                obs.append("SEM RAMO - definir raiz ou uplink manual")
            if not x["ip"]:
                obs.append("sem IP (não vai para o Zabbix)")
            w.writerow([ramo.get(d, ""), prof.get(d, ""), x["nome"], x["ip"], x["modelo"], x["tipo"], x["modo"], x["site"],
                        x["site_pai"], info[p]["nome"] if p else "", info[p]["ip"] if p else "", origem.get(d, ""),
                        "; ".join(obs), ""])
    print(f"{len(prof)} devices em {len(raizes)} ramos · {len(sem_raiz)} sem ramo · vínculos extras (possível laço): {max(ciclos, 0)}")
    print("-> topologia-revisao.csv")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"coletar": coletar, "ramos": ramos, "arvore": arvore}.get(cmd, lambda: print(__doc__))()
