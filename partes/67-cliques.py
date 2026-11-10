# ─────────────── cliques no painel: link katharos://comando abre o Katharos já no comando certo ───────────────
# O painel é um HTML sem scripts, então o clique é um link com protocolo próprio, registrado só para o usuário atual (HKCU), por escolha:
#   painel --ativar-cliques   /   painel --desativar-cliques
# Defesa em camadas, porque qualquer página da internet também pode chamar katharos://:
#   1. o navegador pergunta se pode abrir o Katharos;  2. o script de abertura só aceita exatamente `--uri katharos://comando` (sem mais nada);
#   3. o Windows pede administrador (UAC);  4. o Katharos pergunta de novo, por extenso, antes de qualquer comando;  5. o comando segue o fluxo normal,
#   com a própria confirmação e o desfazer. O link nunca leva parâmetros, nunca aplica sozinho e só abre comandos da lista abaixo.
URI_RE = re.compile(r'katharos://([a-z][a-z0-9-]{1,30})/?')
URI_BLOQUEADOS = frozenset({'desfazer', 'socorro', 'importar', 'exportar', 'atalhos', 'turbo', 'manutencao', 'config', 'estado'})
URI_SO_LEITURA = frozenset({'raiox', 'saude', 'verificar', 'benchmark', 'conselheiro', 'painel', 'tendencia', 'seguranca', 'grandes', 'medir', 'memoria', 'portas', 'ajuda'})
URI_CHAVE = r'Software\Classes\katharos'


def uri_para_comando(valor):
    """'katharos://limpar' -> 'limpar'. Qualquer outra forma (maiúscula, parâmetro, caminho, espaço, comando fora da lista) -> None."""
    m = URI_RE.fullmatch(valor or '')
    if not m:
        return None
    cmd = m.group(1)
    return cmd if cmd in COMANDOS and cmd not in URI_BLOQUEADOS else None


def rotulo_clique(cmd):
    return 'Abrir' if cmd in URI_SO_LEITURA else 'Corrigir'


def link_clique(cmd, ativo):
    """O botão do painel. Sem cliques ativados (ou comando fora da lista), não há botão: o painel continua mostrando o comando para digitar."""
    if not ativo or not uri_para_comando(f'katharos://{cmd}'):
        return ''
    aviso = ('Abre o Katharos neste comando; você confirma lá antes de qualquer mudança' if cmd not in URI_SO_LEITURA else 'Abre o Katharos neste comando (só leitura)')
    return f'<a class="agir" href="katharos://{_e(cmd)}" title="{_e(aviso)}">{rotulo_clique(cmd)}</a>'


def linha_de_comando_clique():
    ps1 = Path(__file__).resolve().with_name('katharos.ps1')
    shell = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'WindowsPowerShell' / 'v1.0' / 'powershell.exe'
    return f'"{shell}" -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{ps1}" --uri "%1"'


def cliques_ativos():
    if not WINDOWS:
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, URI_CHAVE + r'\shell\open\command') as k:
            return 'katharos.ps1' in str(winreg.QueryValueEx(k, '')[0])
    except OSError:
        return False


def ativa_cliques(t):
    if not WINDOWS:
        t.erro('Os cliques só funcionam no Windows.')
        return 1
    if dentro_de_pacote():
        t.erro('Este Python roda dentro da Microsoft Store e não grava o registro de verdade. Use o Python de python.org.')
        return 1
    ps1 = Path(__file__).resolve().with_name('katharos.ps1')
    if not ps1.exists():
        t.erro(f'Não achei o {ps1.name} ao lado do programa. Use a pasta extraída do ZIP.')
        return 1
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, URI_CHAVE) as k:
        winreg.SetValueEx(k, '', 0, winreg.REG_SZ, 'URL:Katharos')
        winreg.SetValueEx(k, 'URL Protocol', 0, winreg.REG_SZ, '')
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, URI_CHAVE + r'\shell\open\command') as k:
        winreg.SetValueEx(k, '', 0, winreg.REG_SZ, linha_de_comando_clique())
    e = estado()
    e['cliques_ativos'] = agora_iso()
    salva_estado(e)
    LOG.escreve('cliques do painel ativados (HKCU\\' + URI_CHAVE + ')')
    t.ok('Cliques ativados. Gere o painel de novo ("painel") para os botões aparecerem.')
    t.nota('  Registra o link katharos:// só para o seu usuário. Ao clicar: o navegador pergunta, o Windows pede administrador e o Katharos pergunta de novo antes de qualquer comando.', 2)
    t.nota('  Para remover: painel --desativar-cliques', 2)
    return 0


def desativa_cliques(t):
    if not WINDOWS:
        t.erro('Os cliques só funcionam no Windows.')
        return 1
    import winreg
    for sub in (r'\shell\open\command', r'\shell\open', r'\shell', ''):
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, URI_CHAVE + sub)
        except OSError:
            pass
    e = estado()
    e.pop('cliques_ativos', None)
    salva_estado(e)
    LOG.escreve('cliques do painel desativados')
    t.ok('Cliques desativados: o link katharos:// foi removido do registro.')
    return 0


def abre_por_clique(cru):
    """Chamado pelo link do painel: só aceita exatamente ['--uri', 'katharos://comando']. Pergunta por extenso e então roda o comando como se a pessoa o tivesse digitado."""
    t = Terminal(False, False)
    cmd = uri_para_comando(cru[1]) if len(cru) == 2 and cru[0] == '--uri' else None
    if not cmd:
        t.erro('Link recusado: o Katharos só abre comandos simples da lista, sem parâmetros.')
        LOG.escreve('link recusado: ' + repr(cru)[:200])
        return 2
    desc = COMANDOS[cmd][0]
    t.cabecalho('link do painel', cmd, app=APP)
    t.paragrafo(f'Você clicou em "{rotulo_clique(cmd)}" no painel. Isto abre o comando "{cmd}" ({desc}). Nada muda antes de você confirmar os passos dele.', 2, 'sub')
    if not t.confirma(f'Abrir "{cmd}" agora?', 'sim'):
        t.nota('  Cancelado. Nada foi feito.', 2)
        return 0
    return main([cmd])
