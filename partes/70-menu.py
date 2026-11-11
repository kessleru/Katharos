

# ███████████████████████████████████████████████████████████████████████████
#
#   PARTE 5 · MENU E ENTRADA
#
# ███████████████████████████████████████████████████████████████████████████

class Ctx:
    def __init__(self, args, t):
        self.args, self.t = args, t
        self.perfil = None
        self.mult = 1.0
        self.achados = []
        self.proximos = []


def ferramenta_config(ctx, args):
    t = ctx.t
    t.aba('preferências que valem em toda execução')
    chave, valor = getattr(args, 'chave', None), getattr(args, 'valor', None)
    validos = VALIDOS_CONFIG
    if chave:
        if chave not in PADROES:
            t.erro(f'"{chave}" não existe. Opções: ' + ', '.join(PADROES))
            return 1
        if valor and chave in validos and valor not in validos[chave]:
            t.erro(f'valores aceitos para {chave}: ' + ', '.join(validos[chave]))
            return 1
        if chave == 'grandes-mb' and valor and not valor.isdigit():
            t.erro('use um número de MB.')
            return 1
        if chave == 'energia-automatica' and valor:   # escolhe os planos e guarda o de antes: não é só gravar a preferência
            return liga_energia_automatica(ctx, args) if valor == 'sim' else desliga_energia_automatica(ctx)
        salva_config(chave, valor)
        if exe_instalado().is_file():
            escreve_config_sp()
        t.ok(f'{chave} = {config(chave)}')
        return 0
    while True:
        t.titulo('preferências')
        for i, (k, (rot, desc)) in enumerate(DESCR_CONFIG.items(), 1):
            t.item(t.p(f'{i:>2}', 'destaque', True), None, rot, t.p(str(config(k)), 'texto'))
            t.paragrafo(desc, 6, 'apagado')
        t.titulo('modos')
        for nome, cor, txt in EXPLICA_MODOS:
            t.item('·', cor, nome)
            t.paragrafo(txt, 6, 'apagado')
        if not t.interativo:
            return 0
        t.escreve()
        r = t.pergunta('mudar qual (número; Enter = voltar)').strip()
        if not r.isdigit() or not 0 < int(r) <= len(DESCR_CONFIG):
            return 0
        k = list(DESCR_CONFIG)[int(r) - 1]
        if k == 'energia-automatica':
            (desliga_energia_automatica(ctx) if config(k, 'nao') == 'sim' else liga_energia_automatica(ctx, args))
            continue
        if k in validos:
            ops = validos[k]
            atual = config(k)
            novo = ops[(ops.index(atual) + 1) % len(ops)] if atual in ops else ops[0]
        else:
            novo = t.pergunta(f'{k} (Enter = padrão {PADROES[k]})').strip()
        salva_config(k, novo)
        if exe_instalado().is_file():
            escreve_config_sp()
        t.ok(f'{DESCR_CONFIG[k][0]}: {config(k)}')


# Todos os comandos, em grupos. O menu de abertura mostra só o MENU (seis linhas); os outros ficam em duas telas:
# "escolher" (as áreas com itens para marcar) e "mais" (as ferramentas). Qualquer nome vale em qualquer tela.
GRUPOS = [
    ('comece por aqui', 'o raio-x diz o que vale a pena; o turbo faz tudo de uma vez', [
        ('raiox', 'nota do PC e o que fazer primeiro (só lê)', 'ferramenta_raiox'),
        ('turbo', 'otimiza tudo de uma vez, no modo que você escolher', 'ferramenta_turbo'),
    ]),
    ('medir', 'só olha, não muda nada', [
        ('medir', 'CPU, RAM, disco e temperatura agora', 'ferramenta_medir'),
        ('benchmark', 'velocidade de disco, CPU e RAM, antes e depois', 'ferramenta_benchmark'),
        ('provas', 'o que cada item rendeu de verdade neste PC', 'ferramenta_provas'),
        ('memoria', 'quem usa a RAM e o que liberar', 'ferramenta_memoria'),
    ]),
    ('acompanhamento', 'o PC ao vivo e ao longo do tempo', [
        ('segundo-plano', 'rodar em segundo plano: ícone, ao vivo e jogos', 'ferramenta_segundo_plano'),
        ('aovivo', 'métricas em tempo real aqui no terminal', 'ferramenta_aovivo'),
        ('painel', 'gráficos do PC ao longo do tempo, no navegador', 'ferramenta_painel'),
        ('tendencia', 'o PC está piorando com o tempo?', 'ferramenta_tendencia'),
        ('conselheiro', 'central de inteligência: propõe com base nas medidas', 'ferramenta_conselheiro'),
        ('saude', 'erros do Windows, drivers e o que ajustar', 'ferramenta_saude'),
        ('agendar', 'manutenção sozinha: semanal, diária ou contínua', 'ferramenta_agendar'),
    ]),
    ('segurança', 'só olha, não muda nada', [
        ('seguranca', 'auditoria: o que está fraco na segurança', 'ferramenta_seguranca'),
        ('portas', 'quem escuta em cada porta, e para quem', 'ferramenta_portas'),
        ('segredos', 'chaves esquecidas nos seus projetos', 'ferramenta_segredos'),
    ]),
    ('espaço', 'arquivos seus vão para a Lixeira ou voltam com desfazer', [
        ('limpar', 'temporários, caches e restos', 'pacote'),
        ('grandes', 'arquivos grandes e duplicados', 'ferramenta_grandes'),
        ('organizar', 'área de trabalho em pastas, com desfazer', 'ferramenta_organizar'),
    ]),
    ('deixar mais leve', 'menos coisa rodando em segundo plano', [
        ('inicializacao', 'o que abre junto com o Windows', 'pacote'),
        ('programas', 'bloatware e antivírus de fábrica', 'pacote'),
        ('apps', 'apps pré-instalados da Loja', 'pacote'),
        ('servicos', 'serviços que este PC não usa', 'pacote'),
        ('visual', 'efeitos, animações e transparência', 'pacote'),
    ]),
    ('privacidade e IA', 'menos coleta de dados, anúncios e IA', [
        ('privacidade', 'telemetria, anúncios e sugestões', 'pacote'),
        ('ia', 'Copilot, Recall e IA do Windows', 'pacote'),
        ('navegador', 'Chrome, Edge e Brave mais leves', 'pacote'),
    ]),
    ('desempenho', 'energia, disco e internet', [
        ('energia', 'plano de energia, turbo e USB', 'pacote'),
        ('disco', 'menos escrita, boot mais rápido', 'pacote'),
        ('rede', 'DNS mais rápido e medição de ping', 'pacote'),
        ('jogos', 'FPS e latência em qualquer jogo: Modo de Jogo, entrada', 'pacote'),
    ]),
    ('manutenção', 'quando algo quebra ou envelhece', [
        ('reparar', 'DISM, SFC, chkdsk, rede e Update', 'pacote'),
        ('atualizar', 'Windows, drivers e programas', 'pacote'),
    ]),
    ('gosto pessoal', 'aparência e atalhos; nada aqui vem marcado', [
        ('ajustes', 'barra, relógio, Num Lock, atualizações', 'pacote'),
        ('interface', 'área de trabalho e atalhos do Edge', 'pacote'),
    ]),
    ('voltar atrás', 'ver o que mudou e voltar', [
        ('desfazer', 'volta qualquer mudança, valor por valor', 'ferramenta_desfazer'),
        ('socorro', 'o PC ficou estranho: volta tudo de uma vez', 'ferramenta_socorro'),
        ('retomar', 'termina o que ficou pela metade', 'ferramenta_retomar'),
        ('restaurar', 'pontos de restauração do Windows', 'ferramenta_restaurar'),
        ('aplicado', 'a lista do que este PC já tem feito, área por área', 'ferramenta_aplicado'),
        ('verificar', 'confere se o que foi aplicado continua valendo', 'ferramenta_verificar'),
        ('estado', 'o que já foi aplicado neste PC', 'ferramenta_estado'),
    ]),
    ('resultado', 'mostrar o que mudou e levar para outro PC', [
        ('cartao', 'antes e depois, num cartão para mostrar', 'ferramenta_cartao'),
        ('relatorio', 'o relatório único: copiar para a IA ou salvar', 'ferramenta_relatorio'),
        ('exportar', 'salva o que foi aplicado, para repetir em outro PC', 'ferramenta_exportar'),
        ('importar', 'aplica um arquivo exportado (ou o relatório)', 'ferramenta_importar'),
    ]),
    ('preferências', 'como o Katharos se comporta neste PC', [
        ('atalhos', 'pasta Katharos na área de trabalho, com ícone', 'ferramenta_atalhos'),
        ('config', 'modo padrão e preferências', 'ferramenta_config'),
        ('buscar', 'acha um ajuste ou comando pelo nome', 'ferramenta_buscar'),
        ('versoes', 'versões que já rodaram aqui e o que está guardado', 'ferramenta_versoes'),
        ('aviso', 'leia antes de usar: riscos e responsabilidade', 'ferramenta_aviso'),
        ('autenticidade', 'confere se este programa é o que o autor publicou', 'ferramenta_autenticidade'),
        ('ajuda', 'os passos mais comuns, em poucas linhas', 'ferramenta_ajuda'),
    ]),
]
# O menu de abertura: poucas linhas. "escolher" e "mais" abrem as telas com o resto.
MENU = [
    ('raiox', 'nota do PC e o que fazer primeiro (só lê)'),
    ('turbo', 'otimiza tudo de uma vez, no modo que você escolher'),
    ('escolher', 'otimiza por área: você escolhe a área e os itens'),
    ('painel', 'gráficos do PC ao longo do tempo, no navegador'),
    ('desfazer', 'volta qualquer mudança'),
    ('mais', 'medir, acompanhamento, segurança, preferências...'),
]
TELAS = ('escolher', 'mais')


def grupos_da_tela(tela):
    """Os grupos de uma tela do menu: "escolher" = só as áreas com itens para marcar; "mais" = as ferramentas
    que não estão no menu de abertura. Grupo vazio some."""
    no_menu = {c for c, _ in MENU}
    out = []
    for titulo, expl, itens in GRUPOS:
        if tela == 'escolher':
            fica = [(c, d) for c, d, f in itens if f == 'pacote' and c not in no_menu]
        else:
            fica = [(c, d) for c, d, f in itens if f != 'pacote' and c not in no_menu]
        if fica:
            out.append((titulo, expl, fica))
    return out


COMANDOS = {cmd: (desc, f) for _, _, itens in GRUPOS for cmd, desc, f in itens}
COMANDOS['manutencao'] = ('a manutenção em si (a tarefa agendada chama)', 'ferramenta_manutencao')
COMANDOS['bandeja'] = ('o ícone do Katharos perto do relógio (o mesmo que segundo-plano)', 'ferramenta_segundo_plano')
COMANDOS['amostrar'] = ('uma leitura leve do sistema (a tarefa de 15 min chama)', 'ferramenta_amostrar')
SEM_ESTADO = {'aplicado', 'bandeja', 'segundo-plano', 'aovivo', 'autenticidade', 'versoes', 'provas', 'buscar', 'aviso', 'amostrar', 'saude', 'conselheiro', 'painel', 'tendencia', 'ajuda', 'config', 'estado', 'desfazer', 'socorro', 'retomar', 'restaurar', 'relatorio', 'cartao', 'benchmark'}


# comandos depois dos quais o motor de inteligência pensa de novo (evento "aplicou" ou "desfez")
MUDAM_O_PC = {cmd for _, _, itens in GRUPOS for cmd, _, f in itens if f == 'pacote'} | {'turbo', 'desfazer', 'restaurar', 'retomar'}


def roda_ferramenta(ctx, args, abre=True):
    t = ctx.t
    desc, f = COMANDOS[args.comando]
    if abre:
        extra = (f'modo {getattr(args, "modo", None) or config("modo")}' if f in ('pacote', 'ferramenta_turbo') else '')
        t.cabecalho(args.comando, ' · '.join(x for x in (extra, 'teste: nada é alterado' if args.teste else '') if x), app=APP)
    if not getattr(args, 'teste', False) and args.comando not in SEM_ESTADO:
        antes = (estado().get('duracoes') or {}).get(args.comando)
        if antes and antes > 20:
            t.nota(f'  Da última vez, neste PC, levou cerca de {duracao(antes)}.')
        if f in ('pacote', 'ferramenta_turbo') and not bench_salvos():
            t.nota('  Para medir o ganho com número, rode "benchmark" antes e depois (leva cerca de 1 minuto).')
    inicio = time.time()
    trava = None
    if args.comando not in SEM_ESTADO and not getattr(args, 'teste', False) and not getattr(args, 'codigo', False):
        trava = Trava()
        if not trava.pega():
            t.aviso(f'Outra janela do Katharos está aplicando mudanças agora (processo {trava.dona}). Espere ela terminar '
                    'ou feche-a, para as duas não escreverem no mesmo backup.')
            return 1
    try:
        cod = ferramenta_pacote(ctx, args, args.comando) if f == 'pacote' else globals()[f](ctx, args)
    except KeyboardInterrupt:
        t.fim('interrompido', 'erro')
        return 130
    finally:
        if trava:
            trava.solta()
    if args.comando not in SEM_ESTADO:
        e = estado()
        e.setdefault('usado', {})[args.comando] = agora_iso()
        gasto = time.time() - inicio
        if not cod and gasto > 5:
            e.setdefault('duracoes', {})[args.comando] = round(gasto)
        salva_estado(e)
    if args.comando in MUDAM_O_PC and not getattr(args, 'teste', False):
        try:   # o motor pensa logo depois de uma mudança (o ícone mostra as propostas novas), não no próximo relógio
            marca_propostas_feitas(args.comando)
            publica_evento('desfez' if args.comando == 'desfazer' else 'aplicou', {'comando': args.comando, 'pela': 'terminal'})
            exporta_propostas(ctx)
        except Exception as ex:
            LOG.escreve(f'pensar depois de {args.comando}: {ex!r}')
    rel_fim(ctx, args, inicio)
    t.fim(('concluído em ' if not cod else 'terminou com pendências · ') + duracao(time.time() - inicio), 'ok' if not cod else 'aviso')
    return cod or 0


def monta_parser():
    comum = argparse.ArgumentParser(add_help=False)
    comum.add_argument('--ascii', action='store_true', help='só caracteres simples (terminal que mostra quadradinhos)')
    comum.add_argument('--sem-cor', action='store_true', help='sem cores')
    comum.add_argument('--teste', action='store_true', help='só mostra o que faria, sem alterar nada')
    comum.add_argument('--sim', action='store_true', help='não pergunta: aplica o que o modo marca')
    comum.add_argument('--modo', choices=MODOS, help='seguro, equilibrado ou extremo (padrão: o da config)')
    comum.add_argument('--copiar', action='store_true', help='no fim, copia o relatório único para colar numa conversa com a IA')
    comum.add_argument('--salvar', metavar='PASTA', help='no fim, salva uma cópia do relatório único nesta pasta (ex.: o cofre)')
    comum.add_argument('--abrir', action='store_true', help='no fim, abre a pasta com o relatório selecionado')
    comum.add_argument('--codigo', action='store_true', help='mostra o PowerShell de cada item escolhido e não aplica nada')
    depois = argparse.ArgumentParser(add_help=False)
    for nome in ('--ascii', '--sem-cor', '--teste', '--sim', '--copiar', '--codigo', '--abrir'):
        depois.add_argument(nome, action='store_true', default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    depois.add_argument('--modo', choices=MODOS, default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    depois.add_argument('--salvar', metavar='PASTA', default=argparse.SUPPRESS, help=argparse.SUPPRESS)

    p = argparse.ArgumentParser(prog='katharos', parents=[comum],
                                description='Deixa qualquer Windows mais leve: diagnóstico, limpeza, programas, serviços, '
                                            'privacidade, energia, disco, reparo e manutenção. Sem comando, abre o menu.')
    p.add_argument('--versao', action='version', version=f'katharos {VERSAO} ({DATA_VERSAO})')
    p.add_argument('--sha256', action='store_true', help='mostra o SHA-256 deste arquivo, para comparar com o SHA256SUMS.txt do repositório')
    sub = p.add_subparsers(dest='comando', metavar='comando')
    r = sub.add_parser('raiox', parents=[depois], help='diagnóstico completo com nota e recomendações (só leitura)')
    r.add_argument('--queixas', metavar='LISTA', help='lento,boot,disco,calor,bateria,jogos,privacidade,tudo')
    sub.add_parser('medir', parents=[depois], help='medidas agora, comparadas com a primeira')
    pb = sub.add_parser('benchmark', parents=[depois], help='disco, CPU e RAM com repetição, comparado com o anterior')
    pb.add_argument('--completo', action='store_true', help='mais rodadas e o teste de todos os núcleos (leva alguns minutos); o padrão é o leve, cerca de 1 minuto, sem estresse')
    td = sub.add_parser('tendencia', parents=[depois], help='mostra se algo está piorando com o tempo, pelas medidas do segundo plano')
    td.add_argument('--agora', action='store_true', help='grava uma medida agora antes de mostrar')
    sd = sub.add_parser('saude', parents=[depois], help='erros do Windows, drivers e o que o sistema precisa ajustar (só lê)')
    sd.add_argument('--ultimo', action='store_true', help='mostra o último retrato em vez de ler os logs de novo')
    cs = sub.add_parser('conselheiro', parents=[depois], help='propõe mudanças com base nas medidas do segundo plano (não aplica nada)')
    cs.add_argument('--dispensar', metavar='ID', help='esconde uma proposta por 30 dias')
    cs.add_argument('--resposta', nargs=2, metavar=('ID', 'RESPOSTA'), help='diz se uma proposta ajudou: sim, nao ou nao-importa')
    cs.add_argument('--exportar', action='store_true', help='só grava as propostas em ~/.katharos/propostas.json (o ícone do segundo plano mostra)')
    pn = sub.add_parser('painel', parents=[depois], help='gera o painel de gráficos (HTML) e abre no navegador')
    pn.add_argument('--nao-abrir', action='store_true', help='só gera o arquivo')
    pn.add_argument('--ativar-cliques', action='store_true', help='liga os botões Corrigir/Abrir do painel (registra katharos:// só para você)')
    pn.add_argument('--desativar-cliques', action='store_true', help='remove o link katharos:// do registro')
    sub.add_parser('ajuda', parents=[depois], help='os passos mais comuns')
    sub.add_parser('versoes', parents=[depois], help='as versões do Katharos que já rodaram neste PC e o que cada troca preservou')
    sub.add_parser('provas', parents=[depois], help='o que cada item rendeu, medido neste PC: na hora e depois de reiniciar')
    sub.add_parser('aviso', parents=[depois], help='o aviso de uso: riscos e responsabilidade')
    au = sub.add_parser('autenticidade', parents=[depois], help='confere se este programa é o que o autor publicou (SHA-256, local e online)')
    au.add_argument('--offline', action='store_true', help='não baixa a lista oficial; só compara com o SHA256SUMS.txt que veio junto')
    rt = sub.add_parser('retomar', parents=[depois], help='termina o que ficou pela metade se o PC travou no meio de uma aplicação')
    rt.add_argument('--descartar', action='store_true', help='esquece a anotação do que ficou pela metade')
    sub.add_parser('socorro', parents=[depois], help='desfaz tudo o que o Katharos mudou e explica o ponto de restauração')
    sub.add_parser('memoria', parents=[depois], help='uso da RAM e limpeza da memória em espera')
    tb = sub.add_parser('turbo', parents=[depois], help='otimiza tudo em sequência, retomando depois de reiniciar')
    tb.add_argument('--continuar', action='store_true', help='continua um turbo pela metade (a tarefa agendada usa)')
    tb.add_argument('--plano', metavar='ARQUIVO', help='usa as escolhas salvas de outro turbo (para repetir em outros PCs, sem perguntas)')
    tb.add_argument('--foco', choices=['geral', 'jogos', 'jogos-max'], help=argparse.SUPPRESS)   # da 2.5.0: os jogos vêm no modo
    for cmd, desc, f in (x for _, _, itens in GRUPOS for x in itens):
        if f == 'pacote':
            sub.add_parser(cmd, parents=[depois], help=desc)
    g = sub.add_parser('grandes', parents=[depois], help='arquivos grandes, duplicados e instaladores velhos (vão para a Lixeira)')
    g.add_argument('pastas', nargs='*', help='onde procurar (padrão: suas pastas pessoais)')
    g.add_argument('--mb', type=int, help='tamanho mínimo em MB (padrão 500 ou o da config)')
    sp = sub.add_parser('segundo-plano', parents=[depois], help='acompanhamento em segundo plano: ícone perto do relógio, métricas ao vivo e sessões de jogo')
    sp.add_argument('--ligar', action='store_true', help='liga, abre com o Windows e mostra o painel ao vivo')
    sp.add_argument('--desligar', action='store_true', help='fecha e tira da inicialização')
    sp.add_argument('--intervalo', choices=['1', '2', '5', '10'], help='de quantos em quantos segundos lê o PC')
    av = sub.add_parser('aovivo', parents=[depois], help='métricas em tempo real no terminal (Ctrl+C sai)')
    av.add_argument('--segundos', type=int, default=0, help='mostra só esta quantidade de leituras e sai')
    a = sub.add_parser('agendar', parents=[depois], help='segundo plano: liga a manutenção sozinha (semanal, diária ou contínua), roda agora ou desliga')
    a.add_argument('--frequencia', choices=['semanal', 'diaria', 'continua'], help='quando o segundo plano roda: semanal (domingo), diaria ou continua (ao iniciar com o Windows e a cada 4 h)')
    a.add_argument('--agora', action='store_true', help='roda a manutenção agora')
    a.add_argument('--remover', action='store_true', help='remove a tarefa agendada')
    sub.add_parser('restaurar', parents=[depois], help='pontos de restauração do Windows')
    d = sub.add_parser('desfazer', parents=[depois], help='desfaz pacotes (nome do pacote ou "tudo")')
    d.add_argument('pacotes', nargs='*', help='ex.: servicos privacidade, ou tudo')
    sub.add_parser('estado', parents=[depois], help='o que já foi aplicado')
    at = sub.add_parser('atalhos', parents=[depois], help='pasta Katharos na área de trabalho, com atalhos que têm o ícone')
    at.add_argument('--remover', action='store_true', help='tira a pasta Katharos da área de trabalho')
    ex = sub.add_parser('exportar', parents=[depois], help='salva o que está aplicado neste PC, para repetir em outro')
    ex.add_argument('alvo', nargs='?', help='arquivo de destino (padrão: katharos-exportado.json na sua pasta)')
    bu = sub.add_parser('buscar', parents=[depois], help='acha um ajuste ou um comando pelo que você digitar')
    bu.add_argument('texto', nargs='*', help='o que procurar (ex.: telemetria, anúncios, boot)')
    im = sub.add_parser('importar', parents=[depois], help='aplica neste PC um arquivo exportado (ou o relatório único)')
    im.add_argument('alvo', nargs='?', help='o arquivo .json exportado, ou o relatório .md')
    sub.add_parser('seguranca', parents=[depois], help='auditoria de segurança (só lê)')
    po = sub.add_parser('portas', parents=[depois], help='quem escuta em cada porta, e para quem')
    po.add_argument('filtro', nargs='?', help='só esta porta (ex.: 3000)')
    sg = sub.add_parser('segredos', parents=[depois], help='chaves e senhas esquecidas em arquivos dos seus projetos')
    sg.add_argument('pastas', nargs='*', help='onde procurar (padrão: Dev, Projects, Documentos, Desktop)')
    org = sub.add_parser('organizar', parents=[depois], help='organiza os arquivos soltos da área de trabalho, com desfazer')
    org.add_argument('--dias', type=int, help='deixa quieto o que foi mexido nos últimos N dias (padrão 1)')
    org.add_argument('--atalhos', action='store_true', help='também junta os atalhos numa pasta')
    org.add_argument('--desfazer', action='store_true', help='põe de volta o que a última organização moveu')
    sub.add_parser('aplicado', parents=[depois], help='a lista do que este PC já tem feito, área por área')
    sub.add_parser('verificar', parents=[depois], help='confere se o que foi aplicado continua valendo')
    sub.add_parser('cartao', parents=[depois], help='antes e depois, num cartão')
    re_ = sub.add_parser('relatorio', parents=[depois], help='o relatório único: copiar, salvar ou apagar')
    re_.add_argument('--zerar', action='store_true', help='apaga o relatório e recomeça')
    c = sub.add_parser('config', parents=[depois], help='preferências (sem nada: mostra e deixa mudar)')
    c.add_argument('chave', nargs='?', help=', '.join(PADROES))
    c.add_argument('valor', nargs='?', help='valor novo (vazio volta ao padrão)')
    m = sub.add_parser('manutencao', parents=[depois], help='a manutenção em si (a tarefa agendada chama)')
    m.add_argument('--agendada', action='store_true', help=argparse.SUPPRESS)
    am = sub.add_parser('amostrar', parents=[depois], help='uma leitura leve do sistema, somada ao histórico por hora (a tarefa de 15 min chama)')
    am.add_argument('--agendada', action='store_true', help=argparse.SUPPRESS)
    bj = sub.add_parser('bandeja', parents=[depois], help='o ícone do Katharos perto do relógio, com a última leitura e atalhos')
    bj.add_argument('--parar', action='store_true', help='fecha o ícone e tira da inicialização')
    bj.add_argument('--agendada', action='store_true', help=argparse.SUPPRESS)
    return p


def _defaults(args):
    for k, v in (('pastas', []), ('mb', None), ('agora', False), ('remover', False), ('pacotes', []), ('chave', None),
                 ('valor', None), ('continuar', False), ('plano', None), ('foco', None), ('agendada', False), ('queixas', None), ('salvar', None),
                 ('copiar', False), ('codigo', False), ('filtro', None), ('dias', None), ('atalhos', False), ('desfazer', False),
                 ('zerar', False), ('acao', None), ('alvo', None)):
        if not hasattr(args, k):
            setattr(args, k, v)
    return args


def proximo_passo(e=None, raiox=None, agora=None):
    """O próximo passo que faz sentido para este PC, pelo que já foi feito: (comando, frase) ou None.
    A ordem é o caminho de quem chega: medir, aplicar o que o raio-x apontou, conferir o ganho, deixar no automático."""
    e = estado() if e is None else e
    agora = agora or datetime.now()
    usados = e.get('usado') or {}
    if not usados.get('raiox'):
        return ('raiox', 'comece medindo o PC: leva cerca de 1 minuto e não muda nada')
    if raiox is None:
        try:
            raiox = ((rel_carrega().get('secoes') or {}).get('raiox') or {}).get('dados') or {}
        except Exception:
            raiox = {}
    aplicados = {n for n, r in (e.get('pacotes') or {}).items() if isinstance(r, dict) and not r.get('revertido')}
    for a in sorted(raiox.get('achados') or [], key=lambda a: -int(a.get('impacto') or 0)):
        cmd = str(a.get('comando') or '')
        if cmd in COMANDOS and cmd not in aplicados and int(a.get('impacto') or 0) >= 2 and not usados.get(cmd):
            return (cmd, f'o raio-x apontou: {str(a.get("titulo") or "").lower()}')
    def dias(cmd):
        try:
            return (agora - datetime.fromisoformat(str(usados.get(cmd)))).days
        except (TypeError, ValueError):
            return None
    if aplicados and dias('raiox') is not None:
        try:
            ultimo = max(datetime.fromisoformat(str(r.get('quando'))) for n, r in (e.get('pacotes') or {}).items() if n in aplicados and r.get('quando'))
            if ultimo > datetime.fromisoformat(str(usados['raiox'])) and not (usados.get('medir') and datetime.fromisoformat(str(usados['medir'])) > ultimo):
                return ('medir', 'veja o antes e depois do que você aplicou')
        except (TypeError, ValueError):
            pass
    if len(aplicados) >= 2 and not e.get('manut_freq'):
        return ('agendar', 'deixe a manutenção rodar sozinha, com o PC parado')
    if (dias('raiox') or 0) >= 30:
        return ('raiox', f'o último raio-x foi há {dias("raiox")} dias: veja como o PC está agora')
    return None


def primeira_vez(ctx, args=None):
    """Na primeira abertura: oferece o atalho com ícone na área de trabalho. Nada mais é perguntado."""
    t = ctx.t
    if not WINDOWS or not t.interativo or estado().get('primeira_vez'):
        return None
    marca_estado('primeira_vez', agora_iso())
    if estado().get('atalhos_criados'):
        return None
    t.limpa()
    t.logo('KATHAROS')
    t.titulo('atalho na área de trabalho')
    t.paragrafo('Posso criar uma pasta "Katharos" na sua área de trabalho, com o ícone, um atalho para abrir o menu e outro '
                'para desfazer tudo. Os relatórios ficam na pasta que você baixou, em "relatorios": deixe ela onde está.', 2, 'sub')
    if t.confirma('Criar a pasta Katharos na área de trabalho?'):
        s = cria_atalhos(ctx, ['menu', 'normal'])
        if s.ok:
            marca_estado('atalhos_criados', agora_iso())
    return None


def _roda_do_menu(ctx, parser, args, cmd, extra=()):
    """Roda um comando escolhido no menu e, se o raio-x sugeriu telas, oferece uma de cada vez."""
    t = ctx.t
    try:
        sub_args = _defaults(parser.parse_args([cmd, *extra]))
    except SystemExit:
        return
    for k in ('ascii', 'sem_cor', 'teste', 'sim', 'modo'):
        if getattr(args, k, None):
            setattr(sub_args, k, getattr(args, k))
    t.limpa()
    roda_ferramenta(ctx, sub_args)
    while ctx.proximos:
        prox = ctx.proximos.pop(0)
        if prox not in COMANDOS:
            continue
        t.escreve(guia=False)
        direto, ctx.direto = getattr(ctx, 'direto', False), False
        try:
            if direto:   # a busca já perguntou qual abrir
                r = ''
            else:
                t.dicas([('Enter', 'abrir'), ('p', 'pular'), ('v', 'voltar ao menu')])
                r = t.pergunta(f'próxima sugestão: {prox}').strip().lower()
            if r in ('p', 'pular'):
                continue
            if r in ('v', 'voltar'):
                ctx.proximos = []
                break
        except KeyboardInterrupt:
            ctx.proximos = []
            break
        sa = _defaults(parser.parse_args([prox]))
        for k in ('ascii', 'sem_cor', 'teste', 'sim', 'modo'):
            if getattr(args, k, None):
                setattr(sa, k, getattr(args, k))
        roda_ferramenta(ctx, sa)
    t.escreve(guia=False)
    t.espera('Enter para voltar ao menu')


def menu(ctx, parser, args, tela=None):
    """O menu, em três níveis curtos: a abertura (seis linhas), a tela "escolher" ou "mais" (uma linha por grupo)
    e o grupo (os comandos dele). Em qualquer nível vale o número da linha ou o nome de qualquer comando."""
    t = ctx.t
    aviso = ''
    grupo = None   # (título, explicação, [(comando, descrição)]) quando um grupo está aberto
    primeira_vez(ctx)
    avisa_janelas(ctx)
    while True:
        usados = estado().get('usado', {})
        t.limpa()
        t.logo('KATHAROS')
        extra = ' · '.join(x for x in ((f'modo {config("modo")}' if config('modo') != PADROES['modo'] else ''), ('sem administrador' if WINDOWS and not eh_admin() else '')) if x)
        t.cabecalho('início' if not tela else (tela if not grupo else f'{tela} › {grupo[0]}'), extra, app=APP)
        if not WINDOWS:
            t.aviso('Este computador não é Windows: dá para ver o menu, mas os comandos só funcionam no Windows.')
        quando = {c: ha_quanto_iso(q) for c, q in usados.items()}
        grupos = grupos_da_tela(tela) if tela else []
        passo = None
        if not tela:
            try:
                passo = proximo_passo()
            except Exception as ex:   # a dica nunca pode derrubar o menu
                LOG.escreve(f'próximo passo falhou: {ex!r}')
            por_numero = t.menu_itens([('', '', MENU)], quando)
            if passo:
                t.escreve(f'  {t.p("próximo passo", "destaque", True)}  {t.p(passo[0], "texto")}  {t.p("(Enter)", "apagado")}')
                t.paragrafo(passo[1][0].upper() + passo[1][1:] + '.', 2, 'apagado')
                t.escreve()
        elif grupo:
            if grupo[1]:
                t.paragrafo(grupo[1], 2, 'apagado')
                t.escreve()
            lista = grupo[2]
            por_numero = t.menu_itens([('', '', lista)], quando, zero='voltar')
        else:
            t.paragrafo('Escolha uma área. Dentro dela os itens já vêm marcados pelo modo, e você tira ou põe o que quiser.'
                        if tela == 'escolher' else 'As outras ferramentas, por assunto.', 2, 'apagado')
            t.escreve()
            por_numero = t.menu_itens([('', '', [(g[0], ' · '.join(c for c, _ in g[2])) for g in grupos])], zero='voltar')
        if aviso:
            t.aviso(aviso)
            aviso = ''
        if ctx.proximos:
            t.info('sugeridos pelo raio-x: ' + ' · '.join(ctx.proximos))
            t.escreve()
        if not tela:
            t.dicas([('número ou nome', 'abre'), ('qualquer palavra', 'procura um ajuste')])
        escolha = t.pergunta('o que fazer').strip().lower()
        if escolha == '' and passo and not tela:   # Enter segue o próximo passo
            escolha = passo[0]
        if escolha in ('', '0', 'q', 'sair', 'v', 'voltar'):
            if grupo:
                grupo = None
            elif tela:
                grupo = None
                tela = None
            else:
                t.fim('até mais', 'nada')
                return 0
            continue
        cmd = por_numero.get(escolha) or (escolha if escolha in COMANDOS or escolha in TELAS else None)
        if cmd and tela and not grupo and cmd not in COMANDOS and cmd not in TELAS:   # uma linha de grupo
            g = next(x for x in grupos if x[0] == cmd)
            if len(g[2]) > 1:
                grupo = g
                continue
            cmd = g[2][0][0]   # grupo de um comando só: abre direto
        if not cmd:
            perto = comando_parecido(escolha)
            if not perto and len(escolha) >= 3 and not escolha.isdigit():   # não é comando: procura nos ajustes
                try:
                    _roda_do_menu(ctx, parser, args, 'buscar', extra=escolha.split())
                except KeyboardInterrupt:
                    return 130
                continue
            aviso = f'"{corta(escolha, 20)}" não é uma das opções.' + (f' Você quis dizer "{perto}"?' if perto else '')
            continue
        if cmd in TELAS:
            tela, grupo = cmd, None
            continue
        try:
            _roda_do_menu(ctx, parser, args, cmd)
        except KeyboardInterrupt:
            return 130


def comando_parecido(texto):
    """O comando mais parecido com o que foi digitado, ou None."""
    import difflib
    perto = difflib.get_close_matches(texto.lower(), list(COMANDOS), n=1, cutoff=0.6)
    return perto[0] if perto else None


def ferramenta_ajuda(ctx, args):
    t = ctx.t
    t.aba('o essencial, em poucas linhas')
    passos = [
        ('raiox', 'mede o PC, dá uma nota e diz o que fazer primeiro. Não muda nada.'),
        ('turbo', 'otimiza tudo de uma vez. Você escolhe o modo (seguro, equilibrado ou extremo) e vê o plano antes de aplicar.'),
        ('escolher', 'no menu: abre as áreas (limpar, privacidade, jogos...) para marcar item por item.'),
        ('benchmark', 'mede disco, CPU e RAM. Rode antes e depois para saber se mudou de verdade.'),
        ('desfazer', 'volta qualquer mudança. Se o PC ficou estranho, "socorro" volta tudo de uma vez.'),
        ('relatorio', 'o relatório do que foi feito, pronto para pedir ajuda (confira o nome do PC antes de compartilhar).'),
    ]
    for cmd, texto in passos:
        t.escreve(f'  {t.p(cmd, "destaque", True)}')
        t.paragrafo(texto, 4, 'sub')
    t.escreve()
    t.nota('  Qualquer comando aceita --teste (mostra o que faria, sem mudar nada) e --codigo (mostra o PowerShell de cada item).')
    return 0


def main(argv=None):
    parser = monta_parser()
    for fluxo in ('stdout', 'stderr'):   # pythonw (tarefa sem janela) não tem saída padrão: sem isto o primeiro print derrubaria o programa
        if getattr(sys, fluxo) is None:
            setattr(sys, fluxo, open(os.devnull, 'w'))
    sem_janela_global()
    cru = list(argv if argv is not None else sys.argv[1:])
    primeiro = cru[0] if cru and not cru[0].startswith('-') else None
    if primeiro == 'api':   # a interface com janelas: JSON por linha, sem tela e sem perguntas (66-api.py)
        return roda_api(cru[1:])
    tela = primeiro if primeiro in TELAS else None
    if tela:
        cru = cru[1:]
        argv = cru
    if primeiro and not tela and primeiro not in COMANDOS and primeiro not in ('manutencao', 'amostrar'):
        perto = comando_parecido(primeiro)
        if perto:
            print(f'katharos: "{primeiro}" não é um comando. Você quis dizer "{perto}"?  (katharos ajuda mostra o essencial)')
            return 2
    if '--uri' in cru:   # link do painel: nada de parser, só o formato exato
        return abre_por_clique(cru)
    args = _defaults(parser.parse_args(argv))
    if args.sha256:
        print(hashlib.sha256(Path(__file__).read_bytes()).hexdigest() + '  katharos.py')
        return 0
    args.ascii = args.ascii or config('simbolos') == 'simples'
    args.sem_cor = args.sem_cor or config('cores') == 'sem cor'
    t = Terminal(args.ascii, args.sem_cor)
    ctx = Ctx(args, t)
    desliga_edicao_rapida()
    limpa_residuos()
    for msg in AVISOS_INICIO:
        t.aviso(msg)
    AVISOS_INICIO.clear()
    globals()['AVISO_VIVO'] = t.aviso
    try:   # versão nova rodando pela primeira vez: reconhece os dados da anterior, converte e atualiza as cópias
        confere_versao(t, silencioso=bool(getattr(args, 'agendada', False)) or args.comando in ('amostrar', 'manutencao'))
    except Exception as e:
        LOG.escreve(f'conferência de versão falhou: {e!r}')
    if not getattr(args, 'agendada', False) and args.comando not in ('amostrar', 'manutencao'):
        try:   # automático e sem rede: avisa só se o SHA256SUMS.txt que veio junto não bate com este arquivo
            confere_na_abertura(t)
        except Exception as e:
            LOG.escreve(f'conferência de autenticidade falhou: {e!r}')
    precisa = (args.comando or 'menu') not in SEM_ACEITE and not args.teste and not getattr(args, 'codigo', False)
    if precisa and not aviso_aceito():
        if t.interativo:
            if not pede_aceite(ctx):
                return 0
        elif not args.sim:   # sem terminal, quem usa --sim já está escolhendo seguir sem perguntar
            t.aviso('Leia o aviso de uso antes (katharos aviso) e aceite no menu, ou use --sim para seguir sem perguntar.')
            return 1
    if WINDOWS and not getattr(args, 'agendada', False) and args.comando not in ('amostrar', 'manutencao', 'segundo-plano', 'bandeja') and not args.teste \
            and not getattr(args, 'exportar', False):
        try:   # quem tinha o acompanhamento contínuo passa para o Katharos.exe; quem já usa, fica com a config atualizada
            migra_segundo_plano(ctx)
        except Exception as e:
            LOG.escreve(f'segundo plano: migração falhou ({e!r})')
    try:
        pend = pendentes_andamento() if args.comando != 'retomar' else None
        if pend:
            t.aviso(f'A última aplicação de {PACOTES[pend[0]].titulo} parou no meio ({pl(len(pend[1]), "item faltou", "itens faltaram")}). '
                    'Rode "retomar" para terminar, ou "retomar --descartar" para esquecer.')
    except Exception as e:
        LOG.escreve(f'aviso de retomar falhou: {e!r}')
    try:
        if args.comando:
            cod = roda_ferramenta(ctx, args)
            if args.comando == 'buscar' and ctx.proximos and getattr(ctx, 'direto', False):   # escolheu um resultado: abre
                ctx.direto = False
                a2 = _defaults(parser.parse_args([ctx.proximos.pop(0)]))
                for k in ('ascii', 'sem_cor', 'teste', 'sim', 'modo'):
                    if getattr(args, k, None):
                        setattr(a2, k, getattr(args, k))
                if a2.comando not in SEM_ACEITE and not a2.teste and not aviso_aceito() and not pede_aceite(ctx):
                    return 0
                cod = roda_ferramenta(ctx, a2)
            return cod
        return menu(ctx, parser, args, tela)
    except KeyboardInterrupt:
        t.fim('interrompido', 'erro')
        t.escreve(guia=False)
        return 130
    except BrokenPipeError:
        try:
            sys.stdout = open(os.devnull, 'w')
        except OSError:
            pass
        return 0


if __name__ == '__main__':
    sys.exit(main())
