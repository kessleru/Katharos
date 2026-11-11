# Segurança

## Verificar o que você baixou

Confira de fora do programa, porque um arquivo alterado pode mentir sobre si mesmo. Em ordem de força:

1. **Assinatura do GitHub** (a mais forte). Cada release é atestada pelo GitHub Actions deste repositório. Com o [GitHub CLI](https://cli.github.com/) instalado:

   ```powershell
   gh attestation verify katharos.py --repo kessleru/Katharos
   gh attestation verify Katharos-win-Setup.exe --repo kessleru/Katharos
   ```

   Passa só se o arquivo foi gerado pela release oficial. Uma cópia alterada, ou publicada por outra conta, falha.
2. **SHA-256 contra a descrição da release.** No PowerShell, na pasta do arquivo:

   ```powershell
   Get-FileHash .\katharos.py -Algorithm SHA256
   ```

   O valor deve ser igual ao da página da release e ao do `SHA256SUMS.txt`. Prefira a página da release em https://github.com/kessleru/Katharos/releases: quem altera o arquivo pode alterar uma lista que veio junto.
3. **Dentro do programa:** `katharos autenticidade` compara com o `SHA256SUMS.txt` que veio junto (sem rede) e com a lista oficial da versão (baixada pelo PowerShell, só quando você roda o comando; `--offline` pula). Na abertura, ele avisa sozinho se o arquivo não bate com a lista que veio junto. É conveniência, não prova: um arquivo alterado pode remover essa conferência, por isso valem as de fora.

Baixe só de https://github.com/kessleru/Katharos. Cópias em outros sites, fóruns ou mensagens podem ter sido alteradas.

## Katharos com janelas (instalador)

- **Instala por usuário**, sem pedir administrador para instalar. Atualiza pelas releases deste repositório (Velopack), baixando só a diferença, e nunca no meio de uma mudança no PC.
- **O motor de administrador não roda da sua pasta.** Quando você aplica algo, o Windows pede permissão uma vez; o PowerShell do Windows (pelo caminho completo) confere o manifesto de SHA-256 do motor e do Python contra o hash gravado no aplicativo no build, copia para `%ProgramData%\Katharos\<versão>` (onde só administradores gravam), confere a cópia de novo e só então abre o motor dali. Se um arquivo foi trocado, ele não abre e diz isso.
- **O motor de administrador só atende a janela que o abriu**: pipe local com permissão só do seu usuário e do sistema, uma conexão, sem rede, e uma senha de uso único. Ele só aceita aplicar e desfazer.
- **Nenhuma porta de rede aberta.** O firewall não tem o que barrar. O antivírus do Windows passa em cada versão antes de sair (no CI).
- **O segundo plano só lê**: contadores do Windows, nomes de processo e o driver de vídeo. Não abre, não lê e não injeta nada em jogo, não instala driver de sensor. O teste de travadas liga por um minuto o rastreio do kernel só com DPC e interrupção, e desliga no fim.

## Política de assinatura de código

O SmartScreen avisa na primeira instalação porque o instalador ainda não é assinado com certificado. O pedido de assinatura gratuita para código aberto (SignPath Foundation) está preparado; quando aprovado:

- só arquivos gerados pelo GitHub Actions deste repositório, a partir de uma tag, são assinados (nenhum arquivo é assinado à mão);
- o que é assinado: o `Katharos-win-Setup.exe`, o `Katharos.exe` com janelas e o `Katharos.exe` do segundo plano;
- quem aprova cada assinatura: o mantenedor (kessleru), conta com autenticação em dois fatores;
- o código assinado é o deste repositório, sem binário de terceiros embutido além do Python oficial (python.org, SHA-256 fixo) e do PresentMon (Intel, MIT, SHA-256 fixo).

Até lá, a prova de procedência é o atestado do GitHub acima.

## O que ele nunca faz

Desligar Defender, firewall, UAC, SmartScreen, VBS, Windows Update, BitLocker ou Proteção do Sistema; mexer na BIOS ou em partições; limpar o registro. Tudo que muda tem o valor anterior guardado e volta com `desfazer`; programas e apps removidos são a exceção, e o item avisa.

## Ver o que ele vai executar

`--codigo` (ou `v 3` na tela de escolha) mostra o PowerShell exato de cada item. O código é aberto e legível: ler o arquivo é a melhor auditoria.

## Dados

Nada é enviado pela rede pelo Katharos. Tudo fica em `%USERPROFILE%\.katharos`, menos o que roda como administrador (backup do `desfazer`, scripts temporários e a cópia das tarefas agendadas), que fica em `%ProgramData%\Katharos`, onde só administradores gravam: um programa sem administrador não consegue trocar esses arquivos para ganhar administrador. O relatório único tem o nome do PC, os programas instalados e caminhos de pastas: confira antes de compartilhar. Textos que vêm do PC entram no relatório limpos, e o arquivo declara que é dado e não instrução.

## Encontrou um problema?

Abra uma issue em https://github.com/kessleru/Katharos/issues. Para algo sensível, não publique detalhes: peça um contato privado na issue.
