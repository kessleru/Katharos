
# =====================================================================================================================================
#   TAREFAS AGENDADAS DO KATHAROS · conferir se ainda rodam e consertar sozinho
# =====================================================================================================================================
# As duas tarefas (manutenção, elevada, e leitura de 15 min, do usuário) guardam o caminho do Python e do katharos.py do dia em que
# foram criadas. Até a 4.4.0, três coisas as quebravam sem ninguém ver: o Python da Microsoft Store atualizado ou removido (o caminho
# some), a cópia protegida do motor apagando o katharos.py da manutenção em %ProgramData%\Katharos, e o Python da cópia protegida, que
# muda de pasta a cada versão. Agora as tarefas usam caminhos que não mudam: %ProgramData%\Katharos\python (elevada) e o Python do
# Katharos instalado (do usuário). O motor confere ao abrir e conserta o que der.

def _pasta_do_python(py):
    """O Python embutido do Katharos (instalador) tem o python3XX.dll e o python3XX._pth ao lado do executável."""
    d = Path(py).parent
    try:
        return any(d.glob('python3*._pth')) and any(d.glob('python3*.dll'))
    except OSError:
        return False


def python_do_usuario():
    """pythonw.exe para a tarefa do usuário: o do Katharos instalado (o caminho "current" não muda entre versões); senão o que roda agora."""
    base = os.environ.get('LOCALAPPDATA')
    if WINDOWS and base:
        pw = Path(base) / 'Katharos' / 'current' / 'python' / 'pythonw.exe'
        if pw.is_file():
            return pw
    pw = Path(sys.executable).with_name('pythonw.exe')
    return pw if pw.exists() else Path(sys.executable)


def python_da_tarefa_elevada():
    """pythonw.exe para a tarefa elevada. Com o Python embutido do Katharos, uma cópia em %ProgramData%\\Katharos\\python (só administrador
    grava, e não muda de pasta a cada versão). Sem ele (código, Python de python.org), o que roda agora. None se não deu para copiar."""
    atual = Path(sys.executable)
    if not WINDOWS or not _pasta_do_python(atual):
        pw = atual.with_name('pythonw.exe')
        return pw if pw.exists() else atual
    destino = pasta_protegida('python')
    if destino is None:
        return None
    marca = destino / 'katharos-versao.txt'
    assinatura = f'{sys.version}|{atual.parent / "python.exe"}'
    try:
        if not (marca.is_file() and marca.read_text(encoding='utf-8') == assinatura and (destino / 'pythonw.exe').is_file()):
            for sub in list(destino.iterdir()):
                if sub.is_dir() and not sub.is_symlink():
                    shutil.rmtree(sub)
                else:
                    sub.unlink()
            shutil.copytree(atual.parent, destino, dirs_exist_ok=True, symlinks=False,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            marca.write_text(assinatura, encoding='utf-8')
            protege_pasta_da_tarefa(pasta_da_tarefa())
    except OSError as e:
        LOG.escreve(f'tarefas: o Python da tarefa elevada não copiou: {e!r}')
        return None
    return destino / 'pythonw.exe'


TAREFAS_PS = r'''
$__l = @()
foreach ($__n in «nomes») {
    $__t = Get-ScheduledTask -TaskName $__n -ErrorAction SilentlyContinue
    if (-not $__t) { continue }
    $__i = Tenta { $__t | Get-ScheduledTaskInfo -ErrorAction Stop } $null
    $__a = @($__t.Actions)[0]
    $__l += @{ nome = $__n; estado = [string]$__t.State; exe = [string]$__a.Execute; args = [string]$__a.Arguments
               ultima = $(if ($__i -and $__i.LastRunTime -and $__i.LastRunTime.Year -gt 2000) { $__i.LastRunTime.ToString('s') } else { '' })
               resultado = $(if ($__i) { [int64]$__i.LastTaskResult } else { $null }) }
}
Dado 'tarefas' @($__l)
'''


def _script_dos_args(args):
    """O katharos.py que a tarefa executa: o primeiro argumento terminado em .py (a tarefa sem pythonw passa pelo PowerShell)."""
    for m in re.finditer(r'"([^"]+?\.py)"|\'([^\']+?\.py)\'|(\S+?\.py)\b', args or ''):
        return next(g for g in m.groups() if g)
    return ''


def confere_tarefas(ctx):
    """[{nome, estado, exe, script, ultima, resultado, problema}] das tarefas do Katharos que existem. problema é '' quando está tudo certo."""
    if not WINDOWS:
        return []
    nomes = '@(' + ', '.join(psq(n) for n in (TAREFA_MANUT, TAREFA_AMOSTRA)) + ')'
    s = roda_ps(ctx.t, ps_monta(TAREFAS_PS, nomes=nomes), 'tarefas', minutos=1, mostra=False)
    out = []
    for tk in lista(s.dados.get('tarefas')):
        if not isinstance(tk, dict):
            continue
        exe, script = str(tk.get('exe') or ''), _script_dos_args(tk.get('args'))
        problema = ''
        res = tk.get('resultado')
        if tk.get('estado') == 'Disabled':
            problema = 'está desligada no Agendador de Tarefas'
        elif '\\windowsapps\\' in exe.lower():
            # o Python da Loja muda de pasta a cada atualização e não roda direito em tarefa agendada (no PC do dono, as duas davam
            # erro 1 em toda execução): a tarefa passa para o Python do Katharos
            problema = 'usa o Python da Microsoft Store, que falha em tarefa agendada'
        elif isinstance(res, int) and res not in (0, 0x41301, 0x41303, 0x41325) and tk.get('ultima'):
            problema = f'a última execução deu erro (código {res})'
        elif exe and exe.lower() != 'powershell.exe' and not Path(os.path.expandvars(exe)).is_file():
            problema = 'o Python que ela usa não existe mais'
        elif script and not Path(os.path.expandvars(script)).is_file():
            problema = 'o katharos.py que ela roda não existe mais'
        else:
            try:
                ver = Path(script).read_text(encoding='utf-8', errors='replace')[:200000] if script else ''
                m = re.search(r"^VERSAO = '([^']+)'", ver, re.M)
                if m and m.group(1) != VERSAO:
                    problema = f'roda a versão {m.group(1)}, não a {VERSAO}'
            except OSError:
                pass
        out.append({'nome': tk.get('nome'), 'estado': tk.get('estado'), 'exe': exe, 'script': script, 'ultima': tk.get('ultima') or '',
                    'resultado': tk.get('resultado'), 'problema': problema})
    return out


def conserta_tarefas(ctx, elevado=None):
    """Cria de novo as tarefas que existem e estão quebradas (mesma frequência). A elevada só como administrador; a do usuário em qualquer
    motor. Devolve [(nome, 'ok' | 'falhou' | 'precisa_admin', problema)]."""
    elevado = eh_admin() if elevado is None else elevado
    out = []
    for tk in confere_tarefas(ctx):
        if not tk['problema']:
            continue
        if tk['nome'] == TAREFA_MANUT:
            if not elevado:
                out.append((tk['nome'], 'precisa_admin', tk['problema']))
                continue
            r = instala_manutencao(ctx, estado().get('manut_freq') or 'semanal')
        else:
            r = instala_amostra(ctx)
        out.append((tk['nome'], 'ok' if r == 0 else 'falhou', tk['problema']))
        LOG.escreve(f'tarefas: {tk["nome"]} ({tk["problema"]}): ' + ('consertada' if r == 0 else 'não consertou'))
    return out


def cura_ao_abrir(ctx):
    """Dentro do preparo do motor: conserta o que der sem perguntar nada (a pessoa já tinha ligado essas tarefas)."""
    try:
        conserta_tarefas(ctx)
    except Exception as e:
        LOG.escreve(f'tarefas: conferência ao abrir falhou: {e!r}')


def amostra_se_velha(ctx, horas=20):
    """O histórico vem das medidas da manutenção. Se ela não roda (desligada, ou quebrada antes de ser consertada), a janela aberta
    grava uma medida por dia no lugar dela: o histórico não para."""
    try:
        am = le_metricas()
        if am and (datetime.now() - am[-1]['_dt']).total_seconds() < horas * 3600:
            return False
        if _jogo_aberto_agora():
            return False
        return bool(amostra_agora(ctx))
    except Exception as e:
        LOG.escreve(f'histórico: medida do dia falhou: {e!r}')
        return False
