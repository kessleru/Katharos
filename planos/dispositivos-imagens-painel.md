# Plano: imagens na interface e o painel do ícone (dispositivos saiu)

15/11/2026. Pedido do dono: tirar a necessidade de instalar o software de cada marca só para ver a bateria ou o DPI. Precisa funcionar com marcas chinesas (Rapoo, Aula, Redragon, Attack Shark, VXE...) e com as grandes (Logitech, Razer, SteelSeries, Corsair, HyperX). Também pediu imagens na interface (ícones dos programas, prévia do que muda) e uma revisão do painel do ícone e do design.

## 1. Dispositivos sem fio: removido

O dono pediu (15/11, 20:03) para tirar a funcionalidade inteira, inclusive o que entrou na 4.5.0. Não volta.

## 2. Imagens na interface

### Ícones dos programas (Memória, Inicialização, Otimizar/apps)

Hoje é uma letra num quadrado (IconeDoPrograma.Inicial). Proposta:
- O motor já sabe o caminho do executável de cada programa (Inicialização, processos da Memória). A janela extrai o ícone do .exe (SHGetFileInfo / Icon.ExtractAssociatedIcon) e guarda um PNG de 32 px em `~/.katharos/cache/icones/<hash do caminho>.png`.
- Sem caminho, ou sem ícone, continua a letra (o fallback atual).
- Apps da Loja: o logo vem do manifesto do pacote (Square44x44Logo).
- Nunca baixa ícone da internet.
- Custo: extração só na primeira vez, cache em disco e leitura preguiçosa (só os que aparecem na tela).

### Prévia do que muda (personalização e afins)

Para itens visuais (barra de tarefas, menu de contexto, menu Iniciar, Explorer, tema), o item ganha uma prévia **antes → depois** desenhada pelo Katharos em vetor: a barra com a lupa e a barra sem a lupa, o menu de clique direito antigo e o novo. Nada de captura de tela de terceiros nem de logotipo da Microsoft.
- Formato: o item ganha `previa: "barra-sem-busca"`, e a janela tem um catálogo de desenhos (Geometry, como os ícones de hoje), no tema do Katharos.
- Onde aparece: ao passar o mouse ou ao expandir o item no Otimizar e na caixa "Aplicar esta correção".
- Começar pelos 10 itens visuais mais usados.

### A refatoração de UI que isso pede

O Otimizar e a Memória montam as linhas à mão em cada tela. Proposta:
- Um componente `LinhaDeItem` (ícone ou prévia, título, ganha/perde, etiqueta, ação) usado por Otimizar, Memória, Inicialização e Dispositivos.
- Um `IconeDoPrograma.De(caminho, nome)` que devolve a imagem ou a letra.
- As telas passam a descrever os dados, e o componente desenha. Menos código repetido e menos lugar para o mesmo bug.
- Fazer em uma versão só de UI (sem mexer no motor), com as fotos do Katharos.Fotos de antes e depois para comparar.

## 3. Painel do ícone (segundo plano)

O que está bom: números grandes, minigráficos, uma linha por recurso, FPS no lugar da rede durante o jogo, e os botões raio-x, jogos e abrir o Katharos.

O que melhorar:
- **Estado do próprio segundo plano**: hoje, se ele cai, ninguém vê. O painel deve mostrar "acompanhando desde 22:31" e a janela deve avisar quando ele não está rodando sem você ter saído (a 4.5.0 religa sozinho).
- **Rodapé**: diz agora "este ícone usa N MB" (o total do Katharos fica no Ao vivo, que conta tudo). Antes parecia contradizer o Ao vivo e o Gerenciador.
- **FPS sem permissão**: o painel manda para a janela, e o botão "Liberar" agora existe (4.5.0).
- **Pausar e retomar** visível no painel, não só no menu do ícone.
- **Temperatura sem sensor**: hoje pede para abrir o Afterburner. Deveria dizer uma vez e depois esconder a linha.

## 4. Design do Katharos (revisão das telas)

Revisado pelas fotos do Katharos.Fotos (980 px):
- Consistente: grade com linhas e "+", títulos em mono, grupos com ícone e subtítulo, ação em âmbar.
- Memória: agora separa abertos e fechados.
- Raio-x rodando: agora tem layout próprio, com o que já foi lido em duas colunas e o que o raio-x olha.
- A melhorar:
  - Telas que terminam cedo deixam metade da janela vazia. Um rodapé leve com "próximo passo" ajudaria.
  - Na Memória, a ação "Desinstalar…" aparece em programas que só estão na RAM por pouco tempo. Mostrar só com o mouse em cima.
  - O cabeçalho do Raio-x mostra "Fazer de novo" durante a leitura. Esconder enquanto roda.
