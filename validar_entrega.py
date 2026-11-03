"""Verificação dos artefatos produzidos; não altera a simulação."""
import csv
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader


def main():
    resultados=Path('resultados')
    ambiente=json.loads((resultados/'ambiente.json').read_text(encoding='utf-8'))
    for nome,info in ambiente['entradas'].items():
        assert hashlib.sha256((Path('cenarios')/nome).read_bytes()).hexdigest()==info['sha256']
    registros=list(csv.DictReader((resultados/'consolidado.csv').open(encoding='utf-8')))
    assert len(registros)==32 and len({r['id'] for r in registros})==32
    pdf=PdfReader('output/pdf/relatorio_m2.pdf')
    texto='\n'.join(p.extract_text() for p in pdf.pages)
    for r in registros:
        pasta=resultados/r['id']
        d=json.loads((pasta/'resultado.json').read_text(encoding='utf-8'))
        assert d['processos']==1000 and d['referencias_logicas']==40398
        assert sum(p['util'] for p in d['por_processo'])==40398
        for c in d['por_cpu']:
            assert c['util']+c['troca']+c['ocioso']==d['makespan']
        for cpu in range(d['config']['cpus']):
            intervalos=[e for e in d['gantt'] if e['cpu']==cpu]
            assert intervalos[0]['inicio']==0 and intervalos[-1]['fim']==200
            assert all(a['fim']==b['inicio'] for a,b in zip(intervalos,intervalos[1:]))
        assert float(r['makespan'])==d['makespan']
        assert r['id'] in texto
        assert len(list(csv.DictReader((pasta/'cpus.csv').open(encoding='utf-8'))))==d['config']['cpus']
        for arquivo in ['resultado.json','processos.csv','cpus.csv','gantt.csv','gantt.png']:
            assert (pasta/arquivo).stat().st_size>0
    assert len(list(Path('relatorio/graficos').glob('*.png')))==3
    saida=dict(configuracoes=32,processos_verificados=32000,gantts=32,paginas_pdf=len(pdf.pages),
               hashes='OK',metricas='OK',gantt_contiguo_0_200='OK',artefatos='OK')
    Path('validacao/entrega.json').write_text(json.dumps(saida,indent=2),encoding='utf-8')
    print(json.dumps(saida,indent=2))


if __name__=='__main__': main()
