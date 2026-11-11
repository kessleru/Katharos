

# ███████████████████████████████████████████████████████████████████████████
#
#   PARTE 2 · ITENS, ESCOLHA E EXECUÇÃO
#   cada mudança é um item explicado (o que faz, ganho, custo, modo); a pessoa marca o que quiser
#
# ███████████████████████████████████████████████████████████████████████████

class Item:
    """Uma mudança. nivel: 1 seguro, 2 equilibrado, 3 extremo, 0 só se a pessoa marcar.
    ps: PowerShell (usa Set-Valor, Set-Servico, Set-Tarefa... que guardam o estado anterior).
    py: função(ctx, item, pr, teste) para o que precisa de Python (remoções uma a uma, ferramentas longas).
    grupo: itens do mesmo grupo se excluem (marcar um desmarca o outro).
    nota: o que este PC tem que mudou a recomendação."""

    def __init__(self, id, titulo, explica, ganho='', custo='', nivel=1, ps=None, py=None, minutos=3,
                 sozinho=False, grupo=None, nota='', reverte=True, dados=None, conflita=(), alerta='', recorrente=False):
        self.id, self.titulo, self.explica, self.ganho, self.custo = id, titulo, explica, ganho, custo
        self.nivel, self.ps, self.py, self.minutos, self.sozinho = nivel, ps, py, minutos, sozinho
        self.grupo, self.nota, self.reverte, self.dados = grupo, nota, reverte, dados
        self.conflita = set(conflita)  # ids que não fazem sentido junto com este (marcar este desmarca aqueles)
        self.alerta = alerta  # o que pode dar problema depois (ex.: anti-cheat), mostrado em amarelo
        self.recorrente = recorrente  # ação que se repete (limpar, otimizar): nunca conta como "já feito", porque o PC volta a precisar
        self.marcado = False
        self.ja = None   # conferido antes de aplicar: True já está assim, False falta, None não entra na conta

    @property
    def definitivo(self):
        """Ajuste que fica gravado no Windows e dá para conferir em modo teste: só estes entram na lista do que já está feito,
        na conferência depois de aplicar e na reaplicação em segundo plano. Ação que se repete (limpar, otimizar) não."""
        return bool(self.ps) and not self.py and not self.sozinho and not self.recorrente


class Pacote:
    def __init__(self, nome, titulo, resumo, explica, itens, reversivel=True, admin=True):
        self.nome, self.titulo, self.resumo, self.explica = nome, titulo, resumo, explica
        self.itens, self.reversivel, self.admin = itens, reversivel, admin


PACOTES = {}
# Pacotes de manutenção: limpar, reparar e atualizar são ações que se repetem. "Nada a limpar agora" não é "já feito":
# com o tempo o PC volta a precisar, então nunca entram na conta do que já está aplicado.
PACOTES_RECORRENTES = ('limpar', 'reparar', 'atualizar')
SEM_ITENS = {}   # pacote -> o que dizer quando não há nada a fazer neste PC


def pacote(nome, titulo, resumo, explica, reversivel=True, admin=True):
    """Registra um pacote: a função recebe ctx e devolve a lista de Itens que se aplicam a este PC."""
    def reg(f):
        PACOTES[nome] = Pacote(nome, titulo, resumo, explica, f, reversivel, admin)
        return f
    return reg


def nivel_do_modo(modo):
    return NIVEL_MODO.get(modo, 2)


def marca_por_modo(itens, modo):
    n = nivel_do_modo(modo)
    vistos = set()
    for it in itens:
        it.marcado = 1 <= it.nivel <= n
        if it.marcado and it.grupo:
            if it.grupo in vistos:
                it.marcado = False
            vistos.add(it.grupo)
    for it in itens:
        if it.marcado and it.conflita:
            for o in itens:
                if o.id in it.conflita:
                    o.marcado = False


def _alterna(itens, idx):
    it = itens[idx]
    it.marcado = not it.marcado
    if it.marcado:
        for o in itens:
            if o is not it and ((it.grupo and o.grupo == it.grupo) or o.id in it.conflita or it.id in o.conflita):
                o.marcado = False


def _numeros(txt, maximo):
    nums = []
    for a, b, c in re.findall(r'(\d+)\s*-\s*(\d+)|(\d+)', txt):
        lo, hi = (int(a), int(b)) if a else (int(c), int(c))
        for n in range(min(lo, hi), max(lo, hi) + 1):
            if 0 < n <= maximo:
                nums.append(n)
    return nums


def _detalhe_item(t, it):
    """O que o item faz, o ganho, o custo e os avisos: o texto inteiro de um item."""
    t.paragrafo(it.explica, 8, 'sub')
    extra = []
    if it.ganho:
        extra.append(t.p('ganho: ', 'apagado') + t.p(it.ganho, 'verde'))
    if it.custo:
        extra.append(t.p('custo: ', 'apagado') + t.p(it.custo, 'amarelo'))
    for e in extra:
        if vlen(e) <= t.largura - 8:
            t.escreve(' ' * 8 + e)
        else:
            rot, _, resto = ANSI.sub('', e).partition(': ')
            t.paragrafo(f'{rot}: {resto}', 8, 'verde' if rot == 'ganho' else 'amarelo')
    if it.nota:
        t.paragrafo('neste PC: ' + it.nota, 8, 'azul')
    medido = prova_do_item(getattr(it, 'pacote', None), it.id) if getattr(it, 'pacote', None) else ''
    if medido:
        t.paragrafo(medido, 8, 'verde' if 'liberou' in medido or 'a menos' in medido or 'a mais' in medido else 'apagado')
    if it.alerta:
        t.paragrafo('atenção: ' + it.alerta, 8, 'amarelo')
    if not it.reverte:
        t.paragrafo('não volta com o "desfazer" (reinstale se precisar)', 8, 'apagado')


def confere_itens(ctx, itens, pacote_=None):
    """Antes de aplicar: roda os itens em modo teste (nada muda) e marca em cada um it.ja = True (o PC já está assim),
    False (ainda falta) ou None (não entra na conta: itens de Python, que rodam sozinhos, ações que se repetem, ou que deram erro).
    Guarda em ctx.ja para não conferir duas vezes na mesma sessão."""
    cache = getattr(ctx, 'ja', None)
    if cache is None:
        cache = ctx.ja = {}
    vs = []
    for i in itens:
        chave = (pacote_ or getattr(i, 'pacote', None) or '', i.id)
        if chave in cache:
            i.ja = cache[chave]
            continue
        i.ja = None
        if i.definitivo and chave[0] not in PACOTES_RECORRENTES:
            vs.append((chave, i))
    if not WINDOWS or not vs:
        return
    corpo = '\n'.join('$__p = $script:PLANOS; $__e = $false\ntry {\n' + i.ps + '\n} catch { $__e = $true }\n'
                      'Dado ' + psq('ja:' + i.id) + ' $(if ($__e) { $null } else { $script:PLANOS -eq $__p })' for _, i in vs)
    s = roda_ps(ctx.t, corpo, 'confere', minutos=max(2, len(vs) // 3), teste=True, mostra=False, mult=getattr(ctx, 'mult', 1.0))
    for chave, i in vs:
        v = s.dados.get('ja:' + i.id)
        i.ja = v if isinstance(v, bool) else None
        cache[chave] = i.ja


def _linha_item(t, it, i):
    """Uma linha por item: marca, número e nome. Depois do nome, em palavras, o que pede atenção: "tem aviso" e "sem volta"."""
    ja = getattr(it, 'ja', None) is True
    marca = t.p('✓', 'verde', True) if it.marcado else (t.p('●', 'verde') if ja else t.p('○', 'apagado'))
    extras = [x for x in (('tem aviso' if it.alerta else ''), ('' if it.reverte else 'sem volta')) if x]
    cauda = ''.join(' · ' + x for x in extras)
    feito = ' · já feito' if ja else ''
    nome = corta(it.titulo, max(10, t.largura - 9 - len(cauda) - len(feito)))
    return (f'  {marca} {t.p(f"{i:>2}", "destaque", True)}  {t.p(nome, "texto" if it.marcado else "sub")}'
            f'{t.p(feito, "verde")}{t.p(cauda, "amarelo")}')


def ordem_de_tela(itens, agrupar=True):
    """Os itens na ordem em que aparecem (e são numerados) na tela: agrupados por seguro, equilibrado, extremo e
    opcional, sem mudar a ordem dentro de cada grupo. A lista original não muda: é nela que a aplicação se baseia."""
    if not agrupar:
        return list(itens)
    return [i for nv in ORDEM_NIVEL for i in itens if (i.nivel if i.nivel in ORDEM_NIVEL else 2) == nv]


def desenha_itens(t, itens, completa=False, zero='', agrupar=True):
    """Desenha os itens já na ordem de tela. Com agrupar, cada grupo ganha um título que diz o que ele é."""
    atual = None
    for i, it in enumerate(itens, 1):
        nv = it.nivel if it.nivel in ORDEM_NIVEL else 2
        if agrupar and nv != atual:
            atual = nv
            t.escreve()
            t.escreve('  ' + t.p(NOME_NIVEL[nv], COR_NIVEL.get(nv, 'apagado'), True) + t.p('  ' + EXPLICA_NIVEL[nv], 'apagado'))
        t.escreve(_linha_item(t, it, i))
        if completa:
            _detalhe_item(t, it)
            t.escreve()
    if zero:   # a saída aparece como uma linha da lista, igual ao menu
        if agrupar:
            t.escreve()
        t.escreve(f'  {t.p("   0", "apagado", True)}  {t.p(zero, "apagado")}')


# As três teclas que aparecem na tela de escolha; as outras ficam na ajuda ("?").
DICAS_ESCOLHA = [('Enter', 'continuar'), ('número', 'marcar ou desmarcar'), ('? 3', 'explica o item 3')]
AJUDA_ESCOLHA = [
    ('Enter', 'continuar com os itens marcados'),
    ('3', 'marcar ou desmarcar o item 3 (vários de uma vez: 3 5 8-10)'),
    ('? 3', 'explicar o item 3: o que faz, o ganho, o custo e o aviso'),
    ('?', 'esta ajuda'),
    ('t', 'marcar todos'),
    ('n', 'desmarcar todos'),
    ('s  e  x', 'marcar o que o modo seguro, equilibrado ou extremo marca'),
    ('c', 'mostrar ou esconder a explicação de todos'),
    ('v 3', 'ver o código (PowerShell) do item 3'),
    ('0', 'voltar sem aplicar nada'),
]


def mostra_codigo(t, itens):
    """Mostra o que cada item vai executar de verdade (PowerShell) antes de aplicar."""
    for it in itens:
        t.titulo(f'{it.titulo}  ·  id: {it.id}')
        if it.ps:
            for linha in it.ps.strip().splitlines():
                t.escreve('    ' + t.p(corta(linha, max(20, t.largura - 6)), 'sub'))
        elif it.py:
            t.paragrafo(f'feito em Python pela função {getattr(it.py, "__name__", "?")} (ler no katharos.py)', 4, 'sub')
        else:
            t.paragrafo('sem código', 4, 'apagado')


def escolhe_itens(ctx, itens, modo, args, titulo='o que fazer', manter_marcas=False, agrupar=True):
    """A tela de escolha: uma linha por item, em grupos (seguro, equilibrado, extremo, opcional) que dizem o que cada
    um é; o modo marca o grupo dele e os de cima, e a pessoa ajusta. Devolve os marcados na ordem original (a de aplicar),
    ou None se voltou. A explicação de um item aparece com "? número" (ou de todos, com "c").
    agrupar=False para listas que não são itens de um pacote (as etapas do turbo)."""
    t = ctx.t
    if agrupar and WINDOWS and any(i.ps for i in itens):
        t.nota('  conferindo o que já está feito neste PC (nada muda)…')
        confere_itens(ctx, itens)
    if not manter_marcas:
        marca_por_modo(itens, modo)
        for i in itens:   # o que o PC já tem não vem marcado: aplicar de novo não muda nada
            if getattr(i, 'ja', None) is True:
                i.marcado = False
    n_ja = sum(getattr(i, 'ja', None) is True for i in itens)
    completa = config('explicacao') == 'completa'
    originais, itens = itens, ordem_de_tela(itens, agrupar)   # a tela numera pelos grupos; a aplicação segue a ordem original
    t.titulo(f'{titulo} · {pl(len(itens), "item", "itens")}' + (f' · {n_ja} já feitos' if n_ja else '')
             + (f' · o modo {modo} marcou {sum(i.marcado for i in itens)}' if not manter_marcas else ''))
    if n_ja and not manter_marcas:
        t.nota(f'  {pl(n_ja, "item já está feito", "itens já estão feitos")} neste PC (● verde): não vêm marcados.')
    interativo = t.interativo and not getattr(args, 'sim', False)
    desenha_itens(t, itens, completa, zero='voltar' if interativo else '', agrupar=agrupar)
    if not interativo:
        return [i for i in originais if i.marcado]
    while True:
        marcados = sum(i.marcado for i in itens)
        t.escreve()
        t.dicas(DICAS_ESCOLHA)
        r = t.pergunta(f'{marcados} de {len(itens)} marcados').strip().lower()
        if r in ('', 'ok', 'seguir', 'aplicar'):
            return [i for i in originais if i.marcado]
        if r in ('0', 'v', 'voltar', 'q', 'sair'):
            return None
        mudou = True
        m = re.match(r'^(?:\?\s*(\d+)|(\d+)\s*\?)$', r)
        if m:
            mudou = False
            n = int(m.group(1) or m.group(2))
            if 0 < n <= len(itens):
                t.escreve()
                t.escreve(_linha_item(t, itens[n - 1], n))
                _detalhe_item(t, itens[n - 1])
            else:
                t.aviso(f'não existe o item {n}.')
        elif r in ('?', 'ajuda', 'h', 'm', 'mais'):
            mudou = False
            t.escreve()
            for tecla, faz in AJUDA_ESCOLHA:
                t.escreve(f'    {t.p(f"{tecla:<8}", "destaque", True)}  {t.p(faz, "sub")}')
            t.escreve()
            t.paragrafo('Os itens estão em grupos. Cada modo marca o grupo dele e os de cima; os opcionais nenhum modo marca. '
                        '"tem aviso" quer dizer que vale ler a explicação antes (? e o número).', 4, 'apagado')
        elif r in ('t', 'todos'):
            for i in itens:
                i.marcado = True
            grupos = set()
            for i in itens:
                if i.grupo:
                    if i.grupo in grupos:
                        i.marcado = False
                    grupos.add(i.grupo)
        elif r in ('n', 'nenhum'):
            for i in itens:
                i.marcado = False
        elif r in ('s', 'seguro', 'e', 'equilibrado', 'x', 'extremo'):
            modo = {'s': 'seguro', 'e': 'equilibrado', 'x': 'extremo'}.get(r, r)
            marca_por_modo(itens, modo)
        elif r in ('c', 'curta', 'completa'):
            completa = not completa
        elif r in ('l', 'listar'):
            pass
        elif re.match(r'^v\s*\d+$', r):
            mudou = False
            n = int(r[1:].strip())
            if 0 < n <= len(itens):
                mostra_codigo(t, [itens[n - 1]])
            else:
                t.aviso(f'não existe o item {n}.')
        else:
            nums = _numeros(r, len(itens)) if re.match(r'^[\d\s,;-]+$', r) else []
            if not nums:
                mudou = False
                t.aviso(f'"{corta(r, 20)}" não é uma opção. Digite ? para ver a ajuda.')
            for n in nums:
                _alterna(itens, n - 1)
        if mudou:
            t.escreve()
            desenha_itens(t, itens, completa, zero='voltar', agrupar=agrupar)


# ─────────────── executar ───────────────

def _envolve(it, prova=None):
    # cada item diz o próprio nome, roda protegido e, no fim, diz se mudou algo ou se já estava assim.
    # prova=N: depois do item sai um retrato (espaço, RAM, processos, serviços) para a prova de ganho item por item
    fim = f"if (-not $TESTE) {{ Dado 'prova:{prova}' (Retrato ($script:MUDOU - $__a)) }}\n" if prova is not None else ''
    return ('Diz "secao" ' + psq(it.titulo) + '\n'
            '$__a = $script:MUDOU; $__p = $script:PLANOS\n'
            'try {\n' + it.ps + '\n} catch { Aviso (' + psq(it.titulo + ': ') + ' + $_.Exception.Message) }\n'
            'if ($TESTE) { if ($script:PLANOS -eq $__p) { Diz "nada" "ja esta assim" } }\n'
            'elseif ($script:MUDOU -gt $__a) { Feito ("feito ({0} {1})" -f ($script:MUDOU - $__a), $(if (($script:MUDOU - $__a) -eq 1) { "mudanca" } else { "mudancas" })) }\n'
            'else { Diz "nada" "ja estava assim" }\n' + fim)


def _andamento_marca(ctx, pac, itens):
    """Anota no estado que uma aplicação começou: se o PC travar ou a janela fechar, o 'retomar' sabe o que faltou."""
    e = estado()
    e['em_andamento'] = {'pacote': pac.nome, 'ids': [i.id for i in itens], 'feitos': [], 'quando': agora_iso(),
                         'origem': getattr(getattr(ctx, 'args', None), 'comando', None) or ''}
    salva_estado(e)


def _andamento_avanca(ids):
    e = estado()
    a = e.get('em_andamento')
    if a:
        a['feitos'] = sorted(set(a.get('feitos', [])) | set(ids))
        salva_estado(e)


def pendentes_andamento():
    """(pacote, ids que faltam, andamento) da última aplicação interrompida, ou None. Pacote que não existe mais é ignorado."""
    a = estado().get('em_andamento')
    if not isinstance(a, dict) or a.get('pacote') not in PACOTES:
        return None
    falta = [i for i in a.get('ids', []) if i not in set(a.get('feitos', []))]
    return (a['pacote'], falta, a) if falta else None


def executa_itens(ctx, pac, itens, teste=False):
    """Roda os itens escolhidos. Os de PowerShell leves vão juntos num processo; os longos, sozinhos.
    Devolve (feitos, avisos, erros)."""
    t = ctx.t
    blocos, atual = [], []
    for it in itens:
        if it.py or it.sozinho:
            if atual:
                blocos.append(atual)
                atual = []
            blocos.append([it])
        else:
            atual.append(it)
    if atual:
        blocos.append(atual)
    feitos, avisos, erros = 0, 0, 0
    eventos = []
    nome_bk = pac.nome if pac.reversivel else None
    provas, ensaio, hw = [], None, ''
    if not teste:
        _andamento_marca(ctx, pac, itens)
        try:   # a prova de ganho nunca pode impedir a aplicação
            ensaio = abre_ensaio(ctx, pac, itens)
            hw = classe_hw(ctx.perfil or {})
        except Exception as e:
            LOG.escreve(f'ensaio não abriu: {e!r}')

    def anota(it, antes, depois, mudou):
        provas.append({'t': agora_iso(), 'pacote': pac.nome, 'id': it.id, 'titulo': it.titulo, 'mudou': int(mudou or 0),
                       'd': delta_retrato(antes, depois), 'ensaio': ensaio, 'hw': hw})
    with Progresso(t, len(itens), 'aplicando' if not teste else 'simulando') as pr:
        for bloco in blocos:
            it0 = bloco[0]
            if it0.py:
                t.escreve('  ' + t.p('◆', 'destaque') + ' ' + t.p(it0.titulo, 'texto', True))
                pr.atual = it0.titulo
                foto = None if teste else retrato()
                try:
                    r = it0.py(ctx, it0, pr, teste) or (0, 0)
                    if foto is not None:
                        anota(it0, foto, retrato(), r[0])
                    feitos += r[0]
                    avisos += r[1] if len(r) > 1 else 0
                    eventos.append({'tipo': 'itens', 'pacote': pac.nome, 'ids': [it0.id], 'feitos': r[0], 'avisos': [], 'erros': []})
                except Exception as e:  # um item com problema não derruba o resto
                    erros += 1
                    t.erro(f'{it0.titulo}: {e}')
                    LOG.escreve(f'ERRO {it0.titulo}: {e!r}')
                    eventos.append({'tipo': 'itens', 'pacote': pac.nome, 'ids': [it0.id], 'feitos': 0, 'avisos': [],
                                    'erros': [f'{type(e).__name__}: {e}' + (f' → {dica_erro(e)}' if dica_erro(e) else '')]})
                pr.avanca(it0.titulo)
                if not teste:
                    _andamento_avanca([it0.id])
                continue
            corpo = "if (-not $TESTE) { Dado 'prova:antes' (Retrato) }\n" + '\n'.join(_envolve(i, n) for n, i in enumerate(bloco))
            minutos = sum(i.minutos for i in bloco)
            pr.atual = it0.titulo
            s = roda_ps(t, corpo, f'{pac.nome}-{it0.id}', minutos=minutos, pacote=nome_bk, teste=teste, pr=pr,
                        mult=ctx.mult, vigia_ocioso=True)
            feitos += len(s.feitos) + len(s.planos)
            avisos += len(s.avisos)
            erros += len(s.erros)
            eventos.append({'tipo': 'itens', 'pacote': pac.nome, 'ids': [i.id for i in bloco], 'feitos': len(s.feitos) + len(s.planos),
                            'avisos': [x + (f' → {dica_erro(x)}' if dica_erro(x) else '') for x in s.avisos[:4]],
                            'erros': [x + (f' → {dica_erro(x)}' if dica_erro(x) else '') for x in s.erros[:4]], 'tempo_s': round(s.tempo)})
            foto = s.dados.get('prova:antes')
            for n, i in enumerate(bloco):   # cada item é comparado com o retrato tirado logo antes dele
                depois = s.dados.get(f'prova:{n}')
                if isinstance(foto, dict) and isinstance(depois, dict):
                    anota(i, foto, depois, depois.get('m'))
                    foto = depois
            if s.estourou:
                eventos[-1]['erros'].append('passou do limite de tempo e foi encerrado → demorou demais: tente de novo com o PC parado')
                erros += 1
                t.erro(f'{it0.titulo}: passou do limite de {br(minutos * ctx.mult, 0)} min e foi encerrado; segui adiante.')
            pr.avanca(bloco[-1].titulo, len(bloco))
            if not teste:
                _andamento_avanca([i.id for i in bloco])
    ctx.ultimos_eventos = eventos   # a API devolve os avisos e erros de cada bloco para a interface
    if not teste:
        e = estado()
        e.pop('em_andamento', None)
        pacs = e.setdefault('pacotes', {})
        reg = pacs.get(pac.nome) or {}
        ids = set(reg.get('itens', [])) | {i.id for i in itens}
        pacs[pac.nome] = {'quando': agora_iso(), 'itens': sorted(ids), 'revertido': False}
        salva_estado(e)
        rel_eventos([ev for ev in eventos if ev['feitos'] or ev['avisos'] or ev['erros']])
        try:
            registra_provas(provas)
            if provas:
                mostra_provas_da_aplicacao(t, provas)
        except Exception as e:
            LOG.escreve(f'provas não gravaram: {e!r}')
    return feitos, avisos, erros


def garante_ponto(ctx, teste=False):
    """Ponto de restauração antes de mexer (no máximo um por dia; liga a Proteção do Sistema se estiver desligada)."""
    if teste or not WINDOWS:
        return
    ult = estado().get('ultimo_ponto')
    try:
        if ult and (datetime.now() - datetime.fromisoformat(ult)).total_seconds() < 86400:
            return
    except ValueError:
        pass
    ok, gb, precisa = espaco_ok('ponto')
    if not ok:
        ctx.t.aviso(f'Só há {gb:.1f} GB livres em C:. O ponto de restauração pede cerca de {precisa:g} GB e pode falhar; '
                    'sem ele, o desfazer por valor continua valendo.')
    corpo = r'''
Vivo 'ponto de restauracao'
try { Enable-ComputerRestore -Drive "$env:SystemDrive\" -ErrorAction Stop } catch {}
$k = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SystemRestore'
$antes = (Get-ItemProperty $k -Name SystemRestorePointCreationFrequency -ErrorAction SilentlyContinue).SystemRestorePointCreationFrequency
New-ItemProperty $k -Name SystemRestorePointCreationFrequency -Value 0 -PropertyType DWord -Force | Out-Null
$__t0 = (Get-Date).AddMinutes(-10)
try {
  Checkpoint-Computer -Description 'Antes do Katharos' -RestorePointType MODIFY_SETTINGS -ErrorAction Stop
  # confere lendo de volta: só diz "criado" se o Windows mostra um ponto novo com este nome
  $__rp = Get-ComputerRestorePoint -ErrorAction SilentlyContinue | Where-Object { $_.Description -eq 'Antes do Katharos' -and $_.ConvertToDateTime($_.CreationTime) -ge $__t0 } | Select-Object -First 1
  if ($__rp) { Ok 'ponto de restauracao criado: "Antes do Katharos"' } else { Aviso 'o Windows nao mostra o ponto de restauracao novo (a Protecao do Sistema pode estar desligada por politica)' }
}
catch { Aviso ('ponto de restauracao nao criado: ' + $_.Exception.Message) }
if ($null -eq $antes) { Remove-ItemProperty $k -Name SystemRestorePointCreationFrequency -ErrorAction SilentlyContinue } else { Set-ItemProperty $k -Name SystemRestorePointCreationFrequency -Value $antes }
'''
    with Progresso(ctx.t, None, 'ponto de restauração') as pr:
        s = roda_ps(ctx.t, corpo, 'ponto', minutos=15, pr=pr, mult=ctx.mult)
    if not s.avisos and s.ok:
        marca_estado('ultimo_ponto', agora_iso())


def precisa_admin(ctx, args):
    """Sem administrador, oferece abrir de novo como administrador. Devolve True se pode seguir."""
    t = ctx.t
    if not WINDOWS:
        t.erro('O katharos só funciona no Windows.')
        return False
    if dentro_de_pacote() and not getattr(ctx, '_avisou_pacote', False):
        ctx._avisou_pacote = True
        t.info('Python da Microsoft Store: o PowerShell vai rodar fora do contêiner dela (pelo WMI), para as mudanças '
               'valerem no registro de verdade.')
    if eh_admin() or args.teste:
        return True
    t.aviso('Isso precisa de administrador.')
    if t.interativo and t.pergunta('abrir como administrador? s = sim, Enter = não').strip().lower() in ('s', 'sim'):
        if eleva(sys.argv[1:] or [args.comando or '']):
            t.info('Abri uma janela nova como administrador; continue por lá.')
        else:
            t.erro('Não consegui abrir como administrador.')
    else:
        t.paragrafo('Feche e abra o terminal com o botão direito > Executar como administrador, ou abra pelo KATHAROS.bat ou pelo atalho na área de trabalho (eles já abrem como administrador).', 2, 'apagado')
    return False


def confere_conta(ctx):
    """Elevado com outra conta, o HKCU mexido seria o do administrador, não o seu."""
    dono = str(pf(ctx.perfil or {}, 'sistema.dono_explorer', '') or '')
    eu = os.environ.get('USERNAME', '')
    if dono and eu and dono.lower() != eu.lower():
        ctx.t.aviso(f'Você abriu como administrador com outra conta ({eu}); a área de trabalho é de {dono}. '
                    'As preferências do usuário seriam mudadas na conta errada. Entre na conta de '
                    f'{dono} e abra como administrador por ela.')
        return False
    return True


def resumo_antes(t, pac, itens, titulo=True, recuo=2):
    """Logo antes do "Aplicar?": o que cada item faz, o que se ganha, o que se perde e se volta com o desfazer."""
    if titulo:
        t.titulo(f'antes de aplicar: {pac.titulo}')
    for it in itens:
        t.item('◆', 'destaque', corta(tela(it.titulo), 70), recuo=recuo)
        if getattr(it, 'ganho', ''):
            t.paragrafo('ganha: ' + it.ganho, recuo + 4, 'sub')
        if getattr(it, 'custo', '') and it.custo != 'nenhum':
            t.paragrafo('perde: ' + it.custo, recuo + 4, 'apagado')
        if getattr(it, 'alerta', ''):
            t.paragrafo('atenção: ' + it.alerta, recuo + 4, 'amarelo')
    if pac.reversivel:
        t.nota(' ' * recuo + 'Tudo isto volta com "katharos desfazer ' + pac.nome + '".')
    else:
        t.aviso('Parte disto não volta com o desfazer (programas e apps removidos, arquivos apagados). Confira a lista.')


def ferramenta_pacote(ctx, args, nome=None):
    """Tela de um pacote: explica, mostra os itens marcados pelo modo, deixa escolher, confirma e aplica."""
    t = ctx.t
    pac = PACOTES[nome or args.comando]
    t.aba(pac.resumo)
    t.paragrafo(pac.explica, 2, 'sub')
    if pac.admin and not precisa_admin(ctx, args):
        return 1
    p = perfil_pc(ctx)
    if pac.admin and not confere_conta(ctx) and not args.teste:
        return 1
    itens = [i for i in (pac.itens(ctx) or []) if i]
    for i in itens:
        i.pacote = pac.nome
    itens, fora = aplica_protegidos(pac.nome, itens)
    if fora:
        t.nota(f'  {pl(fora, "item protegido", "itens protegidos")} (config protegidos): fora desta lista.')
    if not itens:
        if pac.nome in SEM_ITENS:
            t.aviso(SEM_ITENS[pac.nome])
        else:
            t.ok('Nada a fazer aqui neste PC.')
        return 0
    aplica_alertas(pac.nome, itens)
    pode, modo = cuidado_empresa(ctx, args, pac)
    if not pode:
        return 0
    so = (getattr(ctx, 'itens_busca', None) or {}).pop(pac.nome, None)
    if so and any(i.id in so for i in itens):   # veio da busca: só o item procurado vem marcado
        for i in itens:
            i.marcado = i.id in so
        escolhidos = escolhe_itens(ctx, itens, modo, args, titulo='o que você procurou vem marcado', manter_marcas=True)
    else:
        escolhidos = escolhe_itens(ctx, itens, modo, args)
    if escolhidos is None:
        t.nota('voltou sem aplicar nada.')
        return 0
    if not escolhidos:
        t.nota('nada marcado.')
        return 0
    if getattr(args, 'codigo', False):
        mostra_codigo(t, escolhidos)
        t.nota('modo código: nada foi aplicado.')
        return 0
    if args.teste:
        t.titulo('simulação (nada é alterado)')
        executa_itens(ctx, pac, escolhidos, teste=True)
        t.nota('modo teste: o que tem ○ azul seria mudado; o resto já está como deveria.')
        return 0
    resumo_antes(t, pac, escolhidos)
    if not t.confirma(f'Aplicar {pl(len(escolhidos), "item", "itens")} de {pac.titulo}?', sim=args.sim):
        t.nota('nada foi alterado.')
        return 0
    garante_ponto(ctx)
    inicio = time.time()
    livre_ant = livre_bytes()
    t.titulo('aplicando')
    feitos, avisos, erros = executa_itens(ctx, pac, escolhidos)
    livre_dep = livre_bytes()
    liberado = (livre_dep - livre_ant) if (livre_ant is not None and livre_dep is not None and livre_dep > livre_ant) else 0
    if livre_ant is not None and livre_dep is not None and pac.nome in ('limpar', 'disco'):
        rel_eventos([{'tipo': 'espaco', 'pacote': pac.nome, 'livre_antes': livre_ant, 'livre_depois': livre_dep,
                      'texto': f'livre em C: {br(livre_ant / 1073741824, 1)} → {br(livre_dep / 1073741824, 1)} GB'}])
    t.titulo('resumo', caixa=True)
    linhas = [('itens', str(len(escolhidos))), ('mudanças', t.p(str(feitos), 'verde')),
              ('avisos', t.p(str(avisos), 'amarelo' if avisos else 'apagado')),
              ('erros', t.p(str(erros), 'vermelho' if erros else 'apagado')), ('tempo', duracao(time.time() - inicio))]
    if liberado:
        linhas.insert(2, ('espaço liberado', t.p(humano(liberado), 'verde')))
    t.chaves(linhas)
    t.fecha_caixa()
    cache_ja = getattr(ctx, 'ja', None)
    if cache_ja:   # o que foi conferido antes de aplicar já não vale: o PC mudou
        for chave in [c for c in cache_ja if c[0] == pac.nome]:
            del cache_ja[chave]
    if pac.nome in REAPLICA and feitos:
        planos = verifica_pacote(ctx, pac.nome, [i.id for i in escolhidos])
        if planos:
            t.aviso(f'Conferi depois: {pl(len(planos), "ajuste não ficou", "ajustes não ficaram")} (o Windows ou uma política pode estar segurando):')
            for x in planos[:5]:
                t.paragrafo('· ' + corta(x, 90), 6, 'sub')
            rel_eventos([{'tipo': 'nao-ficou', 'pacote': pac.nome, 'texto': '; '.join(planos[:6])}])
        else:
            t.ok('Conferi depois: tudo ficou como foi aplicado.')
    if pac.reversivel:
        t.nota(f'para voltar: katharos desfazer {pac.nome}')
        if feitos:
            manter_ou_desfazer(ctx, args, [pac.nome])
    return 1 if erros else 0
