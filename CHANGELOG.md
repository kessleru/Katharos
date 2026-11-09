# Versões do Katharos

O número tem três partes: **MAIOR.MENOR.CORREÇÃO**.

- **MAIOR** muda quando algo deixa de funcionar como antes: um comando some ou muda de nome, ou o formato do backup do `desfazer` muda de um jeito que a versão nova não lê mais. Esperar poucas vezes.
- **MENOR** muda quando entra coisa nova sem quebrar o que já existia: comandos, ajustes, perfis, testes.
- **CORREÇÃO** muda quando só se conserta algo: um texto errado, um ajuste que não pegava, um erro.

Cada versão tem uma tag no GitHub (`v1.2.0`) e o botão de download do site baixa exatamente essa tag. O arquivo `SHA256SUMS.txt` da tag traz os hashes para você conferir. O número também aparece em `katharos --versao`.

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
