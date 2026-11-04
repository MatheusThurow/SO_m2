"""Gera análise, gráficos e PDF usando exclusivamente os resultados salvos."""
import csv
import json
import os
from io import BytesIO
from pathlib import Path
from statistics import mean
from xml.sax.saxutils import escape

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
from pypdf import PdfReader, PdfWriter
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
    for nome_fonte,peso in [('Arial','normal'),('Arial-Bold','bold')]:
        caminho=font_manager.findfont(font_manager.FontProperties(family='Arial',weight=peso),fallback_to_default=False)
        pdfmetrics.registerFont(TTFont(nome_fonte,caminho))
    pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold')
    rs=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(BASE.glob('*/resultado.json'))]
    assert len(rs)==32
    OUT.mkdir(parents=True,exist_ok=True)
    GRAF.mkdir(parents=True,exist_ok=True)
    rotulos=['FCFS','SJF','RR2','RR5','RR10','RR20','RR50']
    def selecionar(cenario,cpus,subst='lru'):
        selecao=[r for r in rs if r['cenario']==cenario and r['config']['cpus']==cpus and r['config']['subst']==subst]
        return sorted(selecao,key=lambda r: (0 if r['config']['sched']=='fcfs' else 1 if r['config']['sched']=='sjf' else 2+r['config']['quantum']/100))
    cenarios=['cenario_A_t0','cenario_B_espacadas']
    plt.rcParams.update({'font.family':'Arial','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    # Figuras do relatório: mesmos dados de Gantt, com a fonte solicitada.
    from simulador.saidas import figura_gantt
    gantts_relatorio=Path('relatorio/gantts')
    gantts_relatorio.mkdir(exist_ok=True)
    for r in rs:
        figura_gantt(r,gantts_relatorio/(r['id']+'.png'))
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
    styles['Heading1'].fontName='Arial-Bold'
    styles['Heading1'].fontSize=15
    styles['Heading1'].leading=18
    styles.add(ParagraphStyle(name='CorpoM2',fontName='Arial',fontSize=11,leading=14,spaceAfter=8))
    styles.add(ParagraphStyle(name='CelulaM2',fontName='Arial',fontSize=8,leading=10))
    story=[]; md=[]
    def titulo(t):
        story.append(Paragraph(escape(t),styles['Heading1'])); md.append('\n## '+t+'\n')
    def par(t):
        story.append(Paragraph(escape(t),styles['CorpoM2'])); md.append(t+'\n')
    def tabela(headers,linhas,widths=None):
        dados=[[Paragraph(escape(str(x)),styles['CelulaM2']) for x in row] for row in [headers]+linhas]
        tab=Table(dados,colWidths=widths,repeatRows=1,hAlign='LEFT')
        tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8e8e8')),
            ('TEXTCOLOR',(0,0),(-1,0),colors.black),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('BOTTOMPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),
            ('LINEBELOW',(0,0),(-1,0),.5,colors.black),('LINEBELOW',(0,-1),(-1,-1),.5,colors.black)]))
        # Paragraphs carry their own color, so set the header explicitly.
        for cell in dados[0]: cell.style=ParagraphStyle(name='Cab',parent=styles['CelulaM2'],fontName='Arial-Bold',textColor=colors.black)
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
    par('Sistemas Operacionais - Trabalho M2 - 03/11/2026')
    par('Matheus Thurow, Rodrigo Nicola e Eduardo Bez')
    titulo('1. Introdução')
    par('Este trabalho apresenta um simulador em Python que reúne escalonamento de CPU e paginação sob demanda. Foram comparados FCFS, SJF e Round Robin em máquinas simuladas com 1 e 4 CPUs, usando as políticas de memória FIFO e LRU. O objetivo foi observar como essas escolhas afetam os tempos dos processos, as faltas de página e o uso das CPUs.')
    par('Foram usados dois cenários com os mesmos 1.000 processos: no A, todos chegam no instante zero; no B, as chegadas são distribuídas até o instante 10.604. São 952 processos curtos e 48 longos. Cada cenário exige 40.398 unidades de CPU, intercaladas com etapas de E/S.')
    titulo('2. Funcionamento do simulador')
    par('O motor avança em unidades inteiras, com CPUs simuladas e uma fila global. FCFS/RR usam deque (inserção e retirada O(1)); SJF usa heap pelo burst restante e sequência de entrada (O(log P)). Eventos usam heap por instante e pid. Cada processo mantém o índice de burst e referência, estado e acumuladores de tempo. Nenhuma política consulta o rótulo de classe.')
    par('A memória usa dicionário pelo par (pid, página), com ordem de carga, último acesso e proteção. FIFO/LRU buscam o mínimo entre páginas não protegidas (O(F), com F quadros). Acertos são O(1); liberar um processo percorre os quadros. O motor custa O(C) por tick, além dos eventos e substituições; o log opcional custa mais por registrar os conjuntos completos.')
    par('No instante t, concluem-se os bursts da unidade anterior, liberando páginas dos terminados. Entram chegadas e retornos juntos por pid; depois são tratadas preempções por índice de CPU e os despachos. As CPUs são atendidas por índice: cada uma resolve despacho e acesso antes da próxima; faults não consomem tempo e permitem outro despacho no mesmo instante. Empates de acesso são ordenados pelo índice da CPU.')
    par('A página só é carregada no retorno do fault, após 20 unidades. Retornos no mesmo instante são resolvidos por pid. Sem vítima, tenta-se novamente após 20 unidades sem somar novo fault. A proteção dura até o primeiro acesso efetivo. FIFO e LRU usam sequências totais de operações para desempatar; uma carga protegida recebe a sequência de carga como valor inicial de recência.')
    par('O contexto da CPU é identificado pelo último contexto instalado no despacho, inclusive quando o acesso seguinte produz fault. O primeiro despacho cobra troca; um retorno ao mesmo contexto sem outro despacho não cobra. Com custo zero, nenhuma ocorrência é contada como custo cobrado. Resposta e espera encerram-se no despacho, antes da troca.')
    quebra()
    titulo('3. Testes e experimentos')
    par('Os testes automatizados reproduzem o exemplo 7.1 (makespan 13, útil 10, troca 3, espera 4,67 e turnaround 9), o 7.2 (fault de teste = 5, makespan 13, cinco faults, esperas zero) e o 7.3 (esperas médias 3,67 FCFS e 2,33 SJF). O exemplo 5.5 termina em 441, com quatro faults. A latência da CLI de produção permanece fixa em 20.')
    par('Também são testados RR sem concorrentes, chegada no quantum, SJF não preemptivo e empate, FIFO/LRU, quadros protegidos, retentativa sem fault extra e quatro CPUs simultâneas. Asserções em toda execução verificam: útil + troca + ocioso = makespan por CPU; turnaround = espera + útil + troca + bloqueio por processo; todas as referências consumidas e memória liberada ao terminar.')
    par('As 32 configurações foram executadas duas vezes. As repetições produziram os mesmos resultados por processo, por CPU e no Gantt. Em todos os casos, os 1.000 processos terminaram e foram consumidas as 40.398 referências previstas. Os comandos para repetir os testes e os experimentos estão no README do repositório.')
    ambiente=json.loads((BASE/'ambiente.json').read_text(encoding='utf-8'))
    hardware=ambiente.get('hardware',{})
    par(f'Os experimentos foram realizados no Windows, com Python {ambiente["python"].split()[0]} e processador {hardware.get("Name",ambiente["processador"])}. O computador tem {hardware.get("NumberOfCores","-")} núcleos físicos e {hardware.get("NumberOfLogicalProcessors","-")} processadores lógicos. As CPUs do modelo são simuladas dentro de um único programa, sem execução paralela real.')
    par(f'Tempo real do motor: mínimo {min(r["duracao_motor_s"] for r in rs):.3f}s; máximo {max(r["duracao_motor_s"] for r in rs):.3f}s. Motor + saída: máximo {max(r["duracao_motor_s"]+r["duracao_saida_s"] for r in rs):.3f}s. A medição do motor inclui validação e cálculo de métricas, exclui leitura do arquivo, figuras e a repetição de verificação. Todas as configurações ficaram abaixo de um minuto nesta máquina.')
    par('Matriz: FCFS, SJF e RR com Q=2,5,10,20,50; dois cenários e duas quantidades de CPUs; LRU/256 quadros/troca 1. Mais quatro casos FCFS/FIFO. O PDF lista Q=2,10,50, mas menciona cinco quantums na contagem; Q=5 e 20 ampliam a cobertura por decisão de implementação.')
    par('A espera soma apenas o tempo na fila de prontos. O turnaround é o término menos a chegada, e a resposta é o primeiro despacho menos a chegada. O makespan é o instante do último término. A taxa de faults divide as faltas pelas 40.398 referências lógicas, sem contar retentativas como novas faltas. O speedup divide o makespan de 1 CPU pelo de 4 CPUs equivalentes; a eficiência é esse valor dividido por 4. A utilização de cada CPU é (tempo útil + troca) / makespan.')
    for cenario in cenarios:
        quebra(); titulo('4. Resultados - cenário '+('A' if cenario==cenarios[0] else 'B'))
        linhas=[r for r in rs if r['cenario']==cenario]
        par('Valores de tempo em unidades simuladas. Identificação: cenário-CPUs-política[-quantum]-memória. Todos os casos usam 256 quadros e custo de troca 1. Speedup e eficiência indicam o par 1/4 CPUs da mesma configuração, repetidos nas duas linhas.')
        headers=['Execução','Fim','Espera média','Espera máx.','Turn. médio','Resp. média','Trocas','Faults','Taxa %','Speedup','Efic. %']
        tabela(headers,[[nome(r)]+[f(r[k]) for k in ['makespan','espera_media','espera_maxima','turnaround_medio','resposta_media','trocas','faults']]+[f(100*r['taxa_faults']),f(r['speedup']),f(100*r['eficiencia'])] for r in linhas], [154]+[60]*10)
    quebra(); titulo('5. Comparação dos escalonadores')
    figura(GRAF/'espera.png',720)
    par('O gráfico apresenta a espera média com LRU. O eixo vertical usa escala logarítmica porque os tempos de 1 e 4 CPUs são muito diferentes. Os valores exatos estão nas tabelas anteriores.')
    quebra(); titulo('5.1. Quantum do Round Robin')
    figura(GRAF/'quantum.png',720)
    par('O quantum menor aumentou o número de trocas. No cenário B com 4 CPUs, Q=2 também reduziu o tempo de resposta, mas aumentou a espera e o tempo total. Portanto, atender mais cedo pela primeira vez não significou terminar mais rápido.')
    quebra(); titulo('5.2. Ganho com quatro CPUs')
    figura(GRAF/'speedup.png',620)
    for cenario in cenarios:
        fc=selecionar(cenario,4)[0]; sj=selecionar(cenario,4)[1]
        par(f'Em {nome(fc)}, a espera média foi {fc["espera_media"]:.2f}, o makespan foi {fc["makespan"]} e ocorreram {fc["faults"]} faults. Em {nome(sj)}, os valores foram {sj["espera_media"]:.2f}, {sj["makespan"]} e {sj["faults"]}. O SJF terminou a carga antes e teve menos faltas nos dois cenários. No A, porém, sua espera média foi maior. Isso mostra que diminuir o tempo total não garante diminuir a espera de todos os processos.')
        rr=[r for r in selecionar(cenario,4) if r['config']['sched']=='rr']
        a,b=rr[0],rr[-1]
        par(f'Comparando {nome(a)} com {nome(b)}, a resposta média foi {a["resposta_media"]:.2f} e {b["resposta_media"]:.2f}; a espera média foi {a["espera_media"]:.2f} e {b["espera_media"]:.2f}; as trocas foram {a["trocas"]} e {b["trocas"]}. O quantum maior reduziu as trocas e a espera nesses casos.')
    par('O cenário B impõe chegadas até 10.604; CPUs extras não antecipam chegadas. Portanto, o speedup inclui limites de chegada, bloqueios e diferenças de memória, além da capacidade de CPU. Quatro é uma referência ideal, não uma garantia para este modelo integrado.')
    maior=max((r for r in rs if r['config']['cpus']==4),key=lambda r:r['speedup'])
    if maior['speedup']>4:
        equivalente=next(r for r in rs if r['cenario']==maior['cenario'] and r['config']==dict(maior['config'],cpus=1))
        par(f'{nome(maior)} apresenta speedup {maior["speedup"]:.2f} e eficiência {100*maior["eficiencia"]:.2f}%, acima da referência linear. As execuções de 1/4 CPUs têm {equivalente["faults"]}/{maior["faults"]} faults: a ordem de execução altera a pressão na memória. O ganho medido abrange essa interação e não representa paralelização de uma sequência fixa de instruções e faltas.')
    quebra(); titulo('6. Diagramas de Gantt')
    for exemplo in [selecionar(cenarios[0],1)[0],selecionar(cenarios[1],4)[0]]:
        por_tipo={tipo:sum(e['fim']-e['inicio'] for e in exemplo['gantt']
                      if (e['evento'].startswith('P') if tipo=='útil' else e['evento']==tipo))
                  for tipo in ['útil','TROCA','OCIOSA']}
        par(f'{nome(exemplo)}, janela [0,200): soma entre CPUs de {por_tipo["útil"]} unidades úteis, {por_tipo["TROCA"]} de troca e {por_tipo["OCIOSA"]} ociosas. São parcelas da janela, distintas dos totais da execução no apêndice.')
        figura(gantts_relatorio/(exemplo['id']+'.png'),600)
    par('No cenário A/FCFS, a fila inicial de 1.000 processos faz a janela inicial ser dominada por instalação de contextos e primeiras faltas: mesmo ocupada, a CPU ainda não produz trabalho útil. No cenário B com 4 CPUs, chegadas espaçadas permitem retornos atendidos mais cedo; aparecem intervalos úteis e ociosos. O Gantt evidencia por que utilização que inclui troca não equivale a produtividade.')
    quebra(); titulo('7. FIFO e LRU')
    pares=[]
    for cenario in cenarios:
        for cpus in [1,4]:
            l=selecionar(cenario,cpus)[0]; fi=selecionar(cenario,cpus,'fifo')[0]
            pares.append([nome(fi),str(fi['faults']),str(l['faults']),str(fi['makespan']),str(l['makespan']),f(fi['espera_media']),f(l['espera_media'])])
            par(f'{nome(fi)} comparado a {nome(l)}: diferença FIFO - LRU de {fi["faults"]-l["faults"]:+d} faults e {fi["makespan"]-l["makespan"]:+d} unidades de makespan. A comparação preserva cenário, escalonador, CPUs, quadros e custo.')
    tabela(['FIFO (par com LRU)','Faults FIFO','Faults LRU','Fim FIFO','Fim LRU','Espera FIFO','Espera LRU'],pares,[220]+[88]*6)
    par('O LRU teve menos faults e menor makespan nos quatro pares. Mesmo assim, não foi melhor em toda métrica: no cenário B com 4 CPUs, o FIFO teve menor espera média. Os resultados mostram que a substituição de páginas também altera a ordem e o tempo de retorno dos processos à fila.')
    par('A quantidade de faults não basta para afirmar que houve thrashing. Parte das faltas ocorre porque as páginas ainda não foram carregadas. Seria necessário acompanhar o conjunto de trabalho ao longo do tempo para separar esse efeito das substituições frequentes.')
    for cenario in cenarios:
        quebra(); titulo('8. Espera de processos curtos e longos - cenário '+('A' if cenario==cenarios[0] else 'B'))
        justica=[]
        for r in rs:
            if r['cenario']!=cenario: continue
            grupos={classe:[p for p in r['por_processo'] if p['classe']==classe] for classe in ['curto','longo']}
            justica.append([nome(r)]+[f(fun(p['espera'] for p in grupos[c])) for c in ['curto','longo'] for fun in [mean,max]])
        tabela(['Execução','Média curtos (952)','Máx. curtos','Média longos (48)','Máx. longos'],justica,[270,120,120,120,120])
        fc,sj=selecionar(cenario,4)[:2]
        def espera_classe(r,classe):
            return mean(p['espera'] for p in r['por_processo'] if p['classe']==classe)
        par(f'Com 4 CPUs e LRU, a espera média dos curtos foi {espera_classe(fc,"curto"):.2f} no FCFS e {espera_classe(sj,"curto"):.2f} no SJF. Para os longos, foi {espera_classe(fc,"longo"):.2f} e {espera_classe(sj,"longo"):.2f}. Os longos esperaram mais, mas também voltam mais vezes à fila. Por isso, a espera acumulada sozinha não permite concluir que houve injustiça em cada despacho.')
    quebra(); titulo('9. Conclusão e limitações')
    par('As quatro CPUs reduziram o tempo total em todas as configurações. O SJF teve o menor makespan entre os escalonadores testados nos dois cenários, mas não apresentou a menor espera média em todos os casos. No RR, os quantums menores aumentaram o custo de troca. Na comparação de memória, o LRU reduziu as faltas e o tempo total em relação ao FIFO.')
    par('Todos os processos terminaram, então não foi observada starvation nestas cargas. Isso não garante o mesmo resultado com chegadas contínuas de novos processos no SJF. Os dados também não isolam o efeito comboio: a escolha do escalonador muda tanto a fila quanto a sequência de referências à memória.')
    par('SJF conhece o burst futuro; um SO real o estimaria. Não há fila de disco, custo de migração, cache, TLB, bytes, endereços ou paralelismo físico. Latências de E/S e fault são independentes e constantes conforme o modelo. A ordem de operações simultâneas e a instalação de contexto são convenções determinísticas documentadas, relevantes à reprodução.')
    titulo('Referências')
    par('Enunciado do Trabalho M2 de Sistemas Operacionais (2026) e arquivos cenario_A_t0.json e cenario_B_espacadas.json, fornecidos para a atividade. Código, instruções e resultados: https://github.com/MatheusThurow/SO_m2.')
    titulo('Apêndice - Gantts e tempos por CPU')
    par('Cada página seguinte identifica uma configuração e mostra a janela 0 a 200. Pn identifica o processo; TROCA e OCIOSA usam a legenda. Os CSVs preservam exatamente cada intervalo e permitem ampliar qualquer trecho. A tabela abaixo de cada figura cobre toda a execução, e não apenas a janela do gráfico.')
    for r in rs:
        quebra(); titulo(nome(r))
        par(r['id'])
        figura(gantts_relatorio/(r['id']+'.png'),760)
        tabela(['CPU','Útil','Útil %','Troca','Troca %','Ocioso','Ocioso %','Trocas','Utilização %'],
            [[c['cpu'],c['util'],f(c['util_pct']),c['troca'],f(c['troca_pct']),c['ocioso'],f(c['ocioso_pct']),c['trocas'],f(c['utilizacao']*100)] for c in r['por_cpu']], [50]+[88]*8)
        par(f'Makespan {r["makespan"]}; espera média {r["espera_media"]:.2f}; resposta média {r["resposta_media"]:.2f}; faults {r["faults"]}; taxa {100*r["taxa_faults"]:.2f}%.')
    def rodape(canvas,doc):
        canvas.setFont('Arial',9)
        canvas.setFillColor(colors.black)
        canvas.drawString(36,20,'Sistemas Operacionais - Trabalho M2')
        canvas.drawRightString(806,20,str(doc.page))
    doc=SimpleDocTemplate(str(OUT/'relatorio_m2.pdf'),pagesize=landscape(A4),rightMargin=36,leftMargin=36,topMargin=30,bottomMargin=36,
                          title='Trabalho M2 - Sistemas Operacionais',author='Matheus Thurow; Rodrigo Nicola; Eduardo Bez')
    doc.build(story,onFirstPage=rodape,onLaterPages=rodape)
    capa=BytesIO()
    c=pdfcanvas.Canvas(capa,pagesize=A4)
    largura,altura=A4
    c.drawImage('relatorio/assets/univali.png',(largura-150)/2,altura-165,width=150,height=150*40/59,mask='auto')
    c.setFont('Arial-Bold',12)
    c.drawCentredString(largura/2,altura-200,'UNIVERSIDADE DO VALE DO ITAJAÍ')
    c.setFont('Arial',12)
    c.drawCentredString(largura/2,altura-225,'Disciplina: Sistemas Operacionais')
    for y,n in zip([altura-295,altura-315,altura-335],['Matheus Thurow','Rodrigo Nicola','Eduardo Bez']):
        c.drawCentredString(largura/2,y,n)
    c.setFont('Arial-Bold',14)
    c.drawCentredString(largura/2,altura-440,'SIMULADOR DE ESCALONAMENTO')
    c.drawCentredString(largura/2,altura-462,'MULTIPROCESSADO COM PAGINAÇÃO')
    c.drawCentredString(largura/2,altura-484,'SOB DEMANDA')
    c.setFont('Arial',12)
    c.drawCentredString(largura/2,altura-520,'Trabalho M2')
    c.drawCentredString(largura/2,65,'2026')
    c.save()
    capa.seek(0)
    writer=PdfWriter()
    writer.append(PdfReader(capa))
    writer.append(PdfReader(str(OUT/'relatorio_m2.pdf')))
    writer.add_metadata({'/Title':'Trabalho M2 - Sistemas Operacionais','/Author':'Matheus Thurow; Rodrigo Nicola; Eduardo Bez'})
    with (OUT/'relatorio_m2.pdf').open('wb') as arquivo:
        writer.write(arquivo)
    md.insert(0,'![Univali](assets/univali.png)\n\nUniversidade do Vale do Itajaí\n')
    Path('relatorio/relatorio.md').write_text('\n'.join(md),encoding='utf-8')
    print(OUT/'relatorio_m2.pdf')


if __name__=='__main__': main()
