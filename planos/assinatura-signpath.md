# Pedido de assinatura de código à SignPath Foundation (5.3)

O dono envia o pedido em https://signpath.org/apply (precisa da conta do GitHub dele). Este é o texto, pronto para colar.

**Projeto:** Katharos — https://github.com/kessleru/Katharos
**Licença:** MIT (OSI)
**Descrição:** otimizador de Windows de código aberto, em português, que mostra cada mudança antes de aplicar, guarda o valor anterior de cada ajuste e desfaz tudo; com versão de terminal (Python) e versão com janelas (Avalonia/.NET 10) instalada pelo Velopack.
**O que assinar:** `Katharos-win-Setup.exe` (instalador Velopack), `Katharos.exe` (aplicativo com janelas) e `motor\Katharos.exe` (segundo plano em C#), todos gerados pelo workflow `publicar.yml` a partir de uma tag `vX.Y.Z`.
**Build:** 100 % no GitHub Actions, com atestado de procedência (`actions/attest-build-provenance`) e SHA-256 publicado em cada release. Terceiros embutidos: Python embeddable oficial (python.org, SHA-256 fixo no workflow) e PresentMon (Intel, MIT, SHA-256 fixo).
**Política de assinatura publicada:** https://github.com/kessleru/Katharos/blob/main/SECURITY.md#política-de-assinatura-de-código
**Mantenedor que aprova:** kessleru (2FA ligado).

## Depois de aprovado (5.4)

1. No SignPath: criar o projeto `Katharos`, a política `release-signing` e o artifact configuration com os três arquivos acima.
2. No GitHub, em Settings > Secrets: `SIGNPATH_API_TOKEN` e as variáveis `SIGNPATH_ORG_ID`, `SIGNPATH_PROJECT`, `SIGNPATH_POLICY`.
3. O passo "assina (SignPath)" do `publicar.yml` liga sozinho quando o segredo existe (ele já está lá, desligado sem o segredo).
