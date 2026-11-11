# ─────────────── envio de relatório e feedback ───────────────
#
#   A janela manda; o motor só monta. O relatório que sai daqui é feito para melhorar o Katharos: os erros dele, o que foi
#   aplicado, o que cada otimização rendeu de verdade e como o PC está. Só entra o que está numa lista fechada (nada de portas,
#   arquivos, nomes de pastas pessoais), e tudo passa pela limpeza de dado pessoal: usuário, nome do PC, e-mail, IP, MAC, chave
#   de produto e SID viram marcadores. A pessoa vê exatamente o JSON que vai sair antes de mandar. O Python não acessa a rede.

ENVIO_ESQUEMA = 1
ENVIO_MAX_BYTES = 200_000
ENVIO_TIPOS = ('relatorio', 'feedback', 'ambos')
FEEDBACK_TIPOS = ('problema', 'ideia', 'elogio', 'outro')
SECOES_ENVIO = [
    ('sistema', 'O PC e o Windows', 'modelo, processador, placa de vídeo, memória, disco, versão e idioma do Windows, antivírus e as '
                                    'configurações do Katharos que você mudou'),
    ('erros', 'Erros do Katharos', 'erros e avisos do motor, da janela e do acompanhamento nos últimos 30 dias, e os itens que não '
                                   'ficaram como foram aplicados'),
    ('historico', 'O que foi aplicado', 'cada pacote aplicado ou desfeito, com quando e quais itens, e o que voltou sozinho depois'),
    ('eficiencia', 'O que cada otimização rendeu', 'o que cada item mudou medido antes e depois, as medidas de antes e depois de cada '
                                                   'rodada, e as suas respostas de "ajudou" e "não ajudou"'),
    ('saude', 'Saúde do PC', 'nota e achados do raio-x, drivers que travam o PC e o quanto o próprio Katharos pesa'),
    ('jogos', 'Jogos', 'sessões de jogo com FPS médio, 1% mais lento e o que limitou (só o nome do jogo)'),
]
_CHAVES_FORA = re.compile(r'serial|uuid|guid|\bsid\b|mac|ssid|wifi|wi-fi|\bip\b|endere[cç]o|usuario|usuário|user|dono|email|e-mail|'
                          r'caminho|pasta|arquivo|path|nome_pc|computer|hostname|porta', re.I)


# ── limpeza de dado pessoal ──

def _quem():
    """O que identifica esta pessoa e este PC, para trocar por marcadores (mais longo primeiro: o caminho antes do nome)."""
    trocas = []
    try:
        casa = str(Path.home())
        if len(casa) > 3:
            trocas.append((casa, '~'))
            trocas.append((casa.replace('\\', '/'), '~'))
    except Exception:
        pass
    nomes = set()
    for var in ('USERNAME', 'USER', 'LOGNAME'):
        v = os.environ.get(var)
        if v and len(v) >= 3:
            nomes.add((v, '<usuario>'))
    for var, marca in (('COMPUTERNAME', '<pc>'), ('USERDOMAIN', '<dominio>'), ('HOSTNAME', '<pc>')):
        v = os.environ.get(var)
        if v and len(v) >= 3:
            nomes.add((v, marca))
    try:   # o nome da máquina fora do Windows (sem abrir nada de rede)
        h = os.uname().nodename if hasattr(os, 'uname') else ''
        if h and len(h) >= 3:
            nomes.add((h, '<pc>'))
    except Exception:
        pass
    return trocas + sorted(nomes, key=lambda x: -len(x[0]))


_PADROES_PESSOAIS = [
    (re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+'), '<email>'),
    (re.compile(r'\bS-1-\d+(?:-\d+){2,}\b', re.I), '<sid>'),
    (re.compile(r'\b(?:[0-9A-F]{2}[:-]){5}[0-9A-F]{2}\b', re.I), '<mac>'),
    (re.compile(r'\b(?:[A-Z0-9]{5}-){4}[A-Z0-9]{5}\b'), '<chave>'),
    (re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.I), '<id>'),
    (re.compile(r'(?<![\w:])(?:[0-9a-f]{1,4}:){7}[0-9a-f]{1,4}(?![\w:])', re.I), '<ip>'),
    (re.compile(r'(?<![\w:])(?:[0-9a-f]{1,4}:){1,6}:(?:[0-9a-f]{1,4}(?::[0-9a-f]{1,4}){0,5})?(?![\w:])', re.I), '<ip>'),
]
# pasta de outro usuário (a desta pessoa já virou "~" antes): o nome da pasta sai
_PADROES_PASTA = [
    (re.compile(r'([A-Za-z]:[\\/](?:Users|Usuários|Documents and Settings)[\\/])[^\\/:*?"<>|\r\n]+', re.I), r'\1<usuario>'),
    (re.compile(r'(/(?:home|Users)/)[^/\s]+'), r'\1<usuario>'),
]
_IPV4 = re.compile(r'(?<![\d.])(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})(?![\d.])')


def _ip4(m):
    o = [int(x) for x in m.groups()]
    # versão de programa ("4.1.0.0") não é IP: só troca quando parece endereço (todos até 255 e algum de dois dígitos ou mais)
    return '<ip>' if all(x <= 255 for x in o) and any(x >= 10 for x in o) else m.group(0)


def sem_pessoal(s, trocas=None):
    """Um texto sem nada que identifique a pessoa ou o PC."""
    if not isinstance(s, str) or not s:
        return s
    for rx, para in _PADROES_PESSOAIS:   # primeiro os padrões (o e-mail inteiro some antes de o nome dentro dele ser trocado)
        s = rx.sub(para, s)
    # depois os nomes desta pessoa e deste PC, o mais longo primeiro (a pasta pessoal vira "~"; "PC-DO-JOAO" antes de "joao")
    for de, para in sorted(trocas if trocas is not None else _quem(), key=lambda x: -len(x[0])):
        s = re.sub(re.escape(de), para, s, flags=re.I) if len(de) >= 3 else s
    for rx, para in _PADROES_PASTA:
        s = rx.sub(para, s)
    return _IPV4.sub(_ip4, s)


def limpa_envio(o, trocas=None, n=300, fundo=0):
    """O objeto inteiro pronto para sair: sem chaves que costumam guardar dado pessoal, cada texto sem dado pessoal, sem cara de
    instrução (limpa) e curto. Números e booleanos passam."""
    if trocas is None:
        trocas = _quem()
    if fundo > 10:
        return None
    if isinstance(o, str):
        return limpa(sem_pessoal(o, trocas), n)
    if isinstance(o, dict):
        return {limpa(str(k), 60): limpa_envio(v, trocas, n, fundo + 1) for k, v in list(o.items())[:300]
                if not _CHAVES_FORA.search(str(k))}
    if isinstance(o, (list, tuple)):
        return [limpa_envio(v, trocas, n, fundo + 1) for v in list(o)[:400]]
    if isinstance(o, bool) or o is None:
        return o
    if isinstance(o, (int, float)):
        return round(o, 3) if isinstance(o, float) else o
    return limpa(sem_pessoal(str(o), trocas), n)


def _texto_livre(s, trocas, n=4000):
    """O texto que a pessoa escreveu: mantém as quebras de linha, tira controle e dado pessoal, corta no tamanho."""
    s = '' if s is None else str(s)
    s = re.sub('[\x00-\x09\x0b-\x1f\x7f-\x9f​-‏‪-‮⁠-⁤⁦-⁩﻿]', ' ', s)
    s = sem_pessoal(s, trocas).replace('`', "'").strip()
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s if len(s) <= n else s[:n - 1] + '…'


# ── o que cada seção leva ──

def _linhas_de_erro(arq, desde, maximo=40):
    """As linhas de erro de um registro (com as linhas de pilha logo abaixo), das mais novas para trás, desde uma data."""
    try:
        if not arq.is_file() or datetime.fromtimestamp(arq.stat().st_mtime) < desde:
            return []
        with open(arq, encoding='utf-8', errors='replace') as f:
            linhas = f.read().splitlines()[-4000:]
    except OSError:
        return []
    chave = re.compile(r'\berr(?:o|or)\b|traceback|exception|falh(?:a|ou)|n[aã]o (?:deu|abriu|ligou|conseguiu)|interno|fechou por', re.I)
    out, i = [], 0
    while i < len(linhas):
        if chave.search(linhas[i]):
            bloco = [linhas[i]]
            j = i + 1
            while j < len(linhas) and j - i <= 8 and (linhas[j].startswith((' ', '\t')) or linhas[j].startswith(('Traceback', 'File'))):
                bloco.append(linhas[j].strip())
                j += 1
            out.append(' ⏎ '.join(bloco))
            i = j
        else:
            i += 1
    return out[-maximo:]


def _env_sistema(ctx):
    sec = rel_carrega().get('secoes') or {}
    pc = dict((sec.get('pc') or {}).get('dados') or {})
    pc.pop('admin', None)
    jogos = pc.pop('jogos', None)
    if isinstance(jogos, list):
        pc['jogos_instalados'] = len(jogos)
    e = estado()
    return {'katharos': VERSAO, 'versoes_anteriores': [v for v in (e.get('versoes') or [])][-8:] if isinstance(e.get('versoes'), list) else [],
            'pc': pc or None, 'medido_em': (sec.get('pc') or {}).get('quando'),
            'config_mudada': {k: config(k) for k in PADROES if config(k) != PADROES[k]},
            'segundo_plano': e.get('segundo_plano'), 'janelas': bool(os.environ.get('KATHAROS_JANELA')) or None,
            'python': sys.version.split()[0], 'windows': WINDOWS}


def _env_erros(ctx):
    desde = datetime.now() - timedelta(days=30)
    r = rel_carrega()
    eventos = [ev for ev in (r.get('eventos') or []) if ev.get('erros') or ev.get('avisos') or ev.get('tipo') == 'nao-ficou']
    logs = sorted(pasta('logs').glob('*.log'))[-30:]
    motor = []
    for arq in logs:
        motor.extend(_linhas_de_erro(arq, desde, 30))
    return {'eventos': eventos[-60:], 'motor': motor[-60:],
            'janela': _linhas_de_erro(CASA / 'interface.log', desde, 40),
            'segundo_plano': _linhas_de_erro(CASA / 'segundo-plano.log', desde, 30),
            'texto_suspeito_removido': int(r.get('suspeitos_total') or 0)}


def _env_historico(ctx):
    e = estado()
    pacotes = []
    for nome, reg in sorted((e.get('pacotes') or {}).items(), key=lambda kv: str((kv[1] or {}).get('quando', ''))):
        if not isinstance(reg, dict):
            continue
        pacotes.append({'pacote': nome, 'quando': reg.get('quando'), 'itens': list(reg.get('itens') or [])[:120],
                        'desfeito': bool(reg.get('revertido')), 'desfeito_em': reg.get('revertido_em')})
    sec = rel_carrega().get('secoes') or {}
    ver = (sec.get('verificacao') or {}).get('dados') or {}
    aplicacoes = [ev for ev in (rel_carrega().get('eventos') or []) if ev.get('tipo') == 'itens'][-80:]
    return {'pacotes': pacotes, 'aplicacoes': aplicacoes, 'voltaram_sozinhos': ver.get('desvios') or [],
            'manutencao': (sec.get('manutencao') or {}).get('dados'), 'turbo': (sec.get('turbo') or {}).get('dados'),
            'ultimo_ponto': e.get('ultimo_ponto')}


def _env_eficiencia(ctx):
    out = {}
    try:
        its = resumo_itens(le_provas())
        out['itens'] = [{k: r.get(k) for k in ('pacote', 'id', 'vezes', 'livre', 'ram', 'proc', 'svc', 'mudou')} for r in its[:120]]
    except Exception as ex:
        out['itens_erro'] = type(ex).__name__
    try:
        out['rodadas'] = [{'quando': r['quando'], 'pacotes': r['pacotes'], 'itens': r['itens'], 'reiniciou': r['reiniciou'],
                           'medidas': [{'o_que': rot, 'veredito': ver, 'antes': a, 'depois': b, 'unidade': un} for rot, ver, a, b, _, un in r['metricas']]}
                          for r in rodadas(le_ensaios())[:12]]
    except Exception as ex:
        out['rodadas_erro'] = type(ex).__name__
    try:
        h = api_historico(ctx, {'dias': 90}, lambda *a: None) or {}
        out['efeitos'] = h.get('efeitos') or []
        out['fora_do_normal'] = [{k: x.get(k) for k in ('dia', 'titulo', 'tipo', 'confianca')} for x in (h.get('anomalias') or [])][:10]
    except Exception as ex:
        out['efeitos_erro'] = type(ex).__name__
    try:
        s = api_sugestoes(ctx, {}, lambda *a: None) or {}
        out['previsto_e_aconteceu'] = s.get('linha_do_tempo') or []
        out['diagnosticos'] = [{k: d.get(k) for k in ('problema', 'causa', 'confianca')} for d in (s.get('diagnosticos') or [])]
    except Exception as ex:
        out['sugestoes_erro'] = type(ex).__name__
    out['respostas'] = estado().get('conselheiro_respostas') or {}
    sec = rel_carrega().get('secoes') or {}
    out['antes_depois'] = (sec.get('antes_depois') or {}).get('dados')
    out['benchmark'] = (sec.get('benchmark') or {}).get('dados')
    return out


def _env_saude(ctx):
    quando, rx, _ = _raiox_guardado()
    sec = rel_carrega().get('secoes') or {}
    a = le_json(CASA / 'agora.json', None)
    sp = (a or {}).get('segundo_plano') if isinstance(a, dict) else None
    return {'raiox': {'quando': quando, 'nota': rx.get('nota'),
                      'achados': [{k: x.get(k) for k in ('titulo', 'impacto', 'comando')} for x in (rx.get('achados') or [])][:30]} if quando else None,
            'travadas': (sec.get('travadas') or {}).get('dados'),
            'katharos_pesa': {k: sp.get(k) for k in ('ram_mb', 'cpu_pct', 'leitura_ms', 'leitura_maior_ms')} if isinstance(sp, dict) else None,
            'ritmo_s': (a or {}).get('espera_s') if isinstance(a, dict) else None}


def _env_jogos(ctx):
    s = api_sessoes(ctx, {'dias': 60}, lambda *a: None) or {}
    por = []
    for j in s.get('por_jogo') or []:
        ev = [x for x in (j.get('evolucao') or []) if x.get('fps_1low') is not None]
        por.append({'jogo': j.get('jogo'), 'sessoes': j.get('sessoes'), 'horas': j.get('horas'), 'segura': j.get('segura'),
                    '1low_primeira': ev[0].get('fps_1low') if ev else None, '1low_ultima': ev[-1].get('fps_1low') if ev else None})
    return {'resumo': s.get('resumo'), 'por_jogo': por[:20], 'comparacoes': (s.get('comparacoes') or [])[:20],
            'sessoes': [{k: x.get(k) for k in ('jogo', 'inicio', 'min', 'principal', 'fps_med', 'fps_1low', 'temp_cpu_max')}
                        for x in (s.get('sessoes') or [])][-15:]}


_COLETORES = ('sistema', 'erros', 'historico', 'eficiencia', 'saude', 'jogos')   # cada uma é a função _env_<nome>


def _id_envio():
    """Um número aleatório deste PC, só para contar PCs diferentes nos relatórios (não vem do hardware nem da pessoa)."""
    e = estado()
    v = e.get('id_envio')
    if not isinstance(v, str) or not re.match(r'^[0-9a-f]{16}$', v):
        import secrets
        v = secrets.token_hex(8)
        marca_estado('id_envio', v)
    return v


def _encolhe(o):
    """Corta pela metade toda lista longa (para caber no limite), mantendo as mais novas."""
    if isinstance(o, dict):
        return {k: _encolhe(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_encolhe(v) for v in (o[-max(1, len(o) // 2):] if len(o) > 4 else o)]
    return o


def _resumo_secao(s, d):
    """Uma linha do que a parte leva, para a pessoa bater o olho antes de mandar."""
    n = lambda v: len(v) if isinstance(v, list) else 0
    if s == 'sistema':
        pc = d.get('pc') or {}
        return ', '.join(x for x in (str(pc.get('cpu') or ''), f"{pc.get('ram_gb')} GB" if pc.get('ram_gb') else '', str(pc.get('windows') or '')) if x) or 'versão do Katharos e configurações'
    if s == 'erros':
        linhas = n(d.get('motor')) + n(d.get('janela')) + n(d.get('segundo_plano'))
        return f'{n(d.get("eventos"))} avisos ou erros ao aplicar, {linhas} linhas de erro dos registros'
    if s == 'historico':
        return f'{n(d.get("pacotes"))} pacotes, {n(d.get("aplicacoes"))} aplicações, {n(d.get("voltaram_sozinhos"))} itens que voltaram sozinhos'
    if s == 'eficiencia':
        return f'{n(d.get("itens"))} itens medidos, {n(d.get("rodadas"))} rodadas antes e depois, {len(d.get("respostas") or {})} respostas suas'
    if s == 'saude':
        rx = d.get('raiox') or {}
        return (f'raio-x nota {rx.get("nota")}, {n(rx.get("achados"))} achados' if rx else 'sem raio-x') + (', custo do acompanhamento' if d.get('katharos_pesa') else '')
    if s == 'jogos':
        return f'{n(d.get("por_jogo"))} jogos, {n(d.get("sessoes"))} sessões recentes'
    return ''


def monta_envio(ctx, tipo, secoes=None, feedback=None):
    """O pacote que a janela manda, já limpo, e o resumo do que vai. Lança ErroApi se faltar algo."""
    if tipo not in ENVIO_TIPOS:
        raise ErroApi('pedido_invalido', 'tipo precisa ser relatorio, feedback ou ambos')
    trocas = _quem()
    pacote = {'esquema': ENVIO_ESQUEMA, 'tipo': tipo, 'katharos': VERSAO, 'enviado': agora_iso(), 'id_pc': _id_envio()}
    resumo = []
    if tipo in ('feedback', 'ambos'):
        f = feedback if isinstance(feedback, dict) else {}
        texto = _texto_livre(f.get('texto'), trocas)
        if len(texto) < 3:
            raise ErroApi('sem_texto', 'Escreva o que aconteceu ou o que você quer (umas palavras já bastam).')
        nota = f.get('nota')
        nota = nota if isinstance(nota, int) and not isinstance(nota, bool) and 1 <= nota <= 5 else None
        contato = limpa(str(f.get('contato') or ''), 120) or None   # escrito pela pessoa, de propósito: não é trocado
        pacote['feedback'] = {'tipo': f.get('tipo') if f.get('tipo') in FEEDBACK_TIPOS else 'outro', 'texto': texto, 'nota': nota, 'contato': contato}
        resumo.append({'titulo': 'Feedback', 'texto': f'{pacote["feedback"]["tipo"]}, {len(texto)} letras'
                       + (f', nota {nota} de 5' if nota else '') + (', com contato para resposta' if contato else '')})
    if tipo in ('relatorio', 'ambos'):
        pedidas = [s for s in (secoes if isinstance(secoes, list) else [x[0] for x in SECOES_ENVIO]) if s in _COLETORES]
        if not pedidas:
            raise ErroApi('sem_secoes', 'Escolha pelo menos uma parte do relatório.')
        rel = {}
        for s in pedidas:
            try:
                rel[s] = globals()['_env_' + s](ctx)
            except Exception as ex:   # uma parte que falha não derruba o resto: vira um aviso no próprio relatório
                LOG.escreve(f'envio: a parte {s} falhou: {traceback.format_exc()}')
                rel[s] = {'nao_coletado': type(ex).__name__}
        pacote['relatorio'] = limpa_envio(rel, trocas)
        pacote['secoes'] = pedidas
    tamanho = len(json.dumps(pacote, ensure_ascii=False).encode('utf-8'))
    for _ in range(6):
        if tamanho <= ENVIO_MAX_BYTES or 'relatorio' not in pacote:
            break
        pacote['relatorio'] = _encolhe(pacote['relatorio'])
        pacote['encurtado'] = True
        tamanho = len(json.dumps(pacote, ensure_ascii=False).encode('utf-8'))
    if 'relatorio' in pacote:
        titulos = dict((a, b) for a, b, _ in SECOES_ENVIO)
        for s in pacote['secoes']:
            d = pacote['relatorio'].get(s) or {}
            resumo.append({'titulo': titulos[s], 'texto': 'não deu para coletar' if d.get('nao_coletado') else _resumo_secao(s, d)})
    return {'pacote': pacote, 'resumo': resumo, 'bytes': tamanho,
            'json': json.dumps(pacote, ensure_ascii=False, indent=1)}


@metodo_api('envio_secoes')
def api_envio_secoes(ctx, p, ev):
    """As partes que o relatório pode levar (com o que cada uma tem) e os envios já feitos deste PC."""
    return {'secoes': [{'id': a, 'titulo': b, 'explica': c} for a, b, c in SECOES_ENVIO],
            'feedback_tipos': list(FEEDBACK_TIPOS), 'envios': list(reversed(estado().get('envios') or []))[:30]}


@metodo_api('envio_montar')
def api_envio_montar(ctx, p, ev):
    """Monta o que vai ser enviado, já limpo de dado pessoal: o pacote exato, um resumo e o JSON para a pessoa ler antes."""
    return monta_envio(ctx, p.get('tipo'), p.get('secoes'), p.get('feedback'))


@metodo_api('envio_registrar')
def api_envio_registrar(ctx, p, ev):
    """Anota um envio que deu certo (o código que o servidor devolveu), para aparecer na tela e para pedir para apagar depois."""
    codigo = str(p.get('codigo') or '')
    if not re.match(r'^KTH-[A-Z0-9]{4,12}$', codigo):
        raise ErroApi('pedido_invalido', 'código de envio inválido')
    e = estado()
    envios = [x for x in (e.get('envios') or []) if isinstance(x, dict)][-49:]
    envios.append({'codigo': codigo, 'tipo': p.get('tipo') if p.get('tipo') in ENVIO_TIPOS else 'relatorio', 'quando': agora_iso(), 'versao': VERSAO})
    e['envios'] = envios
    salva_estado(e)
    return {'envios': list(reversed(envios))[:30]}
