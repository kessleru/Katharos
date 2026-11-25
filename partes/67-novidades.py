# ─────────────── novidades de cada versão (gerado do CHANGELOG.md por scripts/novidades.py: não edite) ───────────────
NOVIDADES = [
 {
  "versao": "5.0.2",
  "data": "25 de novembro de 2026",
  "resumo": "Revisão de estabilidade e do que cada modo marca: o modo recomendado não pode piorar o PC.",
  "itens": [
   {
    "titulo": "Nada muda sem ponto de restauração calado",
    "texto": "se o Windows não deixa criar o ponto (Proteção do Sistema desligada, disco cheio), nada é aplicado e a janela pergunta se você quer seguir sem ele. Antes seguia sem avisar."
   },
   {
    "titulo": "A manutenção respeita o que você religou",
    "texto": "ela só reaplica os ajustes quando o Windows mudou de versão (é a atualização que desfaz). Antes desligava de novo, toda semana, o que você tinha religado nas Configurações. Quando reaplica, avisa."
   },
   {
    "titulo": "Driver de vídeo fora do Windows Update",
    "texto": "a Microsoft confirmou que o Windows Update troca o driver de vídeo do fabricante por um mais antigo. O Katharos não instala mais driver de vídeo por ele (só em placa sem driver nenhum)."
   },
   {
    "titulo": "Modo equilibrado mais seguro",
    "texto": "saíram do equilibrado e foram para o extremo ou \"só se marcar\" o que tinha custo escondido: Windows.old (sem ele não se volta de versão), atualizar todos os programas pelo winget, desligar a impressão (impressora ligada depois não funcionava), apps da Loja em segundo plano e sem acesso a contatos e chamadas (WhatsApp e Vincular ao Celular), relatório de erros do Windows e fechar programas no desligamento (perdia trabalho não salvo). Chrome, Edge e Brave enxutos saíram do modo seguro."
   },
   {
    "titulo": "Nota que não engana",
    "texto": "disco avisando falha, disco com erros ou PC sem antivírus deixam a nota no vermelho (antes ficava 85, em verde). Desligamentos contados por vez, não por evento (cada um contava duas ou três vezes), e a tela azul é reconhecida mesmo com o relatório de erros do Windows desligado. Windows.old e monitor abaixo da taxa máxima em notebook não tiram mais ponto à toa."
   },
   {
    "titulo": "OneDrive",
    "texto": "só aparece para bloquear se nenhuma conta (pessoal, de trabalho ou escola) e nenhuma pasta sua estiver nele."
   },
   {
    "titulo": "Configurações que não somem",
    "texto": "gravar uma opção no mesmo instante em que outro processo lia o arquivo podia apagar as outras. E os arquivos do Katharos não falham mais por estarem em uso ou sendo examinados pelo antivírus."
   },
   {
    "titulo": "Desfazer",
    "texto": "um backup de versão antiga com o tipo errado volta mesmo assim (era o erro \"SwapEffectUpgradeEnable\" dos relatórios). Dumps de tela azul ficam 30 dias."
   },
   {
    "titulo": "Janela",
    "texto": "abre mesmo se o Python escrever um aviso antes de ficar pronto, fecha junto os PowerShell de um motor que não respondeu e, se \"Reiniciar agora\" falhar, a versão nova entra ao fechar."
   }
  ]
 },
 {
  "versao": "5.0.1",
  "data": "23 de novembro de 2026",
  "resumo": "Corrige o que o relatório de 21/11 (5.0.0) mostrou.",
  "itens": [
   {
    "titulo": "O que só serve para jogo não confunde mais",
    "texto": "o app do Claude, assistentes, chamadas, acesso remoto e editores que usam a placa de vídeo não viram mais \"sessão de jogo\", e as sessões já gravadas com esses nomes saem do Histórico e das contas de jogo."
   },
   {
    "titulo": "Antes e depois honesto",
    "texto": "só compara medidas com até 14 dias entre elas, usa a medida mais nova (antes pegava a mais velha) e ignora um turbo que nunca terminou. CPU, clock e temperatura só são comparados se as duas medidas foram na tomada ou as duas na bateria. Quando não dá para comparar, diz por quê."
   },
   {
    "titulo": "Programa com caminho estranho não é tratado como resto",
    "texto": "um caminho com caractere que o Windows não aceita (como o do Proton VPN) não conta mais como \"o arquivo sumiu\", e o serviço, a tarefa ou a entrada ficam como estão."
   },
   {
    "titulo": "Segundo plano",
    "texto": "a troca de versão só fecha o ícone se o executável mudou, e tenta de novo quando o Windows ainda segura o arquivo. O PresentMon em uso, medindo um jogo, fica para a próxima vez sem derrubar o resto."
   },
   {
    "titulo": "Atualização sem internet",
    "texto": "na abertura com o Windows, antes de o Wi-Fi conectar, a falta de rede não conta mais como erro; a próxima conferência tenta de novo."
   },
   {
    "titulo": "Relatório mais útil",
    "texto": "cada linha de erro leva a data e a versão do Katharos que a escreveu, o tipo do erro vem logo no começo (antes o corte de tamanho o apagava), a mensagem do PowerShell partida em pedaços volta inteira, e o que vem de fora do Katharos (reparo do Windows sem internet, instalador de um programa) vai separado, com dica. Um turbo largado no meio aparece como parado."
   },
   {
    "titulo": "A janela que fecha no meio de um pedido",
    "texto": "não gera mais um erro por resposta perdida."
   }
  ]
 },
 {
  "versao": "5.0.0",
  "data": "17 de novembro de 2026",
  "resumo": "Uma versão grande, que junta tudo o que veio dos relatórios e do uso no PC do dono: mais simples, mais segura e com o começo da UI nova.",
  "itens": [
   {
    "titulo": "Catálogo seguro",
    "texto": "nada que o Desfazer não volta vem marcado em modo nenhum (o \"remover o app Copilot\" saiu do equilibrado). A lista completa, com o modo de cada item e se ele volta, está em planos/catalogo-5.0.0.md."
   },
   {
    "titulo": "Manutenção à parte",
    "texto": "limpeza, reparo e atualização não vêm mais marcados no Otimizar. Ficam num bloco \"Manutenção\", para quando você quiser. O rodapé separa ajustes de tarefas, e uma linha mostra de onde vem o número do botão, área por área."
   },
   {
    "titulo": "Otimizar mais simples",
    "texto": "as áreas em que nada muda ficam numa linha recolhida, e a busca e os atalhos de marcar ficam atrás de \"Personalizar\"."
   },
   {
    "titulo": "Achados honestos",
    "texto": "quando a correção não resolve de verdade (desligamento sem tela azul, monitor em Hz errado, memória em canal único, disco no fim da vida), o botão é \"Como resolver\", não \"Aplicar\". Desligamento sem tela azul, até 12 em 60 dias, não tira ponto da nota."
   },
   {
    "titulo": "A tela Central saiu",
    "texto": "\"o que eu faria\" e o diagnóstico estão no Início; \"o que eu previ e o que aconteceu\" está no Histórico. A caixa \"Pergunte ao Katharos\" saiu."
   },
   {
    "titulo": "Dispositivos saiu",
    "texto": "a tela, a leitura de bateria, a linha no painel do ícone e a lista de periféricos no relatório."
   },
   {
    "titulo": "Tarefas agendadas",
    "texto": "as que usam o Python da Microsoft Store, ou que deram erro, contam como quebradas e são consertadas."
   },
   {
    "titulo": "Leituras mais confiáveis",
    "texto": "o andamento do PowerShell não apaga mais o resultado de uma leitura."
   },
   {
    "titulo": "Segundo plano",
    "texto": "a versão nova é copiada antes de religar. O painel do ícone mostra desde quando acompanha, tem pausar e retomar à vista e esconde a temperatura quando não há sensor."
   },
   {
    "titulo": "Histórico",
    "texto": "com poucos dias de medida, o gráfico começa na primeira, e um dia solto aparece como ponto. Relê quando falta o dia de hoje. Ganhou um calendário das horas de jogo das últimas 12 semanas."
   },
   {
    "titulo": "Menos RAM",
    "texto": "no máximo um PowerShell parado. O Ao vivo para com a janela minimizada, e o motor fecha depois de 5 min parado com a janela escondida (reabre sozinho)."
   },
   {
    "titulo": "Conferir o Katharos",
    "texto": "nas Configurações, confere o segundo plano, as tarefas, a medida do dia, a cópia protegida e o PowerShell, sem mudar nada. O resultado vai no relatório."
   },
   {
    "titulo": "UI nova (começo)",
    "texto": "a nota do PC em matriz de pontos, rótulos técnicos nos números, o lugar do conteúdo desenhado enquanto carrega, alternadores nas Configurações, aviso flutuante e Ctrl+K para ir a qualquer tela ou área digitando."
   },
   {
    "titulo": "Windows 7 e 8",
    "texto": "o Katharos precisa do Windows 10 ou 11 e agora diz isso com uma frase clara, sem ler nem mudar nada."
   }
  ]
 },
 {
  "versao": "4.5.0",
  "data": "15 de novembro de 2026",
  "resumo": "Corrige o que os relatórios de 13 e 14/11 e os achados do dono mostraram. Traz a tela Dispositivos e o começo da UI nova.",
  "itens": [
   {
    "titulo": "Acompanhamento que desligava sozinho",
    "texto": "a janela e o segundo plano usavam a mesma entrada para abrir com o Windows, e a janela apagava a do segundo plano. Agora são duas. A janela conserta a entrada se ela tiver sido trocada e religa o segundo plano se ele fechou sem você sair pelo ícone."
   },
   {
    "titulo": "Manutenção e histórico parados",
    "texto": "ao trocar de versão, o motor de administrador limpava a pasta protegida inteira. Iam junto o programa da manutenção agendada e o backup do desfazer. Agora só sai a cópia da versão anterior. As tarefas agendadas são conferidas ao abrir e consertadas (a do usuário sozinha; a de administrador com um clique no Início). O histórico ganha uma medida por dia mesmo sem a manutenção."
   },
   {
    "titulo": "Desinstalar tira tudo",
    "texto": "o segundo plano sai, as entradas de abrir com o Windows e as tarefas agendadas também. Os seus dados ficam."
   },
   {
    "titulo": "Atualização",
    "texto": "confere a cada 3 h, também com a janela aberta, e pergunta \"reiniciar agora\" ou \"na próxima vez\"."
   },
   {
    "titulo": "Telas que não perdem nada",
    "texto": "o raio-x continua rodando ao trocar de tela, e o texto do relatório não se apaga."
   },
   {
    "titulo": "Dispositivos",
    "texto": "(novo): mouse, teclado, fone e controle ligados, em fichas com a bateria num anel (Bluetooth e controles Xbox). O painel do ícone mostra as baterias e fica vermelho quando uma está baixa. O Katharos só lê: nunca muda nada no aparelho."
   },
   {
    "titulo": "FPS",
    "texto": "o botão para liberar a medida agora existe (Configurações, FPS nos jogos)."
   },
   {
    "titulo": "Consumo do Katharos",
    "texto": "o Ao vivo soma também os PowerShell de leitura, na mesma conta do Gerenciador de Tarefas. Eles fecham depois de 30 s parados e são no máximo 2."
   },
   {
    "titulo": "Memória",
    "texto": "separa o que está aberto agora do que já fechou."
   },
   {
    "titulo": "Jogos",
    "texto": "a dica de ajustes some quando tudo da área já está aplicado."
   },
   {
    "titulo": "Visual",
    "texto": "anel na nota do PC, medidor segmentado no Ao vivo, barra de gravidade nos achados do Início, raio-x rodando com layout próprio e ícones de teclado, fone e controle."
   },
   {
    "titulo": "Relatório",
    "texto": "traz um autodiagnóstico (tarefas quebradas, histórico parado, segundo plano sem ler, FPS sem permissão) e a lista de periféricos, e não manda mais linhas que não são erro."
   }
  ]
 },
 {
  "versao": "4.4.0",
  "data": "13 de novembro de 2026",
  "resumo": "Corrige o que o teste da 4.3.1 e os relatórios mostraram, e traz o que a pesquisa de otimizadores apontou.",
  "itens": [
   {
    "titulo": "Inicialização certa",
    "texto": "o Katharos contava como ligado o que estava desativado no Gerenciador de Tarefas. Agora a contagem, o achado do raio-x e a lista batem com o Gerenciador."
   },
   {
    "titulo": "Conferência sem erro",
    "texto": "dois pedaços da conferência ao mesmo tempo podiam usar o mesmo arquivo e dar \"Token '}' inesperado\". Corrigido."
   },
   {
    "titulo": "Tarefas do Katharos",
    "texto": "com o Python da Microsoft Store, elas não aparecem mais como suspeitas."
   },
   {
    "titulo": "Memória",
    "texto": "ferramentas do Windows (verificação de disco, Windows Update, antivírus) não têm mais \"Fechar\" nem \"Desinstalar\"."
   },
   {
    "titulo": "Otimizar",
    "texto": "cada item mostra o que ganha e o que perde. O botão conta só o que vai mudar. Trocar de modo mostra que está trocando."
   },
   {
    "titulo": "Sessões de jogo",
    "texto": "\"detalhes\" mostra processador, placa de vídeo, RAM, temperatura, FPS e quanto tempo cada parte ficou no limite."
   },
   {
    "titulo": "O Katharos neste PC",
    "texto": "no Ao vivo, quanto a janela, o motor e o segundo plano gastam de processador e RAM, com gráfico."
   },
   {
    "titulo": "Abre com o Windows",
    "texto": "ao ligar o PC, confere se há versão nova e abre a janela, como o Discord (desliga em Configurações)."
   },
   {
    "titulo": "Relatório automático",
    "texto": "uma vez por semana, sem nome, PC ou arquivos. Um aviso na primeira vez deixa desligar na hora."
   },
   {
    "titulo": "Ícone perto do relógio",
    "texto": "o painel ficou só com os números; \"abrir o Katharos\" abre a janela."
   },
   {
    "titulo": "Rede para jogos",
    "texto": "deixa de desligar o limitador de rede do Windows, que medições mostraram aumentar o atraso do driver de rede."
   },
   {
    "titulo": "Xbox em Ryzen X3D de dois CCDs",
    "texto": "não vem marcado, porque o processador usa o Game Bar para mandar o jogo aos núcleos certos."
   },
   {
    "titulo": "Widgets",
    "texto": "sem o app Widgets, o item conta como feito (o Windows 11 25H2 não deixa mudar as chaves)."
   },
   {
    "titulo": "Itens novos",
    "texto": "programa do fabricante gravado no firmware (WPBT), apps de fabricante instalados sozinhos, apps da Loja sem acesso a contatos e e-mail, volume do jogo igual em chamadas e inicialização rápida (só se marcar)."
   },
   {
    "titulo": "Anti-cheat",
    "texto": "o raio-x diz o que falta para o FACEIT e o Valorant (Windows 11 25H2, Secure Boot, VBS, integridade de memória), só com o que deu para ler."
   },
   {
    "titulo": "Textos honestos",
    "texto": "agendador multimídia, temporizador e jogos em janela dizem o que fazem de verdade."
   },
   {
    "titulo": "Barra de tarefas enxuta",
    "texto": "também esconde a lupa da busca."
   },
   {
    "titulo": "PC de escola ou empresa",
    "texto": "quando o Windows bloqueia a pasta protegida do Katharos, a mensagem diz isso em vez de \"código 13\"."
   }
  ]
 },
 {
  "versao": "4.3.1",
  "data": "12 de novembro de 2026",
  "resumo": "Corrige o que o teste da 4.3.0 mostrou (no PC e nos relatórios enviados) e deixa a janela mais rápida e com menos texto.",
  "itens": [
   {
    "titulo": "Mais rápido",
    "texto": "o motor atende várias telas ao mesmo tempo. Abrir o Raio-x durante uma conferência não deixa mais a tela vazia, e toda tela mostra \"carregando\" em vez de ficar preta. O raio-x lê as partes do diagnóstico ao mesmo tempo."
   },
   {
    "titulo": "Leituras quase instantâneas",
    "texto": "as leituras da janela usam um PowerShell que já está aberto, em vez de abrir um novo a cada vez (abrir custava de meio segundo a um segundo e meio). Eles fecham sozinhos depois de um minuto parados. O motor também abre mais rápido: o programa fica guardado já compilado."
   },
   {
    "titulo": "Nota mais justa",
    "texto": "poucos programas na inicialização não são mais \"grave\"; a tarefa do próprio Katharos não aparece como suspeita; cada tipo de problema tem um teto de pontos; cada achado vai para o grupo certo (driver é saúde, HD é disco). Com um jogo aberto, nada \"em repouso\" (CPU, RAM, disco, temperatura) entra na nota."
   },
   {
    "titulo": "Menos alarme falso",
    "texto": "tarefa sem assinatura é para conferir, nunca grave; o plano de energia trocado pelo próprio Katharos não vira achado; RAM só é \"quase cheia\" acima de 85 %."
   },
   {
    "titulo": "O que o Windows bloqueia",
    "texto": "item que o Windows não deixou gravar (como os widgets no Windows 11 25H2) aparece como \"o Windows bloqueia\" e não conta mais como \"vai mudar\"."
   },
   {
    "titulo": "Menos texto",
    "texto": "cada item mostra o nome e o que ganha; o que perde, a atenção e os detalhes ficam em \"detalhes\" ou com o mouse em cima. Conceitos (serviços, telemetria, memória virtual...) abrem numa janelinha."
   },
   {
    "titulo": "Raio-x por grupos",
    "texto": "Saúde, Disco, Memória, Inicialização, cada um com quanto tira da nota. As outras telas seguem o mesmo jeito."
   },
   {
    "titulo": "Otimizar",
    "texto": "o número de mudanças em cada modo, busca, \"Desmarcar tudo\", marcar ou tirar uma área inteira. Trocar de modo não guarda mais as marcas do modo anterior."
   },
   {
    "titulo": "\"Manter alterações?\"",
    "texto": "espera você voltar ao PC. O tempo para desfazer sozinho (3 minutos) só corre com você presente; antes, uma otimização longa era desfeita enquanto você estava longe."
   },
   {
    "titulo": "Ícone da bandeja",
    "texto": "um só desenho em todos os estados, com um sinal pequeno no canto (jogando, atenção, pausado)."
   },
   {
    "titulo": "Atualização",
    "texto": "o segundo plano abre a janela, não o terminal; nenhuma janela de PowerShell aparece."
   },
   {
    "titulo": "",
    "texto": "Corrigidos: \"Aplicar esta correção\" dava erro ao abrir em alguns casos; esvaziar a Lixeira com mais de 2 GB dava erro."
   }
  ]
 }
]


