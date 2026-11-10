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

## 2.0.0 · 9 de novembro de 2026

Terminal mais simples: menu curto, sem perfis e escolha de itens numa linha cada.

- **Menu de sete linhas**: `raiox`, `turbo`, `escolher`, `jogar`, `painel`, `desfazer` e `mais`. `escolher` abre as áreas com itens para marcar e `mais` as outras ferramentas, as duas com uma linha por assunto. Nenhuma ferramenta saiu, e o nome de qualquer comando continua valendo em qualquer tela.
- **Sem perfis**: o comando `perfil` e os perfis prontos saíram. Fica o modo (seguro, equilibrado ou extremo) ou a escolha item por item. O que o `perfil` fazia de útil virou comando: `atalhos`, `exportar` e `importar`. A primeira abertura não pergunta mais para que você usa o PC.
- **`jogar`**: tudo de jogo num lugar só. Primeiro o Windows (`jogos`), depois o jogo que você joga (`cs2`, `minecraft`, `unreal`) e a conferência da Steam. A tela mostra só o que este PC tem: `jogos` (o Windows) sempre, e `steam`, `cs2`, `minecraft` e `unreal` só se o jogo estiver instalado. Embaixo, a lista dos jogos do catálogo (os 61 do pacote `jogos`) que achou neste PC, procurando só os nomes dos arquivos nas pastas da Steam, da Epic, da GOG e dos programas instalados, e quantos jogos com anti-cheat de terceiros estão aqui (o Katharos não mexe neles). O item de prioridade do pacote `jogos` também mostra "neste PC: achei ...". Quem não aparece continua valendo se você digitar o nome, e um pacote de jogo não instalado explica o que não achou.
- **Escolha de itens que se explica**: os itens aparecem em grupos, e cada grupo diz o que é: **seguro** (não tira nada de você), **equilibrado** (tira o que quase ninguém usa), **extremo** (tira algum recurso) e **opcional** (depende do seu caso, só entra se você marcar; era o "só se marcar"). O modo marca o grupo dele e os de cima, e o título diz quantos marcou. Item com aviso ou sem volta diz isso em palavras, ao lado do nome. Uma linha por item; a explicação de um item aparece com `? 3`. Só três teclas na tela, separadas por bolinha: Enter continua, número marca ou desmarca, `? 3` explica o item 3. As outras (`t`, `n`, `s`/`e`/`x`, `c`, `v 3`) continuam valendo e aparecem na ajuda (`?`), uma por linha. A ordem de aplicar não mudou.
- **`buscar`**: digite o que procura (`buscar telemetria`, `buscar ventoinha`) e ele acha o item ou o comando em qualquer área, sem depender de acento, entendendo palavras do dia a dia ("propaganda", "esquenta") e erros de digitação. Escolher um resultado abre a área só com aquele item marcado. No menu, um texto que não é comando já vira busca.
- **Raio-x que mede mais e explica mais**: memória comprometida e páginas lidas do disco (falta de RAM de verdade), disco ocupado com o PC parado e quem está lendo e gravando, interrupções e DPC (driver travando áudio e jogos), memória abaixo da velocidade dela (XMP desligado), monitor rodando abaixo da taxa que aceita, placa de vídeo sem driver ou com driver antigo e TRIM desligado no SSD. Uma tabela nova, "quem mais gasta agora", diz o que é cada processo e o que fazer com ele (mais de 900 conhecidos, de Windows, fabricantes, lojas de jogos, periféricos, antivírus e programação); os que ele não conhece vão para o relatório.
- **Nota mais justa**: o que é só informação (PC de empresa, ajustes disponíveis, telemetria que vem ligada de fábrica) não tira mais ponto, a nota diz quais achados mais pesaram e, se o PC acabou de ligar, avisa que as medidas em repouso ainda não valem.
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
