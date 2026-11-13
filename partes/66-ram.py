# ═══════════════════════════════ RAM por programa (tela Memória) ═══════════════════════════════
# O segundo plano grava, a cada minuto, os 15 programas que mais usam RAM (ram.jsonl: memória privada somada por nome, o Chrome com
# as abas vira um só), o quanto da memória total está prometido (commit) e a memória comprimida. Aqui isso vira: quem usa agora, a média
# e o pico em 24 h e em 7 dias, um minigráfico, se a RAM está cheia de verdade e o que dá para fazer com cada um (com cuidado).

def _le_ram(dias=7, agora=None):
    """[(datetime, {nome: MB}, commit_pct, comprimida_mb)] dos últimos dias, do mais velho para o mais novo."""
    agora = agora or datetime.now()
    corte = agora - timedelta(days=dias)
    out = []
    try:
        linhas = (CASA / 'ram.jsonl').read_text(encoding='utf-8', errors='replace').splitlines()
    except OSError:
        return out
    for l in linhas:
        try:
            d = json.loads(l)
            t = datetime.fromisoformat(str(d['t'])[:19])
        except (ValueError, KeyError, TypeError):
            continue
        if t < corte:
            continue
        progs = {}
        for x in d.get('p') or []:
            if isinstance(x, list) and len(x) == 2 and isinstance(x[1], (int, float)):
                progs[str(x[0])] = float(x[1])
        out.append((t, progs, d.get('commit_pct'), d.get('comprimida_mb')))
    return out


def _nome_amigavel(n):
    """'o Google Chrome' (do dicionário) vira 'Google Chrome'; sem dicionário, o nome do processo."""
    q = quem_e(n)
    if q:
        s = re.sub(r'^(o|a|os|as|um|uma)\s+', '', q[0].strip(), flags=re.I)
        # descrição longa ("o navegador do Google, com as abas") não serve de nome: fica o do processo
        if len(s) <= 32 and ',' not in s:
            return s[0].upper() + s[1:]
    return n


# ferramentas do próprio Windows que o dicionário explica, mas que não se fecham nem se desinstalam (relatório do dono, 4.3.1: a
# "Verificação de disco" aparecia com "Fechar" e "Desinstalar")
FERRAMENTAS_DO_WINDOWS = frozenset(
    'chkdsk autochk defrag dfrgui tiworker trustedinstaller usocoreworker wuaucltcore musnotification musnotifyicon sihclient '
    'memcompression memory compression msmpeng nissrv mpdefendercoreservice mpcmdrun searchindexer searchprotocolhost '
    'searchfilterhost searchhost compattelrunner devicecensus cleanmgr dismhost sfc'.split()) | {'memory compression'}


def classe_programa(n):
    """('protegido' | 'conhecido' | 'desconhecido', o que é, o que fazer). Protegido: Windows, drivers, proteção, anti-cheat e o próprio
    Katharos: aparece, mas sem nenhuma ação. Desconhecido: "não conheço este programa", sem palpite."""
    base = str(n or '').lower()
    base = base[:-4] if base.endswith('.exe') else base
    q = quem_e(base)
    if not pode_sugerir_fechar(base) or base in ANTICHEAT_PROCESSOS or (q and q[1] == _NORMAL) or base in FERRAMENTAS_DO_WINDOWS:
        return 'protegido', (q[0] if q else 'parte do Windows'), 'faz parte do Windows ou da proteção: o Katharos nunca mexe'
    if q:
        return 'conhecido', q[0], q[1]
    return 'desconhecido', 'não conheço este programa', ''


def pressao_ram(linhas, total_gb=None):
    """A RAM está cheia de verdade? Olha a última meia hora: memória prometida (commit) e comprimida. "Alto" sozinho não é alarme: o
    Windows usa RAM livre de cache de propósito."""
    ult = linhas[-30:]
    commits = sorted(c for _, _, c, _ in ult if isinstance(c, (int, float)))
    comps = sorted(c for _, _, _, c in ult if isinstance(c, (int, float)))
    if not commits:
        return {'nivel': 'sem_dado', 'texto': 'Ainda sem medida: com o acompanhamento ligado, em alguns minutos aparece aqui.'}
    commit = commits[len(commits) // 2]
    comp = comps[len(comps) // 2] if comps else None
    comp_pct = (comp / 1024 / total_gb * 100) if comp and total_gb else None
    if commit >= 90 or (comp_pct or 0) >= 15:
        nivel, texto = 'cheia', 'Cheia de verdade: o Windows já está comprimindo memória e usando o disco no lugar da RAM. É aí que tudo engasga.'
    elif commit >= 80:
        nivel, texto = 'apertada', 'Apertada: ainda dá conta, mas abrir mais um programa pesado já começa a engasgar.'
    else:
        nivel, texto = 'folgada', 'Folgada: mesmo com o número alto, sobra memória. O Windows usa a RAM livre de cache de propósito.'
    return {'nivel': nivel, 'texto': texto, 'commit_pct': round(commit, 1), 'comprimida_gb': round(comp / 1024, 2) if comp else None,
            'comprimida_pct': round(comp_pct, 1) if comp_pct is not None else None}


@metodo_api('memoria_programas')
def api_memoria_programas(ctx, p, ev):
    """Quem usa a RAM: um item por programa, com agora, média e pico em 24 h e 7 dias, o minigráfico das últimas 24 h (uma média por
    hora; hora sem leitura fica sem ponto, nunca zero), a classe (protegido, conhecido, desconhecido) e as ações seguras."""
    agora = datetime.now()
    linhas = _le_ram(7, agora)
    total = None
    a = le_agora(max_idade_s=120)
    if isinstance(a, dict):
        total = a.get('ram_total_gb')
    if not total and ctx.perfil:
        total = pf(ctx.perfil, 'ram.total', None)
    if not linhas:
        return {'programas': [], 'pressao': pressao_ram([], total), 'desde': None, 'ram_total_gb': total}
    dia = agora - timedelta(hours=24)
    ultima_t, ultima, _, _ = linhas[-1]
    nomes = set()
    for _, progs, _, _ in linhas:
        nomes |= set(progs)
    progs_out = []
    for n in nomes:
        v7 = [progs.get(n) for _, progs, _, _ in linhas]
        v24 = [progs.get(n) for t, progs, _, _ in linhas if t >= dia]
        tem7 = [x for x in v7 if x is not None]
        tem24 = [x for x in v24 if x is not None]
        horas = []
        for h in range(24):
            ini, fim = dia + timedelta(hours=h), dia + timedelta(hours=h + 1)
            vs = [progs[n] for t, progs, _, _ in linhas if ini <= t < fim and n in progs]
            horas.append(round(sum(vs) / len(vs)) if vs else None)
        classe, oque, faz = classe_programa(n)
        acoes = []
        if classe == 'conhecido':
            q = quem_e(n)
            if q and (q[2] == 'inicializacao' or q[1] == _INI):
                acoes.append('inicializacao')
            acoes += ['fechar', 'desinstalar']
        progs_out.append({
            'processo': n, 'nome': _nome_amigavel(n), 'classe': classe, 'o_que_e': oque, 'faz': faz, 'acoes': acoes,
            # "agora" é a última leitura (se o programa ainda estava entre os 15 maiores nela)
            'agora_mb': ultima.get(n) if (agora - ultima_t).total_seconds() < 600 else None,
            'media_24h_mb': round(sum(tem24) / len(tem24)) if tem24 else None, 'pico_24h_mb': max(tem24) if tem24 else None,
            'media_7d_mb': round(sum(tem7) / len(tem7)) if tem7 else None, 'pico_7d_mb': max(tem7) if tem7 else None,
            'horas': horas, 'leituras': len(tem7),
        })
    progs_out.sort(key=lambda x: -((x['agora_mb'] or 0) * 2 + (x['media_24h_mb'] or 0)))
    return {'programas': progs_out[:25], 'pressao': pressao_ram(linhas, total), 'desde': linhas[0][0].isoformat(timespec='minutes'),
            'ultima': ultima_t.isoformat(timespec='minutes'), 'ram_total_gb': total, 'dias': round((ultima_t - linhas[0][0]).total_seconds() / 86400, 1)}
