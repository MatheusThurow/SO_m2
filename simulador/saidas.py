import csv
import json
from pathlib import Path


def identificador(arquivo, c):
    return (f'{Path(arquivo).stem}_cpu{c.cpus}_{c.sched}_q{c.quantum if c.sched == "rr" else 0}'
            f'_{c.subst}_f{c.quadros}_c{c.custo_troca}')


def salvar(resultado, pasta):
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / 'resultado.json').write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
    for nome, linhas in [('gantt', resultado['gantt']), ('processos', resultado['por_processo']),
                          ('cpus', resultado['por_cpu'])]:
        with (pasta / (nome + '.csv')).open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(linhas[0]))
            w.writeheader()
            w.writerows(linhas)
    figura_gantt(resultado, pasta / 'gantt.png')


def figura_gantt(r, destino):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    fig, ax = plt.subplots(figsize=(15, 2 + r['config']['cpus'] * .7))
    for e in r['gantt']:
        nome = e['evento']
        cor = '#cbd5e1' if nome == 'OCIOSA' else '#334155' if nome == 'TROCA' else plt.cm.tab20(int(nome[1:]) % 20)
        ax.barh(e['cpu'], e['fim']-e['inicio'], left=e['inicio'], height=.65, color=cor, edgecolor='white', linewidth=.25)
        # Rotacionado: cabe também em intervalos de apenas uma unidade.
        if nome.startswith('P'):
            ax.text((e['inicio']+e['fim'])/2, e['cpu'], nome, ha='center', va='center',
                    rotation=90, fontsize=7, clip_on=True)
    ax.set(xlim=(0, 200), yticks=range(r['config']['cpus']),
           yticklabels=[f'CPU {i}' for i in range(r['config']['cpus'])], xlabel='Tempo simulado',
           title=r.get('id', 'Gantt - janela de 0 a 200'))
    ax.set_xticks(range(0, 201, 10))
    ax.grid(axis='x', alpha=.15)
    ax.legend(handles=[Patch(color='#334155', label='TROCA'), Patch(color='#cbd5e1', label='OCIOSA')],
              loc='upper right', fontsize=8)
    fig.tight_layout()
    fig.savefig(destino, dpi=180)
    plt.close(fig)


def resumo(r):
    print(json.dumps({k: v for k, v in r.items() if k not in ('gantt', 'por_processo')}, ensure_ascii=False, indent=2))
