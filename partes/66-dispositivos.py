
# =====================================================================================================================================
#   DISPOSITIVOS · mouse, teclado, fone e controle: o que está ligado e a bateria (só leitura)
# =====================================================================================================================================
# Fase 1 do plano planos/dispositivos-sem-fio.md. Só o que o Windows já sabe, sem abrir o dispositivo nem instalar nada:
#   - a lista de periféricos USB e Bluetooth (fabricante pelo VID, nome que o próprio aparelho informa);
#   - a bateria dos aparelhos Bluetooth (a mesma que aparece em Configurações > Bluetooth): DEVPKEY_Bluetooth_Battery.
# A lista vai também no relatório (sem número de série): é ela que diz quais marcas e modelos as pessoas usam, e em qual ordem vale a
# pena ler a bateria e o DPI de cada protocolo de fabricante (2.4 GHz).

VIDS_FABRICANTE = {
    '046D': 'Logitech', '1532': 'Razer', '1038': 'SteelSeries', '1B1C': 'Corsair', '0951': 'HyperX', '03F0': 'HyperX (HP)', '24AE': 'Rapoo',
    '258A': 'chip Sinowealth', '3554': 'chip Compx', '373B': 'chip Compx',
    '1EA7': 'chip SHARKOON', '25A7': 'chip Areson', '093A': 'chip Pixart',
    '04D9': 'chip Holtek', '0C45': 'chip Microdia', '1A2C': 'chip China Resource', '320F': 'chip Evision',
    '3151': 'chip YiChip', '05AC': 'Apple', '045E': 'Microsoft', '054C': 'Sony', '057E': 'Nintendo', '0B05': 'ASUS', '1E7D': 'ROCCAT',
    '3434': 'Keychron', '0738': 'Mad Catz', '3299': 'Glorious', '22D4': 'Laview (Glorious)', '1915': 'chip Nordic', '0461': 'Primax',
    '17EF': 'Lenovo', '413C': 'Dell', '1D57': 'chip Xenta', '2EA8': 'Pulsar', '373E': 'Lamzu', '19F5': 'Ninjutso', '1E4E': 'Cubeternet',
    '2717': 'Xiaomi', '12D1': 'Huawei', '04E8': 'Samsung', '1395': 'EPOS / Sennheiser', '047F': 'Poly', '0B0E': 'Jabra', '2F68': 'Hoksi',
}

DISPOSITIVOS_PS = r'''
$__bat = '{104EA319-6EE2-4701-BD47-8DDBF425BBE5} 2'
$__bus = '{540B947E-8B40-45BC-A8A2-6A0B894CBDA2} 4'
$__l = @()
$__vistos = @{}
foreach ($__d in @(Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue | Where-Object { $_.InstanceId -match '^USB\\VID_[0-9A-F]{4}&PID_[0-9A-F]{4}\\' -or $_.InstanceId -match '^(BTHENUM|BTHLE|BTHLEDEVICE)\\' })) {
    $__id = [string]$__d.InstanceId
    $__vid = ''; $__pid = ''
    if ($__id -match 'VID_([0-9A-F]{4})&PID_([0-9A-F]{4})') { $__vid = $Matches[1]; $__pid = $Matches[2] }
    elseif ($__id -match '_VID&[0-9A-F]{2}([0-9A-F]{4})_PID&([0-9A-F]{4})') { $__vid = $Matches[1]; $__pid = $Matches[2] }
    $__bt = $__id -match '^BTH'
    if ($__bt -and $__d.Class -notin @('Bluetooth', 'System', 'HIDClass', 'AudioEndpoint', 'Media')) { continue }
    $__chave = $(if ($__vid) { "$__vid$__pid$__bt" } else { $__id })
    $__b = Tenta { (Get-PnpDeviceProperty -InstanceId $__id -KeyName $__bat -ErrorAction Stop).Data } $null
    if ($__vistos.ContainsKey($__chave)) {
        if ($null -ne $__b -and $null -eq $__vistos[$__chave].bateria) { $__vistos[$__chave].bateria = [int]$__b }
        continue
    }
    if (-not $__bt -and $__d.Class -notin @('HIDClass', 'Mouse', 'Keyboard', 'USB', 'Media', 'AudioEndpoint', 'Image', 'XnaComposite', 'XboxComposite')) { continue }
    $__nome = Tenta { [string](Get-PnpDeviceProperty -InstanceId $__id -KeyName $__bus -ErrorAction Stop).Data } ''
    $__o = @{ nome = [string]$__d.FriendlyName; produto = $__nome; classe = [string]$__d.Class; vid = $__vid; pid = $__pid
              conexao = $(if ($__bt) { 'bluetooth' } else { 'usb' }); bateria = $(if ($null -ne $__b) { [int]$__b } else { $null }); ok = ($__d.Status -eq 'OK') }
    $__vistos[$__chave] = $__o
    $__l += $__o
    if ($__l.Count -ge 60) { break }
}
Dado 'dispositivos' @($__l)
'''

# o que é periférico de entrada ou de som (os hubs, leitores e o próprio controlador USB ficam de fora da tela; no relatório vão todos)
_DISPOSITIVO_RUIDO = re.compile(r'hub|root|controlador|controller|host|composite device$|dispositivo composto usb$|usb mass storage|'
                                r'armazenamento|card reader|leitor de cart|enumerator|enumerador|rfcomm|protocolo|protocol|service|serviço|'
                                r'generic attribute|generic access|device information|transport|transporte|adaptador|adapter|radio', re.I)


def tipo_dispositivo(d):
    """mouse, teclado, fone, controle, receptor ou outro, pelo nome e pela classe que o Windows dá."""
    n = f'{d.get("nome") or ""} {d.get("produto") or ""}'.lower()
    c = str(d.get('classe') or '').lower()
    if re.search(r'mouse|rato', n) or c == 'mouse':
        return 'mouse'
    if re.search(r'keyboard|teclado', n) or c == 'keyboard':
        return 'teclado'
    if re.search(r'headset|headphone|fone|buds|earbud|airpods|arctis|cloud|blackshark|kraken|wh-1000|audio|áudio', n) or c in ('audioendpoint', 'media'):
        return 'fone'
    if re.search(r'controller|gamepad|xbox|dualsense|dualshock|wireless controller|joystick|8bitdo', n) or c in ('xnacomposite', 'xboxcomposite'):
        return 'controle'
    if re.search(r'receiver|receptor|dongle|2\.4g|unifying|lightspeed|wireless', n):
        return 'receptor'
    return 'outro'


def le_dispositivos(ctx):
    """[{nome, fabricante, tipo, conexao, vid, pid, bateria, ok}] dos periféricos presentes. Só leitura; nada abre o aparelho."""
    if not WINDOWS:
        return []
    s = roda_ps(ctx.t, DISPOSITIVOS_PS, 'dispositivos', minutos=1, mostra=False)
    out = []
    for d in lista(s.dados.get('dispositivos')):
        if not isinstance(d, dict):
            continue
        nome = str(d.get('produto') or '').strip() or str(d.get('nome') or '').strip()
        if not nome or _DISPOSITIVO_RUIDO.search(nome) and d.get('bateria') is None:
            continue
        vid = str(d.get('vid') or '').upper()
        out.append({'nome': nome[:80], 'nome_windows': str(d.get('nome') or '')[:80], 'fabricante': VIDS_FABRICANTE.get(vid, ''),
                    'tipo': tipo_dispositivo(d), 'conexao': d.get('conexao'), 'vid': vid, 'pid': str(d.get('pid') or '').upper(),
                    'bateria': d.get('bateria') if isinstance(d.get('bateria'), int) and 0 <= d.get('bateria') <= 100 else None, 'ok': bool(d.get('ok'))})
    ordem = {'mouse': 0, 'teclado': 1, 'fone': 2, 'controle': 3, 'receptor': 4, 'outro': 5}
    return sorted(out, key=lambda x: (ordem.get(x['tipo'], 9), x['nome'].lower()))


def controles_xinput():
    """Bateria dos controles Xbox (e dos que se passam por eles) pelo XInput do Windows: XInputGetBatteryInformation só lê o que o
    Windows já sabe. Nada é enviado ao controle. [{nome, tipo, conexao, bateria_nivel}] (o XInput dá nível, não porcentagem)."""
    if not WINDOWS:
        return []
    try:
        import ctypes
        x = ctypes.WinDLL('xinput1_4')
    except OSError:
        return []

    class _Bat(ctypes.Structure):
        _fields_ = [('tipo', ctypes.c_ubyte), ('nivel', ctypes.c_ubyte)]

    class _Estado(ctypes.Structure):
        _fields_ = [('pacote', ctypes.c_uint32), ('dados', ctypes.c_ubyte * 12)]
    out = []
    for i in range(4):
        st = _Estado()
        if x.XInputGetState(i, ctypes.byref(st)) != 0:   # sem controle neste número
            continue
        b = _Bat()
        if x.XInputGetBatteryInformation(i, 0, ctypes.byref(b)) != 0:
            continue
        # tipo: 0 desconectado, 1 com fio, 2 alcalina, 3 recarregável; nível: 0 vazia, 1 baixa, 2 média, 3 cheia
        if b.tipo == 0:
            continue
        nivel = None if b.tipo == 1 else {0: 'vazia', 1: 'baixa', 2: 'média', 3: 'cheia'}.get(b.nivel)
        out.append({'nome': f'Controle Xbox {i + 1}', 'nome_windows': 'XInput', 'fabricante': '', 'tipo': 'controle',
                    'conexao': 'usb' if b.tipo == 1 else 'sem fio', 'vid': '', 'pid': '', 'bateria': None, 'bateria_nivel': nivel, 'ok': True})
    return out


@metodo_api('dispositivos')
def api_dispositivos(ctx, p, ev):
    """Mouse, teclado, fone e controle ligados agora, com a bateria quando o Windows sabe (Bluetooth)."""
    ds = le_dispositivos(ctx)
    try:
        ds += controles_xinput()
    except Exception as e:   # leitura extra: nunca derruba a tela
        LOG.escreve(f'dispositivos: XInput: {e!r}')
    try:   # o ícone (segundo plano) mostra as baterias a partir deste arquivo, sem ele mesmo ler nada
        grava_json(CASA / 'dispositivos.json', {'quando': agora_iso(), 'dispositivos': ds})
    except OSError:
        pass
    return {'dispositivos': ds}
