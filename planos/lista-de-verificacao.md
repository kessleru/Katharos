# Lista de verificação do Katharos

Para usar antes de publicar qualquer versão e quando um PC novo (como o Acer do amigo) for testar. Marque `[x]` ao conferir.
Versão em teste: 4.0.2 (ainda sem tag). O que o CI já cobre fica na parte A; a parte B é à mão, num Windows de verdade.

## A. Automático (aqui e no CI)
- [x] `bash scripts/monta.sh`: motor montado, regras geradas, site e hashes atualizados, 369 testes passando
- [x] A interface compila em Release (`dotnet build`)
- [x] O `Katharos.exe` compila
- [x] A versão é a mesma no motor, na interface, no exe e no CHANGELOG
- [ ] CI longo (`testes.yml`): executável, Python 3.8 e 3.13, PowerShell, Windows 2022 e 2025 (só a pedido)
- [ ] `publicar.yml`: executável, interface, instalador, release com `SHA256SUMS.txt` (só a pedido)
- [ ] Hash de cada arquivo da release confere com o `SHA256SUMS.txt`
- [ ] Ensaios do CI: atualização pelo Velopack e motor de administrador com a cópia protegida

## B. À mão, num Windows de verdade

**Instalar e abrir**
- [ ] O instalador abre sem erro; o antivírus não bloqueia
- [ ] A janela abre e o Início carrega em poucos segundos (se passar de 1 minuto, aparece "Tentar de novo")
- [ ] Abrir o Katharos de novo traz a janela que já está aberta (uma janela só)
- [ ] Primeira abertura: o aviso aparece uma vez e não bloqueia

**Cada tela**
- [ ] Início: nota, próximo passo e botões levam à tela certa
- [ ] Raio-x: roda, mostra a barra andando, termina e guarda o resultado; "Fazer de novo" funciona
- [ ] Otimizar: os três modos mostram os itens; "já está assim" é conferido; nada marcado sozinho no extremo
- [ ] Ao vivo: desligado fica parado, sem piscar; ligar mostra "Ligando…" e depois as leituras; dois cliques seguidos não atrapalham; se falhar, a mensagem fica até "Tentar de novo"
- [ ] Jogos, Sugestões, Histórico: abrem com e sem dados guardados, sem erro
- [ ] Desfazer: lista o que foi aplicado e volta a um clique
- [ ] Configurações: gravam e continuam gravadas ao reabrir

**Mudar o PC (sempre com administrador)**
- [ ] O Windows pede permissão uma vez por sessão; recusar não muda nada e diz isso
- [ ] Aplicar um item do modo seguro: o ponto de restauração é criado, o item é aplicado e lido de volta
- [ ] Desfazer volta o item ao valor de antes
- [ ] Nada que mude a qualidade de imagem ou de som entra sozinho; HAGS só liga se o Windows mostrar suporte

**Acompanhamento em segundo plano**
- [ ] Ligar: o ícone aparece perto do relógio e a barra lateral diz "Acompanhando o PC" e não volta para "desligado"
- [ ] Fechar e abrir a janela: continua ligado
- [ ] Abrir um jogo: a sessão começa; fechar: a sessão grava; a manutenção não roda com jogo aberto
- [ ] Desligar pelo ícone ou pela tela: o processo sai de verdade
- [ ] Num PC lento: a leitura espaça sozinha e a janela não diz "desligado" com ele rodando

**Atualizar e remover**
- [ ] Atualizar pela janela: o segundo plano fecha antes da troca e volta depois
- [ ] Desinstalar: o "iniciar com o Windows" sai e a pasta `.katharos` com os seus dados fica

**Segurança e integridade**
- [ ] O motor de administrador roda da cópia protegida em `%ProgramData%\Katharos` e recusa arquivo alterado
- [ ] O instalador baixado do site tem o mesmo hash do `SHA256SUMS.txt`
- [ ] `interface.log` e `segundo-plano.log` sem erros novos depois do teste

**Site**
- [ ] O botão de download baixa a última tag
- [ ] Os vídeos tocam e o "veja funcionando" continua como estava
- [ ] Celular: sem rolagem horizontal

## C. Se algo falhar
Mandar `%USERPROFILE%\.katharos\interface.log` e `segundo-plano.log`. Eles dizem em qual passo o motor ou o segundo plano parou.

Related: [plano de personalização](2026-11-personalizacao-otimizacao-relatorio.md), [antivírus adiado](adiado-antivirus.md)
