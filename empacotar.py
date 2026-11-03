"""Cria um ZIP portátil, excluindo metadados Git e arquivos temporários."""
from pathlib import Path
import zipfile


def main():
    raiz=Path(__file__).resolve().parent
    destino=raiz/'entrega_m2.zip'
    ignorar={'.git','.venv','__pycache__','tmp','demonstracao'}
    with zipfile.ZipFile(destino,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(raiz.rglob('*')):
            rel=p.relative_to(raiz)
            if p.is_file() and p!=destino and not any(x in ignorar for x in rel.parts):
                z.write(p,rel.as_posix())
    with zipfile.ZipFile(destino) as z:
        assert z.testzip() is None
    print(destino)


if __name__=='__main__': main()
