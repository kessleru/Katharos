# Plano: interface gráfica, instalador com atualização e site novo

Pedido de 10 nov 2026: uma interface gráfica em C#, **bem fácil de entender para qualquer pessoa**, um instalador, atualização sem baixar de
novo a cada versão, a escolha entre a versão com janelas e a de terminal no site, e um site novo feito com bibliotecas de componentes, mais
vivo. Junto: **o painel sai do HTML e vai para dentro da interface**, e melhorias no raio-x e nas otimizações. Este arquivo é o plano e o registro:
cada tarefa tem um código; quando ficar pronta, marque `[x]`, anote no **Registro** (fim do arquivo) a data, a versão e o commit.

**Estado:** planejado, nada implementado.

| fase | o quê | estado |
|---|---|---|
| 0 | fontes no repositório, protótipos e decisões confirmadas | a fazer |
| 1 | motor com API (o Python conversa com a interface por JSON) | a fazer |
| 2 | o aplicativo com janelas (Katharos.App), com o painel dentro dele | a fazer |
| 2b | raio-x mais completo e otimizações guiadas por evidência | a fazer |
| 2c | prova em jogo: teste no PC real, FPS de verdade, antes e depois por jogo, travadas por driver; notebook na tomada e na bateria | a fazer |
| 3 | o segundo plano dentro do aplicativo | a fazer |
| 4 | instalador e atualização (Velopack) | a fazer |
| 5 | publicação dos dois produtos e assinatura do executável | a fazer |
| 6 | site novo (Astro + shadcn/ui + Magic UI) com download CLI ou GUI | a fazer |
| 7 | migração de quem já usa, documentação e lançamento | a fazer |

---

## 1. Decisões

Cada decisão diz o porquê e a alternativa descartada. As marcadas "confirmar na fase 0" dependem de um protótipo antes de valer.

### D1. Atualização automática: viável, com Velopack
- **Velopack** (sucessor do Squirrel, ativo: versão 1.2.161 de set/2026, prévia 1.3 em out/2026) gera o instalador (`Setup.exe`),
  os pacotes de atualização e as **atualizações por diferença** (só o que mudou, por arquivo, com Zstandard). Busca as versões direto nas
  **releases do GitHub** (procura também as diferenças nas releases anteriores). Instala por usuário em `%LocalAppData%\Katharos`,
  **sem pedir administrador** para instalar nem para atualizar.
- O aplicativo confere ao abrir e uma vez por dia, baixa em segundo plano e aplica ao reiniciar (ou na hora, se a pessoa clicar).
- Descartado: **MSIX + App Installer** (exige certificado de assinatura para instalar; sem ele nem instala); **Inno Setup + atualizador
  próprio** (o instalador é ótimo, mas a atualização por diferença e a troca segura dos arquivos teriam de ser escritas à mão).
- Limite honesto: sem assinatura digital, o `Setup.exe` ainda mostra o aviso do SmartScreen na **primeira** instalação. As atualizações
  depois não passam pelo SmartScreen (não são downloads do navegador). Ver D6.

### D2. Interface: C# com Avalonia (confirmar na fase 0)
- **.NET 10 (LTS, suporte até nov/2028)** e **Avalonia 11** com MVVM (CommunityToolkit.Mvvm) e bindings compilados.
- Por que Avalonia e não WPF: a identidade do Katharos é muito própria (escuro, âmbar, gravura); o Avalonia desenha tudo com Skia e estiliza
  com seletores parecidos com CSS, o que deixa reproduzir o site com fidelidade. Ele também compila em **Native AOT** no Windows: um
  executável que abre rápido, sem precisar do .NET instalado.
- Alternativa forte: **WPF + WPF UI (Fluent)**. Mais maduro e só Windows, mas o visual puxa para o Fluent padrão e o AOT não existe. Se o
  protótipo do Avalonia (tarefa 0.4) mostrar problema sério (texto, DPI, acessibilidade, tamanho), a decisão vira WPF.
- Descartado: **WinUI 3** (empacotamento e distribuição mais trabalhosos, sem ganho para este caso); **MAUI** (feito para celular).

### D3. O motor continua sendo o Katharos de hoje, a interface conversa com ele
- Os 176 itens, o PowerShell gerado, o desfazer, as provas e o raio-x estão no Python e funcionam. Reescrever tudo em C# antes de ter a
  interface atrasaria meses e quebraria o que está testado.
- Fase 1 cria `katharos api`: o motor recebe pedidos e responde em **JSON por linha** (entrada e saída padrão). A interface só desenha e pede.
- O instalador leva um **Python embutido** (o pacote "embeddable" oficial do python.org, ~11 MB). Quem instala a versão com janelas não
  precisa ter Python.
- **Preferência por C#** (pedido do usuário): o que fica melhor ou mais rápido em C# migra aos poucos, começando pela leitura do PC
  (raio-x, medir, temperatura), que já existe no Katharos.exe. Cada migração é uma tarefa com teste comparando a saída antiga e a nova.

### D4. Administrador só quando precisa
- O aplicativo roda como o usuário. Para aplicar ou desfazer, abre **um** motor elevado (um pedido do UAC por sessão) e conversa com ele por
  um pipe com nome, restrito ao usuário (ACL). Leitura, painel, ao vivo e central rodam sem elevação.
- Mantém a regra de 3.0.4: nada elevado depende de arquivo que um programa comum consegue trocar (o Python embutido e o motor ficam em
  `%LocalAppData%\Katharos`, que é do usuário: por isso o motor elevado é **copiado e conferido por hash** para `%ProgramData%\Katharos`
  antes de rodar elevado).

### D5. Dois produtos, a mesma versão
- **Katharos (com janelas)**: `Katharos-Setup.exe`, instala, cria atalho, atualiza sozinho. Recomendado.
- **Katharos CLI**: o `Katharos.zip` de hoje (terminal). Ganha `katharos atualizar`, que baixa a release nova pelo PowerShell (o Python
  continua sem rede, regra do módulo de autenticidade), confere o hash e troca os arquivos.
- Mesma numeração de versão para os dois; uma release do GitHub leva os dois.

### D6. Assinatura digital: SignPath Foundation (grátis para código aberto)
- Requisitos: licença aprovada pela OSI (MIT, ok), build automático no CI, MFA no GitHub, política de assinatura publicada no site,
  nome e versão do produto no binário, e o programa avisar das mudanças e permitir desfazer (o Katharos já faz).
- O usuário faz o pedido pela conta dele; a fase 5 deixa o workflow pronto para assinar.
- Nenhuma assinatura tira o aviso na hora: a reputação no SmartScreen cresce com os downloads. Azure Artifact Signing é só para pessoa física
  nos EUA e no Canadá; certificado OV custa US$ 150 a 300 por ano.

### D7. Site: Astro + React (ilhas) + shadcn/ui + Magic UI + Motion
- **Astro** gera o site estático para o GitHub Pages (build no Actions, `actions/deploy-pages`). Só as partes interativas carregam JavaScript.
- **shadcn/ui** (Radix + Tailwind v4): base acessível e copiada para o repositório (não é dependência fechada): abas, acordeão, botões,
  diálogo, tooltip, menu, tabela.
- **Magic UI** (e Aceternity onde fizer sentido): componentes animados prontos, como número que conta, terminal que digita, borda com brilho,
  linha animada entre componentes e marquee.
- **Motion** para as animações próprias.
- Regras que continuam: identidade do site atual (cores, tipografia, gravuras); **a imagem do cavaleiro e da grama nunca muda**; nada de
  animação lenta, pesada ou que trava (reclamação de 9 nov: quadriculado, rodapé, espada); `prefers-reduced-motion` respeitado; sem cara de
  IA (ver a skill frontend-design); linhas e "+" dos containers mantidos.
- Os dados do site (modos, lista das mudanças por área, novidades) saem do programa como JSON gerado no build, como o `gera_site.py` faz hoje.
- **Bibliotecas de referência, sem pagar**: o usuário citou o Magic do 21st.dev (MCP pago, gera componentes por pedido). Alternativas grátis
  que fazem o mesmo papel de "componente pronto e bom" para quem escreve com IA:
  - **MCP oficial do shadcn/ui** (`npx shadcn@latest mcp`): procura, mostra e instala componentes e blocos do registro do shadcn e de
    registros de terceiros, direto na sessão.
  - **MCP do Magic UI** (grátis): os componentes animados do Magic UI pela mesma via.
  - **React Bits** (componentes animados grátis, copiar e colar; o MCP deles é da versão Pro, paga: não usar).
  - **Comunidade do 21st.dev**: os componentes publicados lá são grátis para copiar; o pago é só o gerador (Magic).
  - **Aceternity UI** (grátis) para efeitos pontuais; **Context7** (MCP grátis) para a documentação atual de Astro, Tailwind e Motion.
  - Tarefa 0.6 testa os MCPs grátis na prática e escolhe; 6.1 instala os que ficarem (como servidores MCP desta sessão ou do repositório).

### D8. O painel vai para dentro da interface; acaba o painel em HTML
- Pedido do usuário: nada de painel que gera um arquivo HTML e abre no navegador. Tudo o que o `painel` mostra (agora, o que está mudando,
  evolução, temperatura por hora, consumo, ao vivo e jogos, provas de ganho, benchmark, saúde, propostas) vira a tela **Histórico** e a tela
  **Ao vivo** do aplicativo, com gráficos nativos (LiveCharts2 ou ScottPlot para Avalonia: decidir na fase 0, tarefa 0.4).
- Na CLI, `painel` abre o aplicativo na tela Histórico quando ele está instalado; sem ele, mostra o resumo no terminal (cartões e linhas
  com sparklines, como o `aovivo`). O gerador de HTML (`64-painel.py`, `64-termica.py`) e os links `katharos://` do painel saem; o
  `katharos://` passa a abrir uma tela do aplicativo (ex.: `katharos://raiox`). Isso remove um comando de saída e por isso entra na 4.0.0.

### D9. Fácil para qualquer pessoa
- **Primeira abertura guiada em 3 passos**: (1) o raio-x roda sozinho e mostra a nota e o que mais pesa; (2) a pessoa escolhe o modo, com
  uma frase do que cada um faz e um selo "recomendado para este PC"; (3) revisa a lista do que vai mudar e aplica. Pular é sempre possível.
- **Uma ação principal por tela**, em botão grande; o resto é secundário. Palavras do dia a dia: "deixar o PC mais rápido para jogos", não
  "agendamento de GPU". O termo técnico aparece embaixo, menor, para quem quer saber.
- **Cada item com três linhas fixas**: o que faz, o que você ganha, o que você perde. Ícone de risco (baixo, médio, alto) com cor e texto,
  nunca só cor.
- **Estados vazios que dizem o que fazer** ("Ainda não há medidas. Ligue o acompanhamento em segundo plano" com o botão ali mesmo).
- **Depois de aplicar, o resultado em número** (antes e depois: boot, RAM livre, processos), com o botão desfazer visível.
- **Teste de usabilidade** com 3 pessoas que não são da área antes de lançar (tarefa 2.13): achar o raio-x, aplicar o modo seguro,
  desfazer um item. Onde travarem, a tela muda.

---

## 2. Arquitetura

```
 Katharos.App (C#, Avalonia, como o usuário)           %LocalAppData%\Katharos  (instalado pelo Velopack)
 ├─ janelas: início, raio-x, otimizar, ao vivo, ...     ├─ current\Katharos.App.exe   (+ segundo plano, mesmo executável)
 ├─ segundo plano: ícone + leitura contínua (fase 3)    ├─ current\motor\katharos.py  (+ katharos.ps1)
 ├─ atualização: Velopack + releases do GitHub          ├─ current\python\            (Python embutido)
 └─ fala com o motor ───────────┐                       └─ packages\                  (versões e diferenças)
                                │ JSON por linha
            ┌───────────────────┴───────────────────┐
     motor comum (sem elevação)               motor elevado (um UAC por sessão)
     raio-x, medir, central, painel           aplicar, desfazer, turbo, verificar
     python katharos.py api                   cópia conferida em %ProgramData%\Katharos, pipe com ACL do usuário

 ~/.katharos  (os dados, como hoje: estado, backups do desfazer, medidas, agora.json, minutos, sessões)
```

Protocolo `katharos api` (rascunho; fechar na tarefa 1.1):
- pedido: `{"id": 7, "metodo": "itens", "params": {"area": "privacidade", "modo": "equilibrado"}}`
- resposta: `{"id": 7, "ok": true, "dados": {...}}` ou `{"id": 7, "ok": false, "erro": {"codigo": "...", "texto": "..."}}`
- eventos durante uma operação longa: `{"id": 7, "evento": "progresso", "dados": {"item": "telemetria", "estado": "feito", "n": 12, "de": 40}}`
- métodos: `versao`, `perfil`, `raiox`, `medir`, `areas`, `itens` (com "já feito"), `explicar`, `plano` (modo → o que marca),
  `aplicar`, `desfazer`, `pontos`, `aplicado`, `verificar`, `conselheiro`, `painel_dados`, `sessoes`, `config_ler`, `config_gravar`,
  `segundo_plano`, `cancelar`.

---

## 3. Tarefas por fase

### Fase 0: base e protótipos
- [ ] **0.1** Pôr `partes/` (as fontes do `katharos.py`), `arte/` (gerador e modelo do site) e o script de montagem no repositório, com um
  teste que falha se o `katharos.py` não for exatamente a soma das partes. Hoje elas só existem numa sessão; o outro chat editou o
  `katharos.py` direto, e o trabalho precisou ser recortado à mão.
- [ ] **0.2** Reorganizar o repositório: `motor/` (Python), `app/` (C#), `site/` (Astro), `exe/` (o Katharos.exe atual, até a fase 3).
- [ ] **0.3** Protótipo do Velopack: um app vazio em .NET 10 empacotado com `vpk pack`, publicado numa release de teste, instalado num
  Windows limpo, atualizado de 0.0.1 para 0.0.2 por diferença. Medir o tamanho do instalador e da diferença.
- [ ] **0.4** Protótipo Avalonia 11 + Native AOT: uma tela no visual do Katharos (escuro, âmbar), texto com acentos, escala de 100 % a 200 %,
  leitor de tela (Narrador) e o tamanho do executável. Se falhar, D2 vira WPF.
- [ ] **0.5** Protótipo do Python embutido rodando o `katharos.py` (sem pip, sem rede) e o `katharos.ps1` achando esse Python.
- [ ] **0.6** Protótipo do site: Astro + shadcn/ui + Magic UI no GitHub Pages, com a primeira dobra do site atual reproduzida, para medir
  peso (meta: abaixo de 200 KB de JavaScript na primeira carga) e Lighthouse (meta: 90+ em desempenho e 100 em acessibilidade).
- [ ] **0.7** Registrar as decisões confirmadas (ou trocadas) neste arquivo e no cofre do Obsidian (`04 • Decisions`), com a pesquisa em
  `03 • Research`.

### Fase 1: motor com API
- [ ] **1.1** Fechar o protocolo (seção 2) e escrever `motor/api.py` (`katharos api`), sem mudar o comportamento de nenhum comando.
- [ ] **1.2** Métodos de leitura: `versao`, `perfil`, `raiox`, `medir`, `areas`, `itens` (com "já feito", nível, ganho, custo e "varia"),
  `explicar`, `plano`, `aplicado`, `conselheiro`, `painel_dados`, `sessoes`, `config_*`.
- [ ] **1.3** Métodos que mudam o PC (`aplicar`, `desfazer`, `pontos`, `verificar`) com eventos de progresso, cancelamento seguro entre itens
  e o mesmo backup do desfazer de hoje. Rodam só no motor elevado.
- [ ] **1.4** Motor elevado: cópia conferida por hash para `%ProgramData%\Katharos`, pipe com nome e ACL só do usuário, encerra sozinho
  quando o aplicativo fecha.
- [ ] **1.5** Testes: cada método com PC modelo; contrato do JSON congelado em arquivo (`tests/api/*.json`) para a interface e o motor não
  se desencontrarem.

### Fase 2: o aplicativo com janelas (Katharos.App)
Telas, na ordem do uso real (o raio-x primeiro, como na CLI):
- [ ] **2.1** Casca: janela, navegação lateral, tema do site, ícone da marca, fontes, escala de DPI, teclado (tudo alcançável sem mouse).
- [ ] **2.2** **Início**: nota do PC, o próximo passo recomendado (o mesmo da abertura da CLI), atalhos para raio-x e otimizar.
- [ ] **2.3** **Raio-x**: o diagnóstico com os achados por gravidade e o "o que fazer" de cada um, com botão que leva ao item certo.
- [ ] **2.4** **Otimizar**: os três modos (seguro, equilibrado, extremo) e, embaixo, as áreas com **todos os itens**, cada um com o que faz,
  o que ganha, o que perde e **"já feito"** conferido na hora. Marcar ou desmarcar item por item é obrigatório (regra do usuário, 10 nov).
  Antes de aplicar: a lista final do que vai mudar. Durante: progresso por item. Depois: o que ficou feito e o que falhou.
- [ ] **2.5** **Ao vivo**: as métricas do segundo plano em tamanho grande (CPU, GPU, RAM, temperatura, disco, rede), gráfico de minutos e o
  que está no limite agora.
- [ ] **2.6** **Jogos**: as sessões gravadas e o que segurou cada uma.
- [ ] **2.7** **Central de inteligência**: as propostas com o número que as justifica, botão para executar (pede confirmação) e dispensar.
- [ ] **2.8** **Histórico** (substitui o painel em HTML, D8): agora, o que está mudando (tendência), evolução (espaço, RAM, boot, CPU,
  temperatura) com as marcas de quando cada pacote foi aplicado, temperatura por hora do dia, consumo, provas de ganho, benchmark ao
  longo do tempo e saúde do Windows. Mesmos números que o painel de hoje (teste comparando com `monta_painel`).
- [ ] **2.8b** Tirar o painel em HTML: `painel` na CLI abre esta tela ou mostra o resumo no terminal; remover `64-painel.py`/`64-termica.py`
  da saída HTML e os cliques `katharos://` do HTML (o protocolo passa a abrir telas do aplicativo).
- [ ] **2.9** **Desfazer**: os pacotes com backup, o ponto de restauração "Antes do Katharos" e desfazer tudo.
- [ ] **2.10** **Configurações**: modo padrão, ritmo do segundo plano, avisos, jogo aberto, iniciar com o Windows, atualizações.
- [ ] **2.11** O aviso de uso (o mesmo aceite da CLI) na primeira abertura.
- [ ] **2.12** Testes de interface (Avalonia.Headless) por tela e uma foto de cada tela gerada no CI, como a `--foto` de hoje.
- [ ] **2.13** Primeira abertura guiada (D9) e teste de usabilidade com 3 pessoas leigas; corrigir o que travou.

### Fase 2b: raio-x mais completo e otimizações guiadas por evidência
A ideia: o raio-x acha o problema com prova (número, de onde veio), e a otimização só propõe o item que resolve aquele problema. A leitura
nova é feita em C# (preferência do usuário: mais rápida), e o motor recebe o resultado.

Raio-x, novas leituras (cada uma vira achado com gravidade, prova e o item ou a instrução que resolve):
- [ ] **2b.1** **Monitor abaixo da taxa máxima** (ex.: monitor de 144 Hz rodando em 60 Hz): `EnumDisplaySettings` lista os modos; é um dos
  ganhos mais comuns e mais fáceis. Item novo: usar a taxa máxima (desfaz voltando à anterior).
- [ ] **2b.2** **Memória abaixo da velocidade** (XMP/EXPO desligado): velocidade configurada x velocidade do pente (WMI
  `Win32_PhysicalMemory`). Não dá para ligar pelo Windows: o achado explica como ligar na BIOS, com o nome certo para Intel e AMD.
- [ ] **2b.3** **Memória em canal único** (um pente só ou pentes nos slots errados): reduz FPS em jogos que dependem de CPU.
- [ ] **2b.4** **Integridade de memória (VBS/HVCI) ligada**: custa FPS em alguns PCs. Achado com o custo e o risco de desligar (segurança);
  item só no extremo, com aviso claro, e sempre desfazível.
- [ ] **2b.5** **Driver de vídeo velho** (data da versão): instrução para atualizar pelo site do fabricante (o Katharos não instala driver).
- [ ] **2b.6** **Resizable BAR e agendamento de GPU** (estado atual), **plano de energia** e **modo de jogo**: hoje parte disso está nos
  itens; o raio-x passa a mostrar o estado e o que muda.
- [ ] **2b.7** **Arquivo de paginação num HD** quando há SSD, **disco do sistema quase cheio**, **SSD com desgaste** (SMART, já existe:
  integrar à tela nova).
- [ ] **2b.8** **CPU freando, calor, RAM e disco no limite durante jogos**: vêm das sessões do segundo plano (já gravadas) e entram no
  raio-x como achados com o tempo medido.
- [ ] **2b.9** **Programas que mais pesam ao iniciar** com o impacto medido (tempo de boot por programa, do log do Windows).
- [ ] **2b.10** Nota do raio-x explicada: de onde vem cada ponto perdido e quanto cada correção devolve.

Otimizações:
- [ ] **2b.11** **Plano por evidência**: o turbo e a tela Otimizar marcam primeiro o que o raio-x e o segundo plano provaram que pesa
  (ex.: CPU segurando os jogos → menos processos e energia no máximo; calor → plano fresco e limpeza; RAM cheia → inicialização).
- [ ] **2b.12** **Medir antes e depois de verdade** em toda aplicação feita pela interface (boot, RAM livre, processos, e o ganho nas
  sessões de jogo seguintes), mostrado na tela e guardado nas provas.
- [ ] **2b.13** Itens novos que os achados pedem: taxa máxima do monitor (2b.1), integridade de memória (2b.4, só extremo), economia de
  energia do adaptador de rede e do USB em PC de mesa, efeitos visuais por perfil de hardware fraco.
- [ ] **2b.14** Revisar os 176 itens: tirar o que não dá ganho medido nas provas, juntar os parecidos, e reescrever o texto de cada um no
  formato de três linhas (D9).

### Fase 2c: prova em jogo
Pedido de 10 nov: provar o ganho com número que gamer entende, e com o PC real. Pode começar antes da interface (o Katharos.exe de hoje
já tem o segundo plano e as sessões); o que for tela entra nas telas Ao vivo, Jogos e Histórico da fase 2.

Teste no PC real (primeiro, antes de tudo o que vem abaixo):
- [ ] **2c.1** Roteiro de teste no kesslerupc, com a pessoa jogando: `Katharos.exe --sensores` com o MSI Afterburner aberto (temperatura da
  CPU), ícone e painel ao vivo, sessão de jogo gravada e o limite certo (comparar com o que o Afterburner mostra), migração do acompanhamento
  contínuo, aviso do SmartScreen, pausar, ritmo, sair e voltar no próximo início do Windows.
- [ ] **2c.2** Anotar o resultado de cada ponto (funcionou, falhou, com print) na ficha do kesslerupc no cofre e corrigir o que falhar,
  com teste novo para cada falha.

FPS de verdade:
- [ ] **2c.3** Pesquisar e decidir a captura de FPS: PresentMon (Intel, código aberto, MIT) pelos eventos do Windows (ETW), como o CapFrameX
  faz. Confirmar antes: se precisa de administrador ou só do grupo "Usuários de log de desempenho", se algum anti-cheat (Vanguard, FACEIT,
  EAC, BattlEye) reclama, o custo de CPU e o tamanho. Sem confirmação de que é seguro com anti-cheat, não entra.
- [ ] **2c.4** Medir no segundo plano, só durante a sessão de jogo: FPS médio, 1 % e 0,1 % mais baixos, tempo de quadro (média e
  variação), e as travadas (quadros acima de 2x a média). Nunca abre o processo do jogo: só lê os eventos de apresentação do Windows.
- [ ] **2c.5** Gravar na sessão (`sessoes.jsonl`) e no minuto (`minutos.jsonl`), mostrar no painel ao vivo (FPS e tempo de quadro em
  gráfico) e cruzar com os limites: "FPS caiu quando a CPU freou" vira conclusão.

Antes e depois por jogo:
- [ ] **2c.6** A central compara as sessões do mesmo jogo antes e depois de cada mudança (pacote aplicado, turbo, troca de modo), com
  pelo menos 3 sessões de cada lado e duração parecida, e diz o resultado em número: FPS médio, 1 % low, travadas, temperatura, limite.
  Diferença menor que a variação entre sessões vira "sem diferença" (mesma regra da prova de ganho).
- [ ] **2c.7** Entra nas provas (`provas.jsonl`) por item e por rodada, no Histórico da interface e no `aovivo`. Vale para qualquer jogo
  detectado, sem nada específico de um jogo.
- [ ] **2c.8** Se a mudança piorou o jogo, a central propõe desfazer aquela área, com o número que mostra a piora.

Travadas por driver:
- [ ] **2c.9** Medir a latência de DPC e de interrupção por driver (o que o LatencyMon faz), pelos eventos do kernel do Windows (ETW), num
  teste de 1 a 2 minutos que a pessoa pede (`travadas` ou um botão), não o tempo todo. Precisa de administrador.
- [ ] **2c.10** Dizer o culpado em linguagem simples: "o driver de rede (ndis.sys) segura o processador por 2 ms; atualize o driver da
  placa de rede pelo site do fabricante", com o que fazer para os culpados comuns (rede, Wi-Fi, áudio, armazenamento, ACPI, placa de vídeo).
- [ ] **2c.11** Rodar sozinho uma vez quando a sessão de jogo tiver travadas sem nenhum limite (CPU, GPU, RAM, disco e calor normais) e
  entrar no raio-x como achado.

Notebook na tomada e na bateria (**desligado por padrão: só funciona se a pessoa ligar**):
- [ ] **2c.12** Opção "trocar o perfil sozinho na tomada e na bateria", desligada até a pessoa ligar (na interface, nas Configurações e
  na primeira abertura num notebook, com uma frase do que faz; na CLI, `config energia-automatica sim`). Só aparece em notebook.
- [ ] **2c.13** Na tomada: o perfil de desempenho do modo escolhido. Na bateria: economia (plano equilibrado ou economia de energia,
  processador com teto mais baixo, brilho e efeitos como a pessoa definir). O segundo plano percebe a troca na hora e aplica.
- [ ] **2c.14** Mostrar a troca (aviso discreto no ícone: "na bateria: economia") e permitir travar um perfil por um tempo ("manter
  desempenho por 1 hora na bateria").
- [ ] **2c.15** Tudo pelo `powercfg` e pelo que o pacote energia já guarda para desfazer; desligar a opção volta o plano de antes.

### Fase 3: o segundo plano dentro do aplicativo
- [ ] **3.1** Levar o código de `exe/Katharos.cs` (leitura, regras, sessões, minutos, ícone, painel ao vivo, sensores externos) para o
  aplicativo, como um modo `--segundo-plano` do mesmo executável. Mantém os formatos de `agora.json`, `minutos.jsonl` e `sessoes.jsonl`.
- [ ] **3.2** O painel ao vivo do ícone vira uma janela pequena do Avalonia, no visual da nova interface.
- [ ] **3.3** Manter os testes anti-ban (nenhuma API que abra, leia ou injete em processo de jogo) apontando para o código novo.
- [ ] **3.4** A versão CLI continua com o `Katharos.exe` atual (ou passa a usar o mesmo projeto compilado em modo leve: decidir aqui).

### Fase 4: instalador e atualização
- [ ] **4.1** `vpk pack` com o aplicativo, o motor e o Python embutido; atalho no menu Iniciar e na área de trabalho; desinstalação que
  pergunta se apaga `~/.katharos` (por padrão, não apaga: são os backups do desfazer).
- [ ] **4.2** Atualização: confere ao abrir e uma vez por dia (o segundo plano faz isso em silêncio), baixa a diferença, avisa "versão X
  pronta, reinicie" e aplica. Configurável: automático, avisar ou nunca. Nunca atualiza no meio de uma aplicação (trava enquanto o motor
  elevado estiver ocupado).
- [ ] **4.3** Ao atualizar, rodar a migração de dados que já existe (`68-versoes.py`) e reabrir o segundo plano.
- [ ] **4.4** Canais: `estavel` (padrão) e `previa` (para testar antes).
- [ ] **4.5** CLI: `katharos atualizar` baixa a release pelo PowerShell, confere o hash pela lista da release, troca os arquivos e guarda a
  versão anterior para voltar (`katharos atualizar --voltar`).

### Fase 5: publicação e assinatura
- [ ] **5.1** Workflow `publicar`: compila o aplicativo (Windows), roda os testes do motor e da interface, `vpk pack`, monta o zip da CLI,
  sobe tudo na mesma release (`Katharos-Setup.exe`, pacotes do Velopack, `Katharos.zip`, `katharos.py`, somas) com atestado do GitHub.
- [ ] **5.2** Ensaio que instala e atualiza num Windows do CI (de verdade, da versão anterior para a nova).
- [ ] **5.3** Pedido à SignPath Foundation (o usuário envia; aqui fica o texto do pedido e a política de assinatura publicada no site).
- [ ] **5.4** Ligar a assinatura no workflow quando aprovada (o `Setup.exe`, o aplicativo e o `Katharos.exe` da CLI).

### Fase 6: site novo
- [ ] **6.1** `site/` com Astro, Tailwind v4, shadcn/ui e Magic UI; tokens do site atual (cores, fontes, espaçamentos) num só lugar.
- [ ] **6.2** Dados gerados do motor: modos, áreas e itens, contagens, novidades do changelog, versão (substitui o `gera_site.py`).
- [ ] **6.3** Seções na ordem de hoje, refeitas com componentes: abertura (cavaleiro intacto), como usar, painel (exemplo vivo com números
  contando e gráficos), modos, tudo o que ele faz (filtro por modo, acordeão por área), jogos, limites, FAQ, novidades, contribuir.
- [ ] **6.4** **Baixar**: escolha entre "Com janelas (recomendado)" e "Terminal (CLI)", com tamanho, o que vem em cada um e como conferir a
  assinatura. Detecta Windows e mostra a versão atual lida das releases no build.
- [ ] **6.5** Página do segundo plano e da central de inteligência (o que lê, quanto pesa, anti-cheat).
- [ ] **6.6** Revisão crítica: comparar com sites de referência, cortar texto e animação que não serve, conferir no celular, Lighthouse e
  leitor de tela.
- [ ] **6.7** Deploy pelo Actions no GitHub Pages; manter o endereço `kessleru.github.io/Katharos` e redirecionar âncoras antigas.

### Fase 7: lançamento
- [ ] **7.1** Quem usa a CLI: o `katharos` avisa uma vez que existe a versão com janelas e que os dados são os mesmos (`~/.katharos`).
- [ ] **7.2** README, CONTRIBUTING, SECURITY e CHANGELOG atualizados; versão **4.0.0** (produto novo e troca na distribuição).
- [ ] **7.3** Conferência final: instalar do zero num Windows limpo, atualizar de uma versão anterior, desinstalar, e o mesmo para a CLI.

---

## 4. Critérios de pronto
- Cada fase só fecha com testes passando no CI (Python, interface e Windows de verdade) e com o que mudou anotado no Registro.
- Instalador: instala sem administrador, abre em menos de 2 s num SSD, atualiza por diferença, desinstala limpo.
- Interface: tudo o que a CLI faz de comum (raio-x, otimizar item por item, desfazer, ao vivo, central) funciona sem abrir o terminal.
- Site: Lighthouse 90+ em desempenho e 100 em acessibilidade, sem animação que trave, no celular e no computador.
- Nenhuma regra antiga quebra: mostra antes de mudar, desfaz tudo, ponto de restauração, nada específico de jogo, nada que dê ban.

## 5. Riscos
- **SmartScreen sem assinatura** assusta na primeira instalação. Mitigação: SignPath (fase 5), texto claro no site, atestado do GitHub.
- **Antivírus** costuma desconfiar de instalador novo sem assinatura. Mitigação: assinar, enviar o arquivo para análise da Microsoft
  (Defender) a cada versão maior.
- **Avalonia com AOT**: algo de reflexão pode quebrar no corte do AOT. Mitigação: bindings compilados e o protótipo 0.4; plano B é WPF.
- **Duas interfaces (CLI e janelas) divergirem**. Mitigação: a lógica fica toda no motor; o contrato do JSON é testado nos dois lados.
- **Python embutido** desatualizado com falha de segurança. Mitigação: a versão vem fixada no build e sobe a cada release do Python.
- **Tamanho do site** com bibliotecas de componentes. Mitigação: ilhas do Astro, só o que é usado, meta de peso na fase 0.

## 6. Regras que continuam valendo
- Mostrar cada mudança antes, desfazer tudo, ponto de restauração, nunca mexer em arquivo pessoal sem desfazer.
- Só três modos (seguro, equilibrado, extremo), com jogos dentro de cada um; escolher item por item sempre possível.
- Nada específico por jogo; nada que abra, leia ou injete em processo de jogo; nada de driver de sensor (anti-cheat).
- O Python do motor não acessa a rede: download fica com o PowerShell ou com o C#.
- Commits sem linha de coautoria. Versões pela regra MAIOR.MENOR.CORREÇÃO do CHANGELOG. Cada release conferida (tag, hashes, download).

## 7. Fontes
- [Velopack no NuGet](https://www.nuget.org/packages/Velopack), [atualizações por diferença](https://docs.velopack.io/packaging/deltas)
- [Opções de assinatura da Microsoft](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options),
  [termos da SignPath Foundation](https://signpath.org/terms)
- [Avalonia x WinUI 3](https://avaloniaui.net/winui-compare), [MAUI x Avalonia x Uno em 2026](https://startdebugging.net/2026/05/maui-vs-avalonia-vs-uno-in-2026/)
- [shadcn/ui no Astro](https://ui.shadcn.com/docs/installation/astro), [Magic UI no Astro](https://v3.magicui.design/docs/installation/astro)
- [MCP do shadcn/ui](https://mcpservers.org/servers/shadcn-mcp-server), [MCP do Magic UI](https://mcp.directory/servers/magic-ui),
  [21st.dev Magic MCP (pago)](https://mcp.directory/blog/21st-dev-magic-mcp-complete-guide-2026), [React Bits MCP (Pro)](https://pro.reactbits.dev/docs/mcp)

---

## Registro

| data | tarefa | versão | commit | nota |
|---|---|---|---|---|
| 10 nov 2026 | plano escrito | 3.1.2 | (este commit) | pesquisa: Velopack, Avalonia/WPF, assinatura, Astro + shadcn + Magic UI |
| 10 nov 2026 | plano ampliado: painel dentro da interface (D8), fácil para leigos (D9), fase 2b (raio-x e otimizações) | 3.1.2 | 5380a0f | pedido do usuário |
| 10 nov 2026 | bibliotecas de referência grátis no lugar do Magic (21st.dev) | 3.1.2 | 960b503 | shadcn MCP, Magic UI MCP, React Bits, Aceternity, Context7 |
| 10 nov 2026 | fase 2c: teste no PC real, FPS de verdade, antes e depois por jogo, travadas por driver | 3.1.2 | 014ff01 | pedido do usuário (itens 1, 2, 3 e 5 das sugestões) |
| 10 nov 2026 | 2c.12 a 2c.15: notebook na tomada e na bateria, desligado por padrão | 3.1.2 | (local, sem commit) | pedido do usuário (item 6); não publicar |
