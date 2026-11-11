---
title: Motor de inteligência da v4 (memória, causas, avaliador)
date: 2026-11-11
tags: [decisao, katharos, motor, v4]
---
# Motor de inteligência da v4

**Decisão.** O motor que propõe mudanças vira um ciclo em Python, tudo local: memória do PC em SQLite (`~/.katharos/katharos.db`, 120 dias de minutos e depois a média da hora) → detectores (achado com números, fonte e confiança) → mapa de causas em dados (`CAUSAS`: o que confirma e o que descarta) → planejador (peso aprendido neste PC) → avaliador (resultado medido mexe no peso; o que piorou vira "desfazer").

**Por quê.** Proposta sem causa era palpite; causa sem as descartadas não convence; peso fixo não aprende com o PC. O segundo plano continua só escrevendo `.jsonl` (um escritor por tabela), então o banco nunca trava o ícone.

**Regras que ficam.** Pouco dado é "ainda não sei", nunca alarme (testes com casos de aviso falso). Toda explicação tem quatro partes: o que eu vi, por que acho isso, o que eu faria, o que mudaria a conclusão. Avisos com orçamento (um por tipo a cada 6 h; no jogo, só calor grave).

Related: [Katharos por dentro](../../planos/2026-11-interface-instalador-site.md)
