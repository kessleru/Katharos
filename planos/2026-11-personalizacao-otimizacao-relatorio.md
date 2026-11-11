# Plano: personalização, otimização, relatório com envio e proteção do projeto

Pedido de 11 nov 2026: mais otimização, **muito mais personalização do Windows** com prévia em imagem e vídeo (hospedada fora do programa),
melhorias de interface, segurança e bugs, **relatório completo com envio direto ao dono** e aviso claro de que o projeto **não tem fins
lucrativos**. Personalizações funcionais e sem problemas. Só entra o que dá para fazer hoje.

Marque `[x]` ao concluir e anote no **Registro** (fim) a data, a versão e o commit. Pesquisa de apoio: [cofre/2026-11-11-pesquisa-personalizacao.md](cofre/2026-11-11-pesquisa-personalizacao.md).

**Estado:** planejado, nada começou.

| fase | versão | o quê |
|---|---|---|
| 0 | — | confirmar no Windows do CI as chaves e o PowerToys |
| 1 | 4.1.0 | proteção jurídica e bugs |
| 2 | 4.1.0 | relatório completo com envio |
| 3 | 4.2.0 | personalização nativa com galeria |
| 4 | 4.3.0 | PowerToys |
| 5 | 4.4.0 | otimizações novas e perfis automáticos |
| 6 | 4.5.0 | interface |

---

## 1. Decisões

**P1. Personalização fica fora dos três modos.** Seguro, equilibrado e extremo continuam sendo otimização. Personalização é gosto: a pessoa
abre a tela **Personalizar**, vê a prévia, marca o que quer, e tudo volta pelo Desfazer.

**P2. Caminho de cada opção, nesta ordem:**
1. **Nativo do Windows** (registro, política oficial ou atalho para Configurações): padrão; sobrevive a atualizações e é lido de volta.
2. **PowerToys** (Microsoft, código aberto): instalado pelo winget só se a pessoa pedir.

Fora de qualquer caminho: trocar arquivo do sistema, patch de tema, fonte do sistema, DPI e escala.

**P3. Galeria fora do programa.** Repositório público `kessleru/katharos-galeria` no GitHub Pages (limite de 1 GB). Imagem WebP até 80 KB,
vídeo WebM mudo de 4 a 8 s até 600 KB, teto de 150 MB. O aplicativo baixa só a prévia do cartão aberto, guarda até 40 MB em
`%LOCALAPPDATA%\Katharos\galeria`, confere o SHA-256 pelo `manifesto.json` e, sem internet, mostra só o texto. O download fica no C#. O CI
gera as capturas (próprias, nunca de terceiros) aplicando cada opção numa máquina descartável do Windows.

**P4. Relatório.** Sem conta: o aplicativo envia o relatório já limpo a um Cloudflare Worker (grátis) que abre uma issue no repositório
**privado** `kessleru/katharos-relatorios`; a pessoa recebe um código `KTH-...`. Limites: 200 KB, esquema validado, limite por IP, Turnstile,
nada guardado no Worker. É o **único** caminho de envio: sem conta no GitHub e sem issue pública. Sempre com prévia e consentimento.
**(dono)** cria a conta grátis da Cloudflare e o repositório privado `katharos-relatorios`.

**P5. Sem fins lucrativos.** Pessoal, gratuito, MIT, sem venda, anúncio, rastreamento ou doação. Aparece no site, no aplicativo, no README,
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

## 3. Programa auxiliar

Só o **PowerToys** (Microsoft, gratuito e de código aberto) entra. O Katharos instala pelo winget só a pedido, com fonte oficial, e nunca
empacota programa de terceiro. Nenhum outro programa é integrado nem indicado.

---

## 4. Tarefas

### Fase 0: confirmar no Windows de verdade
- [ ] **0.1** Job `personalizacao` no CI: grava, lê, desfaz e confere cada chave; marca as bloqueadas pelo UCPD.
- [ ] **0.3** PowerToys no CI: onde fica o `settings.json` de cada módulo e se ligar por arquivo vale.
- [ ] **0.4** Protótipo da galeria: 5 opções com foto antes e depois e um vídeo, no `katharos-galeria`.

### Fase 1: proteção jurídica e bugs (4.1.0)
Proteção jurídica:
- [ ] **J1** Site: rodapé "Projeto pessoal, gratuito e de código aberto, sem fins lucrativos. Sem anúncios, venda ou rastreamento. Não é afiliado à Microsoft nem a outras marcas citadas." Mais página **Aviso legal**.
- [ ] **J2** Aplicativo: tela **Sobre** (aviso, MIT, sem garantia, licenças de terceiros) e o aviso curto na primeira abertura, sem bloquear.
- [ ] **J3** README e instalador com o mesmo aviso.
- [ ] **J4** `THIRD-PARTY-NOTICES.md` gerado no CI (Python, .NET, Avalonia, SkiaSharp, HarfBuzz, Velopack, SQLite, OpenSSL, PresentMon, fontes).
- [ ] **J5** Marcas só para dizer compatibilidade, sem logotipo e sem sugerir parceria; revisar site e aplicativo.
- [ ] **J6** Galeria só com capturas próprias.
- [ ] **J7** Política de privacidade (LGPD) no site e no aplicativo antes do envio existir: o que vai, para quê, onde fica, 90 dias, como pedir para apagar pelo `KTH-...`, nada vendido.
- [ ] **J8** Doação, patrocínio e venda não entram.

Bugs:
- [ ] **1.1** Pendências da 4.0: 2.13 (3 pessoas leigas), 2c.1 e 2c.2 (teste jogando no kesslerupc).
- [ ] **1.2** Testes de abuso desta sessão viram testes permanentes no CI (estado corrompido, 57 comandos, sintaxe PowerShell 5.1, `pyflakes`, Python 3.8).
- [ ] **1.3** Ida e volta (aplicar e desfazer, registro e serviços iguais) para **todos** os pacotes no CI.
- [ ] **1.4** Lighthouse no celular (hoje 75), sem tocar na imagem do herói.

### Fase 2: relatório completo (4.1.0)
- [ ] **2.1** Conteúdo novo: erros internos do motor e da janela, itens que "não ficaram", tempo de cada etapa, versão e histórico de atualização; Windows (build, edição, idioma), antivírus e se algum mexeu em arquivo do Katharos; telas azuis, desligamentos, disco, temperatura, travadas.
- [ ] **2.2** Limpeza antes de sair: nome de usuário, nome do PC, números de série, IP, MAC, Wi-Fi, e-mails, arquivos de pastas pessoais. Teste com relatório "envenenado".
- [ ] **2.3** Tela **Enviar relatório**: prévia, seções que dá para tirar, campo "o que aconteceu?", consentimento, envio sem conta (P4), código `KTH-...` no Histórico.
- [ ] **2.4** Worker de recebimento (P4): em `servidor/relatorio-worker`, com testes e deploy pelo CI.
- [ ] **2.5** Envio automático em erro: desligado por padrão; ligado, ainda mostra a prévia no primeiro envio.
- [ ] **2.6** Resumo semanal para o dono, feito pelo CI a partir do repositório privado.

### Fase 3: personalização nativa com galeria (4.2.0)
- [ ] **3.1** Pacote `personalizar` no motor, fora dos modos, com as opções nativas da seção 2; cada uma lida de volta e com desfazer.
- [ ] **3.2** Tela **Personalizar**: categorias, prévia, "o que muda", "funciona neste Windows?", aplicar e desfazer.
- [ ] **3.3** Galeria (P3): repositório, manifesto, geração no CI, cache, modo sem internet.
- [ ] **3.4** Página **Personalizar** no site com a mesma galeria.
- [ ] **3.5** Testes de cada opção em cada Windows do CI; foto refeita quando o Windows mudar.

### Fase 4: PowerToys (4.3.0)
- [ ] **4.1** PowerToys: detectar, instalar a pedido, ligar módulos e explicar.

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
- Nenhuma personalização entra por modo; nenhuma injeta em processo.
- O instalador não cresce por causa da galeria (menos de 100 KB).
- O relatório "envenenado" não deixa sair dado pessoal; nenhum envio sem prévia e consentimento.
- Aviso de "sem fins lucrativos e sem afiliação" no site, no aplicativo, no README e no instalador.

## 6. Riscos
| risco | o que fazer |
|---|---|
| Atualização do Windows muda uma chave | o job 0.1 roda toda semana; a opção vira "não funciona neste Windows" até corrigir |
| Galeria fora do ar | só o texto aparece; nada deixa de funcionar |
| Abuso do endpoint de relatório | Turnstile, limites, nada guardado no Worker, token só do repositório privado |

## 7. Regras que continuam valendo
- Mostrar cada mudança antes, desfazer tudo, ponto de restauração, ler de volta antes de dizer "feito".
- Nada que abra, leia ou injete em processo de jogo; nada de driver; nunca encerrar processo sozinho.
- Nada mexe na qualidade de áudio ou imagem no nível da placa de vídeo; personalização visual só quando a pessoa escolhe.
- O Python do motor não acessa a rede: download fica com o C# ou o PowerShell.
- Herói do site intocado, sem animação pesada, linhas horizontais e "+" mantidos.
- Commits sem coautoria. Versões pela regra do CHANGELOG. Cada release conferida.

## 8. Fontes
[limites do GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).

---

## Registro
- 11 nov 2026: plano escrito (pedidos das 08:22 e 08:26).
- 11 nov 2026 (08:46 e 08:47): enxugado a pedido do dono: só o que dá para fazer hoje.
- 11 nov 2026 (08:49 e 08:51): saíram todos os programas além do PowerToys, inclusive o Windhawk e os mods.
- 11 nov 2026 (08:52): relatório só sem conta (Worker e repositório privado); saíram o caminho pelo GitHub e o formulário de issue pública.
- 11 nov 2026 (08:53): a seção de antivírus saiu da fase 1, só por agora; guardada em [adiado-antivirus.md](adiado-antivirus.md).
- 11 nov 2026 (08:57): a pedido do dono, voltou ao estado de antes das personalizações próprias: PowerToys de volta, kits do winget de volta; seguem fora estilos prontos, exportar e importar, Windhawk, outros programas, antivírus (adiado) e relatório pelo GitHub.
