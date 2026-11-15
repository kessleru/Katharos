# Testes no PC do dono, 15/11/2026 (Katharos 4.4.0 instalado)

Daqui não há terminal do Windows: o "terminal" ligado ao PC é um Linux que só enxerga `~/.katharos` e o cofre. O Windows Terminal e o VS Code aceitam só clique. Então os testes foram feitos pelos arquivos do Katharos (logs, estado, banco SQLite), e o que precisa do Windows ficou como lista para rodar na 4.5.0.

## O que os arquivos mostraram

| # | Achado | Prova | Corrigido na 4.5.0 |
|---|---|---|---|
| 1 | O segundo plano não abre com o Windows desde que a janela passou a abrir junto | segundo-plano.log: subiu às 22:31 de 14/11; a janela abriu à 01:16 (interface.log) e tomou a entrada "Katharos"; no boot de 08:58 só a janela abriu; o agora.json está parado desde 01:17 | sim: entradas separadas e religa |
| 2 | Manutenção agendada parada desde 10/11 | estado.json `manut_ultima` = 2026-11-10T18:27; metricas.jsonl com 2 linhas (9 e 10/11) | sim: a cópia protegida não apaga mais o katharos.py dela; as tarefas são conferidas e consertadas |
| 3 | Histórico parado em 10/11 | consequência do 2 | sim, mais a medida diária pela janela |
| 4 | Leitura de 15 min (tarefa "amostra leve") nunca gravou | katharos.db: tabela `horas` com 0 linhas; a tarefa usa o Python 3.12 da Loja e hoje o Python é o 3.14 | sim: a tarefa do usuário passa a usar o Python do Katharos instalado e é recriada sozinha |
| 5 | O backup do desfazer em %ProgramData%\Katharos\backup pode ter sido apagado a cada troca de versão (desde a 4.2.0) | mesmo código do 2 | sim, para frente; o que já foi apagado não volta (os valores de antes continuam em estado.json/mudancas) |
| 6 | FPS nunca medido | segundo-plano.log: "sem permissão" em todas as sessões | sim: botão Liberar |
| 7 | Consumo do Katharos com três números diferentes | Gerenciador: Katharos 120,9 MB + 2 × PowerShell (123,7 e 109,3 MB); Ao vivo: 325 MB; rodapé: 68 MB | sim: o Ao vivo soma os PowerShell; o rodapé diz "este ícone" |
| 8 | Abertura da janela | interface.log: 0,99 a 1,61 s | ok |
| 9 | Raio-x | 23,5 a 32,4 s | ok (meta: < 20 s na UI 2) |

## Lista de testes para quando a 4.5.0 estiver instalada

Segundo plano:
- [ ] Reiniciar o PC: o ícone aparece perto do relógio sem abrir nada. Ao vivo mostra "ao vivo".
- [ ] Com "abrir com o Windows" ligado: a janela também abre, e o ícone continua.
- [ ] Gerenciador > Inicializar: aparecem "Katharos" e "Katharos Janela".
- [ ] Sair pelo ícone e abrir a janela: ele **não** volta sozinho (você saiu). Ligar no Ao vivo: volta.
- [ ] Fechar o Katharos.exe (segundo plano) pelo Gerenciador e abrir a janela: ele volta e o log diz "estava fechado; abri".

Tarefas e histórico:
- [ ] O Início mostra "A manutenção agendada parou" com "Consertar". Clicar pede administrador e some depois.
- [ ] `C:\ProgramData\Katharos` tem `katharos.py`, `python\`, `backup\` e a pasta da versão. Trocar de versão não apaga os três primeiros.
- [ ] Agendador de Tarefas: "Katharos - segundo plano" aponta para `C:\ProgramData\Katharos\python\pythonw.exe`, e "Katharos - amostra leve" para `%LOCALAPPDATA%\Katharos\current\python\pythonw.exe`.
- [ ] No dia seguinte, o Histórico tem ponto novo.

Telas:
- [ ] Escrever no Enviar, ir ao Raio-x e voltar: o texto continua.
- [ ] Fazer o raio-x, ir ao Início e voltar: ele continua rodando de onde estava.
- [ ] Memória: grupo "Fechados agora" com o cs2 apagado.
- [ ] Jogos: a dica "Ajustes para jogos disponíveis" some, porque já está tudo aplicado.
- [ ] Dispositivos: aparecem o Rapoo e o Aula com o VID/PID no mouse em cima. Mandar um relatório depois (a lista vai junto).
- [ ] Configurações > FPS nos jogos > Liberar, depois sair e entrar na conta: a próxima sessão tem FPS.
- [ ] Ao vivo: "O Katharos neste PC" soma perto do que o Gerenciador mostra (Katharos + os PowerShell).

Atualização:
- [ ] Publicar uma 4.5.1 de teste com a janela aberta: em até 3 h aparece "Versão 4.5.1 pronta" com "Reiniciar agora / Na próxima vez".

Desinstalar (num PC de teste):
- [ ] Desinstalar pela página Aplicativos: o ícone some, "Katharos" e "Katharos Janela" saem da inicialização, e as duas tarefas somem (a de administrador, se o Windows deixar; senão fica registrado em interface.log).

## Melhorias anotadas para depois
- O ícone (segundo plano) poderia conferir a atualização também, para quem nunca abre a janela.
- A tarefa elevada antiga com o Python da Loja: a 4.5.0 conserta com um clique. Uma versão futura pode trocar a tarefa elevada por um serviço pequeno.
- Os testes acima podem virar um "autoteste" na própria janela (Configurações > Conferir o Katharos), que roda a lista e manda junto no relatório.
