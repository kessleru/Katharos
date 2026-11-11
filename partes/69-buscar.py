# ──────────────────────────────────────────────────────────────────────────────
# Buscar: acha um item ou um comando pelo que a pessoa digitou, sem precisar saber em que área ele mora.
# Não depende de acento nem de maiúscula, entende algumas palavras do dia a dia ("propaganda", "esquenta")
# e, se nada bate, tenta a palavra mais parecida. Só lê; aplicar continua sendo na tela da área.
# ──────────────────────────────────────────────────────────────────────────────

# palavra que a pessoa usa → palavras que aparecem nos itens
SINONIMOS = {
    # autenticidade
    'sha': ('autenticidade',), 'sha256': ('autenticidade',), 'hash': ('autenticidade',), 'assinatura': ('autenticidade',), 'original': ('autenticidade',), 'adulterado': ('autenticidade',),
    # privacidade
    'propaganda': ('anuncio', 'sugest'), 'propagandas': ('anuncio', 'sugest'), 'ads': ('anuncio',), 'anuncios': ('anuncio',),
    'publicidade': ('anuncio', 'sugest'), 'sugestao': ('sugest',), 'sugestoes': ('sugest',), 'dica': ('sugest', 'dicas'),
    'espionagem': ('telemetria', 'diagnostico'), 'espiao': ('telemetria',), 'espionar': ('telemetria',), 'rastreio': ('telemetria', 'rastre'),
    'rastreamento': ('telemetria', 'rastre'), 'dados': ('telemetria', 'diagnostico'), 'coleta': ('telemetria',), 'tracking': ('telemetria', 'rastre'),
    'ia': ('copilot', 'recall', 'inteligencia'), 'ai': ('copilot', 'recall'), 'bing': ('busca na web', 'bing', 'pesquisa'),
    'noticias': ('widgets', 'noticia'), 'clima': ('widgets',), 'localizacao': ('localiza',), 'gps': ('localiza',),
    'microfone': ('microfone', 'voz'), 'webcam': ('camera',), 'historico': ('historico', 'atividade'), 'cortana': ('cortana', 'copilot'),
    'edge': ('edge',), 'onedrive': ('onedrive',), 'conta': ('conta', 'microsoft 365'),
    # rede
    'internet': ('rede', 'dns', 'wi-fi'), 'wifi': ('wi-fi', 'rede'), 'wi-fi': ('wi-fi', 'rede'), 'net': ('rede', 'dns'),
    'ping': ('rede', 'latencia', 'nagle'), 'lag': ('rede', 'latencia', 'jogo'), 'latencia': ('latencia', 'nagle', 'rede'),
    'download': ('rede', 'otimizacao de entrega', 'update'), 'upload': ('p2p', 'compartilhar'), 'conexao': ('rede',), 'cabo': ('rede', 'ethernet'),
    'roteador': ('rede', 'dns'), 'navegador': ('edge', 'chrome', 'brave', 'cache'),
    # jogos e vídeo
    'fps': ('jogo', 'gpu', 'video'), 'game': ('jogo',), 'games': ('jogo',), 'gamer': ('jogo',), 'jogar': ('jogo',),
    'engasgo': ('jogo', 'dvr', 'latencia'), 'stutter': ('jogo', 'dvr'), 'travadinha': ('jogo', 'dvr'), 'gravacao': ('dvr', 'captura'),
    'xbox': ('xbox', 'game bar', 'dvr'), 'gamebar': ('game bar', 'dvr'), 'placa': ('gpu', 'video'), 'gpu': ('gpu', 'video'),
    'nvidia': ('nvidia', 'gpu'), 'amd': ('amd', 'radeon', 'gpu'), 'radeon': ('amd', 'radeon'), 'shader': ('shader',), 'shaders': ('shader',),
    'tela-cheia': ('tela cheia', 'fullscreen'), 'fullscreen': ('tela cheia',), 'hz': ('taxa', 'monitor'), 'vsync': ('vsync', 'sincroniza'),
    'input': ('latencia', 'mouse'), 'prioridade': ('prioridade',),
    # calor, energia, bateria
    'esquenta': ('temperatura', 'fresco', 'calor', 'turbo'), 'esquentando': ('temperatura', 'fresco', 'calor'), 'quente': ('temperatura', 'fresco', 'calor'),
    'calor': ('fresco', 'calor', 'temperatura'), 'temperatura': ('temperatura', 'fresco', 'termic'), 'ventoinha': ('fresco', 'calor', 'temperatura'),
    'cooler': ('fresco', 'calor'), 'fan': ('fresco', 'ventoinha'), 'barulho': ('fresco', 'ventoinha'), 'barulhento': ('fresco', 'ventoinha'),
    'bateria': ('bateria', 'energia', 'economia'), 'carregador': ('tomada', 'energia'), 'energia': ('energia', 'plano'), 'economia': ('economia', 'energia'),
    'suspender': ('suspens', 'hibern'), 'hibernar': ('hibern',), 'hibernacao': ('hibern',), 'dormir': ('suspens', 'hibern'),
    'desligar': ('desliga', 'inicializacao rapida'), 'tampa': ('tampa', 'energia'), 'usb': ('usb',), 'desempenho': ('desempenho', 'plano'),
    # espaço e disco
    'lixo': ('temporario', 'cache', 'limp'), 'lixeira': ('lixeira',), 'espaco': ('limp', 'cache', 'temporario', 'disco'), 'cheio': ('limp', 'espaco'),
    'liberar': ('limp', 'cache', 'temporario'), 'limpar': ('limp', 'cache', 'temporario'), 'limpeza': ('limp', 'cache'), 'temp': ('temporario',),
    'temporarios': ('temporario',), 'cache': ('cache',), 'downloads': ('download',), 'duplicados': ('grandes', 'arquivo'), 'grandes': ('grandes',),
    'hd': ('hd', 'disco', 'desfragment'), 'ssd': ('ssd', 'trim'), 'desfragmentar': ('desfragment', 'otimizar a unidade'), 'defrag': ('desfragment',),
    'paginacao': ('paginacao', 'memoria virtual'), 'pagefile': ('paginacao',), 'swap': ('paginacao', 'memoria virtual'),
    'indexacao': ('indexa', 'busca'), 'pesquisa': ('indexa', 'busca', 'pesquisa'), 'windows.old': ('windows.old', 'versao anterior'),
    # lentidão, boot, memória
    'ligar': ('boot', 'inicializ'), 'iniciar': ('boot', 'inicializ'), 'demora': ('boot', 'inicializ'), 'boot': ('boot', 'inicializ'),
    'startup': ('inicializ',), 'inicio': ('inicializ', 'iniciar'), 'abrindo': ('inicializ',), 'sozinho': ('inicializ', 'automatic'),
    'travando': ('servico', 'inicializ', 'memoria'), 'trava': ('servico', 'inicializ', 'memoria'), 'lento': ('servico', 'inicializ', 'visual'),
    'lerdo': ('servico', 'inicializ', 'visual'), 'devagar': ('servico', 'inicializ', 'visual'), 'rapido': ('desempenho', 'inicializ'),
    'acelerar': ('desempenho', 'inicializ', 'visual'), 'otimizar': ('desempenho', 'otimiz'), 'memoria': ('ram', 'memoria'), 'ram': ('ram', 'memoria'),
    'processos': ('servico', 'segundo plano'), 'fundo': ('segundo plano',), 'background': ('segundo plano',), 'servicos': ('servico',),
    'tarefas': ('tarefa',), 'agendadas': ('tarefa',),
    # aparência
    'animacao': ('animac', 'efeito'), 'animacoes': ('animac', 'efeito'), 'efeitos': ('efeito', 'animac', 'transpar'), 'transparencia': ('transpar',),
    'escuro': ('tema escuro', 'escuro'), 'dark': ('tema escuro', 'escuro'), 'tema': ('tema',), 'barra': ('barra de tarefas', 'barra'),
    'taskbar': ('barra de tarefas',), 'iniciar-menu': ('menu iniciar',), 'menu': ('menu',), 'icones': ('icone',), 'widgets': ('widgets',),
    'fonte': ('fonte',), 'fontes': ('fonte',), 'tela': ('tela', 'monitor', 'visual'), 'monitor': ('monitor', 'tela'),
    'explorer': ('explorador', 'explorer', 'pasta'), 'pastas': ('pasta', 'explorador'), 'extensoes': ('extens',), 'ocultos': ('oculto',),
    'clique': ('clique', 'menu de contexto'), 'contexto': ('menu de contexto',), 'notificacoes': ('notifica',), 'notificacao': ('notifica',),
    # programas
    'bloatware': ('fabrica', 'apps', 'remov'), 'bloat': ('fabrica', 'apps', 'remov'), 'desinstalar': ('remov', 'desinstal'), 'remover': ('remov',),
    'apps': ('apps', 'app'), 'programas': ('programa',), 'fabrica': ('fabrica',), 'mcafee': ('mcafee', 'antivirus'), 'norton': ('norton', 'antivirus'),
    'antivirus': ('antivirus', 'defender'), 'virus': ('defender', 'antivirus', 'verifica', 'autenticidade'), 'office': ('office', 'microsoft 365'),
    'teams': ('teams',), 'skype': ('skype',), 'candy': ('apps', 'instalados sozinhos'), 'tiktok': ('apps', 'instalados sozinhos'),
    # sistema
    'atualizacao': ('update', 'atualiz'), 'atualizacoes': ('update', 'atualiz'), 'update': ('update', 'atualiz'), 'updates': ('update', 'atualiz'),
    'driver': ('driver',), 'drivers': ('driver',), 'reparar': ('repar', 'sfc', 'dism'), 'consertar': ('repar',), 'corrompido': ('repar', 'sfc'),
    'erro': ('repar', 'erro'), 'azul': ('repar', 'tela azul'), 'bsod': ('repar', 'tela azul'), 'restaurar': ('restaura',), 'backup': ('restaura', 'backup'),
    'voltar': ('desfaz', 'restaura'), 'undo': ('desfaz',), 'reverter': ('desfaz',), 'seguranca': ('seguranca', 'defender'),
    'senha': ('senha', 'credencia'), 'firewall': ('firewall',), 'remoto': ('remot',), 'impressora': ('impress', 'spooler'), 'imprimir': ('impress', 'spooler'),
    'bluetooth': ('bluetooth',), 'som': ('audio', 'som'), 'audio': ('audio', 'som'), 'mouse': ('mouse', 'ponteiro'), 'teclado': ('teclado', 'tecla'),
    'touchpad': ('touchpad',), 'numlock': ('num lock',), 'agendar': ('agend', 'manutenc'), 'automatico': ('agend', 'automatic', 'segundo plano'),
    'relatorio': ('relatorio',), 'grafico': ('painel', 'grafico'), 'graficos': ('painel', 'grafico'), 'nota': ('raiox', 'nota'),
    'diagnostico': ('raiox', 'diagnostico', 'saude'), 'medir': ('medir', 'benchmark'), 'teste': ('benchmark', 'medir'), 'velocidade': ('benchmark', 'medir'),
}


def sem_acento(txt):
    return unicodedata.normalize('NFKD', str(txt).lower()).encode('ascii', 'ignore').decode()


# palavras de uma frase que não ajudam a achar nada ("como tirar a propaganda do meu pc")
VAZIAS = set('a o as os um uma de do da dos das no na nos nas em para pra por com sem e ou que como meu minha meus minhas pc computador notebook '
             'windows tirar tira quero queria preciso fazer deixar deixa mais menos muito pouco esta estou fica ficar ficando ter tem '
             'se eu ele ela isso esse essa este esta aqui la nao sim ja so the to of my how'.split())


def _palavras(texto):
    todas = [w for w in re.findall(r'[a-z0-9\-\.]+', sem_acento(texto)) if len(w) >= 2 or w.isdigit()]
    uteis = [w for w in todas if w not in VAZIAS]
    return uteis or todas


def _pontos(palavras, campos):
    """Quanto um texto casa com a busca: cada palavra (ou um sinônimo dela) precisa aparecer em algum campo.
    campos: [(texto já sem acento, peso)]. 0 se alguma palavra não aparece em lugar nenhum."""
    total = 0
    for w in palavras:
        melhor = 0
        for alvo, peso_alvo in [(w, 1.0)] + [(s, 0.6) for s in SINONIMOS.get(w, ())]:
            for txt, peso in campos:
                if alvo in txt:
                    melhor = max(melhor, peso * peso_alvo * (1.5 if re.search(r'\b' + re.escape(alvo), txt) else 1))
        if not melhor:
            return 0
        total += melhor
    return total


def indice_busca(ctx):
    """Tudo que dá para achar: os comandos e os itens de cada área deste PC. [(tipo, área, id, título, campos, item)]"""
    out = []
    for cmd, (desc, _) in COMANDOS.items():
        if cmd in ('manutencao', 'amostrar'):
            continue
        out.append(('comando', cmd, cmd, desc, [(sem_acento(cmd), 4), (sem_acento(desc), 2)], None))
    for nome, pac in PACOTES.items():
        try:
            itens = [i for i in (pac.itens(ctx) or []) if i]
        except Exception as e:   # uma área que não se monta neste PC não pode derrubar a busca
            LOG.escreve(f'busca: {nome} não montou: {e!r}')
            continue
        for it in itens:
            campos = [(sem_acento(it.titulo), 4), (sem_acento(it.id), 3), (sem_acento(it.explica), 1.5),
                      (sem_acento(f'{it.ganho} {it.custo} {it.alerta}'), 1), (sem_acento(f'{nome} {pac.titulo}'), 1)]
            out.append(('item', nome, it.id, it.titulo, campos, it))
    return out


def busca(indice, texto, limite=12):
    """Os resultados em ordem de relevância: [(pontos, tipo, área, id, título, item)]. Sem nada exato, tenta a
    palavra mais parecida que existe nos títulos (erro de digitação)."""
    palavras = _palavras(texto)
    if not palavras:
        return []
    def roda(pals):
        achados = [(p, tipo, area, id_, titulo, item) for tipo, area, id_, titulo, campos, item in indice
                   for p in [_pontos(pals, campos)] if p]
        return sorted(achados, key=lambda x: (-x[0], x[1] != 'comando', x[2], x[4]))[:limite]
    r = roda(palavras)
    if not r:
        import difflib
        vocabulario = sorted({w for _, _, _, _, campos, _ in indice for txt, _ in campos[:2] for w in re.findall(r'[a-z0-9]{4,}', txt)})
        perto = [(difflib.get_close_matches(w, vocabulario, n=1, cutoff=0.75) or [w])[0] for w in palavras]
        if perto != palavras:
            r = roda(perto)
    if not r and len(palavras) > 1:   # frase comprida: vale o que casar com a maior parte das palavras
        soma = {}
        for w in palavras:
            for p, tipo, area, id_, titulo, item in roda([w]):
                ch = (tipo, area, id_)
                ant = soma.get(ch, (0, 0, None))
                soma[ch] = (ant[0] + 1, ant[1] + p, (tipo, area, id_, titulo, item))
        minimo = (len(palavras) + 1) // 2
        r = sorted(((pts, *resto) for n, pts, resto in soma.values() if n >= minimo), key=lambda x: -x[0])[:limite]
    return r


def ferramenta_buscar(ctx, args):
    t = ctx.t
    t.aba('acha um ajuste ou um comando pelo que você digitar')
    texto = ' '.join(getattr(args, 'texto', None) or []).strip()
    if not texto and t.interativo:
        texto = t.pergunta('o que você procura (ex.: telemetria, anúncios, boot, ventoinha)').strip()
    if not texto:
        t.nota('  Use: katharos buscar telemetria')
        return 0
    perfil_pc(ctx)
    r = busca(indice_busca(ctx), texto)
    if not r:
        t.aviso(f'Não achei nada para "{corta(texto, 30)}". Tente outra palavra, ou abra "escolher" no menu para ver as áreas.')
        return 0
    t.titulo(f'"{corta(texto, 30)}" · {pl(len(r), "resultado", "resultados")}')
    for n, (_, tipo, area, id_, titulo, item) in enumerate(r, 1):
        onde = 'comando' if tipo == 'comando' else f'{area} · {NOME_NIVEL.get(item.nivel, "")}'
        t.escreve(f'  {t.p(f"{n:>2}", "destaque", True)}  {t.p(id_ if tipo == "comando" else titulo, "texto")}  {t.p(onde, "apagado")}')
        t.paragrafo(titulo if tipo == 'comando' else item.explica.split('. ')[0].rstrip('.') + '.', 6, 'sub')
    if not t.interativo or getattr(args, 'sim', False):
        t.escreve()
        t.nota('  Para abrir um resultado: katharos e o nome da área (a primeira palavra em cinza).')
        return 0
    t.escreve()
    t.dicas([('número', 'abrir esse resultado'), ('Enter', 'voltar')])
    esc = t.pergunta('abrir').strip()
    if not esc.isdigit() or not 0 < int(esc) <= len(r):
        return 0
    _, tipo, area, id_, _, _ = r[int(esc) - 1]
    if tipo == 'item':
        ctx.itens_busca = {area: {id_}}   # a área abre só com este item marcado
    ctx.proximos = [area] + [c for c in ctx.proximos if c != area]
    ctx.direto = True
    return 0


def responde_pergunta(texto, ctx=None):
    """I25: "por que meu jogo trava?" → o que o motor concluiu que bate com a pergunta, e os comandos e itens que tratam disso.
    Tudo local, pelos mesmos sinônimos da busca. Sem nada que bata, diz que não sabe (e o que medir para saber)."""
    texto = str(texto or '')[:500]   # pergunta é uma frase: texto enorme não vira trabalho nem volta inteiro na resposta
    palavras = _palavras(texto)
    d = le_json(CASA / 'propostas.json', {}) or {}
    # sem exigir todas as palavras: conta quantas batem (pergunta é frase, não busca)
    def casa_parcial(*txts):
        alvo = [(sem_acento(str(t or '')), 1) for t in txts]
        return sum(1 for w in palavras if _pontos([w], alvo))
    diags = sorted(((casa_parcial(x.get('titulo'), x.get('nome'), ' '.join(x.get('evidencias') or []), x.get('problema'),
                                  {'jogos': 'jogo jogos fps lento', 'travadas': 'trava travadas engasga stutter', 'pc': 'pc lento devagar'}.get(x.get('problema'), '')), x)
                    for x in d.get('diagnosticos') or []), key=lambda t: -t[0])
    props = sorted(((casa_parcial(x.get('titulo'), x.get('porque'), x.get('comando')), x) for x in d.get('propostas') or []), key=lambda t: -t[0])
    achados = sorted(((casa_parcial(x.get('titulo'), x.get('vi')), x) for x in d.get('achados') or []), key=lambda t: -t[0])
    try:
        cmds = busca(indice_busca(ctx), texto, 6) if ctx is not None else []
    except Exception as ex:
        LOG.escreve(f'perguntar: busca falhou: {ex!r}')
        cmds = []
    out = {'pergunta': texto, 'diagnosticos': [x for n, x in diags if n][:2], 'propostas': [x for n, x in props if n][:3],
           'achados': [x for n, x in achados if n][:3],
           'comandos': [{'tipo': tipo, 'area': area, 'id': id_, 'titulo': titulo} for _, tipo, area, id_, titulo, _ in cmds]}
    if out['diagnosticos']:
        g = out['diagnosticos'][0]
        out['resposta'] = f'{g["titulo"]}: {g["nome"]}. ' + (('O que eu vi: ' + '; '.join(g.get('evidencias') or [])[:300] + '. ') if g.get('evidencias') else '') + \
                          (g.get('faria') or '')[:1].upper() + (g.get('faria') or '')[1:] + '.'
    elif out['propostas']:
        x = out['propostas'][0]
        out['resposta'] = f'{x["titulo"]}. {x.get("porque") or ""}'.strip()
    elif out['achados']:
        out['resposta'] = (out['achados'][0].get('titulo') or '') + ': ' + (out['achados'][0].get('vi') or '') + '.'
    else:
        out['resposta'] = ('Ainda não sei: não tenho medida que responda isso. Com o segundo plano ligado e algumas sessões de jogo, '
                           'eu consigo dizer o que segura o PC.' if not d else 'Não achei nada medido que responda isso; os comandos abaixo tratam do assunto.')
    return out
