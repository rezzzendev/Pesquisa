# Passo a passo (guia pessoal)

O que já está pronto e o que falta, na ordem. Marque `[x]` conforme for concluindo.
A visão geral das etapas está em `PLANO.md`; aqui fica o detalhe de **como** fazer cada uma.

---

## Antes de tudo: entender o que cada parte faz

| Parte | Para que serve no trabalho | Onde entra |
|---|---|---|
| **Bibliometria (VOSviewer)** | **Mapeia a área**: temas, países, referências clássicas, temas recentes. **Não seleciona artigos.** | Introdução: justifica o tema e o recorte e mostra a lacuna brasileira |
| **Triagem PRISMA** | **Seleciona os artigos**: 10.132 → 123 resumos → 31 para ler | Método e resultados da revisão |
| **Cálculo de custo** | Traduz a economia em reais para uma PME típica | Resultados e discussão |

Frases que você precisa saber explicar:
- "O mapa de palavras-chave mostra que autoscaling é um tema central e consolidado, e o Brasil aparece em 14º, com 2,8% da produção."
- "A seleção dos artigos seguiu o PRISMA 2020, com critérios de exclusão explícitos (E1–E5 automáticos e R1–R4 nos resumos)."

---

## Etapa A: conferir o que já foi feito (≈ 3 h no total)

### A1. Coleta e junção (≈ 20 min)
- [ ] Ler `merge_wos.c` e entender o que ele faz (junta os lotes, tira duplicatas pelo campo UT, escreve o cabeçalho e o EF).
- [ ] Rodar e conferir a saída: "Total lidos: 10132 | gravados: 10132 | duplicados removidos: 0".
  ```bash
  gcc -O2 -Wall -o merge_wos merge_wos.c
  ./merge_wos wos_export wos_completo.txt
  ```
- [ ] Abrir `wos_completo.txt` e olhar 2 ou 3 registros: os campos TI (título), AB (resumo), PY (ano), CR (referências) e ER (fim do registro).
- [ ] Marcar a validação da etapa 1 como ✅ no `PLANO.md`.

### A2. Bibliometria (≈ 40 min)
- [ ] Abrir o VOSviewer (`vosviewer` no terminal) → *Open* → `resultados/mapas/palavras_chave_map.txt` + `palavras_chave_network.txt`.
- [ ] Clicar em **autoscaling** e anotar os termos ligados a ele (custo, SLA, Kubernetes…). Isso vai para a introdução.
- [ ] Abrir também `paises` e `cocitacao_refs`.
- [ ] Ler `resultados/tabelas/resumo.txt` e conferir os números do README (seção 5).
- [ ] Conferir os parâmetros na seção 4 do README (limiares e sinônimos) e se fazem sentido para você.
- [ ] Marcar a validação da etapa 2 como ✅ no `PLANO.md`.

### A3. Triagem PRISMA (≈ 2 h)
- [ ] Abrir `analise/triagem_resumos.csv` numa planilha (LibreOffice Calc).
- [ ] Para cada uma das 123 linhas, ler o **título** e a **justificativa**. Abra o resumo (em `resultados/prisma/resumos_triados.csv`) só se tiver dúvida.
- [ ] Preencher **"Conferido pelo autor (S/N)"** com S.
- [ ] Se discordar de alguma decisão:
  - mude **Decisao** (`ler` ou `excluir`) e **Codigo** (R1–R4);
  - escreva o motivo em **"Observacao do autor"**.
- [ ] Salvar como CSV, mantendo o separador vírgula e a codificação UTF-8.
- [ ] Rodar de novo para atualizar as contagens e o fluxograma:
  ```bash
  python3 analise/triagem_prisma.py wos_completo.txt resultados
  ```
- [ ] Marcar a validação da etapa 4 como ✅ no `PLANO.md`.

Os critérios, para consultar durante a conferência:
- **R1:** a economia não é custo de nuvem de quem contrata (é energia, ou custo do provedor).
- **R2:** compara só com outros algoritmos acadêmicos, sem comparar com o fixo ou com o autoscaler padrão.
- **R3:** a carga está fora do cenário web ou de serviço de negócio (lote, big data, streaming, ML…).
- **R4:** o autoscaling é periférico; o foco do artigo é outro problema.

---

## Etapa B: ler os artigos (≈ 3 h para os 10 primeiros)

- [ ] Abrir `resultados/prisma/LEITURA.md`, que tem os links de DOI e CAPES em duas prioridades.
- [ ] Para cada artigo de **prioridade 1** (10 artigos):
  1. ler o resumo, a seção de avaliação/experimentos e a conclusão (15 a 20 min);
  2. preencher em `resultados/prisma/leitura_final.csv`:
     - **Incluir (S/N)**
     - **Provedor**
     - **Aplicacao/carga**
     - **Tipo de autoscaling** (reativo, preditivo ou agendado)
     - **Linha de base** (fixo, HPA/padrão ou outro algoritmo)
     - **Economia medida (%)**
     - **Impacto no SLA/latência**
     - **Avaliação** (nuvem real ou simulação)
  3. se excluir, anotar o motivo em "Motivo exclusao". Ele entra no fluxograma (sem linha de base comparável, sem dados de custo ou texto indisponível).
- [ ] Prioridade 2 (21 artigos): mesmo processo, se der tempo antes do pôster; senão, depois.
- [ ] Ao final, contar quantos foram lidos, excluídos (por motivo) e incluídos, e completar a parte de baixo do fluxograma PRISMA.

Se o link da CAPES não abrir, use o DOI ou procure o título no Google Scholar, que costuma ter uma versão em PDF do autor.

---

## Etapa C: estender o cálculo para Azure e Google Cloud (≈ 3 a 4 h)

### C1. Entender o modelo
- [ ] Ler o início de `analise/calculo_custos.py`: o docstring e os parâmetros `INSTANCIA`, `BANCO`, `CAP_ALVO`, `MIN_VMS`, `PERFIL` e `AGENDA`.
- [ ] Rodar e comparar com `resultados/calculo/resumo.txt`:
  ```bash
  python3 analise/calculo_custos.py dados/precos_aws_sa-east-1.csv resultados
  ```
- [ ] Saber responder: *por que o autoscaling economiza 59% na aplicação, mas só 40% no total?* (Pista: o que é fixo em todos os cenários?)

### C2. Escolher as máquinas equivalentes (justificar a escolha)
| Componente | AWS | Azure | Google Cloud |
|---|---|---|---|
| VM (2 vCPU, 4 GB) | t3.medium | série B (ex.: B2s) | série E2 (ex.: e2-medium) |
| PostgreSQL gerenciado | RDS db.t3.medium | Flexible Server (Burstable) | Cloud SQL (2 vCPU, 4 GB) |
| Balanceador | ALB | Load Balancer / Application Gateway | Cloud Load Balancing |

Sempre na **região São Paulo**: Azure `brazilsouth`, Google `southamerica-east1`.

### C3. Levantar os preços
- [ ] **Azure:** a API pública abre no navegador. Exemplo:
  `https://prices.azure.com/api/retail/prices?$filter=armRegionName eq 'brazilsouth' and armSkuName eq 'Standard_B2s'`
  Use `priceType` = `Consumption` (sob demanda) e `Reservation` (1 ano), com Linux.
- [ ] **Google:** páginas oficiais de preço (VMs, Cloud SQL, balanceamento). Anote **a URL e a data** de cada valor.
- [ ] **Google, atenção:** o desconto automático por uso contínuo (*sustained use*) **não vale para a série E2**. Confira na página de descontos qual se aplica à máquina escolhida e o que existe de compromisso de 1 ano (*committed use*).
- [ ] Criar `dados/precos_azure_brazilsouth.csv` e `dados/precos_gcp_southamerica-east1.csv` no mesmo formato de `dados/precos_aws_sa-east-1.csv`, com a fonte em cada linha.

### C4. Adaptar o script
- [ ] Hoje o script busca os preços com nomes da AWS (ex.: `("EC2", INSTANCIA, "sob demanda (Linux)")`, dentro de `custos()` e `roda()`).
- [ ] Criar um dicionário com, para cada provedor, o nome da VM, do banco e do balanceador e os rótulos das modalidades, e trocar as buscas fixas por ele.
- [ ] Rodar para os três e gerar uma tabela de **5 cenários × 3 provedores** (R$/mês e % de economia).
- [ ] Opcional: um gráfico comparativo (barras agrupadas por cenário, uma cor por provedor).

### C5. Interpretar
- [ ] *A economia percentual muda entre os provedores? Por quê?* (descontos, forma de cobrança, preço do banco)
- [ ] Registrar as respostas no README (seção 7).
- [ ] Marcar a etapa 5 como ✅ no `PLANO.md`.

---

## Etapa D: síntese (≈ 2 h)

- [ ] Com o `leitura_final.csv` preenchido, montar a tabela de síntese: estudo | tipo de autoscaling | linha de base | economia | impacto no SLA | real/simulação.
- [ ] Calcular a faixa de economia (mínimo, mediana e máximo) **só dos estudos que comparam com fixo ou com o autoscaler padrão**.
- [ ] Comparar com o seu cálculo: *o número da PME típica cai dentro da faixa da literatura?*
- [ ] Anotar 3 a 5 achados para a discussão. Pontos para pensar:
  - o banco fixo dilui a economia;
  - o porte importa (sistemas pequenos economizam menos);
  - existe um trade-off entre custo e SLA em picos repentinos;
  - quase nenhum estudo trata de desligamento fora do horário (lacuna).

---

## Etapa E: pôster

### E1. Modelo
- [ ] Aguardar o modelo de pôster que a professora vai enviar e montar o conteúdo abaixo dentro dele.

### E2. Estrutura sugerida (de cima para baixo, em 2 ou 3 colunas)
1. **Cabeçalho:** título, seu nome, orientadora, instituição e logos.
2. **Introdução:** o problema (PMEs pagam pelo pico 24/7), o que é FinOps e a pergunta de pesquisa. Máximo de 3 a 4 frases.
3. **Objetivos:** o geral e os 4 específicos (estão no README).
4. **Método:** um fluxo visual WoS → VOSviewer → PRISMA → cálculo, com os números (10.132 → 123 → 31).
5. **Resultados: bibliometria.** Uma figura do VOSviewer (`palavras_chave_rede.png` ou `palavras_chave_overlay_ano.png`) e um destaque: "Brasil em 14º (2,8%)".
6. **Resultados: revisão.** O fluxograma PRISMA, mais uma tabela curta de síntese (5 a 8 estudos principais com a economia relatada).
7. **Resultados: cálculo.** `custo_mensal_cenarios.png` (ou a versão com os 3 provedores) e `custo_sensibilidade.png`.
8. **Conclusões:** 3 ou 4 tópicos curtos com os números principais.
9. **Limitações e próximos passos:** 2 ou 3 linhas.
10. **Referências:** só as essenciais (5 a 8), em fonte pequena.
11. **QR code** para o repositório no GitHub (dados, scripts e método completo).

### E3. Regras de legibilidade
- [ ] O título deve ser legível a 3 metros (≥ 80–100 pt); textos ≥ 24–28 pt; legendas ≥ 20 pt.
- [ ] Pouco texto: mire em 300 a 500 palavras no total. Prefira tópicos a parágrafos.
- [ ] Use as figuras em **SVG** (`resultados/imagens/*.svg`), que não perdem qualidade na impressão. Se o PNG ficar pixelado, gere com densidade maior: `magick -density 300 arquivo.svg arquivo.png`.
- [ ] Destaque os números (ex.: **−40%**, **R$ 1.767/mês**, **14º lugar**).
- [ ] Mantenha as mesmas cores das figuras em todo o pôster.

### E4. Revisão e impressão
- [ ] Imprimir uma prova em A4 ou A3 para conferir se dá para ler e se há erros.
- [ ] Revisar com a professora.
- [ ] Exportar em PDF com as fontes incorporadas e mandar imprimir com antecedência (gráficas costumam levar de 1 a 2 dias).

### E5. Ao lado do pôster
- [ ] Preparar uma **fala de 1 a 2 minutos**: problema → o que fez → principal resultado → por que importa para PMEs.
- [ ] Ensaiar a fala em voz alta.
- [ ] Respostas para perguntas prováveis:
  - Por que só a Web of Science?
  - Por que autoscaling e não serverless?
  - O cálculo é real ou simulado? (É ilustrativo, com preços reais e carga sintética; as limitações estão no README.)
  - Como os artigos foram selecionados? (PRISMA, com critérios explícitos.)
  - Onde a IA foi usada? (Ver a seção "Divisão do trabalho e uso de IA" no README.)

---

## Etapa F: depois do pôster (iniciação científica)

- [ ] Ler os 21 artigos restantes e fechar o PRISMA.
- [ ] Escrever o artigo: introdução, referencial, método, resultados, discussão, conclusão.
- [ ] Revisar com a professora.
- [ ] (Opcional) Experimento real pequeno, com free tier, para validar o cálculo.
- [ ] Escolher o evento ou periódico e submeter.

---

## Git (ao fim de cada etapa)

```bash
git add -A
git commit -m "Etapa X: <o que foi feito>"
git push
```

## Comandos úteis

```bash
# refazer a triagem depois de editar analise/triagem_resumos.csv
python3 analise/triagem_prisma.py wos_completo.txt resultados

# refazer o cálculo de custo
python3 analise/calculo_custos.py dados/precos_aws_sa-east-1.csv resultados

# abrir o VOSviewer
vosviewer
```
