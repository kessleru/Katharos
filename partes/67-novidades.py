# ─────────────── novidades de cada versão (gerado do CHANGELOG.md por scripts/novidades.py: não edite) ───────────────
NOVIDADES = [
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
 }
]


