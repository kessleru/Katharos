---
title: Segundo plano e janela como um programa só
date: 2026-11-11
tags: [decisao, katharos, segundo-plano, instalador, v4]
---
# Segundo plano e janela como um programa só

**Decisão (com o dono, 11 nov).** O segundo plano continua sendo o `Katharos.exe` em C# 5 (leve, roda no .NET Framework do próprio Windows), mas para quem usa é um programa só: o instalador põe os dois; o ícone e o clique no aviso abrem a janela na tela certa; a janela é única; a troca de versão pede para o segundo plano sair e religa ele na pasta nova; a desinstalação tira o "iniciar com o Windows" e guarda os dados.

**Por quê não juntar no mesmo executável .NET 10.** Um processo .NET 10 com Avalonia residente pesa mais o dia inteiro, e o pedido era segundo plano leve sem perder nada. A integração resolve o que a pessoa sente.

**Segurança.** O motor de administrador roda de uma cópia em `%ProgramData%\Katharos\<versão>` conferida pelo SHA-256 do manifesto gravado no aplicativo no build; o CI testa com um arquivo alterado (recusa).

Related: [Motor de inteligência da v4](2026-11-11-motor-de-inteligencia-v4.md)
