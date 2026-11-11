# ─────────────── detectores, causas, planejador, avaliador e explicações (I8 a I11, I13, I15) ───────────────
#  detectores  → ACHADOS: cada um olha um tipo de dado e diz o que viu, com números, duração, contexto, fonte e confiança
#  causas      → DIAGNÓSTICO: um mapa em dados (CAUSAS) diz que achados confirmam ou descartam cada causa; a de mais pontos ganha,
#                e as descartadas aparecem com o motivo
#  planejador  → a proposta de cada causa (o comando, a previsão, o risco e como desfazer), pesada pelo que já funcionou neste PC
#  avaliador   → resultado medido de cada coisa aplicada mexe no peso daquele alvo neste PC; o que piorou vira proposta de desfazer
#  explicações → sempre quatro partes: o que eu vi, por que acho que é isso, o que eu faria, o que mudaria minha conclusão
# Nada aqui aplica coisa alguma: só propõe. Pouco dado dá "ainda não sei", nunca alarme.

def _achado(id_, tipo, titulo, vi, sintomas, conf, fonte, contexto='', numeros=None, gravidade=2, duracao_min=None):
    return {'id': id_, 'tipo': tipo, 'titulo': titulo, 'vi': vi, 'sintomas': list(sintomas), 'confianca': conf, 'fonte': fonte,
            'contexto': contexto, 'numeros': numeros or {}, 'gravidade': gravidade, 'duracao_min': duracao_min}


DETECTORES = []


def detector(f):
    DETECTORES.append(f)
    return f


@detector
def d_limite_sustentado(ev):
    """Nas sessões de jogo: o que ficou no limite por uma fração relevante do tempo jogado."""
    r = resumo_sessoes(ev.get('sessoes') or [])
    if not r or r['horas'] < REGRAS_MOTOR['central_horas_min'] or r['sessoes'] < 2:   # uma sessão só não conclui nada
        return []
    dias = len({s['_dt'].date() for s in ev.get('sessoes') or [] if s.get('_dt')})
    conf = confianca(int(r['horas'] * 60), dias, r['sessoes'])
    if not conf:
        return []
    out = []
    nomes = {'cpu': ('CPU no limite', 'cpu_limite'), 'gpu': ('placa de vídeo no limite', 'gpu_limite'), 'freio': ('CPU freando', 'freio'),
             'calor': ('calor acima do seguro', 'calor'), 'ram': ('RAM cheia', 'ram_cheia'), 'vram': ('memória de vídeo cheia', 'vram_cheia'),
             'disco': ('disco 100 % ocupado', 'disco_cheio')}
    for chave, (nome, sint) in nomes.items():
        pct = (r['limites'] or {}).get(chave, 0)
        if pct >= REGRAS_MOTOR['central_' + chave]:
            out.append(_achado(f'limite-{chave}', 'limite', f'{nome[0].upper()}{nome[1:]} nos jogos',
                               f'em {r["sessoes"]} sessões de jogo ({br(r["horas"], 1)} h), {nome} em {br(pct, 0)} % do tempo',
                               [sint, 'jogo'], conf, 'sessões do segundo plano', 'jogo', {'pct': pct, 'horas': r['horas'], 'sessoes': r['sessoes']},
                               3 if chave in ('calor', 'freio') else 2, round(r['horas'] * 60 * pct / 100)))
    if r.get('temp_cpu_max') or r.get('temp_gpu_max'):
        out.append(_achado('tem-sensor', 'contexto', 'Há leitura de temperatura', 'o segundo plano leu temperatura nas sessões', ['tem_sensor'], conf, 'sessões'))
    return out


@detector
def d_fps(ev):
    """FPS medido (PresentMon): travadas e 1 % low muito abaixo da média; travadas sem nenhum limite apontam para driver."""
    ss = [s for s in ev.get('sessoes') or [] if isinstance(s.get('fps_med'), (int, float)) and (s.get('min') or 0) >= 5]
    if len(ss) < 2:
        return []
    trav = [s.get('travadas_por_min') or 0 for s in ss]
    med_trav = _mediana_lista(trav)
    razao = _mediana_lista([s['fps_1low'] / s['fps_med'] for s in ss if s.get('fps_1low') and s['fps_med']])
    conf = confianca(sum(int(s['min']) for s in ss), len({s['_dt'].date() for s in ss if s.get('_dt')}), len(ss))
    if not conf:
        return []
    out = []
    if med_trav >= 1 or (razao is not None and razao < 0.5):
        sem_limite = [s for s in ss if max((s.get('tempo_no_limite') or {}).values() or [0]) < 10]
        out.append(_achado('fps-travadas', 'fps', 'Travadas nos jogos', f'mediana de {br(med_trav, 1)} travadas por minuto e 1 % low em '
                           f'{br(100 * (razao or 0), 0)} % do FPS médio, em {len(ss)} sessões', ['travadas'] + (['sem_limite'] if len(sem_limite) * 2 >= len(ss) else []),
                           conf, 'PresentMon (eventos do Windows)', 'jogo', {'travadas_por_min': med_trav, 'razao_1low': razao, 'sessoes_sem_limite': len(sem_limite)}, 3))
    return out


@detector
def d_anomalia(ev):
    """Últimas 24 h fora do normal deste PC (linha de base, mesmo contexto)."""
    out = []
    for s in r_fora_do_normal(ev):
        met = s['metrica']
        out.append(_achado(f'anomalia-{met}', 'anomalia', s['titulo'], s['porque'][0].lower() + s['porque'][1:].rstrip('.'),
                           [f'{met}_acima', 'repouso'], s['confianca'], 'minutos do segundo plano', 'sem_jogo', {'metrica': met}))
    return out


@detector
def d_tendencia(ev):
    """Piorando há dias: medidas diárias (espaço, boot, RAM, CPU, temperatura) com direção firme."""
    ach = _achados_tendencia(ev)
    out = []
    sint = {'livre_c': 'espaco_caindo', 'boot_s': 'boot_lento', 'ram_usada': 'ram_subindo', 'cpu': 'cpu_acima', 'temperatura': 'calor_repouso',
            'inicializacao': 'inicializacao_cresceu'}
    for chave, txt in ach.items():
        if chave in sint:
            out.append(_achado(f'tendencia-{chave}', 'tendencia', 'Mudando com o tempo', txt[0] if isinstance(txt, tuple) else str(txt),
                               [sint[chave]], 'média', 'medidas diárias', 'repouso', {'chave': chave}))
    return out


@detector
def d_piora_pos_mudanca(ev):
    """Depois de uma mudança, algo piorou além da oscilação (e não vinha piorando antes)."""
    out = []
    for s in r_efeito_dos_pacotes(ev) + r_jogo_antes_depois(ev):
        out.append(_achado('piora-' + s['id'], 'piora', s['titulo'], s['porque'].rstrip('.'), ['piorou_depois'], s['confianca'],
                           'medidas antes e depois', '', {'comando': s['comando']}, 3))
    return out


@detector
def d_eventos_windows(ev):
    """Tela azul, driver com erro, disco com erro: do motor de saúde (registro de eventos do Windows)."""
    out = []
    for x in ((ev.get('saude') or {}).get('problemas') or [])[:8]:
        sint = ['evento_windows']
        txt = (x.get('titulo', '') + ' ' + x.get('id', '')).lower()
        if any(p in txt for p in ('tela azul', 'bugcheck', 'bsod', 'whea')):
            sint.append('tela_azul')
        if 'driver' in txt:
            sint.append('driver_erro')
        if 'disco' in txt or 'disk' in txt or 'ntfs' in txt:
            sint.append('disco_erro')
        out.append(_achado('windows-' + x['id'], 'evento', x['titulo'], str(x.get('evidencia') or ''), sint,
                           {'alta': 'alta', 'média': 'média'}.get(x.get('gravidade'), 'baixa'), 'eventos do Windows', '', {}, 3 if x.get('gravidade') == 'alta' else 2))
    return out


@detector
def d_raiox(ev):
    """O que o raio-x mediu e importa para diagnóstico (DPC alto, paginação em HD, pouca RAM, energia em economia)."""
    rx = ev.get('raiox') or {}
    out = []
    dpc = (rx.get('medidas') or {}).get('dpc')
    if isinstance(dpc, (int, float)) and dpc >= 5:
        out.append(_achado('raiox-dpc', 'limite', 'Drivers segurando o processador', f'o raio-x mediu {br(dpc, 1)} % do tempo da CPU em DPC (o normal é abaixo de 2 %)',
                           ['dpc_alto'], 'média', 'raio-x', '', {'dpc': dpc}, 3))
    perfil = ev.get('perfil') or {}
    if (perfil.get('memoria') or {}).get('pagefile_discos') and any(d.get('tipo') == 'HDD' for d in perfil['memoria']['pagefile_discos'] if isinstance(d, dict)):
        out.append(_achado('raiox-pagefile-hd', 'contexto', 'Paginação num HD', 'o arquivo de paginação está num HD', ['pagefile_hd'], 'alta', 'raio-x'))
    if any(m.get('bateria') for m in (ev.get('minutos') or [])[-60:]):
        out.append(_achado('na-bateria', 'contexto', 'Notebook na bateria', 'parte das leituras recentes foi na bateria', ['bateria'], 'alta', 'segundo plano'))
    return out


def detecta(ev):
    """Roda todos os detectores (um com defeito não derruba os outros). Achados com confiança None (ainda não sei) ficam de fora."""
    out = []
    for d in DETECTORES:
        try:
            out += [a for a in (d(ev) or []) if a.get('confianca')]
        except Exception as ex:
            LOG.escreve(f'detector {d.__name__} falhou: {ex!r}')
    return out


# ───────── mapa de causas (dados: sintoma → causas → o que confirma, o que descarta → ação) ─────────
# confirma: {sintoma: pontos}; descarta: [sintoma] (se algum aparecer, a causa sai, com o motivo); precisa: sintomas que a causa exige.
CAUSAS = [
    {'id': 'calor', 'problema': 'jogos', 'nome': 'calor', 'precisa': ['calor'], 'confirma': {'calor': 3, 'freio': 2, 'calor_repouso': 1},
     'descarta': [], 'acao': 'energia', 'faria': 'usar o plano de energia que segura o pico e limpar poeira e pasta térmica (o que resolve de verdade)',
     'previsao': {'chave': 'calor', 'texto': 'menos tempo acima do limite de temperatura'}, 'risco': 'nenhum: o plano volta com o desfazer'},
    {'id': 'economia', 'problema': 'jogos', 'nome': 'economia de energia', 'precisa': ['freio'], 'confirma': {'freio': 2, 'bateria': 3},
     'descarta': ['calor'], 'acao': 'energia', 'faria': 'plano de energia de desempenho na tomada (no notebook, ligar a troca automática)',
     'previsao': {'chave': 'freio', 'texto': 'a CPU deixa de frear com carga'}, 'risco': 'mais consumo de energia'},
    {'id': 'cpu', 'problema': 'jogos', 'nome': 'a CPU', 'precisa': ['cpu_limite'], 'confirma': {'cpu_limite': 3, 'cpu_acima': 1},
     'descarta': ['freio', 'calor'], 'acao': 'turbo', 'faria': 'menos coisa rodando junto e a CPU com energia no máximo',
     'previsao': {'chave': 'cpu', 'texto': 'menos tempo com a CPU no limite'}, 'risco': 'mais consumo de energia'},
    {'id': 'gpu', 'problema': 'jogos', 'nome': 'a placa de vídeo (já no máximo)', 'precisa': ['gpu_limite'], 'confirma': {'gpu_limite': 2},
     'descarta': ['cpu_limite', 'calor', 'freio'], 'acao': '', 'faria': 'nada no Windows: baixar resolução ou qualidade no jogo, ou ligar DLSS/FSR',
     'previsao': None, 'risco': ''},
    {'id': 'ram', 'problema': 'jogos', 'nome': 'RAM cheia', 'precisa': ['ram_cheia'], 'confirma': {'ram_cheia': 3, 'ram_subindo': 1, 'pagefile_hd': 1},
     'descarta': [], 'acao': 'memoria', 'faria': 'ver quem ocupa a RAM e tirar da inicialização o que não precisa abrir com o Windows',
     'previsao': {'chave': 'ram', 'texto': 'menos tempo com a RAM cheia'}, 'risco': 'nenhum: só leitura; você escolhe o que fechar'},
    {'id': 'vram', 'problema': 'jogos', 'nome': 'memória de vídeo cheia', 'precisa': ['vram_cheia'], 'confirma': {'vram_cheia': 3, 'travadas': 1},
     'descarta': [], 'acao': '', 'faria': 'baixar a qualidade das texturas no jogo', 'previsao': None, 'risco': ''},
    {'id': 'disco', 'problema': 'jogos', 'nome': 'o disco', 'precisa': ['disco_cheio'], 'confirma': {'disco_cheio': 3, 'pagefile_hd': 2, 'disco_erro': 2},
     'descarta': [], 'acao': 'raiox', 'faria': 'conferir no raio-x o tipo de disco, o espaço e quem escreve nele', 'previsao': None, 'risco': 'nenhum: só leitura'},
    {'id': 'driver', 'problema': 'travadas', 'nome': 'um driver segurando o processador', 'precisa': ['travadas'],
     'confirma': {'travadas': 1, 'sem_limite': 3, 'dpc_alto': 3, 'driver_erro': 1}, 'descarta': ['ram_cheia', 'vram_cheia', 'disco_cheio', 'calor'],
     'acao': 'travadas', 'faria': 'rodar o teste de travadas (1 minuto) para dizer qual driver é',
     'previsao': None, 'risco': 'nenhum: só leitura'},
    {'id': 'repouso-cpu', 'problema': 'pc', 'nome': 'algo ocupando a CPU fora dos jogos', 'precisa': ['cpu_acima'], 'confirma': {'cpu_acima': 3, 'repouso': 1},
     'descarta': [], 'acao': 'raiox', 'faria': 'ver no raio-x quem gasta a CPU', 'previsao': None, 'risco': 'nenhum: só leitura'},
    {'id': 'repouso-ram', 'problema': 'pc', 'nome': 'RAM ocupada fora dos jogos', 'precisa': ['ram_acima'], 'confirma': {'ram_acima': 3, 'ram_subindo': 2},
     'descarta': [], 'acao': 'memoria', 'faria': 'ver quem ocupa a memória', 'previsao': None, 'risco': 'nenhum: só leitura'},
    {'id': 'boot', 'problema': 'pc', 'nome': 'programas demais ao ligar', 'precisa': ['boot_lento'], 'confirma': {'boot_lento': 2, 'inicializacao_cresceu': 3},
     'descarta': [], 'acao': 'inicializacao', 'faria': 'tirar da inicialização o que pesa (o Windows mede quanto cada um atrasa)',
     'previsao': {'chave': 'boot_s', 'texto': 'boot mais rápido'}, 'risco': 'baixo: o programa continua instalado'},
    {'id': 'estabilidade', 'problema': 'pc', 'nome': 'instabilidade do Windows', 'precisa': ['tela_azul'], 'confirma': {'tela_azul': 3, 'driver_erro': 2},
     'descarta': [], 'acao': 'saude', 'faria': 'ver na saúde do Windows o que falhou e quando', 'previsao': None, 'risco': 'nenhum: só leitura'},
]
PROBLEMAS = {'jogos': 'O que segura os seus jogos', 'travadas': 'Por que os jogos travam', 'pc': 'O que pesa no PC'}
_NOME_SINTOMA = {'calor': 'calor acima do seguro', 'freio': 'CPU freando', 'cpu_limite': 'CPU no limite', 'gpu_limite': 'placa de vídeo no limite',
                 'ram_cheia': 'RAM cheia', 'vram_cheia': 'memória de vídeo cheia', 'disco_cheio': 'disco ocupado', 'bateria': 'na bateria',
                 'travadas': 'travadas', 'sem_limite': 'travadas sem nenhum limite', 'dpc_alto': 'DPC alto', 'driver_erro': 'erro de driver',
                 'pagefile_hd': 'paginação num HD', 'tela_azul': 'tela azul', 'cpu_acima': 'CPU acima do normal', 'ram_acima': 'RAM acima do normal',
                 'boot_lento': 'boot mais lento', 'inicializacao_cresceu': 'mais programas na inicialização', 'ram_subindo': 'RAM subindo',
                 'calor_repouso': 'temperatura subindo', 'disco_erro': 'erro de disco', 'repouso': 'fora dos jogos'}


def diagnostica(achados):
    """Para cada problema com sintoma: as causas pontuadas pelas evidências; a escolhida e as descartadas com o motivo."""
    presentes = {}
    for a in achados:
        for s in a['sintomas']:
            presentes.setdefault(s, a)
    out = []
    for prob, titulo in PROBLEMAS.items():
        cands, descartadas = [], []
        for c in (c for c in CAUSAS if c['problema'] == prob):
            if not all(p in presentes for p in c['precisa']):
                continue
            contra = [s for s in c['descarta'] if s in presentes]
            pontos = sum(v for s, v in c['confirma'].items() if s in presentes)
            if contra:
                descartadas.append({'causa': c['nome'], 'motivo': 'descartada: ' + ', '.join(_NOME_SINTOMA.get(s, s) for s in contra) + ' explica melhor'})
                continue
            confs = [presentes[s]['confianca'] for s in c['confirma'] if s in presentes]
            conf = max(confs, key=lambda x: ORDEM_CONF.get(x, 3)) if confs else 'baixa'   # a evidência mais fraca manda
            cands.append({'causa': c, 'pontos': pontos, 'confianca': conf,
                          'evidencias': [presentes[s]['vi'] for s in c['confirma'] if s in presentes]})
        if not cands:
            continue
        cands.sort(key=lambda x: (-x['pontos'], x['causa']['id']))
        esc = cands[0]
        for c in cands[1:]:
            descartadas.append({'causa': c['causa']['nome'], 'motivo': f'menos provável ({c["pontos"]} pontos contra {esc["pontos"]})'})
        out.append({'problema': prob, 'titulo': titulo, 'causa': esc['causa']['id'], 'nome': esc['causa']['nome'], 'pontos': esc['pontos'],
                    'confianca': esc['confianca'], 'evidencias': esc['evidencias'], 'descartadas': descartadas, 'acao': esc['causa']['acao'],
                    'faria': esc['causa']['faria'], 'previsao': esc['causa']['previsao'], 'risco': esc['causa']['risco'],
                    'mudaria': _o_que_mudaria(esc['causa'], presentes)})
    return out


def _o_que_mudaria(causa, presentes):
    falta = [s for s in causa['confirma'] if s not in presentes]
    contra = causa['descarta']
    partes = []
    if contra:
        partes.append('se aparecer ' + ' ou '.join(_NOME_SINTOMA.get(s, s) for s in contra[:2]))
    if falta:
        partes.append('se ' + ' e '.join(_NOME_SINTOMA.get(s, s) for s in falta[:2]) + ' também aparecer, a confiança sobe')
    return '; '.join(partes) or 'mais sessões medidas confirmam ou descartam'


def explica(d):
    """As quatro partes de toda explicação, de um diagnóstico."""
    return {'vi': '; '.join(d['evidencias'][:3]) + '.', 'porque': f'A causa mais provável é {d["nome"]}'
            + (('. Descartei: ' + '; '.join(f'{x["causa"]} ({x["motivo"]})' for x in d['descartadas'][:3])) if d['descartadas'] else '') + '.',
            'faria': d['faria'][0].upper() + d['faria'][1:] + '.', 'mudaria': d['mudaria'][0].upper() + d['mudaria'][1:] + '.'}


# ───────── planejador ─────────

def _desfazer_de(comando):
    nome = (comando or '').split(' ')[0]
    return f'katharos desfazer {nome}' if nome in PACOTES else ('não muda nada no PC' if nome else '')


def planeja(sugestoes, diagnosticos, pesos=None, protegidos=()):
    """Junta a central (regras) com o diagnóstico: cada proposta ganha a explicação da causa quando bate o comando; causa sem proposta
    vira proposta. O peso aprendido neste PC multiplica os pontos. Nada específico de jogo (o mapa não tem item por jogo)."""
    pesos = pesos or {}
    por_cmd = {x['comando']: x for x in sugestoes if x.get('comando')}
    out = list(sugestoes)
    for d in diagnosticos:
        exp = explica(d)
        alvo = por_cmd.get(d['acao']) if d['acao'] else None
        if alvo:
            alvo['explicacao'] = exp
            alvo['causa'] = d['causa']
            continue
        if d['acao'] in protegidos:
            continue
        s = _sug(f'causa-{d["causa"]}', f'{d["titulo"]}: {d["nome"]}', exp['vi'][0].upper() + exp['vi'][1:], d['acao'],
                 d['confianca'] if d['confianca'] in PESO_CONF else 'baixa', d['faria'], d['risco'], min(5, 2 + d['pontos'] // 2), 0 if 'nenhum' in (d['risco'] or 'nenhum') else 1,
                 tipo='acao' if d['acao'] else 'info',
                 previsao=({'fonte': 'sessoes', 'chave': d['previsao']['chave'], 'delta': None, 'un': '', 'texto': d['previsao']['texto']} if d.get('previsao') else None))
        s['explicacao'] = exp
        s['causa'] = d['causa']
        out.append(s)
        if d['acao']:
            por_cmd[d['acao']] = s
    for x in out:
        x.setdefault('explicacao', {'vi': x['porque'], 'porque': '', 'faria': x.get('impacto') or '', 'mudaria': ''})
        x['desfazer'] = _desfazer_de(x.get('comando'))
        p = pesos.get((x.get('comando') or '').split(' ')[0])
        if p and x['tipo'] == 'acao':
            x['pontos'] = round(x['pontos'] * p, 2)
            x['peso_neste_pc'] = p
    return sorted(out, key=lambda x: (ORDEM_CONF.get(x['confianca'], 3), -x['pontos'], x['id']))


# ───────── avaliador ─────────
FATOR_VEREDITO = {'como previsto': 1.15, 'em parte': 1.0, 'sem diferença': 0.85, 'piorou': 0.6}


def avalia(ev):
    """Cada resultado medido pela primeira vez mexe no peso do alvo neste PC; o que piorou vira proposta de desfazer."""
    feitos = ev.get('feitos') or {}
    vistas = ev.get('vistas') or {}
    props = []
    for r in resultados_previstos({'conselheiro_feitos': feitos}, ev.get('minutos') or [], ev.get('sessoes') or [], ev['agora']):
        if r['veredito'] not in FATOR_VEREDITO:
            continue
        cmd = ((vistas.get(r['id']) or {}).get('comando') or '').split(' ')[0]
        if memoria_grava_resultado(r['id'], r['quando'].isoformat(), r['veredito'], {k: r.get(k) for k in ('antes', 'depois', 'un', 'previsto')}) and cmd:
            memoria_ajusta_peso(cmd, FATOR_VEREDITO[r['veredito']])
        if r['veredito'] == 'piorou' and cmd in PACOTES and not ((estado().get('pacotes') or {}).get(cmd) or {}).get('revertido'):
            props.append(_sug(f'desfazer:{cmd}', f'Desfazer {PACOTES[cmd].titulo}: piorou o que eu previ que melhoraria',
                              f'Previ {r["previsto"]}; medi {br(r["antes"], 0)} → {br(r["depois"], 0)} {r["un"]}.', f'desfazer {cmd}', 'média',
                              'volta cada valor ao que era antes', 'nenhum', 4, 0))
    return props


# ───────── tudo junto ─────────

def pensa(ev):
    """O ciclo inteiro: achados → diagnóstico → propostas (central + causas + avaliador), com explicação. Grava os achados na memória."""
    achados = detecta(ev)
    diags = diagnostica(achados)
    try:
        memoria_grava_achados(achados, ev.get('agora'))
    except Exception as ex:
        LOG.escreve(f'achados na memória: {ex!r}')
    sug = gera_sugestoes(ev)
    try:
        sug += [x for x in avalia(ev) if x['id'] not in {s['id'] for s in sug}]
    except Exception as ex:
        LOG.escreve(f'avaliador: {ex!r}')
    nunca = {x.strip().lower() for x in re.split(r'[,;\s]+', str(config('motor-nunca') or '')) if x.strip()}
    prot = set()
    props = planeja(sug, diags, memoria_pesos(), prot | nunca)
    props = [p for p in props if (p.get('comando') or '').split(' ')[0] not in nunca]
    return {'achados': achados, 'diagnosticos': diags, 'propostas': props}


# ───────── orçamento de avisos (I15) ─────────

def pode_avisar(e, tipo, agora=None, grave=False, em_jogo=False):
    """No máximo um aviso por tipo a cada N horas (config avisos-intervalo); nada durante o jogo salvo o grave (calor)."""
    agora = agora or datetime.now()
    if em_jogo and not grave:
        return False
    try:
        horas = float(str(config('avisos-intervalo') or 6).replace(',', '.'))
    except (TypeError, ValueError):
        horas = 6.0
    ult = (e.get('avisos_por_tipo') or {}).get(tipo)
    return not recente_h(ult, horas)


def marca_aviso(e, tipo, agora=None):
    e.setdefault('avisos_por_tipo', {})[tipo] = (agora or datetime.now()).replace(microsecond=0).isoformat()
