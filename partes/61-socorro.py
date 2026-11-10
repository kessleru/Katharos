

# ─────────────── socorro: voltar tudo quando o PC não está bem ───────────────

def ferramenta_socorro(ctx, args):
    t = ctx.t
    t.aba('o PC ficou estranho depois de aplicar algo? Isto volta tudo')
    t.paragrafo('Desfaz, valor por valor, tudo o que o Katharos mudou neste PC (registro, serviços, tarefas, plano de energia) '
                'e reinicia o Explorer. Não apaga seus arquivos nem mexe em programas. Se mesmo assim algo continuar errado, '
                'o último passo é o ponto de restauração do Windows, que este comando explica no fim.', 2, 'sub')
    if not precisa_admin(ctx, args):
        return 1
    com_backup = [n for n in PACOTES if (dir_backup() / n / 'mudancas.jsonl').exists()]
    if not com_backup:
        t.ok('O Katharos não tem nenhuma mudança guardada neste PC. Se o problema é recente, use o ponto de restauração (passos abaixo).')
    else:
        t.titulo('o que vai voltar')
        for n in com_backup:
            t.escreve(f'  {t.p("•", "destaque")} {PACOTES[n].titulo}')
        t.escreve()
        if not args.teste and not t.confirma('Voltar tudo isso agora?', sim=args.sim):
            return 0
        for n in com_backup:
            t.titulo(PACOTES[n].titulo)
            desfaz_pacote(ctx, n, args.teste)
        if not args.teste:
            roda_ps(t, 'Reinicia-Explorer', 'explorer', minutos=1, mostra=False)
            e = estado()
            e['socorro'] = agora_iso()
            salva_estado(e)
    t.titulo('se ainda não estiver bem')
    for passo in ('Reinicie o PC. Várias mudanças só voltam por completo depois do reinício.',
                  'Abra o Katharos e use o comando restaurar: ele lista os pontos do Windows, e "Antes do Katharos" é o último antes de mexer.',
                  'Sem conseguir abrir nada: segure Shift e clique em Reiniciar, depois Solução de problemas > Opções avançadas > Restauração do Sistema.',
                  'Se o Windows nem inicia, o mesmo caminho aparece sozinho depois de duas falhas seguidas de inicialização.'):
        t.escreve(f'  {t.p("›", "destaque")} {passo}')
    t.escreve()
    return 0


def ferramenta_retomar(ctx, args):
    t = ctx.t
    t.aba('termina o que ficou pela metade, se o PC travou ou a janela fechou')
    t.paragrafo('Cada aplicação anota o que já fez. Se foi interrompida, este comando refaz só os itens que faltaram '
                '(os que já estavam aplicados não são mexidos de novo).', 2, 'sub')
    a = estado().get('em_andamento')
    pend = pendentes_andamento()
    if getattr(args, 'descartar', False):
        if a:
            e = estado()
            e.pop('em_andamento', None)
            salva_estado(e)
            t.ok('Anotação descartada. O que já tinha sido aplicado continua valendo (o "desfazer" volta).')
        else:
            t.ok('Não havia nada pela metade.')
        return 0
    if not pend:
        if a:  # anotação sem itens pendentes (ou de pacote que não existe mais): só limpa
            e = estado()
            e.pop('em_andamento', None)
            salva_estado(e)
        t.ok('Nada pela metade: a última aplicação terminou.')
        return 0
    nome, falta, a = pend
    pac = PACOTES[nome]
    t.titulo('o que ficou pela metade')
    t.chaves([('pacote', pac.titulo), ('começou', ha_quanto_iso(a.get('quando', ''))),
              ('já feitos', f'{len(a.get("feitos", []))} de {len(a.get("ids", []))}')])
    if pac.admin and not precisa_admin(ctx, args):
        return 1
    itens = [i for i in (pac.itens(ctx) or []) if i and i.id in falta]
    itens, _ = aplica_protegidos(pac.nome, itens)
    if not itens:
        t.nota('Os itens que faltavam não se aplicam mais a este PC (ou estão protegidos). Anotação limpa.')
        e = estado()
        e.pop('em_andamento', None)
        salva_estado(e)
        return 0
    resumo_antes(t, pac, itens)
    if args.teste:
        executa_itens(ctx, pac, itens, teste=True)
        t.nota('modo teste: nada foi alterado.')
        return 0
    if not t.confirma(f'Terminar {pl(len(itens), "item", "itens")} de {pac.titulo}?', sim=args.sim):
        t.nota('nada foi alterado. "katharos retomar --descartar" esquece a anotação.')
        return 0
    feitos, avisos, erros = executa_itens(ctx, pac, itens)
    t.ok(f'Terminado: {pl(feitos, "mudança", "mudanças")}, {pl(avisos, "aviso", "avisos")}, {pl(erros, "erro", "erros")}.')
    return 1 if erros else 0
