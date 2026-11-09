# -*- coding: utf-8 -*-
"""katharos (καθαρός, "limpo" em grego): deixa qualquer Windows mais leve, num arquivo só.

Diagnóstico inteligente, limpeza, programas e apps de fábrica, inicialização, serviços, privacidade,
IA do Windows, visual, energia, disco, reparo, atualizações, manutenção automática e reversão de tudo.
Três modos (seguro, equilibrado, extremo) decidem o que vem marcado; você escolhe item por item.

    python katharos.py                 abre o menu
    python katharos.py raiox           diagnóstico com nota e recomendações
    python katharos.py turbo           otimiza tudo, em sequência, retomando depois de reiniciar
    python katharos.py limpar --teste  mostra o que faria, sem alterar nada

Python 3.8+, sem dependências. Só ferramentas nativas do Windows (PowerShell, DISM, sfc, winget, powercfg).
Visual: Kessleru (kterm 2.0.0, embutido abaixo). Dados em ~/.katharos.
"""

import argparse
import ctypes
import hashlib
import json
import queue
import subprocess
from datetime import datetime

VERSAO = '1.0.0'

# ███████████████████████████████████████████████████████████████████████████
#
#   NÚCLEO · o terminal (kterm 2.0.0, do design system Kessleru)
#
# ███████████████████████████████████████████████████████████████████████████

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



# ═══════════════════════════════ paleta: Kessleru (Catppuccin) ═══════════════════════════════
# Valores de 07 • Design System/Kessleru/codigo/tokens.json. Cada papel aponta para um token.

_CTP = {
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


def paleta(tema='frappe', destaque='green'):
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

    tema: 'auto' (padrão), 'mocha', 'macchiato', 'frappe' ou 'latte'. Em auto, usa Latte quando o fundo
    do terminal é claro e Frappé quando é escuro ou desconhecido.
    destaque: uma das 14 cores do Catppuccin (padrão 'green'). Marca o que é interativo: o ◇ dos
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
            tema = 'latte' if claro else 'frappe'
        if tema not in _CTP:
            tema = 'frappe'
        destaque = destaque or env.get('KTERM_DESTAQUE') or 'green'
        if destaque not in DESTAQUES:
            destaque = 'green'
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

    def menu_itens(self, grupos, quando=None):
        """Desenha um menu numerado em grupos e devolve {número: comando}.
        grupos: [(título, [(comando, descrição), ...]), ...]. quando: {comando: 'há 2 dias'} opcional."""
        num, por_numero = 0, {}
        larg_cmd = max([_larg(c) for _, itens in grupos for c, _ in itens] + [6])
        for titulo, itens in grupos:
            self.titulo(titulo)
            for cmd, desc in itens:
                num += 1
                por_numero[str(num)] = cmd
                esq = (f'  {self.p(f"{num:>2}", "destaque", True)}  {self.p(cmd + " " * (larg_cmd - _larg(cmd)), "texto")}  '
                       f'{self.p(corta(desc, self.largura - larg_cmd - 8), "sub")}')
                q = (quando or {}).get(cmd, '')
                if q and vlen(esq) + _larg(q) + 2 <= self.largura:
                    esq += ' ' * (self.largura - vlen(esq) - _larg(q)) + self.p(q, 'apagado')
                self.escreve(esq)
            self.escreve()
        self.escreve(f'  {self.p(" 0", "apagado", True)}  {self.p("sair", "apagado")}')
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
NOME_NIVEL = {0: 'só se marcar', 1: 'seguro', 2: 'equilibrado', 3: 'extremo'}
COR_NIVEL = {0: 'apagado', 1: 'verde', 2: 'azul', 3: 'pessego'}

EXPLICA_MODOS = [
    ('seguro', 'verde', 'Só o que não tem contrapartida: telemetria, anúncios, lixo, apps de propaganda, '
     'tarefas inúteis. Bom para PC de trabalho ou de outra pessoa.'),
    ('equilibrado', 'azul', 'O seguro mais o que quase ninguém usa: serviços de empresa e de telefone, '
     'Xbox (se não joga), IA do Windows, widgets, efeitos visuais, caches. É o recomendado.'),
    ('extremo', 'pessego', 'Tudo o que pode ajudar neste PC: desliga sensores, área de trabalho remota, '
     'scanner, localização, hibernação no SSD, ajustes de jogos e de rede. Você perde recursos (cada item diz quais).'),
]

PADROES = {'modo': 'equilibrado', 'explicacao': 'completa', 'cores': 'automático', 'simbolos': 'automático',
           'grandes-mb': '500', 'navegador': 'nenhum'}
DESCR_CONFIG = {
    'modo': ('modo padrão', 'seguro, equilibrado ou extremo: o que vem marcado em cada tela'),
    'explicacao': ('explicações', 'completa (o que faz, ganho e custo de cada item) ou curta (só o nome)'),
    'cores': ('cores', 'automático ou sem cor'),
    'simbolos': ('símbolos', 'automático ou simples (para terminal que mostra quadradinhos)'),
    'grandes-mb': ('arquivo grande', 'a partir de quantos MB o "grandes" mostra um arquivo'),
    'navegador': ('navegador leve', 'brave ou nenhum: se o turbo instala o Brave enxuto'),
}


def pasta(*partes):
    d = CASA.joinpath(*partes)
    d.mkdir(parents=True, exist_ok=True)
    return d


def le_json(arq, padrao):
    try:
        with open(arq, encoding='utf-8-sig') as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao


def grava_json(arq, dados):
    arq = Path(arq)
    arq.parent.mkdir(parents=True, exist_ok=True)
    tmp = arq.with_suffix(arq.suffix + '.tmp')
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
    """Texto como literal de PowerShell entre aspas simples."""
    return "'" + str(s).replace("'", "''") + "'"


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


def decodifica(b):
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
function Set-Valor([string]$Path, [string]$Name, $Value, [string]$Type = 'DWord', [string]$Rotulo = '') {
    $a = _LeValor $Path $Name
    if ($a.existe -and (_Iguais $a.valor $Value)) { return $false }
    if ($TESTE) {
        if ($Rotulo) { Plano $Rotulo } else { $vv = $Value; if ($Value -is [byte[]]) { $vv = 'binario' }; Plano ("{0} = {1}  ({2})" -f $Name, $vv, (Split-Path $Path -Leaf)) }
        return $true
    }
    $v = $a.valor
    if ($a.tipo -eq 'Binary' -and $null -ne $a.valor) { $v = [Convert]::ToBase64String([byte[]]$a.valor) }
    _BkGuarda ("reg|" + $Path + "|" + $Name) @{ t = 'reg'; p = $Path; n = $Name; existe = $a.existe; tipo = $a.tipo; v = $v }
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
    try { Remove-ItemProperty -LiteralPath $Path -Name $Name -Force -ErrorAction Stop; $script:MUDOU++; return $true } catch { return $false }
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
    $s = (Get-ChildItem -LiteralPath $P -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
    if ($s) { return [double]$s } else { return 0 }
}
function LimpaAntigos([string]$P, [double]$Dias = 0) {
    # Apaga arquivos mais velhos que N dias (arquivo em uso fica). Devolve os bytes liberados.
    if (-not (Test-Path -LiteralPath $P)) { return 0 }
    $limite = (Get-Date).AddDays(-$Dias); $livre = 0
    foreach ($f in @(Get-ChildItem -LiteralPath $P -Recurse -Force -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $limite })) {
        if ($TESTE) { $livre += $f.Length; continue }
        $len = $f.Length
        Remove-Item -LiteralPath $f.FullName -Force -ErrorAction SilentlyContinue
        if (-not (Test-Path -LiteralPath $f.FullName)) { $livre += $len }
    }
    if (-not $TESTE) {
        Get-ChildItem -LiteralPath $P -Recurse -Force -Directory -ErrorAction SilentlyContinue | Sort-Object { $_.FullName.Length } -Descending |
            Where-Object { -not (Get-ChildItem -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue) } | Remove-Item -Force -ErrorAction SilentlyContinue
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
$n = 0
foreach ($l in $linhas) {
    try { $o = ConvertFrom-Json $l } catch { continue }
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
                    if ($nn -eq '') { Remove-Item -LiteralPath $o.p -Recurse -Force -ErrorAction SilentlyContinue }
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
            self.p = subprocess.Popen([ps, '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(arq)],
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
            self.pid = self.p.pid
            threading.Thread(target=self._le_pipe, daemon=True).start()
            return
        self.saida = Path(str(arq) + '.saida.txt')
        linha = f'cmd.exe /c ""{ps}" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "{arq}" > "{self.saida}" 2>&1"'
        cria = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = " + psq(linha) +
                " }; [Console]::Out.Write([string]$r.ProcessId + '|' + [string]$r.ReturnValue)")
        r = subprocess.run([ps, '-NoProfile', '-NonInteractive', '-Command', cria], capture_output=True, text=True, timeout=90)
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
    Devolve Saida. pacote: pasta de backup (~/.katharos/backup/PACOTE) para as mudanças poderem voltar."""
    s = Saida()
    if not WINDOWS:
        s.codigo = 1
        s.erros.append('só funciona no Windows')
        return s
    arq = pasta('tmp') / f'{re.sub(r"[^a-z0-9-]", "-", rotulo.lower())[:30]}-{os.getpid()}-{int(time.time() * 1000) % 100000}.ps1'
    # as variáveis vão dentro do script: o processo criado pelo WMI não herda o ambiente
    cabeca = (f"$env:OTM_TESTE = '{'1' if teste else '0'}'\n$env:OTM_CASA = {psq(CASA)}\n$env:OTM_MULT = '{mult:.2f}'\n"
              f"$env:OTM_BK = {psq(pasta('backup', pacote) if pacote else '')}\n")
    with open(arq, 'w', encoding='utf-8-sig', newline='\r\n') as f:  # BOM: o PowerShell 5.1 lê como UTF-8
        f.write(cabeca + PRELUDIO_PS + '\n' + (DESFAZ_PS if desfaz else corpo) + '\n')
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
        p = subprocess.Popen([str(c) for c in cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
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


# ███████████████████████████████████████████████████████████████████████████
#
#   PARTE 1 · CONHECER O PC
#   perfil (o que o PC tem e usa), medidas (antes/depois) e o raio-x com recomendações
#
# ███████████████████████████████████████████████████████████████████████████

PERFIL_PS = r'''
$cs = Tenta { Get-CimInstance Win32_ComputerSystem }
$os = Tenta { Get-CimInstance Win32_OperatingSystem }
$cv = Tenta { Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' }
$cpu = Tenta { Get-CimInstance Win32_Processor | Select-Object -First 1 }
$enc = Tenta { Get-CimInstance Win32_SystemEnclosure | Select-Object -First 1 }
$bat = Tenta { Get-CimInstance Win32_Battery | Select-Object -First 1 }
$chassi = @(); if ($enc) { $chassi = @($enc.ChassisTypes) }
$notebook = [bool]$bat -or (@($chassi | Where-Object { $_ -in 8,9,10,11,12,14,18,21,30,31,32 }).Count -gt 0)
$tablet = (@($chassi | Where-Object { $_ -in 30,31,32 }).Count -gt 0) -or [bool](Tenta { Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\PriorityControl' -Name ConvertibleSlateMode -ErrorAction Stop })

# disco do sistema
$tipoC = 'desconhecido'; $barC = ''; $saudeC = ''
try {
    $part = Get-Partition -DriveLetter C -ErrorAction Stop
    $pd = Get-PhysicalDisk | Where-Object { $_.DeviceId -eq [string]$part.DiskNumber } | Select-Object -First 1
    if ($pd) { $tipoC = [string]$pd.MediaType; $barC = [string]$pd.BusType; $saudeC = [string]$pd.HealthStatus }
    if ($tipoC -eq 'Unspecified' -and $barC -eq 'NVMe') { $tipoC = 'SSD' }
} catch {}
$ld = Tenta { Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'" }
$livreC = 0; $totalC = 0; if ($ld) { $livreC = [math]::Round($ld.FreeSpace / 1GB, 1); $totalC = [math]::Round($ld.Size / 1GB, 1) }

$pentes = @(Tenta { Get-CimInstance Win32_PhysicalMemory } @())
$arr = Tenta { Get-CimInstance Win32_PhysicalMemoryArray | Select-Object -First 1 }
$slots = 0; if ($arr) { $slots = [int]$arr.MemoryDevices }

function TemClasse([string]$C) { return [bool](Get-PnpDevice -Class $C -PresentOnly -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'OK' } | Select-Object -First 1) }
$impressoras = @(Tenta { Get-Printer -ErrorAction Stop | Where-Object { $_.PortName -notmatch 'PORTPROMPT|XPS|nul|SHRFAX|OneNote|PDF|Microsoft' -and $_.Name -notmatch 'PDF|XPS|OneNote|Fax' } } @())
$ap = Tenta { Get-AppxPackage -ErrorAction Stop | Select-Object -ExpandProperty Name } @()
$prog = @(Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName } | ForEach-Object { [string]$_.DisplayName })
function TemProg([string]$P) { return [bool]($prog | Where-Object { $_ -match $P } | Select-Object -First 1) }
function TemApp([string]$P) { return [bool]($ap | Where-Object { $_ -match $P } | Select-Object -First 1) }

$jogos = @()
foreach ($par in @(@('Steam','^Steam$'), @('Epic Games','Epic Games Launcher'), @('Battle.net','Battle\.net'), @('Riot','Riot Client|Riot Vanguard|League of Legends|VALORANT'), @('EA app','^EA app$|^EA$|Origin'), @('Ubisoft','Ubisoft Connect|Uplay'), @('GOG','GOG GALAXY'), @('Rockstar','Rockstar Games Launcher'), @('Minecraft','Minecraft'))) {
    if (TemProg $par[1]) { $jogos += $par[0] }
}
if (TemApp '^Microsoft\.GamingApp$') { $jogos += 'Xbox (app)' }
$oemGamer = @()
foreach ($par in @(@('Alienware Command Center','Alienware Command Center|AWCC'), @('Armoury Crate','Armoury Crate'), @('Lenovo Vantage','Lenovo Vantage|LenovoVantage'), @('NitroSense','NitroSense|PredatorSense'), @('MSI Center','MSI Center|Dragon Center'), @('OMEN Gaming Hub','OMEN Gaming Hub|OMEN Command Center'))) {
    if ((TemProg $par[1]) -or (TemApp ($par[1] -replace ' ', ''))) { $oemGamer += $par[0] }
}

$av = @(Tenta { Get-CimInstance -Namespace root\SecurityCenter2 -ClassName AntiVirusProduct -ErrorAction Stop | ForEach-Object {
    $estado = '{0:X6}' -f [int]$_.productState
    [pscustomobject]@{ nome = [string]$_.displayName; ativo = ($estado.Substring(2, 2) -in '10','11') }
} } @())
$mp = Tenta { Get-MpComputerStatus -ErrorAction Stop }
$od = Join-Path $env:USERPROFILE 'OneDrive'
$odUsado = $false
if ($env:OneDrive -and (Test-Path -LiteralPath $env:OneDrive)) { $odUsado = [bool](Get-ChildItem -LiteralPath $env:OneDrive -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch '^desktop\.ini$|^\.' } | Select-Object -First 1) }
$plano = Tenta { (powercfg /getactivescheme | Out-String).Trim() } ''
$gpus = @(Tenta { Get-CimInstance Win32_VideoController | ForEach-Object { [string]$_.Name } } @())
$dono = Tenta { (Get-CimInstance Win32_Process -Filter "Name='explorer.exe'" | Select-Object -First 1 | Invoke-CimMethod -MethodName GetOwner).User } ''
$pf = Tenta { Get-CimInstance Win32_PageFileSetting } $null
$pfAuto = Tenta { (Get-CimInstance Win32_ComputerSystem).AutomaticManagedPagefile } $true
$mm = Tenta { (Get-MMAgent -ErrorAction Stop).MemoryCompression } $null
$uptime = 0; if ($os) { $uptime = [math]::Round(((Get-Date) - $os.LastBootUpTime).TotalHours, 1) }
$pend = (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending') -or (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired')
$build = 0; if ($os) { $build = [int]$os.BuildNumber }
$rdp = (Tenta { (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server' -ErrorAction Stop).fDenyTSConnections } 1) -eq 0
$winrm = [bool](Get-ChildItem 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WSMAN\Listener' -ErrorAction SilentlyContinue | Select-Object -First 1)
$ssh = (Test-Path (Join-Path $env:USERPROFILE '.ssh\id_*')) -or (Test-Path (Join-Path $env:USERPROFILE '.ssh\config'))
$wsl = [bool](Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' -ErrorAction SilentlyContinue | Select-Object -First 1)
$hyperv = [bool](Get-Service vmcompute -ErrorAction SilentlyContinue)
$docker = [bool](Get-Service com.docker.service -ErrorAction SilentlyContinue) -or (TemProg 'Docker Desktop')
$fh = [bool](Tenta { (Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\FileHistory' -ErrorAction Stop).ProtectedUpToTime })
$camera = (TemClasse 'Camera') -or (TemClasse 'Image')

Dado 'perfil' @{
    so = @{ nome = [string]$os.Caption; versao = [string]$cv.DisplayVersion; build = $build; win11 = ($build -ge 22000); edicao = [string]$cv.EditionID; idioma = (Get-Culture).Name; instalado = ([string]$os.InstallDate) }
    pc = @{ fabricante = ([string]$cs.Manufacturer).Trim(); modelo = ([string]$cs.Model).Trim(); notebook = $notebook; tablet = $tablet; dominio = [bool]$cs.PartOfDomain; bateria = [bool]$bat }
    cpu = @{ nome = ([string]$cpu.Name).Trim(); nucleos = [int]$cpu.NumberOfCores; threads = [int]$cpu.NumberOfLogicalProcessors; mhz = [int]$cpu.MaxClockSpeed }
    ram = @{ total = [math]::Round([double]$cs.TotalPhysicalMemory / 1GB, 1); usada = [math]::Round(([double]$os.TotalVisibleMemorySize - [double]$os.FreePhysicalMemory) / 1MB, 1); slots = $slots; ocupados = $pentes.Count }
    disco = @{ tipo = $tipoC; barramento = $barC; saude = $saudeC; livre = $livreC; total = $totalC }
    gpus = (Lista $gpus)
    tem = @{ impressora = ($impressoras.Count -gt 0); scanner = (TemClasse 'Image'); camera = $camera; smartcard = (TemClasse 'SmartCardReader'); bluetooth = (TemClasse 'Bluetooth'); biometria = (TemClasse 'Biometric'); rdp = $rdp; winrm = $winrm; ssh = $ssh; wsl = $wsl; hyperv = $hyperv; docker = $docker; historico_arquivos = $fh; office = (TemProg '^Microsoft (Office|365)'); visualstudio = (TemProg '^Visual Studio (Community|Professional|Enterprise|Build Tools)|^Microsoft Visual Studio'); onedrive_usado = $odUsado; onedrive = (Test-Path "$env:LOCALAPPDATA\Microsoft\OneDrive\OneDrive.exe") -or (Test-Path "$env:ProgramFiles\Microsoft OneDrive\OneDrive.exe"); brave = (TemProg '^Brave'); chrome = (TemProg '^Google Chrome'); firefox = (TemProg 'Mozilla Firefox'); edge = (Test-Path "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"); nvidia = [bool]($gpus | Where-Object { $_ -match 'NVIDIA' }); amd = [bool]($gpus | Where-Object { $_ -match 'AMD|Radeon' }); winget = [bool](Get-Command winget.exe -ErrorAction SilentlyContinue) }
    jogos = (Lista $jogos)
    oem_gamer = (Lista $oemGamer)
    antivirus = (Lista $av)
    defender = @{ tempo_real = [bool]$mp.RealTimeProtectionEnabled; ativo = [bool]$mp.AntivirusEnabled; modo = [string]$mp.AMRunningMode }
    energia = @{ plano = $plano }
    memoria = @{ pagefile_auto = [bool]$pfAuto; pagefile_config = [bool]$pf; compressao = $mm }
    sistema = @{ uptime_h = $uptime; reinicio_pendente = $pend; admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator); dono_explorer = [string]$dono; usuario = $env:USERNAME }
}
'''

MEDIDAS_PS = r'''
$os = Get-CimInstance Win32_OperatingSystem
$amostras = @()
for ($i = 0; $i -lt 4; $i++) {
    $p = Tenta { Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -Filter "Name='_Total'" -ErrorAction Stop }
    $q = Tenta { Get-CimInstance Win32_PerfFormattedData_Counters_ProcessorInformation -Filter "Name='_Total'" -ErrorAction Stop }
    if ($p) { $amostras += [pscustomobject]@{ cpu = [double]$p.PercentProcessorTime; kernel = [double]$p.PercentPrivilegedTime; perf = $(if ($q) { [double]$q.PercentProcessorPerformance } else { $null }); limite = $(if ($q) { [double]$q.PercentPerformanceLimit } else { $null }) } }
    Start-Sleep -Milliseconds 900
}
function Media($c) { $v = @($amostras | ForEach-Object { $_.$c } | Where-Object { $null -ne $_ }); if ($v.Count) { [math]::Round(($v | Measure-Object -Average).Average, 1) } else { $null } }
$temp = Tenta { $z = @(Get-CimInstance -Namespace root\wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction Stop | ForEach-Object { ($_.CurrentTemperature / 10) - 273.15 } | Where-Object { $_ -gt 5 -and $_ -lt 120 }); if ($z.Count) { [math]::Round(($z | Measure-Object -Maximum).Maximum, 0) } else { $null } } $null
$boot = Tenta { $e = Get-WinEvent -FilterHashtable @{ LogName = 'Microsoft-Windows-Diagnostics-Performance/Operational'; Id = 100 } -MaxEvents 1 -ErrorAction Stop; [int](([xml]$e.ToXml()).Event.EventData.Data | Where-Object Name -eq 'BootTime').'#text' } $null
$ld = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
$run = 0
foreach ($par in @(@('HKCU:\Software\Microsoft\Windows\CurrentVersion\Run','HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run'), @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run','HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run'), @('HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run','HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run32'))) {
    $it = Tenta { Get-Item $par[0] -ErrorAction Stop } $null
    $ap = Tenta { Get-Item $par[1] -ErrorAction Stop } $null
    if (-not $it) { continue }
    foreach ($n in $it.GetValueNames()) { if (-not $n) { continue }; $b = $null; if ($ap) { $b = $ap.GetValue($n) }; if (-not ($b -is [byte[]] -and $b.Length -gt 0 -and ($b[0] % 2) -eq 1)) { $run++ } }
}
foreach ($par in @(@("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup", 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder'), @("$env:ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp", 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder'))) {
    $ap = Tenta { Get-Item $par[1] -ErrorAction Stop } $null
    foreach ($f in @(Get-ChildItem -LiteralPath $par[0] -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne 'desktop.ini' })) { $b = $null; if ($ap) { $b = $ap.GetValue($f.Name) }; if (-not ($b -is [byte[]] -and $b.Length -gt 0 -and ($b[0] % 2) -eq 1)) { $run++ } }
}
Dado 'medidas' @{
    data = (Get-Date).ToString('s')
    cpu = (Media 'cpu'); kernel = (Media 'kernel'); desempenho = (Media 'perf'); limite = (Media 'limite')
    ram_total = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
    ram_usada = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / 1MB, 2)
    processos = @(Get-Process).Count
    servicos = @(Get-Service | Where-Object Status -eq 'Running').Count
    inicializacao = $run
    livre_c = [math]::Round($ld.FreeSpace / 1GB, 1)
    temperatura = $temp
    boot_s = $(if ($boot) { [math]::Round($boot / 1000, 1) } else { $null })
}
'''


def perfil_pc(ctx, forca=False):
    """O que este PC tem e usa (cache da sessão). Decide o que cada item recomenda."""
    if ctx.perfil and not forca:
        return ctx.perfil
    if not WINDOWS:
        ctx.perfil = PERFIL_VAZIO
        return ctx.perfil
    with Progresso(ctx.t, None, 'conhecendo o PC') as pr:
        s = roda_ps(ctx.t, PERFIL_PS, 'perfil', minutos=3, mostra=False, pr=pr)
    p = s.dados.get('perfil') or PERFIL_VAZIO
    ctx.perfil = p
    ctx.mult = fator_hardware(p)
    return p


PERFIL_VAZIO = {'so': {'win11': False, 'build': 0, 'nome': '', 'versao': '', 'edicao': ''},
                'pc': {'fabricante': '', 'modelo': '', 'notebook': False, 'tablet': False, 'dominio': False, 'bateria': False},
                'cpu': {}, 'ram': {'total': 8, 'usada': 0}, 'disco': {'tipo': 'SSD', 'livre': 100, 'total': 200},
                'gpus': [], 'tem': {}, 'jogos': [], 'oem_gamer': [], 'antivirus': [], 'defender': {},
                'energia': {}, 'memoria': {}, 'sistema': {}}


def pf(p, caminho, padrao=None):
    """Lê p['a']['b'] com 'a.b'."""
    v = p
    for k in caminho.split('.'):
        if not isinstance(v, dict):
            return padrao
        v = v.get(k)
    return padrao if v is None else v


def eh_hd(p):
    return str(pf(p, 'disco.tipo', '')).upper() == 'HDD'


def eh_ssd(p):
    return str(pf(p, 'disco.tipo', '')).upper() == 'SSD'


def joga(p):
    return bool(lista(pf(p, 'jogos', [])))


def fabricante(p):
    f = str(pf(p, 'pc.fabricante', '')).lower()
    for nome, padrao in (('dell', 'dell|alienware'), ('hp', 'hewlett|^hp'), ('lenovo', 'lenovo'), ('acer', 'acer'),
                         ('asus', 'asus'), ('msi', 'micro-star|msi'), ('samsung', 'samsung'), ('positivo', 'positivo')):
        if re.search(padrao, f):
            return nome
    return f.split()[0] if f else ''


def fator_hardware(p):
    m = 1.0
    if eh_hd(p) or pf(p, 'disco.tipo') in ('desconhecido', 'Unspecified', None):
        m *= 2
    if (pf(p, 'ram.total', 8) or 8) < 6:
        m *= 1.5
    return m


def mede(ctx, rotulo='medindo'):
    if not WINDOWS:
        return {}
    with Progresso(ctx.t, None, rotulo) as pr:
        s = roda_ps(ctx.t, MEDIDAS_PS, 'medidas', minutos=2, mostra=False, pr=pr)
    return s.dados.get('medidas') or {}


def salva_medida(m, nome):
    if m:
        grava_json(pasta('medidas') / f'{carimbo()}-{nome}.json', m)


def medidas_salvas():
    return sorted(pasta('medidas').glob('*.json'))


LINHAS_MEDIDA = [
    ('cpu', 'CPU em repouso', '%', 'menor'), ('kernel', 'tempo de kernel', '%', 'menor'),
    ('desempenho', 'clock (desempenho)', '%', 'maior'), ('ram_usada', 'RAM em uso', 'GB', 'menor'),
    ('processos', 'processos', '', 'menor'), ('servicos', 'serviços rodando', '', 'menor'),
    ('inicializacao', 'abrem com o Windows', '', 'menor'), ('livre_c', 'livre em C:', 'GB', 'maior'),
    ('temperatura', 'temperatura', '°C', 'menor'), ('boot_s', 'último boot', 's', 'menor'),
]


def _fmt_medida(v, un):
    if v in (None, ''):
        return '-'
    casas = 0 if un in ('', '%', '°C') else 1
    return br(v, casas) + (' ' + un if un else '')


def mostra_medidas(t, atual, antes=None):
    linhas = []
    for chave, rot, un, melhor in LINHAS_MEDIDA:
        a = atual.get(chave)
        if antes is None:
            linhas.append([rot, _fmt_medida(a, un)])
            continue
        b = antes.get(chave)
        dif = ''
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and a != b:
            d = a - b
            bom = (d < 0) == (melhor == 'menor')
            dif = t.p(('+' if d > 0 else '') + _fmt_medida(d, un), 'verde' if bom else 'amarelo')
        linhas.append([rot, _fmt_medida(b, un), _fmt_medida(a, un), dif])
    if antes is None:
        t.tabela(['medida', 'agora'], linhas, alinha='ed')
    else:
        t.tabela(['medida', 'antes', 'agora', 'mudou'], linhas, alinha='eddd')


def ferramenta_medir(ctx, args):
    t = ctx.t
    t.aba('CPU, kernel, clock, RAM, processos, serviços, inicialização, disco, temperatura e boot')
    t.paragrafo('Meça com o PC parado (sem programas abertos) para comparar de forma justa. As próprias consultas '
                'custam um pouco de CPU; o número em repouso real é um pouco menor.', 2, 'apagado')
    m = mede(ctx)
    if not m:
        t.erro('não consegui medir (só funciona no Windows).')
        return 1
    salvas = medidas_salvas()
    antes = le_json(salvas[0], None) if salvas else None
    salva_medida(m, 'medir')
    if not eh_admin():
        t.nota('  temperatura e tempo de boot só aparecem como administrador.')
    t.titulo('agora' if antes is None else f'comparado com a primeira medida ({salvas[0].name[:10]})')
    mostra_medidas(t, m, antes)
    if m.get('limite') is not None and m['limite'] < 95:
        t.aviso(f'O processador está limitado a {br(m["limite"], 0)}% (calor, carregador fraco ou plano de energia).')
    return 0


# ─────────────── raio-x: diagnóstico completo ───────────────

DIAG_PS = r'''
$dias60 = (Get-Date).AddDays(-60)
Vivo 'processos que mais gastam'
$a = @{}; foreach ($p in Get-Process) { try { $a[$p.Id] = $p.TotalProcessorTime.TotalMilliseconds } catch {} }
Start-Sleep -Seconds 4
$nucleos = [Environment]::ProcessorCount
$top = foreach ($p in Get-Process) { try { if ($a.ContainsKey($p.Id)) { [pscustomobject]@{ n = $p.ProcessName; cpu = [math]::Round(($p.TotalProcessorTime.TotalMilliseconds - $a[$p.Id]) / 40 / $nucleos, 1); mb = [math]::Round($p.WorkingSet64 / 1MB) } } } catch {} }
$porNome = $top | Group-Object n | ForEach-Object { [pscustomobject]@{ n = $_.Name; cpu = [math]::Round(($_.Group | Measure-Object cpu -Sum).Sum, 1); mb = [math]::Round(($_.Group | Measure-Object mb -Sum).Sum); qtd = $_.Count } }
Dado 'top_cpu' (Lista ($porNome | Sort-Object cpu -Descending | Select-Object -First 8))
Dado 'top_ram' (Lista ($porNome | Sort-Object mb -Descending | Select-Object -First 8))

Vivo 'quem chama o WMI'
$wmiCpu = ($porNome | Where-Object { $_.n -eq 'WmiPrvSE' } | Measure-Object cpu -Sum).Sum
$wmi = @()
if ($wmiCpu -gt 1.5) {
    $ev = @(Get-WinEvent -LogName 'Microsoft-Windows-WMI-Activity/Operational' -MaxEvents 400 -ErrorAction SilentlyContinue | Where-Object { $_.Id -eq 11 })
    $wmi = $ev | ForEach-Object { if ($_.Message -match 'ClientProcessId\s*=\s*(\d+)') { [int]$Matches[1] } } | Group-Object | Sort-Object Count -Descending | Select-Object -First 5 | ForEach-Object {
        $pp = Get-Process -Id ([int]$_.Name) -ErrorAction SilentlyContinue
        [pscustomobject]@{ processo = $(if ($pp) { $pp.ProcessName } else { 'pid ' + $_.Name }); consultas = $_.Count }
    }
}
Dado 'wmi' @{ cpu = [double]$wmiCpu; clientes = (Lista $wmi) }

Vivo 'inicializacao'
$ini = @()
foreach ($k in @(@('HKCU:\Software\Microsoft\Windows\CurrentVersion\Run','usuario'), @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run','todos'), @('HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run','todos (32 bits)'))) {
    $it = Tenta { Get-Item $k[0] -ErrorAction Stop }
    if ($it) { foreach ($n in $it.GetValueNames()) { if ($n) { $ini += [pscustomobject]@{ nome = $n; onde = $k[1]; cmd = [string]$it.GetValue($n) } } } }
}
foreach ($pp in @("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup", "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp")) {
    foreach ($f in @(Get-ChildItem -LiteralPath $pp -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne 'desktop.ini' })) { $ini += [pscustomobject]@{ nome = $f.BaseName; onde = 'pasta Inicializar'; cmd = $f.FullName } }
}
Dado 'inicializacao' (Lista $ini)

Vivo 'boot'
$kinds = @{ 101 = 'programa'; 102 = 'driver'; 103 = 'servico'; 106 = 'tarefa'; 109 = 'dispositivo' }
$bootEv = @(Get-WinEvent -FilterHashtable @{ LogName = 'Microsoft-Windows-Diagnostics-Performance/Operational'; Id = @(101,102,103,106,109); StartTime = $dias60 } -ErrorAction SilentlyContinue)
$bootRows = foreach ($e in $bootEv) { $d = @{}; ([xml]$e.ToXml()).Event.EventData.Data | ForEach-Object { $d[$_.Name] = $_.'#text' }; $nm = $d.FriendlyName; if (-not $nm) { $nm = $d.Name }; [pscustomobject]@{ tipo = $kinds[$e.Id]; nome = [string]$nm; ms = [int]$d.DegradationTime } }
Dado 'boot' (Lista ($bootRows | Group-Object tipo, nome | ForEach-Object { [pscustomobject]@{ tipo = $_.Group[0].tipo; nome = $_.Group[0].nome; vezes = $_.Count; s = [math]::Round(($_.Group | Measure-Object ms -Average).Average / 1000, 1) } } | Sort-Object s -Descending | Select-Object -First 8))
$bootT = @(Get-WinEvent -FilterHashtable @{ LogName = 'Microsoft-Windows-Diagnostics-Performance/Operational'; Id = 100 } -MaxEvents 5 -ErrorAction SilentlyContinue | ForEach-Object { [math]::Round([int](([xml]$_.ToXml()).Event.EventData.Data | Where-Object Name -eq 'BootTime').'#text' / 1000, 1) })
Dado 'boot_tempos' (Lista $bootT)

Vivo 'servicos de terceiros'
$terc = @(Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Running' -and $_.PathName -and $_.PathName -notmatch '\\Windows\\(system32|SysWOW64|servicing|Microsoft\.NET)\\|\\Windows Defender\\|\\Microsoft\\Edge|MsMpEng|NisSrv|SecurityHealth' } | ForEach-Object { [pscustomobject]@{ nome = $_.Name; exibe = $_.DisplayName; modo = $_.StartMode } })
Dado 'terceiros' (Lista $terc)

Vivo 'restos de programas'
$orfaos = @(Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | Where-Object { $_.PathName -and $_.PathName -notmatch 'svchost|\\Windows\\' } | ForEach-Object {
    $exe = $_.PathName; if ($exe -match '^"([^"]+)"') { $exe = $Matches[1] } elseif ($exe -match '^(\S+\.exe)') { $exe = $Matches[1] }
    if ($exe -match '\.exe$' -and -not (Test-Path -LiteralPath ([Environment]::ExpandEnvironmentVariables($exe)))) { [pscustomobject]@{ nome = $_.Name; exibe = $_.DisplayName; exe = $exe } }
})
Dado 'servicos_orfaos' (Lista $orfaos)

Vivo 'tarefas agendadas'
$suspeitas = @(); $orfas = @()
foreach ($tk in @(Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { $_.State -ne 'Disabled' })) {
    foreach ($ac in @($tk.Actions)) {
        $exe = [Environment]::ExpandEnvironmentVariables([string]$ac.Execute).Trim('"')
        if (-not $exe) { continue }
        $rep = $null
        foreach ($tr in @($tk.Triggers)) { if ($tr.Repetition -and $tr.Repetition.Interval) { $rep = [string]$tr.Repetition.Interval } }
        $curta = $false
        if ($rep -match '^PT(\d+)M$' -and [int]$Matches[1] -le 15) { $curta = $true }
        if ($rep -match '^PT\d+S$') { $curta = $true }
        if ($exe -match '\\AppData\\|\\Temp\\|\\Users\\Public\\' -and $exe -match '\.(exe|bat|cmd|vbs|js|ps1|scr)$') {
            $suspeitas += [pscustomobject]@{ tarefa = ($tk.TaskPath + $tk.TaskName); exe = $exe; repete = $rep; curta = $curta }
        }
        if ($exe -match '^[A-Za-z]:\\' -and $exe -match '\.exe$' -and $tk.TaskPath -notmatch '^\\Microsoft\\' -and -not (Test-Path -LiteralPath $exe)) {
            $orfas += [pscustomobject]@{ tarefa = ($tk.TaskPath + $tk.TaskName); exe = $exe }
        }
    }
}
Dado 'tarefas_suspeitas' (Lista $suspeitas)
Dado 'tarefas_orfas' (Lista $orfas)
$ameacas = @(Tenta { Get-MpThreatDetection -ErrorAction Stop | Where-Object { $_.InitialDetectionTime -gt $dias60 } } @())
Dado 'ameacas' @{ qtd = $ameacas.Count; ultimas = (Lista ($ameacas | Select-Object -First 5 | ForEach-Object { [pscustomobject]@{ quando = ([datetime]$_.InitialDetectionTime).ToString('s'); id = [string]$_.ThreatID } })) }

Vivo 'saude'
$smart = @(Tenta { Get-PhysicalDisk | ForEach-Object { $r = $_ | Get-StorageReliabilityCounter -ErrorAction SilentlyContinue; [pscustomobject]@{ disco = $_.FriendlyName; tipo = [string]$_.MediaType; saude = [string]$_.HealthStatus; temp = $r.Temperature; horas = $r.PowerOnHours; desgaste = $r.Wear; erros = $r.ReadErrorsTotal } } } @())
Dado 'smart' (Lista $smart)
$falha = [bool](Tenta { Get-CimInstance -Namespace root\wmi -ClassName MSStorageDriver_FailurePredictStatus -ErrorAction Stop | Where-Object PredictFailure } $null)
$crash = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; Id = 41,1001,6008; StartTime = $dias60 } -ErrorAction SilentlyContinue | Where-Object { $_.ProviderName -match 'Kernel-Power|BugCheck|EventLog' }).Count
$telaAzul = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; ProviderName = 'Microsoft-Windows-WER-SystemErrorReporting','BugCheck'; StartTime = $dias60 } -ErrorAction SilentlyContinue).Count
$discoErr = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; ProviderName = 'disk','Ntfs','storahci','stornvme','iaStorA'; Level = 1,2,3; StartTime = $dias60 } -ErrorAction SilentlyContinue).Count
$devs = @(Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue | Where-Object { $_.ConfigManagerErrorCode -ne 0 } | ForEach-Object { [pscustomobject]@{ nome = [string]$_.Name; classe = [string]$_.PNPClass; codigo = [int]$_.ConfigManagerErrorCode } })
$erros = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; Level = 1,2; StartTime = (Get-Date).AddDays(-7) } -ErrorAction SilentlyContinue | Group-Object ProviderName | Sort-Object Count -Descending | Select-Object -First 6 | ForEach-Object { [pscustomobject]@{ fonte = $_.Name; qtd = $_.Count } })
$bios = Tenta { Get-CimInstance Win32_BIOS } $null
$sb = Tenta { Confirm-SecureBootUEFI -ErrorAction Stop } $null
$bl = Tenta { [string](Get-BitLockerVolume -MountPoint 'C:' -ErrorAction Stop).ProtectionStatus } ''
$ultAtual = Tenta { (Get-HotFix | Where-Object InstalledOn | Sort-Object InstalledOn -Descending | Select-Object -First 1).InstalledOn.ToString('s') } ''
$trocas = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; ProviderName = 'Microsoft-Windows-UserModePowerService'; Id = 12; StartTime = (Get-Date).AddDays(-14) } -MaxEvents 30 -ErrorAction SilentlyContinue | ForEach-Object { if ($_.Message -match '([A-Za-z]:\\[^\r\n]+?\.exe)') { Split-Path $Matches[1] -Leaf } } | Group-Object | Sort-Object Count -Descending | Select-Object -First 4 | ForEach-Object { [pscustomobject]@{ processo = $_.Name; vezes = $_.Count } })
$bat = $null
if (Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue) {
    $arq = Join-Path $env:TEMP 'katharos-bateria.html'
    powercfg /batteryreport /output $arq | Out-Null
    $h = Get-Content $arq -Raw -ErrorAction SilentlyContinue
    $proj = $null; $cheia = $null
    if ($h -match '(?:DESIGN CAPACITY|CAPACIDADE DE DESIGN|CAPACIDADE DO PROJETO)</span></td><td>([\d\.,\s]+) mWh') { $proj = [double]($Matches[1] -replace '[^\d]', '') }
    if ($h -match '(?:FULL CHARGE CAPACITY|CAPACIDADE DE CARGA TOTAL|CAPACIDADE DE CARGA COMPLETA)</span></td><td>([\d\.,\s]+) mWh') { $cheia = [double]($Matches[1] -replace '[^\d]', '') }
    if ($proj -and $cheia) { $bat = [math]::Round($cheia / $proj * 100) }
    Remove-Item $arq -ErrorAction SilentlyContinue
}
$fw = @($devs | Where-Object { $_.classe -eq 'Firmware' })
Dado 'saude' @{ falha_iminente = $falha; desligamentos = $crash; telas_azuis = $telaAzul; erros_disco = $discoErr; dispositivos = (Lista $devs); erros_7d = (Lista $erros); bios = $(if ($bios) { [string]$bios.SMBIOSBIOSVersion } else { '' }); bios_data = $(if ($bios -and $bios.ReleaseDate) { ([datetime]$bios.ReleaseDate).ToString('s') } else { '' }); secure_boot = $sb; bitlocker = $bl; ultima_atualizacao = $ultAtual; trocas_plano = (Lista $trocas); bateria_saude = $bat; firmware_erro = ($fw.Count -gt 0) }

Vivo 'espaco em disco'
$L = $env:LOCALAPPDATA
$caches = @(
    @('temporarios do usuario', $env:TEMP), @('temporarios do Windows', "$env:WINDIR\Temp"),
    @('downloads do Windows Update', "$env:WINDIR\SoftwareDistribution\Download"),
    @('Otimizacao de Entrega', "$env:WINDIR\ServiceProfiles\NetworkService\AppData\Local\Microsoft\Windows\DeliveryOptimization\Cache"),
    @('relatorios de erro', "$env:ProgramData\Microsoft\Windows\WER"), @('dumps de travamento', "$L\CrashDumps"),
    @('logs de instalacao (Panther)', "$env:WINDIR\Panther"), @('logs do Windows (CBS)', "$env:WINDIR\Logs\CBS"),
    @('cache de shaders DirectX', "$L\D3DSCache"), @('cache de shaders NVIDIA', "$L\NVIDIA\DXCache"), @('cache OpenGL NVIDIA', "$L\NVIDIA\GLCache"), @('cache de shaders AMD', "$L\AMD\DxCache"),
    @('instaladores baixados guardados', "$L\Downloaded Installations"), @('miniaturas', "$L\Microsoft\Windows\Explorer"),
    @('cache do npm', "$L\npm-cache"), @('cache do pip', "$L\pip\Cache"), @('cache do Yarn', "$L\Yarn\Cache"),
    @('cache do Chrome', "$L\Google\Chrome\User Data\Default\Cache"), @('cache do Edge', "$L\Microsoft\Edge\User Data\Default\Cache"), @('cache do Brave', "$L\BraveSoftware\Brave-Browser\User Data\Default\Cache"),
    @('Windows.old', "$env:SystemDrive\Windows.old")
)
$cs = foreach ($c in $caches) { $b = TamanhoPasta $c[1]; if ($b -gt 50MB) { [pscustomobject]@{ nome = $c[0]; gb = [math]::Round($b / 1GB, 2) } } }
Dado 'caches' (Lista ($cs | Sort-Object gb -Descending))
$hib = Tenta { [math]::Round((Get-Item "$env:SystemDrive\hiberfil.sys" -Force -ErrorAction Stop).Length / 1GB, 1) } 0
$res = Tenta { [string](Get-WindowsReservedStorageState -ErrorAction Stop).ReservedStorageState } ''
Dado 'arquivos_sistema' @{ hiberfil_gb = $hib; armazenamento_reservado = $res }
$odProj = @()
if ($env:OneDrive -and (Test-Path -LiteralPath $env:OneDrive)) {
    $odProj = @(Get-ChildItem -LiteralPath $env:OneDrive -Directory -Recurse -Depth 4 -Filter node_modules -ErrorAction SilentlyContinue | Select-Object -First 10 | ForEach-Object { $_.Parent.FullName })
}
Dado 'onedrive_projetos' (Lista $odProj)

Vivo 'programas instalados'
$progs = @(Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -and -not $_.SystemComponent -and -not $_.ParentKeyName } | ForEach-Object { [string]$_.DisplayName } | Sort-Object -Unique)
Dado 'programas' (Lista $progs)
$apps = @(Tenta { Get-AppxPackage -ErrorAction Stop | Where-Object { -not $_.IsFramework -and $_.SignatureKind -ne 'System' -and -not $_.NonRemovable } | ForEach-Object { [string]$_.Name } } @())
Dado 'apps' (Lista $apps)
'''

QUEIXAS = [
    ('lento', 'lento ou travando no dia a dia'),
    ('boot', 'demora para ligar, muita coisa abrindo junto'),
    ('disco', 'disco cheio'),
    ('calor', 'esquenta demais ou ventoinha alta mesmo parado'),
    ('bateria', 'bateria dura pouco'),
    ('jogos', 'jogos com FPS baixo ou engasgando'),
    ('privacidade', 'propaganda, sugestões e IA que não pedi'),
    ('tudo', 'não sei, só quero que fique melhor'),
]


def pergunta_queixas(t, args):
    """A pergunta do começo: o que mais incomoda. Só prioriza; o diagnóstico olha tudo do mesmo jeito."""
    if getattr(args, 'queixas', None):
        return [q.strip() for q in args.queixas.split(',') if q.strip()]
    if not t.interativo or getattr(args, 'sim', False):
        return ['tudo']
    t.titulo('o que mais incomoda neste PC?')
    for i, (_, txt) in enumerate(QUEIXAS, 1):
        t.escreve(f'  {t.p(f"{i:>2}", "destaque", True)}  {t.p(txt, "texto")}')
    t.escreve()
    t.paragrafo('Pode marcar várias, separadas por espaço (ex.: 1 3). Isso só muda a ordem do que eu mostro: '
                'a análise é sempre completa.', 2, 'apagado')
    r = t.pergunta('queixas', '8')
    nums = [int(x) for x in re.findall(r'\d+', r) if 0 < int(x) <= len(QUEIXAS)]
    return [QUEIXAS[n - 1][0] for n in nums] or ['tudo']


class Achado:
    """Uma dor encontrada: impacto (3 alto, 2 médio, 1 baixo), evidência medida e o que fazer."""

    def __init__(self, impacto, queixas, titulo, evidencia, faz='', comando=''):
        self.impacto, self.queixas, self.titulo = impacto, set(queixas), titulo
        self.evidencia, self.faz, self.comando = evidencia, faz, comando


def analisa(p, m, d):
    """As regras do diagnóstico. p = perfil, m = medidas, d = dados do raio-x."""
    A = []
    ram_t = pf(p, 'ram.total', 0) or 0
    ram_u = m.get('ram_usada') or pf(p, 'ram.usada', 0) or 0
    livre = pf(p, 'disco.livre', 0) or 0
    total = pf(p, 'disco.total', 1) or 1
    ini = lista(d.get('inicializacao'))
    saude = d.get('saude') or {}

    if eh_hd(p):
        A.append(Achado(3, ['lento', 'boot', 'tudo', 'jogos'], 'O Windows está num HD mecânico',
                        'O disco do sistema é HDD: é o maior gargalo possível hoje.',
                        'Trocar por um SSD (de preferência com o Windows instalado do zero) é o maior ganho que existe. '
                        'Até lá: manter SysMain e Inicialização rápida, desfragmentar e reduzir escrita em segundo plano.', 'disco'))
    if ram_t and ram_t <= 4.5:
        A.append(Achado(3, ['lento', 'tudo', 'jogos'], 'Pouca memória RAM',
                        f'{gb(ram_t)} instalados; o Windows sozinho usa perto de 3 GB.',
                        'Aumentar para 8 GB ou mais. Enquanto isso: menos coisas na inicialização e em segundo plano.', 'inicializacao'))
    elif ram_t and ram_u / ram_t > 0.7:
        A.append(Achado(2, ['lento', 'tudo', 'jogos'], 'RAM quase cheia em repouso',
                        f'{gb(ram_u)} de {gb(ram_t)} em uso com o PC parado ({br(100 * ram_u / ram_t, 0)}%).',
                        'Tirar programas da inicialização e serviços de fabricante; se continuar alto, mais RAM.', 'inicializacao'))
    slots, ocup = pf(p, 'ram.slots', 0) or 0, pf(p, 'ram.ocupados', 0) or 0
    if slots > ocup and ocup == 1:
        A.append(Achado(1, ['jogos', 'lento', 'tudo'], 'Memória em canal único',
                        f'{ocup} de {slots} slots ocupados.',
                        'Um segundo pente igual ativa o dual channel, que ajuda muito o vídeo integrado.'))
    pct = 100 * livre / total
    if pct < 15:
        A.append(Achado(3 if pct < 8 else 2, ['disco', 'lento', 'tudo'], 'Pouco espaço livre em C:',
                        f'{gb(livre)} livres ({br(pct, 0)}%). Abaixo de 15% o Windows fica lento e as atualizações falham.',
                        'Limpar caches e temporários, e ver os arquivos grandes.', 'limpar'))
    caches = lista(d.get('caches'))
    soma = sum(c.get('gb', 0) for c in caches if c.get('nome') != 'Windows.old')
    if soma > 2:
        maiores = ', '.join(f'{c["nome"]} {gb(c["gb"])}' for c in caches[:3])
        A.append(Achado(2 if soma > 8 else 1, ['disco', 'tudo'], 'Caches e temporários acumulados',
                        f'{gb(soma)} que se recriam sozinhos. Maiores: {maiores}.', 'Limpar com segurança.', 'limpar'))
    if any(c.get('nome') == 'Windows.old' for c in caches):
        w = next(c['gb'] for c in caches if c.get('nome') == 'Windows.old')
        A.append(Achado(2, ['disco', 'tudo'], 'Windows.old ocupando espaço', f'{gb(w)} da versão anterior do Windows.',
                        'Pode sair se você não pretende voltar à versão anterior.', 'limpar'))
    n_ini = len(ini)
    if n_ini > 8:
        A.append(Achado(3 if n_ini > 14 else 2, ['boot', 'lento', 'tudo'], 'Muita coisa abrindo com o Windows',
                        f'{n_ini} itens na inicialização: ' + ', '.join(i.get('nome', '') for i in ini[:6]) + ('…' if n_ini > 6 else ''),
                        'Desligar o que não precisa abrir sozinho (o Gerenciador de Tarefas usa o mesmo mecanismo).', 'inicializacao'))
    boots = [b for b in lista(d.get('boot_tempos')) if isinstance(b, (int, float))]
    if boots and boots[0] > 60:
        culpados = ', '.join(f'{b.get("nome")} {br(b.get("s"), 1)} s' for b in lista(d.get('boot'))[:3])
        A.append(Achado(2, ['boot', 'tudo'], 'Boot demorado', f'Último boot: {br(boots[0], 0)} s. Mais atrasaram: {culpados or "sem registro"}.',
                        'Inicialização, serviços de terceiros com início atrasado e, em HD, otimização do boot.', 'disco'))
    ativos = [a for a in lista(p.get('antivirus')) if a.get('ativo')]
    terceiros = [a for a in ativos if 'defender' not in str(a.get('nome', '')).lower()]
    if len(ativos) > 1:
        A.append(Achado(3, ['lento', 'tudo', 'jogos'], 'Dois antivírus ativos ao mesmo tempo',
                        ', '.join(a['nome'] for a in ativos) + '. Eles brigam pelo disco e pela CPU.',
                        'Ficar com um só. A decisão é sua: o katharos só remove antivírus de fábrica (McAfee, Norton) se você marcar.', 'programas'))
    elif terceiros and re.search(r'mcafee|norton|avast|avg|avira', terceiros[0].get('nome', ''), re.I):
        A.append(Achado(2, ['lento', 'tudo'], 'Antivírus de fábrica ou gratuito pesado', terceiros[0]['nome'],
                        'O Defender do Windows protege bem e pesa menos. Remover só se você não pagou por ele.', 'programas'))
    if not ativos and not pf(p, 'defender.tempo_real'):
        A.append(Achado(3, ['tudo'], 'PC sem proteção em tempo real', 'Nenhum antivírus ativo.',
                        'Abra Segurança do Windows e ligue a proteção em tempo real (o katharos nunca desliga isso).'))
    cpu = m.get('cpu')
    if cpu is not None and cpu > 15:
        top = ', '.join(f'{x.get("n")} {br(x.get("cpu"), 1)}%' for x in lista(d.get('top_cpu'))[:3])
        A.append(Achado(2, ['lento', 'calor', 'bateria', 'tudo'], 'CPU ocupada com o PC parado',
                        f'{br(cpu, 0)}% em repouso (kernel {br(m.get("kernel"), 0)}%). Quem mais gasta: {top}.',
                        'Ver o que é cada um; serviços de fabricante e atualizadores costumam ser a causa.', 'servicos'))
    w = d.get('wmi') or {}
    if (w.get('cpu') or 0) > 2:
        cli = ', '.join(f'{c.get("processo")} ({c.get("consultas")})' for c in lista(w.get('clientes'))[:3])
        A.append(Achado(2, ['calor', 'bateria', 'lento', 'tudo'], 'WMI gastando CPU parado',
                        f'WmiPrvSE com {br(w.get("cpu"), 1)}% de CPU. Quem mais consulta: {cli or "não registrado"}.',
                        'Normalmente é software de fabricante (centrais de jogo, assistentes de suporte). Atualizar ou deixar em manual.', 'servicos'))
    if m.get('limite') is not None and m['limite'] < 95:
        A.append(Achado(2, ['calor', 'lento', 'jogos', 'tudo'], 'Processador sendo limitado',
                        f'Limite de desempenho em {br(m["limite"], 0)}%.',
                        'Calor (poeira, pasta térmica), carregador fraco ou plano de energia. Limpe as saídas de ar.'))
    if (m.get('temperatura') or 0) >= 80:
        A.append(Achado(2, ['calor', 'tudo'], 'Temperatura alta em repouso', f'{br(m["temperatura"], 0)} °C pela zona térmica do ACPI.',
                        'Limpar ventoinhas; em notebook, usar o plano "fresco" (mínimo de CPU 5% e turbo eficiente).', 'energia'))
    trocas = lista(saude.get('trocas_plano'))
    if trocas:
        A.append(Achado(1, ['calor', 'bateria', 'tudo'], 'Programa trocando o plano de energia',
                        ', '.join(f'{x.get("processo")} ({x.get("vezes")}x)' for x in trocas) + ' nos últimos 14 dias.',
                        'Centrais de fabricante forçam "Alto desempenho". Ajuste o perfil no app e use o plano de energia daqui.', 'energia'))
    if pf(p, 'pc.notebook') and saude.get('bateria_saude') and saude['bateria_saude'] < 70:
        A.append(Achado(2, ['bateria', 'tudo'], 'Bateria gasta', f'{saude["bateria_saude"]}% da capacidade original.',
                        'Abaixo de 60 a 70%, só a troca resolve. O plano "fresco" economiza o que dá.', 'energia'))
    if saude.get('falha_iminente'):
        A.append(Achado(3, ['tudo', 'lento'], 'DISCO PODE FALHAR', 'O próprio disco avisa falha iminente (SMART).',
                        'Faça backup agora e troque o disco.'))
    for s in lista(d.get('smart')):
        if (s.get('erros') or 0) > 0 or (s.get('desgaste') or 0) > 80:
            A.append(Achado(2, ['tudo'], f'Disco {s.get("disco")} com sinais de desgaste',
                            f'Erros de leitura: {s.get("erros")}, desgaste: {s.get("desgaste")}%.', 'Backup em dia e acompanhar.'))
    if (saude.get('desligamentos') or 0) >= 3:
        azuis = saude.get('telas_azuis') or 0
        A.append(Achado(2 if azuis else 1, ['tudo', 'lento'], 'Telas azuis ou desligamentos inesperados',
                        f'{saude["desligamentos"]} desligamentos sem aviso nos últimos 60 dias'
                        + (f', {azuis} com tela azul.' if azuis else ' (nenhuma tela azul: pode ser queda de energia ou botão de desligar segurado).'),
                        'Reparar o sistema e conferir drivers, fonte e temperatura.', 'reparar'))
    if (saude.get('erros_disco') or 0) > 5:
        A.append(Achado(2, ['tudo'], 'Erros de disco no registro de eventos', f'{saude["erros_disco"]} em 60 dias.', 'Verificar o disco (chkdsk).', 'reparar'))
    devs = lista(saude.get('dispositivos'))
    if devs:
        A.append(Achado(1, ['tudo'], 'Dispositivos com problema', ', '.join(f'{x.get("nome")} (código {x.get("codigo")})' for x in devs[:4]),
                        'Atualizar ou reinstalar o driver. Código 31 duplicado costuma ser resto de reinstalação.'))
    if saude.get('firmware_erro'):
        A.append(Achado(2, ['tudo'], 'Atualização de BIOS/firmware falhando',
                        'O dispositivo "System Firmware" está com erro (quase sempre por causa do BitLocker).',
                        'Atualize a BIOS pelo site do fabricante. Antes, suspenda o BitLocker você mesmo: '
                        'manage-bde -protectors -disable C: -RebootCount 3'))
    susp = lista(d.get('tarefas_suspeitas'))
    if susp:
        A.append(Achado(3 if any(x.get('curta') for x in susp) else 2, ['tudo', 'lento'], 'Tarefas agendadas suspeitas',
                        ', '.join(f'{x.get("tarefa")} → {x.get("exe")}' + (' (repete a cada poucos minutos)' if x.get('curta') else '') for x in susp[:3]),
                        'Programa rodando de AppData/Temp é padrão comum de malware. Confira cada um e faça uma verificação completa no Defender.'))
    ame = d.get('ameacas') or {}
    if ame.get('qtd'):
        A.append(Achado(2, ['tudo'], 'O Defender encontrou ameaças', f'{ame["qtd"]} nos últimos 60 dias.',
                        'Abra Segurança do Windows > Histórico de proteção e confira se foram removidas.'))
    orf = lista(d.get('servicos_orfaos')) + lista(d.get('tarefas_orfas'))
    if orf:
        A.append(Achado(1, ['tudo', 'boot'], 'Restos de programas desinstalados',
                        f'{len(orf)} serviços ou tarefas apontando para programas que não existem mais.',
                        'Desligar as tarefas e serviços órfãos.', 'servicos'))
    odp = lista(d.get('onedrive_projetos'))
    if odp:
        A.append(Achado(2, ['lento', 'disco', 'tudo'], 'Projetos de código dentro do OneDrive',
                        f'{len(odp)} pastas com node_modules sendo sincronizadas, ex.: {caminho_curto(odp[0])}.',
                        'Mover os projetos para fora do OneDrive (copie, confira e só depois apague o original).'))
    if (pf(p, 'sistema.uptime_h', 0) or 0) > 24 * 7:
        A.append(Achado(1, ['lento', 'tudo'], 'PC ligado há muitos dias', f'{br(pf(p, "sistema.uptime_h") / 24, 0)} dias sem reiniciar.',
                        'Reiniciar (não só suspender) limpa vazamentos de memória.'))
    if pf(p, 'sistema.reinicio_pendente'):
        A.append(Achado(1, ['tudo'], 'Atualização esperando reinício', 'O Windows pediu para reiniciar.', 'Reinicie quando puder.'))
    ult = saude.get('ultima_atualizacao')
    try:
        if ult and (datetime.now() - datetime.fromisoformat(ult[:19])).days > 45:
            A.append(Achado(2, ['tudo'], 'Windows sem atualizar há tempo', f'Última atualização instalada em {ult[:10]}.', 'Atualizar.', 'atualizar'))
    except ValueError:
        pass
    if not pf(p, 'memoria.pagefile_auto', True) and not pf(p, 'memoria.pagefile_config', True):
        A.append(Achado(2, ['lento', 'tudo'], 'Memória virtual desligada', 'Sem arquivo de paginação.',
                        'Ninguém recomenda desligar: programas fecham sozinhos sem ela. O pacote de disco volta para automático.', 'disco'))
    if pf(p, 'memoria.compressao') is False and ram_t < 16:
        A.append(Achado(1, ['lento', 'tudo'], 'Compressão de memória desligada', f'Com {gb(ram_t)}, ela ajuda.', 'O pacote de disco liga de novo.', 'disco'))
    if not pf(p, 'so.win11') and pf(p, 'so.build', 0):
        A.append(Achado(1, ['tudo'], 'Windows 10 sem suporte', 'O suporte comum acabou em outubro de 2025.',
                        'Atualize para o 11 se o processador for compatível; senão, o Defender e o navegador atualizados seguram por um tempo.'))
    if pf(p, 'pc.dominio'):
        A.append(Achado(1, ['tudo'], 'PC de empresa (domínio)', 'Políticas da empresa podem desfazer ou bloquear ajustes.',
                        'Use o modo seguro e combine com o TI antes de remover programas.'))
    plano = str(pf(p, 'energia.plano', '')).lower()
    if not pf(p, 'pc.notebook') and re.search(r'equilibrado|balanced|economia|power saver', plano):
        A.append(Achado(1, ['lento', 'jogos', 'tudo'], 'Desktop no plano Equilibrado', 'Plano ativo: ' + plano.split('(')[-1].rstrip(')'),
                        'Num desktop, o plano de desempenho mantém o clock alto sem custo de bateria.', 'energia'))
    if pf(p, 'pc.notebook') and re.search(r'alto desempenho|high performance|desempenho m|ultimate', plano):
        A.append(Achado(1, ['calor', 'bateria', 'tudo'], 'Notebook em plano de alto desempenho', 'Plano ativo: ' + plano.split('(')[-1].rstrip(')'),
                        'Esquenta e gasta bateria. O plano "fresco" (mínimo 5%, turbo eficiente) costuma resolver ventoinha alta.', 'energia'))
    if joga(p):
        A.append(Achado(1, ['jogos'], 'Ajustes para jogos disponíveis', 'Launchers encontrados: ' + ', '.join(lista(p.get('jogos'))),
                        'Modo de Jogo, prioridade dos jogos, Game DVR desligado e mais (cada um explicado).', 'jogos'))
    for nome in lista(p.get('oem_gamer')):
        A.append(Achado(1, ['calor', 'bateria', 'jogos'], f'{nome} instalado',
                        'Centrais de fabricante costumam forçar alto desempenho e consultar o WMI sem parar.',
                        'Use o perfil Equilibrado ou Silencioso nele no dia a dia; versões antigas pesam mais (atualize pelo site do fabricante).'))
    A.append(Achado(1, ['privacidade', 'tudo'], 'Telemetria, anúncios e IA do Windows',
                    'Ligados por padrão em toda instalação.', 'Desligar por políticas oficiais (reversível).', 'privacidade'))
    return A


def nota_pc(achados):
    pontos = 100 - sum({3: 14, 2: 6, 1: 2}[a.impacto] for a in achados)
    return max(5, min(100, pontos))


def relatorio_md(p, m, d, achados, queixas):
    L = [f'# Raio-x de {os.environ.get("COMPUTERNAME", "PC")}', '',
         f'Gerado em {datetime.now():%d/%m/%Y %H:%M} pelo katharos {VERSAO} (somente leitura). Nota: {nota_pc(achados)}/100.', '',
         '## Sistema', '', '| Item | Valor |', '|---|---|',
         f'| Modelo | {pf(p, "pc.fabricante", "")} {pf(p, "pc.modelo", "")} ({"notebook" if pf(p, "pc.notebook") else "desktop"}) |',
         f'| Windows | {pf(p, "so.nome", "")} {pf(p, "so.versao", "")} (build {pf(p, "so.build", "")}) |',
         f'| Processador | {pf(p, "cpu.nome", "")}, {pf(p, "cpu.nucleos", "")} núcleos e {pf(p, "cpu.threads", "")} threads |',
         f'| RAM | {gb(pf(p, "ram.total"))} ({pf(p, "ram.ocupados", "?")} de {pf(p, "ram.slots", "?")} slots) |',
         f'| Disco do sistema | {pf(p, "disco.tipo", "")} {pf(p, "disco.barramento", "")}, {gb(pf(p, "disco.livre"))} livres de {gb(pf(p, "disco.total"))} |',
         f'| Vídeo | {", ".join(lista(p.get("gpus")))} |',
         f'| Antivírus | {", ".join(a.get("nome", "") + (" (ativo)" if a.get("ativo") else "") for a in lista(p.get("antivirus")))} |',
         f'| BIOS | {(d.get("saude") or {}).get("bios", "")} ({str((d.get("saude") or {}).get("bios_data", ""))[:10]}) |', '',
         '## Medidas em repouso', '', '| Medida | Valor |', '|---|---|']
    for chave, rot, un, _ in LINHAS_MEDIDA:
        L.append(f'| {rot} | {_fmt_medida(m.get(chave), un)} |')
    nomes = dict(QUEIXAS)
    rel = [a for a in achados if a.queixas & set(queixas) and 'tudo' not in queixas]
    L += ['', '## Dores relatadas', '']
    if 'tudo' in queixas:
        L.append('- (nenhuma em especial)')
    for q in queixas:
        if q == 'tudo':
            continue
        cs = [a for a in achados if q in a.queixas]
        L.append(f'- **{nomes.get(q, q)}**: ' + ('; '.join(a.titulo for a in cs) if cs else 'não confirmada pelas medidas'))
    L += ['', '## O que foi encontrado, por impacto', '']
    for a in sorted(achados, key=lambda a: (-a.impacto, a.titulo)):
        if a in rel:
            continue
        L.append(f'- **{a.titulo}** ({["", "baixo", "médio", "alto"][a.impacto]}): {a.evidencia} {a.faz}'
                 + (f' Comando: `{a.comando}`.' if a.comando else ''))
    L += ['', '## Inicialização', ''] + [f'- {i.get("nome")} ({i.get("onde")})' for i in lista(d.get('inicializacao'))]
    L += ['', '## O que mais atrasou o boot (60 dias)', '']
    L += [f'- {b.get("tipo")}: {b.get("nome")}, {br(b.get("s"), 1)} s em média ({b.get("vezes")}x)' for b in lista(d.get('boot'))] or ['- sem registro']
    L += ['', '## Processos que mais gastam', '', '| Processo | CPU | RAM |', '|---|---|---|']
    L += [f'| {x.get("n")} | {br(x.get("cpu"), 1)}% | {x.get("mb")} MB |' for x in lista(d.get('top_ram'))]
    L += ['', '## Programas instalados', '', ', '.join(lista(d.get('programas')))]
    return '\n'.join(L) + '\n'


def ferramenta_raiox(ctx, args):
    t = ctx.t
    t.aba('diagnóstico completo, só leitura: o que deixa este PC lento e o que fazer')
    if not WINDOWS:
        t.erro('O katharos só funciona no Windows.')
        return 1
    queixas = pergunta_queixas(t, args)
    t.titulo('medindo')
    p = perfil_pc(ctx, forca=True)
    m = mede(ctx, 'medidas em repouso')
    with Progresso(t, None, 'analisando tudo') as pr:
        s = roda_ps(t, DIAG_PS, 'raiox', minutos=8, mostra=False, pr=pr, mult=ctx.mult)
    d = s.dados
    salva_medida(m, 'raiox')
    achados = analisa(p, m, d)
    ctx.achados = achados
    nota = nota_pc(achados)

    t.titulo('este PC')
    t.chaves([
        ('modelo', f'{pf(p, "pc.fabricante", "")} {pf(p, "pc.modelo", "")}'.strip() + (' · notebook' if pf(p, 'pc.notebook') else ' · desktop')),
        ('Windows', f'{pf(p, "so.nome", "")} {pf(p, "so.versao", "")}'.replace('Microsoft ', '')),
        ('processador', str(pf(p, 'cpu.nome', '')).replace('(R)', '').replace('(TM)', '')),
        ('RAM', f'{gb(pf(p, "ram.total"))} · {pf(p, "ram.ocupados", "?")} de {pf(p, "ram.slots", "?")} slots'),
        ('disco C:', f'{pf(p, "disco.tipo", "")} {pf(p, "disco.barramento", "")} · {gb(pf(p, "disco.livre"))} livres'),
        ('vídeo', ', '.join(lista(p.get('gpus')))),
    ])
    t.titulo('em repouso')
    mostra_medidas(t, m)
    if not eh_admin():
        t.nota('  temperatura e tempo de boot só aparecem como administrador.')
    t.titulo('nota')
    cor = 'verde' if nota >= 80 else ('amarelo' if nota >= 55 else 'vermelho')
    t.barra('saúde geral', nota, 100, t.p(f'{nota}/100', cor, True), cor)

    nomes = dict(QUEIXAS)
    if 'tudo' not in queixas:
        t.titulo('o que você relatou')
        for q in queixas:
            cs = [a for a in achados if q in a.queixas and a.impacto >= 2] or [a for a in achados if q in a.queixas]
            if cs:
                t.item('●', 'amarelo', nomes.get(q, q), t.p(pl(len(cs), 'causa'), 'amarelo'))
                for a in cs[:3]:
                    t.paragrafo('· ' + a.titulo, 6, 'sub')
            else:
                t.item('○', 'apagado', nomes.get(q, q), t.p('não confirmada pelas medidas', 'apagado'))
    t.titulo('o que encontrei' if 'tudo' in queixas else 'o que mais encontrei')
    ordem = sorted(achados, key=lambda a: (-(bool(a.queixas & set(queixas))), -a.impacto))
    for a in ordem:
        icone, c = {3: ('■', 'vermelho'), 2: ('●', 'amarelo'), 1: ('·', 'azul')}[a.impacto]
        t.item(icone, c, a.titulo, t.p(a.comando, 'destaque') if a.comando else '')
        t.paragrafo(a.evidencia, 6, 'sub')
        if a.faz:
            t.paragrafo(a.faz, 6, 'apagado')
    nome = f'raiox-{os.environ.get("COMPUTERNAME", "pc").lower()}-{datetime.now():%Y-%m-%d}.md'
    destino = Path(args.salvar) if getattr(args, 'salvar', None) else pasta('relatorios')
    destino.mkdir(parents=True, exist_ok=True)
    arq = destino / nome
    arq.write_text(relatorio_md(p, m, d, achados, queixas), encoding='utf-8')
    comandos = []
    for a in ordem:
        if a.comando and a.comando not in comandos:
            comandos.append(a.comando)
    t.titulo('resumo', caixa=True)
    t.chaves([('nota', t.p(f'{nota}/100', cor, True)), ('achados', str(len(achados))),
              ('alto impacto', t.p(str(sum(a.impacto == 3 for a in achados)), 'vermelho')),
              ('sugestão', ' · '.join(comandos[:6]) or 'nada')])
    t.relatorio(arq, recuo=2)
    if comandos and t.interativo and not args.teste:
        t.fecha_caixa()
        t.escreve()
        t.paragrafo('Quer abrir agora as telas sugeridas, uma de cada vez? Em cada uma você vê tudo explicado '
                    'e escolhe o que aplicar. s = sim, Enter = não', 2, 'apagado')
        if t.pergunta('abrir sugestões').strip().lower() in ('s', 'sim'):
            ctx.proximos = comandos
    return 0


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
                 sozinho=False, grupo=None, nota='', reverte=True, dados=None, conflita=()):
        self.id, self.titulo, self.explica, self.ganho, self.custo = id, titulo, explica, ganho, custo
        self.nivel, self.ps, self.py, self.minutos, self.sozinho = nivel, ps, py, minutos, sozinho
        self.grupo, self.nota, self.reverte, self.dados = grupo, nota, reverte, dados
        self.conflita = set(conflita)  # ids que não fazem sentido junto com este (marcar este desmarca aqueles)
        self.marcado = False


class Pacote:
    def __init__(self, nome, titulo, resumo, explica, itens, reversivel=True, admin=True):
        self.nome, self.titulo, self.resumo, self.explica = nome, titulo, resumo, explica
        self.itens, self.reversivel, self.admin = itens, reversivel, admin


PACOTES = {}


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


def desenha_itens(t, itens, completa=True):
    larg_nivel = 12
    for i, it in enumerate(itens, 1):
        marca = t.p('✓', 'verde', True) if it.marcado else t.p('○', 'apagado')
        nivel = t.p(NOME_NIVEL.get(it.nivel, ''), COR_NIVEL.get(it.nivel, 'apagado'))
        nome = corta(it.titulo, max(10, t.largura - 12 - larg_nivel))
        esq = f'  {marca} {t.p(f"{i:>2}", "destaque", True)}  {t.p(nome, "texto" if it.marcado else "sub")}'
        if vlen(esq) + vlen(nivel) + 2 <= t.largura:
            esq += ' ' * (t.largura - vlen(esq) - vlen(nivel)) + nivel
        t.escreve(esq)
        if completa:
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
            if not it.reverte:
                t.paragrafo('não volta com o "desfazer" (reinstale se precisar)', 8, 'apagado')
            t.escreve()


AJUDA_SELECAO = ('números marcam e desmarcam (ex.: 3 5 8-10) · t = todos · n = nenhum · '
                 's, e, x = o que o modo seguro, equilibrado ou extremo marca · c = explicações curtas ou completas · '
                 'l = listar de novo · Enter = seguir · 0 = voltar')


def escolhe_itens(ctx, itens, modo, args, titulo='o que fazer'):
    """A tela de escolha: tudo explicado, marcado conforme o modo; a pessoa ajusta. Devolve os marcados,
    ou None se voltou."""
    t = ctx.t
    marca_por_modo(itens, modo)
    completa = config('explicacao') != 'curta'
    t.titulo(f'{titulo} · {pl(len(itens), "item", "itens")}')
    desenha_itens(t, itens, completa)
    if getattr(args, 'sim', False) or not t.interativo:
        return [i for i in itens if i.marcado]
    while True:
        marcados = sum(i.marcado for i in itens)
        t.paragrafo(AJUDA_SELECAO, 2, 'apagado')
        r = t.pergunta(f'{marcados} de {len(itens)} marcados · modo {modo}').strip().lower()
        if r in ('', 'ok', 'seguir', 'aplicar'):
            return [i for i in itens if i.marcado]
        if r in ('0', 'v', 'voltar', 'q', 'sair'):
            return None
        mudou = True
        if r in ('t', 'todos'):
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
        elif r in ('?', 'ajuda', 'h'):
            mudou = False
            t.paragrafo('Cada item diz o que faz, o ganho e o custo. "seguro", "equilibrado" e "extremo" à direita '
                        'dizem a partir de qual modo ele vem marcado; "só se marcar" nunca vem marcado sozinho. '
                        'Quase tudo volta com o "desfazer".', 2, 'sub')
        else:
            nums = _numeros(r, len(itens))
            if not nums:
                mudou = False
                t.aviso(f'"{corta(r, 20)}" não é uma opção.')
            for n in nums:
                _alterna(itens, n - 1)
        if mudou:
            t.escreve()
            desenha_itens(t, itens, completa and r in ('c', 'completa', 'l', 'listar'))


# ─────────────── executar ───────────────

def _envolve(it):
    # cada item diz o próprio nome, roda protegido e, no fim, diz se mudou algo ou se já estava assim
    return ('Diz "secao" ' + psq(it.titulo) + '\n'
            '$__a = $script:MUDOU; $__p = $script:PLANOS\n'
            'try {\n' + it.ps + '\n} catch { Aviso (' + psq(it.titulo + ': ') + ' + $_.Exception.Message) }\n'
            'if ($TESTE) { if ($script:PLANOS -eq $__p) { Diz "nada" "ja esta assim" } }\n'
            'elseif ($script:MUDOU -gt $__a) { Feito ("feito ({0} {1})" -f ($script:MUDOU - $__a), $(if (($script:MUDOU - $__a) -eq 1) { "mudanca" } else { "mudancas" })) }\n'
            'else { Diz "nada" "ja estava assim" }\n')


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
    nome_bk = pac.nome if pac.reversivel else None
    with Progresso(t, len(itens), 'aplicando' if not teste else 'simulando') as pr:
        for bloco in blocos:
            it0 = bloco[0]
            if it0.py:
                t.escreve('  ' + t.p('◆', 'destaque') + ' ' + t.p(it0.titulo, 'texto', True))
                pr.atual = it0.titulo
                try:
                    r = it0.py(ctx, it0, pr, teste) or (0, 0)
                    feitos += r[0]
                    avisos += r[1] if len(r) > 1 else 0
                except Exception as e:  # um item com problema não derruba o resto
                    erros += 1
                    t.erro(f'{it0.titulo}: {e}')
                    LOG.escreve(f'ERRO {it0.titulo}: {e!r}')
                pr.avanca(it0.titulo)
                continue
            corpo = '\n'.join(_envolve(i) for i in bloco)
            minutos = sum(i.minutos for i in bloco)
            pr.atual = it0.titulo
            s = roda_ps(t, corpo, f'{pac.nome}-{it0.id}', minutos=minutos, pacote=nome_bk, teste=teste, pr=pr,
                        mult=ctx.mult, vigia_ocioso=True)
            feitos += len(s.feitos) + len(s.planos)
            avisos += len(s.avisos)
            erros += len(s.erros)
            if s.estourou:
                erros += 1
                t.erro(f'{it0.titulo}: passou do limite de {br(minutos * ctx.mult, 0)} min e foi encerrado; segui adiante.')
            pr.avanca(bloco[-1].titulo, len(bloco))
    if not teste:
        e = estado()
        pacs = e.setdefault('pacotes', {})
        reg = pacs.get(pac.nome) or {}
        ids = set(reg.get('itens', [])) | {i.id for i in itens}
        pacs[pac.nome] = {'quando': agora_iso(), 'itens': sorted(ids), 'revertido': False}
        salva_estado(e)
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
    corpo = r'''
Vivo 'ponto de restauracao'
try { Enable-ComputerRestore -Drive "$env:SystemDrive\" -ErrorAction Stop } catch {}
$k = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SystemRestore'
$antes = (Get-ItemProperty $k -Name SystemRestorePointCreationFrequency -ErrorAction SilentlyContinue).SystemRestorePointCreationFrequency
New-ItemProperty $k -Name SystemRestorePointCreationFrequency -Value 0 -PropertyType DWord -Force | Out-Null
try { Checkpoint-Computer -Description 'Antes do Katharos' -RestorePointType MODIFY_SETTINGS -ErrorAction Stop; Ok 'ponto de restauracao criado: "Antes do Katharos"' }
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
        t.paragrafo('Feche e abra o terminal com o botão direito > Executar como administrador, ou use o KATHAROS.bat.', 2, 'apagado')
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
    if not itens:
        t.ok('Nada a fazer aqui neste PC.')
        return 0
    modo = getattr(args, 'modo', None) or config('modo')
    escolhidos = escolhe_itens(ctx, itens, modo, args)
    if escolhidos is None:
        t.nota('voltou sem aplicar nada.')
        return 0
    if not escolhidos:
        t.nota('nada marcado.')
        return 0
    if args.teste:
        t.titulo('simulação (nada é alterado)')
        executa_itens(ctx, pac, escolhidos, teste=True)
        t.nota('modo teste: o que tem ○ azul seria mudado; o resto já está como deveria.')
        return 0
    if not t.confirma(f'Aplicar {pl(len(escolhidos), "item", "itens")} de {pac.titulo}?', sim=args.sim):
        t.nota('nada foi alterado.')
        return 0
    garante_ponto(ctx)
    inicio = time.time()
    t.titulo('aplicando')
    feitos, avisos, erros = executa_itens(ctx, pac, escolhidos)
    t.titulo('resumo', caixa=True)
    t.chaves([('itens', str(len(escolhidos))), ('mudanças', t.p(str(feitos), 'verde')),
              ('avisos', t.p(str(avisos), 'amarelo' if avisos else 'apagado')),
              ('erros', t.p(str(erros), 'vermelho' if erros else 'apagado')), ('tempo', duracao(time.time() - inicio))])
    if pac.reversivel:
        t.nota(f'para voltar: katharos desfazer {pac.nome}')
    return 1 if erros else 0


# ███████████████████████████████████████████████████████████████████████████
#
#   PARTE 3 · OS PACOTES
#   cada função devolve os itens que valem para este PC, com a recomendação ajustada ao que ele tem
#
# ███████████████████████████████████████████████████████████████████████████

def R(caminho, nome, valor, tipo='DWord'):
    """Uma linha de PowerShell que grava um valor no registro guardando o anterior."""
    if isinstance(valor, bytes):
        v = '([byte[]](' + ','.join(f'0x{b:02x}' for b in valor) + '))'
    elif isinstance(valor, str):
        v = psq(valor)
        if tipo == 'DWord':
            tipo = 'String'
    else:
        v = str(int(valor))
    return f'Set-Valor {psq(caminho)} {psq(nome)} {v} {psq(tipo)} | Out-Null'


def RR(*linhas):
    return '\n'.join(linhas)


def SVC(nomes, modo='disabled', parar=True):
    return f"foreach ($__s in {ps_lista(nomes)}) {{ Set-Servico $__s {psq(modo)}{' -Parar' if parar else ''} | Out-Null }}"


def TAREFAS(lista_tarefas):
    return f"foreach ($__t in {ps_lista(lista_tarefas)}) {{ Set-Tarefa $__t $false | Out-Null }}"


HKLM_POL = 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows'
HKCU_POL = 'HKCU:\\Software\\Policies\\Microsoft\\Windows'
CDM = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager'
ADV = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced'
EDGE_POL = 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Edge'


# ═══════════════════════════════ limpar ═══════════════════════════════

def _limpa_ps(rotulo, linhas):
    return ('$__livre = 0\n' + linhas +
            f'\nif ($__livre -gt 1MB) {{ if ($TESTE) {{ Plano ("{rotulo}: liberaria " + (MB $__livre)) }} '
            f'else {{ Feito ("{rotulo}: " + (MB $__livre) + " liberados") }} }}')


NAVEGADORES = [('Chrome', 'chrome', r'Google\Chrome\User Data'), ('Edge', 'msedge', r'Microsoft\Edge\User Data'),
               ('Brave', 'brave', r'BraveSoftware\Brave-Browser\User Data'), ('Opera', 'opera', r'..\Roaming\Opera Software\Opera Stable'),
               ('Vivaldi', 'vivaldi', r'Vivaldi\User Data')]


@pacote('limpar', 'limpeza', 'temporários, caches, restos de atualização e logs',
        'Apaga só o que o Windows e os programas recriam sozinhos. Arquivos seus não são tocados (para eles, use '
        '"grandes", que manda para a Lixeira). Arquivos em uso ficam onde estão.', reversivel=False)
def itens_limpar(ctx):
    nav = []
    for nome, proc, rel in NAVEGADORES:
        base = f'(Join-Path $env:LOCALAPPDATA {psq(rel)})'
        nav.append(f'''if (Get-Process {proc} -ErrorAction SilentlyContinue) {{ Info '{nome} aberto: cache dele fica para a proxima' }}
else {{ foreach ($__pf in @(Get-ChildItem -LiteralPath {base} -Directory -ErrorAction SilentlyContinue | Where-Object {{ $_.Name -match '^(Default|Profile \\d+)$' -or $_.Name -eq 'Opera Stable' }})) {{
  foreach ($__c in 'Cache','Code Cache','GPUCache','Service Worker\\CacheStorage') {{ $__livre += LimpaAntigos (Join-Path $__pf.FullName $__c) 0 }} }}
  if ('{nome}' -eq 'Opera') {{ $__livre += LimpaAntigos (Join-Path $env:LOCALAPPDATA 'Opera Software\\Opera Stable\\Cache') 0 }} }}''')
    nav.append('''if (Get-Process firefox -ErrorAction SilentlyContinue) { Info 'Firefox aberto: cache dele fica para a proxima' }
else { foreach ($__pf in @(Get-ChildItem (Join-Path $env:LOCALAPPDATA 'Mozilla\\Firefox\\Profiles') -Directory -ErrorAction SilentlyContinue)) { $__livre += LimpaAntigos (Join-Path $__pf.FullName 'cache2') 0 } }''')
    dev = '''foreach ($__c in @(@('npm','cache clean --force'), @('pip','cache purge'), @('yarn','cache clean'), @('pnpm','store prune'))) {
  $__e = Get-Command $__c[0] -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($__e) { if ($TESTE) { Plano ($__c[0] + ' ' + $__c[1]) } else { Vivo ($__c[0] + ' ' + $__c[1]); $__r = Roda 'cmd.exe' ('/c ' + $__c[0] + ' ' + $__c[1]) 10; if ($__r -eq 0) { Feito ($__c[0] + ': cache limpo') } } }
}'''
    sagerun = r'''
$__vc = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches'
$__fora = '^(DownloadsFolder|Recycle Bin|Previous Installations|BranchCache|Language Pack)$'
if ($TESTE) { Plano 'Limpeza de Disco do Windows (categorias do sistema, sem Downloads e Lixeira)' }
else {
  foreach ($__k in @(Get-ChildItem $__vc -ErrorAction SilentlyContinue)) {
    if ($__k.PSChildName -match __SO__) { New-ItemProperty -LiteralPath $__k.PSPath -Name StateFlags0911 -Value 2 -PropertyType DWord -Force -ErrorAction SilentlyContinue | Out-Null }
    else { Remove-ItemProperty -LiteralPath $__k.PSPath -Name StateFlags0911 -ErrorAction SilentlyContinue }
  }
  $__d0 = (Get-PSDrive C).Free
  Vivo 'Limpeza de Disco do Windows (pode demorar)'
  $__r = Roda 'cleanmgr.exe' '/sagerun:911' __MIN__
  $__d = (Get-PSDrive C).Free - $__d0
  if ($__r -eq -1) { Aviso 'a Limpeza de Disco passou do tempo e foi encerrada' }
  elseif ($__d -gt 1MB) { Feito ('Limpeza de Disco: ' + (MB $__d) + ' liberados') } else { Diz 'nada' 'nada a limpar' }
}'''
    return [
        Item('temp', 'temporários', 'Arquivos temporários seus e do Windows com mais de 2 dias (os recentes podem estar em uso).',
             'espaço; às vezes centenas de MB', 'nenhum', 1,
             _limpa_ps('temporarios', '$__livre += LimpaAntigos $env:TEMP 2\n$__livre += LimpaAntigos "$env:WINDIR\\Temp" 2')),
        Item('wu', 'downloads do Windows Update', 'Instaladores de atualizações já aplicadas. Não mexe se houver atualização '
             'esperando reinício.', 'espaço (pode passar de 1 GB)', 'nenhum', 1, _limpa_ps('Windows Update', r'''
$__pend = (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending') -or (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired')
if ($__pend) { Info 'ha atualizacao esperando reinicio: downloads mantidos' }
else {
  if (-not $TESTE) { & sc.exe stop wuauserv 2>$null | Out-Null; & sc.exe stop bits 2>$null | Out-Null; Start-Sleep 3 }
  $__livre += LimpaAntigos "$env:WINDIR\SoftwareDistribution\Download" 0
  if (-not $TESTE) { & sc.exe start wuauserv 2>$null | Out-Null; & sc.exe start bits 2>$null | Out-Null }
}'''), minutos=6),
        Item('do', 'cache da Otimização de Entrega', 'Pedaços de atualizações que o Windows guarda para mandar a outros PCs.',
             'espaço', 'nenhum', 1, r'''if ($TESTE) { Plano 'limpar cache da Otimizacao de Entrega' } else { try { Delete-DeliveryOptimizationCache -Force -ErrorAction Stop; Feito 'cache da Otimizacao de Entrega limpo' } catch { Diz 'nada' 'sem cache' } }'''),
        Item('erros', 'relatórios de erro e dumps', 'Relatórios de travamento já enviados ou antigos e cópias de memória de telas azuis.',
             'espaço (dumps podem ter GBs)', 'quem investiga uma tela azul antiga perde o arquivo', 1,
             _limpa_ps('relatorios de erro', r'''foreach ($__p in "$env:ProgramData\Microsoft\Windows\WER\ReportArchive","$env:ProgramData\Microsoft\Windows\WER\ReportQueue","$env:LOCALAPPDATA\Microsoft\Windows\WER","$env:LOCALAPPDATA\CrashDumps","$env:WINDIR\Minidump") { $__livre += LimpaAntigos $__p 7 }
if (Test-Path "$env:WINDIR\MEMORY.DMP") { $__l = (Get-Item "$env:WINDIR\MEMORY.DMP").Length; if (-not $TESTE) { Remove-Item "$env:WINDIR\MEMORY.DMP" -Force -ErrorAction SilentlyContinue }; $__livre += $__l }''')),
        Item('miniaturas', 'cache de miniaturas', 'O Windows recria as miniaturas das fotos e vídeos quando você abre as pastas.',
             'espaço; conserta miniaturas erradas', 'pastas de fotos demoram um pouco na primeira abertura', 1,
             _limpa_ps('miniaturas', r'''foreach ($__f in @(Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Windows\Explorer" -Filter 'thumbcache_*.db' -Force -ErrorAction SilentlyContinue)) { $__l = $__f.Length; if (-not $TESTE) { Remove-Item -LiteralPath $__f.FullName -Force -ErrorAction SilentlyContinue; if (-not (Test-Path -LiteralPath $__f.FullName)) { $__livre += $__l } } else { $__livre += $__l } }''')),
        Item('logs', 'logs antigos do Windows', 'Registros de instalação e manutenção com mais de 30 dias (CBS, DISM, Panther, '
             'MoSetup). O prompt original achou logs gigantes aqui.', 'espaço', 'nenhum no uso normal', 2,
             _limpa_ps('logs', r'''foreach ($__p in "$env:WINDIR\Logs\CBS","$env:WINDIR\Logs\DISM","$env:WINDIR\Logs\MoSetup","$env:WINDIR\Panther","$env:WINDIR\Logs\WindowsUpdate","$env:WINDIR\Logs\SIH") { $__livre += LimpaAntigos $__p 30 }''')),
        Item('navegadores', 'cache dos navegadores', 'Chrome, Edge, Brave, Opera, Vivaldi e Firefox, só os que estiverem fechados. '
             'Histórico, senhas, cookies e abas não são tocados.', 'espaço (às vezes vários GB)',
             'os sites carregam um pouco mais devagar na primeira visita', 2, _limpa_ps('navegadores', '\n'.join(nav)), minutos=6),
        Item('shaders', 'cache de shaders da placa de vídeo', 'DirectX, NVIDIA, AMD e Intel guardam shaders compilados. '
             'Quando ficam grandes ou corrompidos, causam engasgos.', 'espaço; corrige travadinhas de cache corrompido',
             'cada jogo recompila na primeira vez que abrir (pode engasgar alguns minutos)', 2,
             _limpa_ps('shaders', r'''foreach ($__p in "$env:LOCALAPPDATA\D3DSCache","$env:LOCALAPPDATA\NVIDIA\DXCache","$env:LOCALAPPDATA\NVIDIA\GLCache","$env:LOCALAPPDATA\AMD\DxCache","$env:LOCALAPPDATA\AMD\DxcCache","$env:LOCALAPPDATA\AMD\GLCache","$env:LOCALAPPDATA\AMD\VkCache","$env:LOCALAPPDATA\Intel\ShaderCache","$env:ProgramData\NVIDIA Corporation\NV_Cache") { $__livre += LimpaAntigos $__p 0 }''')),
        Item('instaladores', 'instaladores guardados por programas', 'Cópias de instaladores antigos que alguns programas guardam '
             '(Downloaded Installations, mais de 30 dias). O Alienware Command Center guarda ~1 GB por versão aqui.',
             'espaço', 'reparar esses programas pode pedir o instalador de novo', 2,
             _limpa_ps('instaladores', r'''$__livre += LimpaAntigos "$env:LOCALAPPDATA\Downloaded Installations" 30''')),
        Item('dev', 'caches de desenvolvimento', 'npm, pip, yarn e pnpm, pelos próprios comandos (só os que existem).',
             'espaço', 'a próxima instalação de pacotes baixa de novo', 2, dev, minutos=12) if any(shutil.which(x) for x in ('npm', 'pip', 'yarn', 'pnpm')) or not WINDOWS else None,
        Item('cleanmgr', 'Limpeza de Disco do Windows', 'A própria ferramenta do Windows, sem tocar em Downloads nem na Lixeira: '
             'restos de atualizações substituídas, arquivos de instalação, logs de upgrade.',
             'espaço (costuma liberar GBs depois de grandes atualizações)', 'demora (até 30 min em HD)', 2,
             sagerun.replace('__SO__', "'.'").replace('__MIN__', '30').replace("-match '.'", "-notmatch $__fora"), minutos=32, sozinho=True),
        Item('windowsold', 'Windows.old (versão anterior do Windows)', 'A cópia do Windows de antes da última grande atualização. '
             'Sai pela Limpeza de Disco, do jeito oficial.', 'espaço (10 a 30 GB)', 'não dá mais para voltar à versão anterior', 2,
             sagerun.replace('__SO__', "'^Previous Installations$'").replace('__MIN__', '30'), minutos=32, sozinho=True)
        if (not WINDOWS or Path(os.environ.get('SystemDrive', 'C:') + '\\Windows.old').exists()) else None,
        Item('componentes', 'componentes antigos do Windows (DISM)', 'Remove versões substituídas de componentes do sistema, '
             'do jeito oficial (DISM /StartComponentCleanup).', 'espaço (centenas de MB a alguns GB)', 'demora', 2,
             py=_py_dism(['/Online', '/Cleanup-Image', '/StartComponentCleanup'], 'componentes', 40)),
        Item('resetbase', 'componentes, de forma definitiva', 'O mesmo, com /ResetBase: apaga também as versões antigas que '
             'permitiriam desinstalar atualizações.', 'mais espaço', 'não dá mais para desinstalar atualizações já instaladas', 3,
             py=_py_dism(['/Online', '/Cleanup-Image', '/StartComponentCleanup', '/ResetBase'], 'componentes definitivo', 60), reverte=False),
        Item('reservado', 'armazenamento reservado do Windows', 'O Windows separa ~7 GB para atualizações. Desligar devolve esse espaço.',
             'cerca de 7 GB', 'com o disco cheio, atualizações grandes podem falhar', 3, r'''
$__st = Tenta { [string](Get-WindowsReservedStorageState -ErrorAction Stop).ReservedStorageState } ''
if ($__st -match 'Enabled') { if ($TESTE) { Plano 'desligar armazenamento reservado' } else { Guarda-Desfazer 'reservado' 'Set-WindowsReservedStorageState -State Enabled'; Set-WindowsReservedStorageState -State Disabled -ErrorAction Stop; $script:MUDOU++ } }''',
             minutos=5),
        Item('lixeira', 'esvaziar a Lixeira', 'Apaga de vez o que está na Lixeira de todas as unidades.', 'espaço',
             'é definitivo: não dá para recuperar', 0,
             _limpa_ps('Lixeira', r'''$__sh = New-Object -ComObject Shell.Application; $__n = @($__sh.NameSpace(10).Items()).Count
if ($__n -gt 0) { $__d0 = (Get-PSDrive C).Free; if (-not $TESTE) { Clear-RecycleBin -Force -ErrorAction SilentlyContinue; $__livre += [math]::Max(0, (Get-PSDrive C).Free - $__d0) } else { Plano ("esvaziar {0} itens da Lixeira" -f $__n) } }'''), reverte=False),
    ]


def _py_dism(argumentos, rotulo, minutos):
    def f(ctx, it, pr, teste):
        if teste:
            ctx.t.item('○', 'azul', 'DISM ' + ' '.join(argumentos), recuo=4, cor_nome='sub')
            return 1, 0
        antes = livre_c()
        cod, txt = roda_exe(['DISM.exe'] + argumentos, minutos, pr, ctx.mult)
        liberou = livre_c() - antes
        if cod == -1:
            ctx.t.aviso(f'{rotulo}: passou do tempo e foi encerrado.')
            return 0, 1
        if cod not in (0, 3010):
            ctx.t.aviso(f'{rotulo}: DISM saiu com código {cod}.')
            return 0, 1
        ctx.t.item('✓', 'verde', f'{rotulo}: concluído' + (f', {humano(liberou)} liberados' if liberou > 2**20 else ''), recuo=4, cor_nome='sub')
        return 1, 0
    return f


def livre_c():
    try:
        return shutil.disk_usage((os.environ.get('SystemDrive', 'C:') + '\\') if WINDOWS else '/').free
    except OSError:
        return 0


# ═══════════════════════════════ programas de fábrica ═══════════════════════════════

# (padrão do nome, nível, explicação, custo)
CATALOGO_PROGRAMAS = [
    (r'^McAfee', 1, 'Antivírus que vem de fábrica em teste. Briga com o Defender pelo disco e pela CPU.', 'se você pagou a assinatura, perde'),
    (r'^Norton (Security|360|AntiVirus|Internet Security|Online Backup|Utilities)', 2, 'Antivírus de fábrica ou em teste. Pesa mais que o Defender.', 'se você pagou a assinatura, perde'),
    (r'^(Avast|AVG) (Free )?Antivirus|^Avira (Security|Antivirus)', 3, 'Antivírus gratuito pesado; o Defender assume a proteção.', 'você perde esse antivírus'),
    (r'WildTangent|Booking\.com|Amazon Assistant|Dropbox (Promotion|20 GB)|ExpressVPN.*Trial', 1, 'Propaganda instalada de fábrica.', 'nenhum'),
    (r'^CyberLink (PowerDVD|Power2Go|PowerDirector|PhotoDirector|YouCam|Media Suite|LabelPrint|PowerRecover|Power Media Player|RichVideo)', 2,
     'Programas de mídia de fábrica (DVD, edição). O Windows já toca vídeo e música.', 'perde esses programas'),
    (r'^NewBlue|^proDAD', 2, 'Plugins de vídeo de fábrica.', 'perde os plugins'),
    (r'^Dell (SupportAssist|Customer Connect|Data Vault|Digital Delivery|Foundation Services|Product Registration|Help & Support|TechHub|Optimizer|Mobile Connect)|^Ajuda e Suporte da Dell|^Registro de produto Dell|DSC/AA Factory|^My ?Dell',
     2, 'Assistentes, telemetria e propaganda da Dell. O SupportAssist com o TechHub chega a 0,6 GB de RAM e consulta o WMI sem parar. '
        'O Dell Update fica, para drivers e BIOS.', 'perde o diagnóstico da Dell'),
    (r'^HP (JumpStart|Documentation|Connection Optimizer|Welcome|Insights|Privacy Settings|QuickDrop|Audio Switch|Sure Sense|Security Update Service)', 2,
     'Utilitários e telemetria da HP.', 'perde esses utilitários'),
    (r'^HP (Support Assistant|Wolf Security)', 3, 'Assistente de suporte e proteção extra da HP. O Defender continua protegendo.', 'perde o assistente e a proteção extra da HP'),
    (r'^Lenovo (Welcome|Now|Migration Assistant|Smart Meeting)', 2, 'Boas-vindas e propaganda da Lenovo. O Vantage (bateria e drivers) fica.', 'nenhum'),
    (r'^Acer (Jumpstart|Collection|Portal|Product Registration|Registration|Configuration Manager)|^App Explorer', 2, 'Propaganda e registro da Acer.', 'nenhum'),
    (r'^Acer Care Center', 3, 'Central de manutenção da Acer.', 'perde a central da Acer'),
    (r'^ASUS GiftBox|^ASUS Welcome', 2, 'Propaganda da ASUS.', 'nenhum'),
    (r'^Microsoft OneDrive$', 2, 'Sincronização do OneDrive. Desinstala pelo desinstalador oficial dele.', 'arquivos só na nuvem deixam de aparecer no PC (baixe antes o que precisar)'),
    (r'Teams Machine-Wide Installer|^Microsoft Teams \(classic\)', 2, 'Instalador antigo do Teams, que reinstala o Teams a cada login.', 'quem usa o Teams clássico perde'),
    (r'^Microsoft 365 - [a-z]{2}-[a-z]{2}$|^Microsoft OneNote - [a-z]{2}-[a-z]{2}$', 0, 'Office que vem de fábrica, normalmente em teste.', 'você perde o Office (se tiver licença, reinstala pela conta)'),
]


LISTA_PROGRAMAS_PS = r'''
$__ks = 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'
$__r = @(Get-ItemProperty $__ks -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -and ($_.UninstallString -or $_.QuietUninstallString) -and -not $_.SystemComponent } | ForEach-Object {
  [pscustomobject]@{ nome = [string]$_.DisplayName; chave = [string]$_.PSPath; desinst = [string]$_.UninstallString; quieto = [string]$_.QuietUninstallString; mb = [math]::Round([double]$_.EstimatedSize / 1024) }
})
Dado 'programas' (Lista $__r)
'''

REMOVE_PROGRAMA_PS = r'''
$__nome = «nome»; $__chave = «chave»; $__cmd = «desinst»; $__quieto = «quieto»
function _Sumiu([int]$Seg) { for ($i = 0; $i -lt [math]::Max(1, $Seg / 5); $i++) { if (-not (Test-Path -LiteralPath $__chave)) { return $true }; Start-Sleep 5 }; return -not (Test-Path -LiteralPath $__chave) }
if ($TESTE) { Plano ('desinstalar ' + $__nome); return }
Vivo ('desinstalando ' + $__nome)
$exe = $null; $normal = ''; $silencioso = ''
if ($__cmd -match '(?i)msiexec.*(\{[0-9A-F-]{36}\})') { $exe = 'msiexec.exe'; $normal = "/x $($Matches[1]) /norestart"; $silencioso = "/x $($Matches[1]) /qn /norestart" }
else {
  if ($__cmd -match '^"([^"]+)"\s*(.*)$' -or $__cmd -match '(?i)^(.+?\.exe)\s*(.*)$') { $exe = $Matches[1]; $normal = $Matches[2] }
  if ($__quieto -and ($__quieto -match '^"([^"]+)"\s*(.*)$' -or $__quieto -match '(?i)^(.+?\.exe)\s*(.*)$')) { $silencioso = $Matches[2]; $exe = $Matches[1] }
  elseif ($exe -match 'unins\d*\.exe$') { $silencioso = "$normal /VERYSILENT /SUPPRESSMSGBOXES /NORESTART" }
  elseif ($exe) { $silencioso = "$normal /S" }
}
if (-not $exe) { Aviso ("'{0}': desinstalador nao reconhecido; remova em Configuracoes > Aplicativos" -f $__nome); return }
if ($exe -ne 'msiexec.exe' -and -not (Test-Path -LiteralPath $exe)) { Aviso ("'{0}': o desinstalador nao existe mais (entrada orfa)" -f $__nome); return }
$c = Roda $exe $silencioso 6
if (_Sumiu 45) { Feito ("removido: {0}" -f $__nome); return }
Info ("'{0}' nao saiu em silencio (codigo {1}). Abri o desinstalador: clique nele e confirme (ate 10 min)." -f $__nome, $c)
$c = Roda $exe $normal 10 -Visivel
if (_Sumiu 30) { Feito ("removido: {0}" -f $__nome) } else { Aviso ("'{0}' continua instalado (codigo {1}). Erro 1628 = desinstalador quebrado: pode deixar." -f $__nome, $c) }
'''


def _py_remove_programa(ctx, it, pr, teste):
    d = it.dados
    corpo = ps_monta(REMOVE_PROGRAMA_PS, nome=psq(d['nome']), chave=psq(d['chave']), desinst=psq(d['desinst']), quieto=psq(d.get('quieto') or ''))
    s = roda_ps(ctx.t, corpo, 'programa', minutos=18, teste=teste, pr=pr, mult=1.0)
    return len(s.feitos) + len(s.planos), len(s.avisos)


@pacote('programas', 'programas de fábrica', 'bloatware do fabricante, antivírus de teste e propaganda',
        'Procura programas de fábrica conhecidos (Dell, HP, Lenovo, Acer, ASUS, McAfee, Norton, CyberLink...) e tenta desinstalar '
        'em silêncio. Se o programa não sair, abre o desinstalador dele para você clicar. Drivers de áudio, vídeo, Wi-Fi, '
        'touchpad e Bluetooth nunca entram na lista.', reversivel=False)
def itens_programas(ctx):
    s = roda_ps(ctx.t, LISTA_PROGRAMAS_PS, 'lista-programas', minutos=2, mostra=False)
    itens, vistos = [], set()
    for prog in lista(s.dados.get('programas')):
        nome = prog.get('nome', '')
        for padrao, nivel, explica, custo in CATALOGO_PROGRAMAS:
            if re.search(padrao, nome, re.I) and nome not in vistos:
                vistos.add(nome)
                n = nivel
                nota = ''
                if nome == 'Microsoft OneDrive' and pf(ctx.perfil, 'tem.onedrive_usado'):
                    n, nota = 0, 'sua pasta do OneDrive tem arquivos: não vem marcado'
                if re.search(r'antivirus|security|norton|mcafee|avast|avg|avira', nome, re.I):
                    av = [a for a in lista(pf(ctx.perfil, 'antivirus', [])) if a.get('ativo')]
                    if len(av) <= 1 and n == 1:
                        nota = 'é o único antivírus ativo além do Defender; o Defender assume quando ele sair'
                tam = f' · {br(prog["mb"], 0)} MB' if prog.get('mb') else ''
                itens.append(Item('prog:' + nome, nome, explica, 'menos programas rodando e menos espaço' + tam, custo, n,
                                  py=_py_remove_programa, nota=nota, reverte=False, dados=prog))
                break
    return itens


# ═══════════════════════════════ apps da Loja ═══════════════════════════════

# (padrão, nível, título, explicação, custo). Loja, Instalador de Aplicativos, Fotos, Calculadora, Bloco de Notas,
# Paint, Captura, Terminal, frameworks e apps de driver nunca entram.
CATALOGO_APPS = [
    (r'^Microsoft\.BingNews$', 1, 'Notícias', 'App de notícias do Bing.', 'nenhum'),
    (r'^Microsoft\.BingWeather$', 1, 'Clima', 'App de clima (o clima continua no navegador).', 'nenhum'),
    (r'^Microsoft\.BingSearch$', 1, 'Pesquisa Bing', 'Integração do Bing ao Windows.', 'nenhum'),
    (r'^Microsoft\.GetHelp$', 1, 'Obter Ajuda', 'App de ajuda da Microsoft.', 'nenhum'),
    (r'^Microsoft\.Getstarted$', 1, 'Dicas', 'Dicas do Windows.', 'nenhum'),
    (r'^Microsoft\.MicrosoftSolitaireCollection$', 1, 'Solitaire', 'Jogo com propaganda.', 'perde o jogo'),
    (r'^Microsoft\.Microsoft3DViewer$|^Microsoft\.Print3D$|^Microsoft\.MSPaint$|^Microsoft\.MixedReality\.Portal$', 1, 'apps 3D e realidade mista', 'Visualizador 3D, Paint 3D e Portal de Realidade Mista.', 'perde esses apps'),
    (r'^Microsoft\.WindowsFeedbackHub$', 1, 'Hub de Comentários', 'Envio de opinião à Microsoft.', 'nenhum'),
    (r'^Microsoft\.549981C3F5F10$', 1, 'Cortana', 'Assistente descontinuado.', 'nenhum'),
    (r'^Microsoft\.(Messaging|OneConnect|SkypeApp|Wallet|People)$', 1, 'apps antigos (Skype, Pessoas, Carteira)', 'Apps sem uso no Windows atual.', 'perde esses apps'),
    (r'^Clipchamp\.Clipchamp$', 1, 'Clipchamp', 'Editor de vídeo online pré-instalado.', 'perde o editor'),
    (r'Disney|SpotifyAB\.SpotifyMusic|king\.com\.|TikTok|Facebook|Instagram|AmazonVideo\.PrimeVideo|Netflix|Hulu|Twitter|LinkedIn|CandyCrush|BubbleWitch|MarchofEmpires|HiddenCity|Duolingo|PicsArt|Royal Revolt|Asphalt|Sling', 1,
     'apps de propaganda', 'Atalhos de propaganda e jogos que o Windows instala sozinho.', 'se você usa algum deles, reinstale pela Loja'),
    (r'^Microsoft\.MicrosoftOfficeHub$', 1, 'Microsoft 365 (Copilot)', 'Atalho do Office e do Copilot do Microsoft 365.', 'nenhum (o Office instalado continua)'),
    (r'^DellInc\.|^DB6EA5DB\.|^AD2F1837\.(HPJumpStarts|HPPrivacySettings|HPSupportAssistant|HPSystemInformation|HPQuickDrop|HPWorkWell|myHP|HPInc\.EnergyStar)|^AcerIncorporated\.(?!QuickAccess)|^B9ECED6F\.ASUSGIFTBOX', 2,
     'apps do fabricante', 'Apps de suporte, registro e propaganda do fabricante.', 'perde esses apps'),
    (r'^Microsoft\.WindowsMaps$', 2, 'Mapas', 'App de mapas offline.', 'perde os mapas offline'),
    (r'^microsoft\.windowscommunicationsapps$', 2, 'Email e Calendário (antigo)', 'Descontinuado pela Microsoft.', 'quem ainda usa perde'),
    (r'^Microsoft\.OutlookForWindows$', 2, 'Outlook (novo)', 'Novo Outlook gratuito.', 'quem usa perde (dá para usar no navegador)'),
    (r'^Microsoft\.Todos$|^Microsoft\.PowerAutomateDesktop$|^Microsoft\.Windows\.DevHome$|^MicrosoftCorporationII\.MicrosoftFamily$|^Microsoft\.MicrosoftJournal$|^Microsoft\.Whiteboard$|^Microsoft\.Office\.OneNote$', 2,
     'apps de produtividade pré-instalados', 'To Do, Power Automate, Dev Home, Family, Journal, Whiteboard e OneNote da Loja.', 'quem usa algum perde'),
    (r'^Microsoft\.WindowsAlarms$', 2, 'Relógio', 'Alarmes, timer e cronômetro.', 'perde alarme e timer do Windows'),
    (r'^Microsoft\.YourPhone$', 2, 'Vincular ao Celular', 'Liga o celular ao PC. Fica rodando em segundo plano.', 'perde mensagens e fotos do celular no PC'),
    (r'^MicrosoftTeams$|^MSTeams$', 2, 'Teams', 'Teams pessoal. Abre com o Windows.', 'quem usa perde (reinstala quando quiser)'),
    (r'^MicrosoftWindows\.Client\.WebExperience$', 2, 'Widgets', 'O painel de notícias e clima do Windows 11.', 'perde o painel de widgets'),
    (r'^Microsoft\.ZuneVideo$', 2, 'Filmes e TV', 'Player antigo de vídeo.', 'perde o app (o Media Player continua)'),
    (r'^Microsoft\.Edge\.GameAssist$', 2, 'Game Assist do Edge', 'Navegador por cima dos jogos.', 'nenhum'),
    (r'^Microsoft\.(GamingApp|XboxApp|Xbox\.TCUI|XboxGameOverlay|XboxGamingOverlay|XboxIdentityProvider|XboxSpeechToTextOverlay)$', 2,
     'Xbox', 'App Xbox, Game Bar e login do Xbox.', 'perde Game Pass, Game Bar (Win+G) e login Xbox em jogos'),
    (r'^Microsoft\.MicrosoftStickyNotes$', 3, 'Notas Autoadesivas', 'Notas na área de trabalho.', 'perde as notas (salve antes)'),
    (r'^Microsoft\.ZuneMusic$', 3, 'Media Player', 'O player de música e vídeo padrão do Windows 11.', 'você precisa de outro player (ex.: VLC)'),
    (r'^Microsoft\.WindowsSoundRecorder$', 3, 'Gravador de Som', 'Gravador de áudio.', 'perde o gravador'),
    (r'^MicrosoftCorporationII\.QuickAssist$', 3, 'Assistência Rápida', 'Acesso remoto para suporte.', 'ninguém consegue te ajudar por ele'),
    (r'^Microsoft\.WindowsCamera$', 0, 'Câmera', 'App de câmera. A webcam continua funcionando nos sites e no Teams.', 'perde o app de fotos pela webcam'),
]

LISTA_APPS_PS = r'''
$__a = @(Tenta { Get-AppxPackage -AllUsers -ErrorAction Stop } @(Get-AppxPackage))
$__p = @(Tenta { Get-AppxProvisionedPackage -Online -ErrorAction Stop } @())
$__n = @{}
foreach ($x in $__a) { if (-not $x.NonRemovable -and $x.SignatureKind -ne 'System' -and -not $x.IsFramework) { $__n[[string]$x.Name] = 1 } }
foreach ($x in $__p) { $__n[[string]$x.DisplayName] = 1 }
Dado 'apps' (Lista ([string[]]$__n.Keys))
'''

REMOVE_APP_PS = r'''
$__n = «nome»
if ($TESTE) { Plano ('remover app ' + $__n); return }
Vivo ('removendo ' + $__n)
$__pk = @(Get-AppxPackage -AllUsers -Name $__n -ErrorAction SilentlyContinue | Where-Object { -not $_.NonRemovable })
foreach ($x in $__pk) { try { Remove-AppxPackage -Package $x.PackageFullName -AllUsers -ErrorAction Stop } catch { try { Remove-AppxPackage -Package $x.PackageFullName -ErrorAction Stop } catch { Aviso ($__n + ': ' + $_.Exception.Message) } } }
foreach ($x in @(Get-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue | Where-Object DisplayName -eq $__n)) { try { Remove-AppxProvisionedPackage -Online -PackageName $x.PackageName -ErrorAction Stop | Out-Null } catch {} }
if (Get-AppxPackage -Name $__n -ErrorAction SilentlyContinue) { Aviso ('continua instalado: ' + $__n) } else { Feito ('removido: ' + $__n) }
'''


def _py_remove_apps(ctx, it, pr, teste):
    feitos = avisos = travou = 0
    for nome in it.dados:
        if travou >= 3:
            ctx.t.aviso('3 remoções travaram seguidas; parei. Reinicie e rode de novo para o resto.')
            break
        s = roda_ps(ctx.t, ps_monta(REMOVE_APP_PS, nome=psq(nome)), 'app', minutos=3, teste=teste, pr=pr, mult=1.0)
        travou = travou + 1 if s.estourou else 0
        if s.estourou:
            ctx.t.aviso(f'{nome}: travou e foi encerrado (acontece com o Remove-AppxPackage).')
        feitos += len(s.feitos) + len(s.planos)
        avisos += len(s.avisos) + (1 if s.estourou else 0)
    return feitos, avisos


@pacote('apps', 'apps da Loja', 'apps pré-instalados que quase ninguém usa',
        'Remove para todos os usuários e também da instalação padrão (contas novas não recebem de novo). '
        'Apps de sistema e protegidos pelo Windows nunca entram. Cada remoção tem limite de 3 minutos, porque às vezes ela trava.',
        reversivel=False)
def itens_apps(ctx):
    s = roda_ps(ctx.t, LISTA_APPS_PS, 'lista-apps', minutos=3, mostra=False)
    instalados = lista(s.dados.get('apps'))
    itens = []
    for padrao, nivel, titulo, explica, custo in CATALOGO_APPS:
        achados = sorted(n for n in instalados if re.search(padrao, n, re.I))
        if not achados:
            continue
        nota = ''
        if titulo == 'Xbox' and joga(ctx.perfil):
            nivel, nota = 0, 'tem jogos instalados (' + ', '.join(lista(ctx.perfil.get('jogos'))) + '): não vem marcado'
        if titulo == 'Câmera' and not pf(ctx.perfil, 'tem.camera'):
            nivel = 3
        det = ', '.join(a.split('.')[-1] for a in achados[:4]) + ('…' if len(achados) > 4 else '')
        itens.append(Item('app:' + titulo, titulo, explica + (f' ({det})' if len(achados) > 1 or titulo.startswith('apps') else ''),
                          'menos coisas em segundo plano e no menu', custo, nivel, py=_py_remove_apps, nota=nota,
                          reverte=False, dados=achados))
    conhecidos = {a for i in itens for a in i.dados}
    nunca = re.compile(r'Store|DesktopAppInstaller|Photos|Calculator|Notepad|Paint$|ScreenSketch|Terminal|VCLibs|NET\.|UI\.Xaml|'
                       r'WindowsAppRuntime|Services\.Store|SecHealthUI|HEIF|HEVC|VP9|WebMedia|WebpImage|RawImage|AV1|Realtek|Intel|NVIDIA|AMD|'
                       r'Dolby|DTS|Waves|Synaptics|ELAN|Lenovo(Companion|Utility)|E046963F|E0469640|QuickAccess|Wacom|Client\.|Windows\.(Shell|Start|Search|Cortana)|'
                       r'Microsoft\.Windows\.|MicrosoftWindows\.|AAD\.|AccountsControl|LockApp|Win32WebViewHost|BioEnrollment|CredDialogHost|ECApp|'
                       r'OOBE|ParentalControls|PeopleExperienceHost|XGpuEjectDialog|CapturePicker|PinningConfirmation|AsyncTextService|ApplicationCompatibility|'
                       r'Edge$|MicrosoftEdge|WidgetsPlatformRuntime|StorePurchaseApp|Winget|Sense|Extension|Runtime|WinAppRuntime|DirectX|LanguageExperience|'
                       r'GamingServices|OneDriveSync|Xaml|Framework|Codec|Claude|Anthropic', re.I)
    for nome in sorted(n for n in instalados if n not in conhecidos and not nunca.search(n)):
        itens.append(Item('app:' + nome, nome.split('.')[-1] if '.' in nome else nome, f'App instalado ({nome}). Não está na lista de '
                          'conhecidos: remova só se souber o que é.', 'menos um app', 'risco desconhecido', 0, py=_py_remove_apps,
                          reverte=False, dados=[nome]))
    return itens


# ═══════════════════════════════ IA do Windows ═══════════════════════════════

@pacote('ia', 'IA do Windows', 'Copilot, Recall, IA no Paint, Bloco de Notas, Edge e Office',
        'Desliga a IA só por meios oficiais: políticas documentadas pela Microsoft, desinstaladores e Remove-AppxPackage. '
        'Nada de scripts "milagrosos". No Windows Home, atualizações podem trazer o Copilot de volta; a manutenção semanal reaplica. '
        'Algumas tarefas de IA são protegidas pelo sistema e ficam.')
def itens_ia(ctx):
    w = f'{HKLM_POL}\\WindowsAI'
    wu = f'{HKCU_POL}\\WindowsAI'
    win11 = pf(ctx.perfil, 'so.win11', True)
    return [
        Item('copilot', 'Copilot desligado', 'Política oficial que desliga o Copilot do Windows e tira o botão da barra.',
             'menos um app em segundo plano', 'perde o Copilot do Windows', 1,
             RR(R(f'{HKCU_POL}\\WindowsCopilot', 'TurnOffWindowsCopilot', 1), R(f'{HKLM_POL}\\WindowsCopilot', 'TurnOffWindowsCopilot', 1),
                R(ADV, 'ShowCopilotButton', 0),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Shell Extensions\\Blocked', '{CB3B0003-8088-4EDE-8769-8B354AB2FF8C}', '', 'String'))),
        Item('copilot-app', 'remover o app Copilot', 'Desinstala o app Copilot (da Loja e, se houver, a versão Win32 pelo desinstalador dele).',
             'menos espaço e processos', 'perde o app', 2, r'''
foreach ($__n in 'Microsoft.Copilot','Microsoft.Windows.Ai.Copilot.Provider') {
  foreach ($x in @(Get-AppxPackage -AllUsers -Name $__n -ErrorAction SilentlyContinue | Where-Object { -not $_.NonRemovable })) { if ($TESTE) { Plano ('remover ' + $__n) } else { try { Remove-AppxPackage -Package $x.PackageFullName -AllUsers -ErrorAction Stop; $script:MUDOU++ } catch { Aviso ($__n + ': ' + $_.Exception.Message) } } }
}
$__w = @(Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -eq 'Microsoft Copilot' })
foreach ($x in $__w) { if ($TESTE) { Plano 'desinstalar Microsoft Copilot (Win32)' } else { $u = [string]$x.QuietUninstallString; if (-not $u) { $u = [string]$x.UninstallString }; if ($u -match '^"([^"]+)"\s*(.*)$') { $r = Roda $Matches[1] $Matches[2] 5; $script:MUDOU++ } } }''',
             minutos=8, reverte=False),
        Item('recall', 'Recall e análise de IA desligados', 'Políticas oficiais: Recall (fotos da tela), Clique para Fazer, '
             'agente nas Configurações e conectores de agentes desligados, para a máquina e para você.',
             'privacidade; menos processamento em segundo plano', 'perde esses recursos de IA', 1,
             RR(R(w, 'AllowRecallEnablement', 0), R(w, 'DisableAIDataAnalysis', 1), R(w, 'TurnOffSavingSnapshots', 1), R(wu, 'TurnOffSavingSnapshots', 1), R(w, 'DisableClickToDo', 1),
                R(w, 'DisableSettingsAgent', 1), R(w, 'ConfigureAgentConnectors', 2), R(wu, 'DisableAIDataAnalysis', 1),
                R(wu, 'DisableClickToDo', 1))) if win11 else None,
        Item('recall-recurso', 'recurso opcional Recall desativado', 'Desativa o componente Recall pelo DISM (sem apagar: dá para ligar de novo).',
             'tira o componente do sistema', 'nenhum para quem não usa', 2, r'''
$__f = Tenta { Get-WindowsOptionalFeature -Online -FeatureName Recall -ErrorAction Stop } $null
if ($__f -and [string]$__f.State -eq 'Enabled') { if ($TESTE) { Plano 'desativar recurso Recall' } else { Guarda-Desfazer 'recall' 'Enable-WindowsOptionalFeature -Online -FeatureName Recall -NoRestart | Out-Null'; Disable-WindowsOptionalFeature -Online -FeatureName Recall -NoRestart -ErrorAction Stop | Out-Null; $script:MUDOU++ } }''',
             minutos=10) if win11 else None,
        Item('paint', 'IA no Paint', 'Políticas oficiais: Criador de Imagens, Cocreator e Preenchimento Generativo desligados.',
             'menos chamadas à nuvem', 'perde esses recursos do Paint', 2,
             RR(*(R('HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Paint', n, 1) for n in ('DisableImageCreator', 'DisableCocreator', 'DisableGenerativeFill')))) if win11 else None,
        Item('notepad', 'IA no Bloco de Notas', 'Política oficial que desliga reescrever e resumir com IA no Bloco de Notas.',
             'Bloco de Notas mais simples', 'perde a reescrita com IA', 2, R('HKLM:\\SOFTWARE\\Policies\\WindowsNotepad', 'DisableAIFeatures', 1)) if win11 else None,
        Item('edge-ia', 'IA no Edge', 'Políticas do Edge: sem ícone do Copilot, sem leitura da página pelo Copilot, sem escrita com IA '
             'e sem busca no histórico por IA. O Edge passa a mostrar "Gerenciado pela sua organização".',
             'Edge mais leve e privado', 'perde o Copilot no Edge; aparece o aviso de gerenciado', 2,
             RR(R(EDGE_POL, 'Microsoft365CopilotChatIconEnabled', 0), R(EDGE_POL, 'CopilotPageContext', 0),
                R(EDGE_POL, 'ComposeInlineEnabled', 0), R(EDGE_POL, 'EdgeHistoryAISearchEnabled', 0),
                R(EDGE_POL, 'GenAILocalFoundationalModelSettings', 1), R(EDGE_POL, 'HubsSidebarEnabled', 0),
                R(EDGE_POL, 'EdgeEntraCopilotPageContext', 0))) if pf(ctx.perfil, 'tem.edge', True) else None,
        Item('office-ia', 'Microsoft 365 Copilot e IA do Office', 'Remove os pacotes Microsoft 365 (Copilot), ActionsServer e '
             'WritingAssistant, desliga a tarefa Office Actions Server e tira "Perguntar ao Microsoft 365 Copilot" do menu do botão direito.',
             'menos processos do Office em segundo plano', 'perde o Copilot do Office', 2, RR(r'''
foreach ($__n in 'Microsoft.MicrosoftOfficeHub','Microsoft.Office.ActionsServer','Microsoft.WritingAssistant') {
  foreach ($x in @(Get-AppxPackage -AllUsers -Name $__n -ErrorAction SilentlyContinue | Where-Object { -not $_.NonRemovable })) { if ($TESTE) { Plano ('remover ' + $__n) } else { try { Remove-AppxPackage -Package $x.PackageFullName -AllUsers -ErrorAction Stop; $script:MUDOU++ } catch { Aviso ($__n + ': ' + $_.Exception.Message) } } }
}
Desliga-Tarefas '\\Microsoft\\Office\\Office Actions Server' | Out-Null''',
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Shell Extensions\\Blocked', '{DB6BACB1-FC31-4B28-9C53-7240A4F98404}', '', 'String')),
             minutos=6),
        Item('digitacao', 'coleta de digitação e tinta', 'O Windows deixa de aprender com o que você digita e escreve à mão '
             'e de colher contatos para isso.', 'privacidade', 'sugestões de digitação ficam menos personalizadas', 2,
             RR(R('HKCU:\\Software\\Microsoft\\InputPersonalization', 'RestrictImplicitInkCollection', 1),
                R('HKCU:\\Software\\Microsoft\\InputPersonalization', 'RestrictImplicitTextCollection', 1),
                R('HKCU:\\Software\\Microsoft\\InputPersonalization\\TrainedDataStore', 'HarvestContacts', 0),
                R('HKCU:\\Software\\Microsoft\\Personalization\\Settings', 'AcceptedPrivacyPolicy', 0))),
        Item('ia-servico', 'serviço e tarefas de IA', 'Serviço WSAIFabricSvc desativado e tarefas em \\Microsoft\\Windows\\WindowsAI '
             'desligadas (menos a PolicyConfiguration, que aplica as políticas acima).', 'menos processos parados gastando',
             'nenhum para quem não usa IA do Windows', 3,
             RR(SVC(['WSAIFabricSvc']), "Desliga-Tarefas '^\\\\Microsoft\\\\Windows\\\\WindowsAI\\\\' 'PolicyConfiguration' | Out-Null")) if win11 else None,
    ]


# ═══════════════════════════════ inicialização ═══════════════════════════════

LISTA_INICIO_PS = r'''
$__r = New-Object System.Collections.Generic.List[object]
$__ap = @{
  'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run'
  'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run' = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run'
  'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run' = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run32'
}
function _Ligado([string]$Ap, [string]$Nome) { $b = Tenta { (Get-Item -LiteralPath $Ap -ErrorAction Stop).GetValue($Nome) } $null; if ($b -is [byte[]] -and $b.Length -gt 0) { return (($b[0] % 2) -eq 0) }; return $true }
foreach ($k in $__ap.Keys) {
  $it = Tenta { Get-Item -LiteralPath $k -ErrorAction Stop } $null
  if (-not $it) { continue }
  foreach ($n in $it.GetValueNames()) { if ($n) { $__r.Add([pscustomobject]@{ tipo = 'run'; nome = $n; cmd = [string]$it.GetValue($n); ap = $__ap[$k]; ligado = (_Ligado $__ap[$k] $n) }) } }
}
foreach ($par in @(@("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup", 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder'), @("$env:ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp", 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder'))) {
  foreach ($f in @(Get-ChildItem -LiteralPath $par[0] -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne 'desktop.ini' })) {
    $__r.Add([pscustomobject]@{ tipo = 'pasta'; nome = $f.Name; cmd = $f.FullName; ap = $par[1]; ligado = (_Ligado $par[1] $f.Name) })
  }
}
$__sa = 'HKCU:\Software\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion\AppModel\SystemAppData'
foreach ($pkg in @(Get-ChildItem -LiteralPath $__sa -ErrorAction SilentlyContinue)) {
  foreach ($tk in @(Get-ChildItem -LiteralPath $pkg.PSPath -ErrorAction SilentlyContinue | Where-Object { $null -ne (Get-ItemProperty -LiteralPath $_.PSPath -Name State -ErrorAction SilentlyContinue) })) {
    $st = (Get-ItemProperty -LiteralPath $tk.PSPath -Name State).State
    $__r.Add([pscustomobject]@{ tipo = 'loja'; nome = ($pkg.PSChildName -replace '_.*$', '') + ' (' + $tk.PSChildName + ')'; cmd = $pkg.PSChildName; ap = $tk.PSPath; ligado = ($st -eq 2 -or $st -eq 4) })
  }
}
foreach ($tk in @(Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { $_.State -ne 'Disabled' -and $_.TaskPath -notmatch '^\\Microsoft\\' -and @($_.Triggers | Where-Object { $_.CimClass.CimClassName -eq 'MSFT_TaskLogonTrigger' }).Count -gt 0 })) {
  $__r.Add([pscustomobject]@{ tipo = 'tarefa'; nome = $tk.TaskName; cmd = (@($tk.Actions | ForEach-Object { [string]$_.Execute }) -join ' '); ap = ($tk.TaskPath + $tk.TaskName); ligado = $true })
}
Dado 'inicio' (Lista $__r.ToArray())
'''

# (padrão no nome ou comando, nível, por quê). O primeiro que casar vale.
CLASSES_INICIO = [
    (r'SecurityHealth|Windows Defender|MsMpEng|WindowsDefender', None, 'segurança do Windows: fica sempre'),
    (r'vgc|vgtray|Vanguard|EasyAntiCheat|BattlEye|FACEIT|PunkBuster|nProtect|XignCode', 0, 'anti-cheat: só tire se você pedir (alguns jogos deixam de abrir)'),
    (r'SynTP|ETDCtrl|Elan|Synaptics|Touchpad|Precision|Wacom|PenService|Pen Tablet', 0, 'driver de touchpad ou caneta: sem ele os gestos podem parar'),
    (r'RtkAud|RTHDVCPL|Realtek|IntelAudio|SmartAudio|Conexant|IDT|Dolby|DTS|MaxxAudio|Waves|Nahimic|SonicStudio', 3, 'painel de áudio: sem ele, efeitos e alguns atalhos de som param'),
    (r'Bluetooth|BTTray|ibtsiva', 3, 'Bluetooth do fabricante'),
    (r'OneDrive', 1, 'sincronização do OneDrive'),
    (r'Dropbox|GoogleDrive|Google Drive|MEGAsync|iCloud|pCloud|Nextcloud', 3, 'sincronização de arquivos: os arquivos só sincronizam com ele aberto'),
    (r'MicrosoftEdgeAutoLaunch|msedge.*--no-startup-window|MicrosoftEdge', 1, 'Edge pré-carregado sem você pedir'),
    (r'Teams|ms-teams|com\.squirrel\.Teams', 1, 'Teams abrindo sozinho'),
    (r'Update|Updater|GoogleUpdate|AdobeARM|AdobeGC|jusched|iTunesHelper|CCleaner|Helper|Launcher.*-silent|BraveSoftware Update|Edge Update', 1,
     'atualizador: continua atualizando pelas tarefas dele'),
    (r'Cortana|YourPhone|PhoneExperienceHost|Copilot|Widgets', 1, 'recurso do Windows que você não abriu'),
    (r'Spotify|Discord|Steam|EpicGames|Battle\.net|Origin|EADesktop|Ubisoft|GOG|Riot Client|Skype|Zoom|WhatsApp|Telegram|Slack|Opera|Brave|chrome|Vivaldi|Docker|Postman|Notion|Figma|Lghub|Razer|Corsair|SteelSeries|Logitech|Overwolf|Medal|NVIDIA Broadcast',
     2, 'programa que você abre quando quiser'),
    (r'igfx|IntelGraphics|NvBackend|NVIDIA|RadeonSoftware|AMD|cncmd', 2, 'painel da placa de vídeo (o driver continua)'),
    (r'AWCC|Alienware|Armoury|ArmouryCrate|Vantage|NitroSense|PredatorSense|MSI|Dragon Center|OMEN', 3, 'central do fabricante: perfis de ventoinha e luz podem parar'),
]


def _classe_inicio(nome, cmd):
    alvo = f'{nome} {cmd}'
    for padrao, nivel, porque in CLASSES_INICIO:
        if re.search(padrao, alvo, re.I):
            return nivel, porque
    return 3, 'programa que abre com o Windows'


@pacote('inicializacao', 'inicialização', 'o que abre junto com o Windows',
        'Desliga pelo mesmo mecanismo do Gerenciador de Tarefas (StartupApproved): o programa continua instalado e você religa '
        'quando quiser. Também olha a pasta Inicializar, as tarefas de inicialização dos apps da Loja e as tarefas agendadas '
        'que rodam no logon. Antivírus nunca sai; anti-cheat, touchpad e caneta só se você marcar.')
def itens_inicializacao(ctx):
    s = roda_ps(ctx.t, LISTA_INICIO_PS, 'lista-inicio', minutos=2, mostra=False)
    itens = []
    for e in lista(s.dados.get('inicio')):
        if not e.get('ligado'):
            continue
        nome, cmd, tipo = e.get('nome', ''), e.get('cmd', ''), e.get('tipo')
        nivel, porque = _classe_inicio(nome, cmd)
        if nivel is None:
            continue
        nota = ''
        if re.search('OneDrive', nome, re.I) and pf(ctx.perfil, 'tem.onedrive_usado'):
            nivel, nota = 0, 'sua pasta do OneDrive tem arquivos: sem ele abrindo, eles param de sincronizar'
        if tipo in ('run', 'pasta'):
            ps = R(e['ap'], nome, bytes([3] + [0] * 11), 'Binary')
            onde = 'registro' if tipo == 'run' else 'pasta Inicializar'
        elif tipo == 'loja':
            ps = R(e['ap'], 'State', 1)
            onde = 'app da Loja'
        else:
            ps = f'Set-Tarefa {psq(e["ap"])} $false | Out-Null'
            onde = 'tarefa no logon'
            nivel = max(nivel or 0, 2) if nivel else 0
        exe = re.sub(r'^"([^"]+)".*$', r'\1', cmd).split(' -')[0]
        itens.append(Item('ini:' + nome, nome, f'{porque[0].upper() + porque[1:]}. ({onde}: {corta_esq(caminho_curto(exe), 60)})',
                          'liga mais rápido e sobra RAM', 'não abre sozinho; abra pelo menu quando quiser', nivel, ps, nota=nota))
    itens.sort(key=lambda i: (i.nivel == 0, i.nivel, i.titulo.lower()))
    return itens


# ═══════════════════════════════ serviços ═══════════════════════════════

ORFAOS_PS = r'''
foreach ($tk in @(Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { $_.State -ne 'Disabled' -and $_.TaskPath -notmatch '^\\Microsoft\\' })) {
  foreach ($ac in @($tk.Actions)) {
    $exe = [Environment]::ExpandEnvironmentVariables([string]$ac.Execute).Trim('"')
    if ($exe -match '^[A-Za-z]:\\.*\.exe$' -and -not (Test-Path -LiteralPath $exe)) { Set-Tarefa ($tk.TaskPath + $tk.TaskName) $false | Out-Null }
  }
}
foreach ($s in @(Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | Where-Object { $_.StartMode -ne 'Disabled' -and $_.PathName -and $_.PathName -notmatch 'svchost|\\Windows\\' })) {
  $exe = $s.PathName; if ($exe -match '^"([^"]+)"') { $exe = $Matches[1] } elseif ($exe -match '^(\S+\.exe)') { $exe = $Matches[1] }
  if ($exe -match '\.exe$' -and -not (Test-Path -LiteralPath ([Environment]::ExpandEnvironmentVariables($exe)))) { Set-Servico $s.Name 'disabled' | Out-Null }
}'''

FABRICANTE_SVC_PS = r'''
$__pad = 'SupportAssist|TechHub|Dell Client Management|Dell Data Vault|Dell Customer Connect|Dell Foundation|Touchpoint Analytics|HP Insights|HP Diagnostics|HP App Helper|HP Network HSA|HP System Info HSA|HP Comm Recovery|Killer Analytics|Killer Network Service|Killer Provider Data Helper|Intel\(R\) Energy Server|System Usage Report|Intel\(R\) Driver & Support|NVIDIA Telemetry|Acer Quick Access Service|ASUS Optimization'
foreach ($s in @(Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -match $__pad -and $_.StartMode -eq 'Auto' })) { Set-Servico $s.Name 'demand' -Parar | Out-Null }
Desliga-Tarefas 'Killer Startup Task|NvTmRep|NvDriverUpdateCheck|NvProfileUpdater|NvNodeLauncher|Dell SupportAssist|DellUpdate|Dell Data Vault|HP Support Assistant|HPAudioSwitch|Lenovo.*(Welcome|Now)|AcerJumpstart|AcerRegistration|McAfee|Norton' 'Dell Command|DellCommandUpdate' | Out-Null'''

ATUALIZADORES_SVC = ['gupdate', 'gupdatem', 'GoogleUpdaterService', 'GoogleUpdaterInternalService', 'edgeupdate', 'edgeupdatem',
                     'brave', 'bravem', 'BraveElevationService', 'MozillaMaintenance', 'AdobeARMservice', 'AdobeUpdateService',
                     'AGSService', 'AGMService', 'ClickToRunSvc']


@pacote('servicos', 'serviços', 'serviços do Windows e de fabricante que este PC não usa',
        'Desativa (nunca apaga) serviços sem uso. O katharos olha o que o PC tem antes: impressora, scanner, leitor de cartão, '
        'sensores, Bluetooth, área de trabalho remota, WSL/Docker e jogos. Rede, áudio, Windows Update, Defender e firewall nunca entram.')
def itens_servicos(ctx):
    p = ctx.perfil
    tem = p.get('tem') or {}
    itens = [
        Item('basicos', 'mapas, demonstração, mídia e Insider', 'MapsBroker (mapas offline), RetailDemo (modo de loja), '
             'WMPNetworkSvc (compartilhar mídia do Windows Media Player), wisvc (programa Insider) e RemoteRegistry '
             '(editar o registro pela rede: desligar também é mais seguro).', 'menos serviços rodando', 'nenhum', 1,
             SVC(['MapsBroker', 'RetailDemo', 'WMPNetworkSvc', 'wisvc', 'RemoteRegistry'])),
        Item('fax', 'fax', 'Serviço de fax (Fax).', 'um serviço a menos', 'não envia fax pelo PC', 1, SVC(['Fax'])),
        Item('impressao', 'impressão', 'Spooler e notificações de impressora.', 'menos dois serviços',
             'não imprime, nem "Imprimir em PDF"', 2, SVC(['Spooler', 'PrintNotify']),
             nota='') if not tem.get('impressora') else None,
        Item('xbox', 'Xbox', 'Login, salvamentos na nuvem, rede e acessórios do Xbox (XblAuthManager, XblGameSave, XboxNetApiSvc, XboxGipSvc).',
             'menos quatro serviços', 'perde Game Pass, login Xbox em jogos e controle Xbox sem fio pelo adaptador',
             0 if joga(p) else 2, SVC(['XblAuthManager', 'XblGameSave', 'XboxNetApiSvc', 'XboxGipSvc']),
             nota='tem jogos instalados: não vem marcado' if joga(p) else ''),
        Item('busca', 'indexação da busca (Windows Search)', 'O índice de arquivos que deixa a busca do menu rápida. Em HD, ele '
             'mantém o disco ocupado.', 'menos leitura de disco em segundo plano',
             'a busca por arquivos no menu e no Explorador fica bem mais lenta', 2 if eh_hd(p) else 3, SVC(['WSearch']),
             nota='Windows em HD: recomendado' if eh_hd(p) else 'em SSD o ganho é pequeno'),
        Item('empresa', 'recursos de empresa', 'App-V, UE-V, monitor de impressão compartilhada, coletor de eventos, compartilhamento '
             'de portas .NET, pagamentos NFC, Carteira, roteador AllJoyn, gateway ALG, realidade mista e áudio espacial de RV.',
             'menos serviços', 'nenhum em PC doméstico', 2,
             SVC(['AppVClient', 'UevAgentService', 'shpamsvc', 'Wecsvc', 'NetTcpPortSharing', 'SEMgrSvc', 'WalletService',
                  'AJRouter', 'ALG', 'MixedRealityOpenXRSvc', 'perceptionsimulation', 'spectrum'])) if not pf(p, 'pc.dominio') else None,
        Item('telefonia', 'telefonia', 'PhoneSvc e TapiSrv (telefonia pelo PC).', 'menos serviços', 'modem e discador antigos param', 2,
             SVC(['PhoneSvc', 'TapiSrv'])),
        Item('hotspot', 'hotspot móvel', 'Compartilhar a internet do PC por Wi-Fi (icssvc' + ('' if tem.get('wsl') or tem.get('hyperv') else ' e SharedAccess') + ').',
             'menos serviços', 'não cria hotspot pelo PC', 2,
             SVC(['icssvc'] if tem.get('wsl') or tem.get('hyperv') or tem.get('docker') else ['icssvc', 'SharedAccess']),
             nota='WSL/Hyper-V/Docker: SharedAccess fica' if tem.get('wsl') or tem.get('hyperv') or tem.get('docker') else ''),
        Item('controle-pais', 'controle dos pais', 'WpcMonSvc (Family Safety).', 'um serviço a menos', 'controle dos pais da conta Microsoft para', 2,
             SVC(['WpcMonSvc'])),
        Item('atualizadores', 'atualizadores em manual', 'Google, Edge, Brave, Firefox, Adobe e Office deixam de ficar rodando o tempo todo. '
             'Eles continuam se atualizando pelas próprias tarefas agendadas.', 'menos serviços parados gastando RAM',
             'atualizações desses programas podem chegar um pouco depois', 2, SVC(ATUALIZADORES_SVC, 'demand', parar=False)),
        Item('fabricante', 'serviços e tarefas de fabricante', 'Assistentes de suporte e telemetria em manual (SupportAssist, TechHub, '
             'Dell Client Management, HP Touchpoint/Insights, Killer Analytics, Intel Energy Server, telemetria NVIDIA) e tarefas que '
             'ficam falhando ou repetindo (Killer Startup Task, NVIDIA, Dell, HP). Dell Update/Command Update ficam.',
             'menos CPU e WMI parados', 'diagnóstico do fabricante só quando você abrir', 2, FABRICANTE_SVC_PS),
        Item('nahimic', 'Nahimic e efeitos de áudio do fabricante', 'NahimicService e as tarefas dele em manual.', 'menos CPU',
             'os efeitos do Nahimic (surround virtual) param; o som continua normal', 3,
             RR("foreach ($s in @(Get-Service -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^Nahimic' })) { Set-Servico $s.Name 'demand' -Parar | Out-Null }",
                "Desliga-Tarefas 'Nahimic' | Out-Null")),
        Item('orfaos', 'restos de programas desinstalados', 'Tarefas agendadas e serviços que apontam para programas que não existem mais.',
             'menos erros no boot e no registro de eventos', 'nenhum', 2, ORFAOS_PS),
        Item('sob-demanda', 'serviços que podem subir só quando precisar', 'Passa de automático para manual (o Windows liga quando '
             'algo pede): plataforma de dispositivos conectados, inventário de compatibilidade, armazenamento, descoberta de rede (SSDP, UPnP, '
             'publicação de recursos) e NetBIOS.', 'menos serviços rodando desde o boot', 'aparelhos de rede (TVs, impressoras na rede) podem demorar a aparecer', 3,
             "foreach ($__s in 'CDPSvc','InventorySvc','StorSvc','lmhosts','FDResPub','fdPHost','SSDPSRV','upnphost','DusmSvc') { $__m = Get-ModoServico $__s; if ($__m -and $__m.modo -match 'auto') { Set-Servico $__s 'demand' | Out-Null } }"),
        Item('svchost', 'agrupar serviços em menos processos', 'O Windows separa cada serviço num svchost próprio quando há mais de 3,5 GB de RAM. '
             'Com o limite igual à sua RAM, eles voltam a dividir o mesmo processo.', 'dezenas de processos a menos no Gerenciador de Tarefas',
             'ganho de RAM pequeno e não comprovado; se um serviço travar, leva os vizinhos junto', 3,
             R('HKLM:\\SYSTEM\\CurrentControlSet\\Control', 'SvcHostSplitThresholdInKB', int((pf(p, 'ram.total', 8) or 8) * 1024 * 1024))),
        Item('rdp', 'área de trabalho remota', 'TermService, SessionEnv e UmRdpService.', 'menos serviços e menos portas abertas',
             'ninguém acessa este PC pela Área de Trabalho Remota', 3, SVC(['TermService', 'SessionEnv', 'UmRdpService'])) if not tem.get('rdp') else None,
        Item('winrm', 'gerenciamento remoto (WinRM)', 'Serviço de administração remota pelo PowerShell.', 'um serviço a menos',
             'scripts remotos e alguns sistemas de empresa param', 3, SVC(['WinRM'])) if not tem.get('winrm') and not pf(p, 'pc.dominio') else None,
        Item('ssh', 'agente SSH', 'ssh-agent (guarda chaves SSH na memória).', 'um serviço a menos', 'quem usa chave SSH com senha digita de novo', 3,
             SVC(['ssh-agent'])) if not tem.get('ssh') else None,
        Item('smartcard', 'cartão inteligente', 'SCardSvr, ScDeviceEnum e CertPropSvc.', 'menos três serviços',
             'certificado digital em cartão ou token (e-CPF, e-CNPJ) para de funcionar', 3,
             SVC(['SCardSvr', 'ScDeviceEnum', 'CertPropSvc'])) if not tem.get('smartcard') else None,
        Item('sensores', 'sensores e localização', 'Sensores (giro, luz) e o serviço de localização.', 'menos serviços',
             'rotação automática de tela, brilho automático, fuso horário automático e "Encontrar meu dispositivo" param',
             3, SVC(['SensorDataService', 'SensorService', 'SensrSvc', 'lfsvc'])) if not pf(p, 'pc.tablet') else None,
        Item('scanner', 'scanner', 'stisvc (aquisição de imagens).', 'um serviço a menos', 'scanner para de funcionar', 3,
             SVC(['stisvc'])) if not tem.get('scanner') else None,
        Item('biometria', 'biometria', 'WbioSrvc (Windows Hello por rosto ou digital).', 'um serviço a menos', 'Windows Hello com rosto e digital para',
             3, SVC(['WbioSrvc'])) if not tem.get('biometria') else None,
        Item('compat', 'assistente de compatibilidade e rastreio de links', 'PcaSvc (avisos de compatibilidade de programas antigos) '
             'e TrkWks (conserta atalhos quando arquivos mudam de lugar em rede).', 'menos dois serviços',
             'programas muito antigos deixam de receber ajustes automáticos', 3, SVC(['PcaSvc', 'TrkWks'])),
    ]
    return itens


# ═══════════════════════════════ privacidade ═══════════════════════════════

@pacote('privacidade', 'privacidade e propaganda', 'telemetria, anúncios, sugestões, widgets, busca na web',
        'Políticas e configurações oficiais. Nada é apagado: tudo volta com o desfazer. Na edição Home, algumas políticas valem '
        'só em parte (a telemetria fica em "obrigatória", que é o mínimo possível).')
def itens_privacidade(ctx):
    dc = f'{HKLM_POL}\\DataCollection'
    sub = ['SilentInstalledAppsEnabled', 'SoftLandingEnabled', 'SubscribedContentEnabled', 'SystemPaneSuggestionsEnabled',
           'PreInstalledAppsEnabled', 'OemPreInstalledAppsEnabled', 'PreInstalledAppsEverEnabled', 'ContentDeliveryAllowed',
           'SubscribedContent-338388Enabled', 'SubscribedContent-338389Enabled', 'SubscribedContent-353694Enabled',
           'SubscribedContent-353696Enabled', 'SubscribedContent-310093Enabled', 'SubscribedContent-338393Enabled',
           'SubscribedContent-88000326Enabled']
    tarefas = ['\\Microsoft\\Windows\\Application Experience\\Microsoft Compatibility Appraiser',
               '\\Microsoft\\Windows\\Application Experience\\ProgramDataUpdater',
               '\\Microsoft\\Windows\\Application Experience\\MareBackup',
               '\\Microsoft\\Windows\\Customer Experience Improvement Program\\Consolidator',
               '\\Microsoft\\Windows\\Customer Experience Improvement Program\\UsbCeip',
               '\\Microsoft\\Windows\\DiskDiagnostic\\Microsoft-Windows-DiskDiagnosticDataCollector',
               '\\Microsoft\\Windows\\Feedback\\Siuf\\DmClient', '\\Microsoft\\Windows\\Feedback\\Siuf\\DmClientOnScenarioDownload',
               '\\Microsoft\\Windows\\Maps\\MapsUpdateTask', '\\Microsoft\\Windows\\Maps\\MapsToastTask',
               '\\Microsoft\\Windows\\CloudExperienceHost\\CreateObjectTask']
    return [
        Item('telemetria', 'telemetria no mínimo', 'O Windows envia só os dados obrigatórios e para de pedir opinião.',
             'menos uso de rede e disco', 'nenhum', 1,
             RR(R(dc, 'AllowTelemetry', 0), R(dc, 'DoNotShowFeedbackNotifications', 1), R(dc, 'LimitDiagnosticLogCollection', 1),
                R(dc, 'DisableOneSettingsDownloads', 1), R(dc, 'AllowCommercialDataPipeline', 0), R(dc, 'AllowDeviceNameInTelemetry', 0),
                R(dc, 'MicrosoftEdgeDataOptIn', 0), R(f'{HKLM_POL}\\AppCompat', 'DisableInventory', 1), R(f'{HKLM_POL}\\AppCompat', 'AITEnable', 0),
                R(f'{HKLM_POL}\\HandwritingErrorReports', 'PreventHandwritingErrorReports', 1), R(f'{HKLM_POL}\\EdgeUI', 'DisableMFUTracking', 1),
                R('HKCU:\\Software\\Microsoft\\Siuf\\Rules', 'NumberOfSIUFInPeriod', 0),
                R('HKLM:\\SYSTEM\\CurrentControlSet\\Control\\WMI\\Autologger\\AutoLogger-Diagtrack-Listener', 'Start', 0))),
        Item('telemetria-svc', 'serviços de telemetria', 'DiagTrack (Experiências do Usuário Conectado) e dmwappushservice.',
             'menos um serviço que grava e envia o tempo todo', 'nenhum', 1,
             SVC(['DiagTrack', 'dmwappushservice', 'diagnosticshub.standardcollector.service', 'DcpSvc'])),
        Item('autologgers', 'registros contínuos de diagnóstico', 'Desliga os "autologgers" que gravam arquivos .etl o tempo todo '
             '(modelo de apps, rede celular, OOBE, SQM, contexto de diagnóstico, sessões de Wi-Fi).', 'menos escrita contínua em disco',
             'diagnósticos avançados da Microsoft ficam com menos dados', 3,
             RR(*(R(f'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\WMI\\Autologger\\{n}', 'Start', 0) for n in
                  ('AppModel', 'Cellcore', 'CloudExperienceHostOobe', 'DataMarket', 'DiagLog', 'LwtNetLog', 'SQMLogger', 'WdiContextLog', 'WiFiSession')))),
        Item('telemetria-tarefas', 'tarefas de telemetria', 'Avaliador de compatibilidade, programa de experiência do usuário, '
             'coleta de diagnóstico de disco, pesquisas de opinião e mapas (11 tarefas).', 'menos picos de disco e CPU', 'nenhum', 1,
             TAREFAS(tarefas)),
        Item('anuncios', 'anúncios e apps instalados sozinhos', 'Sem ID de propaganda, sem apps de propaganda instalados sozinhos, '
             'sem "sugestões" no menu, na tela de bloqueio e nas Configurações, sem "vamos terminar de configurar".',
             'menos propaganda e instalações surpresa', 'nenhum', 1,
             RR(R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo', 'Enabled', 0),
                R(f'{HKLM_POL}\\AdvertisingInfo', 'DisabledByGroupPolicy', 1),
                R(f'{HKLM_POL}\\CloudContent', 'DisableWindowsConsumerFeatures', 1), R(f'{HKLM_POL}\\CloudContent', 'DisableSoftLanding', 1),
                R(f'{HKCU_POL}\\CloudContent', 'DisableTailoredExperiencesWithDiagnosticData', 1),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Privacy', 'TailoredExperiencesWithDiagnosticDataEnabled', 0),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\UserProfileEngagement', 'ScoobeSystemSettingEnabled', 0),
                R(ADV, 'Start_IrisRecommendations', 0), R(ADV, 'ShowSyncProviderNotifications', 0),
                *(R(CDM, n, 0) for n in sub))),
        Item('atividades', 'histórico de atividades', 'O Windows para de gravar cada arquivo e app aberto.',
             'menos escrita em disco', 'a Linha do Tempo antiga fica vazia', 1,
             RR(*(R(f'{HKLM_POL}\\System', n, 0) for n in ('EnableActivityFeed', 'PublishUserActivities', 'UploadUserActivities')))),
        Item('cortana', 'Cortana', 'Políticas que desligam a Cortana, a busca na nuvem, a Cortana na tela de bloqueio e o uso da localização pela busca.',
             'nenhum processo da Cortana', 'nenhum (foi descontinuada)', 1,
             RR(*(R(f'{HKLM_POL}\\Windows Search', n, 0) for n in ('AllowCortana', 'AllowCloudSearch', 'AllowCortanaAboveLock', 'AllowSearchToUseLocation')),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Search', 'CortanaConsent', 0))),
        Item('anuncios-config', 'propaganda do Microsoft 365 nas Configurações', 'Tira os avisos de "conta" e ofertas do Microsoft 365 '
             'da página inicial das Configurações e do menu.', 'menos propaganda', 'nenhum', 1,
             RR(R(f'{HKLM_POL}\\CloudContent', 'DisableConsumerAccountStateContent', 1), R(f'{HKLM_POL}\\CloudContent', 'DisableThirdPartySuggestions', 1),
                R(CDM, 'SubscribedContent-338387Enabled', 0), R(CDM, 'SubscribedContent-353698Enabled', 0))),
        Item('office-telemetria', 'telemetria do Office', 'Tarefas de telemetria do Office desligadas e políticas que impedem o envio '
             'de dados de uso (Office 2013 a 365).', 'menos processos e uploads do Office', 'nenhum', 2, RR(
                "Desliga-Tarefas 'OfficeTelemetryAgent' | Out-Null",
                *(R(f'HKCU:\\Software\\Policies\\Microsoft\\Office\\{v}\\OSM', n, 0) for v in ('15.0', '16.0') for n in ('EnableLogging', 'EnableUpload')),
                R('HKCU:\\Software\\Policies\\Microsoft\\Office\\Common\\ClientTelemetry', 'DisableTelemetry', 1),
                R('HKCU:\\Software\\Policies\\Microsoft\\Office\\Common\\ClientTelemetry', 'SendTelemetry', 3),
                R('HKCU:\\Software\\Policies\\Microsoft\\Office\\16.0\\Common', 'QMEnable', 0),
                R('HKCU:\\Software\\Policies\\Microsoft\\Office\\16.0\\Common\\Feedback', 'Enabled', 0))) if pf(ctx.perfil, 'tem.office') else None,
        Item('vs-telemetria', 'telemetria do Visual Studio', 'Políticas oficiais: sem telemetria, sem diálogo de opinião e sem SQM.',
             'menos uploads', 'nenhum', 2, RR(R('HKCU:\\Software\\Microsoft\\VisualStudio\\Telemetry', 'TurnOffSwitch', 1),
                R('HKLM:\\SOFTWARE\\Policies\\Microsoft\\VisualStudio\\Feedback', 'DisableFeedbackDialog', 1),
                R('HKLM:\\SOFTWARE\\Policies\\Microsoft\\VisualStudio\\SQM', 'OptIn', 0), SVC(['VSStandardCollectorService150']))) if pf(ctx.perfil, 'tem.visualstudio') else None,
        Item('firefox-telemetria', 'telemetria do Firefox', 'Política oficial do Firefox sem telemetria e sem o "agente de navegador padrão".',
             'menos uploads', 'nenhum', 2, RR(R('HKLM:\\SOFTWARE\\Policies\\Mozilla\\Firefox', 'DisableTelemetry', 1),
                R('HKLM:\\SOFTWARE\\Policies\\Mozilla\\Firefox', 'DisableDefaultBrowserAgent', 1),
                "Desliga-Tarefas '\\\\Mozilla\\\\Firefox Default Browser Agent' | Out-Null")) if pf(ctx.perfil, 'tem.firefox') else None,
        Item('nuvem-clipboard', 'área de transferência na nuvem', 'O que você copia não sincroniza com outros aparelhos.',
             'privacidade', 'perde o colar entre aparelhos', 3, RR(R(f'{HKLM_POL}\\System', 'AllowCrossDeviceClipboard', 0))),
        Item('encontrar', '"Encontrar meu dispositivo"', 'Política que desliga o rastreio de localização do aparelho pela conta Microsoft.',
             'privacidade', 'não dá para localizar o PC perdido pela conta', 3, R('HKLM:\\SOFTWARE\\Policies\\Microsoft\\FindMyDevice', 'AllowFindMyDevice', 0)),
        Item('seguranca', 'portas de entrada antigas fechadas', 'SMBv1 desligado (protocolo usado pelo WannaCry), execução automática '
             'de pendrives e CDs desligada e Assistência Remota desligada.', 'mais segurança', 'aparelhos de rede muito antigos (antes de 2010) podem não abrir pastas', 1, RR(r'''
$__f = Tenta { Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -ErrorAction Stop } $null
if ($__f -and [string]$__f.State -eq 'Enabled') { if ($TESTE) { Plano 'desligar SMBv1' } else { Guarda-Desfazer 'smb1' 'Enable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart | Out-Null'; Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart -ErrorAction SilentlyContinue | Out-Null; $script:MUDOU++ } }''',
                R('HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer', 'NoDriveTypeAutoRun', 255),
                R('HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer', 'NoAutorun', 1),
                R('HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Remote Assistance', 'fAllowToGetHelp', 0)), minutos=6),
        Item('busca-web', 'busca do menu sem resultados da web', 'A busca do menu Iniciar procura só no PC: sem Bing, sem sugestões '
             'da internet e sem "destaques da pesquisa".', 'busca mais rápida e privada', 'pesquisas na web vão para o navegador', 2,
             RR(R(f'{HKCU_POL}\\Explorer', 'DisableSearchBoxSuggestions', 1), R(f'{HKLM_POL}\\Windows Search', 'ConnectedSearchUseWeb', 0),
                R(f'{HKLM_POL}\\Windows Search', 'DisableWebSearch', 1), R(f'{HKLM_POL}\\Windows Search', 'EnableDynamicContentInWSB', 0),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Search', 'BingSearchEnabled', 0),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\SearchSettings', 'IsDynamicSearchBoxEnabled', 0))),
        Item('widgets', 'widgets e notícias', 'O painel de notícias e clima (Windows 11) ou "Notícias e Interesses" (Windows 10).',
             'menos um processo do Edge em segundo plano', 'perde o painel de widgets', 2,
             RR(R('HKLM:\\SOFTWARE\\Policies\\Microsoft\\Dsh', 'AllowNewsAndInterests', 0), R(f'{HKLM_POL}\\Windows Feeds', 'EnableFeeds', 0),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Feeds', 'ShellFeedsTaskbarViewMode', 2))),
        Item('segundo-plano', 'apps da Loja em segundo plano', 'Apps da Loja deixam de rodar escondidos quando você não está usando.',
             'pouco de RAM e CPU', 'apps da Loja fechados (WhatsApp, Teams novo) podem não notificar', 2,
             RR(R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\BackgroundAccessApplications', 'GlobalUserDisabled', 1),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Search', 'BackgroundAppGlobalToggle', 0))),
        Item('segundo-plano-forte', 'bloquear segundo plano para todos', 'Política da máquina que nega segundo plano a todos os apps da '
             'Loja (o Windows 11 ignora o item anterior).', 'mais RAM e CPU livres', 'nenhum app da Loja notifica fechado', 3,
             R(f'{HKLM_POL}\\AppPrivacy', 'LetAppsRunInBackground', 2)),
        Item('erros', 'relatório de erros', 'O Windows para de montar e enviar relatórios de travamento (WerSvc e política).',
             'menos disco depois de travamentos', 'a Microsoft não recebe seus relatórios; soluções automáticas não aparecem', 2,
             RR(R(f'{HKLM_POL}\\Windows Error Reporting', 'Disabled', 1), SVC(['WerSvc']))),
        Item('localizacao', 'localização', 'Política que desliga a localização para todo o Windows.', 'privacidade',
             'fuso automático, mapas, clima local e "Encontrar meu dispositivo" param', 3,
             RR(R(f'{HKLM_POL}\\LocationAndSensors', 'DisableLocation', 1), R(f'{HKLM_POL}\\LocationAndSensors', 'DisableSensors', 1),
                R('HKLM:\\SYSTEM\\Maps', 'AutoUpdateEnabled', 0),
                R('HKLM:\\SOFTWARE\\Microsoft\\PolicyManager\\default\\WiFi\\AllowWiFiHotSpotReporting', 'Value', 0))),
        Item('edge-fundo', 'Edge sem rodar escondido', 'O Edge para de abrir pré-carregado no boot e de continuar aberto depois de fechado. '
             'O Edge passa a mostrar "Gerenciado pela sua organização".', 'menos RAM no boot', 'o Edge demora um pouco mais para abrir', 1,
             RR(R(EDGE_POL, 'StartupBoostEnabled', 0), R(EDGE_POL, 'BackgroundModeEnabled', 0))) if pf(ctx.perfil, 'tem.edge', True) else None,
    ]


# ═══════════════════════════════ visual ═══════════════════════════════

@pacote('visual', 'visual e barra de tarefas', 'efeitos, animações, transparência e barra enxuta',
        'Efeitos visuais têm ganho real em hardware antigo ou vídeo integrado. A suavização de fontes fica ligada (a maioria '
        'prefere). O Explorador reinicia no fim para aplicar.')
def itens_visual(ctx):
    win11 = pf(ctx.perfil, 'so.win11', True)
    d = 'HKCU:\\Control Panel\\Desktop'
    return [
        Item('efeitos', 'efeitos visuais em desempenho', 'Sem sombras, esmaecimento, deslizamento de menus e caixas, mantendo a '
             'suavização de fontes e as miniaturas.', 'janelas e menus mais rápidos em PC fraco', 'visual mais seco', 2,
             RR(R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects', 'VisualFXSetting', 3),
                R(d, 'UserPreferencesMask', bytes([0x90, 0x12, 0x03, 0x80, 0x10, 0x00, 0x00, 0x00]), 'Binary'),
                R(d, 'FontSmoothing', '2', 'String'), R(ADV, 'ListviewAlphaSelect', 0), R(ADV, 'ListviewShadow', 0))),
        Item('animacoes', 'animações', 'Sem animação ao minimizar, maximizar e na barra de tarefas.', 'resposta imediata', 'nenhum', 2,
             RR(R(d + '\\WindowMetrics', 'MinAnimate', '0', 'String'), R(ADV, 'TaskbarAnimations', 0),
                R('HKCU:\\Software\\Microsoft\\Windows\\DWM', 'EnableAeroPeek', 0))),
        Item('menus', 'menus sem espera', 'Submenus abrem na hora (MenuShowDelay 0 em vez de 400 ms).', 'sensação de rapidez', 'nenhum', 1,
             R(d, 'MenuShowDelay', '0', 'String')),
        Item('transparencia', 'transparência', 'Sem efeito acrílico na barra, no menu e na tela de entrada.', 'menos uso da placa de vídeo',
             'visual mais opaco', 2, RR(R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize', 'EnableTransparency', 0),
                                        R(f'{HKLM_POL}\\System', 'DisableAcrylicBackgroundOnLogon', 1))),
        Item('arrastar', 'arrastar janela sem conteúdo', 'Ao arrastar, só o contorno se move.', 'menos trabalho de vídeo em PC fraco',
             'visual estranho para quem não está acostumado', 3, R(d, 'DragFullWindows', '0', 'String')),
        Item('icones', 'ícones no lugar de miniaturas', 'O Explorador mostra ícones em vez de gerar miniaturas de fotos e vídeos.',
             'pastas de mídia abrem mais rápido em HD', 'não vê a prévia das fotos', 3, R(ADV, 'IconsOnly', 1)),
        Item('fundo-preto', 'papel de parede liso', 'Fundo preto em vez de imagem (e sem Windows Destaque).', 'um pouco de RAM',
             'perde o papel de parede', 3, RR(R(d, 'WallPaper', '', 'String'), R('HKCU:\\Control Panel\\Colors', 'Background', '0 0 0', 'String'))),
        Item('barra', 'barra de tarefas enxuta', 'Sem Visão de Tarefas, Chat e botão de widgets; a busca vira só o ícone.',
             'barra limpa', 'esses botões somem (o atalho Win+Tab continua)', 2,
             RR(R(ADV, 'ShowTaskViewButton', 0), R(ADV, 'TaskbarMn', 0), R(ADV, 'TaskbarDa', 0), R(ADV, 'ShowCortanaButton', 0),
                R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Search', 'SearchboxTaskbarMode', 1))),
        Item('extensoes', 'mostrar extensões dos arquivos', 'Mostra ".exe", ".pdf" etc. Ajuda a perceber arquivo disfarçado (foto.jpg.exe).',
             'segurança', 'nomes um pouco mais longos', 1, R(ADV, 'HideFileExt', 0)),
        Item('este-pc', 'Explorador abre em "Este Computador"', 'Em vez do Acesso Rápido com arquivos recentes.', 'privacidade e menos leitura',
             'nenhum', 2, RR(R(ADV, 'LaunchTo', 1), R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer', 'ShowRecent', 0),
                              R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer', 'ShowFrequent', 0))),
        Item('menu-classico', 'menu do botão direito completo', 'No Windows 11, o menu do botão direito volta a mostrar tudo, sem '
             '"Mostrar mais opções".', 'menos cliques', 'visual do Windows 10 no menu', 2,
             R('HKCU:\\Software\\Classes\\CLSID\\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\\InprocServer32', '(default)', '', 'String')) if win11 else None,
        Item('sem-espera-inicio', 'programas da inicialização sem espera', 'O Windows segura os programas da inicialização por alguns '
             'segundos depois do logon; aqui eles abrem na hora.', 'área de trabalho pronta mais cedo', 'em HD, o começo fica mais disputado', 2,
             R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Serialize', 'StartupDelayInMSec', 0)),
        Item('desligar-rapido', 'desligar e fechar travados mais rápido', 'Programas travados são fechados em 1 a 2 s (não 5 a 20 s) '
             'ao desligar, e o Windows espera menos pelos serviços.', 'desliga e reinicia mais rápido',
             'programa que demora para salvar ao fechar pode perder o que não foi salvo', 2,
             RR(R(d, 'AutoEndTasks', '1', 'String'), R(d, 'HungAppTimeout', '1000', 'String'), R(d, 'WaitToKillAppTimeout', '2000', 'String'),
                R(d, 'LowLevelHooksTimeout', '1000', 'String'), R('HKLM:\\SYSTEM\\CurrentControlSet\\Control', 'WaitToKillServiceTimeout', '2000', 'String'))),
        Item('atalhos-rapidos', 'atalhos quebrados sem busca demorada', 'Quando um atalho aponta para algo que sumiu, o Windows não '
             'vasculha o disco e a rede atrás dele, e não pergunta na internet com qual programa abrir um arquivo.', 'sem travadas de vários segundos',
             'atalho de arquivo movido não se conserta sozinho', 3,
             RR(*(R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer', n, 1) for n in
                  ('LinkResolveIgnoreLinkInfo', 'NoResolveSearch', 'NoResolveTrack', 'NoInternetOpenWith')))),
        Item('dump-pequeno', 'cópia de memória pequena em tela azul', 'Em tela azul, o Windows grava só um despejo pequeno, não a memória toda.',
             'GBs de disco e reinício mais rápido depois de travar', 'investigação profunda de telas azuis fica mais difícil', 2,
             R('HKLM:\\SYSTEM\\CurrentControlSet\\Control\\CrashControl', 'CrashDumpEnabled', 3)),
        Item('sacudir', 'sem minimizar tudo ao sacudir a janela', 'Desliga o "Aero Shake".', 'sem minimizar sem querer', 'nenhum', 2,
             R(ADV, 'DisallowShaking', 1)),
        Item('recomendados', 'menu Iniciar sem "Recomendados"', 'Política que esconde a seção de recomendados (arquivos recentes e '
             'sugestões). Vale no Pro, Education e Enterprise.', 'menu limpo e privado', 'perde os arquivos recentes no menu', 3,
             RR(R(f'{HKCU_POL}\\Explorer', 'HideRecommendedSection', 1), R('HKLM:\\SOFTWARE\\Microsoft\\PolicyManager\\current\\device\\Start', 'HideRecommendedSection', 1))) if win11 else None,
        Item('meet-now', 'sem botão "Reunir Agora"', 'Tira o botão do Skype da barra (Windows 10).', 'barra limpa', 'nenhum', 1,
             R('HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer', 'HideSCAMeetNow', 1)) if not win11 else None,
        Item('inicio-win11', 'menu Iniciar com mais fixados', 'No Windows 11, mais espaço para fixados e menos "recomendados".',
             'menu mais útil', 'nenhum', 2, R(ADV, 'Start_Layout', 1)) if win11 else None,
    ]


# ═══════════════════════════════ jogos ═══════════════════════════════

GPU_PS = r'''foreach ($__c in @(Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}' -ErrorAction SilentlyContinue | Where-Object { $_.PSChildName -match '^\d{4}$' })) {
  $__d = [string](Get-ItemProperty -LiteralPath $__c.PSPath -Name DriverDesc -ErrorAction SilentlyContinue).DriverDesc
  if ($__d -match '«fab»') { $__k = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\' + $__c.PSChildName; «reg» }
}'''

JOGOS_EXE = ['VALORANT-Win64-Shipping.exe', 'cs2.exe', 'csgo.exe', 'FortniteClient-Win64-Shipping.exe', 'League of Legends.exe',
             'RocketLeague.exe', 'r5apex.exe', 'r5apex_dx12.exe', 'GTA5.exe', 'GTA5_Enhanced.exe', 'Minecraft.Windows.exe',
             'RobloxPlayerBeta.exe', 'Overwatch.exe', 'dota2.exe', 'RainbowSix.exe', 'RainbowSix_Vulkan.exe', 'TslGame.exe',
             'FC25.exe', 'FC26.exe', 'Cyberpunk2077.exe', 'eldenring.exe', 'cod.exe', 'cod24-cod.exe', 'destiny2.exe',
             'PathOfExile_x64.exe', 'PathOfExileSteam.exe', 'Diablo IV.exe', 'Wow.exe', 'Hearthstone.exe', 'bf2042.exe',
             'bf6.exe', 'RDR2.exe', 'HogwartsLegacy.exe', 'Palworld-Win64-Shipping.exe', 'RustClient.exe',
             'DeadByDaylight-Win64-Shipping.exe', 'EscapeFromTarkov.exe', 'Marvel-Win64-Shipping.exe', 'FallGuys_client_game.exe',
             'ForzaHorizon5.exe', 'ForzaHorizon4.exe', 'Starfield.exe', 'bg3.exe', 'bg3_dx11.exe', 'witcher3.exe',
             'MonsterHunterWilds.exe', 'MonsterHunterWorld.exe', 'Warframe.x64.exe', 'Terraria.exe', 'GenshinImpact.exe',
             'ZenlessZoneZero.exe', 'StarRail.exe', 'Albion-Online.exe', 'LOSTARK.exe', 'NarakaBladepoint.exe', 'deadlock.exe',
             'helldivers2.exe', 'SoTGame.exe', 'Phasmophobia.exe', 'VRChat.exe', 'tf_win64.exe', 'left4dead2.exe',
             'TheFinals.exe', 'Discovery.exe', 'Among Us.exe', 'Lethal Company.exe', 'Stardew Valley.exe', 'RobloxStudioBeta.exe']


@pacote('jogos', 'jogos', 'Modo de Jogo, Game DVR, prioridades e ajustes de latência',
        'Ajustes que os otimizadores de jogos usam, com a verdade sobre cada um: alguns ajudam sempre, outros só em casos específicos, '
        'e alguns são quase placebo (está escrito). Desligar segurança do Windows (VBS, Integridade de Memória) não está aqui de propósito: '
        'é troca de segurança, não ajuste.')
def itens_jogos(ctx):
    p = ctx.perfil
    j = joga(p)
    mm = 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile'
    gc = 'HKCU:\\System\\GameConfigStore'
    ifeo = 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options'
    prio = '\n'.join(R(f'{ifeo}\\{e}\\PerfOptions', 'CpuPriorityClass', 3) for e in JOGOS_EXE)
    nagle = r'''foreach ($__i in @(Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces' -ErrorAction SilentlyContinue)) {
  $__v = Get-ItemProperty -LiteralPath $__i.PSPath -ErrorAction SilentlyContinue
  if ($__v.DhcpIPAddress -or ($__v.IPAddress -and [string]$__v.IPAddress -ne '0.0.0.0')) {
    $__k = 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\' + $__i.PSChildName
    Set-Valor $__k 'TcpAckFrequency' 1 | Out-Null; Set-Valor $__k 'TCPNoDelay' 1 | Out-Null
  }
}'''
    return [
        Item('modo-jogo', 'Modo de Jogo ligado', 'O Windows segura atualizações e tarefas de fundo enquanto um jogo está aberto.',
             'menos engasgos causados pelo sistema', 'nenhum', 1,
             RR(R('HKCU:\\Software\\Microsoft\\GameBar', 'AutoGameModeEnabled', 1), R('HKCU:\\Software\\Microsoft\\GameBar', 'AllowAutoGameMode', 1))),
        Item('gamedvr', 'Game DVR e captura em segundo plano', 'Desliga a gravação contínua do Xbox Game Bar (ela grava os últimos '
             'minutos o tempo todo).', 'mais FPS e menos disco durante o jogo', 'Win+Alt+G e gravação pela Game Bar param', 2,
             RR(R('HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR', 'AppCaptureEnabled', 0), R(gc, 'GameDVR_Enabled', 0),
                R(f'{HKLM_POL}\\GameDVR', 'AllowGameDVR', 0))),
        Item('prioridade-jogos', 'prioridade alta para jogos conhecidos', f'Mais de {len(JOGOS_EXE)} jogos (Valorant, CS2, Fortnite, LoL, '
             'Apex, GTA V, Minecraft, Roblox...) abrem sempre com prioridade alta de CPU, por uma opção oficial do Windows.',
             'o jogo passa na frente de programas em segundo plano', 'em PC fraco, música e Discord podem engasgar durante o jogo',
             2 if j else 3, prio, minutos=4),
        Item('mmcss', 'agendador multimídia favorecendo jogos', 'Jogos ganham prioridade de GPU e CPU no agendador multimídia '
             '(MMCSS) e o sistema reserva menos CPU para tarefas de fundo.', 'pequeno; ajuda jogos que usam o MMCSS',
             'tarefas de fundo ficam com menos CPU enquanto joga', 2 if j else 3,
             RR(R(mm, 'SystemResponsiveness', 10), R(mm, 'NoLazyMode', 1), R(mm, 'AlwaysOn', 1), R(mm + '\\Tasks\\Games', 'GPU Priority', 8), R(mm + '\\Tasks\\Games', 'Priority', 6),
                R(mm + '\\Tasks\\Games', 'Scheduling Category', 'High', 'String'), R(mm + '\\Tasks\\Games', 'SFIO Priority', 'High', 'String'))),
        Item('primeiro-plano', 'prioridade do primeiro plano', 'O programa em que você está mexendo ganha fatias maiores de CPU '
             '(Win32PrioritySeparation 0x26).', 'pequeno; resposta um pouco melhor', 'tarefas de fundo um pouco mais lentas', 2 if j else 3,
             R('HKLM:\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl', 'Win32PrioritySeparation', 38)),
        Item('mouse', 'sem aceleração do mouse', 'O ponteiro anda sempre a mesma distância para o mesmo movimento ("precisão aprimorada" desligada).',
             'mira mais consistente', 'em telas grandes o mouse parece mais lento até se acostumar', 2 if j else 0,
             RR(R('HKCU:\\Control Panel\\Mouse', 'MouseSpeed', '0', 'String'), R('HKCU:\\Control Panel\\Mouse', 'MouseThreshold1', '0', 'String'),
                R('HKCU:\\Control Panel\\Mouse', 'MouseThreshold2', '0', 'String'))),
        Item('teclado', 'teclado mais rápido', 'Repetição de tecla no máximo e atraso mínimo antes de repetir.',
             'movimentos e digitação respondem antes', 'quem digita devagar pode repetir letras sem querer', 2 if j else 0,
             RR(R('HKCU:\\Control Panel\\Keyboard', 'KeyboardDelay', '0', 'String'), R('HKCU:\\Control Panel\\Keyboard', 'KeyboardSpeed', '31', 'String'))),
        Item('aderencia', 'sem atalho das Teclas de Aderência', 'Shift 5 vezes (e segurar Shift ou Num Lock) não abre mais o aviso de acessibilidade '
             'no meio do jogo. Os recursos continuam nas Configurações.', 'sem janela surgindo no jogo', 'quem usa esses atalhos de acessibilidade perde', 2 if j else 3,
             RR(R('HKCU:\\Control Panel\\Accessibility\\StickyKeys', 'Flags', '506', 'String'),
                R('HKCU:\\Control Panel\\Accessibility\\Keyboard Response', 'Flags', '122', 'String'),
                R('HKCU:\\Control Panel\\Accessibility\\ToggleKeys', 'Flags', '58', 'String'))),
        Item('gpu-nvidia', 'NVIDIA sem troca dinâmica de estado de energia', 'A placa NVIDIA fica sempre no estado de desempenho (DisableDynamicPstate).',
             'clock da GPU estável, sem quedas de frequência', 'mais calor e consumo o tempo todo, mesmo parado', 0, GPU_PS.replace('«fab»', 'NVIDIA').replace('«reg»', R('$__k', 'DisableDynamicPstate', 1).replace("'$__k'", '$__k'))) if pf(p, 'tem.nvidia') and not pf(p, 'pc.notebook') else None,
        Item('gpu-amd', 'AMD sem ULPS', 'Desliga o modo de ultra baixo consumo das placas AMD, que às vezes causa engasgo ao acordar a placa '
             '(principalmente com duas placas).', 'menos engasgos ao sair do ocioso', 'mais consumo parado', 3,
             GPU_PS.replace('«fab»', 'AMD|Radeon').replace('«reg»', R('$__k', 'EnableULPS', 0).replace("'$__k'", '$__k'))) if pf(p, 'tem.amd') and not pf(p, 'pc.notebook') else None,
        Item('fse', 'sem otimizações de tela inteira', 'Jogos em tela inteira usam o modo exclusivo antigo.',
             'só em alguns jogos antigos com engasgo ou atraso', 'no Windows 11 pode piorar: o modo moderno costuma ser melhor', 3,
             RR(R(gc, 'GameDVR_FSEBehaviorMode', 2), R(gc, 'GameDVR_HonorUserFSEBehaviorMode', 1), R(gc, 'GameDVR_FSEBehavior', 2),
                R(gc, 'GameDVR_DXGIHonorFSEWindowsCompatible', 1))),
        Item('timer', 'resolução do temporizador global', 'No Windows 11, um programa que pede temporizador fino volta a valer para o '
             'sistema todo (GlobalTimerResolutionRequests).', 'pode reduzir latência em alguns jogos', 'mais consumo de energia; efeito varia', 3,
             R('HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\kernel', 'GlobalTimerResolutionRequests', 1)) if pf(p, 'so.win11') else None,
        Item('rede-jogos', 'rede: sem atraso de pacotes (Nagle) e sem limite multimídia', 'Confirmações TCP imediatas e sem o '
             'limitador de rede do agendador multimídia.', 'quase sempre zero ou mínimo (a maioria dos jogos usa UDP)',
             'um pouco mais de pacotes na rede', 3, RR(nagle, R(mm, 'NetworkThrottlingIndex', -1))),
        Item('mpo', 'desligar o Multiplane Overlay (MPO)', 'Correção conhecida para tela piscando, cintilação e engasgos com '
             'algumas placas NVIDIA e vários monitores.', 'só resolve se você tem esse problema', 'sem o problema, não muda nada (ou piora um pouco)', 0,
             R('HKLM:\\SOFTWARE\\Microsoft\\Windows\\Dwm', 'OverlayTestMode', 5)),
        Item('hags', 'agendamento de GPU acelerado por hardware', 'A placa de vídeo cuida da própria fila (HAGS). Precisa de placa e '
             'driver recentes; vale depois de reiniciar.', 'pequeno; necessário para o DLSS 3 (geração de quadros)',
             'em placas antigas pode causar engasgos', 0, R('HKLM:\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers', 'HwSchMode', 2)),
    ]


# ═══════════════════════════════ energia ═══════════════════════════════

PLANO_DESEMPENHO_PS = r'''
Guarda-Energia
$__arq = Join-Path $CASA 'plano-desempenho.txt'
$__lista = (powercfg /list | Out-String)
$__g = $null
if (Test-Path $__arq) { $__s = (Get-Content $__arq -Raw).Trim(); if ($__lista -match [regex]::Escape($__s)) { $__g = $__s } }
if (-not $__g -and $__lista -match 'e9a42b02-d5df-448d-aa00-03f14749eb61') { $__g = 'e9a42b02-d5df-448d-aa00-03f14749eb61' }
if (-not $__g) {
  if ($TESTE) { Plano 'criar e ativar o plano Desempenho Maximo'; return }
  $__d = (powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61 | Out-String)
  if ($__d -match '([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})') { $__g = $Matches[1]; Set-Content -LiteralPath $__arq -Value $__g; Guarda-Desfazer 'plano-criado' ("powercfg /delete " + $__g) }
  else { $__g = '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'; Info 'Desempenho Maximo indisponivel nesta edicao: usando Alto desempenho' }
}
$__atual = (powercfg /getactivescheme | Out-String)
if ($__atual -notmatch [regex]::Escape($__g)) { if ($TESTE) { Plano 'ativar plano de desempenho' } else { powercfg /setactive $__g | Out-Null; $script:MUDOU++ } }
'''

PLANO_FRESCO_PS = r'''
Guarda-Energia
$__eq = '381b4222-f694-41f0-9685-ff5bb260df2e'
if ((powercfg /getactivescheme | Out-String) -notmatch $__eq) { if ($TESTE) { Plano 'ativar o plano Equilibrado' } else { powercfg /setactive $__eq | Out-Null; $script:MUDOU++ } }
$__gs = @([regex]::Matches((powercfg /list | Out-String), '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}') | ForEach-Object { $_.Value } | Select-Object -Unique)
foreach ($__g in $__gs) {
  Set-Energia $__g 'SUB_PROCESSOR' 'PROCTHROTTLEMIN' 5 5 ("CPU minima 5% no plano " + $__g.Substring(0, 8)) | Out-Null
  Set-Energia $__g 'SUB_PROCESSOR' 'PERFBOOSTMODE' 3 3 ("turbo eficiente no plano " + $__g.Substring(0, 8)) | Out-Null
  Set-Energia $__g 'SUB_PCIEXPRESS' 'ASPM' 1 2 ("economia do PCIe ligada no plano " + $__g.Substring(0, 8)) | Out-Null
}
if (-not $TESTE) { powercfg /setactive SCHEME_CURRENT | Out-Null }
'''


@pacote('energia', 'energia', 'plano de energia, turbo, USB, PCIe e hibernação',
        'Duas filosofias, escolha uma: "desempenho" mantém o clock alto (bom para desktop e jogos na tomada) e "fresco" deixa o '
        'processador descansar (bom para notebook que esquenta, ventoinha alta e bateria). Utilitários de fabricante costumam '
        'forçar alto desempenho; o fresco ajusta todos os planos que eles alternam.')
def itens_energia(ctx):
    p = ctx.perfil
    nb = pf(p, 'pc.notebook')
    usb = '2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226'
    return [
        Item('desempenho', 'plano desempenho máximo', 'Ativa o plano Desempenho Máximo (ou Alto desempenho): o processador não reduz '
             'o clock e responde na hora.', 'mais rápido para responder e em jogos', 'mais calor e consumo; em notebook, a bateria dura menos',
             3 if nb else 2, PLANO_DESEMPENHO_PS, grupo='plano', nota='notebook: o plano fresco vem marcado' if nb else ''),
        Item('fresco', 'plano fresco (notebook que esquenta)', 'Plano Equilibrado e, em TODOS os planos: CPU mínima 5%, turbo no modo '
             'eficiente e economia do PCIe ligada. Resolve ventoinha alta mesmo parado.', 'mais frio, silencioso e mais bateria',
             'picos de desempenho um pouco menores', 1 if nb else 0, PLANO_FRESCO_PS, grupo='plano', minutos=4,
             conflita=('cpu-100', 'aspm', 'throttling')),
        Item('disco', 'disco nunca desliga na tomada', 'O disco não "dorme" com o PC ligado na tomada.', 'sem espera para o HD acordar',
             'gasto mínimo de energia', 2, "Guarda-Energia; Set-Energia 'SCHEME_CURRENT' 'SUB_DISK' 'DISKIDLE' 0 $null 'disco sempre ligado na tomada' | Out-Null; if (-not $TESTE) { powercfg /setactive SCHEME_CURRENT | Out-Null }"),
        Item('usb', 'sem suspensão seletiva de USB na tomada', 'O Windows para de desligar portas USB para economizar.',
             'evita mouse, teclado e headset desconectando ou com atraso', 'gasto mínimo de energia', 3 if nb else 2,
             f"Set-Energia 'SCHEME_CURRENT' {usb.split()[0]} {usb.split()[1]} 0 $null 'USB sem suspensao na tomada' | Out-Null; if (-not $TESTE) {{ powercfg /setactive SCHEME_CURRENT | Out-Null }}"),
        Item('cpu-100', 'clock sempre no máximo na tomada', 'Estado mínimo do processador em 100% na tomada.',
             'zero atraso para subir o clock', 'mais calor e consumo o tempo todo', 0 if nb else 3,
             "Set-Energia 'SCHEME_CURRENT' 'SUB_PROCESSOR' 'PROCTHROTTLEMIN' 100 $null 'CPU minima 100% na tomada' | Out-Null; if (-not $TESTE) { powercfg /setactive SCHEME_CURRENT | Out-Null }"),
        Item('aspm', 'PCIe sem economia na tomada', 'Placa de vídeo e SSD NVMe ficam sempre em potência total (ASPM desligado).',
             'pequeno; evita atrasos ao acordar dispositivos', 'mais consumo', 0 if nb else 3,
             "Set-Energia 'SCHEME_CURRENT' 'SUB_PCIEXPRESS' 'ASPM' 0 $null 'PCIe sem economia na tomada' | Out-Null; if (-not $TESTE) { powercfg /setactive SCHEME_CURRENT | Out-Null }"),
        Item('throttling', 'sem limitação de energia dos processos', 'Desliga o Power Throttling (e o EcoQoS que vem com ele): o '
             'Windows para de jogar programas de fundo nos núcleos lentos.', 'programas de fundo mais rápidos',
             'mais consumo; em notebook, menos bateria', 0 if nb else 3,
             R('HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerThrottling', 'PowerThrottlingOff', 1)),
        Item('rede-energia', 'placa de rede sem economia de energia', 'O Windows não desliga a placa de rede para economizar.',
             'evita quedas de Wi-Fi e atraso ao voltar da suspensão', 'mais consumo', 0 if nb else 3, r'''
$__ad = @(Get-NetAdapter -Physical -ErrorAction SilentlyContinue)
foreach ($a in $__ad) { $pm = Get-NetAdapterPowerManagement -Name $a.Name -ErrorAction SilentlyContinue; if ($pm -and [string]$pm.AllowComputerToTurnOffDevice -eq 'Enabled') { if ($TESTE) { Plano ('sem economia: ' + $a.Name) } else { Guarda-Desfazer ('rede|' + $a.Name) ("Enable-NetAdapterPowerManagement -Name '" + $a.Name + "' -ErrorAction SilentlyContinue"); Disable-NetAdapterPowerManagement -Name $a.Name -NoRestart -ErrorAction SilentlyContinue; $script:MUDOU++ } } }'''),
        Item('inicio-rapido', 'inicialização rápida garantida', 'Ligar depois de desligar fica muito mais rápido. Em HD faz diferença grande.',
             'boot mais curto', 'é preciso "Reiniciar" (não "Desligar") para aplicar algumas atualizações', 1, r'''
$__h = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Power' -ErrorAction SilentlyContinue).HibernateEnabled
if ($__h -eq 0) { if ($TESTE) { Plano 'ligar hibernacao reduzida' } else { Guarda-Desfazer 'hib' 'powercfg /h off'; powercfg /h on | Out-Null; powercfg /h /type reduced | Out-Null; $script:MUDOU++ } }
Set-Valor 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Power' 'HiberbootEnabled' 1 | Out-Null''') if eh_hd(p) else None,
        Item('hibernacao', 'hibernação desligada', 'Apaga o hiberfil.sys (do tamanho de boa parte da RAM). Em SSD o boot já é rápido.',
             'alguns GB de espaço', 'sem hibernar e sem inicialização rápida', 3 if not nb else 0, r'''
$__h = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Power' -ErrorAction SilentlyContinue).HibernateEnabled
if ($__h -ne 0) { if ($TESTE) { Plano 'desligar hibernacao (powercfg /h off)' } else { Guarda-Desfazer 'hib' 'powercfg /h on'; powercfg /h off | Out-Null; $script:MUDOU++ } }''',
             nota='notebook: hibernar salva o trabalho quando a bateria acaba' if nb else '') if eh_ssd(p) else None,
    ]


# ═══════════════════════════════ disco ═══════════════════════════════

@pacote('disco', 'disco e memória', 'menos escrita em segundo plano, boot e abertura de programas',
        'Ajustes do pacote de disco do cofre: varreduras do Defender mais leves, menos tarefas que leem o disco à toa, NTFS mais leve, '
        'Sensor de Armazenamento e otimização da unidade (desfragmenta HD; em SSD só faz TRIM). SysMain e Prefetch ficam ligados: '
        'em HD eles aceleram a abertura de programas (decisão registrada no cofre).')
def itens_disco(ctx):
    p = ctx.perfil
    hd = eh_hd(p)
    ram = pf(p, 'ram.total', 8) or 8
    tarefas = ['\\Microsoft\\Windows\\Maintenance\\WinSAT', '\\Microsoft\\Windows\\Autochk\\Proxy',
               '\\Microsoft\\Windows\\Application Experience\\StartupAppTask', '\\Microsoft\\Windows\\SpacePort\\SpaceAgentTask',
               '\\Microsoft\\Windows\\Work Folders\\Work Folders Maintenance Work']
    if not pf(p, 'tem.historico_arquivos'):
        tarefas.append('\\Microsoft\\Windows\\FileHistory\\File History (maintenance mode)')
    ss = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\StorageSense\\Parameters\\StoragePolicy'
    od_ns = ['HKLM:\\SOFTWARE\\Classes\\CLSID\\{018D5C66-4533-4307-9B53-224DE2ED1FE6}',
             'HKLM:\\SOFTWARE\\WOW6432Node\\Classes\\CLSID\\{018D5C66-4533-4307-9B53-224DE2ED1FE6}']

    def otimiza_unidade(ctx, it, pr, teste):
        if teste:
            ctx.t.item('○', 'azul', 'defrag C: /O' + (' (desfragmentar)' if hd else ' (TRIM)'), recuo=4, cor_nome='sub')
            return 1, 0
        cod, _ = roda_exe(['defrag.exe', 'C:', '/O', '/U'], 120 if hd else 15, pr, ctx.mult)
        if cod == -1:
            ctx.t.aviso('otimização da unidade passou do tempo e foi encerrada.')
            return 0, 1
        ctx.t.item('✓', 'verde', ('desfragmentação' if hd else 'TRIM') + f' concluído (código {cod})', recuo=4, cor_nome='sub')
        return 1, 0

    def boot_hd(ctx, it, pr, teste):
        if teste:
            ctx.t.item('○', 'azul', 'processar tarefas ociosas e defrag C: /B', recuo=4, cor_nome='sub')
            return 1, 0
        pr.atual = 'processando tarefas ociosas'
        roda_exe(['rundll32.exe', 'advapi32.dll,ProcessIdleTasks'], 20, pr, ctx.mult)
        cod, _ = roda_exe(['defrag.exe', 'C:', '/B'], 30, pr, ctx.mult)
        ctx.t.item('✓', 'verde', f'arquivos do boot reorganizados (código {cod})', recuo=4, cor_nome='sub')
        return 1, 0

    return [
        Item('defender-leve', 'varreduras do Defender mais leves', 'Varreduras agendadas com prioridade baixa e no máximo 20% de CPU. '
             'A proteção em tempo real não muda.', 'o PC não trava durante a varredura semanal', 'a varredura completa demora mais',
             1 if hd else 2, r'''
$__m = Get-MpPreference -ErrorAction Stop
if ($__m.ScanAvgCPULoadFactor -ne 20 -or -not $__m.EnableLowCpuPriority) {
  if ($TESTE) { Plano 'Defender: varredura com 20% de CPU e prioridade baixa' }
  else { Guarda-Desfazer 'defender' ("Set-MpPreference -ScanAvgCPULoadFactor {0} -EnableLowCpuPriority `${1}" -f $__m.ScanAvgCPULoadFactor, ([string]$__m.EnableLowCpuPriority).ToLower()); Set-MpPreference -ScanAvgCPULoadFactor 20 -EnableLowCpuPriority $true; $script:MUDOU++ }
}'''),
        Item('p2p', 'Windows Update sem compartilhar com outros PCs', 'Desliga o envio de pedaços de atualizações para outros '
             'computadores (Otimização de Entrega P2P).', 'menos upload e escrita em disco', 'nenhum', 1,
             R(f'{HKLM_POL}\\DeliveryOptimization', 'DODownloadMode', 0)),
        Item('tarefas', 'tarefas de manutenção inúteis', 'WinSAT (nota de desempenho), Autochk Proxy, StartupAppTask, Storage Spaces, '
             'Pastas de Trabalho' + ('' if pf(p, 'tem.historico_arquivos') else ' e Histórico de Arquivos') + '.',
             'menos leitura de disco ociosa', 'nenhum', 2, TAREFAS(tarefas)),
        Item('lastaccess', 'NTFS sem gravar "último acesso"', 'O Windows para de gravar a data de cada leitura de arquivo.',
             'menos escrita em disco', 'programas de backup que dependem dessa data (raros) se confundem', 2, r'''
$__q = (fsutil behavior query disablelastaccess | Out-String)
if ($__q -match '=\s*(\d)') { $__v = $Matches[1] } else { $__v = '2' }
if ($__v -ne '1' -and $__v -ne '3') { if ($TESTE) { Plano 'desligar gravacao de ultimo acesso' } else { Guarda-Desfazer 'lastaccess' ('fsutil behavior set disablelastaccess ' + $__v + ' | Out-Null'); fsutil behavior set disablelastaccess 1 | Out-Null; $script:MUDOU++ } }'''),
        Item('ntfs', 'NTFS sem nomes 8.3 e com mais cache', 'Arquivos novos não ganham nome curto antigo (ARQUIV~1) e o NTFS usa mais '
             'memória para metadados' + (' (há RAM sobrando)' if ram >= 8 else '') + '.', 'pastas grandes mais rápidas',
             'programas de DOS muito antigos podem não achar arquivos novos', 3, r'''
$__a = (fsutil behavior query disable8dot3 | Out-String); $__b = (fsutil behavior query memoryusage | Out-String)
$__v1 = '2'; if ($__a -match 'NtfsDisable8dot3NameCreation\s*=\s*(\d)') { $__v1 = $Matches[1] }
$__v2 = '1'; if ($__b -match '=\s*(\d)') { $__v2 = $Matches[1] }
if ($__v1 -ne '1') { if ($TESTE) { Plano 'sem nomes 8.3' } else { Guarda-Desfazer '8dot3' ('fsutil behavior set disable8dot3 ' + $__v1 + ' | Out-Null'); fsutil behavior set disable8dot3 1 | Out-Null; $script:MUDOU++ } }
if ($__v2 -ne '2' -and «ram» -ge 8) { if ($TESTE) { Plano 'mais cache para o NTFS' } else { Guarda-Desfazer 'memusage' ('fsutil behavior set memoryusage ' + $__v2 + ' | Out-Null'); fsutil behavior set memoryusage 2 | Out-Null; $script:MUDOU++ } }'''.replace('«ram»', str(int(ram)))),
        Item('sensor', 'Sensor de Armazenamento mensal', 'O próprio Windows limpa temporários todo mês, sem tocar na Lixeira nem em Downloads.',
             'disco não enche sozinho', 'nenhum', 1, RR(R(ss, '01', 1), R(ss, '04', 1), R(ss, '2048', 30), R(ss, '08', 0), R(ss, '32', 0))),
        Item('sysmain', 'SysMain e Prefetch ligados', 'Pré-carregam os programas que você mais usa. Em HD aceleram a abertura; há '
             'guias que mandam desligar, mas isso só serve como teste de disco a 100%.', 'programas abrem mais rápido',
             'nenhum', 1, RR(SVC(['SysMain'], 'auto', parar=False), "if (-not $TESTE) { & sc.exe start SysMain 2>$null | Out-Null }",
                             R('HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters', 'EnablePrefetcher', 3))) if hd else None,
        Item('atrasados', 'serviços de terceiros com início atrasado', 'Office (ClickToRun) e Adobe sobem só depois que o Windows '
             'terminou de carregar.', 'boot e área de trabalho prontos mais cedo', 'esses serviços demoram ~2 min para subir', 2,
             "foreach ($__s in 'ClickToRunSvc','AdobeUpdateService','AGSService') { $__m = Get-ModoServico $__s; if ($__m -and $__m.modo -eq 'auto') { Set-Servico $__s 'delayed-auto' | Out-Null } }"),
        Item('boot-hd', 'reorganizar os arquivos do boot no HD', 'O Windows junta no HD os arquivos do boot e dos programas mais usados.',
             'boot e abertura mais rápidos em HD', 'demora até 30 min', 2, py=boot_hd) if hd else None,
        Item('unidade', 'otimizar a unidade', 'Desfragmenta se for HD; se for SSD, só manda o TRIM (nunca desfragmenta SSD).',
             'disco mais rápido' + (' (HD fragmentado é muito lento)' if hd else ''), 'demora' + (' (até 2 h em HD)' if hd else ' pouco'),
             1, py=otimiza_unidade),
        Item('pagefile', 'memória virtual de volta ao automático', 'O arquivo de paginação está desligado ou fixo. Ninguém recomenda '
             'desligar: programas fecham sozinhos sem ele.', 'estabilidade', 'nenhum', 1, r'''
$__c = Get-CimInstance Win32_ComputerSystem
if (-not $__c.AutomaticManagedPagefile) { if ($TESTE) { Plano 'memoria virtual automatica' } else { Guarda-Desfazer 'pagefile' '$c = Get-CimInstance Win32_ComputerSystem; Set-CimInstance -InputObject $c -Property @{ AutomaticManagedPagefile = $false }'; Set-CimInstance -InputObject $__c -Property @{ AutomaticManagedPagefile = $true }; $script:MUDOU++ } }''')
        if not pf(p, 'memoria.pagefile_auto', True) else None,
        Item('compressao', 'compressão de memória ligada', f'Com {gb(ram, 0)}, comprimir a memória evita usar o disco.', 'menos travadas por falta de RAM',
             'nenhum', 1, "if ($TESTE) { Plano 'ligar compressao de memoria' } else { Guarda-Desfazer 'mmc' 'Disable-MMAgent -MemoryCompression'; Enable-MMAgent -MemoryCompression; $script:MUDOU++ }")
        if pf(p, 'memoria.compressao') is False and ram < 16 else None,
        Item('sem-compressao', 'compressão de memória desligada', f'Com {gb(ram, 0)} de RAM sobra memória e comprimir só gasta CPU.',
             'um pouco menos de CPU', 'se a RAM encher, usa mais o disco', 3,
             "if ((Get-MMAgent).MemoryCompression) { if ($TESTE) { Plano 'desligar compressao de memoria' } else { Guarda-Desfazer 'mmc' 'Enable-MMAgent -MemoryCompression'; Disable-MMAgent -MemoryCompression; $script:MUDOU++ } }")
        if ram >= 32 else None,
        Item('onedrive', 'OneDrive bloqueado', 'Política que impede o OneDrive de rodar e tira ele do painel do Explorador. '
             'Sua pasta do OneDrive está vazia.', 'menos um programa sincronizando', 'não sincroniza mais nada com o OneDrive', 2,
             RR(R(f'{HKLM_POL}\\OneDrive', 'DisableFileSyncNGSC', 1), *(f"if (Test-Path {psq(k)}) {{ {R(k, 'System.IsPinnedToNameSpaceTree', 0)} }}" for k in od_ns)))
        if pf(p, 'tem.onedrive') and not pf(p, 'tem.onedrive_usado') else None,
    ]


# ═══════════════════════════════ reparar ═══════════════════════════════

def _py_reparo(rotulo, cmd, minutos, chave=None, pos=None):
    def f(ctx, it, pr, teste):
        if teste:
            ctx.t.item('○', 'azul', ' '.join(cmd), recuo=4, cor_nome='sub')
            return 1, 0
        if chave:
            ult = estado().get('reparo_' + chave)
            try:
                if ult and (datetime.now() - datetime.fromisoformat(ult)).total_seconds() < 86400:
                    ctx.t.nota(f'    {rotulo}: já feito nas últimas 24 h; pulei.')
                    return 0, 0
            except ValueError:
                pass
        cod, txt = roda_exe(cmd, minutos, pr, ctx.mult, saida_arq=pasta('relatorios') / f'{chave or rotulo}.txt')
        if cod == -1:
            ctx.t.aviso(f'{rotulo}: passou do limite e foi encerrado.')
            return 0, 1
        if chave:
            marca_estado('reparo_' + chave, agora_iso())
        msg = pos(ctx, cod, txt) if pos else None
        ctx.t.item('✓' if cod in (0, 3010) else '!', 'verde' if cod in (0, 3010) else 'amarelo',
                   msg or f'{rotulo}: código {cod}', recuo=4, cor_nome='sub')
        return 1, 0 if cod in (0, 3010) else 1
    return f


def _pos_sfc(ctx, cod, txt):
    t = txt.lower()
    if re.search(r'did not find any integrity|não encontrou nenhuma viola|nao encontrou nenhuma viola', t):
        return 'SFC: nenhum arquivo do sistema corrompido'
    if re.search(r'successfully repaired|reparou com', t):
        return 'SFC: encontrou e reparou arquivos corrompidos'
    if re.search(r'unable to fix|não pôde reparar|nao pode reparar', t):
        return 'SFC: há arquivos que não consegui reparar (veja relatorios/sfc.txt)'
    return f'SFC: código {cod}'


def _pos_chkdsk(ctx, cod, txt):
    if cod not in (0,):
        subprocess.run('echo Y| chkdsk C: /f', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return 'chkdsk: encontrou problemas; o reparo completo vai rodar no próximo reinício'
    return 'chkdsk: nenhum problema no disco'


def _pos_wmi(ctx, cod, txt):
    if re.search(r'inconsistent|inconsistente', txt, re.I):
        roda_exe(['winmgmt', '/salvagerepository'], 5)
        return 'WMI: repositório inconsistente, recuperado'
    return 'WMI: repositório em ordem'


@pacote('reparar', 'reparar', 'arquivos do sistema, disco, WMI, rede e Windows Update',
        'Ferramentas oficiais de reparo. DISM conserta a imagem do Windows, SFC confere os arquivos do sistema, chkdsk lê o disco. '
        'DISM e SFC feitos nas últimas 24 h não são refeitos. Os itens "só se marcar" são para quando algo está quebrado.')
def itens_reparar(ctx):
    return [
        Item('dism', 'reparar a imagem do Windows (DISM)', 'Baixa do Windows Update e troca componentes corrompidos.',
             'conserta erros de atualização e travamentos', 'demora (até 1 h em HD)', 1,
             py=_py_reparo('DISM', ['DISM.exe', '/Online', '/Cleanup-Image', '/RestoreHealth'], 90, 'dism')),
        Item('sfc', 'conferir arquivos do sistema (SFC)', 'Confere cada arquivo do Windows e repõe os corrompidos.',
             'conserta erros estranhos e telas azuis por arquivo corrompido', 'demora (até 45 min)', 1,
             py=_py_reparo('SFC', ['sfc.exe', '/scannow'], 45, 'sfc', _pos_sfc)),
        Item('chkdsk', 'verificar o disco (chkdsk)', 'Lê a estrutura do disco sem travar o uso. Se achar erro, agenda o reparo completo '
             'para o próximo reinício.', 'evita perda de arquivos', 'nenhum', 1,
             py=_py_reparo('chkdsk', ['chkdsk.exe', 'C:', '/scan'], 20, None, _pos_chkdsk)),
        Item('wmi', 'conferir o WMI', 'O WMI é o que programas e o próprio Windows usam para ler o hardware. Quebrado, causa CPU alta e erros.',
             'conserta CPU alta do WmiPrvSE por repositório corrompido', 'nenhum', 2,
             py=_py_reparo('WMI', ['winmgmt', '/verifyrepository'], 5, None, _pos_wmi)),
        Item('dns', 'limpar o cache de DNS', 'Esquece endereços de sites guardados.', 'conserta site que mudou de endereço e não abre',
             'nenhum', 1, "if ($TESTE) { Plano 'ipconfig /flushdns' } else { ipconfig /flushdns | Out-Null; Feito 'cache de DNS limpo' }", reverte=False),
        Item('rede-reset', 'restaurar a pilha de rede', 'Winsock e TCP/IP de volta ao padrão (netsh winsock reset e int ip reset).',
             'conserta internet que não funciona por configuração quebrada', 'precisa reiniciar; VPNs e alguns antivírus podem precisar ser reinstalados', 0,
             "if ($TESTE) { Plano 'netsh winsock reset; netsh int ip reset' } else { netsh winsock reset | Out-Null; netsh int ip reset | Out-Null; Feito 'rede restaurada: reinicie o PC' }", reverte=False),
        Item('wu-reset', 'restaurar o Windows Update', 'Para os serviços, renomeia as pastas SoftwareDistribution e catroot2 e liga de novo.',
             'conserta Windows Update preso em erro', 'o histórico de atualizações aparece vazio', 0, r'''
if ($TESTE) { Plano 'restaurar componentes do Windows Update' }
else {
  foreach ($__s in 'wuauserv','bits','cryptsvc','msiserver') { & sc.exe stop $__s 2>$null | Out-Null }
  Start-Sleep 4
  $__c = Get-Date -Format 'yyyyMMddHHmmss'
  Rename-Item "$env:WINDIR\SoftwareDistribution" "SoftwareDistribution.old-$__c" -ErrorAction SilentlyContinue
  Rename-Item "$env:WINDIR\System32\catroot2" "catroot2.old-$__c" -ErrorAction SilentlyContinue
  foreach ($__s in 'cryptsvc','bits','wuauserv') { & sc.exe start $__s 2>$null | Out-Null }
  Feito 'Windows Update restaurado'
}''', reverte=False),
        Item('loja', 'consertar a Loja', 'Limpa o cache da Microsoft Store (wsreset).', 'conserta Loja que não abre ou não baixa', 'nenhum', 0,
             "if ($TESTE) { Plano 'wsreset' } else { $r = Roda 'wsreset.exe' '' 3; Get-Process WinStore.App -ErrorAction SilentlyContinue | Stop-Process -Force; Feito 'cache da Loja limpo' }", reverte=False),
        Item('icones', 'reconstruir o cache de ícones', 'Apaga o cache de ícones e o Windows recria.', 'conserta ícones brancos ou trocados',
             'o Explorador reinicia', 0, r'''
if ($TESTE) { Plano 'reconstruir cache de icones' }
else { Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue; Start-Sleep 2
  Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Windows\Explorer" -Filter 'iconcache_*.db' -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
  Remove-Item "$env:LOCALAPPDATA\IconCache.db" -Force -ErrorAction SilentlyContinue
  Start-Process explorer.exe; Feito 'cache de icones refeito' }''', reverte=False),
        Item('menu', 'registrar de novo o menu Iniciar e a busca', 'Registra de novo os componentes do menu Iniciar, da busca e da barra.',
             'conserta menu Iniciar que não abre', 'nenhum', 0, r'''
foreach ($__n in 'Microsoft.Windows.ShellExperienceHost','Microsoft.Windows.StartMenuExperienceHost','MicrosoftWindows.Client.CBS','Microsoft.Windows.Search') {
  foreach ($x in @(Get-AppxPackage -AllUsers -Name $__n -ErrorAction SilentlyContinue)) { if ($TESTE) { Plano ('registrar ' + $__n) } else { try { Add-AppxPackage -DisableDevelopmentMode -Register (Join-Path $x.InstallLocation 'AppxManifest.xml') -ErrorAction Stop; Feito ('registrado: ' + $__n) } catch { Aviso ($__n + ': ' + $_.Exception.Message) } } }
}''', reverte=False),
    ]


# ═══════════════════════════════ atualizar ═══════════════════════════════

WU_PS = r'''
$__tipo = «tipo»
$__s = New-Object -ComObject Microsoft.Update.Session
Vivo 'procurando atualizacoes'
$__r = $__s.CreateUpdateSearcher().Search("IsInstalled=0 and IsHidden=0 and Type='$__tipo'").Updates
if ($__r.Count -eq 0) { Diz 'nada' 'nada para atualizar'; return }
$__l = New-Object -ComObject Microsoft.Update.UpdateColl
foreach ($u in $__r) { if ($TESTE) { Plano $u.Title; continue }; if (-not $u.EulaAccepted) { $u.AcceptEula() }; [void]$__l.Add($u) }
if ($TESTE) { return }
Vivo ("baixando {0} atualizacoes" -f $__l.Count)
$__d = $__s.CreateUpdateDownloader(); $__d.Updates = $__l; [void]$__d.Download()
Vivo 'instalando'
$__i = $__s.CreateUpdateInstaller(); $__i.Updates = $__l; $__x = $__i.Install()
for ($k = 0; $k -lt $__l.Count; $k++) { $rr = $__x.GetUpdateResult($k).ResultCode; if ($rr -eq 2 -or $rr -eq 3) { Feito $__l.Item($k).Title } else { Aviso ('falhou: ' + $__l.Item($k).Title) } }
if ($__x.RebootRequired) { Info 'o Windows pede reinicio para concluir' }
'''


def _py_winget(ctx, it, pr, teste):
    if teste:
        cod, txt = roda_exe(['winget', 'upgrade', '--accept-source-agreements', '--disable-interactivity'], 3, pr)
        n = len([l for l in txt.splitlines() if re.search(r'\s\d+[\d.]*\s+\d+[\d.]*\s+winget', l)])
        ctx.t.item('○', 'azul', f'winget: {n} programas com versão nova', recuo=4, cor_nome='sub')
        return 1, 0
    cod, txt = roda_exe(['winget', 'upgrade', '--all', '--silent', '--accept-source-agreements', '--accept-package-agreements',
                         '--disable-interactivity', '--include-unknown'], 60, pr, ctx.mult)
    ok = len(re.findall(r'Successfully installed|Instalado com êxito|instalado com sucesso', txt, re.I))
    ctx.t.item('✓' if cod in (0, -1978335189) else '!', 'verde' if cod == 0 else 'amarelo',
               f'winget: {ok} programas atualizados' + ('' if cod == 0 else f' (código {cod}; alguns podem ter falhado)'), recuo=4, cor_nome='sub')
    return 1, 0 if cod == 0 else 1


@pacote('atualizar', 'atualizar', 'Windows Update, drivers, Defender, programas e apps da Loja',
        'Atualiza pelo próprio Windows Update (sem desligar nada dele) e pelo winget. Só versões estáveis.', reversivel=False)
def itens_atualizar(ctx):
    return [
        Item('defender', 'definições do Defender', 'Baixa as definições de vírus mais novas.', 'proteção em dia', 'nenhum', 1,
             "if ($TESTE) { Plano 'Update-MpSignature' } else { try { Update-MpSignature -ErrorAction Stop; Feito 'Defender atualizado' } catch { Aviso ('Defender: ' + $_.Exception.Message) } }",
             minutos=10, reverte=False),
        Item('windows', 'atualizações do Windows', 'Procura, baixa e instala as atualizações pendentes do Windows Update.',
             'segurança e correções', 'demora; pode pedir reinício', 1, ps_monta(WU_PS, tipo="'Software'"), minutos=120, sozinho=True, reverte=False),
        Item('drivers', 'drivers pelo Windows Update', 'Drivers que o Windows Update oferece para este PC.',
             'drivers mais novos e certificados', 'raramente um driver novo traz problema (dá para voltar no Gerenciador de Dispositivos)', 2,
             ps_monta(WU_PS, tipo="'Driver'"), minutos=60, sozinho=True, reverte=False),
        Item('winget', 'programas pelo winget', 'Atualiza os programas instalados que o winget conhece.', 'programas em dia e mais seguros',
             'alguns programas mudam de versão principal', 2, py=_py_winget, reverte=False) if pf(ctx.perfil, 'tem.winget', True) else None,
        Item('loja', 'apps da Loja', 'Pede à Microsoft Store para atualizar os apps.', 'apps em dia', 'nenhum', 2, r'''
if ($TESTE) { Plano 'atualizar apps da Loja' } else { try { Get-CimInstance -Namespace 'root\cimv2\mdm\dmmap' -ClassName 'MDM_EnterpriseModernAppManagement_AppManagement01' -ErrorAction Stop | Invoke-CimMethod -MethodName UpdateScanMethod -ErrorAction Stop | Out-Null; Feito 'Loja verificando atualizacoes' } catch { Aviso 'a Loja nao aceitou o pedido; abra a Loja > Biblioteca' } }''',
             reverte=False),
    ]


# ═══════════════════════════════ interface ═══════════════════════════════

@pacote('interface', 'área de trabalho e menu', 'Edge escondido, área de trabalho limpa, Destaque do Windows',
        'Arrumação visual. Atalhos tirados da área de trabalho vão para o backup e voltam com o desfazer.')
def itens_interface(ctx):
    p = ctx.perfil
    icones = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\HideDesktopIcons\\NewStartPanel'
    edge_lnk = r'''foreach ($__l in @(Get-ChildItem ([Environment]::GetFolderPath('Desktop')), "$env:PUBLIC\Desktop" -Filter 'Microsoft Edge*.lnk' -Force -ErrorAction SilentlyContinue)) { Guarda-Arquivo $__l.FullName | Out-Null }'''
    limpa = r'''foreach ($__d in @([Environment]::GetFolderPath('Desktop'), "$env:PUBLIC\Desktop")) { foreach ($__l in @(Get-ChildItem -LiteralPath $__d -Force -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in '.lnk','.url' })) { Guarda-Arquivo $__l.FullName | Out-Null } }'''
    return [
        Item('edge-atalhos', 'atalhos do Edge fora da área de trabalho', 'Tira os atalhos do Edge que o Windows recoloca.',
             'área de trabalho limpa', 'nenhum (o Edge continua no menu)', 2, edge_lnk) if pf(p, 'tem.edge', True) else None,
        Item('destaque', 'sem "Saiba mais sobre esta foto"', 'Esconde o ícone do Windows Destaque e desliga o recurso na área de trabalho.',
             'área de trabalho limpa', 'sem papel de parede do Bing trocando', 1,
             RR(R(icones, '{2cc5ca98-6485-489a-920e-b3e88a6ccce3}', 1), R(f'{HKCU_POL}\\CloudContent', 'DisableSpotlightCollectionOnDesktop', 1))),
        Item('este-pc', 'ícone "Este Computador" na área de trabalho', 'Mostra o atalho para os discos.', 'acesso rápido', 'nenhum', 2,
             R(icones, '{20D04FE0-3AEA-1069-A2D8-08002B30309D}', 0)),
        Item('limpa', 'área de trabalho só com a Lixeira', 'Todos os atalhos (.lnk e .url) da área de trabalho vão para o backup. '
             'Arquivos e pastas seus ficam.', 'visual limpo', 'você abre programas pelo menu Iniciar', 3, limpa),
    ]


# ═══════════════════════════════ navegador ═══════════════════════════════

def _brave_pol():
    b = 'HKLM:\\SOFTWARE\\Policies\\BraveSoftware\\Brave'
    return RR(R(b, 'BraveRewardsDisabled', 1), R(b, 'BraveWalletDisabled', 1), R(b, 'BraveVPNDisabled', 1), R(b, 'BraveAIChatEnabled', 0),
              R(b, 'BackgroundModeEnabled', 0), R(b, 'HighEfficiencyModeEnabled', 1), R(b, 'MetricsReportingEnabled', 0),
              R(b, 'BraveNewsDisabled', 1), R(b, 'TorDisabled', 1))


@pacote('navegador', 'navegador', 'navegadores mais leves e Brave enxuto',
        'Políticas oficiais de cada navegador: sem rodar em segundo plano, economia de memória ligada, sem métricas. O navegador '
        'mostra "Gerenciado pela sua organização". O Brave foi o escolhido no cofre para PC fraco.')
def itens_navegador(ctx):
    p = ctx.perfil
    tem = p.get('tem') or {}
    ch = 'HKLM:\\SOFTWARE\\Policies\\Google\\Chrome'

    def instala_brave(ctx, it, pr, teste):
        if teste:
            ctx.t.item('○', 'azul', 'winget install Brave.Brave', recuo=4, cor_nome='sub')
            return 1, 0
        cod, _ = roda_exe(['winget', 'install', '--id', 'Brave.Brave', '--exact', '--silent', '--accept-source-agreements',
                           '--accept-package-agreements', '--disable-interactivity'], 15, pr, ctx.mult)
        ctx.t.item('✓' if cod == 0 else '!', 'verde' if cod == 0 else 'amarelo', 'Brave instalado' if cod == 0 else f'Brave: código {cod} (baixe em brave.com)', recuo=4, cor_nome='sub')
        return (1, 0) if cod == 0 else (0, 1)

    return [
        Item('brave', 'instalar o Brave', 'Navegador leve (base do Chrome, bloqueador de anúncios embutido), pelo winget.',
             'menos RAM que Chrome e Edge', 'mais um programa', 2 if config('navegador') == 'brave' else 0, py=instala_brave, reverte=False)
        if not tem.get('brave') else None,
        Item('brave-pol', 'Brave enxuto', 'Sem Rewards, Wallet, VPN, IA, notícias, Tor e segundo plano; economia de memória ligada. '
             'As atualizações de segurança continuam.', 'Brave mais leve', 'perde esses recursos do Brave', 1, _brave_pol()),
        Item('chrome', 'Chrome enxuto', 'Sem continuar aberto depois de fechado, economia de memória ligada, sem métricas e sem modelo de IA local.',
             'menos RAM', 'aparece "Gerenciado pela organização"', 1,
             RR(R(ch, 'BackgroundModeEnabled', 0), R(ch, 'HighEfficiencyModeEnabled', 1), R(ch, 'MetricsReportingEnabled', 0),
                R(ch, 'GenAILocalFoundationalModelSettings', 1), R(ch, 'ChromeCleanupReportingEnabled', 0), R(ch, 'UserFeedbackAllowed', 0),
                R(ch, 'DeviceMetricsReportingEnabled', 0))) if tem.get('chrome') else None,
        Item('edge', 'Edge enxuto', 'Sem pré-carregar, sem segundo plano, sem barra lateral, sem assistente de compras, sem recomendações '
             'e sem primeira execução.', 'menos RAM e propaganda', 'aparece "Gerenciado pela organização"', 1,
             RR(R(EDGE_POL, 'StartupBoostEnabled', 0), R(EDGE_POL, 'BackgroundModeEnabled', 0), R(EDGE_POL, 'HubsSidebarEnabled', 0),
                R(EDGE_POL, 'EdgeShoppingAssistantEnabled', 0), R(EDGE_POL, 'ShowRecommendationsEnabled', 0),
                R(EDGE_POL, 'PersonalizationReportingEnabled', 0), R(EDGE_POL, 'HideFirstRunExperience', 1),
                R(EDGE_POL, 'SpotlightExperiencesAndRecommendationsEnabled', 0), R(EDGE_POL, 'DiagnosticData', 0),
                R(EDGE_POL, 'MetricsReportingEnabled', 0), R(EDGE_POL, 'UserFeedbackAllowed', 0), R(EDGE_POL, 'Edge3PSerpTelemetryEnabled', 0))) if tem.get('edge', True) else None,
    ]


# ═══════════════════════════════ rede ═══════════════════════════════

DNS = [('cloudflare', 'Cloudflare', '1.1.1.1', '1.0.0.1', 'o mais rápido na maioria dos lugares do Brasil'),
       ('google', 'Google', '8.8.8.8', '8.8.4.4', 'estável e rápido'),
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


def _py_ping(ctx, it, pr, teste):
    """Mede a latência até o roteador e os DNS públicos, para escolher com número."""
    alvos = [('roteador', None)] + [(nome, ip) for _, nome, ip, _, _ in DNS[:4]]
    if WINDOWS:
        s = roda_ps(ctx.t, "Dado 'gw' ([string](Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | Sort-Object RouteMetric | Select-Object -First 1).NextHop)", 'gw', minutos=1, mostra=False)
        alvos[0] = ('roteador', s.dados.get('gw') or None)
    linhas = []
    for nome, ip in alvos:
        if not ip:
            continue
        pr.atual = f'ping {ip}'
        args = ['ping', '-n', '6', '-w', '1000', ip] if WINDOWS else ['ping', '-c', '6', '-W', '1', ip]
        cod, txt = roda_exe(args, 1, pr)
        ms = [int(x) for x in re.findall(r'(?:tempo|time)[=<](\d+)', txt, re.I)]
        perda = 100 - 100 * len(ms) // 6
        linhas.append([f'{nome} ({ip})', f'{sum(ms) // len(ms)} ms' if ms else '-', f'{min(ms)}–{max(ms)} ms' if ms else '-', f'{perda}%'])
    ctx.t.tabela(['destino', 'média', 'variação', 'perda'], linhas, alinha='eddd')
    ctx.t.paragrafo('Roteador acima de 5 ms ou perda no roteador = problema no Wi-Fi ou no cabo, não na internet. '
                    'Variação alta é o que causa "lag" em jogos.', 4, 'apagado')
    return 0, 0


@pacote('rede', 'rede e DNS', 'DNS mais rápido ou com bloqueio, medição de ping',
        'Troca o DNS de todas as placas de rede ligadas (o desfazer volta o que estava antes). Mede o ping até o roteador '
        'e os DNS públicos para você decidir com número. Ajustes de TCP "milagrosos" não estão aqui: não têm ganho medido.')
def itens_rede(ctx):
    itens = [Item('ping', 'medir o ping', 'Ping até o roteador e até Cloudflare, Google, Quad9 e AdGuard.', 'decidir com número',
                  'nenhum', 1, py=_py_ping, reverte=False)]
    for id_, nome, a, b, desc in DNS:
        itens.append(Item('dns-' + id_, f'DNS {nome} ({a})', f'Usa o DNS {nome}: {desc}.', 'sites resolvem mais rápido que no DNS da operadora',
                          'redes de empresa com DNS próprio param de achar os servidores internos', 2 if id_ == 'cloudflare' else 0,
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
        Item('caixas', 'caixas de seleção nos arquivos', 'Uma caixinha para marcar vários arquivos sem segurar Ctrl.', 'útil em tela de toque',
             'nenhum', 0, R(ADV, 'AutoCheckSelect', 1)),
    ]


# ███████████████████████████████████████████████████████████████████████████
#
#   PARTE 4 · TURBO, MANUTENÇÃO, REVERSÃO E UTILIDADES
#
# ███████████████████████████████████████████████████████████████████████████

ARQ_TURBO = CASA / 'turbo.json'
TAREFA_CONTINUAR = 'Katharos - continuar depois de reiniciar'
TAREFA_MANUT = 'Katharos - manutencao semanal'

# ordem do turbo: o que libera recursos primeiro, depois reparo e atualização, limpeza, disco e o reinício
ORDEM_TURBO = ['programas', 'apps', 'ia', 'inicializacao', 'servicos', 'privacidade', 'visual', 'jogos', 'energia',
               'reparar', 'atualizar', 'limpar', 'disco', 'navegador', 'interface']
NIVEL_PACOTE = {'programas': 1, 'apps': 1, 'ia': 2, 'inicializacao': 1, 'servicos': 1, 'privacidade': 1, 'visual': 2,
                'jogos': 3, 'energia': 1, 'reparar': 1, 'atualizar': 1, 'limpar': 1, 'disco': 1, 'navegador': 2, 'interface': 3}


def _espera_bateria(t):
    na_tomada, carga = energia_agora()
    avisou = False
    while not na_tomada and carga is not None and carga < 40:
        if not avisou:
            t.aviso(f'Bateria em {carga}% e fora da tomada: ligue o carregador. Esperando...')
            avisou = True
        time.sleep(30)
        na_tomada, carga = energia_agora()


def tarefa_continuar(ctx, criar=True):
    """Tarefa agendada de uma vez: depois do reinício, no seu logon, abre o turbo de novo como administrador
    (sem lançador escondido: uma janela normal do PowerShell chamando o Python)."""
    script = CASA / 'katharos.py'
    try:
        shutil.copy2(Path(__file__).resolve(), script)
    except OSError:
        script = Path(__file__).resolve()
    if criar:
        cmd = (f"& {psq(sys.executable)} {psq(str(script))} turbo --continuar; Read-Host 'Enter para fechar'")
        corpo = ps_monta(r'''
$__a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -Command "' + «cmd» + '"')
$__t = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$__p = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
$__s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 8)
Register-ScheduledTask -TaskName «nome» -Action $__a -Trigger $__t -Principal $__p -Settings $__s -Force | Out-Null
Ok 'o katharos vai continuar sozinho depois do reinicio, quando voce entrar na conta'
''', cmd=psq(cmd.replace('"', '\\"')), nome=psq(TAREFA_CONTINUAR))
    else:
        corpo = f"Unregister-ScheduledTask -TaskName {psq(TAREFA_CONTINUAR)} -Confirm:$false -ErrorAction SilentlyContinue"
    roda_ps(ctx.t, corpo, 'tarefa-continuar', minutos=2, mostra=criar)


def _resumo_pacotes(t):
    for nome in ORDEM_TURBO:
        pac = PACOTES[nome]
        t.item('·', 'apagado', pac.titulo, t.p(pac.resumo, 'apagado'))


def escolhe_modo(t, args):
    if getattr(args, 'modo', None):
        return args.modo
    padrao = config('modo')
    t.titulo('modo')
    for i, (nome, cor, txt) in enumerate(EXPLICA_MODOS, 1):
        marca = t.p(' (padrão)', 'apagado') if nome == padrao else ''
        t.escreve(f'  {t.p(f"{i:>2}", "destaque", True)}  {t.p(nome, cor, True)}{marca}')
        t.paragrafo(txt, 6, 'sub')
    t.escreve()
    if getattr(args, 'sim', False) or not t.interativo:
        return padrao
    r = t.pergunta('modo (número ou nome, Enter = ' + padrao + ')').strip().lower()
    return {'1': 'seguro', '2': 'equilibrado', '3': 'extremo'}.get(r, r if r in MODOS else padrao)


def ferramenta_turbo(ctx, args):
    t = ctx.t
    t.aba('otimiza tudo em sequência; continua sozinho depois de reiniciar')
    if not precisa_admin(ctx, args):
        return 1
    plano = le_json(ARQ_TURBO, None)
    if plano and not plano.get('concluido') and (getattr(args, 'continuar', False) or (t.interativo and not args.teste and
            t.pergunta(f'há um turbo de {str(plano.get("criado", ""))[:10]} pela metade. continuar? s = sim, Enter = começar outro')
            .strip().lower() in ('s', 'sim'))):
        return executa_turbo(ctx, args, plano)
    if getattr(args, 'continuar', False):
        t.nota('nada pela metade para continuar.')
        tarefa_continuar(ctx, criar=False)
        return 0
    t.paragrafo('O turbo junta tudo: cria um ponto de restauração, mede o PC, aplica os pacotes que você escolher, '
                'reinicia e mede de novo. Cada etapa tem limite de tempo (dobrado em HD); se uma travar, ela é encerrada '
                'e o resto segue. Depois do reinício ele continua sozinho de onde parou.', 2, 'sub')
    p = perfil_pc(ctx)
    if not confere_conta(ctx) and not args.teste:
        return 1
    if getattr(args, 'plano', None):
        base = le_json(args.plano, None)
        if not base or 'etapas' not in base:
            t.erro(f'não consegui ler o plano {args.plano}.')
            return 1
        plano = {'criado': agora_iso(), 'modo': base.get('modo', 'equilibrado'), 'etapas': base['etapas'], 'itens': base.get('itens', {}),
                 'feitas': [], 'tentativas': {}, 'concluido': False}
        t.info(f'plano de {caminho_curto(args.plano)}: modo {plano["modo"]}, {pl(len(plano["etapas"]), "etapa")}.')
        if args.teste:
            return 0
        if not t.confirma('Aplicar esse plano neste PC?', sim=args.sim):
            return 0
        grava_json(ARQ_TURBO, plano)
        return executa_turbo(ctx, args, plano)
    modo = escolhe_modo(t, args)
    t.escreve()
    itens = []
    for nome in ORDEM_TURBO:
        pac = PACOTES[nome]
        n = NIVEL_PACOTE[nome]
        nota = ''
        if nome == 'jogos' and joga(p):
            n, nota = 2, 'tem jogos instalados'
        if nome == 'navegador' and config('navegador') == 'brave':
            n = 1
        itens.append(Item(nome, pac.titulo, pac.explica, pac.resumo, '', n, nota=nota))
    itens.append(Item('agendar', 'manutenção semanal automática', 'Tarefa leve que roda com o PC ocioso e na tomada: limpa, '
                      'reaplica o que atualizações desfazem e avisa de problemas de disco.', 'o PC continua leve', 'nenhum', 1))
    itens.append(Item('reinicio', 'reiniciar e medir de novo', 'Reinicia no fim, continua sozinho depois do logon e mede '
                      'o antes e depois com o PC parado.', 'mudanças valem por completo; números reais', 'o PC reinicia', 1))
    escolhidos = escolhe_itens(ctx, itens, modo, args, 'etapas')
    if not escolhidos:
        t.nota('nada escolhido.')
        return 0
    detalhar = False
    if t.interativo and not args.sim:
        t.paragrafo('Quer revisar item por item de cada etapa agora? Sem revisar, cada etapa usa o que o modo '
                    f'{modo} marca. s = revisar, Enter = usar o modo', 2, 'apagado')
        detalhar = t.pergunta('revisar').strip().lower() in ('s', 'sim')
    plano = {'criado': agora_iso(), 'modo': modo, 'etapas': ['medir-antes'] + [i.id for i in escolhidos if i.id != 'reinicio'],
             'itens': {}, 'feitas': [], 'tentativas': {}, 'concluido': False}
    if any(i.id == 'reinicio' for i in escolhidos):
        plano['etapas'] += ['reinicio', 'medir-depois']
    else:
        plano['etapas'] += ['medir-depois']
    if detalhar:
        for i in escolhidos:
            if i.id in PACOTES:
                t.titulo(f'revisar: {PACOTES[i.id].titulo}')
                t.paragrafo(PACOTES[i.id].explica, 2, 'sub')
                its = [x for x in (PACOTES[i.id].itens(ctx) or []) if x]
                if not its:
                    t.nota('nada a fazer aqui neste PC.')
                    continue
                sel = escolhe_itens(ctx, its, modo, args)
                plano['itens'][i.id] = [x.id for x in (sel or [])]
    t.titulo('plano')
    t.passos([('pendente', e if e not in PACOTES else PACOTES[e].titulo,
               ('' if e not in plano['itens'] else pl(len(plano['itens'][e]), 'item', 'itens'))) for e in plano['etapas']])
    if args.teste:
        t.escreve()
        t.nota('modo teste: mostrando o que cada etapa faria.')
        for e in plano['etapas']:
            if e in PACOTES:
                its = _itens_da_etapa(ctx, plano, e)
                if its:
                    t.titulo(PACOTES[e].titulo)
                    executa_itens(ctx, PACOTES[e], its, teste=True)
        return 0
    if not t.confirma(f'Começar o turbo no modo {modo}?', sim=args.sim):
        t.nota('nada foi alterado.')
        return 0
    grava_json(ARQ_TURBO, plano)
    copia = pasta('relatorios') / f'plano-{datetime.now():%Y-%m-%d}.json'
    grava_json(copia, {k: plano[k] for k in ('modo', 'etapas', 'itens')})
    t.nota(f'  plano salvo em {caminho_curto(copia)}: em outro PC, rode "katharos turbo --plano" com esse arquivo.')
    return executa_turbo(ctx, args, plano)


def _itens_da_etapa(ctx, plano, etapa):
    its = [x for x in (PACOTES[etapa].itens(ctx) or []) if x]
    if etapa in plano.get('itens', {}):
        ids = set(plano['itens'][etapa])
        return [x for x in its if x.id in ids]
    marca_por_modo(its, plano['modo'])
    return [x for x in its if x.marcado]


def executa_turbo(ctx, args, plano):
    t = ctx.t
    desliga_edicao_rapida()
    perfil_pc(ctx)
    pid_arq = CASA / 'turbo.pid'
    if pid_arq.exists():
        try:
            outro = int(pid_arq.read_text())
            if outro != os.getpid() and WINDOWS and str(outro) in subprocess.run(['tasklist', '/FI', f'PID eq {outro}'], capture_output=True, text=True).stdout:
                t.aviso('O turbo já está rodando em outra janela. Espere ele terminar.')
                return 0
        except (ValueError, OSError):
            pass
    pid_arq.write_text(str(os.getpid()))
    if t.guia:
        t.fim('começando o turbo', 'nada')
    try:
        garante_ponto(ctx)
        total = len(plano['etapas'])
        for n, etapa in enumerate(plano['etapas'], 1):
            nome = PACOTES[etapa].titulo if etapa in PACOTES else etapa
            if etapa in plano['feitas']:
                continue
            tent = plano['tentativas'].get(etapa, 0)
            if tent >= 3:
                t.aviso(f'{nome}: interrompida 3 vezes; pulei.')
                plano['feitas'].append(etapa)
                grava_json(ARQ_TURBO, plano)
                continue
            plano['tentativas'][etapa] = tent + 1
            grava_json(ARQ_TURBO, plano)
            _espera_bateria(t)
            t.cabecalho(f'turbo › {nome}', f'etapa {n} de {total} · modo {plano["modo"]}', app=APP)
            if etapa == 'medir-antes':
                m = mede(ctx, 'medindo antes')
                salva_medida(m, 'antes')
                plano['antes'] = m
                mostra_medidas(t, m)
            elif etapa == 'medir-depois':
                if t.tty:
                    with Progresso(t, None, 'esperando 2 min de repouso para medir de forma justa') as pr:
                        fim = time.time() + 120
                        while time.time() < fim:
                            pr.atual = f'{int(fim - time.time())} s'
                            time.sleep(1)
                m = mede(ctx, 'medindo depois')
                salva_medida(m, 'depois')
                plano['depois'] = m
                t.titulo('antes e depois')
                mostra_medidas(t, m, plano.get('antes') or {})
            elif etapa == 'agendar':
                instala_manutencao(ctx)
            elif etapa == 'reinicio':
                plano['feitas'].append(etapa)
                grava_json(ARQ_TURBO, plano)
                tarefa_continuar(ctx, criar=True)
                t.aviso('Reiniciando em 60 s. Salve o que estiver aberto. Para cancelar: shutdown /a')
                t.fim('reiniciando', 'aviso')
                subprocess.run(['shutdown', '/r', '/t', '60', '/c', 'Katharos: o turbo continua sozinho depois que você entrar.'])
                return 0
            else:
                its = _itens_da_etapa(ctx, plano, etapa)
                if its:
                    feitos, avisos, erros = executa_itens(ctx, PACOTES[etapa], its)
                    t.nota(f'  {feitos} alterados · {avisos} avisos · {erros} erros')
                    if etapa in ('visual', 'interface'):
                        roda_ps(t, 'Reinicia-Explorer', 'explorer', minutos=1, mostra=False)
                else:
                    t.nota('nada a fazer nesta etapa.')
            plano['feitas'].append(etapa)
            grava_json(ARQ_TURBO, plano)
            t.fim(f'{nome} pronto', 'ok')
        plano['concluido'] = True
        grava_json(ARQ_TURBO, plano)
        tarefa_continuar(ctx, criar=False)
        arq = pasta('relatorios') / f'turbo-{datetime.now():%Y-%m-%d}.md'
        _relatorio_turbo(plano, arq)
        t.cabecalho('turbo', 'concluído', app=APP)
        t.titulo('resumo', caixa=True)
        t.chaves([('modo', plano['modo']), ('etapas', str(len(plano['feitas']))), ('desfazer', 'katharos desfazer PACOTE')])
        t.relatorio(arq, recuo=2)
        return 0
    finally:
        try:
            pid_arq.unlink()
        except OSError:
            pass


def _relatorio_turbo(plano, arq):
    a, d = plano.get('antes') or {}, plano.get('depois') or {}
    L = [f'# Turbo de {datetime.now():%d/%m/%Y}', '', f'Modo {plano["modo"]}. Etapas: ' + ', '.join(plano['feitas']) + '.', '',
         '| Medida | Antes | Depois |', '|---|---|---|']
    for chave, rot, un, _ in LINHAS_MEDIDA:
        L.append(f'| {rot} | {_fmt_medida(a.get(chave), un)} | {_fmt_medida(d.get(chave), un)} |')
    L += ['', 'Para desfazer um pacote: `katharos desfazer NOME` (ou `tudo`). Ponto de restauração: "Antes do Katharos".',
          'Programas e apps removidos não voltam pelo desfazer: reinstale pela Loja ou pelo site.']
    arq.write_text('\n'.join(L) + '\n', encoding='utf-8')


# ─────────────── manutenção semanal ───────────────

REAPLICA = ('privacidade', 'ia', 'servicos', 'visual', 'energia', 'disco', 'jogos', 'navegador', 'interface')

MANUT_PS = r'''
$__alertas = New-Object System.Collections.Generic.List[string]
function Alerta([string]$T) { $__alertas.Add($T); Aviso $T }
$__livre = 0
Vivo 'limpeza leve'
foreach ($__p in @(@($env:TEMP, 7), @("$env:WINDIR\Temp", 7), @("$env:LOCALAPPDATA\CrashDumps", 7), @("$env:WINDIR\Minidump", 30), @("$env:ProgramData\Microsoft\Windows\WER\ReportArchive", 7), @("$env:ProgramData\Microsoft\Windows\WER\ReportQueue", 7), @("$env:LOCALAPPDATA\Microsoft\Windows\WER", 7), @("$env:WINDIR\Logs\CBS", 30))) { $__livre += LimpaAntigos $__p[0] $__p[1] }
$__pend = (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending') -or (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired')
if (-not $__pend) { $__livre += LimpaAntigos "$env:WINDIR\SoftwareDistribution\Download" 14 }
$__th = @(Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Windows\Explorer" -Filter 'thumbcache_*.db' -Force -ErrorAction SilentlyContinue)
if (($__th | Measure-Object Length -Sum).Sum -gt 200MB) { foreach ($f in $__th) { $l = $f.Length; Remove-Item -LiteralPath $f.FullName -Force -ErrorAction SilentlyContinue; if (-not (Test-Path -LiteralPath $f.FullName)) { $__livre += $l } } }
foreach ($par in @(@('brave', "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\User Data\Default\Cache"), @('chrome', "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache"), @('msedge', "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache"))) {
  if (-not (Get-Process $par[0] -ErrorAction SilentlyContinue) -and (TamanhoPasta $par[1]) -gt 500MB) { $__livre += LimpaAntigos $par[1] 0 }
}
Dado 'livre' $__livre

Vivo 'antivirus'
try {
  $mp = Get-MpComputerStatus -ErrorAction Stop
  if (-not $mp.RealTimeProtectionEnabled) { Alerta 'Defender sem protecao em tempo real. Abra Seguranca do Windows.' }
  $mpc = "$env:ProgramFiles\Windows Defender\MpCmdRun.exe"
  if ($mp.AntivirusSignatureAge -gt 2 -and (Test-Path $mpc)) { $c = Roda $mpc '-SignatureUpdate' 10; if ($c -ne 0) { Alerta ("Definicoes do Defender com {0} dias" -f $mp.AntivirusSignatureAge) } }
  if ($mp.QuickScanAge -gt 14 -and (Test-Path $mpc)) { $c = Roda $mpc '-Scan -ScanType 1' 30; if ($c -eq 2) { Alerta 'A verificacao rapida encontrou ameacas. Abra Seguranca do Windows.' } }
} catch { Alerta 'Nao consegui ler o Defender' }

Vivo 'saude do disco'
if (Tenta { Get-CimInstance -Namespace root\wmi -ClassName MSStorageDriver_FailurePredictStatus -ErrorAction Stop | Where-Object PredictFailure } $null) { Alerta 'O disco indica falha iminente. Faca backup agora.' }
$__erros = @(Get-PhysicalDisk | Get-StorageReliabilityCounter -ErrorAction SilentlyContinue | ForEach-Object { [int]$_.ReadErrorsTotal })
Dado 'erros_leitura' (($__erros | Measure-Object -Sum).Sum)
$__sem = (Get-Date).AddDays(-7)
$__d = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; ProviderName = 'disk','Ntfs','storahci','stornvme','iaStorA'; Level = 1,2; StartTime = $__sem } -ErrorAction SilentlyContinue).Count
if ($__d) { Alerta ("{0} erro(s) de disco nesta semana" -f $__d) }
$__c = @(Get-WinEvent -FilterHashtable @{ LogName = 'System'; Id = 41,1001,6008; StartTime = $__sem } -ErrorAction SilentlyContinue).Count
if ($__c) { Alerta ("{0} desligamento(s) inesperado(s) ou tela azul nesta semana" -f $__c) }
$__ld = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
$__pct = [math]::Round($__ld.FreeSpace / $__ld.Size * 100)
if ($__pct -lt 15) { Alerta ("Pouco espaco livre em C: ({0}%)" -f $__pct) }
Dado 'livre_pct' $__pct
Dado 'pendente' $__pend
$__dt = Get-ScheduledTask -TaskPath '\Microsoft\Windows\Defrag\' -TaskName 'ScheduledDefrag' -ErrorAction SilentlyContinue
if ($__dt -and $__dt.State -eq 'Disabled') { $__dt | Enable-ScheduledTask | Out-Null; Info 'otimizacao semanal de disco religada' }
Dado 'alertas' (Lista $__alertas.ToArray())
'''

MENSAL_PS = r'''
try { Checkpoint-Computer -Description 'Manutencao mensal do Katharos' -RestorePointType MODIFY_SETTINGS -ErrorAction Stop; Ok 'ponto de restauracao mensal criado' } catch { Info ('ponto mensal nao criado: ' + $_.Exception.Message) }
try { Delete-DeliveryOptimizationCache -Force -ErrorAction Stop } catch {}
'''

TOAST_PS = r'''
try {
  [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
  $tpl = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
  $n = $tpl.GetElementsByTagName('text')
  [void]$n.Item(0).AppendChild($tpl.CreateTextNode(«titulo»))
  [void]$n.Item(1).AppendChild($tpl.CreateTextNode(«texto»))
  $app = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
  [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app).Show([Windows.UI.Notifications.ToastNotification]::new($tpl))
} catch {}
'''


def ferramenta_manutencao(ctx, args):
    """A manutenção em si: roda pela tarefa agendada (ou pelo menu do agendar, para testar)."""
    t = ctx.t
    t.aba('limpeza leve, reaplica o que atualizações desfazem e confere a saúde do PC')
    if not WINDOWS:
        t.erro('só funciona no Windows.')
        return 1
    if getattr(args, 'agendada', False):
        prioridade_baixa()
        na_tomada, _ = energia_agora()
        if not na_tomada:
            LOG.escreve('manutenção adiada: na bateria')
            return 0
    inicio = time.time()
    p = perfil_pc(ctx)
    e = estado()
    reapl = 0
    with Progresso(t, None, 'manutenção') as pr:
        s = roda_ps(t, MANUT_PS, 'manutencao', minutos=45, pr=pr, mult=1.0, mostra=not getattr(args, 'agendada', False))
        alertas = lista(s.dados.get('alertas'))
        erros_ant = e.get('manut_erros_leitura')
        erros = s.dados.get('erros_leitura')
        if isinstance(erros_ant, int) and isinstance(erros, int) and erros > erros_ant:
            alertas.append(f'Erros de leitura do disco subiram de {erros_ant} para {erros}. Faça backup.')
        if isinstance(erros, int):
            e['manut_erros_leitura'] = erros
        if s.dados.get('pendente'):
            e.setdefault('manut_pendente_desde', agora_iso())
            try:
                if (datetime.now() - datetime.fromisoformat(e['manut_pendente_desde'])).days >= 3:
                    alertas.append('Há atualizações esperando reinício há mais de 3 dias. Reinicie o PC.')
            except ValueError:
                pass
        else:
            e.pop('manut_pendente_desde', None)
        # reaplica o que pertence a cada pacote ainda ativo (grandes atualizações religam serviços e sugestões)
        for nome, reg in (e.get('pacotes') or {}).items():
            if nome not in REAPLICA or reg.get('revertido') or time.time() - inicio > 40 * 60:
                continue
            ids = set(reg.get('itens', []))
            its = [i for i in (PACOTES[nome].itens(ctx) or []) if i and i.id in ids and i.ps and not i.py and not i.sozinho]
            if not its:
                continue
            pr.atual = f'reaplicando {PACOTES[nome].titulo}'
            corpo = '\n'.join(_envolve(i) for i in its)
            r = roda_ps(t, corpo, f'reaplica-{nome}', minutos=8, pacote=nome, pr=pr, mostra=False)
            reapl += len(r.feitos)
        ult = e.get('manut_mensal')
        mensal = True
        try:
            mensal = not ult or (datetime.now() - datetime.fromisoformat(ult)).days >= 30
        except ValueError:
            pass
        if mensal and time.time() - inicio < 35 * 60:
            pr.atual = 'mensal: ponto de restauração e limpeza de componentes'
            roda_ps(t, MENSAL_PS, 'mensal', minutos=10, pr=pr, mostra=False)
            cod, _ = roda_exe(['DISM.exe', '/Online', '/Cleanup-Image', '/StartComponentCleanup'], 35, pr)
            if cod != -1:
                e['manut_mensal'] = agora_iso()
    livre = s.dados.get('livre') or 0
    e['manut_ultima'] = agora_iso()
    salva_estado(e)
    dur = time.time() - inicio
    linhas = [f'Última manutenção: {datetime.now():%d/%m/%Y %H:%M} ({duracao(dur)})',
              f'Espaço liberado: {humano(livre)} · livre em C: {s.dados.get("livre_pct", "?")}%',
              f'Configurações reaplicadas: {reapl}', '', 'ALERTAS:' if alertas else 'Nenhum alerta. Tudo certo.'] + [f'- {a}' for a in alertas]
    (pasta('relatorios') / 'manutencao-status.txt').write_text('\n'.join(linhas) + '\n', encoding='utf-8')
    LOG.escreve(f'manutenção: {humano(livre)} liberados, {reapl} reaplicadas, {len(alertas)} alertas')
    if alertas:
        roda_ps(t, ps_monta(TOAST_PS, titulo=psq('Katharos'), texto=psq(f'{len(alertas)} alerta(s): {alertas[0]}')), 'aviso', minutos=1, mostra=False)
    t.titulo('resumo', caixa=True)
    t.chaves([('liberado', humano(livre)), ('reaplicadas', str(reapl)), ('alertas', t.p(str(len(alertas)), 'amarelo' if alertas else 'verde'))])
    t.relatorio(pasta('relatorios') / 'manutencao-status.txt', recuo=2)
    return 0


def instala_manutencao(ctx):
    script = CASA / 'katharos.py'
    shutil.copy2(Path(__file__).resolve(), script)
    py = sys.executable
    if py.lower().endswith('pythonw.exe'):
        py = py[:-5] + '.exe'
    cmd = f"& {psq(py)} {psq(str(script))} manutencao --agendada --sem-cor"
    corpo = ps_monta(r'''
$__a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -WindowStyle Minimized -Command "' + «cmd» + '"')
$__t = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At '12:00'
$__p = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
$__s = New-ScheduledTaskSettingsSet -RunOnlyIfIdle -IdleDuration (New-TimeSpan -Minutes 10) -IdleWaitTimeout (New-TimeSpan -Hours 12) -RestartOnIdle -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1) -Priority 7 -MultipleInstances IgnoreNew
if ($TESTE) { Plano 'criar a tarefa de manutencao semanal'; return }
Register-ScheduledTask -TaskName «nome» -Action $__a -Trigger $__t -Principal $__p -Settings $__s -Description 'Limpeza leve, saude do disco e reaplicacao das otimizacoes. Criada pelo Katharos.' -Force | Out-Null
Feito 'manutencao agendada: domingo ao meio-dia, ou na proxima vez que o PC ficar ocioso 10 min na tomada'
''', cmd=psq(cmd.replace('"', '\\"')), nome=psq(TAREFA_MANUT))
    s = roda_ps(ctx.t, corpo, 'agendar', minutos=2)
    return 0 if s.ok and not s.erros else 1


def ferramenta_agendar(ctx, args):
    t = ctx.t
    t.aba('manutenção semanal automática, leve e silenciosa')
    t.paragrafo('Roda no domingo ao meio-dia (ou na próxima chance), só com o PC ocioso há 10 min e na tomada, em prioridade '
                'baixa, e para sozinha se você voltar a usar. Limpa temporários e caches antigos, reaplica o que grandes '
                'atualizações desfazem (só dos pacotes que você aplicou e não desfez), atualiza o Defender, confere SMART, '
                'erros de disco, telas azuis e espaço livre, e uma vez por mês cria um ponto de restauração. '
                'Só avisa (notificação do Windows) quando há algo errado.', 2, 'sub')
    if not precisa_admin(ctx, args):
        return 1
    s = roda_ps(t, f"$__x = Get-ScheduledTask -TaskName {psq(TAREFA_MANUT)} -ErrorAction SilentlyContinue; if ($__x) {{ Dado 'tarefa' @{{ estado = [string]$__x.State; ultima = (Tenta {{ ($__x | Get-ScheduledTaskInfo).LastRunTime.ToString('s') }} '') }} }}",
                'tarefa', minutos=1, mostra=False)
    tk = s.dados.get('tarefa')
    t.titulo('situação')
    t.chaves([('tarefa', 'agendada (' + str(tk.get('estado')) + ')' if tk else 'não existe'),
              ('última vez', ha_quanto_iso(estado().get('manut_ultima')) or '-')])
    if getattr(args, 'remover', False):
        acao = 'r'
    elif getattr(args, 'agora', False):
        acao = 'a'
    elif args.sim or not t.interativo:
        acao = 'c'
    else:
        t.escreve()
        t.paragrafo('c = criar ou atualizar a tarefa · a = rodar a manutenção agora · r = remover a tarefa · Enter = voltar', 2, 'apagado')
        acao = t.pergunta('fazer').strip().lower()[:1]
    if acao == 'c':
        return instala_manutencao(ctx)
    if acao == 'a':
        return ferramenta_manutencao(ctx, args)
    if acao == 'r':
        roda_ps(t, f"Unregister-ScheduledTask -TaskName {psq(TAREFA_MANUT)} -Confirm:$false -ErrorAction SilentlyContinue; Feito 'tarefa removida'", 'remover', minutos=1)
    return 0


# ─────────────── restaurar e desfazer ───────────────

def desfaz_pacote(ctx, nome, teste=False):
    t = ctx.t
    bk = CASA / 'backup' / nome
    if not (bk / 'mudancas.jsonl').exists():
        t.nota(f'  {nome}: nada guardado para desfazer.')
        return 0
    s = roda_ps(t, '', f'desfazer-{nome}', minutos=10, pacote=nome, teste=teste, desfaz=True)
    if not teste:
        e = estado()
        if nome in e.get('pacotes', {}):
            e['pacotes'][nome]['revertido'] = True
            e['pacotes'][nome]['revertido_em'] = agora_iso()
        salva_estado(e)
    return 0 if s.ok else 1


def ferramenta_desfazer(ctx, args):
    t = ctx.t
    t.aba('volta cada mudança ao valor exato de antes')
    t.paragrafo('Cada pacote guardou o valor anterior de tudo que mudou: registro, tipo de início dos serviços, tarefas, '
                'plano de energia e atalhos. Programas e apps removidos não voltam por aqui (reinstale pela Loja ou pelo site). '
                'Para voltar o PC inteiro, use o ponto de restauração "Antes do Katharos" (comando restaurar).', 2, 'sub')
    if not precisa_admin(ctx, args):
        return 1
    e = estado().get('pacotes', {})
    com_backup = [n for n in PACOTES if (CASA / 'backup' / n / 'mudancas.jsonl').exists()]
    if not com_backup:
        t.ok('Nenhuma mudança guardada para desfazer.')
        return 0
    alvo = [x for x in (getattr(args, 'pacotes', None) or []) if x]
    if not alvo:
        t.titulo('pacotes com mudanças guardadas')
        for i, n in enumerate(com_backup, 1):
            q = ha_quanto_iso((e.get(n) or {}).get('quando', ''))
            t.escreve(f'  {t.p(f"{i:>2}", "destaque", True)}  {t.p(PACOTES[n].titulo, "texto")}' + t.p(f'  {n} · aplicado {q}', 'apagado'))
        t.escreve()
        if not t.interativo:
            return 0
        r = t.pergunta('desfazer quais (números, "tudo" ou Enter = nenhum)').strip().lower()
        if not r:
            return 0
        alvo = com_backup if r in ('tudo', 't') else [com_backup[n - 1] for n in _numeros(r, len(com_backup))]
    elif alvo == ['tudo']:
        alvo = com_backup
    alvo = [a for a in alvo if a in com_backup]
    if not alvo:
        t.aviso('nenhum desses pacotes tem mudanças guardadas.')
        return 1
    if not args.teste and not t.confirma('Desfazer ' + ', '.join(PACOTES[a].titulo for a in alvo) + '?', sim=args.sim):
        return 0
    for a in alvo:
        t.titulo(PACOTES[a].titulo)
        desfaz_pacote(ctx, a, args.teste)
    if not args.teste:
        roda_ps(t, 'Reinicia-Explorer', 'explorer', minutos=1, mostra=False)
        t.aviso('Reinicie o PC para tudo voltar por completo.')
    return 0


def ferramenta_restaurar(ctx, args):
    t = ctx.t
    t.aba('pontos de restauração do Windows e reversão dos pacotes')
    if not precisa_admin(ctx, args):
        return 1
    s = roda_ps(t, r"Dado 'pontos' (Lista @(Tenta { Get-ComputerRestorePoint -ErrorAction Stop | Sort-Object SequenceNumber -Descending | Select-Object -First 8 | ForEach-Object { [pscustomobject]@{ n = $_.SequenceNumber; d = [string]$_.Description; q = ([Management.ManagementDateTimeConverter]::ToDateTime($_.CreationTime)).ToString('s') } } } @()))",
                'pontos', minutos=2, mostra=False)
    pts = lista(s.dados.get('pontos'))
    t.titulo('pontos de restauração')
    if pts:
        t.tabela(['quando', 'descrição'], [[x.get('q', '')[:16].replace('T', ' '), x.get('d', '')] for x in pts])
    else:
        t.nota('  nenhum ponto (a Proteção do Sistema pode estar desligada).')
    if not t.interativo:
        return 0
    t.escreve()
    t.paragrafo('p = criar um ponto agora · r = abrir a Restauração do Sistema (volta o PC inteiro) · '
                'd = desfazer pacotes do katharos · Enter = voltar', 2, 'apagado')
    a = t.pergunta('fazer').strip().lower()[:1]
    if a == 'p':
        marca_estado('ultimo_ponto', '')
        garante_ponto(ctx)
    elif a == 'r':
        subprocess.Popen(['rstrui.exe'])
        t.info('A Restauração do Sistema abriu numa janela própria.')
    elif a == 'd':
        args.pacotes = []
        return ferramenta_desfazer(ctx, args)
    return 0


def ferramenta_estado(ctx, args):
    t = ctx.t
    t.aba('o que já foi aplicado neste PC')
    e = estado()
    pacs = e.get('pacotes', {})
    t.titulo('pacotes')
    if not pacs:
        t.nota('  nada aplicado ainda.')
    linhas = []
    for n, r in pacs.items():
        situ = t.p('desfeito', 'amarelo') if r.get('revertido') else t.p('ativo', 'verde')
        linhas.append([PACOTES[n].titulo if n in PACOTES else n, situ, ha_quanto_iso(r.get('quando')), str(len(r.get('itens', [])))])
    if linhas:
        t.tabela(['pacote', 'situação', 'quando', 'itens'], linhas, alinha='eeed')
    plano = le_json(ARQ_TURBO, None)
    t.titulo('outros')
    t.chaves([('turbo', ('concluído' if plano.get('concluido') else f'pela metade ({len(plano.get("feitas", []))} de {len(plano.get("etapas", []))})') if plano else 'nunca rodou'),
              ('manutenção', ha_quanto_iso(e.get('manut_ultima')) or 'nunca rodou'),
              ('ponto de restauração', ha_quanto_iso(e.get('ultimo_ponto')) or '-'),
              ('medidas salvas', str(len(medidas_salvas()))), ('dados', caminho_curto(CASA))])
    return 0


# ─────────────── grandes: arquivos grandes, duplicados e instaladores velhos ───────────────

def _hash(arq, tudo=False):
    h = hashlib.sha1()
    with open(arq, 'rb') as f:
        if not tudo:
            h.update(f.read(1 << 20))
        else:
            for bloco in iter(lambda: f.read(1 << 20), b''):
                h.update(bloco)
    return h.hexdigest()


def ferramenta_grandes(ctx, args):
    t = ctx.t
    t.aba('seus arquivos grandes, duplicados e instaladores velhos')
    t.paragrafo('Olha suas pastas (Downloads, Documentos, Área de Trabalho, Vídeos, Imagens, Música). Nada é apagado de vez: '
                'o que você escolher vai para a Lixeira, e eu confiro se chegou lá. Arquivos dentro do OneDrive só aparecem '
                '(mandar para a Lixeira lá dentro pode apagar de vez e sumir em todos os aparelhos).', 2, 'sub')
    casa = Path.home()
    pastas = [Path(x) for x in (args.pastas or [])] or [casa / n for n in ('Downloads', 'Documents', 'Desktop', 'Videos', 'Pictures', 'Music')]
    od = os.environ.get('OneDrive') or os.environ.get('OneDriveConsumer') or ''
    minimo = (args.mb or int(config('grandes-mb'))) * 2**20
    arquivos = []
    with Progresso(t, None, 'procurando') as pr:
        for base in pastas:
            for raiz, dirs, nomes in os.walk(base):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', 'AppData', '$RECYCLE.BIN')]
                for n in nomes:
                    c = os.path.join(raiz, n)
                    try:
                        st = os.stat(c)
                    except OSError:
                        continue
                    if st.st_size >= 10 * 2**20:
                        arquivos.append((c, st.st_size, st.st_mtime))
                pr.avanca(raiz, 0)
                pr.n = len(arquivos)
    grandes = sorted([a for a in arquivos if a[1] >= minimo], key=lambda a: -a[1])[:25]
    por_tam = {}
    for a in arquivos:
        por_tam.setdefault(a[1], []).append(a)
    dups = []
    with Progresso(t, None, 'comparando duplicados') as pr:
        for tam, grupo in por_tam.items():
            if len(grupo) < 2:
                continue
            por_h = {}
            for a in grupo:
                try:
                    por_h.setdefault(_hash(a[0]), []).append(a)
                except OSError:
                    pass
            for g in por_h.values():
                if len(g) > 1:
                    try:
                        hs = {}
                        for a in g:
                            hs.setdefault(_hash(a[0], True), []).append(a)
                        dups += [sorted(x, key=lambda a: a[2]) for x in hs.values() if len(x) > 1]
                    except OSError:
                        pass
            pr.avanca(str(tam))
    velhos = [a for a in arquivos if a[0].startswith(str(casa / 'Downloads')) and re.search(r'\.(exe|msi|iso|zip|rar|7z)$', a[0], re.I)
              and time.time() - a[2] > 30 * 86400]
    opcoes = []
    t.titulo(f'maiores que {humano(minimo)}')
    for c, tam, mt in grandes:
        opcoes.append(c)
        no_od = od and c.startswith(od)
        t.item(t.p(f'{len(opcoes):>2}', 'destaque', True), None, caminho_curto(c), t.p(humano(tam), 'texto') + (t.p(' · OneDrive', 'amarelo') if no_od else ''))
    if not grandes:
        t.nota('  nenhum.')
    t.titulo('duplicados (a cópia mais nova pode sair)')
    soma = 0
    for g in dups[:15]:
        for c, tam, mt in g[1:]:
            opcoes.append(c)
            soma += tam
            t.item(t.p(f'{len(opcoes):>2}', 'destaque', True), None, caminho_curto(c), t.p(humano(tam), 'texto') + t.p(' igual a ' + Path(g[0][0]).name, 'apagado'))
    if not dups:
        t.nota('  nenhum.')
    t.titulo('instaladores e compactados em Downloads há mais de 30 dias')
    for c, tam, mt in sorted(velhos, key=lambda a: -a[1])[:15]:
        if c not in opcoes:
            opcoes.append(c)
            t.item(t.p(f'{len(opcoes):>2}', 'destaque', True), None, caminho_curto(c), t.p(humano(tam), 'texto'))
    if not velhos:
        t.nota('  nenhum.')
    if not opcoes or args.teste or not t.interativo:
        return 0
    t.escreve()
    r = t.pergunta('mandar para a Lixeira (números, ex.: 1 3 5-7; Enter = nada)').strip()
    nums = _numeros(r, len(opcoes))
    escolha = [opcoes[n - 1] for n in nums if not (od and opcoes[n - 1].startswith(od))]
    if len(escolha) < len(nums):
        t.aviso('Arquivos do OneDrive ficaram: copie para fora, confira e apague você mesmo.')
    if not escolha or not t.confirma(f'Mandar {pl(len(escolha), "arquivo")} para a Lixeira?', sim=args.sim):
        return 0
    lista_ps = ps_lista(escolha)
    corpo = r'''Add-Type -AssemblyName Microsoft.VisualBasic
foreach ($__f in «lista») {
  try { [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($__f, 'OnlyErrorDialogs', 'SendToRecycleBin'); if (Test-Path -LiteralPath $__f) { Aviso ('ficou: ' + $__f) } else { Feito ('na Lixeira: ' + (Split-Path $__f -Leaf)) } }
  catch { Aviso ((Split-Path $__f -Leaf) + ': ' + $_.Exception.Message) }
}'''
    roda_ps(t, ps_monta(corpo, lista=lista_ps), 'lixeira', minutos=5)
    return 0


# ─────────────── memória ───────────────

MEMORIA_PS = r'''
$m = Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
$os = Get-CimInstance Win32_OperatingSystem
$standby = [double]$m.StandbyCacheCoreBytes + [double]$m.StandbyCacheNormalPriorityBytes + [double]$m.StandbyCacheReserveBytes
$comp = Tenta { (Get-Process -Name 'Memory Compression' -ErrorAction Stop).WorkingSet64 } 0
Dado 'mem' @{ total = [double]$os.TotalVisibleMemorySize * 1KB; livre_de_verdade = [double]$m.FreeAndZeroPageListBytes; disponivel = [double]$m.AvailableBytes; standby = $standby; modificada = [double]$m.ModifiedPageListBytes; comprometida = [double]$m.CommittedBytes; limite = [double]$m.CommitLimit; pool = [double]$m.PoolNonpagedBytes; compressao = [double]$comp }
Dado 'top' (Lista (Get-Process | Group-Object ProcessName | ForEach-Object { [pscustomobject]@{ n = $_.Name; mb = [math]::Round(($_.Group | Measure-Object WorkingSet64 -Sum).Sum / 1MB); q = $_.Count } } | Sort-Object mb -Descending | Select-Object -First 10))
'''


def _limpa_standby():
    """Esvazia a lista de espera (standby) da memória, como o RAMMap faz. Precisa de administrador."""
    import ctypes.wintypes as w
    adv, k32, nt = ctypes.windll.advapi32, ctypes.windll.kernel32, ctypes.windll.ntdll

    class LUID(ctypes.Structure):
        _fields_ = [('LowPart', w.DWORD), ('HighPart', w.LONG)]

    class TP(ctypes.Structure):
        _fields_ = [('PrivilegeCount', w.DWORD), ('Luid', LUID), ('Attributes', w.DWORD)]

    tok = w.HANDLE()
    if not adv.OpenProcessToken(k32.GetCurrentProcess(), 0x0020 | 0x0008, ctypes.byref(tok)):
        return False
    luid = LUID()
    if not adv.LookupPrivilegeValueW(None, 'SeProfileSingleProcessPrivilege', ctypes.byref(luid)):
        return False
    tp = TP(1, luid, 2)
    adv.AdjustTokenPrivileges(tok, False, ctypes.byref(tp), 0, None, None)
    cmd = ctypes.c_int(4)  # MemoryPurgeStandbyList
    return nt.NtSetSystemInformation(80, ctypes.byref(cmd), ctypes.sizeof(cmd)) == 0


def ferramenta_memoria(ctx, args):
    t = ctx.t
    t.aba('como a RAM está sendo usada e o que dá para liberar de verdade')
    if not WINDOWS:
        t.erro('só funciona no Windows.')
        return 1
    s = roda_ps(t, MEMORIA_PS, 'memoria', minutos=2, mostra=False)
    m = s.dados.get('mem') or {}
    tot = m.get('total') or 1
    t.titulo('memória agora')
    usada = tot - (m.get('disponivel') or 0)
    t.barra('em uso', usada, tot, t.p(humano(usada), 'texto'), 'amarelo' if usada / tot > 0.8 else 'destaque', larg_rotulo=12)
    t.barra('em espera', m.get('standby', 0), tot, t.p(humano(m.get('standby', 0)), 'texto'), 'azul', larg_rotulo=12)
    t.barra('livre', m.get('livre_de_verdade', 0), tot, t.p(humano(m.get('livre_de_verdade', 0)), 'texto'), 'verde', larg_rotulo=12)
    t.chaves([('comprometida', f'{humano(m.get("comprometida", 0))} de {humano(m.get("limite", 0))}'),
              ('comprimida', humano(m.get('compressao', 0))), ('pool do kernel', humano(m.get('pool', 0)))])
    t.paragrafo('"Em espera" é cache: arquivos e programas que o Windows guarda para abrir rápido de novo, e que ele '
                'devolve na hora quando algum programa precisa. Por isso "liberar RAM" quase sempre é placebo. Só ajuda '
                'quando um jogo engasga logo depois de fechar algo pesado.', 2, 'apagado')
    t.titulo('quem mais usa')
    t.tabela(['programa', 'RAM', 'janelas'], [[x.get('n'), f'{x.get("mb")} MB', str(x.get('q'))] for x in lista(s.dados.get('top'))])
    if args.teste or not t.interativo:
        return 0
    if t.pergunta('esvaziar a memória em espera agora? s = sim, Enter = não').strip().lower() in ('s', 'sim'):
        if not eh_admin():
            t.aviso('precisa de administrador.')
            return 1
        antes = (roda_ps(t, MEMORIA_PS, 'memoria', minutos=2, mostra=False).dados.get('mem') or {}).get('livre_de_verdade', 0)
        ok = _limpa_standby()
        depois = (roda_ps(t, MEMORIA_PS, 'memoria', minutos=2, mostra=False).dados.get('mem') or {}).get('livre_de_verdade', 0)
        if ok:
            t.ok(f'feito: livre de verdade foi de {humano(antes)} para {humano(depois)}.')
        else:
            t.aviso('o Windows não deixou.')
    return 0


# ███████████████████████████████████████████████████████████████████████████
#
#   PARTE 5 · MENU E ENTRADA
#
# ███████████████████████████████████████████████████████████████████████████

class Ctx:
    def __init__(self, args, t):
        self.args, self.t = args, t
        self.perfil = None
        self.mult = 1.0
        self.achados = []
        self.proximos = []


def ferramenta_config(ctx, args):
    t = ctx.t
    t.aba('preferências que valem em toda execução')
    chave, valor = getattr(args, 'chave', None), getattr(args, 'valor', None)
    validos = {'modo': MODOS, 'explicacao': ('completa', 'curta'), 'cores': ('automático', 'sem cor'),
               'simbolos': ('automático', 'simples'), 'navegador': ('brave', 'nenhum')}
    if chave:
        if chave not in PADROES:
            t.erro(f'"{chave}" não existe. Opções: ' + ', '.join(PADROES))
            return 1
        if valor and chave in validos and valor not in validos[chave]:
            t.erro(f'valores aceitos para {chave}: ' + ', '.join(validos[chave]))
            return 1
        if chave == 'grandes-mb' and valor and not valor.isdigit():
            t.erro('use um número de MB.')
            return 1
        salva_config(chave, valor)
        t.ok(f'{chave} = {config(chave)}')
        return 0
    while True:
        t.titulo('preferências')
        for i, (k, (rot, desc)) in enumerate(DESCR_CONFIG.items(), 1):
            t.item(t.p(f'{i:>2}', 'destaque', True), None, rot, t.p(str(config(k)), 'texto'))
            t.paragrafo(desc, 6, 'apagado')
        t.titulo('modos')
        for nome, cor, txt in EXPLICA_MODOS:
            t.item('·', cor, nome)
            t.paragrafo(txt, 6, 'apagado')
        if not t.interativo:
            return 0
        t.escreve()
        r = t.pergunta('mudar qual (número; Enter = voltar)').strip()
        if not r.isdigit() or not 0 < int(r) <= len(DESCR_CONFIG):
            return 0
        k = list(DESCR_CONFIG)[int(r) - 1]
        if k in validos:
            ops = validos[k]
            atual = config(k)
            novo = ops[(ops.index(atual) + 1) % len(ops)] if atual in ops else ops[0]
        else:
            novo = t.pergunta(f'{k} (Enter = padrão {PADROES[k]})').strip()
        salva_config(k, novo)
        t.ok(f'{DESCR_CONFIG[k][0]}: {config(k)}')


GRUPOS = [
    ('conhecer o PC', [
        ('raiox', 'diagnóstico completo, nota e o que fazer', 'ferramenta_raiox'),
        ('medir', 'CPU, RAM, disco e temperatura agora', 'ferramenta_medir'),
        ('memoria', 'quem usa a RAM e o que liberar', 'ferramenta_memoria'),
    ]),
    ('otimizar tudo', [
        ('turbo', 'tudo em sequência, com reinício', 'ferramenta_turbo'),
    ]),
    ('otimizar por partes', [
        ('limpar', 'temporários, caches e restos', 'pacote'),
        ('programas', 'bloatware e antivírus de fábrica', 'pacote'),
        ('apps', 'apps pré-instalados da Loja', 'pacote'),
        ('ia', 'Copilot, Recall e IA do Windows', 'pacote'),
        ('inicializacao', 'o que abre com o Windows', 'pacote'),
        ('servicos', 'serviços sem uso neste PC', 'pacote'),
        ('privacidade', 'telemetria, anúncios e sugestões', 'pacote'),
        ('visual', 'efeitos, animações e barra', 'pacote'),
        ('jogos', 'Modo de Jogo, prioridades, latência', 'pacote'),
        ('energia', 'plano, turbo, USB e hibernação', 'pacote'),
        ('disco', 'menos escrita, boot e memória', 'pacote'),
        ('reparar', 'DISM, SFC, chkdsk, rede, Update', 'pacote'),
        ('atualizar', 'Windows, drivers, programas', 'pacote'),
        ('navegador', 'navegadores mais leves', 'pacote'),
        ('rede', 'DNS mais rápido e medição de ping', 'pacote'),
        ('ajustes', 'preferências: barra, tema, relógio', 'pacote'),
        ('interface', 'área de trabalho e Edge', 'pacote'),
        ('grandes', 'arquivos grandes e duplicados', 'ferramenta_grandes'),
    ]),
    ('manutenção e segurança', [
        ('agendar', 'manutenção semanal automática', 'ferramenta_agendar'),
        ('restaurar', 'pontos de restauração', 'ferramenta_restaurar'),
        ('desfazer', 'volta qualquer pacote', 'ferramenta_desfazer'),
        ('estado', 'o que já foi aplicado', 'ferramenta_estado'),
        ('config', 'modo padrão e preferências', 'ferramenta_config'),
    ]),
]
COMANDOS = {cmd: (desc, f) for _, itens in GRUPOS for cmd, desc, f in itens}
COMANDOS['manutencao'] = ('a manutenção em si (a tarefa agendada chama)', 'ferramenta_manutencao')
SEM_ESTADO = {'config', 'estado', 'desfazer', 'restaurar'}


def roda_ferramenta(ctx, args, abre=True):
    t = ctx.t
    desc, f = COMANDOS[args.comando]
    if abre:
        extra = (f'modo {getattr(args, "modo", None) or config("modo")}' if f in ('pacote', 'ferramenta_turbo') else '')
        t.cabecalho(args.comando, ' · '.join(x for x in (extra, 'teste: nada é alterado' if args.teste else '') if x), app=APP)
    inicio = time.time()
    try:
        cod = ferramenta_pacote(ctx, args, args.comando) if f == 'pacote' else globals()[f](ctx, args)
    except KeyboardInterrupt:
        t.fim('interrompido', 'erro')
        return 130
    if args.comando not in SEM_ESTADO:
        e = estado()
        e.setdefault('usado', {})[args.comando] = agora_iso()
        salva_estado(e)
    t.fim(('concluído em ' if not cod else 'terminou com pendências · ') + duracao(time.time() - inicio), 'ok' if not cod else 'aviso')
    return cod or 0


def monta_parser():
    comum = argparse.ArgumentParser(add_help=False)
    comum.add_argument('--ascii', action='store_true', help='só caracteres simples (terminal que mostra quadradinhos)')
    comum.add_argument('--sem-cor', action='store_true', help='sem cores')
    comum.add_argument('--teste', action='store_true', help='só mostra o que faria, sem alterar nada')
    comum.add_argument('--sim', action='store_true', help='não pergunta: aplica o que o modo marca')
    comum.add_argument('--modo', choices=MODOS, help='seguro, equilibrado ou extremo (padrão: o da config)')
    depois = argparse.ArgumentParser(add_help=False)
    for nome in ('--ascii', '--sem-cor', '--teste', '--sim'):
        depois.add_argument(nome, action='store_true', default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    depois.add_argument('--modo', choices=MODOS, default=argparse.SUPPRESS, help=argparse.SUPPRESS)

    p = argparse.ArgumentParser(prog='katharos', parents=[comum],
                                description='Deixa qualquer Windows mais leve: diagnóstico, limpeza, programas, serviços, '
                                            'privacidade, energia, disco, reparo e manutenção. Sem comando, abre o menu.')
    p.add_argument('--versao', action='version', version=f'katharos {VERSAO}')
    sub = p.add_subparsers(dest='comando', metavar='comando')
    r = sub.add_parser('raiox', parents=[depois], help='diagnóstico completo com nota e recomendações (só leitura)')
    r.add_argument('--queixas', metavar='LISTA', help='lento,boot,disco,calor,bateria,jogos,privacidade,tudo')
    r.add_argument('--salvar', metavar='PASTA', help='onde salvar o relatório .md (ex.: a pasta do PC no cofre)')
    sub.add_parser('medir', parents=[depois], help='medidas agora, comparadas com a primeira')
    sub.add_parser('memoria', parents=[depois], help='uso da RAM e limpeza da memória em espera')
    tb = sub.add_parser('turbo', parents=[depois], help='otimiza tudo em sequência, retomando depois de reiniciar')
    tb.add_argument('--continuar', action='store_true', help='continua um turbo pela metade (a tarefa agendada usa)')
    tb.add_argument('--plano', metavar='ARQUIVO', help='usa as escolhas salvas de outro turbo (para repetir em outros PCs, sem perguntas)')
    for cmd, desc, f in GRUPOS[2][1]:
        if f == 'pacote':
            sub.add_parser(cmd, parents=[depois], help=desc)
    g = sub.add_parser('grandes', parents=[depois], help='arquivos grandes, duplicados e instaladores velhos (vão para a Lixeira)')
    g.add_argument('pastas', nargs='*', help='onde procurar (padrão: suas pastas pessoais)')
    g.add_argument('--mb', type=int, help='tamanho mínimo em MB (padrão 500 ou o da config)')
    a = sub.add_parser('agendar', parents=[depois], help='manutenção semanal: cria, roda agora ou remove')
    a.add_argument('--agora', action='store_true', help='roda a manutenção agora')
    a.add_argument('--remover', action='store_true', help='remove a tarefa agendada')
    sub.add_parser('restaurar', parents=[depois], help='pontos de restauração do Windows')
    d = sub.add_parser('desfazer', parents=[depois], help='desfaz pacotes (nome do pacote ou "tudo")')
    d.add_argument('pacotes', nargs='*', help='ex.: servicos privacidade, ou tudo')
    sub.add_parser('estado', parents=[depois], help='o que já foi aplicado')
    c = sub.add_parser('config', parents=[depois], help='preferências (sem nada: mostra e deixa mudar)')
    c.add_argument('chave', nargs='?', help=', '.join(PADROES))
    c.add_argument('valor', nargs='?', help='valor novo (vazio volta ao padrão)')
    m = sub.add_parser('manutencao', parents=[depois], help='a manutenção em si (a tarefa agendada chama)')
    m.add_argument('--agendada', action='store_true', help=argparse.SUPPRESS)
    return p


def _defaults(args):
    for k, v in (('pastas', []), ('mb', None), ('agora', False), ('remover', False), ('pacotes', []), ('chave', None),
                 ('valor', None), ('continuar', False), ('plano', None), ('agendada', False), ('queixas', None), ('salvar', None)):
        if not hasattr(args, k):
            setattr(args, k, v)
    return args


def menu(ctx, parser, args):
    t = ctx.t
    aviso = ''
    usados = estado().get('usado', {})
    while True:
        t.limpa()
        t.logo('KATHAROS')
        extra = f'{len(COMANDOS) - 1} comandos · modo {config("modo")}' + (' · sem administrador' if WINDOWS and not eh_admin() else '')
        t.cabecalho('início', extra, app=APP)
        if not WINDOWS:
            t.aviso('Este computador não é Windows: dá para ver o menu, mas os comandos só funcionam no Windows.')
        quando = {c: ha_quanto_iso(q) for c, q in usados.items()}
        por_numero = t.menu_itens([(g, [(c, d) for c, d, _ in itens]) for g, itens in GRUPOS], quando)
        if aviso:
            t.aviso(aviso)
            aviso = ''
        if ctx.proximos:
            t.info('sugeridos pelo raio-x: ' + ' · '.join(ctx.proximos))
            t.escreve()
        escolha = t.pergunta('número ou nome').strip().lower()
        if escolha in ('', '0', 'q', 'sair'):
            t.fim('até mais', 'nada')
            return 0
        cmd = por_numero.get(escolha) or (escolha if escolha in COMANDOS else None)
        if not cmd:
            aviso = f'"{corta(escolha, 20)}" não é uma das opções.'
            continue
        try:
            sub_args = _defaults(parser.parse_args([cmd]))
        except SystemExit:
            continue
        for k in ('ascii', 'sem_cor', 'teste', 'sim', 'modo'):
            if getattr(args, k, None):
                setattr(sub_args, k, getattr(args, k))
        t.limpa()
        roda_ferramenta(ctx, sub_args)
        # o raio-x pode sugerir telas: abre uma de cada vez
        while ctx.proximos:
            prox = ctx.proximos.pop(0)
            if prox not in COMANDOS:
                continue
            t.escreve(guia=False)
            try:
                if t.pergunta(f'próxima sugestão: {prox}. Enter = abrir, p = pular, v = voltar ao menu').strip().lower() in ('v', 'voltar'):
                    ctx.proximos = []
                    break
            except KeyboardInterrupt:
                ctx.proximos = []
                break
            sa = _defaults(parser.parse_args([prox]))
            for k in ('ascii', 'sem_cor', 'teste', 'sim', 'modo'):
                if getattr(args, k, None):
                    setattr(sa, k, getattr(args, k))
            roda_ferramenta(ctx, sa)
        usados = estado().get('usado', {})
        t.escreve(guia=False)
        try:
            t.espera('Enter para voltar ao menu')
        except KeyboardInterrupt:
            return 130


def main(argv=None):
    parser = monta_parser()
    args = _defaults(parser.parse_args(argv))
    args.ascii = args.ascii or config('simbolos') == 'simples'
    args.sem_cor = args.sem_cor or config('cores') == 'sem cor'
    t = Terminal(args.ascii, args.sem_cor)
    ctx = Ctx(args, t)
    desliga_edicao_rapida()
    try:
        if args.comando:
            return roda_ferramenta(ctx, args)
        return menu(ctx, parser, args)
    except KeyboardInterrupt:
        t.fim('interrompido', 'erro')
        t.escreve(guia=False)
        return 130
    except BrokenPipeError:
        try:
            sys.stdout = open(os.devnull, 'w')
        except OSError:
            pass
        return 0


if __name__ == '__main__':
    sys.exit(main())
