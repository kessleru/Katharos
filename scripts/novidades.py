"""Gera partes/67-novidades.py a partir do CHANGELOG.md: as últimas versões, com a frase de abertura e cada item (título e texto).
A janela mostra isso uma vez depois de atualizar. Roda dentro do monta.sh, antes de juntar as partes:  python3 scripts/novidades.py"""
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
QUANTAS = 6


def limpa(txt):
    txt = re.sub(r'\*\*(.+?)\*\*', r'\1', txt)
    txt = re.sub(r'`([^`]+)`', r'\1', txt)
    txt = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', txt)
    return ' '.join(txt.split())


def le(changelog):
    versoes = []
    atual = None
    for linha in changelog.splitlines():
        m = re.match(r'^## (\d+\.\d+\.\d+)\s*·\s*(.+)$', linha.strip())
        if m:
            atual = {'versao': m.group(1), 'data': m.group(2).strip(), 'resumo': '', 'itens': []}
            versoes.append(atual)
            continue
        if atual is None or linha.startswith('#'):
            if linha.startswith('## '):
                atual = None
            continue
        s = linha.strip()
        if s.startswith('- '):
            m = re.match(r'^- \*\*(.+?)\*\*\s*[:.]?\s*(.*)$', s)
            item = {'titulo': limpa(m.group(1)), 'texto': limpa(m.group(2))} if m else {'titulo': '', 'texto': limpa(s[2:])}
            atual['itens'].append(item)
        elif s and not atual['itens'] and not atual['resumo']:
            atual['resumo'] = limpa(s)
    return versoes[:QUANTAS]


def gera():
    versoes = le((RAIZ / 'CHANGELOG.md').read_text(encoding='utf-8'))
    corpo = json.dumps(versoes, ensure_ascii=False, indent=1)
    return ('# ─────────────── novidades de cada versão (gerado do CHANGELOG.md por scripts/novidades.py: não edite) ───────────────\n'
            f'NOVIDADES = {corpo}\n\n\n')


if __name__ == '__main__':
    (RAIZ / 'partes' / '67-novidades.py').write_text(gera(), encoding='utf-8')
    print('novidades: ok')
