

# ███████████████████████████████████████████████████████████████████████████
#
#   NÚCLEO · utilidades, preferências, PowerShell vigiado, backup e reversão
#
# ███████████████████████████████████████████████████████████████████████████

WINDOWS = os.name == 'nt'
APP = 'katharos'
CASA = Path.home() / '.katharos'
MODOS = ('seguro', 'equilibrado', 'extremo')
NIVEL_MODO = {'seguro': 1, 'equilibrado': 2, 'extremo': 3}
NOME_NIVEL = {0: 'opcional', 1: 'seguro', 2: 'equilibrado', 3: 'extremo'}
# O que cada grupo da tela de escolha quer dizer, em poucas palavras: é o que a pessoa lê ao lado do nome.
# Um modo marca o grupo dele e os de cima; "opcional" nenhum modo marca.
ORDEM_NIVEL = (1, 2, 3, 0)
EXPLICA_NIVEL = {1: 'não tira nada de você', 2: 'tira o que quase ninguém usa', 3: 'tira algum recurso (cada item diz qual)',
                 0: 'depende do seu caso: só entra se você marcar'}
COR_NIVEL = {0: 'apagado', 1: 'verde', 2: 'azul', 3: 'pessego'}

EXPLICA_MODOS = [
    ('seguro', 'verde', 'Só o que não tem contrapartida: telemetria, anúncios, lixo, apps de propaganda, '
     'tarefas inúteis, Modo de Jogo. Bom para PC de trabalho ou de outra pessoa.'),
    ('equilibrado', 'azul', 'O seguro mais o que quase ninguém usa: serviços de empresa e de telefone, '
     'Xbox (se não joga), IA do Windows, widgets, efeitos visuais, caches, sem gravação de fundo do Xbox e, se há jogos instalados, '
     'mouse sem aceleração. É o recomendado.'),
    ('extremo', 'pessego', 'Tudo o que pode ajudar neste PC: energia no máximo e, se há jogos instalados, o máximo de FPS '
     '(placa de vídeo sempre no desempenho, menos atraso de rede e de entrada); desliga sensores, área de trabalho remota, '
     'scanner, localização, hibernação no SSD. Você perde recursos (cada item diz quais).'),
]

PADROES = {'modo': 'equilibrado', 'explicacao': 'curta', 'cores': 'automático', 'simbolos': 'automático',
           'grandes-mb': '500', 'navegador': 'nenhum', 'confirmar': 'risco', 'protegidos': '', 'coleta-em-jogo': 'segura', 'abrir-relatorio': 'perguntar', 'tempo-real': '1', 'avisos': 'sim', 'fps': 'sim', 'energia-automatica': 'nao', 'atualizacoes': 'avisar',
           'avisos-intervalo': '6', 'avisos-no-jogo': 'so-grave', 'resumo-diario': 'nao', 'motor-nunca': '', 'canal': 'estavel'}
DESCR_CONFIG = {
    'modo': ('modo padrão', 'seguro, equilibrado ou extremo: o que vem marcado em cada tela'),
    'explicacao': ('explicações', 'curta (uma linha por item; "? número" explica) ou completa (o que faz, ganho e custo de todos)'),
    'cores': ('cores', 'automático ou sem cor'),
    'simbolos': ('símbolos', 'automático ou simples (para terminal que mostra quadradinhos)'),
    'grandes-mb': ('arquivo grande', 'a partir de quantos MB o "grandes" mostra um arquivo'),
    'navegador': ('navegador leve', 'brave ou nenhum: se o turbo instala o Brave enxuto'),
    'confirmar': ('"manter alterações?"', 'risco (padrão): depois de mudar serviços, jogos, energia, disco ou visual, pergunta se está tudo bem e desfaz '
                  'sozinho se você não responder; sempre; ou nunca'),
    'abrir-relatorio': ('abrir o relatório', 'perguntar (padrão: uma tecla no fim do raio-x, da segurança e do turbo), sempre (abre a pasta sozinho) ou nunca'),
    'coleta-em-jogo': ('acompanhamento com jogo aberto', 'segura (padrão): continua lendo tudo, como o Gerenciador de Tarefas (sem abrir o processo do jogo); ou pausar: não lê nada enquanto houver jogo aberto'),
    'tempo-real': ('ritmo do segundo plano', 'de quantos em quantos segundos o Katharos.exe lê o PC: 1 (padrão), 2, 5 ou 10'),
    'energia-automatica': ('notebook: plano de energia sozinho na tomada e na bateria', 'nao (padrão) ou sim: o segundo plano troca o plano de '
                           'energia quando você liga ou tira o carregador (escolhe os planos ao ligar; desligar volta o plano de antes)'),
    'avisos-intervalo': ('horas entre dois avisos do mesmo tipo', '6 (padrão); de 1 a 48. Calor grave avisa sempre'),
    'avisos-no-jogo': ('avisos durante o jogo', 'so-grave (padrão): só calor grave; nunca; ou todos'),
    'resumo-diario': ('um resumo por dia no lugar de avisos soltos', 'nao (padrão) ou sim: um aviso por dia com o que o motor achou'),
    'motor-nunca': ('o que o motor nunca propõe', 'comandos separados por vírgula (ex.: turbo,energia)'),
    'canal': ('canal de atualização do Katharos com janelas', 'estavel (padrão) ou previa (versões de teste antes de todo mundo)'),
    'atualizacoes': ('atualizações do Katharos com janelas', 'avisar (padrão): baixa a versão nova e pergunta antes de reiniciar; automatico: '
                     'troca quando você fechar; nunca: não confere'),
    'fps': ('FPS nos jogos', 'sim (padrão): mede FPS, 1% low e travadas durante os jogos, pelo PresentMon (precisa liberar uma vez: segundo-plano, opção f); ou nao'),
    'avisos': ('avisos do segundo plano', 'sim (padrão): notificação quando algo fica no limite (calor, RAM cheia, CPU freando); ou nao'),
    'protegidos': ('itens que nunca mexo', 'ids separados por vírgula (ex.: rdp,servicos:xbox,ini:OneDrive). O id aparece em "v N" na tela de escolha'),
}


def pasta(*partes):
    d = CASA.joinpath(*partes)
    d.mkdir(parents=True, exist_ok=True)
    return d


AVISOS_INICIO = []   # avisos de coisas que deram errado antes de haver terminal (mostrados no começo)
AVISO_VIVO = None    # depois que o terminal existe, os avisos aparecem na hora


def le_json(arq, padrao):
    """Lê um JSON. Arquivo que não existe devolve o padrão. Arquivo que existe mas está ilegível é guardado ao lado
    (nome.corrompido-DATA) e a pessoa é avisada: antes isso zerava o estado sem ninguém ver."""
    arq = Path(arq)
    try:
        with open(arq, encoding='utf-8-sig') as f:
            return json.load(f)
    except FileNotFoundError:
        return padrao
    except ValueError:
        try:
            copia = arq.with_name(f'{arq.name}.corrompido-{datetime.now():%Y%m%d-%H%M%S}')
            os.replace(arq, copia)
            msg = f'{arq.name} estava ilegível; guardei uma cópia em {copia.name} e recomecei com o padrão.'
            if AVISO_VIVO:
                AVISO_VIVO(msg)
            else:
                AVISOS_INICIO.append(msg)
            lg = globals().get('LOG')
            if lg:
                lg.escreve(msg)
        except OSError:
            pass
        return padrao
    except OSError:
        return padrao


def grava_json(arq, dados):
    arq = Path(arq)
    arq.parent.mkdir(parents=True, exist_ok=True)
    tmp = arq.with_name(f'{arq.name}.{os.getpid()}.tmp')   # um por processo: o motor comum, o elevado e a manutenção gravam juntos
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
    os.replace(tmp, arq)


def config(chave, padrao=None):
    v = le_json(CASA / 'config.json', {}).get(chave)
    return v if v not in (None, '') else (padrao if padrao is not None else PADROES.get(chave))


def salva_config(chave, valor):
    c = le_json(CASA / 'config.json', {})
    if valor in (None, ''):
        c.pop(chave, None)
    else:
        c[chave] = valor
    grava_json(CASA / 'config.json', c)


def estado():
    return le_json(CASA / 'estado.json', {})


def salva_estado(e):
    grava_json(CASA / 'estado.json', e)


def marca_estado(chave, valor):
    e = estado()
    e[chave] = valor
    salva_estado(e)


def agora_iso():
    return datetime.now().replace(microsecond=0).isoformat()


def carimbo():
    return datetime.now().strftime('%Y-%m-%d-%H%M%S')


def ha_quanto_iso(iso):
    try:
        s = (datetime.now() - datetime.fromisoformat(iso)).total_seconds()
    except (TypeError, ValueError):
        return ''
    if s < 3600:
        return 'agora há pouco'
    if s < 86400:
        return f'há {int(s // 3600)} h'
    d = int(s // 86400)
    return 'ontem' if d == 1 else f'há {d} dias'


def pl(n, um, varios=None):
    return f'{n} {um if n == 1 else (varios or um + "s")}'


def br(x, casas=1):
    """Número no formato brasileiro."""
    try:
        s = f'{float(x):,.{casas}f}'
    except (TypeError, ValueError):
        return '-'
    return s.replace(',', '#').replace('.', ',').replace('#', '.')


def gb(x, casas=1):
    return '-' if x in (None, '') else f'{br(x, casas)} GB'


def lista(v):
    """O PowerShell 5.1 às vezes embrulha listas em {"value": [...], "Count": n}, ou devolve um item solto."""
    if v is None:
        return []
    if isinstance(v, dict) and 'value' in v and ('Count' in v or 'count' in v):
        v = v['value']
    return v if isinstance(v, list) else [v]


def psq(s):
    """Texto como literal de PowerShell entre aspas simples. O PowerShell também fecha a string com as aspas tipográficas
    (‘ ’ ‚ ‛), comuns em nome de arquivo e de programa: cada uma é dobrada como a ' comum."""
    return "'" + re.sub("['‘’‚‛]", lambda m: m.group(0) * 2, str(s)) + "'"


def ps_lista(itens):
    return '@(' + ','.join(psq(i) for i in itens) + ')'


def ps_monta(modelo, **valores):
    """Troca «nome» pelo valor (o PowerShell já usa $, {} e % demais para format())."""
    for k, v in valores.items():
        modelo = modelo.replace('«' + k + '»', str(v))
    return modelo


# ─────────────── Windows: administrador, pacote MSIX, energia, CPU ───────────────

def eh_admin():
    if not WINDOWS:
        return hasattr(os, 'geteuid') and os.geteuid() == 0
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def dentro_de_pacote():
    """True se o Python roda dentro de um pacote MSIX (o Python da Microsoft Store, por exemplo).
    Aí o HKCU e o AppData gravados são uma cópia virtual e as mudanças do usuário não valem de verdade."""
    if not WINDOWS:
        return False
    try:
        n = ctypes.c_uint32(0)
        r = ctypes.windll.kernel32.GetCurrentPackageFullName(ctypes.byref(n), None)
        return r != 15700  # 15700 = APPMODEL_ERROR_NO_PACKAGE (fora); 122 = buffer pequeno (dentro)
    except Exception:
        return 'WindowsApps' in sys.executable


def eleva(argv):
    """Abre o katharos de novo como administrador (o Windows mostra o aviso do UAC)."""
    script = str(Path(__file__).resolve())
    params = subprocess.list2cmdline([script] + list(argv))
    try:
        r = ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, params, str(Path.cwd()), 1)
        return r > 32
    except Exception:
        return False


class _SPS(ctypes.Structure):
    _fields_ = [('ACLineStatus', ctypes.c_ubyte), ('BatteryFlag', ctypes.c_ubyte), ('BatteryLifePercent', ctypes.c_ubyte),
                ('SystemStatusFlag', ctypes.c_ubyte), ('BatteryLifeTime', ctypes.c_ulong), ('BatteryFullLifeTime', ctypes.c_ulong)]


def energia_agora():
    """(na_tomada, carga%) ou (True, None) quando não há bateria."""
    if not WINDOWS:
        return True, None
    s = _SPS()
    try:
        if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s)):
            return True, None
    except Exception:
        return True, None
    sem_bateria = s.BatteryFlag == 128 or s.BatteryLifePercent == 255
    return s.ACLineStatus != 0, (None if sem_bateria else s.BatteryLifePercent)


class _FT(ctypes.Structure):
    _fields_ = [('lo', ctypes.c_ulong), ('hi', ctypes.c_ulong)]


def _tempos_cpu():
    o, k, u = _FT(), _FT(), _FT()
    if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(o), ctypes.byref(k), ctypes.byref(u)):
        return None
    f = lambda x: (x.hi << 32) | x.lo
    return f(o), f(k), f(u)


class MedidorCPU:
    """CPU total do sistema entre duas leituras (GetSystemTimes: barato, não usa WMI)."""

    def __init__(self):
        self.antes = _tempos_cpu() if WINDOWS else None

    def le(self):
        if not WINDOWS:
            return 0.0
        agora = _tempos_cpu()
        if not agora or not self.antes:
            self.antes = agora
            return 0.0
        oc, kc, uc = (a - b for a, b in zip(agora, self.antes))
        self.antes = agora
        total = kc + uc  # o tempo de kernel já inclui o ocioso
        return max(0.0, min(100.0, 100.0 * (total - oc) / total)) if total else 0.0


def prioridade_baixa():
    if WINDOWS:
        try:
            ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x40)  # IDLE
        except Exception:
            pass


def sem_janela_global():
    """Sem console (pythonw, tarefa agendada): todo processo filho nasce sem janela (CREATE_NO_WINDOW). Sem isto, qualquer powershell.exe,
    tasklist ou taskkill abriria e fecharia uma janela, e isso pode tirar um jogo da tela cheia. Com console (uso normal), não muda nada."""
    if not WINDOWS or getattr(subprocess.Popen, '_sem_janela', False):
        return False
    try:
        if ctypes.windll.kernel32.GetConsoleWindow():
            return False
    except Exception:
        return False
    original = subprocess.Popen.__init__

    def init(self, *a, **kw):
        kw['creationflags'] = kw.get('creationflags', 0) | 0x08000000
        original(self, *a, **kw)
    subprocess.Popen.__init__ = init
    subprocess.Popen._sem_janela = True
    return True


def desliga_edicao_rapida():
    """Clique na janela do console não pausa mais o programa (modo de seleção do Windows)."""
    if not WINDOWS:
        return
    try:
        k = ctypes.windll.kernel32
        h = k.GetStdHandle(-10)
        m = ctypes.c_uint32()
        if k.GetConsoleMode(h, ctypes.byref(m)):
            k.SetConsoleMode(h, (m.value & ~0x0040) | 0x0080)
    except Exception:
        pass


_CTRL_TELA = re.compile('[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]')


def tela(s):
    """Texto que veio de fora (nome de arquivo, saída de programa) sem sequências de controle: um nome de arquivo
    com ESC não consegue mexer no seu terminal nem esconder texto."""
    return _CTRL_TELA.sub('', str(s))


def decodifica(b):
    return tela(_decodifica(b))


def _decodifica(b):
    """Saída de ferramentas do Windows: UTF-8, UTF-16 (sfc) ou a página de código do console (DISM, chkdsk)."""
    if not b:
        return ''
    if b.count(b'\x00') > len(b) // 4:
        try:
            return b.decode('utf-16-le', errors='replace').replace('\x00', '')
        except Exception:
            pass
    try:
        return b.decode('utf-8')
    except UnicodeDecodeError:
        pass
    for cod in ('oem', 'cp850', 'latin-1'):
        try:
            return b.decode(cod)
        except (LookupError, UnicodeDecodeError):
            continue
    return b.decode('latin-1', errors='replace')


def env_ps():
    """O ambiente para o Windows PowerShell 5.1: sem os caminhos de módulo do PowerShell 7 (herdados quando o Katharos foi aberto
    de dentro do pwsh), que o 5.1 não carrega e fariam comandos como Get-FileHash e Set-Acl "não existirem"."""
    env = dict(os.environ)
    mp = env.get('PSModulePath')
    if mp:
        env['PSModulePath'] = ';'.join(x for x in mp.split(';')
                                              if 'WindowsPowerShell' in x or not re.search(r'[\\/]PowerShell[\\/]', x, re.I))
    return env


def mata_arvore(pid):
    if WINDOWS:
        subprocess.run(['taskkill', '/PID', str(pid), '/T', '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        try:
            os.kill(pid, 9)
        except OSError:
            pass


class Log:
    """Histórico em ~/.katharos/logs/AAAA-MM-DD.log: tudo o que cada etapa disse."""

    def __init__(self):
        self.arq = pasta('logs') / f'{datetime.now():%Y-%m-%d}.log'

    def escreve(self, txt):
        try:
            with open(self.arq, 'a', encoding='utf-8') as f:
                f.write(f'{datetime.now():%H:%M:%S} {txt}\n')
        except OSError:
            pass


LOG = Log()


# ─────────────── PowerShell vigiado ───────────────
# Cada etapa roda num powershell.exe filho, com limite de tempo. Ele conversa com o Python por linhas
# "@@tipo|texto": feito, plano (modo teste), ok, aviso, erro, info, vivo (o que está fazendo agora) e
# dado (JSON). O resto da saída vai só para o log.

PRELUDIO_PS = r'''
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
try { [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false } catch {}
$TESTE = ($env:OTM_TESTE -eq '1')
$BK = $env:OTM_BK
$CASA = $env:OTM_CASA
$MULT = 1.0
if ($env:OTM_MULT) { $MULT = [double]::Parse($env:OTM_MULT, [Globalization.CultureInfo]::InvariantCulture) }
$script:MUDOU = 0
$script:PLANOS = 0

function Diz([string]$Tipo, [string]$Texto) {
    $Texto = ($Texto -replace '[\r\n]+', ' ').Trim()
    [Console]::Out.WriteLine('@@' + $Tipo + '|' + $Texto)
    [Console]::Out.Flush()
}
function Feito([string]$T) { $script:MUDOU++; Diz 'feito' $T }
function Plano([string]$T) { $script:PLANOS++; Diz 'plano' $T }
function Ok([string]$T) { Diz 'ok' $T }
function Aviso([string]$T) { Diz 'aviso' $T }
function Erro([string]$T) { Diz 'erro' $T }
function Info([string]$T) { Diz 'info' $T }
function Vivo([string]$T) { Diz 'vivo' $T }
function Lista($X) {
    $l = New-Object System.Collections.Generic.List[object]
    foreach ($i in $X) { if ($null -ne $i) { $l.Add($i) } }
    return ,$l.ToArray()
}
function Dado([string]$Chave, $Obj) {
    $j = ConvertTo-Json -InputObject $Obj -Compress -Depth 6
    [Console]::Out.WriteLine('@@dado|' + $Chave + '|' + ($j -replace '[\r\n]+', ' '))
    [Console]::Out.Flush()
}
function Tenta([scriptblock]$B, $Padrao = $null) { try { & $B } catch { $Padrao } }

# ---- backup: cada mudança guarda o valor de antes, uma vez, para o desfazer voltar exatamente ----
$script:_BkMem = $null
function _BkCarrega {
    if ($null -ne $script:_BkMem) { return }
    $script:_BkMem = @{}
    if (-not $BK) { return }
    $f = Join-Path $BK 'mudancas.jsonl'
    if (Test-Path -LiteralPath $f) {
        foreach ($l in (Get-Content -LiteralPath $f -Encoding UTF8)) {
            if ($l) { try { $o = ConvertFrom-Json $l; $script:_BkMem[[string]$o.k] = $true } catch {} }
        }
    }
}
function _BkGuarda([string]$Chave, [hashtable]$Obj) {
    if (-not $BK) { return }
    _BkCarrega
    if ($script:_BkMem.ContainsKey($Chave)) { return }
    New-Item -ItemType Directory -Force -Path $BK | Out-Null
    $Obj['k'] = $Chave
    Add-Content -LiteralPath (Join-Path $BK 'mudancas.jsonl') -Value (ConvertTo-Json -InputObject $Obj -Compress -Depth 4) -Encoding UTF8
    $script:_BkMem[$Chave] = $true
}
function _Iguais($A, $B) {
    if (($A -is [byte[]]) -or ($B -is [byte[]])) { return ((@($A) -join ',') -eq (@($B) -join ',')) }
    if (($A -is [array]) -or ($B -is [array])) { return ((@($A) -join "`n") -eq (@($B) -join "`n")) }
    return ([string]$A -eq [string]$B)
}
function _LeValor([string]$Path, [string]$Name) {
    $r = @{ existe = $false; tipo = $null; valor = $null }
    $n = $Name; if ($n -eq '(default)') { $n = '' }
    try {
        $k = Get-Item -LiteralPath $Path -ErrorAction Stop
        if (@($k.GetValueNames()) -contains $n) {
            $r.existe = $true
            $r.tipo = $k.GetValueKind($n).ToString()
            $r.valor = $k.GetValue($n, $null, 'DoNotExpandEnvironmentNames')
        }
    } catch {}
    return $r
}
# UCPD (Windows 11 24H2 e 10 atualizado): um driver da Microsoft não deixa gravar alguns valores do registro. Esses não contam como
# "falta fazer" nem como erro: o item usa a política que funciona e diz por que aquele valor ficou.
$script:UCPD = $null
function _Protegido([string]$Path, [string]$Name) {
    if (@('TaskbarDa') -notcontains $Name) { return $false }   # = UCPD_PROTEGIDOS (28-windows.py); um teste confere
    if ($null -eq $script:UCPD) { $script:UCPD = [bool](Get-Service UCPD -ErrorAction SilentlyContinue | Where-Object Status -eq 'Running') }
    return $script:UCPD
}
function Set-Valor([string]$Path, [string]$Name, $Value, [string]$Type = 'DWord', [string]$Rotulo = '') {
    if (_Protegido $Path $Name) {
        $b = _LeValor $Path $Name
        if (-not ($b.existe -and (_Iguais $b.valor $Value))) { if (-not $TESTE) { Info ("{0}: o Windows protege este valor nesta versao (UCPD); ficou como estava" -f $Name) } }
        return $false
    }
    $a = _LeValor $Path $Name
    # igual só se o valor E o tipo batem: uma política gravada como texto ("0") não vale como número para o Windows
    if ($a.existe -and (_Iguais $a.valor $Value) -and ($Name -eq '(default)' -or [string]$a.tipo -eq $Type -or (@('String','ExpandString') -contains [string]$a.tipo -and @('String','ExpandString') -contains $Type))) { return $false }
    if ($TESTE) {
        if ($Rotulo) { Plano $Rotulo } else { $vv = $Value; if ($Value -is [byte[]]) { $vv = 'binario' }; Plano ("{0} = {1}  ({2})" -f $Name, $vv, (Split-Path $Path -Leaf)) }
        return $true
    }
    $v = $a.valor
    if ($a.tipo -eq 'Binary' -and $null -ne $a.valor) { $v = [Convert]::ToBase64String([byte[]]$a.valor) }
    _BkGuarda ("reg|" + $Path + "|" + $Name) @{ t = 'reg'; p = $Path; n = $Name; existe = $a.existe; tipo = $a.tipo; v = $v; chave = [bool](Test-Path -LiteralPath $Path) }
    try {
        if (-not (Test-Path -LiteralPath $Path)) { New-Item -Path $Path -Force -ErrorAction Stop | Out-Null }
        if ($Name -eq '(default)') { Set-ItemProperty -LiteralPath $Path -Name '(default)' -Value $Value -ErrorAction Stop }
        else { New-ItemProperty -LiteralPath $Path -Name $Name -Value $Value -PropertyType $Type -Force -ErrorAction Stop | Out-Null }
        $script:MUDOU++
        return $true
    } catch { Aviso ("nao gravou {0} em {1}: {2}" -f $Name, $Path, $_.Exception.Message); return $false }
}
function Remove-Valor([string]$Path, [string]$Name, [string]$Rotulo = '') {
    $a = _LeValor $Path $Name
    if (-not $a.existe) { return $false }
    if ($TESTE) { if ($Rotulo) { Plano $Rotulo } else { Plano ("apagar {0} ({1})" -f $Name, (Split-Path $Path -Leaf)) }; return $true }
    $v = $a.valor
    if ($a.tipo -eq 'Binary' -and $null -ne $a.valor) { $v = [Convert]::ToBase64String([byte[]]$a.valor) }
    _BkGuarda ("reg|" + $Path + "|" + $Name) @{ t = 'reg'; p = $Path; n = $Name; existe = $true; tipo = $a.tipo; v = $v }
    try { Remove-ItemProperty -LiteralPath $Path -Name $Name -Force -ErrorAction Stop; $script:MUDOU++; return $true } catch { Aviso ("nao apagou {0} em {1}: {2}" -f $Name, $Path, $_.Exception.Message); return $false }
}
function Get-ModoServico([string]$Nome) {
    $s = Get-CimInstance Win32_Service -Filter ("Name='" + $Nome + "'") -ErrorAction SilentlyContinue
    if (-not $s) { return $null }
    $m = switch ($s.StartMode) { 'Auto' { if ($s.DelayedAutoStart) { 'delayed-auto' } else { 'auto' } } 'Manual' { 'demand' } 'Disabled' { 'disabled' } default { ([string]$s.StartMode).ToLower() } }
    return @{ modo = $m; rodando = ($s.State -eq 'Running'); nome = $s.DisplayName }
}
function Set-Servico([string]$Nome, [string]$Modo, [switch]$Parar) {
    # Modo: disabled | demand | auto | delayed-auto
    $s = Get-ModoServico $Nome
    if (-not $s) { return $false }
    $parar = $Parar -and $s.rodando
    if ($s.modo -eq $Modo -and -not $parar) { return $false }
    $nomes = @{ 'disabled' = 'desativado'; 'demand' = 'manual'; 'auto' = 'automatico'; 'delayed-auto' = 'automatico atrasado' }
    if ($TESTE) { Plano ("servico {0} ({1}): {2} -> {3}" -f $Nome, $s.nome, $nomes[$s.modo], $nomes[$Modo]); return $true }
    _BkGuarda ("svc|" + $Nome) @{ t = 'svc'; n = $Nome; modo = $s.modo; rodando = $s.rodando }
    if ($s.modo -ne $Modo) {
        $o = & sc.exe config $Nome start= $Modo 2>&1
        if ($LASTEXITCODE -ne 0) { Aviso ("servico {0} nao mudou (protegido pelo Windows): {1}" -f $Nome, (($o | Out-String).Trim())); return $false }
    }
    if ($parar) { & sc.exe stop $Nome 2>&1 | Out-Null }
    $script:MUDOU++
    return $true
}
function Set-Tarefa([string]$Completo, [bool]$Ligada) {
    $i = $Completo.LastIndexOf('\')
    $p = $Completo.Substring(0, $i + 1); $n = $Completo.Substring($i + 1)
    $tk = Get-ScheduledTask -TaskPath $p -TaskName $n -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $tk) { return $false }
    $esta = ($tk.State -ne 'Disabled')
    if ($esta -eq $Ligada) { return $false }
    if ($TESTE) { $o = 'desligar'; if ($Ligada) { $o = 'ligar' }; Plano ("{0} tarefa {1}" -f $o, $n); return $true }
    _BkGuarda ("tarefa|" + $Completo) @{ t = 'tarefa'; n = $Completo; ligada = $esta }
    try {
        if ($Ligada) { $tk | Enable-ScheduledTask -ErrorAction Stop | Out-Null } else { $tk | Disable-ScheduledTask -ErrorAction Stop | Out-Null }
        $script:MUDOU++
        return $true
    } catch { Aviso ("tarefa {0}: {1}" -f $n, $_.Exception.Message); return $false }
}
function Desliga-Tarefas([string]$Padrao, [string]$Exceto = '^$') {
    $n = 0
    foreach ($tk in @(Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { ($_.TaskPath + $_.TaskName) -match $Padrao -and ($_.TaskPath + $_.TaskName) -notmatch $Exceto -and $_.State -ne 'Disabled' })) {
        if (Set-Tarefa ($tk.TaskPath + $tk.TaskName) $false) { $n++ }
    }
    return $n
}
function Guarda-Arquivo([string]$Arq) {
    if (-not (Test-Path -LiteralPath $Arq)) { return $false }
    if ($TESTE) { Plano ("guardar no backup: {0}" -f $Arq); return $true }
    $id = [guid]::NewGuid().ToString('N').Substring(0, 8)
    $dest = Join-Path $BK ('arquivos\' + $id)
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    try {
        Move-Item -LiteralPath $Arq -Destination $dest -Force -ErrorAction Stop
        _BkGuarda ("arq|" + $id) @{ t = 'arquivo'; de = $Arq; para = (Join-Path $dest (Split-Path $Arq -Leaf)) }
        $script:MUDOU++
        return $true
    } catch { return $false }
}
function Guarda-Desfazer([string]$Id, [string]$Codigo) { if (-not $TESTE) { _BkGuarda ("cmd|" + $Id) @{ t = 'cmd'; c = $Codigo } } }
function Guarda-Energia {
    $g = (powercfg /getactivescheme | Out-String)
    if ($g -match '([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})') { if (-not $TESTE) { _BkGuarda 'energia' @{ t = 'energia'; g = $Matches[1] } } }
}
function Get-IndiceEnergia([string]$Esquema, [string]$Sub, [string]$Config) {
    # As duas ultimas linhas com 0x da saida do powercfg /q sao o indice atual na tomada e na bateria (vale em qualquer idioma).
    $o = @(powercfg /q $Esquema $Sub $Config 2>$null | Select-String -Pattern '0x[0-9a-fA-F]+\s*$')
    if ($o.Count -lt 2) { return $null }
    $ac = [Convert]::ToInt32(($o[$o.Count - 2].Line -replace '.*(0x[0-9a-fA-F]+)\s*$', '$1'), 16)
    $dc = [Convert]::ToInt32(($o[$o.Count - 1].Line -replace '.*(0x[0-9a-fA-F]+)\s*$', '$1'), 16)
    return @($ac, $dc)
}
function Set-Energia([string]$Esquema, [string]$Sub, [string]$Config, $Ac, $Dc, [string]$Rotulo) {
    $atual = Get-IndiceEnergia $Esquema $Sub $Config
    if ($null -eq $atual) { return $false }
    $muda = (($null -ne $Ac) -and ($atual[0] -ne $Ac)) -or (($null -ne $Dc) -and ($atual[1] -ne $Dc))
    if (-not $muda) { return $false }
    if ($TESTE) { Plano $Rotulo; return $true }
    Guarda-Desfazer ("energia|" + $Esquema + "|" + $Sub + "|" + $Config) ("powercfg /setacvalueindex {0} {1} {2} {3}; powercfg /setdcvalueindex {0} {1} {2} {4}" -f $Esquema, $Sub, $Config, $atual[0], $atual[1])
    if ($null -ne $Ac) { powercfg /setacvalueindex $Esquema $Sub $Config $Ac | Out-Null }
    if ($null -ne $Dc) { powercfg /setdcvalueindex $Esquema $Sub $Config $Dc | Out-Null }
    $script:MUDOU++
    return $true
}
function _KTela {
    if ('Katharos.KTela' -as [type]) { return }
    Add-Type -Namespace Katharos -Name KTela -ErrorAction Stop -MemberDefinition '
[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)] public struct DEVMODE { [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmDeviceName; public short dmSpecVersion; public short dmDriverVersion; public short dmSize; public short dmDriverExtra; public int dmFields; public int dmPositionX; public int dmPositionY; public int dmDisplayOrientation; public int dmDisplayFixedOutput; public short dmColor; public short dmDuplex; public short dmYResolution; public short dmTTOption; public short dmCollate; [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string dmFormName; public short dmLogPixels; public int dmBitsPerPel; public int dmPelsWidth; public int dmPelsHeight; public int dmDisplayFlags; public int dmDisplayFrequency; public int dmICMMethod; public int dmICMIntent; public int dmMediaType; public int dmDitherType; public int dmReserved1; public int dmReserved2; public int dmPanningWidth; public int dmPanningHeight; }
[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)] public struct DISPLAY_DEVICE { public int cb; [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string DeviceName; [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string DeviceString; public int StateFlags; [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string DeviceID; [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string DeviceKey; }
[DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern bool EnumDisplayDevices(string dev, int i, ref DISPLAY_DEVICE d, int f);
[DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern bool EnumDisplaySettings(string dev, int modo, ref DEVMODE dm);
[DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int ChangeDisplaySettingsEx(string dev, ref DEVMODE dm, IntPtr h, int flags, IntPtr p);'
}
function Get-Monitores {
    # cada tela ligada: a taxa de agora e a maior que ela aceita na MESMA resolucao e cor (nada de mudar resolucao)
    _KTela
    $out = @(); $i = 0
    $d = New-Object 'Katharos.KTela+DISPLAY_DEVICE'; $d.cb = [System.Runtime.InteropServices.Marshal]::SizeOf($d)
    while ($i -lt 16 -and [Katharos.KTela]::EnumDisplayDevices($null, $i, [ref]$d, 0)) {
        if ($d.StateFlags -band 1) {
            $dm = New-Object 'Katharos.KTela+DEVMODE'; $dm.dmSize = [int16][System.Runtime.InteropServices.Marshal]::SizeOf($dm)
            if ([Katharos.KTela]::EnumDisplaySettings($d.DeviceName, -1, [ref]$dm)) {
                $w = $dm.dmPelsWidth; $h = $dm.dmPelsHeight; $b = $dm.dmBitsPerPel; $hz = $dm.dmDisplayFrequency; $max = $hz; $m = 0
                $x = New-Object 'Katharos.KTela+DEVMODE'; $x.dmSize = $dm.dmSize
                while ($m -lt 4000 -and [Katharos.KTela]::EnumDisplaySettings($d.DeviceName, $m, [ref]$x)) {
                    if ($x.dmPelsWidth -eq $w -and $x.dmPelsHeight -eq $h -and $x.dmBitsPerPel -eq $b -and $x.dmDisplayFrequency -gt $max -and $x.dmDisplayFrequency -le 500 -and -not ($x.dmDisplayFlags -band 2)) { $max = $x.dmDisplayFrequency }
                    $m++
                }
                $out += [pscustomobject]@{ dev = $d.DeviceName; nome = $d.DeviceString; hz = $hz; max = $max; w = $w; h = $h; primaria = [bool]($d.StateFlags -band 4) }
            }
        }
        $i++
    }
    return $out
}
function Set-TaxaMonitor([string]$Dev, [int]$Hz, [string]$Rotulo) {
    # muda so a taxa (Hz) da tela, na mesma resolucao; testa antes (CDS_TEST) e le de volta depois. O desfazer volta a taxa de antes.
    _KTela
    $dm = New-Object 'Katharos.KTela+DEVMODE'; $dm.dmSize = [int16][System.Runtime.InteropServices.Marshal]::SizeOf($dm)
    if (-not [Katharos.KTela]::EnumDisplaySettings($Dev, -1, [ref]$dm)) { return $false }
    $antes = $dm.dmDisplayFrequency
    if ($antes -eq $Hz) { return $false }
    if ($TESTE) { Plano $Rotulo; return $true }
    $dm.dmDisplayFrequency = $Hz; $dm.dmFields = 0x400000
    if ([Katharos.KTela]::ChangeDisplaySettingsEx($Dev, [ref]$dm, [IntPtr]::Zero, 2, [IntPtr]::Zero) -ne 0) { Aviso ("{0}: a tela recusou {1} Hz" -f $Rotulo, $Hz); return $false }
    Guarda-Desfazer ("monitor|" + $Dev) ("Set-TaxaMonitor '{0}' {1} 'taxa de antes'" -f ($Dev -replace "'", "''"), $antes)
    if ([Katharos.KTela]::ChangeDisplaySettingsEx($Dev, [ref]$dm, [IntPtr]::Zero, 1, [IntPtr]::Zero) -ne 0) { Aviso ("{0}: o Windows nao aceitou" -f $Rotulo); return $false }
    $l = New-Object 'Katharos.KTela+DEVMODE'; $l.dmSize = $dm.dmSize
    if ([Katharos.KTela]::EnumDisplaySettings($Dev, -1, [ref]$l) -and $l.dmDisplayFrequency -ne $Hz) { Aviso ("{0}: a tela ficou em {1} Hz" -f $Rotulo, $l.dmDisplayFrequency); return $false }
    # como a troca de resolucao do Windows: fica so se a pessoa confirmar "manter" em 90 s (a janela e o terminal gravam tela-ok.txt);
    # sem resposta (tela apagada, ninguem olhando), um vigia separado volta a taxa de antes sozinho
    $k = Join-Path $env:USERPROFILE '.katharos'; New-Item -ItemType Directory -Force -Path $k | Out-Null
    $pend = Join-Path $k 'tela-pendente.txt'; $ok = Join-Path $k 'tela-ok.txt'
    Set-Content -LiteralPath $pend -Value (Get-Date -Format o) -Encoding ascii
    $volta = "Start-Sleep 90; `$p = '$pend'; `$o = '$ok'; if ((Test-Path `$o) -and (Test-Path `$p) -and (Get-Item `$o).LastWriteTime -ge (Get-Item `$p).LastWriteTime) { exit }; " +
             "function _KTela {" + ${function:_KTela}.ToString() + "}; _KTela; `$dm = New-Object 'Katharos.KTela+DEVMODE'; `$dm.dmSize = [int16][Runtime.InteropServices.Marshal]::SizeOf(`$dm); " +
             "if ([Katharos.KTela]::EnumDisplaySettings('" + ($Dev -replace "'", "''") + "', -1, [ref]`$dm) -and `$dm.dmDisplayFrequency -eq $Hz) { `$dm.dmDisplayFrequency = $antes; `$dm.dmFields = 0x400000; [Katharos.KTela]::ChangeDisplaySettingsEx('" + ($Dev -replace "'", "''") + "', [ref]`$dm, [IntPtr]::Zero, 1, [IntPtr]::Zero) | Out-Null }"
    $psx = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    Start-Process -FilePath $psx -WindowStyle Hidden -ArgumentList '-NoProfile', '-NonInteractive', '-EncodedCommand', ([Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($volta)))
    $script:MUDOU++
    return $true
}
function Set-EconomiaAdaptadores {
    # PC de mesa: o Windows para de desligar a placa de rede e o Wi-Fi para economizar (causa de queda e de travada de rede)
    foreach ($a in @(Get-NetAdapter -Physical -ErrorAction SilentlyContinue | Where-Object { $_.Status -ne 'Disabled' })) {
        $pm = Get-NetAdapterPowerManagement -Name $a.Name -ErrorAction SilentlyContinue
        if (-not $pm -or "$($pm.AllowComputerToTurnOffDevice)" -ne 'Enabled') { continue }
        if ($TESTE) { Plano ("{0}: sem desligar para economizar" -f $a.Name); continue }
        $g = "$($a.InterfaceGuid)"
        # o desfazer acha o adaptador pelo GUID (o nome pode mudar)
        Guarda-Desfazer ("adaptador|" + $g) ("Get-NetAdapter -Physical -ErrorAction SilentlyContinue | Where-Object {{ `$_.InterfaceGuid -eq '{0}' }} | ForEach-Object {{ Set-NetAdapterPowerManagement -Name `$_.Name -AllowComputerToTurnOffDevice Enabled -NoRestart -ErrorAction SilentlyContinue }}" -f $g)
        Set-NetAdapterPowerManagement -Name $a.Name -AllowComputerToTurnOffDevice Disabled -NoRestart -ErrorAction SilentlyContinue
        $depois = Get-NetAdapterPowerManagement -Name $a.Name -ErrorAction SilentlyContinue
        if ($depois -and "$($depois.AllowComputerToTurnOffDevice)" -ne 'Enabled') { $script:MUDOU++ } else { Aviso ("{0}: o Windows nao aceitou desligar a economia" -f $a.Name) }
    }
}
function Roda([string]$Exe, [string]$Argumentos = '', [double]$Minutos = 5, [switch]$Visivel) {
    if ($TESTE) { Plano ("rodar {0} {1}" -f (Split-Path $Exe -Leaf), $Argumentos); return 0 }
    $a = @{ FilePath = $Exe; PassThru = $true; ErrorAction = 'Stop' }
    if ($Argumentos) { $a.ArgumentList = $Argumentos }
    if ($Visivel) { $a.WindowStyle = 'Normal' } else { $a.WindowStyle = 'Hidden' }
    try { $p = Start-Process @a } catch { return -2 }
    $null = $p.Handle
    if (-not $p.WaitForExit([int]($Minutos * $MULT * 60000))) { & taskkill.exe /PID $p.Id /T /F 2>$null | Out-Null; return -1 }
    return $p.ExitCode
}
function Reinicia-Explorer {
    if ($TESTE) { return }
    Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
    Start-Sleep 2
    if (-not (Get-Process explorer -ErrorAction SilentlyContinue)) { Start-Process explorer.exe }
}
function TamanhoPasta([string]$P) {
    if (-not (Test-Path -LiteralPath $P)) { return 0 }
    $s = (ListaSemLinks $P | Measure-Object Length -Sum).Sum
    if ($s) { return [double]$s } else { return 0 }
}
function CaminhoSeguro([string]$P) {
    # Recusa caminho vazio, relativo, raiz de disco ou pastas grandes do sistema e do usuario
    # (protege contra variavel de ambiente vazia virando "\Temp" ou "C:\").
    if (-not $P -or $P -notmatch '^[A-Za-z]:\\[^\\]') { return $false }
    $c = $P.TrimEnd('\')
    $prot = @($env:SystemDrive, $env:WINDIR, "$env:WINDIR\System32", $env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:ProgramData,
              "$env:SystemDrive\Users", $env:USERPROFILE, [Environment]::GetFolderPath('MyDocuments'), [Environment]::GetFolderPath('Desktop')) |
            Where-Object { $_ } | ForEach-Object { $_.TrimEnd('\') }
    if ($prot -contains $c) { return $false }
    return (($c -split '\\').Count -ge 3)
}
function ListaSemLinks([string]$P, [switch]$Pastas) {
    # Anda pela pasta SEM entrar em junção nem link simbólico (o Get-ChildItem -Recurse do Windows PowerShell 5.1 entra, e a limpeza
    # apagaria arquivos de fora da pasta). Devolve os arquivos (ou, com -Pastas, as subpastas, das mais fundas para as mais rasas).
    $pilha = New-Object System.Collections.Generic.Stack[string]; $pilha.Push($P); $achadas = New-Object System.Collections.Generic.List[string]
    while ($pilha.Count) {
        $d = $pilha.Pop()
        foreach ($e in @(Get-ChildItem -LiteralPath $d -Force -ErrorAction SilentlyContinue)) {
            if ($e.Attributes -band [IO.FileAttributes]::ReparsePoint) { continue }
            if ($e.PSIsContainer) { $pilha.Push($e.FullName); $achadas.Add($e.FullName) } elseif (-not $Pastas) { $e }
        }
    }
    if ($Pastas) { $achadas.Sort(); $achadas.Reverse(); return $achadas.ToArray() }
}
function LimpaAntigos([string]$P, [double]$Dias = 0) {
    # Apaga arquivos mais velhos que N dias (arquivo em uso fica). Devolve os bytes liberados. Nunca entra em junção nem link simbólico.
    if (-not (CaminhoSeguro $P)) { if ($P) { Aviso ("pulei {0}: caminho fora do esperado" -f $P) }; return 0 }
    if (-not (Test-Path -LiteralPath $P)) { return 0 }
    if ((Get-Item -LiteralPath $P -Force -ErrorAction SilentlyContinue).Attributes -band [IO.FileAttributes]::ReparsePoint) { Aviso ("pulei {0}: e um link para outra pasta" -f $P); return 0 }
    $limite = (Get-Date).AddDays(-$Dias); $livre = 0
    foreach ($f in @(ListaSemLinks $P | Where-Object { $_.LastWriteTime -lt $limite })) {
        if ($TESTE) { $livre += $f.Length; continue }
        $len = $f.Length
        Remove-Item -LiteralPath $f.FullName -Force -ErrorAction SilentlyContinue
        if (-not (Test-Path -LiteralPath $f.FullName)) { $livre += $len }
    }
    if (-not $TESTE) {
        foreach ($d in @(ListaSemLinks $P -Pastas)) { if (-not (Get-ChildItem -LiteralPath $d -Force -ErrorAction SilentlyContinue)) { Remove-Item -LiteralPath $d -Force -ErrorAction SilentlyContinue } }
    }
    return $livre
}
function MB($B) { return ('{0:N0} MB' -f ($B / 1MB)) }
'''

DESFAZ_PS = r'''
$f = Join-Path $BK 'mudancas.jsonl'
if (-not (Test-Path -LiteralPath $f)) { Aviso 'nada guardado para desfazer neste pacote'; return }
$linhas = @(Get-Content -LiteralPath $f -Encoding UTF8 | Where-Object { $_ })
[array]::Reverse($linhas)
$n = 0; $ruins = 0
foreach ($l in $linhas) {
    try { $o = ConvertFrom-Json $l } catch { $ruins++; continue }
    if ($TESTE) { Plano ("voltar {0}: {1}{2}" -f $o.t, $o.n, $o.de); continue }
    try {
        switch ($o.t) {
            'reg' {
                if ($o.existe) {
                    $v = $o.v
                    if ($o.tipo -eq 'Binary') { $v = [Convert]::FromBase64String([string]$o.v) }
                    elseif ($o.tipo -eq 'MultiString') { $v = [string[]]@($o.v) }
                    elseif ($o.tipo -eq 'DWord') { $v = [int64]$o.v; if ($v -gt 2147483647) { $v = [int32]($v - 4294967296) } }
                    if (-not (Test-Path -LiteralPath $o.p)) { New-Item -Path $o.p -Force | Out-Null }
                    if ($o.n -eq '(default)') { Set-ItemProperty -LiteralPath $o.p -Name '(default)' -Value $v }
                    else { New-ItemProperty -LiteralPath $o.p -Name $o.n -Value $v -PropertyType $o.tipo -Force | Out-Null }
                } else {
                    $nn = $o.n; if ($nn -eq '(default)') { $nn = '' }
                    # a chave só é apagada se foi o Katharos que a criou; senão some só o valor
                    if ($nn -eq '' -and $o.chave -eq $false) { Remove-Item -LiteralPath $o.p -Recurse -Force -ErrorAction SilentlyContinue }
                    elseif ($nn -eq '') { Remove-ItemProperty -LiteralPath $o.p -Name '(default)' -Force -ErrorAction SilentlyContinue }
                    else { Remove-ItemProperty -LiteralPath $o.p -Name $nn -Force -ErrorAction SilentlyContinue }
                }
            }
            'svc' { & sc.exe config $o.n start= $o.modo | Out-Null; if ($o.rodando) { & sc.exe start $o.n 2>$null | Out-Null } }
            'tarefa' {
                $i = $o.n.LastIndexOf('\')
                $tk = Get-ScheduledTask -TaskPath $o.n.Substring(0, $i + 1) -TaskName $o.n.Substring($i + 1) -ErrorAction SilentlyContinue
                if ($tk) { if ($o.ligada) { $tk | Enable-ScheduledTask | Out-Null } else { $tk | Disable-ScheduledTask | Out-Null } }
            }
            'arquivo' { if (Test-Path -LiteralPath $o.para) { New-Item -ItemType Directory -Force -Path (Split-Path $o.de) | Out-Null; Move-Item -LiteralPath $o.para -Destination $o.de -Force } }
            'energia' { powercfg /setactive $o.g | Out-Null }
            'cmd' { Invoke-Expression $o.c | Out-Null }
        }
        $n++
    } catch { Aviso ("nao voltou {0}: {1}" -f $o.k, $_.Exception.Message) }
}
if ($ruins) { Aviso ("{0} linha(s) do registro de mudancas estavam ilegiveis e nao puderam voltar (o arquivo foi guardado)" -f $ruins) }
if (-not $TESTE) {
    Rename-Item -LiteralPath $f -NewName ("mudancas-desfeito-{0:yyyyMMdd-HHmmss}.jsonl" -f (Get-Date))
    Feito ("{0} mudancas voltaram ao estado de antes" -f $n)
}
'''


class Saida:
    def __init__(self):
        self.codigo = 0
        self.dados = {}
        self.feitos, self.planos, self.avisos, self.erros = [], [], [], []
        self.linhas = []
        self.estourou = False
        self.tempo = 0.0

    @property
    def ok(self):
        return self.codigo == 0 and not self.estourou


def _exibe(t, tipo, txt, s, mostra):
    if tipo == 'secao':
        if mostra:
            t.escreve('  ' + t.p('◆', 'destaque') + ' ' + t.p(txt, 'texto', True))
    elif tipo == 'feito':
        s.feitos.append(txt)
        if mostra:
            t.item('✓', 'verde', txt, recuo=4, cor_nome='sub')
    elif tipo == 'plano':
        s.planos.append(txt)
        if mostra:
            t.item('○', 'azul', txt, recuo=4, cor_nome='sub')
    elif tipo == 'ok':
        if mostra:
            t.ok(txt)
    elif tipo == 'nada':
        if mostra:
            t.nota('    ' + txt)
    elif tipo == 'aviso':
        s.avisos.append(txt)
        if mostra:
            t.aviso(txt)
    elif tipo == 'erro':
        s.erros.append(txt)
        if mostra:
            t.erro(txt)
    elif tipo == 'info':
        if mostra:
            t.info(txt)


class _Filho:
    """Um processo filho cuja saída chega linha a linha numa fila. Normalmente é um Popen. Quando o Python roda
    dentro de um pacote MSIX (o da Microsoft Store), o PowerShell nasce fora do contêiner pelo WMI
    (Win32_Process.Create): senão o HKCU gravado seria uma cópia virtual. A saída vem então de um arquivo."""

    def __init__(self, ps, arq):
        self.fila = queue.Queue()
        self.fora = WINDOWS and dentro_de_pacote()
        if not self.fora:
            # sem console (pythonw, tarefa agendada): sem esta marca o PowerShell abriria uma janela, que poderia tirar um jogo da tela cheia
            sem_janela = 0x08000000 if WINDOWS and not ctypes.windll.kernel32.GetConsoleWindow() else 0
            self.p = subprocess.Popen([ps, '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(arq)],
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, creationflags=sem_janela, env=env_ps())
            self.pid = self.p.pid
            threading.Thread(target=self._le_pipe, daemon=True).start()
            return
        self.saida = Path(str(arq) + '.saida.txt')
        linha = f'cmd.exe /c ""{ps}" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "{arq}" > "{self.saida}" 2>&1"'
        # ShowWindow = 0: o processo criado pelo WMI nasce com a janela escondida. Sem isto, cada etapa abria uma janela
        # preta do cmd que ficava parada na tela até a etapa terminar.
        cria = ("$si = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ ShowWindow = [uint16]0 }; "
                "$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = " + psq(linha) +
                "; ProcessStartupInformation = $si }; [Console]::Out.Write([string]$r.ProcessId + '|' + [string]$r.ReturnValue)")
        r = subprocess.run([ps, '-NoProfile', '-NonInteractive', '-Command', cria], capture_output=True, text=True, timeout=90, env=env_ps())
        pid, _, rv = r.stdout.strip().partition('|')
        if not pid.isdigit() or rv.strip() != '0':
            raise OSError(f'WMI não criou o processo (retorno {rv or r.stderr.strip()[:80]})')
        self.pid = int(pid)
        k = ctypes.windll.kernel32
        self.h = k.OpenProcess(0x00100000 | 0x1000, False, self.pid)  # SYNCHRONIZE | QUERY_LIMITED_INFORMATION
        threading.Thread(target=self._le_arquivo, daemon=True).start()

    def _le_pipe(self):
        for bruto in iter(self.p.stdout.readline, b''):
            self.fila.put(bruto)
        self.fila.put(None)

    def _vivo(self):
        return bool(self.h) and ctypes.windll.kernel32.WaitForSingleObject(self.h, 0) == 0x102

    def _le_arquivo(self):
        pos, resto = 0, b''
        while True:
            vivo = self._vivo()
            try:
                with open(self.saida, 'rb') as f:
                    f.seek(pos)
                    novo = f.read()
                    pos += len(novo)
            except OSError:
                novo = b''
            if novo:
                resto += novo
                *linhas, resto = resto.split(b'\n')
                for l in linhas:
                    self.fila.put(l + b'\n')
            elif not vivo:
                if resto:
                    self.fila.put(resto)
                self.fila.put(None)
                return
            else:
                time.sleep(0.25)

    def espera(self, timeout=10):
        if not self.fora:
            return self.p.wait(timeout=timeout)
        k = ctypes.windll.kernel32
        k.WaitForSingleObject(self.h, int(timeout * 1000))
        cod = ctypes.c_ulong(0)
        k.GetExitCodeProcess(self.h, ctypes.byref(cod))
        k.CloseHandle(self.h)
        try:
            self.saida.unlink()
        except OSError:
            pass
        return ctypes.c_long(cod.value).value


def roda_ps(t, corpo, rotulo='etapa', minutos=5, pacote=None, teste=False, mostra=True, pr=None, mult=1.0,
            desfaz=False, vigia_ocioso=False):
    """Roda um trecho de PowerShell num processo filho, com limite de tempo (vezes o fator do hardware).
    Devolve Saida. pacote: pasta de backup (dir_backup()/PACOTE) para as mudanças poderem voltar.
    Como administrador, o script vai para a pasta protegida: em ~/.katharos/tmp, um programa sem administrador poderia trocá-lo entre a
    gravação e a execução e rodar o que quisesse como administrador."""
    s = Saida()
    if not WINDOWS:
        s.codigo = 1
        s.erros.append('só funciona no Windows')
        return s
    admin = eh_admin()
    tmp = pasta_protegida('tmp') if admin else pasta('tmp')
    bk = (dir_backup() / pacote) if pacote else ''
    if admin and (tmp is None or (pacote and not teste and pasta_protegida('backup') is None)):
        s.codigo = 1
        _exibe(t, 'erro', f'não consegui proteger a pasta {pasta_da_tarefa()} (só administradores devem gravar nela); nada foi rodado', s, mostra)
        return s
    arq = tmp / f'{re.sub(r"[^a-z0-9-]", "-", rotulo.lower())[:30]}-{os.getpid()}-{int(time.time() * 1000) % 100000}.ps1'
    # as variáveis vão dentro do script: o processo criado pelo WMI não herda o ambiente
    cabeca = (f"$env:OTM_TESTE = '{'1' if teste else '0'}'\n$env:OTM_CASA = {psq(CASA)}\n$env:OTM_MULT = '{mult:.2f}'\n"
              f"$env:OTM_BK = {psq(bk)}\n")
    with open(arq, 'w', encoding='utf-8-sig', newline='\r\n') as f:  # BOM: o PowerShell 5.1 lê como UTF-8
        f.write(cabeca + PRELUDIO_PS + '\n' + RETRATO_PS + '\n' + (DESFAZ_PS if desfaz else corpo) + '\n')
    ps = shutil.which('powershell.exe') or r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
    LOG.escreve(f'--- {rotulo} (limite {minutos * mult:.0f} min{", teste" if teste else ""})')
    inicio = time.time()
    try:
        filho = _Filho(ps, arq)
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        s.codigo = 127
        s.erros.append(f'não abriu o PowerShell: {e}')
        return s
    fila = filho.fila
    limite = inicio + minutos * mult * 60
    ultima_saida = time.time()
    cpu = MedidorCPU()
    ocioso_desde = None
    while True:
        try:
            bruto = fila.get(timeout=1.0)
        except queue.Empty:
            bruto = ''
        if bruto is None:
            break
        if bruto:
            ultima_saida = time.time()
            linha = decodifica(bruto).rstrip('\r\n')
            LOG.escreve(f'  {linha}')
            if linha.startswith('@@'):
                tipo, _, txt = linha[2:].partition('|')
                if tipo == 'dado':
                    chave, _, js = txt.partition('|')
                    try:
                        s.dados[chave] = json.loads(js) if js else None
                    except ValueError:
                        s.dados[chave] = None
                elif tipo == 'vivo':
                    if pr is not None:
                        pr.atual = txt
                else:
                    _exibe(t, tipo, txt, s, mostra)
            elif linha.strip():
                s.linhas.append(linha)
                if pr is not None:
                    pr.atual = linha.strip()
        agora = time.time()
        if agora > limite:
            s.estourou = True
            break
        if vigia_ocioso and agora - ultima_saida > 600:
            # travado: nada na tela há 10 min e o PC parado (o Remove-AppxPackage às vezes nunca volta)
            if cpu.le() < 4:
                ocioso_desde = ocioso_desde or agora
                if agora - ocioso_desde > 120:
                    s.estourou = True
                    break
            else:
                ocioso_desde = None
    if s.estourou:
        mata_arvore(filho.pid)
        s.codigo = -1
        LOG.escreve(f'  TEMPO ESGOTADO: {rotulo}')
    else:
        try:
            s.codigo = filho.espera(timeout=10)
        except subprocess.TimeoutExpired:
            mata_arvore(filho.pid)
            s.codigo = -1
    s.tempo = time.time() - inicio
    try:
        arq.unlink()
    except OSError:
        pass
    return s


def roda_exe(cmd, minutos, pr=None, mult=1.0, saida_arq=None):
    """Roda uma ferramenta do Windows (DISM, sfc, chkdsk, defrag, winget) com limite de tempo,
    mostrando a última linha no progresso. Devolve (código, texto completo); código -1 = tempo esgotado."""
    LOG.escreve('--- ' + subprocess.list2cmdline([str(c) for c in cmd]))
    try:
        # no Windows, as ferramentas pesadas (DISM, sfc, chkdsk) rodam com prioridade abaixo do normal: o PC continua usável
        flags = getattr(subprocess, 'BELOW_NORMAL_PRIORITY_CLASS', 0) if WINDOWS else 0
        p = subprocess.Popen([str(c) for c in cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                             creationflags=flags)
    except OSError as e:
        return 127, str(e)
    fila = queue.Queue()

    def le():
        while True:
            b = p.stdout.read1(4096) if hasattr(p.stdout, 'read1') else p.stdout.read(4096)
            if not b:
                break
            fila.put(b)
        fila.put(None)

    threading.Thread(target=le, daemon=True).start()
    limite = time.time() + minutos * mult * 60
    partes = []
    while True:
        try:
            b = fila.get(timeout=1.0)
        except queue.Empty:
            b = b''
        if b is None:
            break
        if b:
            partes.append(b)
            if pr is not None:
                ult = [x.strip() for x in re.split(r'[\r\n]', decodifica(b)) if x.strip()]
                if ult:
                    pr.atual = ult[-1]
        if time.time() > limite:
            mata_arvore(p.pid)
            texto = decodifica(b''.join(partes))
            LOG.escreve(texto[-4000:])
            return -1, texto
    cod = p.wait()
    texto = decodifica(b''.join(partes))
    LOG.escreve(texto[-4000:])
    if saida_arq:
        try:
            Path(saida_arq).write_text(texto, encoding='utf-8')
        except OSError:
            pass
    return cod, texto
