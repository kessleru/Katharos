
# ─────────────── versões e edições do Windows: o que muda entre elas ───────────────
# O Katharos é feito para o Windows 10 e o 11, em qualquer versão e edição. Aqui fica o que muda de uma para outra e quando cada uma
# deixa de receber atualização de segurança. Fontes e datas: pesquisa "versões do Windows" no cofre (10/11/2026) e o ciclo de vida
# publicado pela Microsoft. Revisar a cada versão nova do Windows (fluxo de publicação, passo de pesquisa).
VERSOES_WINDOWS = {   # build: (família, versão)
    17763: (10, '1809'), 18362: (10, '1903'), 18363: (10, '1909'), 19041: (10, '2004'), 19042: (10, '20H2'), 19043: (10, '21H1'),
    19044: (10, '21H2'), 19045: (10, '22H2'),
    22000: (11, '21H2'), 22621: (11, '22H2'), 22631: (11, '23H2'), 26100: (11, '24H2'), 26200: (11, '25H2'),
}
BUILD_MINIMO = 17763   # Windows 10 1809: antes disso, só o modo seguro
# fim das atualizações de segurança (AAAA-MM-DD) por (família, versão, tipo de ciclo)
FIM_SUPORTE = {
    (10, '1809', 'consumo'): '2020-11-10', (10, '1903', 'consumo'): '2020-12-08', (10, '1909', 'consumo'): '2021-05-11',
    (10, '2004', 'consumo'): '2021-12-14', (10, '20H2', 'consumo'): '2022-05-10', (10, '21H1', 'consumo'): '2022-12-13',
    (10, '21H2', 'consumo'): '2023-06-13', (10, '22H2', 'consumo'): '2025-10-14',
    (10, '21H2', 'empresa'): '2024-06-11', (10, '22H2', 'empresa'): '2025-10-14',
    (10, '1809', 'ltsc'): '2029-01-09', (10, '21H2', 'ltsc'): '2027-01-12',
    (11, '21H2', 'consumo'): '2023-10-10', (11, '22H2', 'consumo'): '2024-10-08', (11, '23H2', 'consumo'): '2025-11-11',
    (11, '24H2', 'consumo'): '2026-10-13', (11, '25H2', 'consumo'): '2027-10-12',
    (11, '21H2', 'empresa'): '2024-10-08', (11, '22H2', 'empresa'): '2025-10-14', (11, '23H2', 'empresa'): '2026-11-10',
    (11, '24H2', 'empresa'): '2027-10-12', (11, '25H2', 'empresa'): '2028-10-10',
    (11, '24H2', 'ltsc'): '2029-10-09',
}
ESU_WINDOWS10 = '2027-10-12'   # atualizações estendidas grátis para pessoa física, no 22H2 em dia e com inscrição (estendidas em jun/2026)
EDICOES = {   # EditionID do registro → tipo
    'core': 'home', 'coren': 'home', 'coresinglelanguage': 'home', 'corecountryspecific': 'home',
    'professional': 'pro', 'professionaln': 'pro', 'professionalworkstation': 'pro', 'professionalworkstationn': 'pro',
    'professionaleducation': 'pro', 'professionaleducationn': 'pro',
    'enterprise': 'empresa', 'enterprisen': 'empresa', 'enterpriseg': 'empresa', 'education': 'educacao', 'educationn': 'educacao',
    'enterprises': 'ltsc', 'enterprisesn': 'ltsc', 'iotenterprises': 'ltsc', 'iotenterprise': 'iot',
    'cloudedition': 'se', 'cloud': 'se', 'cloudn': 'se',
}
NOME_EDICAO = {'home': 'Home', 'pro': 'Pro', 'empresa': 'Enterprise', 'educacao': 'Education', 'ltsc': 'LTSC', 'iot': 'IoT',
               'server': 'Server', 'se': 'SE', '': ''}
UCPD_PROTEGIDOS = ('TaskbarDa',)   # valores que o UCPD (Windows 11 24H2 e 10 atualizado) não deixa gravar: a política que funciona fica no item


def edicao_tipo(edition_id):
    e = (edition_id or '').strip().lower()
    if e.startswith('server'):
        return 'server'
    return EDICOES.get(e, '')


def compat_windows(perfil, hoje=None):
    """O que importa da versão e da edição deste PC: família, versão, edição normalizada, se está no suporte e até quando, UCPD e arquitetura."""
    so = (perfil.get('so') if isinstance(perfil, dict) else None) or {}
    if not isinstance(so, dict):
        so = {}
    build = int(so.get('build') or 0)
    fam, ver = VERSOES_WINDOWS.get(build, (11 if build >= 22000 else 10 if build >= 10240 else 0, so.get('versao') or ''))
    if build and build not in VERSOES_WINDOWS:   # build mais nova que a tabela: usa a versão que o Windows informa
        ver = so.get('versao') or ver
    tipo = edicao_tipo(so.get('edicao'))
    ciclo = 'ltsc' if tipo in ('ltsc', 'iot') else 'empresa' if tipo in ('empresa', 'educacao') else 'consumo'
    fim = FIM_SUPORTE.get((fam, ver, ciclo)) or (FIM_SUPORTE.get((fam, ver, 'consumo')) if ciclo == 'ltsc' else None)
    hoje = hoje or datetime.now().date()
    sem_suporte = bool(fim) and datetime.fromisoformat(fim).date() < hoje
    esu = fam == 10 and ver == '22H2' and ciclo == 'consumo' and datetime.fromisoformat(ESU_WINDOWS10).date() >= hoje
    return {'familia': fam, 'versao': ver, 'build': build, 'edicao': tipo, 'edicao_nome': NOME_EDICAO.get(tipo, so.get('edicao') or ''),
            'ciclo': ciclo, 'fim_suporte': fim, 'sem_suporte': sem_suporte, 'esu_possivel': esu,
            'antigo_demais': bool(build) and build < BUILD_MINIMO, 'conhecida': build in VERSOES_WINDOWS or build > max(VERSOES_WINDOWS),
            'ucpd': bool(so.get('ucpd')), 'arquitetura': (so.get('arq') or '').upper(), 'server': tipo == 'server',
            'telemetria_desliga_de_todo': tipo in ('empresa', 'educacao', 'server', 'ltsc', 'iot'),
            'consumidor_por_politica': tipo in ('empresa', 'educacao', 'ltsc', 'iot')}


def nome_windows(c):
    if not c.get('familia'):
        return 'Windows'
    return ' '.join(x for x in ('Windows', str(c['familia']), c['versao'], c['edicao_nome']) if x)


def achados_da_versao(c, hoje=None):
    """Achados do raio-x sobre a versão: sem atualizações de segurança, antiga demais, Server."""
    out = []
    if c.get('antigo_demais'):
        out.append((3, 'Windows antigo demais para o Katharos',
                    f'Build {c["build"]}: o Katharos é feito para o Windows 10 1809 ou mais novo.',
                    'Atualize o Windows. Até lá, só o modo seguro vem marcado.', 'atualizar'))
    if c.get('sem_suporte'):
        quando = datetime.fromisoformat(c['fim_suporte']).strftime('%d/%m/%Y')
        if c['esu_possivel']:
            faz = (f'O Windows 10 22H2 ainda pode receber atualizações estendidas grátis até 12/10/2027 (ESU): Configurações > Windows Update > '
                   '"Inscreva-se agora" (pede conta Microsoft de administrador). Ou passe para o Windows 11, se o PC aceitar.')
        elif c['familia'] == 11:
            faz = 'Instale a versão mais nova do Windows 11 pelo Windows Update (Configurações > Windows Update > "Obter as atualizações mais recentes").'
        else:
            faz = 'Atualize para o Windows 10 22H2 (e inscreva no ESU) ou para o Windows 11, se o PC aceitar.'
        out.append((3 if not c['esu_possivel'] else 2, f'{nome_windows(c)} sem atualizações de segurança',
                    f'Esta versão deixou de receber correções de segurança em {quando}.', faz, 'atualizar'))
    if c.get('server'):
        out.append((0, 'Windows Server', 'O Katharos é feito para Windows 10 e 11; num servidor, vários itens não se aplicam.',
                    'Use o modo seguro e revise item por item.', ''))
    return out
