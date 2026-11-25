# Artigos para leitura (31)

Os links levam ao texto completo pelo DOI. Para abrir pelo acesso da CAPES, use o link **CAPES** (você precisa estar logado no Portal de Periódicos/CAFe). Se o artigo não abrir, procure o título no Google Scholar, que costuma ter uma versão em PDF do autor.

Preencha a extração em `leitura_final.csv`.

## Prioridade 1 (ler primeiro)

1. **A lightweight heuristic for cost-efficient IaaS auto-scaling of small-scale web applications** (2026). Yadav, D; Sheoran, S; Aman, M; et al.. *Scientific Reports*.  
   [DOI](https://doi.org/10.1038/s41598-026-59763-6) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1038/s41598-026-59763-6)  
   Por que ler: Essencial: auto-scaling para aplicações web de pequena escala (2 a 8 VMs, organizações pequenas); −41,9% vs limiar fixo, com SLA de P99

2. **A Cost-Efficient Container Orchestration Strategy in Kubernetes-Based Cloud Computing Infrastructures with Heterogeneous Resources** (2020). Zhong, ZH; Buyya, R. *Acm Transactions On Internet Technology*.  
   [DOI](https://doi.org/10.1145/3378447) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1145/3378447)  
   Por que ler: Kubernetes com recursos heterogêneos; −23% a −32% vs Kubernetes padrão; 98 citações

3. **Trace-Driven Scaling of Microservice Applications** (2023). Mostofi, VM; Krul, E; Krishnamurthy, D; et al.. *Ieee Access*.  
   [DOI](https://doi.org/10.1109/ACCESS.2023.3260069) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1109/ACCESS.2023.3260069)  
   Por que ler: Baseline é o HPA do Kubernetes (padrão de mercado); −34% de custo e −92% de violações

4. **Predictive Autoscaling with a Safety Net for Microservices** (2026). Kozhinov, M; Mazzara, M. *Advanced Information Networking And Applications, Aina-2026, Vol 4*.  
   [DOI](https://doi.org/10.1007/978-3-032-23304-2_22) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1007/978-3-032-23304-2_22)  
   Por que ler: Mostra o trade-off custo × SLA: economia de 12% piora o SLA; com SLA garantido, custa 6% a mais (trace da Alibaba)

5. **Automated Demand-driven Resource Scaling in Relational Database-as-a-Service** (2016). Das, S; Li, F; Narasayya, VR; et al.. *Sigmod'16: Proceedings Of The 2016 International Conference On Management Of Data*.  
   [DOI](https://doi.org/10.1145/2882903.2903733) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1145/2882903.2903733)  
   Por que ler: Autoscaling de banco relacional como serviço (o BD da PME); 1,5x a 3x mais barato com latência comparável

6. **FOX: Cost-Awareness for Autonomic Resource Management in Public Clouds** (2018). Lesch, V; Bauer, A; Herbst, N; et al.. *Proceedings Of The 2018 Acm/Spec International Conference On Performance Engineering (Icpe '18)*.  
   [DOI](https://doi.org/10.1145/3184407.3184415) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1145/3184407.3184415)  
   Por que ler: Efeito do modelo de cobrança (por hora/segundo) no custo real do autoscaling; −34% na EC2

7. **SERVERLESS DATABASES: FUTURE TRENDS IN CLOUD DATABASE MANAGEMENT AND COST OPTIMIZATION** (2025). Kavuluri, HVR. *Archives For Technical Sciences*.  
   [DOI](https://doi.org/10.70102/afts.2025.1833.307) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.70102/afts.2025.1833.307)  
   Por que ler: BD serverless (Aurora Serverless) vs RDS PostgreSQL fixo; até −45% em carga com picos, com custo de cold start

8. **BurScale: Using Burstable Instances for Cost-Effective Autoscaling in the Public Cloud** (2019). Baarzi, AF; Zhu, T; Urgaonkar, B. *Proceedings Of The 2019 Tenth Acm Symposium On Cloud Computing (Socc '19)*.  
   [DOI](https://doi.org/10.1145/3357223.3362706) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1145/3357223.3362706)  
   Por que ler: Instâncias burstable (t2/t3) + autoscaling; −50% com o mesmo desempenho; opção típica de PME

9. **Autoflex: Service Agnostic Auto-scaling Framework for IaaS Deployment Models** (2013). Morais, F; Brasileiro, F; Lopes, R; et al.. *Proceedings Of The 2013 13Th Ieee/Acm International Symposium On Cluster, Cloud And Grid Computing (Ccgrid 2013)*.  
   [DOI](https://doi.org/10.1109/CCGrid.2013.74) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1109/CCGrid.2013.74)  
   Por que ler: Autoflex: −37% vs prática reativa, com violação de SLO de 0,008% (34 citações)

10. **Techniques for Optimizing Cloud Footprint** (2013). Kejariwal, A. *Proceedings Of The 2013 Ieee International Conference On Cloud Engineering (Ic2E 2013)*.  
   [DOI](https://doi.org/10.1109/IC2E.2013.14) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1109/IC2E.2013.14)  
   Por que ler: Caso real em produção (Netflix); até −50% no custo operacional

## Prioridade 2

1. **RHAS: robust hybrid auto-scaling for web applications in cloud computing** (2021). Singh, P; Kaur, A; Gupta, P; et al.. *Cluster Computing-The Journal Of Networks Software Tools And Applications*.  
   [DOI](https://doi.org/10.1007/s10586-020-03148-5) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1007/s10586-020-03148-5)  
   Por que ler: Autoscaling híbrido (reativo + preditivo) para aplicações web; −14% de custo com melhora de SLA

2. **Gwydion: Efficient auto-scaling for complex containerized applications in Kubernetes through Reinforcement Learning** (2025). Santos, J; Reppas, E; Wauters, T; et al.. *Journal Of Network And Computer Applications*.  
   [DOI](https://doi.org/10.1016/j.jnca.2024.104067) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1016/j.jnca.2024.104067)  
   Por que ler: Autoscaling no Kubernetes com microsserviços reais (Online Boutique); compara com o mecanismo padrão

3. **Erlang: Application-Aware Autoscaling for Cloud Microservices** (2024). Sachidananda, V; Sivaraman, A. *Proceedings Of The 2024 European Conference On Computer Systems, Eurosys 2024*.  
   [DOI](https://doi.org/10.1145/3627703.3650084) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1145/3627703.3650084)  
   Por que ler: Compara com autoscaling por limiar de CPU/memória (prática de mercado); −19,3% atendendo a latência-alvo

4. **AutoScaleAI: An AI-Powered Framework for Cloud Resource Optimization Using Telemetry Analytics** (2026). Gouri, F; Kota, CPK; Shivnatri, M; et al.. *Ieee Access*.  
   [DOI](https://doi.org/10.1109/ACCESS.2026.3677437) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1109/ACCESS.2026.3677437)  
   Por que ler: Compara com políticas por limiar (prática comum); −38% de custo

5. **A reliable and cost-efficient auto-scaling system for web applications using heterogeneous spot instances** (2016). Qu, CH; Calheiros, RN; Buyya, R. *Journal Of Network And Computer Applications*.  
   [DOI](https://doi.org/10.1016/j.jnca.2016.03.001) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1016/j.jnca.2016.03.001)  
   Por que ler: Autoscaling de aplicações web com instâncias spot; disponibilidade e custo (64 citações)

6. **An adaptive auto-scaling framework for cloud resource provisioning** (2023). Chouliaras, S; Sotiriadis, S. *Future Generation Computer Systems-The International Journal Of Escience*.  
   [DOI](https://doi.org/10.1016/j.future.2023.05.017) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1016/j.future.2023.05.017)  
   Por que ler: Auto-scaling adaptativo vs regras de limiar; −48% no custo de MySQL

7. **A Pluggable Autoscaling Service for Open Cloud PaaS Systems** (2012). Bunch, C; Arora, V; Chohan, N; et al.. *2012 Ieee/Acm Fifth International Conference On Utility And Cloud Computing (Ucc 2012)*.  
   [DOI](https://doi.org/10.1109/UCC.2012.12) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1109/UCC.2012.12)  
   Por que ler: Autoscaler para PaaS e aplicações web; spot reduz custo em 91%

8. **A benefit-aware on-demand provisioning approach for multi-tier applications in cloud computing** (2013). Wu, H; Zhang, WB; Zhang, JH; et al.. *Frontiers Of Computer Science*.  
   [DOI](https://doi.org/10.1007/s11704-013-2201-8) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1007/s11704-013-2201-8)  
   Por que ler: Aplicações multicamadas (web + BD); −30% vs abordagem sem custo, com menos violações de SLA

9. **Joint Autoscaling of Containers and Virtual Machines for Cost Optimization in Container Clusters** (2024). Entrialgo, J; García, M; García, J; et al.. *Journal Of Grid Computing*.  
   [DOI](https://doi.org/10.1007/s10723-023-09732-4) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1007/s10723-023-09732-4)  
   Por que ler: Autoscaling conjunto de containers e VMs, com aplicação real; ~20% mais barato

10. **Cost-Optimized Predictive Autoscaling of Cloud Resources Using Game-Theoretic Queuing Theory** (2025). Pandey, V. *Southeastcon 2025*.  
   [DOI](https://doi.org/10.1109/SOUTHEASTCON56624.2025.10971700) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1109/SOUTHEASTCON56624.2025.10971700)  
   Por que ler: Preditivo vs reativo tradicional; −30% mantendo resposta abaixo de 100 ms

11. **AROF: adaptive resource optimization framework for Kubernetes cluster using workload forecasting** (2025). Patel, R; Makwana, A. *International Journal Of Parallel Emergent And Distributed Systems*.  
   [DOI](https://doi.org/10.1080/17445760.2025.2605532) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1080/17445760.2025.2605532)  
   Por que ler: Baseline são os autoscalers padrão do Kubernetes; −81% de violações de SLA e +22,4% de eficiência de custo

12. **Spock: Exploiting Serverless Functions for SLO and Cost Aware Resource Procurement in Public Cloud** (2019). Gunasekaran, JR; Thinakaran, P; Kandemir, MT; et al.. *2019 Ieee 12Th International Conference On Cloud Computing (Ieee Cloud 2019)*.  
   [DOI](https://doi.org/10.1109/CLOUD.2019.00043) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1109/CLOUD.2019.00043)  
   Por que ler: Serviços web com VMs + funções serverless vs só VMs; −33% (54 citações)

13. **Cost-Availability Aware Scaling: Towards Optimal Scaling of Cloud Services** (2023). Bento, A; Araujo, F; Barbosa, R. *Journal Of Grid Computing*.  
   [DOI](https://doi.org/10.1007/s10723-023-09718-2) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1007/s10723-023-09718-2)  
   Por que ler: Custo × disponibilidade no escalonamento ('manter o nível de serviço'); −6% a −18%

14. **DeltaScaling : How resources scalability/termination can be taken place Economically?** (2015). Kouki, Y; Hasan, MS; Ledoux, T. *2015 Ieee World Congress On Services*.  
   sem DOI: buscar o título no Google Scholar  
   Por que ler: Escalonamento e término de VMs considerando a cobrança; −30% com cerca de 1% de violações

15. **FitScale: Scalability of Legacy Applications Through Migration to Cloud** (2016). Hwang, J; Vukovic, M; Anerousis, N. *Service-Oriented Computing, (Icsoc 2016)*.  
   [DOI](https://doi.org/10.1007/978-3-319-46295-0_8) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1007/978-3-319-46295-0_8)  
   Por que ler: Migração de sistemas legados para nuvem com escalonamento vertical; ~5x menor custo; cenário de empresas

16. **Cost-Efficient VM Configuration Algorithm in the Cloud using Mix Scaling Strategy** (2017). Lu, L; Yu, JD; Zhu, YM; et al.. *2017 Ieee International Conference On Communications (Icc)*.  
   sem DOI: buscar o título no Google Scholar  
   Por que ler: Escalonamento misto (vertical + horizontal) para serviços de empresas; −31%

17. **Auto-scaling web applications in clouds: A cost-aware approach** (2017). Aslanpour, MS; Ghobaei-Arani, M; Toosi, AN. *Journal Of Network And Computer Applications*.  
   [DOI](https://doi.org/10.1016/j.jnca.2017.07.012) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1016/j.jnca.2017.07.012)  
   Por que ler: Auto-scaling de aplicações web com consciência de custo; −7%, controlando oscilação (70 citações)

18. **RightCapacity: SLA-driven Cross-Layer Cloud Elasticity Management** (2013). Kouki, Y; Ledoux, T. *International Journal Of Next-Generation Computing*.  
   sem DOI: buscar o título no Google Scholar  
   Por que ler: SLA-driven para provedor SaaS; −30% com cerca de 1% de violações

19. **AutoBurst: Autoscaling Burstable Instances for Cost-effective Latency SLOs** (2024). Hasan, R; Zhu, T; Urgaonkar, B. *Proceedings Of The 2024 Acm Symposium On Cloud Computing, Socc 2024*.  
   [DOI](https://doi.org/10.1145/3698038.3698530) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1145/3698038.3698530)  
   Por que ler: AutoBurst: autoscaling com burstable e SLO de latência; −25%

20. **Machine Learning-Driven Resource Provisioning in Modern Cloud Environments: A Taxonomic Survey** (2026). Kosim, SA; Santoso, BJ; Arrizki, DJ; et al.. *International Journal Of Advanced Computer Science And Applications*.  
   sem DOI: buscar o título no Google Scholar  
   Por que ler: Revisão relacionada (provisionamento com ML, 35 estudos): usar em 'trabalhos relacionados'

21. **Instance Type Selection in Proactive Horizontal Auto-Scaling** (2016). Morais, F; Lopes, R; Brasileiro, F. *2016 8Th Ieee International Conference On Cloud Computing Technology And Science (Cloudcom 2016)*.  
   [DOI](https://doi.org/10.1109/CloudCom.2016.28) · [CAPES](https://ez163.periodicos.capes.gov.br/login?url=https://doi.org/10.1109/CloudCom.2016.28)  
   Por que ler: Escolha do tipo de instância no autoscaling preditivo; até −50%
