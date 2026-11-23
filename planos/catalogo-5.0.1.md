# Catálogo do Katharos 5.0.1

Gerado do código por `scripts/catalogo.py` (PC modelo: Windows 11, com jogos). "Vem marcado a partir de" é o primeiro modo que marca o item; "só se marcar" nunca vem marcado. **Volta** = o Desfazer devolve o valor de antes.

167 itens em 17 áreas. Regras (plano 5.0.0, seção 3.4): item sem volta nunca vem marcado (teste `test_nenhum_item_sem_volta_vem_marcado`); limpeza, reparo e atualização são manutenção e não vêm marcados na janela.

## limpar (manutenção: não vem marcada na janela)

| Item | Vem marcado a partir de | Volta | Ganha | Perde |
|---|---|---|---|---|
| temporários | - | sim | espaço; às vezes centenas de MB | nenhum |
| downloads do Windows Update | - | sim | espaço (pode passar de 1 GB) | nenhum |
| cache da Otimização de Entrega | - | sim | espaço | nenhum |
| relatórios de erro e dumps | - | sim | espaço (dumps podem ter GBs) | quem investiga uma tela azul antiga perde o arquivo |
| cache de miniaturas | - | sim | espaço; conserta miniaturas erradas | pastas de fotos demoram um pouco na primeira abertura |
| logs antigos do Windows | - | sim | espaço | nenhum no uso normal |
| cache dos navegadores | - | sim | espaço (às vezes vários GB) | os sites carregam um pouco mais devagar na primeira visita |
| cache de shaders da placa de vídeo | - | sim | espaço de jogos que você não abre mais | um jogo antigo recompila na primeira vez que abrir |
| instaladores guardados por programas | - | sim | espaço | reparar esses programas pode pedir o instalador de novo |
| caches de desenvolvimento | - | sim | espaço | a próxima instalação de pacotes baixa de novo |
| Limpeza de Disco do Windows | - | sim | espaço (costuma liberar GBs depois de grandes atualizações) | demora (até 30 min em HD) |
| Windows.old (versão anterior do Windows) | - | sim | espaço (10 a 30 GB) | não dá mais para voltar à versão anterior |
| componentes antigos do Windows (DISM) | - | sim | espaço (centenas de MB a alguns GB) | demora |
| componentes, de forma definitiva | - | **não** | mais espaço | não dá mais para desinstalar atualizações já instaladas |
| armazenamento reservado do Windows | - | sim | cerca de 7 GB | com o disco cheio, atualizações grandes podem falhar |
| esvaziar a Lixeira | - | **não** | espaço | é definitivo: não dá para recuperar |

## ia

| Item | Vem marcado a partir de | Volta | Ganha | Perde |
|---|---|---|---|---|
| Copilot desligado | seguro | sim | menos um app em segundo plano | perde o Copilot do Windows |
| remover o app Copilot | só se marcar | **não** | menos espaço e processos | perde o app (volta só reinstalando pela Loja) |
| Recall e análise de IA desligados | seguro | sim | privacidade; menos processamento em segundo plano | perde esses recursos de IA |
| recurso opcional Recall desativado | equilibrado | sim | tira o componente do sistema | nenhum para quem não usa |
| IA no Paint | equilibrado | sim | menos chamadas à nuvem | perde esses recursos do Paint |
| IA no Bloco de Notas | equilibrado | sim | Bloco de Notas mais simples | perde a reescrita com IA |
| IA no Edge | equilibrado | sim | Edge mais leve e privado | perde o Copilot no Edge; aparece o aviso de gerenciado |
| Microsoft 365 Copilot e IA do Office | equilibrado | sim | menos processos do Office em segundo plano | perde o Copilot do Office |
| coleta de digitação e tinta | equilibrado | sim | privacidade | sugestões de digitação ficam menos personalizadas |
| serviço e tarefas de IA | extremo | sim | menos processos parados gastando | nenhum para quem não usa IA do Windows |

## servicos

| Item | Vem marcado a partir de | Volta | Ganha | Perde |
|---|---|---|---|---|
| mapas, demonstração, mídia e Insider | seguro | sim | menos serviços rodando | nenhum |
| fax | seguro | sim | um serviço a menos | não envia fax pelo PC |
| impressão | equilibrado | sim | menos dois serviços | não imprime, nem "Imprimir em PDF" |
| Xbox | só se marcar | sim | menos quatro serviços | perde Game Pass, login Xbox em jogos e controle Xbox sem fio pelo adaptador |
| indexação da busca (Windows Search) | extremo | sim | menos leitura de disco em segundo plano | a busca por arquivos no menu e no Explorador fica bem mais lenta |
| recursos de empresa | equilibrado | sim | menos serviços | nenhum em PC doméstico |
| telefonia | equilibrado | sim | menos serviços | modem e discador antigos param |
| hotspot móvel | equilibrado | sim | menos serviços | não cria hotspot pelo PC |
| controle dos pais | equilibrado | sim | um serviço a menos | controle dos pais da conta Microsoft para |
| atualizadores em manual | equilibrado | sim | menos serviços parados gastando RAM | atualizações desses programas podem chegar um pouco depois |
| serviços e tarefas de fabricante | equilibrado | sim | menos CPU e WMI parados | diagnóstico do fabricante só quando você abrir |
| Nahimic e efeitos de áudio do fabricante | extremo | sim | menos CPU | os efeitos do Nahimic (surround virtual) param; o som continua normal |
| restos de programas desinstalados | equilibrado | sim | menos erros no boot e no registro de eventos | nenhum |
| serviços que podem subir só quando precisar | extremo | sim | menos serviços rodando desde o boot | aparelhos de rede (TVs, impressoras na rede) podem demorar a aparecer |
| agrupar serviços em menos processos | extremo | sim | dezenas de processos a menos no Gerenciador de Tarefas | ganho de RAM pequeno e não comprovado; se um serviço travar, leva os vizinhos junto |
| área de trabalho remota | extremo | sim | menos serviços e menos portas abertas | ninguém acessa este PC pela Área de Trabalho Remota |
| gerenciamento remoto (WinRM) | extremo | sim | um serviço a menos | scripts remotos e alguns sistemas de empresa param |
| agente SSH | extremo | sim | um serviço a menos | quem usa chave SSH com senha digita de novo |
| cartão inteligente | extremo | sim | menos três serviços | certificado digital em cartão ou token (e-CPF, e-CNPJ) para de funcionar |
| sensores e localização | extremo | sim | menos serviços | rotação automática de tela, brilho automático, fuso horário automático e "Encontrar meu dispositivo" param |
| scanner | extremo | sim | um serviço a menos | scanner para de funcionar |
| biometria | extremo | sim | um serviço a menos | Windows Hello com rosto e digital para |
| assistente de compatibilidade e rastreio de links | extremo | sim | menos dois serviços | programas muito antigos deixam de receber ajustes automáticos |

## privacidade

| Item | Vem marcado a partir de | Volta | Ganha | Perde |
|---|---|---|---|---|
| telemetria no mínimo | seguro | sim | menos uso de rede e disco | nenhum |
| serviços de telemetria | seguro | sim | menos um serviço que grava e envia o tempo todo | nenhum |
| registros contínuos de diagnóstico | extremo | sim | menos escrita contínua em disco | diagnósticos avançados da Microsoft ficam com menos dados |
| tarefas de telemetria | seguro | sim | menos picos de disco e CPU | nenhum |
| anúncios e apps instalados sozinhos | seguro | sim | menos propaganda e instalações surpresa | nenhum |
| histórico de atividades | seguro | sim | menos escrita em disco | a Linha do Tempo antiga fica vazia |
| Cortana | seguro | sim | nenhum processo da Cortana | nenhum (foi descontinuada) |
| propaganda do Microsoft 365 nas Configurações | seguro | sim | menos propaganda | nenhum |
| telemetria do Office | equilibrado | sim | menos processos e uploads do Office | nenhum |
| área de transferência na nuvem | extremo | sim | privacidade | perde o colar entre aparelhos |
| "Encontrar meu dispositivo" | extremo | sim | privacidade | não dá para localizar o PC perdido pela conta |
| portas de entrada antigas fechadas | seguro | sim | mais segurança | aparelhos de rede muito antigos (antes de 2010) podem não abrir pastas |
| programa do fabricante gravado no firmware | equilibrado | sim | nenhum programa entra pelo firmware sem você saber | o app da marca não se reinstala sozinho (instale pelo site dela se quiser) |
| apps de fabricante instalados sozinhos | seguro | sim | nada instala sem você pedir | o programa da marca, se você quiser, se instala pelo site dela |
| apps da Loja sem acesso a contatos, agenda, e-mail e chamadas | equilibrado | sim | apps da Loja não leem seus dados pessoais | um app da Loja que precise disso (Outlook novo, Teams) pede de novo ou para de ver |
| busca do menu sem resultados da web | equilibrado | sim | busca mais rápida e privada | pesquisas na web vão para o navegador |
| widgets e notícias | equilibrado | sim | menos um processo do Edge em segundo plano | perde o painel de widgets |
| apps da Loja em segundo plano | equilibrado | sim | pouco de RAM e CPU | apps da Loja fechados (WhatsApp, Teams novo) podem não notificar |
| bloquear segundo plano para todos | extremo | sim | mais RAM e CPU livres | nenhum app da Loja notifica fechado |
| relatório de erros | equilibrado | sim | menos disco depois de travamentos | a Microsoft não recebe seus relatórios; soluções automáticas não aparecem |
| localização | extremo | sim | privacidade | fuso automático, mapas, clima local e "Encontrar meu dispositivo" param |
| Edge sem rodar escondido | seguro | sim | menos RAM no boot | o Edge demora um pouco mais para abrir |

## visual

| Item | Vem marcado a partir de | Volta | Ganha | Perde |
|---|---|---|---|---|
| monitor na taxa máxima (144 Hz) | equilibrado | sim | imagem mais fluida e menos atraso em tudo, principalmente em jogos | em notebook na bateria, um pouco mais de consumo |
| efeitos visuais em desempenho | equilibrado | sim | janelas e menus mais rápidos em PC fraco | visual mais seco |
| animações | equilibrado | sim | resposta imediata | nenhum |
| menus sem espera | seguro | sim | sensação de rapidez | nenhum |
| transparência | só se marcar | sim | menos uso da placa de vídeo; só se nota em placa integrada ou com pouca RAM | visual mais opaco |
| arrastar janela sem conteúdo | extremo | sim | menos trabalho de vídeo em PC fraco | visual estranho para quem não está acostumado |
| ícones no lugar de miniaturas | extremo | sim | pastas de mídia abrem mais rápido em HD | não vê a prévia das fotos |
| papel de parede liso | extremo | sim | um pouco de RAM | perde o papel de parede |
| barra de tarefas enxuta | equilibrado | sim | barra limpa | esses botões somem; a busca abre pela tecla Windows (é só digitar) e o Win+Tab continua |
| mostrar extensões dos arquivos | seguro | sim | segurança | nomes um pouco mais longos |
| Explorador abre em "Este Computador" | equilibrado | sim | privacidade e menos leitura | nenhum |
| menu do botão direito completo | equilibrado | sim | menos cliques | visual do Windows 10 no menu |
| programas da inicialização sem espera | equilibrado | sim | área de trabalho pronta mais cedo | em HD, o começo fica mais disputado |
| desligar e fechar travados mais rápido | equilibrado | sim | desliga e reinicia mais rápido | programa que demora para salvar ao fechar pode perder o que não foi salvo |
| atalhos quebrados sem busca demorada | extremo | sim | sem travadas de vários segundos | atalho de arquivo movido não se conserta sozinho |
| cópia de memória pequena em tela azul | equilibrado | sim | GBs de disco e reinício mais rápido depois de travar | investigação profunda de telas azuis fica mais difícil |
| sem minimizar tudo ao sacudir a janela | equilibrado | sim | sem minimizar sem querer | nenhum |
| menu Iniciar sem "Recomendados" | extremo | sim | menu limpo e privado | perde os arquivos recentes no menu |
| menu Iniciar com mais fixados | equilibrado | sim | menu mais útil | nenhum |

## jogos

| Item | Vem marcado a partir de | Volta | Ganha | Perde |
|---|---|---|---|---|
| Modo de Jogo ligado | seguro | sim | pequeno: segura atualizações e avisos durante o jogo | nenhum |
| Game DVR e captura em segundo plano | equilibrado | sim | pequeno em PC forte; mais perceptível em PC fraco | Win+Alt+G e gravação pela Game Bar param |
| jogos em janela e VRR otimizados | seguro | sim | menos atraso e mais FPS em jogo em janela ou sem borda (DirectX 10 e 11; o DirectX 12 já funciona assim) | nenhum conhecido; se um jogo reclamar, desligue só para ele em Configurações > Sistema > Tela > Gráficos |
| agendador multimídia: menos CPU reservada ao fundo | extremo | sim | pequeno e raramente medido; só em jogo que usa o agendador multimídia | tarefas de fundo ficam com menos CPU enquanto joga |
| prioridade do primeiro plano explícita | só se marcar | sim | provavelmente nenhum, se o valor nunca foi mexido | nenhum |
| sem aceleração do mouse | equilibrado | sim | mira mais consistente | em telas grandes o mouse parece mais lento até se acostumar |
| teclado mais rápido | extremo | sim | movimentos e digitação respondem antes | quem digita devagar pode repetir letras sem querer |
| sem atalho das Teclas de Aderência | equilibrado | sim | sem janela surgindo no jogo | quem usa esses atalhos de acessibilidade perde |
| sem otimizações de tela inteira | só se marcar | sim | só em alguns jogos antigos com engasgo ou atraso | no Windows 11 pode piorar: o modo moderno costuma ser melhor |
| resolução do temporizador global | extremo | sim | só com um programa que pede o temporizador fino | o PC inteiro acorda mais vezes: mais consumo e mais trabalho com programas parados |
| rede: sem atraso de pacotes (Nagle) | extremo | sim | quase sempre zero ou mínimo (a maioria dos jogos usa UDP) | um pouco mais de pacotes na rede |
| desligar o Multiplane Overlay (MPO) | só se marcar | sim | só resolve se você tem esse problema | sem o problema, não muda nada (ou piora um pouco) |
| agendamento de GPU acelerado por hardware | extremo | sim | pequeno; necessário para o DLSS 3 (geração de quadros) | o ganho é pequeno e varia; em placa antiga ou com 8 GB de memória de vídeo pode engasgar, e alguns jogos (VRChat, CS:GO) ficam piores. Já vem ligado no Windows 11; só liga se o Windows mostrar suporte |

## energia

| Item | Vem marcado a partir de | Volta | Ganha | Perde |
|---|---|---|---|---|
| plano desempenho máximo | extremo | sim | mais rápido para responder e em jogos | mais calor e consumo; em notebook, a bateria dura menos |
| plano fresco (notebook que esquenta) | seguro | sim | mais frio, silencioso e mais bateria | picos de desempenho um pouco menores |
| disco nunca desliga na tomada | equilibrado | sim | sem espera para o HD acordar | gasto mínimo de energia |
| sem suspensão seletiva de USB na tomada | extremo | sim | evita mouse, teclado e headset desconectando ou com atraso | gasto mínimo de energia |
| clock sempre no máximo na tomada | só se marcar | sim | zero atraso para subir o clock | mais calor e consumo o tempo todo |
| PCIe sem economia na tomada | só se marcar | sim | pequeno; evita atrasos ao acordar dispositivos | mais consumo |
| sem limitação de energia dos processos | só se marcar | sim | programas de fundo mais rápidos | mais consumo; em notebook, menos bateria |
| placa de rede sem economia de energia | só se marcar | sim | evita quedas de Wi-Fi e atraso ao voltar da suspensão | mais consumo |
| inicialização rápida desligada | só se marcar | sim | "Desligar" passa a zerar o Windows (como Reiniciar) | o PC liga alguns segundos mais devagar |

## disco

| Item | Vem marcado a partir de | Volta | Ganha | Perde |
|---|---|---|---|---|
| varreduras do Defender mais leves | equilibrado | sim | o PC não trava durante a varredura semanal | a varredura completa demora mais |
| Windows Update sem compartilhar com outros PCs | seguro | sim | menos upload e escrita em disco | nenhum |
| tarefas de manutenção inúteis | equilibrado | sim | menos leitura de disco ociosa | nenhum |
| NTFS sem gravar "último acesso" | equilibrado | sim | menos escrita em disco | programas de backup que dependem dessa data (raros) se confundem |
| NTFS sem nomes 8.3 e com mais cache | extremo | sim | pastas grandes mais rápidas | programas de DOS muito antigos podem não achar arquivos novos |
| TRIM ligado no SSD | seguro | sim | o SSD continua rápido para gravar e dura mais | nenhum |
| Sensor de Armazenamento mensal | seguro | sim | disco não enche sozinho | nenhum |
| serviços de terceiros com início atrasado | equilibrado | sim | boot e área de trabalho prontos mais cedo | esses serviços demoram ~2 min para subir |
| otimizar a unidade | seguro | sim | disco mais rápido | demora pouco |
| OneDrive bloqueado | equilibrado | sim | menos um programa sincronizando | não sincroniza mais nada com o OneDrive |

## reparar (manutenção: não vem marcada na janela)

| Item | Vem marcado a partir de | Volta | Ganha | Perde |
|---|---|---|---|---|
| reparar a imagem do Windows (DISM) | - | sim | conserta erros de atualização e travamentos | demora (até 1 h em HD) |
| conferir arquivos do sistema (SFC) | - | sim | conserta erros estranhos e telas azuis por arquivo corrompido | demora (até 45 min) |
| verificar o disco (chkdsk) | - | sim | evita perda de arquivos | nenhum |
| conferir o WMI | - | sim | conserta CPU alta do WmiPrvSE por repositório corrompido | nenhum |
| limpar o cache de DNS | - | **não** | conserta site que mudou de endereço e não abre | nenhum |
| restaurar a pilha de rede | - | **não** | conserta internet que não funciona por configuração quebrada | precisa reiniciar; VPNs e alguns antivírus podem precisar ser reinstalados |
| restaurar o Windows Update | - | **não** | conserta Windows Update preso em erro | o histórico de atualizações aparece vazio |
| consertar a Loja | - | **não** | conserta Loja que não abre ou não baixa | nenhum |
| reconstruir o cache de ícones | - | **não** | conserta ícones brancos ou trocados | o Explorador reinicia |
| registrar de novo o menu Iniciar e a busca | - | **não** | conserta menu Iniciar que não abre | nenhum |

## atualizar (manutenção: não vem marcada na janela)

| Item | Vem marcado a partir de | Volta | Ganha | Perde |
|---|---|---|---|---|
| definições do Defender | - | **não** | proteção em dia | nenhum |
| atualizações do Windows | - | **não** | segurança e correções | demora; pode pedir reinício |
| drivers pelo Windows Update | - | **não** | drivers mais novos e certificados | raramente um driver novo traz problema (dá para voltar no Gerenciador de Dispositivos) |
| programas pelo winget | - | **não** | programas em dia e mais seguros | alguns programas mudam de versão principal |
| apps da Loja | - | **não** | apps em dia | nenhum |

## interface

| Item | Vem marcado a partir de | Volta | Ganha | Perde |
|---|---|---|---|---|
| atalhos do Edge fora da área de trabalho | equilibrado | sim | área de trabalho limpa | nenhum (o Edge continua no menu) |
| sem "Saiba mais sobre esta foto" | seguro | sim | área de trabalho limpa | sem papel de parede do Bing trocando |
| ícone "Este Computador" na área de trabalho | equilibrado | sim | acesso rápido | nenhum |
| área de trabalho só com a Lixeira | extremo | sim | visual limpo | você abre programas pelo menu Iniciar |

## navegador

| Item | Vem marcado a partir de | Volta | Ganha | Perde |
|---|---|---|---|---|
| instalar o Brave | só se marcar | **não** | menos RAM que Chrome e Edge | mais um programa |
| Brave enxuto | seguro | sim | Brave mais leve | perde esses recursos do Brave |
| Chrome enxuto | seguro | sim | menos RAM | aparece "Gerenciado pela organização" |
| Edge enxuto | seguro | sim | menos RAM e propaganda | aparece "Gerenciado pela organização" |

## rede

| Item | Vem marcado a partir de | Volta | Ganha | Perde |
|---|---|---|---|---|
| medir o ping | seguro | **não** | decidir com número | nenhum |
| medir qual DNS responde mais rápido | seguro | **não** | decidir o DNS com número, não com palpite | nenhum |
| DNS Cloudflare (1.1.1.1) | só se marcar | sim | só se o teste de DNS mostrar diferença no seu caso: meça antes de trocar | redes de empresa com DNS próprio param de achar os servidores internos |
| DNS Google (8.8.8.8) | só se marcar | sim | só se o teste de DNS mostrar diferença no seu caso: meça antes de trocar | redes de empresa com DNS próprio param de achar os servidores internos |
| DNS Quad9 (9.9.9.9) | só se marcar | sim | só se o teste de DNS mostrar diferença no seu caso: meça antes de trocar | redes de empresa com DNS próprio param de achar os servidores internos |
| DNS AdGuard (94.140.14.14) | só se marcar | sim | só se o teste de DNS mostrar diferença no seu caso: meça antes de trocar | redes de empresa com DNS próprio param de achar os servidores internos |
| DNS Cloudflare Família (1.1.1.3) | só se marcar | sim | só se o teste de DNS mostrar diferença no seu caso: meça antes de trocar | redes de empresa com DNS próprio param de achar os servidores internos |
| DNS automático (do roteador) | só se marcar | sim | o padrão | nenhum |
| ajuste automático do TCP no normal | seguro | sim | downloads na velocidade certa | nenhum |

## ajustes

| Item | Vem marcado a partir de | Volta | Ganha | Perde |
|---|---|---|---|---|
| "Finalizar tarefa" no botão direito da barra | equilibrado | sim | menos passos para matar travados | nenhum |
| caminhos longos (mais de 260 letras) | equilibrado | sim | menos erros "caminho muito longo" | programas antigos podem não entender esses caminhos |
| volume do jogo igual em chamadas | equilibrado | sim | jogo e chamada no mesmo volume | quem gosta que a música abaixe nas ligações perde isso |
| barra de tarefas à esquerda | só se marcar | sim | costume | nenhum |
| segundos no relógio | só se marcar | sim | precisão | gasta um pouquinho de bateria |
| tema escuro | só se marcar | sim | conforto à noite | nenhum |
| mostrar arquivos ocultos | só se marcar | sim | achar arquivos de configuração | dá para apagar algo importante sem querer |
| Num Lock ligado ao iniciar | só se marcar | sim | digitar o PIN direto | nenhum |
| histórico da área de transferência | só se marcar | sim | produtividade | o que você copia fica guardado na memória |
| Explorador compacto | só se marcar | sim | cabe mais na tela | nenhum |
| adiar as atualizações grandes do Windows por 90 dias | só se marcar | sim | menos surpresas e menos bugs de versão nova | recursos novos chegam 90 dias depois; o Windows passa a dizer que "algumas configurações são gerenciadas pela organização" |
| não reiniciar sozinho com você logado | equilibrado | sim | sem perder trabalho por um reinício surpresa | esquecer de reiniciar deixa a atualização pendente |
| caixas de seleção nos arquivos | só se marcar | sim | útil em tela de toque | nenhum |
