

# ███████████████████████████████████████████████████████████████████████████
#
#   SEGURANÇA E CONFIANÇA
#   itens protegidos, PC de empresa, "manter alterações?", verificação do que foi aplicado,
#   auditor de segurança (só lê), portas abertas, segredos esquecidos em arquivos e cartão de resultado
#
# ███████████████████████████████████████████████████████████████████████████

def livre_bytes():
    try:
        return shutil.disk_usage(os.environ.get('SystemDrive', 'C:') + '\\').free
    except OSError:
        return None


# ─────────────── itens que a pessoa pediu para nunca mexer ───────────────

def protegidos():
    """config protegidos = "rdp,servicos:xbox,ini:OneDrive": ids soltos ou pacote:id (separe por vírgula)."""
    return {x.strip().lower() for x in re.split(r'[,;]+', str(config('protegidos') or '')) if x.strip()}


def aplica_protegidos(pac_nome, itens):
    """Tira os itens protegidos. Devolve (itens que sobram, quantos saíram)."""
    prot = protegidos()
    if not prot:
        return itens, 0
    fica = [i for i in itens if i.id.lower() not in prot and f'{pac_nome}:{i.id}'.lower() not in prot and pac_nome.lower() not in prot]
    return fica, len(itens) - len(fica)


# ─────────────── avisos por item (o que pode dar problema depois) ───────────────

ALERTA_ITEM = {
    ('jogos', 'mpo'): 'mexe no caminho de vídeo do Windows; se um jogo com anti-cheat (Vanguard, EasyAntiCheat, FACEIT, BattlEye) reclamar depois, desfaça este item',
    ('jogos', 'hags'): 'mexe no agendador de GPU; se um jogo com anti-cheat reclamar ou a imagem falhar, desfaça este item',
    ('jogos', 'timer'): 'mexe no temporizador do sistema; se um jogo com anti-cheat reclamar depois, desfaça este item',
    ('jogos', 'mmcss'): 'mexe no agendador de multimídia; se um jogo com anti-cheat reclamar depois, desfaça este item',
    ('jogos', 'fse'): 'muda como jogos em tela cheia são tratados; se um jogo com anti-cheat reclamar depois, desfaça este item',
    ('jogos', 'gpu-nvidia'): 'mexe na energia da placa de vídeo; se o driver ou um jogo com anti-cheat reclamar depois, desfaça este item',
    ('jogos', 'gpu-amd'): 'mexe na energia da placa de vídeo; se o driver ou um jogo com anti-cheat reclamar depois, desfaça este item',
}


def aplica_alertas(pac_nome, itens):
    for it in itens:
        a = ALERTA_ITEM.get((pac_nome, it.id))
        if a and not getattr(it, 'alerta', ''):
            it.alerta = a


# ─────────────── PC de empresa ou escola ───────────────

def pc_gerenciado(p):
    return bool(pf(p, 'pc.gerenciado') or pf(p, 'pc.dominio'))


def cuidado_empresa(ctx, args, pac):
    """PC com domínio, Intune ou conta de trabalho/escola: política da organização pode desfazer ou até travar mudanças.
    Devolve (pode seguir, modo a usar)."""
    t = ctx.t
    modo = getattr(args, 'modo', None) or config('modo')
    if not pc_gerenciado(ctx.perfil or {}) or pac.nome in ('limpar', 'reparar', 'grandes'):
        return True, modo
    porque = pf(ctx.perfil or {}, 'pc.gerenciado_por') or 'domínio, Intune ou conta de trabalho'
    t.aviso(f'Este PC é gerenciado por uma empresa ou escola ({porque}). A organização pode '
            'desfazer estas mudanças, e mexer em serviços e políticas pode violar a política de TI.')
    if not getattr(args, 'modo', None) and modo != 'seguro':
        modo = 'seguro'
        t.nota('  por isso o modo desta tela ficou "seguro" (você ainda pode marcar o que quiser).')
    if args.sim or not t.interativo or args.teste:
        return True, modo
    if t.pergunta('continuar mesmo assim? s = sim, Enter = não').strip().lower() not in ('s', 'sim'):
        t.nota('nada foi alterado.')
        return False, modo
    return True, modo


# ─────────────── "manter alterações?" ───────────────

RISCO_ALTO = ('servicos', 'jogos', 'energia', 'disco', 'visual')


def espera_tecla(t, segundos, texto):
    """Espera uma tecla com contagem regressiva. Devolve a tecla (minúscula) ou None se acabou o tempo
    (ou se não há teclado para ler)."""
    if not WINDOWS or not (sys.stdin and sys.stdin.isatty()):
        return None
    try:
        import msvcrt
    except ImportError:
        return None
    fim = time.time() + segundos
    try:
        while True:
            resta = fim - time.time()
            if resta <= 0:
                return None
            t.vivo(f'{texto} {int(resta) + 1} s')
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ('\x00', '\xe0'):
                    msvcrt.getwch()
                    continue
                return ch.lower()
            time.sleep(0.15)
    finally:
        t.para_vivo()


def manter_ou_desfazer(ctx, args, nomes, segundos=90, desfaz_se_calar=True):
    """Como a troca de resolução do Windows: depois de mudar algo de risco, pergunta se está tudo bem. Se o PC ficar
    pior (tela preta, sem som, jogo que não abre), é só deixar o tempo passar ou apertar D."""
    t = ctx.t
    modo = str(config('confirmar') or 'risco')
    if modo == 'nunca' or getattr(args, 'sim', False) or getattr(args, 'teste', False) or not t.interativo or not nomes:
        return
    if modo == 'risco':
        nomes = [n for n in nomes if n in RISCO_ALTO]
    if not nomes:
        return
    t.titulo('está tudo funcionando?')
    quem = ', '.join(PACOTES[n].titulo for n in nomes)
    t.paragrafo(f'Olhe o PC por um instante ({quem}). M = manter · D = desfazer agora. ' +
                (f'Se não responder em {segundos} s, o Katharos desfaz sozinho: assim, se algo travar, não precisa fazer nada.'
                 if desfaz_se_calar else f'Se não responder em {segundos} s, ele mantém.'), 2, 'sub')
    r = espera_tecla(t, segundos, '  M mantém · D desfaz · desfazendo sozinho em' if desfaz_se_calar else '  M mantém · D desfaz · mantendo sozinho em')
    if r == 'm' or (r is None and not desfaz_se_calar):
        t.ok('Mantido.')
        return
    t.aviso('Desfazendo.' if r == 'd' else 'Sem resposta: desfazendo para garantir.')
    for n in nomes:
        desfaz_pacote(ctx, n)
    roda_ps(t, 'Reinicia-Explorer', 'explorer', minutos=1, mostra=False)
    rel_eventos([{'tipo': 'desfeito', 'texto': f'{", ".join(nomes)}: ' + ('você pediu' if r == 'd' else 'sem resposta em ' + str(segundos) + ' s')}])


# ─────────────── verificar o que foi aplicado ───────────────

def verifica_pacote(ctx, nome, ids=None):
    """Roda de novo, em modo teste, os itens de configuração aplicados: o que ainda "mudaria" é o que não ficou
    (ou que o Windows desfez depois). Devolve a lista de textos."""
    pac = PACOTES[nome]
    reg = (estado().get('pacotes') or {}).get(nome) or {}
    ids = set(ids if ids is not None else reg.get('itens', []))
    its = [i for i in (pac.itens(ctx) or []) if i and i.id in ids and i.definitivo]
    its, _ = aplica_protegidos(nome, its)
    if not its:
        return []
    s = roda_ps(ctx.t, '\n'.join(_envolve(i) for i in its), f'verifica-{nome}', minutos=8, teste=True, mostra=False, mult=ctx.mult)
    return list(s.planos)


def ferramenta_aplicado(ctx, args):
    """A lista do que este PC já tem, área por área: confere item por item em modo teste (nada muda)."""
    t = ctx.t
    t.aba('o que já está feito neste PC, área por área (feito pelo Katharos, por você ou por outro programa)')
    t.paragrafo('Cada ajuste é conferido do jeito que seria aplicado, só que sem gravar nada: se o PC já está como o ajuste deixaria, '
                'ele conta como feito. Só entram ajustes que ficam gravados no Windows. Ações que se repetem (limpar disco, otimizar a unidade) '
                'e as que só dá para saber aplicando ficam de fora, porque com o tempo o PC volta a precisar delas.', 2, 'sub')
    if not precisa_admin(ctx, args):
        return 1
    perfil_pc(ctx)
    ctx.ja = None   # a lista é sempre conferida de novo ao abrir: o que está feito hoje pode ter mudado desde a última vez
    reg = estado().get('pacotes') or {}
    areas = [n for n in REAPLICA if n in PACOTES]
    res = []
    with Progresso(t, len(areas), 'conferindo') as pr:
        for n in areas:
            pr.atual = PACOTES[n].titulo
            its = [i for i in (PACOTES[n].itens(ctx) or []) if i]
            for i in its:
                i.pacote = n
            its, _ = aplica_protegidos(n, its)
            confere_itens(ctx, its, n)
            res.append((n, its))
            pr.avanca(PACOTES[n].titulo)
    tot_ja = tot_falta = 0
    for n, its in res:
        ja = [i for i in its if i.ja is True]
        falta = [i for i in its if i.ja is False]
        tot_ja, tot_falta = tot_ja + len(ja), tot_falta + len(falta)
        if not ja and not falta:
            continue
        pelo = set((reg.get(n) or {}).get('itens', [])) if not (reg.get(n) or {}).get('revertido') else set()
        t.titulo(f'{PACOTES[n].titulo} · {len(ja)} de {len(ja) + len(falta)} feitos')
        for i in ja:
            t.escreve('  ' + t.p('✓', 'verde', True) + ' ' + t.p(corta(i.titulo, t.largura - 24), 'texto')
                      + t.p('  pelo Katharos' if i.id in pelo else '  já estava assim', 'apagado'))
        for i in falta:
            nv = {1: 'seguro', 2: 'equilibrado', 3: 'extremo'}.get(i.nivel, 'opcional')
            t.escreve('  ' + t.p('○', 'apagado') + ' ' + t.p(corta(i.titulo, t.largura - 24), 'sub') + t.p(f'  falta ({nv})', 'apagado'))
    t.titulo('resumo', caixa=True)
    t.chaves([('já feitos', t.p(str(tot_ja), 'verde')), ('faltam', str(tot_falta))])
    t.fecha_caixa()
    if tot_falta:
        t.nota('  para fazer o que falta: katharos turbo (ou abra a área, como katharos privacidade). O que já está feito não vem marcado.')
    rel_eventos([{'tipo': 'aplicado', 'texto': f'{tot_ja} ajustes já feitos, {tot_falta} faltando'}])
    return 0


def ferramenta_verificar(ctx, args):
    t = ctx.t
    t.aba('confere se o que foi aplicado continua valendo (grandes atualizações do Windows desfazem coisas)')
    t.paragrafo('Para cada pacote de configuração que você aplicou, o Katharos refaz a conta em modo teste: o que ainda "mudaria" '
                'foi desfeito pelo Windows, por um programa ou por uma política. Nada é alterado aqui sem você pedir.', 2, 'sub')
    if not precisa_admin(ctx, args):
        return 1
    perfil_pc(ctx)
    aplicados = [n for n, r in (estado().get('pacotes') or {}).items() if n in REAPLICA and n in PACOTES and not r.get('revertido')]
    if not aplicados:
        t.ok('Nenhum pacote de configuração aplicado para conferir.')
        return 0
    desvios, ok = [], []
    with Progresso(t, len(aplicados), 'conferindo') as pr:
        for n in aplicados:
            pr.atual = PACOTES[n].titulo
            planos = verifica_pacote(ctx, n)
            if planos:
                desvios.append((n, planos))
            else:
                ok.append(n)
            pr.avanca(PACOTES[n].titulo)
    t.titulo('resultado')
    for n in ok:
        t.item('✓', 'verde', PACOTES[n].titulo, t.p('tudo como foi aplicado', 'apagado'))
    for n, planos in desvios:
        t.item('●', 'amarelo', PACOTES[n].titulo, t.p(pl(len(planos), 'ajuste voltou', 'ajustes voltaram'), 'amarelo'))
        for x in planos[:5]:
            t.paragrafo('· ' + corta(x, 90), 6, 'sub')
    rel_secao('verificacao', {'conferidos': aplicados, 'desvios': [{'pacote': n, 'o_que': '; '.join(p_[:6])} for n, p_ in desvios]})
    if desvios and not args.teste and (args.sim or (t.interativo and t.pergunta('reaplicar agora o que voltou? s = sim, Enter = não').strip().lower() in ('s', 'sim'))):
        garante_ponto(ctx)
        for n, _ in desvios:
            reg = estado()['pacotes'][n]
            its = [i for i in (PACOTES[n].itens(ctx) or []) if i and i.id in set(reg.get('itens', [])) and i.definitivo]
            its, _x = aplica_protegidos(n, its)
            r = roda_ps(t, '\n'.join(_envolve(i) for i in its), f'reaplica-{n}', minutos=8, pacote=n, mostra=False, mult=ctx.mult)
            t.ok(f'{PACOTES[n].titulo}: {pl(len(r.feitos), "mudança reaplicada", "mudanças reaplicadas")}')
    return 0


# ─────────────── auditor de segurança (só lê) ───────────────

ESCUTA_PS = r'''
$escuta = @(Tenta { Get-NetTCPConnection -State Listen -ErrorAction Stop | ForEach-Object {
    $pr = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
    $cam = ''; $ini = ''
    try { $cam = [string]$pr.Path } catch {}
    try { $ini = $pr.StartTime.ToString('s') } catch {}
    [pscustomobject]@{ porta = [int]$_.LocalPort; ip = [string]$_.LocalAddress; pid = [int]$_.OwningProcess; nome = [string]$pr.ProcessName; caminho = $cam; inicio = $ini }
} } @())
'''

SEGURANCA_PS = ESCUTA_PS + r'''
$mp = Tenta { Get-MpComputerStatus -ErrorAction Stop }
$fw = @(Tenta { Get-NetFirewallProfile -ErrorAction Stop | ForEach-Object { [pscustomobject]@{ nome = [string]$_.Name; ligado = ([string]$_.Enabled -eq 'True') } } } @())
$uac = Tenta { Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' -ErrorAction Stop } $null
$bl = Tenta { [string](Get-BitLockerVolume -MountPoint $env:SystemDrive -ErrorAction Stop).ProtectionStatus } $null
$tpm = Tenta { $x = Get-Tpm -ErrorAction Stop; @{ presente = [bool]$x.TpmPresent; pronto = [bool]$x.TpmReady } } $null
$sb = Tenta { [bool](Confirm-SecureBootUEFI -ErrorAction Stop) } $null
$smb1 = Tenta { [bool](Get-SmbServerConfiguration -ErrorAction Stop).EnableSMB1Protocol } $null
$ts = Tenta { Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server' -ErrorAction Stop } $null
$nla = Tenta { [int](Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -ErrorAction Stop).UserAuthentication } $null
$semSenha = @(Tenta { Get-LocalUser -ErrorAction Stop | Where-Object { $_.Enabled -and -not $_.PasswordRequired } | ForEach-Object { [string]$_.Name } } @())
$guest = Tenta { [bool](Get-LocalUser -ErrorAction Stop | Where-Object { $_.SID.Value -like '*-501' } | Select-Object -First 1).Enabled } $false
$ss = Tenta { [string](Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer' -ErrorAction Stop).SmartScreenEnabled } $null
$lsa = Tenta { [int](Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -ErrorAction Stop).RunAsPPL } $null
$dg = Tenta { [int](Get-CimInstance -Namespace root\Microsoft\Windows\DeviceGuard -ClassName Win32_DeviceGuard -ErrorAction Stop).VirtualizationBasedSecurityStatus } $null
$hot = Tenta { $h = Get-HotFix -ErrorAction Stop | Where-Object { $_.InstalledOn } | Sort-Object InstalledOn -Descending | Select-Object -First 1; if ($h) { [int]((Get-Date) - $h.InstalledOn).TotalDays } else { $null } } $null
$wu = Tenta { [string](Get-CimInstance Win32_Service -Filter "Name='wuauserv'" -ErrorAction Stop).StartMode } $null
Dado 'seg' @{
    defender = @{ tempo_real = [bool]$mp.RealTimeProtectionEnabled; ativo = [bool]$mp.AntivirusEnabled; idade_definicoes = $(if ($mp) { [int]$mp.AntivirusSignatureAge } else { $null }); adulteracao = $(if ($mp) { [bool]$mp.IsTamperProtected } else { $null }); lido = [bool]$mp }
    firewall = (Lista $fw)
    uac = @{ ligado = $(if ($uac) { [int]$uac.EnableLUA } else { $null }); admin = $(if ($uac) { [int]$uac.ConsentPromptBehaviorAdmin } else { $null }) }
    bitlocker = $bl; tpm = $tpm; secureboot = $sb; smb1 = $smb1
    rdp = @{ ligado = $(if ($ts) { ([int]$ts.fDenyTSConnections -eq 0) } else { $false }); nla = $nla }
    sem_senha = (Lista $semSenha); guest = $guest; smartscreen = $ss; lsa = $lsa; vbs = $dg; dias_sem_atualizar = $hot; wu = $wu
    escuta = (Lista $escuta)
}
'''

PORTAS_SENSIVEIS = {21: ('FTP', 3), 23: ('Telnet', 3), 135: ('RPC do Windows', 1), 139: ('NetBIOS', 2), 445: ('compartilhamento de arquivos (SMB)', 2),
                    3389: ('Área de Trabalho Remota', 2), 5985: ('WinRM', 2), 5986: ('WinRM', 2), 5900: ('VNC', 3), 22: ('SSH', 1),
                    3306: ('MySQL', 2), 5432: ('PostgreSQL', 2), 27017: ('MongoDB', 3), 6379: ('Redis', 3), 1433: ('SQL Server', 2)}


def _dedup_portas(escuta):
    vistos, out = set(), []
    for x in lista(escuta):
        if not isinstance(x, dict):
            continue
        chave = (x.get('porta'), x.get('pid'))
        if chave in vistos:
            continue
        vistos.add(chave)
        ip = str(x.get('ip', ''))
        x['exposta'] = ip not in ('127.0.0.1', '::1')
        out.append(x)
    return sorted(out, key=lambda x: (not x['exposta'], x.get('porta') or 0))


def avalia_seguranca(f, p):
    """Devolve (achados [(gravidade, título, evidência, como corrigir)], verificações ok [texto], não deu para ler [texto])."""
    A, ok, nao = [], [], []
    d = f.get('defender') or {}
    avs = lista(p.get('antivirus'))
    outro_av = any(a.get('ativo') and not re.search('defender', str(a.get('nome', '')), re.I) for a in avs)
    if d.get('lido'):
        if not d.get('tempo_real') and not outro_av:
            A.append((3, 'Sem antivírus em tempo real', 'O Defender está sem proteção em tempo real e nenhum outro antivírus está ativo.',
                      'Abra Segurança do Windows > Proteção contra vírus e ameaças e ligue a proteção em tempo real.'))
        else:
            ok.append('antivírus em tempo real')
        idade = d.get('idade_definicoes')
        if isinstance(idade, int) and idade > 7 and d.get('tempo_real'):
            A.append((2, 'Definições do Defender velhas', f'As definições de vírus têm {idade} dias.', 'Rode "atualizar" e marque as definições do Defender.'))
        if d.get('tempo_real') and d.get('adulteracao') is False:
            A.append((1, 'Proteção contra adulteração desligada', 'Um programa mal-intencionado poderia desligar o Defender.',
                      'Segurança do Windows > Proteção contra vírus e ameaças > Configurações > Proteção contra Adulteração.'))
    elif outro_av:
        ok.append('antivírus de terceiros ativo')
    else:
        nao.append('Defender (sem permissão para ler)')
    fw = lista(f.get('firewall'))
    if fw:
        off = [x.get('nome') for x in fw if isinstance(x, dict) and not x.get('ligado')]
        if off:
            A.append((3 if 'Public' in off else 2, 'Firewall desligado', 'Perfis sem firewall: ' + ', '.join(off) + '.',
                      'Segurança do Windows > Firewall e proteção de rede: ligue cada perfil.'))
        else:
            ok.append('firewall nos três perfis')
    u = f.get('uac') or {}
    if u.get('ligado') == 0:
        A.append((3, 'Controle de Conta de Usuário (UAC) desligado', 'Qualquer programa pode ganhar privilégios de administrador sem aviso.',
                  'Painel de Controle > Contas de Usuário > Alterar configurações do Controle de Conta de Usuário.'))
    elif u.get('admin') == 0:
        A.append((2, 'UAC configurado para nunca avisar', 'O Windows não pergunta antes de dar privilégios de administrador.', 'Suba o controle do UAC um nível.'))
    elif u.get('ligado') == 1:
        ok.append('UAC ligado')
    bl = f.get('bitlocker')
    if bl is None:
        nao.append('BitLocker (edição ou permissão não deixam ler)')
    elif str(bl).lower() in ('on', '1'):
        ok.append('disco criptografado (BitLocker)')
    else:
        A.append((2 if pf(p, 'pc.notebook') else 1, 'Disco do sistema sem criptografia',
                  ('Notebook perdido ou roubado deixa todos os seus arquivos legíveis.' if pf(p, 'pc.notebook') else 'Quem tiver o disco em mãos lê os arquivos.'),
                  'Configurações > Privacidade e segurança > Criptografia do dispositivo (ou BitLocker, nas edições Pro).'))
    tpm = f.get('tpm')
    if tpm is not None and not (tpm or {}).get('pronto'):
        A.append((1, 'TPM ausente ou não pronto', 'Recursos como BitLocker e Windows Hello dependem dele.', 'Confira na BIOS se o TPM (fTPM ou PTT) está ligado.'))
    elif tpm is not None:
        ok.append('TPM pronto')
    if f.get('secureboot') is False:
        A.append((2, 'Inicialização segura (Secure Boot) desligada', 'Um software malicioso pode entrar antes do Windows.', 'Ligue o Secure Boot na BIOS/UEFI.'))
    elif f.get('secureboot'):
        ok.append('Secure Boot ligado')
    if f.get('smb1'):
        A.append((3, 'SMBv1 ligado', 'Protocolo antigo e inseguro, usado por vários ataques de rede.',
                  'Painel de Controle > Programas > Ativar ou desativar recursos do Windows > Suporte a Compartilhamento de Arquivos SMB 1.0: desmarque.'))
    elif f.get('smb1') is False:
        ok.append('SMBv1 desligado')
    rdp = f.get('rdp') or {}
    if rdp.get('ligado'):
        A.append((3 if rdp.get('nla') == 0 else 2, 'Área de Trabalho Remota ligada',
                  'Aceita conexões de fora' + ('. A autenticação em nível de rede está desligada, o que é pior.' if rdp.get('nla') == 0 else '.'),
                  'Se não usa, desligue em Configurações > Sistema > Área de Trabalho Remota (o pacote "serviços" também cuida disso).'))
    else:
        ok.append('Área de Trabalho Remota desligada')
    ss = lista(f.get('sem_senha'))
    if ss:
        A.append((3, 'Conta ativa sem senha', 'Contas: ' + ', '.join(str(x) for x in ss[:4]) + '.', 'Defina senha ou PIN em Configurações > Contas > Opções de entrada.'))
    if f.get('guest'):
        A.append((2, 'Conta Convidado ativa', 'Qualquer pessoa pode entrar como convidada.', 'Desative a conta Convidado em Gerenciamento do Computador > Usuários.'))
    if str(f.get('smartscreen') or '').lower() == 'off':
        A.append((2, 'SmartScreen desligado', 'O Windows não confere programas baixados desconhecidos.', 'Segurança do Windows > Controle de aplicativos e navegador > Proteção baseada em reputação.'))
    if f.get('lsa') not in (1, 2) and pf(p, 'so.win11'):
        A.append((1, 'Proteção da LSA desligada', 'Dificulta o roubo de senhas da memória.', 'Segurança do Windows > Segurança do dispositivo > Isolamento do núcleo.'))
    if pf(p, 'so.win11') and f.get('vbs') is not None and f.get('vbs') != 2:
        A.append((1, 'Segurança baseada em virtualização (VBS) desligada',
                  'O Windows 11 liga isso em PCs novos. Desligada, ganha-se desempenho em jogo e perde-se proteção do núcleo.',
                  'Segurança do Windows > Segurança do dispositivo > Isolamento do núcleo (o Katharos nunca mexe nisso).'))
    dias = f.get('dias_sem_atualizar')
    if isinstance(dias, int):
        if dias > 90:
            A.append((3, 'Windows sem atualização de segurança há muito tempo', f'A última correção instalada tem {dias} dias.', 'Rode "atualizar" e marque as atualizações do Windows.'))
        elif dias > 45:
            A.append((2, 'Windows atrasado nas atualizações', f'A última correção instalada tem {dias} dias.', 'Rode "atualizar" e marque as atualizações do Windows.'))
        else:
            ok.append(f'Windows atualizado (última correção há {dias} dias)')
    if str(f.get('wu') or '').lower() == 'disabled':
        A.append((3, 'Windows Update desativado', 'O serviço do Windows Update está desativado: você não recebe correções.', 'Rode "reparar" e marque "restaurar o Windows Update".'))
    if pf(p, 'sistema.reinicio_pendente'):
        A.append((1, 'Reinício pendente', 'Há atualizações esperando reinício para valerem.', 'Reinicie o PC.'))
    exp = [x for x in _dedup_portas(f.get('escuta')) if x['exposta']]
    sens = {}
    for x in exp:
        info = PORTAS_SENSIVEIS.get(x.get('porta'))
        if info:
            sens.setdefault((info[0], info[1]), []).append(x)
    for (nome, grav), xs in sens.items():
        A.append((grav, f'{nome} aceitando conexões da rede', f'Porta {xs[0]["porta"]} aberta por {xs[0].get("nome") or "um programa"}.',
                  'Veja em "portas" quem é e encerre se não for seu; confira o firewall.'))
    outras = [x for x in exp if x.get('porta') not in PORTAS_SENSIVEIS and x.get('porta', 0) >= 1024 and not str(x.get('caminho', '')).lower().startswith(('c:\\windows', 'c:\\program files\\windowsapps'))]
    if outras:
        A.append((1, f'{pl(len(outras), "programa aceita", "programas aceitam")} conexões de toda a rede',
                  ', '.join(sorted({f'{x.get("nome")}:{x.get("porta")}' for x in outras})[:6]) + '.', 'Veja "portas"; programas de desenvolvimento costumam abrir assim.'))
    return A, ok, nao


def nota_seguranca(A):
    return max(5, min(100, 100 - sum({3: 15, 2: 7, 1: 2}[g] for g, *_ in A)))


def ferramenta_seguranca(ctx, args):
    t = ctx.t
    t.aba('auditoria de segurança: só leitura, não muda nada')
    t.paragrafo('Confere antivírus, firewall, UAC, criptografia do disco, TPM, Secure Boot, protocolos antigos, conta sem senha, '
                'Área de Trabalho Remota, atualizações atrasadas e portas abertas para a rede. O Katharos nunca desliga nenhuma dessas '
                'proteções: aqui ele só mostra o que está fraco e onde corrigir.', 2, 'sub')
    if not WINDOWS:
        t.erro('O katharos só funciona no Windows.')
        return 1
    p = perfil_pc(ctx, forca=True)
    with Progresso(t, None, 'conferindo a segurança') as pr:
        s = roda_ps(t, SEGURANCA_PS, 'seguranca', minutos=5, mostra=False, pr=pr, mult=ctx.mult)
    f = s.dados.get('seg')
    if not isinstance(f, dict):
        t.erro('Não consegui ler os dados de segurança.' + (' ' + (dica_erro(' '.join(s.erros)) or '') if s.erros else ''))
        return 1
    if not eh_admin():
        t.nota('  sem administrador, alguns itens (BitLocker, TPM, contas) podem aparecer como "não deu para ler".')
    A, ok, nao = avalia_seguranca(f, p)
    nota = nota_seguranca(A)
    t.titulo('nota de segurança')
    cor = 'verde' if nota >= 80 else ('amarelo' if nota >= 55 else 'vermelho')
    t.barra('segurança', nota, 100, t.p(f'{nota}/100', cor, True), cor)
    if A:
        t.titulo('o que está fraco')
        for g, titulo, ev, corrige in sorted(A, key=lambda a: -a[0]):
            icone, c = {3: ('■', 'vermelho'), 2: ('●', 'amarelo'), 1: ('·', 'azul')}[g]
            t.item(icone, c, titulo)
            t.paragrafo(ev, 6, 'sub')
            t.paragrafo('como corrigir: ' + corrige, 6, 'apagado')
    if ok:
        t.titulo('o que está bem')
        t.paragrafo(' · '.join(ok), 2, 'verde')
    if nao:
        t.nota('  não deu para ler: ' + ', '.join(nao))
    rel_secao('seguranca', {'nota': nota, 'ok': ok, 'nao_leu': nao,
                            'achados': [{'gravidade': g, 'titulo': a, 'evidencia': b, 'corrige': c} for g, a, b, c in A]})
    rel_secao('portas', {'lista': [{k: x.get(k) for k in ('porta', 'nome', 'exposta', 'caminho')} for x in _dedup_portas(f.get('escuta'))][:60]})
    t.relatorio(rel_md_path(), 'relatório único', recuo=2)
    return 0


# ─────────────── portas abertas ───────────────

NUNCA_ENCERRAR = {'system', 'idle', 'registry', 'smss', 'csrss', 'wininit', 'winlogon', 'services', 'lsass', 'svchost', 'explorer', 'dwm',
                  'msmpeng', 'securityhealthservice', 'fontdrvhost', 'spoolsv', 'wudfhost', 'sihost', 'taskhostw', 'dllhost', 'conhost', 'python', 'pythonw'}


def ferramenta_portas(ctx, args):
    t = ctx.t
    t.aba('quem está escutando em cada porta, e para quem')
    t.paragrafo('"só este PC" quer dizer que só programas daqui falam com ele (servidor de desenvolvimento, banco local). '
                '"toda a rede" quer dizer que outros aparelhos da sua rede também conseguem chegar. Encerrar um programa é por sua conta '
                'e nunca vale para processos do sistema.', 2, 'sub')
    if not WINDOWS:
        t.erro('O katharos só funciona no Windows.')
        return 1
    with Progresso(t, None, 'lendo as portas') as pr:
        s = roda_ps(t, ESCUTA_PS + "\nDado 'escuta' (Lista $escuta)", 'portas', minutos=2, mostra=False, pr=pr)
    portas = _dedup_portas(s.dados.get('escuta'))
    filtro = getattr(args, 'filtro', None)
    if filtro:
        portas = [x for x in portas if str(x.get('porta')) == str(filtro)]
    if not portas:
        t.ok('Nenhuma porta encontrada.' if not filtro else f'Nada escutando na porta {filtro}.')
        return 0
    linhas = [[str(i), str(x.get('porta')), corta(str(x.get('nome') or '?'), 20), t.p('toda a rede', 'amarelo') if x['exposta'] else t.p('só este PC', 'apagado'),
               corta_esq(caminho_curto(str(x.get('caminho') or '')), 36)] for i, x in enumerate(portas, 1)]
    t.tabela(['#', 'porta', 'programa', 'aberta para', 'onde está'], linhas, alinha='dedee')
    rel_secao('portas', {'lista': [{k: x.get(k) for k in ('porta', 'nome', 'exposta', 'caminho')} for x in portas][:60]})
    if not t.interativo or args.sim or args.teste:
        return 0
    t.escreve()
    r = t.pergunta('encerrar qual (número; Enter = nenhum)').strip()
    if not r.isdigit() or not 0 < int(r) <= len(portas):
        return 0
    x = portas[int(r) - 1]
    nome = str(x.get('nome') or '').lower()
    cam = str(x.get('caminho') or '').lower()
    win = os.environ.get('WINDIR', r'C:\Windows').lower()
    if not x.get('pid') or x['pid'] <= 4 or nome in NUNCA_ENCERRAR or cam.startswith(win):
        t.aviso('Esse é um processo do sistema (ou do próprio Katharos): não encerro.')
        return 1
    if not t.confirma(f'Encerrar {x.get("nome")} (porta {x.get("porta")})? O que ele estiver fazendo é perdido.', sim=False):
        return 0
    corpo = (f"$p = Get-Process -Id {int(x['pid'])} -ErrorAction SilentlyContinue\n"
             f"if (-not $p -or $p.ProcessName -ne {psq(x.get('nome'))}) {{ Aviso 'o processo mudou; nao encerrei' }} "
             f"else {{ Stop-Process -Id {int(x['pid'])} -Force -ErrorAction SilentlyContinue; Feito 'processo encerrado' }}")
    roda_ps(t, corpo, 'encerrar', minutos=1)
    return 0


# ─────────────── segredos esquecidos em arquivos ───────────────

SEGREDOS = [
    ('Chave da Anthropic', r'sk-ant-[A-Za-z0-9_\-]{20,}', 3), ('Chave da OpenAI', r'\bsk-(?:proj-)?[A-Za-z0-9_\-]{32,}', 3),
    ('Token do GitHub', r'\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{50,})', 3),
    ('Chave de acesso da AWS', r'\b(?:AKIA|ASIA)[0-9A-Z]{16}\b', 3), ('Stripe (produção)', r'\b[rs]k_live_[0-9a-zA-Z]{20,}', 3),
    ('Chave de API do Google', r'\bAIza[0-9A-Za-z_\-]{35}\b', 2), ('Token do Slack', r'\bxox[abprs]-[0-9A-Za-z-]{10,}', 3),
    ('Token do Discord', r'\b[MN][A-Za-z\d]{23,25}\.[\w-]{6}\.[\w-]{27,}', 3),
    ('Chave privada', r'-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY', 3),
    ('Endereço de banco com senha', r'\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^\s:/@]+:[^\s@/]{3,}@[^\s/]+', 3),
    ('JWT', r'\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}', 2),
]
_SEG_RE = [(n, re.compile(r), g) for n, r, g in SEGREDOS]
_ENV_RE = re.compile(r'(?i)^\s*(?:export\s+)?[\w.-]*(?:secret|token|passw(?:or)?d|senha|api[_-]?key|private[_-]?key)[\w.-]*\s*[=:]\s*[\'"]?([^\s\'"#]{12,})')
PULAR_PASTAS = {'.git', 'node_modules', 'venv', '.venv', '__pycache__', 'dist', 'build', '.next', 'target', '.cache', 'site-packages', '.gradle', '.idea', 'vendor'}
EXEMPLO = re.compile(r'example|exemplo|sample|fixture|mock|test|spec|docs?[\\/]|readme|\.md$|changelog', re.I)


def mascara(v):
    v = str(v)
    return v[:4] + '…' + v[-2:] if len(v) > 10 else '…'


def varre_segredos(raizes, limite_s=90, max_arquivos=20000):
    achados, lidos, inicio = [], 0, time.time()
    for raiz in raizes:
        for atual, dirs, arqs in os.walk(raiz):
            dirs[:] = [d for d in dirs if d not in PULAR_PASTAS and not d.startswith('.venv')]
            for nome in arqs:
                if lidos >= max_arquivos or time.time() - inicio > limite_s:
                    return achados, lidos, True
                caminho = os.path.join(atual, nome)
                try:
                    if os.path.getsize(caminho) > 1_000_000 or os.path.islink(caminho):
                        continue
                    with open(caminho, 'rb') as fh:
                        bruto = fh.read()
                except OSError:
                    continue
                if b'\x00' in bruto[:2048]:
                    continue
                lidos += 1
                texto = bruto.decode('utf-8', 'ignore')
                eh_env = nome.lower().startswith('.env') or nome.lower().endswith('.env')
                for n_linha, linha in enumerate(texto.splitlines(), 1):
                    if len(linha) > 2000:
                        continue
                    for tipo, rx, grav in _SEG_RE:
                        m = rx.search(linha)
                        if m:
                            motivo = 'parece exemplo ou documentação' if EXEMPLO.search(caminho) else ''
                            achados.append({'tipo': tipo, 'arquivo': caminho, 'linha': n_linha, 'valor': mascara(m.group(0)),
                                            'gravidade': 1 if motivo else grav, 'motivo': motivo})
                            break
                    else:
                        if eh_env:
                            m = _ENV_RE.search(linha)
                            if m and not re.match(r'(?i)^(your|xxx|change|todo|<)', m.group(1)):
                                achados.append({'tipo': 'Variável secreta em .env', 'arquivo': caminho, 'linha': n_linha, 'valor': mascara(m.group(1)),
                                                'gravidade': 2, 'motivo': 'confira se o .env está no .gitignore'})
    return achados, lidos, False


def pastas_de_projeto(args):
    casa = Path.home()
    cand = [casa / 'Dev', casa / 'Projects', casa / 'Projetos', casa / 'source', casa / 'repos', casa / 'code', casa / 'Documents', casa / 'Documentos', casa / 'Desktop']
    extra = [Path(x).expanduser() for x in (getattr(args, 'pastas', None) or [])]
    return [p for p in (extra or cand) if p.is_dir()]


def ferramenta_segredos(ctx, args):
    t = ctx.t
    t.aba('chaves, tokens e senhas esquecidos em arquivos dos seus projetos (só leitura)')
    t.paragrafo('Lê arquivos de texto pequenos das suas pastas de projeto (pula node_modules, .git e afins) atrás de chaves da OpenAI, Anthropic, '
                'GitHub, AWS, Stripe, Google, Slack, Discord, chaves privadas, endereços de banco com senha e variáveis secretas em .env. '
                'O valor nunca é mostrado inteiro. Nada é alterado nem enviado para fora.', 2, 'sub')
    pastas = pastas_de_projeto(args)
    if not pastas:
        t.aviso('Não achei pastas de projeto. Diga onde procurar: katharos segredos C:\\caminho\\da\\pasta')
        return 1
    t.nota('  procurando em: ' + ', '.join(caminho_curto(p) for p in pastas[:5]))
    with Progresso(t, None, 'lendo arquivos') as pr:
        achados, lidos, parou = varre_segredos([str(p) for p in pastas])
    t.titulo('resultado')
    t.chaves([('arquivos lidos', str(lidos)), ('achados', t.p(str(len(achados)), 'vermelho' if achados else 'verde'))])
    if parou:
        t.nota('  parei no limite de tempo ou de arquivos; rode de novo numa pasta menor para ver o resto.')
    achados.sort(key=lambda a: -a['gravidade'])
    if achados:
        t.tabela(['gravidade', 'tipo', 'arquivo', 'linha', 'valor'],
                 [[IMPACTO[a['gravidade']], corta(a['tipo'], 22), corta_esq(caminho_curto(tela(a['arquivo'])), 34), str(a['linha']), a['valor']] for a in achados[:25]],
                 alinha='eeeed')
        if len(achados) > 25:
            t.nota(f'  e mais {len(achados) - 25} no relatório.')
        t.paragrafo('Se uma chave real aparece aqui: revogue e gere outra no site do serviço (apagar o arquivo não adianta se ela já foi para o git ou para a nuvem).', 2, 'amarelo')
    else:
        t.ok('Nenhum segredo à vista.')
    rel_secao('segredos', {'pastas': [str(p) for p in pastas], 'arquivos': lidos, 'achados': achados[:80]})
    return 0


# ─────────────── cartão de resultado ───────────────

def linhas_antes_depois(antes, depois):
    out = []
    for chave, rot, un, melhor in LINHAS_MEDIDA:
        a, b = antes.get(chave), depois.get(chave)
        if a is None and b is None:
            continue
        dif = ''
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and a != b:
            d = b - a
            dif = ('+' if d > 0 else '') + _fmt_medida(d, un)
        out.append([rot, _fmt_medida(a, un), _fmt_medida(b, un), dif])
    return out


def medida_ref(nome_parte):
    arqs = [a for a in medidas_salvas() if nome_parte in a.name]
    return le_json(arqs[0], {}) if arqs else {}


def livre_total_gb():
    """Soma do espaço que as limpezas registraram como liberado (bytes -> GB)."""
    tot = 0
    for e in rel_carrega().get('eventos', []):
        a, d = e.get('livre_antes'), e.get('livre_depois')
        if isinstance(a, (int, float)) and isinstance(d, (int, float)) and d > a:
            tot += d - a
    return round(tot / 1073741824, 1)


def ferramenta_cartao(ctx, args):
    t = ctx.t
    t.aba('o antes e depois deste PC, num cartão para mostrar')
    plano = le_json(ARQ_TURBO, None) or {}
    antes = plano.get('antes') or medida_ref('-antes') or medida_ref('-raiox') or (le_json(medidas_salvas()[0], {}) if medidas_salvas() else {})
    depois = plano.get('depois') or medida_ref('-depois')
    if not depois:
        if not WINDOWS:
            t.erro('Sem medidas salvas.')
            return 1
        depois = mede(ctx, 'medindo agora')
        salva_medida(depois, 'cartao')
    if not antes:
        t.aviso('Ainda não há uma medida de antes. Rode o raio-x ou o turbo antes de mexer em algo, e depois volte aqui.')
        return 0
    linhas = linhas_antes_depois(antes, depois)
    livre = livre_total_gb()
    t.titulo('antes e depois', caixa=True)
    t.tabela(['medida', 'antes', 'depois', 'mudou'], linhas, alinha='eddd')
    ativos = sorted(n for n, r in (estado().get('pacotes') or {}).items() if not r.get('revertido'))
    t.chaves([('espaço liberado nas limpezas', f'{br(livre, 1)} GB'), ('pacotes ativos', ', '.join(ativos) or 'nenhum'),
              ('desfazer', 'katharos desfazer tudo')])
    t.fecha_caixa()
    rel_secao('antes_depois', {'linhas': linhas, 'livre_gb': livre, 'pacotes': ativos})
    if getattr(args, 'copiar', False):
        return 0
    if t.interativo and not args.sim:
        t.paragrafo('c = copiar o cartão em texto · Enter = voltar', 2, 'apagado')
        if t.pergunta('fazer').strip().lower()[:1] == 'c':
            txt = 'Katharos · antes e depois\n' + '\n'.join(f'{a:<24} {b:>12} → {c:>12}  {d}' for a, b, c, d in linhas) + f'\nEspaço liberado: {br(livre, 1)} GB'
            t.ok('Cartão copiado.') if copia_area(txt) else t.aviso('Não consegui copiar.')
    return 0
