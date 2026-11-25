# Autoscaling como estratégia de FinOps: revisão sistemática e estimativa de economia de custos em nuvem para PMEs brasileiras

## Pergunta e objetivos

**Pergunta de pesquisa:** quanto uma PME pode economizar na nuvem ao trocar o provisionamento fixo, dimensionado para o pico, pelo autoscaling, mantendo o nível de serviço?

**Objetivo geral:** estimar a economia de custos que o autoscaling proporciona a PMEs em relação ao provisionamento fixo, a partir de uma revisão sistemática da literatura e de um cálculo ilustrativo com preços reais de nuvem no Brasil.

**Objetivos específicos:**
1. Mapear a produção científica sobre custo e elasticidade em nuvem e a participação brasileira nela (bibliometria: Web of Science + VOSviewer). Ver seções 1 a 5.
2. Sintetizar a economia relatada na literatura com autoscaling em relação ao provisionamento fixo e o impacto no nível de serviço (revisão sistemática PRISMA 2020). Ver seção 6.
3. Estimar, em reais, a economia para um sistema web típico de PME na AWS São Paulo (cálculo ilustrativo). Ver seção 7.
4. Identificar em que condições o autoscaling compensa e em quais o ganho é pequeno (análise de sensibilidade). Ver seção 7.

**Método:** bibliometria (10.132 registros) → revisão sistemática PRISMA (31 artigos para texto completo) → cálculo ilustrativo de custo.

## Divisão do trabalho e uso de IA

Este levantamento usou um assistente de IA (Claude, da Anthropic) como ferramenta de apoio. A divisão foi a seguinte:

| Etapa | Feito pelo assistente de IA | Feito pelo autor |
|---|---|---|
| Tema e pergunta | — | definição do tema (aprovado pela orientadora) e da pergunta |
| Coleta na WoS | proposta e refinamento da string de busca; automação da exportação dos 21 lotes | acesso via CAPES; acompanhamento da coleta |
| Junção dos arquivos | programa `merge_wos.c` | execução e conferência |
| Bibliometria | `gerar_redes.py` e execução do VOSviewer (redes, mapas, tabelas) | conferência dos mapas e dos parâmetros |
| Recorte e título | propostas de opções | escolha do recorte (autoscaling), do formato do trabalho e do título |
| Triagem PRISMA | script da fase 1; pré-classificação dos 123 resumos pelos critérios R1–R4 | aprovação dos critérios; conferência de cada decisão (coluna *Conferido pelo autor* em `analise/triagem_resumos.csv`) |
| Cálculo de custo | modelo e cálculo para a AWS (`calculo_custos.py`) | conferência das suposições; extensão para Azure e Google Cloud |
| Leitura e síntese | — | leitura dos textos completos, extração dos dados e interpretação |

O andamento de cada etapa está em `PLANO.md`, e o passo a passo detalhado do que falta fazer está em `PASSO_A_PASSO.md`.

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
PLANO.md                     visão geral das etapas e status
PASSO_A_PASSO.md             guia detalhado do que falta fazer
wos_export/                  21 arquivos brutos exportados da WoS (savedrecs_INICIO-FIM.txt)
merge_wos.c                  programa em C que junta os lotes em um único arquivo
wos_completo.txt             base unificada (10.132 registros) — entrada do VOSviewer
analise/gerar_redes.py       gera as redes (formato VOSviewer) e as tabelas descritivas
analise/rodar_vosviewer.sh   roda layout + clustering no VOSviewer e exporta mapas e imagens
analise/triagem_prisma.py    triagem PRISMA automatizada + lista de leitura + fluxograma
analise/triagem_resumos.csv  decisões da leitura dos resumos (editável)
analise/calculo_custos.py    cálculo ilustrativo de custo (fixo × agendado × autoscaling)
dados/                       preços oficiais AWS sa-east-1 e câmbio PTAX usados no cálculo
resultados/calculo/          saídas do cálculo (CSVs e resumo)
resultados/prisma/           saídas da triagem (CSVs, resumos, contagens)
resultados/vosviewer/        redes geradas (map + network), antes do layout
resultados/mapas/            mapas finais do VOSviewer (com posições e clusters) + JSON
resultados/imagens/          figuras (PNG e SVG) para o pôster
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

# 5) cálculo ilustrativo de custo
python3 analise/calculo_custos.py dados/precos_aws_sa-east-1.csv resultados
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

## 5. Principais achados (para o pôster)

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

**Fase 2: classificação dos resumos.** Os 123 resumos foram classificados pelos critérios R1–R4. Cada decisão tem justificativa e está registrada em `analise/triagem_resumos.csv`, com as colunas *Conferido pelo autor* e *Observação do autor* para a validação.

| Critério | Descrição | Excluídos |
|---|---|---|
| R1 | a economia não é custo de nuvem de quem contrata (energia, provedor…) | 15 |
| R2 | compara só com outros algoritmos acadêmicos, sem baseline fixo ou de mercado | 12 |
| R3 | carga fora do cenário web/serviço de negócio (lote, big data, streaming…) | 49 |
| R4 | o autoscaling é periférico no trabalho | 16 |

**31 artigos** seguem para a leitura de texto completo.

Arquivos em `resultados/prisma/`:
- `LEITURA.md`: os 31 artigos com links para o texto completo (DOI e CAPES), em duas prioridades
- `leitura_final.csv`: os 31 artigos, com o motivo de leitura e colunas em branco para a extração (incluir S/N, provedor, aplicação, tipo de autoscaling, linha de base, economia medida, impacto no SLA, nuvem real ou simulação)
- `leitura_final_resumos.txt`: referência, DOI, motivo e resumo de cada um
- `resumos_triados.csv`: os 123 resumos avaliados, com a decisão
- `triagem_completa.csv`: os 10.132 registros, com a decisão e o motivo
- `prisma_contagens.txt`: os números do fluxograma

Fluxograma: `resultados/imagens/prisma_fluxograma.png`. As caixas de elegibilidade e inclusão ficam "a preencher" até a leitura terminar.

Para alterar uma decisão, edite `analise/triagem_resumos.csv` e rode o script de novo. As contagens e o fluxograma são atualizados automaticamente.

## 7. Cálculo ilustrativo de custo

`analise/calculo_custos.py` modela um sistema web típico de PME: aplicação em VMs `t3.medium` atrás de um ALB, com banco PostgreSQL no RDS (`db.t3.medium`, 50 GB). A carga é de horário comercial, com pico de cerca de 100 req/s, almoço, rampa à noite, sábado de manhã e um pico promocional curto. O modelo simula uma semana em intervalos de 15 minutos.

Os preços são **oficiais da AWS para São Paulo** (Price List API, 24/11/2026) e estão em `dados/precos_aws_sa-east-1.csv`. O câmbio é a PTAX do Banco Central (US$ 1 = R$ 5,8573).

| Cenário | R$/mês | Economia total | Economia na aplicação | Risco de SLA* |
|---|---|---|---|---|
| A. Fixo no pico (sob demanda) | 2.960,00 | — | — | 0 |
| B. Fixo no pico (reservada 1 ano) | 2.103,98 | 28,9% | 42,6% | 0 |
| C. Agendado (desliga fora do expediente) | 2.216,00 | 25,1% | 37,0% | 0 |
| D. Autoscaling reativo | 1.767,47 | 40,3% | 59,3% | 2 |
| E. Autoscaling + base reservada | 1.522,89 | 48,6% | 71,4% | 2 |

\* Intervalos de 15 minutos na semana com utilização acima de 85%. No autoscaling, os dois intervalos acontecem no pico promocional: é o atraso de reação do escalonamento reativo.

**Leituras para a discussão:**
- O banco e o balanceador são custos fixos. Por isso a economia no total (40%) fica bem menor que a economia na camada de aplicação (59%).
- **O porte importa** (`custo_sensibilidade.png`). Com até cerca de 2 VMs no pico, não há o que economizar, por causa do mínimo de 2 VMs para alta disponibilidade. A economia cresce com o porte: de 25% com 4 VMs para cerca de 60% com 25 VMs.
- Combinar elasticidade com compra reservada da base (E) dá o melhor resultado. É a abordagem típica de FinOps.

**Limitações:** o modelo não inclui EBS, transferência de dados, impostos ou IOF, nem o tempo de boot dentro do intervalo de 15 minutos, e a carga é sintética. Os parâmetros ficam no início do script.

Figuras: `custo_mensal_cenarios.png`, `custo_semana_vms.png` e `custo_sensibilidade.png`.
