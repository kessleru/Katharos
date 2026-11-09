# Como contribuir com o Katharos

O projeto é pequeno e o código é aberto. Há três jeitos de ajudar.

## 1. Contar um problema

Abra uma issue e conte:

- a versão do Windows (`winver`) e a versão do Katharos (`katharos --versao`);
- o comando que você rodou e o que aconteceu;
- o que você esperava.

O arquivo `relatorios/ultimo.md` ajuda muito. **Ele tem o nome do PC, a lista de programas e outras informações da sua máquina: leia e apague o que não quiser compartilhar antes de colar.**

Problema de segurança (um item que faz algo perigoso, por exemplo) não vai em issue pública: veja o [SECURITY.md](SECURITY.md).

## 2. Propor um ajuste ou um item

Cada item do Katharos é um `Item(...)` em `programa/katharos.py`. Para entrar, ele precisa:

1. **Dizer o que ganha e o que perde.** Se não perde nada, escreva "nenhum". Se o ganho é pequeno, diga que é pequeno.
2. **Ter fonte.** Documentação da Microsoft, da Valve ou uma medição que outra pessoa consiga repetir. "Li num fórum" não basta.
3. **Poder voltar.** Mudanças de registro usam `Set-Valor`, serviços e tarefas usam `Guarda-Desfazer`. O que não volta (programa desinstalado) fica marcado como `reverte=False` e o item avisa antes.
4. **Ter o nível certo.** 1 seguro (nada que a pessoa sinta falta), 2 equilibrado, 3 extremo (tem custo claro), 0 só se marcar.
5. **Passar nos testes.**

O que **não** entra, em nenhum modo: desligar o Defender, o firewall, o UAC, o SmartScreen, o Windows Update, a memória virtual, o BitLocker, a Restauração do Sistema ou a Integridade de Memória. O teste `test_nenhum_script_mexe_nas_protecoes` falha se um script fizer isso.

Em jogos, o Katharos só muda configurações do Windows e arquivos de configuração do usuário. Nada de arquivo ou memória do jogo, e nenhuma mudança por executável em jogo com anti-cheat de terceiros.

### Rodando os testes

```
python -m unittest discover -s tests -v
```

Eles rodam em qualquer sistema (Python 3.8 ou mais novo, sem dependências). No GitHub, um segundo job confere a sintaxe de cada script de item no PowerShell 5.1.

Depois de mudar `programa/katharos.py`:

```
sha256sum KATHAROS.bat programa/katharos.py programa/katharos.ps1 > SHA256SUMS.txt
```

e, se mexeu em itens, perfis ou comandos, atualize o `CHANGELOG.md`.

## 3. Revisar o código

É um arquivo só. `katharos <comando> --codigo` mostra o PowerShell de cada item sem aplicar nada, e `--teste` mostra o que seria feito. Se achar algo que não bate com o que o texto promete, isso vale uma issue.

## Versões

O número tem três partes, MAIOR.MENOR.CORREÇÃO, e as regras de quando cada uma sobe estão no [CHANGELOG.md](CHANGELOG.md). Uma versão é uma entrega com tag (`v1.2.0`), não um commit: mudanças de site, documentação, testes e CI não geram versão. Se a sua mudança altera o que o usuário vê, diga no pull request se é MENOR ou CORREÇÃO; quem publica a versão atualiza `VERSAO`, a data e o CHANGELOG juntos.

## Crédito

Quem ajuda aparece pelo nome:

- o seu commit entra no histórico com a sua autoria (o pull request é aceito sem apagar o seu nome) e o GitHub lista você em *Contributors*;
- quem corrigir um erro ou propor um item é agradecido pelo nome na nota da versão, no [CHANGELOG.md](CHANGELOG.md);
- prefere não aparecer? Diga no pull request e o seu nome fica de fora.
