# Versões do Katharos

O número tem três partes: **MAIOR.MENOR.CORREÇÃO**. Quem decide qual sobe é o que o usuário sente, não o tamanho do trabalho.

| Mudou isto | Sobe | Exemplo |
|---|---|---|
| Um comando some ou muda de nome; o formato do backup do `desfazer` muda e a versão nova não lê o antigo | **MAIOR** | `limpar` vira `faxina` |
| Entra algo que o usuário vê ou usa: comando, item, perfil, jogo no catálogo, medição | **MENOR** | item novo no pacote `cs2` |
| Conserta algo que já existia: texto errado, ajuste que não pegava, erro | **CORREÇÃO** | o item não voltava no `desfazer` |
| Só site, documentação, testes ou CI | **nada** | não vira versão, e não entra aqui |

Quando uma versão existe:

- Uma versão é uma **entrega**: tem tag no GitHub (`v1.4.0`), nota de lançamento e `SHA256SUMS.txt`. Não é um commit nem um dia de trabalho. Várias mudanças pequenas esperam juntas pela próxima entrega.
- Só se corta versão com os testes e o CI verdes e com o número e a data deste arquivo iguais aos do programa (`katharos --versao`). Um teste confere.
- A data é a da tag. Duas entregas no mesmo dia só se a segunda for uma CORREÇÃO urgente da primeira.
- O botão de download do site baixa exatamente a última tag.
- Cada versão lista só o que mudou para o usuário, em ordem de importância.

## 1.4.0 · 9 de novembro de 2026

Pacote do CS2 mais completo e catálogo de jogos maior.

- **CS2**: o pacote agora ajusta o vídeo do jogo, só nas chaves confirmadas em fonte pública, com cópia do arquivo antes (`.katharos.bak`) e o jogo fechado. Resolução, qualidade global de sombras e textura dos modelos não são tocadas. Há uma variante para PC fraco (`video-cs2-fraco`, modo extremo), o Reflex (`reflex-cs2`, só com NVIDIA) e `medir-cs2`, que cria um cfg para mostrar frametime e ping na tela (você digita `exec katharos-medir`).
- **Minecraft Java** ganha pacote próprio (`minecraft`): edita o `options.txt` da pasta padrão, só opções do menu de vídeo, só para baixo, com o jogo fechado e cópia antes. Arquivos de jogo agora são gravados sem BOM.
- **`cs2` e `steam` leem o vídeo atual** (somente leitura) e apontam o que mais pesa: MSAA 4x/8x, V-Sync, oclusão ambiente.
- **Catálogo com 61 jogos em 6 categorias**, todos sem anti-cheat de terceiros, que recebem prioridade de CPU. O CS:GO saiu: virou CS2.
- **Prioridade para jogos com anti-cheat** virou item à parte, desligado por padrão (`prioridade-jogos-ac`), com aviso. Nenhum perfil o marca.
- **`dns-teste`** (pacote `rede`): consulta 6 sites 5 vezes em cada DNS direto no servidor e mostra mediana, faixa típica e falhas. Só diz que vale trocar se a diferença passar de 5 ms, de 25% e do ruído. Os itens de DNS saíram do modo equilibrado e não prometem mais "o mais rápido". O `ping` agora mostra mediana, oscilação e perda em 10 pacotes.
- **`retomar`**: cada aplicação anota o que já fez; se o PC travar ou a janela fechar no meio, o programa avisa na próxima abertura e `retomar` refaz só os itens que faltaram.
- **Benchmark** ganhou CPU em todos os núcleos e marca "medida instável" quando as rodadas variam mais de 15%.
- **Textos honestos**: `mmcss`, `primeiro-plano` e `rede-jogos` deixaram de vir marcados no perfil de jogo. O MMCSS só mexe em `SystemResponsiveness` e na categoria da tarefa Games (a Microsoft documenta que "GPU Priority" e "SFIO Priority" não são usados), e o `primeiro-plano` diz que 0x26 já é o padrão do Windows de cliente.

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
