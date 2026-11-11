# ─────────────── novidades de cada versão (gerado do CHANGELOG.md por scripts/novidades.py: não edite) ───────────────
NOVIDADES = [
 {
  "versao": "4.1.0",
  "data": "11 de novembro de 2026",
  "resumo": "A janela agora conta o que mudou depois de cada atualização.",
  "itens": [
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
 },
 {
  "versao": "3.1.2",
  "data": "10 de novembro de 2026",
  "resumo": "Menu do ícone mais curto, só com o que se resolve num clique.",
  "itens": [
   {
    "titulo": "Menu do ícone enxuto",
    "texto": "painel ao vivo, abrir o Katharos, pausar por 1 hora, ritmo da leitura (1, 2, 5 ou 10 s), avisos ligados ou não, iniciar com o Windows e sair. Turbo, raio-x, limpar, desfazer e o resto ficam no Katharos, a um clique em \"Abrir o Katharos\"."
   },
   {
    "titulo": "",
    "texto": "Ritmo e avisos mudados no ícone valem na hora e ficam salvos nas preferências do Katharos (as mesmas do config)."
   }
  ]
 },
 {
  "versao": "3.1.1",
  "data": "10 de novembro de 2026",
  "resumo": "Temperatura da CPU onde o Windows não mostra, e o painel do ícone com X.",
  "itens": [
   {
    "titulo": "Temperatura da CPU pelos programas de monitoramento",
    "texto": "o Windows só mostra a temperatura da CPU para quem tem driver no kernel, por isso muitos PCs davam \"sem sensor\". Agora o Katharos lê do MSI Afterburner, do HWiNFO (com \"Shared Memory Support\" ligado), do Core Temp e do AIDA64 quando estão abertos, pela memória compartilhada que eles publicam (a mesma que o overlay do RivaTuner usa durante os jogos). Só leitura, sem instalar driver nenhum: driver de sensor é o que anti-cheat bloqueia e o Defender marca. Vale no ícone, no medir, no raio-x e na leitura de 15 minutos."
   },
   {
    "titulo": "X no painel do ícone",
    "texto": "fecha o painel; o segundo plano continua. Clicar no ícone com o painel aberto também fecha (antes ele fechava e abria de novo)."
   },
   {
    "titulo": "Sair pelo ícone vale",
    "texto": "o segundo plano não volta sozinho em 15 minutos; volta no próximo início do Windows ou quando você ligar de novo."
   },
   {
    "titulo": "PC que dormiu com jogo aberto",
    "texto": "a sessão fecha quando o PC parou, sem contar o tempo dormindo."
   },
   {
    "titulo": "",
    "texto": "O executável novo é instalado quando o conteúdo muda (antes, só quando o tamanho mudava)."
   }
  ]
 }
]


