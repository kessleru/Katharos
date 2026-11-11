# ──────────────────────────────────────────────────────────────────────────────
# Aviso de uso: o que a pessoa precisa saber antes de mudar o Windows, dito em poucas linhas.
# Aparece uma vez (com aceite digitado) antes de qualquer comando que muda o PC, e a qualquer hora em "aviso".
# ──────────────────────────────────────────────────────────────────────────────

VERSAO_AVISO = 1   # sobe quando o texto muda de um jeito que pede um novo aceite

AVISO_PONTOS = [
    ('O que ele faz',
     'O Katharos muda configurações do Windows: serviços, tarefas, registro, rede, energia e, se você marcar, remove programas. '
     'É para quem quer escolher o que muda. Cada item diz o que faz (? e o número) e mostra o código (v e o número).'),
    ('Como voltar',
     'Tudo que ele muda guarda o valor anterior e volta com "desfazer". A exceção são os itens marcados "sem volta" '
     '(remover programas e apps, apagar arquivos): esses não voltam. Antes de mexer a fundo, crie um ponto de restauração '
     '("restaurar") e salve o que for importante.'),
    ('Onde não usar',
     'Não use em computador de trabalho, de escola ou de outra pessoa sem a autorização de quem cuida dele. '
     'Programas de empresa, VPN e antivírus corporativo podem parar de funcionar com ajustes de desempenho ou privacidade.'),
    ('Sem garantia',
     'É um programa gratuito, entregue "como está", sem garantia de funcionar no seu PC, de dar ganho de desempenho ou de '
     'ser compatível com tudo. Você usa por sua conta e risco: o autor não responde por perda de dados, falhas ou outros '
     'danos que venham do uso. Isto não tira os direitos que a lei garante a você.'),
    ('Jogos',
     'Itens de jogo podem conflitar com anti-cheat: se o seu jogo usa, leia o aviso do item antes. '
     'O Katharos não tem ligação com a Microsoft, a Steam nem com nenhum jogo ou fabricante.'),
    ('Na dúvida',
     'Comece pelo "raiox" (só lê), use o modo seguro e rode com --teste: ele mostra o que faria sem mudar nada.'),
]

# Comandos que só leem ou que protegem (desfazer nunca pode ficar atrás de um aviso): não pedem o aceite.
SEM_ACEITE = {'autenticidade', 'versoes', 'provas', 'buscar', 'aviso', 'ajuda', 'raiox', 'painel', 'saude', 'conselheiro', 'tendencia', 'estado', 'relatorio', 'cartao',
              'benchmark', 'verificar', 'config', 'desfazer', 'socorro', 'retomar', 'restaurar', 'amostrar', 'manutencao', 'travadas'}


def aviso_aceito():
    a = estado().get('aviso_aceito')
    return isinstance(a, dict) and a.get('versao', 0) >= VERSAO_AVISO


def mostra_aviso(t):
    """O texto do aviso, na tela."""
    t.titulo('antes de usar')
    for titulo, texto in AVISO_PONTOS:
        t.escreve('  ' + t.p(titulo, 'destaque', True))
        t.paragrafo(texto, 4, 'sub')
        t.escreve()


def pede_aceite(ctx):
    """Mostra o aviso e só segue se a pessoa digitar "entendi". Devolve True se pode seguir."""
    t = ctx.t
    t.limpa()
    t.logo('KATHAROS')
    mostra_aviso(t)
    if not mostra_autenticidade_no_aceite(t):
        return False
    if t.confirma('Li o aviso e quero continuar.', palavra='entendi'):
        marca_estado('aviso_aceito', {'versao': VERSAO_AVISO, 'quando': agora_iso()})
        return True
    t.nota('Sem o aceite o Katharos não muda nada. Você pode ler de novo com "katharos aviso".', 2)
    return False


def ferramenta_aviso(ctx, args):
    t = ctx.t
    mostra_aviso(t)
    t.nota('  A licença e o aviso completo estão no arquivo LICENSE e na seção "Antes de usar" do README.', 2)
    return 0
