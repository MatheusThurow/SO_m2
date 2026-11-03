from dataclasses import asdict
import heapq
import json
from statistics import mean
from .modelos import CPU, Config, Processo
from .entrada import validar
from .escalonadores import Prontos
from .memoria import Memoria


def simular(dados, config=Config(), log=None):
    validar(dados)
    processos = {d['pid']: Processo(d) for d in dados}
    cpus = [CPU() for _ in range(config.cpus)]
    prontos = Prontos(config.sched)
    memoria = Memoria(config.quadros, config.subst)
    eventos = [(p.dado['chegada'], p.pid, 'chegada', None) for p in processos.values()]
    heapq.heapify(eventos)
    bloqueados = {}
    t = terminados = 0

    def registrar(evento, p):
        if log is not None:
            log.write(json.dumps(dict(tempo=t, evento=evento, pid=p.pid,
                estado=p.estado, prontos=prontos.pids(),
                bloqueados=[dict(pid=pid, retorno=v[0], motivo=v[1])
                            for pid, v in sorted(bloqueados.items())],
                cpus=[dict(cpu=i, pid=c.processo.pid if c.processo else None,
                           troca_restante=c.troca_restante) for i, c in enumerate(cpus)],
                quadros_ocupados=len(memoria.paginas)), ensure_ascii=False) + '\n')

    def pronto(p, motivo):
        p.estado = 'Pronto'
        p.entrada = t
        prontos.inserir(p)
        registrar(motivo, p)

    def bloquear(p, duracao, motivo, chave=None):
        p.estado = 'Bloqueado'
        p.bloqueio += duracao
        bloqueados[p.pid] = (t + duracao, motivo)
        heapq.heappush(eventos, (t + duracao, p.pid, motivo, chave))
        registrar(motivo, p)

    def intervalo(c, evento):
        if t >= 200:
            return
        if c.gantt and c.gantt[-1][2] == evento and c.gantt[-1][1] == t:
            c.gantt[-1][1] = t + 1
        else:
            c.gantt.append([t, t + 1, evento])

    while terminados < len(processos):
        # Conclusões da unidade [t-1,t): liberam quadros antes dos retornos em t.
        for c in cpus:
            p = c.processo
            if p is not None and p.restante == 0:
                c.processo = None
                registrar('fim_burst', p)
                if p.burst + 1 == len(p.dado['bursts']):
                    p.estado = 'Terminado'
                    p.termino = t
                    terminados += 1
                    memoria.liberar(p.pid)
                    registrar('termino', p)
                else:
                    duracao = p.dado['bursts'][p.burst + 1]['es']
                    p.burst += 2
                    p.ref = 0
                    bloquear(p, duracao, 'es')
        # Heap ordenado por (instante, pid): chegadas e retornos juntos.
        while eventos and eventos[0][0] == t:
            _, pid, motivo, chave = heapq.heappop(eventos)
            p = processos[pid]
            bloqueados.pop(pid, None)
            if motivo == 'fault' and not memoria.carregar(chave):
                bloquear(p, config.latencia_fault, 'fault', chave)
                continue
            pronto(p, 'chegada' if motivo == 'chegada' else 'retorno_' + motivo)
        # Preempções por índice de CPU, após chegadas/retornos.
        for c in cpus:
            if c.processo and config.sched == 'rr' and c.quantum == 0:
                if prontos:
                    p = c.processo
                    c.processo = None
                    pronto(p, 'preempcao')
                else:
                    c.quantum = config.quantum
        if terminados == len(processos):
            break
        # Faults não consomem tempo: uma CPU pode despachar vários processos em t.
        # Cada CPU resolve seu despacho/acesso antes de avançar à próxima CPU.
        for c in cpus:
            while True:
                if c.processo is None:
                    if not prontos:
                        c.ocioso += 1
                        intervalo(c, 'OCIOSA')
                        break
                    p = prontos.retirar()
                    p.espera += t - p.entrada
                    if p.resposta is None:
                        p.resposta = t - p.dado['chegada']
                    p.estado = 'Executando'
                    c.processo = p
                    c.quantum = config.quantum
                    if c.ultimo != p.pid:
                        c.troca_restante = config.custo_troca
                        if config.custo_troca:
                            c.trocas += 1
                        # Contexto instalado, inclusive se o próximo acesso der fault.
                        c.ultimo = p.pid
                    registrar('despacho', p)
                p = c.processo
                if c.troca_restante:
                    c.troca_restante -= 1
                    c.troca += 1
                    p.troca += 1
                    intervalo(c, 'TROCA')
                    break
                chave = (p.pid, p.dado['bursts'][p.burst]['refs'][p.ref])
                if config.memoria and not memoria.acessar(chave):
                    p.faults += 1
                    c.processo = None
                    bloquear(p, config.latencia_fault, 'fault', chave)
                    continue
                p.ref += 1
                p.util += 1
                c.util += 1
                c.quantum -= 1
                intervalo(c, f'P{p.pid}')
                break
        t += 1

    por_processo = [dict(pid=p.pid, classe=p.dado['classe'], chegada=p.dado['chegada'],
        termino=p.termino, espera=p.espera, resposta=p.resposta,
        turnaround=p.termino - p.dado['chegada'], faults=p.faults,
        util=p.util, troca=p.troca, bloqueado=p.bloqueio) for p in processos.values()]
    for p in por_processo:
        assert p['turnaround'] == p['espera'] + p['util'] + p['troca'] + p['bloqueado'], p
    por_cpu = [dict(cpu=i, util=c.util, troca=c.troca, ocioso=c.ocioso, trocas=c.trocas,
        util_pct=100*c.util/t, troca_pct=100*c.troca/t, ocioso_pct=100*c.ocioso/t,
        utilizacao=(c.util+c.troca)/t) for i, c in enumerate(cpus)]
    assert all(c['util'] + c['troca'] + c['ocioso'] == t for c in por_cpu)
    total = sum(b.get('cpu', 0) for p in dados for b in p['bursts'])
    assert sum(c.util for c in cpus) == total
    assert not memoria.paginas and not bloqueados and not prontos
    faults = sum(p.faults for p in processos.values())
    resultado = dict(config=asdict(config), processos=len(processos), makespan=t,
        espera_media=mean(p.espera for p in processos.values()),
        espera_maxima=max(p.espera for p in processos.values()),
        turnaround_medio=mean(p['turnaround'] for p in por_processo),
        resposta_media=mean(p.resposta for p in processos.values()),
        trocas=sum(c.trocas for c in cpus), faults=faults, taxa_faults=faults/total,
        referencias_logicas=total, pico_quadros=memoria.pico,
        substituicoes=memoria.substituicoes, retentativas=memoria.retentativas,
        por_cpu=por_cpu, por_processo=por_processo,
        gantt=[dict(cpu=i, inicio=a, fim=b, evento=e)
               for i,c in enumerate(cpus) for a,b,e in c.gantt])
    return resultado
