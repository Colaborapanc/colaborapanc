# BLOCO 1 — CHECKLIST DE CONFORMIDADE COM O EDITAL

**Categoria considerada para esta versão textual:** MESTRE E DOUTOR (adoção técnica por ausência de categoria preenchida no enunciado).  
**Linha de pesquisa/subtema:** Inteligência Artificial e Meio Ambiente.  
**Idioma:** Português (integral).  
**Estrutura exigida contemplada:** título; autor; orientador; instituição de vínculo; instituição onde se desenvolveu a pesquisa; resumo; introdução; objetivos; material e métodos; resultados e discussão; conclusões; referências bibliográficas; palavras-chave.  
**Faixa de páginas alvo (A4, Arial 12, espaçamento 1,5):** texto redigido com densidade para versão expandida de submissão, dependente de diagramação final.  
**Exigência de resultados finais:** atendida por descrição de resultados efetivamente observáveis no estado real do projeto-base.  
**Exigência de aplicação prática:** atendida, com foco em fluxo operacional de IA assistiva para validação de registros de PANCs.  
**Declaração de uso de IA:** incluída em seção específica obrigatória.

---

# BLOCO 2 — TRABALHO CIENTÍFICO COMPLETO

## Título
**ColaboraPANC: Inteligência Artificial Assistiva para Mapeamento Georreferenciado, Validação Humana e Priorização Territorial de Plantas Alimentícias Não Convencionais**

## Autor
[INSERIR NOME]

## Orientador(a)
[INSERIR NOME]

## Instituição de vínculo
[INSERIR NOME COMPLETO + ENDEREÇO + TELEFONE + E-MAIL]

## Instituição onde a pesquisa foi desenvolvida
[INSERIR NOME COMPLETO + ENDEREÇO + TELEFONE + E-MAIL]

## Resumo
Este trabalho apresenta a consolidação técnico-científica do projeto ColaboraPANC, uma plataforma aplicada ao mapeamento colaborativo de Plantas Alimentícias Não Convencionais (PANCs), articulando geotecnologias, integração de serviços de identificação por imagem e validação humana orientada por papéis. O problema central enfrentado é a dificuldade de transformar registros distribuídos de campo em conhecimento confiável e auditável para uso social e ambiental, sobretudo quando há incerteza na identificação botânica. A pesquisa foi concluída no escopo de implementação e documentação do fluxo científico operacional existente no sistema: cadastro de ponto georreferenciado, envio de imagem, inferência assistida por Inteligência Artificial, revisão por especialista, registro de histórico decisório, produção de métricas e cálculo de priorização territorial. Metodologicamente, foi conduzida auditoria do código-fonte e dos módulos de backend, API e aplicativo móvel, seguida de padronização documental aderente à implementação real, sem inclusão de funcionalidades não comprovadas. Os resultados finais obtidos incluem a explicitação e organização de um ciclo humano-no-loop rastreável, a descrição formal dos componentes de confiança e de risco da inferência, o detalhamento de endpoints científicos efetivamente disponíveis e a sistematização da priorização territorial explicável por heurística. Conclui-se que a contribuição principal do trabalho para o tema “Inteligência Artificial para o Bem Comum” reside na aplicação responsável da IA como suporte à decisão, com governança, transparência e delimitação explícita de limites técnicos.

## Introdução
A ampliação do uso de Inteligência Artificial em problemas de interesse público exige mecanismos técnicos que conciliem desempenho operacional, confiabilidade e responsabilidade social. No contexto de biodiversidade alimentar e segurança socioambiental, o mapeamento de PANCs depende de registros de campo heterogêneos, com diferentes níveis de qualidade de imagem, nomenclatura popular variável e lacunas de validação especializada. Esse cenário cria um problema concreto: sem um fluxo estruturado de inferência e revisão humana, observações potencialmente relevantes permanecem com baixa utilidade para planejamento territorial, educação alimentar e monitoramento ambiental.

O projeto ColaboraPANC foi desenvolvido para enfrentar esse desafio por meio de uma arquitetura que integra georreferenciamento, cadastro colaborativo, serviços de identificação botânica por imagem e mecanismos de revisão por especialistas. A perspectiva científica adotada neste trabalho é a de IA assistiva para o bem comum, isto é, uso da IA como componente de apoio à tomada de decisão, e não como substituição da validação humana em contextos de incerteza.

No estado atual da implementação, o sistema apresenta um núcleo científico operacional com trilha de auditoria: cada inferência pode ser persistida, confrontada com decisão humana e incorporada a métricas de acompanhamento. Essa característica responde diretamente a exigências contemporâneas de governança algorítmica, sobretudo em aplicações de impacto ambiental e territorial. Assim, a relevância deste trabalho está em demonstrar, de forma aplicada, como um sistema real pode estruturar o ciclo completo entre coleta cidadã de dados, inferência automatizada e validação especializada, preservando rastreabilidade e transparência.

## Objetivos
O objetivo geral foi consolidar e apresentar, em formato técnico-científico, o funcionamento concluído do ColaboraPANC como sistema de IA assistiva para mapeamento e validação de PANCs com finalidade pública.

Como objetivos específicos, buscou-se: caracterizar o problema operacional de identificação e validação de registros de PANCs em ambiente colaborativo; descrever a arquitetura real do sistema com ênfase em backend, API, integração externa e aplicativo móvel; formalizar o fluxo científico implementado entre inferência, revisão humana e histórico decisório; explicitar o método de priorização territorial baseado em critérios interpretáveis; documentar resultados finais efetivamente observáveis na implementação; e estabelecer diretrizes de governança, limites e uso responsável da IA no escopo da aplicação.

## Material e Métodos
A pesquisa foi conduzida como estudo técnico aplicado sobre um sistema de software funcional, com abordagem descritiva e analítica do artefato computacional. O material principal foi o repositório do projeto ColaboraPANC, incluindo código-fonte, modelos de dados, serviços de integração, rotas de API, componentes móveis, testes existentes e documentação técnica.

A primeira etapa consistiu em auditoria estruturada da implementação real. Foram verificados módulos do backend Django e da API REST, com foco em entidades centrais de fluxo científico, tais como os modelos de ponto georreferenciado, predição de IA, validação de especialista e histórico de validação. Em paralelo, foram analisados serviços de inferência com múltiplos provedores e o mecanismo de priorização territorial por score composto.

Na segunda etapa, foi realizada análise de consistência entre documentação anterior e estado efetivo do código. Esse procedimento permitiu separar funcionalidades implementadas, parcialmente implementadas e planejadas, evitando descrição de capacidades não comprovadas.

Na terceira etapa, procedeu-se à sistematização científica do fluxo operacional, contemplando: cadastro de ponto, anexação de imagem, execução de inferência, classificação de confiança, encaminhamento para revisão humana, decisão final por especialista, registro de eventos auditáveis e disponibilização de métricas agregadas. Também foram examinadas integrações externas utilizadas na identificação botânica e no contexto ambiental.

Na quarta etapa, elaborou-se o texto técnico final com linguagem científica e aderência ao tema do edital, mantendo compromisso com resultados observáveis e sem inferências quantitativas não suportadas por dados formais publicados no escopo desta pesquisa.

## Resultados da pesquisa e discussão
O primeiro resultado final consiste na caracterização de um fluxo de IA assistiva operacionalizado de modo auditável. A implementação permite que uma imagem associada a um ponto de PANC seja processada por provedores externos de identificação botânica, com retorno normalizado em formato top-k e score de confiança. Esse resultado é tecnicamente relevante porque transforma saídas heterogêneas de serviços terceiros em uma estrutura uniforme para consumo interno do sistema.

O segundo resultado é a incorporação explícita de governança humano-no-loop. A decisão final sobre validação não é automatizada. Em vez disso, a plataforma mantém registro de predição algorítmica, decisão de revisor autorizado e histórico de eventos, incluindo possibilidade de justificar divergência entre hipótese da IA e conclusão humana. Essa solução atende ao princípio de responsabilização em IA aplicada ao bem comum, reduzindo risco de uso acrítico da automação.

O terceiro resultado foi a formalização do componente de priorização territorial em lógica explicável. O score territorial implementado combina incidência local, risco climático, confiabilidade de validação e recência de observação, com pesos definidos e rastreáveis. Embora se trate de heurística e não de modelo preditivo treinado, a abordagem oferece uma base transparente para priorização operacional inicial, passível de revisão e calibração futura.

O quarto resultado refere-se à disponibilidade de métricas operacionais agregadas no dashboard científico, incluindo contagem de pontos submetidos, inferências realizadas, taxas de validação e rejeição, distribuição por confiança e indicadores de concordância entre IA e especialista. Mesmo sem apresentação de séries estatísticas extensas neste texto, a existência desses indicadores no sistema representa avanço metodológico por permitir monitoramento contínuo da qualidade do processo.

Do ponto de vista de aplicação prática, os resultados demonstram que é viável estruturar uma cadeia completa de coleta colaborativa e qualificação de dados ambientais com apoio de IA, desde que a inferência seja tratada como sugestão e submetida a revisão especializada. Esse desenho reduz o risco de decisões automáticas inadequadas e aumenta a utilidade social dos registros para ações de educação, conservação e planejamento territorial.

Como discussão crítica, identificou-se que a dependência de provedores externos de identificação impõe limitações de disponibilidade, custo e cobertura taxonômica. Além disso, a qualidade da imagem e o contexto de coleta influenciam diretamente a confiança das predições. Esses fatores reforçam a pertinência da escolha metodológica de revisão humana obrigatória em cenários de confiança intermediária ou baixa. Também se reconhece que a evolução para métricas científicas mais robustas exige ampliação de base validada e desenho de avaliação experimental dedicado.

## Conclusões
A pesquisa concluiu, com base no sistema implementado, que o ColaboraPANC materializa uma aplicação concreta de Inteligência Artificial para o Bem Comum ao combinar inferência assistiva, validação humana e rastreabilidade decisória em contexto socioambiental. O trabalho demonstra que a principal contribuição não está na automação irrestrita, mas na organização de um processo confiável de apoio à decisão para dados colaborativos de biodiversidade alimentar.

Conclui-se, ainda, que a arquitetura analisada oferece contribuição original na articulação entre georreferenciamento, IA multimprovedor, governança de validação e priorização territorial explicável em um mesmo fluxo operacional. Essa integração fortalece a utilidade pública do sistema e cria condições para replicação metodológica em outros cenários de monitoramento ambiental participativo.

Por fim, o estudo evidencia que resultados finais em projetos de IA aplicada devem ser apresentados com delimitação de escopo e transparência sobre limites técnicos, preservando responsabilidade científica e ética no uso de algoritmos em problemas reais.

## Palavras-chave
Inteligência Artificial Assistiva; Bem Comum; PANC; Validação Humana; Priorização Territorial.

## Referências bibliográficas
BRASIL. Conselho Nacional de Desenvolvimento Científico e Tecnológico. **32º Prêmio Jovem Cientista 2026: Tema Inteligência Artificial para o Bem Comum**. Brasília: CNPq, 2026.

DJANGO SOFTWARE FOUNDATION. **Django Documentation**. Disponível em: <https://docs.djangoproject.com/>. Acesso em: [INSERIR DATA].

POSTGIS PROJECT. **PostGIS Documentation**. Disponível em: <https://postgis.net/documentation/>. Acesso em: [INSERIR DATA].

PLANTNET. **Pl@ntNet API**. Disponível em: <https://my.plantnet.org/>. Acesso em: [INSERIR DATA].

PLANT.ID. **Plant.id API Documentation**. Disponível em: <https://web.plant.id/>. Acesso em: [INSERIR DATA].

OPEN-METEO. **Weather API Documentation**. Disponível em: <https://open-meteo.com/>. Acesso em: [INSERIR DATA].

MAPBIOMAS. **MapBiomas Alerta**. Disponível em: <https://plataforma.alerta.mapbiomas.org/>. Acesso em: [INSERIR DATA].

## Declaração sobre o uso de ferramentas de Inteligência Artificial
Foi utilizada ferramenta de Inteligência Artificial generativa para apoio à redação técnico-científica, organização textual e revisão de coerência estrutural do manuscrito, sem substituição da análise técnica do projeto-base. A responsabilidade intelectual, científica e ética pelo conteúdo final é integralmente do(a) autor(a) do trabalho.

---

# BLOCO 3 — VERIFICAÇÃO FINAL DE ADEQUAÇÃO

O texto atende integralmente à **estrutura da categoria MESTRE E DOUTOR** e às exigências centrais do edital quanto a idioma, formalidade, aplicação prática, resultados finais e declaração de uso de IA.

Pontos que ainda dependem de revisão humana final antes da submissão:
1. Confirmação da categoria oficial do(a) candidato(a), pois o enunciado recebido não trouxe o valor preenchido.
2. Preenchimento de identificação formal: autor, orientador, instituição(ões), endereço, telefone e e-mail.
3. Ajuste final da seção de referências com data de acesso e eventuais normas bibliográficas institucionais exigidas.
4. Revisão de paginação após diagramação (A4, Arial 12, espaçamento 1,5) para aderência exata ao limite da categoria.
5. Validação final do título e da linha de pesquisa, caso a instituição exija nomenclatura específica.
