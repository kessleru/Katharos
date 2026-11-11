# Plano: personalização, mais otimização, relatório com envio e proteção do projeto

Pedido de 11 nov 2026 (08:22 e 08:26): grandes melhorias de otimização, **muito mais personalização do Windows** com exemplo em imagem e
vídeo de cada opção (hospedado fora do programa, sem pesar a instalação), ideias tiradas do Windhawk e de outros programas, melhorias de
interface, de segurança e correção de bugs, **um relatório mais completo com envio direto para o dono** (inclusive problemas do próprio
Katharos). Personalizações **bem funcionais e sem problemas**. E deixar claro, em todo lugar, que o projeto **não tem fins
lucrativos**, para evitar problema jurídico.

Este arquivo é o plano e o registro: cada tarefa tem um código; quando ficar pronta, marque `[x]` e anote no **Registro** (fim do arquivo)
a data, a versão e o commit. A pesquisa que embasa o plano está em [cofre/2026-11-11-pesquisa-personalizacao.md](cofre/2026-11-11-pesquisa-personalizacao.md).

**Escopo (pedido das 08:46):** o plano tem só o que dá para fazer hoje, com o Windows e as ferramentas que existem agora. Ideias
futuras, recursos que dependem de versão ainda não lançada do Windows e extras sem fase ficaram de fora.

**Estado:** planejado. Nada começou. As decisões marcadas **(dono decide)** esperam resposta antes da fase em que entram.

| fase | versão | o quê | estado |
|---|---|---|---|
| 0 | — | confirmar no Windows do CI o que este plano supõe (chaves, Windhawk, PowerToys) | a fazer |
| 1 | 4.1.0 | segurança e antivírus, proteção jurídica, bugs pendentes | a fazer |
| 2 | 4.1.0 | relatório completo com envio direto | a fazer |
| 3 | 4.2.0 | personalização nativa (sem programa extra) com galeria de imagens e vídeos | a fazer |
| 4 | 4.3.0 | estilos prontos e programas auxiliares (PowerToys, Windhawk com receitas) | a fazer |
| 5 | 4.4.0 | otimizações novas e perfis automáticos (jogo aberto, bateria, tomada) | a fazer |
| 6 | 4.5.0 | interface: busca, prévias, acessibilidade, inglês | a fazer |

Cada fase vira uma versão MENOR pela regra do CHANGELOG (entra algo que o usuário vê). As fases 1 e 2 saem juntas na 4.1.0.

---

## 1. Decisões

### P1. Personalização fica fora dos três modos
Seguro, equilibrado e extremo continuam sendo **otimização**. Personalização é gosto: nunca entra sozinha por modo nenhum. A pessoa abre a
tela **Personalizar**, vê a prévia de cada opção e marca o que quer. Tudo volta pelo Desfazer, como hoje. Isso também mantém a regra de
que nada muda a imagem por conta própria.

### P2. "Funcional e sem problemas" decide o caminho de cada opção, nesta ordem
1. **Nativo do Windows** (registro, política oficial ou tela de Configurações): é o padrão. Sobrevive às atualizações, não injeta nada,
   volta pelo Desfazer e é lido de volta depois de aplicar (regra S4).
2. **PowerToys** (Microsoft, assinado, código aberto): instalado pelo winget só se a pessoa pedir; o Katharos liga o módulo e explica.
3. **Windhawk com receita** (fase 4): só mods que entram **apenas no shell do Windows** (explorer, menu Iniciar, central de notificações,
   Configurações). Mods que entram em **todos os processos** (`*`) ou no **compositor de tela** (`dwm.exe`) ficam fora das receitas,
   porque podem chegar a um jogo com anti-cheat ou causar falha na imagem. Ver P3.
4. **Outros programas** (StartAllBack, ExplorerPatcher, Seelen UI etc.): o Katharos **não instala**. Só mostra um cartão com o que fazem,
   o risco conhecido e o link oficial. Motivo concreto: o Windows 11 24H2 chegou a **barrar a atualização** em PCs com StartAllBack e
   ExplorerPatcher ([Pureinfotech](https://pureinfotech.com/windows-11-24h2-blocks-customization-apps)).

Nada de personalização que troque arquivo do sistema (`imageres.dll`, temas não assinados com patch do `uxtheme`), troque a fonte do
sistema, mexa em DPI ou escala, ou dependa de remover proteção do Windows. Isso é o que costuma quebrar depois de uma atualização.

### P3. Windhawk: opcional, com freio para jogos
O Windhawk injeta o próprio motor em **todos os processos**, menos uma lista de exclusões; por padrão já exclui jogos nas pastas comuns de
Steam, Epic, Riot, Ubisoft e EA ([wiki do Windhawk](https://github.com/ramensoftware/windhawk/wiki/Injection-targets-and-critical-system-processes)).
Isso conflita com a regra "nada que injete em processo de jogo", então:
- o Katharos **nunca** instala o Windhawk sozinho; só com a pessoa pedindo, depois de um aviso claro do que ele faz;
- antes de ativar qualquer receita, o Katharos **acrescenta à lista de exclusão do Windhawk** os jogos que ele mesmo achou fora das pastas
  padrão (catálogo e jogos detectados) e os executáveis de anti-cheat; a lista é lida de volta;
- receitas só com mods de alvo explícito no shell (P2.3); nenhum mod `*` ou `dwm.exe` vem por receita.
**(dono decide)** se o Katharos pode instalar o Windhawk pelo winget, ou se só explica e manda para o site oficial.

### P4. Galeria de prévias hospedada fora do programa
- **Onde:** um repositório separado e público, `kessleru/katharos-galeria`, publicado pelo GitHub Pages. Limite do Pages: site de até 1 GB
  e banda de 100 GB/mês, limite flexível ([docs do GitHub](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)).
  Fica separado do site principal para não pesar o deploy dele.
- **Formato e orçamento:** imagem WebP de até 80 KB (1280 px de largura); vídeo curto WebM sem som, 4 a 8 s em loop, até 600 KB. Galeria
  inteira com teto de 150 MB.
- **No aplicativo:** baixa só a prévia do cartão que aparece na tela; guarda até 40 MB em `%LOCALAPPDATA%\Katharos\galeria` (sai o mais
  antigo); confere o SHA-256 contra um `manifesto.json` da galeria; sem internet, mostra o texto e "a prévia aparece quando conectar". O
  download fica no C# (o Python do motor continua sem rede).
- **Quem gera:** o próprio CI. Um job no Windows do GitHub aplica cada opção numa máquina descartável, tira a foto (antes e depois) e
  grava o vídeo curto; assim a prévia é sempre a do Windows de verdade e se refaz sozinha quando algo mudar. Mods do Windhawk com
  animação são gravados do mesmo jeito.
- **Direitos:** todas as imagens são capturas da própria tela, feitas pelo projeto. Nada de imagem tirada de site de terceiros.

### P5. Relatório: envio sem conta, guardado em lugar privado
O relatório tem dados do PC. Issue pública no GitHub expõe esses dados para qualquer um, então:
- **Caminho principal (sem conta):** o aplicativo envia o relatório **já limpo** para um endpoint pequeno (Cloudflare Worker, plano grátis)
  que abre uma issue num repositório **privado** `kessleru/katharos-relatorios`, com um token de GitHub App guardado como segredo do
  Worker. A pessoa recebe um código (`KTH-7F3A`) para citar depois. Proteções: tamanho máximo de 200 KB, esquema validado, limite por
  IP, desafio Turnstile, e nenhum dado guardado no Worker.
- **Caminho alternativo (com conta GitHub):** abre a issue pública com o formulário já preenchido só com o resumo, sem dado pessoal
  (`issues/new?template=...&title=...&body=...`; URL longa demais dá erro 414,
  [docs do GitHub](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-an-issue#creating-an-issue-from-a-url-query)),
  e o aplicativo abre a pasta com o arquivo completo selecionado para a pessoa arrastar, se quiser.
- **Sempre:** prévia do que vai, seções que a pessoa pode tirar, e consentimento explícito antes de cada envio.
**(dono decide)** criar a conta grátis da Cloudflare e o repositório privado. Sem isso, a 4.1.0 sai só com o caminho alternativo.

### P6. Projeto sem fins lucrativos, dito em todo lugar
O Katharos é pessoal, gratuito e de código aberto (licença MIT), sem venda, anúncio, rastreamento ou doação. Isso aparece no site, no
aplicativo, no README, no instalador e no relatório (ver fase 1, J1 a J8). Isto é organização e transparência, não parecer jurídico.

---

## 2. Catálogo de personalização (fase 3 e 4)

Cada opção tem: o que muda, **prévia** (imagem ou vídeo da galeria), caminho (nativo, PowerToys, Windhawk), em que Windows funciona,
e como volta. As chaves listadas são as conhecidas hoje; **todas são confirmadas na fase 0** no Windows 10 22H2, 11 24H2 e 11 25H2 do CI.
Valores que o driver UCPD da Microsoft bloqueia (o Katharos já reconhece essa proteção) viram atalho para a tela do Windows.

### 2.1 Barra de tarefas
| opção | caminho | nota |
|---|---|---|
| ícones à esquerda ou no centro | nativo (`TaskbarAl`) | já existe em ajustes |
| busca: escondida, ícone, caixa | nativo (`SearchboxTaskbarMode`) | |
| esconder Visão de Tarefas, Widgets, Copilot | nativo | Widgets pode estar protegido pelo UCPD |
| nunca agrupar e mostrar rótulos | nativo (`TaskbarGlomLevel`) | Windows 11 23H2+ |
| segundos no relógio | nativo | já existe |
| "Finalizar tarefa" no botão direito | nativo | já existe |
| esconder sozinha | nativo | |
| barra no topo, na lateral ou menor | Windhawk (`taskbar-on-top`, `taskbar-vertical`, `taskbar-icon-size`) | só se a pessoa tiver o Windhawk (fase 4) |
| esconder só quando há janela maximizada | Windhawk `taskbar-auto-hide-when-maximized` | |
| volume rolando o mouse na barra (geral e por app) | Windhawk `taskbar-volume-control`, `taskbar-volume-control-per-app` | |
| relógio com data longa, rede e CPU | Windhawk `taskbar-clock-customization` | |
| esconder ícones do sistema na bandeja e espaçamento | Windhawk `taskbar-tray-system-icon-tweaks`, `taskbar-notification-icon-spacing` | |
| clique do meio fecha o programa | Windhawk `taskbar-button-click` | |
| visual da barra (transparente, arredondada, temas) | Windhawk `windows-11-taskbar-styler` | o mod mais usado (1,1 mi) |

### 2.2 Menu Iniciar
| opção | caminho | nota |
|---|---|---|
| mais fixados ou mais recomendados | nativo (`Start_Layout`) | já existe |
| esconder "Recomendados/Recentes", tamanhos prontos | nativo (Configurações > Personalização > Iniciar, 25H2) | atalho direto para a tela quando não houver chave segura |
| pastas ao lado do botão de energia (Downloads, Configurações, Explorador…) | nativo (política `AllowPinnedFolder*`) | |
| botões de desligar, reiniciar e suspender com um clique | Windhawk `win11-power-buttons` | |
| abrir já em "Todos os apps" | Windhawk `start-menu-all-apps` | |
| visual do Iniciar (temas) | Windhawk `windows-11-start-menu-styler` | 1,0 mi de usuários |

### 2.3 Explorador de Arquivos
| opção | caminho | nota |
|---|---|---|
| abrir em Este Computador, extensões, ocultos, modo compacto, caixas de seleção | nativo | já existem |
| menu do botão direito completo | nativo | já existe (`menu-classico`) |
| tirar Galeria, Início e OneDrive da lateral | nativo (CLSID `System.IsPinnedToNameSpaceTree`) | |
| tamanho das pastas na coluna Tamanho, MB e GB legíveis | Windhawk `explorer-details-better-file-sizes` | 240 mil usuários |
| sem aviso ao trocar a extensão | Windhawk `extension-change-no-warning` | |
| sem clarão branco ao abrir abas no escuro | Windhawk `fix-explorer-white-flash` | |
| tirar itens do menu do botão direito | Windhawk `remove-context-menu-items` | |
| visual do Explorador | Windhawk `windows-11-file-explorer-styler` | |

### 2.4 Cores, tema e área de trabalho
| opção | caminho | nota |
|---|---|---|
| modo escuro | nativo | já existe |
| tema escuro e claro automático pelo horário | PowerToys **Light Switch** | |
| cor de destaque nas barras de título e bordas | nativo (`DWM\ColorPrevalence`) | |
| cor de destaque no Iniciar e na barra | nativo (`Personalize\ColorPrevalence`) | só no modo escuro |
| ícones Este Computador e Lixeira na área de trabalho | nativo (`HideDesktopIcons`) | |
| papel de parede: Destaque do Windows, apresentação, um por monitor | tela de Configurações (atalho) | |
| temas oficiais da Microsoft Store | atalho para a Loja | |
| ponteiro maior ou colorido | tela de Acessibilidade (atalho) | |

### 2.5 Janelas e multitarefa
| opção | caminho | nota |
|---|---|---|
| Alt+Tab sem abas do Edge | nativo (`MultiTaskingAltTabFilter`) | |
| layouts de Snap ao passar no maximizar, sacudir para minimizar | nativo | "sacudir" já existe |
| sempre visível, zonas de janela | PowerToys **Always on Top**, **FancyZones** | |
| Alt+Tab e Win+D só no monitor do mouse | Windhawk `alt-tab-per-monitor`, `win-d-per-monitor` | |
| cantos menos arredondados, bordas, animações, janelas translúcidas | Windhawk (`custom-corner-radius`, `translucent-windows`, `windows-animations`) | **fora das receitas** (P2.3): entram em todos os processos ou no `dwm.exe`. Só como cartão informativo |

### 2.6 Tela de bloqueio, entrada, notificações e sons
| opção | caminho | nota |
|---|---|---|
| sem "curiosidades e dicas" na tela de bloqueio | nativo (`ContentDeliveryManager`) | |
| tela de entrada sem desfoque | nativo (política `DisableAcrylicBackgroundOnLogon`) | já existe dentro de transparência |
| não perturbe com horário | tela de Configurações (atalho) | |
| notificações em outro canto ou monitor | Windhawk `notifications-placement` | |
| visual da central de notificações | Windhawk `windows-11-notification-center-styler` | |
| esquema de sons "Sem sons" | nativo (`AppEvents\Schemes`) | não é qualidade de áudio, é o som do sistema |
| sons de entrar e desligar de volta | Windhawk `logon-logoff-shutdown-sounds` | |

### 2.7 Teclado, mouse e apps do dia a dia
| opção | caminho | nota |
|---|---|---|
| tecla Copilot abre outro programa | tela de Configurações (atalho, 24H2+) | |
| remapear teclas e atalhos | PowerToys **Keyboard Manager** | |
| lançador de apps e comandos | PowerToys **Command Palette** (com Dock desde a 0.98, [Windows Central](https://www.windowscentral.com/software-apps/my-favorite-free-windows-11-app-just-got-another-great-update-whats-new-in-powertoys-v0-98)) | |
| renomear em lote, redimensionar imagens, prévia rápida | PowerToys **PowerRename**, **Image Resizer**, **Peek** | |
| Bloco de Notas escuro (versão antiga) | Windhawk `notepad-dark-mode` | |
| trocar de aba do Chrome e do Edge com a roda do mouse | Windhawk `chrome-wheel-scroll-tabs` | entra só no navegador |

### 2.8 Estilos prontos (fase 4)
Um clique aplica um conjunto, com prévia do conjunto inteiro e volta em grupo:
- **Windows 10 de volta:** ícones à esquerda, menu completo, nunca agrupar, Explorador em Este Computador, sem Galeria.
- **Limpo:** barra só com ícones, sem busca, Widgets e Copilot, Iniciar sem recomendados, tela de bloqueio sem dicas.
- **Escuro e foco:** modo escuro, cor de destaque nas bordas, não perturbe com horário, Alt+Tab sem abas do Edge.
- **Vários monitores:** Alt+Tab e Win+D por monitor, notificações no monitor principal, FancyZones.
- **Parecido com o Mac (Windhawk):** animação de dock na barra, barra centralizada e mais baixa.

---

## 3. Programas auxiliares (o que o Katharos faz com cada um)

| programa | para quê | o que o Katharos faz |
|---|---|---|
| PowerToys (Microsoft) | Light Switch, FancyZones, Keyboard Manager, Command Palette, Peek, PowerRename, Always on Top | instala pelo winget se a pessoa pedir; liga e explica os módulos da tabela |
| Windhawk | mods de barra, Iniciar, Explorador e notificações | receitas conferidas (P3); exclusão dos jogos |
| Auto Dark Mode | tema por horário com mais opções | cartão com link (o Light Switch já cobre o básico) |
| TranslucentTB | barra transparente sem injetar em todos os processos | cartão com link |
| Open-Shell | menu Iniciar clássico | cartão com link |
| StartAllBack, ExplorerPatcher | Windows 10 de volta, mais completo | cartão **com aviso**: já barraram atualização do Windows (P2.4) |
| Seelen UI, YASB, Rainmeter | trocar a barra ou pôr painéis na área de trabalho | cartão: pesam mais e mudam muito o Windows |
| EarTrumpet | volume por app na bandeja | cartão com link |
| Everything, Flow Launcher | busca de arquivos instantânea | cartão com link (o Katharos já sugere quando a indexação está desligada) |
| Bulk Crap Uninstaller | desinstalar programas em lote, restos | cartão com link |
| O&O ShutUp10++, WinUtil, Sophia Script | privacidade e ajustes em massa | não integrar: fazem ajustes que o Katharos já faz, e misturar os dois confunde o Desfazer; o Katharos avisa se achar sinais deles |
| Autoruns, LatencyMon, CapFrameX, MSI Afterburner | diagnóstico avançado | cartão no Raio-x quando o Katharos não conseguir medir sozinho |

Regra: o Katharos **nunca empacota** programa de terceiro. Instala só pelo winget, com fonte oficial, e só quando a pessoa pede.

---

## 4. Tarefas por fase

### Fase 0: confirmar no Windows de verdade
- [ ] **0.1** Job de CI `personalizacao` (windows-2022 e windows-2025, e Windows 10 22H2 se houver imagem): para cada chave do catálogo, grava,
  lê de volta, desfaz e confere; marca quais o UCPD bloqueia. Resultado vira uma tabela no `cofre`.
- [ ] **0.2** Windhawk no CI: instalar pelo winget (`RamenSoftware.Windhawk`), achar onde ficam os mods, as configurações de cada mod e as
  listas de inclusão e exclusão de processos (registro ou arquivo); confirmar que dá para ler e gravar sem a interface dele.
- [ ] **0.3** PowerToys no CI: onde fica o `settings.json` de cada módulo e se ligar um módulo por arquivo vale sem abrir o PowerToys.
- [ ] **0.4** Protótipo da galeria: 5 opções, foto antes e depois e um vídeo, gerados no CI e publicados no `katharos-galeria`.

### Fase 1: segurança, antivírus, proteção jurídica e bugs (4.1.0)
Segurança e antivírus (do diagnóstico do ESET de 11 nov):
- [ ] **1.1** Trocar o `-EncodedCommand` com janela escondida do vigia de tela por um script em arquivo na pasta protegida, rodado com `-File`.
- [ ] **1.2** Desfazer sem `Invoke-Expression`: cada operação de volta vira um registro estruturado (tipo, caminho, nome, valor), executado
  por funções conhecidas. Backups antigos com comando de texto continuam lidos por uma lista de comandos permitidos.
- [ ] **1.3** `atualiza.ps1` fora do instalador (quem instala recebe atualização pelo Velopack); fica só no ZIP de terminal.
- [ ] **1.4** VirusTotal no CI antes de publicar (API grátis, chave como segredo): a release não sai se mais de um motor marcar; se só um
  marcar, publica e abre uma issue com o texto pronto para o envio de falso positivo àquele fabricante.
- [ ] **1.5** Texto pronto de envio de falso positivo para ESET, Microsoft, Avast/AVG, Kaspersky e Bitdefender (`planos/falso-positivo.md`).
- [ ] **1.6** Assinatura pela SignPath (já planejada em `assinatura-signpath.md`): o dono envia o pedido.
- [ ] **1.7** Repositório protegido: proteção da `main` (CI obrigatório), proteção de tags `v*`, ambiente `release` com aprovação do dono,
  ações fixadas por SHA, Dependabot para NuGet e GitHub Actions, CodeQL para C# e Python, varredura de segredos. Checklist para o dono:
  2FA, log de segurança, apps autorizados.
- [ ] **1.8** Notas da release com o hash de cada arquivo e o link da atestação de origem do build (já gerada pelo `attest-build-provenance`).

Proteção jurídica (P6):
- [ ] **J1** Site: rodapé fixo "Projeto pessoal, gratuito e de código aberto, sem fins lucrativos. Sem anúncios, sem venda, sem
  rastreamento. Não é afiliado à Microsoft, à Ramen Software (Windhawk) nem a nenhuma outra marca citada; as marcas pertencem aos
  donos." Mais uma página **Aviso legal** com o mesmo texto, completo.
- [ ] **J2** Aplicativo: tela **Sobre** com o aviso, a licença MIT, "sem garantia" e as licenças de terceiros; o aviso curto também na
  primeira abertura (uma vez, sem bloquear).
- [ ] **J3** README e instalador: o mesmo aviso no topo do README e na página de licença do instalador.
- [ ] **J4** `THIRD-PARTY-NOTICES.md` com a licença de tudo que vai junto: Python, .NET, Avalonia, SkiaSharp, HarfBuzz, Velopack,
  SQLite, OpenSSL, PresentMon e as fontes do site e do aplicativo. Gerado no CI a partir do pacote, para nunca ficar desatualizado.
- [ ] **J5** Marcas: usar nomes de terceiros só para dizer o que é compatível ("funciona com o Windhawk"), sem logotipo da Microsoft, do
  Windows ou de outros, e sem sugerir parceria. Revisão do site e do aplicativo com essa regra.
- [ ] **J6** Galeria e mods: a galeria só usa capturas próprias; o Katharos não redistribui mods do Windhawk (eles vêm do próprio
  Windhawk), só guarda a **configuração** da receita e o link para o mod e o autor.
- [ ] **J7** **Política de privacidade** (LGPD) no site e no aplicativo, antes do envio de relatório existir: o que vai, para quê, onde
  fica (repositório privado), por quanto tempo (90 dias, depois apagado), como pedir para apagar (pelo código `KTH-...`), e que nada
  é vendido nem compartilhado.
- [ ] **J8** Doação, patrocínio e venda: **não entram** no projeto.

Bugs e pendências:
- [ ] **1.9** Pendências da 4.0: 2.13 (primeira abertura com 3 pessoas leigas), 2c.1 e 2c.2 (teste jogando no kesslerupc).
- [ ] **1.10** Os testes de abuso desta sessão viram testes permanentes no CI: estado corrompido em todos os métodos do motor, os 57
  comandos com estado corrompido, sintaxe de todos os scripts PowerShell no Windows PowerShell 5.1 de verdade, `pyflakes` e Python 3.8.
- [ ] **1.11** Teste de ida e volta (aplicar e desfazer, registro e serviços iguais no fim) para **todos** os pacotes no CI, não só privacidade.
- [ ] **1.12** Lighthouse no celular (hoje 75): tudo que não for a imagem do herói (que fica intocada).

### Fase 2: relatório completo com envio (4.1.0)
- [ ] **2.1** Conteúdo novo do relatório, além do que já tem (PC, aplicado, avisos e erros, não reconhecido):
  - **problemas do Katharos:** erros internos do motor (com rastro), exceções da janela (o tratador global já existe), itens que "não
    ficaram", travamentos do segundo plano, tempo de cada etapa, versão, canal e histórico de atualizações;
  - **ambiente:** Windows (build, edição, idioma), antivírus instalados e se algum mexeu em arquivo do Katharos (Defender:
    `Get-MpThreatDetection`; outros: o que o Central de Segurança do Windows informa), PowerShell, .NET, Python;
  - **saúde:** telas azuis, desligamentos inesperados e erros de disco recentes (já medidos), temperatura e travadas.
- [ ] **2.2** Limpeza antes de sair do PC: tirar nome de usuário (vira `%USERPROFILE%`), nome do PC, números de série, IPs, MAC, nomes
  de rede Wi-Fi, e-mails e nomes de arquivos de pastas pessoais. Teste com um relatório "envenenado" com todos esses dados. O filtro de
  texto suspeito que já existe (`limpa`) continua.
- [ ] **2.3** Tela **Enviar relatório**: prévia legível, seções com caixa para tirar, campo "o que aconteceu?", consentimento, e os dois
  caminhos de P5. Depois de enviar, mostra o código `KTH-...` e guarda no Histórico.
- [ ] **2.4** Worker de recebimento (se o dono aprovar P5): código no repositório (`servidor/relatorio-worker`), testes, deploy pelo CI,
  limites de P5. O relatório chega como issue no repositório privado com rótulos automáticos (versão, Windows, tipo de erro).
- [ ] **2.5** Formulário de issue pública (`.github/ISSUE_TEMPLATE/problema.yml`) para quem prefere o GitHub, sem campos de dado pessoal.
- [ ] **2.6** Envio automático quando der erro: **desligado por padrão**; se a pessoa ligar, ainda mostra a prévia antes do primeiro envio.
- [ ] **2.7** Lado do dono: um script que lê os relatórios do repositório privado e monta um resumo (erros mais comuns por versão e
  Windows, itens que mais "não ficam"), rodado pelo CI uma vez por semana.

### Fase 3: personalização nativa com galeria (4.2.0)
- [ ] **3.1** Pacote `personalizar` no motor, fora dos modos (P1), com as opções nativas das seções 2.1 a 2.7; cada uma lida de volta
  e com desfazer; o que só tem tela no Windows vira atalho `ms-settings:` com a explicação de onde clicar.
- [ ] **3.2** Tela **Personalizar** no aplicativo: categorias da seção 2, cartão com prévia (foto antes e depois ou vídeo), "o que muda",
  "funciona neste Windows?", e o botão de aplicar e desfazer; mostra o que já está assim.
- [ ] **3.3** Galeria (P4): repositório, manifesto com SHA-256, geração no CI, cache no aplicativo, comportamento sem internet.
- [ ] **3.4** Página **Personalizar** no site, com a mesma galeria, para quem ainda não instalou.
- [ ] **3.5** Testes: cada opção em cada Windows do CI (aplica, confere, desfaz, confere), e a foto da galeria refeita quando o Windows muda.

### Fase 4: estilos prontos e programas auxiliares (4.3.0)
- [ ] **4.1** Estilos prontos da seção 2.8, com prévia do conjunto e volta em grupo.
- [ ] **4.2** PowerToys: detectar, instalar pelo winget quando pedido, ligar os módulos da seção 3 e explicar cada um.
- [ ] **4.3** Windhawk (P3), se o dono aprovar: detectar, instalar quando pedido, gravar a exclusão dos jogos e dos anti-cheats, aplicar as
  receitas (mod de alvo só no shell e a configuração conferida), e desfazer (desliga o mod e volta a configuração anterior).
- [ ] **4.4** Cartões dos outros programas (seção 3), com o risco conhecido e o link oficial.
- [ ] **4.5** Exportar e importar o seu estilo (um JSON pequeno) para levar a outro PC ou mandar a um amigo; ao importar, o Katharos
  mostra a lista antes de aplicar.

### Fase 5: otimizações novas e perfis automáticos (4.4.0)
- [ ] **5.1** **Perfis automáticos** pelo segundo plano, sem tocar no jogo: ao abrir um jogo, liga o modo de energia "melhor desempenho",
  pausa downloads de atualização e liga o não perturbe; ao fechar, volta tudo. No notebook, troca de perfil na tomada e na bateria.
  Tudo opcional, com registro no Histórico.
- [ ] **5.2** Placa de vídeo por jogo em notebook com duas placas: grava a preferência "alto desempenho" para os jogos detectados (a mesma
  opção de Configurações > Tela > Gráficos), com desfazer. Sem mexer em driver.
- [ ] **5.3** Limite de banda da Otimização de Entrega e horário ativo do Windows Update (políticas oficiais), para atualização não
  roubar internet no jogo.
- [ ] **5.4** Segundo plano por app (em vez de desligar para todos): lista dos apps da Loja que rodam escondidos, com o custo medido de cada um.
- [ ] **5.5** Inicialização atrasada em vez de removida: programa pesado continua abrindo, só alguns minutos depois de entrar no Windows
  (tarefa agendada com atraso), medido no boot seguinte.
- [ ] **5.6** Modo de energia do Windows 11 (sobreposição "melhor desempenho" e "melhor eficiência"), além do plano, lido de volta.
- [ ] **5.7** Disco pequeno: compactação do Windows (`compact /compactos`) só quando o raio-x mostrar SSD pequeno e quase cheio, com o
  ganho estimado antes; e pastas duplicadas grandes, com remoção para a Lixeira.
- [ ] **5.8** Kits de programas pelo winget (jogos, escritório, estudo), com o que já está instalado marcado e a fonte oficial de cada um.
- [ ] **5.9** Itens que **não** entram, com o motivo escrito no site (para ninguém pedir de novo): limpador de memória "standby" (ganho
  não comprovado), arquivo de paginação, desligar Defender ou Integridade de Memória, apagar drivers, "boosters" de FPS.

### Fase 6: interface (4.5.0)
- [ ] **6.1** Busca em tudo (Ctrl+K): itens, personalização, telas e perguntas, com a prévia na própria busca.
- [ ] **6.2** Prévia também no Otimizar: cada item com foto ou vídeo quando fizer sentido (usa a mesma galeria).
- [ ] **6.3** Modo simples e modo avançado: o simples mostra só modos, estilos e o botão de relatório.
- [ ] **6.4** Acessibilidade: navegação completa pelo teclado, nomes para leitor de tela, alto contraste e tamanho de texto do Windows.
- [ ] **6.5** Linha do tempo do Histórico com o "antes e depois" de cada valor e o que foi medido depois.
- [ ] **6.6** Novidades da versão dentro do aplicativo, na primeira abertura depois de atualizar.
- [ ] **6.7** Inglês (aplicativo, site e galeria), com o português continuando o principal.

---

## 5. Critérios de pronto
- Cada opção de personalização: funciona nos Windows do CI, lê de volta, desfaz e tem prévia na galeria.
- Nenhuma personalização entra por modo; nenhuma receita usa mod que entra em todos os processos ou no `dwm.exe`.
- O instalador não cresce por causa da galeria (diferença menor que 100 KB).
- Relatório: o teste "envenenado" não deixa sair nenhum dado pessoal; nenhum envio sem prévia e consentimento.
- Aviso de "sem fins lucrativos e sem afiliação" no site, no aplicativo, no README e no instalador.
- VirusTotal sem alerta de mais de um motor em cada release.

## 6. Riscos
| risco | o que fazer |
|---|---|
| Atualização do Windows muda uma chave de personalização | o job 0.1 roda toda semana; opção que parar vira "não funciona neste Windows" até ser corrigida |
| Mod do Windhawk quebra depois de uma atualização do Windows | receita guarda a versão do mod conferida; a nova só entra depois de passar no CI |
| Anti-cheat reclama do Windhawk | exclusão dos jogos antes de qualquer receita; aviso claro; o Windhawk nunca é instalado sozinho |
| Galeria fora do ar | o aplicativo mostra só o texto; nada deixa de funcionar |
| Abuso do endpoint de relatório | Turnstile, limite por IP e por tamanho, nada guardado no Worker, token com acesso só ao repositório privado |
| Antivírus marcar de novo | fase 1 (1.1 a 1.6) e assinatura |

## 7. Regras que continuam valendo
- Mostrar cada mudança antes, desfazer tudo, ponto de restauração, ler de volta antes de dizer "feito".
- Nada que abra, leia ou injete em processo de jogo; nada de driver; o Katharos nunca encerra processo sozinho.
- Nada mexe na qualidade de áudio ou imagem no nível da placa de vídeo (sem artefato); personalização visual só quando a pessoa escolhe.
- O Python do motor não acessa a rede: download fica com o C# ou o PowerShell.
- Hero do site intocado, sem animação pesada, linhas horizontais e "+" mantidos.
- Commits sem linha de coautoria. Versões pela regra do CHANGELOG. Cada release conferida (tag, hashes, download).

## 8. Fontes
- Windhawk: [catálogo oficial de mods](https://mods.windhawk.net/catalog.json) (898 mods, número de usuários de cada um),
  [repositório dos mods](https://github.com/ramensoftware/windhawk-mods),
  [processos em que entra e exclusões](https://github.com/ramensoftware/windhawk/wiki/Injection-targets-and-critical-system-processes),
  [Windows Central: 7 mods](https://www.windowscentral.com/microsoft/windows-11/7-best-windhawk-mods-to-transform-your-desktop-on-windows-11),
  [TechPP: mods úteis](https://techpp.com/2025/11/17/best-windhawk-mods-windows/),
  [discussão sobre VAC no Steam](https://steamcommunity.com/discussions/forum/9/601891467285283647/?l=swedish)
- Windows: [24H2 barrando StartAllBack e ExplorerPatcher](https://pureinfotech.com/windows-11-24h2-blocks-customization-apps)
- PowerToys: [novidades da 0.98](https://www.windowscentral.com/software-apps/my-favorite-free-windows-11-app-just-got-another-great-update-whats-new-in-powertoys-v0-98)
- WinUtil: [o que faz em 2026](https://christitus.com/winutil-in-2026/)
- GitHub: [limites do Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits),
  [issue por URL](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-an-issue#creating-an-issue-from-a-url-query)

---

## Registro
- 11 nov 2026: plano escrito a partir do pedido das 08:22 e 08:26.
- 11 nov 2026 (08:46): plano enxugado a pedido do dono: saiu a seção de ideias futuras, o recurso do Windows 26H2 e a extensão do Command Palette.
