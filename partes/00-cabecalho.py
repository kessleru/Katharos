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
from datetime import datetime, timedelta

VERSAO = '4.0.1'
DATA_VERSAO = '11 nov 2026'

# ███████████████████████████████████████████████████████████████████████████
#
#   NÚCLEO · o terminal (kterm 2.0.0, do design system Kessleru)
#
# ███████████████████████████████████████████████████████████████████████████

