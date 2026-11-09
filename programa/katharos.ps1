# Abre o Katharos: acha o Python que ja existe no PC (so instala se nao houver nenhum),
# escolhe o melhor terminal (Windows Terminal, depois PowerShell 7, depois Windows PowerShell)
# e abre como administrador. Uso: KATHAROS.bat [comando] [opcoes]
[CmdletBinding(PositionalBinding = $false)]
param(
    [switch]$Dentro,
    [string]$Py,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$Resto
)
$ErrorActionPreference = 'SilentlyContinue'
$aqui = $PSScriptRoot
$programa = Join-Path $aqui 'katharos.py'
if (-not $Resto) { $Resto = @() }

# Link do painel (katharos://comando): qualquer página pode chamar este protocolo, então só passa o formato exato
# "--uri katharos://comando" (minúsculas, sem parâmetros). Qualquer outra coisa encerra aqui, antes de elevar.
if ($Resto -contains '--uri') {
    if ($Resto.Count -ne 2 -or $Resto[0] -cne '--uri' -or $Resto[1] -cnotmatch '^katharos://[a-z][a-z0-9-]{1,30}/?$') { exit 2 }
}

function EhAdmin {
    ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Testa([string]$Exe, [string[]]$Antes = @()) {
    # Roda o Python de verdade: o atalho falso da Loja (quando nao ha Python) falha aqui e e descartado.
    if (-not $Exe) { return $null }
    try {
        $o = & $Exe @Antes -c "import sys; print(sys.executable if sys.version_info >= (3, 8) else '')" 2>$null
        if ($LASTEXITCODE -ne 0 -or -not "$o".Trim()) { return $null }
        if ($Antes.Count) { return "$o".Trim() }   # py -3: devolve o python.exe real
        return $Exe
    } catch { return $null }
}

function AchaPython {
    # 1. o Python Launcher (py -3), que sabe de todas as instalacoes oficiais
    $py = Get-Command py.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($py) { $r = Testa $py.Source @('-3'); if ($r) { return $r } }
    # 2. python no PATH, fora da pasta da Loja
    foreach ($c in @(Get-Command python.exe, python3.exe -All -ErrorAction SilentlyContinue)) {
        if ($c.Source -notmatch '\\WindowsApps\\') { $r = Testa $c.Source; if ($r) { return $r } }
    }
    # 3. o registro (instalacoes oficiais que nao estao no PATH)
    foreach ($raiz in 'HKCU:\Software\Python\PythonCore', 'HKLM:\Software\Python\PythonCore', 'HKLM:\Software\WOW6432Node\Python\PythonCore') {
        foreach ($k in @(Get-ChildItem $raiz -ErrorAction SilentlyContinue | Sort-Object PSChildName -Descending)) {
            $ip = Get-ItemProperty -LiteralPath (Join-Path $k.PSPath 'InstallPath') -ErrorAction SilentlyContinue
            if (-not $ip) { continue }
            foreach ($e in @($ip.ExecutablePath, $(if ($ip.'(default)') { Join-Path $ip.'(default)' 'python.exe' }))) { $r = Testa $e; if ($r) { return $r } }
        }
    }
    # 4. pastas comuns
    foreach ($p in @(Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe", "$env:ProgramFiles\Python3*\python.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending)) {
        $r = Testa $p.FullName; if ($r) { return $r }
    }
    # 5. o Python da Microsoft Store tambem serve: o Katharos roda o PowerShell fora do conteiner dela
    foreach ($c in @(Get-Command python.exe, python3.exe -All -ErrorAction SilentlyContinue)) {
        if ($c.Source -match '\\WindowsApps\\') { $r = Testa $c.Source; if ($r) { return $r } }
    }
    return $null
}

function Para([string]$msg) {
    Write-Host ''
    Write-Host $msg -ForegroundColor Yellow
    Write-Host ''
    Read-Host 'Enter para fechar' | Out-Null
    exit 1
}

# ── dentro da janela nova (ja como administrador): so roda ──
if ($Dentro) {
    $Host.UI.RawUI.WindowTitle = 'Katharos'
    try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
    Set-Location -LiteralPath $aqui
    & $Py $programa @Resto
    Write-Host ''
    Write-Host 'O Katharos fechou. Pode fechar esta janela.' -ForegroundColor DarkGray
    return
}

# ── primeira parte: acha (ou instala) o Python ──
$python = AchaPython
if (-not $python) {
    Write-Host 'Nenhum Python 3.8 ou mais novo neste PC. Instalando o Python 3.12 oficial pelo winget...'
    if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
        Para 'O winget nao esta disponivel. Instale o Python em https://www.python.org/downloads/ e abra o KATHAROS.bat de novo.'
    }
    & winget.exe install --id Python.Python.3.12 --exact --scope user --silent --accept-source-agreements --accept-package-agreements --disable-interactivity
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $python = AchaPython
    if (-not $python) { Para 'Nao consegui instalar o Python. Baixe em https://www.python.org/downloads/ e abra o KATHAROS.bat de novo.' }
}

# ── ja e administrador (aberto pelo proprio PowerShell): roda aqui mesmo ──
if (EhAdmin) {
    try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
    Set-Location -LiteralPath $aqui
    & $python $programa @Resto
    exit $LASTEXITCODE
}

# ── abre o melhor terminal como administrador ──
$shell = (Get-Command pwsh.exe -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if (-not $shell) { $shell = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe' }
$q = { param($s) '"' + ($s -replace '"', '\"') + '"' }
$argsPs = @('-NoExit', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (& $q $PSCommandPath), '-Dentro', '-Py', (& $q $python)) + @($Resto | ForEach-Object { & $q $_ })
$wt = Get-Command wt.exe -ErrorAction SilentlyContinue | Select-Object -First 1
try {
    if ($wt) {
        Start-Process -Verb RunAs -FilePath $wt.Source -ArgumentList (@('-w', 'new', '--title', 'Katharos', (& $q $shell)) + $argsPs) -ErrorAction Stop
    } else {
        Start-Process -Verb RunAs -FilePath $shell -ArgumentList $argsPs -ErrorAction Stop
    }
} catch {
    Para 'O Katharos precisa de administrador para mudar o Windows. Abra de novo e clique em Sim no aviso.'
}
