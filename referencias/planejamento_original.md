# Planejamento — Trabalho M2 de Sistemas Operacionais

**Projeto:** Simulador de escalonamento multiprocessado com paginação sob demanda
**Data:** 03/11/2026
**Equipe:** Matheus Thurow, Rodrigo Nicola e Eduardo Bez.
**Prazo de entrega informado no PDF:** 03/11/2026 até as 19h.
**Status:** planejamento preparado; implementação ainda não iniciada.

## 1. Objetivo

Desenvolver um único simulador que integre escalonamento de CPU e memória virtual, execute os cenários fornecidos pelo professor e permita comparar desempenho, justiça e uso de recursos em máquinas de 1 e 4 CPUs.

Este documento organiza o desenvolvimento em 12 tasks com dependências, entregas e critérios de conclusão. Serve como roteiro para uma execução contínua, com atualizações de progresso e verificação ao final de cada etapa.

## 2. Materiais de referência

- [Enunciado — TRABALHO M2 SO 2026_.pdf](TRABALHO%20M2%20SO%202026_.pdf)
- [Cenário A — cenario_A_t0.json](../cenarios/cenario_A_t0.json)
- [Cenário B — cenario_B_espacadas.json](../cenarios/cenario_B_espacadas.json)

Os requisitos são os do enunciado. As propostas de arquitetura e as escolhas adicionais deste planejamento são decisões de implementação, sujeitas a ajuste se o AVA ou o professor trouxerem outra orientação.

## 3. Situação inicial dos dados

Os dois arquivos foram lidos integralmente e tiveram a estrutura validada.

| Informação | Cenário A | Cenário B |
| --- | ---: | ---: |
| Processos | 1.000 | 1.000 |
| Processos curtos | 952 | 952 |
| Processos longos | 48 | 48 |
| Primeira chegada | 0 | 1 |
| Última chegada | 0 | 10.604 |
| Unidades totais de CPU | 40.398 | 40.398 |
| Referências lógicas a páginas | 40.398 | 40.398 |
| Bursts de CPU | 2.969 | 2.969 |
| Etapas de E/S | 1.969 | 1.969 |
| Páginas por processo | 4 a 32 | 4 a 32 |

Os processos são idênticos nos dois cenários, exceto pelo campo `chegada`. O JSON contém diretamente uma lista de processos.

Validações já realizadas:

- [x] JSON válido nos dois arquivos.
- [x] Identificadores de processos únicos.
- [x] Chegadas inteiras e não negativas.
- [x] Alternância de bursts de CPU e E/S, começando e terminando em CPU.
- [x] Quantidade de referências igual à duração de cada burst de CPU.
- [x] Referências dentro do intervalo de páginas de cada processo.

Essa conferência valida os dados de entrada; ainda não representa uma execução do simulador.

## 4. Proposta técnica

- **Linguagem definida:** Python 3, com a versão de execução registrada no README.
- **Execução principal:** linha de comando, com os parâmetros exigidos no enunciado.
- **Simulação:** tempo discreto, com CPUs simuladas dentro de um único motor determinístico.
- **Organização:** módulos separados para entrada, modelos, motor, escalonadores, memória e saídas.
- **Estruturas previstas:** fila para FCFS/RR, estrutura de seleção por burst restante para SJF e estruturas de eventos e páginas com desempates determinísticos.
- **Saídas:** resumo no terminal, resultados estruturados para consolidação, Gantt em CSV e figura, além de log habilitado por `--log`.
- **Gráficos:** biblioteca de visualização a ser registrada nas dependências; o núcleo do simulador deve permanecer separado da geração de figuras.

Não é necessário criar threads ou processos reais para representar os núcleos: o programa simulará o avanço de 1 ou 4 CPUs e a interação com a memória.

## 5. Quadro de tasks

| ID | Task | Dependências | Status |
| --- | --- | --- | --- |
| T01 | Estrutura, configuração e entrada JSON | Nenhuma | Pendente |
| T02 | Motor da simulação e estados | T01 | Pendente |
| T03 | Escalonadores FCFS e SJF | T02 | Pendente |
| T04 | Escalonador Round Robin | T02 | Pendente |
| T05 | Troca de contexto e tempos por CPU | T02 | Pendente |
| T06 | Memória virtual, FIFO e LRU | T02 | Pendente |
| T07 | Métricas e comparação entre execuções | T03 a T06 | Pendente |
| T08 | Resumo, Gantt e log de estados | T07 | Pendente |
| T09 | Validação integrada | T03 a T08 | Pendente |
| T10 | Execução dos experimentos | T09 | Pendente |
| T11 | Relatório e análise dos resultados | T10 | Pendente |
| T12 | Empacotamento, README e preparação da defesa | T11 | Pendente |

Os critérios de cada task devem ser verificados durante sua implementação. A T09 consolida a validação do sistema completo antes das cargas de 1.000 processos.

## 6. Detalhamento das tasks

### T01 — Estrutura, configuração e entrada JSON

**Objetivo:** preparar a base do programa e carregar os cenários sem alterar os arquivos originais.

- [ ] Criar a estrutura de módulos e definir os dados de processo, burst, CPU, evento e configuração.
- [ ] Implementar a leitura da lista JSON e as validações estruturais já identificadas.
- [ ] Disponibilizar `--arquivo`, `--cpus`, `--sched`, `--quantum`, `--subst`, `--quadros`, `--custo-troca` e `--log`.
- [ ] Aceitar CPUs 1 ou 4, escalonadores fcfs/sjf/rr e substituição fifo/lru.
- [ ] Usar 256 quadros e custo de troca 1 como padrões.
- [ ] Rejeitar configurações inválidas com mensagens claras.

**Concluída quando:** os dois cenários puderem ser carregados e os parâmetros forem escolhidos pela linha de comando, sem edição do código.

### T02 — Motor da simulação e estados

**Objetivo:** controlar o tempo e o ciclo de vida de cada processo.

- [ ] Implementar os estados Novo, Pronto, Executando, Bloqueado e Terminado.
- [ ] Manter uma única fila global de prontos.
- [ ] Simular 1 e 4 CPUs; um processo utiliza somente uma CPU por vez.
- [ ] Executar chegadas e retornos de E/S em seus instantes corretos.
- [ ] Tratar bloqueios em paralelo, sem fila de disco.
- [ ] No mesmo instante, inserir chegadas e retornos em ordem de pid, depois preempções por quantum e então realizar despachos.
- [ ] Atender CPUs livres por índice crescente.
- [ ] Registrar entrada e saída da fila de prontos para medir espera.

**Concluída quando:** pequenos exemplos percorrerem os estados corretamente, sem processos duplicados, perdidos ou executando em duas CPUs.

### T03 — FCFS e SJF

**Objetivo:** implementar as políticas não preemptivas.

- [ ] FCFS: selecionar pela ordem de entrada na fila.
- [ ] SJF: selecionar o menor burst de CPU restante.
- [ ] No empate do SJF, respeitar a ordem de entrada na fila.
- [ ] Recolocar retornos de bloqueio na fila segundo as regras do modelo.
- [ ] Garantir que a chegada de um processo menor não interrompa o SJF.
- [ ] Não usar o campo `classe` como critério de escalonamento.

**Concluída quando:** FCFS e SJF reproduzirem a ordem e os tempos esperados em casos pequenos, incluindo o exemplo da seção 7.3.

### T04 — Round Robin

**Objetivo:** implementar quantum configurável e preempção.

- [ ] Contabilizar o quantum a partir das unidades de CPU efetivamente executadas.
- [ ] Ao esgotar o quantum com outro processo pronto, enviar o processo atual para o fim da fila.
- [ ] Se não houver outro pronto, continuar o mesmo processo com novo quantum e sem troca.
- [ ] Liberar a CPU ao terminar um burst, mesmo que ainda reste quantum.
- [ ] Perder o restante do quantum quando houver page fault.
- [ ] Tratar corretamente chegadas e retornos no mesmo instante da preempção.

**Concluída quando:** RR funcionar com diferentes quantums e respeitar os casos de fila vazia, fim de burst e bloqueio.

### T05 — Troca de contexto

**Objetivo:** aplicar a Convenção A do enunciado.

- [ ] Registrar o último processo executado por cada CPU.
- [ ] Cobrar o custo quando o processo despachado for diferente do último dessa CPU, inclusive no primeiro despacho.
- [ ] Não cobrar quando o mesmo processo continuar ou retornar à CPU sem outro processo ter executado nela.
- [ ] Considerar o processo despachado fora da fila de prontos durante a troca.
- [ ] Durante a troca, ocupar a CPU sem consumir burst, quantum ou referência.
- [ ] Separar tempos útil, de troca e ocioso.

**Concluída quando:** para cada CPU, `útil + troca + ocioso = makespan`, e o custo configurado for aplicado somente nas situações previstas.

### T06 — Memória virtual, FIFO e LRU

**Objetivo:** integrar paginação sob demanda ao motor de execução.

- [ ] Manter quadros globais compartilhados e identificar páginas pelo par `(pid, página)`.
- [ ] Iniciar a memória vazia e realizar uma referência por unidade de CPU executada.
- [ ] Em page fault, bloquear por 20 unidades e liberar a CPU sem consumir a unidade de processamento.
- [ ] No retorno, repetir a referência e proteger a página carregada até seu primeiro acesso efetivo.
- [ ] Usar quadro livre antes de substituir uma página.
- [ ] Implementar substituição global FIFO e LRU, excluindo páginas protegidas.
- [ ] Se não houver vítima disponível, manter o bloqueio e tentar novamente após 20 unidades, sem contar um novo fault.
- [ ] Manter páginas durante a E/S e liberar os quadros quando o processo terminar.
- [ ] Não alterar a memória por causa de troca de contexto.
- [ ] Documentar a ordem de processamento de retornos e os desempates internos das políticas de memória.

**Concluída quando:** os exemplos com faults e os casos de substituição/proteção funcionarem sem exceder o número de quadros.

### T07 — Métricas

**Objetivo:** calcular as métricas conforme as definições do professor.

- [ ] Espera média e máxima, contando somente intervalos na fila de prontos.
- [ ] Turnaround médio: término menos chegada.
- [ ] Resposta média: primeiro despacho menos chegada, incluindo a convenção de despacho anterior à troca.
- [ ] Makespan: instante do último término.
- [ ] Trocas de contexto totais e por CPU.
- [ ] Tempos útil, de troca e ocioso por CPU, com percentuais.
- [ ] Utilização: `(útil + troca) / makespan`.
- [ ] Page faults totais e taxa de faults com denominador documentado.
- [ ] Speedup e eficiência entre execuções equivalentes com 1 e 4 CPUs.
- [ ] Preservar o rótulo curto/longo para análise de justiça, sem influenciar o escalonador.

**Concluída quando:** métricas de exemplos pequenos conferirem com o cálculo manual e as comparações usarem o mesmo cenário, escalonador, quantum e memória.

### T08 — Resumo, Gantt e log

**Objetivo:** produzir saídas que permitam reproduzir e explicar a simulação.

- [ ] Mostrar parâmetros e métricas no resumo de cada execução.
- [ ] Salvar resultados estruturados com identificadores claros de cenário e configuração.
- [ ] Gerar Gantt da janela 0 a 200, com uma faixa por CPU.
- [ ] Identificar os intervalos como pid, TROCA ou OCIOSA.
- [ ] Gerar CSV com as colunas `cpu,inicio,fim,evento` e uma figura legível.
- [ ] Com `--log`, registrar mudanças de estado, evento e pid, fila de prontos em ordem, bloqueados com retornos, ocupação das CPUs e quadros ocupados.
- [ ] Evitar sobrescrever resultados de configurações diferentes.

**Concluída quando:** cada execução produzir as saídas previstas e o log permitir rastrear as regras do modelo em um caso pequeno.

### T09 — Validação integrada

**Objetivo:** verificar a correção antes de executar a matriz completa.

- [ ] Reproduzir o exemplo 7.1 sem memória: makespan 13, CPU útil 10, troca 3, espera média 4,67 e turnaround médio 9.
- [ ] Reproduzir o exemplo 7.2 com latência de fault 5 no ambiente de teste.
- [ ] Reproduzir o exemplo 7.3: espera média 3,67 em FCFS e 2,33 em SJF.
- [ ] Manter a latência de fault de produção em 20; valores especiais servem aos exemplos de validação.
- [ ] Verificar chegadas simultâneas, retorno de E/S, fim de burst e quantum no mesmo instante.
- [ ] Verificar RR sem concorrentes, SJF com empate e CPUs livres simultaneamente.
- [ ] Verificar FIFO/LRU com poucas páginas e o caso de todos os quadros protegidos.
- [ ] Confirmar término dos 1.000 processos e consumo total de CPU igual a 40.398 em cada cenário.
- [ ] Confirmar repetibilidade: entrada e parâmetros iguais produzem os mesmos resultados.
- [ ] Medir o tempo real de execuções completas com 1.000 processos e verificar o objetivo do enunciado de execução em poucos minutos, registrando hardware, versão do interpretador e configuração; o PDF não fixa um limite numérico.

**Concluída quando:** os exemplos e invariantes passarem e não restarem divergências de execução conhecidas.

### T10 — Experimentos

**Objetivo:** executar e consolidar a matriz de comparação.

- [ ] Automatizar as execuções dos cenários A e B.
- [ ] Executar cada variação com 1 e 4 CPUs.
- [ ] Usar LRU, 256 quadros e custo de troca 1 nas execuções base.
- [ ] Executar FCFS, SJF e RR com os quantums definidos na seção 7 deste planejamento.
- [ ] Executar pelo menos quatro configurações adicionais com FIFO e comparar com suas correspondentes LRU.
- [ ] Registrar comandos, parâmetros, resultados e duração real das execuções.
- [ ] Conferir o objetivo de execução em poucos minutos em cada configuração e investigar os casos que o ultrapassarem, preservando as regras do modelo.
- [ ] Calcular speedup e eficiência nas combinações equivalentes.

**Concluída quando:** todas as combinações planejadas estiverem concluídas e consolidadas, sem misturar configurações, e o desempenho tiver sido verificado em relação ao objetivo de execução em poucos minutos, com condições de medição e eventuais limitações registradas.

### T11 — Relatório e análise

**Objetivo:** explicar a implementação e sustentar as conclusões com dados.

- [ ] Descrever o problema, o modelo e as estruturas de dados escolhidas.
- [ ] Apresentar uma tabela por cenário com todas as execuções e métricas obrigatórias.
- [ ] Incluir pelo menos três gráficos: espera por escalonador, efeito do quantum e speedup.
- [ ] Incluir no relatório ou em seu apêndice uma figura legível do Gantt de 0 a 200 para cada execução/configuração, identificada por cenário, CPUs, escalonador, quantum e memória; destacar no corpo exemplos de 1 e 4 CPUs discutidos na análise.
- [ ] Comparar FIFO e LRU, incluindo faults e desempenho.
- [ ] Analisar justiça entre processos curtos e longos e investigar starvation, efeito comboio e thrashing somente quando os dados sustentarem.
- [ ] Vincular cada conclusão à execução e à métrica correspondente.
- [ ] Registrar limitações, incluindo o conhecimento prévio do burst usado pelo SJF e a ausência de fila de disco.

**Concluída quando:** o relatório explicar o comportamento observado, reconhecer limitações e permitir localizar a evidência de cada conclusão.

### T12 — Entrega e defesa

**Objetivo:** deixar o projeto executável e preparar a apresentação.

- [ ] Criar README com requisitos, instalação, execução, parâmetros, exemplos e reprodução dos experimentos.
- [ ] Registrar a versão de Python e as dependências efetivamente usadas.
- [ ] Organizar código, cenários, resultados, gráficos, relatório e validações.
- [ ] Publicar o código em repositório acessível ao professor, com README, instruções de execução e resultados reproduzíveis.
- [ ] Conferir a identificação dos três integrantes e o prazo de entrega informado no PDF, além de eventual atualização no AVA.
- [ ] Conferir as orientações adicionais e critérios de entrega do AVA.
- [ ] Validar a execução a partir do pacote final, seguindo o README.
- [ ] Preparar demonstrações alterando CPUs, escalonador, quantum, quadros e substituição sem editar o código.
- [ ] Garantir que os integrantes consigam explicar as regras, estruturas, métricas e limitações.

**Concluída quando:** o código estiver publicado em repositório acessível ao professor, o projeto puder ser executado pelas instruções fornecidas e todos os itens exigidos estiverem disponíveis para revisão e entrega conforme o AVA.

## 7. Matriz de experimentos e divergência no enunciado

A tabela do enunciado exige RR com quantums 2, 10 e 50, mas a contagem textual menciona cinco quantums e 28 execuções base.

| Interpretação | Variações por cenário/CPU | Execuções base |
| --- | ---: | ---: |
| Tabela: FCFS, SJF, RR com Q = 2, 10 e 50 | 5 | 20 |
| Texto: FCFS, SJF, RR com cinco quantums | 7 | 28 |

**Proposta para avançar sem perder cobertura:** executar RR com Q = 2, 5, 10, 20 e 50. Os valores 5 e 20 são escolhas adicionais deste planejamento, não uma exigência confirmada do professor. Se o AVA esclarecer outros valores, ajustar a matriz antes das execuções.

| Bloco | Configuração | Quantidade prevista |
| --- | --- | ---: |
| Base | 2 cenários × 2 quantidades de CPUs × 7 variações; LRU, 256 quadros, troca 1 | 28 |
| Comparação de memória | FCFS × cenários A/B × CPUs 1/4; FIFO, 256 quadros, troca 1 | 4 |
| Total planejado | Execuções completas dos cenários fornecidos | 32 |

Os quatro casos FIFO possuem correspondentes LRU na base. Casos pequenos de validação são adicionais e não entram nessa contagem. Variação de quadros é opcional e só será incluída se contribuir para a análise.

## 8. Ordem de execução contínua

1. Preparar estrutura e entrada — T01.
2. Implementar motor e estados — T02.
3. Integrar escalonadores e troca de contexto — T03, T04 e T05.
4. Integrar memória virtual — T06.
5. Implementar métricas e saídas — T07 e T08.
6. Consolidar validação e corrigir divergências — T09.
7. Executar a matriz completa — T10.
8. Produzir o relatório com os resultados reais — T11.
9. Organizar a entrega e a defesa — T12.

As tasks serão atualizadas à medida que suas entregas forem verificadas. Uma falha na validação deve ser corrigida antes de iniciar os experimentos completos. Não é necessário pedir confirmação ao final de cada task; decisões rotineiras serão registradas no projeto.

## 9. Convenções e pontos pendentes

| Ponto | Tratamento planejado |
| --- | --- |
| Quantidade de quantums | Cobrir cinco valores conforme proposta acima e conferir eventual esclarecimento do AVA. |
| Taxa de page faults sem fórmula explícita | Documentar a convenção proposta: faults contados / referências lógicas de CPU; tentativas repetidas de resolver o mesmo fault não aumentam o numerador. |
| Empates internos de memória | Definir desempate determinístico e documentá-lo, preservando FIFO/LRU e a proteção exigida. |
| Primeiro despacho | Resposta medida no despacho; a troca posterior não integra a espera na fila. |
| Carga idêntica para 1 e 4 CPUs | Preservar os arquivos e reiniciar integralmente os estados em cada execução. |
| Critérios complementares no AVA | Conferir antes de fechar o pacote; o conteúdo do AVA não foi fornecido nesta conversa. |
| Desempenho do simulador | Verificar o objetivo de execução em poucos minutos por execução completa, sem inventar um limite numérico ausente do PDF; registrar ambiente e duração e evitar processamento desnecessário em intervalos sem eventos, preservando o tempo discreto e a ordem dos eventos. |
| Gantts no relatório | A seção 9.2 do PDF pede uma figura por configuração, enquanto a seção 11 menciona dois Gantts (1 e 4 CPUs). Para cobrir ambas, incluir todas as figuras no relatório ou apêndice e destacar exemplos de 1 e 4 CPUs no corpo. |

## 10. Entregáveis finais previstos

- [ ] Código-fonte do simulador.
- [ ] Cenários originais usados nos experimentos.
- [ ] Validações e casos pequenos reproduzíveis.
- [ ] Comando ou script para reproduzir a matriz de experimentos.
- [ ] Resumos e tabelas consolidadas de resultados.
- [ ] Gantts de cada execução em CSV e figuras, com as figuras incluídas no relatório ou apêndice.
- [ ] Pelo menos três gráficos de análise.
- [ ] Relatório com métodos, resultados, análise e limitações.
- [ ] README com instruções completas de execução.
- [ ] Código publicado em repositório acessível ao professor, com instruções e resultados reproduzíveis.
- [ ] Pacote final organizado no formato solicitado pelo AVA, quando aplicável.

## 11. Critério geral de conclusão

O trabalho estará concluído quando o simulador respeitar as regras do enunciado, reproduzir os casos de validação, executar os dois cenários nas configurações planejadas e gerar evidências suficientes para o relatório e a defesa. Os resultados devem vir das execuções reais e ser reproduzíveis a partir dos arquivos e comandos entregues. O código deve estar publicado em repositório acessível ao professor; o relatório ou seu apêndice deve incluir os Gantts por configuração, e as medições devem demonstrar o atendimento ao objetivo de execução em poucos minutos ou explicitar as limitações encontradas.

**Próxima ação prevista:** iniciar a T01 quando o desenvolvimento for solicitado.

