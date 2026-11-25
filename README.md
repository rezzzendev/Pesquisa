# FinOps e custo de nuvem em PMEs — Análise bibliométrica (Web of Science + VOSviewer)

**Pergunta de pesquisa:** quanto uma PME economiza ao trocar provisionamento fixo (dimensionado para o pico) por elasticidade (autoscaling, spot instances, serverless ou desligamento fora do horário), mantendo o nível de serviço?

Esta etapa é o levantamento bibliométrico que fundamenta o trabalho.

## 1. Coleta (Web of Science)

| Item | Valor |
|---|---|
| Base | Web of Science Core Collection (acesso via Portal CAPES) |
| Data da coleta | 22/11/2026 |
| Campo | TS (título, resumo, palavras-chave do autor e Keywords Plus) |
| Registros | **10.132** (Article 4.928; Proceedings Paper 4.759; Review 226; outros) |
| Período | 2002–2027 |
| Exportação | Plain text, *Full Record and Cited References*, 21 lotes de 500 |

String de busca:

```
TS=(("cloud computing" OR "cloud service*" OR "public cloud" OR "cloud infrastructure*" OR "cloud resource*" OR "cloud provider*" OR "cloud application*" OR serverless OR "function as a service" OR "spot instance*" OR autoscal* OR "auto-scal*" OR "auto scal*" OR "elastic cloud" OR "cloud elasticity") AND ("cost optimi*" OR "cost reduction" OR "cost saving*" OR "cost-effective*" OR "cost effective*" OR "cost-aware" OR "cost aware" OR "cost-efficien*" OR "cost efficien*" OR "monetary cost*" OR "operational cost*" OR "cost model*" OR "cost minimi*" OR "pricing model*" OR "pay-as-you-go" OR "pay-per-use" OR FinOps OR "over-provision*" OR overprovision* OR "right-siz*" OR rightsiz* OR "resource provisioning"))
```

Uma primeira versão com termos de custo genéricos (`"cost*"`, `pricing`, `"virtual machine*"`) retornou 28.180 registros e foi refinada para a string acima.

## 2. Estrutura do repositório

```
wos_export/                  21 arquivos brutos exportados da WoS (savedrecs_INICIO-FIM.txt)
merge_wos.c                  programa em C que junta os lotes em um único arquivo
wos_completo.txt             base unificada (10.132 registros) — entrada do VOSviewer
analise/gerar_redes.py       gera as redes (formato VOSviewer) e as tabelas descritivas
analise/rodar_vosviewer.sh   roda layout + clustering no VOSviewer e exporta mapas e imagens
analise/triagem_prisma.py    triagem PRISMA automatizada + lista de leitura + fluxograma
resultados/prisma/           saídas da triagem (CSVs, resumos, contagens)
resultados/vosviewer/        redes geradas (map + network), antes do layout
resultados/mapas/            mapas finais do VOSviewer (com posições e clusters) + JSON
resultados/imagens/          figuras PNG para a apresentação
resultados/tabelas/          CSVs e resumo.txt
```

## 3. Como reproduzir

```bash
# 1) juntar os lotes (remove duplicatas pelo campo UT)
gcc -O2 -Wall -o merge_wos merge_wos.c
./merge_wos wos_export wos_completo.txt

# 2) gerar redes e tabelas (Python 3, só biblioteca padrão)
python3 analise/gerar_redes.py wos_completo.txt resultados

# 3) layout/clustering e imagens (VOSviewer 1.6.21 + Java 8+)
bash analise/rodar_vosviewer.sh ~/.local/opt/VOSviewer/VOSviewer.jar

# 4) triagem PRISMA e fluxograma
python3 analise/triagem_prisma.py wos_completo.txt resultados
```

Para explorar um mapa interativamente: abra o VOSviewer → *Open* → escolha `resultados/mapas/<nome>_map.txt` e `<nome>_network.txt` (ou o `.json`).

## 4. Análises e parâmetros

Todas com contagem binária por documento; layout, normalização (*association strength*) e clustering são os padrões do VOSviewer.

| Mapa | Unidade / relação | Critério de inclusão | Itens | Links |
|---|---|---|---|---|
| `palavras_chave` | coocorrência de palavras-chave (autor + Keywords Plus) | ≥ 20 ocorrências, top 300 | 300 | 15.970 |
| `cocitacao_refs` | cocitação de referências citadas | ≥ 40 citações, top 300 | 279 | 14.078 |
| `paises` | coautoria entre países | ≥ 5 documentos | 85 | 1.067 |
| `cocitacao_fontes` | cocitação de periódicos/eventos citados | ≥ 150 citações, top 200 | 179 | 15.473 |

Limpeza das palavras-chave: minúsculas, hífen virou espaço e um tesauro de sinônimos (ex.: *auto-scaling/auto scaling* → *autoscaling*; *FaaS/function as a service* → *serverless computing*), definido em `SINONIMOS`, no início de `gerar_redes.py`. Países: *England/Scotland/Wales/North Ireland* → *United Kingdom*. Referências *[anonymous]* foram descartadas.

Imagens geradas:
- `palavras_chave_rede.png`: clusters temáticos
- `palavras_chave_overlay_ano.png`: ano médio de publicação de cada termo; amarelo = mais recente
- `palavras_chave_densidade.png`
- `cocitacao_refs_rede.png`: base teórica
- `paises_rede.png` e `paises_densidade.png`
- `cocitacao_fontes_rede.png`

## 5. Principais achados (para a apresentação)

- **Produção:** cresce a partir de 2009, com pico em 2017–2018 (786 docs/ano), queda em 2019–2023 e retomada em 2024–2025 (765 e 813). Ver `tabelas/producao_por_ano.csv`.
- **Países:** China (2.124), EUA (1.928) e Índia (1.777) dominam. **O Brasil aparece em 14º, com 284 documentos (2,8%)**, e só 4 deles têm autor vinculado a Goiás, nenhum sobre custo de PMEs. Isso sustenta o argumento de "muita demanda real e pouca pesquisa nacional".
- **FinOps** aparece em apenas 13 documentos: o termo é recente e pouco explorado na literatura indexada.
- **Frentes recentes** (overlay, ano médio): *costs* (2024,1), *serverless computing* (2023,4), *kubernetes* (2023,3), *deep reinforcement learning*, *edge computing*. Temas mais antigos e consolidados: *virtual machines* (2019,1), *spot instances* (2019,3), *elasticity* (2018,9), *pricing* (2018,9).
- **Base teórica mais cocitada:** Armbrust et al. (2010, *Commun. ACM*), Calheiros et al. (2011, CloudSim) e Buyya et al. (2009, *FGCS*).
- **Principais veículos:** IEEE Access, Future Generation Computer Systems, IEEE Transactions on Cloud Computing.

Os detalhes estão em `resultados/tabelas/resumo.txt` e nos CSVs (`paises.csv`, `periodicos.csv`, `palavras_chave.csv`, `brasil_artigos.csv`).

## 6. Revisão sistemática (PRISMA 2020), com recorte em autoscaling

A revisão se concentra em **autoscaling**, incluindo escalonamento agendado e desligamento fora do horário, comparado ao provisionamento fixo ou ao autoscaler padrão do mercado. Spot, serverless e instâncias reservadas entram só como contexto na introdução e na discussão.

**Fase 1: triagem automática** (`analise/triagem_prisma.py`)

| Critério | Descrição | Excluídos |
|---|---|---|
| E1 | tipo documental não elegível ou sem resumo | 44 |
| E2 | idioma diferente de inglês/português | 19 |
| E3 | não aborda autoscaling ou escalonamento elástico/agendado | 8.557 |
| E4 | não relata economia de custo **quantificada** no resumo | 1.333 |
| — | versões duplicadas do mesmo trabalho (mesmo título) | 2 |
| E5 | domínio fora do escopo de PMEs (IA/GPU, IoT/edge, HPC, redes móveis…) | 54 |

**Fase 2: leitura assistida dos resumos.** Foram avaliados 123 resumos, e as decisões, com justificativa, estão em `analise/triagem_resumos.csv`.

| Critério | Descrição | Excluídos |
|---|---|---|
| R1 | a economia não é custo de nuvem de quem contrata (energia, provedor…) | 15 |
| R2 | compara só com outros algoritmos acadêmicos, sem baseline fixo ou de mercado | 12 |
| R3 | carga fora do cenário web/serviço de negócio (lote, big data, streaming…) | 49 |
| R4 | o autoscaling é periférico no trabalho | 16 |

**31 artigos** seguem para a leitura de texto completo.

Arquivos em `resultados/prisma/`:
- `leitura_final.csv`: os 31 artigos, com o motivo de leitura e colunas em branco para a extração (incluir S/N, provedor, aplicação, tipo de autoscaling, linha de base, economia medida, impacto no SLA, nuvem real ou simulação)
- `leitura_final_resumos.txt`: referência, DOI, motivo e resumo de cada um
- `resumos_triados.csv`: os 123 resumos avaliados, com a decisão
- `triagem_completa.csv`: os 10.132 registros, com a decisão e o motivo
- `prisma_contagens.txt`: os números do fluxograma

Fluxograma: `resultados/imagens/prisma_fluxograma.png`. As caixas de elegibilidade e inclusão ficam "a preencher" até a leitura terminar.

Para alterar uma decisão, edite `analise/triagem_resumos.csv` e rode o script de novo. As contagens e o fluxograma são atualizados automaticamente.
