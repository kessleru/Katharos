
# ─────────────── motor de inteligência: o normal deste PC, confiança pelos dados, previsão x resultado, sua resposta ───────────────
# A central (65-conselheiro) propõe; este módulo dá a ela três coisas que ela não tinha:
#   · LINHA DE BASE: o normal de cada métrica neste PC, por contexto (com ou sem jogo), a partir dos minutos que o Katharos.exe grava.
#     "Fora do normal deste PC" substitui limite fixo onde limite fixo engana (RAM de 8 GB x 64 GB). Calor continua com limite absoluto.
#   · CONFIANÇA PELOS DADOS: quantas leituras, em quantos dias, quantas vezes se repetiu e se a fonte é boa. Pouco dado = "ainda não sei"
#     (a regra não propõe nada), nunca alarme.
#   · PREVISÃO E RESULTADO: cada proposta diz o que espera mudar; depois de aplicada, o motor mede e compara. O que não ajudou neste PC
#     perde peso. A sua resposta ("ajudou?", "não me importa") também conta.
METRICAS_BASE = {   # métrica do minuto: (nome, unidade, diferença mínima que importa, comando que investiga)
    'cpu': ('a CPU', '%', 8, 'raiox'), 'ram': ('a RAM', '%', 8, 'memoria'), 'disco': ('o disco ocupado', '%', 10, 'raiox'),
    'ram_sistema_gb': ('a RAM dos serviços do Windows', 'GB', 0.4, 'servicos'),
    'temp_cpu': ('a temperatura da CPU', '°C', 5, 'painel'), 'temp_gpu': ('a temperatura da placa de vídeo', '°C', 5, 'painel'),
}
BASE_DIAS = 14
BASE_DIAS_MIN = 3
BASE_MINUTOS_MIN = 300
RESPOSTAS = ('sim', 'nao', 'nao-importa')


def _mediana_lista(v):
    v = sorted(v)
    n = len(v)
    if not n:
        return None
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def _percentil(v, p):
    v = sorted(v)
    if not v:
        return None
    i = min(len(v) - 1, max(0, int(round(p / 100 * (len(v) - 1)))))
    return v[i]


def contexto_do_minuto(m):
    return 'jogo' if m.get('jogo') else 'sem_jogo'


def limpo(m):
    """Minuto que vale para medir: sem manutenção do Windows rodando (atualização, Defender, indexação) e não logo depois do boot."""
    return not m.get('sujo')


def linha_de_base(minutos, metrica, contexto, ate=None, dias=BASE_DIAS):
    """O normal desta métrica neste PC: mediana, dispersão robusta (MAD) e a faixa de 10 a 90 %, dos minutos ANTES de `ate`.
    None se ainda não há dado bastante (menos de 3 dias diferentes ou 300 minutos)."""
    ate = ate or datetime.now()
    de = ate - timedelta(days=dias)
    v, dias_vistos = [], set()
    for m in minutos:
        dt = m.get('_dt')
        x = m.get(metrica)
        if dt is None or not (de <= dt < ate) or not isinstance(x, (int, float)) or contexto_do_minuto(m) != contexto or not limpo(m):
            continue
        v.append(float(x))
        dias_vistos.add(dt.date())
    if len(dias_vistos) < BASE_DIAS_MIN or len(v) < BASE_MINUTOS_MIN:
        return None
    med = _mediana_lista(v)
    mad = _mediana_lista([abs(x - med) for x in v])
    return {'mediana': round(med, 1), 'mad': round(mad, 2), 'p10': round(_percentil(v, 10), 1), 'p90': round(_percentil(v, 90), 1),
            'n': len(v), 'dias': len(dias_vistos)}


def confianca(n, dias=0, repeticoes=0, fonte_boa=True):
    """Confiança pelos dados. None = ainda não sei (não propõe). n: leituras; dias: dias diferentes; repeticoes: sessões ou episódios."""
    if n < 3 or (dias < 1 and repeticoes < 2):
        return None
    if n >= 30 and (dias >= 3 or repeticoes >= 3):
        nivel = 'alta'
    elif n >= 10 and (dias >= 2 or repeticoes >= 2):
        nivel = 'média'
    else:
        nivel = 'baixa'
    if not fonte_boa:
        nivel = {'alta': 'média', 'média': 'baixa'}.get(nivel, 'baixa')
    return nivel


def linha_de_base_toda(minutos, agora=None):
    """{métrica: {contexto: linha de base}} de tudo o que der para calcular. Vai para o Katharos.exe desenhar o normal nos gráficos."""
    out = {}
    for met in METRICAS_BASE:
        for ctx_ in ('sem_jogo', 'jogo'):
            b = linha_de_base(minutos, met, ctx_, agora)
            if b:
                out.setdefault(met, {})[ctx_] = b
    return out


def escreve_linha_de_base(minutos=None, agora=None):
    try:
        d = {'quando': agora_iso(), 'metricas': linha_de_base_toda(minutos if minutos is not None else le_minutos(24 * BASE_DIAS), agora)}
        tmp = CASA / f'linha-de-base.json.{os.getpid()}.tmp'
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
        os.replace(tmp, CASA / 'linha-de-base.json')
        return d
    except OSError as e:
        LOG.escreve(f'linha de base: {e!r}')
        return None


@regra
def r_fora_do_normal(ev):
    """As últimas 24 h comparadas com o normal deste PC nos 14 dias antes (mesmo contexto). Só com dado bastante dos dois lados."""
    mins = ev.get('minutos') or []
    agora = ev['agora']
    corte = agora - timedelta(hours=24)
    out = []
    for met, (nome, un, minimo, cmd) in METRICAS_BASE.items():
        if met.startswith('temp'):
            continue   # calor tem limite absoluto (regra própria); aqui é o que muda em relação ao normal
        base = linha_de_base(mins, met, 'sem_jogo', ate=corte)
        recente = [float(m[met]) for m in mins if m.get('_dt') and m['_dt'] >= corte and isinstance(m.get(met), (int, float))
                   and contexto_do_minuto(m) == 'sem_jogo' and limpo(m)]
        if not base or len(recente) < 60:
            continue
        med = _mediana_lista(recente)
        limiar = base['mediana'] + max(3 * 1.4826 * base['mad'], minimo)
        if med <= limiar:
            continue
        conf = confianca(len(recente), base['dias'], repeticoes=0)
        if not conf:
            continue
        out.append(_sug(f'normal-{met}', f'{nome[0].upper()}{nome[1:]} está acima do normal deste PC',
                        f'Nas últimas 24 horas, sem jogo aberto, {nome} ficou em {br(med, 0)} {un} (mediana de {len(recente)} minutos). '
                        f'O normal deste PC nos {base["dias"]} dias antes era {br(base["mediana"], 0)} {un} (entre {br(base["p10"], 0)} e {br(base["p90"], 0)}).',
                        cmd, conf, f'descobrir o que mudou ({"o raio-x mostra quem gasta" if cmd == "raiox" else "quem ocupa a memória"})', 'nenhum: só leitura',
                        3, 0, met, previsao={'fonte': 'minutos', 'chave': met, 'contexto': 'sem_jogo', 'delta': -(med - base['mediana']), 'un': un,
                                             'texto': f'voltar perto de {br(base["mediana"], 0)} {un}'}))
    return out


# ───────── previsão x resultado ─────────

def _janela(minutos, chave, contexto, de, ate):
    return [float(m[chave]) for m in minutos if m.get('_dt') and de <= m['_dt'] < ate and isinstance(m.get(chave), (int, float))
            and contexto_do_minuto(m) == contexto and limpo(m)]


def intervalo_da_diferenca(a, b, rodadas=400, semente=7):
    """Diferença das medianas (depois - antes) com intervalo de 90 % por reamostragem (bootstrap). Devolve (diferença, baixo, alto)."""
    import random
    r = random.Random(semente)
    base = _mediana_lista(b) - _mediana_lista(a)
    difs = []
    for _ in range(rodadas):
        difs.append(_mediana_lista([r.choice(b) for _ in b]) - _mediana_lista([r.choice(a) for _ in a]))
    difs.sort()
    return base, difs[int(0.05 * (rodadas - 1))], difs[int(0.95 * (rodadas - 1))]


def _limite_sessoes(sessoes, chave, de, ate):
    return [float((s.get('tempo_no_limite') or {}).get(chave, 0)) for s in sessoes
            if s.get('_dt') and de <= s['_dt'] < ate and isinstance(s.get('min'), (int, float)) and s['min'] >= 5]


def mede_previsao(prev, quando, minutos, sessoes, dias=7):
    """Compara a janela antes e a depois de `quando` na métrica da previsão.
    Devolve (veredito, antes, depois): 'como previsto', 'em parte', 'sem diferença', 'piorou' ou 'cedo para dizer'."""
    de, ate = quando - timedelta(days=dias), quando + timedelta(days=dias)
    if prev.get('fonte') == 'sessoes':
        a, b = _limite_sessoes(sessoes, prev['chave'], de, quando), _limite_sessoes(sessoes, prev['chave'], quando, ate)
        minimo = 3
    else:
        a = _janela(minutos, prev['chave'], prev.get('contexto', 'sem_jogo'), de, quando)
        b = _janela(minutos, prev['chave'], prev.get('contexto', 'sem_jogo'), quando, ate)
        minimo = 60
    if len(a) < minimo or len(b) < minimo:
        return 'cedo para dizer', None, None
    ma, mb = _mediana_lista(a), _mediana_lista(b)
    real, baixo, alto = intervalo_da_diferenca(a[-2000:], b[-2000:])
    esperado = float(prev.get('delta') or 0)
    menor = (METRICAS_BASE.get(prev['chave']) or (0, 0, 2.0))[2] / 2   # a menor diferença que importa nesta métrica
    if baixo <= 0 <= alto or abs(real) < menor:   # a margem engole o efeito: não dá para dizer que mudou
        return 'sem diferença', ma, mb
    if esperado and (real > 0) != (esperado > 0):
        return 'piorou', ma, mb
    return ('como previsto' if not esperado or abs(real) >= 0.6 * abs(esperado) else 'em parte'), ma, mb


def resultados_previstos(e, minutos, sessoes, agora=None):
    """Para cada proposta executada (pacote ou comando registrado depois de vista), o previsto e o medido."""
    out = []
    feitos = e.get('conselheiro_feitos') or {}
    for id_, f in feitos.items():
        prev = f.get('previsao')
        try:
            quando = datetime.fromisoformat(f['quando'])
        except (KeyError, TypeError, ValueError):
            continue
        if not prev:
            continue
        ver, a, b = mede_previsao(prev, quando, minutos, sessoes)
        out.append({'id': id_, 'titulo': f.get('titulo') or id_, 'quando': quando, 'previsto': prev.get('texto') or '', 'veredito': ver,
                    'antes': a, 'depois': b, 'un': prev.get('un') or ''})
    return out


def registra_feito(id_, titulo, previsao, quando=None):
    """Guarda que a proposta foi executada, com a previsão: o motor mede depois."""
    e = estado()
    e.setdefault('conselheiro_feitos', {})[id_] = {'quando': (quando or datetime.now()).replace(microsecond=0).isoformat(), 'titulo': titulo, 'previsao': previsao}
    salva_estado(e)


def marca_propostas_feitas(comando):
    """Depois de rodar um comando que muda o PC: as propostas vistas com esse comando viram 'feitas' (com a previsão que tinham)."""
    e = estado()
    vistas = e.get('conselheiro_vistas') or {}
    feitos = e.setdefault('conselheiro_feitos', {})
    for id_, v in vistas.items():
        if (v.get('comando') or '').split(' ')[0] == comando and id_ not in feitos and v.get('previsao'):
            feitos[id_] = {'quando': agora_iso(), 'titulo': v.get('titulo') or id_, 'previsao': v['previsao']}
    salva_estado(e)


# ───────── a sua resposta ─────────

def peso_da_resposta(e, id_):
    """Multiplicador dos pontos da proposta pelo que você respondeu e pelo resultado medido. 0 = nunca mais propor."""
    r = (e.get('conselheiro_respostas') or {}).get(id_, {}).get('resposta')
    if r == 'nao-importa':
        return 0.0
    if r == 'nao':
        return 0.4
    if r == 'sim':
        return 1.3
    return 1.0


def responde(id_, resposta):
    if resposta not in RESPOSTAS:
        raise ValueError(resposta)
    e = estado()
    e.setdefault('conselheiro_respostas', {})[id_] = {'resposta': resposta, 'quando': agora_iso()}
    salva_estado(e)


# ───────── o mesmo jogo antes e depois de cada mudança (fase 2c) ─────────
METRICAS_JOGO = [('fps_1low', '1% low', 'maior', 'FPS'), ('fps_med', 'FPS médio', 'maior', 'FPS'), ('travadas_por_min', 'travadas por minuto', 'menor', '')]


def comparacoes_por_jogo(sessoes, pacotes, minimo=3, dias=30):
    """Para cada pacote aplicado e cada jogo com pelo menos `minimo` sessões antes e depois (na janela de `dias`), a diferença de FPS,
    1% low e travadas, com margem (bootstrap). Devolve [{jogo, pacote, nome_pacote, quando, metrica, rotulo, antes, depois, veredito}]."""
    out = []
    for quando, nome, titulo in pacotes:
        de, ate = quando - timedelta(days=dias), quando + timedelta(days=dias)
        jogos = {s.get('jogo') for s in sessoes if s.get('jogo')}
        for jogo in sorted(jogos):
            antes = [s for s in sessoes if s.get('jogo') == jogo and s.get('_dt') and de <= s['_dt'] < quando]
            depois = [s for s in sessoes if s.get('jogo') == jogo and s.get('_dt') and quando <= s['_dt'] < ate]
            for chave, rot, melhor, un in METRICAS_JOGO:
                a = [float(s[chave]) for s in antes if isinstance(s.get(chave), (int, float))]
                b = [float(s[chave]) for s in depois if isinstance(s.get(chave), (int, float))]
                if len(a) < minimo or len(b) < minimo:
                    continue
                dif, lo, hi = intervalo_da_diferenca(a, b)
                if lo <= 0 <= hi:
                    ver = 'sem diferença'
                else:
                    ver = 'melhorou' if (dif > 0) == (melhor == 'maior') else 'piorou'
                out.append({'jogo': jogo, 'pacote': nome, 'nome_pacote': titulo, 'quando': quando, 'metrica': chave, 'rotulo': rot, 'un': un,
                            'antes': round(_mediana_lista(a), 1), 'depois': round(_mediana_lista(b), 1), 'veredito': ver,
                            'sessoes': (len(a), len(b))})
    return out


@regra
def r_jogo_antes_depois(ev):
    """O resultado de cada mudança nos jogos de verdade; se piorou de forma clara, propõe desfazer aquela área."""
    out = []
    for c in comparacoes_por_jogo(ev.get('sessoes') or [], ev.get('pacotes') or []):
        if c['metrica'] != 'fps_1low' or c['veredito'] == 'sem diferença':
            continue
        n = f'{c["sessoes"][0]} sessões antes e {c["sessoes"][1]} depois'
        num = f'{br(c["antes"], 0)} → {br(c["depois"], 0)} {c["un"]}'.strip()
        if c['veredito'] == 'melhorou':
            out.append(_sug(f'jogo-ganho:{c["pacote"]}:{c["jogo"]}', f'{c["nome_pacote"]} melhorou {c["jogo"]}',
                            f'O 1% low (os momentos mais pesados) foi de {num}, comparando {n}, com margem calculada.', '', 'alta', '', '', 2, 0, tipo='info'))
        else:
            out.append(_sug(f'jogo-piora:{c["pacote"]}:{c["jogo"]}', f'{c["nome_pacote"]} piorou {c["jogo"]}',
                            f'O 1% low caiu de {num} ({n}), além da variação normal. Desfazer esta área volta como estava.',
                            f'desfazer {c["pacote"]}', 'alta', 'o jogo volta ao desempenho de antes', 'perde o que a área fazia', 4, 0))
    return out


def qualidade_da_medida(minutos, de, ate):
    """2e.8: quanto dá para confiar numa comparação: dos minutos medidos na janela, quantos estavam sujos (Windows Update, Defender,
    indexação, logo depois do boot) ou com o PC muito carregado pelos programas da pessoa. {'nivel': 'boa'|'fraca'|None, 'texto': ...}"""
    ms = [m for m in minutos if m.get('_dt') and de <= m['_dt'] < ate and not m.get('jogo')]
    if len(ms) < 30:
        return {'nivel': None, 'texto': 'poucas medidas para dizer a qualidade'}
    sujos = sum(1 for m in ms if m.get('sujo'))
    pesados = sum(1 for m in ms if isinstance(m.get('cpu'), (int, float)) and m['cpu'] >= 60)
    f_sujo, f_pesado = sujos / len(ms), pesados / len(ms)
    if f_sujo < 0.2 and f_pesado < 0.25:
        return {'nivel': 'boa', 'texto': f'medida boa ({len(ms)} minutos, quase todos limpos)'}
    motivos = []
    if f_sujo >= 0.2:
        motivos.append(f'manutenção do Windows rodando em {br(100 * f_sujo, 0)} % dos minutos')
    if f_pesado >= 0.25:
        motivos.append(f'CPU ocupada pelos seus programas em {br(100 * f_pesado, 0)} % dos minutos')
    return {'nivel': 'fraca', 'texto': 'medida fraca (' + '; '.join(motivos) + '): para medir melhor, deixe o PC ligado parado por um tempo'}
