#!/usr/bin/env python3
"""
gerar_redes.py - Le o arquivo WoS unificado (wos_completo.txt) e gera:

  1) Redes no formato do VOSviewer (map + network), uma por analise:
       - palavras_chave  : coocorrencia de todas as palavras-chave (DE + ID)
       - cocitacao_refs  : cocitacao de referencias citadas (CR)
       - paises          : coautoria entre paises (C1)
       - cocitacao_fontes: cocitacao de periodicos/eventos citados (CR)
  2) Tabelas descritivas (CSV) para a apresentacao:
       - producao_por_ano.csv, paises.csv, periodicos.csv,
         palavras_chave.csv, brasil_artigos.csv, resumo.txt

Uso:  python3 analise/gerar_redes.py wos_completo.txt saida/
Somente biblioteca padrao do Python 3.
"""
import csv
import itertools
import os
import re
import sys
from collections import Counter, defaultdict

# ---------------- parametros (documentados no README) ----------------
MIN_OCC_KEYWORD = 20      # ocorrencias minimas de uma palavra-chave
MAX_KEYWORDS = 300        # no maximo N palavras-chave mais frequentes
MIN_CIT_REF = 40          # citacoes minimas de uma referencia
MAX_REFS = 300
MIN_DOCS_COUNTRY = 5      # documentos minimos de um pais
MIN_CIT_SOURCE = 150      # citacoes minimas de uma fonte citada
MAX_SOURCES = 200

# ---------------- leitura do formato WoS ----------------

def ler_registros(path):
    """Gera dicts {tag: [linhas]} para cada registro (PT ... ER)."""
    rec, tag = {}, None
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n").rstrip("\r")
            if line == "ER":
                if rec:
                    yield rec
                rec, tag = {}, None
                continue
            if not line or line.startswith(("FN ", "VR ", "EF")):
                continue
            if line.startswith("   ") and tag:
                rec[tag].append(line[3:])
            else:
                tag = line[:2]
                rec.setdefault(tag, []).append(line[3:])


def campo(rec, tag):
    return " ".join(rec.get(tag, []))

# ---------------- normalizacoes ----------------

SINONIMOS = {
    "auto scaling": "autoscaling",
    "autoscale": "autoscaling",
    "auto scale": "autoscaling",
    "elastic scaling": "autoscaling",
    "function as a service": "serverless computing",
    "function as a service (faas)": "serverless computing",
    "faas": "serverless computing",
    "serverless": "serverless computing",
    "spot instance": "spot instances",
    "over provisioning": "overprovisioning",
    "virtual machine": "virtual machines",
    "vm": "virtual machines",
    "vms": "virtual machines",
    "cloud": "cloud computing",
    "cloud computing (cc)": "cloud computing",
    "internet of things (iot)": "internet of things",
    "iot": "internet of things",
    "quality of service (qos)": "quality of service",
    "qos": "quality of service",
    "service level agreement (sla)": "service level agreement",
    "sla": "service level agreement",
    "deep reinforcement learning (drl)": "deep reinforcement learning",
    "drl": "deep reinforcement learning",
    "reinforcement learning (rl)": "reinforcement learning",
    "machine learning (ml)": "machine learning",
    "mobile edge computing": "mobile edge computing",
    "mec": "mobile edge computing",
}


def norm_kw(k):
    k = k.strip().lower().replace("-", " ")
    k = re.sub(r"\s+", " ", k).strip(" .;,")
    return SINONIMOS.get(k, k)


PAISES = {
    "peoples r china": "China",
    "england": "United Kingdom",
    "scotland": "United Kingdom",
    "wales": "United Kingdom",
    "north ireland": "United Kingdom",
    "u arab emirates": "United Arab Emirates",
    "turkiye": "Turkey",
    "usa": "USA",
    "brazil": "Brazil",
}


def pais_de_endereco(addr):
    addr = re.sub(r"^\[[^\]]*\]\s*", "", addr).strip().rstrip(".")
    if not addr:
        return None
    ult = addr.split(",")[-1].strip()
    # Enderecos dos EUA terminam com "XX 12345 USA"
    if ult.endswith(" USA") or ult == "USA":
        return "USA"
    chave = ult.lower()
    return PAISES.get(chave, ult.title())


def norm_ref(cr):
    """Chave canonica de uma referencia citada: DOI se houver, senao autor+ano+fonte."""
    m = re.search(r"DOI\s+(?:\[)?(10\.[^,\]\s]+)", cr, re.I)
    partes = [p.strip() for p in cr.split(",")]
    autor = partes[0] if partes else ""
    ano = partes[1] if len(partes) > 1 and partes[1].isdigit() else ""
    fonte = partes[2] if len(partes) > 2 else ""
    rotulo = f"{autor.lower()} ({ano}) {fonte.lower()}".strip()
    chave = ("doi:" + m.group(1).lower()) if m else f"{autor.lower()}|{ano}|{fonte.lower()}"
    return chave, rotulo, fonte.upper()

# ---------------- escrita VOSviewer ----------------

def escreve_vos(prefixo, itens, pesos, scores, pares, rotulo_peso, rotulo_score=None):
    """itens: lista de chaves; pesos: Counter; pares: Counter{(a,b): forca}."""
    ids = {k: i + 1 for i, k in enumerate(itens)}
    with open(prefixo + "_map.txt", "w", encoding="utf-8") as f:
        cab = ["id", "label", f"weight<{rotulo_peso}>"]
        if rotulo_score:
            cab.append(f"score<{rotulo_score}>")
        f.write("\t".join(cab) + "\n")
        for k in itens:
            lin = [str(ids[k]), k, str(pesos[k])]
            if rotulo_score:
                lin.append(f"{scores[k]:.2f}")
            f.write("\t".join(lin) + "\n")
    n_links = 0
    with open(prefixo + "_network.txt", "w", encoding="utf-8") as f:
        for (a, b), w in pares.items():
            if a in ids and b in ids:
                f.write(f"{ids[a]}\t{ids[b]}\t{w}\n")
                n_links += 1
    return len(itens), n_links


def coocorrencia(listas, selecionados):
    sel = set(selecionados)
    pares = Counter()
    for itens in listas:
        s = sorted(set(i for i in itens if i in sel))
        for a, b in itertools.combinations(s, 2):
            pares[(a, b)] += 1
    return pares


def top(contador, minimo, maximo):
    return [k for k, v in contador.most_common() if v >= minimo][:maximo]

# ---------------- principal ----------------

def main():
    entrada, saida = sys.argv[1], sys.argv[2]
    os.makedirs(saida, exist_ok=True)
    vos = os.path.join(saida, "vosviewer")
    tab = os.path.join(saida, "tabelas")
    os.makedirs(vos, exist_ok=True)
    os.makedirs(tab, exist_ok=True)

    docs = []
    for r in ler_registros(entrada):
        kws = [norm_kw(k) for k in (campo(r, "DE") + ";" + campo(r, "ID")).split(";") if k.strip()]
        paises = sorted({p for a in r.get("C1", []) if (p := pais_de_endereco(a))})
        refs = [norm_ref(c) for c in r.get("CR", [])
                if c.strip() and not c.lower().startswith("[anonymous]")]
        py = campo(r, "PY").strip() or campo(r, "EA")[-4:]
        docs.append({
            "ut": campo(r, "UT"), "ti": campo(r, "TI"), "so": campo(r, "SO"),
            "py": int(py) if py.isdigit() else None, "dt": campo(r, "DT"),
            "tc": int(campo(r, "TC") or 0), "di": campo(r, "DI"),
            "kws": kws, "paises": paises, "refs": refs,
            "c1": " ".join(r.get("C1", [])).lower(),
        })

    # ---- 1. palavras-chave (coocorrencia, contagem binaria por documento) ----
    occ, soma_ano, n_ano = Counter(), Counter(), Counter()
    for d in docs:
        for k in set(d["kws"]):
            occ[k] += 1
            if d["py"]:
                soma_ano[k] += d["py"]; n_ano[k] += 1
    sel = top(occ, MIN_OCC_KEYWORD, MAX_KEYWORDS)
    ano_medio = {k: soma_ano[k] / n_ano[k] if n_ano[k] else 0 for k in sel}
    r1 = escreve_vos(os.path.join(vos, "palavras_chave"), sel, occ, ano_medio,
                     coocorrencia([d["kws"] for d in docs], sel),
                     "Occurrences", "Avg. pub. year")

    # ---- 2. cocitacao de referencias ----
    cit, rot = Counter(), {}
    for d in docs:
        for chave, rotulo, _ in {x[0]: x for x in d["refs"]}.values():
            cit[chave] += 1
            rot.setdefault(chave, rotulo)
    sel_r = top(cit, MIN_CIT_REF, MAX_REFS)
    pares_r = coocorrencia([[x[0] for x in d["refs"]] for d in docs], sel_r)
    # rotulos legiveis no lugar das chaves
    mapa_rot = {k: rot[k] for k in sel_r}
    r2 = escreve_vos(os.path.join(vos, "cocitacao_refs"), [mapa_rot[k] for k in sel_r],
                     Counter({mapa_rot[k]: cit[k] for k in sel_r}), None,
                     Counter({(mapa_rot[a], mapa_rot[b]): w for (a, b), w in pares_r.items()}),
                     "Citations")

    # ---- 3. coautoria entre paises ----
    docs_p, cit_p = Counter(), Counter()
    for d in docs:
        for p in d["paises"]:
            docs_p[p] += 1; cit_p[p] += d["tc"]
    sel_p = top(docs_p, MIN_DOCS_COUNTRY, 10**6)
    r3 = escreve_vos(os.path.join(vos, "paises"), sel_p, docs_p, None,
                     coocorrencia([d["paises"] for d in docs], sel_p), "Documents")

    # ---- 4. cocitacao de fontes ----
    fontes = Counter()
    listas_f = []
    for d in docs:
        fs = {x[2] for x in d["refs"] if x[2]}
        listas_f.append(fs)
        fontes.update(fs)
    sel_f = top(fontes, MIN_CIT_SOURCE, MAX_SOURCES)
    r4 = escreve_vos(os.path.join(vos, "cocitacao_fontes"), sel_f, fontes, None,
                     coocorrencia(listas_f, sel_f), "Citations")

    # ---------------- tabelas ----------------
    anos = Counter(d["py"] for d in docs if d["py"])
    with open(os.path.join(tab, "producao_por_ano.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["ano", "documentos"])
        for a in sorted(anos):
            w.writerow([a, anos[a]])

    with open(os.path.join(tab, "paises.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["pais", "documentos", "citacoes", "pct_documentos"])
        for p, n in docs_p.most_common():
            w.writerow([p, n, cit_p[p], f"{100 * n / len(docs):.2f}"])

    so = Counter(d["so"] for d in docs)
    with open(os.path.join(tab, "periodicos.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["fonte", "documentos"])
        for s, n in so.most_common(50):
            w.writerow([s, n])

    with open(os.path.join(tab, "palavras_chave.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["palavra_chave", "ocorrencias", "ano_medio"])
        for k, n in occ.most_common(200):
            w.writerow([k, n, f"{soma_ano[k] / n_ano[k]:.1f}" if n_ano[k] else ""])

    br = sorted((d for d in docs if "Brazil" in d["paises"]), key=lambda d: -d["tc"])
    with open(os.path.join(tab, "brasil_artigos.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["ano", "titulo", "fonte", "citacoes", "doi", "ut"])
        for d in br:
            w.writerow([d["py"], d["ti"], d["so"], d["tc"], d["di"], d["ut"]])

    tipos = Counter(d["dt"] for d in docs)
    pos_br = [p for p, _ in docs_p.most_common()].index("Brazil") + 1 if "Brazil" in docs_p else None
    goias = [d for d in br if re.search(r"goias|goiania|\bgo\b,? brazil", d["c1"])]
    with open(os.path.join(tab, "resumo.txt"), "w") as f:
        f.write(f"Documentos: {len(docs)}\n")
        f.write(f"Periodo: {min(anos)}-{max(anos)}\n")
        f.write(f"Tipos de documento: {dict(tipos.most_common(6))}\n")
        f.write(f"Paises distintos: {len(docs_p)}\n")
        f.write("Top 10 paises: " + ", ".join(f"{p} ({n})" for p, n in docs_p.most_common(10)) + "\n")
        f.write(f"Brasil: {docs_p.get('Brazil', 0)} documentos "
                f"({100 * docs_p.get('Brazil', 0) / len(docs):.2f}%), posicao {pos_br} no ranking\n")
        f.write(f"Brasil com autor vinculado a Goias (endereco C1): {len(goias)}\n")
        for d in goias:
            f.write(f"   - {d['py']} | {d['ti'][:110]} | {d['so']}\n")
        f.write(f"Docs com 'FinOps' no titulo/palavras-chave: "
                f"{sum(1 for d in docs if 'finops' in (d['ti'].lower() + ' '.join(d['kws'])))}\n")
        f.write("\nRedes VOSviewer (itens, links):\n")
        f.write(f"  palavras_chave   : {r1}  (min {MIN_OCC_KEYWORD} ocorrencias, max {MAX_KEYWORDS})\n")
        f.write(f"  cocitacao_refs   : {r2}  (min {MIN_CIT_REF} citacoes, max {MAX_REFS})\n")
        f.write(f"  paises           : {r3}  (min {MIN_DOCS_COUNTRY} documentos)\n")
        f.write(f"  cocitacao_fontes : {r4}  (min {MIN_CIT_SOURCE} citacoes, max {MAX_SOURCES})\n")
    print(open(os.path.join(tab, "resumo.txt")).read())


if __name__ == "__main__":
    main()
