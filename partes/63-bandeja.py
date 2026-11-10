# ─────────────── ícone simples na bandeja (reserva de quem roda só o katharos.py, sem o Katharos.exe) ───────────────
# O acompanhamento completo é o Katharos.exe (63-segundoplano.py). Sem ele, este ícone em PowerShell mostra a última amostra que a tarefa de 15 min gravou
# (ultima-amostra.json) e mostra no menu. Clicar abre o menu com os números de agora e atalhos. Roda como o seu usuário, sem administrador,
# num PowerShell sem janela; um só por sessão. Fechar o ícone não desliga a coleta.
TAREFA_BANDEJA = 'Katharos - ícone'
ULTIMA_AMOSTRA = 'ultima-amostra.json'
PAUSA_ARQ = 'leitura-pausada-ate.txt'

BANDEJA_PS = r'''
$ErrorActionPreference = 'SilentlyContinue'
$__novo = $false
$__mutex = New-Object System.Threading.Mutex($true, 'Local\KatharosBandeja', [ref]$__novo)
if (-not $__novo) { return }
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
$VERSAO = «versao»; $PS1 = «ps1»; $PY = «py»; $PYW = «pyw»; $KPY = «kpy»; $CASA = «casa»
$ULTIMA = Join-Path $CASA «ultima»; $PAUSA = Join-Path $CASA «pausa»

function Icone {
    $b = New-Object System.Drawing.Bitmap 32, 32
    $g = [System.Drawing.Graphics]::FromImage($b)
    $g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAliasGridFit'
    $g.Clear([System.Drawing.Color]::Transparent)
    $g.FillRectangle((New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 226, 168, 92))), 3, 3, 26, 26)
    $f = New-Object System.Drawing.Font('Consolas', 20, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $fmt = New-Object System.Drawing.StringFormat; $fmt.Alignment = 'Center'; $fmt.LineAlignment = 'Center'
    $g.DrawString('k', $f, (New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 22, 17, 10))), (New-Object System.Drawing.RectangleF(0, -1, 32, 32)), $fmt)
    $g.Dispose()
    [System.Drawing.Icon]::FromHandle($b.GetHicon())
}
function Abre([string]$cmd) {   # numa janela nova, como o KATHAROS.bat (ele mesmo pede administrador quando precisa)
    if (Test-Path -LiteralPath $PS1) { Start-Process powershell.exe -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "' + $PS1 + '" ' + $cmd) }
    else { Start-Process $PY -ArgumentList ('"' + $KPY + '" ' + $cmd) }
}
function Mede {
    $exe = if (Test-Path -LiteralPath $PYW) { $PYW } else { $PY }
    Start-Process $exe -ArgumentList ('"' + $KPY + '" amostrar --agendada --sem-cor') -WindowStyle Hidden
    $script:proxima = (Get-Date).AddSeconds(8)
}
function Pausada { if (-not (Test-Path -LiteralPath $PAUSA)) { return $false }; try { [datetime](Get-Content -LiteralPath $PAUSA -Raw).Trim() -gt (Get-Date) } catch { $false } }
function AlternaPausa {
    if (Pausada) { Remove-Item -LiteralPath $PAUSA -Force }
    else { (Get-Date).AddHours(1).ToString('s') | Set-Content -LiteralPath $PAUSA -Encoding ASCII }
    Atualiza
}
function N($v, $casas = 0) { if ($null -eq $v) { return $null }; [math]::Round([double]$v, $casas) }

$ni = New-Object System.Windows.Forms.NotifyIcon
$ni.Icon = Icone; $ni.Text = 'Katharos'; $ni.Visible = $true
$menu = New-Object System.Windows.Forms.ContextMenuStrip
$menu.ShowImageMargin = $false
function Item([string]$texto, [scriptblock]$acao) {
    $i = New-Object System.Windows.Forms.ToolStripMenuItem $texto
    if ($acao) { $i.add_Click($acao) } else { $i.Enabled = $false }
    [void]$menu.Items.Add($i); $i
}
$titulo = Item "Katharos $VERSAO, em segundo plano" $null
$titulo.Font = New-Object System.Drawing.Font($menu.Font, [System.Drawing.FontStyle]::Bold)
$lUso = Item 'esperando a primeira leitura' $null
$lTemp = Item '' $null
$lQuando = Item '' $null
[void]$menu.Items.Add((New-Object System.Windows.Forms.ToolStripSeparator))
[void](Item 'Abrir o Katharos' { Abre '' })
[void](Item 'Abrir o painel (gráficos)' { Abre 'painel' })
[void](Item 'Raio-x do PC' { Abre 'raiox' })
[void](Item 'Medir agora' { Mede })
[void]$menu.Items.Add((New-Object System.Windows.Forms.ToolStripSeparator))
$iPausa = Item 'Pausar a leitura por 1 hora' { AlternaPausa }
[void](Item 'Abrir a pasta dos dados' { Start-Process explorer.exe $CASA })
[void](Item 'Desfazer mudanças' { Abre 'desfazer' })
[void]$menu.Items.Add((New-Object System.Windows.Forms.ToolStripSeparator))
[void](Item 'Fechar este ícone' { $ni.Visible = $false; [System.Windows.Forms.Application]::Exit() })
$ni.ContextMenuStrip = $menu
# clique com o botão esquerdo também abre o menu
$ni.add_MouseUp({ param($s, $e) if ($e.Button -eq [System.Windows.Forms.MouseButtons]::Left) {
    [System.Windows.Forms.NotifyIcon].GetMethod('ShowContextMenu', [System.Reflection.BindingFlags]'Instance,NonPublic').Invoke($ni, $null) } })

$script:avisado = [datetime]::MinValue
$script:proxima = Get-Date
function Atualiza {
    $iPausa.Text = if (Pausada) { 'Retomar a leitura agora' } else { 'Pausar a leitura por 1 hora' }
    $a = $null
    if (Test-Path -LiteralPath $ULTIMA) { try { $a = Get-Content -LiteralPath $ULTIMA -Raw -Encoding UTF8 | ConvertFrom-Json } catch {} }
    if (-not $a) { return }
    $cpu = N $a.cpu; $ram = N $a.ram_pct; $tc = N $a.temp; $tg = N $a.gpu_temp
    $lUso.Text = 'CPU ' + $(if ($null -ne $cpu) { "$cpu %" } else { '-' }) + '    RAM ' + $(if ($null -ne $ram) { "$ram %" } else { '-' }) + $(if ($null -ne $a.disco) { '    disco ' + (N $a.disco) + ' %' } else { '' })
    $lTemp.Text = 'temperatura: CPU ' + $(if ($null -ne $tc) { "$tc °C" } else { 'sem sensor' }) + '    GPU ' + $(if ($null -ne $tg) { "$tg °C" } else { '-' })
    $q = $null; try { $q = [datetime]$a.quando } catch {}
    $velha = $q -and ((Get-Date) - $q).TotalMinutes -gt 40
    if (Pausada) { $lQuando.Text = 'leitura pausada (volta sozinha em até 1 hora)' }
    elseif ($velha) { $lQuando.Text = 'sem leitura desde ' + $q.ToString('dd/MM HH:mm') + ': abra o Katharos e rode "agendar"' }
    elseif ($q) { $prox = [math]::Max(1, [math]::Ceiling(15 - ((Get-Date) - $q).TotalMinutes)); $lQuando.Text = 'lido às ' + $q.ToString('HH:mm') + $(if ($a.em_jogo) { ' com jogo aberto' } else { '' }) + ", próxima em ~$prox min" }
    else { $lQuando.Text = '' }
    $dica = 'Katharos: CPU ' + $(if ($null -ne $cpu) { "$cpu%" } else { '-' }) + $(if ($null -ne $tc) { ", $tc °C" } elseif ($null -ne $ram) { ", RAM $ram%" } else { '' })
    if ($velha -and -not (Pausada)) { $dica = 'Katharos: sem leitura desde ' + $q.ToString('HH:mm') }
    $ni.Text = $dica.Substring(0, [math]::Min(63, $dica.Length))
    # calor de verdade: avisa uma vez por hora
    $quente = @(@($tc, $tg) | Where-Object { $null -ne $_ -and $_ -ge 90 })
    if ($quente.Count -and ((Get-Date) - $script:avisado).TotalMinutes -ge 60) {
        $script:avisado = Get-Date
        $ni.ShowBalloonTip(8000, 'Katharos: PC quente', ('Temperatura em ' + ($quente | Measure-Object -Maximum).Maximum + ' °C. Confira ventoinha e poeira; o painel mostra quando esquenta.'), [System.Windows.Forms.ToolTipIcon]::Warning)
    }
}
$tm = New-Object System.Windows.Forms.Timer
$tm.Interval = 4000
$tm.add_Tick({ if ((Get-Date) -ge $script:proxima) { $script:proxima = (Get-Date).AddSeconds(30); Atualiza } })
$menu.add_Opening({ Atualiza })
$tm.Start()
Atualiza
try { [System.Windows.Forms.Application]::Run() } finally { $ni.Visible = $false; $ni.Dispose(); $__mutex.ReleaseMutex() }
'''


def bandeja_arq():
    return CASA / 'bandeja.ps1'


def escreve_bandeja():
    """Grava o script do ícone em ~/.katharos (com BOM: o PowerShell 5.1 só lê acento assim)."""
    py = Path(sys.executable)
    pyw = py.with_name('pythonw.exe')
    ps1 = Path(__file__).resolve().parent / 'katharos.ps1'
    if ps1.is_file():   # rodando da pasta do programa: guarda onde ele está, para a cópia em ~/.katharos saber abrir pelo KATHAROS
        marca_estado('ps1', str(ps1))
    else:
        ps1 = Path(estado().get('ps1') or ps1)
    corpo = ps_monta(BANDEJA_PS, versao=psq(VERSAO), ps1=psq(ps1), py=psq(py), pyw=psq(pyw), kpy=psq(CASA / 'katharos.py'), casa=psq(CASA),
                     ultima=psq(ULTIMA_AMOSTRA), pausa=psq(PAUSA_ARQ))
    arq = bandeja_arq()
    arq.parent.mkdir(parents=True, exist_ok=True)
    arq.write_text(corpo, encoding='utf-8-sig')
    return arq


def _cmd_bandeja():
    return '-NoProfile -STA -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + str(bandeja_arq()) + '"'


def abre_bandeja():
    """Abre o ícone agora, sem janela nenhuma (CREATE_NO_WINDOW). Se já houver um, o novo fecha sozinho."""
    if not WINDOWS:
        return False
    escreve_bandeja()
    try:
        subprocess.Popen(['powershell.exe', '-NoProfile', '-STA', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', str(bandeja_arq())],
                         creationflags=0x08000000, close_fds=True)
        return True
    except OSError as e:
        LOG.escreve(f'ícone: não abriu ({e!r})')
        return False


def instala_bandeja(ctx):
    """Tarefa que abre o ícone quando você entra no Windows, como o seu usuário (sem administrador) e já abre agora."""
    escreve_bandeja()
    # pythonw abre o ícone com CREATE_NO_WINDOW: nada pisca ao entrar no Windows. Sem pythonw, um PowerShell escondido (pisca um instante).
    pw = Path(sys.executable).with_name('pythonw.exe')
    if pw.exists():
        exe, arg = str(pw), subprocess.list2cmdline([str(CASA / 'katharos.py'), 'bandeja', '--agendada', '--sem-cor'])
    else:
        exe, arg = 'powershell.exe', _cmd_bandeja()
    corpo = ps_monta(r'''
$__a = New-ScheduledTaskAction -Execute «exe» -Argument «arg»
$__t = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$__p = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
$__s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -MultipleInstances IgnoreNew
if ($TESTE) { Plano 'criar o ícone do Katharos perto do relógio'; return }
Register-ScheduledTask -TaskName «nome» -Action $__a -Trigger $__t -Principal $__p -Settings $__s -Description 'Ícone do Katharos perto do relógio: mostra a última leitura e atalhos. Criado pelo Katharos.' -Force | Out-Null
Start-ScheduledTask -TaskName «nome» -ErrorAction SilentlyContinue
Feito 'ícone do Katharos ligado perto do relógio'
''', exe=psq(exe), arg=psq(arg), nome=psq(TAREFA_BANDEJA))
    s = roda_ps(ctx.t, corpo, 'agendar-icone', minutos=1, mostra=False)
    ok = s.ok and not s.erros
    if ok:
        marca_estado('bandeja', 'sim')
    return 0 if ok else 1


def remove_bandeja(ctx, por_pedido=False):
    if por_pedido:
        marca_estado('bandeja', 'nao')   # a pessoa tirou: a coleta não põe de volta sozinha
    roda_ps(ctx.t, f'''Unregister-ScheduledTask -TaskName {psq(TAREFA_BANDEJA)} -Confirm:$false -ErrorAction SilentlyContinue
Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue | Where-Object {{ "$($_.CommandLine)" -like '*\\.katharos\\bandeja.ps1*' }} | ForEach-Object {{ Invoke-CimMethod -InputObject $_ -MethodName Terminate | Out-Null }}''',
            'remover-icone', minutos=1, mostra=False)


def grava_ultima_amostra(a):
    """O ícone lê daqui. Um arquivo pequeno, trocado a cada leitura."""
    try:
        d = dict(a)
        d['quando'] = agora_iso()
        tmp = CASA / (ULTIMA_AMOSTRA + '.tmp')
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
        os.replace(tmp, CASA / ULTIMA_AMOSTRA)
    except (OSError, TypeError, ValueError) as e:
        LOG.escreve(f'ícone: não gravei a última amostra ({e!r})')


def leitura_pausada():
    """O ícone pode pausar a coleta por 1 hora (arquivo com a hora de voltar)."""
    try:
        ate = (CASA / PAUSA_ARQ).read_text(encoding='ascii').strip()
        return datetime.fromisoformat(ate) > datetime.now()
    except (OSError, ValueError):
        return False


def ferramenta_bandeja(ctx, args):
    """Mostra (ou tira) o ícone do Katharos perto do relógio."""
    t = ctx.t
    if not WINDOWS:
        t.erro('só funciona no Windows.')
        return 1
    if getattr(args, 'parar', False):
        remove_bandeja(ctx, por_pedido=True)
        t.ok('Ícone fechado e tirado da inicialização. A coleta de 15 min continua (agendar --remover desliga).')
        return 0
    if getattr(args, 'agendada', False):
        return 0 if abre_bandeja() else 1
    try:
        if Path(__file__).resolve() != (CASA / 'katharos.py').resolve():
            CASA.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(__file__).resolve(), CASA / 'katharos.py')
    except OSError as e:
        LOG.escreve(f'ícone: não copiei o programa ({e!r})')
    r = instala_bandeja(ctx)
    if r == 0:
        t.ok('Ícone ligado perto do relógio. Se não aparecer, clique na setinha ^ da barra de tarefas e arraste o ícone para fora.')
    return r
