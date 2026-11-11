## 4.0.0 · {{DATA}}

O Katharos ganha janelas e um instalador que se atualiza sozinho. O terminal continua, com o mesmo motor e os mesmos dados.

- **Katharos com janelas**: Início, Raio-x, Otimizar, Ao vivo, Jogos, Sugestões, Histórico, Desfazer e Configurações, no visual do site. O Otimizar mostra cada item com o que ganha, o que perde e se já está assim no seu PC; o botão diz exatamente quantas mudanças vai fazer.
- **Instalador com atualização**: `Katharos-win-Setup.exe` instala sem pedir nada antes (o .NET e o Python vão dentro) e baixa só a diferença das versões novas. Nunca troca de versão no meio de uma mudança no PC. Em Configurações: avisar, automático ou nunca.
- **Conferido no Windows**: depois de aplicar, cada ajuste é lido de volta; o que não ficou aparece como não ficou. Mudança arriscada pergunta "está tudo funcionando?" e desfaz sozinha em 90 s sem resposta.
- **FPS de verdade nos jogos**: média, 1% mais lento e travadas, pelos eventos do próprio Windows (PresentMon, da Intel, que vem junto e é conferido pela impressão digital antes de rodar). Liberado uma vez, com confirmação. As partidas antes e depois de cada mudança são comparadas, com margem; se piorou, a central propõe desfazer.
- **Central que aprende com o seu PC**: sabe o que é normal neste PC (linha de base por contexto), descarta o minuto em que o Windows estava em manutenção, diz o que previu e o que aconteceu, e pesa a sua resposta (ajudou, não ajudou, não me importa).
- **Segundo plano mais leve**: a lista de processos sai numa chamada só, as leituras pesadas nunca caem juntas e um freio espaça o ritmo se a leitura ficar cara. No Windows do CI: 3 a 6 ms por leitura e 0,1 % da CPU.
- **Notebook**: troca o plano de energia sozinho na tomada e na bateria, se você ligar; confere cada troca e avisa se algo trocou de volta.
- **Todas as versões do Windows 10 e 11**: o raio-x diz quando a sua versão está sem atualização de segurança (e o caminho do ESU no Windows 10), e os itens que uma edição não aceita dizem isso em vez de fingir.
- **Medidas fiéis**: o benchmark mostra o que está aberto e pede para você fechar (nunca fecha nada sozinho); processos do Windows nunca aparecem como "feche este".
- **À prova de invasores**: nenhuma porta de rede aberta, PowerShell sempre pelo caminho completo, o motor de administrador só atende a interface que o abriu (senha de uso único), e o antivírus do Windows passa em cada versão antes de sair.
- **Raio-x**: arquivo de paginação num HD quando há SSD, integridade de memória (só informa: o Katharos não desliga) e agendamento de GPU.
- **Site novo**: vídeos do programa em uso, gravados com a interface de verdade, e a escolha entre janelas e terminal.
