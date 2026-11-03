# Estado do trabalho - 03/11/2026

| Etapa | Estado | Evidência |
| --- | --- | --- |
| T01 - Estrutura, configuração e JSON | Concluída | CLI e entrada validadas; arquivos originais preservados |
| T02 - Motor e estados | Concluída | Testes e invariantes nas 32 configurações |
| T03 - FCFS/SJF | Concluída | Exemplos 7.1/7.3 e testes de empate/não preempção |
| T04 - RR | Concluída | Cinco quantums e testes de fronteira |
| T05 - Troca de contexto | Concluída | Convenção documentada; conservação de tempos por CPU |
| T06 - Memória FIFO/LRU | Concluída | Proteção, retentativa e liberação verificadas |
| T07 - Métricas | Concluída | Resultados por CPU/processo e consolidado |
| T08 - Resumo/Gantt/log | Concluída | 32 figuras/CSVs e demonstração com JSONL |
| T09 - Validação integrada | Concluída | 12 testes; 32 repetições idênticas; 40.398 unidades úteis por execução |
| T10 - Experimentos | Concluída | 28 casos base LRU e quatro FIFO |
| T11 - Relatório | Concluída | PDF, versão Markdown, três gráficos e apêndice com 32 Gantts |
| T12 - Entrega e defesa | Parcial | README, roteiro, pacote validado e publicação concluídos; AVA e preparação individual pendentes |

## Publicação

Publicado em https://github.com/MatheusThurow/SO_m2, na branch `codex/trabalho-m2`,
que se tornou a branch padrão do repositório inicialmente vazio.
O envio foi confirmado por `git ls-remote`, e a página pública foi aberta sem autenticação.
Os bytes dos cenários e do PDF foram comparados com os blobs do commit publicado.
O histórico Git identifica os commits; `validacao/pacote.json` registra execução a partir do ZIP extraído.

## Pendências externas

- Consultar os critérios complementares no AVA e conferir eventual atualização do prazo.
- Fazer a submissão ao AVA no formato exigido. O PDF informa 03/11/2026 às 19h.
- Os integrantes devem revisar e praticar a defesa; a preparação dos arquivos não comprova domínio individual.

Não houve envio de mensagens ao professor nem submissão ao AVA.
