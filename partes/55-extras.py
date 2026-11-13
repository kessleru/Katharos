

# ═══════════════════════════════ rede ═══════════════════════════════

DNS = [('cloudflare', 'Cloudflare', '1.1.1.1', '1.0.0.1', 'resolvedor público com foco em privacidade'),
       ('google', 'Google', '8.8.8.8', '8.8.4.4', 'resolvedor público do Google'),
       ('quad9', 'Quad9', '9.9.9.9', '149.112.112.112', 'bloqueia sites de golpe e malware'),
       ('adguard', 'AdGuard', '94.140.14.14', '94.140.15.15', 'bloqueia anúncios e rastreadores em todos os programas'),
       ('cloudflare-familia', 'Cloudflare Família', '1.1.1.3', '1.0.0.3', 'bloqueia malware e conteúdo adulto')]

DNS_PS = r'''
$__ad = @(Get-NetAdapter -Physical -ErrorAction SilentlyContinue | Where-Object Status -eq 'Up')
foreach ($a in $__ad) {
  $__at = @((Get-DnsClientServerAddress -InterfaceIndex $a.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue).ServerAddresses)
  $__novo = @(«lista»)
  if ((@($__at) -join ',') -eq (@($__novo) -join ',')) { continue }
  if ($TESTE) { Plano ("DNS de {0}: {1}" -f $a.Name, $(if ($__novo.Count) { $__novo -join ', ' } else { 'automatico (do roteador)' })); continue }
  $__volta = 'Set-DnsClientServerAddress -InterfaceIndex ' + $a.ifIndex + ' -ResetServerAddresses'
  $__dhcp = [string](Get-NetIPInterface -InterfaceIndex $a.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue).Dhcp
  if ($__at.Count -and $__dhcp -ne 'Enabled') { $__volta = "Set-DnsClientServerAddress -InterfaceIndex $($a.ifIndex) -ServerAddresses @('" + ($__at -join "','") + "')" }
  Guarda-Desfazer ('dns|' + $a.ifIndex) $__volta
  if ($__novo.Count) { Set-DnsClientServerAddress -InterfaceIndex $a.ifIndex -ServerAddresses $__novo } else { Set-DnsClientServerAddress -InterfaceIndex $a.ifIndex -ResetServerAddresses }
  $script:MUDOU++
}
if (-not $TESTE) { Clear-DnsClientCache -ErrorAction SilentlyContinue }
'''


def analisa_dns(amostras, atual):
    """amostras: {ip: {dominio: [ms ou None]}}; atual: ip do DNS em uso. Devolve (linhas, veredito).
    Cada servidor vira a mediana das medianas por domínio (a 1ª consulta de cada domínio é descartada: aquece o cache).
    Só recomenda trocar se o melhor for pelo menos 5 ms e 25% mais rápido que o atual E o terceiro quartil dele ficar
    abaixo da mediana do atual; senão o veredito é que não vale a troca."""
    linhas = {}
    for ip, doms in amostras.items():
        meds, tudo, falhas, total = [], [], 0, 0
        for d, v in doms.items():
            v = list(v)
            total += len(v)
            falhas += sum(1 for x in v if x is None or x < 0)
            ok = [x for x in (v[1:] if len(v) > 2 else v) if x is not None and x >= 0]
            if ok:
                meds.append(estatistica(ok)['mediana'])
                tudo += ok
        if not meds:
            linhas[ip] = None
            continue
        ordem = sorted(tudo)
        q = lambda f: ordem[min(len(ordem) - 1, int(f * len(ordem)))]
        linhas[ip] = {'mediana': estatistica(meds)['mediana'], 'q1': q(0.25), 'q3': q(0.75), 'falhas': falhas, 'total': total}
    ref = linhas.get(atual)
    if not ref:
        return linhas, 'sem medida do DNS atual: não dá para comparar'
    melhor = min((ip for ip, r in linhas.items() if r and ip != atual), key=lambda i: linhas[i]['mediana'], default=None)
    if melhor is None:
        return linhas, 'só o DNS atual respondeu'
    m = linhas[melhor]
    dif = ref['mediana'] - m['mediana']
    if dif >= 5 and dif >= 0.25 * ref['mediana'] and m['q3'] < ref['mediana'] and m['falhas'] <= ref['falhas']:
        return linhas, f'{melhor} respondeu {dif:.0f} ms ({dif / ref["mediana"] * 100:.0f}%) mais rápido que o atual: a troca vale'
    return linhas, 'nenhum servidor testado foi claramente mais rápido que o atual: não vale trocar só por velocidade'


DNS_TESTE_PS = r'''
$__cur = $null
foreach ($__a in @(Get-NetAdapter -Physical -ErrorAction SilentlyContinue | Where-Object Status -eq 'Up')) {
  $__s = @((Get-DnsClientServerAddress -InterfaceIndex $__a.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue).ServerAddresses)
  if ($__s.Count) { $__cur = $__s[0]; break }
}
$__ips = @($__cur) + @('1.1.1.1', '8.8.8.8', '9.9.9.9', '94.140.14.14') | Where-Object { $_ } | Select-Object -Unique
$__doms = 'google.com', 'youtube.com', 'facebook.com', 'globo.com', 'mercadolivre.com.br', 'steampowered.com'
$__rows = New-Object System.Collections.Generic.List[object]
foreach ($__ip in $__ips) {
  Vivo ('DNS ' + $__ip)
  foreach ($__d in $__doms) {
    $__v = New-Object System.Collections.Generic.List[double]
    for ($__i = 0; $__i -lt 5; $__i++) {
      $__sw = [Diagnostics.Stopwatch]::StartNew()
      $__r = Resolve-DnsName -Name $__d -Server $__ip -Type A -DnsOnly -NoHostsFile -QuickTimeout -ErrorAction SilentlyContinue
      $__sw.Stop()
      if ($__r) { $__v.Add([math]::Round($__sw.Elapsed.TotalMilliseconds, 1)) } else { $__v.Add(-1) }
    }
    $__rows.Add([pscustomobject]@{ ip = $__ip; dom = $__d; ms = @($__v) })
  }
}
Dado 'dns_atual' ([string]$__cur)
Dado 'dns_teste' (Lista $__rows)
'''


def _py_dns_teste(ctx, it, pr, teste):
    """Mede a resposta real de cada DNS (sem cache local) e só recomenda trocar quando a diferença passa do ruído."""
    if not WINDOWS:
        ctx.t.paragrafo('O teste de DNS só roda no Windows.', 4, 'apagado')
        return 0, 0
    s = roda_ps(ctx.t, DNS_TESTE_PS, 'dns-teste', minutos=5, mostra=False, pr=pr)
    atual = s.dados.get('dns_atual') or ''
    amostras = {}
    for r in s.dados.get('dns_teste') or []:
        amostras.setdefault(r['ip'], {})[r['dom']] = [None if x < 0 else x for x in (r['ms'] if isinstance(r['ms'], list) else [r['ms']])]
    if not amostras:
        ctx.t.paragrafo('Nenhum DNS respondeu ao teste (sem internet?).', 4, 'apagado')
        return 0, 0
    linhas, veredito = analisa_dns(amostras, atual)
    tab = []
    for ip, r in sorted(linhas.items(), key=lambda kv: kv[1]['mediana'] if kv[1] else 1e9):
        nome = ('seu DNS atual' if ip == atual else next((n for _, n, i, _, _ in DNS if i == ip), ip))
        tab.append([f'{nome} ({ip})', f'{r["mediana"]:.0f} ms' if r else '-', f'{r["q1"]:.0f}–{r["q3"]:.0f} ms' if r else '-',
                    f'{r["falhas"]}/{r["total"]}' if r else 'sem resposta'])
    ctx.t.tabela(['servidor', 'mediana', 'faixa típica', 'falhas'], tab, alinha='eddd')
    ctx.t.paragrafo(veredito + '. Sites populares costumam estar no cache do servidor; o que mais pesa no dia a dia é o cache do próprio Windows.', 4, 'apagado')
    return 0, 0


def _py_ping(ctx, it, pr, teste):
    """Mede a latência até o roteador e os DNS públicos, para escolher com número."""
    alvos = [('roteador', None)] + [(nome, ip) for _, nome, ip, _, _ in DNS[:4]]
    if WINDOWS:
        s = roda_ps(ctx.t, "Dado 'gw' ([string](Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | Sort-Object RouteMetric | Select-Object -First 1).NextHop)", 'gw', minutos=1, mostra=False)
        alvos[0] = ('roteador', s.dados.get('gw') or None)
    linhas = []
    n = 10
    for nome, ip in alvos:
        if not ip:
            continue
        pr.atual = f'ping {ip}'
        args = ['ping', '-n', str(n), '-w', '1000', ip] if WINDOWS else ['ping', '-c', str(n), '-W', '1', ip]
        cod, txt = roda_exe(args, 1, pr)
        ms = [int(x) for x in re.findall(r'(?:tempo|time)[=<](\d+)', txt, re.I)]
        perda = 100 - 100 * len(ms) // n
        if ms:
            est = estatistica(ms)
            dp = (sum((x - sum(ms) / len(ms)) ** 2 for x in ms) / len(ms)) ** 0.5
            linhas.append([f'{nome} ({ip})', f'{est["mediana"]:.0f} ms', f'{est["minimo"]:.0f}–{est["maximo"]:.0f} ms', f'{dp:.1f} ms', f'{perda}%'])
        else:
            linhas.append([f'{nome} ({ip})', '-', '-', '-', f'{perda}%'])
    ctx.t.tabela(['destino', 'mediana', 'variação', 'oscilação', 'perda'], linhas, alinha='edddd')
    ctx.t.paragrafo('Roteador acima de 5 ms ou perda no roteador = problema no Wi-Fi ou no cabo, não na internet. '
                    'Oscilação alta (desvio acima de 5 ms) e perda são o que causa "lag" em jogos; a média sozinha não mostra isso.', 4, 'apagado')
    return 0, 0


@pacote('rede', 'rede e DNS', 'DNS mais rápido ou com bloqueio, medição de ping',
        'Troca o DNS de todas as placas de rede ligadas (o desfazer volta o que estava antes). Mede o ping até o roteador '
        'e os DNS públicos e mede a resposta real de cada DNS para você decidir com número. Ajustes de TCP "milagrosos" não estão aqui: não têm ganho medido.')
def itens_rede(ctx):
    itens = [Item('ping', 'medir o ping', 'Ping até o roteador e até Cloudflare, Google, Quad9 e AdGuard.', 'decidir com número',
                  'nenhum', 1, py=_py_ping, reverte=False),
             Item('dns-teste', 'medir qual DNS responde mais rápido', 'Consulta 6 sites populares 5 vezes em cada servidor (o seu atual, Cloudflare, Google, Quad9 e AdGuard), '
                  'direto no servidor, sem usar o cache do Windows, e mostra mediana e faixa típica. Só diz que vale trocar se a diferença for de '
                  'pelo menos 5 ms e 25% e maior que o ruído. Leva uns 2 minutos e não muda nada no PC.', 'decidir o DNS com número, não com palpite',
                  'nenhum', 1, py=_py_dns_teste, reverte=False, minutos=3)]
    for id_, nome, a, b, desc in DNS:
        itens.append(Item('dns-' + id_, f'DNS {nome} ({a})', f'Usa o DNS {nome}: {desc}. No Windows 11, para criptografar também, abra as propriedades da conexão em Configurações > Rede e Internet '
                          'e escolha criptografia DNS "somente criptografada" (DNS sobre HTTPS); o Windows já conhece estes servidores.', 'só se o teste de DNS mostrar diferença no seu caso: meça antes de trocar',
                          'redes de empresa com DNS próprio param de achar os servidores internos', 0,
                          ps_monta(DNS_PS, lista=f'{psq(a)},{psq(b)}'), grupo='dns'))
    itens.append(Item('dns-auto', 'DNS automático (do roteador)', 'Volta a usar o DNS que o roteador entrega.', 'o padrão',
                      'nenhum', 0, ps_monta(DNS_PS, lista=''), grupo='dns'))
    itens.append(Item('autotuning', 'ajuste automático do TCP no normal', 'Se algum "otimizador" desligou o ajuste automático da janela TCP, '
                      'downloads ficam lentos. Isto volta ao padrão do Windows.', 'downloads na velocidade certa', 'nenhum', 1, r'''
$__g = (netsh int tcp show global | Out-String)
if ($__g -match '(?im)(Receive Window Auto-Tuning Level|ajuste autom.tico da janela de recebimento)\s*:\s*(\w+)' -and $Matches[2] -notmatch 'normal') {
  if ($TESTE) { Plano 'autotuning do TCP: normal' } else { Guarda-Desfazer 'autotuning' ('netsh int tcp set global autotuninglevel=' + $Matches[2] + ' | Out-Null'); netsh int tcp set global autotuninglevel=normal | Out-Null; $script:MUDOU++ } }'''))
    return itens


# ═══════════════════════════════ ajustes (preferências) ═══════════════════════════════

WU_POL = 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate'


@pacote('ajustes', 'ajustes do Windows', 'preferências: barra, relógio, tema, arquivos ocultos, Num Lock',
        'Personalização, não desempenho: nada aqui vem marcado sozinho (só o "Finalizar tarefa", que é útil para todo mundo). '
        'Marque o que combina com você.')
def itens_ajustes(ctx):
    p = ctx.perfil
    win11 = pf(p, 'so.win11', True)
    pers = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize'
    dev = any(pf(p, 'tem.' + k) for k in ('wsl', 'docker', 'visualstudio', 'ssh')) or bool(shutil.which('git'))
    return [
        Item('finalizar', '"Finalizar tarefa" no botão direito da barra', 'Fecha um programa travado direto pela barra de tarefas, '
             'sem abrir o Gerenciador.', 'menos passos para matar travados', 'nenhum', 2,
             R(ADV + '\\TaskbarDeveloperSettings', 'TaskbarEndTask', 1)) if win11 else None,
        Item('caminhos', 'caminhos longos (mais de 260 letras)', 'Libera nomes de pasta longos, comuns em projetos de programação (node_modules).',
             'menos erros "caminho muito longo"', 'programas antigos podem não entender esses caminhos', 2 if dev else 0,
             R('HKLM:\\SYSTEM\\CurrentControlSet\\Control\\FileSystem', 'LongPathsEnabled', 1)),
        Item('chamadas', 'volume do jogo igual em chamadas', 'O Windows deixa de abaixar os outros sons quando detecta uma chamada '
             '(Discord, Teams): o jogo fica no mesmo volume. Não mexe na qualidade do áudio.', 'jogo e chamada no mesmo volume',
             'quem gosta que a música abaixe nas ligações perde isso', 2,
             R('HKCU:\\Software\\Microsoft\\Multimedia\\Audio', 'UserDuckingPreference', 3)),
        Item('esquerda', 'barra de tarefas à esquerda', 'Ícones alinhados à esquerda, como no Windows 10.', 'costume', 'nenhum', 0,
             R(ADV, 'TaskbarAl', 0)) if win11 else None,
        Item('segundos', 'segundos no relógio', 'Mostra os segundos no relógio da barra.', 'precisão', 'gasta um pouquinho de bateria', 0,
             R(ADV, 'ShowSecondsInSystemClock', 1)),
        Item('escuro', 'tema escuro', 'Windows e apps no modo escuro.', 'conforto à noite', 'nenhum', 0,
             RR(R(pers, 'AppsUseLightTheme', 0), R(pers, 'SystemUsesLightTheme', 0))),
        Item('ocultos', 'mostrar arquivos ocultos', 'O Explorador mostra pastas como AppData.', 'achar arquivos de configuração',
             'dá para apagar algo importante sem querer', 0, R(ADV, 'Hidden', 1)),
        Item('bandeja', 'todos os ícones na bandeja', 'Mostra todos os ícones perto do relógio, sem a setinha (Windows 10).',
             'vê o que está rodando', 'bandeja mais cheia', 0, R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer', 'EnableAutoTray', 0)) if not win11 else None,
        Item('numlock', 'Num Lock ligado ao iniciar', 'O teclado numérico já vem ligado na tela de entrada.', 'digitar o PIN direto', 'nenhum', 0,
             RR(R('HKCU:\\Control Panel\\Keyboard', 'InitialKeyboardIndicators', '2', 'String'),
                R('Registry::HKEY_USERS\\.DEFAULT\\Control Panel\\Keyboard', 'InitialKeyboardIndicators', '2147483650', 'String'))),
        Item('historico-clip', 'histórico da área de transferência', 'Win+V mostra o que você copiou antes.', 'produtividade',
             'o que você copia fica guardado na memória', 0, R('HKCU:\\Software\\Microsoft\\Clipboard', 'EnableClipboardHistory', 1)),
        Item('compacto', 'Explorador compacto', 'Menos espaço entre os itens das pastas.', 'cabe mais na tela', 'nenhum', 0,
             R(ADV, 'UseCompactMode', 1)) if win11 else None,
        Item('adiar-recursos', 'adiar as atualizações grandes do Windows por 90 dias',
             'Define a política "adiar atualizações de recursos" por 90 dias. As correções de segurança continuam chegando todo mês; só a '
             'atualização grande (a que muda o Windows) chega depois, quando já foi testada por mais gente.',
             'menos surpresas e menos bugs de versão nova', 'recursos novos chegam 90 dias depois; o Windows passa a dizer que "algumas configurações são gerenciadas pela organização"', 0,
             RR(R(WU_POL, 'DeferFeatureUpdates', 1), R(WU_POL, 'DeferFeatureUpdatesPeriodInDays', 90))),
        Item('sem-reinicio-auto', 'não reiniciar sozinho com você logado',
             'Impede o Windows Update de reiniciar o PC por conta própria enquanto há alguém usando (o aviso para reiniciar continua).',
             'sem perder trabalho por um reinício surpresa', 'esquecer de reiniciar deixa a atualização pendente', 2,
             R(WU_POL + '\\AU', 'NoAutoRebootWithLoggedOnUsers', 1)),
        Item('caixas', 'caixas de seleção nos arquivos', 'Uma caixinha para marcar vários arquivos sem segurar Ctrl.', 'útil em tela de toque',
             'nenhum', 0, R(ADV, 'AutoCheckSelect', 1)),
    ]
