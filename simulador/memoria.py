class Memoria:
    """Ordenação total por sequência de operações; páginas protegidas não são vítimas."""

    def __init__(self, quadros, politica):
        self.capacidade = quadros
        self.politica = politica
        self.paginas = {}  # identidade -> [ordem de carga, último acesso, protegida]
        self.sequencia = 0
        self.pico = 0
        self.substituicoes = 0
        self.retentativas = 0

    def carregar(self, chave):
        if chave in self.paginas:
            raise AssertionError('Página de fault já residente')
        if len(self.paginas) == self.capacidade:
            elegiveis = [k for k, v in self.paginas.items() if not v[2]]
            if not elegiveis:
                self.retentativas += 1
                return False
            indice = 0 if self.politica == 'fifo' else 1
            vitima = min(elegiveis, key=lambda k: (self.paginas[k][indice], k))
            del self.paginas[vitima]
            self.substituicoes += 1
        self.sequencia += 1
        self.paginas[chave] = [self.sequencia, self.sequencia, True]
        self.pico = max(self.pico, len(self.paginas))
        return True

    def acessar(self, chave):
        if chave not in self.paginas:
            return False
        self.sequencia += 1
        self.paginas[chave][1:] = [self.sequencia, False]
        return True

    def liberar(self, pid):
        for chave in [k for k in self.paginas if k[0] == pid]:
            del self.paginas[chave]
