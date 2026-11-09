# Segurança

## Verificar o que você baixou

O Katharos é um arquivo só (`programa\katharos.py`) e um lançador (`programa\katharos.ps1`), chamados pelo `KATHAROS.bat`. Confira que são os do repositório:

```powershell
python programa\katharos.py --sha256
Get-FileHash programa\katharos.ps1 -Algorithm SHA256
Get-FileHash KATHAROS.bat -Algorithm SHA256
```

Compare com o `SHA256SUMS.txt` da versão em https://github.com/kessleru/Katharos. Se os valores não baterem, não rode.

## O que ele nunca faz

Desligar Defender, firewall, UAC, SmartScreen, VBS, Windows Update, BitLocker ou Proteção do Sistema; mexer na BIOS ou em partições; limpar o registro. Tudo que muda tem o valor anterior guardado e volta com `desfazer`; programas e apps removidos são a exceção, e o item avisa.

## Ver o que ele vai executar

`--codigo` (ou `v 3` na tela de escolha) mostra o PowerShell exato de cada item. O código é aberto e legível: ler o arquivo é a melhor auditoria.

## Dados

Nada é enviado pela rede pelo Katharos. Tudo fica em `%USERPROFILE%\.katharos`. O relatório único tem o nome do PC, os programas instalados e caminhos de pastas: confira antes de compartilhar. Textos que vêm do PC entram no relatório limpos, e o arquivo declara que é dado e não instrução.

## Encontrou um problema?

Abra uma issue em https://github.com/kessleru/Katharos/issues. Para algo sensível, não publique detalhes: peça um contato privado na issue.
