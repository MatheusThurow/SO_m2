import json
from pathlib import Path


def inteiro(valor, minimo=0):
    return type(valor) is int and valor >= minimo


def validar(dados):
    if not isinstance(dados, list) or not dados:
        raise ValueError('Entrada deve ser uma lista não vazia de processos')
    vistos = set()
    for p in dados:
        if not isinstance(p, dict) or not inteiro(p.get('pid')):
            raise ValueError('Processo deve ter pid inteiro não negativo')
        pid = p['pid']
        if pid in vistos:
            raise ValueError(f'pid duplicado: {pid}')
        vistos.add(pid)
        if not inteiro(p.get('chegada')) or not inteiro(p.get('paginas'), 1):
            raise ValueError(f'P{pid}: chegada ou páginas inválidas')
        if p.get('classe') not in ('curto', 'longo'):
            raise ValueError(f'P{pid}: classe deve ser curto ou longo')
        bursts = p.get('bursts')
        if not isinstance(bursts, list) or not bursts or len(bursts) % 2 != 1:
            raise ValueError(f'P{pid}: bursts devem começar e terminar em CPU')
        for i, b in enumerate(bursts):
            if not isinstance(b, dict):
                raise ValueError(f'P{pid}: burst inválido')
            if i % 2:
                if set(b) != {'es'} or not inteiro(b['es'], 1):
                    raise ValueError(f'P{pid}: E/S deve ser inteira positiva')
            else:
                refs = b.get('refs')
                if (set(b) != {'cpu', 'refs'} or not inteiro(b['cpu'], 1)
                        or not isinstance(refs, list) or len(refs) != b['cpu']
                        or any(not inteiro(r) or r >= p['paginas'] for r in refs)):
                    raise ValueError(f'P{pid}: CPU ou referências inválidas')
    return dados


def carregar(arquivo):
    return validar(json.loads(Path(arquivo).read_text(encoding='utf-8-sig')))
