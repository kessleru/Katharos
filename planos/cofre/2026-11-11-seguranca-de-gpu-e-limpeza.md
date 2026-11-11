---
title: Segurança de GPU, limpeza e manutenção (rodada de revisão da 4.0.1)
date: 2026-11-11
tags: [decisao, katharos, otimizador, seguranca, gpu, v4]
---
# Segurança de GPU, limpeza e manutenção

**Decisão.** (1) Ajuste que pode gerar artefato na GPU só entra com sinal de suporte: o HAGS (agendamento de GPU por hardware) continua automático (nível 3, como na 4.0.0), com aviso do que se perde, e só liga se o Windows já mostra a chave `HwSchMode` nesta placa e driver; sem ela, o Katharos avisa e não mexe. (2) A limpeza nunca entra em junção nem link simbólico. (3) A manutenção em segundo plano não roda, nem o ponto de restauração e o DISM, com jogo aberto.

**O que ficou como estava, de propósito.** Os itens de imagem e áudio de terceiros (efeitos visuais, taxa do monitor, Nahimic, utilitários de áudio de fabricante) continuam como melhorias nos níveis de antes: o dono pediu que a regra "não mexer na qualidade" valesse para GPU e artefatos, não para esses ajustes. O áudio do próprio Windows nunca é tocado.

**O que a varredura de GPU achou.** Nada mexe em TDR, aceleração por hardware do navegador, profundidade de cor nem escala. MPO e tela cheia exclusiva são nível 0 (só se a pessoa marcar); NVIDIA sem troca de estado de energia e AMD sem ULPS são nível 3 e só em PC de mesa com jogos.

**Por quê.** Falha na imagem por ajuste de GPU é o tipo de erro que a pessoa culpa no PC, não no programa. Sem sinal de suporte, o custo de não ligar é zero.

Related: [Um programa só](2026-11-11-um-programa-so.md), [Motor de inteligência da v4](2026-11-11-motor-de-inteligencia-v4.md)
