"""Grava o PowerShell de cada item em uma pasta, um arquivo por item, para o CI conferir a sintaxe no PowerShell 5.1."""
import importlib.util
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
destino = Path(sys.argv[1])
destino.mkdir(parents=True, exist_ok=True)
sys.argv = ['katharos']
spec = importlib.util.spec_from_file_location('katharos', RAIZ / 'programa' / 'katharos.py')
k = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k)
sys.path.insert(0, str(Path(__file__).parent))
import test_katharos as t  # noqa: E402

n = 0
for pacote, i in t.ITENS:
    if i.ps:
        (destino / f'{pacote}__{i.id}.ps1').write_text(k.PRELUDIO_PS + '\n' + i.ps, encoding='utf-8-sig')
        n += 1
print(n, 'scripts gravados em', destino)
