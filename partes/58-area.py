

# ███████████████████████████████████████████████████████████████████████████
#
#   ATALHOS, EXPORTAR/IMPORTAR E ÁREA DE TRABALHO
#   exportar e importar o que foi aplicado, uma pasta "Katharos" na área de trabalho com atalhos que têm o ícone,
#   e organizar a área de trabalho
#
# ███████████████████████████████████████████████████████████████████████████

VALIDOS_CONFIG = {'modo': MODOS, 'explicacao': ('completa', 'curta'), 'cores': ('automático', 'sem cor'),
                  'simbolos': ('automático', 'simples'), 'navegador': ('brave', 'nenhum'), 'confirmar': ('risco', 'sempre', 'nunca'), 'coleta-em-jogo': ('segura', 'pausar'), 'tempo-real': ('1', '2', '5', '10'), 'avisos': ('sim', 'nao'), 'fps': ('sim', 'nao'), 'energia-automatica': ('sim', 'nao'), 'atualizacoes': ('avisar', 'automatico', 'nunca'), 'avisos-intervalo': tuple(str(h) for h in range(1, 49)), 'avisos-no-jogo': ('so-grave', 'nunca', 'todos'), 'resumo-diario': ('sim', 'nao'), 'canal': ('estavel', 'previa'), 'abrir-relatorio': ('perguntar', 'sempre', 'nunca')}
CONFIG_EXPORTAVEL = ('modo', 'explicacao', 'cores', 'simbolos', 'grandes-mb', 'navegador', 'protegidos', 'confirmar')

# Um PC "completo" só para listar os itens sem ler o PC de verdade (site e testes).
PC_MODELO = {'jogos': ['Steam'], 'gpus': ['NVIDIA', 'Intel'], 'so': {'win11': True}, 'pc': {'notebook': True},
             'tem': {'nvidia': True, 'edge': True, 'chrome': True, 'office': True, 'onedrive': True},
             'tela': {'largura': 1920, 'altura': 1080, 'hz': 60, 'hz_max': 144}}


def selecao_do_perfil(ctx, selecao):
    """{pacote: ids ou "@modo"} -> [(pacote, itens)] só com o que existe neste PC e não está protegido."""
    out = []
    for nome, ids in selecao.items():
        if nome not in PACOTES:
            continue
        its = [i for i in (PACOTES[nome].itens(ctx) or []) if i]
        for i in its:
            i.pacote = nome
        if isinstance(ids, str):
            if not ids.startswith('@') or ids[1:] not in MODOS:
                continue
            marca_por_modo(its, ids[1:])
            escolhidos = [i for i in its if i.marcado]
        else:
            quer = {str(x) for x in ids}
            escolhidos = [i for i in its if i.id in quer]
        escolhidos, _ = aplica_protegidos(nome, escolhidos)
        if escolhidos:
            aplica_alertas(nome, escolhidos)
            out.append((PACOTES[nome], escolhidos))
    return out


def pacotes_para_escolher():
    """[(nome, descrição)] dos comandos que são pacotes de itens, na ordem do menu."""
    return [(c, d) for _, _, its in GRUPOS for c, d, f in its if f == 'pacote' and c in PACOTES]


def personaliza_selecao(ctx, args, selecao):
    """Deixa a pessoa ajustar item por item o que vai ser aplicado e juntar outros pacotes. Devolve a nova seleção
    ({pacote: [ids]}) ou None se desistiu."""
    t = ctx.t
    nova = {}
    for nome, ids in selecao.items():
        if nome not in PACOTES:
            continue
        its = [i for i in (PACOTES[nome].itens(ctx) or []) if i]
        for i in its:
            i.pacote = nome
        quer = {str(x) for x in ids} if not isinstance(ids, str) else {i.id for i in its if ids.startswith('@') and ids[1:] in MODOS
                                                                         and (i.nivel and i.nivel <= NIVEL_MODO[ids[1:]])}
        for i in its:
            i.marcado = i.id in quer
        r = escolhe_itens(ctx, its, config('modo'), args, titulo=PACOTES[nome].titulo, manter_marcas=True)
        if r is None:
            return None
        if r:
            nova[nome] = [i.id for i in r]
    lista_pac = pacotes_para_escolher()
    while True:
        t.titulo('juntar mais itens' if nova else 'montar do zero')
        for n, (c, d) in enumerate(lista_pac, 1):
            marca = t.p('✓', 'verde') if c in nova else ' '
            t.escreve(f'  {marca} {t.p(f"{n:>2}", "destaque", True)}  {t.p(f"{c:<14}", "texto", True)} {t.p(corta(d, max(10, t.largura - 26)), "sub")}')
        if not t.interativo or args.sim:
            break
        t.dicas([('número', 'abrir a área'), ('Enter', 'pronto'), ('0', 'cancelar')])
        r = t.pergunta('qual área').strip().lower()
        if r in ('', 'ok', 'pronto'):
            break
        if r in ('0', 'q', 'v'):
            return None
        nome = lista_pac[int(r) - 1][0] if r.isdigit() and 0 < int(r) <= len(lista_pac) else (r if r in dict(lista_pac) else None)
        if not nome:
            t.aviso(f'"{corta(r, 20)}" não é um pacote da lista.')
            continue
        its = [i for i in (PACOTES[nome].itens(ctx) or []) if i]
        for i in its:
            i.pacote = nome
        ja = set(nova.get(nome, []))
        for i in its:
            i.marcado = i.id in ja
        r2 = escolhe_itens(ctx, its, config('modo'), args, titulo=PACOTES[nome].titulo, manter_marcas=True)
        if r2 is None:
            continue
        if r2:
            nova[nome] = [i.id for i in r2]
        else:
            nova.pop(nome, None)
    return nova


def aplica_selecao(ctx, args, titulo, selecao, personalizavel=True):
    """Mostra o que uma configuração importada mudaria, deixa personalizar, pede confirmação e aplica."""
    t = ctx.t
    if not WINDOWS:
        t.erro('O katharos só funciona no Windows.')
        return 1
    if not precisa_admin(ctx, args):
        return 1
    perfil_pc(ctx)
    if not confere_conta(ctx) and not args.teste:
        return 1
    while True:
        alvo = selecao_do_perfil(ctx, selecao) if selecao else []
        if not alvo and not (personalizavel and t.interativo and not args.sim):
            t.ok('Nada a aplicar neste PC: tudo já está assim, não existe aqui, ou está protegido.')
            return 0
        if alvo:
            t.titulo(f'{titulo}: o que será aplicado')
            total = 0
            for pac, its in alvo:
                total += len(its)
                t.escreve('  ' + t.p(pac.titulo, 'texto', True) + '  ' + t.p(pl(len(its), 'item', 'itens'), 'apagado'))
                resumo_antes(t, pac, its, titulo=False, recuo=4)
        else:
            t.nota('  Nada escolhido ainda.')
        if not (personalizavel and t.interativo and not args.sim and not args.teste):
            break
        t.dicas([('Enter', 'continuar'), ('p', 'mudar os itens'), ('0', 'cancelar')])
        r = t.pergunta('o que fazer').strip().lower()
        if r in ('0', 'q'):
            t.nota('nada foi alterado.')
            return 0
        if r in ('p', 'personalizar'):
            nova = personaliza_selecao(ctx, args, selecao)
            if nova is not None:
                selecao = nova
                titulo = 'sua escolha'
            continue
        if not alvo:
            t.nota('nada foi alterado.')
            return 0
        break
    if not alvo:
        t.ok('Nada a aplicar neste PC.')
        return 0
    t.nota('  Quase tudo volta com o "desfazer"; programas e apps removidos não voltam. Para ver item por item, use as telas de cada pacote.')
    if pc_gerenciado(ctx.perfil):
        t.aviso('Este PC parece ser gerenciado por empresa ou escola: a organização pode desfazer estas mudanças.')
    if args.teste:
        t.titulo('simulação (nada é alterado)')
        for pac, its in alvo:
            executa_itens(ctx, pac, its, teste=True)
        return 0
    if not t.confirma(f'Aplicar {pl(total, "item", "itens")} de {pl(len(alvo), "pacote")}?', sim=args.sim):
        t.nota('nada foi alterado.')
        return 0
    garante_ponto(ctx)
    feitos = avisos = erros = 0
    t.titulo('aplicando')
    for pac, its in alvo:
        t.escreve('  ' + t.p(pac.titulo, 'texto', True))
        a, b, c = executa_itens(ctx, pac, its)
        feitos, avisos, erros = feitos + a, avisos + b, erros + c
    if any(p.nome in ('visual', 'interface') for p, _ in alvo):
        roda_ps(t, 'Reinicia-Explorer', 'explorer', minutos=1, mostra=False)
    t.titulo('resumo', caixa=True)
    t.chaves([('itens', str(total)), ('mudanças', t.p(str(feitos), 'verde')), ('avisos', t.p(str(avisos), 'amarelo' if avisos else 'apagado')),
              ('erros', t.p(str(erros), 'vermelho' if erros else 'apagado')), ('desfazer', 'katharos desfazer tudo')])
    t.fecha_caixa()
    manter_ou_desfazer(ctx, args, [p.nome for p, _ in alvo if p.reversivel])
    return 1 if erros else 0


# ─────────────── exportar e importar ───────────────

def perfil_atual():
    return {'katharos': VERSAO, 'tipo': 'perfil', 'criado': agora_iso(), 'modo': config('modo'),
            'pacotes': {n: sorted(r.get('itens', [])) for n, r in (estado().get('pacotes') or {}).items() if n in PACOTES and not r.get('revertido')},
            'config': {k: config(k) for k in CONFIG_EXPORTAVEL if config(k) != PADROES.get(k)}}


_BLOCO_DADOS = re.compile(r'<!-- katharos:dados:inicio -->\s*```json\s*(.*?)\s*```\s*<!-- katharos:dados:fim -->', re.S)


def le_perfil(arq):
    """Lê um perfil exportado (.json) ou o relatório único (.md). Valida tudo: só pacotes que existem e listas de
    ids em texto. O arquivo nunca é executado: os ids só escolhem entre os itens que o próprio Katharos conhece."""
    try:
        txt = Path(arq).expanduser().read_text(encoding='utf-8-sig')
    except OSError:
        return None
    if str(arq).lower().endswith('.md'):
        m = _BLOCO_DADOS.search(txt)
        if not m:
            return None
        txt = m.group(1)
    try:
        d = json.loads(txt)
    except ValueError:
        return None
    if not isinstance(d, dict):
        return None
    brutos = d.get('pacotes') if 'pacotes' in d else {n: (v or {}).get('itens', []) for n, v in (d.get('aplicado') or {}).items() if isinstance(v, dict)}
    pacotes = {}
    for n, ids in (brutos if isinstance(brutos, dict) else {}).items():
        if n in PACOTES and isinstance(ids, list):
            pacotes[n] = [str(i)[:120] for i in ids if isinstance(i, (str, int))][:300]
    cfg = {}
    for k, v in (d.get('config') or {}).items():
        if k not in CONFIG_EXPORTAVEL or not isinstance(v, str) or len(v) > 200:
            continue
        if k in VALIDOS_CONFIG and v not in VALIDOS_CONFIG[k]:
            continue
        if k == 'grandes-mb' and not v.isdigit():
            continue
        cfg[k] = v
    return {'pacotes': pacotes, 'config': cfg}


# ─────────────── ícone, app e atalhos ───────────────

def escreve_icone(destino=None):
    import base64
    destino = Path(destino or (CASA / 'katharos.ico'))
    try:
        dados = base64.b64decode(ICONE_B64)
        if not destino.exists() or destino.stat().st_size != len(dados):
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(dados)
    except (OSError, ValueError):
        return None
    return destino


def instala_app():
    """Copia o programa, o lançador e o ícone para ~/.katharos/app: os atalhos apontam para lá e não quebram se você
    mover a pasta de onde baixou."""
    app = pasta('app')
    origem = Path(__file__).resolve()
    try:
        if origem != (app / 'katharos.py').resolve():
            shutil.copy2(origem, app / 'katharos.py')
        ps1 = origem.parent / 'katharos.ps1'
        if ps1.exists() and ps1.resolve() != (app / 'katharos.ps1').resolve():
            shutil.copy2(ps1, app / 'katharos.ps1')
    except OSError as e:
        LOG.escreve(f'instala_app: {e!r}')
    ico = escreve_icone(app / 'katharos.ico')
    return app, ico


def pasta_desktop():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as k:
            v, _ = winreg.QueryValueEx(k, 'Desktop')
        p = Path(os.path.expandvars(v))
        if p.is_dir():
            return p
    except (ImportError, OSError):
        pass
    for c in (Path.home() / 'Desktop', Path.home() / 'OneDrive' / 'Desktop', Path.home() / 'Área de Trabalho'):
        if c.is_dir():
            return c
    return None


PASTA_ATALHOS = 'Katharos'


def lista_atalhos():
    """[(id, nome do atalho, descrição, argumentos)]: o menu e as ações que mais se repetem."""
    return [('menu', 'Abrir o Katharos', 'O menu do Katharos', ''),
            ('raiox', 'Raio-x do PC', 'Só lê: dá a nota do PC e diz o que fazer primeiro', 'raiox'),
            ('turbo', 'Otimizar tudo', 'Otimiza em sequência, no modo que você escolher, com prévia e confirmação', 'turbo'),
            ('painel', 'Painel', 'Gráficos do PC ao longo do tempo, no navegador', 'painel'),
            ('normal', 'Voltar ao normal', 'Desfaz tudo o que o Katharos mudou, valor por valor', 'desfazer tudo'),
            ('manutencao', 'Manutenção agora', 'Limpeza leve e conferência de saúde do PC', 'agendar --agora'),
            ('organizar', 'Organizar a área de trabalho', 'Separa os arquivos soltos em pastas, com desfazer', 'organizar'),
            ('seguranca', 'Auditoria de segurança', 'Só lê: mostra o que está fraco no PC', 'seguranca'),
            ('relatorio', 'Copiar relatório para a IA', 'Copia o relatório único para colar numa conversa', 'relatorio --copiar')]


ATALHOS_PS = r'''
$desk = [Environment]::GetFolderPath('Desktop')
$pasta = Join-Path $desk «pasta»
$defs = «defs»
if ($TESTE) { Plano ('criar a pasta ' + $pasta + ' com ' + @($defs).Count + ' atalhos'); return }
New-Item -ItemType Directory -Force -Path $pasta | Out-Null
$sh = New-Object -ComObject WScript.Shell
$feitos = 0
foreach ($d in $defs) {
    try {
        $arq = Join-Path $pasta ($d.nome + '.lnk')
        $l = $sh.CreateShortcut($arq)
        $l.TargetPath = «alvo»
        $l.Arguments = «pre» + $d.args
        $l.WorkingDirectory = «trab»
        $l.IconLocation = «ico» + ',0'
        $l.Description = $d.desc
        $l.WindowStyle = 1
        $l.Save()
        if («runas») { $b = [IO.File]::ReadAllBytes($arq); $b[0x15] = $b[0x15] -bor 0x20; [IO.File]::WriteAllBytes($arq, $b) }
        $feitos++
    } catch { Aviso ('atalho ' + $d.nome + ': ' + $_.Exception.Message) }
}
$ini = Join-Path $pasta 'desktop.ini'
try {
    if (Test-Path -LiteralPath $ini) { & attrib.exe -s -h $ini | Out-Null }
    Set-Content -LiteralPath $ini -Value @('[.ShellClassInfo]', ('IconResource=' + «ico» + ',0'), 'InfoTip=Atalhos do Katharos') -Encoding Unicode
    & attrib.exe +s +h $ini | Out-Null
    & attrib.exe +s $pasta | Out-Null
} catch {}
Feito ("{0} atalhos criados em {1}" -f $feitos, $pasta)
Dado 'pasta' $pasta
'''


def cria_atalhos(ctx, ids):
    t = ctx.t
    app, ico = instala_app()
    todos = {a[0]: a for a in lista_atalhos()}
    defs = [todos[i] for i in ids if i in todos]
    ps1 = app / 'katharos.ps1'
    if ps1.exists():
        alvo, pre, runas = 'powershell.exe', f'-NoProfile -ExecutionPolicy Bypass -File "{ps1}" ', False
    else:
        py = sys.executable
        if py.lower().endswith('pythonw.exe'):
            py = py[:-5] + '.exe'
        alvo, pre, runas = py, f'"{app / "katharos.py"}" ', True
    lit = '@(' + ','.join(f"@{{ nome = {psq(n)}; desc = {psq(d)}; args = {psq(a)} }}" for _, n, d, a in defs) + ')'
    corpo = ps_monta(ATALHOS_PS, pasta=psq(PASTA_ATALHOS), defs=lit, alvo=psq(alvo), pre=psq(pre), trab=psq(str(app)),
                     ico=psq(str(ico or '')), runas='$true' if runas else '$false')
    return roda_ps(t, corpo, 'atalhos', minutos=2, teste=getattr(ctx.args, 'teste', False))


def remove_atalhos(t):
    d = pasta_desktop()
    if not d or not (d / PASTA_ATALHOS).is_dir():
        t.nota('  não há pasta Katharos na área de trabalho.')
        return
    alvo = d / PASTA_ATALHOS
    nossos = {n + '.lnk' for _, n, _, _ in lista_atalhos()} | {'desktop.ini'}
    for f in alvo.iterdir():
        if f.name in nossos:
            try:
                if f.name == 'desktop.ini':
                    os.chmod(f, 0o666)
                    if WINDOWS:
                        subprocess.run(['attrib.exe', '-s', '-h', str(f)], capture_output=True)
                f.unlink()
            except OSError:
                pass
    try:
        if WINDOWS:
            subprocess.run(['attrib.exe', '-s', str(alvo)], capture_output=True)
        alvo.rmdir()
        t.ok('Pasta Katharos removida da área de trabalho.')
    except OSError:
        t.aviso('A pasta tem outros arquivos além dos atalhos do Katharos; deixei ela e só tirei os atalhos.')


def escolhe_atalhos(ctx, args):
    t = ctx.t
    t.aba('uma pasta "Katharos" na área de trabalho, com atalhos que têm o ícone do Katharos')
    t.paragrafo('Cada atalho abre o Katharos já na ação escolhida (ele pede administrador). Tudo fica numa pasta só, '
                'para não bagunçar a área de trabalho, e você escolhe quais criar. O que muda o PC sempre mostra a prévia '
                'e pede confirmação.', 2, 'sub')
    if getattr(args, 'remover', False):
        remove_atalhos(t)
        return 0
    if not WINDOWS:
        t.erro('O katharos só funciona no Windows.')
        return 1
    todos = lista_atalhos()
    marcados = {'menu', 'normal'}
    while True:
        t.titulo('atalhos')
        for i, (id_, nome, desc, _) in enumerate(todos, 1):
            m = t.p('✓', 'verde', True) if id_ in marcados else t.p('○', 'apagado')
            t.escreve(f'  {m} {t.p(f"{i:>2}", "destaque", True)}  {t.p(f"{nome:<30}", "texto" if id_ in marcados else "sub")}'
                      f'{t.p(corta(desc, max(10, t.largura - 40)), "apagado")}')
        if getattr(args, 'sim', False) or not t.interativo:
            break
        t.dicas([('Enter', 'criar'), ('número', 'marcar ou desmarcar'), ('0', 'cancelar')])
        r = t.pergunta(f'{len(marcados)} marcados').strip().lower()
        if r in ('', 'ok'):
            break
        if r in ('0', 'q', 'v'):
            return 0
        if r in ('t', 'todos'):
            marcados = {a[0] for a in todos}
        elif r in ('n', 'nenhum'):
            marcados = set()
        else:
            for n in _numeros(r, len(todos)):
                marcados ^= {todos[n - 1][0]}
        t.escreve()
    if not marcados:
        t.nota('nenhum atalho escolhido.')
        return 0
    s = cria_atalhos(ctx, [a[0] for a in todos if a[0] in marcados])
    if not getattr(args, 'teste', False):
        marca_estado('atalhos_criados', agora_iso())
        t.nota('  para tirar: katharos atalhos --remover')
    return 0 if s.ok else 1


# ─────────────── atalhos, exportar e importar ───────────────

def ferramenta_atalhos(ctx, args):
    return escolhe_atalhos(ctx, args)


def ferramenta_exportar(ctx, args):
    t = ctx.t
    alvo = getattr(args, 'alvo', None)
    t.aba('salva o que está aplicado neste PC para repetir em outro')
    dest = Path(alvo).expanduser() if alvo else Path.home() / 'katharos-exportado.json'
    d = perfil_atual()
    if not d['pacotes']:
        t.aviso('Nada aplicado ainda: não há o que exportar.')
        return 0
    grava_json(dest, d)
    t.ok(f'Salvo em {caminho_curto(dest)} ({pl(len(d["pacotes"]), "pacote")}). No outro PC: katharos importar ARQUIVO')
    return 0


def ferramenta_importar(ctx, args):
    t = ctx.t
    alvo = getattr(args, 'alvo', None)
    t.aba('aplica neste PC um arquivo exportado (ou o relatório único)')
    if not alvo and t.interativo and not args.sim:
        alvo = t.pergunta('arquivo (.json ou o relatório .md)').strip().strip('"')
    if not alvo:
        t.erro('Diga o arquivo: katharos importar katharos-exportado.json')
        return 1
    d = le_perfil(alvo)
    if not d or not (d['pacotes'] or d['config']):
        t.erro(f'Não consegui ler um arquivo válido em {alvo}.')
        return 1
    t.info('O arquivo só escolhe entre itens que o Katharos já conhece: nada dele é executado como comando.')
    if d['config']:
        t.titulo('preferências do arquivo')
        t.chaves([(k, v) for k, v in d['config'].items()])
        if not args.teste and t.confirma('Adotar estas preferências?', sim=args.sim):
            for k, v in d['config'].items():
                salva_config(k, v)
    return aplica_selecao(ctx, args, 'arquivo importado', d['pacotes']) if d['pacotes'] else 0


# ─────────────── organizar a área de trabalho ───────────────

CATEGORIAS = {
    'Imagens': 'jpg jpeg png gif webp bmp tif tiff heic heif svg ico raw cr2 nef psd ai xcf',
    'Documentos': 'pdf doc docx odt rtf txt md ppt pptx odp key xls xlsx ods csv epub',
    'Vídeos': 'mp4 mkv avi mov wmv webm flv m4v',
    'Áudio': 'mp3 wav flac ogg m4a aac wma opus',
    'Compactados': 'zip rar 7z tar gz bz2 xz iso',
    'Programas': 'exe msi msix appx appxbundle',
    'Código': 'py js ts tsx jsx json html css java c cpp cs go rs php sql sh ps1 bat cmd yml yaml xml ipynb',
}
EXT_CATEGORIA = {e: c for c, exts in CATEGORIAS.items() for e in exts.split()}
PASTA_ORGANIZADO = 'Organizado'
NAO_MEXER = {'desktop.ini', 'thumbs.db'}


def _oculto(caminho):
    try:
        return bool(getattr(os.stat(caminho), 'st_file_attributes', 0) & 0x6)  # oculto ou de sistema
    except OSError:
        return True


def planeja_organizar(desktop, dias=1, atalhos=False):
    """[(origem, categoria, tamanho)] do que está solto na área de trabalho. Pastas, arquivos ocultos, de sistema,
    modificados há pouco e atalhos (a não ser que peça) ficam onde estão."""
    corte = time.time() - dias * 86400
    out = []
    try:
        itens = sorted(desktop.iterdir(), key=lambda p: p.name.lower())
    except OSError:
        return out
    for f in itens:
        try:
            if not f.is_file() or f.is_symlink() or f.name.lower() in NAO_MEXER or _oculto(f):
                continue
            ext = f.suffix.lower().lstrip('.')
            if ext in ('lnk', 'url'):
                cat = 'Atalhos' if atalhos else None
            else:
                cat = EXT_CATEGORIA.get(ext)
            if not cat or f.stat().st_mtime > corte:
                continue
            out.append((f, cat, f.stat().st_size))
        except OSError:
            continue
    return out


def _destino_livre(pasta_cat, nome):
    alvo = pasta_cat / nome
    n = 2
    while alvo.exists():
        alvo = pasta_cat / f'{Path(nome).stem} ({n}){Path(nome).suffix}'
        n += 1
    return alvo


def desfaz_organizar(ctx):
    t = ctx.t
    diario = sorted(pasta('organizar').glob('*.json'))
    diario = [d for d in diario if not d.name.endswith('.desfeito.json')]
    if not diario:
        t.ok('Nenhuma organização para desfazer.')
        return 0
    # a mais recente cuja área de trabalho ainda existe: uma de pasta que sumiu (OneDrive desligado, por exemplo) não trava as outras
    arq = d = raiz = None
    orfas = 0
    for cand in reversed(diario):
        dd = le_json(cand, {})
        rr = Path(dd.get('desktop', '') or '.')
        if dd.get('desktop') and rr.is_dir():
            arq, d, raiz = cand, dd, rr
            break
        orfas += 1
    if arq is None:
        t.erro('A área de trabalho das organizações guardadas não existe mais.')
        return 1
    if orfas:
        t.nota(f'  {pl(orfas, "organização mais nova ficou de lado", "organizações mais novas ficaram de lado")}: a área de trabalho dela não existe mais.')
    n = pulados = 0
    for m in d.get('movidos', []):
        de, para = Path(m.get('de', '')), Path(m.get('para', ''))
        try:
            dentro = raiz in de.parents and raiz in para.parents
            if dentro and para.exists() and not de.exists():
                shutil.move(str(para), str(de))
                n += 1
            else:
                pulados += 1
        except OSError:
            pulados += 1
    org = raiz / PASTA_ORGANIZADO
    if org.is_dir():
        for sub in sorted(org.iterdir()):
            try:
                if sub.is_dir() and not any(sub.iterdir()):
                    sub.rmdir()
            except OSError:
                pass
        try:
            org.rmdir()
        except OSError:
            pass
    arq.rename(arq.with_name(arq.stem + '.desfeito.json'))
    t.ok(f'{pl(n, "arquivo voltou", "arquivos voltaram")} para a área de trabalho' + (f' ({pulados} já tinham sido mexidos e ficaram como estão)' if pulados else '') + '.')
    return 0


def ferramenta_organizar(ctx, args):
    t = ctx.t
    t.aba('separa os arquivos soltos da área de trabalho em pastas, com desfazer')
    t.paragrafo(f'Move só arquivos soltos (imagens, documentos, vídeos, áudio, compactados, programas e código) para '
                f'"{PASTA_ORGANIZADO}", em uma pasta por tipo. Pastas, atalhos, arquivos ocultos e o que você mexeu hoje ficam onde estão. '
                'Você vê a prévia e confirma; depois, "organizar --desfazer" põe tudo de volta no lugar.', 2, 'sub')
    if getattr(args, 'desfazer', False):
        return desfaz_organizar(ctx)
    desktop = pasta_desktop()
    if not desktop:
        t.erro('Não achei a pasta da área de trabalho.')
        return 1
    dias = args.dias if getattr(args, 'dias', None) is not None else 1
    plano = planeja_organizar(desktop, dias, getattr(args, 'atalhos', False))
    if not plano:
        t.ok('A área de trabalho já está organizada: nada solto para mover.')
        return 0
    cats = {}
    for f, cat, tam in plano:
        c = cats.setdefault(cat, {'n': 0, 'tam': 0, 'ex': []})
        c['n'] += 1
        c['tam'] += tam
        if len(c['ex']) < 3:
            c['ex'].append(f.name)
    nomes = sorted(cats, key=lambda k: -cats[k]['n'])
    t.titulo(f'{pl(len(plano), "arquivo solto", "arquivos soltos")} em {desktop.name}')
    t.tabela(['#', 'pasta', 'arquivos', 'tamanho', 'exemplos'],
             [[str(i), k, str(cats[k]['n']), humano(cats[k]['tam']), corta(tela(', '.join(cats[k]['ex'])), 40)] for i, k in enumerate(nomes, 1)], alinha='eedde')
    escolha = set(nomes)
    if t.interativo and not args.sim and not args.teste:
        r = t.pergunta('só estas (números) ou Enter = todas').strip()
        if r:
            sel = {nomes[n - 1] for n in _numeros(r, len(nomes))}
            escolha = sel or escolha
    plano = [p for p in plano if p[1] in escolha]
    if args.teste:
        t.nota(f'  modo teste: {pl(len(plano), "arquivo seria movido", "arquivos seriam movidos")}.')
        return 0
    if not t.confirma(f'Mover {pl(len(plano), "arquivo", "arquivos")} para {PASTA_ORGANIZADO}?', sim=args.sim):
        t.nota('nada foi movido.')
        return 0
    raiz = desktop / PASTA_ORGANIZADO
    movidos, falhas = [], 0
    for f, cat, _ in plano:
        dest_pasta = raiz / cat
        try:
            dest_pasta.mkdir(parents=True, exist_ok=True)
            alvo = _destino_livre(dest_pasta, f.name)
            if desktop not in alvo.parents:
                continue
            shutil.move(str(f), str(alvo))
            movidos.append({'de': str(f), 'para': str(alvo), 'cat': cat})
        except OSError:
            falhas += 1
    if movidos:
        grava_json(pasta('organizar') / f'{carimbo()}-{int(time.time() * 1000) % 100000:05d}.json', {'quando': agora_iso(), 'desktop': str(desktop), 'movidos': movidos})
        porcat = {}
        for m in movidos:
            porcat[m['cat']] = porcat.get(m['cat'], 0) + 1
        rel_secao('desktop', {'movidos': len(movidos), 'categorias': porcat, 'falhas': falhas})
    t.ok(f'{pl(len(movidos), "arquivo movido", "arquivos movidos")} para {PASTA_ORGANIZADO}' + (f'; {falhas} em uso ficaram onde estavam' if falhas else '') + '.')
    t.nota('  para voltar tudo: katharos organizar --desfazer')
    return 0
