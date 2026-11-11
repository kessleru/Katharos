# ─────────────── memória do PC (I7): tudo o que o Katharos aprendeu deste PC, num banco SQLite em ~/.katharos/katharos.db ───────────────
# Quem escreve o quê (um escritor por tabela):
#   o segundo plano (Katharos.exe) só acrescenta linhas nos .jsonl de sempre (minutos, sessões, eventos): é a fila em disco;
#   o motor (este arquivo) importa essas linhas para o banco e é o único que grava nele.
# Por que um banco: os .jsonl giram (minutos ficam 14 dias); o banco guarda 120 dias de minutos e, depois disso, a média de cada hora,
# então tendência e linha de base enxergam meses, não só duas semanas. Ler uma janela é uma consulta, não varrer o arquivo todo.
# Nada aqui é obrigatório: sem sqlite3 (Python sem a biblioteca) ou com o banco ilegível, o motor segue lendo os .jsonl.
try:
    import sqlite3
except ImportError:      # Python montado sem sqlite: a memória longa fica desligada, o resto funciona
    sqlite3 = None

MEMORIA_ESQUEMA = 1
MEMORIA_MINUTOS_DIAS = 120          # minutos crus guardados; os mais velhos viram a média da hora
MEMORIA_EVENTOS_MAX = 5000          # eventos guardados (os mais antigos saem)
_MEMORIA_TABELAS = '''
CREATE TABLE IF NOT EXISTS meta (chave TEXT PRIMARY KEY, valor TEXT);
CREATE TABLE IF NOT EXISTS minutos (t TEXT PRIMARY KEY, jogo TEXT, dados TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS horas (h TEXT PRIMARY KEY, n INTEGER, dados TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessoes (inicio TEXT PRIMARY KEY, jogo TEXT, min REAL, dados TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS mudancas (quando TEXT, tipo TEXT, alvo TEXT, titulo TEXT, PRIMARY KEY (quando, tipo, alvo));
CREATE TABLE IF NOT EXISTS achados (id TEXT, dia TEXT, tipo TEXT, confianca TEXT, dados TEXT NOT NULL, PRIMARY KEY (id, dia));
CREATE TABLE IF NOT EXISTS resultados (id TEXT, quando TEXT, veredito TEXT, dados TEXT NOT NULL, PRIMARY KEY (id, quando));
CREATE TABLE IF NOT EXISTS pesos (alvo TEXT PRIMARY KEY, peso REAL NOT NULL, n INTEGER NOT NULL, atualizado TEXT);
CREATE TABLE IF NOT EXISTS eventos (seq INTEGER PRIMARY KEY AUTOINCREMENT, quando TEXT, tipo TEXT, dados TEXT, chave TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS importado (arquivo TEXT PRIMARY KEY, posicao INTEGER, tamanho INTEGER);
CREATE INDEX IF NOT EXISTS minutos_jogo ON minutos (jogo, t);
CREATE INDEX IF NOT EXISTS sessoes_jogo ON sessoes (jogo, inicio);
'''


def memoria_arq():
    return CASA / 'katharos.db'


def memoria_abre(arq=None):
    """Abre (e cria, se preciso) o banco. None se não dá: quem chama segue sem a memória longa."""
    if sqlite3 is None:
        return None
    try:
        CASA.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(str(arq or memoria_arq()), timeout=10)
        con.execute('PRAGMA journal_mode=WAL')
        con.execute('PRAGMA synchronous=NORMAL')
        con.executescript(_MEMORIA_TABELAS)
        v = con.execute("SELECT valor FROM meta WHERE chave='esquema'").fetchone()
        if v is None:
            con.execute("INSERT INTO meta VALUES ('esquema', ?)", (str(MEMORIA_ESQUEMA),))
            con.commit()
        elif int(v[0]) > MEMORIA_ESQUEMA:
            # gravado por uma versão mais nova: ler pode, mas não escrevemos num formato que não conhecemos
            con.close()
            LOG.escreve(f'memória com esquema {v[0]} (esta versão conhece até {MEMORIA_ESQUEMA}): ficou só leitura')
            return sqlite3.connect(f'file:{arq or memoria_arq()}?mode=ro', uri=True, timeout=10)
        return con
    except Exception as ex:   # banco travado, disco cheio, arquivo corrompido: o motor não para por isso
        LOG.escreve(f'memória: não abriu ({ex!r})')
        return None


def _mem_importa_jsonl(con, nome, tabela, campo):
    """Lê do ponto onde parou (o arquivo só cresce; se encolheu, girou: lê de novo do começo, a chave primária evita repetir)."""
    arq = CASA / nome
    try:
        tam = arq.stat().st_size
    except OSError:
        return 0
    lin = con.execute('SELECT posicao, tamanho FROM importado WHERE arquivo=?', (nome,)).fetchone()
    with open(arq, 'rb') as f:
        cabeca = f.readline()[:200]
    # o segundo plano gira o arquivo tirando linhas do começo e continua escrevendo no fim: o tamanho pode até crescer. O que
    # denuncia a rotação é a primeira linha ter mudado; aí lê de novo do começo (a chave primária evita repetir)
    marca = con.execute('SELECT valor FROM meta WHERE chave=?', ('inicio:' + nome,)).fetchone()
    girou = marca is None or marca[0] != cabeca.decode('utf-8', 'replace')
    pos = lin[0] if lin and lin[1] is not None and tam >= lin[0] and not girou else 0
    n = 0
    with open(arq, 'rb') as f:
        f.seek(pos)
        bloco = f.read()
    fim = bloco.rfind(b'\n') + 1      # só linhas completas: a última pode estar sendo escrita agora
    for bruta in bloco[:fim].splitlines():
        try:
            d = json.loads(bruta.decode('utf-8', 'replace'))
            chave = d[campo]
            datetime.fromisoformat(chave)
        except (ValueError, KeyError, TypeError):
            continue
        if tabela == 'minutos':
            r = con.execute('INSERT OR IGNORE INTO minutos VALUES (?,?,?)', (chave, d.get('jogo'), json.dumps(d, ensure_ascii=False)))
        elif tabela == 'sessoes':
            r = con.execute('INSERT OR IGNORE INTO sessoes VALUES (?,?,?,?)', (chave, d.get('jogo'), d.get('min'), json.dumps(d, ensure_ascii=False)))
        else:
            r = con.execute('INSERT OR IGNORE INTO eventos (quando, tipo, dados, chave) VALUES (?,?,?,?)',
                            (chave, str(d.get('tipo') or ''), json.dumps(d.get('dados') or {}, ensure_ascii=False), f'{chave}|{d.get("tipo")}|{json.dumps(d.get("dados"), sort_keys=True)}'))
        n += r.rowcount
    con.execute('INSERT OR REPLACE INTO importado VALUES (?,?,?)', (nome, pos + fim, tam))
    con.execute('INSERT OR REPLACE INTO meta VALUES (?,?)', ('inicio:' + nome, cabeca.decode('utf-8', 'replace')))
    return n


def _mem_mudancas(con):
    """Pacotes aplicados e desfeitos (do estado) viram linhas de mudança: é o que as marcas dos gráficos e o avaliador usam."""
    n = 0
    for nome, reg in (estado().get('pacotes') or {}).items():
        if not isinstance(reg, dict) or not reg.get('quando'):
            continue
        titulo = PACOTES[nome].titulo if nome in PACOTES else nome
        n += con.execute('INSERT OR IGNORE INTO mudancas VALUES (?,?,?,?)', (reg['quando'], 'aplicou', nome, titulo)).rowcount
        if reg.get('revertido') and reg.get('revertido_em'):   # versões antigas não anotavam quando desfez: sem data, fica só o aplicou
            n += con.execute('INSERT OR IGNORE INTO mudancas VALUES (?,?,?,?)', (reg['revertido_em'], 'desfez', nome, titulo)).rowcount
    return n


def _mem_compacta(con, agora):
    """Minutos com mais de 120 dias viram a média de cada hora (o que importa para tendência e linha de base longa)."""
    corte = (agora - timedelta(days=MEMORIA_MINUTOS_DIAS)).replace(minute=0, second=0, microsecond=0).isoformat(timespec='seconds')   # hora inteira
    velhos = con.execute('SELECT t, dados FROM minutos WHERE t < ? ORDER BY t', (corte,)).fetchall()
    if not velhos:
        return 0
    por_hora = {}
    for t, dados in velhos:
        try:
            por_hora.setdefault(t[:13], []).append(json.loads(dados))
        except ValueError:
            continue
    for h, ms in por_hora.items():
        med = {}
        for k in ('cpu', 'gpu', 'ram', 'disco', 'rede_mbs', 'temp_cpu', 'temp_gpu', 'processos', 'ram_sistema_gb', 'ram_conta_gb', 'katharos_cpu'):
            v = [m[k] for m in ms if isinstance(m.get(k), (int, float)) and not m.get('sujo')]
            if v:
                med[k] = round(sum(v) / len(v), 2)
        med['jogo_min'] = sum(1 for m in ms if m.get('jogo'))
        con.execute('INSERT OR REPLACE INTO horas VALUES (?,?,?)', (h, len(ms), json.dumps(med)))
    con.execute('DELETE FROM minutos WHERE t < ?', (corte,))
    return len(velhos)


def memoria_atualiza(agora=None, con=None):
    """Traz para o banco o que os arquivos têm de novo. Rápido quando não há nada novo (lê só o pedaço depois da última posição).
    Devolve {'minutos': n, 'sessoes': n, 'eventos': n, 'mudancas': n} ou None sem banco."""
    proprio = con is None
    con = con or memoria_abre()
    if con is None:
        return None
    agora = agora or datetime.now()
    try:
        r = {'minutos': _mem_importa_jsonl(con, 'minutos.jsonl', 'minutos', 't'),
             'sessoes': _mem_importa_jsonl(con, 'sessoes.jsonl', 'sessoes', 'inicio'),
             'eventos': _mem_importa_jsonl(con, 'eventos.jsonl', 'eventos', 't'),
             'mudancas': _mem_mudancas(con)}
        ultima = con.execute("SELECT valor FROM meta WHERE chave='compactou'").fetchone()
        if not ultima or ultima[0][:10] != agora.date().isoformat():
            r['compactados'] = _mem_compacta(con, agora)
            con.execute("DELETE FROM eventos WHERE seq <= (SELECT MAX(seq) FROM eventos) - ?", (MEMORIA_EVENTOS_MAX,))
            con.execute("INSERT OR REPLACE INTO meta VALUES ('compactou', ?)", (agora.isoformat(timespec='seconds'),))
        con.commit()
        return r
    except Exception as ex:
        LOG.escreve(f'memória: importação falhou ({ex!r})')
        try:
            con.rollback()
        except Exception:
            pass
        return None
    finally:
        if proprio:
            con.close()


def _mem_linhas(sql, args=()):
    con = memoria_abre()
    if con is None:
        return None
    try:
        return con.execute(sql, args).fetchall()
    except Exception as ex:
        LOG.escreve(f'memória: leitura falhou ({ex!r})')
        return None
    finally:
        con.close()


def memoria_minutos(desde, ate=None):
    """Minutos do banco entre duas datas (com '_dt'), ou None sem banco."""
    ls = _mem_linhas('SELECT dados FROM minutos WHERE t >= ? AND t <= ? ORDER BY t',
                     (desde.isoformat(timespec='seconds'), (ate or datetime.now()).isoformat(timespec='seconds')))
    if ls is None:
        return None
    out = []
    for (dados,) in ls:
        try:
            d = json.loads(dados)
            d['_dt'] = datetime.fromisoformat(d['t'])
            out.append(d)
        except (ValueError, KeyError, TypeError):
            continue
    return out


def memoria_sessoes(desde):
    ls = _mem_linhas('SELECT dados FROM sessoes WHERE inicio >= ? ORDER BY inicio', (desde.isoformat(timespec='seconds'),))
    if ls is None:
        return None
    out = []
    for (dados,) in ls:
        try:
            d = json.loads(dados)
            d['_dt'] = datetime.fromisoformat(d['inicio'])
            out.append(d)
        except (ValueError, KeyError, TypeError):
            continue
    return out


def memoria_eventos(depois_de=0, limite=200):
    """Eventos da fila (o que o segundo plano e o motor publicaram), depois do número `depois_de`."""
    ls = _mem_linhas('SELECT seq, quando, tipo, dados FROM eventos WHERE seq > ? ORDER BY seq LIMIT ?', (int(depois_de), int(limite)))
    out = []
    for seq, quando, tipo, dados in ls or []:
        try:
            out.append({'seq': seq, 'quando': quando, 'tipo': tipo, 'dados': json.loads(dados or '{}')})
        except ValueError:
            continue
    return out


def publica_evento(tipo, dados=None, quando=None):
    """O motor também publica na fila (aplicou, desfez, conclusão nova). Mesmo formato do segundo plano."""
    try:
        linha = json.dumps({'t': (quando or datetime.now()).isoformat(timespec='seconds'), 'tipo': tipo, 'dados': dados or {}}, ensure_ascii=False)
        with open(CASA / 'eventos.jsonl', 'a', encoding='utf-8') as f:
            f.write(linha + '\n')
    except OSError as ex:
        LOG.escreve(f'evento {tipo} não gravado: {ex!r}')


def memoria_grava_achados(achados, agora=None):
    """Um achado por id por dia: dá para ver há quantos dias ele aparece (repetição pesa na confiança)."""
    con = memoria_abre()
    if con is None:
        return
    dia = (agora or datetime.now()).date().isoformat()
    try:
        for a in achados:
            con.execute('INSERT OR REPLACE INTO achados VALUES (?,?,?,?,?)', (a['id'], dia, a.get('tipo', ''), a.get('confianca') or '', json.dumps(a, ensure_ascii=False, default=str)))
        con.commit()
    except Exception as ex:
        LOG.escreve(f'memória: achados não gravados ({ex!r})')
    finally:
        con.close()


def memoria_dias_do_achado(id_, dias=30, agora=None):
    """Em quantos dias diferentes este achado apareceu nos últimos `dias`."""
    desde = ((agora or datetime.now()) - timedelta(days=dias)).date().isoformat()
    ls = _mem_linhas('SELECT COUNT(*) FROM achados WHERE id=? AND dia>=?', (id_, desde))
    return ls[0][0] if ls else 0


def memoria_grava_resultado(id_, quando, veredito, dados):
    con = memoria_abre()
    if con is None:
        return False
    try:
        novo = con.execute('INSERT OR IGNORE INTO resultados VALUES (?,?,?,?)', (id_, quando, veredito, json.dumps(dados, ensure_ascii=False, default=str))).rowcount
        con.commit()
        return bool(novo)
    finally:
        con.close()


def memoria_pesos():
    """{alvo: peso} aprendido neste PC (1 = sem informação)."""
    return {a: p for a, p, _ in (_mem_linhas('SELECT alvo, peso, n FROM pesos') or [])}


def memoria_ajusta_peso(alvo, fator, agora=None):
    """Peso entre 0,3 e 2: cada resultado medido mexe pouco; muitos resultados na mesma direção mexem muito."""
    con = memoria_abre()
    if con is None:
        return None
    try:
        lin = con.execute('SELECT peso, n FROM pesos WHERE alvo=?', (alvo,)).fetchone()
        peso, n = (lin or (1.0, 0))
        peso = max(0.3, min(2.0, peso * fator))
        con.execute('INSERT OR REPLACE INTO pesos VALUES (?,?,?,?)', (alvo, round(peso, 3), n + 1, (agora or datetime.now()).isoformat(timespec='seconds')))
        con.commit()
        return peso
    finally:
        con.close()


def memoria_resumo():
    """O que a memória guarda, para a tela de configurações e o `exportar`."""
    ls = {}
    for t in ('minutos', 'horas', 'sessoes', 'mudancas', 'achados', 'resultados', 'pesos', 'eventos'):
        r = _mem_linhas(f'SELECT COUNT(*) FROM {t}')
        if r is None:
            return None
        ls[t] = r[0][0]
    p = (_mem_linhas('SELECT MIN(t) FROM minutos') or [[None]])[0][0]
    h = (_mem_linhas('SELECT MIN(h) FROM horas') or [[None]])[0][0]
    candidatos = [x for x in (p, h + ':00:00' if h else None) if x]
    desde = min(candidatos) if candidatos else None
    try:
        tam = memoria_arq().stat().st_size
    except OSError:
        tam = 0
    return {'contagens': ls, 'desde': desde, 'bytes': tam}


def memoria_exporta(arq):
    """Tudo o que a memória sabe, em JSON (para guardar antes de apagar, ou levar para outro PC)."""
    con = memoria_abre()
    if con is None:
        return None
    try:
        out = {'katharos': VERSAO, 'esquema': MEMORIA_ESQUEMA, 'exportado': agora_iso()}
        for t in ('minutos', 'horas', 'sessoes', 'mudancas', 'achados', 'resultados', 'pesos', 'eventos'):
            cur = con.execute(f'SELECT * FROM {t}')
            cols = [c[0] for c in cur.description]
            out[t] = [dict(zip(cols, r)) for r in cur.fetchall()]
        e = estado()
        out['estado'] = {k: e.get(k) for k in ('conselheiro_respostas', 'conselheiro_feitos', 'conselheiro_dispensadas', 'conselheiro_vistas')}
        tmp = Path(str(arq) + '.tmp')
        tmp.write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8')
        os.replace(tmp, arq)
        return Path(arq)
    finally:
        con.close()


def memoria_apaga():
    """Apaga o que o motor aprendeu deste PC, guardando antes uma exportação. Não toca em backups do desfazer, provas nem configurações.
    Devolve o caminho da exportação (ou None se não havia o que exportar)."""
    exp = None
    if memoria_arq().exists():
        exp = memoria_exporta(CASA / f'memoria-exportada-{datetime.now():%Y-%m-%d-%H%M%S}.json')
        if not exp:   # sem a cópia guardada, não apaga nada
            raise OSError('a memória está em uso agora e não deu para guardar a cópia antes; tente de novo em instantes')
        try:
            memoria_arq().unlink()   # o banco primeiro: se ele está aberto, nada mais é apagado
        except OSError as ex:
            raise OSError('a memória está em uso agora (o motor está pensando); tente de novo em instantes') from ex
    for nome in ('katharos.db-wal', 'katharos.db-shm', 'linha-de-base.json', 'propostas.json'):
        try:
            (CASA / nome).unlink()
        except OSError:
            pass
    for nome in ('minutos.jsonl', 'sessoes.jsonl', 'eventos.jsonl'):   # o segundo plano reabre e continua do zero
        try:
            with open(CASA / nome, 'w', encoding='utf-8'):
                pass
        except OSError:
            pass
    e = estado()
    for k in ('conselheiro_respostas', 'conselheiro_feitos', 'conselheiro_dispensadas', 'conselheiro_vistas', 'conselheiro_avisadas'):
        e.pop(k, None)
    salva_estado(e)
    return exp
