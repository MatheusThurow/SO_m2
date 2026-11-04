# Trabalho M2 - Sistemas Operacionais

**Equipe:** Matheus Thurow, Rodrigo Nicola e Eduardo Bez.
**Projeto:** escalonamento multiprocessado integrado à paginação sob demanda.

## Instalação e execução

Requer Python 3.11 ou superior. Validado com **Python 3.14.7 no Windows**.
O núcleo usa apenas a biblioteca padrão; matplotlib gera figuras, reportlab gera o relatório
e pypdf verifica o PDF. Versões medidas estão em `requirements-lock.txt`.
Para gerar novamente o relatório, a fonte Arial precisa estar instalada no computador.
O PDF pronto já incorpora a fonte e pode ser lido sem essa instalação.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m simulador --arquivo cenarios/cenario_A_t0.json --cpus 4 --sched rr --quantum 10 --subst lru --quadros 256 --custo-troca 1
```

Se o ambiente já estiver instalado, use `python` diretamente. Execute os comandos na raiz do projeto.

| Argumento | Valores / padrão |
| --- | --- |
| `--arquivo` | JSON obrigatório, lista de processos |
| `--cpus` | 1 ou 4; padrão 1 |
| `--sched` | fcfs, sjf, rr; padrão fcfs |
| `--quantum` | Inteiro positivo; padrão 10; só afeta RR |
| `--subst` | fifo ou lru; padrão lru |
| `--quadros` | Inteiro positivo; padrão 256 |
| `--custo-troca` | Inteiro não negativo; padrão 1 |
| `--log` | Grava eventos e conjuntos em estados.jsonl |
| `--saida` | Diretório de resultados; padrão resultados |

Exemplo pequeno para inspecionar o log:

```powershell
python -m simulador --arquivo cenarios/exemplos/exemplo_73.json --cpus 1 --sched fcfs --custo-troca 0 --log --saida demonstracao
```

Os parâmetros de cada configuração compõem o nome de sua pasta. Configurações diferentes
não se sobrescrevem; repetir a mesma configuração substitui seus arquivos nessa pasta.
Use `--saida` para preservar rodadas separadas.

## Reprodução completa

```powershell
python -m unittest discover -s tests -v
python experimentos.py
python gerar_relatorio.py
python validar_entrega.py
python empacotar.py
```

`experimentos.py` executa 32 configurações e repete cada uma integralmente para verificar
igualdade de métricas, processos e Gantt. A base LRU usa FCFS, SJF e RR com Q=2,5,10,20,50,
nos cenários A/B e com 1/4 CPUs. Quatro execuções adicionais usam FCFS/FIFO.
Q=5 e 20 são escolhas adicionais: o enunciado lista 2,10,50 mas conta cinco quantums.
Cada execução termina 1.000 processos e consome 40.398 unidades de CPU.

## Entregáveis

- `simulador/`: entrada, modelos, motor, escalonadores, memória e saídas.
- `cenarios/`: cópias byte a byte dos JSONs originais; exemplos em subdiretório.
- `tests/`: validações dos exemplos 5.5 e 7.1-7.3 e regras de fronteira.
- `resultados/consolidado.csv`: métricas da matriz, speedup e eficiência.
- `resultados/ambiente.json`: Python, SO, hardware lógico, hashes e comandos.
- `resultados/verificacao.json`: invariantes e repetibilidade.
- `resultados/<configuração>/`: resultado completo em JSON, CSVs por processo/CPU,
  Gantt de 0 a 200 em CSV e PNG.
- `output/pdf/relatorio_m2.pdf`: métodos, tabelas, três gráficos, análise e 32 Gantts.
- `relatorio/relatorio.md`: versão textual com as mesmas evidências.
- `DEFESA.md`: roteiro de demonstração e perguntas.
- `STATUS.md`: estado das tarefas e pendências externas.
- `referencias/`: enunciado e planejamento original preservados como referência.

## Convenções do motor

Tempo inteiro a partir de 0. Ao iniciar t, concluem-se os bursts da unidade anterior,
liberando quadros de terminados; chegadas e retornos são inseridos juntos por pid;
seguem preempções por índice de CPU e despachos. CPUs são atendidas por índice crescente.
Cada CPU resolve despacho/acesso antes da seguinte. Faults não consomem CPU nem tempo
na detecção e permitem outro despacho no mesmo instante. Operações simultâneas de memória
seguem essa ordem. A decisão de RR com fila vazia ocorre antes dos despachos, após entradas.

O contexto da CPU é atualizado no despacho, mesmo se o acesso seguinte gerar fault.
Retorno do mesmo contexto sem outro despacho não cobra troca. Custo zero contabiliza zero
trocas cobradas. Troca não consome burst, quantum ou referência. Resposta é medida no
primeiro despacho; o tempo de troca não integra espera na fila.

Páginas são identificadas por `(pid, página)` em quadros globais. A carga acontece no retorno
do fault, após 20 unidades; fica protegida até o primeiro acesso efetivo. Sem vítima,
repete a tentativa em 20 unidades sem novo fault. FIFO usa sequência de carga e LRU
sequência do último acesso, com ordem total para empates. Durante a proteção, LRU inicializa
a recência pela carga; o primeiro acesso a atualiza antes de a página tornar-se elegível.
Término libera quadros, E/S os mantém. Bloqueios são paralelos, sem fila de disco.

Espera soma apenas permanências na fila; turnaround = término - chegada;
resposta = primeiro despacho - chegada. Fazem-se asserções de conservação:
`útil + troca + ocioso = makespan` por CPU e
`espera + útil + troca + bloqueio = turnaround` por processo.
Taxa de faults = faults / referências lógicas (40.398), sem duplicar retentativas.
Utilização por CPU = (útil + troca) / makespan; percentuais têm intervalo desde t=0.
Speedup = makespan 1 CPU / makespan 4 CPUs equivalentes; eficiência = speedup / 4.
O rótulo curto/longo é usado somente na análise.

## Limitações e entrega externa

SJF conhece o burst futuro. Não se simulam TLB, cache, migração, bytes, endereços ou
fila de disco; CPUs são simuladas dentro de um processo Python. A latência de fault
de produção é 20; a API interna admite 5 e memória desligada apenas para os exemplos.

O PDF informa entrega em **03/11/2026 às 19h**. Critérios adicionais do AVA não foram
consultados. Repositório informado pela equipe: [SO_m2](https://github.com/MatheusThurow/SO_m2).
O estado da publicação é registrado em `STATUS.md`. O pacote local e a publicação no GitHub
não representam submissão ao professor pelo AVA. Confirmar os critérios e fazer o envio no AVA.
