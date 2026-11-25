#!/usr/bin/env python3
"""
calculo_custos.py - Cálculo ilustrativo do custo mensal de um sistema web de PME
(aplicação + banco) na AWS São Paulo (sa-east-1), comparando o provisionamento
fixo dimensionado para o pico com estratégias elásticas.

Uso:  python3 analise/calculo_custos.py dados/precos_aws_sa-east-1.csv resultados

Cenários (camada de aplicação; o banco e o balanceador são iguais em todos):
  A  Fixo no pico, sob demanda, 24/7          (linha de base)
  B  Fixo no pico, instâncias reservadas 1 ano (compra mais barata, sem elasticidade)
  C  Agendado: capacidade de pico no horário comercial, mínimo fora dele
  D  Autoscaling reativo (target tracking), mínimo de 2 VMs
  E  Autoscaling + base reservada (as 2 VMs mínimas reservadas, extras sob demanda)

Modelo:
  - Uma semana típica em intervalos de 15 min, extrapolada para 730 h/mês.
  - A demanda (requisições/s) segue o horário comercial de Goiânia, com ruído
    e um pico promocional curto; parâmetros em PERFIL.
  - Cada VM atende CAP_ALVO req/s na utilização-alvo (60%); acima de 85% de
    utilização o intervalo conta como "risco de degradação" (proxy do SLA).
  - O autoscaling reativo decide com a demanda do intervalo ANTERIOR (atraso de
    reação) e só reduz após 30 min de folga (cooldown), como o target tracking.
  - O EC2 Linux é cobrado por segundo, então custo = horas de VM x preço/hora.

Limitações (declarar no trabalho): não inclui EBS das VMs, transferência de
dados, impostos/IOF, nem o tempo de boot das VMs dentro do intervalo de 15 min.
"""
import csv
import math
import os
import random
import shutil
import subprocess
import sys

# ------------------------- parâmetros do cenário -------------------------
INSTANCIA = "t3.medium"          # VM da aplicação (2 vCPU, 4 GiB)
BANCO = ("db.t3.medium", "Single-AZ")
BANCO_GB = 50
CAP_ALVO = 25.0                  # req/s por VM na utilização-alvo de 60%
UTIL_ALVO = 0.60
UTIL_RISCO = 0.85                # acima disso: risco de degradação do SLA
MIN_VMS = 2                      # alta disponibilidade (2 zonas)
REQ_POR_LCU = 25.0               # aproximação: 1 LCU ~ 25 novas conexões/s
HORAS_MES = 730
SEMENTE = 42

PERFIL = {                       # requisições/s
    "pico": 100.0,               # manhã e tarde em dia útil
    "almoco": 60.0,
    "noite": 5.0,                # madrugada / domingo
    "sabado": 40.0,              # sábado de manhã
    "ruido": 0.10,               # +-10% aleatório
    "promo": (1, 15.0, 1.5),     # terça-feira (dia 1), 15h, demanda x1,5 por 30 min
}
# expediente para o cenário agendado (C): seg-sex 7h-22h (cobre o uso à noite), sáb 7h-13h
AGENDA = {0: (7, 22), 1: (7, 22), 2: (7, 22), 3: (7, 22), 4: (7, 22), 5: (7, 13)}

DIAS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


def le_precos(path):
    p = {}
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            p[(r["servico"], r["item"], r["modalidade"])] = float(r["usd_por_unidade"])
    return p


def base_hora(dia, h, P):
    """Demanda média (req/s) na hora h (float) do dia (0 = segunda)."""
    if dia == 6:
        return P["noite"]
    if dia == 5:
        return P["sabado"] if 8 <= h < 13 else P["noite"] * 2 if 7 <= h < 22 else P["noite"]
    if h < 7 or h >= 22:
        return P["noite"]
    if h < 9:                                   # rampa da manhã
        return P["noite"] + (P["pico"] - P["noite"]) * (h - 7) / 2
    if 12 <= h < 13.5:
        return P["almoco"]
    if h < 18:
        return P["pico"]
    return P["pico"] - (P["pico"] - 15) * (h - 18) / 4   # cai até 22h


def demanda_semana(P, semente=SEMENTE):
    rnd = random.Random(semente)
    d = []
    for dia in range(7):
        for q in range(96):
            h = q / 4
            v = base_hora(dia, h, P) * (1 + rnd.uniform(-P["ruido"], P["ruido"]))
            pd, ph, mult = P["promo"]
            if dia == pd and ph <= h < ph + 0.5:
                v *= mult
            d.append(v)
    return d


def vms_para(v):
    return max(MIN_VMS, math.ceil(v / CAP_ALVO))


def politica_fixa(dem):
    n = max(vms_para(v) for v in dem)
    return [n] * len(dem)


def politica_agendada(dem):
    n = max(vms_para(v) for v in dem)
    out = []
    for i in range(len(dem)):
        dia, h = divmod(i, 96)
        ini, fim = AGENDA.get(dia, (0, 0))
        out.append(n if ini <= h / 4 < fim else MIN_VMS)
    return out


def politica_reativa(dem):
    out, atual, folga = [], vms_para(dem[-1]), 0
    for i in range(len(dem)):
        alvo = vms_para(dem[i - 1])            # decide com o intervalo anterior
        if alvo > atual:
            atual, folga = alvo, 0
        elif alvo < atual:
            folga += 1
            if folga >= 2:                     # cooldown de 30 min para reduzir
                atual, folga = alvo, 0
        else:
            folga = 0
        out.append(atual)
    return out


def avalia(dem, vms):
    risco = sum(1 for v, n in zip(dem, vms) if v / (n * CAP_ALVO / UTIL_ALVO) > UTIL_RISCO)
    util = sum(v / (n * CAP_ALVO / UTIL_ALVO) for v, n in zip(dem, vms)) / len(dem)
    return risco, util


def custos(dem, vms, preco_vm_od, preco_vm_res, base_reservada, precos):
    fator = HORAS_MES / 168.0
    vm_h_sem = sum(vms) / 4
    if base_reservada == "todas":
        app = vm_h_sem * preco_vm_res
    elif base_reservada:
        res_h = base_reservada * 168
        app = res_h * preco_vm_res + (vm_h_sem - res_h) * preco_vm_od
    else:
        app = vm_h_sem * preco_vm_od
    app *= fator
    banco = precos[("RDS PostgreSQL",) + BANCO] * HORAS_MES + \
        precos[("RDS PostgreSQL", "armazenamento gp3", BANCO[1])] * BANCO_GB
    lcu_h = sum(max(1.0, v / REQ_POR_LCU) for v in dem) / 4 * fator
    lb = precos[("ALB", "Application Load Balancer", "sob demanda")] * HORAS_MES + \
        precos[("ALB", "LCU", "sob demanda")] * lcu_h
    return app, banco, lb, vm_h_sem * fator


def roda(P, precos):
    od = precos[("EC2", INSTANCIA, "sob demanda (Linux)")]
    rs = precos[("EC2", INSTANCIA, "reservada 1 ano sem entrada (Standard)")]
    dem = demanda_semana(P)
    pol = {
        "A": ("Fixo no pico (sob demanda)", politica_fixa(dem), None),
        "B": ("Fixo no pico (reservada 1 ano)", politica_fixa(dem), "todas"),
        "C": ("Agendado (desliga fora do expediente)", politica_agendada(dem), None),
        "D": ("Autoscaling reativo", politica_reativa(dem), None),
        "E": ("Autoscaling + base reservada", politica_reativa(dem), MIN_VMS),
    }
    res = {}
    for k, (nome, vms, reserva) in pol.items():
        app, banco, lb, vmh = custos(dem, vms, od, rs, reserva, precos)
        risco, util = avalia(dem, vms)
        res[k] = dict(nome=nome, vms=vms, app=app, banco=banco, lb=lb, total=app + banco + lb,
                      vm_horas=vmh, risco=risco, util=util)
    return dem, res


# ------------------------------- gráficos -------------------------------
COR = {"s1": "#2a78d6", "s2": "#eb6834", "s3": "#1baf7a", "txt": "#0b0b0b", "txt2": "#52514e",
       "grade": "#e4e3df", "fundo": "#fcfcfb", "neutro": "#8a8984"}
FONTE = 'font-family="DejaVu Sans, Arial, sans-serif"'


def salva_svg(path, partes, W, H):
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" {FONTE}>',
           f'<rect width="{W}" height="{H}" fill="{COR["fundo"]}"/>'] + partes + ["</svg>"]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))
    conv = shutil.which("magick") or shutil.which("convert")
    if conv:
        subprocess.run([conv, "-density", "150", path, path[:-4] + ".png"], check=False, capture_output=True)


def txt(x, y, s, size=14, cor=None, anchor="start", peso="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{cor or COR["txt"]}" '
            f'text-anchor="{anchor}" font-weight="{peso}">{s}</text>')


def grafico_semana(path, dem, res):
    W, H, L, R, T, B = 1100, 500, 70, 210, 70, 60
    pw, ph = W - L - R, H - T - B
    n = len(dem)
    ymax = max(max(res["A"]["vms"]), max(v / CAP_ALVO for v in dem)) + 1
    X = lambda i: L + pw * i / n
    Y = lambda v: T + ph * (1 - v / ymax)
    p = [txt(L, 32, "Semana típica: VMs ligadas por estratégia", 20, peso="bold"),
         txt(L, 54, f"Demanda convertida em VMs necessárias ({INSTANCIA}, alvo de {int(UTIL_ALVO*100)}% de CPU)",
             13, COR["txt2"])]
    for v in range(0, int(ymax) + 1):
        p.append(f'<line x1="{L}" x2="{L+pw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{COR["grade"]}" stroke-width="1"/>')
        p.append(txt(L - 10, Y(v) + 5, str(v), 12, COR["txt2"], "end"))
    for d in range(7):
        x = X(d * 96)
        p.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{T}" y2="{T+ph}" stroke="{COR["grade"]}" stroke-width="1"/>')
        p.append(txt(X(d * 96 + 48), T + ph + 22, DIAS[d], 13, COR["txt2"], "middle"))
    p.append(txt(18, T + ph / 2, "VMs", 13, COR["txt2"], "middle"))
    # área: necessário (neutro)
    pts = " ".join(f"{X(i):.1f},{Y(v / CAP_ALVO):.1f}" for i, v in enumerate(dem))
    p.append(f'<polygon points="{X(0):.1f},{Y(0):.1f} {pts} {X(n-1):.1f},{Y(0):.1f}" fill="{COR["neutro"]}" fill-opacity="0.22"/>')

    def degrau(vms):
        s = [f"{X(0):.1f},{Y(vms[0]):.1f}"]
        for i in range(1, n):
            if vms[i] != vms[i - 1]:
                s.append(f"{X(i):.1f},{Y(vms[i-1]):.1f}")
                s.append(f"{X(i):.1f},{Y(vms[i]):.1f}")
        s.append(f"{X(n):.1f},{Y(vms[-1]):.1f}")
        return " ".join(s)
    series = [("A", COR["s1"], "Fixo no pico"), ("C", COR["s2"], "Agendado"), ("D", COR["s3"], "Autoscaling")]
    for k, c, _ in series:
        p.append(f'<polyline points="{degrau(res[k]["vms"])}" fill="none" stroke="{c}" stroke-width="2" '
                 f'stroke-linejoin="round"/>')
    # legenda à direita (identidade nunca só pela cor: nome + traço)
    ly = T + 10
    for k, c, nome in series:
        p.append(f'<line x1="{L+pw+20}" x2="{L+pw+44}" y1="{ly}" y2="{ly}" stroke="{c}" stroke-width="3"/>')
        p.append(txt(L + pw + 52, ly + 5, nome, 13))
        p.append(txt(L + pw + 52, ly + 23, f'{res[k]["vm_horas"]:.0f} VM-h/mês', 12, COR["txt2"]))
        ly += 52
    p.append(f'<rect x="{L+pw+20}" y="{ly-8}" width="24" height="14" fill="{COR["neutro"]}" fill-opacity="0.35"/>')
    p.append(txt(L + pw + 52, ly + 4, "Necessário", 13))
    p.append(txt(L + pw + 52, ly + 22, "(demanda)", 12, COR["txt2"]))
    salva_svg(path, p, W, H)


def grafico_custos(path, res):
    W, H, L, R, T = 1100, 470, 330, 170, 90
    bh, gap = 46, 22
    chaves = ["A", "B", "C", "D", "E"]
    vmax = max(r["total"] for k, r in res.items() if k != "_cambio") * 1.02
    pw = W - L - R
    X = lambda v: L + pw * v / vmax
    base = res["A"]["total"]
    p = [txt(40, 34, "Custo mensal estimado por estratégia (R$)", 20, peso="bold"),
         txt(40, 56, f"Sistema web + PostgreSQL na AWS São Paulo · preços de 24/11/2026 · "
                     f"US$ 1 = R$ {res['_cambio']:.2f}".replace(".", ",", 1), 13, COR["txt2"])]
    segs = [("app", COR["s1"], "Aplicação (EC2)"), ("banco", COR["s2"], "Banco (RDS)"), ("lb", COR["s3"], "Balanceador (ALB)")]
    lx = 40
    for _, c, nome in segs:
        p.append(f'<rect x="{lx}" y="68" width="14" height="14" rx="3" fill="{c}"/>')
        p.append(txt(lx + 20, 80, nome, 13))
        lx += 190
    for j, k in enumerate(chaves):
        r = res[k]
        y = T + 10 + j * (bh + gap)
        p.append(txt(L - 14, y + bh / 2 - 2, f"{k}. {r['nome']}", 14, anchor="end"))
        if r["risco"]:
            p.append(txt(L - 14, y + bh / 2 + 16, f"⚠ {r['risco']} intervalos de 15 min sob risco de SLA",
                         11, COR["txt2"], "end"))
        x0 = L
        for i, (campo, c, _) in enumerate(segs):
            w = pw * r[campo] / vmax
            x1 = x0 + w - (2 if i < 2 else 0)          # 2px de folga entre segmentos
            ry = 4 if i == 2 else 0
            p.append(f'<rect x="{x0:.1f}" y="{y}" width="{max(0, x1 - x0):.1f}" height="{bh}" rx="{ry}" fill="{c}"/>')
            x0 += w
        eco = (1 - r["total"] / base) * 100
        rotulo = f"R$ {brl(r['total'])}" + ("" if k == "A" else f"  (−{eco:.0f}%)")
        p.append(txt(X(r["total"]) + 10, y + bh / 2 + 5, rotulo, 14, peso="bold"))
    salva_svg(path, p, W, T + 10 + len(chaves) * (bh + gap) + 20)


def grafico_sensibilidade(path, pontos):
    W, H, L, R, T, B = 1000, 460, 80, 200, 80, 70
    pw, ph = W - L - R, H - T - B
    xs = [x for x, _, _ in pontos]
    X = lambda v: L + pw * (v - xs[0]) / (xs[-1] - xs[0])
    Y = lambda v: T + ph * (1 - v / 70)
    p = [txt(L, 34, "Sistemas menores economizam menos", 20, peso="bold"),
         txt(L, 56, "Economia no custo total vs. fixo no pico, conforme o porte (o banco e o mínimo de 2 VMs pesam mais)",
             13, COR["txt2"])]
    for v in range(0, 71, 10):
        p.append(f'<line x1="{L}" x2="{L+pw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{COR["grade"]}"/>')
        p.append(txt(L - 10, Y(v) + 5, f"{v}%", 12, COR["txt2"], "end"))
    for x in xs:
        p.append(txt(X(x), T + ph + 22, f"{x:.0f}", 12, COR["txt2"], "middle"))
    p.append(txt(L + pw / 2, T + ph + 48, "VMs necessárias no pico (porte do sistema)", 13, COR["txt2"], "middle"))
    for idx, (c, nome) in enumerate([(COR["s2"], "Agendado"), (COR["s3"], "Autoscaling")], start=1):
        pts = " ".join(f"{X(pt[0]):.1f},{Y(pt[idx]):.1f}" for pt in pontos)
        p.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="2"/>')
        for x, *rest in pontos:
            p.append(f'<circle cx="{X(x):.1f}" cy="{Y(rest[idx-1]):.1f}" r="4" fill="{c}" stroke="{COR["fundo"]}" stroke-width="2"/>')
        lx, ly = X(xs[-1]) + 12, Y(pontos[-1][idx])
        p.append(txt(lx, ly + 5, f"{nome} ({pontos[-1][idx]:.0f}%)", 13))
    salva_svg(path, p, W, H)


def brl(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    precos = le_precos(sys.argv[1])
    cambio = precos[("Cambio", "USD/BRL PTAX venda", "24/11/2026")]
    out = os.path.join(sys.argv[2], "calculo")
    img = os.path.join(sys.argv[2], "imagens")
    os.makedirs(out, exist_ok=True)
    os.makedirs(img, exist_ok=True)

    dem, res = roda(PERFIL, precos)
    base = res["A"]["total"]
    with open(os.path.join(out, "cenarios.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Cenario", "Estrategia", "VM-horas/mes", "Aplicacao US$", "Banco US$", "Balanceador US$",
                    "Total US$", "Total R$", "Economia vs A (%)", "Economia so aplicacao (%)",
                    "Intervalos com risco de SLA", "Utilizacao media (%)"])
        for k, r in res.items():
            w.writerow([k, r["nome"], round(r["vm_horas"]), round(r["app"], 2), round(r["banco"], 2), round(r["lb"], 2),
                        round(r["total"], 2), round(r["total"] * cambio, 2), round((1 - r["total"] / base) * 100, 1),
                        round((1 - r["app"] / res["A"]["app"]) * 100, 1), r["risco"], round(r["util"] * 100, 1)])
    with open(os.path.join(out, "semana_15min.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["dia", "hora", "demanda_req_s", "vms_fixo", "vms_agendado", "vms_autoscaling"])
        for i, v in enumerate(dem):
            d, q = divmod(i, 96)
            w.writerow([DIAS[d], f"{q//4:02d}:{(q%4)*15:02d}", round(v, 1),
                        res["A"]["vms"][i], res["C"]["vms"][i], res["D"]["vms"][i]])

    # sensibilidade: porte do sistema (toda a curva de demanda escalada de 0,25x a 4x)
    pontos = []
    for f in (0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4):
        P = dict(PERFIL, **{k: PERFIL[k] * f for k in ("pico", "almoco", "noite", "sabado")})
        _, r2 = roda(P, precos)
        b = r2["A"]["total"]
        npico = r2["A"]["vms"][0]
        pontos.append((npico, (1 - r2["C"]["total"] / b) * 100, (1 - r2["D"]["total"] / b) * 100))
    with open(os.path.join(out, "sensibilidade.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["vms_no_pico_(fixo)", "economia_agendado_%", "economia_autoscaling_%"])
        for pt in pontos:
            w.writerow([pt[0], round(pt[1], 1), round(pt[2], 1)])

    # gráficos (valores em R$)
    res_brl = {k: dict(r, app=r["app"] * cambio, banco=r["banco"] * cambio, lb=r["lb"] * cambio,
                       total=r["total"] * cambio) for k, r in res.items()}
    res_brl["_cambio"] = cambio
    grafico_semana(os.path.join(img, "custo_semana_vms.svg"), dem, res)
    grafico_custos(os.path.join(img, "custo_mensal_cenarios.svg"),
                   {k: v for k, v in res_brl.items()} )
    grafico_sensibilidade(os.path.join(img, "custo_sensibilidade.svg"), pontos)

    linhas = [f"Cálculo ilustrativo - AWS São Paulo, {INSTANCIA} + {BANCO[0]} {BANCO[1]} ({BANCO_GB} GB) + ALB",
              f"Câmbio PTAX 24/11/2026: US$ 1 = R$ {cambio}", ""]
    for k, r in res.items():
        linhas.append(f"{k}  {r['nome']:40s} R$ {brl(r['total']*cambio):>10s}/mês  "
                      f"economia {100*(1-r['total']/base):5.1f}% (aplicação {100*(1-r['app']/res['A']['app']):5.1f}%)  "
                      f"VM-h {r['vm_horas']:6.0f}  risco SLA {r['risco']:3d}  util. média {100*r['util']:4.1f}%")
    linhas += ["", "Sensibilidade (porte: VMs no pico -> economia agendado / autoscaling):"]
    linhas += [f"  {a:3d} VMs no pico -> {b:5.1f}% / {c:5.1f}%" for a, b, c in pontos]
    with open(os.path.join(out, "resumo.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    print("\n".join(linhas))


if __name__ == "__main__":
    main()
