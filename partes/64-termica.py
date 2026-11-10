# ─────────────── painel: temperatura em janela longa e consumo (a partir das linhas por hora) ───────────────
CSS_HORAS = '''
.banda{fill:var(--ambar);opacity:.22}.linha-b{fill:none;stroke:var(--verde);stroke-width:2;stroke-linejoin:round}.linha-c{fill:none;stroke:var(--ambar);stroke-width:2;stroke-linejoin:round}
.leg{display:flex;flex-wrap:wrap;gap:14px;font:12px var(--mono);color:var(--apagado);margin:6px 0 0}.leg i{display:inline-block;width:18px;height:3px;vertical-align:middle;margin-right:6px;background:var(--ambar)}
.leg i.v{background:var(--verde)}.leg i.b{height:10px;opacity:.35}
.q0{fill:var(--linha)}.q1{fill:var(--ambar);opacity:.28}.q2{fill:var(--ambar);opacity:.55}.q3{fill:var(--ambar);opacity:.95}.q4{fill:var(--verm);opacity:.7}.q5{fill:var(--verm)}
.barra{fill:var(--ambar);opacity:.85}.barra.pico{fill:var(--verm)}.celula:hover{stroke:var(--osso);stroke-width:1}
ul.rank{list-style:none;display:grid;gap:6px;font:13px var(--mono);margin-top:8px}ul.rank li{display:grid;grid-template-columns:minmax(90px,200px) 1fr auto;gap:10px;align-items:center}
ul.rank .tr{height:8px;background:var(--linha)}ul.rank .tr b{display:block;height:100%;background:var(--ambar)}ul.rank span{color:var(--apagado)}
'''
CORES_CALOR = [(50, 'q0'), (60, 'q1'), (70, 'q2'), (80, 'q3'), (90, 'q4')]


def _classe_calor(v):
    for lim, c in CORES_CALOR:
        if v < lim:
            return c
    return 'q5'


def svg_multi(titulo, un, casas, banda=None, linhas=(), limites=(), marcas=(), largura=560, altura=200):
    """Gráfico de tempo com faixa (mín–máx) e várias linhas. banda: [(dt, lo, hi)]; linhas: [([(dt, v)], classe_css, rotulo)]; limites: [(valor, rótulo)]."""
    ml, mr, mt, mb = 46, 14, 14, 26
    w, h = largura - ml - mr, altura - mt - mb
    pontos = [(d, v) for serie, *_ in linhas for d, v in serie] + [(d, v) for d, lo, hi in (banda or []) for v in (lo, hi)]
    if len(pontos) < 2:
        return f'<svg viewBox="0 0 {largura} {altura}" role="img" aria-label="{_e(titulo)}: sem dados"></svg>'
    t0, t1 = min(d for d, _ in pontos), max(d for d, _ in pontos)
    span = max((t1 - t0).total_seconds(), 1.0)
    lo, hi = _escala(min(v for _, v in pontos), max(v for _, v in pontos))
    for lim, _ in limites:
        if lim > hi:
            hi = lim + (hi - lo) * 0.08

    def x(d):
        return ml + (d - t0).total_seconds() / span * w

    def y(v):
        return mt + h - (v - lo) / (hi - lo) * h
    out = [f'<svg viewBox="0 0 {largura} {altura}" role="img" aria-label="{_e(titulo)}, de {t0:%d/%m/%Y} a {t1:%d/%m/%Y}" class="grafico">']
    for v in _ticks(lo, hi, inteiro=casas == 0):
        out.append(f'<line x1="{ml}" x2="{ml + w}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="grade"/><text x="{ml - 6}" y="{y(v) + 4:.1f}" class="eixo" text-anchor="end">{_num(v, casas)}</text>')
    out.append(f'<text x="{ml}" y="{altura - 6}" class="eixo">{t0:%d/%m}</text><text x="{ml + w}" y="{altura - 6}" class="eixo" text-anchor="end">{t1:%d/%m}</text>')
    for lim, rot in limites:
        if lo <= lim <= hi:
            out.append(f'<line x1="{ml}" x2="{ml + w}" y1="{y(lim):.1f}" y2="{y(lim):.1f}" class="limite"/><text x="{ml + w}" y="{y(lim) - 4:.1f}" class="rotulo-limite" text-anchor="end">{_e(rot)}</text>')
    for d, rot in marcas:
        if t0 <= d <= t1:
            out.append(f'<line x1="{x(d):.1f}" x2="{x(d):.1f}" y1="{mt}" y2="{mt + h}" class="marca"><title>{_e(rot)} ({d:%d/%m})</title></line>')
    if banda and len(banda) > 1:
        cima = ' '.join(f'{x(d):.1f},{y(b):.1f}' for d, a, b in banda)
        baixo = ' '.join(f'{x(d):.1f},{y(a):.1f}' for d, a, b in reversed(banda))
        out.append(f'<polygon points="{cima} {baixo}" class="banda"/>')
    for i, (serie, classe, rot) in enumerate(linhas):
        if len(serie) > 1:
            out.append(f'<polyline points="{" ".join(f"{x(d):.1f},{y(v):.1f}" for d, v in serie)}" class="{classe}"/>')
        if serie:
            d, v = serie[-1]
            out.append(f'<circle cx="{x(d):.1f}" cy="{y(v):.1f}" r="3.5" class="ponto"/>')
        for d, v in serie:   # passar o mouse mostra o dia e o valor
            out.append(f'<circle cx="{x(d):.1f}" cy="{y(v):.1f}" r="6" class="alvo"><title>{d:%d/%m/%Y}: {_e(rot)} {_num(v, casas)} {_e(un)}</title></circle>')
    out.append('</svg>')
    return ''.join(out)


def svg_calor(horas, dias=28, largura=560):
    """Mapa de calor: uma linha por dia (o mais recente embaixo), uma coluna por hora; a cor é a temperatura máxima daquela hora."""
    com = [b for b in horas if b.get('tn')]
    if not com:
        return ''
    fim = max(b['_dt'] for b in com).date()
    ini = fim - timedelta(days=dias - 1)
    cel = {(b['_dt'].date(), b['_dt'].hour): b for b in com if ini <= b['_dt'].date() <= fim}
    ml, mt, cw, ch = 40, 6, (largura - 40 - 8) / 24, 12
    altura = mt + dias * ch + 22
    out = [f'<svg viewBox="0 0 {largura} {altura:.0f}" role="img" aria-label="Mapa de calor da temperatura máxima por hora e por dia" class="grafico">']
    for i in range(dias):
        dia = ini + timedelta(days=i)
        if i % 7 == 0 or i == dias - 1:
            out.append(f'<text x="{ml - 6}" y="{mt + i * ch + 10}" class="eixo" text-anchor="end">{dia:%d/%m}</text>')
        for hh in range(24):
            b = cel.get((dia, hh))
            cx, cy = ml + hh * cw, mt + i * ch
            if b:
                out.append(f'<rect x="{cx:.1f}" y="{cy}" width="{cw - 1:.1f}" height="{ch - 1}" class="celula {_classe_calor(b["tx"])}"><title>{dia:%d/%m} {hh:02d}h: máxima {_num(b["tx"], 0)} °C</title></rect>')
            else:
                out.append(f'<rect x="{cx:.1f}" y="{cy}" width="{cw - 1:.1f}" height="{ch - 1}" fill="none" stroke="var(--linha)" stroke-width=".5"/>')
    for hh in (0, 6, 12, 18):
        out.append(f'<text x="{ml + hh * cw:.1f}" y="{altura - 6:.0f}" class="eixo">{hh:02d}h</text>')
    out.append('</svg>')
    return ''.join(out)


def svg_barras24(valores, titulo, un, casas=0, pico=None, largura=560, altura=170):
    """24 barras, uma por hora do dia. valores: lista de 24 números ou None."""
    ml, mr, mt, mb = 40, 8, 10, 24
    w, h = largura - ml - mr, altura - mt - mb
    v = [x for x in valores if x is not None]
    if not v:
        return ''
    hi = max(max(v) * 1.1, 1e-9)
    bw = w / 24
    out = [f'<svg viewBox="0 0 {largura} {altura}" role="img" aria-label="{_e(titulo)} por hora do dia" class="grafico">']
    for t in _ticks(0, hi, inteiro=casas == 0):
        yy = mt + h - t / hi * h
        out.append(f'<line x1="{ml}" x2="{ml + w}" y1="{yy:.1f}" y2="{yy:.1f}" class="grade"/><text x="{ml - 6}" y="{yy + 4:.1f}" class="eixo" text-anchor="end">{_num(t, casas)}</text>')
    for i, val in enumerate(valores):
        if val is None:
            continue
        bh = val / hi * h
        cls = 'barra pico' if pico is not None and val >= pico else 'barra'
        out.append(f'<rect x="{ml + i * bw + 1:.1f}" y="{mt + h - bh:.1f}" width="{bw - 2:.1f}" height="{bh:.1f}" class="{cls}"><title>{i:02d}h: {_num(val, casas)} {_e(un)}</title></rect>')
    for hh in (0, 6, 12, 18):
        out.append(f'<text x="{ml + hh * bw:.1f}" y="{altura - 6}" class="eixo">{hh:02d}h</text>')
    out.append('</svg>')
    return ''.join(out)


def _por_hora_do_dia(horas, pref):
    """Média de um valor por hora do dia (0 a 23), ponderada pelo número de amostras."""
    s, n = [0.0] * 24, [0] * 24
    for b in horas:
        if b.get(pref + 'n'):
            s[b['_dt'].hour] += b[pref + 's']
            n[b['_dt'].hour] += b[pref + 'n']
    return [(s[i] / n[i]) if n[i] >= 3 else None for i in range(24)]


def _cartao(rotulo, valor, un='', nota=''):
    return f'<div class="cartao"><b>{_e(rotulo)}</b><div class="n">{_e(valor)}<i>{_e(un)}</i></div><div class="d neutro">{_e(nota)}</div></div>'


def _fig(titulo, direita, svg, legenda=''):
    return f'<figure><figcaption>{_e(titulo)}<span>{_e(direita)}</span></figcaption>{svg}{legenda}</figure>'


def _secao_termica(horas, marcas=()):
    if len(horas) < 3:
        return ''
    an = analisa_termica(horas)
    cab = '<h2>Temperatura</h2>'
    if not an:
        return (cab + '<div class="vazio">O Windows deste PC não entrega a temperatura sem um programa de terceiros (acontece em muitos desktops): a leitura vem da zona térmica '
                'do ACPI, e aqui ela não apareceu. O Katharos não instala driver de sensor, para não mexer onde um anti-cheat olha. '
                'O consumo abaixo continua sendo medido.</div>')
    n_dias = an['dias']
    ini, fim = horas[0]['_dt'], horas[-1]['_dt']
    partes = [cab, f'<p class="sub">{an["horas"]} horas com leitura em {n_dias} dias (de {ini:%d/%m/%Y} a {fim:%d/%m/%Y}). Leitura da zona térmica do sistema, '
                   'não o sensor de cada núcleo: serve para ver tendência e calor demais, não para comparar com outro PC.</p>']
    cart = [_cartao('Máxima', _num(an['maxima'], 0), '°C', f'em {an["maxima_quando"]:%d/%m %H}h')]
    if an['media_repouso'] is not None:
        cart.append(_cartao('Em repouso (CPU < 15%)', _num(an['media_repouso'], 0), '°C', 'média'))
    if an['media_carga'] is not None:
        cart.append(_cartao('Sob carga (CPU ≥ 50%)', _num(an['media_carga'], 0), '°C', 'média'))
    cart.append(_cartao('Horas acima de 80 °C', f'{an["horas_atencao"]}', f'de {an["horas"]}', f'{_num(an["horas_atencao"] / an["horas"] * 100, 0)}% do tempo medido'))
    partes.append('<div class="cartoes">' + ''.join(cart) + '</div>')
    if an['achados']:
        partes.append('<ul class="achados" style="margin-top:14px">' + ''.join(f'<li><span class="{"mau" if g == "alta" else "neutro"}">{_e(t[0].upper() + t[1:])}.</span></li>' for g, t in an['achados']) + '</ul>')
    figs = []
    dia_t = serie_diaria(horas, 't')
    if len(dia_t) >= 2:
        figs.append(_fig('Temperatura por dia', 'faixa mín–máx e média',
                         svg_multi('Temperatura por dia', '°C', 0, banda=[(d, a, c) for d, a, _m, c in dia_t], linhas=[([(d, m) for d, _a, m, _c in dia_t], 'linha-c', 'média')],
                                   limites=[(80, '80 °C')], marcas=marcas),
                         '<div class="leg"><span><i></i>média do dia</span><span><i class="b"></i>do mínimo ao máximo</span></div>'))
    rep, car = serie_diaria_simples(horas, 'trs', 'trn'), serie_diaria_simples(horas, 'tcs', 'tcn')
    if len(rep) >= 3 and len(car) >= 3:
        figs.append(_fig('Em repouso e sob carga', 'média por dia',
                         svg_multi('Em repouso e sob carga', '°C', 0, linhas=[(rep, 'linha-b', 'em repouso'), (car, 'linha-c', 'sob carga')], marcas=marcas),
                         '<div class="leg"><span><i class="v"></i>em repouso</span><span><i></i>sob carga</span></div>'))
    elif len(rep) >= 3:
        figs.append(_fig('Temperatura em repouso', 'média por dia', svg_multi('Temperatura em repouso', '°C', 0, linhas=[(rep, 'linha-b', 'em repouso')], marcas=marcas)))
    calor = svg_calor(horas)
    if calor and an['dias'] >= 3:
        figs.append(_fig('Quando esquenta', 'máxima por hora, últimos 28 dias', calor,
                         '<div class="leg"><span>cada quadrado é uma hora; cor mais forte é mais quente: abaixo de 50 °C, 60, 70, 80, 90 e acima</span></div>'))
    hora_t = _por_hora_do_dia(horas, 't')
    if sum(x is not None for x in hora_t) >= 6:
        figs.append(_fig('Temperatura média por hora do dia', '°C', svg_barras24(hora_t, 'Temperatura média', '°C', 0, pico=80)))
    if an['tem_gpu']:
        dia_g = serie_diaria(horas, 'g')
        if len(dia_g) >= 2:
            figs.append(_fig('Placa de vídeo NVIDIA', 'faixa mín–máx e média (fora de jogo)',
                             svg_multi('Temperatura da placa de vídeo', '°C', 0, banda=[(d, a, c) for d, a, _m, c in dia_g], linhas=[([(d, m) for d, _a, m, _c in dia_g], 'linha-c', 'média')], limites=[(83, '83 °C')], marcas=marcas),
                             '<p class="legenda">Esta leitura só é feita com nenhum jogo aberto, de propósito: com um jogo aberto o Katharos não chama a ferramenta da placa.</p>'))
    partes.append('<div class="graficos" style="margin-top:14px">' + ''.join(figs) + '</div>')
    partes.append('<p class="legenda">A temperatura do ambiente muda com a estação e com o dia: uma subida lenta pode ser clima. Só chamo de problema o que passa do limite, '
                  'ou o que sobe muito além da oscilação normal em repouso. Linhas verdes pontilhadas: quando você aplicou um pacote.</p>')
    return ''.join(partes)


def _rank_html(contagem, titulo, nota):
    tot = sum(contagem.values())
    if tot < 5:
        return ''
    itens = sorted(contagem.items(), key=lambda kv: -kv[1])[:6]
    mx = itens[0][1]
    lis = ''.join(f'<li><b>{_e(n)}</b><div class="tr"><b style="width:{c / mx * 100:.0f}%"></b></div><span>{c / tot * 100:.0f}%</span></li>' for n, c in itens)
    return f'<h3>{_e(titulo)}</h3><ul class="rank">{lis}</ul><p class="legenda">{_e(nota)}</p>'


def _secao_consumo(horas, marcas=()):
    if len(horas) < 3:
        return ''
    n_am = sum(b.get('n', 0) for b in horas)
    cart = []
    c = [(b['cs'], b['cn']) for b in horas if b.get('cn')]
    r = [(b['rs'], b['rn']) for b in horas if b.get('rn')]
    d = [(b['ds'], b['dn']) for b in horas if b.get('dn')]
    u = [(b['us'], b['un']) for b in horas if b.get('un')]
    if c:
        cart.append(_cartao('CPU média', _num(sum(s for s, _ in c) / sum(n for _, n in c), 0), '%'))
    if r:
        cart.append(_cartao('RAM média', _num(sum(s for s, _ in r) / sum(n for _, n in r), 0), '%'))
    if d:
        cart.append(_cartao('Disco ocupado, média', _num(sum(s for s, _ in d) / sum(n for _, n in d), 0), '%'))
    if u:
        cart.append(_cartao('Placa de vídeo (3D), média', _num(sum(s for s, _ in u) / sum(n for _, n in u), 0), '%'))
    jg = sum(b.get('jg', 0) for b in horas)
    if jg:
        cart.append(_cartao('Leituras com jogo aberto', f'{jg}', f'de {n_am}', f'{_num(jg / n_am * 100, 0)}% do tempo'))
    desc = _descarga(horas)
    if desc:
        cart.append(_cartao('Descarga na bateria', _num(desc, 0), '% por hora', 'média nas horas só na bateria'))
    if not cart:
        return ''
    partes = ['<h2>Consumo</h2>', f'<p class="sub">{n_am} leituras de 15 em 15 minutos, enquanto você usa o PC, jogos incluídos. Só números do sistema: não olho dentro de nenhum jogo.</p>',
              '<div class="cartoes">' + ''.join(cart) + '</div>']
    figs = []
    ph = _por_hora_do_dia(horas, 'c')
    if sum(x is not None for x in ph) >= 6:
        figs.append(_fig('CPU por hora do dia', '% médio', svg_barras24(ph, 'CPU média', '%', 0, pico=80)))
    pr = _por_hora_do_dia(horas, 'r')
    if sum(x is not None for x in pr) >= 6:
        figs.append(_fig('RAM por hora do dia', '% médio', svg_barras24(pr, 'RAM média', '%', 0, pico=90)))
    dia_c = serie_diaria(horas, 'c')
    if len(dia_c) >= 3:
        figs.append(_fig('CPU por dia', 'faixa e média', svg_multi('CPU por dia', '%', 0, banda=[(dd, a, cc) for dd, a, _m, cc in dia_c], linhas=[([(dd, m) for dd, _a, m, _c in dia_c], 'linha-c', 'média')], marcas=marcas)))
    dia_r = serie_diaria(horas, 'r')
    if len(dia_r) >= 3:
        figs.append(_fig('RAM por dia', 'faixa e média', svg_multi('RAM por dia', '%', 0, banda=[(dd, a, cc) for dd, a, _m, cc in dia_r], linhas=[([(dd, m) for dd, _a, m, _c in dia_r], 'linha-c', 'média')], marcas=marcas)))
    if figs:
        partes.append('<div class="graficos" style="margin-top:14px">' + ''.join(figs) + '</div>')
    top, topr = {}, {}
    for b in horas:
        for chave, dest in (('top', top), ('topr', topr)):
            for nome, q in (b.get(chave) or {}).items():
                dest[nome] = dest.get(nome, 0) + q
    partes.append(_rank_html(top, 'Quem mais pesou na CPU', 'Maior consumidor de CPU (acima de 5%) em cada leitura feita fora de jogo. Durante um jogo o Katharos não olha processos.'))
    partes.append(_rank_html(topr, 'Quem mais ocupou RAM', 'Maior ocupante de RAM em cada leitura feita fora de jogo.'))
    return ''.join(partes)


def _descarga(horas):
    """% de bateria por hora, só nas horas em que todas as leituras foram na bateria e a carga caiu (descarta carregamento e horas mistas)."""
    taxas = [b['b0'] - b['b1'] for b in horas if b.get('bn', 0) >= 3 and b['bn'] == b.get('n') and 'b0' in b and b['b0'] > b['b1']]
    if len(taxas) < 4:
        return None
    return _mediana(taxas)
