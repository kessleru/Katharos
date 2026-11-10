# ──────────────────────────────────────────────────────────────────────────────
# Autenticidade: este arquivo é mesmo o que o autor publicou?
#   · Sozinho, na abertura: compara o hash deste arquivo com o SHA256SUMS.txt que veio junto (sem rede). Só fala se não bater.
#   · No comando "autenticidade": confere também contra a lista oficial da release no GitHub. A baixada é feita pelo
#     PowerShell, só quando você pede, para um endereço fixo, sem enviar nada. O Python do Katharos continua sem rede.
# Limite honesto: quem trocar o arquivo e o SHA256SUMS.txt juntos engana a conferência local. Por isso existe a online.
# ──────────────────────────────────────────────────────────────────────────────

URL_SOMAS = 'https://raw.githubusercontent.com/kessleru/Katharos/v{versao}/SHA256SUMS.txt'
NOMES_DO_PROGRAMA = ('katharos.py', 'katharos.ps1', 'KATHAROS.bat')


def sha256_de(caminho):
    h = hashlib.sha256()
    with open(caminho, 'rb') as f:
        for bloco in iter(lambda: f.read(1 << 20), b''):
            h.update(bloco)
    return h.hexdigest()


def le_somas(texto):
    """Linhas "hash  nome" (formato do sha256sum e do SHA256SUMS.txt) -> [(hash, nome)]."""
    saida = []
    for linha in (texto or '').splitlines():
        m = re.match(r'^\s*([0-9a-fA-F]{64})\s+\*?(.+?)\s*$', linha)
        if m:
            saida.append((m.group(1).lower(), m.group(2).replace('\\', '/')))
    return saida


def acha_somas(base=None):
    """O SHA256SUMS.txt que veio junto: na pasta do programa ou na de cima (zip do repositório)."""
    base = Path(base) if base else Path(__file__).resolve().parent
    for pasta_ in (base, base.parent):
        c = pasta_ / 'SHA256SUMS.txt'
        if c.is_file():
            return c
    return None


def compara_com_lista(hash_, nome, somas):
    """'ok' se o hash está na lista; 'diferente' se a lista tem esse nome com outro hash; 'sem' se a lista não fala dele."""
    if any(h == hash_ for h, _ in somas):
        return 'ok'
    if any(n.rsplit('/', 1)[-1].lower() == nome.lower() for _, n in somas):
        return 'diferente'
    return 'sem'


def arquivos_do_programa(base=None):
    eu = Path(base) if base else Path(__file__).resolve().parent
    achados = []
    for nome in NOMES_DO_PROGRAMA:
        for pasta_ in (eu, eu.parent):
            c = pasta_ / nome
            if c.is_file() and c not in achados:
                achados.append(c)
                break
    return achados


def baixa_somas_oficiais(versao=None, segundos=25):
    """A lista oficial da release, baixada pelo PowerShell (HTTPS, endereço fixo). Devolve (texto, erro)."""
    if not WINDOWS:
        return '', 'a conferência online usa o PowerShell do Windows'
    url = URL_SOMAS.format(versao=versao or VERSAO)
    ps = shutil.which('powershell.exe') or r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
    cmd = ("[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; "
           f"(Invoke-WebRequest -UseBasicParsing -TimeoutSec {int(segundos)} -Uri '{url}').Content")
    try:
        r = subprocess.run([ps, '-NoProfile', '-NonInteractive', '-Command', cmd], capture_output=True, timeout=segundos + 15,
                           creationflags=0x08000000)
    except (OSError, subprocess.SubprocessError) as e:
        return '', f'não consegui abrir o PowerShell ({e.__class__.__name__})'
    txt = r.stdout.decode('utf-8', 'replace')
    if r.returncode != 0 or not le_somas(txt):
        return '', 'não consegui baixar a lista oficial (sem internet, ou a versão ainda não foi publicada)'
    return txt, ''


def verifica_autenticidade(online=True, segundos=20):
    """Confere os arquivos do programa. Devolve {'nivel', 'arquivos': [(arquivo, hash, local, oficial)], 'erro'}.
    nivel: 'oficial' (bate com a lista da release no GitHub), 'local' (só com a que veio junto), 'diferente' (alguma lista diz que
    é outro arquivo) ou 'sem' (nada para comparar). Verde só em 'oficial' e 'local'; nunca sem ter comparado com algo."""
    arqs = arquivos_do_programa()
    local = acha_somas()
    somas_local = le_somas(local.read_text(encoding='utf-8', errors='replace')) if local else []
    oficial, erro = baixa_somas_oficiais(segundos=segundos) if online else ('', 'pulada (--offline)')
    somas_of = le_somas(oficial)
    linhas, ruim = [], False
    for a in arqs:
        h = sha256_de(a)
        l_ = compara_com_lista(h, a.name, somas_local) if somas_local else 'sem'
        o_ = compara_com_lista(h, a.name, somas_of) if somas_of else 'sem'
        ruim = ruim or 'diferente' in (l_, o_)
        linhas.append((a, h, l_, o_))
    me = [x for x in linhas if x[0].name == 'katharos.py']
    if ruim:
        nivel = 'diferente'
    elif me and me[0][3] == 'ok':
        nivel = 'oficial'
    elif me and me[0][2] == 'ok':
        nivel = 'local'
    else:
        nivel = 'sem'
    return {'nivel': nivel, 'arquivos': linhas, 'erro': erro if not somas_of else '', 'tem_local': bool(local)}


def mostra_autenticidade_no_aceite(t):
    """Na tela do aviso: confere sozinho e mostra o resultado. Devolve False só se o programa NÃO bate com o publicado."""
    t.escreve('  ' + t.p('Conferindo se este programa é o original (baixa só a lista de hashes do GitHub)…', 'sub'))
    try:
        r = verifica_autenticidade(online=True)
    except Exception as e:
        LOG.escreve(f'autenticidade falhou: {e!r}')
        t.nota('Não consegui conferir a autenticidade agora. Rode "katharos autenticidade" depois.', 2)
        return True
    n = r['nivel']
    if n == 'oficial':
        t.ok('Programa autêntico: bate com a lista oficial da versão ' + VERSAO + ' no GitHub.')
    elif n == 'local':
        t.ok('Bate com o SHA256SUMS.txt que veio junto (sem internet para conferir a lista oficial).')
    elif n == 'diferente':
        t.aviso('ESTE PROGRAMA NÃO BATE com o publicado: pode ter sido alterado. Não continue. Baixe de novo em '
                'github.com/kessleru/Katharos/releases e rode "katharos autenticidade".')
        t.escreve()
        return False
    else:
        t.nota('Não deu para conferir (' + (r['erro'] or 'sem lista para comparar') + '). Rode "katharos autenticidade" quando tiver internet.', 2)
    t.escreve()
    return True


def confere_na_abertura(t):
    """Automático e sem rede: só fala se o SHA256SUMS.txt que veio junto diz que este arquivo é outro. Uma vez por arquivo."""
    somas = acha_somas()
    if not somas:
        return
    eu = Path(__file__).resolve()
    h = sha256_de(eu)
    est = estado().get('autenticidade')
    if isinstance(est, dict) and est.get('hash') == h:
        return
    r = compara_com_lista(h, eu.name, le_somas(somas.read_text(encoding='utf-8', errors='replace')))
    marca_estado('autenticidade', {'hash': h, 'resultado': r, 'quando': agora_iso()})
    if r == 'diferente':
        t.aviso('Este katharos.py não bate com o SHA256SUMS.txt que veio junto: pode ter sido alterado depois de publicado. '
                'Rode "katharos autenticidade" para conferir com a lista oficial antes de aplicar qualquer coisa.')


def ferramenta_autenticidade(ctx, args):
    """Confere se os arquivos do programa são os publicados pelo autor."""
    t = ctx.t
    t.titulo('autenticidade')
    t.paragrafo('Confere se este programa é o que o autor publicou. Cada arquivo tem uma impressão digital (SHA-256) que muda '
                'por completo se um byte mudar.', 2, 'sub')
    t.escreve()
    r = verifica_autenticidade(online=not getattr(args, 'offline', False))
    sel = lambda x: {'ok': 'bate', 'diferente': 'NÃO BATE', 'sem': '—'}[x]
    t.escreve('  ' + t.p(f'versão {VERSAO}', 'destaque', True))
    t.tabela(['arquivo', 'SHA-256', 'lista que veio junto', 'lista oficial'],
             [[a.name, h[:12] + '…', sel(l_), sel(o_)] for a, h, l_, o_ in r['arquivos']])
    t.escreve()
    if not r['tem_local']:
        t.nota('Não achei SHA256SUMS.txt ao lado do programa (baixe o zip completo ou a release para ter a lista local).', 2)
    if r['erro']:
        t.nota(f'Conferência online: {r["erro"]}.', 2)
    n = r['nivel']
    if n == 'diferente':
        t.aviso('Algum arquivo NÃO bate. Não aplique nada com este programa: baixe de novo em '
                'github.com/kessleru/Katharos/releases e confira outra vez.')
        return 1
    if n == 'oficial':
        t.ok('katharos.py bate com a lista oficial da versão ' + VERSAO + '.')
    elif n == 'local':
        t.ok('Bate com a lista que veio junto. Para ter certeza de que a lista também é a do autor, rode com internet.')
    else:
        eu = Path(__file__).resolve()
        t.nota('Sem lista para comparar. Hash completo do katharos.py: ' + sha256_de(eu) + '  (compare com a descrição da release).', 2)
    t.escreve()
    t.escreve('  ' + t.p('Um programa alterado poderia mentir nesta tela. Para ter certeza, confira de fora, no PowerShell:', 'destaque', True))
    t.escreve('    Get-FileHash .\\katharos.py -Algorithm SHA256        ' + t.p('(compare com a descrição da release)', 'sub'))
    t.escreve('    gh attestation verify katharos.py --repo kessleru/Katharos        ' + t.p('(assinatura do GitHub; precisa do gh)', 'sub'))
    t.nota('Isto mostra que é o mesmo arquivo publicado, não que é seguro. O código está aberto: leia antes de aplicar.', 2)
    return 0
