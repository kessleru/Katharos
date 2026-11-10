# ███████████████████████████████████████████████████████████████████████████
#
#   VERSÕES · trocar o Katharos por um mais novo sem perder nada
#
#   Tudo o que o Katharos sabe do PC fica em ~/.katharos (fora da pasta do programa): medidas, raio-x, pacotes
#   aplicados, backups do desfazer, provas de ganho, preferências. Trocar a pasta do programa não apaga nada disso.
#   O que este arquivo garante, na primeira vez que uma versão nova roda:
#     1. reconhece de qual versão os dados vieram (mesmo de versões que ainda não anotavam isso);
#     2. guarda uma cópia dos arquivos pequenos de estado antes de tocar em qualquer coisa;
#     3. converte o formato dos dados, um passo de cada vez (MIGRACOES), sem nunca jogar fora o que não conhece;
#     4. atualiza as cópias do programa que ficam fora da pasta (atalhos, tarefa agendada, link do painel),
#        que senão continuariam rodando a versão antiga;
#     5. traz os relatórios da pasta antiga para a nova;
#     6. diz à pessoa, em poucas linhas, o que continua valendo.
#   Se os dados foram gravados por uma versão MAIS NOVA que esta, nada é convertido nem carimbado: só um aviso.
#
# ███████████████████████████████████████████████████████████████████████████

VERSAO_DADOS = 2          # sobe quando o formato do que fica em ~/.katharos muda (e ganha um passo em MIGRACOES)
COPIAS_DE_VERSAO = 5      # quantas cópias de segurança de troca de versão ficam guardadas
ARQUIVOS_DE_ESTADO = ('estado.json', 'config.json', 'relatorio.json', 'ensaios.json')
MIGRACOES = []            # [(número, descrição, função(estado, casa))], em ordem


def migracao(numero, descricao):
    """Registra um passo de conversão dos dados. Cada passo recebe o estado (dicionário, para alterar no lugar) e a
    pasta dos dados; precisa poder rodar duas vezes sem estragar nada e nunca apagar chave que não conhece."""
    def reg(f):
        MIGRACOES.append((numero, descricao, f))
        MIGRACOES.sort(key=lambda m: m[0])
        return f
    return reg


@migracao(1, 'carimbo de versão nos dados')
def _m_carimbo(e, casa):
    # versões até a 1.4.1 não anotavam a própria versão; o histórico começa com o que dá para saber
    e.setdefault('versoes', [])


@migracao(2, 'os perfis saíram: o uso do comando "perfil" sai da lista de usados')
def _m_sem_perfil(e, casa):
    usado = e.get('usado')
    if isinstance(usado, dict):
        usado.pop('perfil', None)
    cfg = casa / 'config.json'
    c = le_json(cfg, {})
    if isinstance(c, dict) and c.get('explicacao') not in (None, '', 'curta', 'completa'):
        c.pop('explicacao')   # valor que a versão nova não entende volta para o padrão
        grava_json(cfg, c)


def _v(txt):
    """'2.0.0' → (2, 0, 0), para comparar versões. O que não for número vira 0."""
    return tuple(int(x) if x.isdigit() else 0 for x in re.findall(r'\d+', str(txt or '')))[:3] or (0,)


def versao_anterior(e, casa=None):
    """A versão que gravou os dados que estão aqui, ou None se é a primeira vez do Katharos neste PC.
    Versões antigas não carimbavam o estado: aí vale a versão anotada no relatório único, e, sem ele, 'anterior'."""
    if e.get('versao_programa'):
        return str(e['versao_programa'])
    if not e:
        return None
    try:
        r = json.loads((Path(casa or CASA) / 'relatorio.json').read_text(encoding='utf-8-sig'))
        if isinstance(r, dict) and r.get('katharos'):
            return str(r['katharos'])
    except (OSError, ValueError):
        pass
    return 'anterior'


def guarda_copia_de_versao(de, casa=None):
    """Antes de converter: copia os arquivos pequenos de estado para ~/.katharos/versoes/<versão>_<data>. Devolve a pasta."""
    casa = Path(casa or CASA)
    destino = casa / 'versoes' / f'{re.sub(r"[^0-9A-Za-z.]", "", str(de)) or "anterior"}_{datetime.now():%Y%m%d-%H%M%S}'
    try:
        destino.mkdir(parents=True, exist_ok=True)
        for nome in ARQUIVOS_DE_ESTADO:
            if (casa / nome).is_file():
                shutil.copy2(casa / nome, destino / nome)
        antigas = sorted(p for p in (casa / 'versoes').iterdir() if p.is_dir())
        for p in antigas[:-COPIAS_DE_VERSAO]:
            shutil.rmtree(p, ignore_errors=True)
    except OSError as ex:
        LOG.escreve(f'cópia de versão não gravou: {ex!r}')
        return None
    return destino


def o_que_ficou(e=None, casa=None):
    """O que a versão anterior deixou e continua valendo: [(rótulo, texto)]. Só conta; não abre nada pesado."""
    casa = Path(casa or CASA)
    e = estado() if e is None else e
    out = []
    pacs = [n for n, r in (e.get('pacotes') or {}).items() if isinstance(r, dict) and not r.get('revertido')]
    if pacs:
        out.append(('aplicado', pl(len(pacs), 'pacote', 'pacotes') + ' (o "desfazer" continua valendo): ' + ', '.join(sorted(pacs)[:8]) + ('…' if len(pacs) > 8 else '')))

    def linhas(nome):
        try:
            with open(casa / nome, 'rb') as f:
                return sum(1 for _ in f)
        except OSError:
            return 0
    def arquivos(sub, padrao='*'):
        try:
            return sum(1 for _ in (casa / sub).glob(padrao))
        except OSError:
            return 0
    n = linhas('metricas.jsonl')
    if n:
        out.append(('segundo plano', pl(n, 'medida', 'medidas') + ' para os gráficos do painel'))
    n = arquivos('medidas', '*.json')
    if n:
        out.append(('medidas', pl(n, 'medida completa', 'medidas completas') + ' (antes e depois)'))
    n = arquivos('bench', '*.json')
    if n:
        out.append(('benchmark', pl(n, 'rodada', 'rodadas')))
    n = linhas('provas.jsonl')
    if n:
        out.append(('provas de ganho', pl(n, 'item medido', 'itens medidos')))
    try:
        rx = ((json.loads((casa / 'relatorio.json').read_text(encoding='utf-8-sig')).get('secoes') or {}).get('raiox') or {})
        if rx.get('dados', {}).get('nota') is not None:
            out.append(('último raio-x', f'nota {rx["dados"]["nota"]}/100' + (f', {ha_quanto_iso(rx.get("quando"))}' if ha_quanto_iso(rx.get('quando')) else '')))
    except (OSError, ValueError, AttributeError):
        pass
    if e.get('manut_freq'):
        out.append(('manutenção agendada', str(e['manut_freq'])))
    if e.get('aviso_aceito'):
        out.append(('aviso de uso', 'já aceito'))
    return out


def _iguais(a, b):
    try:
        import filecmp
        return filecmp.cmp(str(a), str(b), shallow=False)
    except OSError:
        return False


def atualiza_copias(mudou_versao=True):
    """As cópias do programa que vivem fora da pasta baixada: a dos atalhos (~/.katharos/app), a da tarefa agendada
    (ProgramData, só administrador grava) e o link katharos:// do painel. Sem isto, os atalhos e a manutenção
    continuariam rodando a versão antiga. Devolve [(o que, 'ok' | 'pendente', frase)]. Só age rodando da pasta "programa"."""
    eu = Path(__file__).resolve()
    out = []
    if eu.parent.name.lower() != 'programa':
        return out
    app = CASA / 'app' / 'katharos.py'
    try:
        if app.is_file() and not _iguais(eu, app):
            instala_app()
            out.append(('atalhos', 'ok', 'os atalhos da área de trabalho passaram a abrir esta versão'))
    except Exception as ex:
        LOG.escreve(f'cópia dos atalhos não atualizou: {ex!r}')
    try:
        tarefa = pasta_da_tarefa() / 'katharos.py'
        if tarefa.is_file() and tarefa.resolve() != eu and not _iguais(eu, tarefa):
            try:
                shutil.copy2(eu, tarefa)
                out.append(('manutenção agendada', 'ok', 'a manutenção em segundo plano passou a usar esta versão'))
            except OSError:
                if mudou_versao:
                    out.append(('manutenção agendada', 'pendente', 'a manutenção em segundo plano ainda roda a versão anterior: abra o Katharos '
                                                                    'como administrador uma vez (ou rode "agendar") para ela passar a usar esta'))
    except Exception as ex:
        LOG.escreve(f'cópia da tarefa não atualizou: {ex!r}')
    try:
        if WINDOWS and cliques_ativos():
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, URI_CHAVE + r'\shell\open\command') as k:
                atual = str(winreg.QueryValueEx(k, '')[0])
            nova = linha_de_comando_clique()
            if atual != nova:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, URI_CHAVE + r'\shell\open\command') as k:
                    winreg.SetValueEx(k, '', 0, winreg.REG_SZ, nova)
                out.append(('botões do painel', 'ok', 'os botões Corrigir do painel passaram a abrir esta versão'))
    except Exception as ex:
        LOG.escreve(f'link do painel não atualizou: {ex!r}')
    return out


def traz_relatorios(e, limite=60):
    """Se o programa agora roda de outra pasta, copia os relatórios da pasta antiga para a nova (não apaga os antigos).
    Devolve quantos copiou."""
    eu = Path(__file__).resolve()
    antiga = e.get('pasta_katharos')
    if eu.parent.name.lower() != 'programa' or not antiga:
        return 0
    de, para = Path(antiga) / 'relatorios', eu.parent.parent / 'relatorios'
    try:
        if de.resolve() == para.resolve() or not de.is_dir():
            return 0
        arqs = sorted((a for a in de.glob('*.md') if a.name != 'ultimo.md' and a.stat().st_size < 4 * 1048576), key=lambda a: a.name)[-limite:]
        if not arqs:
            return 0
        para.mkdir(parents=True, exist_ok=True)
        n = 0
        for a in arqs:
            if not (para / a.name).exists():
                shutil.copy2(a, para / a.name)
                n += 1
        return n
    except OSError as ex:
        LOG.escreve(f'relatórios antigos não vieram: {ex!r}')
        return 0


def confere_versao(t=None, silencioso=False):
    """Roda a cada abertura. Na primeira vez de uma versão nova: guarda cópia, converte os dados, atualiza as cópias
    do programa e conta o que continua valendo. Devolve um resumo (dicionário) do que fez, ou None se não havia nada a fazer."""
    e = estado()
    de = versao_anterior(e)
    dados = e.get('versao_dados')
    dados = int(dados) if isinstance(dados, int) else (0 if e else VERSAO_DADOS)
    if de is not None and de != 'anterior' and _v(de) > _v(VERSAO) or dados > VERSAO_DADOS:
        # os dados são de uma versão mais nova que este programa (uma cópia antiga rodando): não converte, não carimba
        if t and not silencioso and e.get('aviso_versao_nova') != VERSAO:
            t.aviso(f'Os dados deste PC foram gravados pelo Katharos {de or "mais novo"}, e este é o {VERSAO}. Funciona, mas o que a versão '
                    'nova guardou a mais fica de fora. Use a pasta da versão mais nova.')
            marca_estado('aviso_versao_nova', VERSAO)
        return {'antiga': True, 'de': de}
    if de == VERSAO and dados == VERSAO_DADOS:
        try:   # mesma versão: só mantém em dia as cópias de fora, em silêncio (ex.: agora há administrador para a da tarefa)
            atualiza_copias(mudou_versao=False)
        except Exception as ex:
            LOG.escreve(f'cópias não conferidas: {ex!r}')
        return None
    resumo = {'de': de, 'para': VERSAO, 'passos': [], 'copia': None, 'copias': [], 'relatorios': 0, 'erro': ''}
    if de is not None:
        resumo['copia'] = guarda_copia_de_versao(de)
    for numero, descricao, f in MIGRACOES:
        if numero <= dados:
            continue
        try:
            f(e, CASA)
            resumo['passos'].append(descricao)
            dados = numero
        except Exception as ex:   # um passo que falha para a conversão ali: os dados ficam como estavam, com a cópia guardada
            LOG.escreve(f'migração {numero} falhou: {ex!r}')
            resumo['erro'] = f'{descricao}: {ex}'
            break
    if de is not None:
        resumo['relatorios'] = traz_relatorios(e)
    e['versao_dados'] = dados
    if not resumo['erro']:
        e['versao_programa'] = VERSAO
        hist = e.setdefault('versoes', [])
        if not hist and de not in (None, VERSAO):
            hist.append({'versao': de, 'desde': None})
        hist.append({'versao': VERSAO, 'desde': agora_iso(), 'de': de})
        del hist[:-30]
    salva_estado(e)
    if de is not None:
        try:
            resumo['copias'] = atualiza_copias()
        except Exception as ex:
            LOG.escreve(f'cópias não atualizadas: {ex!r}')
    LOG.escreve(f'versão: {de} -> {VERSAO}, dados {dados}, passos {resumo["passos"]}, erro {resumo["erro"]!r}')
    if t and not silencioso and de is not None and de != VERSAO:
        mostra_troca_de_versao(t, resumo, e)
    return resumo


def mostra_troca_de_versao(t, resumo, e):
    de = resumo['de']
    t.titulo(f'Katharos atualizado: {"versão anterior" if de == "anterior" else de} → {VERSAO}')
    ficou = o_que_ficou(e)
    if ficou:
        t.paragrafo('Tudo o que a versão anterior guardou neste PC continua valendo:', 2, 'sub')
        t.chaves(ficou)
    else:
        t.paragrafo('Suas preferências continuam valendo.', 2, 'sub')
    for _, estado_, frase in resumo['copias']:
        t.item('✓' if estado_ == 'ok' else '!', 'verde' if estado_ == 'ok' else 'amarelo', frase[0].upper() + frase[1:] + '.')
    if resumo['relatorios']:
        t.item('✓', 'verde', f'{pl(resumo["relatorios"], "relatório antigo veio", "relatórios antigos vieram")} para a pasta "relatorios" desta versão.')
    if resumo['erro']:
        t.aviso(f'Um passo da conversão dos dados falhou ({corta(resumo["erro"], 90)}). Nada foi perdido: os dados ficaram como estavam'
                + (f' e há uma cópia em {resumo["copia"]}.' if resumo['copia'] else '.'))
    elif resumo['copia']:
        t.nota(f'  Cópia do estado anterior guardada em {caminho_curto(str(resumo["copia"]))}.')
    t.escreve()


def ferramenta_versoes(ctx, args):
    t = ctx.t
    t.aba('as versões do Katharos que já rodaram neste PC e o que está guardado')
    e = estado()
    t.chaves([('esta versão', f'{VERSAO} ({DATA_VERSAO})'), ('formato dos dados', f'{e.get("versao_dados", VERSAO_DADOS)} (esta versão usa o {VERSAO_DADOS})'),
              ('onde ficam os dados', caminho_curto(str(CASA)))])
    hist = [h for h in (e.get('versoes') or []) if isinstance(h, dict)]
    if hist:
        t.titulo('histórico')
        t.tabela(['versão', 'desde', 'veio de'], [[str(h.get('versao')), (str(h.get('desde'))[:16].replace('T', ' ') if h.get('desde') else 'antes do registro'),
                                                   str(h.get('de') or '-')] for h in reversed(hist[-12:])], alinha='eee')
    ficou = o_que_ficou(e)
    if ficou:
        t.titulo('o que está guardado')
        t.chaves(ficou)
    try:
        copias = sorted(p.name for p in (CASA / 'versoes').iterdir() if p.is_dir())
    except OSError:
        copias = []
    if copias:
        t.titulo('cópias de segurança das trocas de versão')
        for c in copias[-COPIAS_DE_VERSAO:]:
            t.escreve('  ' + t.p(c, 'sub'))
        t.nota(f'  Ficam em {caminho_curto(str(CASA / "versoes"))}: são os arquivos de estado como estavam antes de cada troca.')
    t.paragrafo('Para atualizar: baixe a versão nova e abra o KATHAROS.bat dela. Pode ser em outra pasta; os dados, o desfazer, os gráficos '
                'e as provas ficam em ' + caminho_curto(str(CASA)) + ' e são reconhecidos sozinhos.', 2, 'apagado')
    return 0
