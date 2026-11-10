#!/bin/bash
# Monta o Katharos a partir da fonte: partes/ → programa/katharos.py, o site (arte/ → docs/index.html),
# a lista de hashes e os testes. Rode da raiz do repositório:  bash scripts/monta.sh
cd "$(dirname "$0")/.." || exit 1
cat partes/0*.py partes/1*.py partes/2*.py partes/3*.py partes/4*.py partes/5*.py partes/6*.py partes/7*.py > programa/katharos.py || exit 1
python3 arte/gera_site.py | tail -1
sha256sum KATHAROS.bat programa/katharos.py programa/katharos.ps1 > SHA256SUMS.txt
python3 -m unittest discover -s tests 2>&1 | tail -4 | cut -c1-400
