# Katharos

*καθαρός*, em grego: limpo, purificado.

**Deixa qualquer Windows mais leve, num arquivo só.** Diagnóstico com nota, limpeza, programas e apps de fábrica, inicialização, serviços, privacidade, IA do Windows, visual, jogos, energia, disco, reparo, atualizações, rede, manutenção automática e reversão de tudo.

Mesmo visual e mesma ideia do [Ferramentas](https://github.com/kessleru/Ferramentas): Python 3.8+, **zero dependências**, terminal kterm 2.0.0 embutido. Por baixo, só ferramentas nativas do Windows: PowerShell, DISM, sfc, chkdsk, defrag, powercfg, winget.

Site: **[kessleru.github.io/Katharos](https://kessleru.github.io/Katharos)**

## Rodando

[Baixe o ZIP](https://github.com/kessleru/Katharos/archive/refs/heads/main.zip), extraia e clique duas vezes no **`KATHAROS.bat`**. Ele pede administrador e, se o PC não tiver Python, instala o oficial pelo winget.

```bat
KATHAROS.bat                       :: menu
KATHAROS.bat raiox                 :: diagnóstico completo (só leitura)
KATHAROS.bat turbo                 :: tudo em sequência, com reinício e retomada
KATHAROS.bat privacidade --teste   :: mostra o que faria, sem alterar nada
```

Ou direto: `python katharos.py [comando] [opções]` num terminal aberto como administrador.

## Modos

Os modos só decidem **o que vem marcado**. Em toda tela você vê cada item explicado (o que faz, ganho, custo e o modo a partir do qual ele vem marcado) e marca ou desmarca o que quiser.

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
| | `jogos` | Modo de Jogo, Game DVR, prioridade alta para mais de 60 jogos, MMCSS, primeiro plano, teclado e mouse, Teclas de Aderência, GPU NVIDIA/AMD, tela inteira, temporizador, Nagle, MPO, HAGS (cada um com a verdade sobre o ganho) |
| | `energia` | Plano "desempenho" ou "fresco" (notebook que esquenta: CPU mínima 5%, turbo eficiente, ASPM em todos os planos), disco, USB, PCIe, throttling, placa de rede, inicialização rápida em HD, hibernação em SSD |
| | `disco` | Defender mais leve, sem P2P do Update, tarefas inúteis, NTFS, Sensor de Armazenamento, SysMain em HD, início atrasado de terceiros, boot no HD, otimizar unidade (TRIM ou desfragmentar), memória virtual e compressão |
| | `reparar` | DISM, SFC, chkdsk, WMI, DNS; e, só se marcar: rede, Windows Update, Loja, ícones, menu Iniciar |
| | `atualizar` | Defender, Windows Update, drivers, winget, apps da Loja |
| | `navegador` | Brave, Chrome e Edge enxutos (sem segundo plano, sem métricas, economia de memória) |
| | `rede` | Mede o ping (roteador e DNS públicos) e troca o DNS (Cloudflare, Google, Quad9, AdGuard) |
| | `ajustes` | Preferências: Finalizar tarefa na barra, caminhos longos, barra à esquerda, segundos, tema escuro, ocultos, Num Lock... |
| | `interface` | Atalhos do Edge, Windows Destaque, Este Computador, área de trabalho só com a Lixeira |
| | `grandes` | Arquivos grandes, duplicados (por hash) e instaladores velhos. Vão para a **Lixeira** (nunca de vez); arquivos do OneDrive só aparecem |
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
| `--ascii` · `--sem-cor` | Para terminais que mostram quadradinhos · sem cores (`NO_COLOR` também vale) |

## Segurança

- **Tudo volta.** Antes de mudar qualquer coisa, cada pacote guarda o valor anterior (registro com tipo, tipo de início de serviço, estado de tarefa, plano e índices de energia, atalhos, DNS). `desfazer` volta exatamente. Programas e apps removidos são o único que não volta (está escrito no item).
- Ponto de restauração "Antes do Katharos" (no máximo um por dia; liga a Proteção do Sistema se estiver desligada).
- Cada etapa roda num PowerShell filho com **limite de tempo** (dobrado em HD); se travar (o `Remove-AppxPackage` às vezes nunca volta), é encerrada e o resto segue. O turbo **retoma** depois de reiniciar, nunca roda duas vezes ao mesmo tempo e espera o carregador com bateria abaixo de 40%.
- Clicar na janela não pausa (modo de edição rápida desligado).
- Nada de lançador `.vbs` escondido, nada de exceção no antivírus: as tarefas agendadas chamam o PowerShell numa janela normal, minimizada.
- **Não faz, de propósito:** desligar Defender, firewall, UAC, SmartScreen, VBS/Integridade de Memória, Windows Update, BitLocker, Proteção do Sistema ou checagem de TPM; desligar a memória virtual; mexer na BIOS ou em partições; limpar registro; "liberar RAM" milagroso; desligar SysMain/Prefetch em HD. Quando algo exige isso (atualizar a BIOS com BitLocker), ele diz o comando e você executa.

Relatórios, medidas, backups, logs e preferências ficam em `%USERPROFILE%\.katharos`.

## De onde veio

- Os scripts e as lições de otimizar um Dell Inspiron 5458 de verdade.
- O prompt de otimização de notebook gamer (estratégias de diagnóstico, IA do Windows, fabricante, MSIX, PowerShell 5.1).
- [optimizerDuck](https://github.com/itsfatduck/optimizerDuck) e [Optimizer](https://github.com/hellzerg/optimizer): ajustes comparados um a um; ficaram os documentados e reversíveis.
- O guia de opções de um otimizador de jogos (energia, Game Bar, prioridades, rede, RAM), com o ganho real de cada um.

## Estrutura

```
katharos.py
  NÚCLEO          kterm (terminal Kessleru) · preferências · PowerShell vigiado · backup e desfazer
  PARTE 1         perfil do PC · medidas · raio-x e regras do diagnóstico
  PARTE 2         itens, tela de escolha e execução
  PARTE 3         os pacotes (limpar … interface, rede, ajustes)
  PARTE 4         turbo, manutenção, restaurar, desfazer, estado, grandes, memória
  PARTE 5         menu e linha de comando
KATHAROS.bat      pede administrador, acha ou instala o Python e abre o menu
docs/             o site (GitHub Pages)
```
