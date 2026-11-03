from dataclasses import dataclass, field


@dataclass(frozen=True)
class Config:
    cpus: int = 1
    sched: str = 'fcfs'
    quantum: int = 10
    subst: str = 'lru'
    quadros: int = 256
    custo_troca: int = 1
    # Exclusivos da API de testes; a CLI sempre usa memória e latência 20.
    memoria: bool = True
    latencia_fault: int = 20

    def __post_init__(self):
        if self.cpus not in (1, 4):
            raise ValueError('CPUs deve ser 1 ou 4')
        if self.sched not in ('fcfs', 'sjf', 'rr') or self.subst not in ('fifo', 'lru'):
            raise ValueError('Política inválida')
        if self.quantum <= 0 or self.quadros <= 0 or self.latencia_fault <= 0 or self.custo_troca < 0:
            raise ValueError('Quantum, quadros e latência devem ser positivos; custo de troca >= 0')


@dataclass
class Processo:
    dado: dict
    burst: int = 0
    ref: int = 0
    estado: str = 'Novo'
    entrada: int = 0
    espera: int = 0
    resposta: int | None = None
    termino: int | None = None
    faults: int = 0
    bloqueio: int = 0
    troca: int = 0
    util: int = 0

    @property
    def pid(self):
        return self.dado['pid']

    @property
    def restante(self):
        return self.dado['bursts'][self.burst]['cpu'] - self.ref


@dataclass
class CPU:
    processo: Processo | None = None
    ultimo: int | None = None
    troca_restante: int = 0
    quantum: int = 0
    util: int = 0
    troca: int = 0
    ocioso: int = 0
    trocas: int = 0
    gantt: list = field(default_factory=list)
