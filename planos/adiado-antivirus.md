# Adiado: antivírus (diagnóstico do ESET)

Tirado da fase 1 do [plano de personalização](2026-11-personalizacao-otimizacao-relatorio.md) em 11 nov 2026 (08:53), **só por agora**.
Quando voltar, entra de novo na fase 1 (4.1.0) ou numa versão própria.

- [ ] **A1** Trocar o `-EncodedCommand` escondido do vigia de tela por script em arquivo na pasta protegida, com `-File`.
- [ ] **A2** Desfazer sem `Invoke-Expression`: operações de volta como registros estruturados; backups antigos lidos por lista de comandos permitidos.
- [ ] **A3** `atualiza.ps1` fora do instalador (fica só no ZIP de terminal).
- [ ] **A4** VirusTotal no CI: não publica se mais de um motor marcar; se só um marcar, publica e abre issue com o texto de falso positivo.
- [ ] **A5** Textos de falso positivo para ESET, Microsoft, Avast/AVG, Kaspersky e Bitdefender (`planos/falso-positivo.md`).
- [ ] **A6** Assinatura pela SignPath ([assinatura-signpath.md](assinatura-signpath.md)): o dono envia o pedido.
- [ ] **A7** Repositório protegido: `main` com CI obrigatório, tags `v*` protegidas, ambiente `release` com aprovação, ações por SHA, Dependabot, CodeQL, varredura de segredos. Checklist do dono: 2FA, log de segurança, apps autorizados.
- [ ] **A8** Notas da release com o hash de cada arquivo e o link da atestação do build.
