# Atualiza a versao de terminal do Katharos (katharos versoes --atualizar) ou volta a anterior (--voltar).
# O Python do Katharos nunca acessa a rede: quem baixa e este script. Confere o SHA-256 de cada arquivo pela lista
# publicada na mesma release (SHA256SUMS-release.txt) antes de trocar qualquer coisa, e guarda a versao de agora
# em ~/.katharos/versoes/<versao> para poder voltar.
param(
    [Parameter(Mandatory = $true)][string]$Pasta,
    [Parameter(Mandatory = $true)][string]$Atual,
    [switch]$Voltar
)
$ErrorActionPreference = 'Stop'
$casa = Join-Path $env:USERPROFILE '.katharos'
$guarda = Join-Path $casa 'versoes'
$repo = 'kessleru/Katharos'

function SegundoPlanoSai {
    # o Katharos.exe (segundo plano) fica com o arquivo aberto: pede para ele sair e lembra de religar
    $agora = Join-Path $casa 'agora.json'
    if ((Test-Path $agora) -and ((Get-Date) - (Get-Item $agora).LastWriteTime).TotalSeconds -lt 20) {
        Set-Content -LiteralPath (Join-Path $casa 'segundo-plano-sair.txt') -Value (Get-Date -Format s) -Encoding ascii
        for ($i = 0; $i -lt 40 -and ((Get-Date) - (Get-Item $agora).LastWriteTime).TotalSeconds -lt 6; $i++) { Start-Sleep -Milliseconds 250 }
        return $true
    }
    return $false
}

function Copia([string]$de, [string]$para) {
    New-Item -ItemType Directory -Force -Path $para | Out-Null
    Get-ChildItem -LiteralPath $de -Force | Where-Object { $_.Name -notin @('relatorios', '__pycache__') } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $para -Recurse -Force
    }
}

if ($Voltar) {
    $ult = Get-ChildItem -LiteralPath $guarda -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $ult) { Write-Host 'Nenhuma versao anterior guardada.'; exit 2 }
    $religa = SegundoPlanoSai
    Copia $ult.FullName $Pasta
    Write-Host "Voltou para a versao $($ult.Name)."
    if ($religa -and (Test-Path (Join-Path $Pasta 'Katharos.exe'))) { Start-Process (Join-Path $Pasta 'Katharos.exe') -ArgumentList '--segundo-plano' }
    exit 0
}

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$rel = Invoke-RestMethod "https://api.github.com/repos/$repo/releases/latest" -Headers @{ 'User-Agent' = 'Katharos' }
$nova = ($rel.tag_name -replace '^v', '')
if ([version]($nova -replace '-.*$', '') -le [version]($Atual -replace '-.*$', '')) { Write-Host "Ja esta na versao mais nova ($Atual)."; exit 3 }
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('katharos-' + [guid]::NewGuid().ToString('n'))
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
try {
    foreach ($nome in 'Katharos.zip', 'SHA256SUMS-release.txt') {
        $a = $rel.assets | Where-Object { $_.name -eq $nome } | Select-Object -First 1
        if (-not $a) { throw "a release $nova nao tem $nome" }
        Invoke-WebRequest $a.browser_download_url -OutFile (Join-Path $tmp $nome) -UseBasicParsing
    }
    $esperado = (Get-Content (Join-Path $tmp 'SHA256SUMS-release.txt') | Where-Object { $_ -match '\s\*?Katharos\.zip$' } | Select-Object -First 1) -split '\s+' | Select-Object -First 1
    $obtido = (Get-FileHash (Join-Path $tmp 'Katharos.zip') -Algorithm SHA256).Hash.ToLower()
    if (-not $esperado -or $esperado.ToLower() -ne $obtido) { throw "o SHA-256 do Katharos.zip nao confere (esperado $esperado, baixado $obtido): nada foi trocado" }
    Expand-Archive -LiteralPath (Join-Path $tmp 'Katharos.zip') -DestinationPath (Join-Path $tmp 'z') -Force
    $novaPasta = Join-Path $tmp 'z\Katharos'
    if (-not (Test-Path (Join-Path $novaPasta 'programa\katharos.py'))) { throw 'o zip nao tem programa\katharos.py' }
    # cada arquivo que vai entrar tambem confere com a lista da release, quando ela lista o arquivo
    foreach ($l in Get-Content (Join-Path $tmp 'SHA256SUMS-release.txt')) {
        if ($l -match '^([0-9a-f]{64})\s+\*?Katharos/(.+)$') {
            $f = Join-Path $novaPasta ($Matches[2] -replace '/', '\')
            if ((Test-Path $f) -and (Get-FileHash $f -Algorithm SHA256).Hash.ToLower() -ne $Matches[1]) { throw "$($Matches[2]) nao confere com a lista da release" }
        }
    }
    $copia = Join-Path $guarda $Atual
    Copia $Pasta $copia
    $religa = SegundoPlanoSai
    Copia $novaPasta $Pasta
    Write-Host "Atualizado de $Atual para $nova. A versao anterior ficou guardada; para voltar: katharos versoes --voltar"
    if ($religa -and (Test-Path (Join-Path $Pasta 'Katharos.exe'))) { Start-Process (Join-Path $Pasta 'Katharos.exe') -ArgumentList '--segundo-plano' }
    exit 0
}
catch { Write-Host "Nao atualizou: $($_.Exception.Message)"; exit 1 }
finally { Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue }
