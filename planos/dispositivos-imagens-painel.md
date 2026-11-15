# Plano: dispositivos sem fio, imagens na interface e o painel do ícone

15/11/2026. Pedido do dono: tirar a necessidade de instalar o software de cada marca só para ver a bateria ou o DPI. Precisa funcionar com marcas chinesas (Rapoo, Aula, Redragon, Attack Shark, VXE...) e com as grandes (Logitech, Razer, SteelSeries, Corsair, HyperX). Também pediu imagens na interface (ícones dos programas, prévia do que muda) e uma revisão do painel do ícone e do design.

## 1. Dispositivos sem fio

### O que é possível, sendo honesto

Não existe um jeito único de ler a bateria de todo aparelho:
- No **Bluetooth**, a bateria é padrão (Battery Service), e o Windows já guarda o valor. Funciona com qualquer marca.
- No **receptor 2.4 GHz**, cada fabricante (ou cada fabricante de chip) inventa o próprio protocolo.

"Funcionar com toda certeza" só dá para garantir assim:
1. Ler primeiro o que é padrão.
2. Cobrir os protocolos por **chip**, não por marca. Centenas de marcas chinesas usam os mesmos poucos chips: Sinowealth, Compx, Beken, Nordic, YiChip, Holtek, Pixart.
3. Nunca chutar. Aparelho desconhecido aparece como "ainda não leio", com o nome e o VID/PID.
4. Usar os relatórios para saber o que as pessoas têm e priorizar. A 4.5.0 já manda a lista de periféricos: VID, PID e nome, sem número de série.

### Camadas (da mais universal para a mais específica)

| Camada | Cobre | Como | Risco |
|---|---|---|---|
| A. Bluetooth padrão | qualquer fone, mouse, teclado e controle Bluetooth | `DEVPKEY_Bluetooth_Battery` ({104EA319-…} 2) no Windows, sem administrador | nenhum (**feito na 4.5.0**) |
| B. HID genérico | receptores 2.4 GHz que seguem a especificação HID de bateria (Generic Device Controls 0x06/0x20 "Battery Strength", Battery System 0x85) | lê o descritor HID (HidP_GetValueCaps) e pede o relatório de entrada ou de feature | só leitura |
| C. Controles | Xbox (XInputGetBatteryInformation), DualSense/DualShock (byte de bateria no relatório de entrada), 8BitDo no modo Xbox | APIs do Windows e relatório de entrada | só leitura |
| D. Protocolos de fabricante (leitura) | Logitech HID++ 2.0 (features 0x1000, 0x1001, 0x1004 de bateria; 0x2201 de DPI), Razer (relatório de feature de 90 bytes), SteelSeries, Corsair, HyperX e fones com protocolo conhecido | pedido de feature report, só os comandos de leitura | baixo: só leitura, comandos documentados por projetos abertos |
| E. Chips chineses | Sinowealth (Redragon, Aula, Attack Shark, Glorious antigo...), Compx (Attack Shark, VXE, ATK), Beken, Nordic | os mesmos relatórios de feature que os "drivers web" (WebHID) dessas marcas usam | médio: varia por firmware; liga um modelo só depois de testado num aparelho real |
| F. Escrita (DPI, taxa de polling, desligar sozinho, LED) | só onde a leitura já funciona | grava e guarda o valor de antes (desfazer) | só quando a pessoa clica, um aparelho por vez, nunca mexe em firmware |

Regras:
- Nada de programa de terceiros. Os protocolos são reimplementados a partir da documentação dos projetos abertos (libratbag e Solaar são MIT/GPL, openrazer é GPL, HeadsetControl é GPL). O código é nosso, e cada protocolo cita a fonte.
- Nada abre processo de jogo. Abrir o aparelho HID é outra coisa: é o mesmo que o software da marca faz.
- Um aparelho só é marcado "suportado" depois de testado num aparelho real, pelo dono ou por alguém que mandou relatório.

### Onde roda

- **Leitura periódica (bateria)**: no segundo plano (ícone, C#). Ele já roda sempre, lê a cada poucos minutos, guarda o histórico e avisa quando a bateria fica baixa. Sem abrir janela.
- **Tela Dispositivos (janela)**: cartões por aparelho com bateria, histórico de descarga, estimativa de horas restantes, DPI e polling.
- **Painel do ícone**: uma faixa "dispositivos" com as baterias. O ícone ganha um ponto vermelho quando algum passa de 15 %.

### Indo além da bateria e do DPI (o que faz sentido)

- **Aviso antes da partida**: abriu um jogo com o mouse em 10 % → "conecte o cabo antes da partida". Fora do jogo, aviso a 20 % e 10 %. No jogo, só o grave, como os outros avisos.
- **Estimativa de horas**: pela curva de descarga dos últimos dias. Mostra "quanto dura uma carga" e quando a bateria está envelhecendo (a carga durando cada vez menos).
- **Receptor em porta ruim**: receptor 2.4 GHz numa porta USB 3 ou atrás do gabinete sofre interferência. Detectado pela porta e pelas quedas de conexão, a dica é usar o extensor ou uma porta da frente.
- **Taxa de polling e teste de mouse**: uma área de teste na janela que mede a taxa de polling real (Raw Input), os cliques duplos fantasma (botão gasto) e o DPI real (arrastar uma distância conhecida).
- **Teste de controle**: zona morta e drift dos analógicos, desenhados ao vivo.
- **Teste de teclado**: ghosting e teclas presas.
- **Monitor**: a taxa de atualização em uso comparada com a máxima ("seu monitor de 144 Hz está em 60 Hz"). Só **avisa** e abre a página do Windows: nada muda a imagem sozinho (regra do Katharos).
- **Software da marca rodando à toa**: se o Katharos já lê a bateria daquele aparelho, a Memória e a Inicialização sugerem tirar o G HUB, o Synapse ou o iCUE da inicialização. Isso mostra a RAM economizada, sem desinstalar sozinho.
- **Histórico**: as baterias entram no histórico (quanto tempo cada aparelho fica longe da tomada).
- **Relatório**: aparelho que o Katharos ainda não lê vai com VID/PID e o descritor HID (sem número de série). É assim que entra o próximo protocolo.

### Fases

1. **4.5.0 (feito)**: lista dos periféricos, bateria Bluetooth, tela Dispositivos, lista no relatório.
2. **4.6**: camadas B e C. Leitura no segundo plano, faixa no painel do ícone, avisos de bateria baixa, histórico e estimativa.
3. **4.7**: camada D (Logitech HID++, Razer, SteelSeries, HyperX, Corsair, fones conhecidos), leitura de DPI e de polling.
4. **4.8**: camada E por chip, começando pelos que mais aparecem nos relatórios (o Rapoo e o Aula do dono primeiro), e a área de testes (mouse, controle, teclado).
5. **4.9**: camada F (escrita) com desfazer.

### O que falta para começar a fase 2 no PC do dono

Abrir a tela Dispositivos na 4.5.0 e mandar um relatório. A lista traz o VID/PID do Rapoo e do Aula, e assim dá para saber qual chip cada um usa.

## 2. Imagens na interface

### Ícones dos programas (Memória, Inicialização, Otimizar/apps)

Hoje é uma letra num quadrado (IconeDoPrograma.Inicial). Proposta:
- O motor já sabe o caminho do executável de cada programa (Inicialização, processos da Memória). A janela extrai o ícone do .exe (SHGetFileInfo / Icon.ExtractAssociatedIcon) e guarda um PNG de 32 px em `~/.katharos/cache/icones/<hash do caminho>.png`.
- Sem caminho, ou sem ícone, continua a letra (o fallback atual).
- Apps da Loja: o logo vem do manifesto do pacote (Square44x44Logo).
- Nunca baixa ícone da internet.
- Custo: extração só na primeira vez, cache em disco e leitura preguiçosa (só os que aparecem na tela).

### Prévia do que muda (personalização e afins)

Para itens visuais (barra de tarefas, menu de contexto, menu Iniciar, Explorer, tema), o item ganha uma prévia **antes → depois** desenhada pelo Katharos em vetor: a barra com a lupa e a barra sem a lupa, o menu de clique direito antigo e o novo. Nada de captura de tela de terceiros nem de logotipo da Microsoft.
- Formato: o item ganha `previa: "barra-sem-busca"`, e a janela tem um catálogo de desenhos (Geometry, como os ícones de hoje), no tema do Katharos.
- Onde aparece: ao passar o mouse ou ao expandir o item no Otimizar e na caixa "Aplicar esta correção".
- Começar pelos 10 itens visuais mais usados.

### A refatoração de UI que isso pede

O Otimizar e a Memória montam as linhas à mão em cada tela. Proposta:
- Um componente `LinhaDeItem` (ícone ou prévia, título, ganha/perde, etiqueta, ação) usado por Otimizar, Memória, Inicialização e Dispositivos.
- Um `IconeDoPrograma.De(caminho, nome)` que devolve a imagem ou a letra.
- As telas passam a descrever os dados, e o componente desenha. Menos código repetido e menos lugar para o mesmo bug.
- Fazer em uma versão só de UI (sem mexer no motor), com as fotos do Katharos.Fotos de antes e depois para comparar.

## 3. Painel do ícone (segundo plano)

O que está bom: números grandes, minigráficos, uma linha por recurso, FPS no lugar da rede durante o jogo, e os botões raio-x, jogos e abrir o Katharos.

O que melhorar:
- **Dispositivos**: a faixa de baterias (fase 2 acima).
- **Estado do próprio segundo plano**: hoje, se ele cai, ninguém vê. O painel deve mostrar "acompanhando desde 22:31" e a janela deve avisar quando ele não está rodando sem você ter saído (a 4.5.0 religa sozinho).
- **Rodapé**: diz agora "este ícone usa N MB" (o total do Katharos fica no Ao vivo, que conta tudo). Antes parecia contradizer o Ao vivo e o Gerenciador.
- **FPS sem permissão**: o painel manda para a janela, e o botão "Liberar" agora existe (4.5.0).
- **Pausar e retomar** visível no painel, não só no menu do ícone.
- **Temperatura sem sensor**: hoje pede para abrir o Afterburner. Deveria dizer uma vez e depois esconder a linha.

## 4. Design do Katharos (revisão das telas)

Revisado pelas fotos do Katharos.Fotos (980 px):
- Consistente: grade com linhas e "+", títulos em mono, grupos com ícone e subtítulo, ação em âmbar.
- Memória: agora separa abertos e fechados.
- Raio-x rodando: agora tem layout próprio, com o que já foi lido em duas colunas e o que o raio-x olha.
- A melhorar:
  - Telas que terminam cedo deixam metade da janela vazia. Um rodapé leve com "próximo passo" ajudaria.
  - Os ícones da tela Dispositivos ainda são todos de mouse. Faltam ícones de teclado, fone e controle.
  - Na Memória, a ação "Desinstalar…" aparece em programas que só estão na RAM por pouco tempo. Mostrar só com o mouse em cima.
  - O cabeçalho do Raio-x mostra "Fazer de novo" durante a leitura. Esconder enquanto roda.
