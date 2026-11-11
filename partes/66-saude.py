# ─────────────── saúde do Windows: erros dos logs, drivers e o que o Windows precisa ───────────────
# Coleta só leitura (Visualizador de Eventos, drivers instalados, estado do Windows) → catálogo de causas conhecidas → problemas
# explicados, com o que fazer. Regras: (1) só explica o que está no catálogo; o resto aparece como "sem explicação catalogada",
# com a mensagem original, nunca inventada; (2) ruído conhecido (ex.: DCOM 10016) é dito como ruído; (3) sem internet: o programa
# não sabe qual é a versão mais nova de um driver, só avisa idade e queda; (4) nada é alterado aqui.
SAUDE_DIAS = 14

SAUDE_PS = r'''
Vivo 'erros do Windows'
$__ini = (Get-Date).AddDays(-14)
$__ev = New-Object System.Collections.Generic.List[object]
foreach ($__log in 'System', 'Application') {
  $__r = @(Get-WinEvent -FilterHashtable @{ LogName = $__log; Level = 1, 2; StartTime = $__ini } -MaxEvents 4000 -ErrorAction SilentlyContinue)
  foreach ($__x in $__r) { $__ev.Add($__x) }
}
$__comArg = @(1000, 1002, 1026, 1001, 41, 7000, 7001, 7009, 7011, 7023, 7024, 7031, 7034)
$__grupos = @{}
foreach ($__e in $__ev) {
  $__k = [string]$__e.ProviderName + '|' + [string]$__e.Id
  $__arg = ''
  if ($__comArg -contains [int]$__e.Id) { try { $__arg = [string]$__e.Properties[0].Value } catch { $__arg = '' } }
  if ($__arg) { $__k += '|' + $__arg }
  if (-not $__grupos.ContainsKey($__k)) { $__grupos[$__k] = @{ p = [string]$__e.ProviderName; id = [int]$__e.Id; arg = $__arg; n = 0; dias = (New-Object System.Collections.Generic.HashSet[string]); primeiro = $__e.TimeCreated; ultimo = $__e.TimeCreated; ev = $__e } }
  $__g = $__grupos[$__k]
  $__g.n = $__g.n + 1
  [void]$__g.dias.Add($__e.TimeCreated.ToString('yyyy-MM-dd'))
  if ($__e.TimeCreated -gt $__g.ultimo) { $__g.ultimo = $__e.TimeCreated; $__g.ev = $__e }
  if ($__e.TimeCreated -lt $__g.primeiro) { $__g.primeiro = $__e.TimeCreated }
}
$__lista = foreach ($__g in ($__grupos.Values | Sort-Object { $_.n } -Descending | Select-Object -First 60)) {
  $__m = ''
  try { $__m = [string]$__g.ev.Message } catch { $__m = '' }
  $__m = ($__m -replace '\s+', ' ')
  if ($__m.Length -gt 240) { $__m = $__m.Substring(0, 240) }
  [pscustomobject]@{ provedor = $__g.p; id = $__g.id; arg = $__g.arg; n = $__g.n; dias = $__g.dias.Count; primeiro = $__g.primeiro.ToString('s'); ultimo = $__g.ultimo.ToString('s'); msg = $__m }
}
Dado 'saude_grupos' (Lista $__lista)
$__porDia = $__ev | Group-Object { $_.TimeCreated.ToString('yyyy-MM-dd') } | ForEach-Object { [pscustomobject]@{ dia = $_.Name; n = $_.Count } }
Dado 'saude_por_dia' (Lista $__porDia)
Dado 'saude_total' @{ eventos = $__ev.Count; dias = 14 }

Vivo 'drivers'
$__cls = 'DISPLAY', 'NET', 'MEDIA', 'BLUETOOTH', 'HDC', 'SCSIADAPTER', 'USB', 'SYSTEM', 'HIDCLASS', 'DISKDRIVE'
$__drv = @(Get-CimInstance Win32_PnPSignedDriver -ErrorAction SilentlyContinue | Where-Object { $_.DeviceName -and $_.DriverDate -and ($__cls -contains [string]$_.DeviceClass) -and ([string]$_.Manufacturer -notmatch '^(Microsoft|\(Standard)') })
$__drvL = foreach ($__d in ($__drv | Sort-Object DriverDate | Select-Object -First 150)) {
  [pscustomobject]@{ nome = [string]$__d.DeviceName; classe = [string]$__d.DeviceClass; fab = [string]$__d.Manufacturer; versao = [string]$__d.DriverVersion; data = $__d.DriverDate.ToString('s'); assinado = [bool]$__d.IsSigned }
}
Dado 'saude_drivers' (Lista $__drvL)
$__prob = foreach ($__p in @(Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue | Where-Object { $_.ConfigManagerErrorCode -ne 0 -and $_.ConfigManagerErrorCode -ne 22 } | Select-Object -First 30)) {
  [pscustomobject]@{ nome = [string]$__p.Name; id = [string]$__p.DeviceID; codigo = [int]$__p.ConfigManagerErrorCode; classe = [string]$__p.PNPClass }
}
Dado 'saude_dispositivos' (Lista $__prob)

Vivo 'estado do Windows'
$__w = @{}
$__w.reinicio_pendente = [bool]((Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending') -or (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired'))
$__os = Get-CimInstance Win32_OperatingSystem
$__w.uptime_dias = [math]::Round(((Get-Date) - $__os.LastBootUpTime).TotalDays, 1)
$__hf = Tenta { Get-HotFix -ErrorAction Stop | Where-Object { $_.InstalledOn } | Sort-Object InstalledOn -Descending | Select-Object -First 1 } $null
$__w.ultima_atualizacao = $(if ($__hf) { ([datetime]$__hf.InstalledOn).ToString('s') } else { '' })
$__ld = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'" -ErrorAction SilentlyContinue
$__w.livre_pct = $(if ($__ld -and $__ld.Size) { [math]::Round(100 * $__ld.FreeSpace / $__ld.Size, 1) } else { $null })
$__w.livre_gb = $(if ($__ld) { [math]::Round($__ld.FreeSpace / 1GB, 1) } else { $null })
$__w.secure_boot = Tenta { [bool](Confirm-SecureBootUEFI) } $null
$__mp = Tenta { Get-MpComputerStatus -ErrorAction Stop } $null
$__w.defender_tempo_real = $(if ($__mp) { [bool]$__mp.RealTimeProtectionEnabled } else { $null })
$__w.defender_assinatura_dias = $(if ($__mp) { [int]$__mp.AntivirusSignatureAge } else { $null })
$__w.pontos_restauracao = @(Tenta { Get-ComputerRestorePoint -ErrorAction Stop } @()).Count
Dado 'saude_windows' $__w
'''

# ───────── catálogo de causas conhecidas ─────────
# (provedor em minúsculas, id) -> dict. 'ruido' marca o que a própria Microsoft diz que pode ser ignorado.
BUGCHECKS = {
    '0x0000000a': ('IRQL_NOT_LESS_OR_EQUAL', 'driver ou memória'), '0x0000001a': ('MEMORY_MANAGEMENT', 'memória RAM'),
    '0x0000001e': ('KMODE_EXCEPTION_NOT_HANDLED', 'driver'), '0x0000003b': ('SYSTEM_SERVICE_EXCEPTION', 'driver'),
    '0x00000050': ('PAGE_FAULT_IN_NONPAGED_AREA', 'memória RAM ou driver'), '0x0000007a': ('KERNEL_DATA_INPAGE_ERROR', 'disco ou cabo'),
    '0x0000007e': ('SYSTEM_THREAD_EXCEPTION_NOT_HANDLED', 'driver'), '0x0000009f': ('DRIVER_POWER_STATE_FAILURE', 'driver ou energia'),
    '0x000000c2': ('BAD_POOL_CALLER', 'driver'), '0x000000d1': ('DRIVER_IRQL_NOT_LESS_OR_EQUAL', 'driver'),
    '0x000000f4': ('CRITICAL_OBJECT_TERMINATION', 'disco ou processo crítico encerrado'), '0x00000116': ('VIDEO_TDR_FAILURE', 'driver de vídeo ou calor da placa'),
    '0x00000119': ('VIDEO_SCHEDULER_INTERNAL_ERROR', 'driver de vídeo'), '0x00000124': ('WHEA_UNCORRECTABLE_ERROR', 'hardware (CPU, RAM, PCIe) ou overclock'),
    '0x00000133': ('DPC_WATCHDOG_VIOLATION', 'driver ou firmware do SSD'),
}
CATALOGO_ERROS = {
    ('disk', 7): ('alta', 'O disco reportou setor ruim', 'O Windows encontrou um bloco defeituoso. É sinal clássico de disco começando a falhar.', 'Faça backup agora. Depois rode a verificação de disco e olhe o SMART.', 'reparar'),
    ('disk', 11): ('alta', 'Erro do controlador do disco', 'O controlador do disco não respondeu direito. Costuma ser cabo SATA, porta ou o próprio disco.', 'Faça backup, troque o cabo ou a porta e confira o SMART.', 'reparar'),
    ('disk', 51): ('média', 'Erro de paginação no disco', 'Um erro de leitura/escrita aconteceu durante a troca de memória com o disco.', 'Faça backup e verifique o disco; em USB externo, tente outra porta.', 'reparar'),
    ('disk', 153): ('média', 'Operação de disco repetida', 'O disco precisou repetir uma operação de leitura/escrita. Um caso isolado é inofensivo; vários são sinal de cabo ou disco.', 'Confira cabo, porta e SMART.', 'reparar'),
    ('ntfs', 55): ('alta', 'Estrutura de arquivos corrompida', 'O sistema de arquivos achou corrupção em um volume.', 'Faça backup e rode a verificação de disco (chkdsk).', 'reparar'),
    ('ntfs', 98): ('baixa', 'Volume verificado pelo NTFS', 'Registro de verificação de integridade do volume.', 'Só preocupa se vier junto com erros de disco.', ''),
    ('whea-logger', 17): ('alta', 'Erro de hardware corrigido (WHEA)', 'O hardware reportou um erro de barramento PCIe, CPU ou memória.', 'Confira temperatura, overclock/XMP e atualize BIOS e driver de chipset.', 'medir'),
    ('whea-logger', 18): ('alta', 'Erro de hardware grave (WHEA)', 'O processador reportou erro de hardware irrecuperável.', 'Tire overclock/XMP, confira temperatura e fonte; se repetir, é hardware.', 'medir'),
    ('whea-logger', 19): ('média', 'Erro de hardware corrigido (WHEA)', 'O hardware corrigiu sozinho um erro de CPU/cache/memória.', 'Em pequena quantidade é normal; muitos por dia indicam instabilidade.', 'medir'),
    ('whea-logger', 47): ('média', 'Erro corrigido de barramento PCIe', 'Um dispositivo PCIe reportou erro corrigido.', 'Reencaixe a placa de vídeo/SSD NVMe e atualize drivers.', 'medir'),
    ('display', 4101): ('alta', 'O driver de vídeo parou de responder e se recuperou', 'O Windows reiniciou o driver da placa de vídeo depois de um travamento (TDR).', 'Atualize o driver de vídeo (instalação limpa), confira temperatura e overclock da placa.', 'medir'),
    ('volmgr', 161): ('baixa', 'Falha ao criar arquivo de despejo', 'O Windows não conseguiu gravar o dump de uma falha.', 'Confira espaço livre e o tamanho do arquivo de paginação.', 'limpar'),
    ('microsoft-windows-dns-client', 1014): ('média', 'O DNS demorou a responder', 'Consultas de DNS estouraram o tempo. Costuma ser DNS do provedor lento ou rede instável.', 'Meça os servidores de DNS e troque se um for claramente melhor.', 'rede'),
    ('windowsupdateclient', 20): ('média', 'Falha ao instalar uma atualização do Windows', 'O Windows Update tentou instalar e falhou.', 'Rode o reparo dos componentes do Windows Update.', 'reparar'),
    ('windowsupdateclient', 25): ('média', 'Falha ao baixar uma atualização do Windows', 'O download de uma atualização falhou.', 'Rode o reparo dos componentes do Windows Update.', 'reparar'),
    ('windowsupdateclient', 31): ('média', 'Falha ao baixar uma atualização do Windows', 'O Windows Update não conseguiu baixar uma atualização.', 'Rode o reparo dos componentes do Windows Update.', 'reparar'),
    ('distributedcom', 10016): ('info', 'DCOM 10016 (ruído conhecido)', 'A Microsoft documenta que este aviso é comum e pode ser ignorado: é uma permissão de ativação de componente, sem efeito prático.', 'Nada a fazer.', ''),
}
# Provedores em que qualquer id é do mesmo problema (o driver de vídeo da NVIDIA e da AMD)
CATALOGO_PROVEDORES = {
    'nvlddmkm': ('alta', 'O driver da NVIDIA parou de responder', 'O driver de vídeo da NVIDIA travou e foi reiniciado.', 'Atualize o driver (instalação limpa), confira temperatura e overclock.', 'medir'),
    'amdkmdag': ('alta', 'O driver da AMD parou de responder', 'O driver de vídeo da AMD travou e foi reiniciado.', 'Atualize o driver, confira temperatura e overclock.', 'medir'),
    'amdwddmg': ('alta', 'O driver da AMD parou de responder', 'O driver de vídeo da AMD travou e foi reiniciado.', 'Atualize o driver, confira temperatura e overclock.', 'medir'),
}
ERROS_SERVICO = {7000: 'não iniciou', 7001: 'depende de outro serviço que falhou', 7009: 'demorou demais para iniciar', 7011: 'não respondeu a tempo',
                 7023: 'terminou com erro', 7024: 'terminou com erro específico', 7031: 'terminou sem avisar', 7034: 'terminou sem avisar'}
# serviços de programas que falham "de propósito" quando o programa está fechado: não é defeito do PC. Só baixa (nunca some): se o PC
# também trava ou cai, vale olhar.
SERVICOS_QUE_SO_SOBEM_COM_O_PROGRAMA = (
    (r'ryzen\s*master', 'O AMD Ryzen Master instala um driver que só sobe com o programa aberto. Com ele instalado e fechado, o Windows '
                        'registra que o driver não iniciou a cada boot: é comum e não afeta o PC.',
     'Só vale olhar se o PC também trava ou desliga sozinho. Se você não usa o Ryzen Master, desinstalar tira o aviso.'),
)
CODIGOS_DISPOSITIVO = {10: 'o dispositivo não consegue iniciar', 28: 'faltam os drivers', 31: 'o Windows não consegue carregar o driver', 43: 'o Windows parou o dispositivo por ele ter reportado problemas',
                       45: 'o dispositivo não está conectado', 24: 'o dispositivo foi removido ou não funciona direito', 12: 'não há recursos livres suficientes', 37: 'o driver falhou ao iniciar'}


def _codigo_bugcheck(arg):
    """'0x000000D1 (...)' (texto do WER) ou '209' (BugcheckCode decimal do Kernel-Power 41) -> '0x000000d1'; '0' ou vazio -> ''."""
    if re.fullmatch(r'\s*\d+\s*', str(arg or '')):
        n = int(str(arg).strip())
        return ('0x%08x' % n) if n else ''
    m = re.search(r'0x[0-9a-fA-F]{1,8}', str(arg or ''))
    return ('0x' + m.group(0)[2:].lower().zfill(8)) if m else ''


def _dt(txt):
    try:
        return datetime.fromisoformat(str(txt))
    except (TypeError, ValueError):
        return None


def _prob(id_, categoria, gravidade, titulo, evidencia, explica, faz, comando='', n=0):
    return {'id': id_, 'categoria': categoria, 'gravidade': gravidade, 'titulo': titulo, 'evidencia': evidencia, 'explica': explica, 'faz': faz, 'comando': comando, 'n': n}


def explica_grupo(g):
    """Um grupo de eventos -> problema explicado, 'ruido' (catalogado como ignorável) ou None (sem explicação catalogada)."""
    p, i, n, dias = str(g.get('provedor', '')).lower(), int(g.get('id') or 0), int(g.get('n') or 0), int(g.get('dias') or 0)
    arg = str(g.get('arg') or '')
    ult = _dt(g.get('ultimo'))
    quando = f'última vez em {ult:%d/%m %H:%M}' if ult else ''
    base_id = f'{p}:{i}:{arg}'
    def freq():
        return f'{pl(n, "ocorrência", "ocorrências")} em {pl(dias, "dia", "dias")} ({quando})'
    if p == 'microsoft-windows-kernel-power' and i == 41:
        cod = _codigo_bugcheck(arg)
        if cod:
            nome, causa = BUGCHECKS.get(cod, ('código ' + cod, 'driver ou hardware'))
            return _prob(base_id, 'erro', 'alta', f'Tela azul: {nome}', freq(), f'O Windows reiniciou depois de uma falha crítica ({nome}). Causa mais comum: {causa}.',
                         'Atualize os drivers (vídeo primeiro); se for memória, rode o Diagnóstico de Memória do Windows; se repetir, anote o código e procure o driver citado.', 'raiox', n)
        return _prob(base_id, 'erro', 'alta', 'O PC desligou sem avisar', freq(), 'O Windows foi desligado sem passar pelo desligamento normal: queda de energia, fonte, superaquecimento ou travamento seguido de reset no botão.',
                     'Confira temperatura (comando medir), a fonte e o cabo de energia. Se for notebook, veja o carregador e a bateria.', 'medir', n)
    if p == 'microsoft-windows-wer-systemerrorreporting' and i == 1001:
        cod = _codigo_bugcheck(arg)
        nome, causa = BUGCHECKS.get(cod, (cod or 'código desconhecido', 'driver ou hardware'))
        return _prob(base_id, 'erro', 'alta', f'Tela azul registrada: {nome}', freq(), f'Causa mais comum para este código: {causa}.',
                     'Atualize os drivers (vídeo primeiro); se for memória, rode o Diagnóstico de Memória do Windows.', 'raiox', n)
    if p == 'service control manager' and i in ERROS_SERVICO and arg:
        for padrao, ex, faz in SERVICOS_QUE_SO_SOBEM_COM_O_PROGRAMA:
            if re.search(padrao, arg, re.I):
                return _prob(base_id, 'erro', 'baixa', f'O serviço "{arg}" {ERROS_SERVICO[i]}', freq(), ex, faz, '', n)
        gr = 'média' if n >= 3 else 'baixa'
        return _prob(base_id, 'erro', gr, f'O serviço "{arg}" {ERROS_SERVICO[i]}', freq(), 'Serviço do Windows ou de um programa falhando. Se for de um programa que você não usa mais, é resto de instalação.',
                     'Se o programa é seu e ainda é usado, atualize ou reinstale. Se não, o pacote de serviços pode desativá-lo.', 'servicos', n)
    if p == 'application error' and i == 1000 and arg:
        crit = arg.lower() in ('explorer.exe', 'dwm.exe', 'svchost.exe', 'csrss.exe', 'winlogon.exe')
        gr = 'alta' if crit else ('média' if n >= 3 else 'baixa')
        return _prob(base_id, 'erro', gr, f'{arg} fechou sozinho', freq(), 'O programa travou e o Windows o encerrou.' + (' É um componente do próprio Windows: investigue.' if crit else ''),
                     'Atualize ou reinstale o programa; se for componente do Windows, rode o reparo do sistema.', 'reparar' if crit else '', n)
    if p == 'application hang' and i == 1002 and arg:
        return _prob(base_id, 'erro', 'média' if n >= 3 else 'baixa', f'{arg} deixou de responder', freq(), 'O programa ficou travado até ser fechado.', 'Atualize ou reinstale o programa; confira se há pouca RAM livre.', 'memoria', n)
    if p in CATALOGO_PROVEDORES:
        gr, tit, ex, faz, cmd = CATALOGO_PROVEDORES[p]
        return _prob(base_id, 'erro', gr, tit, freq(), ex, faz, cmd, n)
    if (p, i) in CATALOGO_ERROS:
        gr, tit, ex, faz, cmd = CATALOGO_ERROS[(p, i)]
        if gr == 'info':
            return 'ruido'
        if gr == 'média' and n >= 5:
            gr = 'alta' if p.startswith('whea') or p == 'disk' else gr
        return _prob(base_id, 'erro', gr, tit, freq(), ex, faz, cmd, n)
    return None


def analisa_drivers(drivers, dispositivos, grupos_erro, agora):
    """Problemas de driver: dispositivo com erro, sem assinatura, vídeo antigo (mais grave se há quedas do driver de vídeo)."""
    out = []
    for d in dispositivos or []:
        cod = int(d.get('codigo') or 0)
        nome = (d.get('nome') or '').strip() or (f'dispositivo da classe {d["classe"]}' if d.get('classe') else '') or (str(d.get('id') or '')[:40]) or 'dispositivo sem nome'
        out.append(_prob(f'dispositivo:{nome}', 'driver', 'alta', f'Dispositivo com problema: {nome}', f'código {cod}: {CODIGOS_DISPOSITIVO.get(cod, "erro do gerenciador de dispositivos")}',
                         'O Gerenciador de Dispositivos marcou este dispositivo com erro.', 'Atualize ou reinstale o driver pelo site do fabricante ou pelo Windows Update.', 'atualizar'))
    quedas_video = sum(int(g.get('n') or 0) for g in grupos_erro or []
                       if str(g.get('provedor', '')).lower() in ('nvlddmkm', 'amdkmdag', 'amdwddmg') or (str(g.get('provedor', '')).lower() == 'display' and int(g.get('id') or 0) == 4101))
    for d in drivers or []:
        data = _dt(d.get('data'))
        nome, classe, versao = d.get('nome', ''), str(d.get('classe', '')).upper(), d.get('versao', '')
        if d.get('assinado') is False:
            out.append(_prob(f'sem-assinatura:{nome}', 'driver', 'média', f'Driver sem assinatura digital: {nome}', f'versão {versao}, fabricante {d.get("fab", "")}',
                             'Driver não assinado pode ser um driver de teste ou adulterado, e o Windows pode bloquear partes dele.', 'Confirme a origem; reinstale pelo site do fabricante.', 'atualizar'))
        if classe == 'DISPLAY' and data:
            meses = (agora - data).days / 30.4
            if meses >= 18 or (quedas_video >= 2 and meses >= 6):
                gr = 'alta' if quedas_video >= 2 else 'média'
                extra = f' Houve {pl(quedas_video, "queda", "quedas")} do driver de vídeo nos últimos {SAUDE_DIAS} dias.' if quedas_video else ''
                out.append(_prob(f'video-antigo:{nome}', 'driver', gr, f'Driver de vídeo com {int(meses)} meses: {nome}', f'versão {versao}, de {data:%m/%Y}',
                                 'Drivers de vídeo recebem correções de estabilidade e desempenho com frequência.' + extra + ' O Katharos não usa internet e não sabe qual é a versão mais nova.',
                                 'Veja a versão mais recente no site do fabricante (NVIDIA, AMD ou Intel) ou no Windows Update; no caso de quedas, prefira instalação limpa.', 'atualizar'))
    return out


def analisa_windows(w, agora):
    """O que o Windows precisa ajustar, a partir do estado coletado."""
    out = []
    w = w or {}
    if w.get('reinicio_pendente'):
        out.append(_prob('reinicio-pendente', 'windows', 'média', 'Há um reinício pendente', 'o Windows pede reinício para terminar de instalar algo', 'Atualizações e instalações só terminam depois do reinício; até lá, partes do sistema ficam em estado intermediário.', 'Reinicie o PC (Reiniciar, não Desligar).', ''))
    ua = _dt(w.get('ultima_atualizacao'))
    if ua and (agora - ua).days > 60:
        out.append(_prob('atualizacao-atrasada', 'windows', 'média', 'O Windows está sem atualizar há muito tempo', f'a última atualização instalada foi em {ua:%d/%m/%Y} ({(agora - ua).days} dias)',
                         'Atualizações trazem correções de segurança e de estabilidade; atrasar muito deixa o PC exposto.', 'Procure atualizações em Configurações > Windows Update.', 'atualizar'))
    if isinstance(w.get('livre_pct'), (int, float)) and w['livre_pct'] < 10:
        out.append(_prob('disco-cheio', 'windows', 'alta' if w['livre_pct'] < 5 else 'média', 'O disco C: está quase cheio', f'{br(w["livre_pct"], 1)}% livre ({br(w.get("livre_gb", 0), 0)} GB)',
                         'Com menos de 10% livre o Windows perde desempenho (arquivo de paginação, atualizações e cópia de sombra precisam de espaço).', 'Libere espaço.', 'limpar'))
    if w.get('defender_tempo_real') is False:
        out.append(_prob('defender-desligado', 'windows', 'alta', 'A proteção em tempo real do Defender está desligada', 'verificação do Defender', 'Sem proteção em tempo real, o PC depende de você abrir verificações. Pode ser outro antivírus ativo.', 'Confira em Segurança do Windows se há outro antivírus; se não houver, ligue.', 'seguranca'))
    if isinstance(w.get('defender_assinatura_dias'), int) and w['defender_assinatura_dias'] > 3 and w.get('defender_tempo_real') is not False:
        out.append(_prob('defender-defasado', 'windows', 'média', 'As definições do Defender estão atrasadas', f'{w["defender_assinatura_dias"]} dias', 'Definições velhas não reconhecem ameaças novas.', 'Atualize as definições em Segurança do Windows.', 'atualizar'))
    if isinstance(w.get('uptime_dias'), (int, float)) and w['uptime_dias'] > 30:
        out.append(_prob('uptime', 'windows', 'baixa', 'O PC está ligado há mais de 30 dias sem reiniciar', f'{br(w["uptime_dias"], 0)} dias', 'Reiniciar de vez em quando libera memória e conclui atualizações pendentes.', 'Reinicie o PC (Reiniciar, não Desligar).', ''))
    if w.get('pontos_restauracao') == 0:
        out.append(_prob('sem-restauracao', 'windows', 'baixa', 'Não há ponto de restauração', 'nenhum ponto encontrado', 'Sem ponto de restauração, desfazer um problema grave é bem mais difícil.', 'Crie um ponto (o Katharos cria um antes de aplicar mudanças).', 'restaurar'))
    return out


def analisa_saude(dados, agora=None):
    """dados: o que o coletor devolveu. Devolve {'problemas': [...], 'ruido': [...], 'outros': [...], 'drivers': [...], 'por_dia': [...], 'resumo': {...}}."""
    agora = agora or datetime.now()
    grupos = [g for g in (dados.get('saude_grupos') or []) if isinstance(g, dict)]
    problemas, ruido, outros = [], [], []
    for g in grupos:
        r = explica_grupo(g)
        if r == 'ruido':
            ruido.append(g)
        elif r:
            problemas.append(r)
        else:
            outros.append(g)
    dr = analisa_drivers(dados.get('saude_drivers'), dados.get('saude_dispositivos'), grupos, agora)
    wn = analisa_windows(dados.get('saude_windows'), agora)
    todos = problemas + dr + wn
    ordem = {'alta': 0, 'média': 1, 'baixa': 2, 'info': 3}
    todos.sort(key=lambda x: (ordem[x['gravidade']], -x['n'], x['id']))
    total = int((dados.get('saude_total') or {}).get('eventos') or 0)
    return {'problemas': todos, 'ruido': ruido, 'outros': sorted(outros, key=lambda g: -int(g.get('n') or 0))[:10],
            'drivers': dados.get('saude_drivers') or [], 'por_dia': dados.get('saude_por_dia') or [],
            'resumo': {'eventos': total, 'graves': sum(1 for x in todos if x['gravidade'] == 'alta'), 'problemas': len(todos), 'ruido': sum(int(g.get('n') or 0) for g in ruido)}}


def novos_graves(atual, anterior):
    """Problemas graves de erro que não estavam no retrato anterior (ou que ganharam ocorrências): para o aviso do segundo plano."""
    ant = {x['id']: x['n'] for x in (anterior or {}).get('problemas', [])}
    return [x for x in atual['problemas'] if x['categoria'] == 'erro' and x['gravidade'] == 'alta' and x['n'] > ant.get(x['id'], 0)]


def saude_arq():
    return CASA / 'saude.json'


def coleta_saude(ctx, mostra=True):
    """Roda a coleta (só leitura), grava o retrato em ~/.katharos/saude.json e devolve a análise. Fora do Windows devolve None."""
    if not WINDOWS:
        return None
    s = roda_ps(ctx.t, SAUDE_PS, 'saude', minutos=6, mostra=False, mult=getattr(ctx, 'mult', 1.0))
    if not s.dados.get('saude_total') and not s.dados.get('saude_windows'):
        return None
    analise = analisa_saude(s.dados)
    grava_json(saude_arq(), {'quando': agora_iso(), 'analise': analise, 'versao': VERSAO})
    return analise


def le_saude():
    d = le_json(saude_arq(), None)
    return d if isinstance(d, dict) and isinstance(d.get('analise'), dict) else None


def ferramenta_saude(ctx, args):
    t = ctx.t
    t.aba('erros do Windows, drivers e o que o sistema precisa ajustar (só leitura)')
    t.paragrafo(f'Lê os erros do Visualizador de Eventos dos últimos {SAUDE_DIAS} dias, confere os drivers instalados e o estado do Windows, e explica o que cada coisa significa e o que fazer. '
                'Não muda nada. Sem internet: o programa não sabe qual é a versão mais nova de um driver, só avisa idade e quedas.', 2, 'sub')
    snap = le_saude() if getattr(args, 'ultimo', False) else None
    if snap is None:
        if not WINDOWS:
            t.erro('Só funciona no Windows.')
            return 1
        with Progresso(t, None, 'lendo os logs e os drivers') as pr:
            analise = coleta_saude(ctx)
        if not analise:
            t.erro('Não consegui ler os logs (precisa de permissão de administrador para alguns).')
            return 1
        quando = 'agora'
    else:
        analise, quando = snap['analise'], ha_quanto_iso(snap.get('quando', ''))
    r = analise['resumo']
    t.chaves([('retrato', quando), ('eventos de erro', str(r['eventos'])), ('problemas encontrados', t.p(str(r['problemas']), 'amarelo' if r['problemas'] else 'verde')),
              ('graves', t.p(str(r['graves']), 'vermelho' if r['graves'] else 'verde'))])
    cor = {'alta': 'vermelho', 'média': 'amarelo', 'baixa': 'apagado', 'info': 'apagado'}
    nomes = {'erro': 'erros do Windows', 'driver': 'drivers', 'windows': 'o que o Windows precisa'}
    for cat in ('erro', 'driver', 'windows'):
        lista_ = [x for x in analise['problemas'] if x['categoria'] == cat]
        if not lista_:
            continue
        t.titulo(nomes[cat])
        for x in lista_:
            t.item('●', cor[x['gravidade']], x['titulo'], t.p(x['gravidade'], cor[x['gravidade']]))
            t.paragrafo(x['evidencia'], 6, 'apagado')
            t.paragrafo(x['explica'], 6, 'texto')
            t.paragrafo('O que fazer: ' + x['faz'] + (f' (comando: katharos {x["comando"]})' if x['comando'] else ''), 6, 'destaque')
    if not analise['problemas']:
        t.ok('Nenhum problema encontrado nos logs, nos drivers nem no estado do Windows.')
    if analise['ruido']:
        t.nota(f'  {pl(r["ruido"], "evento", "eventos")} de ruído conhecido (DCOM 10016) foram ignorados: a Microsoft documenta que não têm efeito.', 2)
    if analise['outros']:
        t.titulo('outros erros frequentes (sem explicação no catálogo)')
        for g in analise['outros'][:6]:
            t.item('○', 'apagado', f'{g.get("provedor")} {g.get("id")}', f'{g.get("n")}x')
            t.paragrafo(corta(str(g.get('msg') or ''), 150), 6, 'apagado')
        t.nota('  Estes eu não sei explicar com segurança: a mensagem acima é a original do Windows.', 2)
    t.nota('  O painel ("painel") mostra tudo isso com gráficos; o "conselheiro" junta com as medidas.', 2)
    return 0


def avisa_saude(ctx, e):
    """No segundo plano: lê os logs no máximo a cada ~20 h e avisa só de erro grave novo (ou que cresceu) desde o retrato anterior. Falha aqui nunca derruba a manutenção."""
    try:
        if recente_h(e.get('saude_ultima'), 20):
            return []
        antes = (le_saude() or {}).get('analise')
        atual = coleta_saude(ctx, mostra=False)
        e['saude_ultima'] = agora_iso()
        if not atual:
            return []
        if antes is None:      # primeiro retrato: sem comparação, sem alarme
            return []
        return [f'{x["titulo"]} ({x["evidencia"]}). Veja: katharos saude' for x in novos_graves(atual, antes)[:3]]
    except Exception as ex:
        LOG.escreve(f'saúde falhou: {ex!r}')
        return []
