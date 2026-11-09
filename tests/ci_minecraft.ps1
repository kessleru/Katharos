# Roda no Windows de verdade (job windows-real): cria um options.txt falso, aplica o pacote do Minecraft e confere
# o resultado byte a byte, sem BOM, só para baixo; depois desfaz e compara com o original.
$ErrorActionPreference = 'Stop'
$dir = Join-Path $env:APPDATA '.minecraft'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$arq = Join-Path $dir 'options.txt'
$orig = "version:3955`r`nrenderDistance:16`r`nsimulationDistance:12`r`nbiomeBlendRadius:3`r`nparticles:0`r`nentityShadows:true`r`ngraphicsMode:2`r`nmaxFps:120`r`nrenderClouds:true`r`nrenderDistanceExtra:99`r`n"
[IO.File]::WriteAllText($arq, $orig, (New-Object Text.UTF8Encoding $false))
python programa/katharos.py minecraft --sim --modo equilibrado --sem-cor
$bytes = [IO.File]::ReadAllBytes($arq)
if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { throw 'o arquivo ganhou BOM' }
$novo = [IO.File]::ReadAllText($arq)
$esperado = "version:3955`r`nrenderDistance:10`r`nsimulationDistance:8`r`nbiomeBlendRadius:1`r`nparticles:1`r`nentityShadows:false`r`ngraphicsMode:1`r`nmaxFps:120`r`nrenderClouds:true`r`nrenderDistanceExtra:99`r`n"
if ($novo -ne $esperado) { Write-Host "ESPERADO:`n$esperado`nOBTIDO:`n$novo"; throw 'options.txt nao ficou como esperado' }
if (-not (Test-Path "$arq.katharos.bak")) { throw 'faltou a copia .katharos.bak' }
# segunda aplicação não muda nada
python programa/katharos.py minecraft --sim --modo equilibrado --sem-cor
if ([IO.File]::ReadAllText($arq) -ne $esperado) { throw 'a segunda aplicacao mudou o arquivo' }
python programa/katharos.py desfazer minecraft --sim --sem-cor
if ([IO.File]::ReadAllText($arq) -ne $orig) { Write-Host ([IO.File]::ReadAllText($arq)); throw 'o desfazer nao devolveu o arquivo original' }
Write-Host 'Minecraft: aplicar, repetir e desfazer deram o resultado esperado'
