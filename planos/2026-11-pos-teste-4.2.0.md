# Katharos: plano depois do teste da 4.2.0

Cópia do cofre (`01 • Inbox/Katharos - plano pós-teste 4.2.0.md`, 11/11/2026). Teste feito no Windows com a 4.2.0 recém-publicada. Para cada problema, a causa achada no código.

| # | Problema | Causa no código | Fase |
|---|---|---|---|
| 1 | Lê "o que dá para fazer" toda vez | Nada fica salvo entre sessões; o Otimizar sempre pede tudo de novo e reconfere | 1 |
| 2 | "Escolher quais abrem" não leva até a inicialização | O Início manda para o Otimizar sem dizer qual área abrir | 1 |
| 3 | "Entender" abre o raio-x com a mesma frase | Não existe tela de detalhe; o botão só troca de tela | 2 |
| 4 | "Aplicar" de uma correção abre o modo inteiro | Comando sem tela própria (ex.: `medir`) cai em "otimizar" | 1 |
| 5 | O próprio Katharos aparece como tarefa suspeita | A regra marca tudo que roda de AppData, e o Katharos fica lá | 1 |
| 6 | Achado sem "como resolver" (OneDrive) | O passo a passo existe, mas fica escondido no texto | 2 |
| 7 | Desfazer só por pacote inteiro | O backup não anota de qual item veio cada mudança | 2 |
| 8 | Não dá para ver quem consome a RAM | O acompanhamento só guarda o nome do maior consumidor | 3 |
| 9 | Jogos ocupa um item do menu | — | 2 |
| 10 | Muito texto, pouco ícone, hierarquia rasa | — | 3 |
| 11 | Gráficos não interagem | O controle `Grafico` só desenha | 3 |
| 12 | Abertura sem tela de carregamento | — | 2 |
| 13 | Não dá para ampliar o gráfico | O gráfico é fixo dentro da célula | 3 |
| 14 | Gráficos cheios de "pontinhos vermelhos" | A confirmar com um print (duas suspeitas) | 1 |
| 15 | Interface sem animação nenhuma | — | 2 |

## Fase 1: correção de bugs (4.2.1)

### 1. Parar de ler tudo de novo a cada abertura
A cada sessão, o Otimizar mostra "Lendo o que dá para fazer neste PC" e depois "Conferindo o que já está feito" (dezenas de segundos em PC lento).

Causa: `Servico.Guardado` fica só na memória; só o Início usa; o Otimizar sempre chama `itens` e depois `itens` com `conferir=true` (PowerShell em todos os itens).

Fazer:
1. O motor salva a conferência em `~/.katharos/cache/itens.json`, com hora e versão (build) do Windows.
2. Vale até: aplicar ou desfazer (invalida só os pacotes mexidos); o build mudar; 24 h.
3. A janela abre com o salvo na hora e confere em segundo plano só o que venceu. "Conferindo" vira uma linha discreta.
4. `Guardado` também vai para o disco (Início, Raio-x, Histórico abrem na hora).
5. O segundo plano pode reconferir de madrugada ou ocioso.

Pronto quando: abrir o Otimizar pela segunda vez, mesmo depois de reiniciar, mostra os itens em menos de 1 s, e o "já está assim" continua certo depois de aplicar ou desfazer.

### 2. Levar a pessoa até o lugar certo
"Muita coisa abrindo com o Windows" > Escolher quais abrem abre o Otimizar no topo. Causa: `Inicio.TelaDoComando` devolve `"otimizar"` sem área (a Central já manda `otimizar:<área>`).
Fazer: todo botão manda para a área exata; o Otimizar abre só aquela área, rola até ela e destaca por um instante. (Fase 2 dá tela própria à inicialização.)

### 4. "Aplicar" aplica só aquela correção
Em "O PC desligou sem avisar", Aplicar e Por quê abrem o Otimizar no Equilibrado com tudo marcado. Causa: o achado de saúde manda `medir`; `Central.TelaDo` não conhece e cai em `otimizar:medir`. Achados só de leitura (desligamento, tela azul, driver) não deveriam ter "Aplicar".
Fazer:
1. Caixa "Aplicar esta correção": só os itens daquela sugestão, o que muda em cada um, como desfazer e um botão; chama `aplicar` só com esses ids.
2. Achado de leitura nunca leva ao Otimizar: mostra "Como investigar" (passo a passo; no desligamento: temperatura, fonte, carregador).
3. Comando desconhecido em `TelaDo`: abre o detalhe do achado, nunca o Otimizar. Teste garantindo que todo comando emitido pelo motor tem destino.

### 5. Falso alarme: o Katharos como "tarefa suspeita"
Causa: `30-conhecer.py` marca tarefa cujo programa roda de AppData, Temp ou Users\Public; o Katharos roda de `%LOCALAPPDATA%\Katharos`.
Fazer: excluir as tarefas do próprio Katharos (pasta/nome do Agendador e programa conferido pelo SHA-256 da instalação); para as outras, assinatura digital de empresa conhecida baixa de "suspeita" para "confira"; teste com uma tarefa do Katharos e uma de programa assinado. Falso alarme é pior que nenhum.

### 14. Os "pontinhos vermelhos" nos gráficos
`Grafico` não desenha pontos: desenha linha, faixa do normal, limite tracejado e marcas de mudança tracejadas âmbar. Suspeitas:
1. Marcas de mudança juntas parecem pontilhado. Correção: agrupar as do mesmo dia numa só, mais discreta, detalhe ao passar o mouse.
2. Dia sem leitura vira zero (`v ?? 0` no Histórico), "dente" até o chão. Correção: lacuna, nunca zero.
Também: com menos de ~7 dias, dizer "ainda aprendendo este PC (X de 7 dias)" em vez de concluir.

### Também na 4.2.1
- Confiança "alta" no desligamento: separar "certeza de que aconteceu" de "causa provável".
- "AMD Ryzen Master Driver não iniciou": explicar que é comum com o Ryzen Master instalado e fechado; só olhar se ligado a quedas. Conferir no código se já é ruído conhecido.

## Fase 2: guiar e explicar (4.3.0)
- **3. Tela de detalhe** (`Detalhe`) reutilizável para achado, item, sugestão, processo, serviço: O que é (frase + ícone); O que eu vi neste PC; Por que importa; Como resolver (passos numerados, botão quando o Katharos resolve, caminho no Windows quando é a pessoa); Como desfazer. Início = estado + 3 coisas mais importantes, cada uma leva ao Detalhe. Raio-x = diagnóstico completo por categoria com nota e o que tira ponto.
- **6. "Como resolver" visível**: achado sem ação automática ganha o botão, que abre o Detalhe nos passos.
- **2b. Tela "O que abre com o Windows"**: lista com ícone, nome amigável, impacto no boot (medido), interruptor; no topo "Desativar os que não preciso" com sugestão marcada; usa o item de inicialização existente e desfaz igual.
- **7. Desfazer por item**: `$ITEM` antes de cada item no `40-itens.py` anotado em `mudancas.jsonl`; `desfazer` aceita `{"itens": [...]}` em ordem reversa; na interface, lista com caixas, "Desfazer marcados" e "Desfazer tudo"; registros antigos sem id só voltam pelo pacote (a tela diz).
- **9. Jogos dentro do Início**: sai do menu; seção com últimas sessões, o que limitou, link.
- **12. Tela de abertura** (Figma: https://www.figma.com/design/BMYPfJByZT6FekbZ95BKym, quadros Abrindo, Lendo, Pronto): mini janela 528×330 sem barra; cavaleiro da hero (`gravura.webp` como está, só recortado) à direita com a grama; à esquerda "Katharos" em JetBrains Mono, "otimizador do Windows", versão; embaixo a etapa real, "2 de 3" e linha âmbar; linhas horizontais com "+". Animação: janela por opacidade 200 ms; linhas do centro para fora e "+" acendem 300 ms; cavaleiro 35%→100% 600 ms só opacidade; progresso só quando etapa real termina (200 ms); some em 150 ms e a principal abre com cache. Imagem 2× webp ~100 KB; nada em loop; sem as sementes; "reduzir animações" = parada; medir no Acer (meta 1–2 s).
- **15. Animações simples**: troca de tela desvanece + desliza poucos px ~150 ms; abrir/fechar com altura suave; hover/afundar em botões; números contam; barra de aplicar desliza, "✓" com destaque; linha do gráfico desenha só na primeira vez. Tudo < 250 ms, nada em loop fora do "ao vivo", respeita "reduzir animações", opção em Configurações. Proibido: desfoque, sombra animada, partículas, vídeo, fundo contínuo, relayout por quadro. Permitido: opacidade, RenderTransform, largura de barras finas. Medir CPU/GPU parado (~0%) e trocando de tela; nada rodando minimizado.

## Fase 3: memória, gráficos e visual (4.4.0)
- **8. RAM por programa**: segundo plano grava a cada minuto os 15 que mais usam, agrupados por programa; tela "Memória" com ícone (C#), nome amigável (descrição do arquivo), agora/média/pico 24 h e 7 d, minigráfico; gargalo real (memória comprimida, paginação, travadas no mesmo horário); protegidos sem ação (31-processos, 32-dicionario); conhecidos com ações seguras (tirar da inicialização, fechar só com clique, desinstalar abre o Windows); desconhecidos "não conheço este programa".
- **11. Gráficos interativos**: linha vertical + valor e hora no mouse; marcas de mudança clicáveis (pacote, itens, ganho); período 24 h/7 d/30 d; legenda liga/desliga série; Histórico, Ao vivo, Memória; `PointerMoved` + dica flutuante em `Controles/Grafico.cs`.
- **13. Ampliar**: botão e duplo clique; quase tela cheia com eixos, faixa com legenda, marcas nomeadas; roda = zoom no tempo, arrastar seleciona, "Ver tudo", comparar duas medidas; Esc fecha.
- **10. Ícones e menos texto**: ícones vetoriais leves (PathGeometry) por categoria (boot, RAM, disco, segurança, saúde, jogo, rede); card com ícone, título, uma linha, "Saiba mais"; textos longos viram lista curta de causas com ícone; manter identidade; mesma revisão no site.

## Ordem
Fase 1 (bug fix, parece quebrado) → Fase 2 (navegação, mais testes) → Fase 3 (depende da coleta nova).

## Conferir no Windows depois
- Tempo para abrir o Otimizar na segunda vez, antes e depois.
- A tarefa do Katharos não aparece mais como suspeita.
- "Aplicar" de uma sugestão muda só aquele item (conferir no Desfazer).
- Desfazer 2 de 18 serviços e os outros 16 continuam aplicados.

## Pendências fora do repositório
- Registrar as decisões em `04 • Decisions` do cofre quando o PC estiver ligado (rascunhos em `planos/decisoes-pendentes.md`).
