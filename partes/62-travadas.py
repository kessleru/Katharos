# ─────────────── travadas por driver (2c.9 a 2c.11): qual driver segura o processador e o que fazer ───────────────
# O Katharos.exe mede (eventos de DPC e de interrupção do kernel, por 1 minuto, só leitura, como administrador); aqui o resultado vira
# frase: "o driver de rede (ndis.sys) segurou o processador por 2,1 ms; atualize o driver da placa de rede pelo site do fabricante".
# Limites (os do LatencyMon): um DPC ou interrupção acima de 1 ms já pode dar estalo no áudio e travadinha em jogo; acima de 4 ms é grave.
TRAVADAS_ARQ = 'travadas.json'
TRAVADAS_RUIM_US = 1000
TRAVADAS_GRAVE_US = 4000
TRAVADAS_VALIDADE_DIAS = 7
# (padrão do nome do driver, o que ele é, o que fazer)
DRIVERS_CONHECIDOS = [
    (r'^(ndis|tcpip|netio|afd|netbt|wfplwfs|pacer)\.sys$', 'a pilha de rede do Windows', 'quase sempre é o driver da placa de rede ou do Wi-Fi por baixo dela: atualize-o pelo site do fabricante da placa-mãe ou do notebook'),
    (r'^(netwtw\d*|netwbw\d*|netwns\d*|athw\w*|rtwlane\w*|rtwlanu\w*|bcmwl\w*|mrvlpcie\w*|qcamain\w*|rtl8\w*|rt640x64|rt68cx21x64|e1[dgr]\w*|e2f\w*|igc\w*|ixgbe\w*|b57nd60a|k57nd60a|bxnd\w*)\.sys$',
     'o driver da placa de rede ou do Wi-Fi', 'atualize pelo site do fabricante (Intel, Realtek, Killer, Qualcomm); no Wi-Fi, desligar a economia de energia do adaptador também ajuda'),
    (r'^(nvlddmkm|nvhda\w*)\.sys$', 'o driver da NVIDIA', 'instale o driver mais novo do site da NVIDIA (instalação limpa); se começou depois de uma atualização, volte para a anterior'),
    (r'^(amdkmdag|atikmdag|atikmpag|amdkmpfd|amdacpbus|amdfendr\w*)\.sys$', 'o driver da AMD', 'instale o driver mais novo do site da AMD; se começou depois de uma atualização, volte para a anterior'),
    (r'^(igdkmd\w*|igdkmdn\w*|igdkmdnd\w*|iacamera\w*|intelppm)\.sys$', 'um driver da Intel (vídeo ou processador)', 'atualize pelo assistente de drivers da Intel ou pelo site do fabricante do PC'),
    (r'^(dxgkrnl|dxgmms\d|watchdog)\.sys$', 'o sistema de vídeo do Windows', 'normalmente é o driver da placa de vídeo por baixo: atualize-o'),
    (r'^(storport|stornvme|storahci|iastor\w*|iastora\w*|nvme\w*|amd_sata|amdsata|amdxata|disk|classpnp|ataport|msahci|pciide\w*|rste\w*|vmd)\.sys$',
     'o armazenamento (SSD, HD ou a controladora)', 'atualize o driver da controladora (Intel RST, AMD SATA/NVMe) e o firmware do SSD; um disco com defeito também faz isso'),
    (r'^(acpi|acpiex|intelpep|amdpep|pci|cng)\.sys$', 'o ACPI (energia e placa-mãe)', 'atualize a BIOS e o driver do chipset pelo site do fabricante; no notebook, teste com o plano de energia em desempenho'),
    (r'^(hdaudbus|hdaudio|portcls|ks|ksthunk|usbaudio\w*|rtkvhd64|rtkhdaud|rtkvhda|cmudaxp|nahimicvad\w*|iusb3\w*|senaudio\w*|wdmaud)\.sys$',
     'o áudio', 'atualize o driver de áudio (Realtek, placa de som); desligue efeitos de áudio do fabricante (Nahimic, Sonic Studio) se tiver'),
    (r'^(usbxhci|usbport|usbhub\d*|ucx01000|ucx\w*|iusb3\w*|hidusb|hidclass|kbdhid|mouhid)\.sys$', 'o USB (ou algo ligado nele)', 'tire um a um os aparelhos USB e meça de novo; atualize o driver do chipset'),
    (r'^(wdf01000|wdfldr)\.sys$', 'a base de drivers do Windows (por baixo de outro driver)', 'não dá para saber qual driver usou; meça de novo com menos coisa ligada'),
    (r'^(ntoskrnl\.exe|hal\.dll|ntkrnlmp\.exe)$', 'o próprio Windows', 'nada a fazer aqui: o próprio Windows aparece sempre e só pesa se outro driver o chamou'),
    (r'^(bthport|bthusb|bthmini|ibtusb|rtkbtfilter|bthenum)\.sys$', 'o Bluetooth', 'atualize o driver do Bluetooth; se não usa, desligue o Bluetooth e meça de novo'),
    (r'^(vmbus|vmswitch|vid|hvservice|winhvr|winhv)\.sys$', 'a virtualização (Hyper-V, WSL, área segura)', 'se não usa máquina virtual, desligar o Hyper-V e a plataforma de máquina virtual costuma ajudar'),
]


def quem_e_o_driver(nome):
    for padrao, o_que, fazer in DRIVERS_CONHECIDOS:
        if re.match(padrao, (nome or '').lower()):
            return o_que, fazer
    return 'um driver', 'procure o nome do driver para saber de qual aparelho ele é e atualize-o pelo site do fabricante'


def analisa_travadas(r):
    """Do JSON do Katharos.exe: os culpados (acima de 1 ms), do pior para o melhor, com o texto do que fazer. O próprio Windows não é culpado."""
    out = []
    for d in r.get('drivers') or []:
        nome = str(d.get('driver') or '')
        maior = float(d.get('maior_us') or 0)
        if maior < TRAVADAS_RUIM_US or nome == '(desconhecido)' or re.match(r'^(ntoskrnl\.exe|hal\.dll|ntkrnlmp\.exe)$', nome.lower()):
            continue
        o_que, fazer = quem_e_o_driver(nome)
        out.append({'driver': nome, 'o_que': o_que, 'fazer': fazer, 'maior_ms': round(maior / 1000, 2), 'vezes_acima_1ms': int(d.get('acima_1ms') or 0),
                    'grave': maior >= TRAVADAS_GRAVE_US, 'n': int(d.get('n') or 0)})
    return out


def le_travadas():
    d = le_json(CASA / TRAVADAS_ARQ, None)
    return d if isinstance(d, dict) and d.get('quando') else None


def travadas_recente(dias=TRAVADAS_VALIDADE_DIAS):
    d = le_travadas()
    return d if d and recente_h(d['quando'], 24 * dias) else None


def mede_travadas(segundos=60, pr=None):
    """Roda o teste no Katharos.exe e devolve o JSON (ou {'erro': ...}). Precisa do Windows e de administrador."""
    if not WINDOWS:
        return {'erro': 'só funciona no Windows'}
    exe = exe_disponivel()
    if not exe or not Path(exe).is_file():
        return {'erro': 'o Katharos.exe não foi encontrado (ele faz a medida)'}
    destino = CASA / TRAVADAS_ARQ
    tmp = CASA / (TRAVADAS_ARQ + '.novo')
    try:
        tmp.unlink()
    except OSError:
        pass
    cod, _ = roda_exe([str(exe), '--travadas', str(int(segundos)), str(tmp)], max(2, segundos / 60 + 1), pr)
    d = le_json(tmp, None)
    if not isinstance(d, dict):
        return {'erro': f'a medida não terminou (código {cod})'}
    if not d.get('erro'):
        os.replace(tmp, destino)
        estado_marca_travadas()
    return d


def estado_marca_travadas():
    e = estado()
    e.pop('travadas_pendente', None)
    salva_estado(e)


def ferramenta_travadas(ctx, args):
    t = ctx.t
    t.aba('qual driver trava o PC: mede 1 minuto e diz o culpado (só lê, precisa de administrador)')
    t.paragrafo('Liga por um minuto o rastreio do próprio Windows só com o tempo que cada driver segura o processador (o que o LatencyMon mede). '
                'Não instala nada e não mexe em nada. Para o resultado valer, deixe o PC fazendo o que trava (um jogo, um vídeo) durante a medida.', 2, 'sub')
    if getattr(args, 'ultimo', False):
        d = le_travadas()
        if not d:
            t.nota('Ainda não há medida. Rode "katharos travadas".')
            return 0
    else:
        seg = int(getattr(args, 'segundos', None) or 60)
        with Progresso(t, None, f'medindo por {seg} s') as pr:
            d = mede_travadas(seg, pr)
    if d.get('erro'):
        t.erro(f'Não deu para medir: {d["erro"]}.')
        return 1
    culpados = analisa_travadas(d)
    rel_secao('travadas', {'quando': d['quando'], 'culpados': culpados, 'eventos': d.get('eventos')})
    if not d.get('eventos'):
        t.aviso('O Windows não entregou nenhum evento. Feche outros programas de diagnóstico e tente de novo.')
        return 1
    if d.get('sem_endereco') and d['sem_endereco'] > 0.5 * d['eventos']:
        t.aviso('Este Windows escondeu o endereço de boa parte dos drivers: o resultado está incompleto.')
    if not culpados:
        t.ok(f'Nenhum driver passou de 1 ms em {br(d["eventos"], 0)} eventos medidos. As travadas, se existirem, não vêm de driver.')
        return 0
    for c in culpados:
        t.titulo(f'{c["o_que"]} ({c["driver"]})')
        t.chaves([('pior momento', t.p(f'{br(c["maior_ms"], 1)} ms', 'vermelho' if c['grave'] else 'amarelo')),
                  ('vezes acima de 1 ms', str(c['vezes_acima_1ms'])), ('o que fazer', c['fazer'])], recuo=4)
    return 0


def Quando_curto(iso):
    try:
        d = datetime.fromisoformat(str(iso))
    except ValueError:
        return str(iso)
    return d.strftime('%d/%m às %H:%M')


def travadas_pendente_no_jogo():
    """Há jogo aberto agora (agora.json do segundo plano)? O teste sozinho só roda fora do jogo."""
    a = le_agora(max_idade_s=60)
    return True if not a else bool(a.get('jogo'))   # sem leitura recente não dá para saber: trata como jogo (não mede)


def roda_travadas_se_pendente(pr=None):
    """2c.11: quando o motor viu travadas sem nenhum limite, a manutenção (que já roda como administrador) mede uma vez, fora do jogo."""
    e = estado()
    if not e.get('travadas_pendente') or travadas_recente() or travadas_pendente_no_jogo():
        return None
    d = mede_travadas(60, pr)
    if d.get('erro'):
        LOG.escreve(f'travadas na manutenção: {d["erro"]}')
        e = estado()
        e['travadas_pendente'] = False   # não insiste: a central continua propondo o teste para a pessoa
        salva_estado(e)
        return None
    publica_evento('travadas', {'culpados': [c['driver'] for c in analisa_travadas(d)]})
    return d
