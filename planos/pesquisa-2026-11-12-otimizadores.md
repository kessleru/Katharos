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
