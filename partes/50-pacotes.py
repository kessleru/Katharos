

# ███████████████████████████████████████████████████████████████████████████
#
#   PARTE 3 · OS PACOTES
#   cada função devolve os itens que valem para este PC, com a recomendação ajustada ao que ele tem
#
# ███████████████████████████████████████████████████████████████████████████

def R(caminho, nome, valor, tipo='DWord'):
    """Uma linha de PowerShell que grava um valor no registro guardando o anterior."""
    if isinstance(valor, bytes):
        v = '([byte[]](' + ','.join(f'0x{b:02x}' for b in valor) + '))'
    elif isinstance(valor, str):
        v = psq(valor)
        if tipo == 'DWord':
            tipo = 'String'
    else:
        v = str(int(valor))
    return f'Set-Valor {psq(caminho)} {psq(nome)} {v} {psq(tipo)} | Out-Null'


def RR(*linhas):
    return '\n'.join(linhas)


def SVC(nomes, modo='disabled', parar=True):
    return f"foreach ($__s in {ps_lista(nomes)}) {{ Set-Servico $__s {psq(modo)}{' -Parar' if parar else ''} | Out-Null }}"


def TAREFAS(lista_tarefas):
    return f"foreach ($__t in {ps_lista(lista_tarefas)}) {{ Set-Tarefa $__t $false | Out-Null }}"


HKLM_POL = 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows'
HKCU_POL = 'HKCU:\\Software\\Policies\\Microsoft\\Windows'
CDM = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager'
ADV = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced'
EDGE_POL = 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Edge'


# ═══════════════════════════════ limpar ═══════════════════════════════

def _limpa_ps(rotulo, linhas):
    return ('$__livre = 0\n' + linhas +
            f'\nif ($__livre -gt 1MB) {{ if ($TESTE) {{ Plano ("{rotulo}: liberaria " + (MB $__livre)) }} '
            f'else {{ Feito ("{rotulo}: " + (MB $__livre) + " liberados") }} }}')


NAVEGADORES = [('Chrome', 'chrome', r'Google\Chrome\User Data'), ('Edge', 'msedge', r'Microsoft\Edge\User Data'),
               ('Brave', 'brave', r'BraveSoftware\Brave-Browser\User Data'), ('Opera', 'opera', r'..\Roaming\Opera Software\Opera Stable'),
               ('Vivaldi', 'vivaldi', r'Vivaldi\User Data')]


@pacote('limpar', 'limpeza', 'temporários, caches, restos de atualização e logs',
        'Apaga só o que o Windows e os programas recriam sozinhos. Arquivos seus não são tocados (para eles, use '
        '"grandes", que manda para a Lixeira). Arquivos em uso ficam onde estão.', reversivel=False)
def itens_limpar(ctx):
    nav = []
    for nome, proc, rel in NAVEGADORES:
        base = f'(Join-Path $env:LOCALAPPDATA {psq(rel)})'
        nav.append(f'''if (Get-Process {proc} -ErrorAction SilentlyContinue) {{ Info '{nome} aberto: cache dele fica para a proxima' }}
else {{ foreach ($__pf in @(Get-ChildItem -LiteralPath {base} -Directory -ErrorAction SilentlyContinue | Where-Object {{ $_.Name -match '^(Default|Profile \\d+)$' -or $_.Name -eq 'Opera Stable' }})) {{
  foreach ($__c in 'Cache','Code Cache','GPUCache','Service Worker\\CacheStorage') {{ $__livre += LimpaAntigos (Join-Path $__pf.FullName $__c) 0 }} }}
  if ('{nome}' -eq 'Opera') {{ $__livre += LimpaAntigos (Join-Path $env:LOCALAPPDATA 'Opera Software\\Opera Stable\\Cache') 0 }} }}''')
    nav.append('''if (Get-Process firefox -ErrorAction SilentlyContinue) { Info 'Firefox aberto: cache dele fica para a proxima' }
else { foreach ($__pf in @(Get-ChildItem (Join-Path $env:LOCALAPPDATA 'Mozilla\\Firefox\\Profiles') -Directory -ErrorAction SilentlyContinue)) { $__livre += LimpaAntigos (Join-Path $__pf.FullName 'cache2') 0 } }''')
    dev = '''foreach ($__c in @(@('npm','cache clean --force'), @('pip','cache purge'), @('yarn','cache clean'), @('pnpm','store prune'))) {
  $__e = Get-Command $__c[0] -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($__e) { if ($TESTE) { Plano ($__c[0] + ' ' + $__c[1]) } else { Vivo ($__c[0] + ' ' + $__c[1]); $__r = Roda 'cmd.exe' ('/c ' + $__c[0] + ' ' + $__c[1]) 10; if ($__r -eq 0) { Feito ($__c[0] + ': cache limpo') } } }
}'''
    sagerun = r'''
$__vc = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches'
$__fora = '^(DownloadsFolder|Recycle Bin|Previous Installations|BranchCache|Language Pack)$'
if ($TESTE) { Plano 'Limpeza de Disco do Windows (categorias do sistema, sem Downloads e Lixeira)' }
else {
  foreach ($__k in @(Get-ChildItem $__vc -ErrorAction SilentlyContinue)) {
    if ($__k.PSChildName -match __SO__) { New-ItemProperty -LiteralPath $__k.PSPath -Name StateFlags0911 -Value 2 -PropertyType DWord -Force -ErrorAction SilentlyContinue | Out-Null }
    else { Remove-ItemProperty -LiteralPath $__k.PSPath -Name StateFlags0911 -ErrorAction SilentlyContinue }
  }
  $__d0 = (Get-PSDrive C).Free
  Vivo 'Limpeza de Disco do Windows (pode demorar)'
  $__r = Roda 'cleanmgr.exe' '/sagerun:911' __MIN__
  $__d = (Get-PSDrive C).Free - $__d0
  if ($__r -eq -1) { Aviso 'a Limpeza de Disco passou do tempo e foi encerrada' }
  elseif ($__d -gt 1MB) { Feito ('Limpeza de Disco: ' + (MB $__d) + ' liberados') } else { Diz 'nada' 'nada a limpar' }
}'''
    return [
        Item('temp', 'temporários', 'Arquivos temporários seus e do Windows com mais de 2 dias (os recentes podem estar em uso).',
             'espaço; às vezes centenas de MB', 'nenhum', 1,
             _limpa_ps('temporarios', '$__livre += LimpaAntigos $env:TEMP 2\n$__livre += LimpaAntigos "$env:WINDIR\\Temp" 2')),
        Item('wu', 'downloads do Windows Update', 'Instaladores de atualizações já aplicadas. Não mexe se houver atualização '
             'esperando reinício.', 'espaço (pode passar de 1 GB)', 'nenhum', 1, _limpa_ps('Windows Update', r'''
$__pend = (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending') -or (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired')
if ($__pend) { Info 'ha atualizacao esperando reinicio: downloads mantidos' }
else {
  if (-not $TESTE) { & sc.exe stop wuauserv 2>$null | Out-Null; & sc.exe stop bits 2>$null | Out-Null; Start-Sleep 3 }
  $__livre += LimpaAntigos "$env:WINDIR\SoftwareDistribution\Download" 0
  if (-not $TESTE) { & sc.exe start wuauserv 2>$null | Out-Null; & sc.exe start bits 2>$null | Out-Null }
}'''), minutos=6),
        Item('do', 'cache da Otimização de Entrega', 'Pedaços de atualizações que o Windows guarda para mandar a outros PCs.',
             'espaço', 'nenhum', 1, r'''if ($TESTE) { Plano 'limpar cache da Otimizacao de Entrega' } else { try { Delete-DeliveryOptimizationCache -Force -ErrorAction Stop; Feito 'cache da Otimizacao de Entrega limpo' } catch { Diz 'nada' 'sem cache' } }'''),
        Item('erros', 'relatórios de erro e dumps', 'Relatórios de travamento já enviados ou antigos e cópias de memória de telas azuis.',
             'espaço (dumps podem ter GBs)', 'quem investiga uma tela azul antiga perde o arquivo', 1,
             _limpa_ps('relatorios de erro', r'''foreach ($__p in "$env:ProgramData\Microsoft\Windows\WER\ReportArchive","$env:ProgramData\Microsoft\Windows\WER\ReportQueue","$env:LOCALAPPDATA\Microsoft\Windows\WER","$env:LOCALAPPDATA\CrashDumps","$env:WINDIR\Minidump") { $__livre += LimpaAntigos $__p 7 }
if (Test-Path "$env:WINDIR\MEMORY.DMP") { $__l = (Get-Item "$env:WINDIR\MEMORY.DMP").Length; if (-not $TESTE) { Remove-Item "$env:WINDIR\MEMORY.DMP" -Force -ErrorAction SilentlyContinue }; $__livre += $__l }''')),
        Item('miniaturas', 'cache de miniaturas', 'O Windows recria as miniaturas das fotos e vídeos quando você abre as pastas.',
             'espaço; conserta miniaturas erradas', 'pastas de fotos demoram um pouco na primeira abertura', 1,
             _limpa_ps('miniaturas', r'''foreach ($__f in @(Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Windows\Explorer" -Filter 'thumbcache_*.db' -Force -ErrorAction SilentlyContinue)) { $__l = $__f.Length; if (-not $TESTE) { Remove-Item -LiteralPath $__f.FullName -Force -ErrorAction SilentlyContinue; if (-not (Test-Path -LiteralPath $__f.FullName)) { $__livre += $__l } } else { $__livre += $__l } }''')),
        Item('logs', 'logs antigos do Windows', 'Registros de instalação e manutenção com mais de 30 dias (CBS, DISM, Panther, '
             'MoSetup). O prompt original achou logs gigantes aqui.', 'espaço', 'nenhum no uso normal', 2,
             _limpa_ps('logs', r'''foreach ($__p in "$env:WINDIR\Logs\CBS","$env:WINDIR\Logs\DISM","$env:WINDIR\Logs\MoSetup","$env:WINDIR\Panther","$env:WINDIR\Logs\WindowsUpdate","$env:WINDIR\Logs\SIH") { $__livre += LimpaAntigos $__p 30 }''')),
        Item('navegadores', 'cache dos navegadores', 'Chrome, Edge, Brave, Opera, Vivaldi e Firefox, só os que estiverem fechados. '
             'Histórico, senhas, cookies e abas não são tocados.', 'espaço (às vezes vários GB)',
             'os sites carregam um pouco mais devagar na primeira visita', 2, _limpa_ps('navegadores', '\n'.join(nav)), minutos=6),
        Item('shaders', 'cache de shaders da placa de vídeo', 'DirectX, NVIDIA, AMD e Intel guardam shaders compilados. '
             'Só apaga o que não foi usado há mais de 30 dias (jogos que você parou de abrir); o que está em uso fica, para não recompilar tudo e engasgar.', 'espaço de jogos que você não abre mais',
             'um jogo antigo recompila na primeira vez que abrir', 2,
             _limpa_ps('shaders', r'''foreach ($__p in "$env:LOCALAPPDATA\D3DSCache","$env:LOCALAPPDATA\NVIDIA\DXCache","$env:LOCALAPPDATA\NVIDIA\GLCache","$env:LOCALAPPDATA\AMD\DxCache","$env:LOCALAPPDATA\AMD\DxcCache","$env:LOCALAPPDATA\AMD\GLCache","$env:LOCALAPPDATA\AMD\VkCache","$env:LOCALAPPDATA\Intel\ShaderCache","$env:ProgramData\NVIDIA Corporation\NV_Cache") { $__livre += LimpaAntigos $__p 30 }''')),
        Item('instaladores', 'instaladores guardados por programas', 'Cópias de instaladores antigos que alguns programas guardam '
             '(Downloaded Installations, mais de 30 dias). O Alienware Command Center guarda ~1 GB por versão aqui.',
             'espaço', 'reparar esses programas pode pedir o instalador de novo', 2,
             _limpa_ps('instaladores', r'''$__livre += LimpaAntigos "$env:LOCALAPPDATA\Downloaded Installations" 30''')),
        Item('dev', 'caches de desenvolvimento', 'npm, pip, yarn e pnpm, pelos próprios comandos (só os que existem).',
             'espaço', 'a próxima instalação de pacotes baixa de novo', 2, dev, minutos=12) if any(shutil.which(x) for x in ('npm', 'pip', 'yarn', 'pnpm')) or not WINDOWS else None,
        Item('cleanmgr', 'Limpeza de Disco do Windows', 'A própria ferramenta do Windows, sem tocar em Downloads nem na Lixeira: '
             'restos de atualizações substituídas, arquivos de instalação, logs de upgrade.',
             'espaço (costuma liberar GBs depois de grandes atualizações)', 'demora (até 30 min em HD)', 2,
             sagerun.replace('__SO__', "'.'").replace('__MIN__', '30').replace("-match '.'", "-notmatch $__fora"), minutos=32, sozinho=True),
        Item('windowsold', 'Windows.old (versão anterior do Windows)', 'A cópia do Windows de antes da última grande atualização. '
             'Sai pela Limpeza de Disco, do jeito oficial.', 'espaço (10 a 30 GB)', 'não dá mais para voltar à versão anterior', 2,
             sagerun.replace('__SO__', "'^Previous Installations$'").replace('__MIN__', '30'), minutos=32, sozinho=True)
        if (not WINDOWS or Path(os.environ.get('SystemDrive', 'C:') + '\\Windows.old').exists()) else None,
        Item('componentes', 'componentes antigos do Windows (DISM)', 'Remove versões substituídas de componentes do sistema, '
             'do jeito oficial (DISM /StartComponentCleanup).', 'espaço (centenas de MB a alguns GB)', 'demora', 2,
             py=_py_dism(['/Online', '/Cleanup-Image', '/StartComponentCleanup'], 'componentes', 40)),
        Item('resetbase', 'componentes, de forma definitiva', 'O mesmo, com /ResetBase: apaga também as versões antigas que '
             'permitiriam desinstalar atualizações.', 'mais espaço', 'não dá mais para desinstalar atualizações já instaladas', 3,
             py=_py_dism(['/Online', '/Cleanup-Image', '/StartComponentCleanup', '/ResetBase'], 'componentes definitivo', 60), reverte=False),
        Item('reservado', 'armazenamento reservado do Windows', 'O Windows separa ~7 GB para atualizações. Desligar devolve esse espaço.',
             'cerca de 7 GB', 'com o disco cheio, atualizações grandes podem falhar', 3, r'''
$__st = Tenta { [string](Get-WindowsReservedStorageState -ErrorAction Stop).ReservedStorageState } ''
if ($__st -match 'Enabled') { if ($TESTE) { Plano 'desligar armazenamento reservado' } else { Guarda-Desfazer 'reservado' 'Set-WindowsReservedStorageState -State Enabled'; Set-WindowsReservedStorageState -State Disabled -ErrorAction Stop; $script:MUDOU++ } }''',
             minutos=5),
        Item('lixeira', 'esvaziar a Lixeira', 'Apaga de vez o que está na Lixeira de todas as unidades.', 'espaço',
             'é definitivo: não dá para recuperar', 0,
             _limpa_ps('Lixeira', r'''$__sh = New-Object -ComObject Shell.Application; $__n = @($__sh.NameSpace(10).Items()).Count
if ($__n -gt 0) { $__d0 = (Get-PSDrive C).Free; if (-not $TESTE) { Clear-RecycleBin -Force -ErrorAction SilentlyContinue; $__livre += [math]::Max(0, (Get-PSDrive C).Free - $__d0) } else { Plano ("esvaziar {0} itens da Lixeira" -f $__n) } }'''), reverte=False),
    ]


def _py_dism(argumentos, rotulo, minutos):
    def f(ctx, it, pr, teste):
        if teste:
            ctx.t.item('○', 'azul', 'DISM ' + ' '.join(argumentos), recuo=4, cor_nome='sub')
            return 1, 0
        if not exige_espaco(ctx.t, 'dism', rotulo):
            return 0, 1
        antes = livre_c()
        cod, txt = roda_exe(['DISM.exe'] + argumentos, minutos, pr, ctx.mult)
        liberou = livre_c() - antes
        if cod == -1:
            ctx.t.aviso(f'{rotulo}: passou do tempo e foi encerrado.')
            return 0, 1
        if cod not in (0, 3010):
            ctx.t.aviso(f'{rotulo}: DISM saiu com código {cod}.')
            return 0, 1
        ctx.t.item('✓', 'verde', f'{rotulo}: concluído' + (f', {humano(liberou)} liberados' if liberou > 2**20 else ''), recuo=4, cor_nome='sub')
        return 1, 0
    return f


def livre_c():
    try:
        return shutil.disk_usage((os.environ.get('SystemDrive', 'C:') + '\\') if WINDOWS else '/').free
    except OSError:
        return 0


# ═══════════════════════════════ programas de fábrica ═══════════════════════════════

# (padrão do nome, nível, explicação, custo)
CATALOGO_PROGRAMAS = [
    (r'^McAfee', 1, 'Antivírus que vem de fábrica em teste. Briga com o Defender pelo disco e pela CPU.', 'se você pagou a assinatura, perde'),
    (r'^Norton (Security|360|AntiVirus|Internet Security|Online Backup|Utilities)', 2, 'Antivírus de fábrica ou em teste. Pesa mais que o Defender.', 'se você pagou a assinatura, perde'),
    (r'^(Avast|AVG) (Free )?Antivirus|^Avira (Security|Antivirus)', 3, 'Antivírus gratuito pesado; o Defender assume a proteção.', 'você perde esse antivírus'),
    (r'WildTangent|Booking\.com|Amazon Assistant|Dropbox (Promotion|20 GB)|ExpressVPN.*Trial', 1, 'Propaganda instalada de fábrica.', 'nenhum'),
    (r'^CyberLink (PowerDVD|Power2Go|PowerDirector|PhotoDirector|YouCam|Media Suite|LabelPrint|PowerRecover|Power Media Player|RichVideo)', 2,
     'Programas de mídia de fábrica (DVD, edição). O Windows já toca vídeo e música.', 'perde esses programas'),
    (r'^NewBlue|^proDAD', 2, 'Plugins de vídeo de fábrica.', 'perde os plugins'),
    (r'^Dell (SupportAssist|Customer Connect|Data Vault|Digital Delivery|Foundation Services|Product Registration|Help & Support|TechHub|Optimizer|Mobile Connect)|^Ajuda e Suporte da Dell|^Registro de produto Dell|DSC/AA Factory|^My ?Dell',
     2, 'Assistentes, telemetria e propaganda da Dell. O SupportAssist com o TechHub chega a 0,6 GB de RAM e consulta o WMI sem parar. '
        'O Dell Update fica, para drivers e BIOS.', 'perde o diagnóstico da Dell'),
    (r'^HP (JumpStart|Documentation|Connection Optimizer|Welcome|Insights|Privacy Settings|QuickDrop|Audio Switch|Sure Sense|Security Update Service)', 2,
     'Utilitários e telemetria da HP.', 'perde esses utilitários'),
    (r'^HP (Support Assistant|Wolf Security)', 3, 'Assistente de suporte e proteção extra da HP. O Defender continua protegendo.', 'perde o assistente e a proteção extra da HP'),
    (r'^Lenovo (Welcome|Now|Migration Assistant|Smart Meeting)', 2, 'Boas-vindas e propaganda da Lenovo. O Vantage (bateria e drivers) fica.', 'nenhum'),
    (r'^Acer (Jumpstart|Collection|Portal|Product Registration|Registration|Configuration Manager)|^App Explorer', 2, 'Propaganda e registro da Acer.', 'nenhum'),
    (r'^Acer Care Center', 3, 'Central de manutenção da Acer.', 'perde a central da Acer'),
    (r'^ASUS GiftBox|^ASUS Welcome', 2, 'Propaganda da ASUS.', 'nenhum'),
    (r'^Microsoft OneDrive$', 2, 'Sincronização do OneDrive. Desinstala pelo desinstalador oficial dele.', 'arquivos só na nuvem deixam de aparecer no PC (baixe antes o que precisar)'),
    (r'Teams Machine-Wide Installer|^Microsoft Teams \(classic\)', 2, 'Instalador antigo do Teams, que reinstala o Teams a cada login.', 'quem usa o Teams clássico perde'),
    (r'^Microsoft 365 - [a-z]{2}-[a-z]{2}$|^Microsoft OneNote - [a-z]{2}-[a-z]{2}$', 0, 'Office que vem de fábrica, normalmente em teste.', 'você perde o Office (se tiver licença, reinstala pela conta)'),
]


LISTA_PROGRAMAS_PS = r'''
$__ks = 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'
$__r = @(Get-ItemProperty $__ks -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -and ($_.UninstallString -or $_.QuietUninstallString) -and -not $_.SystemComponent } | ForEach-Object {
  [pscustomobject]@{ nome = [string]$_.DisplayName; chave = [string]$_.PSPath; desinst = [string]$_.UninstallString; quieto = [string]$_.QuietUninstallString; mb = [math]::Round([double]$_.EstimatedSize / 1024) }
})
Dado 'programas' (Lista $__r)
'''

REMOVE_PROGRAMA_PS = r'''
$__nome = «nome»; $__chave = «chave»; $__cmd = «desinst»; $__quieto = «quieto»
function _Sumiu([int]$Seg) { for ($i = 0; $i -lt [math]::Max(1, $Seg / 5); $i++) { if (-not (Test-Path -LiteralPath $__chave)) { return $true }; Start-Sleep 5 }; return -not (Test-Path -LiteralPath $__chave) }
if ($TESTE) { Plano ('desinstalar ' + $__nome); return }
Vivo ('desinstalando ' + $__nome)
$exe = $null; $normal = ''; $silencioso = ''
if ($__cmd -match '(?i)msiexec.*(\{[0-9A-F-]{36}\})') { $exe = 'msiexec.exe'; $normal = "/x $($Matches[1]) /norestart"; $silencioso = "/x $($Matches[1]) /qn /norestart" }
else {
  if ($__cmd -match '^"([^"]+)"\s*(.*)$' -or $__cmd -match '(?i)^(.+?\.exe)\s*(.*)$') { $exe = $Matches[1]; $normal = $Matches[2] }
  if ($__quieto -and ($__quieto -match '^"([^"]+)"\s*(.*)$' -or $__quieto -match '(?i)^(.+?\.exe)\s*(.*)$')) { $silencioso = $Matches[2]; $exe = $Matches[1] }
  elseif ($exe -match 'unins\d*\.exe$') { $silencioso = "$normal /VERYSILENT /SUPPRESSMSGBOXES /NORESTART" }
  elseif ($exe) { $silencioso = "$normal /S" }
}
if (-not $exe) { Aviso ("'{0}': desinstalador nao reconhecido; remova em Configuracoes > Aplicativos" -f $__nome); return }
if ($exe -ne 'msiexec.exe' -and -not (Test-Path -LiteralPath $exe)) { Aviso ("'{0}': o desinstalador nao existe mais (entrada orfa)" -f $__nome); return }
$c = Roda $exe $silencioso 6
if (_Sumiu 45) { Feito ("removido: {0}" -f $__nome); return }
Info ("'{0}' nao saiu em silencio (codigo {1}). Abri o desinstalador: clique nele e confirme (ate 10 min)." -f $__nome, $c)
$c = Roda $exe $normal 10 -Visivel
if (_Sumiu 30) { Feito ("removido: {0}" -f $__nome) } else { Aviso ("'{0}' continua instalado (codigo {1}). Erro 1628 = desinstalador quebrado: pode deixar." -f $__nome, $c) }
'''


def _py_remove_programa(ctx, it, pr, teste):
    d = it.dados
    corpo = ps_monta(REMOVE_PROGRAMA_PS, nome=psq(d['nome']), chave=psq(d['chave']), desinst=psq(d['desinst']), quieto=psq(d.get('quieto') or ''))
    s = roda_ps(ctx.t, corpo, 'programa', minutos=18, teste=teste, pr=pr, mult=1.0)
    return len(s.feitos) + len(s.planos), len(s.avisos)


@pacote('programas', 'programas de fábrica', 'bloatware do fabricante, antivírus de teste e propaganda',
        'Procura programas de fábrica conhecidos (Dell, HP, Lenovo, Acer, ASUS, McAfee, Norton, CyberLink...) e tenta desinstalar '
        'em silêncio. Se o programa não sair, abre o desinstalador dele para você clicar. Drivers de áudio, vídeo, Wi-Fi, '
        'touchpad e Bluetooth nunca entram na lista.', reversivel=False)
def itens_programas(ctx):
    s = roda_ps(ctx.t, LISTA_PROGRAMAS_PS, 'lista-programas', minutos=2, mostra=False)
    itens, vistos = [], set()
    for prog in lista(s.dados.get('programas')):
        nome = prog.get('nome', '')
        for padrao, nivel, explica, custo in CATALOGO_PROGRAMAS:
            if re.search(padrao, nome, re.I) and nome not in vistos:
                vistos.add(nome)
                n = nivel
                nota = ''
                if nome == 'Microsoft OneDrive' and pf(ctx.perfil, 'tem.onedrive_usado'):
                    n, nota = 0, 'sua pasta do OneDrive tem arquivos: não vem marcado'
                if re.search(r'antivirus|security|norton|mcafee|avast|avg|avira', nome, re.I):
                    av = [a for a in lista(pf(ctx.perfil, 'antivirus', [])) if a.get('ativo')]
                    if len(av) <= 1 and n == 1:
                        nota = 'é o único antivírus ativo além do Defender; o Defender assume quando ele sair'
                tam = f' · {br(prog["mb"], 0)} MB' if prog.get('mb') else ''
                itens.append(Item('prog:' + nome, nome, explica, 'menos programas rodando e menos espaço' + tam, custo, n,
                                  py=_py_remove_programa, nota=nota, reverte=False, dados=prog))
                break
    return itens


# ═══════════════════════════════ apps da Loja ═══════════════════════════════

# (padrão, nível, título, explicação, custo). Loja, Instalador de Aplicativos, Fotos, Calculadora, Bloco de Notas,
# Paint, Captura, Terminal, frameworks e apps de driver nunca entram.
CATALOGO_APPS = [
    (r'^Microsoft\.BingNews$', 1, 'Notícias', 'App de notícias do Bing.', 'nenhum'),
    (r'^Microsoft\.BingWeather$', 1, 'Clima', 'App de clima (o clima continua no navegador).', 'nenhum'),
    (r'^Microsoft\.BingSearch$', 1, 'Pesquisa Bing', 'Integração do Bing ao Windows.', 'nenhum'),
    (r'^Microsoft\.GetHelp$', 1, 'Obter Ajuda', 'App de ajuda da Microsoft.', 'nenhum'),
    (r'^Microsoft\.Getstarted$', 1, 'Dicas', 'Dicas do Windows.', 'nenhum'),
    (r'^Microsoft\.MicrosoftSolitaireCollection$', 1, 'Solitaire', 'Jogo com propaganda.', 'perde o jogo'),
    (r'^Microsoft\.Microsoft3DViewer$|^Microsoft\.Print3D$|^Microsoft\.MSPaint$|^Microsoft\.MixedReality\.Portal$', 1, 'apps 3D e realidade mista', 'Visualizador 3D, Paint 3D e Portal de Realidade Mista.', 'perde esses apps'),
    (r'^Microsoft\.WindowsFeedbackHub$', 1, 'Hub de Comentários', 'Envio de opinião à Microsoft.', 'nenhum'),
    (r'^Microsoft\.549981C3F5F10$', 1, 'Cortana', 'Assistente descontinuado.', 'nenhum'),
    (r'^Microsoft\.(Messaging|OneConnect|SkypeApp|Wallet|People)$', 1, 'apps antigos (Skype, Pessoas, Carteira)', 'Apps sem uso no Windows atual.', 'perde esses apps'),
    (r'^Clipchamp\.Clipchamp$', 1, 'Clipchamp', 'Editor de vídeo online pré-instalado.', 'perde o editor'),
    (r'Disney|SpotifyAB\.SpotifyMusic|king\.com\.|TikTok|Facebook|Instagram|AmazonVideo\.PrimeVideo|Netflix|Hulu|Twitter|LinkedIn|CandyCrush|BubbleWitch|MarchofEmpires|HiddenCity|Duolingo|PicsArt|Royal Revolt|Asphalt|Sling', 1,
     'apps de propaganda', 'Atalhos de propaganda e jogos que o Windows instala sozinho.', 'se você usa algum deles, reinstale pela Loja'),
    (r'^Microsoft\.MicrosoftOfficeHub$', 1, 'Microsoft 365 (Copilot)', 'Atalho do Office e do Copilot do Microsoft 365.', 'nenhum (o Office instalado continua)'),
    (r'^DellInc\.|^DB6EA5DB\.|^AD2F1837\.(HPJumpStarts|HPPrivacySettings|HPSupportAssistant|HPSystemInformation|HPQuickDrop|HPWorkWell|myHP|HPInc\.EnergyStar)|^AcerIncorporated\.(?!QuickAccess)|^B9ECED6F\.ASUSGIFTBOX', 2,
     'apps do fabricante', 'Apps de suporte, registro e propaganda do fabricante.', 'perde esses apps'),
    (r'^Microsoft\.WindowsMaps$', 2, 'Mapas', 'App de mapas offline.', 'perde os mapas offline'),
    (r'^microsoft\.windowscommunicationsapps$', 2, 'Email e Calendário (antigo)', 'Descontinuado pela Microsoft.', 'quem ainda usa perde'),
    (r'^Microsoft\.OutlookForWindows$', 2, 'Outlook (novo)', 'Novo Outlook gratuito.', 'quem usa perde (dá para usar no navegador)'),
    (r'^Microsoft\.Todos$|^Microsoft\.PowerAutomateDesktop$|^Microsoft\.Windows\.DevHome$|^MicrosoftCorporationII\.MicrosoftFamily$|^Microsoft\.MicrosoftJournal$|^Microsoft\.Whiteboard$|^Microsoft\.Office\.OneNote$', 2,
     'apps de produtividade pré-instalados', 'To Do, Power Automate, Dev Home, Family, Journal, Whiteboard e OneNote da Loja.', 'quem usa algum perde'),
    (r'^Microsoft\.WindowsAlarms$', 2, 'Relógio', 'Alarmes, timer e cronômetro.', 'perde alarme e timer do Windows'),
    (r'^Microsoft\.YourPhone$', 2, 'Vincular ao Celular', 'Liga o celular ao PC. Fica rodando em segundo plano.', 'perde mensagens e fotos do celular no PC'),
    (r'^MicrosoftTeams$|^MSTeams$', 2, 'Teams', 'Teams pessoal. Abre com o Windows.', 'quem usa perde (reinstala quando quiser)'),
    (r'^MicrosoftWindows\.Client\.WebExperience$', 2, 'Widgets', 'O painel de notícias e clima do Windows 11.', 'perde o painel de widgets'),
    (r'^Microsoft\.ZuneVideo$', 2, 'Filmes e TV', 'Player antigo de vídeo.', 'perde o app (o Media Player continua)'),
    (r'^Microsoft\.Edge\.GameAssist$', 2, 'Game Assist do Edge', 'Navegador por cima dos jogos.', 'nenhum'),
    (r'^Microsoft\.(GamingApp|XboxApp|Xbox\.TCUI|XboxGameOverlay|XboxGamingOverlay|XboxIdentityProvider|XboxSpeechToTextOverlay)$', 2,
     'Xbox', 'App Xbox, Game Bar e login do Xbox.', 'perde Game Pass, Game Bar (Win+G) e login Xbox em jogos'),
    (r'^Microsoft\.MicrosoftStickyNotes$', 3, 'Notas Autoadesivas', 'Notas na área de trabalho.', 'perde as notas (salve antes)'),
    (r'^Microsoft\.ZuneMusic$', 3, 'Media Player', 'O player de música e vídeo padrão do Windows 11.', 'você precisa de outro player (ex.: VLC)'),
    (r'^Microsoft\.WindowsSoundRecorder$', 3, 'Gravador de Som', 'Gravador de áudio.', 'perde o gravador'),
    (r'^MicrosoftCorporationII\.QuickAssist$', 3, 'Assistência Rápida', 'Acesso remoto para suporte.', 'ninguém consegue te ajudar por ele'),
    (r'^Microsoft\.WindowsCamera$', 0, 'Câmera', 'App de câmera. A webcam continua funcionando nos sites e no Teams.', 'perde o app de fotos pela webcam'),
]

LISTA_APPS_PS = r'''
$__a = @(Tenta { Get-AppxPackage -AllUsers -ErrorAction Stop } @(Get-AppxPackage))
$__p = @(Tenta { Get-AppxProvisionedPackage -Online -ErrorAction Stop } @())
$__n = @{}
foreach ($x in $__a) { if (-not $x.NonRemovable -and $x.SignatureKind -ne 'System' -and -not $x.IsFramework) { $__n[[string]$x.Name] = 1 } }
foreach ($x in $__p) { $__n[[string]$x.DisplayName] = 1 }
Dado 'apps' (Lista ([string[]]$__n.Keys))
'''

REMOVE_APP_PS = r'''
$__n = «nome»
if ($TESTE) { Plano ('remover app ' + $__n); return }
Vivo ('removendo ' + $__n)
$__pk = @(Get-AppxPackage -AllUsers -Name $__n -ErrorAction SilentlyContinue | Where-Object { -not $_.NonRemovable })
foreach ($x in $__pk) { try { Remove-AppxPackage -Package $x.PackageFullName -AllUsers -ErrorAction Stop } catch { try { Remove-AppxPackage -Package $x.PackageFullName -ErrorAction Stop } catch { Aviso ($__n + ': ' + $_.Exception.Message) } } }
foreach ($x in @(Get-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue | Where-Object DisplayName -eq $__n)) { try { Remove-AppxProvisionedPackage -Online -PackageName $x.PackageName -ErrorAction Stop | Out-Null } catch {} }
if (Get-AppxPackage -Name $__n -ErrorAction SilentlyContinue) { Aviso ('continua instalado: ' + $__n) } else { Feito ('removido: ' + $__n) }
'''


def _py_remove_apps(ctx, it, pr, teste):
    feitos = avisos = travou = 0
    for nome in it.dados:
        if travou >= 3:
            ctx.t.aviso('3 remoções travaram seguidas; parei. Reinicie e rode de novo para o resto.')
            break
        s = roda_ps(ctx.t, ps_monta(REMOVE_APP_PS, nome=psq(nome)), 'app', minutos=3, teste=teste, pr=pr, mult=1.0)
        travou = travou + 1 if s.estourou else 0
        if s.estourou:
            ctx.t.aviso(f'{nome}: travou e foi encerrado (acontece com o Remove-AppxPackage).')
        feitos += len(s.feitos) + len(s.planos)
        avisos += len(s.avisos) + (1 if s.estourou else 0)
    return feitos, avisos


@pacote('apps', 'apps da Loja', 'apps pré-instalados que quase ninguém usa',
        'Remove para todos os usuários e também da instalação padrão (contas novas não recebem de novo). '
        'Apps de sistema e protegidos pelo Windows nunca entram. Cada remoção tem limite de 3 minutos, porque às vezes ela trava.',
        reversivel=False)
def itens_apps(ctx):
    s = roda_ps(ctx.t, LISTA_APPS_PS, 'lista-apps', minutos=3, mostra=False)
    instalados = lista(s.dados.get('apps'))
    itens = []
    for padrao, nivel, titulo, explica, custo in CATALOGO_APPS:
        achados = sorted(n for n in instalados if re.search(padrao, n, re.I))
        if not achados:
            continue
        nota = ''
        if titulo == 'Xbox' and joga(ctx.perfil):
            nivel, nota = 0, 'tem jogos instalados (' + ', '.join(lista(ctx.perfil.get('jogos'))) + '): não vem marcado'
        if titulo == 'Câmera' and not pf(ctx.perfil, 'tem.camera'):
            nivel = 3
        det = ', '.join(a.split('.')[-1] for a in achados[:4]) + ('…' if len(achados) > 4 else '')
        itens.append(Item('app:' + titulo, titulo, explica + (f' ({det})' if len(achados) > 1 or titulo.startswith('apps') else ''),
                          'menos coisas em segundo plano e no menu', custo, nivel, py=_py_remove_apps, nota=nota,
                          reverte=False, dados=achados))
    conhecidos = {a for i in itens for a in i.dados}
    nunca = re.compile(r'Store|DesktopAppInstaller|Photos|Calculator|Notepad|Paint$|ScreenSketch|Terminal|VCLibs|NET\.|UI\.Xaml|'
                       r'WindowsAppRuntime|Services\.Store|SecHealthUI|HEIF|HEVC|VP9|WebMedia|WebpImage|RawImage|AV1|Realtek|Intel|NVIDIA|AMD|'
                       r'Dolby|DTS|Waves|Synaptics|ELAN|Lenovo(Companion|Utility)|E046963F|E0469640|QuickAccess|Wacom|Client\.|Windows\.(Shell|Start|Search|Cortana)|'
                       r'Microsoft\.Windows\.|MicrosoftWindows\.|AAD\.|AccountsControl|LockApp|Win32WebViewHost|BioEnrollment|CredDialogHost|ECApp|'
                       r'OOBE|ParentalControls|PeopleExperienceHost|XGpuEjectDialog|CapturePicker|PinningConfirmation|AsyncTextService|ApplicationCompatibility|'
                       r'Edge$|MicrosoftEdge|WidgetsPlatformRuntime|StorePurchaseApp|Winget|Sense|Extension|Runtime|WinAppRuntime|DirectX|LanguageExperience|'
                       r'GamingServices|OneDriveSync|Xaml|Framework|Codec|Claude|Anthropic', re.I)
    for nome in sorted(n for n in instalados if n not in conhecidos and not nunca.search(n)):
        itens.append(Item('app:' + nome, nome.split('.')[-1] if '.' in nome else nome, f'App instalado ({nome}). Não está na lista de '
                          'conhecidos: remova só se souber o que é.', 'menos um app', 'risco desconhecido', 0, py=_py_remove_apps,
                          reverte=False, dados=[nome]))
    return itens


# ═══════════════════════════════ IA do Windows ═══════════════════════════════

@pacote('ia', 'IA do Windows', 'Copilot, Recall, IA no Paint, Bloco de Notas, Edge e Office',
        'Desliga a IA só por meios oficiais: políticas documentadas pela Microsoft, desinstaladores e Remove-AppxPackage. '
        'Nada de scripts "milagrosos". No Windows Home, atualizações podem trazer o Copilot de volta; a manutenção semanal reaplica. '
        'Algumas tarefas de IA são protegidas pelo sistema e ficam.')
def itens_ia(ctx):
    w = f'{HKLM_POL}\\WindowsAI'
    wu = f'{HKCU_POL}\\WindowsAI'
    win11 = pf(ctx.perfil, 'so.win11', True)
    return [
        Item('copilot', 'Copilot desligado', 'Política oficial que desliga o Copilot do Windows e tira o botão da barra.',
             'menos um app em segundo plano', 'perde o Copilot do Windows', 1,
             RR(R(f'{HKCU_POL}\\WindowsCopilot', 'TurnOffWindowsCopilot', 1), R(f'{HKLM_POL}\\WindowsCopilot', 'TurnOffWindowsCopilot', 1),
                R(ADV, 'ShowCopilotButton', 0),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Shell Extensions\\Blocked', '{CB3B0003-8088-4EDE-8769-8B354AB2FF8C}', '', 'String'))),
        Item('copilot-app', 'remover o app Copilot', 'Desinstala o app Copilot (da Loja e, se houver, a versão Win32 pelo desinstalador dele).',
             'menos espaço e processos', 'perde o app', 2, r'''
foreach ($__n in 'Microsoft.Copilot','Microsoft.Windows.Ai.Copilot.Provider') {
  foreach ($x in @(Get-AppxPackage -AllUsers -Name $__n -ErrorAction SilentlyContinue | Where-Object { -not $_.NonRemovable })) { if ($TESTE) { Plano ('remover ' + $__n) } else { try { Remove-AppxPackage -Package $x.PackageFullName -AllUsers -ErrorAction Stop; $script:MUDOU++ } catch { Aviso ($__n + ': ' + $_.Exception.Message) } } }
}
$__w = @(Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -eq 'Microsoft Copilot' })
foreach ($x in $__w) { if ($TESTE) { Plano 'desinstalar Microsoft Copilot (Win32)' } else { $u = [string]$x.QuietUninstallString; if (-not $u) { $u = [string]$x.UninstallString }; if ($u -match '^"([^"]+)"\s*(.*)$') { $r = Roda $Matches[1] $Matches[2] 5; $script:MUDOU++ } } }''',
             minutos=8, reverte=False),
        Item('recall', 'Recall e análise de IA desligados', 'Políticas oficiais: Recall (fotos da tela), Clique para Fazer, '
             'agente nas Configurações e conectores de agentes desligados, para a máquina e para você.',
             'privacidade; menos processamento em segundo plano', 'perde esses recursos de IA', 1,
             RR(R(w, 'AllowRecallEnablement', 0), R(w, 'DisableAIDataAnalysis', 1), R(w, 'TurnOffSavingSnapshots', 1), R(wu, 'TurnOffSavingSnapshots', 1), R(w, 'DisableClickToDo', 1),
                R(w, 'DisableSettingsAgent', 1), R(w, 'ConfigureAgentConnectors', 2), R(wu, 'DisableAIDataAnalysis', 1),
                R(wu, 'DisableClickToDo', 1))) if win11 else None,
        Item('recall-recurso', 'recurso opcional Recall desativado', 'Desativa o componente Recall pelo DISM (sem apagar: dá para ligar de novo).',
             'tira o componente do sistema', 'nenhum para quem não usa', 2, r'''
$__f = Tenta { Get-WindowsOptionalFeature -Online -FeatureName Recall -ErrorAction Stop } $null
if ($__f -and [string]$__f.State -eq 'Enabled') { if ($TESTE) { Plano 'desativar recurso Recall' } else { Guarda-Desfazer 'recall' 'Enable-WindowsOptionalFeature -Online -FeatureName Recall -NoRestart | Out-Null'; Disable-WindowsOptionalFeature -Online -FeatureName Recall -NoRestart -ErrorAction Stop | Out-Null; $script:MUDOU++ } }''',
             minutos=10) if win11 else None,
        Item('paint', 'IA no Paint', 'Políticas oficiais: Criador de Imagens, Cocreator e Preenchimento Generativo desligados.',
             'menos chamadas à nuvem', 'perde esses recursos do Paint', 2,
             RR(*(R('HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Paint', n, 1) for n in ('DisableImageCreator', 'DisableCocreator', 'DisableGenerativeFill')))) if win11 else None,
        Item('notepad', 'IA no Bloco de Notas', 'Política oficial que desliga reescrever e resumir com IA no Bloco de Notas.',
             'Bloco de Notas mais simples', 'perde a reescrita com IA', 2, R('HKLM:\\SOFTWARE\\Policies\\WindowsNotepad', 'DisableAIFeatures', 1)) if win11 else None,
        Item('edge-ia', 'IA no Edge', 'Políticas do Edge: sem ícone do Copilot, sem leitura da página pelo Copilot, sem escrita com IA '
             'e sem busca no histórico por IA. O Edge passa a mostrar "Gerenciado pela sua organização".',
             'Edge mais leve e privado', 'perde o Copilot no Edge; aparece o aviso de gerenciado', 2,
             RR(R(EDGE_POL, 'Microsoft365CopilotChatIconEnabled', 0), R(EDGE_POL, 'CopilotPageContext', 0),
                R(EDGE_POL, 'ComposeInlineEnabled', 0), R(EDGE_POL, 'EdgeHistoryAISearchEnabled', 0),
                R(EDGE_POL, 'GenAILocalFoundationalModelSettings', 1), R(EDGE_POL, 'HubsSidebarEnabled', 0),
                R(EDGE_POL, 'EdgeEntraCopilotPageContext', 0))) if pf(ctx.perfil, 'tem.edge', True) else None,
        Item('office-ia', 'Microsoft 365 Copilot e IA do Office', 'Remove os pacotes Microsoft 365 (Copilot), ActionsServer e '
             'WritingAssistant, desliga a tarefa Office Actions Server e tira "Perguntar ao Microsoft 365 Copilot" do menu do botão direito.',
             'menos processos do Office em segundo plano', 'perde o Copilot do Office', 2, RR(r'''
foreach ($__n in 'Microsoft.MicrosoftOfficeHub','Microsoft.Office.ActionsServer','Microsoft.WritingAssistant') {
  foreach ($x in @(Get-AppxPackage -AllUsers -Name $__n -ErrorAction SilentlyContinue | Where-Object { -not $_.NonRemovable })) { if ($TESTE) { Plano ('remover ' + $__n) } else { try { Remove-AppxPackage -Package $x.PackageFullName -AllUsers -ErrorAction Stop; $script:MUDOU++ } catch { Aviso ($__n + ': ' + $_.Exception.Message) } } }
}
Desliga-Tarefas '\\Microsoft\\Office\\Office Actions Server' | Out-Null''',
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Shell Extensions\\Blocked', '{DB6BACB1-FC31-4B28-9C53-7240A4F98404}', '', 'String')),
             minutos=6),
        Item('digitacao', 'coleta de digitação e tinta', 'O Windows deixa de aprender com o que você digita e escreve à mão '
             'e de colher contatos para isso.', 'privacidade', 'sugestões de digitação ficam menos personalizadas', 2,
             RR(R('HKCU:\\Software\\Microsoft\\InputPersonalization', 'RestrictImplicitInkCollection', 1),
                R('HKCU:\\Software\\Microsoft\\InputPersonalization', 'RestrictImplicitTextCollection', 1),
                R('HKCU:\\Software\\Microsoft\\InputPersonalization\\TrainedDataStore', 'HarvestContacts', 0),
                R('HKCU:\\Software\\Microsoft\\Personalization\\Settings', 'AcceptedPrivacyPolicy', 0))),
        Item('ia-servico', 'serviço e tarefas de IA', 'Serviço WSAIFabricSvc desativado e tarefas em \\Microsoft\\Windows\\WindowsAI '
             'desligadas (menos a PolicyConfiguration, que aplica as políticas acima).', 'menos processos parados gastando',
             'nenhum para quem não usa IA do Windows', 3,
             RR(SVC(['WSAIFabricSvc']), "Desliga-Tarefas '^\\\\Microsoft\\\\Windows\\\\WindowsAI\\\\' 'PolicyConfiguration' | Out-Null")) if win11 else None,
    ]


# ═══════════════════════════════ inicialização ═══════════════════════════════

LISTA_INICIO_PS = INICIO_PS + r'''
Dado 'inicio' (Lista (ListaInicio))
'''

# (padrão no nome ou comando, nível, por quê). O primeiro que casar vale.
CLASSES_INICIO = [
    (r'SecurityHealth|Windows Defender|MsMpEng|WindowsDefender', None, 'segurança do Windows: fica sempre'),
    (r'Avast|AVG ?(UI|Antivirus|Internet)|Kaspersky|\bavp\b|ESET|\begui\b|Bitdefender|bdagent|Norton|McAfee|Malwarebytes|Avira|Sophos|Trend ?Micro|F-Secure|Panda (Dome|Security)|'
     r'CrowdStrike|SentinelOne|Cylance|Carbon ?Black', None, 'antivírus: fica sempre (é a sua proteção)'),
    (r'GlobalProtect|Cisco AnyConnect|vpnui|FortiClient|Zscaler|Netskope|Pulse Secure|Ivanti|Citrix|Intune|CompanyPortal|ManageEngine|Tanium', None,
     'programa da empresa: fica sempre (o TI precisa dele)'),
    (r'1Password|Bitwarden|KeePass|LastPass|Dashlane|NordPass|Proton ?Pass', 0, 'gerenciador de senhas: sem ele aberto, as senhas não preenchem sozinhas'),
    (r'NordVPN|ExpressVPN|ProtonVPN|Surfshark|OpenVPN|WireGuard|Tailscale|Cloudflare WARP|Mullvad|Windscribe|Hamachi|ZeroTier|Radmin', 0,
     'VPN: se você depende dela ligada sempre, deixe'),
    (r'Veeam|Acronis|Macrium|Backblaze|CrashPlan|Carbonite|SyncBack|FreeFileSync|Duplicati', 0, 'backup: sem ele abrindo, o backup automático para'),
    (r'f\.lux|flux|PowerToys|AutoHotkey|ShareX|Lightshot|Greenshot|Flameshot|Ditto|Everything|EarTrumpet|TranslucentTB|StartAllBack|ExplorerPatcher|'
     r'Twinkle ?Tray|Listary|Flow\.Launcher|espanso|QuickLook|Rainmeter|Wallpaper ?Engine|Lively|DisplayFusion|FancyZones', 0,
     'utilitário que só funciona se abrir com o Windows: você instalou para isso'),
    (r'HP ?Smart|HPStatus|Epson|EEventManager|Canon|IJ ?Scan|Brother|BrMfcWnd|BrStMonW|ControlCenter4|Lexmark|Samsung Printer|StatusMonitor|Status Monitor', 2,
     'monitor da impressora: ela continua imprimindo sem ele'),
    (r'Creative ?Cloud|CCXProcess|CCLibrary|Adobe ?(Desktop|Collab|Creative|Genuine)|AGSService|CoreSync|Acrobat ?Assistant|AcroTray|Adobe ?Acrobat ?Synchronizer', 1,
     'Adobe em segundo plano: os programas da Adobe abrem ele quando precisam'),
    (r'CCleaner|IObit|Advanced SystemCare|Driver ?Booster|Driver ?Easy|Glary|Wise ?Care|Auslogics|Reimage|Restoro|Outbyte|PC ?App ?Store|Smart ?Defrag|'
     r'Avast ?Cleanup|AVG ?TuneUp|Razer ?Cortex|Game ?Booster|WinZip (Driver|System)', 1, '"otimizador" residente: fica ligado só para vender limpeza'),
    (r'qBittorrent|uTorrent|BitTorrent|Transmission|Deluge|Tixati|Free Download Manager|IDMan|Internet Download Manager|JDownloader|eMule|Soulseek', 2,
     'programa de download: abra quando for baixar'),
    (r'MSIAfterburner|RTSS|RivaTuner|HWiNFO|HWMonitor|Core ?Temp|AIDA64|FanControl|SpeedFan|ThrottleStop|Open ?Hardware|Libre ?Hardware', 0,
     'monitor ou controle de ventoinha: se o seu perfil de ventoinha ou de undervolt depende dele, deixe'),
    (r'TeamViewer|AnyDesk|RustDesk|Parsec|Chrome Remote|Splashtop|LogMeIn|RemotePC|Supremo', 3,
     'acesso remoto: sem ele abrindo, ninguém (nem você) entra neste PC de fora'),
    (r'VirtualBox|VBoxTray|VMware|vmware-tray|BlueStacks|LDPlayer|\bNox|MEmu|Android ?Studio|Docker', 2, 'máquina virtual ou emulador: abra quando for usar'),
    (r'Ollama|LM ?Studio|GitHub ?Desktop|JetBrains ?Toolbox|Sourcetree|GitKraken|Postman|Insomnia|DBeaver|XAMPP|WampServer|Laragon', 2,
     'ferramenta de programação: abra quando for usar'),
    (r'Java ?Update|jusched|SunJavaUpdateSched|QuickTime|qttask|RealPlayer|Winamp ?Agent|WinZip|\bNero\b|Roxio|CyberLink|PowerDVD|Bonjour|Apple ?Push|APSDaemon|iCloud ?(Services|Photos)?Helper', 1,
     'resto de programa antigo ou atualizador: não precisa abrir sozinho'),
    (r'vgc|vgtray|Vanguard|EasyAntiCheat|BattlEye|FACEIT|PunkBuster|nProtect|XignCode', 0, 'anti-cheat: só tire se você pedir (alguns jogos deixam de abrir)'),
    (r'SynTP|ETDCtrl|Elan|Synaptics|Touchpad|Precision|Wacom|PenService|Pen Tablet', 0, 'driver de touchpad ou caneta: sem ele os gestos podem parar'),
    (r'RtkAud|RTHDVCPL|Realtek|IntelAudio|SmartAudio|Conexant|IDT|Dolby|DTS|MaxxAudio|Waves|Nahimic|SonicStudio', 3, 'painel de áudio: sem ele, efeitos e alguns atalhos de som param'),
    (r'Bluetooth|BTTray|ibtsiva', 3, 'Bluetooth do fabricante'),
    (r'OneDrive', 1, 'sincronização do OneDrive'),
    (r'Dropbox|GoogleDrive|Google Drive|GoogleDriveFS|MEGAsync|iCloud|pCloud|Nextcloud|Box Sync|\\Box\\|Sync\.com|Syncthing|Resilio|Proton ?Drive|Yandex\.Disk', 3, 'sincronização de arquivos: os arquivos só sincronizam com ele aberto'),
    (r'MicrosoftEdgeAutoLaunch|msedge.*--no-startup-window|MicrosoftEdge', 1, 'Edge pré-carregado sem você pedir'),
    (r'Teams|ms-teams|com\.squirrel\.Teams', 1, 'Teams abrindo sozinho'),
    (r'Update|Updater|GoogleUpdate|AdobeARM|AdobeGC|jusched|iTunesHelper|CCleaner|Helper|Launcher.*-silent|BraveSoftware Update|Edge Update', 1,
     'atualizador: continua atualizando pelas tarefas dele'),
    (r'Cortana|YourPhone|PhoneExperienceHost|Copilot|Widgets', 1, 'recurso do Windows que você não abriu'),
    (r'Spotify|Deezer|TIDAL|Amazon Music|Apple Music|Discord|Guilded|Steam|EpicGames|Epic Games|Battle\.net|Origin|EADesktop|EA app|Ubisoft|GOG|Riot Client|Rockstar|Amazon Games|\bitch\b|Playnite|Heroic|CurseForge|Minecraft|Xbox|'
     r'Skype|Zoom|Webex|GoToMeeting|WhatsApp|Telegram|Signal|Element|Viber|WeChat|Slack|Mattermost|Thunderbird|Mailbird|Opera|Brave|chrome|Vivaldi|Firefox|\bArc\b|Notion|Obsidian|Evernote|Todoist|Trello|Figma|Canva|'
     r'Lghub|LGHUB|Razer|Corsair|iCUE|SteelSeries|Logitech|\bLogi(?!n)|HyperX|NGENUITY|ROCCAT|NZXT|OpenRGB|SignalRGB|Wootility|Overwolf|Medal|Outplayed|\bOBS|Streamlabs|NVIDIA Broadcast|Elgato|Stream ?Deck|Voicemod|Krisp|Clownfish|SteelSeries Sonar',
     2, 'programa que você abre quando quiser'),
    (r'igfx|IntelGraphics|NvBackend|NVIDIA|RadeonSoftware|AMD|cncmd', 2, 'painel da placa de vídeo (o driver continua)'),
    (r'AWCC|Alienware|Armoury|ArmouryCrate|MyASUS|Vantage|Legion|NitroSense|PredatorSense|Acer ?(Quick|Care)|MSI|Dragon Center|Mystic ?Light|OMEN|Gigabyte|RGB ?Fusion|AORUS|Samsung ?Settings|Galaxy ?Book|LG ?(Control|Smart)|Huawei|PC ?Manager|Dell ?(Optimizer|Power|Command)|SupportAssist|HP ?(Support|Command|System Event|JumpStart)', 3, 'central do fabricante: perfis de ventoinha e luz podem parar'),
]


def _classe_inicio(nome, cmd):
    alvo = f'{nome} {cmd}'
    for padrao, nivel, porque in CLASSES_INICIO:
        if re.search(padrao, alvo, re.I):
            return nivel, porque
    return 3, 'programa que abre com o Windows'


ASSINATURA_PS = r'''
$lista = «lista»
$out = @()
foreach ($c in $lista) {
  $e = [Environment]::ExpandEnvironmentVariables([string]$c).Trim('"')
  $s = $null; $quem = ''; $st = 'SemArquivo'
  if (Test-Path -LiteralPath $e -PathType Leaf) { $s = Tenta { Get-AuthenticodeSignature -LiteralPath $e -ErrorAction Stop } $null }
  if ($s) { $st = [string]$s.Status; if ($s.SignerCertificate) { $quem = $s.SignerCertificate.GetNameInfo('SimpleName', $false) } }
  $out += [pscustomobject]@{ exe = [string]$c; status = $st; quem = [string]$quem }
}
Dado 'assinaturas' (Lista $out)
'''


BOOT_PROG_PS = r'''
$__ini = (Get-Date).AddDays(-60)
$__ev = @(Get-WinEvent -FilterHashtable @{ LogName = 'Microsoft-Windows-Diagnostics-Performance/Operational'; Id = 101; StartTime = $__ini } -ErrorAction SilentlyContinue)
$__l = foreach ($e in $__ev) {
  $d = @{}; ([xml]$e.ToXml()).Event.EventData.Data | ForEach-Object { $d[$_.Name] = $_.'#text' }
  [pscustomobject]@{ nome = [string]$d.Name; exibe = [string]$d.FriendlyName; ms = [int]$d.DegradationTime }
}
Dado 'boot_programas' (Lista ($__l | Group-Object nome, exibe | ForEach-Object { [pscustomobject]@{ nome = $_.Group[0].nome; exibe = $_.Group[0].exibe; vezes = $_.Count; s = [math]::Round(($_.Group | Measure-Object ms -Average).Average / 1000, 1) } }))
'''


def _chave(txt):
    return re.sub(r'[^a-z0-9]', '', str(txt or '').lower().replace('.exe', ''))


def impacto_boot(boot, nome, exe):
    """(segundos, vezes) que o Windows mediu de atraso no boot para este item de inicialização, ou None.
    Casa pelo nome do item ou do executável com o nome (ou nome amigável) que o log de diagnóstico guarda.
    Só vale com chave de pelo menos 4 letras, para 'a' ou 'ms' não casarem com tudo."""
    chaves = {c for c in (_chave(nome), _chave(Path(str(exe or '').replace('\\', '/')).name)) if len(c) >= 4}
    melhor = None
    for b in boot or []:
        alvos = {_chave(b.get('nome')), _chave(b.get('exibe'))}
        if any(c in x or (x and len(x) >= 4 and x in c) for c in chaves for x in alvos if x):
            if melhor is None or b.get('s', 0) > melhor[0]:
                melhor = (float(b.get('s', 0)), int(b.get('vezes', 1)))
    return melhor


@pacote('inicializacao', 'inicialização', 'o que abre junto com o Windows',
        'Desliga pelo mesmo mecanismo do Gerenciador de Tarefas (StartupApproved): o programa continua instalado e você religa '
        'quando quiser. Também olha a pasta Inicializar, as tarefas de inicialização dos apps da Loja e as tarefas agendadas '
        'que rodam no logon. Antivírus nunca sai; anti-cheat, touchpad e caneta só se você marcar.')
def itens_inicializacao(ctx):
    s = roda_ps(ctx.t, LISTA_INICIO_PS, 'lista-inicio', minutos=2, mostra=False)
    itens = []
    impactos = {}
    exes = {}
    for e in lista(s.dados.get('inicio')):
        if e.get('ligado') and e.get('existe') is not False:
            exes[e.get('nome', '')] = re.sub(r'^"([^"]+)".*$', r'\1', e.get('cmd', '')).split(' -')[0]
    boot = []
    if exes and WINDOWS:
        boot = [x for x in lista(roda_ps(ctx.t, BOOT_PROG_PS, 'boot-programas', minutos=2, mostra=False).dados.get('boot_programas')) if isinstance(x, dict)]
    assin = {}
    if exes and WINDOWS:
        r = roda_ps(ctx.t, ps_monta(ASSINATURA_PS, lista=ps_lista(sorted(set(exes.values())))), 'assinaturas', minutos=3, mostra=False)
        assin = {x.get('exe'): x for x in lista(r.dados.get('assinaturas')) if isinstance(x, dict)}
    for e in lista(s.dados.get('inicio')):
        if not e.get('ligado') or e.get('existe') is False:   # programa que já saiu do PC não abre nada
            continue
        nome, cmd, tipo = e.get('nome', ''), e.get('cmd', ''), e.get('tipo')
        nivel, porque = _classe_inicio(nome, cmd)
        if nivel is None:
            continue
        nota = ''
        if re.search('OneDrive', nome, re.I) and pf(ctx.perfil, 'tem.onedrive_usado'):
            nivel, nota = 0, 'sua pasta do OneDrive tem arquivos: sem ele abrindo, eles param de sincronizar'
        if tipo in ('run', 'pasta'):
            ps = R(e['ap'], nome, bytes([3] + [0] * 11), 'Binary')
            onde = 'registro' if tipo == 'run' else 'pasta Inicializar'
        elif tipo == 'loja':
            ps = R(e['ap'], 'State', 1)
            onde = 'app da Loja'
        else:
            ps = f'Set-Tarefa {psq(e["ap"])} $false | Out-Null'
            onde = 'tarefa no logon'
            nivel = max(nivel or 0, 2) if nivel else 0
        exe = re.sub(r'^"([^"]+)".*$', r'\1', cmd).split(' -')[0]
        if assin.get(exe, {}).get('status') == 'NotSigned' and not re.match(r'(?i)^[a-z]:\\windows', exe):
            nota = (nota + ' · ' if nota else '') + 'sem assinatura digital: confira o que é antes de manter'
            rel_desconhecido('inicialização sem assinatura digital', nome, corta_esq(exe, 70))
        if porque == 'programa que abre com o Windows':
            rel_desconhecido('inicialização que o Katharos não classificou', nome, corta_esq(exe, 70))
        imp = impacto_boot(boot, nome, exe)
        ganho = 'liga mais rápido e sobra RAM'
        if imp and imp[0] > 0:
            ganho = f'o Windows mediu ~{br(imp[0], 1)} s de atraso no boot (média de {pl(imp[1], "boot", "boots")}) e sobra RAM'
        impactos[nome] = imp[0] if imp else 0.0
        q = quem_e(Path(str(exe).replace('\\', '/')).name) if porque == 'programa que abre com o Windows' else None
        if q:
            porque = f'{q[0]}: {q[1]}'
        itens.append(Item('ini:' + nome, nome, f'{porque[0].upper() + porque[1:]}. ({onde}: {corta_esq(caminho_curto(exe), 60)})',
                          ganho, 'não abre sozinho; abra pelo menu quando quiser', nivel, ps, nota=nota))
    itens.sort(key=lambda i: (i.nivel == 0, i.nivel, -impactos.get(i.titulo, 0.0), i.titulo.lower()))
    return itens


# ═══════════════════════════════ serviços ═══════════════════════════════

ORFAOS_PS = r'''
foreach ($tk in @(Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { $_.State -ne 'Disabled' -and $_.TaskPath -notmatch '^\\Microsoft\\' })) {
  foreach ($ac in @($tk.Actions)) {
    $exe = [Environment]::ExpandEnvironmentVariables([string]$ac.Execute).Trim('"')
    if ($exe -match '^[A-Za-z]:\\.*\.exe$' -and -not (Test-Path -LiteralPath $exe)) { Set-Tarefa ($tk.TaskPath + $tk.TaskName) $false | Out-Null }
  }
}
foreach ($s in @(Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | Where-Object { $_.StartMode -ne 'Disabled' -and $_.PathName -and $_.PathName -notmatch 'svchost|\\Windows\\' })) {
  $exe = $s.PathName; if ($exe -match '^"([^"]+)"') { $exe = $Matches[1] } elseif ($exe -match '^(\S+\.exe)') { $exe = $Matches[1] }
  if ($exe -match '\.exe$' -and -not (Test-Path -LiteralPath ([Environment]::ExpandEnvironmentVariables($exe)))) { Set-Servico $s.Name 'disabled' | Out-Null }
}'''

FABRICANTE_SVC_PS = r'''
$__pad = 'SupportAssist|TechHub|Dell Client Management|Dell Data Vault|Dell Customer Connect|Dell Foundation|Touchpoint Analytics|HP Insights|HP Diagnostics|HP App Helper|HP Network HSA|HP System Info HSA|HP Comm Recovery|Killer Analytics|Killer Network Service|Killer Provider Data Helper|Intel\(R\) Energy Server|System Usage Report|Intel\(R\) Driver & Support|NVIDIA Telemetry|Acer Quick Access Service|ASUS Optimization'
foreach ($s in @(Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -match $__pad -and $_.StartMode -eq 'Auto' })) { Set-Servico $s.Name 'demand' -Parar | Out-Null }
Desliga-Tarefas 'Killer Startup Task|NvTmRep|NvDriverUpdateCheck|NvProfileUpdater|NvNodeLauncher|Dell SupportAssist|DellUpdate|Dell Data Vault|HP Support Assistant|HPAudioSwitch|Lenovo.*(Welcome|Now)|AcerJumpstart|AcerRegistration|McAfee|Norton' 'Dell Command|DellCommandUpdate' | Out-Null'''

ATUALIZADORES_SVC = ['gupdate', 'gupdatem', 'GoogleUpdaterService', 'GoogleUpdaterInternalService', 'edgeupdate', 'edgeupdatem',
                     'brave', 'bravem', 'BraveElevationService', 'MozillaMaintenance', 'AdobeARMservice', 'AdobeUpdateService',
                     'AGSService', 'AGMService', 'ClickToRunSvc']


@pacote('servicos', 'serviços', 'serviços do Windows e de fabricante que este PC não usa',
        'Desativa (nunca apaga) serviços sem uso. O katharos olha o que o PC tem antes: impressora, scanner, leitor de cartão, '
        'sensores, Bluetooth, área de trabalho remota, WSL/Docker e jogos. Rede, áudio, Windows Update, Defender e firewall nunca entram.')
def itens_servicos(ctx):
    p = ctx.perfil
    tem = p.get('tem') or {}
    itens = [
        Item('basicos', 'mapas, demonstração, mídia e Insider', 'MapsBroker (mapas offline), RetailDemo (modo de loja), '
             'WMPNetworkSvc (compartilhar mídia do Windows Media Player), wisvc (programa Insider) e RemoteRegistry '
             '(editar o registro pela rede: desligar também é mais seguro).', 'menos serviços rodando', 'nenhum', 1,
             SVC(['MapsBroker', 'RetailDemo', 'WMPNetworkSvc', 'wisvc', 'RemoteRegistry'])),
        Item('fax', 'fax', 'Serviço de fax (Fax).', 'um serviço a menos', 'não envia fax pelo PC', 1, SVC(['Fax'])),
        Item('impressao', 'impressão', 'Spooler e notificações de impressora.', 'menos dois serviços',
             'não imprime, nem "Imprimir em PDF"', 2, SVC(['Spooler', 'PrintNotify']),
             nota='') if not tem.get('impressora') else None,
        Item('xbox', 'Xbox', 'Login, salvamentos na nuvem, rede e acessórios do Xbox (XblAuthManager, XblGameSave, XboxNetApiSvc, XboxGipSvc).',
             'menos quatro serviços', 'perde Game Pass, login Xbox em jogos e controle Xbox sem fio pelo adaptador',
             0 if joga(p) else 2, SVC(['XblAuthManager', 'XblGameSave', 'XboxNetApiSvc', 'XboxGipSvc']),
             nota='tem jogos instalados: não vem marcado' if joga(p) else ''),
        Item('busca', 'indexação da busca (Windows Search)', 'O índice de arquivos que deixa a busca do menu rápida. Em HD, ele '
             'mantém o disco ocupado.', 'menos leitura de disco em segundo plano',
             'a busca por arquivos no menu e no Explorador fica bem mais lenta', 2 if eh_hd(p) else 3, SVC(['WSearch']),
             nota='Windows em HD: recomendado' if eh_hd(p) else 'em SSD o ganho é pequeno'),
        Item('empresa', 'recursos de empresa', 'App-V, UE-V, monitor de impressão compartilhada, coletor de eventos, compartilhamento '
             'de portas .NET, pagamentos NFC, Carteira, roteador AllJoyn, gateway ALG, realidade mista e áudio espacial de RV.',
             'menos serviços', 'nenhum em PC doméstico', 2,
             SVC(['AppVClient', 'UevAgentService', 'shpamsvc', 'Wecsvc', 'NetTcpPortSharing', 'SEMgrSvc', 'WalletService',
                  'AJRouter', 'ALG', 'MixedRealityOpenXRSvc', 'perceptionsimulation', 'spectrum'])) if not pf(p, 'pc.dominio') else None,
        Item('telefonia', 'telefonia', 'PhoneSvc e TapiSrv (telefonia pelo PC).', 'menos serviços', 'modem e discador antigos param', 2,
             SVC(['PhoneSvc', 'TapiSrv'])),
        Item('hotspot', 'hotspot móvel', 'Compartilhar a internet do PC por Wi-Fi (icssvc' + ('' if tem.get('wsl') or tem.get('hyperv') else ' e SharedAccess') + ').',
             'menos serviços', 'não cria hotspot pelo PC', 2,
             SVC(['icssvc'] if tem.get('wsl') or tem.get('hyperv') or tem.get('docker') else ['icssvc', 'SharedAccess']),
             nota='WSL/Hyper-V/Docker: SharedAccess fica' if tem.get('wsl') or tem.get('hyperv') or tem.get('docker') else ''),
        Item('controle-pais', 'controle dos pais', 'WpcMonSvc (Family Safety).', 'um serviço a menos', 'controle dos pais da conta Microsoft para', 2,
             SVC(['WpcMonSvc'])),
        Item('atualizadores', 'atualizadores em manual', 'Google, Edge, Brave, Firefox, Adobe e Office deixam de ficar rodando o tempo todo. '
             'Eles continuam se atualizando pelas próprias tarefas agendadas.', 'menos serviços parados gastando RAM',
             'atualizações desses programas podem chegar um pouco depois', 2, SVC(ATUALIZADORES_SVC, 'demand', parar=False)),
        Item('fabricante', 'serviços e tarefas de fabricante', 'Assistentes de suporte e telemetria em manual (SupportAssist, TechHub, '
             'Dell Client Management, HP Touchpoint/Insights, Killer Analytics, Intel Energy Server, telemetria NVIDIA) e tarefas que '
             'ficam falhando ou repetindo (Killer Startup Task, NVIDIA, Dell, HP). Dell Update/Command Update ficam.',
             'menos CPU e WMI parados', 'diagnóstico do fabricante só quando você abrir', 2, FABRICANTE_SVC_PS),
        Item('nahimic', 'Nahimic e efeitos de áudio do fabricante', 'NahimicService e as tarefas dele em manual.', 'menos CPU',
             'os efeitos do Nahimic (surround virtual) param; o som continua normal', 3,
             RR("foreach ($s in @(Get-Service -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^Nahimic' })) { Set-Servico $s.Name 'demand' -Parar | Out-Null }",
                "Desliga-Tarefas 'Nahimic' | Out-Null")),
        Item('orfaos', 'restos de programas desinstalados', 'Tarefas agendadas e serviços que apontam para programas que não existem mais.',
             'menos erros no boot e no registro de eventos', 'nenhum', 2, ORFAOS_PS),
        Item('sob-demanda', 'serviços que podem subir só quando precisar', 'Passa de automático para manual (o Windows liga quando '
             'algo pede): plataforma de dispositivos conectados, inventário de compatibilidade, armazenamento, descoberta de rede (SSDP, UPnP, '
             'publicação de recursos) e NetBIOS.', 'menos serviços rodando desde o boot', 'aparelhos de rede (TVs, impressoras na rede) podem demorar a aparecer', 3,
             "foreach ($__s in 'CDPSvc','InventorySvc','StorSvc','lmhosts','FDResPub','fdPHost','SSDPSRV','upnphost','DusmSvc') { $__m = Get-ModoServico $__s; if ($__m -and $__m.modo -match 'auto') { Set-Servico $__s 'demand' | Out-Null } }"),
        Item('svchost', 'agrupar serviços em menos processos', 'O Windows separa cada serviço num svchost próprio quando há mais de 3,5 GB de RAM. '
             'Com o limite igual à sua RAM, eles voltam a dividir o mesmo processo.', 'dezenas de processos a menos no Gerenciador de Tarefas',
             'ganho de RAM pequeno e não comprovado; se um serviço travar, leva os vizinhos junto', 3,
             R('HKLM:\\SYSTEM\\CurrentControlSet\\Control', 'SvcHostSplitThresholdInKB', int((pf(p, 'ram.total', 8) or 8) * 1024 * 1024))),
        Item('rdp', 'área de trabalho remota', 'TermService, SessionEnv e UmRdpService.', 'menos serviços e menos portas abertas',
             'ninguém acessa este PC pela Área de Trabalho Remota', 3, SVC(['TermService', 'SessionEnv', 'UmRdpService'])) if not tem.get('rdp') else None,
        Item('winrm', 'gerenciamento remoto (WinRM)', 'Serviço de administração remota pelo PowerShell.', 'um serviço a menos',
             'scripts remotos e alguns sistemas de empresa param', 3, SVC(['WinRM'])) if not tem.get('winrm') and not pf(p, 'pc.dominio') else None,
        Item('ssh', 'agente SSH', 'ssh-agent (guarda chaves SSH na memória).', 'um serviço a menos', 'quem usa chave SSH com senha digita de novo', 3,
             SVC(['ssh-agent'])) if not tem.get('ssh') else None,
        Item('smartcard', 'cartão inteligente', 'SCardSvr, ScDeviceEnum e CertPropSvc.', 'menos três serviços',
             'certificado digital em cartão ou token (e-CPF, e-CNPJ) para de funcionar', 3,
             SVC(['SCardSvr', 'ScDeviceEnum', 'CertPropSvc'])) if not tem.get('smartcard') else None,
        Item('sensores', 'sensores e localização', 'Sensores (giro, luz) e o serviço de localização.', 'menos serviços',
             'rotação automática de tela, brilho automático, fuso horário automático e "Encontrar meu dispositivo" param',
             3, SVC(['SensorDataService', 'SensorService', 'SensrSvc', 'lfsvc'])) if not pf(p, 'pc.tablet') else None,
        Item('scanner', 'scanner', 'stisvc (aquisição de imagens).', 'um serviço a menos', 'scanner para de funcionar', 3,
             SVC(['stisvc'])) if not tem.get('scanner') else None,
        Item('biometria', 'biometria', 'WbioSrvc (Windows Hello por rosto ou digital).', 'um serviço a menos', 'Windows Hello com rosto e digital para',
             3, SVC(['WbioSrvc'])) if not tem.get('biometria') else None,
        Item('compat', 'assistente de compatibilidade e rastreio de links', 'PcaSvc (avisos de compatibilidade de programas antigos) '
             'e TrkWks (conserta atalhos quando arquivos mudam de lugar em rede).', 'menos dois serviços',
             'programas muito antigos deixam de receber ajustes automáticos', 3, SVC(['PcaSvc', 'TrkWks'])),
    ]
    return itens


# ═══════════════════════════════ privacidade ═══════════════════════════════

@pacote('privacidade', 'privacidade e propaganda', 'telemetria, anúncios, sugestões, widgets, busca na web',
        'Políticas e configurações oficiais. Nada é apagado: tudo volta com o desfazer. Na edição Home, algumas políticas valem '
        'só em parte (a telemetria fica em "obrigatória", que é o mínimo possível).')
def itens_privacidade(ctx):
    dc = f'{HKLM_POL}\\DataCollection'
    sub = ['SilentInstalledAppsEnabled', 'SoftLandingEnabled', 'SubscribedContentEnabled', 'SystemPaneSuggestionsEnabled',
           'PreInstalledAppsEnabled', 'OemPreInstalledAppsEnabled', 'PreInstalledAppsEverEnabled', 'ContentDeliveryAllowed',
           'SubscribedContent-338388Enabled', 'SubscribedContent-338389Enabled', 'SubscribedContent-353694Enabled',
           'SubscribedContent-353696Enabled', 'SubscribedContent-310093Enabled', 'SubscribedContent-338393Enabled',
           'SubscribedContent-88000326Enabled']
    tarefas = ['\\Microsoft\\Windows\\Application Experience\\Microsoft Compatibility Appraiser',
               '\\Microsoft\\Windows\\Application Experience\\ProgramDataUpdater',
               '\\Microsoft\\Windows\\Application Experience\\MareBackup',
               '\\Microsoft\\Windows\\Customer Experience Improvement Program\\Consolidator',
               '\\Microsoft\\Windows\\Customer Experience Improvement Program\\UsbCeip',
               '\\Microsoft\\Windows\\DiskDiagnostic\\Microsoft-Windows-DiskDiagnosticDataCollector',
               '\\Microsoft\\Windows\\Feedback\\Siuf\\DmClient', '\\Microsoft\\Windows\\Feedback\\Siuf\\DmClientOnScenarioDownload',
               '\\Microsoft\\Windows\\Maps\\MapsUpdateTask', '\\Microsoft\\Windows\\Maps\\MapsToastTask',
               '\\Microsoft\\Windows\\CloudExperienceHost\\CreateObjectTask']
    cw = compat_windows(ctx.perfil)
    tele = ('O Windows para de enviar dados de diagnóstico e de pedir opinião.' if cw['telemetria_desliga_de_todo'] else
            f'O Windows envia só os dados obrigatórios e para de pedir opinião (no {cw["edicao_nome"] or "Home e no Pro"}, o mínimo que a '
            'Microsoft permite é o obrigatório: desligar de todo só no Enterprise e no Education).')
    anun = ('Sem ID de propaganda, sem apps de propaganda instalados sozinhos, sem "sugestões" no menu, na tela de bloqueio e nas '
            'Configurações, sem "vamos terminar de configurar".' + ('' if cw['consumidor_por_politica'] else
            ' Nesta edição a política de "experiências do consumidor" não vale; o que desliga são os ajustes da sua conta, que vêm junto.'))
    return [
        Item('telemetria', 'telemetria no mínimo', tele,
             'menos uso de rede e disco', 'nenhum', 1,
             RR(R(dc, 'AllowTelemetry', 0), R(dc, 'DoNotShowFeedbackNotifications', 1), R(dc, 'LimitDiagnosticLogCollection', 1),
                R(dc, 'DisableOneSettingsDownloads', 1), R(dc, 'AllowCommercialDataPipeline', 0), R(dc, 'AllowDeviceNameInTelemetry', 0),
                R(dc, 'MicrosoftEdgeDataOptIn', 0), R(f'{HKLM_POL}\\AppCompat', 'DisableInventory', 1), R(f'{HKLM_POL}\\AppCompat', 'AITEnable', 0),
                R(f'{HKLM_POL}\\HandwritingErrorReports', 'PreventHandwritingErrorReports', 1), R(f'{HKLM_POL}\\EdgeUI', 'DisableMFUTracking', 1),
                R('HKCU:\\Software\\Microsoft\\Siuf\\Rules', 'NumberOfSIUFInPeriod', 0),
                R('HKLM:\\SYSTEM\\CurrentControlSet\\Control\\WMI\\Autologger\\AutoLogger-Diagtrack-Listener', 'Start', 0))),
        Item('telemetria-svc', 'serviços de telemetria', 'DiagTrack (Experiências do Usuário Conectado) e dmwappushservice.',
             'menos um serviço que grava e envia o tempo todo', 'nenhum', 1,
             SVC(['DiagTrack', 'dmwappushservice', 'diagnosticshub.standardcollector.service', 'DcpSvc'])),
        Item('autologgers', 'registros contínuos de diagnóstico', 'Desliga os "autologgers" que gravam arquivos .etl o tempo todo '
             '(modelo de apps, rede celular, OOBE, SQM, contexto de diagnóstico, sessões de Wi-Fi).', 'menos escrita contínua em disco',
             'diagnósticos avançados da Microsoft ficam com menos dados', 3,
             RR(*(R(f'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\WMI\\Autologger\\{n}', 'Start', 0) for n in
                  ('AppModel', 'Cellcore', 'CloudExperienceHostOobe', 'DataMarket', 'DiagLog', 'LwtNetLog', 'SQMLogger', 'WdiContextLog', 'WiFiSession')))),
        Item('telemetria-tarefas', 'tarefas de telemetria', 'Avaliador de compatibilidade, programa de experiência do usuário, '
             'coleta de diagnóstico de disco, pesquisas de opinião e mapas (11 tarefas).', 'menos picos de disco e CPU', 'nenhum', 1,
             TAREFAS(tarefas)),
        Item('anuncios', 'anúncios e apps instalados sozinhos', anun,
             'menos propaganda e instalações surpresa', 'nenhum', 1,
             RR(R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo', 'Enabled', 0),
                R(f'{HKLM_POL}\\AdvertisingInfo', 'DisabledByGroupPolicy', 1),
                R(f'{HKLM_POL}\\CloudContent', 'DisableWindowsConsumerFeatures', 1), R(f'{HKLM_POL}\\CloudContent', 'DisableSoftLanding', 1),
                R(f'{HKCU_POL}\\CloudContent', 'DisableTailoredExperiencesWithDiagnosticData', 1),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Privacy', 'TailoredExperiencesWithDiagnosticDataEnabled', 0),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\UserProfileEngagement', 'ScoobeSystemSettingEnabled', 0),
                R(ADV, 'Start_IrisRecommendations', 0), R(ADV, 'ShowSyncProviderNotifications', 0),
                *(R(CDM, n, 0) for n in sub))),
        Item('atividades', 'histórico de atividades', 'O Windows para de gravar cada arquivo e app aberto.',
             'menos escrita em disco', 'a Linha do Tempo antiga fica vazia', 1,
             RR(*(R(f'{HKLM_POL}\\System', n, 0) for n in ('EnableActivityFeed', 'PublishUserActivities', 'UploadUserActivities')))),
        Item('cortana', 'Cortana', 'Políticas que desligam a Cortana, a busca na nuvem, a Cortana na tela de bloqueio e o uso da localização pela busca.',
             'nenhum processo da Cortana', 'nenhum (foi descontinuada)', 1,
             RR(*(R(f'{HKLM_POL}\\Windows Search', n, 0) for n in ('AllowCortana', 'AllowCloudSearch', 'AllowCortanaAboveLock', 'AllowSearchToUseLocation')),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Search', 'CortanaConsent', 0))),
        Item('anuncios-config', 'propaganda do Microsoft 365 nas Configurações', 'Tira os avisos de "conta" e ofertas do Microsoft 365 '
             'da página inicial das Configurações e do menu.', 'menos propaganda', 'nenhum', 1,
             RR(R(f'{HKLM_POL}\\CloudContent', 'DisableConsumerAccountStateContent', 1), R(f'{HKLM_POL}\\CloudContent', 'DisableThirdPartySuggestions', 1),
                R(CDM, 'SubscribedContent-338387Enabled', 0), R(CDM, 'SubscribedContent-353698Enabled', 0))),
        Item('office-telemetria', 'telemetria do Office', 'Tarefas de telemetria do Office desligadas e políticas que impedem o envio '
             'de dados de uso (Office 2013 a 365).', 'menos processos e uploads do Office', 'nenhum', 2, RR(
                "Desliga-Tarefas 'OfficeTelemetryAgent' | Out-Null",
                *(R(f'HKCU:\\Software\\Policies\\Microsoft\\Office\\{v}\\OSM', n, 0) for v in ('15.0', '16.0') for n in ('EnableLogging', 'EnableUpload')),
                R('HKCU:\\Software\\Policies\\Microsoft\\Office\\Common\\ClientTelemetry', 'DisableTelemetry', 1),
                R('HKCU:\\Software\\Policies\\Microsoft\\Office\\Common\\ClientTelemetry', 'SendTelemetry', 3),
                R('HKCU:\\Software\\Policies\\Microsoft\\Office\\16.0\\Common', 'QMEnable', 0),
                R('HKCU:\\Software\\Policies\\Microsoft\\Office\\16.0\\Common\\Feedback', 'Enabled', 0))) if pf(ctx.perfil, 'tem.office') else None,
        Item('vs-telemetria', 'telemetria do Visual Studio', 'Políticas oficiais: sem telemetria, sem diálogo de opinião e sem SQM.',
             'menos uploads', 'nenhum', 2, RR(R('HKCU:\\Software\\Microsoft\\VisualStudio\\Telemetry', 'TurnOffSwitch', 1),
                R('HKLM:\\SOFTWARE\\Policies\\Microsoft\\VisualStudio\\Feedback', 'DisableFeedbackDialog', 1),
                R('HKLM:\\SOFTWARE\\Policies\\Microsoft\\VisualStudio\\SQM', 'OptIn', 0), SVC(['VSStandardCollectorService150']))) if pf(ctx.perfil, 'tem.visualstudio') else None,
        Item('firefox-telemetria', 'telemetria do Firefox', 'Política oficial do Firefox sem telemetria e sem o "agente de navegador padrão".',
             'menos uploads', 'nenhum', 2, RR(R('HKLM:\\SOFTWARE\\Policies\\Mozilla\\Firefox', 'DisableTelemetry', 1),
                R('HKLM:\\SOFTWARE\\Policies\\Mozilla\\Firefox', 'DisableDefaultBrowserAgent', 1),
                "Desliga-Tarefas '\\\\Mozilla\\\\Firefox Default Browser Agent' | Out-Null")) if pf(ctx.perfil, 'tem.firefox') else None,
        Item('nuvem-clipboard', 'área de transferência na nuvem', 'O que você copia não sincroniza com outros aparelhos.',
             'privacidade', 'perde o colar entre aparelhos', 3, RR(R(f'{HKLM_POL}\\System', 'AllowCrossDeviceClipboard', 0))),
        Item('encontrar', '"Encontrar meu dispositivo"', 'Política que desliga o rastreio de localização do aparelho pela conta Microsoft.',
             'privacidade', 'não dá para localizar o PC perdido pela conta', 3, R('HKLM:\\SOFTWARE\\Policies\\Microsoft\\FindMyDevice', 'AllowFindMyDevice', 0)),
        Item('seguranca', 'portas de entrada antigas fechadas', 'SMBv1 desligado (protocolo usado pelo WannaCry), execução automática '
             'de pendrives e CDs desligada e Assistência Remota desligada.', 'mais segurança', 'aparelhos de rede muito antigos (antes de 2010) podem não abrir pastas', 1, RR(r'''
$__f = Tenta { Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -ErrorAction Stop } $null
if ($__f -and [string]$__f.State -eq 'Enabled') { if ($TESTE) { Plano 'desligar SMBv1' } else { Guarda-Desfazer 'smb1' 'Enable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart | Out-Null'; Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart -ErrorAction SilentlyContinue | Out-Null; $script:MUDOU++ } }''',
                R('HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer', 'NoDriveTypeAutoRun', 255),
                R('HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer', 'NoAutorun', 1),
                R('HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Remote Assistance', 'fAllowToGetHelp', 0)), minutos=6),
        Item('busca-web', 'busca do menu sem resultados da web', 'A busca do menu Iniciar procura só no PC: sem Bing, sem sugestões '
             'da internet e sem "destaques da pesquisa".', 'busca mais rápida e privada', 'pesquisas na web vão para o navegador', 2,
             RR(R(f'{HKCU_POL}\\Explorer', 'DisableSearchBoxSuggestions', 1), R(f'{HKLM_POL}\\Windows Search', 'ConnectedSearchUseWeb', 0),
                R(f'{HKLM_POL}\\Windows Search', 'DisableWebSearch', 1), R(f'{HKLM_POL}\\Windows Search', 'EnableDynamicContentInWSB', 0),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Search', 'BingSearchEnabled', 0),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\SearchSettings', 'IsDynamicSearchBoxEnabled', 0))),
        Item('widgets', 'widgets e notícias', 'O painel de notícias e clima (Windows 11) ou "Notícias e Interesses" (Windows 10).',
             'menos um processo do Edge em segundo plano', 'perde o painel de widgets', 2,
             RR(R('HKLM:\\SOFTWARE\\Policies\\Microsoft\\Dsh', 'AllowNewsAndInterests', 0), R(f'{HKLM_POL}\\Windows Feeds', 'EnableFeeds', 0),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Feeds', 'ShellFeedsTaskbarViewMode', 2))),
        Item('segundo-plano', 'apps da Loja em segundo plano', 'Apps da Loja deixam de rodar escondidos quando você não está usando.',
             'pouco de RAM e CPU', 'apps da Loja fechados (WhatsApp, Teams novo) podem não notificar', 2,
             RR(R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\BackgroundAccessApplications', 'GlobalUserDisabled', 1),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Search', 'BackgroundAppGlobalToggle', 0))),
        Item('segundo-plano-forte', 'bloquear segundo plano para todos', 'Política da máquina que nega segundo plano a todos os apps da '
             'Loja (o Windows 11 ignora o item anterior).', 'mais RAM e CPU livres', 'nenhum app da Loja notifica fechado', 3,
             R(f'{HKLM_POL}\\AppPrivacy', 'LetAppsRunInBackground', 2)),
        Item('erros', 'relatório de erros', 'O Windows para de montar e enviar relatórios de travamento (WerSvc e política).',
             'menos disco depois de travamentos', 'a Microsoft não recebe seus relatórios; soluções automáticas não aparecem', 2,
             RR(R(f'{HKLM_POL}\\Windows Error Reporting', 'Disabled', 1), SVC(['WerSvc']))),
        Item('localizacao', 'localização', 'Política que desliga a localização para todo o Windows.', 'privacidade',
             'fuso automático, mapas, clima local e "Encontrar meu dispositivo" param', 3,
             RR(R(f'{HKLM_POL}\\LocationAndSensors', 'DisableLocation', 1), R(f'{HKLM_POL}\\LocationAndSensors', 'DisableSensors', 1),
                R('HKLM:\\SYSTEM\\Maps', 'AutoUpdateEnabled', 0),
                R('HKLM:\\SOFTWARE\\Microsoft\\PolicyManager\\default\\WiFi\\AllowWiFiHotSpotReporting', 'Value', 0))),
        Item('edge-fundo', 'Edge sem rodar escondido', 'O Edge para de abrir pré-carregado no boot e de continuar aberto depois de fechado. '
             'O Edge passa a mostrar "Gerenciado pela sua organização".', 'menos RAM no boot', 'o Edge demora um pouco mais para abrir', 1,
             RR(R(EDGE_POL, 'StartupBoostEnabled', 0), R(EDGE_POL, 'BackgroundModeEnabled', 0))) if pf(ctx.perfil, 'tem.edge', True) else None,
    ]


# ═══════════════════════════════ visual ═══════════════════════════════

@pacote('visual', 'visual e barra de tarefas', 'efeitos, animações, transparência e barra enxuta',
        'Efeitos visuais têm ganho real em hardware antigo ou vídeo integrado. A suavização de fontes fica ligada (a maioria '
        'prefere). O Explorador reinicia no fim para aplicar.')
def itens_visual(ctx):
    win11 = pf(ctx.perfil, 'so.win11', True)
    d = 'HKCU:\\Control Panel\\Desktop'
    tela = pf(ctx.perfil, 'tela')
    tela = tela if isinstance(tela, dict) else {}
    nb = bool(pf(ctx.perfil, 'pc.notebook'))
    # hardware fraco (pouca RAM ou só vídeo integrado): os efeitos visuais pesam de verdade, então entram já no modo seguro
    ram_gb = pf(ctx.perfil, 'ram.total') if isinstance(pf(ctx.perfil, 'ram.total'), (int, float)) else 0
    videos = [v for v in lista(pf(ctx.perfil, 'video')) if isinstance(v, dict)]
    fraco = (0 < ram_gb < 7.5) or bool(videos and all(v.get('integrada') for v in videos))
    hz = tela.get('hz') if isinstance(tela.get('hz'), int) else 0
    hz_max = tela.get('hz_max') if isinstance(tela.get('hz_max'), int) else 0
    return [
        Item('monitor-hz', f'monitor na taxa máxima ({hz_max} Hz)' if hz_max else 'monitor na taxa máxima',
             'O Windows às vezes deixa a tela em 60 Hz mesmo quando ela aceita mais. Usa a maior taxa que a tela principal informa na resolução '
             'de agora (a resolução não muda). Só fica se você confirmar "manter" em 90 segundos; sem resposta, volta sozinha.',
             'imagem mais fluida e menos atraso em tudo, principalmente em jogos', 'em notebook na bateria, um pouco mais de consumo',
             2 if nb else 1, 'foreach ($m in @(Get-Monitores | Where-Object { $_.primaria })) { if ($m.max -ge $m.hz + 15) { Set-TaxaMonitor $m.dev $m.max ("{0} de {1} para {2} Hz" -f $m.nome, $m.hz, $m.max) | Out-Null } }',
             nota=f'a tela está em {hz} Hz e aceita {hz_max} Hz', reaplica=False) if hz and hz_max >= hz + 15 else None,
        Item('efeitos', 'efeitos visuais em desempenho', 'Sem sombras, esmaecimento, deslizamento de menus e caixas, mantendo a '
             'suavização de fontes e as miniaturas.', 'janelas e menus mais rápidos em PC fraco', 'visual mais seco', 1 if fraco else 2,
             RR(R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects', 'VisualFXSetting', 3),
                R(d, 'UserPreferencesMask', bytes([0x90, 0x12, 0x03, 0x80, 0x10, 0x00, 0x00, 0x00]), 'Binary'),
                R(d, 'FontSmoothing', '2', 'String'), R(ADV, 'ListviewAlphaSelect', 0), R(ADV, 'ListviewShadow', 0))),
        Item('animacoes', 'animações', 'Sem animação ao minimizar, maximizar e na barra de tarefas.', 'resposta imediata', 'nenhum', 2,
             RR(R(d + '\\WindowMetrics', 'MinAnimate', '0', 'String'), R(ADV, 'TaskbarAnimations', 0),
                R('HKCU:\\Software\\Microsoft\\Windows\\DWM', 'EnableAeroPeek', 0))),
        Item('menus', 'menus sem espera', 'Submenus abrem na hora (MenuShowDelay 0 em vez de 400 ms).', 'sensação de rapidez', 'nenhum', 1,
             R(d, 'MenuShowDelay', '0', 'String')),
        Item('transparencia', 'transparência', 'Sem efeito acrílico na barra, no menu e na tela de entrada.',
             'menos uso da placa de vídeo; só se nota em placa integrada ou com pouca RAM',
             'visual mais opaco', 2 if (not pf(ctx.perfil, 'tem.nvidia') and not pf(ctx.perfil, 'tem.amd')) or pf(ctx.perfil, 'ram.total', 16) <= 8 else 0, RR(R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize', 'EnableTransparency', 0),
                                        R(f'{HKLM_POL}\\System', 'DisableAcrylicBackgroundOnLogon', 1))),
        Item('arrastar', 'arrastar janela sem conteúdo', 'Ao arrastar, só o contorno se move.', 'menos trabalho de vídeo em PC fraco',
             'visual estranho para quem não está acostumado', 3, R(d, 'DragFullWindows', '0', 'String')),
        Item('icones', 'ícones no lugar de miniaturas', 'O Explorador mostra ícones em vez de gerar miniaturas de fotos e vídeos.',
             'pastas de mídia abrem mais rápido em HD', 'não vê a prévia das fotos', 3, R(ADV, 'IconsOnly', 1)),
        Item('fundo-preto', 'papel de parede liso', 'Fundo preto em vez de imagem (e sem Windows Destaque).', 'um pouco de RAM',
             'perde o papel de parede', 3, RR(R(d, 'WallPaper', '', 'String'), R('HKCU:\\Control Panel\\Colors', 'Background', '0 0 0', 'String'))),
        Item('barra', 'barra de tarefas enxuta', 'Sem Visão de Tarefas, Chat e botão de widgets; a busca vira só o ícone.',
             'barra limpa', 'esses botões somem (o atalho Win+Tab continua)', 2,
             RR(R(ADV, 'ShowTaskViewButton', 0), R(ADV, 'TaskbarMn', 0), R(ADV, 'TaskbarDa', 0), R(ADV, 'ShowCortanaButton', 0),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Search', 'SearchboxTaskbarMode', 1))),
        Item('extensoes', 'mostrar extensões dos arquivos', 'Mostra ".exe", ".pdf" etc. Ajuda a perceber arquivo disfarçado (foto.jpg.exe).',
             'segurança', 'nomes um pouco mais longos', 1, R(ADV, 'HideFileExt', 0)),
        Item('este-pc', 'Explorador abre em "Este Computador"', 'Em vez do Acesso Rápido com arquivos recentes.', 'privacidade e menos leitura',
             'nenhum', 2, RR(R(ADV, 'LaunchTo', 1), R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer', 'ShowRecent', 0),
                              R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer', 'ShowFrequent', 0))),
        Item('menu-classico', 'menu do botão direito completo', 'No Windows 11, o menu do botão direito volta a mostrar tudo, sem '
             '"Mostrar mais opções".', 'menos cliques', 'visual do Windows 10 no menu', 2,
             R('HKCU:\\Software\\Classes\\CLSID\\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\\InprocServer32', '(default)', '', 'String')) if win11 else None,
        Item('sem-espera-inicio', 'programas da inicialização sem espera', 'O Windows segura os programas da inicialização por alguns '
             'segundos depois do logon; aqui eles abrem na hora.', 'área de trabalho pronta mais cedo', 'em HD, o começo fica mais disputado', 2,
             R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Serialize', 'StartupDelayInMSec', 0)),
        Item('desligar-rapido', 'desligar e fechar travados mais rápido', 'Programas travados são fechados em 1 a 2 s (não 5 a 20 s) '
             'ao desligar, e o Windows espera menos pelos serviços.', 'desliga e reinicia mais rápido',
             'programa que demora para salvar ao fechar pode perder o que não foi salvo', 2,
             RR(R(d, 'AutoEndTasks', '1', 'String'), R(d, 'HungAppTimeout', '1000', 'String'), R(d, 'WaitToKillAppTimeout', '2000', 'String'),
                R(d, 'LowLevelHooksTimeout', '1000', 'String'), R('HKLM:\\SYSTEM\\CurrentControlSet\\Control', 'WaitToKillServiceTimeout', '2000', 'String'))),
        Item('atalhos-rapidos', 'atalhos quebrados sem busca demorada', 'Quando um atalho aponta para algo que sumiu, o Windows não '
             'vasculha o disco e a rede atrás dele, e não pergunta na internet com qual programa abrir um arquivo.', 'sem travadas de vários segundos',
             'atalho de arquivo movido não se conserta sozinho', 3,
             RR(*(R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer', n, 1) for n in
                  ('LinkResolveIgnoreLinkInfo', 'NoResolveSearch', 'NoResolveTrack', 'NoInternetOpenWith')))),
        Item('dump-pequeno', 'cópia de memória pequena em tela azul', 'Em tela azul, o Windows grava só um despejo pequeno, não a memória toda.',
             'GBs de disco e reinício mais rápido depois de travar', 'investigação profunda de telas azuis fica mais difícil', 2,
             R('HKLM:\\SYSTEM\\CurrentControlSet\\Control\\CrashControl', 'CrashDumpEnabled', 3)),
        Item('sacudir', 'sem minimizar tudo ao sacudir a janela', 'Desliga o "Aero Shake".', 'sem minimizar sem querer', 'nenhum', 2,
             R(ADV, 'DisallowShaking', 1)),
        Item('recomendados', 'menu Iniciar sem "Recomendados"', 'Política que esconde a seção de recomendados (arquivos recentes e '
             'sugestões). Vale no Pro, Education e Enterprise.', 'menu limpo e privado', 'perde os arquivos recentes no menu', 3,
             RR(R(f'{HKCU_POL}\\Explorer', 'HideRecommendedSection', 1), R('HKLM:\\SOFTWARE\\Microsoft\\PolicyManager\\current\\device\\Start', 'HideRecommendedSection', 1))) if win11 else None,
        Item('meet-now', 'sem botão "Reunir Agora"', 'Tira o botão do Skype da barra (Windows 10).', 'barra limpa', 'nenhum', 1,
             R('HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer', 'HideSCAMeetNow', 1)) if not win11 else None,
        Item('inicio-win11', 'menu Iniciar com mais fixados', 'No Windows 11, mais espaço para fixados e menos "recomendados".',
             'menu mais útil', 'nenhum', 2, R(ADV, 'Start_Layout', 1)) if win11 else None,
    ]


# ═══════════════════════════════ jogos ═══════════════════════════════

GPU_PS = r'''foreach ($__c in @(Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}' -ErrorAction SilentlyContinue | Where-Object { $_.PSChildName -match '^\d{4}$' })) {
  $__d = [string](Get-ItemProperty -LiteralPath $__c.PSPath -Name DriverDesc -ErrorAction SilentlyContinue).DriverDesc
  if ($__d -match '«fab»') { $__k = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\' + $__c.PSChildName; «reg» }
}'''

# Itens que só servem para jogo: num PC sem jogos instalados, ficam fora de todo modo (placa de vídeo, entrada, rede e agendador).
SO_COM_JOGOS = frozenset({'mmcss', 'mouse', 'teclado', 'gpu-nvidia', 'gpu-amd', 'timer', 'rede-jogos', 'hags'})


@pacote('jogos', 'jogos', 'Modo de Jogo, Game DVR, entrada e latência: vale para qualquer jogo',
        'Ajustes que os otimizadores de jogos usam, com a verdade sobre cada um: alguns ajudam sempre, outros só em casos específicos, '
        'e alguns são quase placebo (está escrito). Desligar segurança do Windows (VBS, Integridade de Memória) não está aqui de propósito: '
        'é troca de segurança, não ajuste.')
def itens_jogos(ctx):
    p = ctx.perfil
    j = joga(p)
    mm = 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile'
    gc = 'HKCU:\\System\\GameConfigStore'
    nagle = r'''foreach ($__i in @(Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces' -ErrorAction SilentlyContinue)) {
  $__v = Get-ItemProperty -LiteralPath $__i.PSPath -ErrorAction SilentlyContinue
  if ($__v.DhcpIPAddress -or ($__v.IPAddress -and [string]$__v.IPAddress -ne '0.0.0.0')) {
    $__k = 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\' + $__i.PSChildName
    Set-Valor $__k 'TcpAckFrequency' 1 | Out-Null; Set-Valor $__k 'TCPNoDelay' 1 | Out-Null
  }
}'''
    itens = [
        Item('modo-jogo', 'Modo de Jogo ligado', 'O Windows segura atualizações e tarefas de fundo enquanto um jogo está aberto.',
             'pequeno: segura atualizações e avisos durante o jogo', 'nenhum', 1,
             RR(R('HKCU:\\Software\\Microsoft\\GameBar', 'AutoGameModeEnabled', 1), R('HKCU:\\Software\\Microsoft\\GameBar', 'AllowAutoGameMode', 1))),
        Item('gamedvr', 'Game DVR e captura em segundo plano', 'Desliga a gravação contínua do Xbox Game Bar (ela grava os últimos '
             'minutos o tempo todo).', 'pequeno em PC forte; mais perceptível em PC fraco', 'Win+Alt+G e gravação pela Game Bar param', 2,
             RR(R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR', 'AppCaptureEnabled', 0), R(gc, 'GameDVR_Enabled', 0),
                R(f'{HKLM_POL}\\GameDVR', 'AllowGameDVR', 0))),
        Item('directx-jogos', 'jogos em janela e VRR otimizados', 'Liga as duas opções de Configurações > Sistema > Tela > Gráficos: '
             '"Otimizações para jogos em janela" (o jogo em janela ou sem borda passa a apresentar quadros como em tela cheia) e '
             '"Otimizações para taxa de atualização variável". Mantém as outras opções que você já tinha ali (como o HDR automático).',
             'menos atraso e mais FPS em jogo em janela ou sem borda (DirectX 10 e 11)', 'nenhum conhecido; desligue nas Configurações se um jogo antigo reclamar', 1,
             r"""$__k = 'HKCU:\Software\Microsoft\DirectX\UserGpuPreferences'
$__a = (Get-ItemProperty -LiteralPath $__k -Name DirectXUserGlobalSettings -ErrorAction SilentlyContinue).DirectXUserGlobalSettings
$__d = [ordered]@{}
foreach ($__p in ("$__a" -split ';')) { if ($__p -match '^\s*([^=]+?)\s*=\s*(.*)$') { $__d[$Matches[1]] = $Matches[2] } }
$__d['SwapEffectUpgradeEnable'] = '1'; $__d['VRROptimizeEnable'] = '1'
$__n = ((@($__d.GetEnumerator() | ForEach-Object { $_.Key + '=' + $_.Value })) -join ';') + ';'
Set-Valor $__k 'DirectXUserGlobalSettings' $__n 'String' 'otimizações de jogos em janela e de VRR' | Out-Null""") if pf(p, 'so.win11') else None,
        Item('mmcss', 'agendador multimídia: menos CPU reservada ao fundo', 'Baixa a reserva de CPU para tarefas de fundo de 20% para 10% '
             '(SystemResponsiveness) e põe a tarefa "Games" do agendador multimídia em categoria High. Só isso: a Microsoft documenta que '
             '"GPU Priority" e "SFIO Priority" não são usados, então eles não são tocados. Só vale para jogos que usam o MMCSS.',
             'pequeno e raramente medido; só em jogo que usa o agendador multimídia', 'tarefas de fundo ficam com menos CPU enquanto joga', 3,
             RR(R(mm, 'SystemResponsiveness', 10), R(mm + '\\Tasks\\Games', 'Scheduling Category', 'High', 'String'))),
        Item('primeiro-plano', 'prioridade do primeiro plano explícita', 'Grava Win32PrioritySeparation = 0x26, o valor que a opção "Programas" '
             'do Windows grava em Desempenho. É o comportamento que o Windows de cliente já usa por padrão (fatias curtas, variáveis, com '
             'reforço ao programa em uso): só muda alguma coisa se outro programa tiver alterado esse valor.',
             'provavelmente nenhum, se o valor nunca foi mexido', 'nenhum', 0,
             R('HKLM:\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl', 'Win32PrioritySeparation', 38)),
        Item('mouse', 'sem aceleração do mouse', 'O ponteiro anda sempre a mesma distância para o mesmo movimento ("precisão aprimorada" desligada).',
             'mira mais consistente', 'em telas grandes o mouse parece mais lento até se acostumar', 2,
             RR(R('HKCU:\\Control Panel\\Mouse', 'MouseSpeed', '0', 'String'), R('HKCU:\\Control Panel\\Mouse', 'MouseThreshold1', '0', 'String'),
                R('HKCU:\\Control Panel\\Mouse', 'MouseThreshold2', '0', 'String'))),
        Item('teclado', 'teclado mais rápido', 'Repetição de tecla no máximo e atraso mínimo antes de repetir.',
             'movimentos e digitação respondem antes', 'quem digita devagar pode repetir letras sem querer', 3,
             RR(R('HKCU:\\Control Panel\\Keyboard', 'KeyboardDelay', '0', 'String'), R('HKCU:\\Control Panel\\Keyboard', 'KeyboardSpeed', '31', 'String'))),
        Item('aderencia', 'sem atalho das Teclas de Aderência', 'Shift 5 vezes (e segurar Shift ou Num Lock) não abre mais o aviso de acessibilidade '
             'no meio do jogo. Os recursos continuam nas Configurações.', 'sem janela surgindo no jogo', 'quem usa esses atalhos de acessibilidade perde', 2 if j else 3,
             RR(R('HKCU:\\Control Panel\\Accessibility\\StickyKeys', 'Flags', '506', 'String'),
                R('HKCU:\\Control Panel\\Accessibility\\Keyboard Response', 'Flags', '122', 'String'),
                R('HKCU:\\Control Panel\\Accessibility\\ToggleKeys', 'Flags', '58', 'String'))),
        Item('gpu-nvidia', 'NVIDIA sem troca dinâmica de estado de energia', 'A placa NVIDIA fica sempre no estado de desempenho (DisableDynamicPstate).',
             'clock da GPU estável, sem quedas de frequência', 'mais calor e consumo o tempo todo, mesmo parado', 3, GPU_PS.replace('«fab»', 'NVIDIA').replace('«reg»', R('$__k', 'DisableDynamicPstate', 1).replace("'$__k'", '$__k'))) if pf(p, 'tem.nvidia') and not pf(p, 'pc.notebook') else None,
        Item('gpu-amd', 'AMD sem ULPS', 'Desliga o modo de ultra baixo consumo das placas AMD, que às vezes causa engasgo ao acordar a placa '
             '(principalmente com duas placas).', 'menos engasgos ao sair do ocioso', 'mais consumo parado', 3,
             GPU_PS.replace('«fab»', 'AMD|Radeon').replace('«reg»', R('$__k', 'EnableULPS', 0).replace("'$__k'", '$__k'))) if pf(p, 'tem.amd') and not pf(p, 'pc.notebook') else None,
        Item('fse', 'sem otimizações de tela inteira', 'Jogos em tela inteira usam o modo exclusivo antigo.',
             'só em alguns jogos antigos com engasgo ou atraso', 'no Windows 11 pode piorar: o modo moderno costuma ser melhor', 0,
             RR(R(gc, 'GameDVR_FSEBehaviorMode', 2), R(gc, 'GameDVR_HonorUserFSEBehaviorMode', 1), R(gc, 'GameDVR_FSEBehavior', 2),
                R(gc, 'GameDVR_DXGIHonorFSEWindowsCompatible', 1))),
        Item('timer', 'resolução do temporizador global', 'No Windows 11, um programa que pede temporizador fino volta a valer para o '
             'sistema todo (GlobalTimerResolutionRequests).', 'pode reduzir latência em alguns jogos', 'mais consumo de energia; efeito varia', 3,
             R('HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\kernel', 'GlobalTimerResolutionRequests', 1)) if pf(p, 'so.win11') else None,
        Item('rede-jogos', 'rede: sem atraso de pacotes (Nagle) e sem limite multimídia', 'Confirmações TCP imediatas e sem o '
             'limitador de rede do agendador multimídia.', 'quase sempre zero ou mínimo (a maioria dos jogos usa UDP)',
             'um pouco mais de pacotes na rede', 3, RR(nagle, R(mm, 'NetworkThrottlingIndex', -1))),
        Item('mpo', 'desligar o Multiplane Overlay (MPO)', 'Correção conhecida para tela piscando, cintilação e engasgos com '
             'algumas placas NVIDIA e vários monitores.', 'só resolve se você tem esse problema', 'sem o problema, não muda nada (ou piora um pouco)', 0,
             R('HKLM:\\SOFTWARE\\Microsoft\\Windows\\Dwm', 'OverlayTestMode', 5)),
        Item('hags', 'agendamento de GPU acelerado por hardware', 'A placa de vídeo cuida da própria fila (HAGS). Precisa de placa e '
             'driver recentes; vale depois de reiniciar.', 'pequeno; necessário para o DLSS 3 (geração de quadros)',
             'em placas antigas pode causar engasgos', 3, r'''$__k = 'HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers'
$__v = (Get-ItemProperty -LiteralPath $__k -Name HwSchMode -ErrorAction SilentlyContinue).HwSchMode
if ($null -eq $__v) { Info 'o Windows nao mostra suporte a este recurso nesta placa ou driver: nao mexi (em placa sem suporte ele pode gerar falhas na imagem)' }
else { Set-Valor $__k 'HwSchMode' 2 'DWord' 'agendamento de GPU por hardware' | Out-Null }'''),
    ]
    if not j:   # sem jogos instalados, o que só serve para jogo não entra em modo nenhum (continua dando para escolher à mão)
        for it in itens:
            if it and it.id in SO_COM_JOGOS:
                it.nivel = 0
    return itens


# ═══════════════════════════════ energia ═══════════════════════════════

PLANO_DESEMPENHO_PS = r'''
Guarda-Energia
$__arq = Join-Path $CASA 'plano-desempenho.txt'
$__lista = (powercfg /list | Out-String)
$__g = $null
if (Test-Path $__arq) { $__s = (Get-Content $__arq -Raw).Trim(); if ($__lista -match [regex]::Escape($__s)) { $__g = $__s } }
if (-not $__g -and $__lista -match 'e9a42b02-d5df-448d-aa00-03f14749eb61') { $__g = 'e9a42b02-d5df-448d-aa00-03f14749eb61' }
if (-not $__g) {
  if ($TESTE) { Plano 'criar e ativar o plano Desempenho Maximo'; return }
  $__d = (powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61 | Out-String)
  if ($__d -match '([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})') { $__g = $Matches[1]; Set-Content -LiteralPath $__arq -Value $__g; Guarda-Desfazer 'plano-criado' ("powercfg /delete " + $__g) }
  else { $__g = '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'; Info 'Desempenho Maximo indisponivel nesta edicao: usando Alto desempenho' }
}
$__atual = (powercfg /getactivescheme | Out-String)
if ($__atual -notmatch [regex]::Escape($__g)) { if ($TESTE) { Plano 'ativar plano de desempenho' } else { powercfg /setactive $__g | Out-Null; $script:MUDOU++ } }
'''

PLANO_FRESCO_PS = r'''
Guarda-Energia
$__eq = '381b4222-f694-41f0-9685-ff5bb260df2e'
if ((powercfg /getactivescheme | Out-String) -notmatch $__eq) { if ($TESTE) { Plano 'ativar o plano Equilibrado' } else { powercfg /setactive $__eq | Out-Null; $script:MUDOU++ } }
$__gs = @([regex]::Matches((powercfg /list | Out-String), '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}') | ForEach-Object { $_.Value } | Select-Object -Unique)
foreach ($__g in $__gs) {
  Set-Energia $__g 'SUB_PROCESSOR' 'PROCTHROTTLEMIN' 5 5 ("CPU minima 5% no plano " + $__g.Substring(0, 8)) | Out-Null
  Set-Energia $__g 'SUB_PROCESSOR' 'PERFBOOSTMODE' 3 3 ("turbo eficiente no plano " + $__g.Substring(0, 8)) | Out-Null
  Set-Energia $__g 'SUB_PCIEXPRESS' 'ASPM' 1 2 ("economia do PCIe ligada no plano " + $__g.Substring(0, 8)) | Out-Null
}
if (-not $TESTE) { powercfg /setactive SCHEME_CURRENT | Out-Null }
'''


@pacote('energia', 'energia', 'plano de energia, turbo, USB, PCIe e hibernação',
        'Duas filosofias, escolha uma: "desempenho" mantém o clock alto (bom para desktop e jogos na tomada) e "fresco" deixa o '
        'processador descansar (bom para notebook que esquenta, ventoinha alta e bateria). Utilitários de fabricante costumam '
        'forçar alto desempenho; o fresco ajusta todos os planos que eles alternam.')
def itens_energia(ctx):
    p = ctx.perfil
    nb = pf(p, 'pc.notebook')
    usb = '2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226'
    return [
        Item('desempenho', 'plano desempenho máximo', 'Ativa o plano Desempenho Máximo (ou Alto desempenho): o processador não reduz '
             'o clock e responde na hora.', 'mais rápido para responder e em jogos', 'mais calor e consumo; em notebook, a bateria dura menos',
             3 if nb else 2, PLANO_DESEMPENHO_PS, grupo='plano', nota='notebook: o plano fresco vem marcado' if nb else ''),
        Item('fresco', 'plano fresco (notebook que esquenta)', 'Plano Equilibrado e, em TODOS os planos: CPU mínima 5%, turbo no modo '
             'eficiente e economia do PCIe ligada. Resolve ventoinha alta mesmo parado.', 'mais frio, silencioso e mais bateria',
             'picos de desempenho um pouco menores', 1 if nb else 0, PLANO_FRESCO_PS, grupo='plano', minutos=4,
             conflita=('cpu-100', 'aspm', 'throttling')),
        Item('disco', 'disco nunca desliga na tomada', 'O disco não "dorme" com o PC ligado na tomada.', 'sem espera para o HD acordar',
             'gasto mínimo de energia', 2, "Guarda-Energia; Set-Energia 'SCHEME_CURRENT' 'SUB_DISK' 'DISKIDLE' 0 $null 'disco sempre ligado na tomada' | Out-Null; if (-not $TESTE) { powercfg /setactive SCHEME_CURRENT | Out-Null }"),
        Item('adaptadores', 'placa de rede sem desligar para economizar', 'Em PC de mesa, o Windows deixa de desligar a placa de rede e o Wi-Fi '
             'para economizar energia (opção "permitir que o computador desligue este dispositivo").', 'evita queda e travadinha de rede',
             'gasto mínimo de energia', 2, 'Set-EconomiaAdaptadores', reaplica=False) if not nb else None,
        Item('usb', 'sem suspensão seletiva de USB na tomada', 'O Windows para de desligar portas USB para economizar.',
             'evita mouse, teclado e headset desconectando ou com atraso', 'gasto mínimo de energia', 3 if nb else 2,
             f"Set-Energia 'SCHEME_CURRENT' {usb.split()[0]} {usb.split()[1]} 0 $null 'USB sem suspensao na tomada' | Out-Null; if (-not $TESTE) {{ powercfg /setactive SCHEME_CURRENT | Out-Null }}"),
        Item('cpu-100', 'clock sempre no máximo na tomada', 'Estado mínimo do processador em 100% na tomada.',
             'zero atraso para subir o clock', 'mais calor e consumo o tempo todo', 0 if nb else 3,
             "Set-Energia 'SCHEME_CURRENT' 'SUB_PROCESSOR' 'PROCTHROTTLEMIN' 100 $null 'CPU minima 100% na tomada' | Out-Null; if (-not $TESTE) { powercfg /setactive SCHEME_CURRENT | Out-Null }"),
        Item('aspm', 'PCIe sem economia na tomada', 'Placa de vídeo e SSD NVMe ficam sempre em potência total (ASPM desligado).',
             'pequeno; evita atrasos ao acordar dispositivos', 'mais consumo', 0 if nb else 3,
             "Set-Energia 'SCHEME_CURRENT' 'SUB_PCIEXPRESS' 'ASPM' 0 $null 'PCIe sem economia na tomada' | Out-Null; if (-not $TESTE) { powercfg /setactive SCHEME_CURRENT | Out-Null }"),
        Item('throttling', 'sem limitação de energia dos processos', 'Desliga o Power Throttling (e o EcoQoS que vem com ele): o '
             'Windows para de jogar programas de fundo nos núcleos lentos.', 'programas de fundo mais rápidos',
             'mais consumo; em notebook, menos bateria', 0 if nb else 3,
             R('HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerThrottling', 'PowerThrottlingOff', 1)),
        Item('rede-energia', 'placa de rede sem economia de energia', 'O Windows não desliga a placa de rede para economizar.',
             'evita quedas de Wi-Fi e atraso ao voltar da suspensão', 'mais consumo', 0 if nb else 3, r'''
$__ad = @(Get-NetAdapter -Physical -ErrorAction SilentlyContinue)
foreach ($a in $__ad) { $pm = Get-NetAdapterPowerManagement -Name $a.Name -ErrorAction SilentlyContinue; if ($pm -and [string]$pm.AllowComputerToTurnOffDevice -eq 'Enabled') { if ($TESTE) { Plano ('sem economia: ' + $a.Name) } else { Guarda-Desfazer ('rede|' + $a.Name) ("Enable-NetAdapterPowerManagement -Name '" + ($a.Name -replace "['\u2018\u2019\u201a\u201b]", '$0$0') + "' -ErrorAction SilentlyContinue"); Disable-NetAdapterPowerManagement -Name $a.Name -NoRestart -ErrorAction SilentlyContinue; $script:MUDOU++ } } }'''),
        Item('inicio-rapido', 'inicialização rápida garantida', 'Ligar depois de desligar fica muito mais rápido. Em HD faz diferença grande.',
             'boot mais curto', 'é preciso "Reiniciar" (não "Desligar") para aplicar algumas atualizações', 1, r'''
$__h = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Power' -ErrorAction SilentlyContinue).HibernateEnabled
if ($__h -eq 0) { if ($TESTE) { Plano 'ligar hibernacao reduzida' } else { Guarda-Desfazer 'hib' 'powercfg /h off'; powercfg /h on | Out-Null; powercfg /h /type reduced | Out-Null; $script:MUDOU++ } }
Set-Valor 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Power' 'HiberbootEnabled' 1 | Out-Null''') if eh_hd(p) else None,
        Item('hibernacao', 'hibernação desligada', 'Apaga o hiberfil.sys (do tamanho de boa parte da RAM). Em SSD o boot já é rápido.',
             'alguns GB de espaço', 'sem hibernar e sem inicialização rápida', 3 if not nb else 0, r'''
$__h = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Power' -ErrorAction SilentlyContinue).HibernateEnabled
if ($__h -ne 0) { if ($TESTE) { Plano 'desligar hibernacao (powercfg /h off)' } else { Guarda-Desfazer 'hib' 'powercfg /h on'; powercfg /h off | Out-Null; $script:MUDOU++ } }''',
             nota='notebook: hibernar salva o trabalho quando a bateria acaba' if nb else '') if eh_ssd(p) else None,
    ]


# ═══════════════════════════════ disco ═══════════════════════════════

@pacote('disco', 'disco e memória', 'menos escrita em segundo plano, boot e abertura de programas',
        'Ajustes do pacote de disco do cofre: varreduras do Defender mais leves, menos tarefas que leem o disco à toa, NTFS mais leve, '
        'Sensor de Armazenamento e otimização da unidade (desfragmenta HD; em SSD só faz TRIM). SysMain e Prefetch ficam ligados: '
        'em HD eles aceleram a abertura de programas (decisão registrada no cofre).')
def itens_disco(ctx):
    p = ctx.perfil
    hd = eh_hd(p)
    ram = pf(p, 'ram.total', 8) or 8
    tarefas = ['\\Microsoft\\Windows\\Maintenance\\WinSAT', '\\Microsoft\\Windows\\Autochk\\Proxy',
               '\\Microsoft\\Windows\\Application Experience\\StartupAppTask', '\\Microsoft\\Windows\\SpacePort\\SpaceAgentTask',
               '\\Microsoft\\Windows\\Work Folders\\Work Folders Maintenance Work']
    if not pf(p, 'tem.historico_arquivos'):
        tarefas.append('\\Microsoft\\Windows\\FileHistory\\File History (maintenance mode)')
    ss = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\StorageSense\\Parameters\\StoragePolicy'
    od_ns = ['HKLM:\\SOFTWARE\\Classes\\CLSID\\{018D5C66-4533-4307-9B53-224DE2ED1FE6}',
             'HKLM:\\SOFTWARE\\WOW6432Node\\Classes\\CLSID\\{018D5C66-4533-4307-9B53-224DE2ED1FE6}']

    def otimiza_unidade(ctx, it, pr, teste):
        if teste:
            ctx.t.item('○', 'azul', 'defrag C: /O' + (' (desfragmentar)' if hd else ' (TRIM)'), recuo=4, cor_nome='sub')
            return 1, 0
        cod, _ = roda_exe(['defrag.exe', 'C:', '/O', '/U'], 120 if hd else 15, pr, ctx.mult)
        if cod == -1:
            ctx.t.aviso('otimização da unidade passou do tempo e foi encerrada.')
            return 0, 1
        ctx.t.item('✓', 'verde', ('desfragmentação' if hd else 'TRIM') + f' concluído (código {cod})', recuo=4, cor_nome='sub')
        return 1, 0

    def boot_hd(ctx, it, pr, teste):
        if teste:
            ctx.t.item('○', 'azul', 'processar tarefas ociosas e defrag C: /B', recuo=4, cor_nome='sub')
            return 1, 0
        pr.atual = 'processando tarefas ociosas'
        roda_exe(['rundll32.exe', 'advapi32.dll,ProcessIdleTasks'], 20, pr, ctx.mult)
        cod, _ = roda_exe(['defrag.exe', 'C:', '/B'], 30, pr, ctx.mult)
        ctx.t.item('✓', 'verde', f'arquivos do boot reorganizados (código {cod})', recuo=4, cor_nome='sub')
        return 1, 0

    return [
        Item('defender-leve', 'varreduras do Defender mais leves', 'Varreduras agendadas com prioridade baixa e no máximo 20% de CPU. '
             'A proteção em tempo real não muda.', 'o PC não trava durante a varredura semanal', 'a varredura completa demora mais',
             1 if hd else 2, r'''
$__m = Get-MpPreference -ErrorAction Stop
if ($__m.ScanAvgCPULoadFactor -ne 20 -or -not $__m.EnableLowCpuPriority) {
  if ($TESTE) { Plano 'Defender: varredura com 20% de CPU e prioridade baixa' }
  else { Guarda-Desfazer 'defender' ("Set-MpPreference -ScanAvgCPULoadFactor {0} -EnableLowCpuPriority `${1}" -f $__m.ScanAvgCPULoadFactor, ([string]$__m.EnableLowCpuPriority).ToLower()); Set-MpPreference -ScanAvgCPULoadFactor 20 -EnableLowCpuPriority $true; $script:MUDOU++ }
}'''),
        Item('p2p', 'Windows Update sem compartilhar com outros PCs', 'Desliga o envio de pedaços de atualizações para outros '
             'computadores (Otimização de Entrega P2P).', 'menos upload e escrita em disco', 'nenhum', 1,
             R(f'{HKLM_POL}\\DeliveryOptimization', 'DODownloadMode', 0)),
        Item('tarefas', 'tarefas de manutenção inúteis', 'WinSAT (nota de desempenho), Autochk Proxy, StartupAppTask, Storage Spaces, '
             'Pastas de Trabalho' + ('' if pf(p, 'tem.historico_arquivos') else ' e Histórico de Arquivos') + '.',
             'menos leitura de disco ociosa', 'nenhum', 2, TAREFAS(tarefas)),
        Item('lastaccess', 'NTFS sem gravar "último acesso"', 'O Windows para de gravar a data de cada leitura de arquivo.',
             'menos escrita em disco', 'programas de backup que dependem dessa data (raros) se confundem', 2, r'''
$__q = (fsutil behavior query disablelastaccess | Out-String)
if ($__q -match '=\s*(\d)') { $__v = $Matches[1] } else { $__v = '2' }
if ($__v -ne '1' -and $__v -ne '3') { if ($TESTE) { Plano 'desligar gravacao de ultimo acesso' } else { Guarda-Desfazer 'lastaccess' ('fsutil behavior set disablelastaccess ' + $__v + ' | Out-Null'); fsutil behavior set disablelastaccess 1 | Out-Null; $script:MUDOU++ } }'''),
        Item('ntfs', 'NTFS sem nomes 8.3 e com mais cache', 'Arquivos novos não ganham nome curto antigo (ARQUIV~1) e o NTFS usa mais '
             'memória para metadados' + (' (há RAM sobrando)' if ram >= 8 else '') + '.', 'pastas grandes mais rápidas',
             'programas de DOS muito antigos podem não achar arquivos novos', 3, r'''
$__a = (fsutil behavior query disable8dot3 | Out-String); $__b = (fsutil behavior query memoryusage | Out-String)
$__v1 = '2'; if ($__a -match 'NtfsDisable8dot3NameCreation\s*=\s*(\d)') { $__v1 = $Matches[1] }
$__v2 = '1'; if ($__b -match '=\s*(\d)') { $__v2 = $Matches[1] }
if ($__v1 -ne '1') { if ($TESTE) { Plano 'sem nomes 8.3' } else { Guarda-Desfazer '8dot3' ('fsutil behavior set disable8dot3 ' + $__v1 + ' | Out-Null'); fsutil behavior set disable8dot3 1 | Out-Null; $script:MUDOU++ } }
if ($__v2 -ne '2' -and «ram» -ge 8) { if ($TESTE) { Plano 'mais cache para o NTFS' } else { Guarda-Desfazer 'memusage' ('fsutil behavior set memoryusage ' + $__v2 + ' | Out-Null'); fsutil behavior set memoryusage 2 | Out-Null; $script:MUDOU++ } }'''.replace('«ram»', str(int(ram)))),
        *([Item('trim', 'TRIM ligado no SSD', 'O TRIM é o aviso que o Windows dá ao SSD sobre os blocos que ficaram livres. Vem ligado; '
                'alguns "otimizadores" e clonagens de disco desligam.', 'o SSD continua rápido para gravar e dura mais', 'nenhum', 1, r'''
$__q = (fsutil behavior query DisableDeleteNotify | Out-String)
if ($__q -match '(?m)^\s*(?:NTFS\s+)?DisableDeleteNotify\s*=\s*1') { if ($TESTE) { Plano 'ligar o TRIM do SSD' } else { Guarda-Desfazer 'trim' 'fsutil behavior set DisableDeleteNotify 1 | Out-Null'; fsutil behavior set DisableDeleteNotify 0 | Out-Null; $script:MUDOU++ } }''',
                nota=('o raio-x viu o TRIM desligado neste PC' if pf(p, 'disco.trim') is False else ''))] if not hd else []),
        Item('sensor', 'Sensor de Armazenamento mensal', 'O próprio Windows limpa temporários todo mês, sem tocar na Lixeira nem em Downloads.',
             'disco não enche sozinho', 'nenhum', 1, RR(R(ss, '01', 1), R(ss, '04', 1), R(ss, '2048', 30), R(ss, '08', 0), R(ss, '32', 0))),
        Item('sysmain', 'SysMain e Prefetch ligados', 'Pré-carregam os programas que você mais usa. Em HD aceleram a abertura; há '
             'guias que mandam desligar, mas isso só serve como teste de disco a 100%.', 'programas abrem mais rápido',
             'nenhum', 1, RR(SVC(['SysMain'], 'auto', parar=False), "if (-not $TESTE) { & sc.exe start SysMain 2>$null | Out-Null }",
                             R('HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters', 'EnablePrefetcher', 3))) if hd else None,
        Item('atrasados', 'serviços de terceiros com início atrasado', 'Office (ClickToRun) e Adobe sobem só depois que o Windows '
             'terminou de carregar.', 'boot e área de trabalho prontos mais cedo', 'esses serviços demoram ~2 min para subir', 2,
             "foreach ($__s in 'ClickToRunSvc','AdobeUpdateService','AGSService') { $__m = Get-ModoServico $__s; if ($__m -and $__m.modo -eq 'auto') { Set-Servico $__s 'delayed-auto' | Out-Null } }"),
        Item('boot-hd', 'reorganizar os arquivos do boot no HD', 'O Windows junta no HD os arquivos do boot e dos programas mais usados.',
             'boot e abertura mais rápidos em HD', 'demora até 30 min', 2, py=boot_hd, recorrente=True) if hd else None,
        Item('unidade', 'otimizar a unidade', 'Desfragmenta se for HD; se for SSD, só manda o TRIM (nunca desfragmenta SSD).',
             'disco mais rápido' + (' (HD fragmentado é muito lento)' if hd else ''), 'demora' + (' (até 2 h em HD)' if hd else ' pouco'),
             1, py=otimiza_unidade, recorrente=True),
        Item('pagefile', 'memória virtual de volta ao automático', 'O arquivo de paginação está desligado ou fixo. Ninguém recomenda '
             'desligar: programas fecham sozinhos sem ele.', 'estabilidade', 'nenhum', 1, r'''
$__c = Get-CimInstance Win32_ComputerSystem
if (-not $__c.AutomaticManagedPagefile) { if ($TESTE) { Plano 'memoria virtual automatica' } else { Guarda-Desfazer 'pagefile' '$c = Get-CimInstance Win32_ComputerSystem; Set-CimInstance -InputObject $c -Property @{ AutomaticManagedPagefile = $false }'; Set-CimInstance -InputObject $__c -Property @{ AutomaticManagedPagefile = $true }; $script:MUDOU++ } }''')
        if not pf(p, 'memoria.pagefile_auto', True) else None,
        Item('compressao', 'compressão de memória ligada', f'Com {gb(ram, 0)}, comprimir a memória evita usar o disco.', 'menos travadas por falta de RAM',
             'nenhum', 1, "if ($TESTE) { Plano 'ligar compressao de memoria' } else { Guarda-Desfazer 'mmc' 'Disable-MMAgent -MemoryCompression'; Enable-MMAgent -MemoryCompression; $script:MUDOU++ }")
        if pf(p, 'memoria.compressao') is False and ram < 16 else None,
        Item('sem-compressao', 'compressão de memória desligada', f'Com {gb(ram, 0)} de RAM a compressão quase nunca entra em ação: ela só trabalha '
             'quando a memória aperta, então desligar não tem ganho medido.',
             'nenhum medido', 'se a RAM encher, usa mais o disco', 0,
             "if ((Get-MMAgent).MemoryCompression) { if ($TESTE) { Plano 'desligar compressao de memoria' } else { Guarda-Desfazer 'mmc' 'Enable-MMAgent -MemoryCompression'; Disable-MMAgent -MemoryCompression; $script:MUDOU++ } }")
        if ram >= 32 else None,
        Item('onedrive', 'OneDrive bloqueado', 'Política que impede o OneDrive de rodar e tira ele do painel do Explorador. '
             'Sua pasta do OneDrive está vazia.', 'menos um programa sincronizando', 'não sincroniza mais nada com o OneDrive', 2,
             RR(R(f'{HKLM_POL}\\OneDrive', 'DisableFileSyncNGSC', 1), *(f"if (Test-Path {psq(k)}) {{ {R(k, 'System.IsPinnedToNameSpaceTree', 0)} }}" for k in od_ns)))
        if pf(p, 'tem.onedrive') and not pf(p, 'tem.onedrive_usado') else None,
    ]


# ═══════════════════════════════ reparar ═══════════════════════════════

def _py_reparo(rotulo, cmd, minutos, chave=None, pos=None):
    def f(ctx, it, pr, teste):
        if teste:
            ctx.t.item('○', 'azul', ' '.join(cmd), recuo=4, cor_nome='sub')
            return 1, 0
        if chave == 'sfc' and not exige_espaco(ctx.t, 'sfc', rotulo):
            return 0, 1
        if chave:
            ult = estado().get('reparo_' + chave)
            try:
                if ult and (datetime.now() - datetime.fromisoformat(ult)).total_seconds() < 86400:
                    ctx.t.nota(f'    {rotulo}: já feito nas últimas 24 h; pulei.')
                    return 0, 0
            except ValueError:
                pass
        cod, txt = roda_exe(cmd, minutos, pr, ctx.mult, saida_arq=pasta('logs') / f'{chave or rotulo}.txt')
        if cod == -1:
            ctx.t.aviso(f'{rotulo}: passou do limite e foi encerrado.')
            return 0, 1
        if chave:
            marca_estado('reparo_' + chave, agora_iso())
        msg = pos(ctx, cod, txt) if pos else None
        ctx.t.item('✓' if cod in (0, 3010) else '!', 'verde' if cod in (0, 3010) else 'amarelo',
                   msg or f'{rotulo}: código {cod}', recuo=4, cor_nome='sub')
        return 1, 0 if cod in (0, 3010) else 1
    return f


def _pos_sfc(ctx, cod, txt):
    t = txt.lower()
    if re.search(r'did not find any integrity|não encontrou nenhuma viola|nao encontrou nenhuma viola', t):
        return 'SFC: nenhum arquivo do sistema corrompido'
    if re.search(r'successfully repaired|reparou com', t):
        return 'SFC: encontrou e reparou arquivos corrompidos'
    if re.search(r'unable to fix|não pôde reparar|nao pode reparar', t):
        return 'SFC: há arquivos que não consegui reparar (veja a pasta relatorios)'
    return f'SFC: código {cod}'


def _pos_chkdsk(ctx, cod, txt):
    if cod not in (0,):
        subprocess.run('echo Y| chkdsk C: /f', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return 'chkdsk: encontrou problemas; o reparo completo vai rodar no próximo reinício'
    return 'chkdsk: nenhum problema no disco'


def _pos_wmi(ctx, cod, txt):
    if re.search(r'inconsistent|inconsistente', txt, re.I):
        roda_exe(['winmgmt', '/salvagerepository'], 5)
        return 'WMI: repositório inconsistente, recuperado'
    return 'WMI: repositório em ordem'


@pacote('reparar', 'reparar', 'arquivos do sistema, disco, WMI, rede e Windows Update',
        'Ferramentas oficiais de reparo. DISM conserta a imagem do Windows, SFC confere os arquivos do sistema, chkdsk lê o disco. '
        'DISM e SFC feitos nas últimas 24 h não são refeitos. Os itens opcionais são para quando algo está quebrado.')
def itens_reparar(ctx):
    return [
        Item('dism', 'reparar a imagem do Windows (DISM)', 'Baixa do Windows Update e troca componentes corrompidos.',
             'conserta erros de atualização e travamentos', 'demora (até 1 h em HD)', 1,
             py=_py_reparo('DISM', ['DISM.exe', '/Online', '/Cleanup-Image', '/RestoreHealth'], 90, 'dism')),
        Item('sfc', 'conferir arquivos do sistema (SFC)', 'Confere cada arquivo do Windows e repõe os corrompidos.',
             'conserta erros estranhos e telas azuis por arquivo corrompido', 'demora (até 45 min)', 1,
             py=_py_reparo('SFC', ['sfc.exe', '/scannow'], 45, 'sfc', _pos_sfc)),
        Item('chkdsk', 'verificar o disco (chkdsk)', 'Lê a estrutura do disco sem travar o uso. Se achar erro, agenda o reparo completo '
             'para o próximo reinício.', 'evita perda de arquivos', 'nenhum', 1,
             py=_py_reparo('chkdsk', ['chkdsk.exe', 'C:', '/scan'], 20, None, _pos_chkdsk)),
        Item('wmi', 'conferir o WMI', 'O WMI é o que programas e o próprio Windows usam para ler o hardware. Quebrado, causa CPU alta e erros.',
             'conserta CPU alta do WmiPrvSE por repositório corrompido', 'nenhum', 2,
             py=_py_reparo('WMI', ['winmgmt', '/verifyrepository'], 5, None, _pos_wmi)),
        Item('dns', 'limpar o cache de DNS', 'Esquece endereços de sites guardados.', 'conserta site que mudou de endereço e não abre',
             'nenhum', 1, "if ($TESTE) { Plano 'ipconfig /flushdns' } else { ipconfig /flushdns | Out-Null; Feito 'cache de DNS limpo' }", reverte=False),
        Item('rede-reset', 'restaurar a pilha de rede', 'Winsock e TCP/IP de volta ao padrão (netsh winsock reset e int ip reset).',
             'conserta internet que não funciona por configuração quebrada', 'precisa reiniciar; VPNs e alguns antivírus podem precisar ser reinstalados', 0,
             "if ($TESTE) { Plano 'netsh winsock reset; netsh int ip reset' } else { netsh winsock reset | Out-Null; netsh int ip reset | Out-Null; Feito 'rede restaurada: reinicie o PC' }", reverte=False),
        Item('wu-reset', 'restaurar o Windows Update', 'Para os serviços, renomeia as pastas SoftwareDistribution e catroot2 e liga de novo.',
             'conserta Windows Update preso em erro', 'o histórico de atualizações aparece vazio', 0, r'''
if ($TESTE) { Plano 'restaurar componentes do Windows Update' }
else {
  foreach ($__s in 'wuauserv','bits','cryptsvc','msiserver') { & sc.exe stop $__s 2>$null | Out-Null }
  Start-Sleep 4
  $__c = Get-Date -Format 'yyyyMMddHHmmss'
  Rename-Item "$env:WINDIR\SoftwareDistribution" "SoftwareDistribution.old-$__c" -ErrorAction SilentlyContinue
  Rename-Item "$env:WINDIR\System32\catroot2" "catroot2.old-$__c" -ErrorAction SilentlyContinue
  foreach ($__s in 'cryptsvc','bits','wuauserv') { & sc.exe start $__s 2>$null | Out-Null }
  Feito 'Windows Update restaurado'
}''', reverte=False),
        Item('loja', 'consertar a Loja', 'Limpa o cache da Microsoft Store (wsreset).', 'conserta Loja que não abre ou não baixa', 'nenhum', 0,
             "if ($TESTE) { Plano 'wsreset' } else { $r = Roda 'wsreset.exe' '' 3; Get-Process WinStore.App -ErrorAction SilentlyContinue | Stop-Process -Force; Feito 'cache da Loja limpo' }", reverte=False),
        Item('icones', 'reconstruir o cache de ícones', 'Apaga o cache de ícones e o Windows recria.', 'conserta ícones brancos ou trocados',
             'o Explorador reinicia', 0, r'''
if ($TESTE) { Plano 'reconstruir cache de icones' }
else { Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue; Start-Sleep 2
  Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Windows\Explorer" -Filter 'iconcache_*.db' -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
  Remove-Item "$env:LOCALAPPDATA\IconCache.db" -Force -ErrorAction SilentlyContinue
  Start-Process explorer.exe; Feito 'cache de icones refeito' }''', reverte=False),
        Item('menu', 'registrar de novo o menu Iniciar e a busca', 'Registra de novo os componentes do menu Iniciar, da busca e da barra.',
             'conserta menu Iniciar que não abre', 'nenhum', 0, r'''
foreach ($__n in 'Microsoft.Windows.ShellExperienceHost','Microsoft.Windows.StartMenuExperienceHost','MicrosoftWindows.Client.CBS','Microsoft.Windows.Search') {
  foreach ($x in @(Get-AppxPackage -AllUsers -Name $__n -ErrorAction SilentlyContinue)) { if ($TESTE) { Plano ('registrar ' + $__n) } else { try { Add-AppxPackage -DisableDevelopmentMode -Register (Join-Path $x.InstallLocation 'AppxManifest.xml') -ErrorAction Stop; Feito ('registrado: ' + $__n) } catch { Aviso ($__n + ': ' + $_.Exception.Message) } } }
}''', reverte=False),
    ]


# ═══════════════════════════════ atualizar ═══════════════════════════════

WU_PS = r'''
$__tipo = «tipo»
$__s = New-Object -ComObject Microsoft.Update.Session
Vivo 'procurando atualizacoes'
$__r = $__s.CreateUpdateSearcher().Search("IsInstalled=0 and IsHidden=0 and Type='$__tipo'").Updates
if ($__r.Count -eq 0) { Diz 'nada' 'nada para atualizar'; return }
$__l = New-Object -ComObject Microsoft.Update.UpdateColl
foreach ($u in $__r) { if ($TESTE) { Plano $u.Title; continue }; if (-not $u.EulaAccepted) { $u.AcceptEula() }; [void]$__l.Add($u) }
if ($TESTE) { return }
Vivo ("baixando {0} atualizacoes" -f $__l.Count)
$__d = $__s.CreateUpdateDownloader(); $__d.Updates = $__l; [void]$__d.Download()
Vivo 'instalando'
$__i = $__s.CreateUpdateInstaller(); $__i.Updates = $__l; $__x = $__i.Install()
for ($k = 0; $k -lt $__l.Count; $k++) { $rr = $__x.GetUpdateResult($k).ResultCode; if ($rr -eq 2 -or $rr -eq 3) { Feito $__l.Item($k).Title } else { Aviso ('falhou: ' + $__l.Item($k).Title) } }
if ($__x.RebootRequired) { Info 'o Windows pede reinicio para concluir' }
'''


def _py_winget(ctx, it, pr, teste):
    if teste:
        cod, txt = roda_exe(['winget', 'upgrade', '--accept-source-agreements', '--disable-interactivity'], 3, pr)
        n = len([l for l in txt.splitlines() if re.search(r'\s\d+[\d.]*\s+\d+[\d.]*\s+winget', l)])
        ctx.t.item('○', 'azul', f'winget: {n} programas com versão nova', recuo=4, cor_nome='sub')
        return 1, 0
    cod, txt = roda_exe(['winget', 'upgrade', '--all', '--silent', '--accept-source-agreements', '--accept-package-agreements',
                         '--disable-interactivity', '--include-unknown'], 60, pr, ctx.mult)
    ok = len(re.findall(r'Successfully installed|Instalado com êxito|instalado com sucesso', txt, re.I))
    ctx.t.item('✓' if cod in (0, -1978335189) else '!', 'verde' if cod == 0 else 'amarelo',
               f'winget: {ok} programas atualizados' + ('' if cod == 0 else f' (código {cod}; alguns podem ter falhado)'), recuo=4, cor_nome='sub')
    return 1, 0 if cod == 0 else 1


@pacote('atualizar', 'atualizar', 'Windows Update, drivers, Defender, programas e apps da Loja',
        'Atualiza pelo próprio Windows Update (sem desligar nada dele) e pelo winget. Só versões estáveis.', reversivel=False)
def itens_atualizar(ctx):
    return [
        Item('defender', 'definições do Defender', 'Baixa as definições de vírus mais novas.', 'proteção em dia', 'nenhum', 1,
             "if ($TESTE) { Plano 'Update-MpSignature' } else { try { Update-MpSignature -ErrorAction Stop; Feito 'Defender atualizado' } catch { Aviso ('Defender: ' + $_.Exception.Message) } }",
             minutos=10, reverte=False),
        Item('windows', 'atualizações do Windows', 'Procura, baixa e instala as atualizações pendentes do Windows Update.',
             'segurança e correções', 'demora; pode pedir reinício', 1, ps_monta(WU_PS, tipo="'Software'"), minutos=120, sozinho=True, reverte=False),
        Item('drivers', 'drivers pelo Windows Update', 'Drivers que o Windows Update oferece para este PC.',
             'drivers mais novos e certificados', 'raramente um driver novo traz problema (dá para voltar no Gerenciador de Dispositivos)', 2,
             ps_monta(WU_PS, tipo="'Driver'"), minutos=60, sozinho=True, reverte=False),
        Item('winget', 'programas pelo winget', 'Atualiza os programas instalados que o winget conhece.', 'programas em dia e mais seguros',
             'alguns programas mudam de versão principal', 2, py=_py_winget, reverte=False) if pf(ctx.perfil, 'tem.winget', True) else None,
        Item('loja', 'apps da Loja', 'Pede à Microsoft Store para atualizar os apps.', 'apps em dia', 'nenhum', 2, r'''
if ($TESTE) { Plano 'atualizar apps da Loja' } else { try { Get-CimInstance -Namespace 'root\cimv2\mdm\dmmap' -ClassName 'MDM_EnterpriseModernAppManagement_AppManagement01' -ErrorAction Stop | Invoke-CimMethod -MethodName UpdateScanMethod -ErrorAction Stop | Out-Null; Feito 'Loja verificando atualizacoes' } catch { Aviso 'a Loja nao aceitou o pedido; abra a Loja > Biblioteca' } }''',
             reverte=False),
    ]


# ═══════════════════════════════ interface ═══════════════════════════════

@pacote('interface', 'área de trabalho e menu', 'Edge escondido, área de trabalho limpa, Destaque do Windows',
        'Arrumação visual. Atalhos tirados da área de trabalho vão para o backup e voltam com o desfazer.')
def itens_interface(ctx):
    p = ctx.perfil
    icones = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\HideDesktopIcons\\NewStartPanel'
    edge_lnk = r'''foreach ($__l in @(Get-ChildItem ([Environment]::GetFolderPath('Desktop')), "$env:PUBLIC\Desktop" -Filter 'Microsoft Edge*.lnk' -Force -ErrorAction SilentlyContinue)) { Guarda-Arquivo $__l.FullName | Out-Null }'''
    limpa = r'''foreach ($__d in @([Environment]::GetFolderPath('Desktop'), "$env:PUBLIC\Desktop")) { foreach ($__l in @(Get-ChildItem -LiteralPath $__d -Force -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in '.lnk','.url' })) { Guarda-Arquivo $__l.FullName | Out-Null } }'''
    return [
        Item('edge-atalhos', 'atalhos do Edge fora da área de trabalho', 'Tira os atalhos do Edge que o Windows recoloca.',
             'área de trabalho limpa', 'nenhum (o Edge continua no menu)', 2, edge_lnk) if pf(p, 'tem.edge', True) else None,
        Item('destaque', 'sem "Saiba mais sobre esta foto"', 'Esconde o ícone do Windows Destaque e desliga o recurso na área de trabalho.',
             'área de trabalho limpa', 'sem papel de parede do Bing trocando', 1,
             RR(R(icones, '{2cc5ca98-6485-489a-920e-b3e88a6ccce3}', 1), R(f'{HKCU_POL}\\CloudContent', 'DisableSpotlightCollectionOnDesktop', 1))),
        Item('este-pc', 'ícone "Este Computador" na área de trabalho', 'Mostra o atalho para os discos.', 'acesso rápido', 'nenhum', 2,
             R(icones, '{20D04FE0-3AEA-1069-A2D8-08002B30309D}', 0)),
        Item('limpa', 'área de trabalho só com a Lixeira', 'Todos os atalhos (.lnk e .url) da área de trabalho vão para o backup. '
             'Arquivos e pastas seus ficam.', 'visual limpo', 'você abre programas pelo menu Iniciar', 3, limpa, recorrente=True),
    ]


# ═══════════════════════════════ navegador ═══════════════════════════════

def _brave_pol():
    b = 'HKLM:\\SOFTWARE\\Policies\\BraveSoftware\\Brave'
    return RR(R(b, 'BraveRewardsDisabled', 1), R(b, 'BraveWalletDisabled', 1), R(b, 'BraveVPNDisabled', 1), R(b, 'BraveAIChatEnabled', 0),
              R(b, 'BackgroundModeEnabled', 0), R(b, 'HighEfficiencyModeEnabled', 1), R(b, 'MetricsReportingEnabled', 0),
              R(b, 'BraveNewsDisabled', 1), R(b, 'TorDisabled', 1))


@pacote('navegador', 'navegador', 'navegadores mais leves e Brave enxuto',
        'Políticas oficiais de cada navegador: sem rodar em segundo plano, economia de memória ligada, sem métricas. O navegador '
        'mostra "Gerenciado pela sua organização". O Brave foi o escolhido no cofre para PC fraco.')
def itens_navegador(ctx):
    p = ctx.perfil
    tem = p.get('tem') or {}
    ch = 'HKLM:\\SOFTWARE\\Policies\\Google\\Chrome'

    def instala_brave(ctx, it, pr, teste):
        if teste:
            ctx.t.item('○', 'azul', 'winget install Brave.Brave', recuo=4, cor_nome='sub')
            return 1, 0
        cod, _ = roda_exe(['winget', 'install', '--id', 'Brave.Brave', '--exact', '--silent', '--accept-source-agreements',
                           '--accept-package-agreements', '--disable-interactivity'], 15, pr, ctx.mult)
        ctx.t.item('✓' if cod == 0 else '!', 'verde' if cod == 0 else 'amarelo', 'Brave instalado' if cod == 0 else f'Brave: código {cod} (baixe em brave.com)', recuo=4, cor_nome='sub')
        return (1, 0) if cod == 0 else (0, 1)

    return [
        Item('brave', 'instalar o Brave', 'Navegador leve (base do Chrome, bloqueador de anúncios embutido), pelo winget.',
             'menos RAM que Chrome e Edge', 'mais um programa', 2 if config('navegador') == 'brave' else 0, py=instala_brave, reverte=False)
        if not tem.get('brave') else None,
        Item('brave-pol', 'Brave enxuto', 'Sem Rewards, Wallet, VPN, IA, notícias, Tor e segundo plano; economia de memória ligada. '
             'As atualizações de segurança continuam.', 'Brave mais leve', 'perde esses recursos do Brave', 1, _brave_pol()),
        Item('chrome', 'Chrome enxuto', 'Sem continuar aberto depois de fechado, economia de memória ligada, sem métricas e sem modelo de IA local.',
             'menos RAM', 'aparece "Gerenciado pela organização"', 1,
             RR(R(ch, 'BackgroundModeEnabled', 0), R(ch, 'HighEfficiencyModeEnabled', 1), R(ch, 'MetricsReportingEnabled', 0),
                R(ch, 'GenAILocalFoundationalModelSettings', 1), R(ch, 'ChromeCleanupReportingEnabled', 0), R(ch, 'UserFeedbackAllowed', 0),
                R(ch, 'DeviceMetricsReportingEnabled', 0))) if tem.get('chrome') else None,
        Item('edge', 'Edge enxuto', 'Sem pré-carregar, sem segundo plano, sem barra lateral, sem assistente de compras, sem recomendações '
             'e sem primeira execução.', 'menos RAM e propaganda', 'aparece "Gerenciado pela organização"', 1,
             RR(R(EDGE_POL, 'StartupBoostEnabled', 0), R(EDGE_POL, 'BackgroundModeEnabled', 0), R(EDGE_POL, 'HubsSidebarEnabled', 0),
                R(EDGE_POL, 'EdgeShoppingAssistantEnabled', 0), R(EDGE_POL, 'ShowRecommendationsEnabled', 0),
                R(EDGE_POL, 'PersonalizationReportingEnabled', 0), R(EDGE_POL, 'HideFirstRunExperience', 1),
                R(EDGE_POL, 'SpotlightExperiencesAndRecommendationsEnabled', 0), R(EDGE_POL, 'DiagnosticData', 0),
                R(EDGE_POL, 'MetricsReportingEnabled', 0), R(EDGE_POL, 'UserFeedbackAllowed', 0), R(EDGE_POL, 'Edge3PSerpTelemetryEnabled', 0))) if tem.get('edge', True) else None,
    ]
