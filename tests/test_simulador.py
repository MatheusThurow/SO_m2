import io
import json
import unittest
from dataclasses import replace
from simulador.entrada import validar, carregar
from simulador.memoria import Memoria
from simulador.modelos import Config
from simulador.motor import simular


def processo(pid, n, chegada=0, refs=None, bursts=None):
    refs = refs if refs is not None else [0]*n
    return dict(pid=pid, chegada=chegada, classe='curto', paginas=max(refs)+1,
                bursts=bursts or [dict(cpu=n, refs=refs)])


class ExemplosProfessor(unittest.TestCase):
    def test_71(self):
        r = simular([processo(1,5), processo(2,3), processo(3,2,2)], Config(memoria=False))
        self.assertEqual((r['makespan'], r['por_cpu'][0]['util'], r['trocas']), (13,10,3))
        self.assertAlmostEqual(r['espera_media'], 14/3)
        self.assertEqual(r['turnaround_medio'], 9)
        self.assertEqual([p['espera'] for p in r['por_processo']], [0,6,8])

    def test_72(self):
        r = simular([processo(1,2,refs=[0,1]), processo(2,2,1,[0,1]), processo(3,1,2)],
                    Config(custo_troca=0,latencia_fault=5))
        self.assertEqual(r['makespan'],13)
        self.assertEqual(r['faults'],5)
        self.assertEqual(r['espera_media'],0)
        self.assertEqual([p['turnaround'] for p in r['por_processo']], [12,12,6])

    def test_73(self):
        dados = [processo(1,4), processo(2,3), processo(3,2)]
        for sched, esperas in [('fcfs',[0,4,7]), ('sjf',[5,2,0])]:
            r = simular(dados, Config(sched=sched,custo_troca=0))
            self.assertEqual([p['espera'] for p in r['por_processo']], esperas)
            self.assertEqual(r['makespan'],29)

    def test_55(self):
        p = processo(17,4,342,[0,1,1,2], [dict(cpu=4,refs=[0,1,1,2]),dict(es=12),dict(cpu=3,refs=[2,3,3])])
        p['paginas']=4
        r=simular([p],Config(custo_troca=0))
        self.assertEqual((r['makespan'],r['faults'],r['turnaround_medio']), (441,4,99))


class Regras(unittest.TestCase):
    def test_rr_sem_concorrentes_e_retorno(self):
        p=processo(1,5,bursts=[dict(cpu=5,refs=[0]*5),dict(es=3),dict(cpu=2,refs=[0]*2)])
        r=simular([p],Config(sched='rr',quantum=1,memoria=False))
        self.assertEqual((r['trocas'],r['makespan']), (1,11))

    def test_rr_chegada_antes_preempcao(self):
        r=simular([processo(1,4),processo(2,1,2)], Config(sched='rr',quantum=2,custo_troca=0,memoria=False))
        self.assertEqual([(e['inicio'],e['evento']) for e in r['gantt']], [(0,'P1'),(2,'P2'),(3,'P1')])

    def test_sjf_nao_preemptivo_e_empate(self):
        r=simular([processo(1,5),processo(2,2,1),processo(3,2,1)],Config(sched='sjf',memoria=False,custo_troca=0))
        self.assertEqual([e['evento'] for e in r['gantt']], ['P1','P2','P3'])

    def test_protecao_retentativa_e_log(self):
        log=io.StringIO()
        r=simular([processo(1,1),processo(2,1)],Config(quadros=1,custo_troca=0),log)
        self.assertEqual((r['faults'],r['retentativas'],r['makespan']), (2,1,41))
        eventos=[json.loads(l) for l in log.getvalue().splitlines()]
        self.assertTrue(all('bloqueados' in e and 'cpus' in e for e in eventos))

    def test_fifo_lru(self):
        for politica, vitima in [('fifo',(1,0)), ('lru',(1,1))]:
            m=Memoria(2,politica)
            for chave in [(1,0),(1,1)]:
                self.assertTrue(m.carregar(chave))
                m.acessar(chave)
            m.acessar((1,0))
            m.carregar((2,0))
            self.assertNotIn(vitima,m.paginas)
            self.assertTrue(m.paginas[(2,0)][2])

    def test_quatro_cpus_e_repetibilidade(self):
        dados=[processo(i,2) for i in range(1,9)]
        c=Config(cpus=4,memoria=False)
        r=simular(dados,c)
        self.assertEqual(r,simular(dados,c))
        self.assertEqual(r['makespan'],6)
        self.assertEqual([e['evento'] for e in r['gantt'] if e['inicio']==1],['P1','P2','P3','P4'])

    def test_conservacao_combinacoes(self):
        dados=[processo(i,3,i%3,[0,1,0]) for i in range(1,9)]
        for cpus in [1,4]:
            for sched in ['fcfs','sjf','rr']:
                for subst in ['fifo','lru']:
                    r=simular(dados,Config(cpus=cpus,sched=sched,subst=subst,quadros=1,quantum=1))
                    self.assertEqual(sum(p['util'] for p in r['por_processo']),24)
                    self.assertEqual(r['pico_quadros'],1)

    def test_entrada_invalida(self):
        for dados in [[],[processo(1,1),processo(1,1)], [dict(pid=True)], [processo(1,2,refs=[-1,0])]]:
            with self.assertRaises(ValueError): validar(dados)
        for kwargs in [dict(cpus=2),dict(quadros=0),dict(quantum=0),dict(custo_troca=-1)]:
            with self.assertRaises(ValueError): Config(**kwargs)


if __name__=='__main__':
    unittest.main()
