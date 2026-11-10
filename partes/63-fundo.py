# ─────────────── segundo plano: métricas ao longo do tempo e tendência ───────────────
# A manutenção agendada mede o PC (espaço, boot, RAM, processos...) e grava UMA linha em ~/.katharos/metricas.jsonl: é a medida de
# longo prazo. O tempo real fica com o Katharos.exe. O arquivo tem teto de linhas; passou do teto, as mais antigas saem.
METRICAS_MAX = 1500          # uma medida a cada 4 h dá ~250 dias; ~300 bytes por linha = uns 450 KB no máximo
METRICAS_CHAVES = ('cpu', 'desempenho', 'limite', 'ram_total', 'ram_usada', 'processos', 'servicos', 'inicializacao', 'livre_c', 'temperatura', 'boot_s')


def metricas_arq():
    return CASA / 'metricas.jsonl'


def registra_metrica(m, quando=None, arq=None):
    """Acrescenta uma amostra e apara o arquivo. Devolve a amostra gravada (ou None se não havia o que gravar)."""
    amostra = {k: m[k] for k in METRICAS_CHAVES if isinstance(m.get(k), (int, float))}
    if not amostra:
        return None
    if arq is None:   # a medida do segundo plano também fecha os ensaios da prova de ganho (é ela que roda depois do reinício)
        try:
            fecha_ensaios(m)
        except Exception as e:
            LOG.escreve(f'ensaios não fecharam: {e!r}')
    amostra['t'] = quando or agora_iso()
    arq = Path(arq or metricas_arq())
    arq.parent.mkdir(parents=True, exist_ok=True)
    with open(arq, 'a', encoding='utf-8') as f:
        f.write(json.dumps(amostra, ensure_ascii=False, separators=(',', ':')) + '\n')
    try:
        linhas = arq.read_text(encoding='utf-8', errors='replace').splitlines()
        if len(linhas) > METRICAS_MAX:
            tmp = arq.with_suffix('.tmp')
            tmp.write_text('\n'.join(linhas[-METRICAS_MAX:]) + '\n', encoding='utf-8')
            os.replace(tmp, arq)
    except OSError as e:
        LOG.escreve(f'não consegui aparar as métricas: {e!r}')
    return amostra


def le_metricas(arq=None):
    """Amostras em ordem de data. Linha ilegível é pulada (queda de energia no meio de uma escrita não estraga o resto)."""
    arq = Path(arq or metricas_arq())
    out = []
    try:
        for l in arq.read_text(encoding='utf-8', errors='replace').splitlines():
            try:
                d = json.loads(l)
                d['_dt'] = datetime.fromisoformat(d['t'])
                out.append(d)
            except (ValueError, KeyError, TypeError):
                continue
    except OSError:
        pass
    return sorted(out, key=lambda d: d['_dt'])


def _mediana(v):
    v = sorted(v)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def _serie(amostras, chave):
    return [(a['_dt'], float(a[chave])) for a in amostras if isinstance(a.get(chave), (int, float))]


def _tercos(serie):
    """Mediana do primeiro e do último terço da série (mais estável que comparar dois pontos soltos)."""
    n = len(serie)
    k = max(1, n // 3)
    return _mediana([v for _, v in serie[:k]]), _mediana([v for _, v in serie[-k:]])


def _inclinacao_por_dia(serie):
    """Mínimos quadrados: variação por dia."""
    t0 = serie[0][0]
    xs = [(d - t0).total_seconds() / 86400 for d, _ in serie]
    ys = [v for _, v in serie]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    den = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0


def analisa_tendencia(amostras, minimo=6, dias_minimos=3):
    """Lista de achados [(chave, texto)] só com o que piorou de forma clara. Poucas amostras ou poucos dias = nada (não é tendência, é ruído)."""
    if len(amostras) < minimo or (amostras[-1]['_dt'] - amostras[0]['_dt']).days < dias_minimos:
        return []
    achados = []
    s = _serie(amostras, 'livre_c')
    if len(s) >= minimo:
        por_dia = _inclinacao_por_dia(s)
        atual = _tercos(s)[1]
        if por_dia < -0.5 and atual / -por_dia < 30:
            achados.append(('livre_c', f'o espaço livre em C: está caindo uns {br(-por_dia, 1)} GB por dia; no ritmo atual ({br(atual, 0)} GB livres) acaba em cerca de {int(atual / -por_dia)} dias'))
    s = _serie(amostras, 'boot_s')
    if len(s) >= minimo:
        a, b = _tercos(s)
        if b - a >= 8 and b >= a * 1.2:
            achados.append(('boot_s', f'o boot passou de {br(a, 0)} s para {br(b, 0)} s (mediana do começo e do fim do período)'))
    s = _serie(amostras, 'ram_usada')
    if len(s) >= minimo:
        a, b = _tercos(s)
        if b - a >= 1.5 and b >= a * 1.25:
            achados.append(('ram_usada', f'a RAM em uso subiu de {br(a, 1)} GB para {br(b, 1)} GB (pode ser um programa novo abrindo com o Windows ou um vazamento)'))
    s = _serie(amostras, 'inicializacao')
    if len(s) >= minimo:
        a, b = _tercos(s)
        if b - a >= 3:
            achados.append(('inicializacao', f'os programas que abrem com o Windows passaram de {br(a, 0)} para {br(b, 0)}'))
    s = _serie(amostras, 'temperatura')
    if len(s) >= minimo and _tercos(s)[1] >= 85:
        achados.append(('temperatura', f'a temperatura em repouso está em {br(_tercos(s)[1], 0)} °C: confira ventoinha, poeira e pasta térmica'))
    s = _serie(amostras, 'cpu')
    if len(s) >= minimo:
        a, b = _tercos(s)
        if b >= 20 and b >= a * 2:
            achados.append(('cpu', f'o uso de CPU em repouso passou de {br(a, 0)}% para {br(b, 0)}%: algo novo está rodando sem parar'))
    return achados


def amostra_agora(ctx):
    """Mede o PC (leve) e grava a amostra. Roda dentro da manutenção em segundo plano e no 'tendencia --agora'."""
    if not WINDOWS:
        return None
    s = roda_ps(ctx.t, MEDIDAS_PS, 'metrica', minutos=2, mostra=False)
    return registra_metrica(s.dados.get('medidas') or {})


def ferramenta_tendencia(ctx, args):
    t = ctx.t
    t.aba('o PC está piorando com o tempo? (usa as medidas do segundo plano)')
    t.paragrafo('Cada vez que o segundo plano roda, o Katharos grava uma medida pequena (RAM, CPU, espaço, boot, temperatura). Aqui você vê '
                'se algo está mudando de forma clara. Pouca medida ou poucos dias não é tendência: o programa diz isso em vez de chutar.', 2, 'sub')
    if getattr(args, 'agora', False) or (not le_metricas() and WINDOWS and not args.teste):
        if amostra_agora(ctx):
            t.nota('  medida de agora gravada.')
    am = le_metricas()
    if not am:
        t.nota('Ainda não há medidas. Ligue o segundo plano com "agendar" (a opção contínua mede ao iniciar o Windows e a cada 4 h).')
        return 0
    dias = (am[-1]['_dt'] - am[0]['_dt']).days
    t.chaves([('medidas', str(len(am))), ('período', f'{dias} dia(s), de {am[0]["_dt"]:%d/%m} a {am[-1]["_dt"]:%d/%m}')])
    linhas = []
    for chave, rot, un, _ in LINHAS_MEDIDA:
        s = _serie(am, chave)
        if len(s) >= 2:
            a, b = _tercos(s)
            linhas.append([rot, _fmt_medida(a, un), _fmt_medida(b, un), sparkline_txt([v for _, v in s], getattr(args, 'ascii', False))])
    if linhas:
        t.titulo('começo e fim do período (mediana)')
        t.tabela(['medida', 'começo', 'fim', 'evolução'], linhas, alinha='eddd')
        t.nota('  O painel com gráficos de verdade: comando "painel".')
    achados = analisa_tendencia(am)
    t.titulo('o que está mudando')
    if achados:
        for _, txt in achados:
            t.aviso(txt[0].upper() + txt[1:] + '.')
    elif len(am) < 6 or dias < 3:
        t.nota('  Poucas medidas ainda (preciso de pelo menos 6, espalhadas por 3 dias ou mais).')
    else:
        t.ok('Nada piorando de forma clara.')
    return 0


def avisa_tendencia(ctx, e):
    """Dentro da manutenção: grava a amostra e devolve os alertas novos (cada achado só volta a avisar depois de 7 dias)."""
    try:
        amostra_agora(ctx)
        vistos = e.setdefault('tendencia_avisos', {})
        novos = []
        for chave, txt in analisa_tendencia(le_metricas()):
            if not recente_h(vistos.get(chave), 24 * 7):
                novos.append(txt[0].upper() + txt[1:])
                vistos[chave] = agora_iso()
        return novos
    except Exception as ex:  # métrica nunca derruba a manutenção
        LOG.escreve(f'tendência falhou: {ex!r}')
        return []


# ─────────────── análise "inteligente" das séries (usada pelo painel e testável sem desenhar nada) ───────────────

def mediana_movel(serie, janela=7):
    """Suaviza uma série [(t, v)] com a mediana dos últimos `janela` pontos (resistente a picos, ao contrário da média)."""
    out = []
    for i, (d, _) in enumerate(serie):
        trecho = [v for _, v in serie[max(0, i - janela + 1):i + 1]]
        out.append((d, _mediana(trecho)))
    return out


def anomalias(serie, limite=3.5, minimo=12):
    """Pontos muito fora do normal da própria série (escore robusto por MAD). Poucos pontos ou série sem variação = nenhum."""
    if len(serie) < minimo:
        return []
    v = [x for _, x in serie]
    med = _mediana(v)
    mad = _mediana([abs(x - med) for x in v])
    if mad < 1e-9:
        return []
    return [(d, x) for d, x in serie if 0.6745 * abs(x - med) / mad > limite]


def efeito_antes_depois(serie, quando, melhor='menor', janela_dias=7, minimo=4):
    """Compara a série nos `janela_dias` antes e depois de `quando`. Devolve (veredito, antes, depois):
    'melhorou' / 'piorou' só se a mudança for maior que o ruído das duas janelas (MAD) e passar de 5%;
    'já vinha mudando' se a série já andava nessa direção ANTES (então não dá para atribuir ao que foi feito);
    'sem diferença mensurável' se for oscilação; 'poucas medidas' se faltar amostra de um dos lados."""
    from datetime import timedelta
    pares_antes = [(d, v) for d, v in serie if quando - timedelta(days=janela_dias) <= d < quando]
    antes = [v for _, v in pares_antes]
    depois = [v for d, v in serie if quando <= d < quando + timedelta(days=janela_dias)]
    if len(antes) < minimo or len(depois) < minimo:
        return 'poucas medidas', None, None
    a, b = _mediana(antes), _mediana(depois)
    ruido = max(_mediana([abs(x - a) for x in antes]), _mediana([abs(x - b) for x in depois]))
    dif = b - a
    if abs(dif) <= 2 * ruido or abs(dif) < 0.05 * max(abs(a), 1e-9):
        return 'sem diferença mensurável', a, b
    previa = _inclinacao_por_dia(pares_antes) * janela_dias   # quanto a série já mudaria em 7 dias só pela inclinação de antes
    if previa * dif > 0 and abs(previa) >= 0.5 * abs(dif):
        return 'já vinha mudando', a, b
    bom = (dif < 0) == (melhor == 'menor')
    return ('melhorou' if bom else 'piorou'), a, b


def projecao_enchimento(serie, minimo=6):
    """(dias até chegar a 0, data) se o espaço livre vem caindo de forma consistente; None caso contrário."""
    from datetime import timedelta
    if len(serie) < minimo:
        return None
    por_dia = _inclinacao_por_dia(serie)
    atual = _tercos(serie)[1]
    if por_dia >= -0.3 or atual <= 0:
        return None
    dias = atual / -por_dia
    return (dias, serie[-1][0] + timedelta(days=dias)) if dias < 120 else None
