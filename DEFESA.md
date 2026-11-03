# Roteiro de defesa

Equipe: Matheus Thurow, Rodrigo Nicola e Eduardo Bez.

## Demonstração em cinco etapas

1. Rodar `python -m unittest discover -s tests -v`. Explicar os valores manuais dos exemplos 7.1, 7.2 e 7.3.
2. Executar o exemplo 7.3 com FCFS e SJF, troca zero e `--log`. Mostrar todos os faults em t=0, retornos em t=20 e a diferença na fila.
3. Executar um cenário com `--cpus 1` e depois `--cpus 4`, preservando os outros argumentos. Conferir o speedup no consolidado.
4. Trocar RR entre `--quantum 2` e `--quantum 50`; mostrar resposta, espera, trocas e Gantt. Não prever melhora universal: consultar os resultados.
5. Trocar `--subst fifo/lru` e `--quadros 1/256` no exemplo pequeno. Mostrar proteção e retentativa sem duplicar faults. Evitar log de carga grande durante a apresentação.

```powershell
python -m simulador --arquivo cenarios/exemplos/exemplo_73.json --sched fcfs --custo-troca 0 --log --saida demo_fcfs
python -m simulador --arquivo cenarios/exemplos/exemplo_73.json --sched sjf --custo-troca 0 --log --saida demo_sjf
python -m simulador --arquivo cenarios/exemplos/exemplo_73.json --sched rr --quantum 2 --cpus 4 --quadros 1 --subst fifo --log --saida demo_memoria
```

## Questões que todos devem saber explicar

- Por que a referência que gera fault é repetida? O fault não consumiu a unidade de CPU.
- Por que proteger a página? Ela precisa permanecer disponível até o primeiro acesso após o retorno.
- Por que espera não inclui E/S, fault ou troca? A definição só conta presença na fila global.
- Por que resposta pode ser zero mesmo com troca e fault? É medida no primeiro despacho.
- Como um processo usa quatro CPUs? Ele usa uma por vez; os outros núcleos atendem outros processos.
- Como se resolve simultaneidade? Conclusões, chegadas/retornos por pid, preempções por CPU, despachos/acessos por CPU.
- FIFO e LRU são locais? Não: substituição global, excluindo páginas protegidas.
- O que acontece se todos os quadros estão protegidos? O processo continua bloqueado e tenta após 20 unidades sem um novo fault.
- O SJF usa a classe? Não; usa burst restante e desempata pela entrada na fila.
- Todos terminaram: isso prova ausência de starvation em geral? Não; somente não houve inanição observada nestas cargas finitas.
- Muitos faults provam thrashing? Não; faltas compulsórias e localidade também afetam a contagem.
- Por que speedup pode ficar abaixo de quatro? Chegadas espaçadas, E/S, faults, troca e mudança na interação com a memória.

## Divisão sugerida da apresentação

- Matheus: modelo, fila global, escalonadores e CLI.
- Rodrigo: paginação, proteção, substituição e testes.
- Eduardo: métricas, experimentos, gráficos e limitações.

A divisão é uma sugestão de preparação, não um registro de autoria individual do código.
Os três devem revisar e compreender toda a implementação antes da defesa.
