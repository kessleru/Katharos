# UI 2: plano de redesenho do Katharos

15/11/2026. Pedido do dono: "a UI está monótona". Ele quer algo audacioso e bonito, com vários tipos de elemento, que rode bem e seja fácil de ler.

Regras que continuam valendo:
- A imagem do herói não muda.
- As linhas horizontais e as marcas "+" continuam.
- Nada de animação pesada.
- Nada de texto longo em espaço pequeno.
- Falso alarme é pior que nenhum: a UI nunca "enfeita" um dado que não existe.

## Referências (o que pegar de cada uma)

| Referência | O que pegar |
|---|---|
| Teenage Engineering (OP-1, OP-1 field) | Paleta mínima com **um** acento (o âmbar do Katharos). Grade de especificações com linhas finas, sem sombra. Rótulos em MAIÚSCULAS com espaçamento largo. Cada modo ocupa a tela inteira. Tudo a no máximo dois cliques. Gráficos vivos e simples (onda, ponteiro). |
| Nothing OS | Números e ícones em **matriz de pontos** como elemento de identidade (usado com parcimônia: a nota, a bateria, o FPS). Monocromático, com um vermelho só para o que é grave. |
| Linear (redesenho de 2025) | "Não brigue por atenção que você não conquistou": a barra lateral recua, o conteúdo manda. Divisórias mais suaves e em menor número. Cinza mais quente e menos saturado. |
| iStat Menus 7 / Stats | Gráfico de histórico em todo número ao vivo. Modo "empilhado" (rótulo em cima do valor). A bateria muda de cara conforme carrega, descarrega ou está cheia. |
| Painéis de 2026 (Vercel, Grafana, guia 925studios) | De 5 a 9 elementos por tela, o resto atrás de um clique. Um número principal maior que os outros. A cor carrega sentido ("vermelho é quebrado, não 'olhe aqui'"). Fundo carvão em vez de preto puro. Resumo que expande ao clicar. |
| Wintoys | A tela inicial lida "de relance", como um gerenciador de tarefas. Grupos Boost / Health / Tweaks, cada um com uma frase. |
| Overlay do Steam Deck e do MSI Afterburner | FPS e 1% low como protagonistas durante o jogo. Faixa de tempo de quadro. |

## Linguagem visual nova

1. **Hierarquia por tamanho, não por cor**: cada tela tem **um** número herói (a nota, o FPS, a RAM livre) em tamanho grande. O resto é menor.
2. **Rótulos técnicos**: rótulo pequeno em MAIÚSCULAS mono com espaçamento (`NOTA DO PC`, `CPU`, `BATERIA`), no estilo da TE. O texto corrido continua em caixa normal.
3. **Cor só com sentido**:
   - âmbar: ação e identidade
   - verde: saudável
   - vermelho: quebrado ou grave
   - cinza: o resto

   As faixas de severidade viram uma **barra vertical fina** à esquerda da linha, e não só uma etiqueta.
4. **Superfícies**: fundo carvão quente (não #000), e as seções com 2 a 3 % a mais de luz. As divisórias ficam mais suaves, mas os "+" nos cruzamentos continuam.
5. **Matriz de pontos** (novo): um componente que desenha números em pontos 5×7, só para três heróis (nota, FPS, bateria). É a assinatura visual nova.
6. **Movimento**: só transições curtas (≤150 ms) de entrada e de valor (o número "rola" do antigo ao novo). Nada em laço, exceto o ponto "ao vivo". O desligar animações das Configurações continua valendo.

## Componentes novos (Controles/)

| Componente | Uso | Estado |
|---|---|---|
| `Anel` | nota do PC, bateria, % de uma área aplicada | **feito (4.5.0)** |
| `Medidor` | barra fina segmentada (10 a 20 segmentos, estilo VU) sob cada número ao vivo, cor pela faixa | 4.5.0/5.0.0 |
| `Matriz` | número em matriz de pontos (herói) | 5.0.0 |
| `Mapa de calor` | calendário de 12 semanas (Histórico: horas de jogo, travadas, temperatura por dia) | 5.0.0 |
| `Linha do tempo` | o que mudou no PC, com marcas nos gráficos (Histórico e Desfazer) | 5.0.0 |
| `Antes / Depois` | prévia vetorial dos itens visuais (barra de tarefas, menu de contexto) e números de antes e depois de uma mudança | 5.0.0 |
| `Ficha` (tile) | cartão quadrado com ícone grande, número e minigráfico: Dispositivos e o painel de Jogos | 5.0.0 |
| `Chips` | filtros (mostrar só graves, só desta área) | 5.0.0 |
| `Alternador` | troca sim/não no lugar de dois botões nas Configurações | 5.0.0 |
| `Paleta de comandos` (Ctrl+K) | ir para qualquer tela, item ou ação digitando ("desligar teams", "raio-x") | 5.0.0 |
| `Aviso flutuante` | resultado de uma ação sem cobrir a tela (substitui caixas de "Pronto") | 5.0.0 |
| `Esqueleto` | o lugar do conteúdo enquanto carrega, no formato do que vem (no lugar de "Carregando") | 5.0.0 |
| `IconeDoPrograma.De(caminho)` | ícone real do .exe com cache, com a letra quando não há | 5.0.0 (plano em dispositivos-imagens-painel.md) |

## Tela por tela

- **Início**:
  - Herói: a nota em matriz de pontos e anel, com a frase do próximo passo ao lado.
  - Uma fileira de fichas: CPU, RAM, disco, temperatura, cada uma com minigráfico do dia.
  - "O mais importante agora" com barra de severidade à esquerda.
  - Um rodapé de "últimas 24 h" (linha do tempo curta).
- **Raio-x**:
  - A nota no topo com as 7 categorias em barras horizontais (quanto cada uma tira).
  - Os achados agrupados por categoria e recolhidos (expandem ao clicar).
  - Rodando: as categorias acendem conforme terminam (feito em parte na 4.5.0).
- **Otimizar**:
  - As áreas viram fichas com o anel de "quanto já está aplicado" (8 de 23).
  - Dentro da área, a lista com ganha/perde, o ícone real do programa e a prévia antes/depois nos itens visuais.
  - O rodapé fixo de "Aplicar N" mostra o que ganha somado (menos serviços, menos tarefas).
- **Ao vivo**:
  - O medidor segmentado sob cada número.
  - Em jogo, o FPS em matriz de pontos, o 1% low e a faixa de tempo de quadro. Fora do jogo, a grade de seis.
  - "O Katharos neste PC" vira uma faixa discreta no fim.
- **Memória**: barras horizontais proporcionais ao uso, de cima para baixo, com o ícone real. Abertos e fechados separados (feito na 4.5.0).
- **Dispositivos**: fichas por aparelho (ícone grande, anel de bateria, horas restantes, DPI). Aparelho com bateria baixa em vermelho no topo.
- **Histórico**: mapa de calor do ano, linha do tempo das mudanças e gráficos com as marcas de cada mudança.
- **Central**: cartões de proposta com "se fizer, espero X" e, depois, "deu Y" (antes/depois).
- **Configurações**: alternadores, grupos recolhidos e busca no topo.

## Desempenho (rodar bem)

- Listas longas (Otimizar, Memória) com virtualização (só desenha o que está na tela).
- Os gráficos desenham numa geometria guardada e só refazem quando chega um dado novo. No Ao vivo, 1 vez por segundo no máximo.
- Ícones de programa extraídos uma vez e guardados em disco.
- Uma meta medida pelo Katharos.Fotos e pelo log: abrir a janela em menos de 1,5 s (hoje 1,0 a 1,6 s) e trocar de tela em menos de 100 ms com dado guardado.

## Fases (pedido do dono, 15/11: depois da 4.5.0, uma publicação só, a 5.0.0, com tudo)

1. **4.5.0 (feito)**: anel da nota, ícones por tipo de aparelho, raio-x rodando com layout próprio, Memória abertos/fechados, Dispositivos.
2. **5.0.0 (UI 2, parte 1)**: tokens novos (carvão quente, rótulos técnicos, barra de severidade), Medidor, Fichas, Esqueleto, Aviso flutuante, Alternador, ícone real dos programas, Início e Ao vivo redesenhados.
3. **5.0.0 (parte 2)**: Matriz de pontos, Mapa de calor, Linha do tempo, Antes/Depois, Paleta de comandos, Otimizar e Histórico redesenhados.
4. **5.0.0**: Dispositivos em fichas com bateria de 2.4 GHz (plano de dispositivos) e revisão final com o dono pelas fotos.

Cada fase passa pelo Katharos.Fotos: as fotos de antes e depois vão para o dono aprovar antes de publicar.

## Fontes

- [Linear: behind the latest design refresh](https://linear.app/blog/behind-the-latest-design-refresh)
- [Teenage Engineering: constraints as aesthetic](https://blakecrosley.com/guides/design/teenage-engineering)
- [Nothing OS 3 hands-on](https://androidauthority.com/nothing-os-3-hands-on-3488739)
- [iStat Menus 7](https://www.macrumors.com/2024/07/31/istat-menus-7-0-brings-new-features)
- [35 SaaS dashboard design examples (2026)](https://925studios.co/blog/saas-dashboard-design-examples-2026)
- [Wintoys (Windows Central)](https://www.windowscentral.com/software-apps/wintoys-streamlined-bloatware-removal-and-quick-system-tweaks)
