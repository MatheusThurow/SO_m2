from collections import deque
import heapq


class Prontos:
    def __init__(self, politica):
        self.sjf = politica == 'sjf'
        self.fila = [] if self.sjf else deque()
        self.ordem = 0

    def inserir(self, p):
        self.ordem += 1
        if self.sjf:
            heapq.heappush(self.fila, (p.restante, self.ordem, p.pid, p))
        else:
            self.fila.append(p)

    def retirar(self):
        return heapq.heappop(self.fila)[3] if self.sjf else self.fila.popleft()

    def pids(self):
        return [e[2] for e in sorted(self.fila)] if self.sjf else [p.pid for p in self.fila]

    def __bool__(self):
        return bool(self.fila)
