"""Executa e verifica a matriz; nenhum resultado é estimado."""
import csv
from dataclasses import asdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import platform
import os
import subprocess
import sys
import time
from simulador.entrada import carregar
from simulador.modelos import Config
from simulador.motor import simular
from simulador.saidas import identificador, salvar


def main():
    destino=Path('resultados')
    destino.mkdir(exist_ok=True)
    registros=[]
    metadados=dict(python=sys.version, sistema=platform.platform(), processador=platform.processor(),
                   data_local=datetime.now().astimezone().isoformat(), entradas={}, comandos=[])
    metadados['cpus_logicas_host']=os.cpu_count()
    if os.name == 'nt':
        comando_hw='Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json -Compress'
        consulta=subprocess.run(['powershell','-NoProfile','-Command',comando_hw],capture_output=True,text=True)
        if consulta.returncode==0:
            metadados['hardware']=json.loads(consulta.stdout)
    for arquivo in sorted(Path('cenarios').glob('*.json')):
        dados=carregar(arquivo)
        metadados['entradas'][arquivo.name]=dict(sha256=hashlib.sha256(arquivo.read_bytes()).hexdigest(),
            processos=len(dados), cpu_total=sum(b.get('cpu',0) for p in dados for b in p['bursts']))
        assert len(dados)==1000
        for subst in ['lru','fifo']:
            variacoes=[('fcfs',10),('sjf',10)]+[('rr',q) for q in [2,5,10,20,50]] if subst=='lru' else [('fcfs',10)]
            for sched, q in variacoes:
                for cpus in [1,4]:
                    c=Config(cpus=cpus,sched=sched,quantum=q,subst=subst)
                    nome=identificador(arquivo,c)
                    inicio=time.perf_counter()
                    r=simular(dados,c)
                    motor_s=time.perf_counter()-inicio
                    # Segunda execução integral: igualdade de métricas, processos e Gantt.
                    assert r==simular(dados,c), nome
                    assert r['referencias_logicas']==40398
                    r.update(id=nome,cenario=arquivo.stem,duracao_motor_s=motor_s)
                    inicio_saida=time.perf_counter()
                    salvar(r,destino/nome)
                    r['duracao_saida_s']=time.perf_counter()-inicio_saida
                    (destino/nome/'resultado.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
                    registros.append(r)
                    comando=(f'python -m simulador --arquivo cenarios/{arquivo.name} --cpus {cpus} '
                             f'--sched {sched} --quantum {q} --subst {subst} --quadros 256 --custo-troca 1')
                    metadados['comandos'].append(comando)
                    print(f'{nome}: makespan={r["makespan"]}, faults={r["faults"]}, motor={motor_s:.3f}s',flush=True)
    for r in registros:
        c=r['config']
        equivalente=next(x for x in registros if x['cenario']==r['cenario'] and
            x['config']==dict(c,cpus=1))
        quatro=next(x for x in registros if x['cenario']==r['cenario'] and
            x['config']==dict(c,cpus=4))
        r['speedup']=equivalente['makespan']/quatro['makespan']
        r['eficiencia']=r['speedup']/4
        (destino/r['id']/'resultado.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    colunas=['id','cenario','cpus','sched','quantum','subst','quadros','custo_troca','makespan',
             'espera_media','espera_maxima','turnaround_medio','resposta_media','trocas','faults',
             'taxa_faults','speedup','eficiencia','duracao_motor_s','duracao_saida_s','substituicoes','retentativas']
    with (destino/'consolidado.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=colunas)
        w.writeheader()
        for r in registros:
            w.writerow({k:r['config'].get(k,r.get(k)) for k in colunas})
    (destino/'ambiente.json').write_text(json.dumps(metadados,ensure_ascii=False,indent=2),encoding='utf-8')
    (destino/'verificacao.json').write_text(
        json.dumps(dict(execucoes=len(registros), repeticoes_identicas=32, processos_por_execucao=1000,
                        referencias_por_execucao=40398, invariantes='OK'),indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
