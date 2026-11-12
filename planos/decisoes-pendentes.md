# Decisões para o cofre (04 • Decisions)

Escritas com o PC desligado; vão para `04 • Decisions` do cofre Knowledge quando ele estiver ligado. Uma nota por bloco abaixo.

---
arquivo: 2026-11-11 conferencia-guardada-e-sem-travar.md
---
resumo: "O \"já está assim\" fica em disco e é conferido de novo uma área por vez, por trás, só quando precisa: aplicar/desfazer, Windows novo, mais de 24 h, área aberta com mais de 6 h, ou \"Ler de novo\"."
tipo: decisao
status: aceita
criado: 2026-11-11
tags: [tipo/decisao, projeto/katharos, area/interface, area/desempenho]
---
# Conferência guardada e sem travar

## Contexto
No teste da 4.2.0 o Otimizar lia tudo de novo a cada abertura (dezenas de segundos). O cache só existia na memória e o motor comum e o de administrador, processos diferentes, não se falavam: depois de aplicar, o "já está assim" ficava errado na mesma sessão.

## Decisão
- `~/.katharos/cache/itens.json` (por item) e `cache/areas.json` (por área: quando e quanto falta). Valem para o mesmo build do Windows e a mesma versão do Katharos.
- Executar um item de verdade apaga o item do cache; desfazer apaga o pacote. A janela manda `forcar` depois de aplicar ou desfazer.
- A janela confere uma área por pedido, numa fila que vive fora das telas. A área que a pessoa abriu ou vai aplicar passa na frente. Só a linha muda.
- O segundo plano confere com o PC parado (10 min sem mexer, sem jogo, CPU < 25 %), no máximo a cada 20 h.
- O perfil do PC também fica em disco (24 h) para a lista abrir sem medir o PC de novo.

## Por quê
Ler é necessário às vezes, mas nunca pode impedir a pessoa de mexer (pedido do dono em 11/11).

Relacionado: [[02 • Projects/Otimizador/Otimizador|Otimizador]] · plano: `planos/2026-11-pos-teste-4.2.0.md`

---
arquivo: 2026-11-11 inicio-de-acordo-com-o-otimizar.md
---
resumo: "Achado e proposta são fotos do momento; antes de mostrar, o motor concilia com o estado conferido. Resolvido sai do Início, a nota sobe e a inicialização mostra a contagem de agora."
tipo: decisao
status: aceita
criado: 2026-11-11
tags: [tipo/decisao, projeto/katharos, area/interface, area/confiabilidade]
---
# Início de acordo com o Otimizar

## Contexto
O Início mostrava "15 programas na inicialização"; ao clicar, o Otimizar dizia que já estava feito. Duas causas: o raio-x contava até antivírus e drivers (que o Otimizar nunca oferece) e o achado era de antes de a pessoa mudar o PC.

## Decisão
- O raio-x conta só o que o Otimizar oferece desligar, com a mesma régua (`_classe_inicio`).
- `situacao_achado`: área conferida depois do raio-x sem nada faltando = resolvido; aplicada depois = resolvido; inicialização conferida = a contagem de agora. Vale para o Início, o Raio-x (resolvidos apagados no fim) e as propostas da central.
- A tela de abertura confere antes as áreas que o Início vai citar (até 8 s).

## Por quê
Mostrar algo e depois desmentir é pior que não mostrar.

---
arquivo: 2026-11-11 rotas-detalhe-e-aplicar-so-esta-correcao.md
---
resumo: "Um lugar só (Rotas.cs) decide para onde cada comando leva; área vira \"Aplicar esta correção\" com só os itens dela; o que só se investiga abre o Detalhe com passos, nunca o Otimizar. Um teste garante destino para todo comando do motor."
tipo: decisao
status: aceita
criado: 2026-11-11
tags: [tipo/decisao, projeto/katharos, area/interface, area/ux]
---
# Rotas, Detalhe e "Aplicar esta correção"

- Comando de área: caixa "Aplicar esta correção" (itens que faltam, os do modo já marcados).
- Inicialização: tela própria "O que abre com o Windows".
- Leitura (medir, travadas, segurança, restaurar…): Detalhe com "Como investigar".
- Saúde: proposta de leitura tem `tipo: leitura`, `certeza: aconteceu` e `causa: a investigar` ou `provável`; a tela nunca mostra "confiança alta" numa causa.
- Teste: `test_todo_comando_que_o_motor_emite_tem_destino_na_janela`.

---
arquivo: 2026-11-11 desfazer-por-item.md
---
resumo: "Cada registro de backup anota o item que o criou ($script:ITEM); o desfazer aceita itens e reescreve o arquivo com o que sobrou. Registro antigo, sem item, só volta com a área inteira."
tipo: decisao
status: aceita
criado: 2026-11-11
tags: [tipo/decisao, projeto/katharos, area/seguranca, area/desfazer]
---
# Desfazer por item

- Dono de uma chave é o primeiro item que mexeu nela (o backup guarda o valor de antes uma vez só).
- Desfazer parcial: o que voltou vai para `mudancas-desfeito-*.jsonl`; o resto fica em `mudancas.jsonl`, na ordem original. O estado tira só esses ids e não marca a área como desfeita.
- Bug corrigido junto: reaplicar uma área desfeita somava os itens antigos ao registro.

---
arquivo: 2026-11-11 ram-por-programa.md
---
resumo: "O segundo plano grava a cada minuto os 15 programas que mais usam RAM (memória privada somada por nome) em ram.jsonl, mais memória prometida e comprimida. \"Cheia de verdade\" só com commit ≥ 90 % ou comprimida ≥ 15 % da RAM."
tipo: decisao
status: aceita
criado: 2026-11-11
tags: [tipo/decisao, projeto/katharos, area/otimizacao, area/memoria]
---
# RAM por programa

- Coleta sem abrir processo nenhum (a mesma chamada que já existia, a cada 5 s; grava o pico do minuto). Rotação de 8 dias.
- Classes: protegido (NUNCA_ENCERRAR, anti-cheat, "parte do Windows"): sem ação; conhecido: tirar da inicialização, fechar (só com clique, pedido igual ao X da janela, nunca forçado) e desinstalar (abre a página do Windows); desconhecido: "não conheço este programa".
- Ícone: o do .exe quando há caminho (inicialização); sem caminho, a inicial do nome num quadrado (o Katharos não abre processos de outros por causa de anti-cheat).

---
arquivo: 2026-11-11 versao-4.3.0-com-as-tres-fases.md
---
resumo: "As três fases do plano pós-teste saem juntas como 4.3.0 (o desenho da abertura no Figma já dizia 4.3.0), sem publicar até o dono pedir."
tipo: decisao
status: aceita
criado: 2026-11-11
tags: [tipo/decisao, projeto/katharos, area/publicacao]
---
# 4.3.0 com as três fases

O dono pediu para fazer o plano inteiro sem parar e segurar a publicação. Ramo `v4.3.0` no GitHub, sem tag (o publicar.yml só roda com tag ou à mão).

Falta conferir no Windows: tempo da segunda abertura do Otimizar, a tarefa do Katharos fora das suspeitas, "Aplicar esta correção" mudando só aquele item, desfazer 2 de 18 serviços, CPU e GPU da janela parada e trocando de tela (meta ~0 % parada), e a tela de abertura em 1 a 2 s com cache.

---
arquivo: 2026-11-12 nota-e-alarme-falso-4.3.1.md
---
resumo: "Nota com teto por categoria e grupo decidido pelo título; nada 'em repouso' com jogo aberto ou GPU ≥ 40 %; tarefa sem assinatura no máximo 2; powercfg do próprio Katharos não vira achado; RAM 'quase cheia' só acima de 85 %."
tipo: decisao
status: aceita
criado: 2026-11-12
tags: [tipo/decisao, projeto/katharos, area/diagnostico, area/confiabilidade]
---
# Nota e alarme falso (4.3.1)

## Contexto
Relatório KTH-MM9NKS (PC do dono, 4.3.0): nota 62 com "Muita coisa abrindo" grave (3 programas), "Tarefas agendadas suspeitas" grave (a tarefa do próprio Katharos) e "Programa trocando o plano de energia" (powercfg.exe 1x, o Katharos aplicando energia).

## Decisão
- PESO_NOTA {3:15, 2:7, 1:2}; teto por categoria (segurança 30, saúde 30, disco 20, memória 20, inicialização 10, jogos 15, geral 15).
- `categoria_achado` olha o título antes das queixas (HD é disco, driver é saúde, antivírus é segurança).
- Raio-x: fase 1 (medida em repouso + amostra de processos) em fila, para a própria leitura não virar "WMI gastando CPU"; fase 2 em paralelo.
- `ocupado` (anti-cheat visto, jogo no agora.json ou GPU ≥ 40 %): as regras de repouso saem e um aviso sem ponto diz isso.
- Itens que o Windows nega ("operação não autorizada") ficam em `cache/bloqueados.json` por build e não são marcados nem contados.

---
arquivo: 2026-11-12 motor-em-paralelo.md
---
resumo: "O motor comum atende pedidos em paralelo (6 linhas); o que grava arquivos do Katharos vai numa trava só e o raio-x tem a dele. A janela já casava respostas pelo id."
tipo: decisao
status: aceita
criado: 2026-11-12
tags: [tipo/decisao, projeto/katharos, area/desempenho]
---
# Motor em paralelo

Abrir o Raio-x durante a conferência deixava a tela preta até a conferência acabar (o motor atendia um pedido por vez). Agora a leitura rápida responde antes; `grava_json` usa arquivo temporário por processo e linha, e `marca_estado` tem trava. Toda tela mostra "Carregando" depois de 150 ms sem conteúdo.
