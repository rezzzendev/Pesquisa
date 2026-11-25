#!/usr/bin/env python3
"""
triagem_prisma.py - Triagem automatizada (titulo/resumo/palavras-chave) da base WoS
seguindo as etapas do PRISMA 2020, e geracao do fluxograma.

Uso:  python3 analise/triagem_prisma.py wos_completo.txt resultados

Etapas automaticas (criterios de exclusao, aplicados nesta ordem):
  E1  tipo documental nao elegivel (editorial, carta, retratacao, artigo retratado)
      ou registro sem resumo
  E2  idioma diferente de ingles ou portugues
  E3  nao aborda nenhuma estrategia de elasticidade (autoscaling, spot/preemptible,
      serverless/FaaS, desligamento/agendamento, right-sizing, modelos de compra
      reservada x sob demanda)
  E4  nao relata economia de custo QUANTIFICADA no resumo (percentual ou "x vezes"
      na mesma frase que um termo de custo e um verbo de reducao)

Quem passa vai para a leitura de texto completo (elegibilidade). Os candidatos sao
pontuados para priorizar a leitura (evidencia empirica em nuvem real, cenario
web/PME, recencia, citacoes), e uma lista equilibrada por estrategia e sugerida.

Saidas em <saida>/prisma/ e <saida>/imagens/prisma_fluxograma.{svg,png}
"""
import csv
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gerar_redes import campo, ler_registros  # noqa: E402

N_LEITURA = 60          # tamanho da lista de leitura prioritaria
MIN_POR_ESTRATEGIA = 8  # garante diversidade na lista prioritaria

TIPOS_EXCLUIDOS = ("editorial material", "letter", "retraction", "retracted publication",
                   "correction", "meeting abstract", "book review", "news item")
IDIOMAS = ("english", "portuguese")

ESTRATEGIAS = {
    "autoscaling": r"auto[- ]?scal|elastic(ity)? scal|horizontal scal|vertical scal|scale[- ](in|out)\b|"
                   r"elastic (resource|provision)|dynamic (resource )?provision|cloud elasticity|\belasticity\b",
    "spot/preemptible": r"spot (instance|market|price|vm|virtual)|preemptible|transient (server|instance|vm)|"
                        r"\bspot\b",
    "serverless/FaaS": r"serverless|function[- ]as[- ]a[- ]service|\bfaas\b|aws lambda|cloud functions",
    "reservada x sob demanda": r"reserved instance|on[- ]demand (instance|pricing|price)|savings plan|"
                               r"reservation (plan|strateg)|pricing (plan|option)s?|instance purchas",
    "desligamento/agendamento": r"shut ?down|power(ing)? off|turn(ing)? off|idle (resource|instance|vm)|"
                                r"off[- ]peak|working hours|scale to zero|hibernat",
    "right-sizing": r"right[- ]?siz|over[- ]?provision|under[- ]?provision|instance (type )?selection|"
                    r"vm (type|size) selection|resource (allocation|sizing)",
}
RE_ESTR = {k: re.compile(v, re.I) for k, v in ESTRATEGIAS.items()}

RE_NUM = re.compile(r"(\d+(?:[.,]\d+)?)\s?(%|percent|x\b|times|-fold|fold)", re.I)
RE_CUSTO = re.compile(r"cost|saving|expens|cheaper|price|pricing|bill|monetary|budget|\$|dollar|spend", re.I)
RE_REDUZ = re.compile(r"reduc|sav|lower|cheaper|less|decreas|cut|minimi|cheap", re.I)

RE_EMPIRICO = re.compile(r"amazon|aws|ec2|azure|google cloud|gcp|kubernetes|real[- ]world|production|"
                         r"case study|testbed|real (cloud|trace|workload)|deploy|experiment", re.I)
RE_WEB = re.compile(r"web (application|service|server|app|system)|e-?commerce|microservice|multi-tier|"
                    r"three-tier|relational database|rubis|tpc-w|wikipedia trace|business application|"
                    r"enterprise application|saas", re.I)
# temas distantes do cenario de PME (servir modelos de IA, GPU, HPC, robotica...)
RE_NICHO = re.compile(r"inference|\bllms?\b|large language|\bgpus?\b|deep learning|model serving|"
                      r"robot|bioinformatic|genom|scientific workflow|\bhpc\b|high performance comput|"
                      r"blockchain|vehicular|\buavs?\b|satellite", re.I)
RE_PME = re.compile(r"small and medium|\bsmes?\b|small business|\bstart-?ups\b|startup compan|small compan|"
                    r"small enterprise|medium[- ]sized", re.I)

FRASE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def frases_economia(ab):
    """Frases do resumo que quantificam reducao de custo."""
    out = []
    for f in FRASE.split(ab):
        if RE_NUM.search(f) and RE_CUSTO.search(f) and RE_REDUZ.search(f):
            out.append(f.strip())
    return out


def valores_pct(frases):
    vals = []
    for f in frases:
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s?(%|percent)", f, re.I):
            v = float(m.group(1))
            if 0 < v <= 100:
                vals.append(v)
    return vals


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    entrada, saida = sys.argv[1], sys.argv[2]
    pdir = os.path.join(saida, "prisma")
    idir = os.path.join(saida, "imagens")
    os.makedirs(pdir, exist_ok=True)
    os.makedirs(idir, exist_ok=True)

    todos, cont = [], {"E1": 0, "E2": 0, "E3": 0, "E4": 0}
    ut_vistos, duplicados = set(), 0
    for r in ler_registros(entrada):
        ut = campo(r, "UT")
        if ut in ut_vistos:
            duplicados += 1
            continue
        ut_vistos.add(ut)
        ti, ab = campo(r, "TI"), campo(r, "AB")
        kw = campo(r, "DE") + "; " + campo(r, "ID")
        texto = f"{ti} {ab} {kw}"
        dt, la = campo(r, "DT").lower(), campo(r, "LA").lower()
        d = {
            "UT": ut, "DOI": campo(r, "DI"), "Ano": campo(r, "PY"), "Titulo": ti,
            "Autores": "; ".join(r.get("AU", [])[:3]) + ("; et al." if len(r.get("AU", [])) > 3 else ""),
            "Fonte": campo(r, "SO"), "Tipo": campo(r, "DT"), "Citacoes": campo(r, "TC") or "0",
        }
        estr = [k for k, rx in RE_ESTR.items() if rx.search(texto)]
        frases = frases_economia(ab)
        d["Estrategias"] = "; ".join(estr)

        if any(t in dt for t in TIPOS_EXCLUIDOS) or not ab:
            d["Decisao"], d["Motivo"] = "excluido", "E1 tipo documental/sem resumo"
        elif la not in IDIOMAS:
            d["Decisao"], d["Motivo"] = "excluido", "E2 idioma"
        elif not estr:
            d["Decisao"], d["Motivo"] = "excluido", "E3 sem estrategia de elasticidade"
        elif not frases:
            d["Decisao"], d["Motivo"] = "excluido", "E4 sem economia quantificada"
        else:
            d["Decisao"], d["Motivo"] = "texto completo", ""
        if d["Motivo"]:
            cont[d["Motivo"][:2]] += 1

        vals = valores_pct(frases)
        d["Economia_%_resumo"] = "; ".join(f"{v:g}" for v in vals)
        d["Trecho_economia"] = " | ".join(frases)[:600]
        emp, web, pme = bool(RE_EMPIRICO.search(texto)), bool(RE_WEB.search(texto)), bool(RE_PME.search(texto))
        d["Empirico"], d["Web/BD"], d["PME"] = ("sim" if emp else ""), ("sim" if web else ""), ("sim" if pme else "")
        ano = int(d["Ano"]) if d["Ano"].isdigit() else 2000
        tc = int(d["Citacoes"]) if d["Citacoes"].isdigit() else 0
        nicho = bool(RE_NICHO.search(texto))
        d["Nicho"] = "sim" if nicho else ""
        score = 3 * emp + 2 * web + 3 * pme - 3 * nicho + (2 if ano >= 2019 else 1 if ano >= 2014 else 0) \
            + min(tc, 300) / 100 + 0.5 * len(estr) + (1 if "review" in dt else 0)
        d["Pontuacao"] = round(score, 2)
        d["_abstract"] = ab
        todos.append(d)

    cand = sorted([d for d in todos if d["Decisao"] == "texto completo"],
                  key=lambda d: -d["Pontuacao"])
    # mesmo trabalho indexado duas vezes (ex.: versao de evento e de periodico) -> lista so uma vez
    titulos, cand_unicos = set(), []
    for d in cand:
        t = re.sub(r"\W+", " ", d["Titulo"].lower()).strip()
        if t not in titulos:
            titulos.add(t); cand_unicos.append(d)

    # lista prioritaria: garante MIN_POR_ESTRATEGIA por estrategia, completa pela pontuacao
    escolhidos, ids = [], set()
    for est in ESTRATEGIAS:
        n = 0
        for d in cand_unicos:
            if n >= MIN_POR_ESTRATEGIA:
                break
            if est in d["Estrategias"].split("; ") and d["UT"] not in ids:
                escolhidos.append(d); ids.add(d["UT"]); n += 1
            elif est in d["Estrategias"].split("; "):
                n += 1
    for d in cand_unicos:
        if len(escolhidos) >= N_LEITURA:
            break
        if d["UT"] not in ids:
            escolhidos.append(d); ids.add(d["UT"])
    escolhidos.sort(key=lambda d: -d["Pontuacao"])

    cols = ["UT", "DOI", "Ano", "Autores", "Titulo", "Fonte", "Tipo", "Citacoes", "Estrategias",
            "Empirico", "Web/BD", "PME", "Nicho", "Pontuacao", "Economia_%_resumo", "Trecho_economia",
            "Decisao", "Motivo"]

    def grava(nome, linhas, extra=()):
        with open(os.path.join(pdir, nome), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols + list(extra))
            for d in linhas:
                w.writerow([d[c] for c in cols] + ["" for _ in extra])

    grava("triagem_completa.csv", todos)
    grava("candidatos_texto_completo.csv", cand)
    # lista de leitura ja com as colunas da planilha de extracao para o leitor preencher
    grava("leitura_prioritaria.csv", escolhidos,
          extra=("Incluir (S/N)", "Motivo exclusao (texto completo)", "Provedor", "Carga/aplicacao",
                 "Linha de base (fixo)", "Economia medida (%)", "Impacto no SLA/desempenho",
                 "Tipo de avaliacao (real/simulacao)", "Observacoes"))

    # resumos dos prioritarios em txt, para leitura rapida
    with open(os.path.join(pdir, "leitura_prioritaria_resumos.txt"), "w", encoding="utf-8") as f:
        for i, d in enumerate(escolhidos, 1):
            f.write(f"[{i}] {d['Autores']} ({d['Ano']}). {d['Titulo']}. {d['Fonte']}.\n")
            f.write(f"    DOI: {d['DOI'] or '-'} | citacoes: {d['Citacoes']} | estrategias: {d['Estrategias']}\n")
            f.write(f"    economia no resumo (%): {d['Economia_%_resumo'] or '-'}\n\n")
            f.write("    " + d["_abstract"] + "\n\n" + "-" * 90 + "\n\n")

    # estatisticas por estrategia entre os candidatos
    por_est = {}
    for est in ESTRATEGIAS:
        sub = [d for d in cand if est in d["Estrategias"].split("; ")]
        vals = sorted(v for d in sub for v in map(float, filter(None, d["Economia_%_resumo"].split("; "))))
        med = vals[len(vals) // 2] if vals else None
        por_est[est] = (len(sub), len(vals), med, vals[0] if vals else None, vals[-1] if vals else None)

    total = len(todos) + duplicados
    triados = len(todos)
    n_cand = len(cand)
    with open(os.path.join(pdir, "prisma_contagens.txt"), "w", encoding="utf-8") as f:
        f.write("PRISMA 2020 - contagens da triagem automatizada\n\n")
        f.write(f"Identificados na Web of Science ......................... {total}\n")
        f.write(f"Duplicados removidos (UT) ............................... {duplicados}\n")
        f.write(f"Registros triados (titulo/resumo/palavras-chave) ........ {triados}\n")
        f.write(f"  E1 tipo documental nao elegivel ou sem resumo ......... {cont['E1']}\n")
        f.write(f"  E2 idioma (nao ingles/portugues) ...................... {cont['E2']}\n")
        f.write(f"  E3 sem estrategia de elasticidade ..................... {cont['E3']}\n")
        f.write(f"  E4 sem economia de custo quantificada no resumo ....... {cont['E4']}\n")
        f.write(f"Encaminhados para leitura de texto completo ............. {n_cand}\n")
        f.write(f"Lista de leitura prioritaria ............................ {len(escolhidos)}\n\n")
        f.write("Candidatos por estrategia (um artigo pode ter varias):\n")
        f.write(f"  {'estrategia':28s} {'artigos':>7s} {'valores %':>9s} {'mediana':>8s} {'min':>6s} {'max':>6s}\n")
        for est, (n, nv, med, mn, mx) in por_est.items():
            fmt = lambda x: f"{x:g}" if x is not None else "-"
            f.write(f"  {est:28s} {n:7d} {nv:9d} {fmt(med):>8s} {fmt(mn):>6s} {fmt(mx):>6s}\n")
        f.write("\nObs.: os percentuais vem do resumo (extracao automatica) e servem apenas para\n"
                "orientar a leitura; os valores do artigo devem ser conferidos no texto completo.\n")

    with open(os.path.join(pdir, "estrategias_resumo.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Estrategia", "Artigos candidatos", "Valores % extraidos", "Mediana %", "Min %", "Max %"])
        for est, t in por_est.items():
            w.writerow([est, *["" if x is None else x for x in t]])

    fluxograma(idir, total, duplicados, triados, cont, n_cand, len(escolhidos))
    print(open(os.path.join(pdir, "prisma_contagens.txt"), encoding="utf-8").read())


def fluxograma(idir, total, dup, triados, cont, n_cand, n_prio):
    def n(x):
        return f"{x:,}".replace(",", ".")
    W, H = 1000, 860
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="DejaVu Sans, Arial, sans-serif">',
         f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
         '<defs><marker id="a" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">'
         '<path d="M0,0 L10,5 L0,10 z" fill="#444"/></marker></defs>']

    def caixa(x, y, w, h, linhas, fill="#eef3fb", stroke="#3b6fb6", bold_first=True):
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        ty = y + (h - 20 * len(linhas)) / 2 + 15
        for i, t in enumerate(linhas):
            wgt = "bold" if (i == 0 and bold_first) else "normal"
            s.append(f'<text x="{x + w / 2}" y="{ty + 20 * i}" font-size="15" text-anchor="middle" '
                     f'font-weight="{wgt}" fill="#222">{t}</text>')

    def seta(x1, y1, x2, y2):
        s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#444" stroke-width="1.5" marker-end="url(#a)"/>')

    def etapa(y, h, nome):
        s.append(f'<rect x="10" y="{y}" width="34" height="{h}" rx="4" fill="#3b6fb6"/>')
        s.append(f'<text x="27" y="{y + h / 2}" font-size="14" fill="#fff" font-weight="bold" text-anchor="middle" '
                 f'transform="rotate(-90 27 {y + h / 2})">{nome}</text>')

    s.append(f'<text x="{W / 2}" y="32" font-size="20" font-weight="bold" text-anchor="middle" fill="#222">'
             'Fluxograma PRISMA 2020 da revisão</text>')
    L, CW, R, RW = 70, 400, 540, 430
    etapa(60, 120, "Identificação")
    caixa(L, 70, CW, 100, ["Registros identificados", "Web of Science Core Collection", f"(n = {n(total)})"])
    caixa(R, 70, RW, 100, ["Removidos antes da triagem", f"Duplicados (UT): n = {n(dup)}"], fill="#fbf1ee", stroke="#b65a3b")
    seta(L + CW, 120, R, 120)

    etapa(210, 300, "Triagem")
    caixa(L, 220, CW, 90, ["Registros triados", "(título, resumo e palavras-chave)", f"(n = {n(triados)})"])
    seta(L + CW / 2, 170, L + CW / 2, 220)
    caixa(R, 220, RW, 180, ["Registros excluídos", f"E1 tipo/sem resumo: n = {n(cont['E1'])}",
                             f"E2 idioma: n = {n(cont['E2'])}", f"E3 sem estratégia elástica: n = {n(cont['E3'])}",
                             f"E4 sem economia quantificada: n = {n(cont['E4'])}"], fill="#fbf1ee", stroke="#b65a3b")
    seta(L + CW, 265, R, 265)
    caixa(L, 420, CW, 90, ["Encaminhados para texto completo", f"(n = {n(n_cand)})",
                            f"leitura prioritária: n = {n(n_prio)}"])
    seta(L + CW / 2, 310, L + CW / 2, 420)

    etapa(540, 140, "Elegibilidade")
    caixa(L, 550, CW, 110, ["Textos completos avaliados", "(n = a preencher)"], fill="#f5f5f5", stroke="#888")
    seta(L + CW / 2, 510, L + CW / 2, 550)
    caixa(R, 550, RW, 110, ["Excluídos na leitura completa", "sem linha de base fixa: n = …",
                             "sem dados de custo: n = …", "texto indisponível: n = …"], fill="#f5f5f5", stroke="#888")
    seta(L + CW, 605, R, 605)

    etapa(710, 110, "Inclusão")
    caixa(L, 720, CW, 90, ["Estudos incluídos na síntese", "(n = a preencher)"], fill="#eef8ee", stroke="#3b8f4a")
    seta(L + CW / 2, 660, L + CW / 2, 720)
    s.append(f'<text x="{W - 20}" y="{H - 14}" font-size="11" text-anchor="end" fill="#777">'
             'Etapas de identificação e triagem automatizadas (scripts em analise/); elegibilidade e inclusão por leitura manual.</text>')
    s.append("</svg>")
    svg = os.path.join(idir, "prisma_fluxograma.svg")
    with open(svg, "w", encoding="utf-8") as f:
        f.write("\n".join(s))
    conv = shutil.which("magick") or shutil.which("convert")
    if conv:
        subprocess.run([conv, "-density", "150", svg, os.path.join(idir, "prisma_fluxograma.png")],
                       check=False, capture_output=True)


if __name__ == "__main__":
    main()
