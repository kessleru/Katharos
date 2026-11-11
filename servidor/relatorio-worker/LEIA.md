# Servidor de relatórios do Katharos

O botão **Enviar** da janela manda o relatório e o feedback para este Worker da Cloudflare. Ele confere o formato e guarda cada envio
no repositório **privado** `kessleru/katharos-relatorios`: um arquivo JSON completo (`relatorios/AAAA/MM/KTH-XXXXXX.json`) e uma
issue com a ficha para triagem. O Worker em si não guarda nada. É grátis no plano gratuito da Cloudflare (100 mil pedidos por dia).

Enquanto ele não estiver no ar, a janela diz que o envio ainda não está disponível e guarda o pacote no PC para mandar depois.

## Pôr no ar (uma vez, uns 15 minutos)

### 1. O repositório privado
1. Em github.com, **New repository**, nome `katharos-relatorios`, marque **Private**, marque **Add a README**, crie.

### 2. O token do GitHub (só para esse repositório)
1. github.com > foto > **Settings** > **Developer settings** > **Personal access tokens** > **Fine-grained tokens** > **Generate new token**.
2. Nome `katharos-relatorios-worker`, validade de 1 ano.
3. **Repository access**: *Only select repositories* > `katharos-relatorios`.
4. **Permissions** > Repository permissions: **Contents: Read and write** e **Issues: Read and write**. Nada mais.
5. **Generate token** e copie (começa com `github_pat_`). Ele aparece uma vez só.

### 3. A conta da Cloudflare
1. Crie a conta em dash.cloudflare.com/sign-up (plano **Free**; não precisa de cartão nem de domínio).
2. Confirme o e-mail.

### 4. O Worker, pelo painel (sem instalar nada)
1. No painel: **Workers & Pages** > **Create** > **Create Worker**. Nome: `katharos-relatorios`. **Deploy**.
2. **Edit code**: apague o exemplo, cole todo o `src/index.js` deste diretório e clique em **Deploy**.
3. **Settings** > **Variables and Secrets** > **Add**:
   - tipo **Text**, nome `REPO`, valor `kessleru/katharos-relatorios`;
   - tipo **Secret**, nome `GITHUB_TOKEN`, valor: o token do passo 2.
4. Copie o endereço do Worker (algo como `https://katharos-relatorios.SEU-NOME.workers.dev`) e abra no navegador:
   tem que aparecer `{"ok":true,"servico":"katharos-relatorios"}`.

O limite de envios por IP (`LIMITE`) só entra pelo jeito do passo 4b. Sem ele o Worker funciona; com ele, cada IP manda no máximo 5
por minuto.

### 4b. (Opcional) O mesmo, pelo terminal, com o limite por IP
Com o Node.js instalado, dentro desta pasta:

```
npx wrangler login
npx wrangler deploy
npx wrangler secret put GITHUB_TOKEN
```

### 5. Ligar a janela ao Worker
A janela lê o endereço de `https://kessleru.github.io/Katharos/envio.json`. Basta pôr o endereço do Worker em `docs/envio.json` no
repositório do Katharos e publicar o site (não precisa de versão nova do programa):

```json
{ "url": "https://katharos-relatorios.SEU-NOME.workers.dev/enviar", "ativo": true }
```

## Testar
- Os testes do Worker: `node --test servidor/relatorio-worker/test/worker.test.mjs` (sem dependências).
- Um envio de verdade: na janela, **Enviar relatório** > só feedback > "teste". Deve aparecer um código `KTH-...` e uma issue nova no
  repositório privado.

## Ler o que chegou
`python3 scripts/relatorios.py --repo kessleru/katharos-relatorios` baixa os envios (pelo `gh`, com a sua conta) e escreve
`relatorios-resumo.md`: os erros mais comuns, o que cada otimização rendeu em todos os PCs, os itens que não ficam, o feedback e a
lista do que melhorar primeiro.

## Apagar um envio
Quem mandou pede pelo código `KTH-...`. Apague o arquivo `relatorios/.../KTH-....json` e a issue com esse código.
