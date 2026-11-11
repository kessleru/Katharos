# ███████████████████████████████████████████████████████████████████████████
#
#   PROVA DE GANHO · o que cada item rendeu de verdade, medido neste PC
#
#   Duas provas, porque há dois tipos de ganho:
#   1. NA HORA, item por item: um retrato barato (espaço livre, RAM disponível, processos, serviços rodando) antes
#      e depois de cada item. Disco liberado e serviço parado aparecem aqui, com o nome do item ao lado.
#   2. DEPOIS DE REINICIAR, por rodada: boot, CPU e RAM em repouso só mudam depois do próximo boot, e aí não dá
#      para separar um item do outro. Cada aplicação abre um "ensaio" com a medida de antes; a primeira medida
#      feita depois de reiniciar (pelo "medir", pelo "raiox" ou pelo segundo plano) fecha o ensaio.
#   O que fica abaixo do ruído normal do PC é dito como "sem diferença mensurável", nunca como ganho.
#
# ███████████████████████████████████████████████████████████████████████████

PROVAS_MAX = 3000       # linhas guardadas em provas.jsonl (uma por item aplicado)
ENSAIOS_MAX = 80
# abaixo disto é oscilação normal entre dois retratos seguidos: não conta como ganho nem como perda
RUIDO_RETRATO = {'livre': 10, 'ram': 60, 'proc': 2, 'svc': 1}   # MB, MB, processos, serviços
# métricas do ensaio: chave, rótulo, melhor, casas, unidade, mínimo absoluto, mínimo relativo, só vale com reinício
METRICAS_ENSAIO = [
    ('boot_s', 'tempo de boot', 'menor', 0, 's', 2, 0.10, True),
    ('inicializacao', 'abrem com o Windows', 'menor', 0, '', 1, 0, False),
    ('ram_usada', 'RAM em repouso', 'menor', 1, 'GB', 0.3, 0.05, False),
    ('cpu', 'CPU em repouso', 'menor', 0, '%', 2, 0, False),
    ('processos', 'processos', 'menor', 0, '', 5, 0, False),
    ('servicos', 'serviços rodando', 'menor', 0, '', 2, 0, False),
    ('livre_c', 'livre em C:', 'maior', 1, 'GB', 0.5, 0, False),
]

RETRATO_PS = r'''
function Retrato([int]$Mudou = 0) {
    $r = @{ livre = $null; ram = $null; proc = $null; svc = $null; m = $Mudou }
    try { $r.livre = [math]::Round(([System.IO.DriveInfo]::new($env:SystemDrive.Substring(0, 1))).AvailableFreeSpace / 1MB) } catch {}
    try { $r.ram = [math]::Round((Get-CimInstance Win32_OperatingSystem -Property FreePhysicalMemory -ErrorAction Stop).FreePhysicalMemory / 1KB) } catch {}
    try { $r.proc = [System.Diagnostics.Process]::GetProcesses().Count } catch {}
    try { $r.svc = @(Get-Service -ErrorAction Stop | Where-Object { $_.Status -eq 'Running' }).Count } catch {}
    return $r
}
'''


def provas_arq():
    return CASA / 'provas.jsonl'


def ensaios_arq():
    return CASA / 'ensaios.json'


def retrato():
    """O retrato barato, pelo Python (para os itens que não são PowerShell): MB livres em C:, MB de RAM disponível
    e número de processos. O que não der para ler fica None."""
    r = {'livre': None, 'ram': None, 'proc': None, 'svc': None}
    try:
        r['livre'] = round(shutil.disk_usage(os.environ.get('SystemDrive', 'C:') + '\\' if WINDOWS else '/').free / 1048576)
    except OSError:
        pass
    if WINDOWS:
        try:
            import ctypes

            class _Mem(ctypes.Structure):
                _fields_ = [('tam', ctypes.c_ulong), ('carga', ctypes.c_ulong)] + [(n, ctypes.c_ulonglong) for n in
                            ('total', 'disp', 'pag_total', 'pag_disp', 'virt_total', 'virt_disp', 'ext')]
            m = _Mem()
            m.tam = ctypes.sizeof(_Mem)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
                r['ram'] = round(m.disp / 1048576)
            ids = (ctypes.c_ulong * 4096)()
            usados = ctypes.c_ulong()
            if ctypes.windll.psapi.EnumProcesses(ctypes.byref(ids), ctypes.sizeof(ids), ctypes.byref(usados)):
                r['proc'] = usados.value // ctypes.sizeof(ctypes.c_ulong)
        except Exception as e:
            LOG.escreve(f'retrato: {e!r}')
    return r


def delta_retrato(antes, depois):
    """O que mudou entre dois retratos, já no sentido do ganho (positivo é bom): MB liberados em disco, MB de RAM
    a mais disponível, processos a menos, serviços a menos. O que está dentro do ruído vira 0; sem leitura, None."""
    d = {}
    for ch, sinal in (('livre', 1), ('ram', 1), ('proc', -1), ('svc', -1)):
        a, b = (antes or {}).get(ch), (depois or {}).get(ch)
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            d[ch] = None
            continue
        v = sinal * (b - a)
        d[ch] = round(v) if abs(v) >= RUIDO_RETRATO[ch] else 0
    return d


def classe_hw(p):
    """'ssd-16gb-desktop': o tipo de máquina, para comparar provas entre PCs parecidos."""
    disco = 'hd' if eh_hd(p) else ('ssd' if eh_ssd(p) else 'disco')
    ram = pf(p, 'ram.total', 0) or 0
    faixa = '4gb' if ram <= 4.5 else ('8gb' if ram <= 9 else ('16gb' if ram <= 17 else '32gb'))
    return f'{disco}-{faixa}-{"notebook" if pf(p, "pc.notebook") else "desktop"}'


def registra_provas(linhas, arq=None):
    """Acrescenta as provas (uma por item aplicado) e apara o arquivo."""
    if not linhas:
        return
    arq = Path(arq or provas_arq())
    try:
        arq.parent.mkdir(parents=True, exist_ok=True)
        with open(arq, 'a', encoding='utf-8') as f:
            for l in linhas:
                f.write(json.dumps(l, ensure_ascii=False, separators=(',', ':')) + '\n')
        todas = arq.read_text(encoding='utf-8', errors='replace').splitlines()
        if len(todas) > PROVAS_MAX:
            arq.write_text('\n'.join(todas[-PROVAS_MAX:]) + '\n', encoding='utf-8')
    except OSError as e:
        LOG.escreve(f'provas: não gravou: {e!r}')


def le_provas(arq=None):
    out = []
    try:
        for l in Path(arq or provas_arq()).read_text(encoding='utf-8', errors='replace').splitlines():
            try:
                d = json.loads(l)
                if isinstance(d, dict) and d.get('id') and isinstance(d.get('d'), dict):
                    out.append(d)
            except ValueError:
                continue
    except OSError:
        pass
    return out


def le_ensaios(arq=None):
    d = le_json(Path(arq or ensaios_arq()), [])
    return [x for x in d if isinstance(x, dict) and x.get('id')] if isinstance(d, list) else []


def _medida_recente(horas=2, agora=None):
    """A última medida completa salva, se tiver menos de N horas. Evita medir de novo a cada pacote."""
    agora = agora or datetime.now()
    for arq in reversed(medidas_salvas()):
        m = le_json(arq, {})
        try:
            if 0 <= (agora - datetime.fromisoformat(str(m.get('data'))[:19])).total_seconds() <= horas * 3600:
                return m
        except (TypeError, ValueError):
            continue
        break
    return None


def abre_ensaio(ctx, pac, itens, agora=None):
    """Começa um ensaio: guarda a medida de antes e o que vai ser aplicado. Devolve o id do ensaio."""
    agora = agora or datetime.now()
    antes = _medida_recente(agora=agora)
    if antes is None and WINDOWS:
        try:
            antes = mede(ctx, 'medindo antes, para provar o ganho depois')
            salva_medida(antes, 'antes-' + pac.nome)
        except Exception as e:
            LOG.escreve(f'ensaio sem medida de antes: {e!r}')
    ens = {'id': f'{agora:%Y%m%d%H%M%S}-{pac.nome}', 't': agora.replace(microsecond=0).isoformat(), 'pacote': pac.nome,
           'itens': [i.id for i in itens], 'antes': antes or None, 'depois': None, 'fechado': None, 'reiniciou': None}
    try:
        todos = le_ensaios() + [ens]
        grava_json(ensaios_arq(), todos[-ENSAIOS_MAX:])
    except OSError as e:
        LOG.escreve(f'ensaio não gravou: {e!r}')
    return ens['id']


def fecha_ensaios(m, agora=None, arq=None):
    """Chamada a cada medida completa: fecha os ensaios abertos que já podem ser comparados. Um ensaio fecha na
    primeira medida feita depois de reiniciar (com o PC ligado há pelo menos 10 minutos), ou, sem reinício, depois
    de 14 dias. Devolve quantos fechou."""
    if not isinstance(m, dict) or not m:
        return 0
    agora = agora or datetime.now()
    ens = le_ensaios(arq)
    up = m.get('uptime_h')
    ligou = agora - timedelta(hours=up) if isinstance(up, (int, float)) else None
    n = 0
    for e in ens:
        if e.get('fechado'):
            continue
        try:
            t0 = datetime.fromisoformat(e['t'])
        except (KeyError, TypeError, ValueError):
            continue
        reiniciou = ligou is not None and ligou > t0
        if (reiniciou and up * 60 >= 10) or (agora - t0).days >= 14:
            e['depois'] = {k: v for k, v in m.items() if isinstance(v, (int, float))}
            e['fechado'] = agora.replace(microsecond=0).isoformat()
            e['reiniciou'] = bool(reiniciou)
            n += 1
    if n:
        try:
            grava_json(Path(arq or ensaios_arq()), ens)
        except OSError as ex:
            LOG.escreve(f'ensaios não gravaram: {ex!r}')
    return n


def veredito_ensaio(a, b, melhor, minimo, relativo=0):
    """'melhorou', 'piorou' ou 'igual' entre uma medida de antes e uma de depois, descontado o ruído."""
    d = b - a
    if abs(d) < max(minimo, relativo * abs(a)):
        return 'igual'
    return 'melhorou' if (d < 0) == (melhor == 'menor') else 'piorou'


def rodadas(ensaios):
    """Junta os ensaios fechados pela mesma medida (tudo o que foi aplicado entre dois reinícios é uma rodada só,
    porque não dá para separar o efeito). Mais novas primeiro. Cada rodada:
    {quando, fechado, reiniciou, pacotes, itens, metricas: [(rótulo, veredito, antes, depois, casas, unidade)]}"""
    grupos = {}
    for e in ensaios:
        if e.get('fechado') and isinstance(e.get('depois'), dict):
            grupos.setdefault(e['fechado'], []).append(e)
    out = []
    for fechado, es in grupos.items():
        es.sort(key=lambda e: e.get('t', ''))
        antes = next((e['antes'] for e in es if isinstance(e.get('antes'), dict)), None)
        depois = es[-1]['depois']
        reiniciou = any(e.get('reiniciou') for e in es)
        mets = []
        for ch, rot, melhor, casas, un, minimo, rel, so_boot in METRICAS_ENSAIO:
            a, b = (antes or {}).get(ch), depois.get(ch)
            if not isinstance(a, (int, float)) or not isinstance(b, (int, float)) or (so_boot and not reiniciou):
                continue
            mets.append((rot, veredito_ensaio(a, b, melhor, minimo, rel), a, b, casas, un))
        pacotes = []
        for e in es:
            if e.get('pacote') not in pacotes:
                pacotes.append(e.get('pacote'))
        out.append({'quando': es[0].get('t'), 'fechado': fechado, 'reiniciou': reiniciou, 'pacotes': pacotes,
                    'itens': sum(len(e.get('itens') or []) for e in es), 'metricas': mets})
    return sorted(out, key=lambda r: r['fechado'], reverse=True)


def ensaios_abertos(ensaios):
    return [e for e in ensaios if not e.get('fechado')]


def resumo_itens(provas):
    """Junta as provas por item: [{pacote, id, titulo, vezes, livre, ram, proc, svc, mudou, quando}], o maior ganho primeiro.
    Disco e serviços somam (cada aplicação liberou de novo); RAM e processos ficam com a mediana (oscilam)."""
    por = {}
    for p in provas:
        por.setdefault((p.get('pacote'), p['id']), []).append(p)
    out = []
    for (pacote, id_), ps in por.items():
        def vals(ch):
            return [x['d'].get(ch) for x in ps if isinstance(x['d'].get(ch), (int, float))]
        def mediana(v):
            v = sorted(v)
            return v[len(v) // 2] if v else None
        r = {'pacote': pacote, 'id': id_, 'titulo': ps[-1].get('titulo') or id_, 'vezes': len(ps),
             'livre': sum(vals('livre')) if vals('livre') else None, 'svc': max(vals('svc')) if vals('svc') else None,
             'ram': mediana(vals('ram')), 'proc': mediana(vals('proc')),
             'mudou': sum(x.get('mudou') or 0 for x in ps), 'quando': ps[-1].get('t')}
        r['pontos'] = max(0, r['livre'] or 0) / 100 + max(0, r['ram'] or 0) / 50 + max(0, r['proc'] or 0) + 2 * max(0, r['svc'] or 0)
        out.append(r)
    return sorted(out, key=lambda r: (-r['pontos'], str(r['titulo']).lower()))


def texto_ganho(d):
    """'liberou 1,2 GB · 2 serviços a menos', ou '' se nada passou do ruído. d: um delta (ou um resumo de item)."""
    partes = []
    livre = d.get('livre') or 0
    if livre >= RUIDO_RETRATO['livre']:
        partes.append('liberou ' + (f'{br(livre / 1024, 1)} GB' if livre >= 1024 else f'{br(livre, 0)} MB') + ' em disco')
    if (d.get('svc') or 0) >= 1:
        partes.append(pl(d['svc'], 'serviço a menos', 'serviços a menos'))
    if (d.get('proc') or 0) >= RUIDO_RETRATO['proc']:
        partes.append(pl(d['proc'], 'processo a menos', 'processos a menos'))
    if (d.get('ram') or 0) >= RUIDO_RETRATO['ram']:
        partes.append(f'cerca de {br(d["ram"], 0)} MB de RAM a mais')
    return ' · '.join(partes)


def prova_do_item(pacote, id_, provas=None):
    """A frase que entra na explicação de um item: o que ele rendeu neste PC da última vez, ou ''."""
    try:
        ps = [p for p in (le_provas() if provas is None else provas) if p.get('pacote') == pacote and p.get('id') == id_]
    except Exception:
        return ''
    if not ps:
        return ''
    u = ps[-1]
    quando = ha_quanto_iso(u.get('t')) or ''
    g = texto_ganho(u['d'])
    if g:
        return f'medido aqui ({quando}): {g}'
    if not u.get('mudou'):
        return f'medido aqui ({quando}): já estava assim, não mudou nada'
    return f'medido aqui ({quando}): mudou {pl(u["mudou"], "ajuste", "ajustes")}, sem ganho imediato mensurável (o efeito vem depois de reiniciar)'


def mostra_provas_da_aplicacao(t, linhas):
    """Logo depois de aplicar: o que cada item rendeu agora, em uma tabela curta. Só entram itens com ganho medido."""
    com = [l for l in linhas if texto_ganho(l['d'])]
    mudaram = sum(1 for l in linhas if l.get('mudou'))
    t.titulo('o que rendeu agora')
    if com:
        com.sort(key=lambda l: -(max(0, l['d'].get('livre') or 0) / 100 + 2 * max(0, l['d'].get('svc') or 0) + max(0, l['d'].get('proc') or 0)))
        for l in com[:8]:
            t.item('✓', 'verde', corta(l['titulo'], 44), t.p(texto_ganho(l['d']), 'verde'))
        if len(com) > 8:
            t.nota(f'  e mais {len(com) - 8}: veja todos em "provas".')
    resto = mudaram - len([l for l in com if l.get('mudou')])
    if resto > 0 or not com:
        t.paragrafo((f'{pl(resto, "item mudou", "itens mudaram")} o Windows sem ganho imediato mensurável. ' if resto > 0 else 'Nenhum ganho imediato mensurável. ')
                    + 'Boot, CPU e RAM em repouso só mudam depois de reiniciar: a medida de antes ficou guardada e o Katharos compara '
                    'sozinho na próxima medição (comando "provas").', 2, 'apagado')


def ensaio_repetido(ctx, nome, medir=None, desfazer=None, aplicar=None):
    """2e.7: para efeito pequeno, uma medida só engana. Com a área aplicada: mede, desfaz, mede, aplica de novo os mesmos itens, mede.
    O ganho "se repetiu" quando desfazer perde e reaplicar devolve, além do ruído, na mesma métrica. Devolve o resultado (e grava nas provas)."""
    medir = medir or retrato
    reg = (estado().get('pacotes') or {}).get(nome) or {}
    pac = PACOTES.get(nome)
    if not pac or not reg or reg.get('revertido'):
        return {'erro': 'a área precisa estar aplicada (o ensaio desfaz e aplica de novo os mesmos itens)'}
    if not pac.reversivel:
        return {'erro': 'esta área não volta pelo desfazer (remoções): não dá para ensaiar'}
    ids = set(reg.get('itens') or [])
    r0 = medir()
    cod = (desfazer or (lambda: desfaz_pacote(ctx, nome)))()
    if cod:
        return {'erro': 'o desfazer não terminou: o ensaio parou aqui'}
    r1 = medir()
    its = [i for i in (pac.itens(ctx) or []) if i and i.id in ids]
    (aplicar or (lambda: executa_itens(ctx, pac, its)))()
    r2 = medir()
    perdeu, voltou = delta_retrato(r1, r0), delta_retrato(r1, r2)   # positivo = o ganho que a área dá
    out = {'pacote': nome, 'titulo': pac.titulo, 'itens': len(its), 'metricas': {}}
    for ch in ('livre', 'ram', 'proc', 'svc'):
        a, b = perdeu.get(ch), voltou.get(ch)
        if a is None or b is None:
            continue
        out['metricas'][ch] = {'ao_desfazer': a, 'ao_reaplicar': b, 'repetiu': a > 0 and b > 0, 'sem_efeito': a == 0 and b == 0}
    m = out['metricas'].values()
    out['veredito'] = 'repetiu' if any(x['repetiu'] for x in m) else ('sem efeito imediato' if all(x['sem_efeito'] for x in m) else 'não repetiu')
    try:
        registra_provas([{'t': agora_iso(), 'pacote': nome, 'id': '*ensaio', 'titulo': f'ensaio repetido de {pac.titulo}', 'd': voltou, 'mudou': len(its),
                          'ensaio': out}])
    except Exception as ex:
        LOG.escreve(f'ensaio repetido: {ex!r}')
    return out


def ferramenta_provas(ctx, args):
    t = ctx.t
    if getattr(args, 'repetir', None):
        nome = args.repetir
        t.aba(f'ensaio repetido de {nome}: desfaz, mede, aplica de novo, mede')
        if nome not in PACOTES:
            t.erro(f'Área "{nome}" não existe.')
            return 1
        if not aviso_aceito():
            t.erro('Este ensaio muda o PC: leia e aceite o aviso antes ("katharos aviso").')
            return 1
        if not t.confirma(f'Vou desfazer {PACOTES[nome].titulo} e aplicar de novo os mesmos itens, medindo antes e depois. Continuar?', sim=bool(getattr(args, 'sim', False))):
            return 0
        r = ensaio_repetido(ctx, nome)
        if r.get('erro'):
            t.erro(r['erro'] + '.')
            return 1
        nomes = {'livre': 'espaço livre', 'ram': 'RAM disponível', 'proc': 'processos', 'svc': 'serviços'}
        for ch, x in r['metricas'].items():
            t.item('●', 'verde' if x['repetiu'] else 'apagado', nomes[ch], f'ao desfazer: {x["ao_desfazer"]:+d}; ao reaplicar: {x["ao_reaplicar"]:+d}'
                   + (' (o ganho se repetiu)' if x['repetiu'] else ''))
        t.ok({'repetiu': 'O ganho se repetiu: é efeito da área, não acaso.', 'sem efeito imediato': 'Sem efeito imediato mensurável (pode aparecer depois de reiniciar).',
              'não repetiu': 'O ganho não se repetiu: o que se viu da primeira vez era oscilação.'}[r['veredito']])
        return 0
    t.aba('o que cada item rendeu de verdade, medido neste PC')
    provas, ens = le_provas(), le_ensaios()
    try:   # 2c.7: o antes e depois nos jogos (sessões do mesmo jogo antes e depois de cada mudança) também é prova
        jogos = comparacoes_por_jogo(le_sessoes(90), pacotes_aplicados_dt())
    except Exception as ex:
        LOG.escreve(f'provas: jogos: {ex!r}')
        jogos = []
    if jogos:
        t.titulo('nos jogos (sessões antes e depois de cada mudança)')
        cor = {'melhor': 'verde', 'pior': 'vermelho'}
        for c in jogos[:10]:
            t.item('●', next((v for k_, v in cor.items() if k_ in str(c.get('veredito'))), 'apagado'), f'{c["jogo"]} · {c["rotulo"]}',
                   f'{br(c.get("antes"), 0)} → {br(c.get("depois"), 0)} {c.get("un") or ""} depois de {c["nome_pacote"]} ({c["veredito"]})')
    if not provas and not ens:
        if jogos:
            return 0
        t.paragrafo('Ainda não há provas. A partir de agora, cada item que você aplicar é medido antes e depois (espaço, RAM, processos e '
                    'serviços), e cada aplicação guarda a medida de antes para comparar boot, CPU e RAM depois que você reiniciar.', 2, 'sub')
        return 0
    rs = rodadas(ens)
    if rs:
        t.titulo('depois de reiniciar')
        nomes_ver = {'melhorou': ('verde', 'melhorou'), 'piorou': ('vermelho', 'piorou'), 'igual': ('apagado', 'sem diferença mensurável')}
        for r in rs[:4]:
            dq = _dt_prova(r['quando'])
            t.escreve('  ' + t.p(f'{dq:%d/%m/%Y}' if dq else '', 'destaque', True) + '  '
                      + t.p(' + '.join(PACOTES[p].titulo if p in PACOTES else str(p) for p in r['pacotes']) + f' · {pl(r["itens"], "item", "itens")}', 'texto'))
            if not r['metricas']:
                t.paragrafo('Sem medida de antes para comparar.', 4, 'apagado')
            for rot, ver, a, b, casas, un in r['metricas']:
                cor, nome = nomes_ver[ver]
                un_ = (' ' + un) if un else ''
                t.item('·', cor, rot, t.p(f'{br(a, casas)}{un_} → {br(b, casas)}{un_}' if ver != 'igual' else nome, cor), recuo=4)
            if not r['reiniciou']:
                t.paragrafo('O PC não foi reiniciado neste período: o tempo de boot não entra.', 4, 'apagado')
            t.escreve()
        t.paragrafo('Uma medida antes e uma depois: vale como indício. Tudo o que foi aplicado entre dois reinícios entra na mesma rodada, '
                    'porque não dá para separar o efeito de cada pacote. O painel mostra também a mediana de 7 dias.', 2, 'apagado')
    ab = ensaios_abertos(ens)
    if ab:
        t.titulo('esperando o próximo reinício')
        t.paragrafo(', '.join(f'{e.get("pacote")} ({ha_quanto_iso(e.get("t")) or "agora"})' for e in ab[-6:])
                    + '. Reinicie, espere 10 minutos e rode "medir" (ou deixe o segundo plano medir): a comparação aparece aqui.', 2, 'sub')
    its = resumo_itens(provas)
    com = [r for r in its if r['pontos'] > 0]
    if its:
        t.titulo('na hora, item por item')
        if com:
            def cel(v, un, div=1, casas=0):
                return '-' if not v or v <= 0 else br(v / div, casas) + un
            t.tabela(['item', 'área', 'disco', 'RAM', 'processos', 'serviços'],
                     [[corta(str(r['titulo']), 38), str(r['pacote']), cel(r['livre'], ' GB', 1024, 1) if (r['livre'] or 0) >= 1024 else cel(r['livre'], ' MB'),
                       cel(r['ram'], ' MB'), cel(r['proc'], ''), cel(r['svc'], '')] for r in com[:15]], alinha='eedddd', flex=0)
        total = sum(max(0, r['livre'] or 0) for r in its)
        sem = [r for r in its if r['pontos'] <= 0 and r['mudou']]
        nada = [r for r in its if not r['mudou'] and r['pontos'] <= 0]
        t.escreve()
        t.chaves([('itens medidos', str(len(its))), ('com ganho na hora', t.p(str(len(com)), 'verde')),
                  ('disco liberado', gb(total / 1024) if total >= 1024 else f'{br(total, 0)} MB'),
                  ('mudaram sem ganho imediato', str(len(sem))), ('já estavam assim', str(len(nada)))])
        t.paragrafo('RAM e processos oscilam sozinhos: só entram quando a diferença passa do ruído normal, e são aproximados. '
                    'Disco liberado e serviços parados são exatos.', 2, 'apagado')
    rel_secao('provas', {'rodadas': [{'quando': r['quando'], 'pacotes': r['pacotes'], 'itens': r['itens'], 'reiniciou': r['reiniciou'],
                                      'metricas': [[rot, ver, a, b, un] for rot, ver, a, b, _, un in r['metricas']]} for r in rs[:6]],
                         'itens': [{'titulo': r['titulo'], 'pacote': r['pacote'], 'ganho': texto_ganho(r) or ('mudou sem ganho imediato' if r['mudou'] else 'já estava assim'),
                                    'vezes': r['vezes']} for r in its[:60]],
                         'hardware': next((p.get('hw') for p in reversed(provas) if p.get('hw')), '')})
    return 0


def _dt_prova(txt):
    try:
        return datetime.fromisoformat(str(txt))
    except (TypeError, ValueError):
        return None
