# ─────────────── painel: gráficos em HTML autocontido (SVG feito aqui, sem internet, sem biblioteca) ───────────────
import html as _html
import math

PAINEL_SERIES = [   # chave, título, unidade, melhor, casas
    ('livre_c', 'Espaço livre em C:', 'GB', 'maior', 0),
    ('ram_usada', 'RAM em uso', 'GB', 'menor', 1),
    ('boot_s', 'Tempo de boot', 's', 'menor', 0),
    ('cpu', 'CPU em repouso', '%', 'menor', 0),
    ('temperatura', 'Temperatura', '°C', 'menor', 0),
    ('inicializacao', 'Abrem com o Windows', '', 'menor', 0),
    ('processos', 'Processos', '', 'menor', 0),
]
PAINEL_BENCH = [('disco_escrita', 'Disco: escrita sequencial', 'MB/s'), ('disco_4k', 'Disco: escritas pequenas', 'ops/s'),
                ('cpu', 'CPU: um núcleo', 'MB/s'), ('cpu_multi', 'CPU: todos os núcleos', 'MB/s'), ('ram', 'RAM: cópia', 'MB/s')]


def _e(x):
    return _html.escape(str(x), quote=True)


def _num(v, casas):
    return br(v, casas)


def _escala(lo, hi):
    """Limites 'redondos' para o eixo y, sem esticar um valor constante até virar uma reta no meio do nada."""
    if hi - lo < 1e-9:
        folga = max(abs(hi) * 0.1, 1.0)
        return lo - folga, hi + folga
    folga = (hi - lo) * 0.12
    return lo - folga, hi + folga


def _passo_bonito(intervalo, alvo=4):
    """Passo 1, 2, 2.5, 5 x 10^n que dá perto de `alvo` divisões."""
    bruto = intervalo / alvo
    mag = 10 ** math.floor(math.log10(bruto))
    for m in (1, 2, 2.5, 5, 10):
        if bruto <= m * mag:
            return m * mag
    return 10 * mag


def _ticks(lo, hi, inteiro=False):
    passo = _passo_bonito(hi - lo)
    if inteiro:
        passo = max(1.0, round(passo))
    t = math.ceil(lo / passo - 1e-9) * passo
    out = []
    while t <= hi + 1e-9 and len(out) < 8:
        out.append(round(t, 6))
        t += passo
    return out


def svg_linha(serie, titulo, un='', casas=0, marcas=(), tendencia=None, largura=560, altura=190, zero=False, suave=False, destaque=False, projecao=None, limite=None):
    """serie: [(datetime, valor)]; marcas: [(datetime, rótulo)] (ex.: quando um pacote foi aplicado); tendencia: True mostra a reta de ajuste."""
    ml, mr, mt, mb = 46, 14, 14, 26
    w, h = largura - ml - mr, altura - mt - mb
    if not serie:
        return f'<svg viewBox="0 0 {largura} {altura}" role="img" aria-label="{_e(titulo)}: sem dados"></svg>'
    t0, t1 = serie[0][0], serie[-1][0]
    span = max((t1 - t0).total_seconds(), 1.0)
    lo, hi = _escala(min(v for _, v in serie), max(v for _, v in serie))
    if limite and limite[0] > hi:   # a linha de limite precisa caber no gráfico, senão ela some e o aviso perde o sentido
        hi = limite[0] + (hi - lo) * 0.08
    if projecao:
        t1p = projecao[1]
        span_p = max((t1p - t0).total_seconds(), span)
    else:
        span_p = span
    if zero:   # percentuais: começar em 0 evita transformar ruído em montanha
        lo, hi = 0.0, max(hi, 10.0)

    def x(d):
        return ml + (w / 2 if len(serie) == 1 else (d - t0).total_seconds() / span_p * w)

    def y(v):
        return mt + h - (v - lo) / (hi - lo) * h
    partes = [f'<svg viewBox="0 0 {largura} {altura}" role="img" aria-label="{_e(titulo)}: de {_num(serie[0][1], casas)} a {_num(serie[-1][1], casas)} {_e(un)}" class="grafico">']
    for v in _ticks(lo, hi, inteiro=casas == 0):
        partes.append(f'<line x1="{ml}" x2="{ml + w}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="grade"/>'
                      f'<text x="{ml - 6}" y="{y(v) + 4:.1f}" class="eixo" text-anchor="end">{_num(v, casas)}</text>')
    partes.append(f'<text x="{ml}" y="{altura - 6}" class="eixo">{t0:%d/%m}</text><text x="{ml + w}" y="{altura - 6}" class="eixo" text-anchor="end">{t1:%d/%m}</text>')
    if limite and lo <= limite[0] <= hi:
        partes.append(f'<line x1="{ml}" x2="{ml + w}" y1="{y(limite[0]):.1f}" y2="{y(limite[0]):.1f}" class="limite"/>'
                      f'<text x="{ml + w}" y="{y(limite[0]) - 4:.1f}" class="rotulo-limite" text-anchor="end">{_e(limite[1])}</text>')
    for d, rot in marcas:
        if t0 <= d <= t1 and len(serie) > 1:
            partes.append(f'<line x1="{x(d):.1f}" x2="{x(d):.1f}" y1="{mt}" y2="{mt + h}" class="marca"><title>{_e(rot)} ({d:%d/%m})</title></line>')
    if len(serie) > 1:
        pts = ' '.join(f'{x(d):.1f},{y(v):.1f}' for d, v in serie)
        partes.append(f'<polygon points="{x(t0):.1f},{mt + h} {pts} {x(t1):.1f},{mt + h}" class="area"/>')
        partes.append(f'<polyline points="{pts}" class="{"linha fraca" if suave else "linha"}"/>')
        if suave:
            sm = mediana_movel(serie)
            partes.append('<polyline points="' + ' '.join(f'{x(d):.1f},{y(v):.1f}' for d, v in sm) + '" class="linha"/>')
        if tendencia:
            xs = [(d - t0).total_seconds() / 86400 for d, _ in serie]
            ys = [v for _, v in serie]
            mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
            den = sum((a - mx) ** 2 for a in xs)
            if den:
                b = sum((a - mx) * (c - my) for a, c in zip(xs, ys)) / den
                a0 = my - b * mx
                dias = span / 86400
                partes.append(f'<line x1="{x(t0):.1f}" y1="{y(min(max(a0, lo), hi)):.1f}" x2="{x(t1):.1f}" y2="{y(min(max(a0 + b * dias, lo), hi)):.1f}" class="tendencia"/>')
    if projecao and len(serie) > 1:
        d_fim, v_fim = serie[-1][0], mediana_movel(serie)[-1][1]
        partes.append(f'<line x1="{x(d_fim):.1f}" y1="{y(v_fim):.1f}" x2="{x(projecao[1]):.1f}" y2="{y(max(lo, 0)):.1f}" class="projecao"/>'
                      f'<text x="{x(projecao[1]) - 4:.1f}" y="{y(max(lo, 0)) - 6:.1f}" class="rotulo-proj" text-anchor="end">{_e(projecao[2])}</text>')
    if destaque:
        for dd, vv in anomalias(serie):
            partes.append(f'<circle cx="{x(dd):.1f}" cy="{y(vv):.1f}" r="4" class="anomalia"><title>fora do normal: {dd:%d/%m %H:%M}, {_num(vv, casas)} {_e(un)}</title></circle>')
    d, v = serie[-1]
    partes.append(f'<circle cx="{x(d):.1f}" cy="{y(v):.1f}" r="3.5" class="ponto"/>')
    for dd, vv in serie:   # tooltips: passar o mouse mostra o valor de cada medida
        partes.append(f'<circle cx="{x(dd):.1f}" cy="{y(vv):.1f}" r="7" class="alvo"><title>{dd:%d/%m %H:%M}: {_num(vv, casas)} {_e(un)}</title></circle>')
    partes.append('</svg>')
    return ''.join(partes)


def sparkline_txt(valores, ascii_=False):
    """Mini gráfico de uma linha para o terminal."""
    v = [float(x) for x in valores if isinstance(x, (int, float))]
    if not v:
        return ''
    blocos = ' .:-=+*#' if ascii_ else '▁▂▃▄▅▆▇█'
    lo, hi = min(v), max(v)
    if hi - lo < 1e-9:
        return blocos[len(blocos) // 2] * min(len(v), 24)
    if len(v) > 24:   # reamostra para caber na linha
        v = [v[int(i * (len(v) - 1) / 23)] for i in range(24)]
    return ''.join(blocos[min(len(blocos) - 1, int((x - lo) / (hi - lo) * (len(blocos) - 1) + 0.5))] for x in v)


PAINEL_CSS = '''
:root{--fundo:#0c0c0d;--painel:#131315;--linha:#26262b;--forte:#3a3a41;--apagado:#8a877f;--texto:#d2cdc2;--osso:#f1ebe0;--ambar:#e2a85c;--verde:#9ccf8c;--verm:#e5737a;--mono:ui-monospace,Consolas,"Cascadia Mono",monospace;--sans:"Segoe UI",system-ui,-apple-system,sans-serif}
@media (prefers-color-scheme:light){:root{--fundo:#f6f3ec;--painel:#fffdf8;--linha:#e2ddd1;--forte:#c9c2b2;--apagado:#6d6a63;--texto:#2b2a27;--osso:#161512;--ambar:#a8650f;--verde:#3d7a2e;--verm:#b3262f}}
*{box-sizing:border-box;margin:0;padding:0}html{background:var(--fundo);color:var(--texto);font:15px/1.55 var(--sans)}
body{max-width:1180px;margin:0 auto;padding:32px 16px 64px}
h1{font:600 30px/1.1 var(--sans);color:var(--osso);letter-spacing:-.01em}h1 small{font:400 14px var(--mono);color:var(--apagado);margin-left:10px}
.sub{color:var(--apagado);margin:6px 0 28px;max-width:70ch}
h2{font:600 17px var(--sans);color:var(--osso);margin:36px 0 12px}h3{font:600 14px var(--sans);color:var(--osso);margin:22px 0 8px}
.cartoes{display:grid;grid-template-columns:repeat(auto-fill,minmax(168px,1fr));gap:12px}
.cartao{background:var(--painel);border:1px solid var(--linha);padding:14px 14px 10px}.cartao b{display:block;font:500 12px var(--sans);color:var(--apagado)}
.cartao .n{font:600 26px/1.2 var(--mono);color:var(--osso)}.cartao .n i{font:400 13px var(--mono);color:var(--apagado);font-style:normal;margin-left:3px}
.cartao .d{font:12px var(--mono);margin-top:2px}.bom{color:var(--verde)}.mau{color:var(--verm)}.neutro{color:var(--apagado)}
.graficos{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:16px}
figure{background:var(--painel);border:1px solid var(--linha);padding:14px 14px 6px}figcaption{font:600 14px var(--sans);color:var(--osso);display:flex;justify-content:space-between;gap:8px}
figcaption span{font:400 12px var(--mono);color:var(--apagado)}
.grafico{width:100%;height:auto;display:block;margin-top:6px}.grade{stroke:var(--linha);stroke-width:1}.eixo{fill:var(--apagado);font:11px var(--mono)}
.linha{fill:none;stroke:var(--ambar);stroke-width:2;stroke-linejoin:round}.area{fill:var(--ambar);opacity:.1}.tendencia{stroke:var(--apagado);stroke-width:1.5;stroke-dasharray:5 4}
.linha.fraca{opacity:.35;stroke-width:1.2}.limite{stroke:var(--verm);stroke-width:1.2;stroke-dasharray:6 4}.rotulo-limite,.rotulo-proj{fill:var(--verm);font:11px var(--mono)}.projecao{stroke:var(--verm);stroke-width:1.8;stroke-dasharray:3 4}.anomalia{fill:var(--verm);stroke:var(--painel);stroke-width:1.5}.ponto{fill:var(--ambar)}.marca{stroke:var(--verde);stroke-width:1.5;stroke-dasharray:2 3}.alvo{fill:transparent}.alvo:hover{fill:var(--ambar);opacity:.35}
.legenda{font:12px var(--mono);color:var(--apagado);margin-top:10px}.legenda .m{color:var(--verde)}
.achados{list-style:none;border:1px solid var(--linha);background:var(--painel)}.achados li{padding:12px 14px;border-bottom:1px solid var(--linha)}.achados li:last-child{border:0}
.achados .mau{font-weight:600}.vazio{border:1px dashed var(--forte);padding:22px;color:var(--apagado)}code{font:13px var(--mono);color:var(--osso)}
details{margin-top:28px}summary{cursor:pointer;color:var(--apagado)}table{border-collapse:collapse;margin-top:10px;font:12px var(--mono)}td,th{padding:3px 12px 3px 0;text-align:left;border-bottom:1px solid var(--linha)}
@media (max-width:620px){.eixo{font-size:16px}.graficos{gap:12px}h1{font-size:26px}}
ul.propostas{list-style:none;display:grid;gap:12px}.propostas li{background:var(--painel);border:1px solid var(--linha);border-left:3px solid var(--forte);padding:12px 14px}
.agir{display:inline-block;margin-top:10px;font:600 13px var(--sans);color:var(--fundo);background:var(--ambar);padding:6px 14px;border-radius:4px;text-decoration:none}.agir:hover,.agir:focus-visible{background:var(--osso);outline:2px solid var(--ambar);outline-offset:2px}
.propostas .c-alta{border-left-color:var(--verm)}.propostas .c-media{border-left-color:var(--ambar)}.propostas b{color:var(--osso)}.propostas p{margin-top:4px}.propostas .det{font:12px var(--mono);color:var(--apagado)}
.rolagem{overflow-x:auto}table.efeito{width:100%;font:13px var(--sans)}table.efeito td,table.efeito th{padding:8px 12px 8px 0;vertical-align:top;border-bottom:1px solid var(--linha)}table.efeito th{color:var(--osso);white-space:nowrap}
.indice{position:sticky;top:0;z-index:5;display:flex;flex-wrap:wrap;gap:4px 18px;padding:10px 0;margin:0 0 8px;background:var(--fundo);border-bottom:1px solid var(--linha);font:13px var(--sans)}
.indice a{color:var(--apagado);text-decoration:none;padding:2px 0;border-bottom:2px solid transparent}.indice a:hover,.indice a:focus-visible{color:var(--osso);border-bottom-color:var(--ambar);outline:0}
h2{scroll-margin-top:56px}.cartao svg{display:block;width:100%;height:26px;margin-top:6px}.cartao svg polyline{fill:none;stroke:var(--forte);stroke-width:1.5}
.rodada{background:var(--painel);border:1px solid var(--linha);padding:14px;margin-bottom:12px}.rodada header{display:flex;flex-wrap:wrap;gap:4px 12px;align-items:baseline;margin-bottom:8px}
.rodada header b{color:var(--osso);font:600 14px var(--sans)}.rodada header span{color:var(--apagado);font:12px var(--mono)}
.par{display:grid;grid-template-columns:minmax(120px,190px) 1fr minmax(120px,auto);gap:4px 14px;align-items:center;padding:5px 0;border-top:1px solid var(--linha);font:13px var(--sans)}
.par .barras{display:grid;gap:3px}.par .barras i{display:block;height:7px;background:var(--forte);min-width:2px}.par .barras i.dep.bom{background:var(--verde)}.par .barras i.dep.mau{background:var(--verm)}.par .barras i.dep.neutro{background:var(--apagado)}
.par .v{font:12px var(--mono);text-align:right;white-space:nowrap}
.itens-prova{list-style:none;background:var(--painel);border:1px solid var(--linha)}.itens-prova li{display:grid;grid-template-columns:minmax(0,1fr) minmax(90px,30%);gap:4px 14px;padding:9px 14px;border-bottom:1px solid var(--linha);align-items:center}
.itens-prova li:last-child{border:0}.itens-prova b{color:var(--osso);font-weight:600}.itens-prova small{display:block;color:var(--apagado);font:12px var(--mono)}.itens-prova .g{color:var(--verde);font:12px var(--mono)}
.itens-prova .barra{height:7px;background:var(--linha)}.itens-prova .barra i{display:block;height:7px;background:var(--verde);min-width:2px}
@media (max-width:620px){.par{grid-template-columns:1fr}.par .v{text-align:left}.itens-prova li{grid-template-columns:1fr}}
footer{margin-top:44px;color:var(--apagado);font:12px var(--mono)}
'''


def _proj_painel(chave, s):
    if chave != 'livre_c':
        return None
    pr = projecao_enchimento(s)
    return (pr[0], pr[1], f'cheio ~{pr[1]:%d/%m}') if pr else None


def _tabela_efeito_html(efeitos):
    """efeitos: de tabela_efeito(). Só colore o que passou do ruído; o resto é 'sem diferença mensurável' (honestidade)."""
    cls = {'melhorou': 'bom', 'piorou': 'mau'}
    linhas = []
    for titulo, quando, cel in efeitos:
        tds = []
        for rot, ver, a, b, casas, un in cel:
            if ver in ('melhorou', 'piorou'):
                tds.append(f'<td class="{cls[ver]}">{_e(rot)}: {_num(a, casas)} → {_num(b, casas)}{(" " + _e(un)) if un else ""}</td>')
            else:
                tds.append(f'<td class="neutro">{_e(rot)}: {_e(ver)}</td>')
        linhas.append(f'<tr><th>{_e(titulo)}<br><span class="neutro">{quando:%d/%m/%Y}</span></th>' + ''.join(tds) + '</tr>')
    return ('<div class="rolagem"><table class="efeito">' + ''.join(linhas) + '</table></div>'
            '<p class="legenda">Compara a mediana dos 7 dias antes e dos 7 dias depois. Só mostra melhora ou piora quando a mudança passa da oscilação normal; '
            'com vários pacotes na mesma semana, não dá para saber qual deles causou.</p>')


def _faisca(serie):
    """Um risco pequeno com os últimos valores, para o cartão mostrar para onde a medida está indo."""
    vals = [v for _, v in serie[-40:]]
    if len(vals) < 3:
        return ''
    lo, hi = min(vals), max(vals)
    faixa = (hi - lo) or 1
    pts = ' '.join(f'{i * 120 / (len(vals) - 1):.1f},{24 - (v - lo) / faixa * 22:.1f}' for i, v in enumerate(vals))
    return f'<svg viewBox="0 0 120 26" preserveAspectRatio="none" aria-hidden="true"><polyline points="{pts}"/></svg>'


def _mb(v):
    return f'{_num(v / 1024, 1)} GB' if v >= 1024 else f'{_num(v, 0)} MB'


def _secao_provas(pv, efeitos=()):
    """Prova de ganho: o que foi medido na hora (item por item), depois de reiniciar (por rodada) e na semana (mediana)."""
    pv = pv or {}
    rs, its, abertos = pv.get('rodadas') or [], pv.get('itens') or [], pv.get('abertos') or []
    if not (rs or its or abertos or efeitos):
        return ''
    com = [r for r in its if r.get('pontos', 0) > 0]
    total = sum(max(0, r.get('livre') or 0) for r in its)
    svc = sum(max(0, r.get('svc') or 0) for r in its)
    melhoras = sum(1 for r in rs for m in r['metricas'] if m[1] == 'melhorou')
    out = ['<h2>Prova de ganho</h2><p class="sub">O que cada mudança rendeu de verdade neste PC. Cada item é medido antes e depois na hora; '
           'boot, CPU e RAM em repouso são comparados depois que você reinicia. O que fica dentro da oscilação normal aparece como sem diferença.</p>']
    cart = [('Disco liberado', _mb(total) if total else '0', 'somando todas as aplicações'), ('Itens com ganho na hora', str(len(com)), f'de {len(its)} medidos'),
            ('Serviços a menos', str(svc), 'parados na hora'), ('Medidas que melhoraram', str(melhoras), f'em {len(rs)} rodada{"s" if len(rs) != 1 else ""} depois de reiniciar')]
    out.append('<div class="cartoes">' + ''.join(f'<div class="cartao"><b>{_e(a)}</b><div class="n">{_e(b)}</div><div class="d neutro">{_e(c)}</div></div>' for a, b, c in cart) + '</div>')
    if rs:
        out.append('<h3>Depois de reiniciar</h3>')
        cls = {'melhorou': 'bom', 'piorou': 'mau', 'igual': 'neutro'}
        for r in rs[:6]:
            linhas = []
            for rot, ver, a, b, casas, un in r['metricas']:
                topo = max(abs(a), abs(b)) or 1
                un_ = (' ' + _e(un)) if un else ''
                valor = (f'{_num(a, casas)}{un_} → <span class="{cls[ver]}">{_num(b, casas)}{un_}</span>' if ver != 'igual'
                         else f'<span class="neutro">sem diferença ({_num(b, casas)}{un_})</span>')
                linhas.append(f'<div class="par"><span>{_e(rot)}</span><div class="barras"><i style="width:{abs(a) / topo * 100:.0f}%"></i>'
                              f'<i class="dep {cls[ver]}" style="width:{abs(b) / topo * 100:.0f}%"></i></div><span class="v">{valor}</span></div>')
            if not linhas:
                linhas.append('<div class="par"><span class="neutro">Sem medida de antes para comparar.</span></div>')
            quando = str(r.get('quando') or '')[:10]
            try:
                quando = f'{datetime.fromisoformat(str(r["quando"])):%d/%m/%Y}'
            except (TypeError, ValueError):
                pass
            out.append(f'<div class="rodada"><header><b>{_e(" + ".join(PACOTES[p].titulo if p in PACOTES else str(p) for p in r["pacotes"]))}</b><span>{_e(quando)} · {r["itens"]} iten{"s" if r["itens"] != 1 else ""}'
                       + ('' if r['reiniciou'] else ' · sem reinício: o boot não entra') + '</span></header>' + ''.join(linhas) + '</div>')
        out.append('<p class="legenda">Barra de cima: antes. Barra de baixo: depois. Tudo o que foi aplicado entre dois reinícios entra na mesma rodada, '
                   'porque não dá para separar o efeito de cada pacote. É uma medida antes e uma depois: vale como indício.</p>')
    if abertos:
        out.append('<div class="vazio" style="margin:12px 0">Esperando o próximo reinício para comparar: <b>' + _e(', '.join(dict.fromkeys(PACOTES[e.get('pacote')].titulo if e.get('pacote') in PACOTES else str(e.get('pacote')) for e in abertos[-8:])))
                   + '</b>. Reinicie o PC; a primeira medida depois disso (do segundo plano ou do comando <code>medir</code>) fecha a comparação.</div>')
    if com:
        topo = max(max(0, r.get('livre') or 0) for r in com) or 1
        lis = []
        for r in com[:20]:
            ganho = texto_ganho(r)
            lis.append(f'<li><div><b>{_e(r["titulo"])}</b><small>{_e(r["pacote"])}' + (f' · aplicado {r["vezes"]}x' if r['vezes'] > 1 else '') + '</small>'
                       f'<span class="g">{_e(ganho)}</span></div><div class="barra"><i style="width:{max(0, r.get("livre") or 0) / topo * 100:.0f}%"></i></div></li>')
        out.append('<h3>Na hora, item por item</h3><ul class="itens-prova">' + ''.join(lis) + '</ul>'
                   '<p class="legenda">A barra é o espaço em disco liberado. Disco e serviços parados são exatos; RAM e processos oscilam sozinhos e só entram '
                   'quando passam do ruído. ' + (f'{len(its) - len(com)} itens mudaram o Windows sem ganho imediato: o efeito deles é o da rodada acima.' if len(its) > len(com) else '') + '</p>')
    elif its:
        out.append('<h3>Na hora, item por item</h3><div class="vazio">' + f'{len(its)} itens medidos, nenhum com ganho imediato acima do ruído. '
                   'É o normal para ajustes de registro e de inicialização: o efeito aparece depois de reiniciar.</div>')
    if efeitos:
        out.append('<h3>Na semana: efeito de cada pacote que você aplicou</h3>' + _tabela_efeito_html(efeitos))
    return ''.join(out)


NOMES_INDICE = {'O que eu proporia': 'Propostas', 'O que está mudando': 'Tendências', 'O que aconteceu depois das propostas que você executou': 'Resultados',
                'Benchmark ao longo do tempo': 'Benchmark', 'Saúde do Windows': 'Saúde', 'Prova de ganho': 'Prova de ganho'}


def _com_indice(corpo_html):
    """Dá uma âncora a cada seção e devolve (índice no topo, corpo). Sem script: são só links para dentro da página."""
    secoes = []

    def ancora(m):
        slug = re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', _html.unescape(m.group(1)).lower()).encode('ascii', 'ignore').decode()).strip('-')
        secoes.append((slug, m.group(1)))
        return f'<h2 id="{slug}">{m.group(1)}</h2>'
    corpo_html = re.sub(r'<h2>([^<]+)</h2>', ancora, corpo_html)
    if len(secoes) < 3:
        return '', corpo_html
    return ('<nav class="indice" aria-label="Seções do painel">' + ''.join(f'<a href="#{s}">{NOMES_INDICE.get(_html.unescape(t), t)}</a>' for s, t in secoes) + '</nav>'), corpo_html


def _delta_cartao(serie, melhor, casas, un):
    if len(serie) < 4:
        return '<span class="neutro">poucas medidas</span>'
    a, b = _tercos(serie)
    d = b - a
    if abs(d) < 10 ** -casas / 2:
        return '<span class="neutro">estável</span>'
    bom = (d < 0) == (melhor == 'menor')
    return f'<span class="{"bom" if bom else "mau"}">{"+" if d > 0 else ""}{_num(d, casas)}{(" " + _e(un)) if un else ""} no período</span>'


def _secao_saude(sa, cliques=False):
    """sa: {'quando': iso, 'analise': analisa_saude(...)}. Erros do Windows, drivers e o que o sistema precisa, cada um com explicação e o que fazer."""
    from datetime import timedelta
    an = sa['analise']
    r = an['resumo']
    dq = _dt(sa.get('quando'))
    quando = _e(f'{dq:%d/%m/%Y %H:%M}' if dq else '')
    cab = (f'<h2>Saúde do Windows</h2><p class="sub">Retrato de {quando}: {r["eventos"]} eventos de erro nos últimos {SAUDE_DIAS} dias, '
           f'{r["problemas"]} problema{"s" if r["problemas"] != 1 else ""} encontrado{"s" if r["problemas"] != 1 else ""}, {r["graves"]} grave{"s" if r["graves"] != 1 else ""}.</p>')
    por_dia = {}
    for d in an.get('por_dia') or []:
        try:
            por_dia[datetime.fromisoformat(str(d['dia'])).date()] = int(d['n'])
        except (KeyError, TypeError, ValueError):
            continue
    fig = ''
    if por_dia:
        fim = max(por_dia)
        serie = [(datetime.combine(fim - timedelta(days=i), datetime.min.time()), float(por_dia.get(fim - timedelta(days=i), 0))) for i in range(SAUDE_DIAS - 1, -1, -1)]
        fig = ('<div class="graficos"><figure><figcaption>Erros graves e críticos por dia<span>Visualizador de Eventos</span></figcaption>'
               + svg_linha(serie, 'Erros por dia', 'eventos', 0, (), largura=1100, altura=190, zero=True, destaque=True) + '</figure></div>'
               '<p class="legenda">Dias com pico merecem atenção: veja abaixo o que aconteceu. Parte desses eventos é ruído conhecido do Windows (já descontado dos problemas).</p>')
    nomes = {'erro': 'Erros do Windows', 'driver': 'Drivers', 'windows': 'O que o Windows precisa'}
    blocos = []
    for cat in ('erro', 'driver', 'windows'):
        itens = [x for x in an['problemas'] if x['categoria'] == cat]
        if not itens:
            continue
        lis = ''.join(f'<li class="c-{ {"alta": "alta", "média": "media"}.get(x["gravidade"], "baixa") }"><b>{_e(x["titulo"])}</b>'
                      f'<p class="det">{_e(x["evidencia"])} · gravidade {_e(x["gravidade"])}</p><p>{_e(x["explica"])}</p>'
                      f'<p><b>O que fazer:</b> {_e(x["faz"])}' + (f' <code>katharos {_e(x["comando"])}</code>' if x['comando'] else '') + '</p>' + link_clique(x['comando'], cliques) + '</li>' for x in itens)
        blocos.append(f'<h3>{nomes[cat]}</h3><ul class="propostas">{lis}</ul>')
    if not an['problemas']:
        blocos.append('<div class="vazio">Nenhum problema encontrado nos logs, nos drivers nem no estado do Windows.</div>')
    if an.get('ruido'):
        blocos.append(f'<p class="legenda">{r["ruido"]} eventos de ruído conhecido (DCOM 10016) foram ignorados: a Microsoft documenta que não têm efeito.</p>')
    if an.get('outros'):
        linhas = ''.join(f'<tr><td>{_e(g.get("provedor"))} {_e(g.get("id"))}</td><td>{_e(g.get("n"))}x</td><td>{_e(corta(str(g.get("msg") or ""), 140))}</td></tr>' for g in an['outros'][:6])
        blocos.append('<details><summary>Outros erros frequentes sem explicação no catálogo</summary><div class="rolagem"><table><tr><th>origem</th><th>vezes</th><th>mensagem original</th></tr>'
                      + linhas + '</table></div><p class="legenda">Não sei explicar estes com segurança; a mensagem é a original do Windows.</p></details>')
    drv = an.get('drivers') or []
    if drv:
        linhas = ''.join(f'<tr><td>{_e(d.get("nome"))}</td><td>{_e(d.get("classe"))}</td><td>{_e(d.get("versao"))}</td><td>{_e(str(d.get("data") or "")[:7])}</td></tr>'
                         for d in sorted(drv, key=lambda d: str(d.get('data') or ''))[:25])
        blocos.append('<details><summary>Drivers instalados (os 25 mais antigos, sem os da Microsoft)</summary><div class="rolagem"><table><tr><th>dispositivo</th><th>tipo</th><th>versão</th><th>data</th></tr>'
                      + linhas + '</table></div><p class="legenda">Sem internet eu não sei qual é a versão mais nova: só mostro a idade e se houve quedas.</p></details>')
    return cab + fig + ''.join(blocos)


def _secao_ao_vivo(minutos, sessoes):
    """As últimas 24 h minuto a minuto e as sessões de jogo, do segundo plano (Katharos.exe)."""
    if not minutos and not sessoes:
        return ('<h2>Ao vivo e jogos</h2><div class="vazio">Ligue o acompanhamento em segundo plano (<code>katharos segundo-plano --ligar</code>): '
                'o Katharos passa a ler o PC segundo a segundo e a gravar cada sessão de jogo, e esta seção mostra as últimas 24 horas e o que segurou cada jogo.</div>')
    out = ['<h2>Ao vivo e jogos</h2>']
    figs = []
    for chave, titulo, un, lim in (('cpu', 'CPU (média do minuto)', '%', None), ('gpu', 'Placa de vídeo (média do minuto)', '%', None),
                                   ('temp_cpu', 'Temperatura da CPU (máxima do minuto)', '°C', (85, '85 °C')), ('temp_gpu', 'Temperatura da placa de vídeo', '°C', (85, '85 °C')),
                                   ('ram', 'RAM (média do minuto)', '%', (90, '90 %'))):
        s = [(m['_dt'], float(m[chave])) for m in minutos if isinstance(m.get(chave), (int, float))]
        if len(s) >= 10:
            jogos = []
            ant = None
            for m in minutos:   # marca o começo de cada jogo no gráfico
                if m.get('jogo') and m.get('jogo') != ant:
                    jogos.append((m['_dt'], f'jogo: {m["jogo"]}'))
                ant = m.get('jogo')
            figs.append(f'<figure><figcaption>{_e(titulo)}<span>{_num(min(v for _, v in s), 0)} a {_num(max(v for _, v in s), 0)} {_e(un)}</span></figcaption>'
                        + svg_linha(s, titulo, un, 0, jogos[-12:], zero=(un == '%'), suave=True, destaque=True, limite=lim) + '</figure>')
    if figs:
        out.append('<p class="legenda">Últimas 24 horas, um ponto por minuto. As linhas verdes pontilhadas marcam quando um jogo abriu.</p><div class="graficos">' + ''.join(figs) + '</div>')
    r = resumo_sessoes(sessoes, minimo_min=1)
    if r:
        lim = r['limites']
        partes_ = [f'{_e(NOMES_LIMITE.get(k, k))}: {_num(v, 0)} %' for k, v in sorted(lim.items(), key=lambda x: -x[1]) if v >= 1]
        out.append(f'<p>{r["sessoes"]} {"sessão" if r["sessoes"] == 1 else "sessões"} de jogo, {_num(r["horas"], 1)} h no total. '
                   f'O que mais segurou: <b>{_e(NOMES_LIMITE.get(r["principal"], r["principal"]))}</b>.'
                   + (f' Tempo de cada limite: {"; ".join(partes_)}.' if partes_ else '') + '</p>')
        linhas = ''.join(f'<tr><td>{_e(s.get("jogo") or "?")}</td><td>{s["_dt"]:%d/%m %H:%M}</td><td>{_num(s.get("min"), 0)} min</td>'
                         f'<td>{_num(s.get("cpu"), 0)} %</td><td>{_num(s.get("gpu"), 0)} %</td><td>{_num(s.get("ram_max"), 0)} %</td>'
                         f'<td>{_num(s.get("temp_cpu_max"), 0) if isinstance(s.get("temp_cpu_max"), (int, float)) else "-"} / {_num(s.get("temp_gpu_max"), 0) if isinstance(s.get("temp_gpu_max"), (int, float)) else "-"} °C</td>'
                         f'<td>{_e(NOMES_LIMITE.get(s.get("principal"), s.get("principal") or "-"))}</td></tr>' for s in reversed(sessoes[-20:]))
        out.append('<table><tr><th>jogo</th><th>quando</th><th>duração</th><th>CPU média</th><th>GPU média</th><th>RAM máx.</th><th>temp. máx. CPU / GPU</th><th>o que segurou</th></tr>'
                   + linhas + '</table><p class="legenda">"O que segurou" é o limite em que o jogo passou mais tempo (pelo menos 20 % da sessão). '
                   'Placa de vídeo no limite é o normal de um jogo pesado; CPU, calor, RAM ou disco no limite são o que dá para melhorar.</p>')
    return ''.join(out)


def monta_painel(amostras, benchs, pacotes, achados, pc='', versao='', sugestoes=(), efeitos=(), resultados=(), saude=None, cliques=False, horas=(), provas=None,
                 ao_vivo=None):
    """HTML completo do painel. amostras: de le_metricas(); benchs: [(datetime, {chave: mediana})]; pacotes: [(datetime, título)]."""
    marcas = [(d, f'aplicou: {t}') for d, t in pacotes]
    corpo = []
    periodo = ''
    if amostras:
        periodo = f'{len(amostras)} medidas, de {amostras[0]["_dt"]:%d/%m/%Y} a {amostras[-1]["_dt"]:%d/%m/%Y}'
    if not amostras:
        corpo.append('<div class="vazio">Ainda não há medidas. Ligue o segundo plano com <code>katharos agendar --frequencia continua</code>: '
                     'ele mede ao iniciar o Windows e a cada 4 horas, sem programa aberto, e este painel passa a mostrar a evolução do PC.</div>')
    else:
        cartoes, figuras = [], []
        for chave, titulo, un, melhor, casas in PAINEL_SERIES:
            s = [(d['_dt'], float(d[chave])) for d in amostras if isinstance(d.get(chave), (int, float))]
            if not s:
                continue
            cartoes.append(f'<div class="cartao"><b>{_e(titulo)}</b><div class="n">{_num(s[-1][1], casas)}<i>{_e(un)}</i></div>'
                           f'<div class="d">{_delta_cartao(s, melhor, casas, un)}</div>{_faisca(s)}</div>')
            if len(s) >= 2:
                figuras.append(f'<figure><figcaption>{_e(titulo)}<span>{_num(min(v for _, v in s), casas)} a {_num(max(v for _, v in s), casas)} {_e(un)}</span></figcaption>'
                               + svg_linha(s, titulo, un, casas, marcas, tendencia=len(s) >= 6 and len(s) < 12, zero=(chave == 'cpu'), suave=len(s) >= 12, destaque=True,
                                           projecao=_proj_painel(chave, s), limite=(85, '85 °C') if chave == 'temperatura' else None) + '</figure>')
        corpo.append('<h2>Agora</h2><div class="cartoes">' + ''.join(cartoes) + '</div>')
        if sugestoes:
            corpo.append('<h2>O que eu proporia</h2><ul class="propostas">' + ''.join(
                f'<li class="{"c-" + {"média": "media"}.get(x["confianca"], x["confianca"])}"><b>{_e(x["titulo"])}</b><p>{_e(x["porque"])}</p>'
                f'<p class="det">Confiança {_e(x["confianca"])}' + (f' · comando <code>katharos {_e(x["comando"])}</code>' if x['comando'] else '')
                + (f' · {_e(x["impacto"])}' if x['impacto'] else '') + '</p>' + link_clique(x['comando'], cliques) + '</li>' for x in sugestoes) + '</ul>'
                '<p class="legenda">Só proponho; nada é aplicado sem você pedir. Cada proposta tem o número que a justifica.'
                + ('' if cliques else ' Quer um botão <b>Corrigir</b> em cada uma? Rode <code>katharos painel --ativar-cliques</code> (registra um link só para o seu usuário; <code>--desativar-cliques</code> remove).')
                + ' Ao clicar, o Katharos abre no comando e você confirma lá.</p>')
        corpo.append('<h2>O que está mudando</h2>')
        if achados:
            corpo.append('<ul class="achados">' + ''.join(f'<li><span class="mau">{_e(t[0].upper() + t[1:])}.</span></li>' for _, t in achados) + '</ul>')
        elif len(amostras) < 6 or (amostras[-1]['_dt'] - amostras[0]['_dt']).days < 3:
            corpo.append('<div class="vazio">Poucas medidas ainda: preciso de pelo menos 6, espalhadas por 3 dias ou mais, para dizer se algo está mudando. Menos que isso seria chute.</div>')
        else:
            corpo.append('<div class="vazio">Nada piorando de forma clara neste período.</div>')
        if resultados:
            corpo.append('<h2>O que aconteceu depois das propostas que você executou</h2><ul class="achados">' + ''.join(
                f'<li><b>{_e(t)}</b> ({q:%d/%m}): {_e(rot)} ' + (f'<span class="{"bom" if ver == "melhorou" else "mau"}">{_num(a, c)} → {_num(b, c)}{(" " + _e(u)) if u else ""}</span>' if ver in ('melhorou', 'piorou')
                                                          else f'<span class="neutro">{_e(ver)}</span>') + '</li>' for t, q, rot, ver, a, b, c, u in resultados) + '</ul>')
        corpo.append(_secao_provas(provas, efeitos))
        if figuras:
            corpo.append('<h2>Evolução</h2><div class="graficos">' + ''.join(figuras) + '</div>')
            leg = ('Linha forte: mediana móvel (tira o ruído); linha clara: cada medida; <span class="mau">pontos vermelhos</span>: valores muito fora do normal desta série; '
                   'linha tracejada: tendência; <span class="mau">linha vermelha pontilhada</span>: projeção ou limite.')
            if marcas:
                leg += ' <span class="m">Linhas verdes pontilhadas</span>: quando você aplicou um pacote do Katharos (passe o mouse).'
            corpo.append(f'<p class="legenda">{leg}</p>')
    if not amostras:
        corpo.append(_secao_provas(provas))
    if ao_vivo is not None:
        corpo.append(_secao_ao_vivo(ao_vivo.get('minutos') or [], ao_vivo.get('sessoes') or []))
    if horas:
        corpo.append(_secao_termica(horas, marcas))
        corpo.append(_secao_consumo(horas, marcas))
    if saude:
        corpo.append(_secao_saude(saude, cliques))
    figs_b = []
    for chave, titulo, un in PAINEL_BENCH:
        s = [(d, float(m[chave])) for d, m in benchs if isinstance(m.get(chave), (int, float))]
        if len(s) >= 2:
            figs_b.append(f'<figure><figcaption>{_e(titulo)}<span>{_e(un)}</span></figcaption>' + svg_linha(s, titulo, un, 0, marcas) + '</figure>')
    if figs_b:
        corpo.append('<h2>Benchmark ao longo do tempo</h2><div class="graficos">' + ''.join(figs_b) + '</div>'
                     '<p class="legenda">Cada ponto é uma rodada do comando <code>benchmark</code>. Oscilação pequena é normal: só vale diferença maior que a variação.</p>')
    if amostras:
        linhas = ''.join('<tr><td>' + f'{d["_dt"]:%d/%m/%Y %H:%M}</td>' + ''.join(f'<td>{_num(d[c], 1) if isinstance(d.get(c), (int, float)) else "-"}</td>' for c, *_ in PAINEL_SERIES) + '</tr>'
                         for d in reversed(amostras[-60:]))
        corpo.append('<details><summary>Ver as medidas em tabela (últimas 60)</summary><table><tr><th>quando</th>'
                     + ''.join(f'<th>{_e(t)}</th>' for _, t, *_ in PAINEL_SERIES) + '</tr>' + linhas + '</table></details>')
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Katharos · painel do PC</title><style>' + PAINEL_CSS + CSS_HORAS + '</style></head><body>'
            f'<h1>Painel do PC<small>{_e(pc)}</small></h1>'
            f'<p class="sub">{_e(periodo) if periodo else "Gráficos gerados pelo Katharos, neste computador. Nada sai do PC."}</p>'
            + ''.join(_com_indice(''.join(corpo))) +
            f'<footer>Katharos {_e(versao)} · arquivo gerado aqui, sem internet e sem scripts: pode apagar quando quiser.</footer></body></html>')


def benchs_para_painel():
    out = []
    for arq in bench_salvos():
        d = le_json(arq, {})
        try:
            quando = datetime.fromisoformat(d.get('quando') or '')
        except (TypeError, ValueError):
            continue
        out.append((quando, {c: v.get('mediana') for c, v in (d.get('medidas') or {}).items() if isinstance(v, dict)}))
    return sorted(out, key=lambda x: x[0])


def provas_para_painel():
    """O que a seção Prova de ganho do painel mostra. Se a leitura falhar, a seção só não aparece."""
    try:
        ens = le_ensaios()
        return {'rodadas': rodadas(ens), 'abertos': ensaios_abertos(ens), 'itens': resumo_itens(le_provas())}
    except Exception as e:
        LOG.escreve(f'provas para o painel: {e!r}')
        return None


def pacotes_para_painel():
    out = []
    for nome, reg in (estado().get('pacotes') or {}).items():
        try:
            if nome in PACOTES and not reg.get('revertido'):
                out.append((datetime.fromisoformat(reg['quando']), PACOTES[nome].titulo))
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(out)


def ferramenta_painel(ctx, args):
    t = ctx.t
    t.aba('gráficos do PC ao longo do tempo, num painel que abre no navegador')
    t.paragrafo('Gera um arquivo HTML neste computador, com gráficos das medidas do segundo plano (espaço, RAM, boot, CPU, temperatura), '
                'dos benchmarks e de quando você aplicou cada pacote. Sem internet, sem programa extra e sem scripts: é só um arquivo que você pode apagar.', 2, 'sub')
    if getattr(args, 'ativar_cliques', False):
        return ativa_cliques(t)
    if getattr(args, 'desativar_cliques', False):
        return desativa_cliques(t)
    if not le_metricas() and WINDOWS and not args.teste:
        amostra_agora(ctx)
    am = le_metricas()
    ev = coleta_evidencias(ctx)
    ev['amostras'] = am
    html_ = monta_painel(am, ev['benchs'], pacotes_para_painel(), analisa_tendencia(am), nome_do_pc(), VERSAO, gera_sugestoes(ev),
                         tabela_efeito(am, ev['pacotes']), resultados_das_propostas(ev), saude=le_saude(), cliques=cliques_ativos(), horas=le_horas(),
                         provas=provas_para_painel(), ao_vivo={'minutos': le_minutos(24), 'sessoes': le_sessoes(60)})
    destino = CASA / 'painel.html'
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html_, encoding='utf-8')
    t.ok(f'Painel gerado: {destino}')
    if not am:
        t.nota('Ainda sem medidas: ligue o segundo plano com "agendar" para o painel ter o que mostrar.')
    if args.teste or getattr(args, 'nao_abrir', False):
        return 0
    try:
        if WINDOWS:
            os.startfile(str(destino))
        else:
            import webbrowser
            webbrowser.open(destino.as_uri())
    except Exception as e:
        t.aviso(f'Não consegui abrir o navegador ({e}). Abra o arquivo acima.')
    return 0
