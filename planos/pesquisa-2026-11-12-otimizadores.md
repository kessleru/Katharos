---
resumo: "TogsBoost (pago, fechado, FPS sem método) e seis otimizadores abertos comparados item a item com o Katharos 4.3.1: o que falta, o que eles fazem e o Katharos não deve fazer, e por quê."
tipo: pesquisa
criado: 2026-11-12
tags: [tipo/pesquisa, projeto/katharos, area/otimizacao, area/concorrencia]
---
# Otimizadores: TogsBoost e os abertos (12/11/2026)

Vai para `03 • Research` do cofre quando ele estiver ligado.

## TogsBoost (togsboost.com.br/sobre)
- App pago, com chave de licença; o site também vende cursos. Código fechado.
- Promete FPS: CS2 +23,6 %, Valorant +40 %, Roblox +58 %. Não diz hardware, resolução, quantas medições, nem como mediu.
- Fala de "menor ping possível" sem dizer como. Não fala de anti-cheat nem de segurança.
- "Ajustes reversíveis" e "você vê o que está sendo aplicado". Fluxo em etapas: análise, preparar o Windows, jogos, ajuste fino. Mais de 30 opções, do seguro ao avançado.
- O que vale copiar: o fluxo em etapas e falar a língua de quem joga competitivo (144/240 Hz, input lag).
- O que não copiar: número de FPS sem método. O Katharos mede antes e depois neste PC e diz "sem diferença" quando não teve.

## Os abertos lidos (código clonado)
| Projeto | Licença | Como é |
|---|---|---|
| Chris Titus WinUtil | MIT | 69 ajustes em JSON (registro, serviço e script), "Essential" e "Advanced - CAUTION" |
| Win11Debloat (Raphire) | MIT | ~90 arquivos .reg, um por ajuste |
| Sophia Script | MIT | 120 funções PowerShell, cada uma com liga e desliga |
| Optimizer (hellzerg) | GPL-3.0 | app em C#, liga e desliga por ajuste |
| Winhance | PolyForm Shield (não é aberto de verdade: proíbe concorrer) | 1.000 linhas de opções (jogos, privacidade, energia, som) |
| AtlasOS | GPL-3.0 | "playbook" que reconfigura o Windows inteiro |

## O Katharos já cobre
Telemetria, anúncios, IA (Copilot, Recall, Paint, Bloco de Notas, Edge, Office), serviços em manual, svchost agrupado, efeitos visuais, menus sem espera, inicialização sem atraso, Modo de Jogo, Game DVR, jogos em janela e VRR, MMCSS, Nagle e limite de rede, timer, MPO, HAGS, mouse sem aceleração, Teclas de Aderência, plano de energia, USB e PCIe, NTFS, TRIM, Defender mais leve, P2P do Windows Update, reparos (DISM, SFC, chkdsk, WMI, DNS, rede, Loja), navegadores enxutos, DNS testado, "Finalizar tarefa", caminhos longos e não reiniciar sozinho.

## O que falta e vale fazer (em ordem)
1. **Widgets do jeito que funciona.** No 25H2, o driver UCPD bloqueia o PowerShell de gravar as chaves dos widgets (TaskbarDa, Feeds, Dsh). Foi o "operação não autorizada" do relatório KTH-MM9NKS. O Sophia Script contorna copiando o powershell.exe com outro nome; isso é burlar uma proteção do Windows, e o Katharos não deve fazer. O WinUtil remove o pacote `MicrosoftWindows.Client.WebExperience`. Para o Katharos: o item "widgets" passa a contar como feito quando esse pacote não existe (o dono já removeu "Widgets" em Apps) e, se existir, aponta para remover o app ou para Configurações > Barra de tarefas.
2. **WPBT desligado** (`DisableWpbtExecution = 1`, WinUtil "Essential"). Impede o fabricante de rodar programa gravado no firmware a cada boot. É seguro e reversível; nível 2, em segurança.
3. **Sem apps de fabricante instalados sozinhos** (`PreventDeviceMetadataFromNetwork = 1`, WinUtil e Win11Debloat). Ligar um mouse da Razer ou da Logitech não instala mais o programa dela sozinho. Nível 1, em privacidade.
4. **Inicialização rápida (Fast Startup) como opção** (`HiberbootEnabled = 0`). Com ela ligada, "desligar" não zera o Windows: o tempo ligado não volta a zero, o que bate com o achado "PC ligado há muitos dias". Nível 0 (só se marcar), com a explicação.
5. **Hibernação desligada em desktop** (`powercfg /h off`): libera um arquivo de uns 40 % da RAM no C:. Nível 3, só desktop. Desliga junto a Inicialização rápida.
6. **Explorador sem adivinhar o tipo da pasta** (WinUtil, nível 3). Deixa pastas grandes mais rápidas, mas perde o agrupamento por data em Downloads.
7. **"Não reduzir o volume em chamadas"** (Winhance, Som). Não mexe na qualidade do áudio, só impede o Windows de abaixar o jogo quando o Discord detecta chamada. Nível 2.

## O que eles fazem e o Katharos não deve fazer
| Ajuste | Quem | Por que não |
|---|---|---|
| Desligar Defender, SmartScreen, VBS ou HVCI, restauração do sistema | Optimizer, Winhance | Tira proteção do PC; o Katharos só informa (achado sem ponto) e deixa a decisão com a pessoa |
| Desligar HPET ou CPU idle | Optimizer, Atlas | Sem ganho medido em PC moderno; CPU sem idle esquenta e gasta mais |
| GPU Priority / SFIO Priority | Winhance | A Microsoft documenta que não são usados (o Katharos já explica isso no item MMCSS) |
| SysMain/Prefetch desligado em SSD | Winhance | Mito: no SSD o Windows já se ajusta; desligar piora a abertura de programas |
| IPv6 e Teredo desligados | WinUtil (Advanced) | Quebra Xbox e alguns jogos; sem ganho de ping |
| Copiar powershell.exe com outro nome para passar pelo UCPD | Sophia | Burla uma proteção do Windows |
| Desligar Windows Update, ou atualização de driver | Optimizer, Atlas | O Katharos atualiza; segurança primeiro |

## Fontes
- [TogsBoost: Sobre](https://togsboost.com.br/sobre)
- [WinUtil (ChrisTitusTech/winutil)](https://github.com/ChrisTitusTech/winutil), `config/tweaks.json`
- [Win11Debloat (Raphire)](https://github.com/Raphire/Win11Debloat), `Regfiles/`
- [Sophia Script for Windows](https://github.com/farag2/Sophia-Script-for-Windows), `Module/Sophia.psm1` (TaskbarWidgets: o comentário sobre o UCPD)
- [Optimizer (hellzerg)](https://github.com/hellzerg/optimizer)
- [Winhance](https://github.com/memstechtips/Winhance), `Core/Features/Optimize/Models`
- [AtlasOS](https://github.com/Atlas-OS/Atlas), `playbook/`
- [What is Windows 11's new UCPD feature (oofhours)](https://oofhours.com/2025/05/02/what-is-windows-11s-new-ucpd-feature/)
- [UCPD bloqueia o widget de notícias: "Access is denied" (NTLite)](https://ntlite.com/community/goto/post?id=47100)

Relacionado: [[02 • Projects/Otimizador/Otimizador|Otimizador]] · decisões: `planos/decisoes-pendentes.md`

---

# Busca maior (12/11, à tarde)

Cada seção abaixo foi lida no código ou no texto do projeto (clonado), não em resumo de terceiros.

## PC-Tuning (valleyofdoom) · GPL-3.0 · guia, não programa
O guia mais citado por quem mede (fórum Blur Busters, r/OptimizedGaming). A regra dele: hardware > BIOS > sistema; não aplicar nada sem medir antes e depois (o mesmo princípio do Katharos).
- **Registrar o jogo no GameConfigStore.** O Modo de Jogo e o modo de apresentação só funcionam direito se o jogo aparece em `HKCU\System\GameConfigStore` (Game Bar > "Lembrar que isto é um jogo"). **Ideia para o Katharos:** conferir se os jogos que o segundo plano já viu estão registrados e avisar ("o Modo de Jogo não reconhece o cs2.exe"). Só leitura, sem risco.
- **Modo de apresentação** (Flip independente, DWM, Legacy Flip): o guia manda medir com o PresentMon, que o Katharos já usa. **Ideia:** mostrar no Ao vivo e em Jogos o modo de apresentação de cada sessão. O PresentMon dá isso de graça e explica o atraso a mais em jogo "sem borda" composto pelo DWM.
- **Timer (`GlobalTimerResolutionRequests`).** O guia explica que, desde o Windows 10 2004, o pedido de timer fino é por processo; o valor global faz o pedido de um programa voltar a valer para todos, o que aumenta o trabalho do processador com programas parados. **Para o Katharos:** o item "timer" só tem efeito se algum programa (RTSS, um "timer resolution") pedir o timer; sem isso não muda nada. O texto do item deve dizer isso (hoje diz "pode reduzir latência").
- **Modo de Jogo** pode atrapalhar o aumento de prioridade de threads. O guia manda testar ligado e desligado. O Katharos liga no seguro; com a medição de sessões dá para comparar sozinho (o motor já compara antes e depois).
- **Memória comprimida, SysMain e Prefetch:** só desligar sem HD e medindo. O Katharos mantém, o que bate com o guia (o guia recomenda desligar só em uso de tempo real).
- **CPU sem estados de repouso (C-states):** o guia diz para não fazer com Turbo Boost ou PBO (perde clock de um núcleo), que é o caso de quase todo PC de jogo. Confirma não fazer.
- **Integridade de memória e VBS:** pesam no desempenho (Tom's Hardware), mas **Vanguard (Valorant) e FACEIT podem exigir HVCI ligado.** Confirma o Katharos só informar, sem desligar.
- **QoS DSCP 46 para o jogo:** só ajuda se o roteador respeita DSCP (a maioria dos roteadores de casa ignora). Pouco ganho para o público do Katharos.
- **MSI (interrupção por mensagem):** pode dar tela azul com driver errado (SATA do Windows 7). Fica fora.
- **Hibernação:** `powercfg /h off` desliga a Inicialização rápida, a hibernação e apaga o `hiberfil.sys`. Confirma o item 5 da lista.

## GamingPCSetup (djdallmann) · MIT · pesquisa com medição (xperf, WinDBG, eventos do MMCSS)
Testa os ajustes famosos medindo dentro do Windows. Três resultados mexem em itens que o Katharos já aplica:
- **`NetworkThrottlingIndex` desligado (0xFFFFFFFF) piora.** Medido com xperf: a latência de DPC do `NDIS.sys` (driver de rede) **sobe bastante** com ele desligado, mesmo sem chegar ao limite (10 pacotes por ms, ~15 Mbps). O limite existe para o áudio não engasgar. **O item "rede-jogos" do Katharos desliga esse limite: tirar essa parte e deixar só o Nagle.** Para a 4.3.2.
- **Tarefa "Games" do MMCSS: nenhum jogo, antigo ou novo, se registra nela.** Mexer em "Scheduling Category = High" dessa tarefa não muda nada. **O item "mmcss" do Katharos faz isso: o texto precisa dizer que a parte de "Games" quase nunca vale; o que pode valer é só o `SystemResponsiveness`.**
- **`SFIO Priority` não é usado** (confirma a documentação da Microsoft; o Katharos já não mexe).
- **`Win32PrioritySeparation` vale na hora, sem reiniciar** (WinDBG). O item "primeiro-plano" do Katharos pode dizer "vale na hora".
- **HPET, `useplatformclock`, `useplatformtick`:** a tabela mostra que mexer no bcdedit muda o relógio do sistema de jeitos diferentes conforme a BIOS. Sem medir em cada PC, fica fora.

## privacy.sexy (undergroundwires) · AGPL-3.0 · 44 mil linhas de scripts de privacidade
Gera um script escolhendo itens numa árvore. Foco em privacidade, não em desempenho.
- O Katharos já cobre o que importa: telemetria, CEIP, compatibilidade (PCA), Cortana, anúncios, NVIDIA (tarefas `NvTm*`), atualizadores de Google, Adobe e Dropbox (item "atualizadores em manual"), SMBv1, NetBIOS e LLMNR.
- Tem uma seção **"Privacy over security"** que desliga o Defender inteiro, o AMSI e o SmartScreen. Ele próprio separa e avisa; o Katharos não deve ter isso.
- "Desligar verificação de conectividade" (NCSI) faz o Windows achar que está sem internet (Loja, Teams e o ícone de rede reclamam). Fica fora.
- Ideia aproveitável: **permissões de apps por categoria** (arquivos, telefone, Bluetooth, ativação por voz). São só do usuário e reversíveis; podem entrar como itens de privacidade nível 2.

## ReviOS playbook (meetrevision) · CC BY-SA 4.0 · reinstala o Windows "tunado"
- **Desliga o serviço `UCPD`.** É assim que eles conseguem mexer nos widgets. Desligar uma proteção do Windows (que impede programas de trocar o navegador padrão sozinhos) para isso não vale. Fica fora.
- **Bloqueia programas pelo IFEO (`Debugger`):** `CompatTelRunner.exe` e `DeviceCensus.exe` (telemetria), `BingChatInstaller.exe`, `BGAUpsell.exe` e `BCILauncher.exe` (os pop-ups do Bing que aparecem no Chrome). **Ideia para o Katharos:** o bloqueio dos pop-ups do Bing é útil e reversível (apagar a chave). Risco: o Defender pode olhar IFEO com desconfiança (malware usa a mesma chave). Precisa de teste no Windows antes.
- **"Quando o Windows detectar comunicação: não fazer nada"** (`UserDuckingPreference = 3`). Confirma o item 7 da primeira lista.
- `Win32PrioritySeparation = 38` (0x26): o mesmo valor do item "primeiro-plano" do Katharos.
- Desliga a manutenção automática do Windows e a verificação de disco no boot (`BootExecute`). Fica fora: a manutenção faz o TRIM e a otimização da unidade; sem o autochk, um disco com erro não é consertado.
- Liga o TSX da CPU (mais rápido em banco de dados, desligado por segurança). Fica fora.
- Desliga `GpuEnergyDrv`, `dam` (moderador de atividade) e `Ndu` (uso de dados de rede). O `Ndu` é conhecido por vazar memória do kernel em algumas versões. **Ideia:** o raio-x pode detectar o vazamento ("memória não paginada alta com Ndu") em vez de desligar sempre.

## Hone (auraside) · licença própria que proíbe modificar e uso comercial · não é aberto
O repositório só tem o instalador e binários (`EmptyStandbyList.exe`, `dccmd.exe`). Não dá para ler o que ele faz. Fica como exemplo do que o r/OptimizedGaming pede para evitar: ferramenta de "otimização" que não mostra o que muda.

## optimizerDuck (itsfatduck) · GPL-3.0 · app em C# com testes de aplicar e desfazer
Bem feito por dentro: cada otimização tem nível de risco, guarda o que mudou e tem teste de reverter.
- Cobre o que o Katharos já tem (telemetria, Copilot, Recall, Click to Do, anúncios, svchost, efeitos, teclado, USB, MMCSS, prioridade).
- **Ajustes de driver de placa de vídeo pelo registro:** NVIDIA `DisableDynamicPstate` (placa sempre no clock alto), AMD ULPS e power gating desligados, Intel sem "async flips" e sem VSync adaptativo. Deixam a placa mais quente e gastando mais parada, e o ganho depende do jogo. Fica fora, pela regra de não mexer no que a placa de vídeo faz.
- `MaximizeUpdatePauseLimit` (pausar atualizações por anos): fica fora.
- **Ideia:** o "nível de risco por item", visível na lista, é o mesmo conceito dos modos do Katharos. Lá o risco aparece no item; aqui está no modo. Vale mostrar uma etiqueta "pode quebrar algo" nos itens nível 3, como o "atenção".

## Windows-Optimize-Harden-Debloat (simeononsecurity) · MIT
Aplica as normas STIG do governo americano (políticas de grupo de empresa) mais debloat. É para endurecer PC corporativo, não para jogar; muitas políticas atrapalham o uso doméstico (bloqueio de macros, regras de senha). Fica como referência só para o item "portas de entrada antigas fechadas".

## Debloat-Windows-10 (W4RH4WK) · encerrado
O próprio autor marcou como fim de vida. Bloqueava telemetria pelo arquivo `hosts` (quebra Windows Update e Loja quando a Microsoft troca os endereços) e desligava o Defender. Mostra por que o Katharos usa as chaves oficiais e não o `hosts`.

## Limpar a "lista de espera" da RAM (ISLC, EmptyStandbyList)
Programas como o ISLC e o `EmptyStandbyList.exe` (que vem junto com o Hone) esvaziam a memória em espera. Nasceram de um problema de engasgo do Windows 10 1803 (2018). Não achei confirmação de que o problema continue no Windows 10 2004+ e no 11: no fórum do autor a pergunta ficou sem resposta. **Para o Katharos:** não oferecer limpar; se um dia oferecer, só depois de o segundo plano medir travadas junto com a memória em espera alta.

---

# Síntese da busca maior: o que muda no Katharos

Em ordem. Os dois primeiros corrigem coisas que o Katharos já aplica.

| # | O quê | Por quê | Fonte |
|---|---|---|---|
| 1 | **Tirar `NetworkThrottlingIndex = 0xFFFFFFFF` do item "rede-jogos"** (fica só o Nagle) | Medido: aumenta a latência de DPC do driver de rede | GamingPCSetup |
| 2 | **Texto honesto no "mmcss" e no "timer"** | A tarefa "Games" do MMCSS não é usada por jogos; o timer global só vale se algum programa pedir | GamingPCSetup, PC-Tuning |
| 3 | Widgets: contar como feito sem o pacote WebExperience; senão, remover o app ou abrir Configurações | O UCPD bloqueia o registro | WinUtil, Sophia, ReviOS |
| 4 | Conferir se os jogos estão no GameConfigStore (só leitura, aviso no Detalhe do jogo) | Sem isso o Modo de Jogo não reconhece o jogo | PC-Tuning |
| 5 | Mostrar o modo de apresentação de cada sessão (PresentMon já mede) | Explica atraso a mais em "sem borda" | PC-Tuning |
| 6 | WPBT desligado (nível 2) | Fabricante deixa de rodar programa do firmware no boot | WinUtil |
| 7 | Sem app de fabricante instalado sozinho (nível 1) | Mouse ou teclado novo não instala o programa da marca | WinUtil, Win11Debloat |
| 8 | Não abaixar o volume em chamadas (nível 2) | Jogo não fica baixo quando o Discord detecta voz | Winhance, ReviOS |
| 9 | Inicialização rápida e hibernação como opções (nível 0 e 3) | Tempo ligado zera; libera ~40 % da RAM no disco | Win11Debloat, PC-Tuning |
| 10 | Bloquear os pop-ups do Bing (IFEO de `BGAUpsell.exe`, `BCILauncher.exe`), **só depois de testar no Windows com o Defender** | Propaganda do Bing no Chrome | ReviOS |
| 11 | Permissões de apps por categoria (arquivos, telefone, Bluetooth, voz) | Privacidade, reversível | privacy.sexy |

**Continua fora, agora com mais fontes:** desligar Defender, SmartScreen, AMSI, VBS ou HVCI (Vanguard e FACEIT podem exigir), UCPD, CPU sem repouso, HPET e bcdedit, IPv6 e Teredo, manutenção automática, autochk, TSX, clock fixo da placa de vídeo, bloqueio pelo `hosts`, pausar atualizações por anos, limpar a lista de espera da RAM.

## Fontes da busca maior
- [PC-Tuning (valleyofdoom)](https://github.com/valleyofdoom/PC-Tuning): `README.md` (Register Game in Config Store, Presentation Mode, Timer Resolution, Memory Integrity, CPU Idle States, Hibernation) e `docs/research.md`
- [GamingPCSetup (djdallmann)](https://github.com/djdallmann/GamingPCSetup): `CONTENT/RESEARCH/NETWORK`, `WINSERVICES` (MMCSS) e `WINKERNEL`
- [privacy.sexy](https://github.com/undergroundwires/privacy.sexy): `src/application/collections/windows.yaml`
- [ReviOS playbook](https://github.com/meetrevision/playbook): `src/Configuration/Tasks` (`services.yml`, `registry/system/ifeo.yml`, `registry/misc/enable-audio-communications-do-nothing.yml`)
- [Hone (auraside)](https://github.com/auraside/HoneCtrl)
- [optimizerDuck](https://github.com/itsfatduck/optimizerDuck): `Domain/Optimizations/Categories`
- [Windows-Optimize-Harden-Debloat](https://github.com/simeononsecurity/Windows-Optimize-Harden-Debloat)
- [Debloat-Windows-10 (W4RH4WK)](https://github.com/W4RH4WK/Debloat-Windows-10)
- [ISLC: ainda é necessário no 2004+? (fórum Wagnardsoft)](https://www.wagnardsoft.com/forums/viewtopic.php?p=7076)
- Aviso do moderador do r/OptimizedGaming ("Avoid ANY tweak or optimization tools, even more so those closed source"): só o título foi lido; o Reddit bloqueou a página.

---

# Terceira rodada: o que a imprensa mediu, anti-cheat, processadores e golpes (12/11)

## Debloat dá FPS? A imprensa mediu
- **PC Games Hardware (Ancient Gameplays), Windows 11 normal contra "Nano 11" enxuto:** Ryzen 7 7800X3D, RX 9070, 1080p. **FPS médio igual, dentro da margem de medição.** A interface do enxuto respondia mais rápido. Conclusão deles: para jogos, não compensa.
- **Gridinsoft (out/2026), riscos do debloat:** desinstalar o programa de ajuste não desfaz o que ele mudou; ponto de restauração não é backup; o AtlasOS só sai reinstalando o Windows; download de "versão" em vídeo, anúncio ou chat é outra cadeia de distribuição, mesmo com o nome certo.
- **Para o Katharos:** confirma o caminho de não prometer FPS e de medir neste PC. Também confirma que desfazer item por item, com registro do valor de antes, é o diferencial que importa (o que a Gridinsoft diz faltar nos outros).

## Segurança do Windows contra FPS: quanto custa de verdade
- **Tom's Hardware (mar/2023), VBS ligado contra desligado:** Core i9-13900K e RTX 4090, 15 jogos. **Em média até 5 % menos com VBS** (cerca de 2 % em 4K), 10 % no Flight Simulator (15 % no 1% low), quase nada em vários jogos. Em PC menos extremo, "poucos pontos percentuais".
- **Anti-cheat agora exige essa segurança:**
  - **FACEIT (central de ajuda):** Windows 11 obrigatório desde **14/10/2026**. TPM 2.0, Secure Boot, VBS e IOMMU estão sendo exigidos "em ondas".
  - **Riot Vanguard, modo sob demanda (Tom's Hardware, 25/06/2026):** exige Windows 11 25H2, Secure Boot, TPM 2.0, VBS, HVCI e IOMMU. Assim o driver só carrega quando o jogo abre. Cerca de 35 % dos jogadores já atendem. **Com VBS, a lista de bloqueio de drivers vulneráveis pode desligar driver antigo de periférico.**
- **Para o Katharos:**
  1. Nunca oferecer desligar VBS ou HVCI; quem joga FACEIT ou Valorant perderia o jogo.
  2. **Ideia nova, só leitura: "Pronto para o anti-cheat"** no raio-x ou no Detalhe de jogos. Mostra Windows 11 25H2, TPM 2.0, Secure Boot, VBS, HVCI e IOMMU (ligado ou não), e o que falta para o FACEIT e para o Vanguard sob demanda. O que fica na BIOS vira passo a passo (o Katharos não mexe na BIOS).
  3. O achado "Integridade de memória ligada" (sem ponto) ganha a frase: "custa de 0 a 5 % de FPS na maioria dos jogos; o FACEIT e o Valorant podem exigir ligada".

## Ryzen X3D com dois CCDs precisa do Game Bar
- No Ryzen 9 7900X3D, 7950X3D, 9900X3D e 9950X3D, o driver de chipset da AMD usa o **Xbox Game Bar para saber que um jogo abriu** e mandar o jogo para os núcleos com o cache extra (os outros "estacionam"). Guias de montadores (Evetech) mandam manter o Game Bar instalado e atualizado. Os fóruns da EA, da ASUS e da Bitsum têm casos de núcleos que não estacionam.
- **Risco real no Katharos:** o item "app:Xbox" (pacote apps) remove o `XboxGamingOverlay` (o Game Bar). Hoje ele só deixa de vir marcado quando há jogos instalados. **Mudança:** com um Ryzen X3D de dois CCDs, "app:Xbox" fica nível 0 com o alerta "o seu processador usa o Game Bar para mandar o jogo aos núcleos certos". O "gamedvr" (só a gravação) pode continuar.
- Do lado da Intel, o equivalente é o **Intel APO** (Application Optimization, 14ª geração e Core Ultra 200S, vem pelo Dynamic Tuning). **Ideia:** o raio-x pode dizer "o seu processador tem o APO; instale pelo site do fabricante da placa-mãe" (só aviso, sem programa de terceiros). A página da Corsair não abriu; falta confirmar a lista de processadores e jogos numa fonte da Intel antes de escrever o texto.

## Golpes de "otimização" no Brasil
- **Canaltech (02/02/2026), com dados da Flare via BleepingComputer:**
  - Mods e "melhoradores de FPS" falsos do Roblox circulam no YouTube, em anúncios do Google e no Discord, e pedem para desligar o antivírus.
  - São ladrões de senha (LummaStealer, RedLine, Vidar) que levam senhas do navegador, Discord e carteiras de cripto, e de lá chegam à conta bancária da família.
  - Mais de 40 % das invasões chegam por arquivo de jogo.
- **Reclame Aqui:** reclamações de serviços pagos de "otimização de FPS" (XD FPS, Bravo Technologies, TweaksBW) por propaganda enganosa, instabilidade depois do serviço e reembolso negado. Uma tem o título "perdi tudo do computador". As páginas não abriram; só os títulos foram lidos.
- **Para o Katharos:**
  1. O site e o aviso de uso podem dizer com todas as letras: "o Katharos nunca pede para desligar o antivírus".
  2. O download só vem do GitHub, com SHA-256.
  3. O raio-x já acusa "Tarefas agendadas suspeitas". Ele pode também procurar restos conhecidos de "packs" (tarefa ou serviço com nome de otimizador de FPS rodando de AppData). Fica para pensar, sem falso alarme.

## Fontes da terceira rodada
- [PCGH: Windows 11 Standard gegen Nano Debloat](https://www.pcgameshardware.de/Windows-Software-277633/News/Standard-gegen-Nano-Debloat-Gaming-Performance-1472429/)
- [Gridinsoft: Windows 11 Debloat Tools, Safety, Rollback and Security Trade-Offs](https://blog.gridinsoft.com/windows-11-debloat-tools-safety/)
- [Tom's Hardware: Default Windows VBS Setting Slows Games Up to 10%](https://www.tomshardware.com/news/windows-vbs-harms-performance-rtx-4090)
- [FACEIT: Windows Security Requirements FAQ](https://support.faceit.com/hc/en-us/articles/23117181142556)
- [Tom's Hardware: Riot Vanguard on-demand mode](https://www.tomshardware.com/video-games/pc-gaming/riot-vanguard-adds-an-on-demand-mode-that-stops-anti-cheat-loading-at-boot-on-secured-windows-11-pcs)
- [Evetech: microstutter no Ryzen 9 9950X3D](https://evezone.evetech.co.za/build-lab/how-to-fix-microstutter-on-windows-11-with-a-ryzen-9-9950x3d-build) · [EA Forums: 9950X3D core parking](https://forums.ea.com/discussions/battlefield-6-technical-issues-en/9950x3d-core-parking/12741808) · [Bitsum: "Not Functional With Xbox Game Bar"](https://community.bitsum.com/forum/index.php?msg=31381)
- [Canaltech: macete para melhorar Roblox pode limpar conta bancária](https://canaltech.com.br/seguranca/alerta-macete-para-melhorar-roblox-pode-limpar-conta-bancaria-dos-pais/)
- Reclame Aqui: [XD FPS, propaganda enganosa](https://www.reclameaqui.com.br/xd-fps-tecnologia/propaganda-enganosa-e-falta-de-suporte-apos-compra-de-otimizacao-de-fps_k9BjE7Pml7eSwB5d/) · [Bravo Technologies, instabilidade](https://www.reclameaqui.com.br/bravo-technologies/servico-de-otimizacao-de-pc-causa-instabilidade-e-nao-cumpre-o-prometido-solicito-reembolso_z-lX504RVAb5mr9v/)

## O que a própria Microsoft diz
- **"Configurar um dispositivo para tempo real" (Windows IoT Enterprise):** é a página que os guias de "tunagem" citam para desligar SysMain, DPS, CPU idle e Windows Update. A própria página diz que **só serve para um aparelho e um programa feitos sob medida** (máquina industrial), não para PC de uso geral. A mesma lista desliga o **áudio do Windows (Audiosrv)** e o **Windows Update** (a Microsoft avisa que deixa o aparelho vulnerável). **Para o Katharos:** quando alguém perguntar "por que vocês não desligam SysMain e C-states, se a Microsoft recomenda?", a resposta tem fonte: é recomendação para máquina industrial, junto com tirar o som e as atualizações.
- **"Otimizações para jogos em janela" (suporte da Microsoft, em pt-BR):** muda jogos **DirectX 10 e 11** em janela ou sem borda do modelo antigo de apresentação (blt) para o novo (flip). Isso reduz a latência do quadro e libera VRR e HDR automático. Não cita DirectX 12 (que já usa flip). Ligar o HDR automático liga isso junto; dá para desligar por jogo em Configurações > Sistema > Vídeo > Gráficos. **Confirma o item "directx-jogos" do Katharos.** Falta o texto dizer que vale para DX10 e DX11 e que um jogo com problema pode ser desligado sozinho, por jogo.

Fontes: [Microsoft Learn: How to set up a device for real-time performance](https://learn.microsoft.com/en-us/windows/iot/iot-enterprise/soft-real-time/soft-real-time-device) · [Suporte Microsoft: Otimizações para jogos com janelas no Windows 11](https://support.microsoft.com/pt-BR/Windows/Hardware/Display-Graphics/optimizations-for-windowed-games-in-windows-11)

---

# Lista única do que fazer (junta as três rodadas)

**Corrigir no que o Katharos já aplica (4.3.2):**
1. "rede-jogos": tirar o `NetworkThrottlingIndex` desligado (piora a latência do driver de rede). Fica só o Nagle.
2. "app:Xbox": nível 0 e alerta em Ryzen X3D de dois CCDs (o Game Bar manda o jogo aos núcleos com cache).
3. Textos honestos: "mmcss" (a tarefa Games não é usada), "timer" (só vale se um programa pedir), "directx-jogos" (DX10 e DX11, dá para desligar por jogo), "Integridade de memória" (0 a 5 % e exigida por FACEIT e Valorant).
4. Widgets: feito sem o pacote WebExperience; senão, remover o app ou abrir Configurações.

**Novos, só leitura (4.4.0):**
5. "Pronto para o anti-cheat": Windows 11 25H2, TPM 2.0, Secure Boot, VBS, HVCI e IOMMU, com o que falta para o FACEIT e o Vanguard sob demanda.
6. Jogo registrado no GameConfigStore (Modo de Jogo funcionando).
7. Modo de apresentação de cada sessão (PresentMon).
8. Processador com Intel APO (só aviso, depois de confirmar numa fonte da Intel).

**Novos itens (4.4.0):**
9. WPBT desligado (2) · sem app de fabricante sozinho (1) · não abaixar o volume em chamadas (2) · Inicialização rápida (0) · hibernação em desktop (3) · permissões de apps (2).
10. Pop-ups do Bing pelo IFEO, só depois de testar no Windows com o Defender.

**Comunicação:** no site e no aviso, "o Katharos nunca pede para desligar o antivírus e não promete FPS: mede no seu PC".
