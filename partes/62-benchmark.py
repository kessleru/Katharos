

# ─────────────── benchmark: provar o ganho com número, sem enganar ───────────────
# Regra: só declara melhora ou piora quando a diferença é maior que a variação das próprias medidas.

REPETICOES = {'rapido': 4, 'completo': 6}   # a primeira rodada é descartada (cache frio ou quente muda tudo)
LINHAS_BENCH = [
    ('disco_escrita', 'disco: escrita sequencial', 'MB/s', 'maior'),
    ('disco_4k', 'disco: escritas pequenas (4K, com flush)', 'ops/s', 'maior'),
    ('cpu', 'CPU: um núcleo (hash)', 'MB/s', 'maior'),
    ('cpu_multi', 'CPU: todos os núcleos (hash)', 'MB/s', 'maior'),
    ('ram', 'RAM: cópia de memória', 'MB/s', 'maior'),
]


def estatistica(medidas):
    """{n, mediana, minimo, maximo, amplitude} de uma lista de medidas (precisa de pelo menos uma)."""
    v = sorted(float(x) for x in medidas)
    n = len(v)
    meio = v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2
    return {'n': n, 'mediana': meio, 'minimo': v[0], 'maximo': v[-1], 'amplitude': v[-1] - v[0]}


def compara_bench(antes, depois, melhor='maior'):
    """Compara duas estatísticas. Devolve (veredito, variação em %): 'melhorou', 'piorou' ou 'sem diferença mensurável'
    (também quando há menos de 3 medidas de cada lado, porque aí não dá para saber o que é ruído)."""
    if min(antes['n'], depois['n']) < 3 or not antes['mediana']:
        return 'poucas repetições para comparar', 0.0
    dif = depois['mediana'] - antes['mediana']
    pct = dif / antes['mediana'] * 100
    ruido = max(antes['amplitude'], depois['amplitude'])
    if abs(dif) <= ruido:
        return 'sem diferença mensurável', pct
    bom = dif > 0 if melhor == 'maior' else dif < 0
    return ('melhorou' if bom else 'piorou'), pct


def _mede(fn, reps):
    """Roda fn() reps vezes, descarta a primeira, devolve a estatística das demais."""
    vals = [fn() for _ in range(reps)]
    return estatistica(vals[1:] if len(vals) > 2 else vals)


def bench_cpu(mb=48):
    import hashlib as _h
    bloco = bytes(range(256)) * 4096       # 1 MB
    t0 = time.perf_counter()
    h = _h.sha256()
    for _ in range(mb):
        h.update(bloco)
    return mb / (time.perf_counter() - t0)


def bench_cpu_multi(mb=24):
    """Todos os núcleos ao mesmo tempo: cada thread faz o hash do seu bloco (o hashlib solta o GIL em blocos grandes)."""
    import hashlib as _h
    from concurrent.futures import ThreadPoolExecutor
    n = max(1, min(os.cpu_count() or 1, 32))
    bloco = bytes(range(256)) * 4096

    def trabalho(_):
        h = _h.sha256()
        for _ in range(mb):
            h.update(bloco)
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=n) as ex:
        list(ex.map(trabalho, range(n)))
    return n * mb / (time.perf_counter() - t0)


def instavel(e, limite=0.15):
    """True quando as rodadas variaram mais de 15% da mediana: PC ocupado, esquentando ou com economia de energia mexendo no clock."""
    return bool(e and e.get('mediana') and e['amplitude'] / e['mediana'] > limite)


def bench_ram(mb=64):
    origem = bytearray(mb * 2**20)
    t0 = time.perf_counter()
    destino = bytes(origem)               # cópia de verdade, mb megabytes
    dt = time.perf_counter() - t0
    del destino
    return mb / dt if dt > 0 else 0.0


def bench_disco_escrita(arq, mb=64):
    bloco = os.urandom(2**20)
    t0 = time.perf_counter()
    with open(arq, 'wb') as f:
        for _ in range(mb):
            f.write(bloco)
        f.flush()
        os.fsync(f.fileno())
    return mb / (time.perf_counter() - t0)


def bench_disco_4k(arq, ops=200):
    bloco = os.urandom(4096)
    t0 = time.perf_counter()
    with open(arq, 'wb') as f:
        for _ in range(ops):
            f.write(bloco)
            f.flush()
            os.fsync(f.fileno())
    return ops / (time.perf_counter() - t0)


def roda_bench(t, rapido=True, leve=False, pasta_tmp=None, multi=False):
    """Roda os testes e devolve {chave: estatística}. O arquivo temporário é apagado em qualquer caso."""
    reps = REPETICOES['rapido' if rapido else 'completo']
    mb = 16 if leve else 64
    tmp = Path(pasta_tmp or (CASA / 'bench'))
    tmp.mkdir(parents=True, exist_ok=True)
    arq = tmp / 'teste.bin'
    out = {}
    try:
        etapas = [('cpu', lambda: bench_cpu(16 if leve else 48)),
                  ('ram', lambda: bench_ram(mb)),
                  ('disco_escrita', lambda: bench_disco_escrita(arq, mb)),
                  ('disco_4k', lambda: bench_disco_4k(arq, 100 if leve else 200))]
        if multi:   # só com --completo: todos os núcleos a 100% por alguns segundos é o mais perto de um teste de estresse que o programa chega
            etapas.insert(1, ('cpu_multi', lambda: bench_cpu_multi(8 if leve else 24)))
        for chave, fn in etapas:
            rotulo = next(l[1] for l in LINHAS_BENCH if l[0] == chave)
            with Progresso(t, None, rotulo) as pr:
                out[chave] = _mede(fn, reps)
    finally:
        try:
            arq.unlink()
        except OSError:
            pass
    return out


def bench_salvos():
    return sorted(pasta('benchmarks').glob('*.json'))


def mostra_bench(t, atual, antes=None, rotulo_antes=''):
    t.titulo('resultado' if antes is None else f'comparado com {rotulo_antes}')
    for chave, nome, un, melhor in LINHAS_BENCH:
        e = atual.get(chave)
        if not e:
            continue
        linha = f'{nome:<42} {e["mediana"]:>9.0f} {un}  (de {e["minimo"]:.0f} a {e["maximo"]:.0f})'
        if antes and chave in antes:
            v, pct = compara_bench(antes[chave], e, melhor)
            cor = {'melhorou': 'verde', 'piorou': 'pessego'}.get(v, 'apagado')
            linha += '  ' + t.p(f'{v}' + (f' ({pct:+.0f}%)' if v in ('melhorou', 'piorou') else ''), cor)
        if instavel(e):
            linha += '  ' + t.p('medida instável', 'pessego')
        t.escreve('  ' + linha)
    if atual.get('cpu') and atual.get('cpu_multi') and atual['cpu']['mediana'] > 0:
        t.escreve('  ' + t.p(f'os núcleos juntos fizeram {atual["cpu_multi"]["mediana"] / atual["cpu"]["mediana"]:.1f}x o trabalho de um (núcleos lógicos: {os.cpu_count()})', 'apagado'))
    if any(instavel(atual.get(c)) for c, *_ in LINHAS_BENCH):
        t.escreve('  ' + t.p('Linhas "instáveis" variaram mais de 15% entre as rodadas: feche programas, ligue na tomada e rode de novo; comparar com elas não vale.', 'apagado'))
    t.escreve()


def pc_apertado(p):
    """Motivo (texto) para usar a versão leve do benchmark, ou ''. Em PC com pouca RAM livre ou HD, o teste pesado
    competiria com o próprio Windows e a medida sairia falseada."""
    try:
        ram = (p or {}).get('ram') or {}
        total, usada = float(ram.get('total') or 0), float(ram.get('usada') or 0)
        if total and total <= 4:
            return f'só {br(total, 0)} GB de RAM'
        if total and total - usada < 1.5:
            return f'só {br(total - usada, 1)} GB de RAM livre agora'
        if ((p or {}).get('disco') or {}).get('tipo') == 'HDD':
            return 'o disco é um HD'
    except (TypeError, ValueError):
        pass
    return ''


def bateria_fraca(ctx):
    """Notebook na bateria com menos de 30%? O teste gasta bateria e a CPU pode baixar o clock, o que falsearia a medida."""
    if not WINDOWS:
        return False
    corpo = ("$b = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Select-Object -First 1\n"
             "if ($b) { Dado 'bateria' @{ carga = [int]$b.EstimatedChargeRemaining; ligada = ([int]$b.BatteryStatus -ne 1) } }")
    s = roda_ps(ctx.t, corpo, 'bateria', minutos=1, mostra=False)
    d = s.dados.get('bateria') or {}
    return bool(d) and not d.get('ligada') and (d.get('carga') or 100) < 30


def ferramenta_benchmark(ctx, args):
    t = ctx.t
    rapido = not getattr(args, 'completo', False)
    t.aba('mede disco, CPU e RAM com repetição e diz se a diferença é real')
    t.paragrafo('Meça com o PC parado e sem programas abertos, antes e depois de aplicar algo. O programa repete cada teste, '
                'descarta a primeira rodada e só diz "melhorou" ou "piorou" quando a diferença é maior que a variação das próprias '
                'medidas. É um teste leve (cerca de 1 minuto), não um teste de estresse: não leva a CPU ao limite nem esquenta o PC. '
                'Os arquivos de teste ficam em ~/.katharos/bench e são apagados no fim. Nada sai do PC.', 2, 'sub')
    if args.teste:
        t.item('○', 'azul', f'{REPETICOES["rapido" if rapido else "completo"]} rodadas de 5 testes, até 64 MB no disco', recuo=2, cor_nome='sub')
        return 0
    if not exige_espaco(t, 'bench', 'benchmark'):
        return 1
    if bateria_fraca(ctx):
        t.aviso('O notebook está na bateria com menos de 30%. Ligue na tomada e rode de novo: o teste gasta bateria e a CPU baixaria o clock, o que falsearia a medida.')
        return 1
    ok, gb, _ = espaco_ok('bench')
    leve = bool(gb and gb < 5)
    if leve:
        t.nota('  Pouco espaço livre: usando a versão leve (arquivos menores).')
    apertado = pc_apertado(perfil_pc(ctx))
    if apertado and not leve:
        leve = True
        t.nota(f'  Modo leve do teste ({apertado}): arquivos menores e uma etapa de cada vez.')
    t.escreve()
    atual = roda_bench(t, rapido=rapido, leve=leve, multi=not rapido)
    salvos = bench_salvos()
    antes = le_json(salvos[-1], {}).get('medidas') if salvos else None
    quando = salvos[-1].stem[:16].replace('_', ' ') if salvos else ''
    mostra_bench(t, atual, antes, 'o benchmark anterior (' + quando + ')' if antes else '')
    dados = {'versao': VERSAO, 'quando': agora_iso(), 'pc': nome_do_pc(), 'leve': leve, 'medidas': atual,
             'perfil_aplicado': (estado().get('perfil') or '')}
    grava_json(pasta('benchmarks') / f'{datetime.now():%Y-%m-%d_%H-%M-%S}.json', dados)
    try:
        rel_secao('benchmark', {k: round(v['mediana'], 1) for k, v in atual.items()})
    except Exception as e:
        LOG.escreve(f'benchmark não entrou no relatório: {e!r}')
    t.nota('  Rode de novo depois de aplicar algo: o programa compara com este resultado.')
    return 0
