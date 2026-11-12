# ─────────────── novidades de cada versão (gerado do CHANGELOG.md por scripts/novidades.py: não edite) ───────────────
NOVIDADES = [
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
 },
 {
  "versao": "4.3.0",
  "data": "11 de novembro de 2026",
  "resumo": "Corrige o que apareceu no primeiro teste da 4.2.0 num PC de verdade e deixa a janela mais fácil de entender: abre na hora, cada botão leva ao lugar certo e o Início nunca sugere o que já está feito.",
  "itens": [
   {
    "titulo": "Abre na hora",
    "texto": "o que o Katharos conferiu no PC fica guardado e vale até você aplicar ou desfazer, o Windows atualizar ou passar um dia. Quando precisa ler de novo, lê uma área por vez, por trás, sem travar a janela: só a linha muda quando chega."
   },
   {
    "titulo": "Tela de abertura",
    "texto": "com o cavaleiro do site. Ela prepara tudo antes da janela abrir, inclusive conferir o que o Início vai mostrar."
   },
   {
    "titulo": "O Início não se contradiz",
    "texto": "o que já foi resolvido depois do raio-x sai da lista e a nota sobe junto. A inicialização mostra quantos programas abrem agora, os mesmos que a tela seguinte mostra."
   },
   {
    "titulo": "Cada botão leva ao lugar certo",
    "texto": "\"Aplicar esta correção\" mostra só os itens daquela sugestão. Achado que só se investiga (desligamento, tela azul, driver) mostra o passo a passo e nunca abre o Otimizar."
   },
   {
    "titulo": "Tela de detalhe",
    "texto": "o que é, o que o Katharos viu neste PC, por que importa, como resolver e como desfazer, para qualquer achado."
   },
   {
    "titulo": "O que abre com o Windows",
    "texto": "uma tela própria, com o ícone de cada programa, o atraso medido no boot e um interruptor. Os que o Katharos desligou ficam embaixo, com Religar."
   },
   {
    "titulo": "Desfazer por item",
    "texto": "escolha quais itens voltam e o resto continua aplicado. O que foi aplicado antes desta versão só volta com a área inteira, e a tela diz isso."
   },
   {
    "titulo": "Memória",
    "texto": "quem usa a RAM, com a média e o pico do dia e da semana, e se ela está cheia de verdade ou só alta. Windows, drivers e proteção aparecem sem nenhuma ação; o que o Katharos não conhece diz \"não conheço\"."
   },
   {
    "titulo": "Gráficos",
    "texto": "passe o mouse para ver o valor e a data, clique numa marca para ver o que foi aplicado, amplie com dois cliques (zoom com a roda, comparar duas medidas). Dia sem leitura fica em branco, e não mais como zero."
   },
   {
    "titulo": "Sem falso alarme",
    "texto": "as tarefas do próprio Katharos não aparecem mais como suspeitas, e programa com assinatura digital vira \"para conferir\". O driver do Ryzen Master fechado é explicado como comum. No desligamento, o que é certo (aconteceu) fica separado do que é provável (a causa)."
   },
   {
    "titulo": "Visual",
    "texto": "ícones no menu e nas seções, listas com marcador, menos texto, Jogos dentro do Início e animações curtas que respeitam o \"reduzir animações\" do Windows (dá para desligar nas Configurações)."
   }
  ]
 },
 {
  "versao": "4.2.0",
  "data": "11 de novembro de 2026",
  "resumo": "Agora dá para mandar um relatório, a sua opinião, ou os dois, direto da janela. É com isso que o Katharos vai melhorar: os erros que aparecem nos PCs de verdade e o que cada otimização rende em cada um.",
  "itens": [
   {
    "titulo": "Tela Enviar relatório",
    "texto": "no menu, no Início e em toda caixa de erro. Você escolhe mandar o relatório, o feedback (problema, ideia, elogio ou outro, com nota de 1 a 5 e um contato opcional para resposta) ou os dois."
   },
   {
    "titulo": "Relatório completo",
    "texto": "erros do Katharos (motor, janela e acompanhamento), o que foi aplicado e desfeito, o que voltou sozinho, o que cada otimização rendeu medido antes e depois, as suas respostas de \"ajudou\", a saúde do PC, o peso do próprio Katharos e as sessões de jogo. Cada parte pode ser desmarcada."
   },
   {
    "titulo": "Nada pessoal sai",
    "texto": "nome de usuário, nome do PC, pastas pessoais, e-mail, IP, MAC, chave de produto e identificadores do Windows viram marcadores antes de sair, e partes como portas abertas e arquivos nunca entram. Antes de mandar, você vê o resumo e o texto exato."
   },
   {
    "titulo": "Só sai quando você clica",
    "texto": "nada é enviado sozinho. Sem internet, o envio fica guardado no PC e você manda depois pela mesma tela. Cada envio recebe um código (KTH-...) que fica na tela e serve para pedir para apagar."
   },
   {
    "titulo": "Sempre dá para ver que está fazendo",
    "texto": "todo botão que conversa com o motor mostra \"…\" e fica desligado enquanto trabalha (um segundo clique não roda de novo), e a barra lateral acende em âmbar com o que está acontecendo. Ligar o acompanhamento mostra cada passo (\"abrindo\", \"esperando a primeira leitura\") e, num PC lento, diz que já está rodando em vez de parecer travado. Aplicar e desfazer mostram onde aparece o pedido de permissão do Windows, e toda espera longa mostra há quantos segundos está trabalhando."
   },
   {
    "titulo": "Ao vivo mais leve",
    "texto": "a tela não se refaz mais a cada leitura, só os números mudam, e a leitura do arquivo saiu da linha da janela (um disco lento não trava a tela)."
   },
   {
    "titulo": "Início abre na hora",
    "texto": "mostra a última leitura e troca quando a nova chega, sem \"carregando\" a cada visita."
   },
   {
    "titulo": "Otimizar não pula",
    "texto": "a conferência do que já está feito atualiza os itens no lugar, sem refazer a tela (antes a rolagem pulava)."
   },
   {
    "titulo": "Erros que dizem o que fazer",
    "texto": "cada erro aparece com um título claro (\"O motor do Katharos fechou\", \"Sem permissão para um arquivo\", \"Arquivo em uso\"), o que fazer em seguida, o que aconteceu com o PC, um número de referência e os botões \"Copiar detalhes\" e \"Abrir os registros\". O número também fica no registro, ao lado do erro inteiro. Trocar de modo no Otimizar com erro volta ao modo de antes, e um erro que fecharia o aplicativo fica registrado."
   },
   {
    "titulo": "Novidades ao abrir",
    "texto": "na primeira abertura depois de atualizar, uma caixa mostra o que mudou desde a última versão que você viu, com o mesmo texto deste histórico. Aparece uma vez só por versão e nunca na primeira instalação. Para rever depois, vá em Configurações > Novidades."
   },
   {
    "titulo": "Esc fecha as caixas",
    "texto": "as caixas de aviso e de resultado também fecham com a tecla Esc."
   }
  ]
 },
 {
  "versao": "4.0.2",
  "data": "11 de novembro de 2026",
  "resumo": "Correção da interface, vista num notebook Acer: a janela carregava os dados para sempre e o botão de ligar o acompanhamento só fazia a tela piscar.",
  "itens": [
   {
    "titulo": "Ligar o acompanhamento",
    "texto": "a tela Ao vivo se refazia a cada segundo, o que derrubava o clique no botão e trocava o \"Ligando\" pelo aviso de desligado. Agora ela só se refaz quando o estado muda, ignora o segundo clique e espera até 20 s pela primeira leitura (PC mais lento). Se não ligar, a mensagem de erro fica na tela, com \"tentar de novo\"."
   },
   {
    "titulo": "Carregando para sempre",
    "texto": "o motor agora avisa que está pronto antes de converter dados e conferir o segundo plano; antes, um desses passos lento ou travado deixava toda tela em \"carregando\" sem nenhum sinal. A janela também desiste de esperar um motor mudo (60 s para abrir, 2 min sem resposta; 10 min no raio-x), fecha ele e mostra \"tentar de novo\"."
   },
   {
    "titulo": "\"Desligado\" com o acompanhamento rodando",
    "texto": "num PC lento o segundo plano espaça as leituras (até 30 s, para não pesar) e a janela e o motor só aceitavam uma leitura de até 20 s, então diziam \"desligado\" e o botão de ligar parecia não fazer nada. Agora o segundo plano grava o ritmo real (espera_s) e quem lê espera três ritmos. Ligar também espera até 20 s o Katharos.exe abrir (antes 5 s), para o caso de o antivírus verificá-lo na primeira vez."
   },
   {
    "titulo": "Telas travadas esperando a permissão do Windows",
    "texto": "o motor comum e o de administrador usavam a mesma fila de abertura; enquanto o Windows esperava a resposta do pedido de permissão (até 90 s), toda tela ficava em \"carregando\". Agora cada motor tem a sua fila."
   },
   {
    "titulo": "Versão na janela",
    "texto": "a barra lateral mostra os três números (4.0.2), que é o que a pessoa precisa dizer ao pedir ajuda."
   }
  ]
 },
 {
  "versao": "4.0.1",
  "data": "11 de novembro de 2026",
  "resumo": "Correções da revisão depois da 4.0.0. Nenhum item novo.",
  "itens": [
   {
    "titulo": "Limpeza segura com links",
    "texto": "a limpeza nunca entra em junção nem em link simbólico. Antes, um link dentro de uma pasta limpa (como a de temporários) podia levar a limpeza a apagar arquivos antigos de fora dela."
   },
   {
    "titulo": "Manutenção em segundo plano espera o jogo",
    "texto": "com um jogo aberto ela adia, e o ponto de restauração mensal e a limpeza de componentes (DISM), que pesam no disco, só rodam com o PC livre."
   },
   {
    "titulo": "Limpezas que não atrapalham o uso",
    "texto": "o cache de shaders só apaga o que não é usado há mais de 30 dias (apagar tudo fazia cada jogo recompilar e engasgar); o cache dos navegadores na manutenção só apaga o que tem mais de 14 dias."
   },
   {
    "titulo": "Aviso claro no HAGS",
    "texto": "o agendamento de GPU por hardware só liga se o Windows já mostra suporte nessa placa e driver, e o texto do que se perde diz que o ganho é pequeno e que placa antiga ou com pouca memória de vídeo pode engasgar."
   },
   {
    "titulo": "Arquivo de estado do tipo errado",
    "texto": "um arquivo de estado ou configuração com JSON válido mas de outro tipo (lista, nulo, número) derrubava sete métodos do motor; agora é tratado como ilegível, guarda a cópia e recomeça com o padrão."
   },
   {
    "titulo": "Windows PowerShell 5.1 sem módulos do PowerShell 7",
    "texto": "no Windows as variáveis de ambiente vêm em maiúsculas e a limpeza do PSModulePath nunca era aplicada; agora é."
   },
   {
    "titulo": "Pergunte ao Katharos",
    "texto": "\"vírus\" voltou a achar o comando que confere se o programa é o original, e pergunta enorme é cortada em 500 caracteres."
   }
  ]
 },
 {
  "versao": "4.0.0",
  "data": "11 de novembro de 2026",
  "resumo": "O Katharos ganha janelas e um instalador que se atualiza sozinho. O terminal continua, com o mesmo motor e os mesmos dados.",
  "itens": [
   {
    "titulo": "Katharos com janelas",
    "texto": "Início, Raio-x, Otimizar, Ao vivo, Jogos, Central, Histórico, Desfazer e Configurações, no visual do site. O Otimizar mostra cada item com o que ganha, o que perde e se já está assim no seu PC; o botão diz exatamente quantas mudanças vai fazer. Na primeira abertura, três passos guiados."
   },
   {
    "titulo": "Um programa só",
    "texto": "o ícone perto do relógio (segundo plano) abre a janela na tela certa, o aviso também; a janela liga e desliga o segundo plano, e a troca de versão fecha e religa ele sozinha."
   },
   {
    "titulo": "Instalador com atualização",
    "texto": "Katharos-win-Setup.exe instala sem pedir nada antes (o .NET e o Python vão dentro) e baixa só a diferença das versões novas. Nunca troca de versão no meio de uma mudança no PC. Em Configurações: avisar, automático ou nunca, e o canal estável ou prévia. A versão de terminal também se atualiza: katharos versoes --atualizar (confere o SHA-256 antes de trocar e guarda a anterior; --voltar desfaz)."
   },
   {
    "titulo": "Conferido no Windows",
    "texto": "depois de aplicar, cada ajuste é lido de volta; o que não ficou aparece como não ficou. Mudança arriscada pergunta \"está tudo funcionando?\" e desfaz sozinha em 90 s sem resposta."
   },
   {
    "titulo": "FPS de verdade nos jogos",
    "texto": "média, 1% mais lento e travadas, pelos eventos do próprio Windows (PresentMon, da Intel, que vem junto e é conferido pela impressão digital antes de rodar). Liberado uma vez, com confirmação. As partidas antes e depois de cada mudança são comparadas, com margem; se piorou, a central propõe desfazer."
   },
   {
    "titulo": "Central que aprende com o seu PC",
    "texto": "sabe o que é normal neste PC (linha de base por contexto, guardada por meses numa memória local em SQLite), acha o que pesa (limite nos jogos, fora do normal, piorando há dias, piora depois de uma mudança, erros do Windows, travadas) e diz a causa mais provável com as descartadas: o que viu, por que acha isso, o que faria e o que mudaria a conclusão. Diz o que previu e o que aconteceu, pesa a sua resposta e o resultado medido, e propõe desfazer o que piorou. Pergunte ao Katharos (\"por que meu jogo trava?\") responde com o que ele mediu, sem nada sair do PC."
   },
   {
    "titulo": "Qual driver trava",
    "texto": "katharos travadas (e o botão na central) mede por um minuto o tempo que cada driver segura o processador, como o LatencyMon, e diz o culpado em linguagem simples. Quando os jogos travam sem nenhum limite, a manutenção mede sozinha uma vez."
   },
   {
    "titulo": "Avisos com orçamento",
    "texto": "no máximo um por tipo a cada 6 horas (você escolhe), nada durante o jogo além de calor grave, e um resumo por dia se preferir."
   },
   {
    "titulo": "Segundo plano mais leve",
    "texto": "a lista de processos sai numa chamada só, as leituras pesadas nunca caem juntas e um freio espaça o ritmo se a leitura ficar cara. No Windows do CI: 3 a 6 ms por leitura e 0,1 % da CPU."
   },
   {
    "titulo": "Notebook",
    "texto": "troca o plano de energia sozinho na tomada e na bateria, se você ligar; confere cada troca e avisa se algo trocou de volta."
   },
   {
    "titulo": "Todas as versões do Windows 10 e 11",
    "texto": "o raio-x diz quando a sua versão está sem atualização de segurança (e o caminho do ESU no Windows 10), e os itens que uma edição não aceita dizem isso em vez de fingir."
   },
   {
    "titulo": "Medidas fiéis",
    "texto": "o benchmark mostra o que está aberto e pede para você fechar (nunca fecha nada sozinho); processos do Windows nunca aparecem como \"feche este\"."
   },
   {
    "titulo": "À prova de invasores",
    "texto": "nenhuma porta de rede aberta, PowerShell sempre pelo caminho completo, o motor de administrador roda de uma cópia em %ProgramData% conferida pelo SHA-256 gravado no aplicativo e só atende a janela que o abriu (senha de uso único), e o antivírus do Windows passa em cada versão antes de sair. Testado no Windows do CI: instalar, atualizar com o segundo plano rodando e desinstalar guardando os dados."
   },
   {
    "titulo": "Raio-x e itens novos",
    "texto": "arquivo de paginação num HD quando há SSD, integridade de memória (só informa: o Katharos não desliga), agendamento de GPU e o que ficou no limite nos jogos. Itens novos: monitor na taxa máxima (testa antes, lê de volta e volta sozinho se a tela apagar), placa de rede sem economia em PC de mesa, efeitos visuais já no modo seguro em PC fraco."
   },
   {
    "titulo": "Medidas fiéis de verdade",
    "texto": "boot medido pelo Windows (caminho principal, sem o boot logo depois de atualização, mediana dos últimos), qualidade da medida em toda tela de ganho, o antes e depois de cada aplicação pela janela e o ensaio repetido (provas --repetir)."
   },
   {
    "titulo": "Site novo",
    "texto": "vídeos do programa em uso, gravados com a interface de verdade, e a escolha entre janelas e terminal."
   },
   {
    "titulo": "Windows Server 2022 e 2025",
    "texto": "no teste de verdade do CI, além do Windows 10 e 11."
   }
  ]
 }
]


