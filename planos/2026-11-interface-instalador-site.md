# Plano: interface gráfica, instalador com atualização e site novo

Pedido de 10 nov 2026: uma interface gráfica em C#, **bem fácil de entender para qualquer pessoa**, um instalador, atualização sem baixar de
novo a cada versão, a escolha entre a versão com janelas e a de terminal no site, e um site novo feito com bibliotecas de componentes, mais
vivo. Junto: **o painel sai do HTML e vai para dentro da interface**, e melhorias no raio-x e nas otimizações. Este arquivo é o plano e o registro:
cada tarefa tem um código; quando ficar pronta, marque `[x]`, anote no **Registro** (fim do arquivo) a data, a versão e o commit.

**Estado:** em andamento no ramo `v4` do GitHub (backup e ensaios no Windows do CI); nada vai para a `main` nem vira release até a **4.0.0**, que sai de uma vez com tudo.

| fase | o quê | estado |
|---|---|---|
| 0 | fontes no repositório, protótipos e decisões confirmadas | a fazer |
| 1 | motor com API (o Python conversa com a interface por JSON) | a fazer |
| 1b | motor de inteligência novo: memória do PC, linha de base, detectores, causa, planejador, avaliador, eventos | a fazer |
| 2 | o aplicativo com janelas (Katharos.App), com o painel dentro dele | a fazer |
| 2b | raio-x mais completo e otimizações guiadas por evidência | a fazer |
| 2c | prova em jogo: teste no PC real, FPS de verdade, antes e depois por jogo, travadas por driver; notebook na tomada e na bateria | a fazer |
| 2d | funcionar bem em todas as versões do Windows 10 e 11 (e edições) | em andamento |
| 2e | medidas e benchmarks fiéis: tirar o efeito de fatores externos | a fazer |
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

### D10. Um motor de inteligência só, que aprende com este PC
Pedido de 10 nov: melhorar o motor de inteligência (a "central") e como ele conversa com tudo.

Hoje: a central é uma lista de regras em Python que lê um dicionário montado na hora e devolve propostas com confiança escrita à mão; o
segundo plano em C# tem outras regras, com os mesmos limites duplicados; os limites são fixos para qualquer PC; o aprendizado é só o antes
e depois de um pacote; a comunicação é por arquivo e o ícone chama o Python escondido a cada hora; achado, causa e ação ficam soltos.

O motor novo:
- **Memória do PC** num banco **SQLite** local (Python tem `sqlite3` nativo; o C# do .NET 10 usa Microsoft.Data.Sqlite): fatos, sessões,
  minutos, mudanças, provas, achados, propostas, previsões, resultados e as respostas da pessoa. Uma fonte só para o ícone, a interface,
  a CLI e o motor. Os arquivos de hoje (`horas.jsonl`, `minutos.jsonl`, `sessoes.jsonl`, `provas.jsonl`...) migram para ele, com
  exportação para JSON para quem quiser ver.
- **Fato** é a unidade: métrica, valor, unidade, quando, de onde veio (sensor e confiança da fonte) e contexto (repouso, jogo, bateria,
  hora do dia, modo aplicado).
- **Cinco camadas**: linha de base → detectores → diagnóstico de causa → planejador → avaliador, com o avaliador realimentando os pesos.
- **Regras como dados**: limites, janelas, duração mínima, textos e ações num arquivo (`REGRAS_MOTOR` no Python; a montagem grava `exe/regras.json`, embutido no exe, e o Katharos grava `~/.katharos/regras.json`) lido pelo C# e pelo Python.
  Nunca mais um limite duplicado em código.
- **Eventos em vez de relógio**: o segundo plano e a interface avisam o motor por um pipe local; o motor pensa quando algo acontece.
- **Honestidade acima de tudo**: cada conclusão com os números e a fonte; pouco dado vira "ainda não sei"; aviso falso é bug.
- **Tudo no PC**: sem rede e sem modelo de IA externo; as explicações saem de modelos de texto preenchidos com os números reais.

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
- [x] **0.1** Pôr `partes/` (as fontes do `katharos.py`), `arte/` (gerador e modelo do site) e o script de montagem no repositório, com um
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

### Fase 1b: motor de inteligência (D10)
Arquitetura, em ordem de dependência. As tarefas I1 a I6 dá para fazer antes da interface (melhoram o ícone e a CLI de hoje).

```
 sensores (Katharos.exe, raio-x, PowerShell, PresentMon da fase 2c)
        │  fatos: métrica, valor, quando, fonte, contexto
        ▼
 memória do PC (SQLite: fatos, sessões, mudanças, provas, achados, propostas, previsões, resultados, respostas)
        │
        ▼
 linha de base ─▶ detectores ─▶ diagnóstico de causa ─▶ planejador ─▶ avaliador
   o normal        limite,         achados viram uma      ações com        mede o
   deste PC        tendência,      causa provável,        ganho previsto   resultado e
                   anomalia,       com o porquê           e risco          ajusta os pesos
                   piora pós-mudança                                            │
        ▲                                                                       │
        └─────────────────────────── aprende ◀─────────────────────────────────┘
 eventos (pipe local): sessão começou/terminou, limite sustentado, aplicou, desfez, driver mudou, Windows atualizou, bateria
 consumidores: ícone, interface, CLI (pela API da fase 1), notificações
```

Ajustes imediatos (antes da interface):
- [x] **I1** **Regras como dados**: tirar os limites do `Katharos.cs` (`Regras`) e do `conselheiro` para `motor/regras.json`
  (métrica, condição, janela, duração mínima, nível, título, texto, comando). O C# e o Python leem o mesmo arquivo; um teste falha se um
  limite aparecer escrito no código.
- [x] **I2** **Pensar por evento**: no fim de cada sessão de jogo, depois de aplicar ou desfazer, ao mudar de driver ou depois de uma
  atualização do Windows, o segundo plano chama o motor (`katharos conselheiro --exportar` hoje; o pipe depois). Sai o relógio de 1 hora.
- [x] **I3** **Linha de base por PC**: mediana e dispersão robusta (MAD) de cada métrica por contexto (repouso, jogo, bateria, faixa do
  dia), recalculada por dia, com pelo menos 3 dias de dado antes de usar. "Fora do normal deste PC" substitui os limites fixos de RAM,
  CPU, disco e rede; calor continua com limite absoluto de segurança.
- [x] **I4** **Confiança calculada**: a partir do número de amostras, da duração, de em quantas sessões ou dias se repetiu e da
  confiança da fonte (sensor de verdade x zona térmica). Faixas: "ainda não sei", baixa, média, alta. Pouco dado nunca vira alarme.
- [x] **I5** **Previsão e resultado**: cada proposta e cada item aplicado guardam o que se espera (ex.: −5 °C em jogo, +5 a 10 % no 1 %
  low, −8 s de boot); o avaliador compara com o resultado medido e grava nas provas.
- [x] **I6** **"Ajudou?"** no painel do ícone e na CLI (`conselheiro --resposta ID sim|nao|nao-importa`). "Não me importa" para de propor
  aquilo; "não ajudou" baixa o peso do item neste PC.

Motor novo:
- [ ] **I7** **Memória do PC em SQLite** (`~/.katharos/katharos.db`): esquema versionado (a migração entra no `68-versoes.py`), escrita
  só pelo motor e pelo segundo plano (um escritor por tabela), leitura por todos; importação dos `.jsonl` de hoje; `exportar` para JSON.
- [ ] **I8** **Detectores** como módulos pequenos, cada um com teste: limite sustentado (gargalo de GPU, CPU, freio, RAM, VRAM, disco,
  calor), tendência (piorando há dias), anomalia (fora da linha de base), piora depois de uma mudança, evento do Windows (tela azul,
  driver, disco), FPS e travadas (fase 2c). Saída: **achado** com números, duração, contexto, fonte e confiança.
- [ ] **I9** **Diagnóstico de causa**: um mapa de conhecimento em dados (`motor/causas.json`): sintoma → causas possíveis → o que confirma
  ou descarta cada uma → ação. Ex.: FPS cai + CPU freando + temperatura ≥ limite → calor; CPU freando + bateria → economia de energia;
  travadas + nenhum limite → driver (teste de DPC da fase 2c). Pontua as causas pelas evidências e explica a escolhida e as descartadas.
- [ ] **I10** **Planejador**: escolhe as ações pelo ganho esperado (peso do item neste PC x confiança da causa) contra o risco, respeitando
  modo, itens protegidos, o que já está feito (`item.definitivo`), conflitos e a regra "nada específico de jogo". Cada proposta sai com
  previsão, risco, como desfazer e o número que a justifica.
- [ ] **I11** **Avaliador**: compara previsão e resultado com janelas comparáveis (mesmo contexto, sessões de duração parecida, pelo
  menos 3 de cada lado), separa ruído de efeito pela variação (mesma regra da prova de ganho), atualiza o peso do item neste PC e propõe
  desfazer quando piorou.
- [ ] **I12** **Eventos**: pipe local com nome e ACL do usuário; o segundo plano publica, o motor assina e responde; a interface e o ícone
  assinam as conclusões. Fila em disco para eventos que chegam com o motor fechado.
- [ ] **I13** **Explicações**: modelos de texto por achado, causa e proposta, preenchidos com os números reais; sempre "o que eu vi",
  "por que acho que é isso", "o que eu faria", "o que mudaria minha conclusão". Linguagem do dia a dia (D9).
- [ ] **I14** **Testes com dados reais**: gravar sessões e semanas de dado de PCs de verdade (anonimizados: só números), reproduzir no
  teste e conferir que o motor conclui o mesmo; um teste por aviso falso já visto (inicialização cheia, PC de empresa, sem sensor). Medir
  a taxa de aviso falso a cada versão.
- [ ] **I15** **Orçamento de avisos**: no máximo um aviso por tipo a cada X horas (configurável), nada durante o jogo salvo calor grave,
  e um resumo diário opcional em vez de vários avisos soltos.

O que o motor faz na interface (liga com a fase 2):
- [ ] **I16** **Início**: a frase principal sai do motor ("seu PC está bem; o que mais pesa é o calor em jogo") com um botão para a ação
  que mais rende, a previsão do ganho e o caminho para desfazer.
- [ ] **I17** **Central de inteligência (tela)**: propostas em cartões por prioridade, cada uma com o que eu vi (gráfico pequeno do
  dado), por que acho que é isso (causas, com as descartadas), o que eu faria, quanto espero ganhar, risco, "aplicar", "agora não",
  "não me importa" e "ajudou?" depois de aplicar.
- [ ] **I18** **Resultado das propostas**: linha do tempo com o que foi aplicado, a previsão e o que aconteceu de verdade (verde, cinza
  ou vermelho), e o botão desfazer onde piorou.
- [ ] **I19** **Ao vivo**: as conclusões de agora vindas do motor (as mesmas regras do ícone), com o porquê ao passar o mouse, e o "normal
  deste PC" desenhado como faixa nos gráficos.
- [ ] **I20** **Jogos**: por jogo detectado, o que segura o FPS, a evolução de FPS e travadas entre sessões, o antes e depois de cada
  mudança (fase 2c) e a recomendação para aquele perfil de uso.
- [ ] **I21** **Raio-x**: os achados vêm dos detectores, com a nota explicada (de onde vem cada ponto perdido e quanto cada correção
  devolve) e o "ainda não sei" quando falta dado.
- [ ] **I22** **Otimizar**: os itens que o motor recomenda para este PC aparecem marcados e com o motivo ("recomendado: a CPU segurou
  seus jogos em 40 % do tempo"); o modo continua decidindo o resto, e a pessoa marca o que quiser.
- [ ] **I23** **Histórico**: os gráficos com as marcas das mudanças, a linha de base e as anomalias destacadas, e a explicação de cada
  anomalia ao clicar.
- [ ] **I24** **Configurações do motor**: o que ele pode avisar, com que frequência, se pensa durante jogo, o que nunca propor, e apagar a
  memória do PC (com exportação antes).
- [ ] **I25** **Perguntar ao Katharos** (depois de tudo acima, opcional): uma caixa onde a pessoa escreve "por que meu jogo trava?" e a
  resposta sai do motor (achados, causas e propostas que batem com a pergunta, pela busca e pelos sinônimos que já existem), sem modelo de
  IA externo.

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
- [x] **2c.3** Pesquisar e decidir a captura de FPS: PresentMon (Intel, código aberto, MIT) pelos eventos do Windows (ETW), como o CapFrameX
  faz. Confirmar antes: se precisa de administrador ou só do grupo "Usuários de log de desempenho", se algum anti-cheat (Vanguard, FACEIT,
  EAC, BattlEye) reclama, o custo de CPU e o tamanho. Sem confirmação de que é seguro com anti-cheat, não entra.
- [x] **2c.4** Medir no segundo plano, só durante a sessão de jogo: FPS médio, 1 % e 0,1 % mais baixos, tempo de quadro (média e
  variação), e as travadas (quadros acima de 2x a média). Nunca abre o processo do jogo: só lê os eventos de apresentação do Windows.
- [x] **2c.5** Gravar na sessão (`sessoes.jsonl`) e no minuto (`minutos.jsonl`), mostrar no painel ao vivo (FPS e tempo de quadro em
  gráfico) e cruzar com os limites: "FPS caiu quando a CPU freou" vira conclusão.

Antes e depois por jogo:
- [x] **2c.6** A central compara as sessões do mesmo jogo antes e depois de cada mudança (pacote aplicado, turbo, troca de modo), com
  pelo menos 3 sessões de cada lado e duração parecida, e diz o resultado em número: FPS médio, 1 % low, travadas, temperatura, limite.
  Diferença menor que a variação entre sessões vira "sem diferença" (mesma regra da prova de ganho).
- [ ] **2c.7** Entra nas provas (`provas.jsonl`) por item e por rodada, no Histórico da interface e no `aovivo`. Vale para qualquer jogo
  detectado, sem nada específico de um jogo.
- [x] **2c.8** Se a mudança piorou o jogo, a central propõe desfazer aquela área, com o número que mostra a piora.

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

### Fase 2d: todas as versões do Windows 10 e 11
Pedido de 10 nov: funcionar bem principalmente no Windows 10 e no 11, em qualquer versão e edição, sabendo o que muda entre elas.

O que já se sabe (fontes na pesquisa do cofre `2026-11-10 versoes-do-windows`):
- **Fim de suporte**: Windows 11 21H2 (out/2023), 22H2 (out/2024), 23H2 (nov/2025) e **24H2 Home/Pro (13/10/2026)** já não recebem
  atualização de segurança; 24H2 Enterprise/Education vai até 12/10/2027. Windows 10 22H2 acabou em 14/10/2025, mas o **ESU de pessoa
  física foi estendido até 12/10/2027** (precisa do 22H2 em dia e de inscrição).
- **Edição muda o efeito**: "telemetria 0" só desliga de todo no Enterprise, Education e Server; no Home e no Pro vale o mínimo da edição
  (dados obrigatórios). A política "experiências do consumidor" (`DisableWindowsConsumerFeatures`) só vale no Enterprise e no Education
  desde 2016; no Home e no Pro o que funciona são as chaves por usuário do ContentDeliveryManager.
- **UCPD**: no Windows 11 24H2 (e no 10 com as atualizações de 2024) um driver da Microsoft protege alguns valores do registro; gravar o
  botão de Widgets (`TaskbarDa`) dá "acesso negado". Desligar pela política `Dsh\AllowNewsAndInterests` funciona.
- **WMIC** sai do Windows (25H2 e atualizações do 24H2): o Katharos não pode depender dele (hoje não depende; um teste garante).
- O que só existe numa versão: modo de janela otimizado para jogos (Windows 11 22H2+), Recall e Click to Do (Copilot+ e 24H2+),
  agendamento de GPU (Windows 10 2004+ e driver WDDM 2.7), Copilot como app (24H2) x botão e política (23H2 e antes).
- Edições que mudam o jogo: **S mode** (só apps da Loja: o Katharos nem roda), **LTSC** (sem Loja e sem a maioria dos apps), **Server**,
  **IoT**, **ARM64** (Python x64 roda emulado; o executável .NET roda nativo).

Tarefas:
- [x] **2d.1** Perfil de compatibilidade (`compat_windows`): família (10 ou 11), versão (21H2…25H2), build, edição normalizada (home, pro,
  empresa, educação, ltsc, server, iot, s-mode), arquitetura, se está no suporte e até quando, UCPD ligado.
- [x] **2d.2** Raio-x: achado "versão sem atualizações de segurança" com a data e o que fazer (atualizar para a versão atual; no Windows 10,
  o ESU até 12/10/2027), e aviso de versão antiga demais (antes do Windows 10 1809) com só o modo seguro.
- [x] **2d.3** Itens honestos por edição: telemetria e anúncios dizem o que de fato acontece no Home e no Pro.
- [x] **2d.4** UCPD: valor protegido não conta como "falta fazer" nem como erro; o item usa a política que funciona (Widgets).
- [x] **2d.5** Matriz de testes: o Katharos monta os itens e os scripts para perfis de Windows 10 1809, 21H2 e 22H2, Windows 11 21H2,
  22H2, 23H2, 24H2 e 25H2, nas edições Home, Pro, Enterprise, LTSC e Server, sem erro e com os itens certos em cada um.
- [ ] **2d.6** Rodar o Katharos de verdade nas versões que o GitHub oferece (Windows Server 2022 e 2025) no job `windows-real`.
- [ ] **2d.7** Ler o que mudou a cada versão nova do Windows (lista de recursos removidos e as notas de cada atualização) e anotar na
  pesquisa do cofre; virar rotina do fluxo de publicação.

### Fase 2e: medidas e benchmarks fiéis
Pedido de 10 nov: as medidas e os benchmarks precisam mostrar o efeito do Katharos, não o de um programa aberto, de o PC estar ligado há
dias ou de uma atualização rodando. Sem obrigar ninguém a fechar nada, e pedindo só quando ajuda de verdade.

O que distorce hoje: programas abertos (RAM, CPU), tempo ligado (cache, vazamento de memória), boot logo depois de atualização, Windows
Update ou Defender rodando, indexação, bateria e plano de energia, calor (o chip freia), o próprio segundo plano, e comparar um dia de
uso pesado com um de uso leve.

Tarefas:
- [x] **2e.1** **Contexto em toda medida**: junto de cada leitura e de cada benchmark, o que pode distorcer: tempo ligado, minutos desde o
  boot, quantos processos e quais os 5 que mais gastam, RAM dos programas da pessoa x RAM do sistema, Windows Update, Defender e indexação
  ativos, na bateria ou na tomada, plano de energia, temperatura, jogo aberto.
- [x] **2e.2** **Separar o sistema dos programas da pessoa**: a métrica que o Katharos promete melhorar é a do sistema (Windows, serviços,
  o que abre sozinho), não a do navegador aberto. RAM e processos passam a ter as duas partes, e a comparação usa a do sistema.
- [x] **2e.3** **Descartar leituras sujas**: minutos com atualização instalando, verificação do Defender, os primeiros 10 minutos depois do
  boot e boots logo depois de uma atualização do Windows não entram na linha de base nem na comparação (ficam guardados, marcados).
- [x] **2e.4** **Comparar o comparável**: antes e depois só entre situações parecidas (mesmo contexto, faixa de tempo ligado, de processos e
  de carga), pareando as janelas; diferença com intervalo de confiança (bootstrap) em vez de um número solto; "sem diferença" quando a
  margem engole o efeito.
- [x] **2e.5** **Benchmark em condições de bancada**: antes de medir, o Katharos confere e mostra o que vai atrapalhar (programas pesados
  abertos, atualização rodando, bateria, PC quente) e **pergunta** se a pessoa quer fechar os que ele lista (nunca fecha sozinho); espera
  a CPU ficar ociosa (ex.: abaixo de 10 % por 30 s), pausa o próprio segundo plano, faz uma rodada de aquecimento, roda várias vezes,
  usa a mediana, descarta os pontos fora da curva e diz a variação. Se a variação for grande, repete ou avisa que o resultado é fraco.
- [ ] **2e.6** **Boot medido pelo Windows**: o tempo do caminho principal do boot (evento 100 do Diagnostics-Performance), sem os boots
  logo depois de atualização; mediana dos últimos boots em vez de um só.
- [ ] **2e.7** **Prova de ganho com ensaio repetido** (onde dá): aplicar, medir, desfazer, medir, aplicar de novo, nas mesmas condições,
  para itens com efeito pequeno; o resultado diz se o ganho se repetiu.
- [ ] **2e.8** Mostrar a qualidade da medida em toda tela que mostra ganho: "medida boa" ou "medida fraca (programas pesados abertos em
  3 de 5 leituras)", com o que fazer para medir melhor.

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
Pedido de 10 nov: **mudança extrema** no site, com uma reformulação boa de verdade, **mantendo o hero** (a abertura com o cavaleiro na
grama, o título e o botão: mais ou menos a mesma pegada) e **a mesma linha de design** (escuro, osso, âmbar, gravura, linhas e "+" dos
containers). Todo o resto pode ser refeito: estrutura, ordem, componentes, interações e animações.

Ferramentas para isso (usar, não só citar):
- **Skills de design do cofre** (`Knowledge/10 • Skills`), carregadas antes de desenhar cada parte: `impeccable` (desenhar, criticar e
  polir), `design-taste-frontend` e `frontend-design` (direção visual sem cara de IA), `emil-design-eng` (acabamento e detalhes),
  `ui-ux-pro-max` (padrões de UI e UX), `animate`, `animation-performance` e `review-animations` (movimento que serve e não trava),
  `gsap-*` (se a animação pedir GSAP), `web-design-guidelines` (revisão de acessibilidade e boas práticas no fim),
  `vercel-react-best-practices` e `vercel-composition-patterns` (as ilhas em React).
- **MCPs**: shadcn/ui e Magic UI (componentes prontos, grátis), Context7 (documentação atual de Astro, Tailwind e Motion), Figma (gerar e
  testar variações de seção antes de codar, como já foi feito na cena do hero) e o navegador para conferir no celular e no computador.
- Referências de sites com a mesma ideia de arte (Hermes/Nous, kc1t e outros), com crítica: pegar o que serve, não copiar.

**Todas as seções repaginadas** (pedido de 10 nov, 19:53): repensar cada seção depois do hero; criar seções novas (ao vivo e central de
inteligência, FPS de verdade, versões do Windows, segurança, CLI x GUI) e tirar as que não fazem mais sentido. Nada fica como está só porque
já existia; o hero é a única parte que mantém a pegada.

**Vídeos do programa em uso** (pedido de 10 nov, 20:02): o site mostra o Katharos funcionando em vídeo, não só em print. Vídeos curtos
rodando sozinhos (sem som, em laço, leves), gravados da interface nova de verdade (fase 2), editados em nível profissional: cortes
limpos, zoom suave no que importa, cursor visível, ritmo rápido, nada de tela parada. No mesmo visual do site (moldura, cores e "+" dos
containers) e bem visíveis. Um para a capa (thumb do hero e prévia nas redes) e um por seção que mostra ação (raio-x, aplicar e
desfazer, painel ao vivo, central de inteligência, FPS em jogo).

**Site épico e profissional**: antes de desenhar, pesquisar o que os melhores sites de produto fazem bem (velocidade, clareza da
primeira tela, prova visual, ritmo de leitura, vídeo e movimento que servem ao conteúdo) e registrar no cofre (`03 • Research`).

Tarefas a mais desta reformulação:
- [ ] **6.R** Pesquisa de sites de produto excelentes (lançamentos de apps de desktop, ferramentas de dev, sites premiados): o que
  repetem, o que evitam, como usam vídeo sem pesar. Nota no cofre e critérios para a revisão 6.6.
- [ ] **6.V** Vídeos: roteiro de cada um (5 a 15 s), gravação da interface com dados de exemplo (o modo `--foto` vira `--video`:
  roteiro de cliques e telas, quadro a quadro, sem depender de tela real), edição com ffmpeg (zoom, cortes, moldura), saída em AV1 ou
  H.264 + WebM com poster, `preload="none"` e tocar só quando aparece na tela (sem pesar no celular nem no Lighthouse). Uma versão
  curta em GIF ou MP4 para o README.
- [ ] **6.0** Direção visual antes de codar: 2 ou 3 propostas para as seções depois do hero (rascunho no Figma ou em HTML), escolha com o
  dono e registro da escolha no cofre (`04 • Decisions`).
- [ ] **6.0b** Mapa das seções novas: o que cada uma precisa contar (baixar CLI ou GUI, o que ele faz, o painel ao vivo, a central de
  inteligência, jogos com FPS de verdade, segurança e desfazer, novidades) e o componente de cada uma.
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

## 6. Segurança do PC acima de tudo (pedido de 10 nov)
Nada que o Katharos faz pode travar o PC, dar tela azul, apagar o arquivo errado ou derrubar o processo errado. Regras:
- **Processos**: o Katharos nunca encerra processo sozinho. Quando um programa atrapalha (benchmark, RAM cheia), ele diz qual é e a
  pessoa fecha. Processos do Windows (sessão 0, `csrss`, `winlogon`, `lsass`, `svchost`, `dwm`, `explorer`…) nunca aparecem como
  "feche este". Nada de `Stop-Process`, `taskkill` ou `TerminateProcess` em código de medida (teste).
- **Arquivos**: limpeza só em caminhos da lista conhecida, nunca na raiz de um disco, nunca em pastas do sistema ou da pessoa (já
  existe: recusa caminho vazio, raiz e pastas protegidas); arquivo da pessoa vai para a Lixeira ou volta com desfazer; nada de apagar
  por padrão amplo (`*.*` numa pasta inteira) fora dos caches conhecidos.
- **O que pode dar tela azul ou não ligar**: nada de driver, BCD (`bcdedit`), modo de inicialização, assinatura de driver, memória
  virtual, serviços críticos (lista fixa no código, com teste), registro de classes de dispositivo, ou desligar proteções (lista
  `PROIBIDO` dos testes). Ponto de restauração antes de qualquer pacote e desfazer exato de cada valor.
- **Serviço desligado**: só se o PC não usa o recurso (o perfil confirma) e sempre com volta no desfazer; serviços dos quais o Windows
  depende para ligar, logar, atualizar ou proteger nunca entram.
- **Mudança arriscada** pergunta "manter alterações?" e desfaz sozinha se a pessoa não responder (já existe: `config confirmar`).

- [ ] **S1** Revisão de segurança antes da 4.0.0: ler todos os itens e scripts com essas regras na mão (um agente separado revisa, sem ter
  escrito o código), rodar a ida e volta de cada pacote (aplicar e desfazer) num Windows descartável do CI e comparar o registro e os
  serviços antes e depois.
- [x] **S2** Lista de processos e serviços protegidos num lugar só, usada pelo raio-x, pela memória, pelo benchmark e pela interface, com
  teste.
- [x] **S3** Segundo plano leve sem perder nada (pedido de 10 nov, 19:57): RAM pode usar, mas nunca pico de CPU nem muita coisa no mesmo
  instante. Lista de processos numa chamada só (NtQuerySystemInformation, poucos ms, sem abrir processo) no lugar do contador "Process"
  (dezenas a centenas de ms); leituras pesadas espalhadas (uma por vez no ritmo de 1 s); freio que espaça o ritmo se a leitura passar
  de 1/10 do tempo; nada pesado nos primeiros minutos depois de ligar; barra de tarefas só atualizada quando o texto muda; custo de
  cada fonte medido e gravado (`agora.json`, `katharos_cpu` em cada minuto); `--teste-custo` no Windows do CI (média < 50 ms, CPU < 2 %).

## 7. Regras que continuam valendo
- Mostrar cada mudança antes, desfazer tudo, ponto de restauração, nunca mexer em arquivo pessoal sem desfazer.
- Só três modos (seguro, equilibrado, extremo), com jogos dentro de cada um; escolher item por item sempre possível.
- Nada específico por jogo; nada que abra, leia ou injete em processo de jogo; nada de driver de sensor (anti-cheat).
- O Python do motor não acessa a rede: download fica com o PowerShell ou com o C#.
- Commits sem linha de coautoria. Versões pela regra MAIOR.MENOR.CORREÇÃO do CHANGELOG. Cada release conferida (tag, hashes, download).

## 8. Fontes
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
| 10 nov 2026 | 2c.12 a 2c.15: notebook na tomada e na bateria, desligado por padrão | 3.1.2 | d7107c3 (local) | pedido do usuário (item 6); não publicar |
| 10 nov 2026 | D10 e fase 1b: motor de inteligência novo (I1 a I25), com tudo o que ele faz na interface | 3.1.2 | (este commit, local) | pedido do usuário; não publicar |
| 10 nov 2026 | 0.1 fonte no repositório: `partes/`, `arte/gera_site.py`, `arte/site.html`, `scripts/monta.sh`, teste da soma | 3.1.2 | ramo v4 | |
| 10 nov 2026 | fase 6: mudança extrema no site mantendo o hero e a linha de design; skills do cofre e MCPs | 3.1.2 | ramo v4 | pedido do usuário |
| 10 nov 2026 | I1 regras como dados: `REGRAS_MOTOR` única, `exe/regras.json` embutido, `Lim.G()` no C#, central usando as mesmas | 3.1.2 | ramo v4 | testes: sem limite no código das Regras do exe |
| 10 nov 2026 | I2 pensar por evento (fim de sessão no exe; depois de aplicar e desfazer no Katharos; relógio vira reserva de 6 h) | 3.1.2 | ramo v4 | |
| 10 nov 2026 | I3 linha de base por PC (`65-motor.py`, `linha-de-base.json`, faixa do normal nos gráficos do ícone, regra "fora do normal deste PC") | 3.1.2 | ramo v4 | |
| 10 nov 2026 | I4 confiança pelos dados (uma sessão só não conclui nada); I5 previsão x resultado (`conselheiro_feitos`, "o que eu previ e o que aconteceu"); I6 "ajudou?" e "não me importa" no ícone e na CLI | 3.1.2 | ramo v4 | |
| 10 nov 2026 | fases 2d (versões do Windows) e 2e (medidas fiéis) no plano | 3.1.2 | ramo v4 | pedidos do usuário |
| 10 nov 2026 | 2d.1 a 2d.5: `28-windows.py` (versões, fim de suporte, edição, UCPD, arquitetura), aviso no raio-x, só modo seguro em build antiga e Server, telemetria e anúncios honestos por edição, `Set-Valor` ciente do UCPD, matriz de testes (8 builds x 5 edições), sem WMIC | 3.1.2 | ramo v4 | |
| 10 nov 2026 | 2e.1 a 2e.5: contexto em cada minuto (tempo ligado, processos, RAM do sistema x da conta, manutenção, top 5), minuto sujo fora da conta, diferença com margem (bootstrap), benchmark com bancada (mostra, pede, espera a CPU, pausa o segundo plano; nunca fecha nada) | 3.1.2 | ramo v4 | |
| 10 nov 2026 | seção de segurança do PC (S1, S2) no plano | 3.1.2 | ramo v4 | pedido do usuário |
| 10 nov 2026 | S2 lista única de processos protegidos (`NUNCA_ENCERRAR` em `28-windows.py`, ampliada) e `pode_sugerir_fechar`; a bancada do benchmark só sugere fechar programa da pessoa | 3.1.2 | ramo v4 | |
| 10 nov 2026 | 2c.3 a 2c.6 e 2c.8: FPS pelo PresentMon (Intel, MIT, v2.6.0 fixa no zip), só durante a sessão de jogo; média, 1% low e 0,1% low (média dos quadros mais lentos), travadas; permissão pelo grupo Usuários de log de desempenho com confirmação e volta; FPS no ícone, no `aovivo`, nas sessões e no painel; antes e depois por jogo com margem e proposta de desfazer quando piora | 3.1.2 | ramo v4 | autoteste `--teste-fps` |
| 10 nov 2026 | site: todas as seções repaginadas, criar e tirar seções (fase 6) | 3.1.2 | ramo v4 | pedido do usuário |
| 10 nov 2026 | S3: segundo plano leve (processos numa chamada só, leituras espalhadas, freio de 1/10, custo medido, `--teste-custo` no CI) | 3.1.2 | ramo v4 | testes 304 |
| 10 nov 2026 | site: vídeos do programa em uso, editados, e pesquisa de sites de produto excelentes (6.R, 6.V) | 3.1.2 | ramo v4 | pedido do usuário |
