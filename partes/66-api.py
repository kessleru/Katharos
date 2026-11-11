
# ███████████████████████████████████████████████████████████████████████████
#
#   API PARA A INTERFACE COM JANELAS (katharos api)
#   A interface (Katharos.App, C#) conversa com este mesmo programa por JSON, uma linha por mensagem, na entrada e na saída padrão.
#   Nada aqui muda o comportamento dos comandos de terminal: a API chama as mesmas funções e só troca a tela pelo JSON.
#
# ███████████████████████████████████████████████████████████████████████████
#
# pedido:   {"id": 7, "metodo": "itens", "params": {"modo": "equilibrado"}}
# resposta: {"id": 7, "ok": true, "dados": {...}}   ou   {"id": 7, "ok": false, "erro": {"codigo": "...", "texto": "..."}}
# evento:   {"id": 7, "evento": "progresso", "dados": {...}}   (durante uma operação longa, antes da resposta)
# A primeira linha que a API escreve é {"pronto": true, "api": 1, "versao": "..."}. "sair" encerra.

import traceback

API_VERSAO = 1
METODOS_API = {}


def metodo_api(nome, muda=False):
    """Registra um método. muda=True: muda o PC (pede o aceite do aviso e administrador; roda no motor elevado)."""
    def reg(f):
        METODOS_API[nome] = (f, muda)
        return f
    return reg


class ErroApi(Exception):
    def __init__(self, codigo, texto):
        super().__init__(texto)
        self.codigo, self.texto = codigo, texto


class CanalApi:
    """Escreve as mensagens no canal da interface. Uma trava: eventos e respostas nunca se misturam na mesma linha."""

    def __init__(self, saida):
        self.saida = saida
        self.trava = threading.Lock()

    def manda(self, msg):
        linha = json.dumps(msg, ensure_ascii=False, default=str)
        with self.trava:
            self.saida.write(linha + '\n')
            self.saida.flush()

    def evento(self, id_, tipo, dados):
        self.manda({'id': id_, 'evento': tipo, 'dados': dados})


def responde_api(ctx, canal, pedido):
    """Um pedido → uma resposta (e os eventos no meio). Erro nunca derruba a API: vira resposta com código."""
    id_ = pedido.get('id') if isinstance(pedido, dict) else None
    try:
        if not isinstance(pedido, dict) or not isinstance(pedido.get('metodo'), str):
            raise ErroApi('pedido_invalido', 'o pedido precisa de "metodo" (texto) e, se tiver, "params" (objeto)')
        nome = pedido['metodo']
        if nome not in METODOS_API:
            raise ErroApi('metodo_desconhecido', f'"{nome}" não existe; os métodos estão em "metodos"')
        f, muda = METODOS_API[nome]
        params = pedido.get('params') or {}
        if not isinstance(params, dict):
            raise ErroApi('pedido_invalido', '"params" precisa ser um objeto')
        if muda:
            if not aviso_aceito():
                raise ErroApi('precisa_aceite', 'Aceite o aviso de uso antes de mudar o PC.')
            if WINDOWS and not eh_admin():
                raise ErroApi('precisa_admin', 'Mudar o PC precisa de administrador: a interface abre o motor elevado.')
        dados = f(ctx, params, lambda tipo, d: canal.evento(id_, tipo, d))
        canal.manda({'id': id_, 'ok': True, 'dados': dados})
    except ErroApi as e:
        canal.manda({'id': id_, 'ok': False, 'erro': {'codigo': e.codigo, 'texto': e.texto}})
    except Exception as e:   # o erro vai para o log com a pilha; a interface recebe o texto
        LOG.escreve(f'api {pedido!r}: {traceback.format_exc()}')
        canal.manda({'id': id_, 'ok': False, 'erro': {'codigo': 'interno', 'texto': f'{type(e).__name__}: {e}'}})


def roda_api(argv, entrada=None, saida=None):
    """katharos api              conversa por linhas (a interface usa assim)
       katharos api METODO [JSON] um pedido só, para testar no terminal"""
    if argv and argv[0] == '--pipe':   # motor elevado (ver roda_api_elevada)
        op = dict(zip(argv[0::2], argv[1::2]))
        return roda_api_elevada(op.get('--pipe'), op.get('--dono'), op.get('--senha'))
    canal_real = saida or sys.stdout
    sys.stdout = sys.stderr   # tudo o que as funções escreveriam na tela vai para o erro padrão (o log da interface), nunca no canal
    try:
        t = Terminal(True, True, largura=100, consulta_fundo=False)
        t.interativo = False
        t.tty = False
        args = _defaults(monta_parser().parse_args([]))
        args.sim, args.sem_cor, args.ascii = True, True, True
        ctx = Ctx(args, t)
        canal = CanalApi(canal_real)
        if argv:
            try:
                params = json.loads(argv[1]) if len(argv) > 1 else {}
            except ValueError:
                params = None
            responde_api(ctx, canal, {'id': 1, 'metodo': argv[0], 'params': params})
            return 0
        canal.manda({'pronto': True, 'api': API_VERSAO, 'versao': VERSAO})
        for linha in (entrada or sys.stdin):
            linha = linha.strip()
            if not linha:
                continue
            try:
                pedido = json.loads(linha)
            except ValueError:
                canal.manda({'id': None, 'ok': False, 'erro': {'codigo': 'json_invalido', 'texto': 'a linha não é JSON'}})
                continue
            if isinstance(pedido, dict) and pedido.get('metodo') == 'sair':
                canal.manda({'id': pedido.get('id'), 'ok': True, 'dados': None})
                break
            responde_api(ctx, canal, pedido)
        return 0
    finally:
        sys.stdout = canal_real


# ───────── métodos de leitura (não mudam nada) ─────────

@metodo_api('metodos')
def api_metodos(ctx, p, ev):
    return {n: {'muda': m} for n, (_, m) in sorted(METODOS_API.items())}


@metodo_api('versao')
def api_versao(ctx, p, ev):
    return {'versao': VERSAO, 'api': API_VERSAO, 'windows': WINDOWS, 'admin': bool(WINDOWS and eh_admin()),
            'python': sys.version.split()[0], 'casa': str(CASA)}


@metodo_api('aviso')
def api_aviso(ctx, p, ev):
    """O aviso de uso (o mesmo da CLI) e se já foi aceito."""
    return {'aceito': aviso_aceito(), 'versao': VERSAO_AVISO, 'pontos': [{'titulo': ti, 'texto': tx} for ti, tx in AVISO_PONTOS]}


@metodo_api('aceitar_aviso')
def api_aceitar_aviso(ctx, p, ev):
    """A pessoa leu e marcou "Li e quero continuar" na interface (o mesmo que digitar "entendi" na CLI)."""
    if p.get('li') is not True:
        raise ErroApi('pedido_invalido', 'o aceite precisa de {"li": true}')
    marca_estado('aviso_aceito', {'versao': VERSAO_AVISO, 'quando': agora_iso(), 'onde': 'interface'})
    return {'aceito': aviso_aceito()}


def _raiox_guardado():
    sec = (rel_carrega().get('secoes') or {})
    rx, pc = sec.get('raiox') or {}, sec.get('pc') or {}
    return rx.get('quando'), rx.get('dados') or {}, pc.get('dados') or {}


def _ultima_mudanca():
    """O pacote aplicado por último (não revertido), com quando e quantos itens."""
    ps = pacotes_aplicados_dt()
    if not ps:
        return None
    dt, nome, titulo = ps[-1]
    reg = (estado().get('pacotes') or {}).get(nome) or {}
    return {'pacote': nome, 'titulo': titulo, 'quando': dt.isoformat(timespec='minutes'), 'itens': len(reg.get('itens') or [])}


def _segundo_plano():
    a = le_agora()
    sp = (a or {}).get('segundo_plano') or {}
    return {'rodando': bool(a) and (sp_rodando() if WINDOWS else True), 'ligado': estado().get('segundo_plano') == 'sim',
            'cpu_pct': sp.get('cpu_pct'), 'ram_mb': sp.get('ram_mb'), 'intervalo_s': (a or {}).get('intervalo_s')}


@metodo_api('inicio')
def api_inicio(ctx, p, ev):
    """O que a tela Início mostra, só com o que já está guardado (abre na hora; nada roda)."""
    quando, rx, pc = _raiox_guardado()
    a = le_agora(max_idade_s=60)
    achados = [x for x in (rx.get('achados') or []) if (x.get('impacto') or 0) > 0]
    return {
        'raiox': {'quando': quando, 'nota': rx.get('nota'), 'achados': achados[:5], 'total': len(achados)} if quando else None,
        'pc': pc or None,
        'temperatura': ({'cpu': a.get('temp_cpu'), 'cpu_fonte': a.get('temp_cpu_fonte'), 'gpu': a.get('temp_gpu'),
                         'gpu_fonte': a.get('temp_gpu_fonte')} if a else None),
        'ultima_mudanca': _ultima_mudanca(),
        'segundo_plano': _segundo_plano(),
        'aviso_aceito': aviso_aceito(),
    }


@metodo_api('raiox')
def api_raiox(ctx, p, ev):
    """Roda o raio-x (só lê; leva 1 a 3 minutos) e devolve o mesmo que o terminal mostra, em dados."""
    if not WINDOWS:
        raise ErroApi('so_windows', 'o raio-x só roda no Windows')
    ev('etapa', {'texto': 'lendo o PC', 'n': 1, 'de': 3})
    perf = perfil_pc(ctx, forca=True)
    m = mede(ctx, 'medidas em repouso')
    ev('etapa', {'texto': 'analisando', 'n': 2, 'de': 3})
    s = roda_ps(ctx.t, DIAG_PS, 'raiox', minutos=8, mostra=False, mult=ctx.mult)
    salva_medida(m, 'raiox')
    achados = analisa(perf, m, s.dados)
    ctx.achados = achados
    queixas = [q for q in (p.get('queixas') or ['tudo']) if q in dict(QUEIXAS) or q == 'tudo']
    ev('etapa', {'texto': 'pronto', 'n': 3, 'de': 3})
    dados = raiox_dados(perf, m, s.dados, achados, queixas)
    rel_secao('raiox', dados)
    rel_pc(perf)
    dados['quando'] = agora_iso()
    dados['pesa'] = [{'titulo': ti, 'pontos': pt} for ti, pt in pesa_na_nota(achados)]
    dados['pc'] = {'modelo': f'{pf(perf, "pc.fabricante", "")} {pf(perf, "pc.modelo", "")}'.strip(), 'notebook': bool(pf(perf, 'pc.notebook')),
                   'windows': nome_windows(compat_windows(perf)), 'cpu': texto_cpu(perf), 'ram': texto_ram(perf),
                   'disco': texto_disco(perf), 'video': texto_video(perf)}
    return dados


def _pc_curto(pc):
    """O resumo do PC guardado no relatório, no mesmo formato do raio-x."""
    if not pc:
        return {}
    gb = lambda v: f'{br(v, 0)} GB' if isinstance(v, (int, float)) and v else ''
    return {'modelo': f'{pc.get("fabricante", "")} {pc.get("modelo", "")}'.strip(), 'notebook': bool(pc.get('notebook')),
            'windows': f'{pc.get("windows", "")} {pc.get("versao", "")}'.replace('Microsoft ', '').strip(),
            'cpu': str(pc.get('cpu') or ''), 'ram': gb(pc.get('ram_gb')),
            'disco': ' · '.join(x for x in (str(pc.get('disco') or ''), (gb(pc.get('disco_livre_gb')) + ' livres') if pc.get('disco_livre_gb') else '') if x),
            'video': ', '.join(str(g.get('nome') if isinstance(g, dict) else g) for g in (pc.get('gpus') or []))}


@metodo_api('raiox_guardado')
def api_raiox_guardado(ctx, p, ev):
    """O último raio-x, completo (todos os achados), sem rodar nada. null se ainda não teve."""
    quando, rx, pc = _raiox_guardado()
    if not quando:
        return None
    d = dict(rx)
    d['quando'] = quando
    d['pesa'] = sorted(({'titulo': a.get('titulo'), 'pontos': PESO_NOTA.get(a.get('impacto'), 0)} for a in (rx.get('achados') or [])
                        if PESO_NOTA.get(a.get('impacto'), 0)), key=lambda x: -x['pontos'])[:3]
    d['pc'] = _pc_curto(pc)
    return d


def _item_api(it, pac):
    return {'id': it.id, 'pacote': pac, 'titulo': it.titulo, 'explica': it.explica, 'ganho': it.ganho, 'custo': it.custo,
            'nivel': it.nivel, 'marcado': bool(it.marcado), 'ja': it.ja, 'alerta': it.alerta or '', 'nota': it.nota or '',
            'sem_volta': not it.reverte, 'grupo': it.grupo, 'conflita': sorted(it.conflita), 'recorrente': bool(it.recorrente)}


@metodo_api('itens')
def api_itens(ctx, p, ev):
    """As áreas e os itens deste PC, marcados pelo modo, com o "já está assim" conferido na hora se pedir (conferir: true; leva alguns
    segundos por área, em modo teste: nada muda)."""
    modo = p.get('modo') or config('modo')
    if modo not in MODOS:
        raise ErroApi('pedido_invalido', 'modo: ' + ', '.join(MODOS))
    if ctx.perfil is None:
        if WINDOWS:
            ev('etapa', {'texto': 'lendo o PC'})
            ctx.perfil = perfil_pc(ctx)
        else:   # fora do Windows (testes e site): o PC modelo, com tudo
            ctx.perfil = json.loads(json.dumps(PC_MODELO))
    pedidas = p.get('areas') or [n for n in ORDEM_TURBO if n in PACOTES] + [n for n in PACOTES if n not in ORDEM_TURBO]
    out = []
    for i, nome in enumerate(pedidas):
        if nome not in PACOTES:
            continue
        pac = PACOTES[nome]
        its = [x for x in (pac.itens(ctx) or []) if x]
        for x in its:
            x.pacote = nome
        its, _ = aplica_protegidos(nome, its)
        aplica_alertas(nome, its)
        marca_por_modo(its, modo)
        if p.get('conferir') and WINDOWS:
            ev('etapa', {'texto': f'conferindo {pac.titulo}', 'n': i + 1, 'de': len(pedidas)})
            confere_itens(ctx, its, nome)
        out.append({'nome': nome, 'titulo': pac.titulo, 'resumo': pac.resumo, 'explica': pac.explica, 'reversivel': pac.reversivel,
                    'recorrente': nome in PACOTES_RECORRENTES, 'vazio': SEM_ITENS.get(nome, '') if not its else '',
                    'itens': [_item_api(x, nome) for x in ordem_de_tela(its)]})
    return {'modo': modo, 'modos': list(MODOS), 'areas': out}


@metodo_api('aplicado')
def api_aplicado(ctx, p, ev):
    """O que está aplicado (pacotes não revertidos, com quando e quantos itens) e o que dá para desfazer."""
    e = estado()
    out = []
    for dt, nome, titulo in reversed(pacotes_aplicados_dt()):
        reg = (e.get('pacotes') or {}).get(nome) or {}
        out.append({'pacote': nome, 'titulo': titulo, 'quando': dt.isoformat(timespec='minutes'), 'itens': reg.get('itens') or [],
                    'desfaz': PACOTES[nome].reversivel})
    return {'pacotes': out, 'ponto': e.get('ultimo_ponto')}


@metodo_api('sugestoes')
def api_sugestoes(ctx, p, ev):
    """As propostas da central de inteligência, com o número que as justifica, e o que ela previu e aconteceu."""
    exporta_propostas(ctx)
    d = le_json(CASA / 'propostas.json', {}) or {}
    return {'quando': d.get('quando'), 'propostas': d.get('propostas') or [], 'resultados': d.get('resultados') or []}


@metodo_api('responder')
def api_responder(ctx, p, ev):
    """A resposta da pessoa a uma proposta ou resultado: sim (ajudou), nao, nao-importa."""
    id_, r = p.get('id'), p.get('resposta')
    if not isinstance(id_, str) or r not in ('sim', 'nao', 'nao-importa'):
        raise ErroApi('pedido_invalido', '{"id": "...", "resposta": "sim" | "nao" | "nao-importa"}')
    responde(id_, r)
    return {'ok': True}


@metodo_api('agora')
def api_agora(ctx, p, ev):
    """A leitura de agora do segundo plano (agora.json), ou null se ele não está rodando."""
    a = le_agora()
    if a:
        a.pop('_dt', None)
    return a


@metodo_api('sessoes')
def api_sessoes(ctx, p, ev):
    """As sessões de jogo gravadas, o resumo e o antes e depois de cada jogo."""
    dias = int(p.get('dias') or 60)
    ss = le_sessoes(dias)
    try:
        comp = comparacoes_por_jogo(ss, pacotes_aplicados_dt())
    except Exception as e:
        LOG.escreve(f'api sessoes: comparação falhou: {e!r}')
        comp = []
    for c in comp:
        if isinstance(c.get('quando'), datetime):
            c['quando'] = c['quando'].isoformat(timespec='minutes')
    resumo = resumo_sessoes(ss)
    return {'sessoes': [{k: v for k, v in x.items() if k != '_dt'} for x in ss[-200:]], 'resumo': resumo, 'comparacoes': comp}


@metodo_api('config_ler')
def api_config_ler(ctx, p, ev):
    return {k: {'valor': config(k), 'rotulo': DESCR_CONFIG.get(k, (k, ''))[0], 'explica': DESCR_CONFIG.get(k, ('', ''))[1],
                'opcoes': list(VALIDOS_CONFIG.get(k, ()))} for k in PADROES}


@metodo_api('config_gravar')
def api_config_gravar(ctx, p, ev):
    k, v = p.get('chave'), p.get('valor')
    if k not in PADROES:
        raise ErroApi('pedido_invalido', f'"{k}" não existe')
    if k in ('energia-automatica', 'fps'):   # têm passos (escolher planos, permissão do Windows): a interface usa o método próprio
        raise ErroApi('precisa_fluxo', f'"{k}" tem passos próprios; use o método dela')
    if not isinstance(v, str) or (k in VALIDOS_CONFIG and v not in VALIDOS_CONFIG[k]):
        raise ErroApi('pedido_invalido', f'valores aceitos para {k}: ' + ', '.join(VALIDOS_CONFIG.get(k, ('texto',))))
    salva_config(k, v)
    if WINDOWS and exe_instalado().is_file():
        escreve_config_sp()
    return {'chave': k, 'valor': config(k)}


# ───────── métodos que mudam o PC (rodam no motor elevado; pedem o aceite do aviso) ─────────

def _selecao(p):
    sel = p.get('itens')
    if not isinstance(sel, dict) or not sel or not all(isinstance(k, str) and isinstance(v, list) for k, v in sel.items()):
        raise ErroApi('pedido_invalido', '{"itens": {"pacote": ["id", ...]}}')
    ruins = [k for k in sel if k not in PACOTES]
    if ruins:
        raise ErroApi('pedido_invalido', 'pacote desconhecido: ' + ', '.join(ruins))
    return {k: [str(x) for x in v] for k, v in sel.items() if v}


def _com_trava(f):
    trava = Trava()
    if not trava.pega():
        raise ErroApi('ocupado', f'Outra janela do Katharos está mudando o PC agora (processo {trava.dona}). Espere ela terminar.')
    try:
        return f()
    finally:
        trava.solta()


@metodo_api('aplicar', muda=True)
def api_aplicar(ctx, p, ev):
    """Aplica exatamente os itens pedidos (a interface manda o que a pessoa deixou marcado), na ordem do turbo, com ponto de restauração
    antes, progresso por item e conferência depois (o que não ficou volta como "nao_ficou": sem falso positivo)."""
    sel = _selecao(p)

    def faz():
        if ctx.perfil is None:
            ctx.perfil = perfil_pc(ctx)
        ev('etapa', {'texto': 'criando o ponto de restauração'})
        garante_ponto(ctx)
        ordem = [n for n in ORDEM_TURBO if n in sel] + [n for n in sel if n not in ORDEM_TURBO]

        def ouvinte(rotulo, n, total, atual):
            ev('progresso', {'rotulo': rotulo, 'n': n, 'de': total, 'item': atual})
        OUVINTES_PROGRESSO.append(ouvinte)
        res = []
        try:
            for k, nome in enumerate(ordem):
                pac = PACOTES[nome]
                ids = set(sel[nome])
                its = [x for x in (pac.itens(ctx) or []) if x and x.id in ids]
                for x in its:
                    x.pacote = nome
                its, fora = aplica_protegidos(nome, its)
                ev('pacote', {'nome': nome, 'titulo': pac.titulo, 'n': k + 1, 'de': len(ordem), 'itens': len(its)})
                if not its:
                    res.append({'pacote': nome, 'titulo': pac.titulo, 'itens': 0, 'feitos': 0, 'avisos': [], 'erros': [],
                                'nao_ficou': [], 'ignorados': sorted(ids)})
                    continue
                livre_ant = livre_bytes()
                ctx.ultimos_eventos = []
                feitos, avisos, erros = executa_itens(ctx, pac, its)
                evs = getattr(ctx, 'ultimos_eventos', []) or []
                nao_ficou = []
                if nome in REAPLICA and feitos:
                    nao_ficou = verifica_pacote(ctx, nome, [i.id for i in its])
                    if nao_ficou:
                        rel_eventos([{'tipo': 'nao-ficou', 'pacote': nome, 'texto': '; '.join(nao_ficou[:6])}])
                livre_dep = livre_bytes()
                cache_ja = getattr(ctx, 'ja', None)
                if cache_ja:
                    for chave in [c for c in cache_ja if c[0] == nome]:
                        del cache_ja[chave]
                res.append({'pacote': nome, 'titulo': pac.titulo, 'itens': len(its), 'feitos': feitos,
                            'avisos': [a for e in evs for a in e.get('avisos', [])], 'erros': [a for e in evs for a in e.get('erros', [])],
                            'nao_ficou': nao_ficou, 'ignorados': sorted(ids - {i.id for i in its}),
                            'liberado': (livre_dep - livre_ant) if livre_ant is not None and livre_dep is not None and livre_dep > livre_ant else 0,
                            'desfaz': pac.reversivel})
        finally:
            OUVINTES_PROGRESSO.remove(ouvinte)
        try:
            for nome in ordem:
                marca_propostas_feitas(nome)
            exporta_propostas(ctx)
        except Exception as ex:
            LOG.escreve(f'api aplicar: pensar depois falhou: {ex!r}')
        arriscados = [n for n in ordem if n in RISCO_ALTO and any(r['feitos'] for r in res if r['pacote'] == n)]
        return {'pacotes': res, 'confirmar': str(config('confirmar') or 'risco'),
                'perguntar_manter': arriscados if str(config('confirmar') or 'risco') != 'nunca' else []}
    return _com_trava(faz)


@metodo_api('desfazer', muda=True)
def api_desfazer(ctx, p, ev):
    """Volta pacotes aplicados (o mesmo backup do desfazer da CLI). {"pacotes": ["servicos", ...]}."""
    nomes = p.get('pacotes')
    if not isinstance(nomes, list) or not nomes or not all(n in PACOTES for n in nomes):
        raise ErroApi('pedido_invalido', '{"pacotes": ["nome", ...]} com pacotes que existem')

    def faz():
        res = []
        for k, n in enumerate(nomes):
            ev('pacote', {'nome': n, 'titulo': PACOTES[n].titulo, 'n': k + 1, 'de': len(nomes)})
            tem = WINDOWS and (dir_backup() / n / 'mudancas.jsonl').exists()
            cod = desfaz_pacote(ctx, n) if tem else 0
            # "ok" só quando havia o que voltar e o desfazer terminou sem erro; "nada" quando não havia backup deste pacote
            res.append({'pacote': n, 'titulo': PACOTES[n].titulo, 'ok': bool(tem and cod == 0), 'nada': not tem})
        try:
            marca_propostas_feitas('desfazer')
            exporta_propostas(ctx)
        except Exception as ex:
            LOG.escreve(f'api desfazer: pensar depois falhou: {ex!r}')
        return {'pacotes': res}
    return _com_trava(faz)


# ───────── motor elevado: a mesma API num pipe com nome, só para quem tem a senha da sessão ─────────
# A interface roda como o usuário. Para mudar o PC, ela abre este mesmo programa como administrador (um UAC por sessão) com
#   katharos api --pipe NOME --dono SID --senha SENHA
# Segurança: o pipe só aceita o SID do dono e o SYSTEM (ACL), uma conexão só (FILE_FLAG_FIRST_PIPE_INSTANCE, 1 instância, sem rede),
# e a primeira linha precisa ser a senha de uso único que a interface gerou e passou na linha de comando do processo elevado (um
# processo comum não lê a linha de comando de um processo elevado). Sem a senha certa, o motor fecha. Quando a interface desconecta,
# o motor elevado sai.

def _pipe_servidor(nome, sid):
    """Cria o pipe com a ACL do dono e espera a interface conectar. Devolve (leitor, escritor) em bytes."""
    import msvcrt
    from ctypes import wintypes
    k32, adv = ctypes.WinDLL('kernel32', use_last_error=True), ctypes.WinDLL('advapi32', use_last_error=True)
    if not re.fullmatch(r'S-1-5-21(-\d+){3,4}', sid or ''):
        raise ErroApi('pedido_invalido', 'SID do dono inválido')
    if not re.fullmatch(r'[A-Za-z0-9_.-]{8,80}', nome or ''):
        raise ErroApi('pedido_invalido', 'nome de pipe inválido')

    class SA(ctypes.Structure):
        _fields_ = [('nLength', wintypes.DWORD), ('lpSecurityDescriptor', ctypes.c_void_p), ('bInheritHandle', wintypes.BOOL)]
    sd = ctypes.c_void_p()
    if not adv.ConvertStringSecurityDescriptorToSecurityDescriptorW(f'D:P(A;;GA;;;{sid})(A;;GA;;;SY)', 1, ctypes.byref(sd), None):
        raise OSError(ctypes.get_last_error(), 'descritor de segurança do pipe')
    sa = SA(ctypes.sizeof(SA), sd, False)
    PIPE_ACCESS_DUPLEX, FIRST, REJ_REMOTO = 0x3, 0x00080000, 0x8
    k32.CreateNamedPipeW.restype = wintypes.HANDLE
    h = k32.CreateNamedPipeW('\\\\.\\pipe\\' + nome, PIPE_ACCESS_DUPLEX | FIRST, REJ_REMOTO, 1, 65536, 65536, 0, ctypes.byref(sa))
    if not h or h == wintypes.HANDLE(-1).value:
        raise OSError(ctypes.get_last_error(), 'criar o pipe')
    if not k32.ConnectNamedPipe(wintypes.HANDLE(h), None) and ctypes.get_last_error() != 535:   # 535: já conectou antes da chamada
        raise OSError(ctypes.get_last_error(), 'esperar a interface')
    fd = msvcrt.open_osfhandle(h, 0)
    return os.fdopen(fd, 'rb', buffering=0), os.fdopen(os.dup(fd), 'wb', buffering=0)


class _TextoPipe:
    """Linhas de texto UTF-8 sobre o pipe (o canal da API espera write/flush; o laço espera iterar linhas)."""

    def __init__(self, leitor, escritor):
        self.leitor, self.escritor = leitor, escritor

    def write(self, s):
        self.escritor.write(s.encode('utf-8'))

    def flush(self):
        try:
            self.escritor.flush()
        except OSError:
            pass

    def __iter__(self):
        buf = b''
        while True:
            try:
                bloco = self.leitor.read(65536)
            except OSError:
                return
            if not bloco:
                return
            buf += bloco
            while b'\n' in buf:
                linha, buf = buf.split(b'\n', 1)
                yield linha.decode('utf-8', 'replace')


def roda_api_elevada(nome, sid, senha):
    """O motor elevado: espera a interface no pipe, confere a senha da sessão na primeira linha e então atende como a API normal."""
    import hmac
    leitor, escritor = _pipe_servidor(nome, sid)
    canal = _TextoPipe(leitor, escritor)
    linhas = iter(canal)
    primeira = next(linhas, '')
    try:
        dada = json.loads(primeira).get('senha', '')
    except (ValueError, AttributeError):
        dada = ''
    if not (isinstance(dada, str) and senha and hmac.compare_digest(dada, senha)):
        LOG.escreve('motor elevado: senha errada na conexão; fechando')
        canal.write(json.dumps({'id': None, 'ok': False, 'erro': {'codigo': 'senha', 'texto': 'senha da sessão errada'}}) + '\n')
        return 3
    return roda_api([], entrada=linhas, saida=canal)


@metodo_api('segundo_plano')
def api_segundo_plano(ctx, p, ev):
    """Liga ou desliga o acompanhamento (o ícone perto do relógio). Roda como o usuário. Só diz "rodando" se o processo está mesmo de pé."""
    if not WINDOWS:
        raise ErroApi('so_windows', 'o acompanhamento só roda no Windows')
    if not exe_disponivel():
        raise ErroApi('sem_exe', 'O Katharos.exe não está junto do programa: reinstale o Katharos.')
    if p.get('ligar') is True:
        ok = instala_segundo_plano(ctx, mostrar=False)
        for _ in range(20):
            if sp_rodando():
                break
            time.sleep(0.25)
        if not (ok and sp_rodando()):
            raise ErroApi('nao_ligou', 'O acompanhamento não abriu. Veja ~/.katharos/segundo-plano.log.')
    elif p.get('ligar') is False:
        remove_segundo_plano(ctx)
    return _segundo_plano()


@metodo_api('historico')
def api_historico(ctx, p, ev):
    """O PC ao longo do tempo (substitui o painel em HTML): cada medida por dia (mediana), as marcas de quando cada mudança entrou,
    o efeito de cada mudança (com veredito honesto: melhorou, piorou, sem diferença, já vinha mudando, poucas medidas) e o que está
    mudando agora."""
    am = le_metricas()
    dias = int(p.get('dias') or 60)
    corte = datetime.now() - timedelta(days=dias)
    pacotes = pacotes_aplicados_dt()
    series = []
    for chave, rot, melhor, casas, un in METRICAS_EFEITO:
        s = [(d, v) for d, v in _serie(am, chave) if d >= corte]
        if not s:
            continue
        por_dia = {}
        for d, v in s:
            por_dia.setdefault(d.date(), []).append(v)
        pontos = [{'dia': dia.isoformat(), 'v': round(sorted(vs)[len(vs) // 2], casas)} for dia, vs in sorted(por_dia.items())]
        series.append({'chave': chave, 'rotulo': rot, 'melhor': melhor, 'unidade': un, 'casas': casas, 'pontos': pontos})
    efeitos = []
    for titulo, quando, cel in tabela_efeito(am, pacotes):
        efeitos.append({'titulo': titulo, 'quando': quando.isoformat(timespec='minutes'),
                        'medidas': [{'rotulo': r, 'veredito': v, 'antes': round(a, c) if isinstance(a, (int, float)) else a,
                                     'depois': round(b, c) if isinstance(b, (int, float)) else b, 'casas': c, 'unidade': u} for r, v, a, b, c, u in cel]})
    return {'series': series, 'marcas': [{'quando': q.isoformat(timespec='minutes'), 'titulo': t} for q, _, t in pacotes if q >= corte],
            'efeitos': efeitos, 'tendencia': [t for _, t in analisa_tendencia(am)], 'amostras': len(am)}
