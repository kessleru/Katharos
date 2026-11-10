

# ─────────────── robustez: lixo, trava de instância e espaço em disco ───────────────

DIAS_LOG = 90
MAX_CORROMPIDOS = 5


def limpa_residuos(casa=None, agora=None):
    """Tira o que sobra sozinho: .tmp de gravações interrompidas, logs com mais de 90 dias e cópias de JSON
    corrompidos além das 5 mais recentes. Nunca mexe em backup/ (o desfazer depende dele) nem em relatórios."""
    casa = Path(casa or CASA)
    agora = agora or time.time()
    n = 0
    try:
        for tmp in list(casa.rglob('*.tmp')):
            if 'backup' in tmp.parts:
                continue
            if agora - tmp.stat().st_mtime > 3600:
                tmp.unlink()
                n += 1
        logs = casa / 'logs'
        if logs.is_dir():
            for lg in logs.glob('*.log'):
                if agora - lg.stat().st_mtime > DIAS_LOG * 86400:
                    lg.unlink()
                    n += 1
        ruins = sorted(casa.glob('*.corrompido-*'), key=lambda a: a.stat().st_mtime)   # pela data: pelo nome, os de config.json iam primeiro
        for velho in ruins[:-MAX_CORROMPIDOS]:
            velho.unlink()
            n += 1
    except OSError:
        pass
    return n


def _vivo(pid):
    """O processo com este PID ainda existe?"""
    if pid <= 0:
        return False
    if WINDOWS:
        try:
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                return False
            ctypes.windll.kernel32.CloseHandle(h)
            return True
        except Exception:
            return True
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except OSError:
        return True


def _eh_python(pid):
    """O processo com este PID é um Python (o Katharos)? Depois de um travamento, o Windows pode dar o PID da trava a outro programa."""
    if not WINDOWS:
        return True
    try:
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return True
        try:
            buf = ctypes.create_unicode_buffer(1024)
            n = ctypes.c_uint32(1024)
            if not k.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
                return True
            return 'python' in Path(buf.value).name.lower()
        finally:
            k.CloseHandle(h)
    except Exception:
        return True


class Trava:
    """Uma única instância do Katharos mexendo no sistema por vez (duas janelas aplicando juntas escreveriam no mesmo
    backup e no mesmo estado). Arquivo ~/.katharos/katharos.lock com o PID; trava de processo que já morreu é ignorada."""

    def __init__(self, casa=None):
        self.arq = Path(casa or CASA) / 'katharos.lock'
        self.minha = False
        self.dona = None

    def pega(self):
        """Cria a trava de uma vez só (O_EXCL): duas janelas abertas juntas não passam as duas. Uma trava de processo que já morreu,
        ou cujo PID o Windows deu a outro programa, é apagada e criada de novo."""
        try:
            self.arq.parent.mkdir(parents=True, exist_ok=True)
            for _ in range(3):
                try:
                    fd = os.open(str(self.arq), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                except FileExistsError:
                    try:
                        pid = int((self.arq.read_text(encoding='utf-8').split() or ['0'])[0])
                    except (OSError, ValueError):
                        pid = 0
                    if pid == os.getpid():
                        self.minha = True
                        return True
                    if pid and _vivo(pid) and _eh_python(pid):
                        self.dona = pid
                        return False
                    try:
                        self.arq.unlink()   # trava velha
                    except FileNotFoundError:
                        pass
                    continue
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    f.write(f'{os.getpid()} {datetime.now().isoformat(timespec="seconds")}\n')
                self.minha = True
                return True
            return False
        except OSError:
            self.minha = False     # sem como gravar a trava: não impede o uso
        return True

    def solta(self):
        if self.minha:
            try:
                self.arq.unlink()
            except OSError:
                pass
            self.minha = False


ESPACO_MIN_GB = {'dism': 3.0, 'sfc': 1.0, 'ponto': 2.0, 'bench': 1.0}


def espaco_ok(para, livre=None):
    """(ok, livre_gb, precisa_gb): antes de DISM, SFC, ponto de restauração e benchmark confere o espaço livre em C:.
    Sem conseguir ler o espaço, deixa seguir (não bloqueia por falta de informação)."""
    livre = livre_c() if livre is None else livre
    precisa = ESPACO_MIN_GB.get(para, 1.0)
    if not livre:
        return True, 0.0, precisa
    gb = livre / 2**30
    return gb >= precisa, gb, precisa


def exige_espaco(t, para, rotulo):
    ok, gb, precisa = espaco_ok(para)
    if not ok:
        t.aviso(f'{rotulo}: só há {gb:.1f} GB livres em C: e isto pede pelo menos {precisa:g} GB. Libere espaço (comando limpar) e tente de novo.')
    return ok
