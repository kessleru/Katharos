# ─────────────── acompanhamento em segundo plano: o Katharos.exe ───────────────
# O Katharos.exe fica rodando perto do relógio e lê o PC sem parar, no ritmo da config tempo-real (padrão: a cada 1 s): CPU, placa de vídeo,
# RAM, disco, rede, temperatura. Percebe quando há um jogo aberto e grava a sessão. Tudo vai para ~/.katharos:
#   agora.json      a leitura de agora (o "aovivo" e o medir leem daqui)
#   minutos.jsonl   uma linha por minuto, 14 dias (o painel desenha as últimas 24 h)
#   sessoes.jsonl   uma linha por sessão de jogo: quanto tempo, o que ficou no limite (a central de inteligência aprende com elas)
# O código do executável está em exe/Katharos.cs, e a publicação compila ele no próprio Windows, com assinatura do GitHub.
# Os limites do motor de inteligência, numa fonte só. O Katharos.exe recebe uma cópia embutida (exe/regras.json, gravada pela montagem)
# e a de ~/.katharos/regras.json, que o Katharos grava junto com a config: mudar aqui muda o ícone, a central e o raio-x.
REGRAS_MOTOR = {
    'versao': 1,
    # gargalo agora (por leitura): placa de vídeo no limite com a CPU sobrando, e o contrário
    'gpu_limite': 95, 'gpu_nucleo_folga': 90, 'cpu_nucleo_limite': 95, 'cpu_gpu_folga': 85,
    # CPU freando: abaixo desta % da frequência normal, com pelo menos esta % de uso
    'freio_desempenho': 75, 'freio_cpu_min': 40,
    'ram_cheia': 90, 'vram_cheia': 95, 'disco_cheio': 95, 'calor_cpu': 90, 'calor_gpu': 85,
    # quanto da janela precisa estar no limite para virar conclusão
    'janela_s': 30, 'janela_min_leituras': 3, 'minutos_depois_do_boot': 10, 'fracao_calor': 0.5, 'fracao_freio': 0.6, 'fracao_gargalo': 0.6, 'fracao_vram': 0.6, 'fracao_ram': 0.8, 'fracao_disco': 0.8,
    'cpu_ocupada': 85, 'fracao_cpu_ocupada': 0.8,
    # o que conta como jogo aberto e como a sessão fecha
    'jogo_gpu_min': 20, 'jogo_gpu_ativo': 5, 'jogo_segundos_comecar': 10, 'jogo_segundos_fechar': 30, 'sessao_principal_min': 0.2,
    # a central, olhando as sessões (% do tempo jogado em cada limite) e os minutos fora de jogo
    'central_horas_min': 1, 'central_cpu': 25, 'central_freio': 15, 'central_calor': 10, 'central_ram': 15, 'central_vram': 20, 'central_disco': 15,
    'central_gpu': 40, 'repouso_minutos_min': 120, 'repouso_cpu': 60, 'repouso_cpu_fracao': 0.25, 'repouso_ram': 85, 'repouso_ram_fracao': 0.4,
}


def escreve_regras(destino=None):
    """Grava os limites para o Katharos.exe ler (relidos a cada minuto)."""
    try:
        arq = Path(destino) if destino else CASA / 'regras.json'
        arq.parent.mkdir(parents=True, exist_ok=True)
        tmp = arq.with_name(arq.name + '.tmp')
        tmp.write_text(json.dumps(REGRAS_MOTOR, ensure_ascii=False, indent=1, sort_keys=True) + '\n', encoding='utf-8')
        os.replace(tmp, arq)
        return True
    except OSError as e:
        LOG.escreve(f'regras: {e!r}')
        return False


EXE_NOME = 'Katharos.exe'
SP_CONFIG = 'segundo-plano.json'
SP_MUTEX = 'Local\\KatharosSegundoPlano'
SP_EV_SAIR = 'Local\\KatharosSegundoPlanoSair'
RUN_CHAVE = r'Software\Microsoft\Windows\CurrentVersion\Run'
TAREFA_ABRE_SP = 'Katharos - abrir segundo plano'
NOMES_LIMITE = {'gpu': 'placa de vídeo no limite', 'cpu': 'CPU segurando o jogo', 'freio': 'CPU abaixo da velocidade', 'ram': 'RAM cheia',
                'vram': 'memória de vídeo cheia', 'disco': 'disco ocupado', 'calor': 'calor', 'equilibrado': 'nada no limite'}


def exe_do_pacote():
    """O Katharos.exe que veio no zip, ao lado da pasta programa (Katharos/Katharos.exe e Katharos/programa/katharos.py)."""
    p = Path(__file__).resolve().parent.parent / EXE_NOME
    return p if p.is_file() else None


def exe_instalado():
    return CASA / EXE_NOME


def exe_disponivel():
    p = exe_do_pacote()
    if p:
        return p
    i = exe_instalado()
    return i if i.is_file() else None


def sp_rodando():
    """O segundo plano está aberto? (o executável segura um mutex com nome enquanto roda)"""
    if not WINDOWS:
        return False
    try:
        import ctypes
        h = ctypes.windll.kernel32.OpenMutexW(0x00100000, False, SP_MUTEX)
        if h:
            ctypes.windll.kernel32.CloseHandle(h)
            return True
    except Exception:
        pass
    return False


def sp_para(espera_s=6):
    """Pede para o segundo plano fechar (evento com nome) e espera ele sair."""
    if not WINDOWS or not sp_rodando():
        return True
    try:
        import ctypes
        h = ctypes.windll.kernel32.OpenEventW(0x0002, False, SP_EV_SAIR)
        if h:
            ctypes.windll.kernel32.SetEvent(h)
            ctypes.windll.kernel32.CloseHandle(h)
    except Exception as e:
        LOG.escreve(f'segundo plano: não pedi para fechar ({e!r})')
    fim = time.time() + espera_s
    while time.time() < fim:
        if not sp_rodando():
            return True
        time.sleep(0.25)
    return not sp_rodando()


def config_segundo_plano():
    """O que o executável lê (e relê a cada 30 s): onde está o Katharos, o ritmo e os limites."""
    py = Path(sys.executable)
    pyw = py.with_name('pythonw.exe')
    ps1 = Path(__file__).resolve().parent / 'katharos.ps1'
    if ps1.is_file():
        marca_estado('ps1', str(ps1))
    else:
        ps1 = Path(estado().get('ps1') or ps1)
    try:
        intervalo = float(config('tempo-real', '1'))
    except (TypeError, ValueError):
        intervalo = 1.0
    return {'versao': VERSAO, 'ps1': str(ps1), 'py': str(py if not py.name.lower().startswith('pythonw') else py.with_name('python.exe')),
            'pyw': str(pyw) if pyw.exists() else '', 'kpy': str(CASA / 'katharos.py'), 'intervalo_s': intervalo,
            'em_jogo': config('coleta-em-jogo', 'segura'), 'notificar': config('avisos', 'sim'), 'fps': config('fps', 'sim'),
            'energia_auto': config('energia-automatica', 'nao') == 'sim', 'energia_tomada': config('energia-tomada', ''),
            'energia_bateria': config('energia-bateria', ''), 'energia_tomada_nome': config('energia-tomada-nome', ''),
            'energia_bateria_nome': config('energia-bateria-nome', ''),
            'aviso_cpu': REGRAS_MOTOR['calor_cpu'], 'aviso_gpu': REGRAS_MOTOR['calor_gpu'],
            'nomes_de_jogo': nomes_de_jogo()}


def escreve_config_sp():
    try:
        CASA.mkdir(parents=True, exist_ok=True)
        tmp = CASA / (SP_CONFIG + '.tmp')
        tmp.write_text(json.dumps(config_segundo_plano(), ensure_ascii=False, indent=1), encoding='utf-8')
        os.replace(tmp, CASA / SP_CONFIG)
        escreve_regras()
        return True
    except OSError as e:
        LOG.escreve(f'segundo plano: não gravei a config ({e!r})')
        return False


def inicia_com_windows(ligar=True):
    """Abre ao entrar no Windows pela chave Run do seu usuário: aparece na aba Inicializar do Gerenciador de Tarefas, onde dá para desligar."""
    if not WINDOWS:
        return False
    try:
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_CHAVE) as k:
            if ligar:
                winreg.SetValueEx(k, 'Katharos', 0, winreg.REG_SZ, f'"{exe_instalado()}" --segundo-plano')
            else:
                try:
                    winreg.DeleteValue(k, 'Katharos')
                except FileNotFoundError:
                    pass
        return True
    except OSError as e:
        LOG.escreve(f'segundo plano: chave Run ({e!r})')
        return False


def inicia_com_windows_ligado():
    if not WINDOWS:
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_CHAVE) as k:
            winreg.QueryValueEx(k, 'Katharos')
            return True
    except OSError:
        return False


def abre_segundo_plano(ctx=None, mostrar=False):
    """Abre o executável como o seu usuário. Se o Katharos estiver como administrador, abre por uma tarefa de uso único sem privilégio
    elevado: o segundo plano nunca roda como administrador."""
    exe = exe_instalado()
    if not WINDOWS or not exe.is_file():
        return False
    args = ['--segundo-plano'] + (['--mostrar'] if mostrar else [])
    if eh_admin() and ctx is not None:
        corpo = ps_monta(r'''
$__a = New-ScheduledTaskAction -Execute «exe» -Argument «arg»
$__p = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
if ($TESTE) { Plano 'abrir o segundo plano como o seu usuário'; return }
Register-ScheduledTask -TaskName «nome» -Action $__a -Principal $__p -Force | Out-Null
Start-ScheduledTask -TaskName «nome»
Start-Sleep -Seconds 2
Unregister-ScheduledTask -TaskName «nome» -Confirm:$false -ErrorAction SilentlyContinue
''', exe=psq(exe), arg=psq(' '.join(args)), nome=psq(TAREFA_ABRE_SP))
        s = roda_ps(ctx.t, corpo, 'abrir-segundo-plano', minutos=1, mostra=False)
        return s.ok and not s.erros
    try:
        subprocess.Popen([str(exe)] + args, creationflags=0x00000008 | 0x00000200, close_fds=True)
        return True
    except OSError as e:
        LOG.escreve(f'segundo plano: não abriu ({e!r})')
        return False


def instala_segundo_plano(ctx, mostrar=True, quieto=False):
    """Copia o executável e o programa para ~/.katharos (sobrevivem a apagar a pasta do zip), grava a config, liga ao entrar no Windows,
    tira o ícone antigo (PowerShell) e abre. Devolve False se não há executável (rodando só o katharos.py)."""
    t = ctx.t
    origem = exe_disponivel()
    if not origem:
        return False
    destino = exe_instalado()
    try:
        CASA.mkdir(parents=True, exist_ok=True)
        if Path(__file__).resolve() != (CASA / 'katharos.py').resolve():
            shutil.copy2(Path(__file__).resolve(), CASA / 'katharos.py')
        if origem.resolve() != destino.resolve():
            if destino.is_file() and sp_rodando():
                sp_para()
            shutil.copy2(origem, destino)
        pm = origem.with_name('PresentMon.exe')
        if pm.is_file() and pm.resolve() != (CASA / 'PresentMon.exe').resolve():
            shutil.copy2(pm, CASA / 'PresentMon.exe')   # FPS nas sessões de jogo (Intel, licença MIT); roda só durante o jogo
    except OSError as e:
        if not quieto:
            t.erro(f'Não consegui copiar o Katharos.exe para {CASA} ({e}). Feche o ícone do Katharos e tente de novo.')
        LOG.escreve(f'segundo plano: cópia falhou ({e!r})')
        return False
    escreve_config_sp()
    inicia_com_windows(True)
    if estado().get('bandeja') == 'sim' or WINDOWS:
        try:
            remove_bandeja(ctx)   # o ícone antigo, em PowerShell, sai: o executável faz tudo o que ele fazia e mais
        except Exception as e:
            LOG.escreve(f'ícone antigo: {e!r}')
    e = estado()
    e['segundo_plano'] = 'sim'
    e['bandeja'] = 'executavel'
    salva_estado(e)
    try:
        (CASA / 'segundo-plano-fechado.txt').unlink()   # ligar de novo vale mais que o "sair" de antes
    except OSError:
        pass
    if not sp_rodando():
        abre_segundo_plano(ctx, mostrar=mostrar)
    return True


def _sha(arq):
    try:
        return hashlib.sha256(Path(arq).read_bytes()).hexdigest()
    except OSError:
        return ''


def remove_segundo_plano(ctx):
    sp_para()
    inicia_com_windows(False)
    marca_estado('segundo_plano', 'nao')


def garante_segundo_plano(ctx):
    """Na leitura de 15 min: se o segundo plano está ligado e caiu, abre de novo (como o seu usuário: a tarefa já roda assim)."""
    if not WINDOWS or estado().get('segundo_plano') != 'sim' or not exe_instalado().is_file() or sp_rodando():
        return False
    if (CASA / 'segundo-plano-fechado.txt').exists():   # você saiu pelo ícone: volta só no próximo início do Windows ou quando ligar de novo
        return False
    try:
        subprocess.Popen([str(exe_instalado()), '--segundo-plano'], creationflags=0x00000008 | 0x00000200, close_fds=True)
        LOG.escreve('segundo plano: tinha fechado, abri de novo')
        return True
    except OSError:
        return False


def migra_segundo_plano(ctx):
    """Quem já tinha o acompanhamento contínuo (ou o ícone antigo) passa para o executável na primeira vez que abre esta versão pelo zip."""
    if not WINDOWS:
        return False
    e = estado()
    if e.get('segundo_plano') in ('sim', 'nao') or not exe_do_pacote():
        if e.get('segundo_plano') == 'sim':
            escreve_config_sp()   # caminho do programa e do Python podem ter mudado
            if exe_do_pacote() and exe_instalado().is_file() and _sha(exe_do_pacote()) != _sha(exe_instalado()):
                instala_segundo_plano(ctx, mostrar=False, quieto=True)   # versão nova do executável
        return False
    if e.get('manut_freq') == 'continua' or e.get('bandeja') == 'sim':
        if instala_segundo_plano(ctx, mostrar=True, quieto=True):
            ctx.t.ok('O acompanhamento contínuo agora roda pelo Katharos.exe: o ícone está perto do relógio, com as métricas ao vivo.')
            return True
    return False


# ───────── temperatura de quem tem driver de sensor ─────────

def temperaturas_externas(espera_s=8):
    """Temperatura de CPU e GPU pelo Katharos.exe: a leitura de agora do segundo plano, ou uma leitura avulsa (--sensores). Ele lê do
    LibreHardwareMonitor, HWiNFO, MSI Afterburner, Core Temp ou AIDA64 abertos (memória compartilhada, só leitura) e do driver de vídeo.
    Devolve {'cpu', 'cpu_fonte', 'gpu', 'gpu_fonte'} ou None."""
    a = le_agora()
    if a and (a.get('temp_cpu') is not None or a.get('temp_gpu') is not None):
        return {'cpu': a.get('temp_cpu'), 'cpu_fonte': a.get('temp_cpu_fonte'), 'gpu': a.get('temp_gpu'), 'gpu_fonte': a.get('temp_gpu_fonte')}
    exe = exe_disponivel() if WINDOWS else None
    if not exe:
        return None
    destino = CASA / 'sensores.json'
    try:
        CASA.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(exe), '--sensores', str(destino)], timeout=espera_s, creationflags=0x08000000, close_fds=True)
    except (OSError, subprocess.SubprocessError) as e:
        LOG.escreve(f'sensores: {e!r}')
        return None
    d = le_json(destino, None)
    return d if isinstance(d, dict) and (d.get('cpu') is not None or d.get('gpu') is not None) else None


def completa_temperaturas(m, cpu='temperatura', cpu_fonte='temp_fonte', gpu='temperatura_gpu', gpu_fonte='temp_gpu_fonte'):
    """Preenche o que o PowerShell não achou (o Windows não mostra a CPU de muitos PCs) com a leitura do Katharos.exe. Sobrescreve a zona
    térmica do ACPI, que é da placa-mãe e não da CPU."""
    if not isinstance(m, dict) or (m.get(cpu) is not None and m.get(cpu_fonte) not in (None, 'zona térmica') and m.get(gpu) is not None):
        return m
    x = temperaturas_externas()
    if not x:
        return m
    if x.get('cpu') is not None and (m.get(cpu) is None or m.get(cpu_fonte) in (None, 'zona térmica')) and x.get('cpu_fonte') != 'zona térmica':
        m[cpu], m[cpu_fonte] = x['cpu'], x.get('cpu_fonte')
    if x.get('gpu') is not None and m.get(gpu) is None:
        m[gpu], m[gpu_fonte] = x['gpu'], x.get('gpu_fonte')
    return m


# ───────── FPS de verdade: o grupo "Usuários de log de desempenho" ─────────
# O PresentMon lê eventos do Windows (ETW) e, sem administrador, só funciona para quem está nesse grupo (SID S-1-5-32-559, o nome
# muda com o idioma). Entrar no grupo é opcional, pedido e explicado; vale depois de sair e entrar na conta; desligar tira de volta.
GRUPO_LOG_DESEMPENHO = 'S-1-5-32-559'


def fps_no_grupo(ctx):
    """O usuário já está no grupo? (lido do Windows; None se não deu para saber)"""
    if not WINDOWS:
        return None
    s = roda_ps(ctx.t, f"Dado 'grupo' ([bool](Tenta {{ Get-LocalGroupMember -SID '{GRUPO_LOG_DESEMPENHO}' -ErrorAction Stop | Where-Object {{ $_.Name -like ('*\\' + $env:USERNAME) }} }} $null))",
                'fps-grupo', minutos=1, mostra=False)
    return s.dados.get('grupo')


def fps_permissao(ctx, ligar=True):
    """Põe (ou tira) o seu usuário no grupo. Precisa de administrador; vale depois de sair e entrar de novo na conta do Windows."""
    acao = 'Add-LocalGroupMember' if ligar else 'Remove-LocalGroupMember'
    corpo = f'''
$__quem = "$env:USERDOMAIN\\$env:USERNAME"
if ($TESTE) {{ Plano '{"pôr" if ligar else "tirar"} o seu usuário no grupo Usuários de log de desempenho (medida de FPS)'; return }}
try {{ {acao} -SID '{GRUPO_LOG_DESEMPENHO}' -Member $__quem -ErrorAction Stop; Feito '{"medida de FPS liberada: vale depois de sair e entrar na conta" if ligar else "medida de FPS desligada"}' }}
catch {{ if ("$($_.Exception.Message)" -match 'already|já é membro|not a member|não é membro') {{ Feito 'já estava assim' }} else {{ Aviso ("nao consegui: " + $_.Exception.Message) }} }}
'''
    s = roda_ps(ctx.t, corpo, 'fps-permissao', minutos=1)
    if s.ok and not s.erros:
        marca_estado('fps_grupo', 'sim' if ligar else 'nao')
        return True
    return False


# ───────── os dados que o executável grava ─────────

def le_agora(max_idade_s=15):
    """A leitura de agora, se o segundo plano está rodando (e escreveu há pouco)."""
    d = le_json(CASA / 'agora.json', None)
    if not isinstance(d, dict):
        return None
    try:
        q = datetime.fromisoformat(d.get('quando'))
    except (TypeError, ValueError):
        return None
    if (datetime.now() - q).total_seconds() > max_idade_s:
        return None
    d['_dt'] = q
    return d


def _le_jsonl(arq, campo, desde):
    out = []
    try:
        with open(arq, encoding='utf-8', errors='replace') as f:
            for linha in f:
                try:
                    d = json.loads(linha)
                    dt = datetime.fromisoformat(d[campo])
                except (ValueError, KeyError, TypeError):
                    continue
                if dt >= desde:
                    d['_dt'] = dt
                    out.append(d)
    except OSError:
        pass
    return out


def le_minutos(horas=24, agora=None):
    return _le_jsonl(CASA / 'minutos.jsonl', 't', (agora or datetime.now()) - timedelta(hours=horas))


def le_sessoes(dias=60, agora=None):
    return _le_jsonl(CASA / 'sessoes.jsonl', 'inicio', (agora or datetime.now()) - timedelta(days=dias))


def resumo_sessoes(sessoes, minimo_min=5):
    """O que as sessões de jogo dizem juntas: horas jogadas, o limite mais comum e quanto tempo cada limite durou (ponderado pela duração)."""
    ss = [s for s in sessoes if isinstance(s.get('min'), (int, float)) and s['min'] >= minimo_min]
    if not ss:
        return None
    total = sum(s['min'] for s in ss)
    limites = {}
    for s in ss:
        for k, v in (s.get('tempo_no_limite') or {}).items():
            if isinstance(v, (int, float)):
                limites[k] = limites.get(k, 0) + v * s['min'] / total
    principal = {}
    for s in ss:
        p = s.get('principal') or 'equilibrado'
        principal[p] = principal.get(p, 0) + s['min']
    def maxi(c):
        v = [s[c] for s in ss if isinstance(s.get(c), (int, float))]
        return max(v) if v else None
    jogos = {}
    for s in ss:
        jogos[s.get('jogo') or '?'] = jogos.get(s.get('jogo') or '?', 0) + s['min']
    return {'sessoes': len(ss), 'horas': round(total / 60, 1), 'limites': {k: round(v, 0) for k, v in limites.items()},
            'principal': max(principal, key=principal.get), 'temp_cpu_max': maxi('temp_cpu_max'), 'temp_gpu_max': maxi('temp_gpu_max'),
            'ram_max': maxi('ram_max'), 'vram_max': maxi('vram_max'), 'desempenho_min': min([s['desempenho_min'] for s in ss if isinstance(s.get('desempenho_min'), (int, float))] or [0]) or None,
            'jogos': sorted(jogos.items(), key=lambda x: -x[1])}


# ───────── os comandos ─────────

def ferramenta_segundo_plano(ctx, args):
    """Acompanhamento: liga, desliga e ajusta o segundo plano."""
    t = ctx.t
    t.aba('acompanhamento em segundo plano: o Katharos perto do relógio, lendo o PC sem parar')
    if not WINDOWS:
        t.erro('só funciona no Windows.')
        return 1
    exe = exe_disponivel()
    if not exe:   # só o katharos.py, sem o zip: fica o ícone simples de antes
        t.paragrafo('Para o acompanhamento completo (métricas ao vivo, sessões de jogo, painel no ícone) baixe o Katharos.zip: ele traz o Katharos.exe. '
                    'Só com o katharos.py, o Katharos liga o ícone simples, que mostra a leitura de 15 em 15 minutos.', 2, 'sub')
        return ferramenta_bandeja(ctx, args)
    if getattr(args, 'parar', False) or getattr(args, 'desligar', False):
        remove_segundo_plano(ctx)
        t.ok('Segundo plano desligado e tirado da inicialização. Os dados que ele guardou ficam em ' + str(CASA) + '.')
        return 0
    iv = getattr(args, 'intervalo', None)
    if iv:
        salva_config('tempo-real', str(iv))
        escreve_config_sp()
        t.ok(f'Lendo a cada {iv} s (vale em até 30 s, sem reiniciar).')
        return 0
    if getattr(args, 'ligar', False) or getattr(args, 'agendada', False) or (not t.interativo and args.sim):
        ok = instala_segundo_plano(ctx, mostrar=not getattr(args, 'agendada', False))
        if ok:
            t.ok('Segundo plano ligado. O ícone do Katharos está perto do relógio (se não aparecer, clique na setinha ^ e arraste-o para fora).')
        return 0 if ok else 1
    rodando = sp_rodando()
    a = le_agora()
    t.paragrafo('O ícone do Katharos fica perto do relógio. Clique nele para o painel ao vivo: CPU, placa de vídeo, RAM, temperatura, disco e rede, '
                'o que está no limite agora e o que a central de inteligência propõe. Com um jogo aberto, ele grava a sessão (quanto tempo, o que segurou o FPS). '
                'Usa uns 30 a 60 MB de RAM e menos de 1 % de CPU, em prioridade baixa. Lê o que o Gerenciador de Tarefas lê: não abre o processo do jogo.', 2, 'sub')
    ss = le_sessoes(30)
    t.titulo('situação')
    t.chaves([('segundo plano', t.p('rodando', 'verde') if rodando else (t.p('ligado, mas fechado', 'amarelo') if estado().get('segundo_plano') == 'sim' else 'desligado')),
              ('abre com o Windows', 'sim' if inicia_com_windows_ligado() else 'não'),
              ('ritmo', f'a cada {config("tempo-real", "1")} s'),
              ('com jogo aberto', 'continua lendo' if config('coleta-em-jogo', 'segura') != 'pausar' else 'pausa'),
              ('avisos', config('avisos', 'sim')),
              *([('notebook: energia sozinha', estado_da_energia(a))] if a and a.get('bateria') is not None else []),
              ('FPS nos jogos', {'sim': 'ligado' + ('' if estado().get('fps_grupo') == 'sim' else ' (falta liberar: f)'), 'nao': 'desligado'}.get(config('fps', 'sim'), '-')),
              ('agora', (f'CPU {br(a.get("cpu"), 0)} % · GPU {br(a.get("gpu"), 0)} % · RAM {br(a.get("ram_pct"), 0)} %'
                         + (f' · {br(a.get("temp_cpu"), 0)} °C' if a.get('temp_cpu') is not None else '')) if a else '-'),
              ('sessões de jogo (30 dias)', str(len(ss)))])
    if not t.interativo:
        return 0
    t.escreve()
    t.paragrafo('l = ligar (e abrir o painel) · d = desligar · r = ritmo (1, 2, 5 ou 10 s) · j = com jogo aberto (continuar ou pausar) · '
                'a = avisos (sim ou não) · f = medir FPS nos jogos · e = notebook: energia sozinha na tomada e na bateria · t = testar neste PC (relatório) · v = ver ao vivo aqui · Enter = voltar', 2, 'apagado')
    r = t.pergunta('fazer').strip().lower()[:1]
    if r == 'l':
        return 0 if instala_segundo_plano(ctx, mostrar=True) else 1
    if r == 'd':
        remove_segundo_plano(ctx)
        t.ok('Segundo plano desligado.')
    elif r == 'r':
        ops = VALIDOS_CONFIG['tempo-real']
        atual = config('tempo-real', '1')
        salva_config('tempo-real', ops[(ops.index(atual) + 1) % len(ops)] if atual in ops else '1')
        escreve_config_sp()
        t.ok(f'Lendo a cada {config("tempo-real")} s.')
    elif r == 'j':
        salva_config('coleta-em-jogo', 'pausar' if config('coleta-em-jogo', 'segura') != 'pausar' else 'segura')
        escreve_config_sp()
        t.ok('Com jogo aberto: ' + ('pausa a leitura.' if config('coleta-em-jogo') == 'pausar' else 'continua lendo.'))
    elif r == 'a':
        salva_config('avisos', 'nao' if config('avisos', 'sim') == 'sim' else 'sim')
        escreve_config_sp()
        t.ok('Avisos: ' + config('avisos'))
    elif r == 'f':
        return liga_fps(ctx, args)
    elif r == 't':
        return teste_no_pc(ctx, exe)
    elif r == 'e':
        return desliga_energia_automatica(ctx) if config('energia-automatica', 'nao') == 'sim' else liga_energia_automatica(ctx, args)
    elif r == 'v':
        return ferramenta_aovivo(ctx, args)
    return 0


def teste_no_pc(ctx, exe):
    """Roda o Katharos.exe --teste-no-pc (uns 40 s, só lê) e mostra o relatório: o que o segundo plano vê neste PC, quanto pesa, e a lista
    do que só você pode conferir. O arquivo fica em ~/.katharos/teste-no-pc.txt."""
    t = ctx.t
    destino = CASA / 'teste-no-pc.txt'
    t.nota('Lendo o PC por uns 40 segundos (nada muda). Se tiver o MSI Afterburner ou o HWiNFO, deixe aberto.')
    try:
        subprocess.run([str(exe), '--teste-no-pc', str(destino)], timeout=180)
    except (OSError, subprocess.TimeoutExpired) as e:
        t.erro(f'o teste não terminou: {e}')
        return 1
    try:
        texto = destino.read_text(encoding='utf-8-sig', errors='replace')
    except OSError:
        t.erro('o teste não gravou o relatório (veja ~/.katharos/segundo-plano.log).')
        return 1
    for linha in texto.splitlines():
        t.escreve(linha)
    t.ok(f'Relatório em {destino}. Anote o que só você pode conferir no fim dele.')
    return 0


def liga_fps(ctx, args):
    """Explica, pergunta e libera (ou desliga) a medida de FPS. Nada muda sem o sim da pessoa."""
    t = ctx.t
    if config('fps', 'sim') == 'sim' and estado().get('fps_grupo') == 'sim':
        if t.confirma('A medida de FPS está ligada. Desligar e tirar o seu usuário do grupo "Usuários de log de desempenho"?', sim=False):
            if not precisa_admin(ctx, args):
                return 1
            fps_permissao(ctx, ligar=False)
            salva_config('fps', 'nao')
            escreve_config_sp()
        return 0
    t.paragrafo('Para medir o FPS de verdade (média, 1% low e travadas) durante os jogos, o Katharos usa o PresentMon, da Intel: ele lê '
                'os eventos de quadro que o próprio Windows registra, como o FrameView da NVIDIA e o CapFrameX. Não abre, não lê e não muda '
                'nada no jogo. O Windows só deixa isso para quem está no grupo "Usuários de log de desempenho". O Katharos põe o seu '
                'usuário nesse grupo (vale depois de sair e entrar na conta) e tira de volta quando você desligar.', 2, 'sub')
    if not t.confirma('Liberar a medida de FPS?', sim=False):
        return 0
    if not precisa_admin(ctx, args):
        return 1
    if fps_permissao(ctx, ligar=True):
        # confere lendo o grupo de volta: só diz "pronto" se o Windows mostra o seu usuário lá
        if fps_no_grupo(ctx) is False:
            marca_estado('fps_grupo', 'nao')
            t.erro('O Windows não mostra o seu usuário no grupo "Usuários de log de desempenho": a medida de FPS não foi liberada. '
                   'Em PC de empresa, uma política pode impedir.')
            return 1
        salva_config('fps', 'sim')
        escreve_config_sp()
        t.ok('Pronto (conferido no Windows). Saia e entre de novo na sua conta do Windows (ou reinicie) para começar a medir.')
        return 0
    return 1


# ───────── notebook: plano de energia sozinho na tomada e na bateria (desligado até a pessoa ligar) ─────────
# O Katharos.exe percebe quando o carregador entra ou sai e ativa o plano escolhido para cada lado (PowerSetActiveScheme: o mesmo que
# escolher o plano no Painel de Controle; não precisa de administrador e não muda nenhum valor dentro dos planos). Desligar volta o
# plano que estava ativo antes de ligar.
PLANO_EQUILIBRADO = '381b4222-f694-41f0-9685-ff5bb260df2e'
PLANO_ECONOMIA = 'a1841308-3541-4fab-bc81-f71556f20b4a'
_RE_PLANO = re.compile(r'([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\s+\((.+?)\)(\s*\*)?')


def planos_de_energia(texto):
    """A saída do `powercfg /list` (em qualquer idioma) vira [{guid, nome, ativo}]."""
    out, vistos = [], set()
    for m in _RE_PLANO.finditer(texto or ''):
        g = m.group(1).lower()
        if g in vistos:
            continue
        vistos.add(g)
        out.append({'guid': g, 'nome': m.group(2).strip(), 'ativo': bool(m.group(3))})
    return out


def sugestao_de_energia(planos):
    """Na tomada: o plano que está ativo agora (o que a pessoa já usa). Na bateria: Equilibrado, ou Economia de energia se o Equilibrado
    já é o da tomada. None quando o PC só tem um plano (notebook moderno: o Windows 11 já separa o modo de energia por tomada e bateria)."""
    if len(planos) < 2:
        return None
    ativo = next((p for p in planos if p['ativo']), planos[0])
    por = {p['guid']: p for p in planos}
    bateria = por.get(PLANO_EQUILIBRADO) if ativo['guid'] != PLANO_EQUILIBRADO else por.get(PLANO_ECONOMIA)
    if not bateria:
        bateria = next(p for p in planos if p['guid'] != ativo['guid'])
    return ativo, bateria


def estado_da_energia(a):
    """O que o segundo plano conferiu de verdade (não o que foi pedido): erro, se a última troca não pegou."""
    if config('energia-automatica', 'nao') != 'sim':
        return 'desligada (e)'
    pedido = config('energia-tomada-nome', '?') + ' na tomada, ' + config('energia-bateria-nome', '?') + ' na bateria'
    en = (a or {}).get('energia') or {}
    if en.get('erro'):
        return 'ERRO: ' + en['erro']
    if en.get('estado') and en.get('conferida'):
        return f'{pedido} · agora {en["estado"]} (conferido às {en["conferida"][11:16]})'
    return pedido + ' · ainda não conferido'


def le_planos_de_energia(ctx):
    s = roda_ps(ctx.t, "Dado 'planos' ((powercfg /list | Out-String)); Dado 'bateria' ([bool](Tenta { Get-CimInstance Win32_Battery -ErrorAction Stop } $null))",
                'planos-de-energia', minutos=1, mostra=False)
    return planos_de_energia(s.dados.get('planos') or ''), bool(s.dados.get('bateria'))


def liga_energia_automatica(ctx, args=None):
    """Mostra os planos, sugere um para a tomada e outro para a bateria, pergunta e liga. Nada muda sem o sim da pessoa."""
    t = ctx.t
    if not WINDOWS:
        t.erro('só funciona no Windows.')
        return 1
    planos, bateria = le_planos_de_energia(ctx)
    if not bateria:
        t.nota('Este PC não tem bateria: a troca automática é só para notebook.')
        return 0
    sug = sugestao_de_energia(planos)
    if not sug:
        t.paragrafo('Este notebook só tem um plano de energia (o Equilibrado), como a maioria dos notebooks novos. Nele, o próprio Windows '
                    'já guarda um modo para a tomada e outro para a bateria: Configurações > Sistema > Energia e bateria > Modo de energia. '
                    'Não há o que o Katharos trocar.', 2, 'sub')
        return 0
    t.paragrafo('Quando você ligar ou tirar o carregador, o segundo plano ativa o plano de energia escolhido para cada lado, na hora. '
                'Não muda nada dentro dos planos e não precisa de administrador. No ícone dá para manter o desempenho por 1 hora na bateria. '
                'Desligar isto volta o plano que está ativo agora.', 2, 'sub')
    for i, p in enumerate(planos, 1):
        t.item(t.p(f'{i:>2}', 'destaque', True), None, p['nome'], t.p('ativo agora' if p['ativo'] else '', 'apagado'))
    tomada, bat = sug

    def escolhe(rotulo, padrao):
        r = t.pergunta(f'{rotulo} (número; Enter = {padrao["nome"]})').strip() if t.interativo else ''
        return planos[int(r) - 1] if r.isdigit() and 0 < int(r) <= len(planos) else padrao
    tomada = escolhe('na tomada', tomada)
    bat = escolhe('na bateria', bat)
    if tomada['guid'] == bat['guid']:
        t.nota('O mesmo plano nos dois lados: não há o que trocar. Nada foi ligado.')
        return 0
    if not t.confirma(f'Ligar: {tomada["nome"]} na tomada e {bat["nome"]} na bateria?', sim=False):
        return 0
    antes = next((p for p in planos if p['ativo']), None)
    # prova antes de dizer que ligou: ativa o plano do lado de agora e lê de volta 3 s depois. Se o Windows não ficar assim, não liga.
    v = confere_troca_de_energia(ctx, tomada['guid'], bat['guid'])
    if not v['ok']:
        t.erro('Não deu para ligar neste PC: ' + v['motivo'])
        if antes and v.get('mudou'):
            roda_ps(ctx.t, f"powercfg /setactive {antes['guid']} | Out-Null", 'energia-de-volta', minutos=1, mostra=False)
        return 1
    if antes:
        salva_config('energia-antes', antes['guid'])
    salva_config('energia-tomada', tomada['guid'])
    salva_config('energia-tomada-nome', tomada['nome'])
    salva_config('energia-bateria', bat['guid'])
    salva_config('energia-bateria-nome', bat['nome'])
    salva_config('energia-automatica', 'sim')
    escreve_config_sp()
    t.ok(f'Ligado e conferido: {v["lado"]}, o Windows ficou no plano certo. A troca vale em até 30 s, sem reiniciar'
         + ('' if sp_rodando() else ' (quando o segundo plano estiver rodando)') + '; cada troca é conferida de novo, e se não pegar o ícone avisa.')
    return 0


def confere_troca_de_energia(ctx, tomada, bateria):
    """Ativa o plano do lado de agora (tomada ou bateria) e confere, lendo de volta, se o Windows ficou nele. Sem falso positivo:
    só devolve ok quando a leitura bate."""
    for g in (tomada, bateria):
        if not re.fullmatch(r'[0-9a-f-]{36}', g or ''):
            return {'ok': False, 'motivo': 'plano inválido.'}
    corpo = f'''
Add-Type -AssemblyName System.Windows.Forms
$__l = "$([System.Windows.Forms.SystemInformation]::PowerStatus.PowerLineStatus)"
$__alvo = if ($__l -eq 'Offline') {{ '{bateria}' }} else {{ '{tomada}' }}
$__antes = (powercfg /getactivescheme | Out-String)
powercfg /setactive $__alvo 2>&1 | Out-Null
$__cod = $LASTEXITCODE
Start-Sleep -Seconds 3
$__depois = (powercfg /getactivescheme | Out-String)
Dado 'lado' $__l; Dado 'codigo' $__cod; Dado 'ok' ($__depois -match $__alvo); Dado 'mudou' ($__antes -notmatch $__alvo)
'''
    s = roda_ps(ctx.t, corpo, 'confere-energia', minutos=1, mostra=False)
    lado = {'Offline': 'na bateria', 'Online': 'na tomada'}.get(s.dados.get('lado'), 'agora')
    if s.dados.get('ok') is True:
        return {'ok': True, 'lado': lado, 'mudou': bool(s.dados.get('mudou'))}
    if s.dados.get('ok') is None:
        return {'ok': False, 'motivo': 'não consegui ler o plano ativo do Windows.', 'mudou': False}
    cod = s.dados.get('codigo')
    motivo = ('o Windows recusou a troca de plano (talvez política da empresa).' if cod not in (0, None)
              else 'o Windows não ficou no plano escolhido (algum programa, como o de energia do fabricante, pode estar segurando o plano).')
    return {'ok': False, 'motivo': motivo, 'mudou': bool(s.dados.get('mudou'))}


def desliga_energia_automatica(ctx):
    """Desliga a troca e volta o plano que estava ativo antes de ligar (se ele ainda existe)."""
    t = ctx.t
    salva_config('energia-automatica', 'nao')
    escreve_config_sp()
    antes = config('energia-antes', '')
    if WINDOWS and re.fullmatch(r'[0-9a-f-]{36}', antes or ''):
        planos, _ = le_planos_de_energia(ctx)
        if any(p['guid'] == antes for p in planos):
            roda_ps(ctx.t, f"powercfg /setactive {antes} | Out-Null; Feito 'plano de energia de antes ativado'", 'energia-de-volta', minutos=1)
    t.ok('Troca automática de energia desligada.')
    return 0


def ferramenta_aovivo(ctx, args):
    """As métricas de agora, atualizando no terminal até você apertar Ctrl+C."""
    t = ctx.t
    t.aba('métricas em tempo real (Ctrl+C para sair)')
    if not le_agora():
        if WINDOWS and exe_disponivel() and not sp_rodando():
            t.nota('O segundo plano não está rodando; vou abrir.')
            if estado().get('segundo_plano') != 'sim':
                instala_segundo_plano(ctx, mostrar=False)
            else:
                abre_segundo_plano(ctx)
            for _ in range(12):
                time.sleep(0.5)
                if le_agora():
                    break
        if not le_agora():
            t.erro('Sem leitura ao vivo: o tempo real vem do Katharos.exe (acompanhamento). Abra o Katharos pelo Katharos.exe do zip e ligue o segundo plano.')
            return 1
    vezes = int(getattr(args, 'segundos', 0) or 0)
    linhas_ant = 0
    hist = {'cpu': [], 'gpu': []}
    n = 0
    try:
        while True:
            a = le_agora() or {}
            for k in hist:
                hist[k] = (hist[k] + [a.get(k) if isinstance(a.get(k), (int, float)) else 0])[-40:]
            j = a.get('jogo') or {}
            ls = [f'  CPU   {br(a.get("cpu"), 0):>4} %   {sparkline_txt(hist["cpu"], getattr(t, "ascii", False))}   núcleo máx. {br(a.get("nucleo_max"), 0)} %'
                  + (f' · {br(a.get("cpu_ghz"), 1)} GHz' if a.get('cpu_ghz') else ''),
                  f'  GPU   {br(a.get("gpu"), 0):>4} %   {sparkline_txt(hist["gpu"], getattr(t, "ascii", False))}   memória {br(a.get("vram_gb"), 1)} GB',
                  f'  RAM   {br(a.get("ram_pct"), 0):>4} %   {br(a.get("ram_gb"), 1)} de {br(a.get("ram_total_gb"), 0)} GB',
                  f'  temp  CPU {br(a.get("temp_cpu"), 0) if a.get("temp_cpu") is not None else "-"} °C · GPU {br(a.get("temp_gpu"), 0) if a.get("temp_gpu") is not None else "-"} °C',
                  f'  disco {br(a.get("disco"), 0):>4} %   rede ↓ {br((a.get("rede_baixa_mbs") or 0) * 8, 1)} Mb/s ↑ {br((a.get("rede_sobe_mbs") or 0) * 8, 1)} Mb/s',
                  ('  jogo  ' + f'{j.get("nome")} há {br(j.get("min"), 0)} min · limite: {NOMES_LIMITE.get(j.get("principal"), j.get("principal"))}') if j else '  jogo  nenhum aberto']
            if j and j.get('fps') is not None:
                ls.append(f'  fps   {br(j.get("fps"), 0):>4}     média {br(j.get("fps_med"), 0)} · 1% low {br(j.get("fps_1low"), 0)} · travadas/min {br(j.get("travadas_por_min"), 1)}')
            elif j and j.get('fps_estado') == 'sem permissão':
                ls.append('  fps   não liberado: katharos segundo-plano, opção f')
            for c in (a.get('conclusoes') or [])[:2]:
                ls.append(f'  {"!" if c.get("nivel", 0) >= 1 else "·"} {c.get("titulo")}: {c.get("texto")}'[:160])
            if linhas_ant and t.interativo and t.cor:
                sys.stdout.write(f'\x1b[{linhas_ant}F\x1b[J')
            for l in ls:
                t.escreve(l)
            sys.stdout.flush()
            linhas_ant = len(ls)
            n += 1
            if vezes and n >= vezes:
                return 0
            if not t.interativo and not vezes:
                return 0
            time.sleep(max(0.5, float(a.get('intervalo_s') or 1)))
    except KeyboardInterrupt:
        t.escreve()
        return 0
