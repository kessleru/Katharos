# Plano: personalização, otimização, relatório com envio e proteção do projeto

Pedido de 11 nov 2026: mais otimização, **muito mais personalização do Windows** com prévia em imagem e vídeo (hospedada fora do programa),
melhorias de interface, segurança e bugs, **relatório completo com envio direto ao dono** e aviso claro de que o projeto **não tem fins
lucrativos**. Personalizações funcionais e sem problemas. Só entra o que dá para fazer hoje.

Marque `[x]` ao concluir e anote no **Registro** (fim) a data, a versão e o commit. Pesquisa de apoio: [cofre/2026-11-11-pesquisa-personalizacao.md](cofre/2026-11-11-pesquisa-personalizacao.md).

**Estado:** planejado, nada começou.

| fase | versão | o quê |
|---|---|---|
| 0 | — | confirmar no Windows do CI as chaves, o Windhawk e o PowerToys |
| 1 | 4.1.0 | antivírus, proteção jurídica, bugs |
| 2 | 4.1.0 | relatório completo com envio |
| 3 | 4.2.0 | personalização nativa com galeria |
| 4 | 4.3.0 | estilos prontos, PowerToys, Windhawk |
| 5 | 4.4.0 | otimizações novas e perfis automáticos |
| 6 | 4.5.0 | interface |

---

## 1. Decisões

**P1. Personalização fica fora dos três modos.** Seguro, equilibrado e extremo continuam sendo otimização. Personalização é gosto: a pessoa
abre a tela **Personalizar**, vê a prévia, marca o que quer, e tudo volta pelo Desfazer.

**P2. Caminho de cada opção, nesta ordem:**
1. **Nativo do Windows** (registro, política oficial ou atalho para Configurações): padrão; sobrevive a atualizações e é lido de volta.
2. **PowerToys** (Microsoft, código aberto): instalado pelo winget só se a pessoa pedir.
3. **Windhawk com receita:** só mods que entram apenas no shell (explorer, Iniciar, notificações). Nenhum mod de todos os processos (`*`)
   nem do `dwm.exe`.

Fora de qualquer caminho: trocar arquivo do sistema, patch de tema, fonte do sistema, DPI e escala.

**P3. Windhawk.** Injeta em todos os processos, menos numa lista de exclusão ([wiki](https://github.com/ramensoftware/windhawk/wiki/Injection-targets-and-critical-system-processes)).
Por isso: nunca é instalado sozinho; antes de qualquer receita o Katharos põe na exclusão os jogos detectados e os anti-cheats, e lê de volta.
**(dono decide)** se instala pelo winget ou só manda para o site oficial.

**P4. Galeria fora do programa.** Repositório público `kessleru/katharos-galeria` no GitHub Pages (limite de 1 GB). Imagem WebP até 80 KB,
vídeo WebM mudo de 4 a 8 s até 600 KB, teto de 150 MB. O aplicativo baixa só a prévia do cartão aberto, guarda até 40 MB em
`%LOCALAPPDATA%\Katharos\galeria`, confere o SHA-256 pelo `manifesto.json` e, sem internet, mostra só o texto. O download fica no C#. O CI
gera as capturas (próprias, nunca de terceiros) aplicando cada opção numa máquina descartável do Windows.

**P5. Relatório.** Sem conta: o aplicativo envia o relatório já limpo a um Cloudflare Worker (grátis) que abre uma issue no repositório
**privado** `kessleru/katharos-relatorios`; a pessoa recebe um código `KTH-...`. Limites: 200 KB, esquema validado, limite por IP, Turnstile,
nada guardado no Worker. Com conta GitHub: abre a issue pública só com o resumo, sem dado pessoal. Sempre com prévia e consentimento.
**(dono decide)** criar a conta da Cloudflare e o repositório privado; sem isso, a 4.1.0 sai só com o caminho do GitHub.

**P6. Sem fins lucrativos.** Pessoal, gratuito, MIT, sem venda, anúncio, rastreamento ou doação. Aparece no site, no aplicativo, no README,
no instalador e no relatório (J1 a J8). Isso é transparência, não parecer jurídico.

---

## 2. Personalização (fases 3 e 4)

Todas as chaves são confirmadas na fase 0 (Windows 10 22H2, 11 24H2, 11 25H2). Valor bloqueado pelo UCPD vira atalho para a tela do Windows.

**Nativo (fase 3)**
- Barra: ícones à esquerda ou centro, busca (escondida, ícone, caixa), esconder Visão de Tarefas, Widgets e Copilot, nunca agrupar com
  rótulos, esconder sozinha.
- Iniciar: mais fixados ou recomendados, esconder Recomendados, pastas ao lado do botão de energia.
- Explorador: tirar Galeria, Início e OneDrive da lateral; extensões, ocultos, modo compacto e abrir em Este Computador (já existem).
- Cores: cor de destaque nas bordas, no Iniciar e na barra; ícones da área de trabalho; Alt+Tab sem abas do Edge; Snap.
- Bloqueio e sons: sem dicas na tela de bloqueio, tela de entrada sem desfoque, esquema "Sem sons".
- Atalhos para Configurações: papel de parede, não perturbe com horário, ponteiro, tecla Copilot, temas da Loja.

**PowerToys (fase 4):** Light Switch (tema por horário), FancyZones, Always on Top, Keyboard Manager, Command Palette, PowerRename, Image Resizer, Peek.

**Windhawk, só receitas de shell (fase 4):** volume na barra, relógio com data e rede, ícones da bandeja, clique do meio fecha, barra no topo
ou na lateral, esconder com janela maximizada, botões de energia do Iniciar, tamanho de pastas no Explorador, sem aviso ao trocar extensão,
sem clarão branco, tirar itens do menu do botão direito, notificações em outro canto, Alt+Tab por monitor, e os "stylers" de barra, Iniciar,
Explorador e notificações. Cantos, bordas e janelas translúcidas ficam fora (`dwm.exe`).

**Estilos prontos (fase 4):** Windows 10 de volta, Limpo, Escuro e foco, Vários monitores; um clique, prévia do conjunto e volta em grupo.

## 3. Programas auxiliares

Só dois programas entram: **PowerToys** e **Windhawk** (com os mods da seção 2). Ambos são gratuitos e de código aberto. O Katharos instala
pelo winget só a pedido, com fonte oficial, e nunca empacota programa de terceiro. Nenhum outro programa é integrado nem indicado.

---

## 4. Tarefas

### Fase 0: confirmar no Windows de verdade
- [ ] **0.1** Job `personalizacao` no CI: grava, lê, desfaz e confere cada chave; marca as bloqueadas pelo UCPD.
- [ ] **0.2** Windhawk no CI: instalar pelo winget, achar mods, configurações e listas de exclusão; confirmar que dá para ler e gravar sem a interface.
- [ ] **0.3** PowerToys no CI: onde fica o `settings.json` de cada módulo e se ligar por arquivo vale.
- [ ] **0.4** Protótipo da galeria: 5 opções com foto antes e depois e um vídeo, no `katharos-galeria`.

### Fase 1: antivírus, proteção jurídica e bugs (4.1.0)
Antivírus (diagnóstico do ESET):
- [ ] **1.1** Trocar o `-EncodedCommand` escondido do vigia de tela por script em arquivo na pasta protegida, com `-File`.
- [ ] **1.2** Desfazer sem `Invoke-Expression`: operações de volta como registros estruturados; backups antigos lidos por lista de comandos permitidos.
- [ ] **1.3** `atualiza.ps1` fora do instalador (fica só no ZIP de terminal).
- [ ] **1.4** VirusTotal no CI: não publica se mais de um motor marcar; se só um marcar, publica e abre issue com o texto de falso positivo.
- [ ] **1.5** Textos de falso positivo para ESET, Microsoft, Avast/AVG, Kaspersky e Bitdefender (`planos/falso-positivo.md`).
- [ ] **1.6** Assinatura pela SignPath (`assinatura-signpath.md`): o dono envia o pedido.
- [ ] **1.7** Repositório protegido: `main` com CI obrigatório, tags `v*` protegidas, ambiente `release` com aprovação, ações por SHA, Dependabot, CodeQL, varredura de segredos. Checklist do dono: 2FA, log de segurança, apps autorizados.
- [ ] **1.8** Notas da release com o hash de cada arquivo e o link da atestação do build.

Proteção jurídica:
- [ ] **J1** Site: rodapé "Projeto pessoal, gratuito e de código aberto, sem fins lucrativos. Sem anúncios, venda ou rastreamento. Não é afiliado à Microsoft, à Ramen Software (Windhawk) nem a outras marcas citadas." Mais página **Aviso legal**.
- [ ] **J2** Aplicativo: tela **Sobre** (aviso, MIT, sem garantia, licenças de terceiros) e o aviso curto na primeira abertura, sem bloquear.
- [ ] **J3** README e instalador com o mesmo aviso.
- [ ] **J4** `THIRD-PARTY-NOTICES.md` gerado no CI (Python, .NET, Avalonia, SkiaSharp, HarfBuzz, Velopack, SQLite, OpenSSL, PresentMon, fontes).
- [ ] **J5** Marcas só para dizer compatibilidade, sem logotipo e sem sugerir parceria; revisar site e aplicativo.
- [ ] **J6** Galeria só com capturas próprias; o Katharos não redistribui mods do Windhawk, só a configuração da receita e o link do mod e do autor.
- [ ] **J7** Política de privacidade (LGPD) no site e no aplicativo antes do envio existir: o que vai, para quê, onde fica, 90 dias, como pedir para apagar pelo `KTH-...`, nada vendido.
- [ ] **J8** Doação, patrocínio e venda não entram.

Bugs:
- [ ] **1.9** Pendências da 4.0: 2.13 (3 pessoas leigas), 2c.1 e 2c.2 (teste jogando no kesslerupc).
- [ ] **1.10** Testes de abuso desta sessão viram testes permanentes no CI (estado corrompido, 57 comandos, sintaxe PowerShell 5.1, `pyflakes`, Python 3.8).
- [ ] **1.11** Ida e volta (aplicar e desfazer, registro e serviços iguais) para **todos** os pacotes no CI.
- [ ] **1.12** Lighthouse no celular (hoje 75), sem tocar na imagem do herói.

### Fase 2: relatório completo (4.1.0)
- [ ] **2.1** Conteúdo novo: erros internos do motor e da janela, itens que "não ficaram", tempo de cada etapa, versão e histórico de atualização; Windows (build, edição, idioma), antivírus e se algum mexeu em arquivo do Katharos; telas azuis, desligamentos, disco, temperatura, travadas.
- [ ] **2.2** Limpeza antes de sair: nome de usuário, nome do PC, números de série, IP, MAC, Wi-Fi, e-mails, arquivos de pastas pessoais. Teste com relatório "envenenado".
- [ ] **2.3** Tela **Enviar relatório**: prévia, seções que dá para tirar, campo "o que aconteceu?", consentimento, os dois caminhos de P5, código `KTH-...` no Histórico.
- [ ] **2.4** Worker de recebimento (se o dono aprovar P5): em `servidor/relatorio-worker`, com testes e deploy pelo CI.
- [ ] **2.5** Formulário de issue pública (`.github/ISSUE_TEMPLATE/problema.yml`) sem campo de dado pessoal.
- [ ] **2.6** Envio automático em erro: desligado por padrão; ligado, ainda mostra a prévia no primeiro envio.
- [ ] **2.7** Resumo semanal para o dono, feito pelo CI a partir do repositório privado.

### Fase 3: personalização nativa com galeria (4.2.0)
- [ ] **3.1** Pacote `personalizar` no motor, fora dos modos, com as opções nativas da seção 2; cada uma lida de volta e com desfazer.
- [ ] **3.2** Tela **Personalizar**: categorias, prévia, "o que muda", "funciona neste Windows?", aplicar e desfazer.
- [ ] **3.3** Galeria (P4): repositório, manifesto, geração no CI, cache, modo sem internet.
- [ ] **3.4** Página **Personalizar** no site com a mesma galeria.
- [ ] **3.5** Testes de cada opção em cada Windows do CI; foto refeita quando o Windows mudar.

### Fase 4: estilos e programas auxiliares (4.3.0)
- [ ] **4.1** Estilos prontos com prévia do conjunto e volta em grupo.
- [ ] **4.2** PowerToys: detectar, instalar a pedido, ligar módulos e explicar.
- [ ] **4.3** Windhawk (P3, se o dono aprovar): detectar, instalar a pedido, exclusão de jogos e anti-cheats, receitas de shell, desfazer.
- [ ] **4.4** Exportar e importar o seu estilo (JSON), com lista antes de aplicar.

### Fase 5: otimizações novas (4.4.0)
- [ ] **5.1** Perfis automáticos pelo segundo plano, sem tocar no jogo: ao abrir, plano "melhor desempenho", pausa de downloads do Windows Update e não perturbe; ao fechar, volta. No notebook, perfil de tomada e de bateria. Tudo opcional, no Histórico.
- [ ] **5.2** Placa de vídeo por jogo em notebook com duas placas (preferência "alto desempenho" de Configurações > Tela > Gráficos), com desfazer.
- [ ] **5.3** Limite de banda da Otimização de Entrega e horário ativo do Windows Update (políticas oficiais).
- [ ] **5.4** Segundo plano por app, com o custo medido de cada um.
- [ ] **5.5** Inicialização atrasada em vez de removida, medida no boot seguinte.
- [ ] **5.6** Modo de energia do Windows 11 (melhor desempenho e melhor eficiência), lido de volta.
- [ ] **5.7** Disco pequeno: compactação do Windows só em SSD pequeno e quase cheio, com o ganho estimado antes.
- [ ] **5.8** Kits de programas pelo winget (jogos, escritório, estudo), com os já instalados marcados.
- [ ] **5.9** Não entram, com o motivo no site: limpador de memória standby, arquivo de paginação, desligar Defender ou Integridade de Memória, apagar drivers, "boosters" de FPS.

### Fase 6: interface (4.5.0)
- [ ] **6.1** Busca em tudo (Ctrl+K), com prévia.
- [ ] **6.2** Prévia também no Otimizar, usando a mesma galeria.
- [ ] **6.3** Modo simples e avançado.
- [ ] **6.4** Acessibilidade: teclado, leitor de tela, alto contraste, tamanho de texto.
- [ ] **6.5** Histórico com o "antes e depois" de cada valor.
- [ ] **6.6** Novidades da versão na primeira abertura depois de atualizar.
- [ ] **6.7** Inglês no aplicativo, no site e na galeria.

---

## 5. Critérios de pronto
- Cada opção de personalização: funciona nos Windows do CI, lê de volta, desfaz e tem prévia.
- Nenhuma personalização entra por modo; nenhuma receita usa mod de todos os processos ou do `dwm.exe`.
- O instalador não cresce por causa da galeria (menos de 100 KB).
- O relatório "envenenado" não deixa sair dado pessoal; nenhum envio sem prévia e consentimento.
- Aviso de "sem fins lucrativos e sem afiliação" no site, no aplicativo, no README e no instalador.
- VirusTotal sem alerta de mais de um motor em cada release.

## 6. Riscos
| risco | o que fazer |
|---|---|
| Atualização do Windows muda uma chave | o job 0.1 roda toda semana; a opção vira "não funciona neste Windows" até corrigir |
| Mod do Windhawk quebra com o Windows | a receita guarda a versão conferida; a nova só entra depois do CI |
| Anti-cheat reclama do Windhawk | exclusão antes de qualquer receita; nunca instalado sozinho |
| Galeria fora do ar | só o texto aparece; nada deixa de funcionar |
| Abuso do endpoint de relatório | Turnstile, limites, nada guardado no Worker, token só do repositório privado |
| Antivírus marcar de novo | 1.1 a 1.6 e assinatura |

## 7. Regras que continuam valendo
- Mostrar cada mudança antes, desfazer tudo, ponto de restauração, ler de volta antes de dizer "feito".
- Nada que abra, leia ou injete em processo de jogo; nada de driver; nunca encerrar processo sozinho.
- Nada mexe na qualidade de áudio ou imagem no nível da placa de vídeo; personalização visual só quando a pessoa escolhe.
- O Python do motor não acessa a rede: download fica com o C# ou o PowerShell.
- Herói do site intocado, sem animação pesada, linhas horizontais e "+" mantidos.
- Commits sem coautoria. Versões pela regra do CHANGELOG. Cada release conferida.

## 8. Fontes
[Catálogo de mods do Windhawk](https://mods.windhawk.net/catalog.json), [repositório dos mods](https://github.com/ramensoftware/windhawk-mods),
[injeção e exclusões](https://github.com/ramensoftware/windhawk/wiki/Injection-targets-and-critical-system-processes),
[limites do GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits),
[issue por URL](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-an-issue#creating-an-issue-from-a-url-query).

---

## Registro
- 11 nov 2026: plano escrito (pedidos das 08:22 e 08:26).
- 11 nov 2026 (08:46 e 08:47): enxugado a pedido do dono: só o que dá para fazer hoje.
- 11 nov 2026 (08:49): saíram todos os programas além de PowerToys e Windhawk (StartAllBack, ExplorerPatcher e os demais).
