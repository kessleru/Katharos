# Versões do Katharos

O número tem três partes: **MAIOR.MENOR.CORREÇÃO**. Quem decide qual sobe é o que o usuário sente, não o tamanho do trabalho.

| Mudou isto | Sobe | Exemplo |
|---|---|---|
| Um comando some ou muda de nome; o formato do backup do `desfazer` muda e a versão nova não lê o antigo | **MAIOR** | `limpar` vira `faxina` |
| Entra algo que o usuário vê ou usa: comando, item, perfil, jogo no catálogo, medição | **MENOR** | item novo no pacote `cs2` |
| Conserta algo que já existia: texto errado, ajuste que não pegava, erro | **CORREÇÃO** | o item não voltava no `desfazer` |
| Só site, documentação, testes ou CI | **nada** | não vira versão, e não entra aqui |

Quando uma versão existe:

- Dentro de uma série (1.4.x), as entregas seguintes podem subir só o terceiro número mesmo trazendo recurso novo, a pedido do mantenedor: o MENOR sobe quando a série fecha ou quando o recurso muda o jeito de usar o programa.
- Uma versão é uma **entrega**: tem tag no GitHub (`v1.4.0`), nota de lançamento e `SHA256SUMS.txt`. Não é um commit nem um dia de trabalho. Várias mudanças pequenas esperam juntas pela próxima entrega.
- Só se corta versão com os testes e o CI verdes e com o número e a data deste arquivo iguais aos do programa (`katharos --versao`). Um teste confere.
- A data é a da tag. Duas entregas no mesmo dia só se a segunda for uma CORREÇÃO urgente da primeira ou se o mantenedor pedir uma série curta (como a 1.4.x).
- O botão de download do site baixa exatamente a última tag.
- Cada versão lista só o que mudou para o usuário, em ordem de importância.

## 3.1.0 · 10 de novembro de 2026

O Katharos ganha um executável e um acompanhamento em segundo plano de verdade, que lê o PC sem parar e pensa em cima disso.

- **Katharos.exe**: a porta de entrada, com o ícone da marca. Clique duas vezes para abrir o Katharos (faz o mesmo que o `KATHAROS.bat`, que continua no zip). O código está em `exe/Katharos.cs`; a publicação compila ele num Windows, com o compilador que vem no próprio sistema, roda uma conferência lá e assina o zip.
- **Acompanhamento › rodar em segundo plano** (`segundo-plano`): o Katharos.exe fica perto do relógio e lê o PC no ritmo que você escolher (`config tempo-real`: 1, 2, 5 ou 10 s, padrão 1): CPU por núcleo e a frequência de verdade, placa de vídeo (uso e memória), RAM, disco, rede, temperatura (LibreHardwareMonitor, driver de vídeo, zona térmica) e bateria. Uns 30 a 60 MB de RAM, prioridade baixa, sempre como o seu usuário.
- **Painel ao vivo no ícone**: clique e aparece, com o gráfico dos últimos 2 minutos de cada métrica, o que está no limite agora e as propostas da central de inteligência. O botão direito traz turbo, raio-x, verificar, limpar, desfazer, pausar e iniciar com o Windows. O ícone ganha um ponto de cor: verde jogando, âmbar atenção, vermelho grave.
- **Sessões de jogo**: ele percebe o jogo aberto (quem usa a placa de vídeo, na frente ou em tela cheia, ou um anti-cheat rodando) e grava a sessão: quanto tempo e quanto dele ficou no limite (placa de vídeo, CPU, CPU freando, RAM, memória de vídeo, disco, calor). Na hora, diz o que segura o FPS.
- **Central de inteligência mais esperta**: aprende com as sessões de jogo e com os minutos da última semana. "A CPU segura seus jogos", "a CPU freia durante os jogos", "a RAM enche nos jogos", "seus jogos esquentam o PC" viram propostas com o comando que resolve; placa de vídeo no limite vira só informação (é o normal de jogo pesado). O ícone mostra as primeiras e ela pensa de novo a cada hora.
- **Painel**: seção "Ao vivo e jogos", com as últimas 24 horas minuto a minuto e a tabela das sessões.
- **`aovivo`**: as mesmas métricas no terminal, atualizando até o Ctrl+C.
- **Quem já tinha o acompanhamento contínuo** passa para o executável sozinho na primeira vez que abre esta versão pelo zip, e o ícone antigo (em PowerShell, que em alguns PCs nem aparecia) sai. Só com o `katharos.py`, sem o zip, o ícone simples continua.
- **Anti-cheat**: o segundo plano lê o que o Gerenciador de Tarefas lê e nunca abre o processo do jogo; um teste confere que o código do executável não usa nenhuma API que abra, leia ou injete em outro processo.
- `agendar` agora é só a manutenção sozinha (semanal, diária ou contínua); a contínua liga também o segundo plano.

## 3.0.4 · 10 de novembro de 2026

Nada que roda como administrador depende de arquivo que um programa comum consegue trocar.

- **Backup do `desfazer`, scripts temporários e a tarefa que continua o `turbo` saem de `~/.katharos`**: vão para `%ProgramData%\Katharos`, onde só administradores gravam, como já era com a tarefa de segundo plano. Antes, um programa rodando sem administrador podia trocar o script que a tarefa do turbo roda depois do reinício, o PowerShell que o Katharos acabou de gravar ou o registro do `desfazer`, e ganhar administrador. O backup que já existia vai para lá sozinho na primeira vez como administrador, e a pasta passa a ter Administradores como dono.
- **Nome com aspas tipográficas (’) não quebra mais os scripts**: o PowerShell trata ‘ e ’ como aspas; agora elas são dobradas como a ' comum.
- **O que só serve para jogo fica fora em PC sem jogos**: placa de vídeo sempre no desempenho (NVIDIA e AMD), agendamento de GPU, temporizador, rede, agendador multimídia, teclado mais rápido e mouse sem aceleração não entram mais no extremo de quem não tem jogo instalado. A prioridade do primeiro plano continua opcional.
- **O pacote `jogos` entra no turbo do modo seguro também em PC com jogos** (ficava de fora justamente de quem joga).
- **Turbo começado na 2.5.0 termina com o que foi aprovado lá**, também pelo `--plano`. O `--foco` antigo avisa sempre, vira `--modo extremo` no "jogos no máximo" e recusa valor errado.
- **Caminho que termina em `\`** (como `D:\Jogos\`) chega inteiro quando o Katharos abre como administrador, e no Windows Terminal um `;` dentro de um argumento não vira outro comando.
- **Duas janelas abertas juntas não passam as duas pela trava**, e a trava de um Katharos que fechou à força não bloqueia mais quando o Windows dá o mesmo número de processo a outro programa.
- **`organizar --desfazer`** pula a organização de uma área de trabalho que não existe mais e desfaz a anterior.
- **A conferência de autenticidade espera 20 segundos pela lista oficial** (eram 8, que numa conexão lenta davam "não deu para conferir").
- Das cópias de JSON ilegível, ficam as 5 mais recentes de verdade (antes, as últimas em ordem alfabética).

## 3.0.3 · 10 de novembro de 2026

A lista do que já está feito é conferida de novo toda vez que abre.

- **`aplicado` refaz a conferência a cada abertura**, mesmo dentro da mesma sessão: o que está feito hoje pode ter mudado desde a última vez.
- **Depois de aplicar uma área, a conferência dela é descartada**, para a tela de escolha não mostrar "falta" de algo que acabou de ser feito.

## 3.0.2 · 10 de novembro de 2026

Ação que se repete fica fora de tudo que confere "o que já está aplicado".

- **A reaplicação em segundo plano e o `verificar` não refazem mais ações que se repetem**: depois de uma atualização do Windows, "área de trabalho só com a Lixeira" não move mais atalhos novos sozinho nem acusa "ajuste voltou" por causa deles.
- **Limpar, reparar e atualizar nunca contam como "já feito"**: "nada a limpar agora" não é "já feito", e o item não vem mais riscado como feito no `turbo`.

## 3.0.1 · 10 de novembro de 2026

Lista do que já está feito só com o que é definitivo.

- **"Já feito" só conta ajuste que fica gravado no Windows**: ações que se repetem, como otimizar a unidade, reorganizar o boot no HD e limpar a área de trabalho, não entram na lista do `aplicado` nem aparecem como feitas no `turbo`, porque com o tempo o PC volta a precisar delas.

## 3.0.0 · 10 de novembro de 2026

Três escolhas só: seguro, equilibrado e extremo. Jogos vêm dentro delas.

- **Sem perguntas a mais**: saem o "para quê" do `turbo` e o comando `jogar`. O pacote `jogos` entra no turbo em todo modo, e o modo decide os itens: o seguro põe Modo de Jogo e jogos em janela otimizados; o equilibrado, também sem gravação de fundo e mouse sem aceleração; o extremo, também a placa de vídeo sempre no desempenho, o agendamento de GPU, o temporizador fino e menos atraso de rede e de entrada. Continua dando para revisar e escolher item por item (no turbo, `r`; ou pela área, em `escolher`).
- **Versão maior** porque saem comandos: `jogar` agora, e `cs2`, `minecraft`, `unreal` e `steam` na 2.5.0.
- Site: "Tudo o que ele faz", a lista inteira das mudanças por área, com botões que mostram o que cada modo marca.

## 2.5.0 · 10 de novembro de 2026

Jogos sem pacote por jogo, e menos alarme falso.

- **Otimização para jogos é uma escolha**: o `turbo` pergunta para quê (uso geral, jogos ou jogos no máximo) e o `jogar` vai direto às duas de jogo. "Jogos" põe Modo de Jogo, sem gravação de fundo, mouse sem aceleração, agendamento de GPU e energia de desempenho. "Jogos no máximo" põe ainda energia no máximo, efeitos visuais desligados, placa de vídeo sempre no desempenho, temporizador fino e menos atraso de rede e de entrada. Tudo vale para qualquer jogo.
- **Item novo, para qualquer jogo** (Windows 11): otimizações para jogos em janela e para taxa de atualização variável, as mesmas das Configurações de gráficos, sem apagar as outras opções que já estavam lá.
- **Cuidado com ban**: nada muda por executável de jogo (a prioridade por jogo saiu junto com o catálogo) e, com um anti-cheat aberto, o raio-x não consulta nem o caminho dos processos.
- **Saíram os pacotes de um jogo só e o catálogo**: `cs2`, `minecraft`, `unreal`, `steam`, a prioridade por jogo conhecido e a tela de jogos do menu. O pacote `jogos` fica na área de desempenho, com o que vale para todos.
- **"Há jogo aberto" sem catálogo**: a coleta de fundo reconhece jogo aberto pelo anti-cheat, pela sobreposição de jogo das lojas (Steam, Epic, EA, Ubisoft, Xbox, NVIDIA, AMD) ou pela GPU acima de 60 %.
- **Menos aviso falso no raio-x**: a contagem de inicialização do raio-x passa a ignorar o que está desativado no Gerenciador de Tarefas e programa que já saiu (antes contava tudo do registro); o Defender em modo passivo não conta mais como segundo antivírus; "processador limitado" só abaixo de 85 % e fora da bateria; temperatura pela zona térmica só alerta a partir de 90 °C; CPU ocupada parada só acima de 20 % e com o PC ligado há 10 minutos; erros de disco contam só erros, não avisos de pendrive.

## 2.4.0 · 10 de novembro de 2026

O Katharos sabe o que já está feito no PC antes de mexer.

- **Já feito antes de aplicar**: antes de cada lista de ajustes, o Katharos confere item por item em modo teste (nada muda). O que o PC já tem aparece com ● verde e "já feito" e não vem marcado. No turbo, o plano mostra quantos ajustes de cada etapa faltam e quantos já estão feitos; etapa toda feita é pulada.
- **Lista do que já está aplicado** (`aplicado`): área por área, cada ajuste feito (pelo Katharos ou que já estava assim) e o que falta, com o nível de cada um.
- **Inicialização certa**: não conta mais programa que já foi desinstalado, app da Loja que saiu do PC, nem as tarefas do próprio Katharos; e respeita o "desativado" do Gerenciador de Tarefas guardado no usuário ou na máquina. Atalhos da pasta Inicializar são conferidos pelo programa para onde apontam.
- **PC de empresa só quando é**: domínio, Azure AD ou gestão remota com conta de trabalho. A conta pessoal da Microsoft deixava rastro parecido e dava aviso falso. O aviso agora diz o motivo.
- **Processos**: quem o Katharos não conhece aparece com a descrição e a empresa que o próprio arquivo declara, como no Gerenciador de Tarefas.

## 2.3.0 · 10 de novembro de 2026

Identificação do PC mais completa e segundo plano mais esperto.

- **Identificação**: memória de vídeo de verdade (o Windows mostrava no máximo 4 GB) e se a placa é integrada; tipo e velocidade da RAM (DDR4, DDR5...) e quantos pentes; modelo do disco, desgaste, temperatura e horas ligado; todos os discos do PC; placa-mãe e versão da BIOS; cache e núcleos do processador. O raio-x mostra tudo em "este PC".
- **Avisos novos no raio-x**: disco com erros que ele mesmo não corrige (faça cópia e troque), SSD perto do fim da vida útil e disco quente.
- **Medidas**: temperatura da GPU, uso da GPU e memória de vídeo em uso entram no `medir` e no raio-x.
- **Segundo plano**: o ícone diz quando foi a última leitura e quando vem a próxima, e avisa se a coleta parou. Quem já tinha a coleta ligada ganha o ícone sozinho na próxima leitura. Ao atualizar o Katharos, o ícone passa a usar a versão nova.

## 2.2.0 · 10 de novembro de 2026

Ícone perto do relógio, leituras mais certas e o terminal com a cara da landing.

- **Ícone na bandeja** (`bandeja`): com o modo contínuo ligado, o Katharos mostra um ícone perto do relógio. Clicar abre o menu com CPU, RAM, disco e temperatura da CPU e da GPU da última leitura, e atalhos: abrir o Katharos, o painel, o raio-x, medir agora, pausar a leitura por 1 hora, abrir a pasta dos dados e desfazer. Avisa uma vez por hora se passar de 90 °C. O ícone não mede nada sozinho e roda como o seu usuário, sem administrador. `bandeja --parar` tira.
- **Leituras como o Gerenciador de Tarefas**: CPU pela utilidade (conta o turbo), RAM em uso sem a memória em espera (antes parecia quase cheia) e disco pelo tempo ativo (antes podia passar de 100 %).
- **Tema novo do terminal**: o mesmo da landing, fundo quase preto, texto cor de osso e destaque âmbar. Em terminal de fundo claro, o tema Pergaminho. A janela do Katharos abre já com o fundo escuro.

## 2.1.0 · 10 de novembro de 2026

Temperatura da CPU e da GPU em mais PCs.

- **Temperatura da CPU**: lê primeiro o LibreHardwareMonitor ou o OpenHardwareMonitor, se estiver aberto (o sensor de verdade: CPU Package, Tctl/Tdie); depois a zona térmica do Windows por dois caminhos. Descarta o valor fixo de 25 a 28 °C que muitas placas-mãe informam sem medir nada. Cada leitura diz de onde veio.
- **Temperatura da GPU**: placas AMD, NVIDIA e Intel dedicadas passam a ser lidas pelo driver de vídeo, o mesmo dado do Gerenciador de Tarefas (Windows 10 2004 ou mais novo), além da ferramenta da NVIDIA. A coleta de fundo só faz isso fora de jogo, como antes.
- Quando o Windows não mostra o sensor da CPU, o `amostrar` diz como resolver: abrir o LibreHardwareMonitor.

## 2.0.1 · 9 de novembro de 2026

Conferir que o programa baixado é o original.

- **Autenticidade** (`autenticidade`): confere se os arquivos do programa são os publicados, contra o `SHA256SUMS.txt` que veio junto e contra a lista oficial da versão (baixada pelo PowerShell; `--offline` pula). Na primeira vez, a tela do aviso faz isso sozinha e mostra o resultado em verde; se o programa não bate, ela não deixa continuar. Na abertura, avisa sozinho se o arquivo não bate com a lista que veio junto. Só a lista de hashes é baixada, nada é enviado.
- **Assinatura do GitHub**: cada release passa a ser atestada pelo GitHub Actions. Quem baixar confere de fora do programa com `gh attestation verify katharos.py --repo kessleru/Katharos`.
- **Publicação automática** (`publicar` no GitHub Actions): confere versão, changelog e hashes, roda os testes, monta o `Katharos.zip`, assina os arquivos e cria a release com o texto do changelog. Tem modo ensaio, que não publica nada. O botão Baixar do site passa a apontar sempre para a última release.
- Site: rolagem suave da roda do mouse e do touchpad (Lenis, o mesmo do portfólio), servida pelo próprio site; o toque no celular continua nativo e "reduzir movimento" desliga. O texto solto no topo da página saiu e o rodapé ficou mais curto.

## 2.0.0 · 9 de novembro de 2026

Terminal mais simples: menu curto, sem perfis e escolha de itens numa linha cada.

- **Menu de sete linhas**: `raiox`, `turbo`, `escolher`, `jogar`, `painel`, `desfazer` e `mais`. `escolher` abre as áreas com itens para marcar e `mais` as outras ferramentas, as duas com uma linha por assunto. Nenhuma ferramenta saiu, e o nome de qualquer comando continua valendo em qualquer tela.
- **Sem perfis**: o comando `perfil` e os perfis prontos saíram. Fica o modo (seguro, equilibrado ou extremo) ou a escolha item por item. O que o `perfil` fazia de útil virou comando: `atalhos`, `exportar` e `importar`. A primeira abertura não pergunta mais para que você usa o PC.
- **`jogar`**: tudo de jogo num lugar só. Primeiro o Windows (`jogos`), depois o jogo que você joga (`cs2`, `minecraft`, `unreal`) e a conferência da Steam. A tela mostra só o que este PC tem: `jogos` (o Windows) sempre, e `steam`, `cs2`, `minecraft` e `unreal` só se o jogo estiver instalado. Embaixo, a lista dos jogos do catálogo (os 61 do pacote `jogos`) que achou neste PC, procurando só os nomes dos arquivos nas pastas da Steam, da Epic, da GOG e dos programas instalados, e quantos jogos com anti-cheat de terceiros estão aqui (o Katharos não mexe neles). O item de prioridade do pacote `jogos` também mostra "neste PC: achei ...". Quem não aparece continua valendo se você digitar o nome, e um pacote de jogo não instalado explica o que não achou.
- **Escolha de itens que se explica**: os itens aparecem em grupos, e cada grupo diz o que é: **seguro** (não tira nada de você), **equilibrado** (tira o que quase ninguém usa), **extremo** (tira algum recurso) e **opcional** (depende do seu caso, só entra se você marcar; era o "só se marcar"). O modo marca o grupo dele e os de cima, e o título diz quantos marcou. Item com aviso ou sem volta diz isso em palavras, ao lado do nome. Uma linha por item; a explicação de um item aparece com `? 3`. Só três teclas na tela, separadas por bolinha: Enter continua, número marca ou desmarca, `? 3` explica o item 3. As outras (`t`, `n`, `s`/`e`/`x`, `c`, `v 3`) continuam valendo e aparecem na ajuda (`?`), uma por linha. A ordem de aplicar não mudou.
- **`buscar`**: digite o que procura (`buscar telemetria`, `buscar ventoinha`) e ele acha o item ou o comando em qualquer área, sem depender de acento, entendendo palavras do dia a dia ("propaganda", "esquenta") e erros de digitação. Escolher um resultado abre a área só com aquele item marcado. No menu, um texto que não é comando já vira busca.
- **Raio-x que mede mais e explica mais**: memória comprometida e páginas lidas do disco (falta de RAM de verdade), disco ocupado com o PC parado e quem está lendo e gravando, interrupções e DPC (driver travando áudio e jogos), memória abaixo da velocidade dela (XMP desligado), monitor rodando abaixo da taxa que aceita, placa de vídeo sem driver ou com driver antigo e TRIM desligado no SSD. Uma tabela nova, "quem mais gasta agora", diz o que é cada processo e o que fazer com ele (mais de 900 conhecidos, de Windows, fabricantes, lojas de jogos, periféricos, antivírus e programação); os que ele não conhece vão para o relatório.
- **Nota mais justa**: o que é só informação (PC de empresa, ajustes disponíveis, telemetria que vem ligada de fábrica) não tira mais ponto, a nota diz quais achados mais pesaram e, se o PC acabou de ligar, avisa que as medidas em repouso ainda não valem.
- **Prova de ganho** (`provas`): cada item aplicado é medido antes e depois na hora (espaço em disco, RAM, processos, serviços), e cada aplicação guarda a medida de antes para comparar boot, CPU e RAM depois que você reinicia. Depois de aplicar, a tela mostra "o que rendeu agora"; a explicação de cada item (`? 3`) passa a dizer o que ele rendeu neste PC; o painel ganhou a seção Prova de ganho, com barras de antes e depois. O que fica dentro da oscilação normal aparece como "sem diferença", nunca como ganho.
- **Painel**: índice fixo no topo para pular entre as seções, um risco de tendência em cada cartão e a seção nova de provas. Continua sem scripts.
- **Trocar de versão sem perder nada** (`versoes`): a versão nova reconhece os dados da anterior (mesmo das que não anotavam a versão), guarda uma cópia do estado, converte o formato passo a passo, atualiza as cópias que os atalhos, a manutenção agendada e os botões do painel usam, traz os relatórios da pasta antiga e mostra o que continua valendo. Dados gravados por uma versão mais nova nunca são tocados por uma mais antiga.
- **Relatório fácil de achar**: no fim do raio-x, da segurança, do turbo, da saúde e das provas, `a` abre a pasta com o relatório selecionado e `v` abre o arquivo. `--abrir` faz isso em qualquer comando, e `config abrir-relatorio sempre` abre sozinho.
- Ajuste: com o Python da Microsoft Store, cada etapa abria uma janela preta do cmd que ficava parada na tela. Agora ela nasce escondida.
- **Próximo passo no menu**: a abertura diz o que faz sentido agora neste PC (medir, aplicar o que o raio-x apontou, conferir o ganho, deixar no automático) e o Enter segue esse passo. `0` sai.
- **Busca por frase**: "meu notebook esquenta e faz barulho" ou "como tirar a propaganda" acham o ajuste certo; o dicionário de palavras do dia a dia passou de 20 para mais de 200.
- **Catálogo de jogos com 132 títulos** (eram 61), todos sem anti-cheat de terceiros; a lista dos que ficam de fora por ter anti-cheat também cresceu (GTA Online, Halo, Sea of Thieves, ARK e outros).
- **Inicialização mais esperta**: antivírus de terceiros e programas da empresa nunca são oferecidos; gerenciador de senhas, VPN, backup e utilitários de bandeja só saem se você marcar; "otimizadores" residentes, restos da Adobe e monitores de impressora vêm identificados; o que ele não classifica ganha a explicação do dicionário de processos.
- **Jogos de mais lojas**: a procura dos jogos instalados passa a olhar também o Xbox / Microsoft Store, a Ubisoft Connect, o EA app e a Riot.
- **Item novo `trim`** no pacote de disco: liga de novo o TRIM do SSD quando algum programa o desligou.
- **Aviso de uso**: antes da primeira mudança o Katharos mostra os riscos e pede que você digite `entendi`; `aviso` mostra de novo. O que só lê e o `desfazer` nunca pedem aceite. O projeto passa a ter licença MIT.
- Ajuste: um valor do registro que já existia com o conteúdo certo mas o tipo errado (texto no lugar de número) agora é corrigido; antes era dado como feito.
- **Turbo com uma pergunta a menos**: depois do plano, uma pergunta só (Enter começa, `r` revisa item por item, `0` cancela).

## 1.4.1 · 9 de novembro de 2026

Segundo plano com métricas e gráficos, mais um pacote de jogos.

- **Segundo plano** (`agendar --frequencia semanal|diaria|continua`): a tarefa do Windows agora pode rodar ao iniciar o sistema e a cada 4 horas, só com o PC ocioso e na tomada, em prioridade baixa, sem programa aberto na memória. Cada execução grava uma medida pequena (teto de 1500 linhas).
- **`conselheiro`**, o motor de inteligência: junta medidas, benchmarks, pacotes aplicados, erros do relatório e achados do raio-x e propõe o que mudar, cada proposta com o número que a justifica, a confiança e o comando. Nunca aplica sozinho; depois que você executa uma proposta, mede o resultado. Não culpa um pacote por piora que já vinha antes dele, e baixa a confiança quando vários pacotes foram aplicados na mesma semana.
- **`tendencia`** mostra se espaço, boot, RAM, CPU ou temperatura estão piorando com o tempo, e o segundo plano avisa. Poucas medidas não viram conclusão.
- **`painel`** gera um arquivo HTML com gráficos que interpretam os dados: linha suavizada, pontos fora do normal, projeção de quando o disco enche, limite de temperatura, as datas de cada pacote e o efeito de cada um (antes e depois, só quando passa do ruído), mais as propostas do conselheiro. Funciona sem internet e sem scripts.
- **Leitura leve a cada 15 minutos** (modo `continua` do `agendar`): temperatura, CPU, RAM, disco, placa de vídeo e bateria, somadas em uma linha por hora (até ~400 dias, uns 2 MB). O painel ganhou **Temperatura** (faixa mín–máx por dia, repouso contra carga, mapa de calor hora por dia, média por hora do dia, placa NVIDIA) e **Consumo** (por hora do dia, por dia, quem mais pesou). O conselheiro só propõe quando a temperatura passa de 90 °C em várias horas ou sobe em repouso além da oscilação normal. Cuidado com jogos: só lê contadores do Windows (como o Gerenciador de Tarefas), nunca abre o processo de um jogo, não lê memória, não injeta nada e não instala driver. Com jogo ou anti-cheat aberto, não olha processos nem chama a ferramenta da placa; `config coleta-em-jogo pausar` não coleta nada nesse caso. A tarefa roda sem janela (pythonw) e sem administrador.
- **Segurança das tarefas agendadas**: a tarefa elevada agora executa uma cópia do programa em `%ProgramData%\Katharos` (só administradores gravam ali), não mais em `~/.katharos`, onde qualquer programa do seu usuário poderia trocar o arquivo e ganhar administrador. Se o Python estiver na sua pasta de usuário, o programa avisa e explica como fechar a brecha. Nenhuma tarefa de segundo plano abre janela: sem console, todo processo filho nasce sem janela, o que impede um jogo em tela cheia de ser minimizado.
- **Botões no painel** (`painel --ativar-cliques`): cada proposta e cada problema ganha um botão "Corrigir" (ou "Abrir", quando o comando só lê) que abre o Katharos já no comando certo. Como o painel não tem scripts, o botão é um link `katharos://comando`, registrado só para o seu usuário e só se você pedir (`--desativar-cliques` remove). Camadas de proteção, porque qualquer página da internet também pode chamar um link assim: o navegador pergunta, o script só aceita exatamente `--uri katharos://comando` (sem parâmetros, só comandos da lista; `desfazer`, `socorro`, `perfil`, `turbo` ficam de fora), o Windows pede administrador, o Katharos pergunta de novo por extenso e o comando segue o fluxo normal, com a própria confirmação e o `desfazer`.
- **`saude`**: lê os erros graves do Visualizador de Eventos (14 dias), confere os drivers e o estado do Windows, e explica cada problema: tela azul com o nome do código, desligamento sem aviso, programa e serviço que falham, driver de vídeo antigo (mais grave quando há quedas), dispositivo com erro, driver sem assinatura, reinício pendente, atualização atrasada, pouco espaço, Defender desligado. Só leitura. Ruído conhecido (DCOM 10016) é dito como ruído; erro que o catálogo não conhece aparece com a mensagem original, sem explicação inventada. Sem internet, não diz qual é a versão mais nova de um driver, só a idade e as quedas. O segundo plano refaz a leitura no máximo a cada 20 horas e avisa só de erro grave novo; o painel e o conselheiro usam o resultado.
- **`unreal`**: pacote para jogos da Unreal Engine (Satisfactory e Stray), baixa sombras, efeitos e distância de "Épico" para "Alto" no `GameUserSettings.ini`, com cópia, jogo fechado e BOM preservado.
- **`dns-teste`** (pacote `rede`): consulta 6 sites 5 vezes em cada DNS direto no servidor e mostra mediana, faixa típica e falhas. Só diz que vale trocar se a diferença passar de 5 ms, de 25% e do ruído. Os itens de DNS saíram do modo equilibrado e não prometem mais "o mais rápido". O `ping` agora mostra mediana, oscilação e perda em 10 pacotes.
- **`retomar`**: cada aplicação anota o que já fez; se o PC travar ou a janela fechar no meio, o programa avisa na próxima abertura e `retomar` refaz só os itens que faltaram.
- **Benchmark** continua leve (cerca de 1 minuto, sem teste de estresse); a CPU em todos os núcleos só roda com `--completo`. Marca "medida instável" quando as rodadas variam mais de 15%.
- **Inicialização com número**: cada programa que abre com o Windows mostra o atraso de boot que o próprio Windows mediu (log de diagnóstico, média dos últimos 60 dias), e a lista sai ordenada por esse atraso.
- **Modo leve do benchmark** em PC com até 4 GB de RAM, pouca RAM livre ou HD. A transparência só vem marcada em placa integrada ou com 8 GB ou menos; "compressão de memória desligada" saiu dos modos (sem ganho medido).
- **Textos honestos**: `mmcss`, `primeiro-plano` e `rede-jogos` deixaram de vir marcados no perfil de jogo. O MMCSS só mexe em `SystemResponsiveness` e na categoria da tarefa Games (a Microsoft documenta que "GPU Priority" e "SFIO Priority" não são usados), e o `primeiro-plano` diz que 0x26 já é o padrão do Windows de cliente.

## 1.4.0 · 9 de novembro de 2026

Pacote do CS2 mais completo e catálogo de jogos maior.

- **CS2**: o pacote agora ajusta o vídeo do jogo, só nas chaves confirmadas em fonte pública, com cópia do arquivo antes (`.katharos.bak`) e o jogo fechado. Resolução, qualidade global de sombras e textura dos modelos não são tocadas. Há uma variante para PC fraco (`video-cs2-fraco`, modo extremo), o Reflex (`reflex-cs2`, só com NVIDIA) e `medir-cs2`, que cria um cfg para mostrar frametime e ping na tela (você digita `exec katharos-medir`).
- **Minecraft Java** ganha pacote próprio (`minecraft`): edita o `options.txt` da pasta padrão, só opções do menu de vídeo, só para baixo, com o jogo fechado e cópia antes. Arquivos de jogo agora são gravados sem BOM.
- **`cs2` e `steam` leem o vídeo atual** (somente leitura) e apontam o que mais pesa: MSAA 4x/8x, V-Sync, oclusão ambiente.
- **Catálogo com 61 jogos em 6 categorias**, todos sem anti-cheat de terceiros, que recebem prioridade de CPU. O CS:GO saiu: virou CS2.
- **Prioridade para jogos com anti-cheat** virou item à parte, desligado por padrão (`prioridade-jogos-ac`), com aviso. Nenhum perfil o marca.

## 1.3.0 · 9 de novembro de 2026

Mais cuidado com o PC e com quem usa.

- **Perfil sugerido para o seu PC**, com o motivo (por exemplo: "tem só 4 GB de RAM" ou "tem jogos instalados e placa dedicada"). Aparece na primeira abertura e na tela de perfis. É só uma sugestão.
- **Windows que o programa não reconhece** (versão que não é 10 nem 11): só vão marcados os itens do modo seguro, e o programa avisa.
- **Comando digitado errado** sugere o mais parecido ("quis dizer limpar?"). Novo comando `ajuda`, com os passos mais comuns.
- **Estimativa de tempo**: o programa lembra quanto cada comando levou neste PC e mostra "da última vez levou cerca de X".
- **DISM, SFC e chkdsk rodam com prioridade abaixo do normal**, para o PC continuar usável enquanto eles trabalham.
- **Benchmark** recusa rodar em notebook na bateria com menos de 30%, e sugere rodar antes e depois de aplicar.
- **Desfazer** avisa quantas linhas do registro de mudanças estavam ilegíveis, em vez de pulá-las em silêncio.
- **CI**: o job do Python agora roda no Python 3.8 (Ubuntu 22.04) e no 3.13; há um job `windows-real` experimental que roda os testes no Windows, o `benchmark` e a ida e volta do `desfazer` num Windows descartável.

## 1.2.0 · 9 de novembro de 2026

Jogos, perfis personalizáveis, robustez e medição.

- **Jogos sem risco de ban**: comandos `steam` e `cs2`. Não tocam em arquivo nem na memória do jogo; a prioridade de CPU por executável só vale para jogos sem anti-cheat de terceiros.
- **Perfis com barras** que mostram o que cada um ataca, o que você perde e o risco.
- **Confirmação explicada** antes de aplicar: o que muda, o que ganha, o que perde e se volta com `desfazer`.
- **ZIP de download limpo**: só o `KATHAROS.bat` e a pasta `programa`; atalho com ícone oferecido na primeira vez.
- **Site** reescrito e mais enxuto, com a versão à mostra e o download fixo na versão.

- **Novo `benchmark`**: mede disco (escrita e escritas pequenas com flush), CPU e RAM com repetição, descarta a primeira rodada e só diz "melhorou" ou "piorou" quando a diferença é maior que a variação das medidas. Compara com o resultado anterior. Os arquivos de teste são apagados no fim.
- **Novo `socorro`**: desfaz tudo o que o Katharos mudou, reinicia o Explorer e explica o ponto de restauração do Windows.
- **Estado corrompido não some mais em silêncio**: se `estado.json` ou `config.json` estiverem ilegíveis, o Katharos guarda uma cópia (`.corrompido-DATA`), avisa e recomeça.
- **Uma instância por vez**: duas janelas não aplicam mudanças ao mesmo tempo.
- **Espaço em disco conferido** antes de DISM, SFC, ponto de restauração e benchmark.
- **Limpeza automática do que sobra**: `.tmp` de gravações interrompidas, logs com mais de 90 dias e cópias antigas de arquivos corrompidos. O backup do `desfazer` nunca é apagado sozinho.
- **Perfis personalizáveis**: `p` ajusta um perfil antes de aplicar, `perfil montar` começa do zero e a escolha pode ser salva como perfil seu. Na primeira abertura o programa pergunta para que você usa o PC.
- **Pasta `relatorios/`** ao lado do `KATHAROS.bat`, com um relatório por execução, com data e hora, e `ultimo.md` com o atual.
- **Testes automáticos** (28) e CI no GitHub: nenhum script mexe em Defender, firewall, UAC, SmartScreen, Windows Update, memória virtual, BitLocker, Restauração do Sistema ou Integridade de Memória; perfis e menu coerentes; o Python do programa não abre conexões de rede; os hashes publicados batem. O CI também confere a sintaxe dos scripts no PowerShell 5.1.
- Perfil "Modo jogo" renomeado para "Jogos", para não se confundir com os modos de cada item.

## 1.1.0 · 9 de novembro de 2026

- Relatório único, auditoria de segurança (`seguranca`), perfis e atalhos, organizador da área de trabalho (`organizar`).

## 1.0.0 · 9 de novembro de 2026

- Primeira versão: otimizador num arquivo só, com modos (seguro, equilibrado, extremo), escolha item por item, `desfazer`, menu em grupos e site.
