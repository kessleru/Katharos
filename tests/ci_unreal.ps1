# Roda no Windows de verdade (job windows-real): cria um GameUserSettings.ini falso (com BOM, como alguns jogos gravam), aplica o pacote
# "unreal" e confere: só baixa de Epico para Alto, chaves fora da lista e valores ja baixos ficam iguais, BOM e quebras de linha preservados;
# repetir nao muda nada; desfazer devolve o original byte a byte.
$ErrorActionPreference = 'Stop'
$dir = Join-Path $env:LOCALAPPDATA 'FactoryGame\Saved\Config\WindowsNoEditor'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$arq = Join-Path $dir 'GameUserSettings.ini'
$orig = "[ScalabilityGroups]`r`nsg.ResolutionQuality=100.000000`r`nsg.ViewDistanceQuality=3`r`nsg.ShadowQuality=3`r`nsg.EffectsQuality=1`r`nsg.TextureQuality=3`r`nsg.PostProcessQuality=3`r`nsg.FoliageQuality=2`r`n`r`n[/Script/Engine.GameUserSettings]`r`nResolutionSizeX=1920`r`n"
[IO.File]::WriteAllText($arq, $orig, (New-Object Text.UTF8Encoding $true))
$bytesOrig = [IO.File]::ReadAllBytes($arq)
python programa/katharos.py unreal --sim --modo equilibrado --sem-cor
$bytes = [IO.File]::ReadAllBytes($arq)
if (-not ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)) { throw 'o BOM original nao foi preservado' }
$novo = [IO.File]::ReadAllText($arq)
$esperado = "[ScalabilityGroups]`r`nsg.ResolutionQuality=100.000000`r`nsg.ViewDistanceQuality=2`r`nsg.ShadowQuality=2`r`nsg.EffectsQuality=1`r`nsg.TextureQuality=3`r`nsg.PostProcessQuality=2`r`nsg.FoliageQuality=2`r`n`r`n[/Script/Engine.GameUserSettings]`r`nResolutionSizeX=1920`r`n"
if ($novo -ne $esperado) { Write-Host "ESPERADO:`n$esperado`nOBTIDO:`n$novo"; throw 'GameUserSettings.ini nao ficou como esperado' }
if (-not (Test-Path "$arq.katharos.bak")) { throw 'faltou a copia .katharos.bak' }
python programa/katharos.py unreal --sim --modo equilibrado --sem-cor
if ([IO.File]::ReadAllText($arq) -ne $esperado) { throw 'a segunda aplicacao mudou o arquivo' }
python programa/katharos.py desfazer unreal --sim --sem-cor
$volta = [IO.File]::ReadAllBytes($arq)
if (($volta -join ',') -ne ($bytesOrig -join ',')) { Write-Host ([IO.File]::ReadAllText($arq)); throw 'o desfazer nao devolveu o arquivo original byte a byte' }
# arquivo em UTF-16 nao e reescrito
[IO.File]::WriteAllText($arq, $orig, [Text.Encoding]::Unicode)
$antes = [IO.File]::ReadAllBytes($arq)
python programa/katharos.py unreal --sim --modo equilibrado --sem-cor
if ((([IO.File]::ReadAllBytes($arq)) -join ',') -ne ($antes -join ',')) { throw 'arquivo UTF-16 foi alterado' }
Write-Host 'Unreal: aplicar, repetir, desfazer e recusar UTF-16 deram o resultado esperado'
