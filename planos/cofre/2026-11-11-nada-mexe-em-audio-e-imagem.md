---
title: Nada que mude áudio ou imagem entra sozinho
date: 2026-11-11
tags: [decisao, katharos, otimizador, seguranca, v4]
---
# Nada que mude áudio ou imagem entra sozinho

**Decisão.** Qualquer item que mude como o som ou a tela se apresentam fica em nível 0: só entra se a pessoa marcar à mão. Vale para efeitos visuais, transparência, arrastar janela, ícones no lugar de miniaturas, papel de parede liso, taxa do monitor, Nahimic, sensores e localização (brilho automático e Luz Noturna) e utilitários de áudio dos fabricantes (a tarefa HP Audio Switch e o painel de áudio da inicialização nem são tocados).

**Por quê.** Regra do dono: a qualidade de áudio e imagem não se mexe por conta própria. Um otimizador que muda o som ou a tela sem avisar quebra a confiança mais do que qualquer ganho de FPS paga.

**Como fica garantido.** Teste `test_nada_que_muda_imagem_ou_som_entra_sozinho` falha se algum desses itens voltar a um nível automático. Varredura por palavras (áudio, cor, resolução, gama, HDR, tema) nos scripts de todos os itens automáticos não achou mais nada.

**Também desta rodada.** A limpeza nunca entra em junção nem link simbólico (o PowerShell 5.1 entra, e arquivos de fora da pasta seriam apagados). A manutenção em segundo plano não roda, nem o ponto de restauração e o DISM, com jogo aberto.

Related: [Um programa só](2026-11-11-um-programa-so.md), [Motor de inteligência da v4](2026-11-11-motor-de-inteligencia-v4.md)
