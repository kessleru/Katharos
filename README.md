# Katharos

*καθαρός*, em grego: limpo, purificado.

**Deixa qualquer Windows mais leve, num arquivo só.** Diagnóstico com nota, limpeza, programas e apps de fábrica, inicialização, serviços, privacidade, IA do Windows, visual, jogos, energia, disco, reparo, atualizações, rede, manutenção automática e reversão de tudo.

Mesmo visual e mesma ideia do [Ferramentas](https://github.com/kessleru/Ferramentas): Python 3.8+, **zero dependências**, terminal kterm 2.0.0 embutido. Por baixo, só ferramentas nativas do Windows: PowerShell, DISM, sfc, chkdsk, defrag, powercfg, winget.

Site: **[kessleru.github.io/Katharos](https://kessleru.github.io/Katharos)**

## Rodando

[Baixe o ZIP](https://github.com/kessleru/Katharos/archive/refs/heads/main.zip) e extraia. Ele traz só duas coisas: o **`KATHAROS.bat`**, que é onde você clica, e a pasta `programa`, que ele usa. Na primeira vez, o Katharos oferece criar uma pasta **Katharos** na área de trabalho, com ícone; depois disso a pasta baixada pode ser apagada.

O `KATHAROS.bat`:

1. acha o Python que você já tem (Python Launcher, PATH, registro, pastas comuns e até o da Microsoft Store) e só instala o oficial pelo winget se não houver nenhum;
2. abre o Katharos como administrador no melhor terminal do PC: **Windows Terminal**, senão PowerShell 7, senão Windows PowerShell.

```bat
KATHAROS.bat                       :: menu
KATHAROS.bat raiox                 :: diagnóstico completo (só leitura)
KATHAROS.bat turbo                 :: tudo em sequência, com reinício e retomada
KATHAROS.bat privacidade --teste   :: mostra o que faria, sem alterar nada
```

Ou direto, num PowerShell aberto como administrador: `python programa\katharos.py [comando] [opções]`.

## Modos

Todo item tem uma etiqueta de modo, e o modo só decide **o que vem marcado** quando você abre um pacote sozinho (`limpar`, `jogos`...). Quem escolhe os itens num perfil é o perfil: a lista dele mostra a etiqueta de cada item. Na primeira abertura o programa pergunta para que você usa o PC, então a maioria das pessoas nunca precisa pensar em modo. Em toda tela você vê cada item explicado (o que faz, ganho, custo e o modo a partir do qual ele vem marcado) e marca ou desmarca o que quiser.

| Modo | O que marca |
| --- | --- |
| **seguro** | Só o que não tem contrapartida: telemetria, anúncios, lixo, apps de propaganda, tarefas inúteis. Para PC de trabalho ou de outra pessoa. |
| **equilibrado** | O seguro mais o que quase ninguém usa: serviços de empresa e telefone, Xbox (se não joga), IA do Windows, widgets, efeitos, caches. Recomendado. |
| **extremo** | Tudo o que pode ajudar neste PC: sensores, área de trabalho remota, scanner, localização, hibernação no SSD, ajustes de jogos e de rede. Cada item diz o que se perde. |
| *só se marcar* | Itens que nunca vêm marcados (esvaziar a Lixeira, trocar DNS, MPO, HAGS, remover o Office, preferências). |

Na tela de escolha: números marcam e desmarcam (`3 5 8-10`), `t` todos, `n` nenhum, `s` `e` `x` remarca pelo modo, `c` explicações curtas ou completas, Enter segue, `0` volta.

## Inteligente

Antes de mostrar qualquer item, ele olha o PC: HD ou SSD, RAM e slots, notebook ou desktop, tablet, fabricante, Windows 10 ou 11, impressora, scanner, leitor de cartão, biometria, Bluetooth, área de trabalho remota, WinRM, SSH, WSL, Hyper-V, Docker, jogos instalados (Steam, Epic, Riot, Xbox...), central do fabricante (AWCC, Armoury Crate, Vantage...), OneDrive em uso, Office, antivírus ativos e domínio de empresa. Daí:

- não oferece desligar o que o PC usa (Spooler com impressora, SharedAccess com WSL, cartão inteligente com leitor...);
- muda a recomendação (Xbox não vem marcado em quem joga; plano "fresco" em notebook, "desempenho" em desktop; indexação só em HD);
- dobra os limites de tempo em HD e aumenta em pouca RAM;
- com o Python da Microsoft Store, roda o PowerShell **fora do contêiner** dela pelo WMI (senão o registro do usuário seria gravado numa cópia virtual), e avisa quando o administrador é outra conta.

## Comandos

| Grupo | Comando | O que faz |
| --- | --- | --- |
| Conhecer | `raiox` | Pergunta o que mais incomoda, mede tudo e mostra nota, causas das suas queixas e o que mais encontrou (HD, RAM, inicialização, dois antivírus, WMI ocupado, CPU limitada, temperatura, quem troca o plano de energia, bateria, SMART, telas azuis, tarefas suspeitas em AppData/Temp, ameaças do Defender, restos de programas, projetos dentro do OneDrive, BIOS com atualização falhando...). Gera um `.md` para a ficha do PC; `--salvar PASTA`. |
| | `medir` | CPU, kernel, clock, RAM, processos, serviços, inicialização, espaço, temperatura e boot, comparados com a primeira medida |
| | `memoria` | Como a RAM está dividida (em uso, em espera, livre), quem mais usa e, se quiser, esvazia a memória em espera (explicando por que quase sempre é placebo) |
| Tudo | `turbo` | Modo → etapas → (opcional) item por item → ponto de restauração → mede → aplica → reinicia → continua sozinho → mede de novo. Salva o plano em JSON: `turbo --plano arquivo.json` repete as mesmas escolhas em outro PC sem perguntar |
| Partes | `limpar` | Temporários, Windows Update, Otimização de Entrega, relatórios de erro e dumps, miniaturas, logs, navegadores fechados, shaders, instaladores guardados, caches de dev, Limpeza de Disco do Windows, Windows.old, componentes (DISM), armazenamento reservado, Lixeira |
| | `programas` | Bloatware de Dell, HP, Lenovo, Acer, ASUS, McAfee, Norton, CyberLink, OneDrive, Teams antigo: tenta em silêncio e, se não sair, abre o desinstalador |
| | `apps` | Apps da Loja conhecidos (com explicação) e qualquer outro removível ("risco desconhecido", só se marcar) |
| | `ia` | Copilot, Recall, Clique para Fazer, IA no Paint, Bloco de Notas, Edge e Office, coleta de digitação, serviço e tarefas de IA, só por políticas oficiais |
| | `inicializacao` | Registro, pasta Inicializar, apps da Loja e tarefas de logon, pelo mesmo mecanismo do Gerenciador de Tarefas. Antivírus nunca sai; anti-cheat, touchpad e caneta só se marcar |
| | `servicos` | Desativa (nunca apaga) serviços sem uso, de fabricante (SupportAssist, Killer, Nahimic...), atualizadores em manual, restos de programas desinstalados |
| | `privacidade` | Telemetria do Windows, Office, VS e Firefox, autologgers, anúncios, sugestões, busca na web, widgets, segundo plano, relatório de erros, localização, SMBv1, execução automática de pendrive |
| | `visual` | Efeitos, animações, transparência, barra enxuta, extensões visíveis, menu clássico, desligar mais rápido, atalhos sem busca demorada |
| | `jogos` | Modo de Jogo, Game DVR, prioridade alta para jogos **sem anti-cheat de terceiros** (Valorant, LoL, Fortnite, Apex, Rainbow Six, PUBG, Tarkov e afins ficam de fora), MMCSS, primeiro plano, teclado e mouse, Teclas de Aderência, GPU NVIDIA/AMD, tela inteira, temporizador, Nagle, MPO, HAGS (cada um com a verdade sobre o ganho) |
| | `steam` | Só lê: onde estão as bibliotecas (SSD, HD ou USB), espaço livre, maiores jogos, CS2 num HD, tela em 60 Hz, gravação de fundo, CS2 na placa integrada, Steam abrindo com o Windows. Mais as configurações da Steam e do CS2 que valem mudar à mão |
| | `cs2` | Vídeo do CS2 no preset de FPS (MSAA, oclusão, partículas e shader no baixo; sombras ficam), CS2 na placa dedicada, otimizações para jogos em janela, tela inteira sem otimizações (opcional) e um `katharos.cfg` com comandos do próprio jogo. Cópia do arquivo de vídeo antes; `desfazer cs2` volta tudo |
| | `energia` | Plano "desempenho" ou "fresco" (notebook que esquenta: CPU mínima 5%, turbo eficiente, ASPM em todos os planos), disco, USB, PCIe, throttling, placa de rede, inicialização rápida em HD, hibernação em SSD |
| | `disco` | Defender mais leve, sem P2P do Update, tarefas inúteis, NTFS, Sensor de Armazenamento, SysMain em HD, início atrasado de terceiros, boot no HD, otimizar unidade (TRIM ou desfragmentar), memória virtual e compressão |
| | `reparar` | DISM, SFC, chkdsk, WMI, DNS; e, só se marcar: rede, Windows Update, Loja, ícones, menu Iniciar |
| | `atualizar` | Defender, Windows Update, drivers, winget, apps da Loja |
| | `navegador` | Brave, Chrome e Edge enxutos (sem segundo plano, sem métricas, economia de memória) |
| | `rede` | Mede o ping (roteador e DNS públicos) e troca o DNS (Cloudflare, Google, Quad9, AdGuard) |
| | `ajustes` | Preferências: Finalizar tarefa na barra, caminhos longos, barra à esquerda, segundos, tema escuro, ocultos, Num Lock... |
| | `interface` | Atalhos do Edge, Windows Destaque, Este Computador, área de trabalho só com a Lixeira |
| | `grandes` | Arquivos grandes, duplicados (por hash) e instaladores velhos. Vão para a **Lixeira** (nunca de vez); arquivos do OneDrive só aparecem |
| Segurança | `seguranca` | Auditoria que **só lê**: antivírus, firewall, UAC, BitLocker, TPM, Secure Boot, SMBv1, Área de Trabalho Remota, conta sem senha, atualizações atrasadas e portas abertas para a rede. Nota e onde corrigir; nunca desliga nada |
| | `portas` | Quem escuta em cada porta (programa, pasta, "só este PC" ou "toda a rede") e, se você pedir, encerra o processo (nunca os do sistema) |
| | `segredos` | Chaves, tokens, senhas e endereços de banco esquecidos nos arquivos dos seus projetos. Valor mascarado, nada sai do PC |
| | `verificar` | Refaz a conta em modo teste dos pacotes aplicados: o que o Windows ou uma política desfez; oferece reaplicar |
| Atalhos | `perfil` | Perfis prontos (jogos, notebook na bateria, PC fraco, privacidade, programador, PC de trabalho). Antes de aplicar, `p` deixa tirar, pôr ou juntar itens de outros pacotes; `perfil montar` começa sem perfil nenhum e a escolha pode ser salva com um nome (fica em `~/.katharos/perfis` e aparece na lista). Cada um mostra barras de 0 a 5 do que ataca (desempenho, leveza, espaço, bateria, privacidade, conforto), o que você perde e o risco, com prévia e confirmação. `perfil atalhos` cria a pasta **Katharos** na área de trabalho, com o ícone, um atalho por perfil à sua escolha. `perfil exportar` e `perfil importar` repetem a configuração em outro PC |
| | `organizar` | Separa os arquivos soltos da área de trabalho em pastas por tipo (prévia, confirmação e `--desfazer`). Pastas, atalhos, ocultos e o que você mexeu hoje ficam |
| Resultado | `cartao` · `relatorio` | O antes e depois num cartão · o **relatório único** (copiar para a IA, salvar numa pasta ou apagar) |
| Manutenção | `agendar` | Tarefa semanal: só ocioso e na tomada, prioridade baixa, limpa, reaplica o que atualizações desfazem, Defender, SMART, avisos por notificação; uma vez por mês, ponto de restauração e limpeza de componentes |
| | `restaurar` | Pontos de restauração: lista, cria, abre a Restauração do Sistema |
| | `desfazer` | `desfazer servicos privacidade` ou `desfazer tudo`: volta cada valor ao que era antes |
| | `estado` · `config` | O que já foi aplicado · modo padrão, explicações, cores, símbolos, tamanho mínimo do `grandes`, navegador do turbo |

## Opções

| Opção | Efeito |
| --- | --- |
| `--teste` | Mostra exatamente o que mudaria (cada valor), sem alterar nada |
| `--sim` | Não pergunta: aplica o que o modo marca |
| `--modo seguro\|equilibrado\|extremo` | Modo desta execução |
| `--copiar` · `--salvar PASTA` | No fim de qualquer comando: copia o relatório único para a área de transferência · salva uma cópia dele numa pasta (ex.: o cofre) |
| `--codigo` | Mostra o PowerShell de cada item escolhido e não aplica nada (na tela de escolha, `v 3` mostra o do item 3) |
| `--ascii` · `--sem-cor` | Para terminais que mostram quadradinhos · sem cores (`NO_COLOR` também vale) |

## Segurança

- **Tudo volta.** Antes de mudar qualquer coisa, cada pacote guarda o valor anterior (registro com tipo, tipo de início de serviço, estado de tarefa, plano e índices de energia, atalhos, DNS). `desfazer` volta exatamente. Programas e apps removidos são o único que não volta (está escrito no item).
- Ponto de restauração "Antes do Katharos" (no máximo um por dia; liga a Proteção do Sistema se estiver desligada).
- Cada etapa roda num PowerShell filho com **limite de tempo** (dobrado em HD); se travar (o `Remove-AppxPackage` às vezes nunca volta), é encerrada e o resto segue. O turbo **retoma** depois de reiniciar, nunca roda duas vezes ao mesmo tempo e espera o carregador com bateria abaixo de 40%.
- Clicar na janela não pausa (modo de edição rápida desligado).
- Nada de lançador `.vbs` escondido, nada de exceção no antivírus: as tarefas agendadas chamam o PowerShell numa janela normal, minimizada.
- **Não faz, de propósito:** desligar Defender, firewall, UAC, SmartScreen, VBS/Integridade de Memória, Windows Update, BitLocker, Proteção do Sistema ou checagem de TPM; desligar a memória virtual; mexer na BIOS ou em partições; limpar registro; "liberar RAM" milagroso; desligar SysMain/Prefetch em HD. Quando algo exige isso (atualizar a BIOS com BitLocker), ele diz o comando e você executa.

- **"Manter alterações?"** Depois de mudar serviços, jogos, energia, disco ou visual, o Katharos pergunta se está tudo bem (como a troca de resolução do Windows). Sem resposta em 90 s, desfaz sozinho: se a tela ficar preta, não precisa fazer nada. `config confirmar nunca` desliga.
- **Conferência.** Depois de aplicar, ele refaz a conta em modo teste e diz se algum ajuste não ficou. `verificar` faz o mesmo mais tarde, depois de uma atualização grande do Windows.
- **PC de empresa ou escola** (domínio, Intune ou conta de trabalho) é detectado: o modo da tela cai para "seguro" e ele avisa que a organização pode desfazer as mudanças.
- **Itens protegidos.** `config protegidos rdp,servicos:xbox` e o Katharos nunca mexe neles (nem no turbo, nem na manutenção).
- **Código à vista.** `--codigo` e `v N` mostram o PowerShell exato antes de aplicar. Itens de jogo que podem conflitar com anti-cheat têm um aviso em amarelo.
- **Relatório único.** Em vez de um arquivo por ferramenta, tudo vai para `katharos-relatorio.md` (com um bloco JSON): PC, raio-x, segurança, o que foi aplicado, avisos e erros com dica, e o que o Katharos não reconheceu. É feito para mandar a uma IA melhorar a base de dados. Tudo que vem do PC (nomes de programa, de arquivo, mensagens) é limpo antes de entrar (sem controle, sem Markdown, sem frases que pareçam ordens) e o arquivo avisa que é dado, não instrução. Cada execução também grava uma cópia com data e hora na pasta `relatorios/`, ao lado do `KATHAROS.bat` (`AAAA-MM-DD_HH-MM-SS_pc_comando.md`; ficam as 60 mais recentes). Pelos atalhos da área de trabalho a pasta é a mesma (o programa lembra onde ela está). Só se você apagar ou mover a pasta, ou ela não aceitar escrita, os relatórios vão para `~/.katharos/relatorios`. Confira antes de compartilhar: tem o nome do PC, os programas instalados e caminhos de pastas.
- **Jogos sem risco de ban.** Nada toca em arquivo ou memória de jogo, e nada roda junto com ele. No CS2, só os arquivos de configuração do usuário (o mesmo que o menu do jogo grava) e um `.cfg` à parte, com cópia antes. Céu preto e texturas trocadas não existem aqui: no CS2 os comandos de céu exigem `sv_cheats`, e trocar textura é bloqueado em servidor oficial.
- **Perfil importado nunca é executado.** `perfil importar` só escolhe, entre os itens que o Katharos já conhece, quais aplicar, depois da prévia e da confirmação.
- **Verifique o download.** `python programa\katharos.py --sha256` deve bater com o `SHA256SUMS.txt` do repositório. Veja o [SECURITY.md](SECURITY.md).

Relatório, medidas, backups, logs e preferências ficam em `%USERPROFILE%\.katharos`.

## De onde veio

- Os scripts e as lições de otimizar um Dell Inspiron 5458 de verdade.
- O prompt de otimização de notebook gamer (estratégias de diagnóstico, IA do Windows, fabricante, MSIX, PowerShell 5.1).
- [optimizerDuck](https://github.com/itsfatduck/optimizerDuck) e [Optimizer](https://github.com/hellzerg/optimizer): ajustes comparados um a um; ficaram os documentados e reversíveis.
- O guia de opções de um otimizador de jogos (energia, Game Bar, prioridades, rede, RAM), com o ganho real de cada um.

## Estrutura

```
programa\katharos.py
  NÚCLEO          kterm (terminal Kessleru) · preferências · PowerShell vigiado · backup e desfazer
  PARTE 1         perfil do PC · medidas · raio-x e regras do diagnóstico
  PARTE 2         itens, tela de escolha e execução
  PARTE 3         os pacotes (limpar … interface, rede, ajustes)
  PARTE 4         turbo, manutenção, restaurar, desfazer, estado, grandes, memória
  PARTE 5         menu e linha de comando
KATHAROS.bat               chama o programa\katharos.ps1
programa\katharos.ps1      acha o Python, escolhe o terminal e abre como administrador
docs/             o site (GitHub Pages)
```
