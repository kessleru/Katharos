# Katharos

*καθαρός*, em grego: limpo, purificado.

**Deixa qualquer Windows mais leve, num arquivo só.** Diagnóstico com nota, limpeza, programas e apps de fábrica, inicialização, serviços, privacidade, IA do Windows, visual, jogos, energia, disco, reparo, atualizações, rede, manutenção automática e reversão de tudo.

Mesmo visual e mesma ideia do [Ferramentas](https://github.com/kessleru/Ferramentas): Python 3.8+, **zero dependências**, terminal kterm 2.0.0 embutido. Por baixo, só ferramentas nativas do Windows: PowerShell, DISM, sfc, chkdsk, defrag, powercfg, winget.

Site: **[kessleru.github.io/Katharos](https://kessleru.github.io/Katharos)**

## Antes de usar

O Katharos muda configurações do Windows. Leia isto antes de rodar (o programa mostra o mesmo aviso na primeira vez e pede que você digite `entendi`; depois, `katharos aviso`).

- **O que ele faz.** O Katharos muda configurações do Windows: serviços, tarefas, registro, rede, energia e, se você marcar, remove programas. É para quem quer escolher o que muda. Cada item diz o que faz (? e o número) e mostra o código (v e o número).
- **Como voltar.** Tudo que ele muda guarda o valor anterior e volta com "desfazer". A exceção são os itens marcados "sem volta" (remover programas e apps, apagar arquivos): esses não voltam. Antes de mexer a fundo, crie um ponto de restauração ("restaurar") e salve o que for importante.
- **Onde não usar.** Não use em computador de trabalho, de escola ou de outra pessoa sem a autorização de quem cuida dele. Programas de empresa, VPN e antivírus corporativo podem parar de funcionar com ajustes de desempenho ou privacidade.
- **Sem garantia.** É um programa gratuito, entregue "como está", sem garantia de funcionar no seu PC, de dar ganho de desempenho ou de ser compatível com tudo. Você usa por sua conta e risco: o autor não responde por perda de dados, falhas ou outros danos que venham do uso. Isto não tira os direitos que a lei garante a você.
- **Jogos.** Itens de jogo podem conflitar com anti-cheat: se o seu jogo usa, leia o aviso do item antes. O Katharos não tem ligação com a Microsoft, a Steam nem com nenhum jogo ou fabricante.
- **Na dúvida.** Comece pelo "raiox" (só lê), use o modo seguro e rode com --teste: ele mostra o que faria sem mudar nada.

O programa é distribuído sob a licença MIT (arquivo `LICENSE`), que também diz que ele é entregue "como está", sem garantia de nenhum tipo.

## Rodando

[Baixe o Katharos.zip da última versão](https://github.com/kessleru/Katharos/releases/latest/download/Katharos.zip) e extraia. Ele traz o **`Katharos.exe`**, que é onde você clica, e a pasta `programa`, que ele usa (o `KATHAROS.bat` continua lá e faz o mesmo). Na primeira vez, o Katharos oferece criar uma pasta **Katharos** na área de trabalho, com ícone. Deixe a pasta baixada onde está: é nela que ficam os relatórios (`relatorios/`).

O `Katharos.exe` (ou o `KATHAROS.bat`):

1. acha o Python que você já tem (Python Launcher, PATH, registro, pastas comuns e até o da Microsoft Store) e só instala o oficial pelo winget se não houver nenhum;
2. abre o Katharos como administrador no melhor terminal do PC: **Windows Terminal**, senão PowerShell 7, senão Windows PowerShell.

```bat
Katharos.exe                       :: menu
Katharos.exe raiox                 :: diagnóstico completo (só leitura)
Katharos.exe turbo                 :: tudo em sequência, com reinício e retomada
Katharos.exe privacidade --teste   :: mostra o que faria, sem alterar nada
```

O Windows pode avisar "aplicativo não reconhecido" na primeira vez: é o aviso de todo programa novo sem certificado pago. Clique em **Mais informações** e **Executar assim mesmo**. Para conferir que o zip saiu daqui: `gh attestation verify Katharos.zip --repo kessleru/Katharos`.

## Acompanhamento em segundo plano

`segundo-plano` (no menu: mais › acompanhamento) liga o **Katharos.exe perto do relógio**, com o ícone da marca. Ele lê o PC sem parar, no ritmo que você escolher (`config tempo-real`: 1, 2, 5 ou 10 s): CPU por núcleo e a frequência de verdade, placa de vídeo (uso e memória), RAM, disco, rede, temperatura e bateria.

- **Clique no ícone**: o painel ao vivo, com gráfico dos últimos 2 minutos de cada métrica, o que está no limite agora e o que a central de inteligência propõe. Botão direito: o que se resolve num clique (abrir o Katharos, pausar, ritmo da leitura, avisos, iniciar com o Windows, sair).
- **Jogos**: ele percebe quando há um jogo aberto (quem usa a placa de vídeo, na frente ou em tela cheia) e grava a sessão: quanto tempo, o que ficou no limite (placa de vídeo, CPU, CPU freando, RAM, memória de vídeo, disco, calor).
- **Central de inteligência** (`conselheiro`): aprende com as sessões e com as últimas 24 horas minuto a minuto. Exemplo: "a CPU segura seus jogos em 40 % do tempo" vira uma proposta com o comando que resolve.
- **Painel** (`painel`): seção "Ao vivo e jogos", com as últimas 24 horas e a tabela das sessões.
- **No terminal**: `aovivo`.
- **Custo**: uns 30 a 60 MB de RAM e menos de 1 % de CPU, em prioridade baixa. Roda como o seu usuário (nunca como administrador).
- **Anti-cheat**: lê o que o Gerenciador de Tarefas lê (contadores do Windows, nomes de processo, temperatura do driver de vídeo). Não abre o processo do jogo, não lê memória, não injeta nada. Um teste confere isso no código.

O código do executável está em `exe/Katharos.cs`. A publicação compila ele no próprio Windows, com o compilador que vem no sistema, e assina o zip. `Katharos.exe --diagnostico arquivo.json` grava tudo o que ele consegue ler neste PC (bom para relatar problema).

Ou direto, num PowerShell aberto como administrador: `python programa\katharos.py [comando] [opções]`.

## Modos

A abertura mostra o **próximo passo** para este PC (medir, aplicar o que o raio-x apontou, conferir o ganho, agendar) e o Enter segue; qualquer palavra que não seja comando vira busca (`ventoinha`, `como tirar a propaganda`). Não há perfis: você escolhe um **modo** e ele decide o que vem marcado, ou abre uma área (`limpar`, `jogos`...) e marca item por item. O menu de abertura tem seis linhas (`raiox`, `turbo`, `escolher`, `painel`, `desfazer`, `mais`): `escolher` mostra as áreas e `mais` as outras ferramentas, por assunto. Jogos não são uma escolha à parte: cada modo já traz o que ajuda FPS e atraso em qualquer jogo (o extremo vai mais longe), e você tira ou põe item por item. Em qualquer tela vale o número da linha ou o nome de um comando.

| Modo | O que marca |
| --- | --- |
| **seguro** | Só o que não tem contrapartida: telemetria, anúncios, lixo, apps de propaganda, tarefas inúteis. Para PC de trabalho ou de outra pessoa. |
| **equilibrado** | O seguro mais o que quase ninguém usa: serviços de empresa e telefone, Xbox (se não joga), IA do Windows, widgets, efeitos, caches. Recomendado. |
| **extremo** | Tudo o que pode ajudar neste PC: sensores, área de trabalho remota, scanner, localização, hibernação no SSD, ajustes de jogos e de rede. Cada item diz o que se perde. |
| *opcional* | Itens que nenhum modo marca: só entram se você marcar (esvaziar a Lixeira, trocar DNS, MPO, HAGS, remover o Office, preferências). |

Na tela de escolha os itens vêm em grupos que dizem o que são: **seguro** (não tira nada de você), **equilibrado** (tira o que quase ninguém usa), **extremo** (tira algum recurso) e **opcional** (só entra se você marcar). O modo marca o grupo dele e os de cima. Item com aviso ou sem volta diz isso ao lado do nome. A tela mostra só três teclas: Enter continua, um número marca ou desmarca (`3 5 8-10`) e `? 3` explica o item 3; `?` abre a ajuda com o resto (`t` todos, `n` nenhum, `s` `e` `x` remarca pelo modo, `c` explicação de todos, `v 3` o código do item, `0` volta). `config explicacao completa` volta a mostrar tudo sempre.

## Inteligente

Antes de mostrar qualquer item, ele olha o PC: HD ou SSD, RAM e slots, notebook ou desktop, tablet, fabricante, Windows 10 ou 11, impressora, scanner, leitor de cartão, biometria, Bluetooth, área de trabalho remota, WinRM, SSH, WSL, Hyper-V, Docker, jogos instalados (Steam, Epic, Riot, Xbox...), central do fabricante (AWCC, Armoury Crate, Vantage...), OneDrive em uso, Office, antivírus ativos e domínio de empresa. Daí:

- não oferece desligar o que o PC usa (Spooler com impressora, SharedAccess com WSL, cartão inteligente com leitor...);
- muda a recomendação (Xbox não vem marcado em quem joga; plano "fresco" em notebook, "desempenho" em desktop; indexação só em HD);
- dobra os limites de tempo em HD e aumenta em pouca RAM;
- com o Python da Microsoft Store, roda o PowerShell **fora do contêiner** dela pelo WMI (senão o registro do usuário seria gravado numa cópia virtual), e avisa quando o administrador é outra conta.

O `raiox` não só lista: ele mede e explica. Além de CPU, RAM e disco, olha a memória comprometida (falta de RAM de verdade, não só "em uso"), o disco ocupado com o PC parado e quem está lendo e gravando, as interrupções e DPC (o driver que picota o áudio e engasga o jogo), a velocidade real dos pentes de memória (XMP desligado), a taxa de atualização do monitor contra a que ele aceita, a idade do driver de vídeo e o TRIM do SSD. Cada processo que aparece gastando vem com o que ele é e o que fazer (mais de 900 conhecidos, e pelo começo ou fim do nome ele ainda reconhece de quem é ou o que faz). A nota diz quais achados mais pesaram, e o que é só informação não tira ponto.

## Comandos

| Grupo | Comando | O que faz |
| --- | --- | --- |
| Conhecer | `raiox` | Pergunta o que mais incomoda, mede tudo e mostra nota, causas das suas queixas e o que mais encontrou (HD, RAM, inicialização, dois antivírus, WMI ocupado, CPU limitada, temperatura, quem troca o plano de energia, bateria, SMART, telas azuis, tarefas suspeitas em AppData/Temp, ameaças do Defender, restos de programas, projetos dentro do OneDrive, BIOS com atualização falhando...). Gera um `.md` para a ficha do PC; `--salvar PASTA`. |
| | `medir` | CPU, kernel, clock, RAM, processos, serviços, inicialização, espaço, temperatura e boot, comparados com a primeira medida |
| | `benchmark` | Disco (escrita sequencial e escritas pequenas com flush), CPU e RAM, com repetição. Descarta a primeira rodada e só diz "melhorou" ou "piorou" quando a diferença é maior que a variação das medidas; compara com o resultado anterior. `--completo` faz mais rodadas |
| | `memoria` | Como a RAM está dividida (em uso, em espera, livre), quem mais usa e, se quiser, esvazia a memória em espera (explicando por que quase sempre é placebo) |
| Tudo | `turbo` | Modo → etapas → (opcional) item por item → ponto de restauração → mede → aplica → reinicia → continua sozinho → mede de novo. Salva o plano em JSON: `turbo --plano arquivo.json` repete as mesmas escolhas em outro PC sem perguntar |
| Partes | `limpar` | Temporários, Windows Update, Otimização de Entrega, relatórios de erro e dumps, miniaturas, logs, navegadores fechados, shaders, instaladores guardados, caches de dev, Limpeza de Disco do Windows, Windows.old, componentes (DISM), armazenamento reservado, Lixeira |
| | `programas` | Bloatware de Dell, HP, Lenovo, Acer, ASUS, McAfee, Norton, CyberLink, OneDrive, Teams antigo: tenta em silêncio e, se não sair, abre o desinstalador |
| | `apps` | Apps da Loja conhecidos (com explicação) e qualquer outro removível ("risco desconhecido", opcional) |
| | `ia` | Copilot, Recall, Clique para Fazer, IA no Paint, Bloco de Notas, Edge e Office, coleta de digitação, serviço e tarefas de IA, só por políticas oficiais |
| | `inicializacao` | Registro, pasta Inicializar, apps da Loja e tarefas de logon, pelo mesmo mecanismo do Gerenciador de Tarefas. Antivírus nunca sai; anti-cheat, touchpad e caneta são opcionais |
| | `servicos` | Desativa (nunca apaga) serviços sem uso, de fabricante (SupportAssist, Killer, Nahimic...), atualizadores em manual, restos de programas desinstalados |
| | `privacidade` | Telemetria do Windows, Office, VS e Firefox, autologgers, anúncios, sugestões, busca na web, widgets, segundo plano, relatório de erros, localização, SMBv1, execução automática de pendrive |
| | `visual` | Efeitos, animações, transparência, barra enxuta, extensões visíveis, menu clássico, desligar mais rápido, atalhos sem busca demorada |
| | `jogos` | Vale para qualquer jogo: Modo de Jogo, Game DVR, MMCSS, primeiro plano, teclado e mouse, Teclas de Aderência, GPU NVIDIA/AMD, tela inteira, temporizador, Nagle, MPO, HAGS (cada um com a verdade sobre o ganho) |
| | `energia` | Plano "desempenho" ou "fresco" (notebook que esquenta: CPU mínima 5%, turbo eficiente, ASPM em todos os planos), disco, USB, PCIe, throttling, placa de rede, inicialização rápida em HD, hibernação em SSD |
| | `disco` | Defender mais leve, sem P2P do Update, tarefas inúteis, NTFS, Sensor de Armazenamento, SysMain em HD, início atrasado de terceiros, boot no HD, otimizar unidade (TRIM ou desfragmentar), memória virtual e compressão |
| | `reparar` | DISM, SFC, chkdsk, WMI, DNS; e, opcionais: rede, Windows Update, Loja, ícones, menu Iniciar |
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
| Atalhos | `atalhos` | Cria a pasta **Katharos** na área de trabalho, com o ícone e os atalhos que você escolher (menu, raio-x, otimizar, painel, voltar ao normal...); `--remover` tira |
| | `exportar` · `importar` | Salva o que está aplicado neste PC e repete em outro; antes de aplicar, `p` deixa tirar, pôr ou juntar itens |
| | `organizar` | Separa os arquivos soltos da área de trabalho em pastas por tipo (prévia, confirmação e `--desfazer`). Pastas, atalhos, ocultos e o que você mexeu hoje ficam |
| Resultado | `cartao` · `relatorio` | O antes e depois num cartão · o **relatório único** (copiar para a IA, salvar numa pasta ou apagar) |
| Manutenção | `agendar` | Segundo plano (semanal, diária ou contínua: ao iniciar com o Windows e a cada 4 h): tarefa do Windows, sem programa aberto; só ocioso e na tomada, prioridade baixa, limpa, reaplica o que atualizações desfazem, Defender, SMART, avisos por notificação; uma vez por mês, ponto de restauração e limpeza de componentes |
| | `restaurar` | Pontos de restauração: lista, cria, abre a Restauração do Sistema |
| | `desfazer` | `desfazer servicos privacidade` ou `desfazer tudo`: volta cada valor ao que era antes |
| | `socorro` | O PC ficou estranho: desfaz tudo o que o Katharos mudou e explica o ponto de restauração do Windows |
| Conhecer | `tendencia` | Mostra se espaço, boot, RAM, CPU ou temperatura estão piorando com o tempo (usa as medidas do segundo plano) |
| | `conselheiro` | O motor de inteligência: propõe mudanças com o número que as justifica, a confiança e o comando; não aplica nada sozinho e mede o resultado depois |
| | `saude` | Lê os erros do Windows (Visualizador de Eventos, 14 dias), confere drivers e o estado do sistema e explica cada problema e o que fazer; só leitura |
| | `painel` | Gera um painel HTML com gráficos das medidas, dos benchmarks, das datas de cada pacote e da saúde do Windows; sem internet e sem scripts. `--ativar-cliques` liga botões "Corrigir" que abrem o Katharos já no comando (você confirma lá) |
| | `amostrar` | Uma leitura leve do sistema (CPU, RAM, disco, temperatura), somada ao histórico por hora; a tarefa de 15 min do modo contínuo chama. `config coleta-em-jogo pausar` para não coletar com jogo aberto |
| | `retomar` | Se o PC travou ou a janela fechou no meio de uma aplicação, termina só o que faltou (`--descartar` esquece a anotação) |
| | `provas` | O que cada item rendeu de verdade neste PC: na hora (disco, RAM, processos e serviços, item por item) e depois de reiniciar (boot, CPU e RAM em repouso, por rodada). O painel mostra o mesmo com barras |
| | `versoes` | As versões que já rodaram neste PC, o que está guardado e as cópias feitas a cada troca. Para atualizar, basta abrir a versão nova: os dados ficam em `~/.katharos` e são reconhecidos e convertidos sozinhos |
| | `buscar` | Acha um item ou comando pelo que você digitar (`buscar telemetria`, `buscar ventoinha`): sem acento, com palavras do dia a dia e erro de digitação; abre a área só com o item achado marcado |
| | `estado` · `config` | O que já foi aplicado · modo padrão, explicações, cores, símbolos, tamanho mínimo do `grandes`, navegador do turbo |

## Opções

| Opção | Efeito |
| --- | --- |
| `--teste` | Mostra exatamente o que mudaria (cada valor), sem alterar nada |
| `--sim` | Não pergunta: aplica o que o modo marca |
| `--modo seguro\|equilibrado\|extremo` | Modo desta execução |
| `--copiar` · `--salvar PASTA` | No fim de qualquer comando: copia o relatório único para a área de transferência · salva uma cópia dele numa pasta (ex.: o cofre) |
| `--abrir` | No fim de qualquer comando: abre a pasta com o relatório único selecionado (sem precisar procurar). `config abrir-relatorio sempre` faz isso sozinho |
| `--codigo` | Mostra o PowerShell de cada item escolhido e não aplica nada (na tela de escolha, `v 3` mostra o do item 3) |
| `--ascii` · `--sem-cor` | Para terminais que mostram quadradinhos · sem cores (`NO_COLOR` também vale) |

## Versões e contribuição

O número é MAIOR.MENOR.CORREÇÃO, explicado no [CHANGELOG.md](CHANGELOG.md); cada versão tem uma tag (`v1.2.0`) e `katharos --versao` mostra a sua. Para ajudar, veja o [CONTRIBUTING.md](CONTRIBUTING.md): rodar os testes (`python -m unittest discover -s tests`), propor um item e contar um problema.

## Segurança

- **Tudo volta.** Antes de mudar qualquer coisa, cada pacote guarda o valor anterior (registro com tipo, tipo de início de serviço, estado de tarefa, plano e índices de energia, atalhos, DNS). `desfazer` volta exatamente. Programas e apps removidos são o único que não volta (está escrito no item).
- Ponto de restauração "Antes do Katharos" (no máximo um por dia; liga a Proteção do Sistema se estiver desligada).
- Cada etapa roda num PowerShell filho com **limite de tempo** (dobrado em HD); se travar (o `Remove-AppxPackage` às vezes nunca volta), é encerrada e o resto segue. O turbo **retoma** depois de reiniciar, nunca roda duas vezes ao mesmo tempo e espera o carregador com bateria abaixo de 40%.
- Clicar na janela não pausa (modo de edição rápida desligado).
- Nada de lançador `.vbs` escondido, nada de exceção no antivírus: as tarefas agendadas chamam o PowerShell numa janela normal, minimizada.
- **Não faz, de propósito:** desligar Defender, firewall, UAC, SmartScreen, VBS/Integridade de Memória, Windows Update, BitLocker, Proteção do Sistema ou checagem de TPM; desligar a memória virtual; mexer na BIOS ou em partições; limpar registro; "liberar RAM" milagroso; desligar SysMain/Prefetch em HD. Quando algo exige isso (atualizar a BIOS com BitLocker), ele diz o comando e você executa.

- **"Manter alterações?"** Depois de mudar serviços, jogos, energia, disco ou visual, o Katharos pergunta se está tudo bem (como a troca de resolução do Windows). Sem resposta em 90 s, desfaz sozinho: se a tela ficar preta, não precisa fazer nada. `config confirmar nunca` desliga.
- **Conferência.** Depois de aplicar, ele refaz a conta em modo teste e diz se algum ajuste não ficou. `verificar` faz o mesmo mais tarde, depois de uma atualização grande do Windows.
- **PC de empresa ou escola** (domínio, Azure AD ou gestão remota com conta de trabalho) é detectado, e o aviso diz qual dos três: o modo da tela cai para "seguro" e ele avisa que a organização pode desfazer as mudanças.
- **Itens protegidos.** `config protegidos rdp,servicos:xbox` e o Katharos nunca mexe neles (nem no turbo, nem na manutenção).
- **Código à vista.** `--codigo` e `v N` mostram o PowerShell exato antes de aplicar. Itens de jogo que podem conflitar com anti-cheat têm um aviso em amarelo.
- **Relatório único.** Em vez de um arquivo por ferramenta, tudo vai para `relatorios/ultimo.md` (o relatório atual; os dados em JSON ficam em `.katharos`): PC, raio-x, segurança, o que foi aplicado, avisos e erros com dica, e o que o Katharos não reconheceu. É feito para mandar a uma IA melhorar a base de dados. Tudo que vem do PC (nomes de programa, de arquivo, mensagens) é limpo antes de entrar (sem controle, sem Markdown, sem frases que pareçam ordens) e o arquivo avisa que é dado, não instrução. Cada execução também grava uma cópia com data e hora na mesma pasta `relatorios/`, ao lado do `KATHAROS.bat` (`AAAA-MM-DD_HH-MM-SS_pc_comando.md`; ficam as 60 mais recentes). Pelos atalhos da área de trabalho a pasta é a mesma (o programa lembra onde ela está). Só se você apagar ou mover a pasta, ou ela não aceitar escrita, os relatórios vão para `~/.katharos/relatorios`. Confira antes de compartilhar: tem o nome do PC, os programas instalados e caminhos de pastas.
- **Jogos sem risco de ban.** Só ajustes do Windows que valem para qualquer jogo. Nada toca em arquivo ou memória de jogo, e nada roda junto com ele.
- **Arquivo importado nunca é executado.** `importar` só escolhe, entre os itens que o Katharos já conhece, quais aplicar, depois da prévia e da confirmação.
- **Verifique o download, de fora do programa.** `gh attestation verify katharos.py --repo kessleru/Katharos` confere a assinatura que o GitHub põe em cada release, e `Get-FileHash .\katharos.py -Algorithm SHA256` deve bater com a página da release. Dentro do programa, `katharos autenticidade` faz a conferência local e online, e a abertura avisa sozinha se o arquivo não bate com o `SHA256SUMS.txt` que veio junto; mas um arquivo alterado pode esconder isso, por isso valem as de fora. Veja o [SECURITY.md](SECURITY.md).

Relatório, medidas, logs e preferências ficam em `%USERPROFILE%\.katharos`. O que roda como administrador fica em `%ProgramData%\Katharos`, onde só administradores gravam: o backup do `desfazer`, os scripts temporários do PowerShell e a cópia do programa que as tarefas do Windows executam.

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
Katharos.exe               abre o Katharos e roda o segundo plano (código em exe\Katharos.cs)
KATHAROS.bat               o mesmo que o Katharos.exe sem argumentos: chama o programa\katharos.ps1
programa\katharos.ps1      acha o Python, escolhe o terminal e abre como administrador
docs/             o site (GitHub Pages)
tests/            testes automáticos (rodam também no GitHub Actions)
CHANGELOG.md      o que mudou em cada versão
CONTRIBUTING.md   como ajudar
relatorios\       criada no primeiro uso: um relatório por execução, com data e hora
```
