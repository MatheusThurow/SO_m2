"""Gera análise, gráficos e PDF usando exclusivamente os resultados salvos."""
import csv
import json
import os
from pathlib import Path
from statistics import mean
from xml.sax.saxutils import escape

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

BASE=Path('resultados')
OUT=Path('output/pdf')
GRAF=Path('relatorio/graficos')


def nome(r):
    c=r['config']
    return ('A' if r['cenario']=='cenario_A_t0' else 'B')+f'-{c["cpus"]}CPU-'+c['sched'].upper()+(f'-Q{c["quantum"]}' if c['sched']=='rr' else '')+'-'+c['subst'].upper()


def main():
    rs=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(BASE.glob('*/resultado.json'))]
    assert len(rs)==32
    OUT.mkdir(parents=True,exist_ok=True)
    GRAF.mkdir(parents=True,exist_ok=True)
    rotulos=['FCFS','SJF','RR2','RR5','RR10','RR20','RR50']
    def selecionar(cenario,cpus,subst='lru'):
        selecao=[r for r in rs if r['cenario']==cenario and r['config']['cpus']==cpus and r['config']['subst']==subst]
        return sorted(selecao,key=lambda r: (0 if r['config']['sched']=='fcfs' else 1 if r['config']['sched']=='sjf' else 2+r['config']['quantum']/100))
    cenarios=['cenario_A_t0','cenario_B_espacadas']
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(1,2,figsize=(12,4.5))
    for ax,cenario in zip(axs,cenarios):
        for j,cpus in enumerate([1,4]):
            ax.bar([x+(j-.5)*.36 for x in range(7)], [r['espera_media'] for r in selecionar(cenario,cpus)],width=.35,label=f'{cpus} CPU(s)')
        ax.set(xticks=range(7),xticklabels=rotulos,yscale='log',ylabel='Espera média (escala log)',title=cenario)
        ax.legend()
    fig.tight_layout(); fig.savefig(GRAF/'espera.png',dpi=180); plt.close(fig)
    fig,axs=plt.subplots(1,3,figsize=(13,4.4))
    for ax,chave,titulo in zip(axs,['espera_media','resposta_media','trocas'],['Espera média','Resposta média','Trocas de contexto']):
        for cenario in cenarios:
            for cpus in [1,4]:
                linhas=[r for r in selecionar(cenario,cpus) if r['config']['sched']=='rr']
                ax.plot([r['config']['quantum'] for r in linhas],[r[chave] for r in linhas],marker='o',label=f'{cenario[8]} / {cpus}CPU')
        ax.set(xlabel='Quantum RR',title=titulo)
        ax.grid(alpha=.2)
    axs[-1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(GRAF/'quantum.png',dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,4))
    for cenario in cenarios:
        ax.plot(rotulos,[r['speedup'] for r in selecionar(cenario,4)],marker='o',label=cenario)
    ax.axhline(4,color='gray',linestyle='--',label='Referência ideal = 4')
    ax.set(ylabel='Makespan 1 CPU / makespan 4 CPUs',title='Speedup com LRU e 256 quadros')
    ax.legend(); fig.tight_layout(); fig.savefig(GRAF/'speedup.png',dpi=180); plt.close(fig)

    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CorpoM2',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=9))
    styles.add(ParagraphStyle(name='CelulaM2',fontName='Helvetica',fontSize=7,leading=9))
    story=[]; md=[]
    def titulo(t):
        story.append(Paragraph(escape(t),styles['Heading1'])); md.append('\n## '+t+'\n')
    def par(t):
        story.append(Paragraph(escape(t),styles['CorpoM2'])); md.append(t+'\n')
    def tabela(headers,linhas,widths=None):
        dados=[[Paragraph(escape(str(x)),styles['CelulaM2']) for x in row] for row in [headers]+linhas]
        tab=Table(dados,colWidths=widths,repeatRows=1,hAlign='LEFT')
        tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#16324f')),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#edf2f7')]),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('BOTTOMPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),
            ('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#16324f'))]))
        # Paragraphs carry their own color, so set the header explicitly.
        for cell in dados[0]: cell.style=ParagraphStyle(name='Cab',parent=styles['CelulaM2'],textColor=colors.white)
        story.append(tab); story.append(Spacer(1,10))
        md.append('| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+
                  '\n'.join('| '+' | '.join(str(x) for x in row)+' |' for row in linhas)+'\n')
    def figura(path,w=760):
        from PIL import Image as PILImage
        with PILImage.open(path) as im: h=w*im.height/im.width
        story.append(Image(str(path),width=w,height=h))
        md.append(f'![{path.stem}]({Path(os.path.relpath(path,"relatorio")).as_posix()})\n')
    def quebra(): story.append(PageBreak())
    def f(x): return f'{x:.2f}' if isinstance(x,float) else str(x)

    titulo('Simulador de escalonamento multiprocessado com paginação sob demanda')
    par('Sistemas Operacionais - Trabalho M2 | 03/11/2026')
    par('Equipe: Matheus Thurow, Rodrigo Nicola e Eduardo Bez.')
    par('Implementação em Python; 32 configurações executadas e repetidas integralmente, com resultados idênticos. Cada execução concluiu os 1.000 processos e consumiu exatamente 40.398 unidades úteis de CPU.')
    titulo('Modelo e estruturas de dados')
    par('O motor avança em unidades inteiras, com CPUs simuladas e uma fila global. FCFS/RR usam deque (inserção e retirada O(1)); SJF usa heap pelo burst restante e sequência de entrada (O(log P)). Eventos usam heap por instante e pid. Cada processo mantém o índice de burst e referência, estado e acumuladores de tempo. Nenhuma política consulta o rótulo de classe.')
    par('A memória usa dicionário pelo par (pid, página), com ordem de carga, último acesso e proteção. FIFO/LRU buscam o mínimo entre páginas não protegidas (O(F), com F quadros). Acertos são O(1); liberar um processo percorre os quadros. O motor custa O(C) por tick, além dos eventos e substituições; o log opcional custa mais por registrar os conjuntos completos.')
    par('No instante t, concluem-se os bursts da unidade anterior, liberando páginas dos terminados. Entram chegadas e retornos juntos por pid; depois são tratadas preempções por índice de CPU e os despachos. As CPUs são atendidas por índice: cada uma resolve despacho e acesso antes da próxima; faults não consomem tempo e permitem outro despacho no mesmo instante. Empates de acesso são ordenados pelo índice da CPU.')
    par('A página só é carregada no retorno do fault, após 20 unidades. Retornos no mesmo instante são resolvidos por pid. Sem vítima, tenta-se novamente após 20 unidades sem somar novo fault. A proteção dura até o primeiro acesso efetivo. FIFO e LRU usam sequências totais de operações para desempatar; uma carga protegida recebe a sequência de carga como valor inicial de recência.')
    par('O contexto da CPU é identificado pelo último contexto instalado no despacho, inclusive quando o acesso seguinte produz fault. O primeiro despacho cobra troca; um retorno ao mesmo contexto sem outro despacho não cobra. Com custo zero, nenhuma ocorrência é contada como custo cobrado. Resposta e espera encerram-se no despacho, antes da troca.')
    quebra()
    titulo('Validação e reprodução')
    par('Os testes automatizados reproduzem o exemplo 7.1 (makespan 13, útil 10, troca 3, espera 4,67 e turnaround 9), o 7.2 (fault de teste = 5, makespan 13, cinco faults, esperas zero) e o 7.3 (esperas médias 3,67 FCFS e 2,33 SJF). O exemplo 5.5 termina em 441, com quatro faults. A latência da CLI de produção permanece fixa em 20.')
    par('Também são testados RR sem concorrentes, chegada no quantum, SJF não preemptivo e empate, FIFO/LRU, quadros protegidos, retentativa sem fault extra e quatro CPUs simultâneas. Asserções em toda execução verificam: útil + troca + ocioso = makespan por CPU; turnaround = espera + útil + troca + bloqueio por processo; todas as referências consumidas e memória liberada ao terminar.')
    par('Comandos: python -m unittest discover -s tests -v; python experimentos.py; python gerar_relatorio.py. Cada diretório em resultados contém resultado.json, processos.csv, cpus.csv, gantt.csv e gantt.png. O consolidado.csv resume a matriz; ambiente.json contém hashes SHA-256, interpretador e comandos exatos. Tempos reais não são tempos simulados.')
    ambiente=json.loads((BASE/'ambiente.json').read_text(encoding='utf-8'))
    par(f'Ambiente medido: {ambiente["sistema"]}; Python {ambiente["python"].split()[0]}; {ambiente["processador"]}. Hardware registrado: {ambiente.get("hardware", "consultar ambiente.json")}. As CPUs 1/4 são simuladas sequencialmente, sem paralelismo real.')
    par(f'Tempo real do motor: mínimo {min(r["duracao_motor_s"] for r in rs):.3f}s; máximo {max(r["duracao_motor_s"] for r in rs):.3f}s. Motor + saída: máximo {max(r["duracao_motor_s"]+r["duracao_saida_s"] for r in rs):.3f}s. A medição do motor inclui validação e cálculo de métricas, exclui leitura do arquivo, figuras e a repetição de verificação. Todas as configurações ficaram abaixo de um minuto nesta máquina.')
    par('Matriz: FCFS, SJF e RR com Q=2,5,10,20,50; dois cenários e duas quantidades de CPUs; LRU/256 quadros/troca 1. Mais quatro casos FCFS/FIFO. O PDF lista Q=2,10,50, mas menciona cinco quantums na contagem; Q=5 e 20 ampliam a cobertura por decisão de implementação.')
    par('Taxa de faults = faults / 40.398 referências lógicas. Retentativas por falta de vítima não aumentam o numerador. Speedup = makespan 1 CPU / makespan 4 CPUs equivalentes; eficiência = speedup / 4. Percentuais por CPU incluem o intervalo desde t=0, inclusive antes da primeira chegada.')
    for cenario in cenarios:
        quebra(); titulo('Resultados - '+cenario)
        linhas=[r for r in rs if r['cenario']==cenario]
        par('Valores de tempo em unidades simuladas. Identificação: cenário-CPUs-política[-quantum]-memória. Todos os casos usam 256 quadros e custo de troca 1. Speedup e eficiência indicam o par 1/4 CPUs da mesma configuração, repetidos nas duas linhas.')
        headers=['Execução','Fim','Espera média','Espera máx.','Turn. médio','Resp. média','Trocas','Faults','Taxa %','Speedup','Efic. %']
        tabela(headers,[[nome(r)]+[f(r[k]) for k in ['makespan','espera_media','espera_maxima','turnaround_medio','resposta_media','trocas','faults']]+[f(100*r['taxa_faults']),f(r['speedup']),f(100*r['eficiencia'])] for r in linhas], [154]+[60]*10)
    quebra(); titulo('Espera e efeito do quantum')
    figura(GRAF/'espera.png',720)
    par('A escala logarítmica permite comparar os cenários; use os valores absolutos das tabelas para quantificar as diferenças. Os gráficos mostram apenas a base LRU.')
    quebra(); titulo('Efeito do quantum no Round Robin')
    figura(GRAF/'quantum.png',720)
    quebra(); titulo('Speedup e evidências')
    figura(GRAF/'speedup.png',620)
    for cenario in cenarios:
        fc=selecionar(cenario,4)[0]; sj=selecionar(cenario,4)[1]
        par(f'{nome(fc)} versus {nome(sj)}: espera média {fc["espera_media"]:.2f} versus {sj["espera_media"]:.2f}; makespan {fc["makespan"]} versus {sj["makespan"]}; faults {fc["faults"]} versus {sj["faults"]}. A mudança conjunta de fila e referências impede atribuir a diferença apenas à escolha do menor burst. O comportamento é compatível com a redução de atrasos causados por bursts longos no FCFS, sem isolar causalmente o efeito comboio.')
        rr=[r for r in selecionar(cenario,4) if r['config']['sched']=='rr']
        a,b=rr[0],rr[-1]
        par(f'{nome(a)} versus {nome(b)}: Q=2/50 produz resposta média {a["resposta_media"]:.2f}/{b["resposta_media"]:.2f}, espera média {a["espera_media"]:.2f}/{b["espera_media"]:.2f} e {a["trocas"]}/{b["trocas"]} trocas. Esses dados mostram o compromisso observado entre atendimento inicial e custo, que também é afetado pelos faults.')
    par('O cenário B impõe chegadas até 10.604; CPUs extras não antecipam chegadas. Portanto, o speedup inclui limites de chegada, bloqueios e diferenças de memória, além da capacidade de CPU. Quatro é uma referência ideal, não uma garantia para este modelo integrado.')
    maior=max((r for r in rs if r['config']['cpus']==4),key=lambda r:r['speedup'])
    if maior['speedup']>4:
        equivalente=next(r for r in rs if r['cenario']==maior['cenario'] and r['config']==dict(maior['config'],cpus=1))
        par(f'{nome(maior)} apresenta speedup {maior["speedup"]:.2f} e eficiência {100*maior["eficiencia"]:.2f}%, acima da referência linear. As execuções de 1/4 CPUs têm {equivalente["faults"]}/{maior["faults"]} faults: a ordem de execução altera a pressão na memória. O ganho medido abrange essa interação e não representa paralelização de uma sequência fixa de instruções e faltas.')
    quebra(); titulo('Leitura dos Gantts de 1 e 4 CPUs')
    for exemplo in [selecionar(cenarios[0],1)[0],selecionar(cenarios[1],4)[0]]:
        por_tipo={tipo:sum(e['fim']-e['inicio'] for e in exemplo['gantt']
                      if (e['evento'].startswith('P') if tipo=='útil' else e['evento']==tipo))
                  for tipo in ['útil','TROCA','OCIOSA']}
        par(f'{nome(exemplo)}, janela [0,200): soma entre CPUs de {por_tipo["útil"]} unidades úteis, {por_tipo["TROCA"]} de troca e {por_tipo["OCIOSA"]} ociosas. São parcelas da janela, distintas dos totais da execução no apêndice.')
        figura(BASE/exemplo['id']/'gantt.png',600)
    par('No cenário A/FCFS, a fila inicial de 1.000 processos faz a janela inicial ser dominada por instalação de contextos e primeiras faltas: mesmo ocupada, a CPU ainda não produz trabalho útil. No cenário B com 4 CPUs, chegadas espaçadas permitem retornos atendidos mais cedo; aparecem intervalos úteis e ociosos. O Gantt evidencia por que utilização que inclui troca não equivale a produtividade.')
    quebra(); titulo('Comparação de memória e justiça')
    pares=[]
    for cenario in cenarios:
        for cpus in [1,4]:
            l=selecionar(cenario,cpus)[0]; fi=selecionar(cenario,cpus,'fifo')[0]
            pares.append([nome(fi),str(fi['faults']),str(l['faults']),str(fi['makespan']),str(l['makespan']),f(fi['espera_media']),f(l['espera_media'])])
            par(f'{nome(fi)} comparado a {nome(l)}: diferença FIFO - LRU de {fi["faults"]-l["faults"]:+d} faults e {fi["makespan"]-l["makespan"]:+d} unidades de makespan. A comparação preserva cenário, escalonador, CPUs, quadros e custo.')
    tabela(['FIFO (par com LRU)','Faults FIFO','Faults LRU','Fim FIFO','Fim LRU','Espera FIFO','Espera LRU'],pares,[220]+[88]*6)
    par('Faults frequentes, isoladamente, não provam thrashing: faltas compulsórias e localidade também pesam. São registrados substituições e retentativas, mas não uma série temporal de conjunto de trabalho. A análise não declara thrashing sem essa evidência adicional.')
    par('Todos os processos terminaram nas cargas finitas. Isso exclui inanição observada nestas execuções, mas não prova ausência de starvation para chegadas ilimitadas no SJF. A tabela seguinte separa classes somente na análise; espera é o tempo acumulado na fila, não tempo total de bloqueio.')
    for cenario in cenarios:
        quebra(); titulo('Justiça por classe - '+cenario)
        justica=[]
        for r in rs:
            if r['cenario']!=cenario: continue
            grupos={classe:[p for p in r['por_processo'] if p['classe']==classe] for classe in ['curto','longo']}
            justica.append([nome(r)]+[f(fun(p['espera'] for p in grupos[c])) for c in ['curto','longo'] for fun in [mean,max]])
        tabela(['Execução','Média curtos (952)','Máx. curtos','Média longos (48)','Máx. longos'],justica,[270,120,120,120,120])
        fc,sj=selecionar(cenario,4)[:2]
        def espera_classe(r,classe):
            return mean(p['espera'] for p in r['por_processo'] if p['classe']==classe)
        par(f'Com 4 CPUs/LRU, {nome(fc)} e {nome(sj)} produzem espera média dos curtos de {espera_classe(fc,"curto"):.2f}/{espera_classe(sj,"curto"):.2f}, e dos longos de {espera_classe(fc,"longo"):.2f}/{espera_classe(sj,"longo"):.2f}. A separação mostra que a média global não descreve igualmente as duas classes. A espera acumulada não é normalizada pela demanda de CPU; processos longos têm mais oportunidades de retornar à fila, portanto valores maiores não demonstram, por si só, tratamento injusto por despacho.')
    quebra(); titulo('Limitações e entrega')
    par('SJF conhece o burst futuro; um SO real o estimaria. Não há fila de disco, custo de migração, cache, TLB, bytes, endereços ou paralelismo físico. Latências de E/S e fault são independentes e constantes conforme o modelo. A ordem de operações simultâneas e a instalação de contexto são convenções determinísticas documentadas, relevantes à reprodução.')
    par('Os critérios complementares do AVA não foram consultados: não há acesso autenticado disponibilizado. O prazo do PDF é 03/11/2026 às 19h. Repositório de destino informado pela equipe: https://github.com/MatheusThurow/SO_m2. O estado da publicação está registrado em STATUS.md. O envio ao AVA continua pendente; publicação no GitHub não constitui submissão ao AVA.')
    par('Defesa: demonstrar a CLI com --cpus 1/4, --sched fcfs/sjf/rr, --quantum 2/50, --quadros 1/256 e --subst fifo/lru; usar o exemplo pequeno com --log; explicar a proteção no retorno, consumo de referências, fila global, resposta antes da troca e identidades de conservação de tempo. Consulte DEFESA.md para o roteiro completo.')
    titulo('Apêndice - Gantts e tempos por CPU')
    par('Cada página seguinte identifica uma configuração e mostra a janela 0 a 200. Pn identifica o processo; TROCA e OCIOSA usam a legenda. Os CSVs preservam exatamente cada intervalo e permitem ampliar qualquer trecho. A tabela abaixo de cada figura cobre toda a execução, e não apenas a janela do gráfico.')
    for r in rs:
        quebra(); titulo(nome(r))
        par(r['id'])
        figura(BASE/r['id']/'gantt.png',760)
        tabela(['CPU','Útil','Útil %','Troca','Troca %','Ocioso','Ocioso %','Trocas','Utilização %'],
            [[c['cpu'],c['util'],f(c['util_pct']),c['troca'],f(c['troca_pct']),c['ocioso'],f(c['ocioso_pct']),c['trocas'],f(c['utilizacao']*100)] for c in r['por_cpu']], [50]+[88]*8)
        par(f'Makespan {r["makespan"]}; espera média {r["espera_media"]:.2f}; resposta média {r["resposta_media"]:.2f}; faults {r["faults"]}; taxa {100*r["taxa_faults"]:.2f}%.')
    def rodape(canvas,doc):
        canvas.setFont('Helvetica',8)
        canvas.setFillColor(colors.HexColor('#526579'))
        canvas.drawString(36,20,'SO M2 | Thurow, Nicola e Bez | Resultados de simulação')
        canvas.drawRightString(806,20,str(doc.page))
    doc=SimpleDocTemplate(str(OUT/'relatorio_m2.pdf'),pagesize=landscape(A4),rightMargin=36,leftMargin=36,topMargin=30,bottomMargin=36,
                          title='Trabalho M2 - Sistemas Operacionais',author='Matheus Thurow; Rodrigo Nicola; Eduardo Bez')
    doc.build(story,onFirstPage=rodape,onLaterPages=rodape)
    Path('relatorio/relatorio.md').write_text('\n'.join(md),encoding='utf-8')
    print(OUT/'relatorio_m2.pdf')


if __name__=='__main__': main()
