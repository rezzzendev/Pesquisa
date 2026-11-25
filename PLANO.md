# Plano da pesquisa

**Título:** Autoscaling como estratégia de FinOps: revisão sistemática e estimativa de economia de custos em nuvem para PMEs brasileiras

**Pergunta:** quanto uma PME pode economizar na nuvem ao trocar o provisionamento fixo, dimensionado para o pico, pelo autoscaling, mantendo o nível de serviço?

Detalhes de como fazer cada etapa: `PASSO_A_PASSO.md`.

Legenda: ✅ feito · 🔄 em andamento · ⬜ a fazer

---

## Parte 1: até o pôster

Cada etapa tem um **ponto de validação do autor**: o que foi feito por script ou ferramenta só é dado como concluído depois de conferido.

| # | Etapa | Como é feito | Validação do autor | Status |
|---|---|---|---|---|
| 1 | Coleta na Web of Science e junção dos lotes | exportação WoS + `merge_wos.c` | conferir a contagem (10.132 registros, 0 duplicados) e uma amostra do `wos_completo.txt` | ✅ execução · ⬜ validação |
| 2 | Bibliometria | `gerar_redes.py` + VOSviewer | conferir os parâmetros (limiares, sinônimos) e os mapas | ✅ execução · ⬜ validação |
| 3 | Recorte, título, pergunta e objetivos | decisão do autor | — | ✅ |
| 4 | Triagem PRISMA (10.132 → 123 → 31) | fase 1: `triagem_prisma.py` · fase 2: classificação dos resumos pelos critérios R1–R4 | conferir as 123 decisões em `analise/triagem_resumos.csv` (coluna "Conferido pelo autor") | ✅ execução · ⬜ validação |
| 5 | Cálculo de custo (AWS, Azure, Google Cloud) | AWS: `calculo_custos.py` (pronto) · Azure e Google: **autor**, estendendo o script | conferir as suposições (carga, tipos de máquina) e os preços | 🔄 |
| 6 | Leitura dos 10 artigos de prioridade 1 | **autor** | — | ⬜ |
| 7 | Síntese da literatura × cálculo | tabela a partir da planilha de leitura | interpretação do autor | ⬜ |
| 8 | Pôster | montagem com as figuras e tabelas | revisão do autor e da orientadora | ⬜ |
| 9 | Fala de 1 a 2 min ao lado do pôster e impressão | **autor** | — | ⬜ |

As etapas 5 e 6 **correm em paralelo**: o cálculo não depende da leitura.

Se a leitura (6) não terminar até o pôster, ele usa os números dos resumos, marcados como **resultados preliminares**.

## Parte 2: depois do pôster (iniciação científica / artigo)

| # | Etapa | Status |
|---|---|---|
| 10 | Ler os 21 artigos de prioridade 2 e fechar o PRISMA (elegibilidade e inclusão) | ⬜ |
| 11 | Escrever o artigo: introdução, método, resultados, discussão, conclusão | ⬜ |
| 12 | Revisão com a professora | ⬜ |
| 13 | (Opcional) Experimento real em pequena escala para validar o cálculo | ⬜ |
| 14 | Escolher o evento ou periódico e submeter | ⬜ |

---

## Onde está cada coisa

| Para… | Abra |
|---|---|
| ler os artigos | `resultados/prisma/LEITURA.md` (links) e `resultados/prisma/leitura_final_resumos.txt` |
| anotar a leitura | `resultados/prisma/leitura_final.csv` |
| figuras do pôster | `resultados/imagens/` |
| números da bibliometria | `resultados/tabelas/resumo.txt` |
| números do cálculo | `resultados/calculo/resumo.txt` |
| método e reprodução | `README.md` |

## Como ler cada artigo (15 a 20 min)

1. Leia o **resumo**, a seção de **avaliação/experimentos** e a **conclusão**.
2. Preencha no `leitura_final.csv`:
   - **Incluir (S/N)**
   - **Linha de base:** com o que o artigo compara (fixo, autoscaler padrão ou outro algoritmo)
   - **Economia medida (%)**
   - **Impacto no SLA/latência**
   - **Nuvem real ou simulação**
3. Se excluir, anote o motivo. Ele entra no fluxograma PRISMA.

## Commits sugeridos (ao fim de cada etapa)

```bash
git add -A
git commit -m "<etapa concluída>"
git push
```
