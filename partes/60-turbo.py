

# ███████████████████████████████████████████████████████████████████████████
#
#   PARTE 4 · TURBO, MANUTENÇÃO, REVERSÃO E UTILIDADES
#
# ███████████████████████████████████████████████████████████████████████████

ARQ_TURBO = CASA / 'turbo.json'
TAREFA_CONTINUAR = 'Katharos - continuar depois de reiniciar'
TAREFA_MANUT = 'Katharos - segundo plano'
TAREFA_MANUT_ANTIGA = 'Katharos - manutencao semanal'   # nome até a 1.3: removida junto, para não rodar duas vezes
# Como a tarefa de segundo plano dispara. 'continua' roda ao entrar no Windows e de novo a cada 4 h enquanto o PC estiver ligado.
FREQ_FUNDO = {
    'semanal': ('domingo ao meio-dia', "New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At '12:00'"),
    'diaria': ('todo dia ao meio-dia', "New-ScheduledTaskTrigger -Daily -At '12:00'"),
    'continua': ('ao entrar no Windows e a cada 4 horas', "@((New-ScheduledTaskTrigger -AtLogOn), (New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Hours 4)))"),
}
INTERVALO_MINIMO_H = 3   # duas execuções agendadas nunca ficam mais perto que isso (o disparo ao entrar e o de 4 h não se atropelam)

# ordem do turbo: o que libera recursos primeiro, depois reparo e atualização, limpeza, disco e o reinício
ORDEM_TURBO = ['programas', 'apps', 'ia', 'inicializacao', 'servicos', 'privacidade', 'visual', 'jogos', 'energia',
               'reparar', 'atualizar', 'limpar', 'disco', 'navegador', 'interface']
NIVEL_PACOTE = {'programas': 1, 'apps': 1, 'ia': 2, 'inicializacao': 1, 'servicos': 1, 'privacidade': 1, 'visual': 2,
                'jogos': 1, 'energia': 1, 'reparar': 1, 'atualizar': 1, 'limpar': 1, 'disco': 1, 'navegador': 2, 'interface': 3}


def nivel_etapa_turbo(nome, p):
    """Nível de cada pacote no turbo (1 = entra até no seguro) e a nota que aparece ao lado."""
    n, nota = NIVEL_PACOTE[nome], ''
    if nome == 'jogos':
        nota = 'com os itens de jogo do modo' if joga(p) else 'sem jogos instalados: só o básico'
    if nome == 'navegador' and config('navegador') == 'brave':
        n = 1
    return n, nota


def _espera_bateria(t):
    na_tomada, carga = energia_agora()
    avisou = False
    while not na_tomada and carga is not None and carga < 40:
        if not avisou:
            t.aviso(f'Bateria em {carga}% e fora da tomada: ligue o carregador. Esperando...')
            avisou = True
        time.sleep(30)
        na_tomada, carga = energia_agora()


def tarefa_continuar(ctx, criar=True):
    """Tarefa agendada de uma vez: depois do reinício, no seu logon, abre o turbo de novo como administrador
    (sem lançador escondido: uma janela normal do PowerShell chamando o Python).
    A tarefa é elevada, então o script que ela roda fica na pasta protegida: em ~/.katharos, um programa sem administrador poderia
    trocá-lo antes do próximo logon e ganhar administrador. Sem a proteção, a tarefa não é criada e o turbo continua quando você o abrir."""
    if criar:
        destino = pasta_protegida('turbo')
        if destino is None:
            ctx.t.aviso('Não consegui proteger a pasta da tarefa que continua o turbo. Depois do reinício, abra o Katharos e rode "turbo": '
                        'ele pergunta se continua de onde parou.')
            return False
        script = destino / 'katharos.py'
        try:
            shutil.copy2(Path(__file__).resolve(), script)
        except OSError as e:
            ctx.t.aviso(f'Não consegui copiar o programa para {destino} ({e.__class__.__name__}). Depois do reinício, abra o Katharos e rode "turbo".')
            return False
        if python_em_pasta_do_usuario():
            ctx.t.aviso('O Python que a tarefa usa está dentro da sua pasta de usuário, que programas sem administrador conseguem alterar. '
                        'Para fechar essa brecha, instale o Python "para todos os usuários" (python.org, "Install for all users").')
    if criar:
        cmd = (f"& {psq(sys.executable)} {psq(str(script))} turbo --continuar; Read-Host 'Enter para fechar'")
        corpo = ps_monta(r'''
$__a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -Command "' + «cmd» + '"')
$__t = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$__p = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
$__s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 8)
Register-ScheduledTask -TaskName «nome» -Action $__a -Trigger $__t -Principal $__p -Settings $__s -Force | Out-Null
Ok 'o katharos vai continuar sozinho depois do reinicio, quando voce entrar na conta'
''', cmd=psq(cmd.replace('"', '\\"')), nome=psq(TAREFA_CONTINUAR))
    else:
        corpo = f"Unregister-ScheduledTask -TaskName {psq(TAREFA_CONTINUAR)} -Confirm:$false -ErrorAction SilentlyContinue"
    return roda_ps(ctx.t, corpo, 'tarefa-continuar', minutos=2, mostra=criar).ok


def _resumo_pacotes(t):
    for nome in ORDEM_TURBO:
        pac = PACOTES[nome]
        t.item('·', 'apagado', pac.titulo, t.p(pac.resumo, 'apagado'))


def escolhe_modo(t, args):
    if getattr(args, 'modo', None):
        return args.modo
    padrao = config('modo')
    t.titulo('modo')
    for i, (nome, cor, txt) in enumerate(EXPLICA_MODOS, 1):
        marca = t.p(' (padrão)', 'apagado') if nome == padrao else ''
        t.escreve(f'  {t.p(f"{i:>2}", "destaque", True)}  {t.p(nome, cor, True)}{marca}')
        t.paragrafo(txt, 6, 'sub')
    t.escreve()
    if getattr(args, 'sim', False) or not t.interativo:
        return padrao
    r = t.pergunta('modo: 1, 2 ou 3 (Enter = ' + padrao + ')').strip().lower()
    return {'1': 'seguro', '2': 'equilibrado', '3': 'extremo'}.get(r, r if r in MODOS else padrao)


ETAPAS_FIXAS = ('medir-antes', 'medir-depois', 'reinicio', 'agendar')

# Um turbo começado na 2.5.0 (com "para quê") e continuado nesta versão aplica o que foi aprovado lá.
FOCO_ANTIGO_ITENS = {
    'jogos': {'modo-jogo', 'gamedvr', 'aderencia', 'mouse', 'hags', 'directx-jogos'},
    'jogos-max': {'modo-jogo', 'gamedvr', 'aderencia', 'mouse', 'teclado', 'hags', 'directx-jogos', 'mmcss', 'primeiro-plano', 'rede-jogos', 'timer',
                  'gpu-nvidia', 'gpu-amd'},
}
FOCO_ANTIGO_EXTREMO = {'jogos-max': ('energia', 'visual')}

def le_plano(arq):
    """O plano de um turbo anterior: um .json com etapas, ou o relatório único (.md) de onde ele veio. Só vale o que o
    Katharos conhece: etapas e ids são nomes, nunca comandos."""
    d = le_json(arq, None) if not str(arq).lower().endswith('.md') else None
    if d is None and str(arq).lower().endswith('.md'):
        try:
            m = _BLOCO_DADOS.search(Path(arq).expanduser().read_text(encoding='utf-8-sig'))
            d = (((json.loads(m.group(1)).get('secoes') or {}).get('turbo') or {}).get('dados') or {}) if m else None
        except (OSError, ValueError):
            d = None
    if not isinstance(d, dict) or not isinstance(d.get('etapas'), list):
        return None
    etapas = [e for e in d['etapas'] if isinstance(e, str) and (e in PACOTES or e in ETAPAS_FIXAS)]
    itens = {k: [str(i)[:120] for i in v] for k, v in (d.get('itens') or {}).items() if k in PACOTES and isinstance(v, list)}
    base = {'modo': d.get('modo') if d.get('modo') in MODOS else 'equilibrado', 'etapas': etapas, 'itens': itens}
    if d.get('foco') in FOCO_ANTIGO_ITENS:   # plano gravado pela 2.5.0 com "para quê"
        base['foco'] = d['foco']
    return base


def foco_antigo(t, args):
    """O --foco da 2.5.0. "jogos no máximo" vira --modo extremo quando o modo não veio junto; devolve o foco que vale para o plano
    (jogos ou jogos-max) ou None. Avisa sempre, para ninguém achar que a opção antiga fez o que fazia."""
    foco = getattr(args, 'foco', None)
    if not foco:
        return None
    if foco == 'jogos-max' and not getattr(args, 'modo', None):
        args.modo = 'extremo'
    t.nota('"--foco" saiu na 3.0.0: os jogos vêm dentro do modo ("jogos no máximo" é o --modo extremo).')
    return foco if foco in FOCO_ANTIGO_ITENS else None


def ferramenta_turbo(ctx, args):
    t = ctx.t
    t.aba('otimiza tudo em sequência; continua sozinho depois de reiniciar')
    if not precisa_admin(ctx, args):
        return 1
    foco = foco_antigo(t, args)
    plano = le_json(ARQ_TURBO, None)
    if plano and not plano.get('concluido') and (getattr(args, 'continuar', False) or (t.interativo and not args.teste and
            t.pergunta(f'há um turbo de {str(plano.get("criado", ""))[:10]} pela metade. continuar? s = sim, Enter = começar outro')
            .strip().lower() in ('s', 'sim'))):
        return executa_turbo(ctx, args, plano)
    if getattr(args, 'continuar', False):
        t.nota('nada pela metade para continuar.')
        tarefa_continuar(ctx, criar=False)
        return 0
    t.paragrafo('O turbo junta tudo: cria um ponto de restauração, mede o PC, aplica os pacotes que você escolher, '
                'reinicia e mede de novo. Cada etapa tem limite de tempo (dobrado em HD); se uma travar, ela é encerrada '
                'e o resto segue. Depois do reinício ele continua sozinho de onde parou.', 2, 'sub')
    p = perfil_pc(ctx)
    if not confere_conta(ctx) and not args.teste:
        return 1
    if getattr(args, 'plano', None):
        base = le_plano(args.plano)
        if not base or 'etapas' not in base:
            t.erro(f'não consegui ler o plano {args.plano}.')
            return 1
        plano = {'criado': agora_iso(), 'modo': base.get('modo', 'equilibrado'), 'etapas': base['etapas'], 'itens': base.get('itens', {}),
                 'feitas': [], 'tentativas': {}, 'concluido': False}
        if base.get('foco') or foco:
            plano['foco'] = base.get('foco') or foco
        t.info(f'plano de {caminho_curto(args.plano)}: modo {plano["modo"]}, {pl(len(plano["etapas"]), "etapa")}.')
        if args.teste:
            return 0
        if not t.confirma('Aplicar esse plano neste PC?', sim=args.sim):
            return 0
        grava_json(ARQ_TURBO, plano)
        return executa_turbo(ctx, args, plano)
    modo = escolhe_modo(t, args)
    t.escreve()
    itens = []
    for nome in ORDEM_TURBO:
        pac = PACOTES[nome]
        n, nota = nivel_etapa_turbo(nome, p)
        itens.append(Item(nome, pac.titulo, pac.explica, pac.resumo, '', n, nota=nota))
    itens.append(Item('agendar', 'manutenção semanal automática', 'Tarefa leve que roda com o PC ocioso e na tomada: limpa, '
                      'reaplica o que atualizações desfazem e avisa de problemas de disco.', 'o PC continua leve', 'nenhum', 1))
    itens.append(Item('reinicio', 'reiniciar e medir de novo', 'Reinicia no fim, continua sozinho depois do logon e mede '
                      'o antes e depois com o PC parado.', 'mudanças valem por completo; números reais', 'o PC reinicia', 1))
    escolhidos = escolhe_itens(ctx, itens, modo, args, 'etapas', agrupar=False)
    if not escolhidos:
        t.nota('nada escolhido.')
        return 0
    plano = {'criado': agora_iso(), 'modo': modo, 'etapas': ['medir-antes'] + [i.id for i in escolhidos if i.id != 'reinicio'],
             'itens': {}, 'feitas': [], 'tentativas': {}, 'concluido': False}
    if any(i.id == 'reinicio' for i in escolhidos):
        plano['etapas'] += ['reinicio', 'medir-depois']
    else:
        plano['etapas'] += ['medir-depois']

    # antes de mostrar o plano: o que de cada etapa este PC já tem (modo teste, nada muda)
    resumo_ja = {}
    etapas_pac = [e for e in plano['etapas'] if e in PACOTES]
    if WINDOWS and etapas_pac and not args.teste:
        with Progresso(t, len(etapas_pac), 'conferindo o que já está feito') as pr:
            for e in etapas_pac:
                pr.atual = PACOTES[e].titulo
                its = _itens_da_etapa(ctx, plano, e, filtra_ja=False)
                confere_itens(ctx, its, e)
                resumo_ja[e] = (sum(getattr(x, 'ja', None) is True for x in its), len(its))
                pr.avanca(PACOTES[e].titulo)

    def mostra_plano():
        t.titulo('plano')
        def det(e):
            if e in plano['itens']:
                return pl(len(plano['itens'][e]), 'item', 'itens')
            if e in resumo_ja:
                ja, tot = resumo_ja[e]
                if tot and ja == tot:
                    return 'tudo já feito: pula'
                return f'{tot - ja} a fazer' + (f', {ja} já feitos' if ja else '')
            return ''
        t.passos([('ok' if e in resumo_ja and resumo_ja[e][1] and resumo_ja[e][0] == resumo_ja[e][1] else 'pendente',
                   e if e not in PACOTES else PACOTES[e].titulo, det(e)) for e in plano['etapas']])

    def revisa():
        for i in escolhidos:
            if i.id in PACOTES:
                t.titulo(f'revisar: {PACOTES[i.id].titulo}')
                t.paragrafo(PACOTES[i.id].explica, 2, 'sub')
                its = [x for x in (PACOTES[i.id].itens(ctx) or []) if x]
                for x in its:
                    x.pacote = i.id
                if not its:
                    t.nota('nada a fazer aqui neste PC.')
                    continue
                sel = escolhe_itens(ctx, its, modo, args)
                plano['itens'][i.id] = [x.id for x in (sel or [])]

    mostra_plano()
    if args.teste:
        t.escreve()
        t.nota('modo teste: mostrando o que cada etapa faria.')
        for e in plano['etapas']:
            if e in PACOTES:
                its = _itens_da_etapa(ctx, plano, e)
                if its:
                    t.titulo(PACOTES[e].titulo)
                    executa_itens(ctx, PACOTES[e], its, teste=True)
        return 0
    if args.sim or not t.interativo:
        if not t.confirma(f'Começar o turbo no modo {modo}?', sim=args.sim):
            t.nota('nada foi alterado.')
            return 0
    else:
        # uma pergunta só: começar, revisar item por item ou desistir
        while True:
            t.escreve()
            t.dicas([('Enter', 'começar'), ('r', 'revisar item por item'), ('0', 'cancelar')])
            r = t.pergunta(f'começar o turbo no modo {modo}').strip().lower()
            if r in ('0', 'n', 'nao', 'não', 'q', 'v', 'cancelar'):
                t.nota('nada foi alterado.')
                return 0
            if r in ('r', 'revisar'):
                revisa()
                mostra_plano()
                continue
            if r in ('', 's', 'sim', 'ok'):
                break
            t.aviso(f'"{corta(r, 20)}" não é uma opção.')
    grava_json(ARQ_TURBO, plano)
    rel_secao('turbo', {'modo': plano['modo'], 'etapas': plano['etapas'], 'itens': plano['itens'], 'feitas': [], 'concluido': False})
    t.nota('  o plano ficou no relatório único: em outro PC, rode "katharos turbo --plano" com esse relatório (ou com o arquivo do "exportar").')
    return executa_turbo(ctx, args, plano)


def _itens_da_etapa(ctx, plano, etapa, filtra_ja=True):
    its = [x for x in (PACOTES[etapa].itens(ctx) or []) if x]
    for x in its:
        x.pacote = etapa
    its, _ = aplica_protegidos(etapa, its)
    aplica_alertas(etapa, its)
    if etapa in plano.get('itens', {}):
        ids = set(plano['itens'][etapa])
        its = [x for x in its if x.id in ids]
    else:
        foco = plano.get('foco')
        marca_por_modo(its, 'extremo' if etapa in FOCO_ANTIGO_EXTREMO.get(foco, ()) else plano['modo'])
        if etapa == 'jogos':
            for x in its:
                if x.id in FOCO_ANTIGO_ITENS.get(foco, ()):
                    x.marcado = True
        its = [x for x in its if x.marcado]
    if filtra_ja:   # o que já foi conferido como feito nesta sessão não roda de novo
        cache = getattr(ctx, 'ja', None) or {}
        its = [x for x in its if cache.get((etapa, x.id)) is not True]
    return its


def executa_turbo(ctx, args, plano):
    t = ctx.t
    desliga_edicao_rapida()
    perfil_pc(ctx)
    pid_arq = CASA / 'turbo.pid'
    if pid_arq.exists():
        try:
            outro = int(pid_arq.read_text())
            if outro != os.getpid() and WINDOWS and str(outro) in subprocess.run(['tasklist', '/FI', f'PID eq {outro}'], capture_output=True, text=True).stdout:
                t.aviso('O turbo já está rodando em outra janela. Espere ele terminar.')
                return 0
        except (ValueError, OSError):
            pass
    pid_arq.write_text(str(os.getpid()))
    if t.guia:
        t.fim('começando o turbo', 'nada')
    try:
        garante_ponto(ctx)
        total = len(plano['etapas'])
        for n, etapa in enumerate(plano['etapas'], 1):
            nome = PACOTES[etapa].titulo if etapa in PACOTES else etapa
            if etapa in plano['feitas']:
                continue
            tent = plano['tentativas'].get(etapa, 0)
            if tent >= 3:
                t.aviso(f'{nome}: interrompida 3 vezes; pulei.')
                plano['feitas'].append(etapa)
                grava_json(ARQ_TURBO, plano)
                continue
            plano['tentativas'][etapa] = tent + 1
            grava_json(ARQ_TURBO, plano)
            _espera_bateria(t)
            t.cabecalho(f'turbo › {nome}', f'etapa {n} de {total} · modo {plano["modo"]}', app=APP)
            if etapa == 'medir-antes':
                m = mede(ctx, 'medindo antes')
                salva_medida(m, 'antes')
                plano['antes'] = m
                mostra_medidas(t, m)
            elif etapa == 'medir-depois':
                if t.tty:
                    with Progresso(t, None, 'esperando 2 min de repouso para medir de forma justa') as pr:
                        fim = time.time() + 120
                        while time.time() < fim:
                            pr.atual = f'{int(fim - time.time())} s'
                            time.sleep(1)
                m = mede(ctx, 'medindo depois')
                salva_medida(m, 'depois')
                plano['depois'] = m
                t.titulo('antes e depois')
                mostra_medidas(t, m, plano.get('antes') or {})
            elif etapa == 'agendar':
                instala_manutencao(ctx)
            elif etapa == 'reinicio':
                plano['feitas'].append(etapa)
                grava_json(ARQ_TURBO, plano)
                tarefa_continuar(ctx, criar=True)
                t.aviso('Reiniciando em 60 s. Salve o que estiver aberto. Para cancelar: shutdown /a')
                t.fim('reiniciando', 'aviso')
                subprocess.run(['shutdown', '/r', '/t', '60', '/c', 'Katharos: o turbo continua sozinho depois que você entrar.'])
                return 0
            else:
                its = _itens_da_etapa(ctx, plano, etapa)
                if its:
                    feitos, avisos, erros = executa_itens(ctx, PACOTES[etapa], its)
                    t.nota(f'  {feitos} alterados · {avisos} avisos · {erros} erros')
                    if etapa in ('visual', 'interface'):
                        roda_ps(t, 'Reinicia-Explorer', 'explorer', minutos=1, mostra=False)
                else:
                    t.nota('nada a fazer nesta etapa.')
            plano['feitas'].append(etapa)
            grava_json(ARQ_TURBO, plano)
            t.fim(f'{nome} pronto', 'ok')
        plano['concluido'] = True
        grava_json(ARQ_TURBO, plano)
        tarefa_continuar(ctx, criar=False)
        _relatorio_turbo(plano)
        t.cabecalho('turbo', 'concluído', app=APP)
        t.titulo('resumo', caixa=True)
        t.chaves([('modo', plano['modo']), ('etapas', str(len(plano['feitas']))), ('desfazer', 'katharos desfazer PACOTE')])
        t.relatorio(rel_md_path(), 'relatório único', recuo=2)
        t.fecha_caixa()
        aplicados = [e for e in plano['etapas'] if e in RISCO_ALTO]
        manter_ou_desfazer(ctx, args, aplicados, segundos=120, desfaz_se_calar=False)
        return 0
    finally:
        try:
            pid_arq.unlink()
        except OSError:
            pass


def _relatorio_turbo(plano):
    a, d = plano.get('antes') or {}, plano.get('depois') or {}
    rel_secao('turbo', {'modo': plano['modo'], 'etapas': plano['etapas'], 'itens': plano.get('itens', {}), 'feitas': plano['feitas'],
                        'concluido': bool(plano.get('concluido'))})
    rel_secao('antes_depois', {'linhas': linhas_antes_depois(a, d), 'livre_gb': livre_total_gb(),
                               'pacotes': [e for e in plano['etapas'] if e in PACOTES]})


# ─────────────── manutenção semanal ───────────────

REAPLICA = ('privacidade', 'ia', 'servicos', 'visual', 'energia', 'disco', 'jogos', 'navegador', 'interface')

MANUT_PS = r'''
$__alertas = New-Object System.Collections.Generic.List[string]
function Alerta([string]$T) { $__alertas.Add($T); Aviso $T }
$__livre = 0
Vivo 'limpeza leve'
foreach ($__p in @(@($env:TEMP, 7), @("$env:WINDIR\Temp", 7), @("$env:LOCALAPPDATA\CrashDumps", 7), @("$env:WINDIR\Minidump", 30), @("$env:ProgramData\Microsoft\Windows\WER\ReportArchive", 7), @("$env:ProgramData\Microsoft\Windows\WER\ReportQueue", 7), @("$env:LOCALAPPDATA\Microsoft\Windows\WER", 7), @("$env:WINDIR\Logs\CBS", 30))) { $__livre += LimpaAntigos $__p[0] $__p[1] }
$__pend = (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending') -or (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired')
if (-not $__pend) { $__livre += LimpaAntigos "$env:WINDIR\SoftwareDistribution\Download" 14 }
$__th = @(Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Windows\Explorer" -Filter 'thumbcache_*.db' -Force -ErrorAction SilentlyContinue)
if (($__th | Measure-Object Length -Sum).Sum -gt 200MB) { foreach ($f in $__th) { $l = $f.Length; Remove-Item -LiteralPath $f.FullName -Force -ErrorAction SilentlyContinue; if (-not (Test-Path -LiteralPath $f.FullName)) { $__livre += $l } } }
foreach ($par in @(@('brave', "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\User Data\Default\Cache"), @('chrome', "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache"), @('msedge', "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache"))) {
  if (-not (Get-Process $par[0] -ErrorAction SilentlyContinue) -and (TamanhoPasta $par[1]) -gt 500MB) { $__livre += LimpaAntigos $par[1] 0 }
}
Dado 'livre' $__livre

Vivo 'antivirus'
try {
  $mp = Get-MpComputerStatus -ErrorAction Stop
  if (-not $mp.RealTimeProtectionEnabled) { Alerta 'Defender sem protecao em tempo real. Abra Seguranca do Windows.' }
  $mpc = "$env:ProgramFiles\Windows Defender\MpCmdRun.exe"
  if ($mp.AntivirusSignatureAge -gt 2 -and (Test-Path $mpc)) { $c = Roda $mpc '-SignatureUpdate' 10; if ($c -ne 0) { Alerta ("Definicoes do Defender com {0} dias" -f $mp.AntivirusSignatureAge) } }
  if ($mp.QuickScanAge -gt 14 -and (Test-Path $mpc)) { $c = Roda $mpc '-Scan -ScanType 1' 30; if ($c -eq 2) { Alerta 'A verificacao rapida encontrou ameacas. Abra Seguranca do Windows.' } }
} catch { Alerta 'Nao consegui ler o Defender' }

Vivo 'saude do disco'
if (Tenta { Get-CimInstance -Namespace root\wmi -ClassName MSStorageDriver_FailurePredictStatus -ErrorAction Stop | Where-Object PredictFailure } $null) { Alerta 'O disco indica falha iminente. Faca backup agora.' }
$__erros = @(Get-PhysicalDisk | Get-StorageReliabilityCounter -ErrorAction SilentlyContinue | ForEach-Object { [int]$_.ReadErrorsTotal })
Dado 'erros_leitura' (($__erros | Measure-Object -Sum).Sum)
$__sem = (Get-Date).AddDays(-7)
$__d = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; ProviderName = 'disk','Ntfs','storahci','stornvme','iaStorA'; Level = 1,2; StartTime = $__sem } -ErrorAction SilentlyContinue).Count
if ($__d) { Alerta ("{0} erro(s) de disco nesta semana" -f $__d) }
$__c = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; Id = 41,1001,6008; StartTime = $__sem } -ErrorAction SilentlyContinue).Count
if ($__c) { Alerta ("{0} desligamento(s) inesperado(s) ou tela azul nesta semana" -f $__c) }
$__ld = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
$__pct = [math]::Round($__ld.FreeSpace / $__ld.Size * 100)
if ($__pct -lt 15) { Alerta ("Pouco espaco livre em C: ({0}%)" -f $__pct) }
Dado 'livre_pct' $__pct
Dado 'pendente' $__pend
$__dt = Get-ScheduledTask -TaskPath '\Microsoft\Windows\Defrag\' -TaskName 'ScheduledDefrag' -ErrorAction SilentlyContinue
if ($__dt -and $__dt.State -eq 'Disabled') { $__dt | Enable-ScheduledTask | Out-Null; Info 'otimizacao semanal de disco religada' }
Dado 'alertas' (Lista $__alertas.ToArray())
'''

MENSAL_PS = r'''
try { Checkpoint-Computer -Description 'Manutencao mensal do Katharos' -RestorePointType MODIFY_SETTINGS -ErrorAction Stop; Ok 'ponto de restauracao mensal criado' } catch { Info ('ponto mensal nao criado: ' + $_.Exception.Message) }
try { Delete-DeliveryOptimizationCache -Force -ErrorAction Stop } catch {}
'''

TOAST_PS = r'''
try {
  [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
  $tpl = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
  $n = $tpl.GetElementsByTagName('text')
  [void]$n.Item(0).AppendChild($tpl.CreateTextNode(«titulo»))
  [void]$n.Item(1).AppendChild($tpl.CreateTextNode(«texto»))
  $app = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
  [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app).Show([Windows.UI.Notifications.ToastNotification]::new($tpl))
} catch {}
'''


def recente_h(iso, horas):
    """True se o instante ISO é de menos de `horas` horas atrás (vazio ou ilegível = não é recente)."""
    try:
        return (datetime.now() - datetime.fromisoformat(iso)).total_seconds() < horas * 3600
    except (TypeError, ValueError):
        return False


def ferramenta_manutencao(ctx, args):
    """A manutenção em si: roda pela tarefa agendada (ou pelo menu do agendar, para testar)."""
    t = ctx.t
    t.aba('limpeza leve, reaplica o que atualizações desfazem e confere a saúde do PC')
    if not WINDOWS:
        t.erro('só funciona no Windows.')
        return 1
    if getattr(args, 'agendada', False):
        prioridade_baixa()
        if recente_h(estado().get('manut_ultima'), INTERVALO_MINIMO_H):
            LOG.escreve('manutenção adiada: a última foi há menos de %d h' % INTERVALO_MINIMO_H)
            return 0
        na_tomada, _ = energia_agora()
        if not na_tomada:
            LOG.escreve('manutenção adiada: na bateria')
            return 0
    inicio = time.time()
    p = perfil_pc(ctx)
    e = estado()
    reapl = 0
    with Progresso(t, None, 'manutenção') as pr:
        s = roda_ps(t, MANUT_PS, 'manutencao', minutos=45, pr=pr, mult=1.0, mostra=not getattr(args, 'agendada', False))
        alertas = lista(s.dados.get('alertas'))
        erros_ant = e.get('manut_erros_leitura')
        erros = s.dados.get('erros_leitura')
        if isinstance(erros_ant, int) and isinstance(erros, int) and erros > erros_ant:
            alertas.append(f'Erros de leitura do disco subiram de {erros_ant} para {erros}. Faça backup.')
        if isinstance(erros, int):
            e['manut_erros_leitura'] = erros
        if s.dados.get('pendente'):
            e.setdefault('manut_pendente_desde', agora_iso())
            try:
                if (datetime.now() - datetime.fromisoformat(e['manut_pendente_desde'])).days >= 3:
                    alertas.append('Há atualizações esperando reinício há mais de 3 dias. Reinicie o PC.')
            except ValueError:
                pass
        else:
            e.pop('manut_pendente_desde', None)
        # reaplica o que pertence a cada pacote ainda ativo (grandes atualizações religam serviços e sugestões)
        for nome, reg in (e.get('pacotes') or {}).items():
            if nome not in REAPLICA or reg.get('revertido') or time.time() - inicio > 40 * 60:
                continue
            ids = set(reg.get('itens', []))
            its = [i for i in (PACOTES[nome].itens(ctx) or []) if i and i.id in ids and i.definitivo]
            its, _ = aplica_protegidos(nome, its)
            if not its:
                continue
            pr.atual = f'reaplicando {PACOTES[nome].titulo}'
            corpo = '\n'.join(_envolve(i) for i in its)
            r = roda_ps(t, corpo, f'reaplica-{nome}', minutos=8, pacote=nome, pr=pr, mostra=False)
            reapl += len(r.feitos)
        ult = e.get('manut_mensal')
        mensal = True
        try:
            mensal = not ult or (datetime.now() - datetime.fromisoformat(ult)).days >= 30
        except ValueError:
            pass
        if mensal and time.time() - inicio < 35 * 60:
            pr.atual = 'mensal: ponto de restauração e limpeza de componentes'
            roda_ps(t, MENSAL_PS, 'mensal', minutos=10, pr=pr, mostra=False)
            cod, _ = roda_exe(['DISM.exe', '/Online', '/Cleanup-Image', '/StartComponentCleanup'], 35, pr)
            if cod != -1:
                e['manut_mensal'] = agora_iso()
    try:   # o motor viu travadas sem nenhum limite: mede uma vez qual driver é (fora do jogo; esta tarefa já roda como administrador)
        tv = roda_travadas_se_pendente(pr)
        if tv:
            alertas += [f'travadas: {c["o_que"]} ({c["driver"]}), até {br(c["maior_ms"], 1)} ms' for c in analisa_travadas(tv)[:2]]
    except Exception as ex:
        LOG.escreve(f'manutenção: travadas: {ex!r}')
    alertas += avisa_tendencia(ctx, e)
    alertas += avisa_saude(ctx, e)
    alertas += avisa_propostas(e, ctx)
    livre = s.dados.get('livre') or 0
    e['manut_ultima'] = agora_iso()
    salva_estado(e)
    dur = time.time() - inicio
    rel_secao('manutencao', {'liberado': humano(livre), 'reaplicadas': reapl, 'livre_pct': s.dados.get('livre_pct', '?'), 'alertas': alertas,
                             'duracao': duracao(dur)})
    rel_eventos([{'tipo': 'espaco', 'pacote': 'manutencao', 'livre_antes': 0, 'livre_depois': int(livre or 0), 'texto': f'limpeza leve: {humano(livre)}'}]
                if livre else [])
    LOG.escreve(f'manutenção: {humano(livre)} liberados, {reapl} reaplicadas, {len(alertas)} alertas')
    if alertas:
        roda_ps(t, ps_monta(TOAST_PS, titulo=psq('Katharos'), texto=psq(f'{len(alertas)} alerta(s): {alertas[0]}')), 'aviso', minutos=1, mostra=False)
    t.titulo('resumo', caixa=True)
    t.chaves([('liberado', humano(livre)), ('reaplicadas', str(reapl)), ('alertas', t.p(str(len(alertas)), 'amarelo' if alertas else 'verde'))])
    t.relatorio(rel_md_path(), 'relatório único', recuo=2)
    return 0


def pasta_da_tarefa():
    """Onde fica a cópia do programa que a tarefa ELEVADA executa. %ProgramData%\\Katharos: só administradores gravam ali. Se ficasse em
    ~/.katharos, qualquer programa rodando como o seu usuário (sem administrador) poderia trocar o arquivo e ganhar administrador no próximo logon."""
    base = os.environ.get('ProgramData') if WINDOWS else None
    return Path(base) / 'Katharos' if base else CASA


def protege_pasta_da_tarefa(pasta):
    """Pasta só com SYSTEM e Administradores gravando (por SID, vale em qualquer idioma); Usuários só leem e executam. True se o icacls aceitou.
    O dono passa a ser Administradores (quem criou a pasta antes, sem administrador, continuaria podendo mudar as permissões) e o que já estava
    dentro volta a herdar da pasta (um arquivo deixado ali com permissão própria continuaria gravável)."""
    def icacls(*a):
        return subprocess.run(['icacls', *a], capture_output=True, text=True, timeout=60).returncode == 0
    try:
        if not icacls(str(pasta), '/setowner', '*S-1-5-32-544', '/T', '/C', '/Q'):
            return False
        try:
            tem_dentro = any(Path(pasta).iterdir())
        except OSError:
            tem_dentro = False
        if tem_dentro and not icacls(str(Path(pasta) / '*'), '/reset', '/T', '/C', '/Q'):
            return False
        return icacls(str(pasta), '/inheritance:r', '/grant:r', '*S-1-5-18:(OI)(CI)F', '*S-1-5-32-544:(OI)(CI)F', '*S-1-5-32-545:(OI)(CI)RX')
    except (OSError, subprocess.SubprocessError):
        return False


_PROTEGIDA = {}


def pasta_protegida(*partes):
    """Subpasta de %ProgramData%\\Katharos, onde só administradores gravam, para tudo o que um processo elevado executa ou em que confia:
    a cópia do programa das tarefas, os scripts temporários do PowerShell e o backup do desfazer. Em ~/.katharos, qualquer programa rodando
    como o seu usuário (sem administrador) poderia trocar esses arquivos e ganhar administrador. Só no Windows e como administrador;
    devolve None se não der para proteger."""
    if not WINDOWS or not eh_admin():
        return None
    base = pasta_da_tarefa()
    chave = str(base)
    if chave not in _PROTEGIDA:
        try:
            base.mkdir(parents=True, exist_ok=True)
            _PROTEGIDA[chave] = protege_pasta_da_tarefa(base)
        except OSError:
            _PROTEGIDA[chave] = False
        if not _PROTEGIDA[chave]:
            LOG.escreve(f'não consegui proteger {base}: nada elevado vai usar essa pasta')
    if not _PROTEGIDA[chave]:
        return None
    d = base.joinpath(*partes)
    d.mkdir(parents=True, exist_ok=True)
    return d


_BACKUP_MIGRADO = []


def dir_backup():
    """Onde fica o backup do desfazer. No Windows, na pasta protegida (o desfazer roda como administrador e executa o que está guardado ali);
    na primeira vez como administrador, o que estava em ~/.katharos/backup (versões até a 3.0.3) vai para lá."""
    if not WINDOWS:
        return CASA / 'backup'
    novo = pasta_da_tarefa() / 'backup'
    if not _BACKUP_MIGRADO and pasta_protegida('backup'):
        _BACKUP_MIGRADO.append(True)
        velho = CASA / 'backup'
        try:
            for sub in (list(velho.iterdir()) if velho.is_dir() else []):
                if sub.is_dir() and not sub.is_symlink() and not (novo / sub.name).exists():
                    shutil.move(str(sub), str(novo / sub.name))
            if velho.is_dir() and not any(velho.iterdir()):
                velho.rmdir()
        except OSError as e:
            LOG.escreve(f'backup antigo não foi movido: {e!r}')
        protege_pasta_da_tarefa(pasta_da_tarefa())   # o que veio de ~/.katharos passa a herdar a proteção
    return novo


def python_em_pasta_do_usuario():
    """O Python que a tarefa elevada usa está numa pasta que um programa sem administrador consegue alterar (AppData, por exemplo)?"""
    try:
        return str(Path(sys.executable).resolve()).lower().startswith(str(Path.home().resolve()).lower())
    except (OSError, RuntimeError):
        return False


def executavel_sem_janela():
    """(executável, True) com pythonw.exe quando existe (não abre console: nada pisca na tela); senão o python.exe e False."""
    pw = Path(sys.executable).with_name('pythonw.exe')
    if pw.exists():
        return str(pw), True
    py = sys.executable
    return (py[:-11] + 'python.exe' if py.lower().endswith('pythonw.exe') else py), False


def instala_manutencao(ctx, freq='semanal'):
    if freq not in FREQ_FUNDO:
        freq = 'semanal'
    t = ctx.t
    quando, gatilho = FREQ_FUNDO[freq]
    pasta = pasta_da_tarefa()
    pasta.mkdir(parents=True, exist_ok=True)
    if WINDOWS and not protege_pasta_da_tarefa(pasta):
        t.erro(f'Não consegui proteger a pasta {pasta} (só administradores devem gravar nela). Sem isso a tarefa elevada ficaria insegura; nada foi criado.')
        return 1
    script = pasta / 'katharos.py'
    shutil.copy2(Path(__file__).resolve(), script)
    exe, sem_janela = executavel_sem_janela()
    arg = subprocess.list2cmdline([str(script), 'manutencao', '--agendada', '--sem-cor'])
    if WINDOWS and python_em_pasta_do_usuario():
        t.aviso('O Python que a tarefa usa está dentro da sua pasta de usuário, que programas sem administrador conseguem alterar; a tarefa roda como administrador e herdaria esse risco. '
                'Para fechar essa brecha, instale o Python "para todos os usuários" (python.org, marque "Install for all users": vai para Arquivos de Programas) e rode "agendar" de novo.')
    if not sem_janela:
        t.aviso('Não achei o pythonw.exe ao lado do Python: a tarefa pode piscar uma janela ao rodar. O Python de python.org traz o pythonw.exe.')
    corpo = ps_monta(r'''
$__a = New-ScheduledTaskAction -Execute «exe» -Argument «arg»
$__t = «gatilho»
$__p = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
$__s = New-ScheduledTaskSettingsSet -RunOnlyIfIdle -IdleDuration (New-TimeSpan -Minutes 10) -IdleWaitTimeout (New-TimeSpan -Hours 12) -RestartOnIdle -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1) -Priority 7 -MultipleInstances IgnoreNew
if ($TESTE) { Plano 'criar a tarefa de segundo plano'; return }
Unregister-ScheduledTask -TaskName «antiga» -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName «nome» -Action $__a -Trigger $__t -Principal $__p -Settings $__s -Description 'Limpeza leve, saude do disco e reaplicacao das otimizacoes, em segundo plano, sem janela. Criada pelo Katharos.' -Force | Out-Null
# confere lendo de volta: a tarefa existe e está pronta
$__tk = Get-ScheduledTask -TaskName «nome» -ErrorAction SilentlyContinue
if ($__tk -and "$($__tk.State)" -ne 'Disabled') { Feito 'manutenção sozinha ligada: «quando», com o PC ocioso por 10 min e na tomada' }
else { Erro 'o Windows não mostra a tarefa de manutenção depois de criar: nada foi ligado' }
''', exe=psq(exe), arg=psq(arg), nome=psq(TAREFA_MANUT), antiga=psq(TAREFA_MANUT_ANTIGA), gatilho=gatilho, quando=quando)
    s = roda_ps(ctx.t, corpo, 'agendar', minutos=2)
    if s.ok and not s.erros:
        marca_estado('manut_freq', freq)
        if freq == 'continua':
            instala_amostra(ctx)   # a leitura de 15 min (temperatura e consumo, sem janela) faz parte do modo contínuo
        else:
            remove_amostra(ctx)
        return 0
    return 1


def ferramenta_agendar(ctx, args):
    t = ctx.t
    t.aba('manutenção sozinha: o Katharos cuida do PC quando você não está usando')
    t.paragrafo('É uma tarefa do próprio Windows que acorda quando o PC está ocioso há 10 min e na tomada, '
                'em prioridade baixa, e para sozinha se você voltar a usar. Limpa temporários e caches antigos, reaplica o que grandes '
                'atualizações desfazem (só dos pacotes que você aplicou e não desfez), atualiza o Defender, confere SMART, '
                'erros de disco, telas azuis e espaço livre, e uma vez por mês cria um ponto de restauração. '
                'Só avisa (notificação do Windows) quando há algo errado. Escolha quando: semanal (domingo), diária ou '
                'contínua (ao iniciar com o Windows e a cada 4 horas, e liga também o acompanhamento em segundo plano: '
                'o ícone com as métricas ao vivo e as sessões de jogo).', 2, 'sub')
    if not precisa_admin(ctx, args):
        return 1
    s = roda_ps(t, f"$__x = Get-ScheduledTask -TaskName {psq(TAREFA_MANUT)} -ErrorAction SilentlyContinue; if (-not $__x) {{ $__x = Get-ScheduledTask -TaskName {psq(TAREFA_MANUT_ANTIGA)} -ErrorAction SilentlyContinue }}; if ($__x) {{ Dado 'tarefa' @{{ estado = [string]$__x.State; ultima = (Tenta {{ ($__x | Get-ScheduledTaskInfo).LastRunTime.ToString('s') }} '') }} }}",
                'tarefa', minutos=1, mostra=False)
    tk = s.dados.get('tarefa')
    freq_atual = estado().get('manut_freq') or ('semanal' if tk else '')
    t.titulo('situação')
    t.chaves([('segundo plano', ('ligado (' + FREQ_FUNDO.get(freq_atual, ('', ''))[0] + ')') if tk else 'desligado'),
              ('última vez', ha_quanto_iso(estado().get('manut_ultima')) or '-')])
    freq = getattr(args, 'frequencia', None)
    if getattr(args, 'remover', False):
        acao = 'r'
    elif getattr(args, 'agora', False):
        acao = 'a'
    elif freq:
        acao = 'c'
    elif args.sim or not t.interativo:
        acao, freq = 'c', freq_atual or 'semanal'
    else:
        t.escreve()
        t.paragrafo('s = semanal · d = diária · c = contínua (inicia com o Windows e a cada 4 h) · a = rodar agora · r = desligar · Enter = voltar', 2, 'apagado')
        r = t.pergunta('fazer').strip().lower()[:1]
        acao = 'c' if r in ('s', 'd', 'c') else r
        freq = {'s': 'semanal', 'd': 'diaria', 'c': 'continua'}.get(r)
    if acao == 'c':
        return instala_manutencao(ctx, freq or 'semanal')
    if acao == 'a':
        return ferramenta_manutencao(ctx, args)
    if acao == 'r':
        for nome in (TAREFA_MANUT, TAREFA_MANUT_ANTIGA):
            roda_ps(t, f"Unregister-ScheduledTask -TaskName {psq(nome)} -Confirm:$false -ErrorAction SilentlyContinue", 'remover', minutos=1, mostra=False)
        remove_amostra(ctx)
        try:
            (pasta_da_tarefa() / 'katharos.py').unlink()
        except OSError:
            pass
        e = estado()
        e.pop('manut_freq', None)
        salva_estado(e)
        t.ok('Manutenção sozinha desligada. O acompanhamento em segundo plano (ícone) continua; "segundo-plano --desligar" fecha ele.')
    return 0


# ─────────────── restaurar e desfazer ───────────────

def desfaz_pacote(ctx, nome, teste=False):
    t = ctx.t
    bk = dir_backup() / nome
    if not (bk / 'mudancas.jsonl').exists():
        t.nota(f'  {nome}: nada guardado para desfazer.')
        return 0
    s = roda_ps(t, '', f'desfazer-{nome}', minutos=10, pacote=nome, teste=teste, desfaz=True)
    if not teste:
        e = estado()
        if nome in e.get('pacotes', {}):
            e['pacotes'][nome]['revertido'] = True
            e['pacotes'][nome]['revertido_em'] = agora_iso()
        salva_estado(e)
    return 0 if s.ok else 1


def ferramenta_desfazer(ctx, args):
    t = ctx.t
    t.aba('volta cada mudança ao valor exato de antes')
    t.paragrafo('Cada pacote guardou o valor anterior de tudo que mudou: registro, tipo de início dos serviços, tarefas, '
                'plano de energia e atalhos. Programas e apps removidos não voltam por aqui (reinstale pela Loja ou pelo site). '
                'Para voltar o PC inteiro, use o ponto de restauração "Antes do Katharos" (comando restaurar).', 2, 'sub')
    if not precisa_admin(ctx, args):
        return 1
    e = estado().get('pacotes', {})
    com_backup = [n for n in PACOTES if (dir_backup() / n / 'mudancas.jsonl').exists()]
    if not com_backup:
        t.ok('Nenhuma mudança guardada para desfazer.')
        return 0
    alvo = [x for x in (getattr(args, 'pacotes', None) or []) if x]
    if not alvo:
        t.titulo('pacotes com mudanças guardadas')
        for i, n in enumerate(com_backup, 1):
            q = ha_quanto_iso((e.get(n) or {}).get('quando', ''))
            t.escreve(f'  {t.p(f"{i:>2}", "destaque", True)}  {t.p(PACOTES[n].titulo, "texto")}' + t.p(f'  {n} · aplicado {q}', 'apagado'))
        t.escreve()
        if not t.interativo:
            return 0
        r = t.pergunta('desfazer quais (números, "tudo" ou Enter = nenhum)').strip().lower()
        if not r:
            return 0
        alvo = com_backup if r in ('tudo', 't') else [com_backup[n - 1] for n in _numeros(r, len(com_backup))]
    elif alvo == ['tudo']:
        alvo = com_backup
    alvo = [a for a in alvo if a in com_backup]
    if not alvo:
        t.aviso('nenhum desses pacotes tem mudanças guardadas.')
        return 1
    if not args.teste and not t.confirma('Desfazer ' + ', '.join(PACOTES[a].titulo for a in alvo) + '?', sim=args.sim):
        return 0
    for a in alvo:
        t.titulo(PACOTES[a].titulo)
        desfaz_pacote(ctx, a, args.teste)
    if not args.teste:
        roda_ps(t, 'Reinicia-Explorer', 'explorer', minutos=1, mostra=False)
        t.aviso('Reinicie o PC para tudo voltar por completo.')
    return 0


def ferramenta_restaurar(ctx, args):
    t = ctx.t
    t.aba('pontos de restauração do Windows e reversão dos pacotes')
    if not precisa_admin(ctx, args):
        return 1
    s = roda_ps(t, r"Dado 'pontos' (Lista @(Tenta { Get-ComputerRestorePoint -ErrorAction Stop | Sort-Object SequenceNumber -Descending | Select-Object -First 8 | ForEach-Object { [pscustomobject]@{ n = $_.SequenceNumber; d = [string]$_.Description; q = ([Management.ManagementDateTimeConverter]::ToDateTime($_.CreationTime)).ToString('s') } } } @()))",
                'pontos', minutos=2, mostra=False)
    pts = lista(s.dados.get('pontos'))
    t.titulo('pontos de restauração')
    if pts:
        t.tabela(['quando', 'descrição'], [[x.get('q', '')[:16].replace('T', ' '), x.get('d', '')] for x in pts])
    else:
        t.nota('  nenhum ponto (a Proteção do Sistema pode estar desligada).')
    if not t.interativo:
        return 0
    t.escreve()
    t.paragrafo('p = criar um ponto agora · r = abrir a Restauração do Sistema (volta o PC inteiro) · '
                'd = desfazer pacotes do katharos · Enter = voltar', 2, 'apagado')
    a = t.pergunta('fazer').strip().lower()[:1]
    if a == 'p':
        marca_estado('ultimo_ponto', '')
        garante_ponto(ctx)
    elif a == 'r':
        subprocess.Popen(['rstrui.exe'])
        t.info('A Restauração do Sistema abriu numa janela própria.')
    elif a == 'd':
        args.pacotes = []
        return ferramenta_desfazer(ctx, args)
    return 0


def ferramenta_estado(ctx, args):
    t = ctx.t
    t.aba('o que já foi aplicado neste PC')
    e = estado()
    pacs = e.get('pacotes', {})
    t.titulo('pacotes')
    if not pacs:
        t.nota('  nada aplicado ainda.')
    linhas = []
    for n, r in pacs.items():
        situ = t.p('desfeito', 'amarelo') if r.get('revertido') else t.p('ativo', 'verde')
        linhas.append([PACOTES[n].titulo if n in PACOTES else n, situ, ha_quanto_iso(r.get('quando')), str(len(r.get('itens', [])))])
    if linhas:
        t.tabela(['pacote', 'situação', 'quando', 'itens'], linhas, alinha='eeed')
    plano = le_json(ARQ_TURBO, None)
    t.titulo('outros')
    t.chaves([('turbo', ('concluído' if plano.get('concluido') else f'pela metade ({len(plano.get("feitas", []))} de {len(plano.get("etapas", []))})') if plano else 'nunca rodou'),
              ('manutenção', ha_quanto_iso(e.get('manut_ultima')) or 'nunca rodou'),
              ('ponto de restauração', ha_quanto_iso(e.get('ultimo_ponto')) or '-'),
              ('medidas salvas', str(len(medidas_salvas()))), ('dados', caminho_curto(CASA))])
    return 0


# ─────────────── grandes: arquivos grandes, duplicados e instaladores velhos ───────────────

def _hash(arq, tudo=False):
    h = hashlib.sha1()
    with open(arq, 'rb') as f:
        if not tudo:
            h.update(f.read(1 << 20))
        else:
            for bloco in iter(lambda: f.read(1 << 20), b''):
                h.update(bloco)
    return h.hexdigest()


def ferramenta_grandes(ctx, args):
    t = ctx.t
    t.aba('seus arquivos grandes, duplicados e instaladores velhos')
    t.paragrafo('Olha suas pastas (Downloads, Documentos, Área de Trabalho, Vídeos, Imagens, Música). Nada é apagado de vez: '
                'o que você escolher vai para a Lixeira, e eu confiro se chegou lá. Arquivos dentro do OneDrive só aparecem '
                '(mandar para a Lixeira lá dentro pode apagar de vez e sumir em todos os aparelhos).', 2, 'sub')
    casa = Path.home()
    pastas = [Path(x) for x in (args.pastas or [])] or [casa / n for n in ('Downloads', 'Documents', 'Desktop', 'Videos', 'Pictures', 'Music')]
    od = os.environ.get('OneDrive') or os.environ.get('OneDriveConsumer') or ''
    minimo = (args.mb or int(config('grandes-mb'))) * 2**20
    arquivos = []
    with Progresso(t, None, 'procurando') as pr:
        for base in pastas:
            for raiz, dirs, nomes in os.walk(base):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', 'AppData', '$RECYCLE.BIN')]
                for n in nomes:
                    c = os.path.join(raiz, n)
                    try:
                        st = os.stat(c)
                    except OSError:
                        continue
                    if st.st_size >= 10 * 2**20:
                        arquivos.append((c, st.st_size, st.st_mtime))
                pr.avanca(raiz, 0)
                pr.n = len(arquivos)
    grandes = sorted([a for a in arquivos if a[1] >= minimo], key=lambda a: -a[1])[:25]
    por_tam = {}
    for a in arquivos:
        por_tam.setdefault(a[1], []).append(a)
    dups = []
    with Progresso(t, None, 'comparando duplicados') as pr:
        for tam, grupo in por_tam.items():
            if len(grupo) < 2:
                continue
            por_h = {}
            for a in grupo:
                try:
                    por_h.setdefault(_hash(a[0]), []).append(a)
                except OSError:
                    pass
            for g in por_h.values():
                if len(g) > 1:
                    try:
                        hs = {}
                        for a in g:
                            hs.setdefault(_hash(a[0], True), []).append(a)
                        dups += [sorted(x, key=lambda a: a[2]) for x in hs.values() if len(x) > 1]
                    except OSError:
                        pass
            pr.avanca(str(tam))
    velhos = [a for a in arquivos if a[0].startswith(str(casa / 'Downloads')) and re.search(r'\.(exe|msi|iso|zip|rar|7z)$', a[0], re.I)
              and time.time() - a[2] > 30 * 86400]
    opcoes = []
    t.titulo(f'maiores que {humano(minimo)}')
    for c, tam, mt in grandes:
        opcoes.append(c)
        no_od = od and c.startswith(od)
        t.item(t.p(f'{len(opcoes):>2}', 'destaque', True), None, caminho_curto(tela(c)), t.p(humano(tam), 'texto') + (t.p(' · OneDrive', 'amarelo') if no_od else ''))
    if not grandes:
        t.nota('  nenhum.')
    t.titulo('duplicados (a cópia mais nova pode sair)')
    soma = 0
    for g in dups[:15]:
        for c, tam, mt in g[1:]:
            opcoes.append(c)
            soma += tam
            t.item(t.p(f'{len(opcoes):>2}', 'destaque', True), None, caminho_curto(tela(c)), t.p(humano(tam), 'texto') + t.p(' igual a ' + tela(Path(g[0][0]).name), 'apagado'))
    if not dups:
        t.nota('  nenhum.')
    t.titulo('instaladores e compactados em Downloads há mais de 30 dias')
    for c, tam, mt in sorted(velhos, key=lambda a: -a[1])[:15]:
        if c not in opcoes:
            opcoes.append(c)
            t.item(t.p(f'{len(opcoes):>2}', 'destaque', True), None, caminho_curto(tela(c)), t.p(humano(tam), 'texto'))
    if not velhos:
        t.nota('  nenhum.')
    if not opcoes or args.teste or not t.interativo:
        return 0
    t.escreve()
    r = t.pergunta('mandar para a Lixeira (números, ex.: 1 3 5-7; Enter = nada)').strip()
    nums = _numeros(r, len(opcoes))
    escolha = [opcoes[n - 1] for n in nums if not (od and opcoes[n - 1].startswith(od))]
    if len(escolha) < len(nums):
        t.aviso('Arquivos do OneDrive ficaram: copie para fora, confira e apague você mesmo.')
    if not escolha or not t.confirma(f'Mandar {pl(len(escolha), "arquivo")} para a Lixeira?', sim=args.sim):
        return 0
    lista_ps = ps_lista(escolha)
    corpo = r'''Add-Type -AssemblyName Microsoft.VisualBasic
foreach ($__f in «lista») {
  try { [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($__f, 'OnlyErrorDialogs', 'SendToRecycleBin'); if (Test-Path -LiteralPath $__f) { Aviso ('ficou: ' + $__f) } else { Feito ('na Lixeira: ' + (Split-Path $__f -Leaf)) } }
  catch { Aviso ((Split-Path $__f -Leaf) + ': ' + $_.Exception.Message) }
}'''
    roda_ps(t, ps_monta(corpo, lista=lista_ps), 'lixeira', minutos=5)
    return 0


# ─────────────── memória ───────────────

MEMORIA_PS = r'''
$m = Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
$os = Get-CimInstance Win32_OperatingSystem
$standby = [double]$m.StandbyCacheCoreBytes + [double]$m.StandbyCacheNormalPriorityBytes + [double]$m.StandbyCacheReserveBytes
$comp = Tenta { (Get-Process -Name 'Memory Compression' -ErrorAction Stop).WorkingSet64 } 0
Dado 'mem' @{ total = [double]$os.TotalVisibleMemorySize * 1KB; livre_de_verdade = [double]$m.FreeAndZeroPageListBytes; disponivel = [double]$m.AvailableBytes; standby = $standby; modificada = [double]$m.ModifiedPageListBytes; comprometida = [double]$m.CommittedBytes; limite = [double]$m.CommitLimit; pool = [double]$m.PoolNonpagedBytes; compressao = [double]$comp }
Dado 'top' (Lista (Get-Process | Group-Object ProcessName | ForEach-Object { [pscustomobject]@{ n = $_.Name; mb = [math]::Round(($_.Group | Measure-Object WorkingSet64 -Sum).Sum / 1MB); q = $_.Count } } | Sort-Object mb -Descending | Select-Object -First 10))
'''


def _limpa_standby():
    """Esvazia a lista de espera (standby) da memória, como o RAMMap faz. Precisa de administrador."""
    import ctypes.wintypes as w
    adv, k32, nt = ctypes.windll.advapi32, ctypes.windll.kernel32, ctypes.windll.ntdll

    class LUID(ctypes.Structure):
        _fields_ = [('LowPart', w.DWORD), ('HighPart', w.LONG)]

    class TP(ctypes.Structure):
        _fields_ = [('PrivilegeCount', w.DWORD), ('Luid', LUID), ('Attributes', w.DWORD)]

    tok = w.HANDLE()
    if not adv.OpenProcessToken(k32.GetCurrentProcess(), 0x0020 | 0x0008, ctypes.byref(tok)):
        return False
    luid = LUID()
    if not adv.LookupPrivilegeValueW(None, 'SeProfileSingleProcessPrivilege', ctypes.byref(luid)):
        return False
    tp = TP(1, luid, 2)
    adv.AdjustTokenPrivileges(tok, False, ctypes.byref(tp), 0, None, None)
    cmd = ctypes.c_int(4)  # MemoryPurgeStandbyList
    return nt.NtSetSystemInformation(80, ctypes.byref(cmd), ctypes.sizeof(cmd)) == 0


def ferramenta_memoria(ctx, args):
    t = ctx.t
    t.aba('como a RAM está sendo usada e o que dá para liberar de verdade')
    if not WINDOWS:
        t.erro('só funciona no Windows.')
        return 1
    s = roda_ps(t, MEMORIA_PS, 'memoria', minutos=2, mostra=False)
    m = s.dados.get('mem') or {}
    tot = m.get('total') or 1
    t.titulo('memória agora')
    usada = tot - (m.get('disponivel') or 0)
    t.barra('em uso', usada, tot, t.p(humano(usada), 'texto'), 'amarelo' if usada / tot > 0.8 else 'destaque', larg_rotulo=12)
    t.barra('em espera', m.get('standby', 0), tot, t.p(humano(m.get('standby', 0)), 'texto'), 'azul', larg_rotulo=12)
    t.barra('livre', m.get('livre_de_verdade', 0), tot, t.p(humano(m.get('livre_de_verdade', 0)), 'texto'), 'verde', larg_rotulo=12)
    t.chaves([('comprometida', f'{humano(m.get("comprometida", 0))} de {humano(m.get("limite", 0))}'),
              ('comprimida', humano(m.get('compressao', 0))), ('pool do kernel', humano(m.get('pool', 0)))])
    t.paragrafo('"Em espera" é cache: arquivos e programas que o Windows guarda para abrir rápido de novo, e que ele '
                'devolve na hora quando algum programa precisa. Por isso "liberar RAM" quase sempre é placebo. Só ajuda '
                'quando um jogo engasga logo depois de fechar algo pesado.', 2, 'apagado')
    t.titulo('quem mais usa')
    t.tabela(['programa', 'RAM', 'janelas'], [[x.get('n'), f'{x.get("mb")} MB', str(x.get('q'))] for x in lista(s.dados.get('top'))])
    if args.teste or not t.interativo:
        return 0
    if t.pergunta('esvaziar a memória em espera agora? s = sim, Enter = não').strip().lower() in ('s', 'sim'):
        if not eh_admin():
            t.aviso('precisa de administrador.')
            return 1
        antes = (roda_ps(t, MEMORIA_PS, 'memoria', minutos=2, mostra=False).dados.get('mem') or {}).get('livre_de_verdade', 0)
        ok = _limpa_standby()
        depois = (roda_ps(t, MEMORIA_PS, 'memoria', minutos=2, mostra=False).dados.get('mem') or {}).get('livre_de_verdade', 0)
        if ok:
            t.ok(f'feito: livre de verdade foi de {humano(antes)} para {humano(depois)}.')
        else:
            t.aviso('o Windows não deixou.')
    return 0
