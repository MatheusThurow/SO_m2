import argparse
from contextlib import nullcontext
from pathlib import Path
import time
from .entrada import carregar
from .modelos import Config
from .motor import simular
from .saidas import identificador, salvar, resumo


def main():
    p = argparse.ArgumentParser(description='Escalonamento multiprocessado com paginação sob demanda')
    p.add_argument('--arquivo', required=True)
    p.add_argument('--cpus', type=int, choices=(1, 4), default=1)
    p.add_argument('--sched', choices=('fcfs', 'sjf', 'rr'), default='fcfs')
    p.add_argument('--quantum', type=int, default=10)
    p.add_argument('--subst', choices=('fifo', 'lru'), default='lru')
    p.add_argument('--quadros', type=int, default=256)
    p.add_argument('--custo-troca', type=int, default=1)
    p.add_argument('--log', action='store_true')
    p.add_argument('--saida', default='resultados')
    a = p.parse_args()
    try:
        c = Config(a.cpus, a.sched, a.quantum, a.subst, a.quadros, a.custo_troca)
        dados = carregar(a.arquivo)
    except (ValueError, OSError) as e:
        p.error(str(e))
    pasta = Path(a.saida) / identificador(a.arquivo, c)
    pasta.mkdir(parents=True, exist_ok=True)
    inicio = time.perf_counter()
    with (pasta / 'estados.jsonl').open('w', encoding='utf-8') if a.log else nullcontext(None) as log:
        r = simular(dados, c, log)
    r.update(id=pasta.name, duracao_motor_s=time.perf_counter()-inicio)
    salvar(r, pasta)
    resumo(r)


if __name__ == '__main__':
    main()
