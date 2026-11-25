#!/usr/bin/env python3
"""
triagem_prisma.py - Triagem PRISMA 2020 da base WoS com recorte em AUTOSCALING
(inclui escalonamento agendado / desligamento fora do horario) e geracao do fluxograma.

Uso:  python3 analise/triagem_prisma.py wos_completo.txt resultados

Fase 1 - triagem automatica (titulo, resumo, palavras-chave), nesta ordem:
  E1  tipo documental nao elegivel (editorial, carta, retratacao...) ou sem resumo
  E2  idioma diferente de ingles ou portugues
  E3  nao aborda autoscaling / escalonamento elastico ou agendado
  E4  nao relata economia de custo QUANTIFICADA no resumo (percentual ou "x vezes"
      na mesma frase que um termo de custo e um verbo de reducao)
  --  versoes duplicadas do mesmo trabalho (mesmo titulo) -> mantida so uma
  E5  dominio de aplicacao fora do escopo de PMEs (servir modelos de IA/GPU, IoT/edge,
      HPC, workflows cientificos, robotica, blockchain, redes moveis...)

Fase 2 - classificacao dos resumos pelos criterios R1-R4, registrada em
  analise/triagem_resumos.csv  (colunas: UT, Titulo, Decisao, Codigo, Justificativa,
  Conferido pelo autor, Observacao do autor)
  Decisao = "ler" (vai para texto completo) ou "excluir", com o codigo:
  R1  a economia relatada nao e de custo de nuvem para quem contrata (energia,
      receita do provedor, preco de leilao...)
  R2  compara apenas com outros algoritmos academicos, sem referencia a
      provisionamento fixo ou a um autoscaler de mercado (HPA, AWS, limiar)
  R3  carga fora do cenario web/servico de negocio (lote, big data, streaming, jogos...)
  R4  autoscaling e periferico no trabalho (o foco e outro problema)

Saidas: <saida>/prisma/*  e  <saida>/imagens/prisma_fluxograma.{svg,png}
"""
import csv
import os
import re
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from gerar_redes import campo, ler_registros  # noqa: E402

CLASSIF = os.path.join(AQUI, "triagem_resumos.csv")

TIPOS_EXCLUIDOS = ("editorial material", "letter", "retraction", "retracted publication",
                   "correction", "meeting abstract", "book review", "news item")
IDIOMAS = ("english", "portuguese")

RE_FOCO = re.compile(
    r"auto[- ]?scal|elastic(ity)? scal|horizontal (pod )?scal|vertical (pod )?scal|scale[- ](in|out)\b|"
    r"elastic (resource|provision)|dynamic (resource )?provision|cloud elasticity|\belasticity\b|"
    r"shut ?down|power(ing)? off|turn(ing)? off|idle (resource|instance|vm)|off[- ]peak|working hours|"
    r"scale to zero|scheduled scaling|hibernat", re.I)
OUTRAS = {  # so para informacao (combinacoes com outras estrategias)
    "spot": r"spot (instance|market|price|vm)|preemptible|transient (server|instance)",
    "serverless": r"serverless|function[- ]as[- ]a[- ]service|\bfaas\b|aws lambda",
    "reservada": r"reserved instance|savings plan|on[- ]demand (instance|pricing|price)",
}
RE_OUTRAS = {k: re.compile(v, re.I) for k, v in OUTRAS.items()}

RE_NUM = re.compile(r"(\d+(?:[.,]\d+)?)\s?(%|percent|x\b|times|-fold|fold)", re.I)
RE_CUSTO = re.compile(r"cost|saving|expens|cheaper|price|pricing|bill|monetary|budget|\$|dollar|spend", re.I)
RE_REDUZ = re.compile(r"reduc|sav|lower|cheaper|less|decreas|cut|minimi|cheap", re.I)

RE_EMPIRICO = re.compile(r"amazon|aws|ec2|azure|google cloud|gcp|kubernetes|real[- ]world|production|"
                         r"case study|testbed|real (cloud|trace|workload)|deploy|experiment", re.I)
RE_WEB = re.compile(r"web (application|service|server|app|system)|e-?commerce|microservice|multi-tier|"
                    r"three-tier|relational database|rubis|tpc-w|wikipedia trace|business application|"
                    r"enterprise application|saas", re.I)
RE_NICHO = re.compile(r"inference|\bllms?\b|large language|\bgpus?\b|deep learning model|model serving|"
                      r"robot|bioinformatic|genom|scientific workflow|\bhpc\b|high performance comput|"
                      r"blockchain|vehicular|\buavs?\b|satellite|\biot\b|internet of things|edge comput|"
                      r"fog comput|\b5g\b|\b6g\b|nextg|radio access|network function virtuali|\bnfv\b", re.I)
RE_PME = re.compile(r"small and medium|\bsmes?\b|small business|\bstart-?ups\b|startup compan|small compan|"
                    r"small enterprise|medium[- ]sized|small[- ]scale web", re.I)

FRASE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def frases_economia(ab):
    return [f.strip() for f in FRASE.split(ab)
            if RE_NUM.search(f) and RE_CUSTO.search(f) and RE_REDUZ.search(f)]


def valores_pct(frases):
    vals = []
    for f in frases:
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s?(%|percent)", f, re.I):
            v = float(m.group(1))
            if 0 < v <= 100:
                vals.append(v)
    return vals


def le_classificacao():
    if not os.path.exists(CLASSIF):
        return {}
    with open(CLASSIF, encoding="utf-8") as f:
        return {r["UT"]: r for r in csv.DictReader(f)}


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    entrada, saida = sys.argv[1], sys.argv[2]
    pdir, idir = os.path.join(saida, "prisma"), os.path.join(saida, "imagens")
    os.makedirs(pdir, exist_ok=True)
    os.makedirs(idir, exist_ok=True)
    classif = le_classificacao()

    todos, ut_vistos, titulos = [], set(), set()
    dup_ut = 0
    for r in ler_registros(entrada):
        ut = campo(r, "UT")
        if ut in ut_vistos:
            dup_ut += 1
            continue
        ut_vistos.add(ut)
        ti, ab = campo(r, "TI"), campo(r, "AB")
        texto = f"{ti} {ab} {campo(r, 'DE')}; {campo(r, 'ID')}"
        dt, la = campo(r, "DT").lower(), campo(r, "LA").lower()
        aus = r.get("AU", [])
        d = {"UT": ut, "DOI": campo(r, "DI"), "Ano": campo(r, "PY"), "Titulo": ti,
             "Autores": "; ".join(aus[:3]) + ("; et al." if len(aus) > 3 else ""),
             "Fonte": campo(r, "SO"), "Tipo": campo(r, "DT"), "Citacoes": campo(r, "TC") or "0",
             "Combina_com": "; ".join(k for k, rx in RE_OUTRAS.items() if rx.search(texto)),
             "_abstract": ab}
        frases = frases_economia(ab)
        d["Economia_%_resumo"] = "; ".join(f"{v:g}" for v in valores_pct(frases))
        d["Trecho_economia"] = " | ".join(frases)[:600]
        emp, web, pme = (bool(rx.search(texto)) for rx in (RE_EMPIRICO, RE_WEB, RE_PME))
        d["Empirico"], d["Web/BD"], d["PME"] = ("sim" if emp else ""), ("sim" if web else ""), ("sim" if pme else "")
        ano = int(d["Ano"]) if d["Ano"].isdigit() else 2000
        tc = int(d["Citacoes"]) if d["Citacoes"].isdigit() else 0
        d["Pontuacao"] = round(3 * emp + 2 * web + 3 * pme + (2 if ano >= 2019 else 1 if ano >= 2014 else 0)
                               + min(tc, 300) / 100, 2)

        tnorm = re.sub(r"\W+", " ", ti.lower()).strip()
        if any(t in dt for t in TIPOS_EXCLUIDOS) or not ab:
            motivo = "E1 tipo documental/sem resumo"
        elif la not in IDIOMAS:
            motivo = "E2 idioma"
        elif not RE_FOCO.search(texto):
            motivo = "E3 sem autoscaling/escalonamento"
        elif not frases:
            motivo = "E4 sem economia quantificada"
        elif tnorm in titulos:
            motivo = "D  versao duplicada (mesmo titulo)"
        elif RE_NICHO.search(texto):
            titulos.add(tnorm)
            motivo = "E5 dominio fora do escopo"
        else:
            titulos.add(tnorm)
            c = classif.get(ut)
            if not c:
                motivo = "pendente"
            elif c["Decisao"].strip().lower() == "ler":
                motivo = "LER"
            else:
                motivo = f"{c['Codigo'].strip()} {c['Justificativa'].strip()}"
            d["Justificativa"] = c["Justificativa"] if c else ""
        d["Motivo"] = motivo
        todos.append(d)

    def conta(prefixo):
        return sum(1 for d in todos if d["Motivo"].startswith(prefixo))

    resumos = [d for d in todos if d["Motivo"] == "pendente" or d["Motivo"] == "LER"
               or re.match(r"R\d", d["Motivo"])]
    ler = sorted([d for d in todos if d["Motivo"] == "LER"], key=lambda d: -d["Pontuacao"])
    pend = [d for d in todos if d["Motivo"] == "pendente"]

    cols = ["UT", "DOI", "Ano", "Autores", "Titulo", "Fonte", "Citacoes", "Combina_com", "Empirico",
            "Web/BD", "PME", "Pontuacao", "Economia_%_resumo", "Trecho_economia", "Motivo"]

    def grava(nome, linhas, extra=(), pre=None):
        with open(os.path.join(pdir, nome), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols + list(extra))
            for d in linhas:
                w.writerow([d[c] for c in cols] + [pre(d, e) if pre else "" for e in extra])

    grava("triagem_completa.csv", todos)
    grava("resumos_triados.csv", sorted(resumos, key=lambda d: -d["Pontuacao"]))
    grava("leitura_final.csv", ler,
          extra=("Por que ler (triagem)", "Incluir (S/N)", "Motivo exclusao (texto completo)", "Provedor",
                 "Aplicacao/carga", "Tipo de autoscaling (reativo/preditivo/agendado)",
                 "Linha de base (fixo/HPA/outro)", "Economia medida (%)", "Impacto no SLA/latencia",
                 "Avaliacao (nuvem real/simulacao)", "Observacoes"),
          pre=lambda d, e: d.get("Justificativa", "") if e == "Por que ler (triagem)" else "")

    def grava_txt(nome, linhas):
        with open(os.path.join(pdir, nome), "w", encoding="utf-8") as f:
            for i, d in enumerate(linhas, 1):
                f.write(f"[{i}] {d['Autores']} ({d['Ano']}). {d['Titulo']}. {d['Fonte']}.\n")
                f.write(f"    DOI: {d['DOI'] or '-'} | citacoes: {d['Citacoes']} | UT: {d['UT']}\n")
                if d.get("Justificativa"):
                    f.write(f"    por que ler: {d['Justificativa']}\n")
                f.write("\n    " + d["_abstract"] + "\n\n" + "-" * 90 + "\n\n")

    grava_txt("leitura_final_resumos.txt", ler)
    if pend:
        grava_txt("pendentes_resumos.txt", pend)

    n = {"total": len(todos) + dup_ut, "dup_ut": dup_ut, "triados": len(todos),
         "E1": conta("E1"), "E2": conta("E2"), "E3": conta("E3"), "E4": conta("E4"),
         "D": conta("D "), "E5": conta("E5"), "resumos": len(resumos),
         "R1": conta("R1"), "R2": conta("R2"), "R3": conta("R3"), "R4": conta("R4"),
         "ler": len(ler), "pend": len(pend)}
    linhas = [
        "PRISMA 2020 - recorte: autoscaling (inclui escalonamento agendado)", "",
        f"Identificados na Web of Science ............................ {n['total']}",
        f"Duplicados removidos (UT) .................................. {n['dup_ut']}",
        f"Triados automaticamente (titulo/resumo/palavras-chave) ..... {n['triados']}",
        f"  E1 tipo documental nao elegivel ou sem resumo ............ {n['E1']}",
        f"  E2 idioma (nao ingles/portugues) ......................... {n['E2']}",
        f"  E3 sem autoscaling/escalonamento elastico ................ {n['E3']}",
        f"  E4 sem economia de custo quantificada no resumo .......... {n['E4']}",
        f"  versoes duplicadas do mesmo trabalho ..................... {n['D']}",
        f"  E5 dominio fora do escopo (IA/GPU, IoT/edge, HPC...) ..... {n['E5']}",
        f"Resumos avaliados (criterios R1-R4) ........................ {n['resumos']}",
        f"  R1 economia nao e custo de nuvem do contratante .......... {n['R1']}",
        f"  R2 so compara com outros algoritmos academicos ........... {n['R2']}",
        f"  R3 carga fora do cenario web/servico de negocio .......... {n['R3']}",
        f"  R4 autoscaling periferico no trabalho .................... {n['R4']}",
        f"Encaminhados para leitura de texto completo ................ {n['ler']}",
    ]
    if pend:
        linhas.append(f"  (ainda sem classificacao: {n['pend']} - ver pendentes_resumos.txt)")
    with open(os.path.join(pdir, "prisma_contagens.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    fluxograma(idir, n)
    print("\n".join(linhas))


def fluxograma(idir, n):
    def f(x):
        return f"{x:,}".replace(",", ".")
    W, H = 1000, 1010
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="DejaVu Sans, Arial, sans-serif">',
         f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
         '<defs><marker id="a" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">'
         '<path d="M0,0 L10,5 L0,10 z" fill="#444"/></marker></defs>']

    def caixa(x, y, w, h, linhas, fill="#eef3fb", stroke="#3b6fb6"):
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        ty = y + (h - 20 * len(linhas)) / 2 + 15
        for i, t in enumerate(linhas):
            s.append(f'<text x="{x + w / 2}" y="{ty + 20 * i}" font-size="15" text-anchor="middle" '
                     f'font-weight="{"bold" if i == 0 else "normal"}" fill="#222">{t}</text>')

    def seta(x1, y1, x2, y2):
        s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#444" stroke-width="1.5" marker-end="url(#a)"/>')

    def etapa(y, h, nome):
        s.append(f'<rect x="10" y="{y}" width="34" height="{h}" rx="4" fill="#3b6fb6"/>')
        s.append(f'<text x="27" y="{y + h / 2}" font-size="14" fill="#fff" font-weight="bold" text-anchor="middle" '
                 f'transform="rotate(-90 27 {y + h / 2})">{nome}</text>')

    exc = dict(fill="#fbf1ee", stroke="#b65a3b")
    cinza = dict(fill="#f5f5f5", stroke="#888")
    s.append(f'<text x="{W / 2}" y="32" font-size="20" font-weight="bold" text-anchor="middle" fill="#222">'
             'Fluxograma PRISMA 2020 — recorte: autoscaling</text>')
    L, CW, R, RW = 70, 400, 540, 430
    cx = L + CW / 2

    etapa(60, 110, "Identificação")
    caixa(L, 65, CW, 100, ["Registros identificados", "Web of Science Core Collection", f"(n = {f(n['total'])})"])
    caixa(R, 65, RW, 100, ["Removidos antes da triagem", f"Duplicados (UT): n = {f(n['dup_ut'])}"], **exc)
    seta(L + CW, 115, R, 115)

    etapa(195, 500, "Triagem")
    caixa(L, 200, CW, 90, ["Registros triados (automático)", "título, resumo e palavras-chave", f"(n = {f(n['triados'])})"])
    seta(cx, 165, cx, 200)
    caixa(R, 200, RW, 170, ["Excluídos automaticamente",
                             f"E1 tipo/sem resumo: n = {f(n['E1'])}  ·  E2 idioma: n = {f(n['E2'])}",
                             f"E3 sem autoscaling: n = {f(n['E3'])}",
                             f"E4 sem economia quantificada: n = {f(n['E4'])}",
                             f"versões duplicadas: n = {f(n['D'])}",
                             f"E5 domínio fora do escopo: n = {f(n['E5'])}"], **exc)
    seta(L + CW, 245, R, 245)
    caixa(L, 400, CW, 90, ["Resumos avaliados", "(critérios R1–R4)", f"(n = {f(n['resumos'])})"])
    seta(cx, 290, cx, 400)
    caixa(R, 400, RW, 140, ["Resumos excluídos",
                             f"R1 economia não é custo de nuvem: n = {f(n['R1'])}",
                             f"R2 só compara com outros algoritmos: n = {f(n['R2'])}",
                             f"R3 carga fora do cenário web: n = {f(n['R3'])}",
                             f"R4 autoscaling periférico: n = {f(n['R4'])}"], **exc)
    seta(L + CW, 445, R, 445)
    caixa(L, 600, CW, 90, ["Encaminhados para texto completo", f"(n = {f(n['ler'])})"])
    seta(cx, 490, cx, 600)

    etapa(720, 130, "Elegibilidade")
    caixa(L, 730, CW, 110, ["Textos completos avaliados", "(n = a preencher)"], **cinza)
    seta(cx, 690, cx, 730)
    caixa(R, 730, RW, 110, ["Excluídos na leitura completa", "sem linha de base comparável: n = …",
                             "sem dados de custo: n = …", "texto indisponível: n = …"], **cinza)
    seta(L + CW, 785, R, 785)

    etapa(870, 100, "Inclusão")
    caixa(L, 875, CW, 90, ["Estudos incluídos na síntese", "(n = a preencher)"], fill="#eef8ee", stroke="#3b8f4a")
    seta(cx, 840, cx, 875)
    s.append(f'<text x="{W - 20}" y="{H - 14}" font-size="11" text-anchor="end" fill="#777">'
             'Triagem automática e classificação dos resumos: scripts e critérios em analise/.</text>')
    s.append("</svg>")
    svg = os.path.join(idir, "prisma_fluxograma.svg")
    with open(svg, "w", encoding="utf-8") as fh:
        fh.write("\n".join(s))
    conv = shutil.which("magick") or shutil.which("convert")
    if conv:
        subprocess.run([conv, "-density", "150", svg, os.path.join(idir, "prisma_fluxograma.png")],
                       check=False, capture_output=True)


if __name__ == "__main__":
    main()
