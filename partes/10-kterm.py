import atexit
import os
import re
import shutil
import sys
import textwrap
import threading
import time
import unicodedata
from pathlib import Path



# ═══════════════════════════════ paleta: Katharos (padrão) e Kessleru (Catppuccin) ═══════════════════════════════
# Valores de 07 • Design System/Kessleru/codigo/tokens.json. Cada papel aponta para um token.

_CTP = {
    # Katharos: a mesma paleta da landing (fundo quase preto, texto cor de osso, um âmbar só). É o tema padrão.
    'katharos': {
        'text': '#cdc8be', 'subtext1': '#b5b0a6', 'subtext0': '#a9a49b', 'overlay2': '#8e8a82',
        'overlay1': '#86837c', 'overlay0': '#5f5d58', 'surface2': '#38383e', 'surface1': '#2a2a2f',
        'surface0': '#18181b', 'base': '#0c0c0d', 'mantle': '#09090a', 'crust': '#060607',
        'rosewater': '#efe9de', 'flamingo': '#e8c9b4', 'pink': '#d9a3b0', 'mauve': '#b9a3c9', 'red': '#e5737a',
        'maroon': '#d9646c', 'peach': '#e2a85c', 'yellow': '#ecb876', 'green': '#9ccf8c', 'teal': '#8fc4b4',
        'sky': '#9cc4cf', 'sapphire': '#8fb3c4', 'blue': '#9db0c8', 'lavender': '#b3b6d6'},
    # o mesmo clima para terminal de fundo claro: papel envelhecido, tinta escura, âmbar queimado
    'pergaminho': {
        'text': '#2a2622', 'subtext1': '#3d3832', 'subtext0': '#4a443d', 'overlay2': '#5e574e',
        'overlay1': '#6f675c', 'overlay0': '#8a8173', 'surface2': '#b9ae9c', 'surface1': '#d6ccbb',
        'surface0': '#e6ddcd', 'base': '#f4efe6', 'mantle': '#faf7f1', 'crust': '#e9e2d4',
        'rosewater': '#7a4a2a', 'flamingo': '#8a4b3a', 'pink': '#9a3f5f', 'mauve': '#6d4a8a', 'red': '#b0303a',
        'maroon': '#9a2f38', 'peach': '#9a5a12', 'yellow': '#86620e', 'green': '#3f7a2c', 'teal': '#1f7268',
        'sky': '#1f6a85', 'sapphire': '#255f7a', 'blue': '#2f5694', 'lavender': '#4f5aa0'},
    'mocha': {
        'text': '#cdd6f4', 'subtext1': '#bac2de', 'subtext0': '#a6adc8', 'overlay2': '#9399b2',
        'overlay1': '#7f849c', 'overlay0': '#6c7086', 'surface2': '#585b70', 'surface1': '#45475a',
        'surface0': '#313244', 'base': '#1e1e2e', 'mantle': '#1c1c2b', 'crust': '#181825',
        'rosewater': '#f5e0dc', 'flamingo': '#f2cdcd', 'pink': '#f5c2e7', 'mauve': '#cba6f7', 'red': '#f38ba8',
        'maroon': '#eba0ac', 'peach': '#fab387', 'yellow': '#f9e2af', 'green': '#a6e3a1', 'teal': '#94e2d5',
        'sky': '#89dceb', 'sapphire': '#74c7ec', 'blue': '#89b4fa', 'lavender': '#b4befe'},
    'macchiato': {
        'text': '#cad3f5', 'subtext1': '#b8c0e0', 'subtext0': '#a5adcb', 'overlay2': '#939ab7',
        'overlay1': '#8087a2', 'overlay0': '#6e738d', 'surface2': '#5b6078', 'surface1': '#494d64',
        'surface0': '#363a4f', 'base': '#24273a', 'mantle': '#1e2030', 'crust': '#181926',
        'rosewater': '#f4dbd6', 'flamingo': '#f0c6c6', 'pink': '#f5bde6', 'mauve': '#c6a0f6', 'red': '#ed8796',
        'maroon': '#ee99a0', 'peach': '#f5a97f', 'yellow': '#eed49f', 'green': '#a6da95', 'teal': '#8bd5ca',
        'sky': '#91d7e3', 'sapphire': '#7dc4e4', 'blue': '#8aadf4', 'lavender': '#b7bdf8'},
    'frappe': {
        'text': '#c6d0f5', 'subtext1': '#b5bfe2', 'subtext0': '#a5adce', 'overlay2': '#949cbb',
        'overlay1': '#838ba7', 'overlay0': '#737994', 'surface2': '#626880', 'surface1': '#51576d',
        'surface0': '#414559', 'base': '#303446', 'mantle': '#292c3c', 'crust': '#232634',
        'rosewater': '#f2d5cf', 'flamingo': '#eebebe', 'pink': '#f4b8e4', 'mauve': '#ca9ee6', 'red': '#e78284',
        'maroon': '#ea999c', 'peach': '#ef9f76', 'yellow': '#e5c890', 'green': '#a6d189', 'teal': '#81c8be',
        'sky': '#99d1db', 'sapphire': '#85c1dc', 'blue': '#8caaee', 'lavender': '#babbf1'},
    'latte': {
        'text': '#4c4f69', 'subtext1': '#5c5f77', 'subtext0': '#5f627a', 'overlay2': '#7c7f93',
        'overlay1': '#8c8fa1', 'overlay0': '#9ca0b0', 'surface2': '#c6c1b5', 'surface1': '#d8d4ca',
        'surface0': '#e7e4dc', 'base': '#f5f3ee', 'mantle': '#fdfcf9', 'crust': '#e9e6de',
        'rosewater': '#dc8a78', 'flamingo': '#dd7878', 'pink': '#ea76cb', 'mauve': '#8839ef', 'red': '#d20f39',
        'maroon': '#e64553', 'peach': '#fe640b', 'yellow': '#df8e1d', 'green': '#40a02b', 'teal': '#179299',
        'sky': '#04a5e5', 'sapphire': '#209fb5', 'blue': '#1e66f5', 'lavender': '#7287fd'},
}
TEMAS = tuple(_CTP)
DESTAQUES = ('rosewater', 'flamingo', 'pink', 'mauve', 'red', 'maroon', 'peach', 'yellow', 'green', 'teal', 'sky',
             'sapphire', 'blue', 'lavender')

# papel -> token. "apagado" usa ctp-meta (overlay-2; no Latte, #5f627a): o original usava overlay-1, que o
# design system proíbe em texto por falta de contraste.
_PAPEIS = {
    'texto': 'text', 'sub': 'subtext0', 'apagado': 'overlay2', 'borda': 'overlay0', 'trilho': 'surface1',
    'verde': 'green', 'vermelho': 'red', 'amarelo': 'yellow', 'pessego': 'peach', 'azul': 'blue',
    'roxo': 'mauve', 'teal': 'teal', 'rosa': 'pink', 'escuro': 'crust',
}
_LATTE_AJUSTES = {'apagado': '#5f627a', 'escuro': '#fdfcf9'}  # ctp-meta do Latte; texto do selo claro
# nomes antigos do ferramentas.py continuam valendo
_APELIDOS = {'superficie': 'borda', 'fundo': 'trilho'}

# 16 cores: o texto usa a cor padrão do terminal (39), que funciona em fundo claro e escuro
_CORES16 = {'texto': 39, 'sub': 39, 'apagado': 90, 'borda': 90, 'trilho': 90, 'verde': 32, 'vermelho': 31,
            'amarelo': 33, 'pessego': 33, 'azul': 34, 'roxo': 35, 'teal': 36, 'rosa': 35, 'escuro': 30}
_DESTAQUE16 = {'rosewater': 35, 'flamingo': 35, 'pink': 35, 'mauve': 35, 'red': 31, 'maroon': 31, 'peach': 33,
               'yellow': 33, 'green': 32, 'teal': 36, 'sky': 36, 'sapphire': 36, 'blue': 34, 'lavender': 34}
_CLARAS16 = {'verde': 92, 'vermelho': 91, 'amarelo': 93, 'azul': 94, 'roxo': 95, 'teal': 96, 'rosa': 95}


def _hex(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def paleta(tema='katharos', destaque='peach'):
    """Cores RGB de cada papel no tema, com a cor de destaque escolhida."""
    c = _CTP[tema]
    p = {papel: _hex(c[tok]) for papel, tok in _PAPEIS.items()}
    if tema == 'latte':
        p.update({k: _hex(v) for k, v in _LATTE_AJUSTES.items()})
    p['destaque'] = _hex(c[destaque])
    return p


# ═══════════════════════════════ marca ═══════════════════════════════

LOGO_SIMBOLO = [' ▄▀   █ ▀▄ ', '▀▄  ▄▀   ▄▀', '  ▀ ▀   ▀  ']
LOGO_NOME = ['█ █ █▀▀ █▀▀ █▀▀ █   █▀▀ █▀▄ █ █',
             '█▀▄ █▀  ▀▀█ ▀▀█ █   █▀  █▀▄ █ █',
             '▀ ▀ ▀▀▀ ▀▀▀ ▀▀▀ ▀▀▀ ▀▀▀ ▀ ▀ ▀▀▀']

# Fonte de 3x5 pixels; cada par de linhas de pixels vira uma linha de meio-bloco (▀ ▄ █).
# É a mesma fonte do logo KESSLERU: texto_em_blocos('KESSLERU') == LOGO_NOME.
_FONTE = {
    'A': '### #.# ### #.# #.#', 'B': '##. #.# ##. #.# ##.', 'C': '### #.. #.. #.. ###', 'D': '##. #.# #.# #.# ##.',
    'E': '### #.. ##. #.. ###', 'F': '### #.. ##. #.. #..', 'G': '### #.. #.# #.# ###', 'H': '#.# #.# ### #.# #.#',
    'I': '### .#. .#. .#. ###', 'J': '..# ..# ..# #.# ###', 'K': '#.# #.# ##. #.# #.#', 'L': '#.. #.. #.. #.. ###',
    'M': '#.# ### ### #.# #.#', 'N': '##. #.# #.# #.# #.#', 'O': '### #.# #.# #.# ###', 'P': '### #.# ### #.. #..',
    'Q': '### #.# #.# ### ..#', 'R': '##. #.# ##. #.# #.#', 'S': '### #.. ### ..# ###', 'T': '### .#. .#. .#. .#.',
    'U': '#.# #.# #.# #.# ###', 'V': '#.# #.# #.# #.# .#.', 'W': '#.# #.# ### ### #.#', 'X': '#.# #.# .#. #.# #.#',
    'Y': '#.# #.# .#. .#. .#.', 'Z': '### ..# .#. #.. ###',
    '0': '### #.# #.# #.# ###', '1': '.#. ##. .#. .#. ###', '2': '### ..# ### #.. ###', '3': '### ..# ### ..# ###',
    '4': '#.# #.# ### ..# ..#', '5': '### #.. ### ..# ###', '6': '### #.. ### #.# ###', '7': '### ..# ..# ..# ..#',
    '8': '### #.# ### #.# ###', '9': '### #.# ### ..# ###',
    ' ': '... ... ... ... ...', '-': '... ... ### ... ...', '.': '... ... ... ... .#.', '_': '... ... ... ... ###',
    '/': '..# ..# .#. #.. #..', '<': '..# .#. #.. .#. ..#', '>': '#.. .#. ..# .#. #..', '+': '... .#. ### .#. ...',
    '!': '.#. .#. .#. ... .#.', '?': '### ..# .## ... .#.', ':': '... .#. ... .#. ...', '&': '##. #.. ### #.# ###',
}
_MEIO = {(False, False): ' ', (True, False): '▀', (False, True): '▄', (True, True): '█'}


def texto_em_blocos(txt):
    """Texto em letras de blocos, 3 linhas de altura. Acentos caem para a letra sem acento."""
    txt = unicodedata.normalize('NFKD', str(txt).upper()).encode('ascii', 'ignore').decode()
    letras = [_FONTE.get(ch, _FONTE['?']).split() for ch in txt]
    linhas = []
    for par in ((0, 1), (2, 3), (4, None)):
        partes = []
        for pix in letras:
            cima = pix[par[0]]
            baixo = pix[par[1]] if par[1] is not None else '...'
            partes.append(''.join(_MEIO[(cima[i] == '#', baixo[i] == '#')] for i in range(3)))
        linhas.append(' '.join(partes))
    return linhas


# ═══════════════════════════════ texto: largura visível ═══════════════════════════════

# cor (SGR) e link clicável (OSC 8) não ocupam espaço na tela
ANSI = re.compile(r'\033\[[0-9;?]*[A-Za-z]|\033\]8;;[^\033\007]*(?:\033\\|\007)|\033\][0-9]+;[^\007\033]*(?:\007|\033\\)')


def _larg_char(ch):
    o = ord(ch)
    if o < 0x300:
        return 1
    if unicodedata.combining(ch) or o in (0x200B, 0x200C, 0x200D, 0xFE0E, 0xFE0F):
        return 0
    if unicodedata.east_asian_width(ch) in ('W', 'F') or 0x1F300 <= o <= 0x1FAFF:
        return 2
    return 1


def _larg(s):
    return sum(_larg_char(c) for c in s)


def vlen(s):
    """Quantas colunas o texto ocupa na tela (sem códigos de cor; emoji e CJK contam 2)."""
    return _larg(ANSI.sub('', str(s)))


def _ate(s, n):
    # maior prefixo de s que cabe em n colunas
    tot, i = 0, 0
    for i, ch in enumerate(s):
        w = _larg_char(ch)
        if tot + w > n:
            return s[:i]
        tot += w
    return s


def corta(s, n):
    s = str(s)
    if _larg(s) <= n:
        return s
    return _ate(s, n - 1) + '…' if n > 1 else _ate(s, max(n, 0))


def corta_esq(s, n):
    s = str(s)
    if _larg(s) <= n:
        return s
    if n < 2:
        return '…'[:max(n, 0)]
    fim = _ate(s[::-1], n - 1)[::-1]
    return '…' + fim


def corta_visivel(s, n):
    """Corta um texto com cores em n colunas visíveis, sem quebrar as sequências de cor."""
    if vlen(s) <= n:
        return s
    saida, vistos, pos = [], 0, 0
    for m in ANSI.finditer(s):
        trecho = s[pos:m.start()]
        if vistos + _larg(trecho) >= n:
            saida.append(_ate(trecho, max(0, n - vistos)))
            vistos = n
            break
        saida.append(trecho + m.group())
        vistos += _larg(trecho)
        pos = m.end()
    else:
        saida.append(_ate(s[pos:], max(0, n - vistos)))
    return ''.join(saida) + ('\033[0m' if '\033[' in s else '')


def caminho_curto(p, n=None):
    s, casa = str(p), str(Path.home())
    if s.startswith(casa):
        s = '~' + s[len(casa):]
    s = s.replace('\\', '/')
    return corta_esq(s, n) if n else s


def humano(n):
    for u in ('B', 'KB', 'MB', 'GB', 'TB'):
        if n < 1024 or u == 'TB':
            return f'{n:.0f} {u}' if u in ('B', 'KB') else f'{n:.1f} {u}'.replace('.', ',')
        n /= 1024


def duracao(s):
    if s < 1:
        return f'{s * 1000:.0f} ms'
    if s < 90:
        return f'{s:.0f} s' if s >= 10 else f'{s:.1f} s'.replace('.', ',')
    return f'{s // 60:.0f} min {s % 60:02.0f} s'


# ═══════════════════════════════ símbolos por nível ═══════════════════════════════
# pleno: fonte moderna. simples: console antigo do Windows e TTY do Linux (só o que a fonte do
# console tem). ascii: qualquer coisa, até log e e-mail.

TROCA_SIMPLES = str.maketrans({'✓': '√', '✗': 'x', '↳': '>', '↻': '*', '↑': '^', '→': '->', '●': '•', '◆': '♦',
                               '◇': '♦', '›': '>', '╮': '┐', '╯': '┘', '○': 'o', '…': '~', '↓': 'v', '◉': '•'})
TROCA_ASCII = str.maketrans({'✓': '+', '✗': 'x', '·': '.', '…': '~', '─': '-', '●': '*', '◆': '>', '■': '#',
                             '█': '#', '▀': '"', '▄': '_', '↳': '>', '↑': '^', '↻': '*', '→': '->', '—': '-',
                             '•': '*', '♦': '>', '↓': 'v', '₂': '2', '≈': '~', '×': 'x', '◉': '*', '√': '+',
                             '◇': '*', '│': '|', '┌': '+', '└': '+', '›': '>', '╮': '+', '╯': '+', '├': '+',
                             '○': 'o', '┐': '+', '┘': '+', '┬': '+', '┴': '+', '┼': '+', '╭': '+', '╰': '+',
                             '“': '"', '”': '"', '‘': "'", '’': "'", '–': '-'})


def _xterm256(r, g, b):
    niveis = [0, 95, 135, 175, 215, 255]

    def perto(c):
        return min(range(6), key=lambda i: abs(niveis[i] - c))

    ri, gi, bi = perto(r), perto(g), perto(b)
    d_cubo = (niveis[ri] - r) ** 2 + (niveis[gi] - g) ** 2 + (niveis[bi] - b) ** 2
    ci = max(0, min(23, int(round(((r + g + b) / 3 - 8) / 10))))
    d_cinza = sum((8 + ci * 10 - c) ** 2 for c in (r, g, b))
    return 232 + ci if d_cinza < d_cubo else 16 + 36 * ri + 6 * gi + bi


# ═══════════════════════════════ detecção do terminal ═══════════════════════════════

def _liga_vt_windows():
    """Liga as sequências ANSI no console do Windows 10+. None = não é console (pipe, mintty)."""
    try:
        import ctypes
        from ctypes import wintypes
        k = ctypes.windll.kernel32
        h = k.GetStdHandle(-11)
        modo = wintypes.DWORD()
        if not k.GetConsoleMode(h, ctypes.byref(modo)):
            return None
        if modo.value & 0x0004:
            return True
        return bool(k.SetConsoleMode(h, modo.value | 0x0004))
    except Exception:
        return None


def _aceita_links(env):
    # mesma régua do pacote supports-hyperlinks (usado pelo npm e pelo Vite)
    if env.get('FORCE_HYPERLINK'):
        return env['FORCE_HYPERLINK'] != '0'
    if 'WT_SESSION' in env:
        return True
    if os.name == 'nt' or env.get('CI'):
        return False
    prog, ver = env.get('TERM_PROGRAM', ''), env.get('TERM_PROGRAM_VERSION', '')
    num = tuple(int(x) for x in re.findall(r'\d+', ver)[:2]) or (0,)
    if prog == 'iTerm.app':
        return num >= (3, 1)
    if prog == 'vscode':
        return num >= (1, 72) or bool(env.get('CURSOR_TRACE_ID'))
    if prog in ('WezTerm', 'ghostty', 'zed', 'WarpTerminal'):
        return True
    vte = env.get('VTE_VERSION', '')
    if vte.isdigit():
        return vte != '5000' and int(vte) >= 5000
    return env.get('TERM') in ('alacritty', 'xterm-kitty', 'xterm-ghostty', 'foot')


def _fundo_claro(env, consulta):
    """True/False se der para saber a cor de fundo; None se não der."""
    fb = env.get('COLORFGBG', '')
    if fb:
        try:
            bg = int(fb.split(';')[-1])
            return bg == 7 or 9 <= bg <= 15
        except ValueError:
            pass
    if consulta:
        return _consulta_fundo()
    return None


def _consulta_fundo(espera=0.12):
    # Pergunta a cor de fundo ao terminal (OSC 11). Só em Unix com TTY; quem não responde é ignorado.
    if os.name == 'nt':
        return None
    try:
        import select
        import termios
        import tty
    except ImportError:
        return None
    try:
        fd = sys.stdin.fileno()
        antigo = termios.tcgetattr(fd)
    except (OSError, ValueError, termios.error):
        return None
    resposta = ''
    try:
        tty.setcbreak(fd)
        sys.stdout.write('\033]11;?\033\\')
        sys.stdout.flush()
        fim = time.time() + espera
        while time.time() < fim:
            pronto, _, _ = select.select([fd], [], [], max(0, fim - time.time()))
            if not pronto:
                break
            resposta += os.read(fd, 64).decode('latin-1', 'ignore')
            if resposta.endswith(('\007', '\033\\')):
                break
    except OSError:
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, antigo)
    m = re.search(r'rgb:([0-9a-fA-F]+)/([0-9a-fA-F]+)/([0-9a-fA-F]+)', resposta)
    if not m:
        return None
    r, g, b = (int(x[:2], 16) for x in m.groups())
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) > 140


_CURSOR_ESCONDIDO = []


def _restaura_cursor():
    if _CURSOR_ESCONDIDO:
        try:
            sys.stdout.write('\033[?25h\033[0m')
            sys.stdout.flush()
        except (OSError, ValueError):
            pass


atexit.register(_restaura_cursor)


# ═══════════════════════════════ Terminal ═══════════════════════════════

class Terminal:
    """Saída formatada: blocos com guia lateral, títulos, itens, caixas, tabelas, mensagens e perguntas.

    tema: 'auto' (padrão), 'katharos', 'pergaminho' ou os do Catppuccin ('mocha', 'macchiato', 'frappe', 'latte'). Em auto,
    usa Pergaminho quando o fundo do terminal é claro e Katharos (o da landing) quando é escuro ou desconhecido.
    destaque: uma das 14 cores do tema (padrão 'peach', o âmbar da landing). Marca o que é interativo: o ◇ dos
    títulos, os números do menu, o spinner, o › da pergunta.
    nivel: 'pleno', 'simples' ou 'ascii' (None = descobre).
    cores: 24, 256 ou 16 (None = descobre).
    """

    def __init__(self, ascii_forcado=False, sem_cor=False, tema=None, destaque=None, nivel=None, cores=None,
                 largura=None, consulta_fundo=True):
        env = os.environ
        vt = _liga_vt_windows() if os.name == 'nt' else None
        cod_original = (getattr(sys.stdout, 'encoding', '') or '').lower().replace('-', '')
        for fluxo in (sys.stdout, sys.stderr):
            try:
                fluxo.reconfigure(encoding='utf-8', errors='replace')
            except (AttributeError, ValueError):
                pass
        # o Git Bash (mintty) entrega pipes ao Python, que então acha que não está num terminal
        mintty = bool(env.get('MSYSTEM')) or env.get('TERM_PROGRAM') == 'mintty'
        win_moderno = ('WT_SESSION' in env or 'TERM_PROGRAM' in env or mintty or env.get('ConEmuANSI') == 'ON'
                       or bool(env.get('WEZTERM_PANE')))
        termo = env.get('TERM', '')
        self.tty = sys.stdout.isatty() or mintty
        self.interativo = sys.stdin.isatty() or mintty
        if self.interativo and os.name == 'nt' and not mintty:
            # no Windows, "< nul" também passa por terminal no isatty; o console de verdade aceita GetConsoleMode
            try:
                import ctypes
                m = ctypes.c_uint32()
                self.interativo = bool(ctypes.windll.kernel32.GetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-10), ctypes.byref(m)))
            except Exception:
                pass

        # cor: NO_COLOR > FORCE_COLOR/CLICOLOR_FORCE > TTY; console do Windows sem VT não tem cor
        forca = env.get('FORCE_COLOR')
        if sem_cor or 'NO_COLOR' in env or forca == '0':
            self.cor = False
        elif (forca and forca != '0') or env.get('CLICOLOR_FORCE', '0') != '0':
            self.cor = True
        else:
            self.cor = self.tty and termo != 'dumb' and vt is not False
        ct = env.get('COLORTERM', '').lower()
        if cores in (16, 256, 24):
            self.modo_cor = cores
        elif forca in ('1', '2', '3'):
            self.modo_cor = {'1': 16, '2': 256, '3': 24}[forca]
        elif (ct in ('truecolor', '24bit') or 'WT_SESSION' in env or mintty or env.get('WEZTERM_PANE')
              or env.get('TERM_PROGRAM') in ('vscode', 'iTerm.app', 'WezTerm', 'Hyper', 'ghostty', 'zed', 'WarpTerminal')
              or termo in ('xterm-kitty', 'xterm-ghostty', 'alacritty', 'foot')):
            self.modo_cor = 24
        elif env.get('GITHUB_ACTIONS') or env.get('GITLAB_CI'):
            self.modo_cor = 24
        elif termo == 'linux':
            self.modo_cor = 16
        elif (os.name == 'nt' or '256' in termo or env.get('TERM_PROGRAM') == 'Apple_Terminal'
              or termo.startswith(('xterm', 'screen', 'tmux', 'rxvt'))):
            self.modo_cor = 256
        else:
            self.modo_cor = 16

        # o Python força UTF-8 até em locale "C", então quem diz se o terminal entende UTF-8 é o idioma
        idioma = env.get('LC_ALL') or env.get('LC_CTYPE') or env.get('LANG') or ''
        sem_utf8 = os.name != 'nt' and ((idioma and 'utf' not in idioma.lower())
                                        or (cod_original and 'utf8' not in cod_original))
        if nivel in ('pleno', 'simples', 'ascii'):
            self.nivel = nivel
        elif ascii_forcado or env.get('KTERM_ASCII') or env.get('FERRAMENTAS_ASCII') or sem_utf8 or termo == 'dumb':
            self.nivel = 'ascii'
        elif (os.name == 'nt' and not win_moderno) or termo == 'linux':
            self.nivel = 'simples'
        else:
            self.nivel = 'pleno'

        # tema e destaque
        tema = tema or env.get('KTERM_TEMA') or 'auto'
        if tema == 'auto':
            claro = None
            if self.cor and self.modo_cor != 16:
                pode = consulta_fundo and self.tty and self.interativo and not env.get('CI') and termo not in ('linux', 'dumb')
                claro = _fundo_claro(env, pode)
            tema = 'pergaminho' if claro else 'katharos'
        if tema not in _CTP:
            tema = 'katharos'
        destaque = destaque or env.get('KTERM_DESTAQUE') or 'peach'
        if destaque not in DESTAQUES:
            destaque = 'peach'
        self.tema, self.destaque = tema, destaque
        self.paleta = paleta(tema, destaque)

        self.links = self.cor and self.tty and _aceita_links(env)
        self._largura_fixa = largura
        self.largura = self._mede()
        self.trava = threading.RLock()
        self.vivo_txt = ''
        self.guia = False
        self._vazia = False
        self._caixa = None

    # ─────────────── medidas e cores ───────────────

    def _mede(self):
        # a guia lateral e os dois espaços depois dela ocupam duas colunas: o conteúdo é montado
        # para `largura` e cabe na tela
        cols = self._largura_fixa or shutil.get_terminal_size((72, 24)).columns
        return max(36, min(cols - 3, 78))

    def atualiza_largura(self):
        """Mede a tela de novo (se a janela mudou de tamanho). Chamado a cada cabeçalho."""
        if self._caixa is None:
            self.largura = self._mede()

    def _adapta(self, txt):
        if self.nivel == 'pleno':
            return txt
        if self.nivel == 'simples':
            return txt.translate(TROCA_SIMPLES)
        return unicodedata.normalize('NFKD', txt.translate(TROCA_ASCII)).encode('ascii', 'ignore').decode()

    def _rgb(self, rgb, fundo=False, nome=None):
        if self.modo_cor == 16:
            if nome == 'destaque':
                n = _DESTAQUE16.get(self.destaque, 32)
            else:
                n = _CORES16.get(nome, 39)
            if fundo:
                n = {39: 49, 90: 100}.get(n, n + 10)
            return f'\033[{n}m'
        camada = 48 if fundo else 38
        if self.modo_cor == 24:
            return f'\033[{camada};2;{rgb[0]};{rgb[1]};{rgb[2]}m'
        return f'\033[{camada};5;{_xterm256(*rgb)}m'

    def _cod(self, nome, fundo=False):
        nome = _APELIDOS.get(nome, nome)
        return self._rgb(self.paleta[nome], fundo, nome)

    def p(self, txt, cor=None, negrito=False, fundo=None):
        """Pinta um texto com um papel da paleta: texto, sub, apagado, borda, trilho, destaque, verde,
        vermelho, amarelo, pessego, azul, roxo, teal, rosa, escuro."""
        if not self.cor or (cor is None and not negrito and fundo is None):
            return str(txt)
        s = ('\033[1m' if negrito else '') + (self._cod(cor) if cor else '') + (self._cod(fundo, True) if fundo else '')
        return s + str(txt) + '\033[0m'

    def degrade(self, txt, cores=None, negrito=False):
        """Pinta cada coluna com uma cor entre as da lista (o logo, por exemplo)."""
        cores = cores or ('destaque', 'teal', 'azul')
        if not self.cor or self.modo_cor == 16:
            return self.p(txt, cores[0], negrito)
        pontos = [self.paleta[_APELIDOS.get(c, c)] for c in cores]
        saida, n = [], max(len(txt) - 1, 1)
        for i, ch in enumerate(txt):
            if ch == ' ':
                saida.append(ch)
                continue
            pos = i / n * (len(pontos) - 1)
            a, b = pontos[int(pos)], pontos[min(int(pos) + 1, len(pontos) - 1)]
            f = pos - int(pos)
            rgb = tuple(round(x + (y - x) * f) for x, y in zip(a, b))
            saida.append(self._rgb(rgb) + ch)
        return ('\033[1m' if negrito else '') + ''.join(saida) + '\033[0m'

    def selo(self, txt, cor):
        """Etiqueta com fundo colorido, como os PASS/FAIL do Vitest; sem cor vira [TEXTO]."""
        if not self.cor:
            return f'[{txt}]'
        if self.modo_cor == 16:
            return self.p(f' {txt} ', None, True, fundo=cor) if cor else f'[{txt}]'
        return self.p(f' {txt} ', 'escuro', True, fundo=cor)

    def link(self, txt, alvo):
        # OSC 8: o texto vira clicável nos terminais que entendem; nos outros, fica só o texto
        if not self.links or not alvo:
            return txt
        if not re.match(r'[a-z]+://', str(alvo)):
            try:
                alvo = Path(alvo).resolve().as_uri()
            except (OSError, ValueError):
                return txt
        return f'\033]8;;{alvo}\033\\{txt}\033]8;;\033\\'

    def caminho(self, arq, n=None):
        return self.link(caminho_curto(arq, n), arq)

    def titulo_janela(self, txt):
        if self.tty and self.cor:
            sys.stdout.write(f'\033]0;{txt}\007')

    # ─────────────── escrita ───────────────

    def _com_guia(self, txt):
        # dentro de um bloco, a linha ganha a guia lateral no lugar dos dois espaços do começo
        if not self.guia:
            return txt
        barra = ' ' + self.p('│', 'borda')
        if not txt:
            return barra
        return barra + '  ' + (txt[2:] if txt.startswith('  ') else txt)

    def escreve(self, txt='', guia=True):
        if self._caixa is not None and guia:
            self._caixa['linhas'].append(txt)
            return
        vazia = not ANSI.sub('', txt).strip()
        if vazia and self._vazia:
            return  # duas linhas em branco seguidas viram uma
        self._vazia = vazia
        linha = self._adapta(self._com_guia(txt) if guia else txt)
        with self.trava:
            if self.vivo_txt and self.tty:
                sys.stdout.write('\r\033[2K')
            sys.stdout.write(linha + '\n')
            if self.vivo_txt and self.tty:
                sys.stdout.write(self.vivo_txt)
            sys.stdout.flush()

    def vivo(self, txt, guia=True):
        """Linha que se reescreve no lugar (spinner, contagem). Some quando não há terminal."""
        if not self.tty:
            return
        with self.trava:
            # linha viva mais larga que a tela quebra, e o \r só apaga o último pedaço: corta antes
            linha = self._com_guia(txt) if guia else txt
            self.vivo_txt = self._adapta(corta_visivel(linha, self.largura + 2))
            sys.stdout.write('\r\033[2K' + self.vivo_txt)
            sys.stdout.flush()

    def para_vivo(self):
        with self.trava:
            if self.vivo_txt and self.tty:
                sys.stdout.write('\r\033[2K')
                sys.stdout.flush()
            self.vivo_txt = ''

    def limpa(self):
        if self.tty:
            sys.stdout.write('\033[2J\033[H')

    # ─────────────── estrutura ───────────────

    def logo(self, nome=None, simbolo=True, cores=None):
        """Logo em blocos com degradê. Sem nome, o </> KESSLERU. Tela estreita ou ASCII: uma linha só."""
        linhas = LOGO_NOME if nome is None else texto_em_blocos(nome)
        sim = LOGO_SIMBOLO if simbolo else None
        cores = cores or ('destaque', 'teal', 'azul')
        larg = len(linhas[0]) + (len(LOGO_SIMBOLO[0]) + 3 if sim else 0) + 2
        self.escreve(guia=False)
        if larg <= self.largura + 2 and self.nivel != 'ascii':
            for i, n in enumerate(linhas):
                pre = self.p(sim[i], 'texto') + '   ' if sim else ''
                self.escreve('  ' + pre + self.degrade(n, cores), guia=False)
        else:
            curto = (self.p('</>', 'texto', True) + '  ' if sim else '')
            self.escreve('  ' + curto + self.degrade((nome or 'KESSLERU').upper(), cores, True), guia=False)

    def cabecalho(self, caminho, extra='', app='ferramentas'):
        """Abre um bloco: a primeira linha, com o nome do app (e da tela), e a guia lateral daí para baixo.
        caminho='início' mostra só o nome do app."""
        self.fecha_caixa()
        self.atualiza_largura()
        self.escreve(guia=False)
        marca = self.p('┌', 'borda')
        if caminho in ('início', '', None):
            nome = self.p(app, 'texto', True)
            self.titulo_janela(app)
        else:
            nome = (self.p(app, 'apagado') + self.p(' › ', 'borda')
                    + self.p(f' {caminho} ', 'texto', True, fundo='trilho' if self.modo_cor != 16 else None))
            self.titulo_janela(f'{app} › {caminho}')
        if extra:
            cabe = self.largura - vlen(nome) - 3
            extra = self.p('  ' + corta(extra, cabe), 'apagado') if cabe >= 6 else ''
        self.escreve(' ' + marca + '  ' + nome + extra, guia=False)
        self.guia = True
        self.escreve()

    def fim(self, txt='', nivel='ok'):
        """Fecha o bloco aberto pelo cabeçalho; o ícone diz como terminou: ok, aviso, erro ou nada."""
        self.fecha_caixa()
        if not self.guia:
            return
        self.para_vivo()
        self.escreve()
        self.guia = False
        icone = {'ok': self.p('✓', 'verde'), 'aviso': self.p('!', 'amarelo', True),
                 'erro': self.p('■', 'vermelho'), 'nada': ''}[nivel]
        self.escreve(' ' + self.p('└', 'borda') + '  ' + (icone + ' ' if icone else '') + self.p(txt, 'apagado'),
                     guia=False)

    def titulo(self, txt, caixa=False):
        """Título de seção (◇ no destaque). caixa=True junta o que vem depois numa caixa, até o próximo
        título, pergunta, progresso ou fim."""
        self.fecha_caixa()
        if caixa and self.guia and self.nivel != 'ascii':
            # o resumo vai numa caixa (como o "note" do Clack); o conteúdo é montado mais estreito
            self._caixa = {'titulo': txt, 'linhas': []}
            self.largura -= 3
            return
        self.escreve()
        self.escreve(' ' + self.p('◇', 'destaque') + '  ' + self.p(txt, 'texto', True), guia=False)

    def fecha_caixa(self):
        cx, self._caixa = self._caixa, None
        if cx is None:
            return
        self.largura += 3
        linhas = [l[2:] if l.startswith('  ') else l for l in cx['linhas']]
        while linhas and not ANSI.sub('', linhas[0]).strip():
            linhas.pop(0)
        while linhas and not ANSI.sub('', linhas[-1]).strip():
            linhas.pop()
        tit = _larg(cx['titulo'])
        larg = max([vlen(l) for l in linhas] + [tit + 3]) + 2
        borda = lambda s: self.p(s, 'borda')
        self.escreve()
        self.escreve(' ' + self.p('◇', 'destaque') + '  ' + self.p(cx['titulo'], 'texto', True) + ' '
                     + borda('─' * (larg - tit - 1) + '╮'), guia=False)
        for l in [''] + linhas + ['']:
            self.escreve(' ' + borda('│') + '  ' + l + ' ' * (larg - vlen(l)) + borda('│'), guia=False)
        self.escreve(' ' + borda('├' + '─' * (larg + 2) + '╯'), guia=False)
        self._vazia = False

    def aba(self, descricao=''):
        """A descrição da tela logo abaixo do cabeçalho, discreta."""
        if descricao:
            self.escreve('  ' + self.p(corta(descricao, self.largura - 4), 'apagado'))
            self.escreve()

    # ─────────────── conteúdo ───────────────

    def prompt(self, pasta, txt, alvo=None):
        """Linha no estilo de prompt: ~/pasta  comando."""
        txt = corta(txt, self.largura - _larg(pasta) - 6)
        self.escreve('  ' + self.p('~/', 'destaque') + self.p(pasta, 'apagado') + '  ' + self.link(self.p(txt, 'texto'), alvo))

    def item(self, icone, cor, nome, detalhe='', recuo=2, cor_nome='texto', alvo=None):
        """Linha de lista: ícone, nome e detalhe alinhado à direita com pontos guia."""
        w, d = self.largura, vlen(detalhe)
        nomeia = lambda n: self.link(self.p(n, cor_nome), alvo)  # o link entra depois do corte
        if d and recuo + 6 + min(_larg(nome), 16) + d > w:
            self.escreve(' ' * recuo + self.p(icone, cor) + ' ' + nomeia(corta(nome, w - recuo - 2)))
            self.escreve(' ' * (recuo + 2) + corta_visivel(detalhe, w - recuo - 2))
            return
        n = corta(nome, w - recuo - 5 - d)
        if not d:
            self.escreve(' ' * recuo + self.p(icone, cor) + ' ' + nomeia(n))
            return
        pontos = max(1, w - recuo - 2 - _larg(n) - 2 - d)
        self.escreve(' ' * recuo + self.p(icone, cor) + ' ' + nomeia(n) + ' '
                     + self.p('·' * pontos, 'trilho') + ' ' + detalhe)

    def partes(self, itens, recuo=4):
        """Junta com " · " e quebra a linha entre itens, nunca no meio de um."""
        linha, larg = '', 0
        for it in itens:
            n = vlen(it)
            if linha and recuo + larg + 3 + n > self.largura:
                self.escreve(' ' * recuo + linha)
                linha, larg = '', 0
            if linha:
                linha += self.p(' · ', 'apagado')
                larg += 3
            linha += it
            larg += n
        if linha:
            self.escreve(' ' * recuo + linha)

    def paragrafo(self, txt, recuo=4, cor='sub'):
        for linha in textwrap.wrap(txt, max(20, self.largura - recuo), break_on_hyphens=False):
            self.escreve(' ' * recuo + self.p(linha, cor))

    def chaves(self, pares, recuo=2, cor_valor='texto'):
        """Pares rótulo: valor, com os rótulos alinhados."""
        if not pares:
            return
        k = min(max(_larg(str(a)) for a, _ in pares), max(8, self.largura // 2))
        for a, b in pares:
            v = str(b)
            espaco = self.largura - recuo - k - 2
            valor = corta_visivel(v, espaco) if vlen(v) != len(v) else self.p(corta(v, espaco), cor_valor)
            rot = corta(str(a), k)
            self.escreve(' ' * recuo + self.p(rot, 'apagado') + ' ' * (k - _larg(rot) + 2) + valor)

    def tabela(self, cabecalhos, linhas, alinha=None, recuo=2, flex=None):
        """Tabela simples: cabeçalho discreto, fio embaixo, colunas alinhadas.
        alinha: string com 'e' (esquerda) ou 'd' (direita) por coluna; números ficam à direita sozinhos.
        flex: índice da coluna que encolhe para caber (padrão: a mais larga)."""
        cols = len(cabecalhos)
        linhas = [[str(c) for c in l] + [''] * (cols - len(l)) for l in linhas]
        if alinha is None:
            num = re.compile(r'^[\s\d.,%+\-–kKMGTBms/]+$')
            alinha = ''.join('d' if linhas and all(num.match(ANSI.sub('', l[i]) or '0') for l in linhas) else 'e'
                             for i in range(cols))
        larg = [max([_larg(cabecalhos[i])] + [vlen(l[i]) for l in linhas]) for i in range(cols)]
        sobra = self.largura - recuo - sum(larg) - 2 * (cols - 1)
        if sobra < 0:
            f = flex if flex is not None else max(range(cols), key=lambda i: larg[i])
            larg[f] = max(4, larg[f] + sobra)

        def celula(txt, i, cor=None):
            txt = corta_visivel(txt, larg[i]) if vlen(txt) != len(ANSI.sub('', txt)) or '\033' in txt else corta(txt, larg[i])
            pintado = self.p(txt, cor) if cor and '\033' not in txt else txt
            pad = ' ' * (larg[i] - vlen(txt))
            return pad + pintado if alinha[i] == 'd' else pintado + pad

        self.escreve(' ' * recuo + '  '.join(celula(c, i, 'apagado') for i, c in enumerate(cabecalhos)).rstrip())
        self.escreve(' ' * recuo + self.p('─' * (sum(larg) + 2 * (cols - 1)), 'trilho'))
        for l in linhas:
            self.escreve(' ' * recuo + '  '.join(celula(c, i, 'texto' if i == 0 else 'sub') for i, c in enumerate(l)).rstrip())

    def barra(self, rotulo, valor, total, detalhe='', cor='destaque', recuo=2, larg_rotulo=None):
        """Medidor estático: rótulo, barra proporcional e detalhe (como o peso por tipo de arquivo)."""
        total = max(total, 1e-9)
        lr = larg_rotulo or min(14, _larg(rotulo))
        # largura fixa (não depende do detalhe), para várias barras seguidas ficarem do mesmo tamanho
        n = max(6, min(30, self.largura - recuo - lr - 18))
        cheio = max(0, min(n, int(round(n * valor / total))))
        bloco, vazio = ('#', '-') if self.nivel == 'ascii' else ('■', '■' if self.cor else '·')
        corpo = self.p(bloco * cheio, cor) + self.p(vazio * (n - cheio), 'trilho')
        rot = corta(rotulo, lr)
        self.escreve(' ' * recuo + self.p(rot, 'sub') + ' ' * (lr - _larg(rot) + 1) + corpo + ('  ' + detalhe if detalhe else ''))

    def passos(self, lista, recuo=2):
        """Lista de etapas com estado: ('ok'|'atual'|'pendente'|'erro'|'pulado', texto[, detalhe])."""
        icones = {'ok': ('✓', 'verde'), 'atual': ('◆', 'destaque'), 'pendente': ('○', 'apagado'),
                  'erro': ('✗', 'vermelho'), 'pulado': ('↷' if self.nivel == 'pleno' else '-', 'apagado')}
        for p in lista:
            estado, txt = p[0], p[1]
            det = p[2] if len(p) > 2 else ''
            ic, cor = icones.get(estado, icones['pendente'])
            cor_txt = 'texto' if estado in ('ok', 'atual', 'erro') else 'apagado'
            self.item(ic, cor, txt, self.p(det, 'apagado') if det else '', recuo=recuo, cor_nome=cor_txt)

    # ─────────────── mensagens ───────────────

    def _mensagem(self, icone, txt, cor):
        if vlen(txt) != len(txt):  # já vem colorido: não dá para quebrar sem estragar as cores
            self.escreve('  ' + icone + ' ' + txt)
            return
        for i, linha in enumerate(textwrap.wrap(txt, max(20, self.largura - 4), break_on_hyphens=False) or ['']):
            self.escreve(('  ' + icone if i == 0 else '   ') + ' ' + (self.p(linha, cor) if cor else linha))

    def ok(self, txt):
        self._mensagem(self.p('✓', 'verde'), txt, None)

    def aviso(self, txt):
        self._mensagem(self.p('!', 'amarelo', True), txt, 'amarelo')

    def erro(self, txt):
        self._mensagem(self.p('✗', 'vermelho', True), txt, 'vermelho')

    def info(self, txt):
        self._mensagem(self.p('›', 'azul', True), txt, None)

    def nota(self, txt, recuo=2):
        self.escreve(' ' * recuo + self.p(txt, 'apagado'))

    def dicas(self, pares, recuo=2):
        """As teclas que valem agora, numa linha: a tecla em destaque, o que ela faz ao lado, bolinha entre uma e outra.
        pares: [('Enter', 'continuar'), ('?', 'ajuda')]. Poucas: o resto fica na ajuda da tela."""
        linha, larg = ' ' * recuo, recuo
        for i, (tecla, faz) in enumerate(pares):
            pedaco = self.p(tecla, 'destaque', True) + ' ' + self.p(faz, 'apagado')
            n = _larg(tecla) + 1 + _larg(faz)
            sep = '  ·  ' if i else ''
            if i and larg + len(sep) + n > self.largura:
                self.escreve(linha)
                linha, larg, sep = ' ' * recuo, recuo, ''
            linha += self.p(sep, 'apagado') + pedaco
            larg += len(sep) + n
        self.escreve(linha)

    def relatorio(self, arq, rotulo='relatório', recuo=4):
        """A linha "relatório: caminho", com o caminho clicável onde o terminal deixa."""
        self.escreve(' ' * recuo + self.p(f'{rotulo}: ', 'apagado')
                     + self.p(self.caminho(arq, max(12, self.largura - recuo - _larg(rotulo) - 2)), 'sub'))

    # ─────────────── entrada ───────────────

    def pergunta(self, txt, padrao=''):
        """Pergunta numa linha, com o › no destaque. Sem entrada (pipe vazio), devolve o padrão."""
        self.fecha_caixa()
        self.para_vivo()
        rotulo = self._com_guia('  ' + self.p(txt, 'sub') + ' ' + self.p('› ', 'destaque'))
        try:
            return input(self._adapta(rotulo)) or padrao
        except EOFError:
            return padrao

    def confirma(self, pergunta, palavra='sim', sim=False):
        """Pergunta destacada (◆ amarelo) que só segue se a pessoa digitar a palavra.
        sim=True responde sozinho (para --sim). Sem terminal, recusa."""
        if sim:
            return True
        if not self.interativo:
            self.aviso('Sem terminal para confirmar; use --sim para seguir sem perguntar.')
            return False
        self.fecha_caixa()
        self.escreve()
        self.escreve(' ' + self.p('◆', 'amarelo') + '  ' + self.p(pergunta, 'amarelo', True), guia=False)
        return self.pergunta(f'digite {palavra.upper()} para confirmar').strip().lower() == palavra.lower()

    def espera(self, txt='Enter para continuar'):
        try:
            input(self._adapta('  ' + self.p(txt, 'apagado') + ' '))
        except EOFError:
            raise KeyboardInterrupt  # sem entrada (fim do pipe): sai do laço em vez de repetir para sempre

    def menu_itens(self, grupos, quando=None, destaque=None, zero='sair'):
        """Desenha um menu numerado em grupos e devolve {número: comando}.
        grupos: [(título, explicação, [(comando, descrição), ...]), ...] (a explicação pode faltar).
        quando: {comando: 'há 2 dias'}; destaque: {comando: 'etiqueta'} aparece à direita, em destaque."""
        num, por_numero = 0, {}
        larg_cmd = max([_larg(c) for g in grupos for c, _ in g[-1]] + [6])
        for g in grupos:
            titulo, itens = g[0], g[-1]
            expl = g[1] if len(g) == 3 else ''
            if titulo:   # grupo sem título (o menu de abertura): só as linhas
                self.escreve()
                linha = ' ' + self.p('◇', 'destaque') + '  ' + self.p(titulo, 'texto', True)
                if expl and _larg(titulo) + _larg(expl) + 8 <= self.largura:
                    linha += self.p('  ' + expl, 'apagado')
                self.escreve(linha, guia=False)
            for cmd, desc in itens:
                num += 1
                por_numero[str(num)] = cmd
                esq = (f'  {self.p(f"{num:>2}", "destaque", True)}  {self.p(cmd + " " * (larg_cmd - _larg(cmd)), "texto", True)}  '
                       f'{self.p(corta(desc, self.largura - larg_cmd - 8), "sub")}')
                q = (destaque or {}).get(cmd)
                cor_q = 'destaque'
                if not q:
                    q, cor_q = (quando or {}).get(cmd, ''), 'apagado'
                if q and vlen(esq) + _larg(q) + 2 <= self.largura:
                    esq += ' ' * (self.largura - vlen(esq) - _larg(q)) + self.p(q, cor_q)
                self.escreve(esq)
        self.escreve()
        self.escreve(f'  {self.p(" 0", "apagado", True)}  {self.p(zero, "apagado")}')
        self.escreve()
        return por_numero


# ═══════════════════════════════ Progresso ═══════════════════════════════

class Progresso:
    """Spinner com barra (ou só contagem, com total=None). Ao sair, deixa uma linha de registro:
    o que foi feito e quanto demorou, como o spinner do Clack.

        with Progresso(t, len(itens), 'arquivos') as p:
            for x in itens:
                ...
                p.avanca(x.nome)
    """
    QUADROS = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'

    def __init__(self, term, total, rotulo, registro=True):
        self.t, self.total, self.rotulo, self.registro = term, total, rotulo, registro
        self.n, self.atual, self._i = 0, '', 0
        self._parar = threading.Event()
        self._fio = threading.Thread(target=self._gira, daemon=True)
        if term.nivel != 'pleno':
            self.QUADROS = '|/-\\'
        self.cheio = '#' if term.nivel == 'ascii' else '■'
        self.vazio = '■' if term.cor else ('-' if term.nivel == 'ascii' else '·')
        self.inicio = time.time()

    def __enter__(self):
        self.t.fecha_caixa()
        self.inicio = time.time()
        if self.t.tty:
            if self.t.cor:
                sys.stdout.write('\033[?25l')  # esconde o cursor enquanto gira (ele piscava no meio da linha)
                _CURSOR_ESCONDIDO.append(1)
            self._fio.start()
        return self

    def __exit__(self, tipo, *_):
        self._parar.set()
        if self._fio.is_alive():
            self._fio.join()
        self.t.para_vivo()
        if self.t.tty and self.t.cor:
            sys.stdout.write('\033[?25h')
            sys.stdout.flush()
            if _CURSOR_ESCONDIDO:
                _CURSOR_ESCONDIDO.pop()
        dur = time.time() - self.inicio
        if self.registro and (dur >= 1 or tipo is not None or not self.t.tty):
            if self.total is None:
                conta = f'{self.n:,}'.replace(',', '.') + ' · ' if self.n else ''
            else:
                conta = f'{self.n}/{self.total} · '
            if tipo is KeyboardInterrupt:
                icone, fim = self.t.p('■', 'vermelho'), 'interrompido'
            else:
                icone, fim = self.t.p('◇', 'verde' if tipo is None else 'vermelho'), duracao(dur)
            self.t.escreve(' ' + icone + '  ' + self.t.p(self.rotulo, 'sub') + self.t.p(f'  {conta}{fim}', 'apagado'),
                           guia=not self.t.guia)
        return False

    def avanca(self, atual='', n=1):
        self.n += n
        self.atual = str(atual)

    def _desenho(self):
        t = self.t
        q = t.p(self.QUADROS[self._i % len(self.QUADROS)], 'destaque')
        self._i += 1
        dur = time.time() - self.inicio
        tempo = f' · {duracao(dur)}' if dur >= 3 else ''
        if self.total is None:
            conta = (f'{self.n:,}'.replace(',', '.') if self.n else '') + (tempo[3:] if not self.n else tempo)
            resto = t.largura - 6 - _larg(self.rotulo) - _larg(conta)
            return (f' {q}  {t.p(self.rotulo, "sub")} {t.p(conta, "texto")} '
                    f'{t.p(corta_esq(self.atual, max(0, resto)), "apagado")}')
        total = max(self.total, 1)
        conta = f'{self.n}/{total}'
        larg = max(6, min(20, t.largura - _larg(self.rotulo) - len(conta) - 26))
        cheio = int(larg * min(self.n, total) / total)
        barra = t.p(self.cheio * cheio, 'destaque') + t.p(self.vazio * (larg - cheio), 'trilho')
        resto = t.largura - 7 - _larg(self.rotulo) - larg - len(conta) - len(tempo)
        return (f' {q}  {t.p(self.rotulo, "sub")} {barra} {t.p(conta, "texto")}{t.p(tempo, "apagado")} '
                f'{t.p(corta(self.atual, max(0, resto)), "apagado")}')

    def _gira(self):
        while not self._parar.wait(0.08):
            self.t.vivo(self._desenho(), guia=False)

