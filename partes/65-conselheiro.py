# ─────────────── motor de inteligência: junta tudo o que o Katharos sabe e propõe, com prova, o que mudar ───────────────
# Pipeline:  coletor de evidências → regras independentes → pontuação → memória → aprendizado.
#  1. COLETOR     medidas do segundo plano, benchmarks, pacotes aplicados, eventos/erros do relatório, achados do raio-x, perfil do PC.
#  2. REGRAS      cada regra olha as evidências e devolve propostas (ou nada). Regra nova = uma função com @regra.
#  3. PONTUAÇÃO   pontos = impacto × confiança ÷ (1 + risco). A ordem de exibição vem daqui.
#  4. MEMÓRIA     o que a pessoa dispensa não volta por 30 dias; o que já foi mostrado fica registrado com a data.
#  5. APRENDIZADO quando a pessoa executa uma proposta, o motor mede 7 dias depois se a métrica visada mudou além do ruído
#                 e mostra o resultado (inclusive "sem diferença mensurável"): a confiança nas propostas vem de resultado, não de promessa.
# Princípios: só propõe o que a evidência mostra; toda proposta carrega o número que a justifica; nunca aplica sozinho;
# quando não sabe, diz que não sabe; não culpa um pacote por algo que já vinha piorando antes dele.
ORDEM_CONF = {'alta': 0, 'média': 1, 'baixa': 2}
PESO_CONF = {'alta': 1.0, 'média': 0.6, 'baixa': 0.3}
DISPENSA_DIAS = 30
ALVO_METRICA = {'espaco': 'livre_c', 'boot': 'boot_s', 'ram': 'ram_usada', 'cpu': 'cpu'}
METRICAS_EFEITO = [('boot_s', 'o tempo de boot', 'menor', 0, 's'), ('ram_usada', 'a RAM em uso', 'menor', 1, 'GB'),
                   ('livre_c', 'o espaço livre em C:', 'maior', 0, 'GB'), ('cpu', 'a CPU em repouso', 'menor', 0, '%'),
                   ('inicializacao', 'os programas que abrem com o Windows', 'menor', 0, ''), ('processos', 'o número de processos', 'menor', 0, '')]
REGRAS = []


def regra(f):
    REGRAS.append(f)
    return f


def _sug(id_, titulo, porque, comando, conf, impacto='', risco='', pontos_impacto=3, risco_n=0, metrica='', tipo='acao', previsao=None):
    return {'id': id_, 'titulo': titulo, 'porque': porque, 'comando': comando, 'confianca': conf, 'impacto': impacto, 'risco': risco,
            'impacto_n': pontos_impacto, 'risco_n': risco_n, 'metrica': metrica, 'tipo': tipo, 'previsao': previsao,
            'pontos': round(pontos_impacto * PESO_CONF[conf] / (1 + risco_n), 2)}


def pacotes_aplicados_dt():
    """[(datetime, nome, título)] dos pacotes aplicados e não revertidos."""
    out = []
    for nome, reg in (estado().get('pacotes') or {}).items():
        try:
            if nome in PACOTES and not reg.get('revertido'):
                out.append((datetime.fromisoformat(reg['quando']), nome, PACOTES[nome].titulo))
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(out)


def coleta_evidencias(ctx=None, agora=None):
    """Tudo o que o Katharos sabe, num dicionário só. Fonte que falhar vira vazio: o motor trabalha com o que tem."""
    e = estado()
    try:
        rel = rel_carrega()
    except Exception as ex:  # relatório corrompido não pode derrubar o conselheiro
        LOG.escreve(f'conselheiro sem relatório: {ex!r}')
        rel = {'eventos': [], 'secoes': {}}
    return {'amostras': le_metricas(), 'benchs': benchs_para_painel(), 'pacotes': pacotes_aplicados_dt(),
            'eventos': rel.get('eventos') or [], 'raiox': ((rel.get('secoes') or {}).get('raiox') or {}).get('dados') or {},
            'dispensadas': e.get('conselheiro_dispensadas') or {}, 'vistas': e.get('conselheiro_vistas') or {},
            'saude': (le_saude() or {}).get('analise') or {}, 'termica': analisa_termica(le_horas()), 'fundo_ligado': bool(e.get('manut_freq')) or e.get('segundo_plano') == 'sim',
            'agora': agora or datetime.now(), 'perfil': getattr(ctx, 'perfil', None) or {},
            'sessoes': le_sessoes(60, agora), 'minutos': le_minutos(24 * BASE_DIAS + 24, agora), 'segundo_plano': e.get('segundo_plano') == 'sim',
            'respostas': e.get('conselheiro_respostas') or {}, 'feitos': e.get('conselheiro_feitos') or {}, 'travadas': travadas_recente()}


# ───────── regras ─────────

@regra
def r_ligar_fundo(ev):
    if ev.get('segundo_plano') or ev.get('minutos') or ev['fundo_ligado'] or ev['amostras']:
        return []
    sem_nada = True
    return [_sug('ligar-fundo', 'Ligar o acompanhamento em segundo plano para eu pensar com dados de verdade',
                 ('Ainda não há nenhuma medida deste PC: sem medidas eu só chutaria. ' if sem_nada else '') +
                 'Com o segundo plano, eu vejo o PC segundo a segundo e em cada jogo: o que segura o FPS, calor, RAM cheia, CPU freando.',
                 'segundo-plano', 'alta', 'métricas ao vivo no ícone, sessões de jogo e propostas com base nelas',
                 'nenhum: uns 30 a 60 MB de RAM, em prioridade baixa; desliga quando quiser', 4 if sem_nada else 3, 0)]


# ───────── o que as sessões de jogo e o tempo real dizem ─────────

@regra
def r_jogos_gargalo(ev):
    """Nas sessões de jogo dos últimos 30 dias, o que mais ficou no limite (ponderado pelo tempo jogado)."""
    r = resumo_sessoes(ev.get('sessoes') or [])
    if not r or r['horas'] < REGRAS_MOTOR['central_horas_min']:
        return []
    lim, h, n = r['limites'], br(r['horas'], 1), r['sessoes']
    base = f'Em {n} {"sessão" if n == 1 else "sessões"} de jogo ({h} h), '
    out = []
    dias = len({s['_dt'].date() for s in ev.get('sessoes') or [] if s.get('_dt')})
    conf = confianca(int(r['horas'] * 60), dias, n)   # cada minuto jogado é uma leitura; repetição = sessões
    if not conf:
        return []
    conf_info = conf
    def prev(chave, quanto):
        return {'fonte': 'sessoes', 'chave': chave, 'delta': -quanto, 'un': '% do tempo', 'texto': f'menos tempo com {NOMES_LIMITE.get(chave, chave)}'}
    if lim.get('cpu', 0) >= REGRAS_MOTOR['central_cpu']:
        out.append(_sug('jogo-cpu', 'A CPU segura seus jogos',
                        base + f'um núcleo da CPU ficou no limite com a placa de vídeo sobrando em {br(lim["cpu"], 0)} % do tempo. '
                        'Menos coisa rodando junto e a CPU no máximo de energia (turbo no modo extremo) dão FPS de verdade aqui.', 'turbo', conf,
                        'menos serviços e programas disputando a CPU; plano de energia no máximo', 'mais consumo de energia', 4, 1, tipo='acao',
                        previsao=prev('cpu', lim['cpu'] / 3)))
        out.append(_sug('jogo-cpu-inicio', 'Tirar da inicialização o que pesa durante o jogo', base + 'a CPU foi o limite. Cada programa que abre com o Windows '
                        'fica disputando ela durante o jogo.', 'inicializacao', {'alta': 'média'}.get(conf, 'baixa'), 'menos processos em segundo plano', 'nenhum: você escolhe cada um', 3, 0,
                        previsao=prev('cpu', lim['cpu'] / 4)))
    if lim.get('freio', 0) >= REGRAS_MOTOR['central_freio']:
        out.append(_sug('jogo-freio', 'A CPU freia durante os jogos',
                        base + f'com carga, ela rodou abaixo de 75 % da frequência normal em {br(lim["freio"], 0)} % do tempo'
                        + (f' (chegou a {br(r["desempenho_min"], 0)} %)' if r.get('desempenho_min') else '') +
                        '. Isso é calor ou o plano de energia economizando.', 'energia', conf, 'plano de energia no máximo; se continuar, é calor (limpeza e pasta térmica)', 'mais consumo', 4, 1,
                        previsao=prev('freio', lim['freio'] / 2)))
    if lim.get('calor', 0) >= REGRAS_MOTOR['central_calor']:
        mx = max([x for x in (r.get('temp_cpu_max'), r.get('temp_gpu_max')) if x] or [0])
        out.append(_sug('jogo-calor', 'Seus jogos esquentam o PC além do seguro',
                        base + f'a temperatura passou do limite em {br(lim["calor"], 0)} % do tempo (máxima de {br(mx, 0)} °C). '
                        'Acima disso o chip reduz a velocidade e o FPS cai sozinho.', 'painel', conf,
                        'o histórico mostra quando e quanto; poeira, ventoinha e pasta térmica resolvem de verdade', 'nenhum: só leitura', 4, 0))
    if lim.get('ram', 0) >= REGRAS_MOTOR['central_ram']:
        out.append(_sug('jogo-ram', 'A RAM enche durante os jogos',
                        base + f'a RAM passou de 90 % em {br(lim["ram"], 0)} % do tempo. Aí o Windows usa o disco no lugar e o jogo engasga.',
                        'memoria', conf, 'mostra quem ocupa a RAM e o que dá para fechar ou tirar da inicialização', 'nenhum: só leitura', 4, 0,
                        previsao=prev('ram', lim['ram'] / 2)))
    if lim.get('vram', 0) >= REGRAS_MOTOR['central_vram']:
        out.append(_sug('jogo-vram', 'A memória da placa de vídeo enche nos jogos',
                        base + f'ela ficou acima de 95 % em {br(lim["vram"], 0)} % do tempo. Baixar a qualidade das texturas no jogo tira as travadas.',
                        '', 'média', 'travadas curtas somem', 'texturas menos nítidas', 3, 0, tipo='info'))
    if lim.get('disco', 0) >= REGRAS_MOTOR['central_disco']:
        out.append(_sug('jogo-disco', 'O disco trava seus jogos',
                        base + f'o disco ficou 100 % ocupado em {br(lim["disco"], 0)} % do tempo. Jogo num HD ou disco quase cheio faz isso.',
                        'raiox', 'média', 'o raio-x mostra o tipo de disco, o espaço e quem escreve nele', 'nenhum: só leitura', 3, 0))
    if not out and lim.get('gpu', 0) >= REGRAS_MOTOR['central_gpu']:
        out.append(_sug('jogo-gpu', 'Seus jogos já usam tudo da placa de vídeo',
                        base + f'ela ficou no limite em {br(lim["gpu"], 0)} % do tempo, com a CPU sobrando. O PC já entrega o máximo dela: '
                        'mais FPS só baixando resolução ou qualidade no jogo (ou ativando DLSS/FSR, se o jogo tiver).',
                        '', conf_info, 'nada a otimizar no Windows para isso', '', 2, 0, tipo='info'))
    return out


@regra
def r_tempo_real_repouso(ev):
    """Fora de jogo, nos minutos da última semana: CPU ocupada por muito tempo ou RAM sempre cheia."""
    mins = [m for m in (ev.get('minutos') or []) if not m.get('jogo')]
    if len(mins) < REGRAS_MOTOR['repouso_minutos_min']:
        return []
    out = []
    cpu_alta = sum(1 for m in mins if isinstance(m.get('cpu'), (int, float)) and m['cpu'] >= REGRAS_MOTOR['repouso_cpu'])
    if cpu_alta / len(mins) >= REGRAS_MOTOR['repouso_cpu_fracao']:
        out.append(_sug('repouso-cpu', 'Algo mantém a CPU ocupada fora dos jogos',
                        f'Na última semana, sem jogo aberto, a CPU ficou acima de 60 % em {br(100 * cpu_alta / len(mins), 0)} % dos minutos medidos.',
                        'raiox', confianca(len(mins), len({m['_dt'].date() for m in mins})) or 'baixa', 'o raio-x mostra quem gasta', 'nenhum: só leitura', 3, 0, 'cpu'))
    ram_alta = sum(1 for m in mins if isinstance(m.get('ram'), (int, float)) and m['ram'] >= REGRAS_MOTOR['repouso_ram'])
    if ram_alta / len(mins) >= REGRAS_MOTOR['repouso_ram_fracao']:
        out.append(_sug('repouso-ram', 'A RAM vive cheia', f'Na última semana, a RAM ficou acima de 85 % em {br(100 * ram_alta / len(mins), 0)} % dos minutos medidos.',
                        'memoria', confianca(len(mins), len({m['_dt'].date() for m in mins})) or 'baixa', 'mostra quem ocupa e o que tirar da inicialização', 'nenhum: só leitura', 3, 0, 'ram'))
    return out


def _achados_tendencia(ev):
    return dict(analisa_tendencia(ev['amostras'])) if ev['amostras'] else {}


@regra
def r_espaco(ev):
    ach = _achados_tendencia(ev)
    proj = projecao_enchimento(_serie(ev['amostras'], 'livre_c'))
    if 'livre_c' not in ach or not proj:
        return []
    return [_sug('espaco', 'Liberar espaço antes que o disco encha', ach['livre_c'][0].upper() + ach['livre_c'][1:] + f'. Projeção: cheio por volta de {proj[1]:%d/%m}.',
                 'limpar', 'alta' if proj[0] < 30 else 'média', 'recupera o que é lixo (temporários, caches, instaladores); para o que é seu use "grandes"',
                 'baixo: arquivos pessoais vão para a Lixeira', 5 if proj[0] < 30 else 4, 1, 'livre_c')]


@regra
def r_boot(ev):
    ach = _achados_tendencia(ev)
    if 'boot_s' not in ach:
        return []
    extra = ' Também subiu a quantidade de programas na inicialização.' if 'inicializacao' in ach else ''
    return [_sug('boot', 'Rever o que abre junto com o Windows', ach['boot_s'][0].upper() + ach['boot_s'][1:] + '.' + extra, 'inicializacao',
                 'alta' if 'inicializacao' in ach else 'média', 'o próprio Windows mede quanto cada programa atrasa o boot e o item mostra esse número',
                 'baixo: o programa continua instalado e você reabre quando quiser', 4, 1, 'boot_s')]


@regra
def r_ram(ev):
    am = ev['amostras']
    ultimo = am[-1] if am else {}
    if not ultimo.get('ram_total'):
        return []
    usado = ultimo.get('ram_usada', 0) / ultimo['ram_total']
    ach = _achados_tendencia(ev)
    if 'ram_usada' in ach:
        return [_sug('ram', 'A RAM em uso cresceu: ver quem está gastando', ach['ram_usada'][0].upper() + ach['ram_usada'][1:] + f' (agora {int(usado * 100)}% do total).',
                     'memoria', 'alta' if usado >= 0.8 else 'média', 'mostra os processos que mais ocupam e o que dá para fechar', 'nenhum: só leitura', 4 if usado >= 0.8 else 3, 0, 'ram_usada')]
    if usado >= 0.85 and len(am) >= 6:
        return [_sug('ram', 'RAM quase cheia', f'{int(usado * 100)}% de {br(ultimo["ram_total"], 0)} GB em uso na última medida. O Windows começa a usar o disco no lugar da memória.',
                     'memoria', 'média', 'ver quem gasta e fechar o que não precisa', 'nenhum: só leitura', 4, 0, 'ram_usada')]
    return []


@regra
def r_cpu(ev):
    ach = _achados_tendencia(ev)
    if 'cpu' not in ach:
        return []
    return [_sug('cpu', 'Algo novo mantém a CPU ocupada em repouso', ach['cpu'][0].upper() + ach['cpu'][1:] + '.', 'raiox', 'média',
                 'o raio-x lista os processos que mais gastam e o que chama o WMI', 'nenhum: só leitura', 3, 0, 'cpu')]


@regra
def r_temperatura(ev):
    ach = _achados_tendencia(ev)
    if 'temperatura' not in ach:
        return []
    return [_sug('temperatura', 'Temperatura alta em repouso', ach['temperatura'][0].upper() + ach['temperatura'][1:] + '.', 'energia', 'média',
                 'limpeza física e pasta térmica resolvem de verdade; no notebook, o plano "fresco" do pacote energia ajuda', 'nenhum', 3, 0)]


@regra
def r_efeito_dos_pacotes(ev):
    """Aprende com o resultado: depois de aplicar um pacote, o que piorou além do ruído e que NÃO já vinha piorando antes."""
    out = []
    am = ev['amostras']
    for quando, nome, titulo in ev['pacotes']:
        piores = []
        for chave, rot, melhor, casas, un in METRICAS_EFEITO:
            s = _serie(am, chave)
            if s:
                ver, a, b = efeito_antes_depois(s, quando, melhor)
                if ver == 'piorou':
                    piores.append(f'{rot} foi de {br(a, casas)} para {br(b, casas)}{(" " + un) if un else ""}')
        if not piores:
            continue
        vizinhos = [n for q, n, _ in ev['pacotes'] if n != nome and abs((q - quando).days) <= 7]
        aviso = ' Outros pacotes foram aplicados na mesma semana, então não dá para saber qual causou.' if vizinhos else ''
        out.append(_sug(f'efeito:{nome}', f'Conferir o pacote {titulo}: algo piorou depois dele',
                        'Mediana de 7 dias antes e depois de ' + f'{quando:%d/%m}: ' + '; '.join(piores) + f', mais que a oscilação normal e sem já vir nessa direção antes.{aviso}',
                        f'desfazer {nome}', 'baixa' if vizinhos else 'média', 'volta ao valor exato de antes; se a medida melhorar, o pacote era o motivo',
                        'baixo: o desfazer guarda e devolve cada valor', 4, 0))
    return out


@regra
def r_benchmark(ev):
    out = []
    for chave, titulo, un in PAINEL_BENCH:
        s = [(d, float(m[chave])) for d, m in ev['benchs'] if isinstance(m.get(chave), (int, float))]
        if len(s) >= 3:
            ant = _mediana([v for _, v in s[:-1]])
            atual = s[-1][1]
            if ant > 0 and atual < 0.75 * max(v for _, v in s) and atual < 0.8 * ant:
                out.append(_sug(f'bench:{chave}', f'{titulo} caiu em relação ao normal', f'Última rodada: {br(atual, 0)} {un}; a mediana das anteriores é {br(ant, 0)} {un}.',
                                'reparar' if 'disco' in chave else 'raiox', 'baixa', 'descartar problema de disco, driver ou calor', 'nenhum: só leitura', 2, 0))
    return out


@regra
def r_ajustes_que_nao_ficam(ev):
    """O relatório registra 'nao-ficou' quando a conferência depois de aplicar mostra algo que não pegou. Repetido = algo desfaz os ajustes."""
    cont = {}
    for x in ev['eventos']:
        if x.get('tipo') == 'nao-ficou' and x.get('pacote'):
            cont[x['pacote']] = cont.get(x['pacote'], 0) + 1
    return [_sug(f'nao-fica:{p}', f'Os ajustes de {PACOTES[p].titulo if p in PACOTES else p} não estão ficando',
                 f'A conferência depois de aplicar encontrou ajuste desfeito {n} vezes. Costuma ser política da empresa, ferramenta do fabricante ou o Windows Update reaplicando.',
                 'verificar', 'alta' if n >= 3 else 'média', 'mostra exatamente quais ajustes voltaram e o que pode estar segurando', 'nenhum: só leitura', 3, 0)
            for p, n in cont.items() if n >= 2]


@regra
def r_itens_que_falham(ev):
    cont = {}
    for x in ev['eventos']:
        if x.get('tipo') == 'itens' and x.get('erros'):
            for i in x.get('ids') or []:
                cont[(x.get('pacote'), i)] = cont.get((x.get('pacote'), i), 0) + 1
    return [_sug(f'falha:{p}:{i}', f'O item {i} de {p} falhou {n} vezes', 'Um item que erra sempre só atrapalha. Se não for essencial, deixe de fora.',
                 'config protegidos', 'baixa', 'o item deixa de aparecer nas listas', 'nenhum', 1, 0)
            for (p, i), n in cont.items() if n >= 3 and p]


@regra
def r_limpeza_que_nao_rende(ev):
    """Honestidade: se a limpeza já não libera quase nada, dizer que repetir não ajuda."""
    sobras = [(x.get('livre_depois', 0) - x.get('livre_antes', 0)) for x in ev['eventos'] if x.get('tipo') == 'espaco' and x.get('pacote') in ('limpar', 'disco')]
    if len(sobras) >= 3 and all(v < 500 * 2 ** 20 for v in sobras[-3:]):
        return [_sug('limpeza-rende-pouco', 'A limpeza já não rende: o PC está limpo', 'As últimas 3 limpezas liberaram menos de 0,5 GB cada. Repetir não ajuda; '
                     'se falta espaço, o que ocupa é arquivo seu: use "grandes".', 'grandes', 'média', 'mostra os arquivos grandes e duplicados', 'baixo: vão para a Lixeira', 2, 1, tipo='info')]
    return []


@regra
def r_achados_do_raiox(ev):
    """O raio-x aponta o que fazer, mas só uma vez. Aqui o que ele apontou e ainda não foi feito entra na fila, ordenado pelo impacto."""
    aplicados = {n for _, n, _ in ev['pacotes']}
    out = []
    for a in (ev['raiox'].get('achados') or [])[:12]:
        cmd = (a.get('comando') or '').strip()
        if not cmd or cmd in aplicados or int(a.get('impacto') or 0) < 2:
            continue
        out.append(_sug('raiox:' + re.sub(r'[^a-z0-9]+', '-', str(a.get('titulo', '')).lower())[:40], str(a.get('titulo')), str(a.get('evidencia') or ''), cmd,
                        'média' if int(a.get('impacto') or 0) >= 3 else 'baixa', str(a.get('faz') or ''), '', int(a.get('impacto') or 2), 1))
    return out[:3]


@regra
def r_termica(ev):
    """Temperatura em janela longa (leituras de 15 em 15 min, por hora): só propõe quando passa do limite ou sobe além da oscilação normal."""
    out = []
    for i, (grav, texto) in enumerate((ev.get('termica') or {}).get('achados', [])):
        out.append(_sug(f'termica:{i}:{texto[:30]}', 'Temperatura alta' if grav == 'alta' else 'Temperatura em alta ao longo do tempo', texto[0].upper() + texto[1:] + '.',
                        'energia', 'alta' if grav == 'alta' else 'média', 'o plano de energia limita o pico de CPU; limpeza física e pasta térmica resolvem a causa', '',
                        5 if grav == 'alta' else 3, 0, metrica='temperatura'))
    return out


@regra
def r_saude(ev):
    """Erros do Windows, drivers e estado do sistema vêm do motor de saúde (66-saude): aqui só viram propostas, com a mesma régua das outras."""
    conf = {'alta': 'alta', 'média': 'média', 'baixa': 'baixa'}
    out = []
    for x in (ev.get('saude') or {}).get('problemas', [])[:8]:
        if x['gravidade'] not in conf or not x.get('comando'):
            continue
        out.append(_sug('saude:' + x['id'], x['titulo'], f'{x["evidencia"]}. {x["faz"]}', x['comando'], conf[x['gravidade']], x['explica'], '',
                        {'alta': 5, 'média': 3, 'baixa': 1}[x['gravidade']], 0, tipo='acao'))
    return out


# ───────── pontuação, memória e aprendizado ─────────

def gera_sugestoes(ev):
    """Roda todas as regras, tira repetidas (mesmo comando) e dispensadas, e ordena por confiança e pontos."""
    out = []
    for r in REGRAS:
        try:
            out += r(ev) or []
        except Exception as ex:  # uma regra com defeito não derruba as outras
            LOG.escreve(f'regra {r.__name__} falhou: {ex!r}')
    dis = ev.get('dispensadas') or {}
    out = [x for x in out if not recente_h(dis.get(x['id']), 24 * DISPENSA_DIAS)]
    resp = {'conselheiro_respostas': ev.get('respostas') or {}}
    for x in out:   # a sua resposta muda o peso; "não me importa" tira de vez
        x['pontos'] = round(x['pontos'] * peso_da_resposta(resp, x['id']), 2)
    out = [x for x in out if x['pontos'] > 0 or x['tipo'] != 'acao']
    por_cmd = {}
    for x in sorted(out, key=lambda x: (ORDEM_CONF[x['confianca']], -x['pontos'], x['id'])):
        chave = x['comando'] or x['id']
        # várias regras podem chegar ao mesmo comando: fica a de maior confiança (as outras viram "também:")
        if chave in por_cmd and x['tipo'] == 'acao':
            por_cmd[chave].setdefault('tambem', []).append(x['titulo'])
            continue
        por_cmd[chave] = x
    return sorted(por_cmd.values(), key=lambda x: (ORDEM_CONF[x['confianca']], -x['pontos'], x['id']))


def registra_vistas(e, sugestoes, agora=None):
    """Memória: guarda quando cada proposta foi mostrada pela primeira vez (com o comando e a métrica que ela visa)."""
    v = e.setdefault('conselheiro_vistas', {})
    for x in sugestoes:
        if x['tipo'] == 'acao' and x['id'] not in v:
            v[x['id']] = {'quando': (agora or datetime.now()).replace(microsecond=0).isoformat(), 'comando': x['comando'], 'metrica': x['metrica'] or ALVO_METRICA.get(x['id'], ''),
                          'titulo': x['titulo'], 'previsao': x.get('previsao')}


def resultados_das_propostas(ev):
    """Aprendizado: para cada proposta mostrada cujo comando virou pacote aplicado DEPOIS, mede o efeito na métrica visada (7 dias antes e depois).
    Devolve [(título do pacote, quando aplicou, métrica, veredito, antes, depois, casas, unidade)]."""
    out = []
    por_nome = {n: (q, t) for q, n, t in ev['pacotes']}
    for id_, v in (ev.get('vistas') or {}).items():
        try:
            visto = datetime.fromisoformat(v['quando'])
        except (KeyError, TypeError, ValueError):
            continue
        cmd, chave = (v.get('comando') or '').split(' ')[0], v.get('metrica')
        if cmd not in por_nome or not chave:
            continue
        quando, titulo = por_nome[cmd]
        if quando < visto or (ev['agora'] - quando).days < 7:
            continue
        s = _serie(ev['amostras'], chave)
        meta = next((m for m in METRICAS_EFEITO if m[0] == chave), None)
        if s and meta:
            ver, a, b = efeito_antes_depois(s, quando, meta[2])
            out.append((titulo, quando, meta[1], ver, a, b, meta[3], meta[4]))
    return out


def tabela_efeito(amostras, pacotes):
    """Linhas [(título, quando, [(rótulo, veredito, antes, depois, casas, unidade)])] para o painel."""
    linhas = []
    for quando, nome, titulo in pacotes:
        cel = []
        for chave, rot, melhor, casas, un in METRICAS_EFEITO:
            s = _serie(amostras, chave)
            if s:
                ver, a, b = efeito_antes_depois(s, quando, melhor)
                cel.append((rot, ver, a, b, casas, un))
        linhas.append((titulo, quando, cel))
    return linhas


def ferramenta_conselheiro(ctx, args):
    t = ctx.t
    t.aba('o motor de inteligência: propõe mudanças com base em tudo que o Katharos sabe (você decide)')
    t.paragrafo('Junta as medidas do segundo plano, os benchmarks, os pacotes que você aplicou, os erros do relatório e o que o raio-x apontou, e diz o que mudaria, '
                'com o número que justifica, a confiança e o comando. Não aplica nada sozinho. Depois que você executa uma proposta, ele mede o resultado.', 2, 'sub')
    e = estado()
    if getattr(args, 'exportar', False):
        return exporta_propostas(ctx)
    resp = getattr(args, 'resposta', None)
    if resp:
        responde(resp[0], resp[1])
        t.ok({'sim': 'Anotado: ajudou. Esse tipo de proposta ganha peso neste PC.', 'nao': 'Anotado: não ajudou. Ela perde peso neste PC.',
              'nao-importa': 'Anotado: não te importa. Não proponho mais isso.'}[resp[1]])
        try:
            exporta_propostas(ctx)
        except Exception as ex:
            LOG.escreve(f'exportar depois da resposta: {ex!r}')
        return 0
    alvo = getattr(args, 'dispensar', None)
    if alvo:
        dis = e.get('conselheiro_dispensadas') or {}
        dis[alvo] = agora_iso()
        e['conselheiro_dispensadas'] = dis
        salva_estado(e)
        t.ok(f'Proposta "{alvo}" dispensada por {DISPENSA_DIAS} dias.')
        return 0
    ev = coleta_evidencias(ctx)
    t.chaves([('medidas', str(len(ev['amostras']))), ('pacotes aplicados', str(len(ev['pacotes']))), ('eventos no relatório', str(len(ev['eventos']))),
              ('achados do raio-x', str(len(ev['raiox'].get('achados') or [])))])
    res = resultados_das_propostas(ev)
    if res:
        t.titulo('resultado das propostas que você executou')
        for titulo, quando, rot, ver, a, b, casas, un in res:
            if ver in ('melhorou', 'piorou'):
                t.item('●', 'verde' if ver == 'melhorou' else 'amarelo', f'{titulo} ({quando:%d/%m})', f'{rot}: {br(a, casas)} → {br(b, casas)}{(" " + un) if un else ""} ({ver})')
            else:
                t.item('○', 'apagado', f'{titulo} ({quando:%d/%m})', f'{rot}: {ver}')
    prevs = [r for r in resultados_previstos(e, ev.get('minutos') or [], ev.get('sessoes') or [], ev['agora'])]
    if prevs:
        t.titulo('o que eu previ e o que aconteceu')
        cor_v = {'como previsto': 'verde', 'em parte': 'amarelo', 'sem diferença': 'apagado', 'piorou': 'vermelho', 'cedo para dizer': 'apagado'}
        for r in prevs:
            num = (f': {br(r["antes"], 0)} → {br(r["depois"], 0)} {r["un"]}' if r['antes'] is not None else '')
            t.item('●', cor_v.get(r['veredito'], 'apagado'), f'{r["titulo"]} ({r["quando"]:%d/%m})', f'previ {r["previsto"]}; {r["veredito"]}{num}')
        t.nota('    ajudou? "katharos conselheiro --resposta ID sim" (ou nao, ou nao-importa)', 4)
    memoria_atualiza()
    pz = pensa(ev)
    sug = pz['propostas']
    registra_vistas(e, sug)
    salva_estado(e)
    for d in pz['diagnosticos']:
        x = explica(d)
        t.titulo(f'{d["titulo"].lower()}: {d["nome"]}')
        t.chaves([('o que eu vi', x['vi']), ('por que acho isso', x['porque']), ('o que eu faria', x['faria']), ('o que mudaria a conclusão', x['mudaria']),
                  ('confiança', d['confianca'])], recuo=4)
    if not sug:
        if len(ev['amostras']) < 6:
            t.nota('Poucas medidas ainda para propor algo (preciso de pelo menos 6, em 3 dias ou mais).')
        else:
            t.ok('Nada a propor: nenhuma evidência de algo piorando.')
        return 0
    cor = {'alta': 'verde', 'média': 'amarelo', 'baixa': 'apagado'}
    for i, x in enumerate(sug, 1):
        t.titulo(f'{i}. {x["titulo"]}')
        t.paragrafo(x['porque'], 4, 'texto')
        linhas = [('confiança', t.p(x['confianca'], cor[x['confianca']]))]
        if x['comando']:
            linhas.append(('comando', t.p('katharos ' + x['comando'], 'destaque')))
        if x['impacto']:
            linhas.append(('o que muda', x['impacto']))
        if x['risco']:
            linhas.append(('risco', x['risco']))
        if x.get('previsao'):
            linhas.append(('o que espero', x['previsao'].get('texto') or ''))
        if x.get('tambem'):
            linhas.append(('também aponta', '; '.join(x['tambem'])))
        t.chaves(linhas, recuo=4)
        t.nota(f'    não quer? "katharos conselheiro --dispensar {x["id"]}" esconde por {DISPENSA_DIAS} dias.', 4)
    return 0


def exporta_propostas(ctx=None):
    """Grava as propostas de agora em ~/.katharos/propostas.json: o ícone do segundo plano mostra as primeiras."""
    try:
        memoria_atualiza()
        ev = coleta_evidencias(ctx)
        p = pensa(ev)
        sug = p['propostas']
        escreve_linha_de_base(ev.get('minutos'), ev.get('agora'))
        res = resultados_previstos({'conselheiro_feitos': ev.get('feitos') or {}}, ev.get('minutos') or [], ev.get('sessoes') or [], ev.get('agora'))
        respondidas = ev.get('respostas') or {}
        pendentes = [dict(r, quando=r['quando'].isoformat()) for r in res if r['veredito'] != 'cedo para dizer' and r['id'] not in respondidas]
        d = {'quando': agora_iso(), 'propostas': [{k: x.get(k) for k in ('id', 'titulo', 'porque', 'comando', 'confianca', 'tipo', 'explicacao', 'desfazer', 'causa')} for x in sug[:6]],
             'resultados': pendentes[:3], 'diagnosticos': [{k: x.get(k) for k in ('problema', 'titulo', 'causa', 'nome', 'confianca', 'evidencias', 'descartadas', 'faria', 'mudaria')}
                                                           for x in p['diagnosticos']],
             'achados': [{k: x.get(k) for k in ('id', 'tipo', 'titulo', 'vi', 'confianca', 'gravidade', 'contexto', 'fonte')} for x in p['achados']][:20]}
        tmp = CASA / f'propostas.json.{os.getpid()}.tmp'
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
        os.replace(tmp, CASA / 'propostas.json')
        return 0
    except Exception as ex:
        LOG.escreve(f'exportar propostas: {ex!r}')
        return 1


def avisa_propostas(e, ctx=None):
    """No segundo plano: só propostas de confiança alta e ainda não avisadas nos últimos 7 dias viram notificação."""
    try:
        ev = coleta_evidencias(ctx)
        ev['fundo_ligado'] = True
        sug = pensa(ev)['propostas']
        registra_vistas(e, sug)
        vistos = e.setdefault('conselheiro_avisadas', {})
        novas = []
        for x in sug:
            if x['confianca'] == 'alta' and x['tipo'] == 'acao' and not recente_h(vistos.get(x['id']), 24 * 7) and pode_avisar(e, 'proposta:' + x['id']):
                novas.append(f'{x["titulo"]} (katharos {x["comando"]})')
                vistos[x['id']] = agora_iso()
                marca_aviso(e, 'proposta:' + x['id'])
        if config('resumo-diario', 'nao') == 'sim':   # um aviso por dia, com tudo, no lugar de vários soltos
            if novas and not recente_h(e.get('resumo_diario_em'), 20):
                e['resumo_diario_em'] = agora_iso()
                return [f'Resumo do dia: {len(novas)} {"proposta nova" if len(novas) == 1 else "propostas novas"}: ' + '; '.join(novas)]
            return []
        return novas
    except Exception as ex:
        LOG.escreve(f'conselheiro falhou: {ex!r}')
        return []
