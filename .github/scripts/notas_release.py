"""Texto da release: a entrada da versão no CHANGELOG.md, mais o que quem baixa precisa saber para conferir o arquivo.
Uso: python .github/scripts/notas_release.py 2.0.1 [hash-do-katharos.py]  (escreve no stdout; sai com erro se a versão não tem entrada)."""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def entrada(versao, texto):
    """O trecho '## VERSÃO · data' até o próximo '## '. Sem o título (o GitHub já mostra o da release)."""
    m = re.search(r'^## ' + re.escape(versao) + r'\b[^\n]*\n(.*?)(?=^## |\Z)', texto, re.S | re.M)
    return m.group(1).strip() if m else None


def notas(versao, sha=None, texto=None):
    corpo = entrada(versao, texto if texto is not None else (RAIZ / 'CHANGELOG.md').read_text(encoding='utf-8'))
    if not corpo:
        raise SystemExit(f'CHANGELOG.md não tem a entrada "## {versao}".')
    rodape = ['', '---', '',
              '**Antes de usar:** leia o [aviso](https://github.com/kessleru/Katharos#antes-de-usar). Grátis, de código aberto e sem garantia. '
              'Comece pelo `raiox`, que só lê.', '',
              '**Como rodar:** baixe `Katharos.zip`, extraia e abra `KATHAROS.bat` (ou `python programa\\katharos.py` no Windows).', '',
              '**Conferir o download** (de fora do programa):',
              '```powershell', 'gh attestation verify Katharos.zip --repo kessleru/Katharos', 'Get-FileHash .\\katharos.py -Algorithm SHA256', '```']
    if sha:
        rodape += ['', f'SHA-256 do `katharos.py` desta versão: `{sha}`']
    return corpo + '\n' + '\n'.join(rodape) + '\n'


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    sys.stdout.write(notas(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
