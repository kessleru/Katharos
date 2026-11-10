# ─────────────── coleta leve em segundo plano: temperatura e consumo por hora, com cuidado em jogo ───────────────
# A cada 15 min uma tarefa do Windows acorda, lê alguns contadores do próprio sistema (os mesmos que o Gerenciador de Tarefas mostra),
# com mais fontes de temperatura (LibreHardwareMonitor, driver de vídeo, nvidia-smi) e quem mais consome, e grava. As amostras viram UMA
# linha por hora (mín, máx, soma e contagem), por até ~400 dias: é o histórico de meses. O tempo real (segundo a segundo, sessões de jogo)
# é do Katharos.exe, em 63-segundoplano.py; esta tarefa também reabre ele se tiver fechado.
#
# CUIDADO COM JOGOS (anti-cheat): o coletor só lê contadores de desempenho e WMI do sistema. Nunca abre o processo de um jogo, nunca lê
# memória, nunca injeta DLL, não instala driver nem overlay. Enquanto há jogo aberto (anti-cheat, sobreposição de jogo de uma loja ou GPU acima de 60 %), ele nem olha
# a lista de processos para saber quem consome, nem chama a ferramenta da placa de vídeo: só CPU, RAM, disco, temperatura da zona térmica
# e bateria do sistema. Com `config coleta-em-jogo pausar` ele não coleta nada enquanto houver jogo aberto.
HORAS_MAX = 24 * 400
HORAS_ARQ_NOME = 'horas.jsonl'
TAREFA_AMOSTRA = 'Katharos - amostra leve'
INTERVALO_AMOSTRA_MIN = 15
# nomes de processo (minúsculas, sem .exe) que contam como "há jogo aberto": o catálogo + exemplos com anti-cheat + processos de anti-cheat conhecidos
ANTICHEAT_PROCESSOS = ['easyanticheat', 'easyanticheat_eos', 'beservice', 'vgc', 'vgtray', 'faceit', 'faceitclient', 'faceit-ac', 'battleye', 'eac_launcher']
# processos que só existem com um jogo aberto: a sobreposição das lojas (Steam, Epic, EA, Ubisoft, Xbox, NVIDIA e AMD in-game)
SOBREPOSICOES_DE_JOGO = ['gameoverlayui', 'gameoverlayui64', 'eosoverlayrenderer-win64-shipping', 'igo64', 'igoproxy64', 'upc_overlay', 'uplay_r1_loader64',
                         'gamebarftserver', 'nvsphelper64', 'amdow']
GPU_EM_JOGO = 60   # % de GPU 3D: acima disso, conta como jogo aberto mesmo sem sobreposição


def nomes_de_jogo():
    return sorted(set(ANTICHEAT_PROCESSOS) | set(SOBREPOSICOES_DE_JOGO))


AMOSTRA_PS = r'''
$__pausar = «pausar»
$__jogos = @(«jogos»)
$__nomes = @([System.Diagnostics.Process]::GetProcesses() | ForEach-Object { $_.ProcessName.ToLower() })
$__gpuU = Tenta { $g = @(Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine -Filter "Name LIKE '%engtype_3D%'" -ErrorAction Stop); if ($g.Count) { [math]::Min(100, [math]::Round(($g | Measure-Object -Property UtilizationPercentage -Sum).Sum, 0)) } else { $null } } $null
$__emJogo = [bool](@($__nomes | Where-Object { $__jogos -contains $_ }).Count) -or ($null -ne $__gpuU -and $__gpuU -ge «gpu»)
if ($__emJogo -and $__pausar) { Dado 'amostra' @{ em_jogo = $true; pausado = $true }; return }
$__cpuS = @()
for ($i = 0; $i -lt 3; $i++) {
    $p = Tenta { Get-CimInstance Win32_PerfFormattedData_Counters_ProcessorInformation -Filter "Name='_Total'" -ErrorAction Stop }
    if ($p -and $i -gt 0) { $__cpuS += $(if ($null -ne $p.PercentProcessorUtility) { [math]::Min(100, [double]$p.PercentProcessorUtility) } else { [double]$p.PercentProcessorTime }) }
    if ($i -lt 2) { Start-Sleep -Milliseconds 500 }
}
$__os = Get-CimInstance Win32_OperatingSystem
$__ramT = $__os.TotalVisibleMemorySize / 1MB
$__memD = Tenta { [double](Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory -ErrorAction Stop).AvailableMBytes / 1024 } $null
$__ramU = $(if ($null -ne $__memD) { [math]::Max(0, $__ramT - $__memD) } else { ($__os.TotalVisibleMemorySize - $__os.FreePhysicalMemory) / 1MB })
''' + TEMP_PS + r'''
$__tt = LeTemperaturas (-not $__emJogo)   # em jogo: só sensores do sistema; o driver de vídeo e a NVIDIA ficam para fora de jogo
$__temp = $__tt.cpu
$__disco = Tenta { [math]::Max(0, [math]::Min(100, 100 - [double](Get-CimInstance Win32_PerfFormattedData_PerfDisk_PhysicalDisk -Filter "Name='_Total'" -ErrorAction Stop).PercentIdleTime)) } $null
$__bat = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Select-Object -First 1
$a = @{ em_jogo = $__emJogo; ram_pct = [math]::Round($__ramU / $__ramT * 100, 1); ram_gb = [math]::Round($__ramU, 2) }
if ($__cpuS.Count) { $a.cpu = [math]::Round(($__cpuS | Measure-Object -Average).Average, 1) }
if ($null -ne $__temp) { $a.temp = $__temp; $a.temp_fonte = $__tt.cpu_fonte }
if ($null -ne $__tt.gpu) { $a.gpu_temp = $__tt.gpu; $a.gpu_fonte = $__tt.gpu_fonte }
if ($null -ne $__disco) { $a.disco = $__disco }
if ($null -ne $__gpuU) { $a.gpu_util = $__gpuU }
if ($__bat) { $a.bat = [int]$__bat.EstimatedChargeRemaining; $a.na_bateria = ([int]$__bat.BatteryStatus -eq 1) }
if (-not $__emJogo) {
    # fora de jogo dá para saber quem mais pesa e a temperatura/consumo da placa NVIDIA (ferramenta oficial da própria NVIDIA, só leitura)
    $__pp = Tenta { Get-CimInstance Win32_PerfFormattedData_PerfProc_Process -ErrorAction Stop | Where-Object { $_.Name -notmatch '^(_Total|Idle)$' } | Sort-Object PercentProcessorTime -Descending | Select-Object -First 1 } $null
    if ($__pp -and [double]$__pp.PercentProcessorTime -ge 5) { $a.top_cpu = ([string]$__pp.Name -replace '#\d+$', '') }
    $__pm = Tenta { Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 1 } $null
    if ($__pm) { $a.top_ram = [string]$__pm.ProcessName }
    $__smi = Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($__smi) {
        $__l = Tenta { (& $__smi.Source --query-gpu=temperature.gpu,power.draw --format=csv,noheader,nounits 2>$null | Select-Object -First 1) } $null
        if ($__l) { $__v = @("$__l" -split ',' | ForEach-Object { $_.Trim() }); $__d = 0.0
            if (-not $a.ContainsKey('gpu_temp') -and $__v.Count -ge 1 -and [double]::TryParse($__v[0], [ref]$__d)) { $a.gpu_temp = $__d }
            if ($__v.Count -ge 2 -and [double]::TryParse($__v[1], [System.Globalization.NumberStyles]::Float, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$__d)) { $a.gpu_w = $__d } }
    }
}
Dado 'amostra' $a
'''


SEM_SENSOR_CPU = ('o Windows não mostra o sensor deste processador. Deixe aberto o MSI Afterburner, o HWiNFO (com "Shared Memory Support"), o Core Temp '
                  'ou o LibreHardwareMonitor: o Katharos lê deles. Ou instale o LibreHardwareMonitor (winget install LibreHardwareMonitor.LibreHardwareMonitor) '
                  'e deixe aberto: o Katharos passa a ler dele')


def horas_arq():
    return CASA / HORAS_ARQ_NOME


def _acum(b, pref, v, minmax=True):
    """Soma/contagem (e mínimo/máximo) de um valor numérico num balde horário. Valor ausente não entra."""
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return
    b[pref + 'n'] = b.get(pref + 'n', 0) + 1
    b[pref + 's'] = round(b.get(pref + 's', 0) + v, 2)
    if minmax:
        b[pref + 'x'] = max(b.get(pref + 'x', v), v)
        b[pref + 'm'] = min(b.get(pref + 'm', v), v)


def agrega_hora(b, a):
    """Soma uma amostra no balde da hora. Chaves: c=CPU %, r=RAM %, d=disco ocupado %, t=temperatura, g=temperatura da GPU, u=uso da GPU,
    w=consumo da GPU (W); tr/tc=temperatura em repouso (CPU<15%) e sob carga (CPU>=50%); jg=amostras com jogo aberto; bn/b0/b1=bateria."""
    b['n'] = b.get('n', 0) + 1
    _acum(b, 'c', a.get('cpu'))
    _acum(b, 'r', a.get('ram_pct'))
    _acum(b, 'd', a.get('disco'))
    _acum(b, 't', a.get('temp'))
    _acum(b, 'g', a.get('gpu_temp'))
    _acum(b, 'u', a.get('gpu_util'))
    _acum(b, 'w', a.get('gpu_w'), minmax=False)
    cpu, temp = a.get('cpu'), a.get('temp')
    if isinstance(cpu, (int, float)) and isinstance(temp, (int, float)):
        if cpu < 15:
            _acum(b, 'tr', temp, minmax=False)
        elif cpu >= 50:
            _acum(b, 'tc', temp, minmax=False)
    if a.get('em_jogo'):
        b['jg'] = b.get('jg', 0) + 1
    if isinstance(a.get('bat'), (int, float)) and a.get('na_bateria'):
        b['bn'] = b.get('bn', 0) + 1
        b.setdefault('b0', a['bat'])
        b['b1'] = a['bat']
    for chave, campo in (('top', 'top_cpu'), ('topr', 'top_ram')):
        nome = a.get(campo)
        if isinstance(nome, str) and nome:
            d = b.setdefault(chave, {})
            d[nome[:40]] = d.get(nome[:40], 0) + 1
            if len(d) > 6:   # só os mais frequentes ficam: a linha não cresce
                for peq in sorted(d, key=d.get)[:len(d) - 6]:
                    del d[peq]
    return b


def registra_hora(a, quando=None, arq=None):
    """Soma a amostra na linha da hora atual (cria a linha se a hora é nova). Só reescreve o fim do arquivo."""
    if not isinstance(a, dict) or a.get('pausado') or not any(isinstance(a.get(k), (int, float)) for k in ('cpu', 'ram_pct', 'temp')):
        return None
    quando = quando or datetime.now()
    h = quando.strftime('%Y-%m-%dT%H')
    arq = Path(arq or horas_arq())
    arq.parent.mkdir(parents=True, exist_ok=True)
    try:
        dados = arq.read_bytes() if arq.exists() else b''
    except OSError:
        dados = b''
    linhas = dados.decode('utf-8', errors='replace').splitlines()
    ultimo = None
    if linhas:
        try:
            ultimo = json.loads(linhas[-1])
        except ValueError:
            linhas.pop()   # última linha cortada por queda de energia: descarta e segue
    if ultimo and ultimo.get('h') == h:
        linhas.pop()
        bucket = ultimo
    else:
        bucket = {'h': h}
    agrega_hora(bucket, a)
    linhas.append(json.dumps(bucket, ensure_ascii=False, separators=(',', ':')))
    if len(linhas) > HORAS_MAX + 240:   # aparar só de vez em quando: reescrever um arquivo grande a cada 15 min seria desperdício
        linhas = linhas[-HORAS_MAX:]
    tmp = arq.with_suffix('.tmp')
    tmp.write_text('\n'.join(linhas) + '\n', encoding='utf-8')
    os.replace(tmp, arq)
    return bucket


def le_horas(arq=None):
    out = []
    try:
        for l in Path(arq or horas_arq()).read_text(encoding='utf-8', errors='replace').splitlines():
            try:
                b = json.loads(l)
                b['_dt'] = datetime.strptime(b['h'], '%Y-%m-%dT%H')
                out.append(b)
            except (ValueError, KeyError, TypeError):
                continue
    except OSError:
        pass
    return sorted(out, key=lambda b: b['_dt'])


def _med(b, pref):
    return b[pref + 's'] / b[pref + 'n'] if b.get(pref + 'n') else None


def serie_diaria(horas, pref):
    """[(dia, mínimo, média, máximo)] por dia, de um valor (pref='t' temperatura, 'c' CPU...). A média pesa pelo número de amostras."""
    dias = {}
    for b in horas:
        if not b.get(pref + 'n'):
            continue
        d = dias.setdefault(b['_dt'].date(), [None, 0.0, 0, None])
        d[0] = b[pref + 'm'] if d[0] is None else min(d[0], b[pref + 'm'])
        d[3] = b[pref + 'x'] if d[3] is None else max(d[3], b[pref + 'x'])
        d[1] += b[pref + 's']
        d[2] += b[pref + 'n']
    return [(datetime.combine(dia, datetime.min.time()), v[0], v[1] / v[2], v[3]) for dia, v in sorted(dias.items())]


def serie_diaria_simples(horas, pref_s, pref_n, minimo=3):
    """[(dia, média)] só de dias com pelo menos `minimo` amostras (repouso e carga têm poucas amostras por dia)."""
    dias = {}
    for b in horas:
        if b.get(pref_n):
            d = dias.setdefault(b['_dt'].date(), [0.0, 0])
            d[0] += b[pref_s]
            d[1] += b[pref_n]
    return [(datetime.combine(dia, datetime.min.time()), s / n) for dia, (s, n) in sorted(dias.items()) if n >= minimo]


def analisa_termica(horas, limite_atencao=80, limite_grave=90):
    """Resumo honesto da temperatura (zona térmica do sistema, não o sensor do núcleo da CPU). Devolve {} se não há leituras."""
    com_t = [b for b in horas if b.get('tn')]
    if not com_t:
        return {}
    pico = max(com_t, key=lambda b: b['tx'])
    r = {'horas': len(com_t), 'dias': len({b['_dt'].date() for b in com_t}), 'maxima': pico['tx'], 'maxima_quando': pico['_dt'],
         'horas_atencao': sum(1 for b in com_t if b['tx'] >= limite_atencao), 'horas_graves': sum(1 for b in com_t if b['tx'] >= limite_grave),
         'media_repouso': None, 'media_carga': None, 'achados': [], 'tem_gpu': any(b.get('gn') for b in horas)}
    tr = [(b['trs'], b['trn']) for b in horas if b.get('trn')]
    tc = [(b['tcs'], b['tcn']) for b in horas if b.get('tcn')]
    if tr and sum(n for _, n in tr) >= 6:
        r['media_repouso'] = sum(s for s, _ in tr) / sum(n for _, n in tr)
    if tc and sum(n for _, n in tc) >= 6:
        r['media_carga'] = sum(s for s, _ in tc) / sum(n for _, n in tc)
    if r['horas_graves'] >= 2:
        r['achados'].append(('alta', f'a temperatura passou de {limite_grave} °C em {pl(r["horas_graves"], "hora", "horas")} (máxima {br(r["maxima"], 0)} °C em {pico["_dt"]:%d/%m %H}h): '
                                     'confira ventoinha, poeira, pasta térmica e fluxo de ar do gabinete'))
    elif r['horas_atencao'] >= 6 and r['horas_atencao'] / r['horas'] >= 0.10:
        r['achados'].append(('média', f'a temperatura passou de {limite_atencao} °C em {r["horas_atencao"]} de {r["horas"]} horas medidas ({br(r["horas_atencao"] / r["horas"] * 100, 0)}%)'))
    rep = serie_diaria_simples(horas, 'trs', 'trn')
    if len(rep) >= 14 and (rep[-1][0] - rep[0][0]).days >= 14:
        valores = [v for _, v in rep]
        antes, depois = _tercos([(d, v) for d, v in rep])
        # ruído = variação de um dia para o seguinte (a subida lenta que queremos detectar não entra nessa conta)
        ruido = _mediana([abs(b - a) for a, b in zip(valores, valores[1:])]) * 3
        if depois - antes >= max(4.0, ruido):
            r['achados'].append(('média', f'a temperatura em repouso subiu de {br(antes, 0)} para {br(depois, 0)} °C em {(rep[-1][0] - rep[0][0]).days} dias '
                                          '(mediana do começo e do fim). O clima do ambiente também pesa; se continuar subindo, limpe o PC e troque a pasta térmica'))
    return r


def amostra_leve(ctx, args=None):
    """Lê o PC (leve, uns 2 s) e soma na linha da hora. Devolve a amostra, ou None."""
    if not WINDOWS:
        return None
    pausar = config('coleta-em-jogo', 'segura') == 'pausar'
    corpo = ps_monta(AMOSTRA_PS, pausar='$true' if pausar else '$false', jogos=', '.join(psq(n) for n in nomes_de_jogo()), gpu=str(GPU_EM_JOGO))
    s = roda_ps(ctx.t, corpo, 'amostra', minutos=1, mostra=False)
    a = s.dados.get('amostra')
    if isinstance(a, dict) and not a.get('pausado'):
        try:
            completa_temperaturas(a, 'temp', 'temp_fonte', 'gpu_temp', 'gpu_fonte')
        except Exception as e:
            LOG.escreve(f'temperatura pelo executável: {e!r}')
    if isinstance(a, dict):
        registra_hora(a)
        if not a.get('pausado'):
            grava_ultima_amostra(a)
    return a


def ferramenta_amostrar(ctx, args):
    t = ctx.t
    if not WINDOWS:
        t.erro('só funciona no Windows.')
        return 1
    agendada = getattr(args, 'agendada', False)
    if agendada:
        if leitura_pausada():   # o ícone pausou por 1 hora
            return 0
        if WINDOWS and estado().get('segundo_plano') == 'sim':
            garante_segundo_plano(ctx)   # o executável caiu ou o PC acabou de ligar: abre de novo
        elif WINDOWS and not estado().get('bandeja'):   # coleta ligada numa versão sem ícone: liga o ícone uma vez (a tarefa é do seu usuário)
            try:
                instala_bandeja(ctx)
            except Exception as e:
                LOG.escreve(f'ícone: {e!r}')
            if not estado().get('bandeja'):
                marca_estado('bandeja', 'falhou')
        try:   # versão nova: o ícone passa a usar o script dela na próxima vez que abrir
            b = bandeja_arq()
            if b.is_file() and f"$VERSAO = '{VERSAO}'" not in b.read_text(encoding='utf-8-sig', errors='replace'):
                escreve_bandeja()
        except OSError:
            pass
        prioridade_baixa()
    a = amostra_leve(ctx, args)
    if agendada:
        return 0
    t.aba('uma leitura leve do sistema, somada ao histórico por hora')
    if not a:
        t.erro('Não consegui ler o sistema.')
        return 1
    if a.get('pausado'):
        t.nota('  Há um jogo aberto e a coleta está em "pausar": nada foi lido. (config coleta-em-jogo segura liga de novo a leitura só do sistema.)', 2)
        return 0
    t.chaves([('CPU', f'{br(a.get("cpu"), 0)} %' if 'cpu' in a else '-'), ('RAM', f'{br(a.get("ram_pct"), 0)} % ({br(a.get("ram_gb"), 1)} GB)'),
              ('disco ocupado', f'{br(a.get("disco"), 0)} %' if 'disco' in a else '-'), ('CPU temperatura', f'{br(a.get("temp"), 0)} °C ({a.get("temp_fonte") or "zona térmica"})' if 'temp' in a else SEM_SENSOR_CPU),
              ('GPU temperatura', f'{br(a.get("gpu_temp"), 0)} °C ({a.get("gpu_fonte") or "nvidia-smi"})' if 'gpu_temp' in a else ('pulada: jogo aberto' if a.get('em_jogo') else 'o driver de vídeo não informa')),
              ('jogo aberto', 'sim: leitura só do sistema' if a.get('em_jogo') else 'não')])
    return 0


def comando_da_amostra():
    """(executável, argumentos) da tarefa de 15 min. Preferência por pythonw.exe: não tem console, então nada pisca na tela (um jogo em tela cheia
    poderia ser minimizado por uma janela que abre e fecha). Sem pythonw, cai no PowerShell escondido e avisa."""
    script = CASA / 'katharos.py'
    pw = Path(sys.executable).with_name('pythonw.exe')
    if pw.exists():
        return str(pw), subprocess.list2cmdline([str(script), 'amostrar', '--agendada', '--sem-cor']), True
    py = sys.executable
    return 'powershell.exe', ('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "& \'' + py + '\' \'' + str(script) + '\' amostrar --agendada --sem-cor"'), False


def instala_amostra(ctx):
    """Cria a tarefa de 15 min. Roda com o PC em uso e na bateria (é quando há o que medir), prioridade baixa, no máximo 2 min."""
    t = ctx.t
    script = CASA / 'katharos.py'
    shutil.copy2(Path(__file__).resolve(), script)
    exe, arg, sem_janela = comando_da_amostra()
    # sem privilégio elevado de propósito: a leitura não precisa dele (o contador de zona térmica funciona sem administrador), e uma tarefa
    # elevada executando um script em pasta do usuário seria uma porta de escalada de privilégio
    corpo = ps_monta(r'''
$__a = New-ScheduledTaskAction -Execute «exe» -Argument «arg»
$__t = New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Minutes «min»)
$__p = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
$__s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 2) -Priority 7 -MultipleInstances IgnoreNew
if ($TESTE) { Plano 'criar a tarefa de leitura leve a cada 15 minutos'; return }
Register-ScheduledTask -TaskName «nome» -Action $__a -Trigger $__t -Principal $__p -Settings $__s -Description 'Leitura leve de temperatura e consumo a cada 15 minutos, sem janela. Criada pelo Katharos.' -Force | Out-Null
Feito 'leitura leve ligada: a cada «min» min, sem janela'
''', exe=psq(exe), arg=psq(arg), min=INTERVALO_AMOSTRA_MIN, nome=psq(TAREFA_AMOSTRA))
    s = roda_ps(t, corpo, 'agendar-amostra', minutos=2)
    if not (s.ok and not s.erros):
        return 1
    marca_estado('amostra_ligada', agora_iso())
    try:   # o acompanhamento contínuo inclui o segundo plano: o Katharos.exe, ou o ícone simples se só há o katharos.py
        if not instala_segundo_plano(ctx, mostrar=True, quieto=True):
            instala_bandeja(ctx)
    except Exception as e:
        LOG.escreve(f'ícone: {e!r}')
    if not sem_janela:
        t.aviso('Não achei o pythonw.exe: a leitura de 15 min usa um PowerShell escondido, que pode piscar na tela por um instante. '
                'Instale o Python de python.org (traz o pythonw.exe) se isso incomodar durante jogos em tela cheia.')
    return 0


def remove_amostra(ctx):
    if estado().get('bandeja') == 'sim':   # o ícone simples só existe junto da leitura de 15 min; o segundo plano (executável) é independente
        remove_bandeja(ctx)
    roda_ps(ctx.t, f"Unregister-ScheduledTask -TaskName {psq(TAREFA_AMOSTRA)} -Confirm:$false -ErrorAction SilentlyContinue", 'remover-amostra', minutos=1, mostra=False)
    e = estado()
    e.pop('amostra_ligada', None)
    salva_estado(e)
