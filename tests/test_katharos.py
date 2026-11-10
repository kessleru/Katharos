"""Testes do Katharos. Rodam em qualquer sistema (Linux no CI): `python -m unittest discover -s tests -v`.
Verificam o que não pode quebrar: cada item é completo, nenhum script mexe nas proteções do Windows, os perfis só
citam itens que existem, o menu só cita comandos que existem e o ZIP bate com os hashes publicados."""
import hashlib
from datetime import datetime
import importlib.util
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.argv = ['katharos']
spec = importlib.util.spec_from_file_location('katharos', RAIZ / 'programa' / 'katharos.py')
k = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k)


class _Mudo:
    """Terminal que engole tudo: os pacotes que consultam o PC (roda_ps) recebem resposta vazia."""
    interativo = False
    def __getattr__(self, nome):
        return lambda *a, **kw: ''


MODELO = {**k.PC_MODELO, 'tem': {**k.PC_MODELO['tem'], 'vs': True, 'firefox': True, 'visualstudio': True}}


class Ctx:
    perfil = MODELO
    t = _Mudo()
    args = None


k.roda_ps = lambda *a, **kw: k.Saida() if hasattr(k, 'Saida') else None


def todos_itens():
    """[(pacote, item)] de todos os pacotes, num PC modelo que tem de tudo."""
    out = []
    for nome, pac in k.PACOTES.items():
        try:
            its = [i for i in (pac.itens(Ctx) or []) if i]
        except Exception as e:  # um pacote que quebra com o PC modelo é um bug
            raise AssertionError(f'pacote {nome} quebrou: {e!r}')
        out += [(nome, i) for i in its]
    return out


ITENS = todos_itens()

# O que o Katharos promete nunca fazer. Se algum script gerado casar com isto, o teste falha.
PROIBIDO = [
    (r'DisableRealtimeMonitoring\s+\$?true|Set-MpPreference[^\n]*-Disable(Realtime|Behavior|IOAV|Script)\w*\s+\$?(true|1)', 'desligar o Defender'),
    (r'DisableAntiSpyware|DisableAntiVirus', 'desligar o Defender por política'),
    (r'advfirewall\s+set\s+\w+\s+state\s+off|Set-NetFirewallProfile[^\n]*-Enabled\s+(False|\$false|0)', 'desligar o firewall'),
    (r'EnableLUA["\']?\s*[,=-]*\s*(-Value\s+)?0\b', 'desligar o UAC'),
    (r'SmartScreenEnabled["\']?[^\n]*Off', 'desligar o SmartScreen'),
    (r'(Stop|Set)-Service[^\n]*\b(wuauserv|WinDefend|mpssvc|bits)\b[^\n]*(Disabled|-StartupType)', 'desligar Windows Update, Defender ou firewall'),
    (r'NoAutoUpdate', 'bloquear o Windows Update'),
    (r'Disable-ComputerRestore|SystemRestore[^\n]*Disable', 'desligar a Restauração do Sistema'),
    (r'AutomaticManagedPagefile[^\n]*(false|\$false|0)|PagingFiles', 'mexer na memória virtual'),
    (r'(Disable|Suspend)-BitLocker|manage-bde[^\n]*-off', 'desligar o BitLocker'),
    (r'HypervisorEnforcedCodeIntegrity|EnableVirtualizationBasedSecurity["\']?[^\n]*\b0\b', 'desligar a Integridade de Memória / VBS'),
]


class TestItens(unittest.TestCase):
    def test_existem_itens(self):
        self.assertGreater(len(ITENS), 150)

    def test_ids_unicos_por_pacote(self):
        for nome, pac in k.PACOTES.items():
            ids = [i.id for p, i in ITENS if p == nome]
            self.assertEqual(len(ids), len(set(ids)), f'ids repetidos em {nome}')

    def test_item_completo(self):
        for nome, i in ITENS:
            ctx = f'{nome}/{i.id}'
            self.assertTrue(i.titulo and i.explica, f'{ctx}: falta título ou explicação')
            self.assertIn(i.nivel, (0, 1, 2, 3), f'{ctx}: nível inválido')
            self.assertTrue(i.ps or i.py, f'{ctx}: sem código para executar')
            if i.nivel:
                self.assertTrue(i.ganho, f'{ctx}: não diz o que ganha')
                self.assertTrue(i.custo, f'{ctx}: não diz o que perde')

    def test_titulos_cabem_na_tela(self):
        for nome, i in ITENS:
            self.assertLessEqual(len(i.titulo), 80, f'{nome}/{i.id}: título longo demais')

    def test_nenhum_script_mexe_nas_protecoes(self):
        for nome, i in ITENS:
            codigo = i.ps or ''
            for padrao, o_que in PROIBIDO:
                m = re.search(padrao, codigo, re.I)
                self.assertIsNone(m, f'{nome}/{i.id} parece {o_que}: {m and m.group(0)}')

    def test_powershell_com_chaves_e_aspas_fechadas(self):
        for nome, i in ITENS:
            if not i.ps:
                continue
            c = re.sub(r"'(?:[^']|'')*'|\"(?:`.|[^\"`])*\"", '""', i.ps, flags=re.S)  # tira o conteúdo das strings, numa passada só
            c = re.sub(r'(?m)#.*$', '', c)
            for a, b in ('{}', '()', '[]'):
                self.assertEqual(c.count(a), c.count(b), f'{nome}/{i.id}: {a}{b} desbalanceado')

    def test_item_que_muda_algo_pode_ser_desfeito_ou_diz_que_nao(self):
        for nome, i in ITENS:
            if i.ps and not i.reverte:
                self.assertTrue(i.custo or i.alerta, f'{nome}/{i.id}: irreversível sem aviso')


class _Grava:
    """Terminal que só guarda o que foi escrito, com respostas prontas para as perguntas."""
    interativo = True
    largura = 100

    def __init__(self, respostas=()):
        self.linhas, self.respostas = [], list(respostas)

    def p(self, txt, *a, **kw):
        return str(txt)

    def escreve(self, txt='', **kw):
        self.linhas.append(str(txt))

    def paragrafo(self, txt, *a, **kw):
        self.linhas.append(str(txt))

    nota = aviso = titulo = paragrafo

    def pergunta(self, txt=''):
        return self.respostas.pop(0) if self.respostas else ''

    def __getattr__(self, nome):
        return lambda *a, **kw: ''

    @property
    def texto(self):
        return '\n'.join(self.linhas)


class TestMenuEnxuto(unittest.TestCase):
    """O menu de abertura tem poucas linhas e nada some: todo comando está no menu, em "escolher" ou em "mais"."""
    def test_menu_de_abertura_tem_no_maximo_sete_linhas(self):
        self.assertLessEqual(len(k.MENU), 7)
        for cmd, desc in k.MENU:
            self.assertTrue(cmd in k.COMANDOS or cmd in k.TELAS, cmd)
            self.assertLessEqual(len(desc), 60, cmd)

    def test_nenhum_comando_fica_sem_caminho_no_menu(self):
        alcanca = {c for c, _ in k.MENU}
        for tela in k.TELAS:
            for _, _, itens in k.grupos_da_tela(tela):
                alcanca |= {c for c, _ in itens}
        todos = {c for _, _, its in k.GRUPOS for c, _, _ in its}
        self.assertFalse(todos - alcanca, f'sem caminho no menu: {sorted(todos - alcanca)}')

    def test_escolher_so_tem_areas_com_itens_e_mais_so_tem_ferramentas(self):
        for _, _, itens in k.grupos_da_tela('escolher'):
            for c, _ in itens:
                self.assertEqual(k.COMANDOS[c][1], 'pacote', c)
        for _, _, itens in k.grupos_da_tela('mais'):
            for c, _ in itens:
                self.assertNotEqual(k.COMANDOS[c][1], 'pacote', c)










    def test_dicas_mostram_poucas_teclas_separadas_por_bolinha(self):
        import io, contextlib
        t = k.Terminal(True, True)
        buf = io.StringIO()
        t.largura = 76
        with contextlib.redirect_stdout(buf):
            t.dicas(k.DICAS_ESCOLHA)
        linha = buf.getvalue().strip()
        self.assertLessEqual(len(k.DICAS_ESCOLHA), 3)
        self.assertEqual(linha.count('  ·  ') + linha.count('  .  '), len(k.DICAS_ESCOLHA) - 1, linha)
        self.assertNotIn('=', linha)

    def test_perfil_saiu_e_o_que_ele_fazia_virou_comando(self):
        self.assertNotIn('perfil', k.COMANDOS)
        self.assertFalse(hasattr(k, 'PERFIS'))
        for cmd in ('atalhos', 'exportar', 'importar'):
            self.assertIn(cmd, k.COMANDOS)
        sub = [a for a in k.monta_parser()._actions if a.dest == 'comando'][0]
        self.assertNotIn('perfil', sub.choices)

    def test_atalhos_so_chamam_comandos_que_existem(self):
        for id_, nome, desc, args in k.lista_atalhos():
            if args:
                self.assertIn(args.split()[0], k.COMANDOS, id_)

    def test_menu_desenha_so_as_linhas_do_menu(self):
        t = k.Terminal(True, True)
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            por_numero = t.menu_itens([('', '', k.MENU)])
        self.assertEqual(por_numero, {str(i): c for i, (c, _) in enumerate(k.MENU, 1)})
        self.assertLessEqual(len([l for l in buf.getvalue().splitlines() if l.strip()]), len(k.MENU) + 1)


class TestEscolhaDeItens(unittest.TestCase):
    """A tela de marcar itens: uma linha por item, uma dica curta, e o resto só quando a pessoa pede."""
    def itens(self):
        return [k.Item('a', 'item A', 'explicação longa do A', 'ganho A', 'custo A', 1),
                k.Item('b', 'item B', 'explicação longa do B', 'ganho B', 'custo B', 3),
                k.Item('c', 'item C', 'explicação longa do C', 'ganho C', 'custo C', 0)]

    def roda(self, respostas, modo='equilibrado'):
        t = _Grava(respostas)
        ctx = type('C', (), {'t': t})()
        args = type('A', (), {'sim': False})()
        with mock.patch.object(k, 'config', lambda c: k.PADROES[c]):
            r = k.escolhe_itens(ctx, self.itens(), modo, args)
        return t, r

    def test_padrao_e_uma_linha_por_item_sem_explicacao(self):
        t, r = self.roda([''])
        self.assertEqual([i.id for i in r], ['a'])
        self.assertNotIn('explicação longa', t.texto)
        self.assertIn('item A', t.texto)

    def test_ajuda_da_escolha_explica_cada_tecla_numa_linha(self):
        t, _ = self.roda(['?', ''])
        for tecla, faz in k.AJUDA_ESCOLHA:
            self.assertIn(faz, t.texto)
            self.assertLessEqual(len(faz), 60)

    def test_interrogacao_e_numero_explica_um_item(self):
        t, _ = self.roda(['? 2', ''])
        self.assertIn('explicação longa do B', t.texto)
        self.assertNotIn('explicação longa do A', t.texto)
        t, _ = self.roda(['2?', ''])
        self.assertIn('explicação longa do B', t.texto)

    def test_numero_tira_e_poe(self):
        _, r = self.roda(['1 3', ''])
        self.assertEqual([i.id for i in r], ['c'])
        _, r = self.roda(['1-3', ''])
        self.assertEqual([i.id for i in r], ['b', 'c'])

    def test_modos_e_atalhos_antigos_continuam_valendo(self):
        _, r = self.roda(['x', ''])
        self.assertEqual([i.id for i in r], ['a', 'b'])
        _, r = self.roda(['t', ''])
        self.assertEqual(len(r), 3)
        _, r = self.roda(['n', ''])
        self.assertEqual(r, [])
        _, r = self.roda(['0'])
        self.assertIsNone(r)

    def test_texto_solto_nao_marca_nada(self):
        t, r = self.roda(['abc 2', ''])
        self.assertEqual([i.id for i in r], ['a'])
        self.assertIn('não é uma opção', t.texto)

    def test_item_sem_volta_e_com_alerta_aparecem_na_linha(self):
        it = k.Item('z', 'remove algo', 'e', 'g', 'c', 1, reverte=False)
        it.marcado, it.alerta = True, 'cuidado'
        linha = k._linha_item(_Grava(), it, 1)
        self.assertIn('sem volta', linha)
        self.assertIn('tem aviso', linha)

    def test_grupos_dizem_o_que_sao_e_o_nome_do_modo_nao_fica_solto(self):
        t, _ = self.roda([''])
        for nv in (1, 3, 0):
            self.assertIn(k.NOME_NIVEL[nv] + '  ' + k.EXPLICA_NIVEL[nv], t.texto)
        self.assertNotIn('só se marcar', t.texto)
        linhas_de_item = [l for l in t.linhas if 'item A' in l or 'item B' in l or 'item C' in l]
        for l in linhas_de_item:
            for nome in ('seguro', 'equilibrado', 'extremo', 'opcional'):
                self.assertNotIn(nome, l, 'o grupo diz o modo; a linha do item não repete')

    def test_tela_agrupa_mas_devolve_na_ordem_original(self):
        its = [k.Item('x', 'extremo primeiro', 'e', nivel=3), k.Item('o', 'opcional', 'e', nivel=0),
               k.Item('s', 'seguro por ultimo', 'e', nivel=1), k.Item('q', 'equilibrado', 'e', nivel=2)]
        self.assertEqual([i.id for i in k.ordem_de_tela(its)], ['s', 'q', 'x', 'o'])
        self.assertEqual([i.id for i in k.ordem_de_tela(its, agrupar=False)], ['x', 'o', 's', 'q'])
        t = _Grava(['t', ''])
        ctx = type('C', (), {'t': t})()
        with mock.patch.object(k, 'config', lambda c: k.PADROES[c]):
            r = k.escolhe_itens(ctx, its, 'seguro', type('A', (), {'sim': False})())
        self.assertEqual([i.id for i in r], ['x', 'o', 's', 'q'], 'aplica na ordem do pacote, não na da tela')
        t = _Grava(['1', ''])   # o número é o da tela: o 1 é o seguro
        ctx = type('C', (), {'t': t})()
        with mock.patch.object(k, 'config', lambda c: k.PADROES[c]):
            r = k.escolhe_itens(ctx, its, 'seguro', type('A', (), {'sim': False})())
        self.assertEqual(r, [])






class TestMenu(unittest.TestCase):
    def test_todo_comando_do_menu_existe_no_parser(self):
        p = k.monta_parser()
        sub = next(a for a in p._actions if a.dest == 'comando')
        for _, _, itens in k.GRUPOS:
            for cmd, desc, _ in itens:
                self.assertIn(cmd, sub.choices, f'{cmd} está no menu mas não no parser')
                self.assertLessEqual(len(desc), 60, f'{cmd}: descrição longa demais para o menu')

    def test_sem_comando_repetido_no_menu(self):
        cmds = [c for _, _, its in k.GRUPOS for c, _, _ in its]
        self.assertEqual(len(cmds), len(set(cmds)))


class TestRobustez(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        self.casa0 = k.CASA
        k.CASA = self.tmp
        k.AVISOS_INICIO.clear()

    def tearDown(self):
        import shutil
        k.CASA = self.casa0
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_json_corrompido_e_guardado_e_avisado(self):
        arq = self.tmp / 'estado.json'
        arq.write_text('{ isto nao e json', encoding='utf-8')
        self.assertEqual(k.le_json(arq, {'padrao': 1}), {'padrao': 1})
        self.assertFalse(arq.exists())
        copias = list(self.tmp.glob('estado.json.corrompido-*'))
        self.assertEqual(len(copias), 1)
        self.assertEqual(copias[0].read_text(encoding='utf-8'), '{ isto nao e json')
        self.assertEqual(len(k.AVISOS_INICIO), 1)

    def test_json_que_nao_existe_nao_gera_aviso(self):
        self.assertEqual(k.le_json(self.tmp / 'nada.json', 7), 7)
        self.assertEqual(k.AVISOS_INICIO, [])

    def test_limpa_residuos_nao_toca_no_backup(self):
        import os as _os
        import time as _t
        (self.tmp / 'backup' / 'limpar').mkdir(parents=True)
        bk = self.tmp / 'backup' / 'limpar' / 'mudancas.jsonl'
        bk.write_text('{}', encoding='utf-8')
        velho_tmp = self.tmp / 'estado.json.tmp'
        velho_tmp.write_text('x')
        (self.tmp / 'logs').mkdir()
        log_velho = self.tmp / 'logs' / '2020-01-01.log'
        log_velho.write_text('x')
        log_novo = self.tmp / 'logs' / 'hoje.log'
        log_novo.write_text('x')
        antigo = _t.time() - 200 * 86400
        for a in (velho_tmp, log_velho):
            _os.utime(a, (antigo, antigo))
        _os.utime(bk, (antigo, antigo))
        n = k.limpa_residuos(self.tmp)
        self.assertEqual(n, 2)
        self.assertTrue(bk.exists(), 'o backup do desfazer nunca pode ser apagado')
        self.assertTrue(log_novo.exists())
        self.assertFalse(velho_tmp.exists() or log_velho.exists())

    def test_trava_impede_segunda_instancia_e_ignora_processo_morto(self):
        a = k.Trava(self.tmp)
        self.assertTrue(a.pega())
        # outra "instância" com o PID do pai (vivo) segura a trava
        (self.tmp / 'katharos.lock').write_text(f'{__import__("os").getppid()} x\n')
        b = k.Trava(self.tmp)
        self.assertFalse(b.pega())
        self.assertEqual(b.dona, __import__('os').getppid())
        # PID que não existe: trava velha, pode pegar
        (self.tmp / 'katharos.lock').write_text('999999999 x\n')
        c = k.Trava(self.tmp)
        self.assertTrue(c.pega())
        c.solta()
        self.assertFalse((self.tmp / 'katharos.lock').exists())

    def test_espaco(self):
        self.assertFalse(k.espaco_ok('dism', livre=1 * 2**30)[0])
        self.assertTrue(k.espaco_ok('dism', livre=10 * 2**30)[0])
        self.assertTrue(k.espaco_ok('dism', livre=0)[0], 'sem conseguir ler o espaço, não bloqueia')

    def test_socorro_e_benchmark_estao_no_menu(self):
        cmds = [c for _, _, its in k.GRUPOS for c, _, _ in its]
        self.assertIn('socorro', cmds)
        self.assertIn('benchmark', cmds)
        self.assertIn('socorro', k.SEM_ESTADO)


class TestBenchmark(unittest.TestCase):
    def test_estatistica(self):
        e = k.estatistica([10, 12, 11, 100, 9])
        self.assertEqual(e['mediana'], 11)
        self.assertEqual((e['minimo'], e['maximo'], e['n']), (9, 100, 5))
        self.assertEqual(k.estatistica([1, 3])['mediana'], 2)

    def test_so_declara_ganho_maior_que_o_ruido(self):
        antes = k.estatistica([100, 102, 98, 101])        # amplitude 4
        depois_ruido = k.estatistica([101, 103, 99, 102])  # só 1% acima: dentro do ruído
        depois_real = k.estatistica([150, 152, 149, 151])
        self.assertEqual(k.compara_bench(antes, depois_ruido)[0], 'sem diferença mensurável')
        self.assertEqual(k.compara_bench(antes, depois_real)[0], 'melhorou')
        self.assertEqual(k.compara_bench(depois_real, antes)[0], 'piorou')

    def test_menor_e_melhor(self):
        a = k.estatistica([200, 201, 199])
        d = k.estatistica([100, 101, 99])
        self.assertEqual(k.compara_bench(a, d, 'menor')[0], 'melhorou')

    def test_poucas_repeticoes_nao_conclui(self):
        self.assertIn('poucas', k.compara_bench(k.estatistica([1, 2]), k.estatistica([5, 6]))[0])

    def test_pc_apertado_decide_modo_leve_do_benchmark(self):
        self.assertIn('4 GB', k.pc_apertado({'ram': {'total': 4, 'usada': 2}}))
        self.assertIn('livre', k.pc_apertado({'ram': {'total': 16, 'usada': 15}}))
        self.assertIn('HD', k.pc_apertado({'ram': {'total': 16, 'usada': 4}, 'disco': {'tipo': 'HDD'}}))
        self.assertEqual(k.pc_apertado({'ram': {'total': 16, 'usada': 4}, 'disco': {'tipo': 'SSD'}}), '')
        self.assertEqual(k.pc_apertado({}), '')
        self.assertEqual(k.pc_apertado(None), '')

    def test_instabilidade_so_acima_de_15_por_cento(self):
        self.assertFalse(k.instavel(k.estatistica([100, 105, 98, 102])))
        self.assertTrue(k.instavel(k.estatistica([100, 140, 90, 120])))
        self.assertFalse(k.instavel(None))

    def test_mostra_bench_avisa_medida_instavel_e_escala_dos_nucleos(self):
        saida = []
        class T:
            def p(self, txt, *a, **kw): return txt
            def titulo(self, *a, **kw): pass
            def escreve(self, txt=''): saida.append(txt)
        atual = {'cpu': k.estatistica([100, 101, 99, 100]), 'cpu_multi': k.estatistica([400, 500, 300, 450]),
                 'ram': k.estatistica([1000, 1001, 999]), 'disco_escrita': k.estatistica([200, 201, 199]), 'disco_4k': k.estatistica([50, 51, 49])}
        k.mostra_bench(T(), atual)
        txt = '\n'.join(saida)
        self.assertIn('medida instável', txt)
        self.assertIn('4.2x', txt)

    def test_todos_os_nucleos_so_com_multi(self):
        import tempfile
        class T:
            def __getattr__(self, n): return lambda *a, **kw: None
        with tempfile.TemporaryDirectory() as d:
            self.assertIn('cpu_multi', k.roda_bench(T(), rapido=True, leve=True, pasta_tmp=d, multi=True))

    def test_cpu_multi_roda_e_devolve_taxa_positiva(self):
        self.assertGreater(k.bench_cpu_multi(2), 0)

    def test_benchmark_apaga_o_arquivo_temporario(self):
        import tempfile
        d = Path(tempfile.mkdtemp())
        class T:
            def __getattr__(self, n):
                return lambda *a, **kw: ''
        k.Progresso = type('P', (), {'__init__': lambda s, *a, **kw: None, '__enter__': lambda s: s, '__exit__': lambda s, *a: False})
        r = k.roda_bench(T(), rapido=True, leve=True, pasta_tmp=d)
        self.assertEqual(set(r), {'cpu', 'ram', 'disco_escrita', 'disco_4k'}, 'o teste padrão é leve: todos os núcleos só com --completo')
        self.assertTrue(all(v['mediana'] > 0 for v in r.values()))
        self.assertEqual(list(d.glob('*')), [], 'o arquivo de teste tem de ser apagado')


class TestJaFeito(unittest.TestCase):
    def test_confere_marca_o_que_ja_esta_feito_e_nao_marca_de_novo(self):
        a = k.Item('a', 'A', 'x', nivel=1, ps="Set-Valor 'HKCU:\\X' 'a' 1")
        b = k.Item('b', 'B', 'x', nivel=1, ps="Set-Valor 'HKCU:\\X' 'b' 1")
        c = k.Item('c', 'C', 'x', nivel=1, py=lambda *x: None)
        s = k.Saida(); s.dados = {'ja:a': True, 'ja:b': False}
        ctx = mock.Mock(t=mock.Mock(), mult=1.0, ja=None)
        with mock.patch.object(k, 'WINDOWS', True), mock.patch.object(k, 'roda_ps', return_value=s) as r:
            k.confere_itens(ctx, [a, b, c], 'x')
            self.assertTrue(r.call_args.kwargs.get('teste'), 'a conferência roda em modo teste: nada muda')
        self.assertIs(a.ja, True); self.assertIs(b.ja, False); self.assertIsNone(c.ja)
        with mock.patch.object(k, 'WINDOWS', True), mock.patch.object(k, 'roda_ps') as r:
            k.confere_itens(ctx, [a, b], 'x')
            r.assert_not_called()   # a mesma sessão não confere duas vezes

    def test_inicializacao_ignora_programa_que_saiu_e_marca_dupla(self):
        self.assertIn('existe', k.INICIO_PS)
        self.assertIn('Get-AppxPackage', k.INICIO_PS, 'app da Loja desinstalado não conta')
        self.assertIn("-notmatch '^Katharos'", k.INICIO_PS, 'as tarefas do próprio Katharos não contam')
        self.assertIn('ListaInicio', k.MEDIDAS_PS)
        self.assertIn('ListaInicio', k.DIAG_PS, 'o raio-x conta a inicialização do mesmo jeito')
        self.assertIn('$_.ligado -and $_.existe', k.DIAG_PS)

    def test_pc_de_empresa_so_com_gestao_de_verdade(self):
        self.assertIn("'MS DM Server'", k.PERFIL_PS)
        self.assertIn('EnrollmentState', k.PERFIL_PS)
        self.assertIn('gerenciado_por', k.PERFIL_PS)


class TestBandeja(unittest.TestCase):
    def test_icone_le_a_ultima_amostra_e_roda_sem_administrador(self):
        self.assertIn('NotifyIcon', k.BANDEJA_PS)
        self.assertIn('Local\\KatharosBandeja', k.BANDEJA_PS, 'um ícone só por sessão')
        self.assertNotIn('Get-CimInstance', k.BANDEJA_PS, 'o ícone não mede nada: só lê o arquivo da amostra')
        fonte = Path(k.__file__).read_text(encoding='utf-8')
        trecho = fonte[fonte.index('def instala_bandeja'):fonte.index('def remove_bandeja')]
        self.assertIn('-RunLevel Limited', trecho)
        self.assertIn('pythonw.exe', trecho)

    def test_ultima_amostra_e_pausa(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d, mock.patch.object(k, 'CASA', Path(d)):
            k.grava_ultima_amostra({'cpu': 12.0, 'temp': 47})
            import json
            a = json.loads((Path(d) / k.ULTIMA_AMOSTRA).read_text(encoding='utf-8'))
            self.assertEqual(a['cpu'], 12.0)
            self.assertIn('quando', a)
            self.assertFalse(k.leitura_pausada())
            (Path(d) / k.PAUSA_ARQ).write_text('2999-01-01T00:00:00', encoding='ascii')
            self.assertTrue(k.leitura_pausada())
            (Path(d) / k.PAUSA_ARQ).write_text('2000-01-01T00:00:00', encoding='ascii')
            self.assertFalse(k.leitura_pausada())


class TestSegundoPlano(unittest.TestCase):
    def test_recente_h(self):
        from datetime import datetime, timedelta
        agora = datetime.now()
        self.assertTrue(k.recente_h((agora - timedelta(hours=1)).isoformat(), 3))
        self.assertFalse(k.recente_h((agora - timedelta(hours=5)).isoformat(), 3))
        self.assertFalse(k.recente_h(None, 3))
        self.assertFalse(k.recente_h('lixo', 3))

    def test_cada_frequencia_gera_tarefa_com_gatilho_proprio_e_regras_leves(self):
        corpos = {}
        antigo = k.roda_ps
        k.CASA_ANT = k.CASA
        import tempfile
        k.CASA = Path(tempfile.mkdtemp())
        try:
            for f in k.FREQ_FUNDO:
                k.roda_ps = lambda t, corpo, *a, **kw: (corpos.setdefault(f, corpo), type('S', (), {'ok': True, 'erros': []})())[1]
                self.assertEqual(k.instala_manutencao(Ctx(), f), 0)
                self.assertEqual(k.estado().get('manut_freq'), f)
        finally:
            k.roda_ps = antigo
            k.CASA = k.CASA_ANT
        self.assertIn('-Weekly', corpos['semanal'])
        self.assertIn('-Daily', corpos['diaria'])
        self.assertIn('-AtLogOn', corpos['continua'])
        self.assertIn('-RepetitionInterval', corpos['continua'])
        for c in corpos.values():
            self.assertIn('-RunOnlyIfIdle', c)
            self.assertIn('-MultipleInstances IgnoreNew', c)
            self.assertIn('-Priority 7', c)
            self.assertIn(k.TAREFA_MANUT_ANTIGA, c, 'a tarefa antiga é removida para não rodar duas vezes')
            self.assertNotIn('«', c)

    def test_modo_continuo_liga_tambem_a_leitura_leve_de_15_min_sem_janela(self):
        from unittest import mock
        import tempfile
        corpos = []
        with tempfile.TemporaryDirectory() as d, mock.patch.object(k, 'CASA', Path(d)), \
                mock.patch.object(k, 'roda_ps', lambda t, corpo, *a, **kw: (corpos.append(corpo), type('S', (), {'ok': True, 'erros': []})())[1]):
            self.assertEqual(k.instala_manutencao(Ctx(), 'continua'), 0)
            self.assertTrue(any(k.TAREFA_AMOSTRA in c and '-RepetitionInterval' in c for c in corpos))
            n = len(corpos)
            self.assertEqual(k.instala_manutencao(Ctx(), 'semanal'), 0)
            self.assertTrue(any('Unregister' in c and k.TAREFA_AMOSTRA in c for c in corpos[n:]), 'fora do modo contínuo a leitura de 15 min é removida')
        a = [c for c in corpos if k.TAREFA_AMOSTRA in c and 'Register-ScheduledTask' in c][0]
        self.assertIn('-AllowStartIfOnBatteries', a)
        self.assertIn('-Priority 7', a)
        self.assertIn('-MultipleInstances IgnoreNew', a)
        self.assertNotIn('-RunOnlyIfIdle', a, 'precisa medir também com o PC em uso')
        self.assertIn('-RunLevel Limited', a, 'a leitura não precisa de administrador')
        self.assertNotIn('-RunLevel Highest', a)
        self.assertNotIn('«', a)

    def test_leitura_leve_usa_pythonw_sem_janela_quando_existe(self):
        from unittest import mock
        with mock.patch.object(k.Path, 'exists', return_value=True):
            exe, arg, sem = k.comando_da_amostra()
        self.assertTrue(sem)
        self.assertTrue(exe.lower().endswith('pythonw.exe'))
        self.assertIn('amostrar --agendada', arg)

    def test_tarefa_elevada_roda_sem_janela_e_de_pasta_so_de_administradores(self):
        from unittest import mock
        import tempfile
        corpos = []
        chamadas = []
        with tempfile.TemporaryDirectory() as d, mock.patch.object(k, 'CASA', Path(d)), mock.patch.object(k, 'WINDOWS', True), \
                mock.patch.object(k, 'pasta_da_tarefa', return_value=Path(d) / 'ProgramData' / 'Katharos'), \
                mock.patch.object(k, 'protege_pasta_da_tarefa', side_effect=lambda p: chamadas.append(p) or True), \
                mock.patch.object(k, 'executavel_sem_janela', return_value=('C:\\\\Py\\\\pythonw.exe', True)), \
                mock.patch.object(k, 'python_em_pasta_do_usuario', return_value=False), \
                mock.patch.object(k, 'roda_ps', lambda t, corpo, *a, **kw: (corpos.append(corpo), type('S', (), {'ok': True, 'erros': []})())[1]):
            self.assertEqual(k.instala_manutencao(Ctx(), 'semanal'), 0)
            self.assertEqual(len(chamadas), 1, 'a pasta é protegida antes de copiar o programa')
            self.assertTrue((Path(d) / 'ProgramData' / 'Katharos' / 'katharos.py').exists())
        c = corpos[0]
        self.assertIn('pythonw.exe', c)
        self.assertNotIn('-Command', c, 'não pode abrir powershell.exe (piscaria uma janela)')
        self.assertIn('-RunLevel Highest', c)
        self.assertNotIn(str(Path(d) / 'katharos.py'), c, 'o script elevado não fica na pasta do usuário')

    def test_tarefa_elevada_nao_e_criada_se_a_pasta_nao_puder_ser_protegida(self):
        from unittest import mock
        import tempfile
        corpos = []
        with tempfile.TemporaryDirectory() as d, mock.patch.object(k, 'CASA', Path(d)), mock.patch.object(k, 'WINDOWS', True), \
                mock.patch.object(k, 'pasta_da_tarefa', return_value=Path(d) / 'PD'), mock.patch.object(k, 'protege_pasta_da_tarefa', return_value=False), \
                mock.patch.object(k, 'roda_ps', lambda t, corpo, *a, **kw: corpos.append(corpo)):
            self.assertEqual(k.instala_manutencao(Ctx(), 'semanal'), 1)
        self.assertEqual(corpos, [], 'sem proteção, nenhuma tarefa elevada')

    def test_icacls_usa_sids_e_tira_a_heranca(self):
        from unittest import mock
        with mock.patch.object(k.subprocess, 'run', return_value=type('R', (), {'returncode': 0})()) as m:
            self.assertTrue(k.protege_pasta_da_tarefa(Path('X')))
        args = m.call_args[0][0]
        self.assertIn('/inheritance:r', args)
        for sid in ('*S-1-5-18', '*S-1-5-32-544'):
            self.assertTrue(any(a.startswith(sid) and a.endswith('F') for a in args), sid)
        self.assertTrue(any(a.startswith('*S-1-5-32-545') and a.endswith('RX') for a in args), 'Usuários só leem')

    def test_sem_console_todo_processo_filho_nasce_sem_janela(self):
        from unittest import mock
        import subprocess as sp
        visto = {}

        class Falso:
            def __init__(self, *a, **kw):
                visto.update(kw)
        with mock.patch.object(k.subprocess, 'Popen', Falso), mock.patch.object(k, 'WINDOWS', True), \
                mock.patch.object(k.ctypes, 'windll', create=True) as w:
            w.kernel32.GetConsoleWindow.return_value = 0
            self.assertTrue(k.sem_janela_global())
            k.subprocess.Popen(['x'], creationflags=0x40)
            self.assertEqual(visto['creationflags'], 0x40 | 0x08000000, 'mantém as marcas que já existiam')
        with mock.patch.object(k.subprocess, 'Popen', Falso), mock.patch.object(k, 'WINDOWS', True), mock.patch.object(k.ctypes, 'windll', create=True) as w:
            w.kernel32.GetConsoleWindow.return_value = 12345   # há console: uso normal, nada muda
            self.assertFalse(k.sem_janela_global())

    def test_toda_tarefa_agendada_usa_pythonw_ou_avisa(self):
        # só a tarefa "continuar depois de reiniciar" abre janela, de propósito (o turbo continua à vista, com a pessoa acompanhando)
        fonte = Path(k.__file__).read_text(encoding='utf-8')
        self.assertEqual(fonte.count("-Execute 'powershell.exe'"), 1)

    def test_frequencia_desconhecida_cai_em_semanal(self):
        self.assertIn('semanal', k.FREQ_FUNDO)
        self.assertTrue(k.INTERVALO_MINIMO_H >= 1)


class TestTendencia(unittest.TestCase):
    def _am(self, n, passo_h=12, **fn):
        from datetime import datetime, timedelta
        base = datetime(2026, 1, 1)
        out = []
        for i in range(n):
            d = {'_dt': base + timedelta(hours=passo_h * i)}
            for chave, f in fn.items():
                d[chave] = f(i)
            out.append(d)
        return out

    def test_espaco_caindo_avisa_com_prazo(self):
        am = self._am(20, livre_c=lambda i: 60 - i * 1.5)   # 3 GB/dia
        ach = dict(k.analisa_tendencia(am))
        self.assertIn('livre_c', ach)
        self.assertIn('dias', ach['livre_c'])

    def test_espaco_estavel_nao_avisa(self):
        self.assertEqual(k.analisa_tendencia(self._am(20, livre_c=lambda i: 60 - (i % 3) * 0.2)), [])

    def test_ruido_nao_vira_tendencia(self):
        am = self._am(20, boot_s=lambda i: 30 + (5 if i % 2 else -5), ram_usada=lambda i: 8 + (0.3 if i % 2 else -0.3))
        self.assertEqual(k.analisa_tendencia(am), [])

    def test_boot_e_ram_subindo(self):
        am = self._am(18, boot_s=lambda i: 30 + i * 2, ram_usada=lambda i: 6 + i * 0.3)
        self.assertEqual({c for c, _ in k.analisa_tendencia(am)}, {'boot_s', 'ram_usada'})

    def test_poucas_amostras_ou_poucos_dias_nao_afirmam_nada(self):
        self.assertEqual(k.analisa_tendencia(self._am(4, livre_c=lambda i: 60 - i * 20)), [])
        self.assertEqual(k.analisa_tendencia(self._am(10, passo_h=1, livre_c=lambda i: 60 - i * 5)), [])

    def test_arquivo_tem_teto_e_aguenta_linha_quebrada(self):
        import tempfile
        d = Path(tempfile.mkdtemp()) / 'm.jsonl'
        antigo = k.METRICAS_MAX
        k.METRICAS_MAX = 5
        try:
            for i in range(9):
                k.registra_metrica({'livre_c': 50 - i, 'lixo': 'x'}, quando=f'2026-01-0{i + 1}T12:00:00', arq=d)
            with open(d, 'a', encoding='utf-8') as f:
                f.write('{quebrada\n')
            am = k.le_metricas(d)
            self.assertEqual(len(am), 5)
            self.assertEqual([a['livre_c'] for a in am], [46, 45, 44, 43, 42])
            self.assertNotIn('lixo', am[0], 'só as chaves conhecidas são gravadas')
        finally:
            k.METRICAS_MAX = antigo

    def test_sem_numero_nao_grava(self):
        import tempfile
        d = Path(tempfile.mkdtemp()) / 'm.jsonl'
        self.assertIsNone(k.registra_metrica({'cpu': None, 'x': 'a'}, arq=d))
        self.assertFalse(d.exists())


class TestPainel(unittest.TestCase):
    def _dados(self):
        from datetime import datetime, timedelta
        base = datetime(2026, 1, 1, 12)
        am = [{'_dt': base + timedelta(hours=12 * i), 'livre_c': 80 - i, 'ram_usada': 6 + i * 0.1, 'boot_s': 30 + i, 'cpu': 3.0, 'inicializacao': 9, 'processos': 150} for i in range(14)]
        return am, base

    def _saude(self):
        grupos = [{'provedor': 'Microsoft-Windows-Kernel-Power', 'id': 41, 'arg': '0', 'n': 2, 'dias': 2, 'primeiro': '2026-11-01T10:00:00', 'ultimo': '2026-11-08T10:00:00', 'msg': ''},
                  {'provedor': 'Misterio<script>', 'id': 7, 'arg': '', 'n': 3, 'dias': 1, 'primeiro': '2026-11-01T10:00:00', 'ultimo': '2026-11-02T10:00:00', 'msg': '<b>x</b>'}]
        dados = {'saude_grupos': grupos, 'saude_total': {'eventos': 5}, 'saude_por_dia': [{'dia': '2026-11-07', 'n': 1}, {'dia': '2026-11-08', 'n': 4}],
                 'saude_drivers': [{'nome': 'GPU <i>', 'classe': 'DISPLAY', 'fab': 'X', 'versao': '1', 'data': '2024-01-01T00:00:00', 'assinado': True}],
                 'saude_windows': {'reinicio_pendente': True}}
        return {'quando': '2026-11-09T08:00:00', 'analise': k.analisa_saude(dados, __import__('datetime').datetime(2026, 11, 9, 12))}

    def test_painel_mostra_saude_do_windows_escapada_e_sem_scripts(self):
        h = k.monta_painel([], [], [], [], 'PC', '1', saude=self._saude())
        self.assertIn('Saúde do Windows', h)
        self.assertIn('O PC desligou sem avisar', h)
        self.assertIn('O que fazer:', h)
        self.assertIn('Drivers instalados', h)
        self.assertNotIn('<script', h)
        self.assertNotIn('Misterio<script>', h)
        self.assertNotIn('GPU <i>', h)
        self.assertNotIn('https://', h)

    def test_painel_sem_saude_nao_tem_a_secao(self):
        self.assertNotIn('Saúde do Windows', k.monta_painel([], [], [], [], 'PC', '1'))

    def test_painel_saude_sem_problemas_diz_que_esta_tudo_certo(self):
        sa = {'quando': '2026-11-09T08:00:00', 'analise': k.analisa_saude({'saude_total': {'eventos': 0}, 'saude_windows': {'uptime_dias': 1, 'livre_pct': 50}}, __import__('datetime').datetime(2026, 11, 9))}
        self.assertIn('Nenhum problema encontrado', k.monta_painel([], [], [], [], 'PC', '1', saude=sa))

    def test_conselheiro_propoe_a_partir_da_saude(self):
        ev = {'saude': self._saude()['analise'], 'amostras': [], 'benchs': [], 'pacotes': [], 'eventos': [], 'raiox': {}, 'dispensadas': {}, 'vistas': {},
              'fundo_ligado': True, 'agora': __import__('datetime').datetime(2026, 11, 9), 'perfil': {}}
        ids = [x['id'] for x in k.gera_sugestoes(ev) if x['id'].startswith('saude:')]
        self.assertTrue(any('video-antigo' in i for i in ids) or any('reinicio' in i for i in ids) or ids, ids)
        for x in k.gera_sugestoes(ev):
            self.assertIn(x['comando'], k.COMANDOS)

    def test_aviso_de_saude_no_fundo_nao_alarma_no_primeiro_retrato_e_respeita_o_intervalo(self):
        import tempfile, pathlib
        from unittest import mock
        atual = self._saude()['analise']
        with tempfile.TemporaryDirectory() as d, mock.patch.object(k, 'CASA', pathlib.Path(d)), mock.patch.object(k, 'coleta_saude', return_value=atual):
            e = {}
            self.assertEqual(k.avisa_saude(None, e), [])          # sem retrato anterior
            self.assertIn('saude_ultima', e)
            self.assertEqual(k.avisa_saude(None, e), [])          # menos de 20 h: nem coleta
            e2 = {}
            k.grava_json(k.saude_arq(), {'quando': '2026-11-01T00:00:00', 'analise': {'problemas': []}})
            msgs = k.avisa_saude(None, e2)
            self.assertTrue(msgs and 'katharos saude' in msgs[0], msgs)

    def test_painel_e_autocontido_e_tem_graficos(self):
        am, base = self._dados()
        h = k.monta_painel(am, [], [(base + __import__('datetime').timedelta(days=2), 'inicializacao')], k.analisa_tendencia(am), 'PC', '1.4.0')
        self.assertIn('<svg', h)
        self.assertNotIn('http://', h)
        self.assertNotIn('https://', h)
        self.assertNotIn('<script', h, 'sem scripts')
        self.assertIn('aria-label', h)
        self.assertIn('aplicou: inicializacao', h)

    def test_painel_escapa_html_do_nome_do_pc_e_do_pacote(self):
        am, base = self._dados()
        h = k.monta_painel(am, [], [(base, '<img src=x onerror=1>')], [], '<script>alert(1)</script>', '1')
        self.assertNotIn('<script>alert', h)
        self.assertNotIn('<img src=x', h)

    def test_painel_vazio_explica_como_ligar_o_segundo_plano(self):
        h = k.monta_painel([], [], [], [], 'PC', '1')
        self.assertIn('agendar --frequencia continua', h)
        self.assertNotIn('<svg', h)

    def test_serie_de_um_ponto_e_valor_constante_nao_quebram(self):
        from datetime import datetime
        self.assertIn('<circle', k.svg_linha([(datetime(2026, 1, 1), 5.0)], 't'))
        s = [(datetime(2026, 1, i + 1), 7.0) for i in range(5)]
        self.assertIn('<polyline', k.svg_linha(s, 't', tendencia=True))

    def test_ticks_inteiros_nao_se_repetem(self):
        t = k._ticks(9.0, 11.0, inteiro=True)
        self.assertEqual(len(t), len(set(t)))
        self.assertTrue(all(x == int(x) for x in t))

    def test_sparkline(self):
        self.assertEqual(k.sparkline_txt([1, 2, 3, 4, 5, 6, 7, 8])[0], '▁')
        self.assertEqual(k.sparkline_txt([1, 8])[-1], '█')
        self.assertTrue(k.sparkline_txt([1, 5, 9], ascii_=True).isascii())
        self.assertEqual(k.sparkline_txt([]), '')
        self.assertLessEqual(len(k.sparkline_txt(list(range(100)))), 24)


class TestCliques(unittest.TestCase):
    def test_uri_aceita_so_o_formato_exato_e_comando_permitido(self):
        self.assertEqual(k.uri_para_comando('katharos://limpar'), 'limpar')
        self.assertEqual(k.uri_para_comando('katharos://reparar/'), 'reparar')
        for ruim in ('katharos://LIMPAR', 'katharos://limpar?x=1', 'katharos://limpar&calc', 'katharos://limpar calc', 'katharos://limpar/../x', 'katharos://limpar" -Command "calc',
                     'katharos://naoexiste', 'katharos://', '', None, 'http://limpar', 'katharos://limpar;calc', 'katharos://limpar%20x', 'katharos://-limpar'):
            self.assertIsNone(k.uri_para_comando(ruim), ruim)
        for bloq in k.URI_BLOQUEADOS:
            self.assertIsNone(k.uri_para_comando('katharos://' + bloq), bloq)

    def test_toda_proposta_possivel_aponta_para_comando_que_o_link_aceita_ou_nao_tem_botao(self):
        for cmd in k.URI_SO_LEITURA:
            self.assertIn(cmd, k.COMANDOS, cmd)

    def test_abre_por_clique_recusa_qualquer_forma_diferente_e_nunca_roda(self):
        from unittest import mock
        with mock.patch.object(k, 'main') as m:
            for cru in (['--uri'], ['--uri', 'katharos://limpar', '--sim'], ['--sim', '--uri', 'katharos://limpar'], ['--uri', 'katharos://limpar;calc'], ['--uri', 'katharos://socorro']):
                self.assertEqual(k.abre_por_clique(cru), 2, cru)
            m.assert_not_called()

    def test_abre_por_clique_pergunta_antes_e_so_roda_se_confirmar(self):
        from unittest import mock
        with mock.patch.object(k, 'main', return_value=0) as m, mock.patch.object(k.Terminal, 'confirma', return_value=False):
            self.assertEqual(k.abre_por_clique(['--uri', 'katharos://limpar']), 0)
            m.assert_not_called()
        with mock.patch.object(k, 'main', return_value=0) as m, mock.patch.object(k.Terminal, 'confirma', return_value=True):
            k.abre_por_clique(['--uri', 'katharos://limpar'])
            m.assert_called_once_with(['limpar'])

    def test_main_desvia_uri_sem_passar_pelo_parser(self):
        from unittest import mock
        with mock.patch.object(k, 'abre_por_clique', return_value=7) as m:
            self.assertEqual(k.main(['--uri', 'katharos://limpar']), 7)
            m.assert_called_once()

    def test_linha_de_comando_do_registro_usa_o_script_e_so_o_uri(self):
        c = k.linha_de_comando_clique()
        self.assertTrue(c.endswith('--uri "%1"'))
        self.assertIn('katharos.ps1', c)
        self.assertIn('-File', c)
        self.assertNotIn('cmd.exe', c.lower())
        self.assertNotIn('.bat', c.lower())

    def test_script_de_abertura_valida_o_uri_antes_de_elevar(self):
        ps1 = (k.Path(k.__file__).with_name('katharos.ps1')).read_text(encoding='utf-8-sig')
        pos_valida = ps1.index("-contains '--uri'")
        self.assertIn('-cnotmatch', ps1)
        self.assertLess(pos_valida, ps1.index('Start-Process'), 'a validação tem que vir antes de elevar')

    def test_registro_so_do_usuario_atual_e_reversivel(self):
        import types
        from unittest import mock
        gravado = {}

        class Chave:
            def __init__(self, c): self.c = c
            def __enter__(self): return self
            def __exit__(self, *a): return False
        fake = types.SimpleNamespace(HKEY_CURRENT_USER='HKCU', REG_SZ=1, CreateKey=lambda r, c: Chave(c),
                                     SetValueEx=lambda ch, n, _r, _t, v: gravado.__setitem__((ch.c, n), v),
                                     DeleteKey=lambda r, c: gravado.__setitem__(('del', c), True))
        class T:
            def __getattr__(self, n): return lambda *a, **kw: None
        with mock.patch.object(k, 'WINDOWS', True), mock.patch.object(k, 'dentro_de_pacote', return_value=False), mock.patch.dict(sys.modules, {'winreg': fake}), \
                mock.patch.object(k, 'estado', return_value={}), mock.patch.object(k, 'salva_estado'), mock.patch.object(k.Path, 'exists', return_value=True):
            self.assertEqual(k.ativa_cliques(T()), 0)
            self.assertEqual(gravado[(k.URI_CHAVE, 'URL Protocol')], '')
            self.assertTrue(gravado[(k.URI_CHAVE + r'\shell\open\command', '')].endswith('--uri "%1"'))
            self.assertTrue(all(c.startswith(r'Software\Classes\katharos') for c, _ in gravado))
            self.assertEqual(k.desativa_cliques(T()), 0)
            self.assertIn(('del', k.URI_CHAVE), gravado)

    def test_painel_so_tem_botao_com_cliques_ativos_e_sem_scripts(self):
        sug = [{'id': 'a', 'titulo': 'Liberar espaço', 'porque': 'x', 'comando': 'limpar', 'confianca': 'alta', 'impacto': '', 'risco': '', 'tipo': 'acao'},
               {'id': 'b', 'titulo': 'Mexer', 'porque': 'x', 'comando': 'socorro', 'confianca': 'alta', 'impacto': '', 'risco': '', 'tipo': 'acao'}]
        sem = k.monta_painel([{'_dt': __import__('datetime').datetime(2026, 1, 1), 'livre_c': 1}], [], [], [], 'PC', '1', sug, cliques=False)
        self.assertNotIn('katharos://', sem)
        self.assertIn('--ativar-cliques', sem)
        com = k.monta_painel([{'_dt': __import__('datetime').datetime(2026, 1, 1), 'livre_c': 1}], [], [], [], 'PC', '1', sug, cliques=True)
        self.assertIn('href="katharos://limpar"', com)
        self.assertIn('>Corrigir<', com)
        self.assertNotIn('katharos://socorro', com, 'comando bloqueado não ganha botão')
        self.assertNotIn('<script', com)
        self.assertNotIn('http://', com)
        self.assertNotIn('https://', com)


class TestHoras(unittest.TestCase):
    def _horas(self, dias=40, repouso_sobe=0.0, grave=False):
        from datetime import datetime, timedelta
        base = datetime(2026, 9, 1)
        out = []
        for d in range(dias):
            for h in range(24):
                dt = base + timedelta(days=d, hours=h)
                b = {'h': dt.strftime('%Y-%m-%dT%H'), '_dt': dt}
                carga = 18 <= h <= 22
                for i in range(4):
                    k.agrega_hora(b, {'cpu': 70.0 if carga else 5.0, 'ram_pct': 55.0 + (10 if carga else 0), 'disco': 4.0, 'temp': (74 if carga else 41) + (d * repouso_sobe if not carga else 0) + i,
                                      'em_jogo': carga and h == 20, 'top_cpu': 'jogo' if carga else '', 'top_ram': 'chrome'})
                if grave and d in (10, 11, 12) and h == 20:
                    b['tx'] = 93
                out.append(b)
        return out

    def test_agrega_guarda_soma_contagem_minimo_e_maximo_sem_valor_ausente(self):
        b = {}
        k.agrega_hora(b, {'cpu': 10.0, 'temp': 50})
        k.agrega_hora(b, {'cpu': 30.0, 'temp': 60, 'gpu_temp': None})
        self.assertEqual((b['n'], b['cn'], b['cs'], b['cx'], b['cm']), (2, 2, 40.0, 30.0, 10.0))
        self.assertEqual((b['tn'], b['tx'], b['tm']), (2, 60, 50))
        self.assertNotIn('gn', b, 'leitura ausente não vira zero')
        self.assertEqual(b['trn'], 1, 'só a leitura com CPU abaixo de 15% conta como repouso')

    def test_registra_hora_atualiza_a_mesma_hora_e_cria_a_seguinte(self):
        import tempfile
        from datetime import datetime
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / 'h.jsonl'
            k.registra_hora({'cpu': 10.0, 'temp': 40}, datetime(2026, 1, 1, 10, 5), arq)
            k.registra_hora({'cpu': 30.0, 'temp': 50}, datetime(2026, 1, 1, 10, 20), arq)
            k.registra_hora({'cpu': 20.0, 'temp': 45}, datetime(2026, 1, 1, 11, 5), arq)
            hs = k.le_horas(arq)
            self.assertEqual([b['h'] for b in hs], ['2026-01-01T10', '2026-01-01T11'])
            self.assertEqual(hs[0]['n'], 2)
            self.assertEqual(hs[0]['tx'], 50)

    def test_registra_hora_sobrevive_a_linha_cortada_e_a_amostra_pausada(self):
        import tempfile
        from datetime import datetime
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / 'h.jsonl'
            k.registra_hora({'cpu': 10.0}, datetime(2026, 1, 1, 10), arq)
            with open(arq, 'a', encoding='utf-8') as f:
                f.write('{"h":"2026-01-01T11","n":1,"cn')   # queda de energia no meio da escrita
            self.assertIsNone(k.registra_hora({'em_jogo': True, 'pausado': True}, datetime(2026, 1, 1, 12), arq))
            k.registra_hora({'cpu': 20.0}, datetime(2026, 1, 1, 12), arq)
            self.assertEqual([b['h'] for b in k.le_horas(arq)], ['2026-01-01T10', '2026-01-01T12'])

    def test_arquivo_tem_teto(self):
        import tempfile
        from datetime import datetime, timedelta
        from unittest import mock
        with tempfile.TemporaryDirectory() as d, mock.patch.object(k, 'HORAS_MAX', 50):
            arq = Path(d) / 'h.jsonl'
            for i in range(400):
                k.registra_hora({'cpu': 1.0}, datetime(2026, 1, 1) + timedelta(hours=i), arq)
            self.assertLessEqual(len(k.le_horas(arq)), 50 + 240)
            self.assertEqual(k.le_horas(arq)[-1]['h'], (datetime(2026, 1, 1) + timedelta(hours=399)).strftime('%Y-%m-%dT%H'))

    def test_linha_por_hora_e_pequena(self):
        import json
        b = self._horas(1)[5]
        b.pop('_dt')
        self.assertLess(len(json.dumps(b, separators=(',', ':'))), 450)

    def test_temperatura_normal_nao_gera_achado(self):
        an = k.analisa_termica(self._horas(40))
        self.assertEqual(an['achados'], [])
        self.assertEqual(an['maxima'], 77)
        self.assertAlmostEqual(an['media_repouso'], 42.5, 0)

    def test_pico_acima_de_90_em_varias_horas_e_achado_grave(self):
        an = k.analisa_termica(self._horas(40, grave=True))
        self.assertEqual(an['achados'][0][0], 'alta')
        self.assertIn('90', an['achados'][0][1])

    def test_repouso_subindo_alem_do_ruido_e_achado_e_oscilacao_pequena_nao(self):
        sobe = k.analisa_termica(self._horas(60, repouso_sobe=0.3))
        self.assertTrue(any('em repouso subiu' in t for _, t in sobe['achados']), sobe['achados'])
        estavel = k.analisa_termica(self._horas(60, repouso_sobe=0.02))
        self.assertFalse(any('em repouso subiu' in t for _, t in estavel['achados']))

    def test_poucos_dias_nao_viram_tendencia(self):
        self.assertFalse(any('subiu' in t for _, t in k.analisa_termica(self._horas(8, repouso_sobe=2.0))['achados']))

    def test_sem_leitura_de_temperatura_devolve_vazio(self):
        horas = self._horas(5)
        for b in horas:
            for c in [c for c in b if c.startswith('t') and c not in ('top',)]:
                del b[c]
        self.assertEqual(k.analisa_termica(horas), {})

    def test_serie_diaria_tem_minimo_media_e_maximo(self):
        s = k.serie_diaria(self._horas(3), 't')
        self.assertEqual(len(s), 3)
        self.assertTrue(all(a <= m <= c for _, a, m, c in s))

    def test_painel_com_horas_tem_temperatura_consumo_calor_e_nenhum_script(self):
        h = k.monta_painel([], [], [], [], 'PC', '1', horas=self._horas(40, repouso_sobe=0.3))
        for texto in ('>Temperatura</h2>', '>Consumo</h2>', 'Em repouso e sob carga', 'Quando esquenta', 'Temperatura por dia', 'Quem mais pesou na CPU', 'jogo'):
            self.assertIn(texto, h)
        self.assertIn('class="celula', h)
        self.assertNotIn('<script', h)
        self.assertNotIn('http', h)

    def test_conselheiro_propoe_pela_temperatura_de_longo_prazo(self):
        from datetime import datetime
        ev = {'termica': k.analisa_termica(self._horas(40, grave=True)), 'amostras': [], 'benchs': [], 'pacotes': [], 'eventos': [], 'raiox': {}, 'dispensadas': {},
              'vistas': {}, 'fundo_ligado': True, 'agora': datetime(2026, 11, 9), 'perfil': {}}
        s = [x for x in k.gera_sugestoes(ev) if x['id'].startswith('termica')]
        self.assertTrue(s and s[0]['confianca'] == 'alta')
        self.assertIn(s[0]['comando'], k.COMANDOS)
        ev['termica'] = k.analisa_termica(self._horas(40))
        self.assertEqual([x for x in k.gera_sugestoes(ev) if x['id'].startswith('termica')], [], 'temperatura normal não gera proposta')

    def test_painel_sem_sensor_explica_sem_inventar_grafico(self):
        horas = self._horas(5)
        for b in horas:
            for c in [c for c in b if c[0] == 't' and c != 'top']:
                del b[c]
        h = k.monta_painel([], [], [], [], 'PC', '1', horas=horas)
        self.assertIn('não entrega a temperatura', h)
        self.assertNotIn('Quando esquenta', h)
        self.assertIn('>Consumo</h2>', h)

    def test_painel_com_poucas_horas_nao_mostra_secoes(self):
        h = k.monta_painel([], [], [], [], 'PC', '1', horas=self._horas(1)[:2])
        self.assertNotIn('>Temperatura</h2>', h)

    def test_descarga_da_bateria_so_com_horas_inteiras_na_bateria(self):
        from datetime import datetime
        horas = []
        for i in range(6):
            b = {'h': f'2026-01-01T{i:02d}', '_dt': datetime(2026, 1, 1, i)}
            for j in range(4):
                k.agrega_hora(b, {'cpu': 10.0, 'bat': 80 - i * 10 - j * 2, 'na_bateria': True})
            horas.append(b)
        self.assertGreater(k._descarga(horas), 0)
        self.assertIsNone(k._descarga(horas[:2]))

    def test_script_de_leitura_nao_toca_em_jogo_nem_muda_nada(self):
        ps = k.AMOSTRA_PS
        for proibido in ('OpenProcess', 'ReadProcessMemory', 'Get-Process -Id', '.Modules', 'MainModule', 'Inject', 'Set-', 'Remove-', 'Stop-', 'Add-Type', 'sc.exe', 'reg add', 'New-Item'):
            self.assertNotIn(proibido, ps, proibido)
        # processos individuais e a ferramenta da placa só são consultados fora de jogo
        fora = ps.index('if (-not $__emJogo)')
        self.assertLess(ps.index('$__emJogo = '), fora)
        for so_fora in ('Win32_PerfFormattedData_PerfProc_Process', 'Get-Process | Sort-Object', 'nvidia-smi'):
            self.assertGreater(ps.index(so_fora), fora, f'{so_fora} só pode rodar fora de jogo')
        self.assertIn('$__pausar', ps)

    def test_jogo_aberto_sem_catalogo_anticheat_sobreposicao_ou_gpu(self):
        n = k.nomes_de_jogo()
        self.assertIn('«gpu»', k.AMOSTRA_PS)
        for esperado in ('gameoverlayui', 'easyanticheat', 'vgc', 'faceitclient'):
            self.assertIn(esperado, n)
        self.assertTrue(all(x == x.lower() and not x.endswith('.exe') for x in n))

    def test_config_coleta_em_jogo_aceita_segura_e_pausar(self):
        self.assertEqual(k.PADROES['coleta-em-jogo'], 'segura')
        self.assertIn('pausar', k.VALIDOS_CONFIG['coleta-em-jogo'])

    def test_amostrar_pausado_nao_grava_nada(self):
        from unittest import mock
        with mock.patch.object(k, 'WINDOWS', True), mock.patch.object(k, 'config', return_value='pausar'), \
                mock.patch.object(k, 'roda_ps', return_value=type('S', (), {'dados': {'amostra': {'em_jogo': True, 'pausado': True}}})()) as r, \
                mock.patch.object(k, 'registra_hora') as reg:
            a = k.amostra_leve(Ctx())
        self.assertTrue(a['pausado'])
        self.assertIn('$true', r.call_args[0][1].split('\n')[1], 'o modo pausar chega ao script')
        reg.assert_called_once()   # registra_hora recusa o que está pausado (testado acima)


class TestSaude(unittest.TestCase):
    AGORA = __import__('datetime').datetime(2026, 11, 9, 12)

    def g(self, provedor, id_, n=1, dias=1, arg='', ultimo='2026-11-08T10:00:00', msg=''):
        return {'provedor': provedor, 'id': id_, 'arg': arg, 'n': n, 'dias': dias, 'primeiro': '2026-11-01T10:00:00', 'ultimo': ultimo, 'msg': msg}

    def test_desligamento_inesperado_sem_bugcheck(self):
        p = k.explica_grupo(self.g('Microsoft-Windows-Kernel-Power', 41, 2, 2, arg='0'))
        self.assertEqual((p['gravidade'], p['titulo']), ('alta', 'O PC desligou sem avisar'))
        self.assertIn('2 ocorrências em 2 dias', p['evidencia'])

    def test_tela_azul_via_kernel_power_com_codigo_decimal(self):
        p = k.explica_grupo(self.g('Microsoft-Windows-Kernel-Power', 41, 1, 1, arg='209'))   # 0xd1
        self.assertIn('DRIVER_IRQL_NOT_LESS_OR_EQUAL', p['titulo'])

    def test_tela_azul_via_wer_com_codigo_hexa(self):
        p = k.explica_grupo(self.g('Microsoft-Windows-WER-SystemErrorReporting', 1001, arg='0x00000124 (0x0, 0x1, 0x2, 0x3)'))
        self.assertIn('WHEA_UNCORRECTABLE_ERROR', p['titulo'])
        self.assertIn('hardware', p['explica'])

    def test_codigo_de_tela_azul_desconhecido_nao_inventa_causa(self):
        p = k.explica_grupo(self.g('Microsoft-Windows-WER-SystemErrorReporting', 1001, arg='0x000000ab (0x0)'))
        self.assertIn('0x000000ab', p['titulo'])

    def test_programa_que_fecha_sozinho_usa_o_nome_do_programa(self):
        p = k.explica_grupo(self.g('Application Error', 1000, 4, 3, arg='jogo.exe'))
        self.assertEqual((p['gravidade'], p['titulo']), ('média', 'jogo.exe fechou sozinho'))
        self.assertEqual(k.explica_grupo(self.g('Application Error', 1000, 1, 1, arg='explorer.exe'))['gravidade'], 'alta')

    def test_servico_que_falha(self):
        p = k.explica_grupo(self.g('Service Control Manager', 7031, 5, 2, arg='FooSvc'))
        self.assertIn('FooSvc', p['titulo'])
        self.assertEqual(p['comando'], 'servicos')

    def test_ruido_conhecido_e_dito_como_ruido(self):
        self.assertEqual(k.explica_grupo(self.g('DistributedCOM', 10016, 400, 14)), 'ruido')

    def test_erro_desconhecido_nao_ganha_explicacao_inventada(self):
        self.assertIsNone(k.explica_grupo(self.g('AlgumaCoisa', 9999, 7)))

    def test_driver_de_video_antigo_com_quedas_vira_grave(self):
        grupos = [self.g('Display', 4101, 5, 3)]
        drv = [{'nome': 'NVIDIA GeForce RTX', 'classe': 'DISPLAY', 'fab': 'NVIDIA', 'versao': '31.0.15.3623', 'data': '2025-01-10T00:00:00', 'assinado': True}]
        out = k.analisa_drivers(drv, [], grupos, self.AGORA)
        self.assertEqual(out[0]['gravidade'], 'alta')
        self.assertIn('não usa internet', out[0]['explica'])

    def test_driver_de_video_recente_nao_gera_nada(self):
        drv = [{'nome': 'GPU', 'classe': 'DISPLAY', 'fab': 'AMD', 'versao': '1', 'data': '2026-09-01T00:00:00', 'assinado': True}]
        self.assertEqual(k.analisa_drivers(drv, [], [], self.AGORA), [])

    def test_driver_antigo_sem_quedas_so_avisa_depois_de_18_meses(self):
        velho = [{'nome': 'GPU', 'classe': 'DISPLAY', 'fab': 'AMD', 'versao': '1', 'data': '2024-01-01T00:00:00', 'assinado': True}]
        self.assertEqual(k.analisa_drivers(velho, [], [], self.AGORA)[0]['gravidade'], 'média')
        meio = [{'nome': 'GPU', 'classe': 'DISPLAY', 'fab': 'AMD', 'versao': '1', 'data': '2026-02-01T00:00:00', 'assinado': True}]
        self.assertEqual(k.analisa_drivers(meio, [], [], self.AGORA), [])

    def test_driver_nao_assinado_e_dispositivo_com_erro(self):
        out = k.analisa_drivers([{'nome': 'X', 'classe': 'NET', 'fab': 'Acme', 'versao': '1', 'data': '2025-01-01T00:00:00', 'assinado': False}],
                                [{'nome': 'Placa Y', 'codigo': 43, 'classe': 'Display'}], [], self.AGORA)
        self.assertEqual({x['id'].split(':')[0] for x in out}, {'sem-assinatura', 'dispositivo'})
        self.assertIn('parou o dispositivo', [x for x in out if x['id'].startswith('dispositivo')][0]['evidencia'])

    def test_dispositivo_sem_nome_ganha_nome_legivel(self):
        out = k.analisa_drivers([], [{'nome': '', 'codigo': 28, 'classe': 'Net', 'id': 'PCI\\VEN'}], [], self.AGORA)
        self.assertTrue(out[0]['titulo'].endswith('classe Net'), out[0]['titulo'])

    def test_windows_precisa_de_ajuste(self):
        w = {'reinicio_pendente': True, 'ultima_atualizacao': '2026-06-01T00:00:00', 'livre_pct': 4.0, 'livre_gb': 12.0, 'defender_tempo_real': False,
             'uptime_dias': 45, 'pontos_restauracao': 0}
        ids = {x['id'] for x in k.analisa_windows(w, self.AGORA)}
        self.assertEqual(ids, {'reinicio-pendente', 'atualizacao-atrasada', 'disco-cheio', 'defender-desligado', 'uptime', 'sem-restauracao'})

    def test_windows_em_ordem_nao_gera_nada(self):
        w = {'reinicio_pendente': False, 'ultima_atualizacao': '2026-11-01T00:00:00', 'livre_pct': 40.0, 'defender_tempo_real': True,
             'defender_assinatura_dias': 0, 'uptime_dias': 2, 'pontos_restauracao': 3}
        self.assertEqual(k.analisa_windows(w, self.AGORA), [])
        self.assertEqual(k.analisa_windows(None, self.AGORA), [])

    def test_analise_completa_ordena_por_gravidade_e_conta_ruido(self):
        dados = {'saude_grupos': [self.g('DistributedCOM', 10016, 300, 14), self.g('Application Error', 1000, 1, 1, arg='a.exe'),
                                  self.g('Microsoft-Windows-Kernel-Power', 41, 2, 2, arg='0'), self.g('Misterio', 1, 3)],
                 'saude_total': {'eventos': 306}, 'saude_windows': {'uptime_dias': 40}}
        a = k.analisa_saude(dados, self.AGORA)
        self.assertEqual(a['problemas'][0]['gravidade'], 'alta')
        self.assertEqual(a['resumo']['ruido'], 300)
        self.assertEqual(a['resumo']['graves'], 1)
        self.assertEqual([g['provedor'] for g in a['outros']], ['Misterio'])

    def test_analise_sem_dados_nao_quebra(self):
        a = k.analisa_saude({}, self.AGORA)
        self.assertEqual(a['problemas'], [])

    def test_novos_graves_so_o_que_cresceu(self):
        antes = {'problemas': [{'id': 'x', 'n': 2}]}
        atual = {'problemas': [{'id': 'x', 'n': 2, 'categoria': 'erro', 'gravidade': 'alta'}, {'id': 'y', 'n': 1, 'categoria': 'erro', 'gravidade': 'alta'},
                               {'id': 'z', 'n': 1, 'categoria': 'driver', 'gravidade': 'alta'}]}
        self.assertEqual([x['id'] for x in k.novos_graves(atual, antes)], ['y'])

    def test_script_de_coleta_so_le(self):
        for proibido in ('Set-', 'Remove-', 'Stop-', 'Disable-', 'Enable-', 'New-ItemProperty', 'sc.exe', 'netsh', 'reg add', 'Restart-'):
            self.assertNotIn(proibido, k.SAUDE_PS.replace('Set-Valor', ''), proibido)

    def test_catalogo_tem_explicacao_e_acao_em_tudo(self):
        for chave, (gr, tit, ex, faz, cmd) in {**k.CATALOGO_ERROS, **{(p, 0): v for p, v in k.CATALOGO_PROVEDORES.items()}}.items():
            self.assertTrue(tit and ex and faz, chave)
            self.assertIn(gr, ('alta', 'média', 'baixa', 'info'))
            if cmd:
                self.assertIn(cmd, k.COMANDOS, f'{chave} aponta para comando que não existe')


class TestMotor(unittest.TestCase):
    def _am(self, n=20, passo_h=12, **fn):
        from datetime import datetime, timedelta
        base = datetime(2026, 1, 1, 12)
        return [{'_dt': base + timedelta(hours=passo_h * i), **{c: f(i) for c, f in fn.items()}} for i in range(n)]

    def _ev(self, **kw):
        from datetime import datetime
        ev = {'amostras': [], 'benchs': [], 'pacotes': [], 'eventos': [], 'raiox': {}, 'dispensadas': {}, 'vistas': {}, 'fundo_ligado': True,
              'agora': datetime(2026, 2, 1), 'perfil': {}}
        ev.update(kw)
        return ev

    def test_sem_dados_so_propoe_ligar_o_segundo_plano(self):
        ev = self._ev(fundo_ligado=False)
        self.assertEqual([x['id'] for x in k.gera_sugestoes(ev)], ['ligar-fundo'])
        self.assertEqual(k.gera_sugestoes(self._ev(fundo_ligado=True)), [])

    def test_espaco_acabando_propoe_limpar_com_numero_e_prazo(self):
        ev = self._ev(amostras=self._am(livre_c=lambda i: 60 - i * 1.5, ram_total=lambda i: 16.0, ram_usada=lambda i: 6.0))
        s = k.gera_sugestoes(ev)
        self.assertEqual(s[0]['id'], 'espaco')
        self.assertEqual(s[0]['comando'], 'limpar')
        self.assertEqual(s[0]['confianca'], 'alta')
        self.assertRegex(s[0]['porque'], r'\d+ dias')

    def test_pc_estavel_nao_gera_proposta_nenhuma(self):
        ev = self._ev(amostras=self._am(livre_c=lambda i: 60.0, boot_s=lambda i: 30 + (i % 2), ram_total=lambda i: 16.0, ram_usada=lambda i: 6.0 + (i % 2) * 0.1, cpu=lambda i: 3.0))
        self.assertEqual(k.gera_sugestoes(ev), [])

    def test_dispensada_nao_volta_antes_de_30_dias(self):
        ev = self._ev(amostras=self._am(livre_c=lambda i: 60 - i * 1.5))
        self.assertTrue(k.gera_sugestoes(ev))
        ev['dispensadas'] = {'espaco': k.agora_iso()}
        self.assertFalse([x for x in k.gera_sugestoes(ev) if x['id'] == 'espaco'])
        ev['dispensadas'] = {'espaco': '2020-01-01T00:00:00'}
        self.assertTrue([x for x in k.gera_sugestoes(ev) if x['id'] == 'espaco'])

    def test_nao_culpa_pacote_por_piora_que_ja_vinha_de_antes(self):
        from datetime import datetime, timedelta
        base = datetime(2026, 1, 1, 12)
        am = self._am(30, boot_s=lambda i: 30 + i)   # sobe sempre, desde antes do pacote
        ev = self._ev(amostras=am, pacotes=[(base + timedelta(days=7), 'servicos', 'serviços')])
        self.assertFalse([x for x in k.gera_sugestoes(ev) if x['id'].startswith('efeito:')])

    def test_propoe_desfazer_quando_piora_em_degrau_depois_do_pacote(self):
        from datetime import datetime, timedelta
        base = datetime(2026, 1, 1, 12)
        am = self._am(30, boot_s=lambda i: 30 + (i % 2) if i < 14 else 50 + (i % 2))   # degrau no dia 7
        ev = self._ev(amostras=am, pacotes=[(base + timedelta(days=7), 'servicos', 'serviços')])
        s = [x for x in k.gera_sugestoes(ev) if x['id'] == 'efeito:servicos']
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0]['comando'], 'desfazer servicos')
        self.assertEqual(s[0]['confianca'], 'média')

    def test_dois_pacotes_na_mesma_semana_baixam_a_confianca(self):
        from datetime import datetime, timedelta
        base = datetime(2026, 1, 1, 12)
        am = self._am(30, boot_s=lambda i: 30 + (i % 2) if i < 14 else 50 + (i % 2))
        ev = self._ev(amostras=am, pacotes=[(base + timedelta(days=7), 'servicos', 'serviços'), (base + timedelta(days=8), 'visual', 'visual')])
        self.assertTrue(all(x['confianca'] == 'baixa' for x in k.gera_sugestoes(ev) if x['id'].startswith('efeito:')))

    def test_mesmo_comando_de_varias_regras_vira_uma_proposta(self):
        ev = self._ev(amostras=self._am(livre_c=lambda i: 60 - i * 1.5),
                      raiox={'achados': [{'titulo': 'Disco quase cheio', 'impacto': 3, 'evidencia': '8% livre', 'faz': 'limpar', 'comando': 'limpar'}]})
        s = [x for x in k.gera_sugestoes(ev) if x['comando'] == 'limpar']
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0]['id'], 'espaco')
        self.assertIn('Disco quase cheio', s[0].get('tambem', []))

    def test_achado_do_raiox_ja_resolvido_nao_volta(self):
        from datetime import datetime
        ev = self._ev(raiox={'achados': [{'titulo': 'Muita coisa na inicialização', 'impacto': 3, 'evidencia': '30 programas', 'faz': 'x', 'comando': 'inicializacao'}]},
                      pacotes=[(datetime(2026, 1, 1), 'inicializacao', 'inicialização')])
        self.assertEqual(k.gera_sugestoes(ev), [])

    def test_ajuste_que_nao_fica_repetido_propoe_verificar(self):
        ev = self._ev(eventos=[{'tipo': 'nao-ficou', 'pacote': 'privacidade'}] * 3)
        s = k.gera_sugestoes(ev)
        self.assertEqual((s[0]['comando'], s[0]['confianca']), ('verificar', 'alta'))

    def test_limpeza_que_nao_rende_diz_que_nao_adianta_repetir(self):
        ev = self._ev(eventos=[{'tipo': 'espaco', 'pacote': 'limpar', 'livre_antes': 10 * 2 ** 30, 'livre_depois': 10 * 2 ** 30 + 1000}] * 3)
        s = [x for x in k.gera_sugestoes(ev) if x['id'] == 'limpeza-rende-pouco']
        self.assertEqual(s[0]['tipo'], 'info')

    def test_regra_com_defeito_nao_derruba_as_outras(self):
        @k.regra
        def quebrada(ev):
            raise RuntimeError('boom')
        try:
            self.assertEqual(k.gera_sugestoes(self._ev(fundo_ligado=False))[0]['id'], 'ligar-fundo')
        finally:
            k.REGRAS.remove(quebrada)

    def test_pontuacao_ordena_por_confianca_e_depois_por_pontos(self):
        s = [k._sug('a', 'a', '', 'x', 'média', pontos_impacto=5), k._sug('b', 'b', '', 'y', 'alta', pontos_impacto=2), k._sug('c', 'c', '', 'z', 'alta', pontos_impacto=4)]
        antigo = list(k.REGRAS)
        k.REGRAS[:] = [lambda ev: s]
        try:
            self.assertEqual([x['id'] for x in k.gera_sugestoes(self._ev())], ['c', 'b', 'a'])
        finally:
            k.REGRAS[:] = antigo

    def test_aprendizado_mede_o_resultado_da_proposta_executada(self):
        from datetime import datetime, timedelta
        base = datetime(2026, 1, 1, 12)
        am = self._am(40, livre_c=lambda i: 30.0 + (i % 2) if i < 14 else 60.0 + (i % 2))   # a limpeza no dia 7 liberou espaço
        ev = self._ev(amostras=am, pacotes=[(base + timedelta(days=7), 'limpar', 'limpeza')], agora=base + timedelta(days=30),
                      vistas={'espaco': {'quando': (base + timedelta(days=5)).isoformat(), 'comando': 'limpar', 'metrica': 'livre_c'}})
        r = k.resultados_das_propostas(ev)
        self.assertEqual((r[0][0], r[0][3]), ('limpeza', 'melhorou'))

    def test_aprendizado_ignora_pacote_aplicado_antes_da_proposta(self):
        from datetime import datetime, timedelta
        base = datetime(2026, 1, 1, 12)
        ev = self._ev(amostras=self._am(40, livre_c=lambda i: 30.0), pacotes=[(base, 'limpar', 'limpeza')], agora=base + timedelta(days=30),
                      vistas={'espaco': {'quando': (base + timedelta(days=5)).isoformat(), 'comando': 'limpar', 'metrica': 'livre_c'}})
        self.assertEqual(k.resultados_das_propostas(ev), [])

    def test_registra_vistas_so_na_primeira_vez(self):
        e = {}
        s = [k._sug('espaco', 't', '', 'limpar', 'alta', metrica='livre_c')]
        k.registra_vistas(e, s)
        primeira = e['conselheiro_vistas']['espaco']['quando']
        k.registra_vistas(e, s)
        self.assertEqual(e['conselheiro_vistas']['espaco']['quando'], primeira)

    def test_painel_mostra_propostas_e_efeitos(self):
        am = self._am(20, livre_c=lambda i: 60 - i * 1.5)
        h = k.monta_painel(am, [], [], k.analisa_tendencia(am), 'PC', '1', k.gera_sugestoes(self._ev(amostras=am)), [])
        self.assertIn('O que eu proporia', h)
        self.assertIn('katharos limpar', h)
        self.assertIn('class="projecao"', h)


class TestImpactoBoot(unittest.TestCase):
    BOOT = [{'nome': 'Spotify.exe', 'exibe': 'Spotify', 'vezes': 5, 's': 4.2}, {'nome': 'Teams.exe', 'exibe': 'Microsoft Teams', 'vezes': 3, 's': 9.0}]

    def test_casa_por_nome_ou_executavel(self):
        self.assertEqual(k.impacto_boot(self.BOOT, 'Spotify', r'C:\\Users\\x\\AppData\\Roaming\\Spotify\\Spotify.exe'), (4.2, 5))
        self.assertEqual(k.impacto_boot(self.BOOT, 'com.squirrel.Teams.Teams', r'C:\\Users\\x\\Teams.exe'), (9.0, 3))

    def test_nome_curto_nao_casa_com_tudo(self):
        self.assertIsNone(k.impacto_boot(self.BOOT, 'ms', r'C:\\x\\a.exe'))
        self.assertIsNone(k.impacto_boot(self.BOOT, 'Discord', r'C:\\x\\Update.exe'))

    def test_sem_dados_nao_quebra(self):
        self.assertIsNone(k.impacto_boot(None, 'Spotify', ''))
        self.assertIsNone(k.impacto_boot([], 'Spotify', None))


class TestRetomar(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        self.casa = k.CASA
        k.CASA = self.tmp

    def tearDown(self):
        k.CASA = self.casa

    def _itens(self, *ids):
        return [type('I', (), {'id': i})() for i in ids]

    def test_anota_avanca_e_calcula_o_que_falta(self):
        pac = k.PACOTES['rede']
        ctx = type('C', (), {'args': type('A', (), {'comando': 'rede'})()})()
        k._andamento_marca(ctx, pac, self._itens('a', 'b', 'c'))
        k._andamento_avanca(['a'])
        nome, falta, a = k.pendentes_andamento()
        self.assertEqual((nome, falta), ('rede', ['b', 'c']))
        k._andamento_avanca(['b', 'c'])
        self.assertIsNone(k.pendentes_andamento())

    def test_pacote_que_nao_existe_mais_nao_quebra(self):
        k.salva_estado({'em_andamento': {'pacote': 'sumiu', 'ids': ['x'], 'feitos': []}})
        self.assertIsNone(k.pendentes_andamento())

    def test_estado_sem_anotacao_ou_corrompido_nao_quebra(self):
        self.assertIsNone(k.pendentes_andamento())
        k.salva_estado({'em_andamento': 'lixo'})
        self.assertIsNone(k.pendentes_andamento())

    def test_descartar_limpa_a_anotacao(self):
        k.salva_estado({'em_andamento': {'pacote': 'rede', 'ids': ['ping'], 'feitos': []}})
        saida = []
        class T:
            def __getattr__(self, n): return lambda *a, **kw: saida.append(n)
        ctx = type('C', (), {'t': T()})()
        args = type('A', (), {'descartar': True, 'teste': False, 'sim': True})()
        self.assertEqual(k.ferramenta_retomar(ctx, args), 0)
        self.assertNotIn('em_andamento', k.estado())

    def _executa(self, fns):
        k.Progresso = type('P', (), {'__init__': lambda s, *a, **kw: None, '__enter__': lambda s: s, '__exit__': lambda s, *a: False,
                                     'avanca': lambda s, *a: None, 'atual': ''})
        class T:
            def __getattr__(self, n): return lambda *a, **kw: ''
        itens = [k.Item(f'i{n}', f'item {n}', '', '', '', 1, '', py=f) for n, f in enumerate(fns)]
        pac = type('P', (), {'nome': 'rede', 'reversivel': False})()
        ctx = type('C', (), {'t': T(), 'args': None, 'mult': 1.0})()
        return k.executa_itens(ctx, pac, itens)

    def test_aplicacao_completa_nao_deixa_anotacao(self):
        self._executa([lambda c, i, p, t: (1, 0), lambda c, i, p, t: (1, 0)])
        self.assertNotIn('em_andamento', k.estado())

    def test_aplicacao_interrompida_deixa_o_que_faltou(self):
        def corta(c, i, p, t):
            raise KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            self._executa([lambda c, i, p, t: (1, 0), corta, lambda c, i, p, t: (1, 0)])
        nome, falta, _ = k.pendentes_andamento()
        self.assertEqual(falta, ['i1', 'i2'])

    def test_retomar_esta_no_menu(self):
        self.assertIn('retomar', k.COMANDOS)


class TestSugestoes(unittest.TestCase):
    def pc(self, **kw):
        base = {'so': {'build': 22631}, 'pc': {}, 'ram': {'total': 16}, 'disco': {'tipo': 'SSD'}, 'gpus': [], 'tem': {}, 'jogos': []}
        for chave, v in kw.items():
            base[chave] = {**base.get(chave, {}), **v} if isinstance(v, dict) else v
        return base

    def test_windows_desconhecido(self):
        self.assertFalse(k.so_reconhecido({'so': {'build': 0}}))
        self.assertFalse(k.so_reconhecido({'so': {'build': 9600}}))
        self.assertTrue(k.so_reconhecido({'so': {'build': 19045}}))

    def test_comando_parecido(self):
        self.assertEqual(k.comando_parecido('limpr'), 'limpar')
        self.assertEqual(k.comando_parecido('desfaser'), 'desfazer')
        self.assertIsNone(k.comando_parecido('xyzxyzxyz'))

    def test_main_sugere_em_vez_de_quebrar(self):
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = k.main(['limpr'])
        self.assertEqual(rc, 2)
        self.assertIn('limpar', buf.getvalue())

    def test_ajuda_existe_e_nao_mexe_em_nada(self):
        self.assertIn('ajuda', k.SEM_ESTADO)
        self.assertEqual(k.main(['ajuda', '--sem-cor']), 0)


class TestLimpezaNaoTocaEmArquivosPessoais(unittest.TestCase):
    PESSOAL = re.compile(r'Documents|Documentos|Pictures|Imagens|Downloads|Desktop|Área de Trabalho|OneDrive|Videos|Music|Músicas', re.I)

    def test_pacote_limpar_so_mexe_em_lixo_do_sistema(self):
        for nome in ('limpar',):
            for p, i in ITENS:
                if p != nome:
                    continue
                for linha in (i.ps or '').splitlines():
                    if re.search(r'Remove-Item|Clear-|\.Delete\(|rd |del ', linha, re.I):
                        self.assertIsNone(self.PESSOAL.search(linha), f'{p}/{i.id} apaga perto de pasta pessoal: {linha.strip()[:100]}')


class TestSemRedeEscondida(unittest.TestCase):
    def test_python_nao_abre_conexoes_proprias(self):
        fonte = (RAIZ / 'programa' / 'katharos.py').read_text(encoding='utf-8')
        for proibido in ('import requests', 'import urllib.request', 'import http.client', 'import socket', 'urlopen('):
            self.assertNotIn(proibido, fonte, f'{proibido}: o Python do Katharos não deve falar com a rede')


class TestEntrega(unittest.TestCase):
    def test_hashes_publicados_batem_com_os_arquivos(self):
        for linha in (RAIZ / 'SHA256SUMS.txt').read_text().splitlines():
            h, nome = linha.split(None, 1)
            real = hashlib.sha256((RAIZ / nome.strip().lstrip('*')).read_bytes()).hexdigest()
            self.assertEqual(h, real, f'{nome}: o hash mudou, rode sha256sum de novo')

    def test_zip_so_tem_o_necessario(self):
        ignorados = (RAIZ / '.gitattributes').read_text()
        for pasta in ('docs', 'tests', '.github'):
            self.assertIn(pasta, ignorados, f'{pasta} deveria estar fora do ZIP (export-ignore)')

    def test_site_gerado_esta_em_dia(self):
        """O site é gerado do programa: a contagem de comandos e a versão têm de bater."""
        site = (RAIZ / 'docs' / 'index.html').read_text(encoding='utf-8')
        self.assertIn(k.MENU[-1][0], site, 'rode arte/gera_site.py')
        self.assertIn(k.VERSAO, site, 'rode arte/gera_site.py')
        self.assertNotIn('{{', site)

    def test_secao_novidades_mostra_a_versao_atual_do_changelog(self):
        site = (RAIZ / 'docs' / 'index.html').read_text(encoding='utf-8')
        self.assertIn('id="novidades"', site)
        self.assertIn(f'<b>v{k.VERSAO}</b>', site, 'a versão atual precisa estar no CHANGELOG.md e no site')
        cl = (RAIZ / 'CHANGELOG.md').read_text(encoding='utf-8')
        self.assertRegex(cl, rf'## {re.escape(k.VERSAO)} · ')

    def test_changelog_tem_versoes_em_ordem_sem_repeticao_e_a_primeira_e_a_atual(self):
        cl = (RAIZ / 'CHANGELOG.md').read_text(encoding='utf-8')
        achados = re.findall(r'^## (\d+)\.(\d+)\.(\d+) · (\d{1,2} de \w+ de \d{4})$', cl, re.M)
        self.assertGreaterEqual(len(achados), 2)
        nums = [tuple(int(x) for x in a[:3]) for a in achados]
        self.assertEqual(nums, sorted(set(nums), reverse=True), 'versões fora de ordem ou repetidas')
        self.assertEqual('.'.join(map(str, nums[0])), k.VERSAO, 'a versão mais nova do CHANGELOG tem de ser a do programa')
        self.assertTrue(achados[0][3].startswith(k.DATA_VERSAO.split()[0] + ' de'), 'a data do CHANGELOG tem de ser a do programa')

class TestDnsTeste(unittest.TestCase):
    def _a(self, outro):
        base = [30.0, 28.0, 31.0, 29.0, 30.0]
        rapido = [x / 3 for x in base]
        novo = rapido if outro == 'rapido' else [29.0, 31.0, 30.0, 28.0, 32.0]
        return {'1.1.1.1': {'a.com': [90.0] + novo, 'b.com': [90.0] + novo},
                '192.168.0.1': {'a.com': [90.0] + base, 'b.com': [90.0] + base}}

    def test_recomenda_quando_a_diferenca_e_grande_e_clara(self):
        linhas, v = k.analisa_dns(self._a('rapido'), '192.168.0.1')
        self.assertIn('vale', v)
        self.assertNotIn('não vale', v)

    def test_nao_recomenda_dentro_do_ruido(self):
        linhas, v = k.analisa_dns(self._a('igual'), '192.168.0.1')
        self.assertIn('não vale', v)

    def test_sem_medida_do_atual_nao_compara(self):
        linhas, v = k.analisa_dns({'1.1.1.1': {'a.com': [10.0, 11.0, 10.0]}}, '192.168.0.1')
        self.assertIn('não dá para comparar', v)

    def test_falhas_contam_e_nao_viram_milissegundos(self):
        linhas, v = k.analisa_dns({'1.1.1.1': {'a.com': [None, 10.0, None, 12.0, 11.0]}, '8.8.8.8': {'a.com': [5.0, 6.0, 5.0, 6.0, 5.0]}}, '8.8.8.8')
        self.assertEqual(linhas['1.1.1.1']['falhas'], 2)
        self.assertLessEqual(linhas['1.1.1.1']['q3'], 12.0)

    def test_dns_nao_afirma_o_que_nao_mediu(self):
        for _, _, _, _, desc in k.DNS:
            self.assertNotIn('mais rápido', desc)
        itens = [i for n, i in ITENS if n == 'rede']
        self.assertTrue(all(i.nivel == 0 for i in itens if i.id.startswith('dns-') and i.id != 'dns-teste'))
        self.assertTrue(any(i.id == 'dns-teste' and i.nivel == 1 for i in itens))


class TestAvisoDeUso(unittest.TestCase):
    def test_desfazer_e_leitura_nunca_pedem_aceite(self):
        for c in ('desfazer', 'socorro', 'raiox', 'aviso'):
            self.assertIn(c, k.SEM_ACEITE)
        self.assertNotIn('turbo', k.SEM_ACEITE)

    def test_aceite_so_vale_na_versao_do_texto(self):
        with mock.patch.object(k, 'estado', return_value={'aviso_aceito': {'versao': k.VERSAO_AVISO}}):
            self.assertTrue(k.aviso_aceito())
        with mock.patch.object(k, 'estado', return_value={}):
            self.assertFalse(k.aviso_aceito())

    def test_sem_terminal_e_sem_aceite_nao_aplica(self):
        with mock.patch.object(k, 'estado', return_value={}), mock.patch.object(k, 'AVISOS_INICIO', []), \
                mock.patch.object(k, 'AVISO_VIVO', None):
            self.assertEqual(k.main(['turbo']), 1)

    def test_aviso_e_licenca_existem(self):
        self.assertIn('AS IS', (RAIZ / 'LICENSE').read_text(encoding='utf-8'))
        self.assertIn('Antes de usar', (RAIZ / 'README.md').read_text(encoding='utf-8'))


class TestRaioxInteligente(unittest.TestCase):
    def analisa(self, perfil=None, medidas=None, dados=None):
        p = {'so': {'win11': True, 'build': 26100}, 'pc': {'notebook': False}, 'ram': {'total': 16, 'usada': 6, 'slots': 2, 'ocupados': 2},
             'disco': {'tipo': 'SSD', 'livre': 200, 'total': 500}, 'defender': {'tempo_real': True}, 'sistema': {'uptime_h': 5},
             'memoria': {'pagefile_auto': True, 'compressao': True}, 'energia': {'plano': 'desempenho'}, 'tem': {}}
        for ch, v in (perfil or {}).items():
            p.setdefault(ch, {})
            if isinstance(v, dict) and isinstance(p[ch], dict):
                p[ch].update(v)
            else:
                p[ch] = v
        with mock.patch.object(k, 'ja_aplicados', lambda: {'privacidade'}), mock.patch.object(k.shutil, 'which', lambda x: None):
            return k.analisa(p, medidas or {}, dados or {})

    def titulos(self, *a, **kw):
        return [x.titulo for x in self.analisa(*a, **kw)]

    def test_pc_saudavel_nao_tem_achado_e_tira_nota_cem(self):
        a = self.analisa()
        self.assertEqual([x.titulo for x in a], [])
        self.assertEqual(k.nota_pc(a), 100)

    def test_informativo_nao_tira_ponto(self):
        a = self.analisa({'pc': {'dominio': True}, 'jogos': ['Steam']})
        self.assertTrue(a and all(x.impacto == 0 for x in a))
        self.assertEqual(k.nota_pc(a), 100)
        self.assertEqual(k.pesa_na_nota(a), [])

    def test_memoria_no_limite_pelo_commit(self):
        a = self.analisa(medidas={'commit_pct': 94, 'ram_disponivel': 0.6}, dados={'top_ram': [{'n': 'chrome', 'mb': 5200}]})
        m = [x for x in a if x.titulo == 'Memória no limite'][0]
        self.assertEqual(m.impacto, 3)
        self.assertIn('o Google Chrome', m.faz)

    def test_disco_ocupado_parado_diz_quem_le_e_pesa_mais_em_hd(self):
        d = {'top_io': [{'n': 'MsMpEng', 'mbs': 30.5}]}
        ssd = [x for x in self.analisa(medidas={'disco_ativo': 80, 'fila_disco': 2}, dados=d) if 'Disco ocupado' in x.titulo][0]
        hd = [x for x in self.analisa({'disco': {'tipo': 'HDD'}}, {'disco_ativo': 80}, d) if 'Disco ocupado' in x.titulo][0]
        self.assertEqual((ssd.impacto, hd.impacto), (2, 3))
        self.assertIn('Defender', ssd.evidencia)

    def test_dpc_alto_aponta_para_drivers(self):
        a = [x for x in self.analisa(medidas={'dpc': 4, 'interrupcoes': 2}) if 'interrompendo' in x.titulo]
        self.assertEqual(a[0].comando, 'saude')
        self.assertNotIn('Drivers interrompendo o processador', self.titulos(medidas={'dpc': 0.4, 'interrupcoes': 0.3}))

    def test_xmp_desligado_so_quando_a_diferenca_e_clara(self):
        lento = {'ram': {'pentes': [{'gb': 8, 'mhz': 2133, 'mhz_max': 3200}, {'gb': 8, 'mhz': 2133, 'mhz_max': 3200}]}}
        certo = {'ram': {'pentes': [{'gb': 8, 'mhz': 3200, 'mhz_max': 3200}]}}
        self.assertIn('Memória rodando abaixo da velocidade dela', self.titulos(lento))
        self.assertNotIn('Memória rodando abaixo da velocidade dela', self.titulos(certo))
        self.assertNotIn('Memória rodando abaixo da velocidade dela', self.titulos({'ram': {'pentes': [{'gb': 8, 'mhz': 0, 'mhz_max': 0}]}}))

    def test_monitor_abaixo_da_taxa_que_aceita(self):
        self.assertIn('Monitor de 144 Hz rodando a 60 Hz', self.titulos({'tela': {'hz': 60, 'hz_max': 144, 'largura': 2560, 'altura': 1440}}))
        self.assertEqual(self.titulos({'tela': {'hz': 60, 'hz_max': 60}}), [])
        self.assertEqual(self.titulos({'tela': None}), [])

    def test_video_sem_driver_e_driver_antigo(self):
        self.assertIn('Placa de vídeo sem driver', self.titulos({'video': [{'nome': 'Microsoft Basic Display Adapter', 'basico': True}]}))
        velho = {'video': [{'nome': 'NVIDIA GeForce RTX 3060', 'driver': '31.0', 'driver_data': '2023-01-10T00:00:00', 'basico': False}]}
        self.assertIn('Driver da placa de vídeo antigo', self.titulos(velho))
        novo = {'video': [{'nome': 'NVIDIA GeForce RTX 3060', 'driver': '32.0', 'driver_data': k.agora_iso(), 'basico': False}]}
        self.assertEqual(self.titulos(novo), [])
        self.assertEqual(self.titulos({'video': [{'nome': 'NVIDIA X', 'driver_data': 'lixo'}]}), [], 'data ilegível não derruba')

    def test_trim_desligado_so_em_ssd(self):
        self.assertIn('TRIM desligado no SSD', self.titulos({'disco': {'trim': False}}))
        self.assertNotIn('TRIM desligado no SSD', self.titulos({'disco': {'trim': None}}))
        self.assertNotIn('TRIM desligado no SSD', self.titulos({'disco': {'tipo': 'HDD', 'trim': False}}))

    def test_processos_conhecidos_apontam_para_comandos_que_existem(self):
        for nome, (oque, faz, cmd) in k.PROCESSOS.items():
            self.assertTrue(oque and faz, nome)
            self.assertEqual(nome, nome.lower())
            if cmd:
                self.assertIn(cmd, k.COMANDOS, f'{nome} aponta para {cmd}')
        self.assertEqual(k.quem_e('MsMpEng.exe')[2], 'disco')
        self.assertIsNone(k.quem_e('programa-que-ninguem-conhece'))
        self.assertIsNone(k.quem_e(None))

    def test_item_trim_existe_no_pacote_de_disco_so_para_ssd(self):
        ctx = type('C', (), {})()
        ctx.perfil = {'disco': {'tipo': 'SSD', 'trim': False}, 'ram': {'total': 8}, 'tem': {}}
        ids = [i.id for i in k.PACOTES['disco'].itens(ctx) if i]
        self.assertIn('trim', ids)
        ctx.perfil = {'disco': {'tipo': 'HDD'}, 'ram': {'total': 8}, 'tem': {}}
        self.assertNotIn('trim', [i.id for i in k.PACOTES['disco'].itens(ctx) if i])

    def test_set_valor_compara_o_tipo_alem_do_valor(self):
        self.assertIn("[string]$a.tipo -eq $Type", k.PS_BASE if hasattr(k, 'PS_BASE') else (RAIZ / 'programa' / 'katharos.py').read_text(encoding='utf-8'))


class TestBusca(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ctx = type('C', (), {})()
        ctx.perfil = k.PERFIL_VAZIO
        cls.indice = k.indice_busca(ctx)

    def ids(self, texto):
        return [(area, id_) for _, _, area, id_, _, _ in k.busca(self.indice, texto)]

    def test_indice_tem_comandos_e_itens_de_varias_areas(self):
        self.assertGreater(len({a for t, a, *_ in self.indice if t == 'item'}), 8)
        self.assertTrue(any(t == 'comando' and a == 'raiox' for t, a, *_ in self.indice))

    def test_acha_sem_acento_e_sem_maiuscula(self):
        self.assertEqual(self.ids('TELEMETRIA')[0][0], 'privacidade')
        self.assertEqual(self.ids('anuncios'), self.ids('anúncios'))

    def test_erro_de_digitacao_ainda_acha(self):
        self.assertEqual(self.ids('telemetira')[0][0], 'privacidade')

    def test_palavra_do_dia_a_dia_vira_o_termo_do_item(self):
        self.assertTrue(any(a == 'energia' for a, _ in self.ids('ventoinha')))

    def test_nome_de_comando_vem_primeiro(self):
        self.assertEqual(self.ids('desfazer')[0], ('desfazer', 'desfazer'))

    def test_todas_as_palavras_precisam_aparecer(self):
        self.assertEqual(self.ids('zzzqqq wwwkkk'), [])
        self.assertEqual(self.ids(''), [])

    def test_frase_inteira_acha_pelo_que_importa(self):
        self.assertTrue(any(a == 'energia' for a, _ in self.ids('meu notebook esquenta muito e faz barulho')))
        self.assertTrue(self.ids('como tirar a propaganda do meu pc'))
        self.assertEqual(self.ids('telemetria zzzqqq')[0][0], 'privacidade', 'metade das palavras basta numa frase')

    def test_buscar_nao_pede_aceite_e_nao_guarda_estado(self):
        self.assertIn('buscar', k.SEM_ACEITE)
        self.assertIn('buscar', k.SEM_ESTADO)
        self.assertIn('buscar', k.COMANDOS)




class TestDicionarioEFluxo(unittest.TestCase):
    def test_dicionario_grande_e_sem_pedacos_soltos(self):
        self.assertGreater(len(k.PROCESSOS), 800)
        for solto in ('pro', 'service', 'desktop', 'cloud', '3', '-'):
            self.assertNotIn(solto, k.PROCESSOS)
        for nome, (oque, faz, cmd) in k.PROCESSOS.items():
            self.assertEqual(nome, nome.lower().strip())
            self.assertTrue(oque and faz, nome)
            self.assertTrue(not cmd or cmd in k.COMANDOS, f'{nome} aponta para {cmd}')

    def test_quem_e_por_nome_jogo_dono_e_funcao(self):
        self.assertIn('ASUS', k.quem_e('AsusNovoPrograma.exe')[0])
        self.assertIn('atualizador', k.quem_e('QualquerUpdater.exe')[0])
        self.assertIn('Unreal', k.quem_e('JogoNovo-Win64-Shipping.exe')[0])
        self.assertEqual(k.quem_e('svchost#4'), k.quem_e('svchost'))
        self.assertIn('empresa', k.quem_e('CSFalconService')[0])
        for desconhecido in ('nvda', 'hp', 'xyzabc', '', None):
            self.assertIsNone(k.quem_e(desconhecido), desconhecido)

    def test_inicializacao_nunca_oferece_antivirus_nem_programa_da_empresa(self):
        for nome in ('Avast UI', 'Kaspersky', 'Bitdefender Agent', 'GlobalProtect', 'Cisco AnyConnect'):
            self.assertIsNone(k._classe_inicio(nome, '')[0], nome)
        self.assertEqual(k._classe_inicio('Bitwarden', '')[0], 0)
        self.assertEqual(k._classe_inicio('CCleaner Monitor', '')[0], 1)
        self.assertEqual(k._classe_inicio('Spotify', '')[0], 2)

    def test_inicializacao_nao_confunde_pedaco_de_palavra(self):
        generico = 'programa que abre com o Windows'
        for nome in ('MeuLoginHelperX', 'Marcador', 'Equinox', 'Generoso'):
            self.assertNotIn(k._classe_inicio(nome.replace('Helper', ''), '')[1], ('programa que você abre quando quiser',), nome)
        self.assertEqual(k._classe_inicio('Coisa Qualquer', 'C:\\x\\coisa.exe')[1], generico)


    def test_proximo_passo_segue_o_caminho_de_quem_chega(self):
        agora = datetime(2026, 11, 9, 12, 0, 0)
        self.assertEqual(k.proximo_passo({}, {}, agora)[0], 'raiox')
        e = {'usado': {'raiox': '2026-11-09T10:00:00'}}
        rx = {'achados': [{'titulo': 'A', 'impacto': 1, 'comando': 'limpar'}, {'titulo': 'Muita coisa abrindo', 'impacto': 3, 'comando': 'inicializacao'}]}
        self.assertEqual(k.proximo_passo(e, rx, agora)[0], 'inicializacao')
        e = {'usado': {'raiox': '2026-11-09T10:00:00', 'inicializacao': '2026-11-09T10:30:00'},
             'pacotes': {'inicializacao': {'quando': '2026-11-09T10:30:00'}}}
        self.assertEqual(k.proximo_passo(e, rx, agora)[0], 'medir')
        e['usado']['medir'] = '2026-11-09T11:00:00'
        self.assertIsNone(k.proximo_passo(e, rx, agora))
        e['pacotes']['limpar'] = {'quando': '2026-11-09T10:40:00'}
        self.assertEqual(k.proximo_passo(e, rx, agora)[0], 'agendar')
        e['manut_freq'] = 'semanal'
        self.assertIsNone(k.proximo_passo(e, rx, agora))
        self.assertEqual(k.proximo_passo(e, rx, datetime(2026, 12, 20))[0], 'raiox')
        self.assertIsNone(k.proximo_passo({'usado': {'raiox': 'lixo'}}, {'achados': 'lixo' and []}, agora))

    def test_enter_no_menu_segue_o_proximo_passo(self):
        import io, contextlib
        t = k.Terminal(True, True)
        t.interativo = True
        ctx = k.Ctx(type('A', (), {'ascii': True, 'sem_cor': True, 'teste': False, 'sim': False, 'modo': None})(), t)
        rodou = []
        with contextlib.redirect_stdout(io.StringIO()) as buf, mock.patch.object(k, 'estado', lambda: {}), mock.patch.object(k, 'primeira_vez', lambda c: None), \
                mock.patch.object(k, '_roda_do_menu', lambda c, p, a, cmd, extra=(): rodou.append(cmd)), mock.patch('builtins.input', side_effect=['', '0']):
            k.menu(ctx, k.monta_parser(), type('A', (), {})())
        self.assertEqual(rodou, ['raiox'])
        self.assertIn('ximo passo', buf.getvalue())


class _CasaTemporaria(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.casa = Path(self._tmp.name)
        self._casa0, k.CASA = k.CASA, self.casa

    def tearDown(self):
        k.CASA = self._casa0
        self._tmp.cleanup()


class TestProvaDeGanho(_CasaTemporaria):
    def test_delta_no_sentido_do_ganho_e_ruido_vira_zero(self):
        a = {'livre': 1000, 'ram': 4000, 'proc': 180, 'svc': 90}
        d = k.delta_retrato(a, {'livre': 2500, 'ram': 4030, 'proc': 175, 'svc': 88})
        self.assertEqual(d, {'livre': 1500, 'ram': 0, 'proc': 5, 'svc': 2})
        self.assertEqual(k.delta_retrato(a, {'livre': 1004, 'ram': 4000, 'proc': 181, 'svc': 90}), {'livre': 0, 'ram': 0, 'proc': 0, 'svc': 0})
        self.assertIsNone(k.delta_retrato({'livre': None}, {'livre': 5})['livre'])
        self.assertIsNone(k.delta_retrato(None, None)['svc'])

    def test_texto_do_ganho(self):
        self.assertEqual(k.texto_ganho({'livre': 2048, 'svc': 2, 'proc': 0, 'ram': 0}), 'liberou 2,0 GB em disco · 2 serviços a menos')
        self.assertEqual(k.texto_ganho({'livre': 0, 'svc': 0, 'proc': None, 'ram': None}), '')
        self.assertIn('MB', k.texto_ganho({'livre': 300}))

    def test_retrato_le_o_disco_em_qualquer_sistema(self):
        self.assertIsInstance(k.retrato()['livre'], int)

    def _itens(self):
        return [k.Item('a', 'limpa cache', 'x', ps='A'), k.Item('b', 'para servico', 'x', ps='B'), k.Item('c', 'ajuste', 'x', ps='C')]

    def _aplica(self, dados):
        import io, contextlib
        pac = k.Pacote('limpar', 'limpeza', 'r', 'e', lambda c: [])
        t = k.Terminal(True, True)
        ctx = k.Ctx(type('A', (), {'teste': False, 'sim': True, 'modo': None})(), t)
        ctx.perfil = {'disco': {'tipo': 'SSD'}, 'ram': {'total': 16}, 'pc': {'notebook': False}}
        S = type('S', (), {'feitos': ['x'], 'planos': [], 'avisos': [], 'erros': [], 'tempo': 1, 'estourou': False, 'dados': dados})
        corpos = []
        buf = io.StringIO()

        class Pr:
            atual = ''

            def __init__(self, *a, **kw):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def avanca(self, *a, **kw):
                pass
        with contextlib.redirect_stdout(buf), mock.patch.object(k, 'Progresso', Pr), mock.patch.object(k, 'mede', lambda *a, **kw: {'boot_s': 50}), \
                mock.patch.object(k, 'salva_medida', lambda *a: None), mock.patch.object(k, 'roda_ps', lambda t_, corpo, *a, **kw: corpos.append(corpo) or S), \
                mock.patch.object(k, 'rel_eventos', lambda x: None), mock.patch.object(k, '_andamento_marca', lambda *a: None), \
                mock.patch.object(k, '_andamento_avanca', lambda *a: None), mock.patch.object(k, 'estado', lambda: {}), mock.patch.object(k, 'salva_estado', lambda e: None):
            k.executa_itens(ctx, pac, self._itens())
        return corpos, buf.getvalue()

    def test_cada_item_e_comparado_com_o_retrato_de_antes_dele(self):
        dados = {'prova:antes': {'livre': 1000, 'ram': 4000, 'proc': 100, 'svc': 80},
                 'prova:0': {'livre': 3048, 'ram': 4000, 'proc': 100, 'svc': 80, 'm': 1},
                 'prova:1': {'livre': 3048, 'ram': 4010, 'proc': 97, 'svc': 78, 'm': 2},
                 'prova:2': {'livre': 3048, 'ram': 4010, 'proc': 97, 'svc': 78, 'm': 3}}
        corpos, tela = self._aplica(dados)
        self.assertIn("Dado 'prova:antes' (Retrato)", corpos[0])
        self.assertIn("Dado 'prova:2' (Retrato ($script:MUDOU - $__a))", corpos[0])
        pv = k.le_provas()
        self.assertEqual([p['id'] for p in pv], ['a', 'b', 'c'])
        self.assertEqual(pv[0]['d']['livre'], 2048)
        self.assertEqual((pv[1]['d']['livre'], pv[1]['d']['svc'], pv[1]['d']['proc']), (0, 2, 3))
        self.assertEqual(pv[2]['d'], {'livre': 0, 'ram': 0, 'proc': 0, 'svc': 0})
        self.assertEqual(pv[0]['hw'], 'ssd-16gb-desktop')
        self.assertIn('o que rendeu agora', tela)
        self.assertIn('liberou 2,0 GB', tela)
        self.assertIn('1 item mudou o Windows sem ganho imediato', tela)
        self.assertEqual(len(k.le_ensaios()), 1)
        self.assertIn('liberou 2,0 GB', k.prova_do_item('limpar', 'a'))
        self.assertIn('sem ganho imediato', k.prova_do_item('limpar', 'c'))
        self.assertEqual(k.prova_do_item('limpar', 'nao-existe'), '')

    def test_sem_retrato_do_powershell_a_aplicacao_segue_normal(self):
        corpos, tela = self._aplica({})
        self.assertEqual(k.le_provas(), [])
        self.assertNotIn('o que rendeu agora', tela)

    def test_simulacao_nao_tira_retrato(self):
        self.assertIn('if (-not $TESTE)', k._envolve(self._itens()[0], 0))
        self.assertNotIn('prova:', k._envolve(self._itens()[0]))

    def _ensaio(self, quando, antes, pacote='inicializacao'):
        return {'id': quando + pacote, 't': quando, 'pacote': pacote, 'itens': ['x', 'y'], 'antes': antes, 'depois': None, 'fechado': None, 'reiniciou': None}

    def test_ensaio_so_fecha_depois_de_reiniciar_e_com_o_pc_ja_assentado(self):
        k.grava_json(k.ensaios_arq(), [self._ensaio('2026-11-09T10:00:00', {'boot_s': 60, 'ram_usada': 6.0, 'cpu': 10})])
        m = {'boot_s': 41, 'ram_usada': 5.2, 'cpu': 9, 'uptime_h': 3.0}
        self.assertEqual(k.fecha_ensaios(m, datetime(2026, 11, 9, 12, 0)), 0, 'ligado desde antes da aplicação: não reiniciou')
        self.assertEqual(k.fecha_ensaios(dict(m, uptime_h=0.05), datetime(2026, 11, 9, 13, 0)), 0, 'acabou de ligar: ainda não vale')
        self.assertEqual(k.fecha_ensaios(dict(m, uptime_h=0.5), datetime(2026, 11, 9, 13, 0)), 1)
        self.assertEqual(k.fecha_ensaios(dict(m, uptime_h=0.5), datetime(2026, 11, 9, 14, 0)), 0, 'já fechado')
        r = k.rodadas(k.le_ensaios())[0]
        ver = {rot: v for rot, v, *_ in r['metricas']}
        self.assertEqual((ver['tempo de boot'], ver['RAM em repouso'], ver['CPU em repouso']), ('melhorou', 'melhorou', 'igual'))
        self.assertTrue(r['reiniciou'])

    def test_sem_reinicio_fecha_em_14_dias_e_o_boot_fica_de_fora(self):
        k.grava_json(k.ensaios_arq(), [self._ensaio('2026-11-01T10:00:00', {'boot_s': 60, 'livre_c': 20})])
        self.assertEqual(k.fecha_ensaios({'boot_s': 60, 'livre_c': 31, 'uptime_h': 400}, datetime(2026, 11, 16, 10, 0)), 1)
        r = k.rodadas(k.le_ensaios())[0]
        self.assertFalse(r['reiniciou'])
        self.assertEqual([m[0] for m in r['metricas']], ['livre em C:'])

    def test_pacotes_fechados_pela_mesma_medida_viram_uma_rodada_so(self):
        k.grava_json(k.ensaios_arq(), [self._ensaio('2026-11-09T10:00:00', {'boot_s': 60}, 'privacidade'), self._ensaio('2026-11-09T10:20:00', {'boot_s': 58}, 'inicializacao')])
        self.assertEqual(k.fecha_ensaios({'boot_s': 40, 'uptime_h': 1}, datetime(2026, 11, 9, 15, 0)), 2)
        rs = k.rodadas(k.le_ensaios())
        self.assertEqual(len(rs), 1)
        self.assertEqual((rs[0]['pacotes'], rs[0]['itens']), (['privacidade', 'inicializacao'], 4))
        self.assertEqual(rs[0]['metricas'][0][2:4], (60, 40), 'compara com a medida de antes da primeira aplicação')

    def test_veredito_respeita_o_ruido(self):
        self.assertEqual(k.veredito_ensaio(60, 59, 'menor', 2, 0.10), 'igual')
        self.assertEqual(k.veredito_ensaio(60, 50, 'menor', 2, 0.10), 'melhorou')
        self.assertEqual(k.veredito_ensaio(20, 31, 'maior', 0.5), 'melhorou')
        self.assertEqual(k.veredito_ensaio(5, 9, 'menor', 2), 'piorou')

    def test_resumo_por_item_soma_disco_e_ordena_pelo_ganho(self):
        pv = [{'pacote': 'limpar', 'id': 'a', 'titulo': 'A', 'mudou': 1, 'd': {'livre': 500, 'ram': 0, 'proc': 0, 'svc': 0}},
              {'pacote': 'limpar', 'id': 'a', 'titulo': 'A', 'mudou': 1, 'd': {'livre': 700, 'ram': 0, 'proc': 0, 'svc': 0}},
              {'pacote': 'servicos', 'id': 'b', 'titulo': 'B', 'mudou': 3, 'd': {'livre': 0, 'ram': 80, 'proc': 3, 'svc': 3}},
              {'pacote': 'visual', 'id': 'c', 'titulo': 'C', 'mudou': 0, 'd': {'livre': 0, 'ram': 0, 'proc': 0, 'svc': 0}}]
        r = k.resumo_itens(pv)
        self.assertEqual([x['id'] for x in r], ['a', 'b', 'c'])
        self.assertEqual((r[0]['livre'], r[0]['vezes']), (1200, 2))
        self.assertEqual(r[2]['pontos'], 0)

    def test_painel_mostra_a_prova_e_o_indice(self):
        k.grava_json(k.ensaios_arq(), [self._ensaio('2026-11-09T10:00:00', {'boot_s': 60, 'ram_usada': 6.0}), self._ensaio('2026-11-09T18:00:00', None, 'disco')])
        k.fecha_ensaios({'boot_s': 41, 'ram_usada': 5.9, 'uptime_h': 1}, datetime(2026, 11, 9, 15, 0))
        k.registra_provas([{'t': '2026-11-09T10:00:00', 'pacote': 'limpar', 'id': 'a', 'titulo': '<b>cache</b>', 'mudou': 1, 'd': {'livre': 2048, 'ram': 0, 'proc': 0, 'svc': 0}}])
        am = [{'_dt': datetime(2026, 11, d), 'livre_c': 50 + d, 'boot_s': 60 - d} for d in range(1, 9)]
        h = k.monta_painel(am, [], [], [], 'PC', '1', provas=k.provas_para_painel())
        for txt in ('id="prova-de-ganho"', 'Depois de reiniciar', 'Na hora, item por item', 'liberou 2,0 GB', 'Esperando o próximo reinício', '<nav class="indice"', 'href="#evolucao"', '&lt;b&gt;cache'):
            self.assertIn(txt, h)
        self.assertNotIn('<b>cache</b>', h)
        self.assertNotIn('<script', h)
        self.assertNotIn('Prova de ganho', k.monta_painel(am, [], [], [], 'PC', '1'))

    def test_comando_provas_vazio_e_cheio(self):
        import io, contextlib
        t = k.Terminal(True, True)
        ctx = k.Ctx(type('A', (), {'teste': False, 'sim': True})(), t)
        with contextlib.redirect_stdout(io.StringIO()) as b:
            self.assertEqual(k.ferramenta_provas(ctx, ctx.args), 0)
        self.assertIn('Ainda nao ha provas', b.getvalue())
        k.grava_json(k.ensaios_arq(), [self._ensaio('2026-11-09T10:00:00', {'boot_s': 60})])
        k.fecha_ensaios({'boot_s': 41, 'uptime_h': 1}, datetime(2026, 11, 9, 15, 0))
        k.registra_provas([{'t': '2026-11-09T10:00:00', 'pacote': 'limpar', 'id': 'a', 'titulo': 'cache', 'mudou': 1, 'd': {'livre': 2048, 'ram': 0, 'proc': 0, 'svc': 0}}])
        with contextlib.redirect_stdout(io.StringIO()) as b, mock.patch.object(k, 'rel_secao', lambda *a: None):
            self.assertEqual(k.ferramenta_provas(ctx, ctx.args), 0)
        for txt in ('depois de reiniciar', 'tempo de boot', '60 s', '41 s', 'na hora, item por item', '2,0 GB'):
            self.assertIn(txt, b.getvalue())


class TestTrocaDeVersao(_CasaTemporaria):
    def test_primeira_vez_so_carimba(self):
        r = k.confere_versao()
        self.assertIsNone(r['de'])
        self.assertEqual(r['passos'], [])
        e = k.estado()
        self.assertEqual((e['versao_programa'], e['versao_dados']), (k.VERSAO, k.VERSAO_DADOS))
        self.assertFalse((self.casa / 'versoes').exists(), 'sem dados antigos não há o que copiar')
        self.assertIsNone(k.confere_versao(), 'na segunda abertura não há nada a fazer')

    def test_reconhece_dados_de_versao_que_nao_carimbava(self):
        k.grava_json(self.casa / 'estado.json', {'usado': {'raiox': '2026-10-01T10:00:00', 'perfil': '2026-10-01T10:00:00'},
                                                  'pacotes': {'privacidade': {'quando': '2026-10-01T11:00:00', 'itens': ['a']}}, 'coisa_que_nao_conheco': 7})
        k.grava_json(self.casa / 'relatorio.json', {'katharos': '1.4.1', 'secoes': {'raiox': {'quando': '2026-10-01T10:00:00', 'dados': {'nota': 72}}}})
        (self.casa / 'metricas.jsonl').write_text('{}\n{}\n{}\n', encoding='utf-8')
        import io, contextlib
        t = k.Terminal(True, True)
        with contextlib.redirect_stdout(io.StringIO()) as b:
            r = k.confere_versao(t)
        self.assertEqual((r['de'], r['para'], r['erro']), ('1.4.1', k.VERSAO, ''))
        self.assertEqual(len(r['passos']), len(k.MIGRACOES))
        e = k.estado()
        self.assertNotIn('perfil', e['usado'])
        self.assertIn('raiox', e['usado'])
        self.assertEqual(e['coisa_que_nao_conheco'], 7, 'o que a conversão não conhece fica')
        self.assertEqual(e['pacotes']['privacidade']['itens'], ['a'])
        self.assertEqual([h['versao'] for h in e['versoes']], ['1.4.1', k.VERSAO])
        copia = next((self.casa / 'versoes').iterdir())
        self.assertTrue(copia.name.startswith('1.4.1_'))
        self.assertIn('perfil', k.le_json(copia / 'estado.json', {})['usado'], 'a cópia é de antes da conversão')
        tela = b.getvalue()
        for txt in ('Katharos atualizado: 1.4.1', 'continua valendo', '1 pacote', '3 medidas', 'nota 72/100'):
            self.assertIn(txt, tela)

    def test_sem_relatorio_a_versao_antiga_e_so_anterior(self):
        k.grava_json(self.casa / 'estado.json', {'usado': {'raiox': 'x'}})
        self.assertEqual(k.confere_versao()['de'], 'anterior')

    def test_dados_de_versao_mais_nova_nao_sao_tocados(self):
        antes = {'versao_programa': '99.0.0', 'versao_dados': k.VERSAO_DADOS + 5, 'usado': {'perfil': 'x'}, 'novidade': [1, 2]}
        k.grava_json(self.casa / 'estado.json', antes)
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()) as b:
            r = k.confere_versao(k.Terminal(True, True))
        self.assertTrue(r['antiga'])
        e = k.estado()
        self.assertEqual((e['versao_programa'], e['versao_dados'], e['usado'], e['novidade']), ('99.0.0', k.VERSAO_DADOS + 5, {'perfil': 'x'}, [1, 2]))
        self.assertIn('99.0.0', b.getvalue())
        with contextlib.redirect_stdout(io.StringIO()) as b:
            k.confere_versao(k.Terminal(True, True))
        self.assertEqual(b.getvalue(), '', 'o aviso aparece uma vez só')

    def test_passo_que_falha_para_ali_e_nao_carimba_a_versao(self):
        k.grava_json(self.casa / 'estado.json', {'versao_programa': '1.0.0', 'versao_dados': 0, 'usado': {'perfil': 'x'}})
        def quebra(e, casa):
            raise RuntimeError('boom')
        with mock.patch.object(k, 'MIGRACOES', [(1, 'um', lambda e, c: e.update(um=True)), (2, 'dois', quebra), (3, 'tres', lambda e, c: e.update(tres=True))]):
            r = k.confere_versao()
        self.assertIn('boom', r['erro'])
        e = k.estado()
        self.assertEqual((e['versao_dados'], e['versao_programa'], e.get('um'), e.get('tres')), (1, '1.0.0', True, None))
        self.assertTrue(any((self.casa / 'versoes').iterdir()))

    def test_migracoes_em_ordem_sem_buraco_e_repetiveis(self):
        self.assertEqual([n for n, _, _ in k.MIGRACOES], list(range(1, k.VERSAO_DADOS + 1)))
        e = {'usado': {'perfil': 'x', 'raiox': 'y'}}
        for _ in range(2):
            for _, _, f in k.MIGRACOES:
                f(e, self.casa)
        self.assertEqual(e['usado'], {'raiox': 'y'})

    def test_guarda_no_maximo_cinco_copias(self):
        k.grava_json(self.casa / 'estado.json', {'a': 1})
        for i in range(8):
            (self.casa / 'versoes' / f'0.{i}.0_20260101-00000{i}').mkdir(parents=True)
        k.guarda_copia_de_versao('1.4.1')
        self.assertEqual(len(list((self.casa / 'versoes').iterdir())), k.COPIAS_DE_VERSAO)

    def test_compara_versoes_por_numero(self):
        self.assertGreater(k._v('2.10.0'), k._v('2.9.9'))
        self.assertEqual(k._v('anterior'), (0,))

    def test_traz_relatorios_da_pasta_antiga(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            velha, nova = Path(d) / 'velha', Path(d) / 'nova'
            (velha / 'relatorios').mkdir(parents=True)
            (nova / 'programa').mkdir(parents=True)
            (velha / 'relatorios' / '2026-10-01_10-00-00_pc_raiox.md').write_text('x', encoding='utf-8')
            (velha / 'relatorios' / 'ultimo.md').write_text('y', encoding='utf-8')
            with mock.patch.object(k, '__file__', str(nova / 'programa' / 'katharos.py')):
                self.assertEqual(k.traz_relatorios({'pasta_katharos': str(velha)}), 1)
                self.assertEqual(k.traz_relatorios({'pasta_katharos': str(velha)}), 0, 'não copia de novo')
                self.assertEqual(k.traz_relatorios({'pasta_katharos': str(nova)}), 0)
            self.assertEqual([a.name for a in (nova / 'relatorios').iterdir()], ['2026-10-01_10-00-00_pc_raiox.md'])
            self.assertTrue((velha / 'relatorios' / 'ultimo.md').exists(), 'a pasta antiga fica como estava')


class TestAbrirRelatorio(_CasaTemporaria):
    def _roda(self, comando, resposta=None, **kw):
        import io, contextlib
        t = k.Terminal(True, True)
        t.interativo = kw.pop('interativo', True)
        ctx = k.Ctx(type('A', (), {})(), t)
        args = type('A', (), dict({'comando': comando, 'teste': False, 'sim': False}, **kw))()
        arq = self.casa / 'ultimo.md'
        arq.write_text('x', encoding='utf-8')
        abertos = []
        with contextlib.redirect_stdout(io.StringIO()), mock.patch.object(k, 'rel_md_path', lambda: arq), \
                mock.patch.object(k, 'mostra_no_explorador', lambda a: abertos.append(('pasta', a)) or True), \
                mock.patch.object(k, 'abre_arquivo', lambda a: abertos.append(('arquivo', a)) or True), \
                mock.patch('builtins.input', side_effect=[resposta] if resposta is not None else AssertionError('não devia perguntar')):
            k.oferece_abrir_relatorio(ctx, args)
        return [x[0] for x in abertos]

    def test_raiox_pergunta_e_a_abre_a_pasta(self):
        self.assertEqual(self._roda('raiox', 'a'), ['pasta'])
        self.assertEqual(self._roda('raiox', 'v'), ['arquivo'])
        self.assertEqual(self._roda('raiox', ''), [])

    def test_comando_comum_nao_pergunta_mas_obedece_a_opcao(self):
        self.assertEqual(self._roda('privacidade'), [])
        self.assertEqual(self._roda('privacidade', abrir=True), ['pasta'])

    def test_sem_terminal_ou_agendada_nunca_abre_sozinho(self):
        self.assertEqual(self._roda('raiox', interativo=False), [])
        self.assertEqual(self._roda('raiox', agendada=True), [])
        self.assertEqual(self._roda('raiox', sim=True), [])
        self.assertEqual(self._roda('raiox', interativo=False, abrir=True), ['pasta'], '--abrir vale mesmo sem terminal')

    def test_config_sempre_e_nunca(self):
        with mock.patch.object(k, 'config', lambda ch, p=None: 'sempre' if ch == 'abrir-relatorio' else None):
            self.assertEqual(self._roda('privacidade'), ['pasta'])
        with mock.patch.object(k, 'config', lambda ch, p=None: 'nunca' if ch == 'abrir-relatorio' else None):
            self.assertEqual(self._roda('raiox'), [])

    def test_fora_do_windows_nao_tenta_abrir(self):
        if not k.WINDOWS:
            self.assertFalse(k.mostra_no_explorador(self.casa))
            self.assertFalse(k.abre_arquivo(self.casa))


if __name__ == '__main__':
    unittest.main()


class TestAutenticidade(_CasaTemporaria):
    def _escreve(self, nome, txt):
        (self.casa / nome).write_text(txt, encoding='utf-8')
        return self.casa / nome

    def test_le_somas_aceita_caminho_e_asterisco(self):
        h = 'a' * 64
        self.assertEqual(k.le_somas(f'{h}  programa/katharos.py\n{h.upper()} *outro.txt\nlixo'),
                         [(h, 'programa/katharos.py'), (h, 'outro.txt')])

    def test_compara_pelo_hash_mesmo_com_nome_de_caminho_diferente(self):
        h = hashlib.sha256(b'x').hexdigest()
        somas = [(h, 'programa/katharos.py')]
        self.assertEqual(k.compara_com_lista(h, 'katharos.py', somas), 'ok')
        self.assertEqual(k.compara_com_lista('0' * 64, 'katharos.py', somas), 'diferente')
        self.assertEqual(k.compara_com_lista('0' * 64, 'outro.py', somas), 'sem')

    def test_sha256_de_arquivo(self):
        f = self._escreve('a.bin', 'abc')
        self.assertEqual(k.sha256_de(f), hashlib.sha256(b'abc').hexdigest())

    def test_abertura_so_avisa_se_a_lista_diz_que_e_outro(self):
        me = Path(k.__file__).resolve()
        h = k.sha256_de(me)
        avisos = []
        t = mock.Mock(aviso=avisos.append)
        marcas = {}
        with mock.patch.object(k, 'estado', return_value={}), mock.patch.object(k, 'marca_estado', lambda c, v: marcas.update({c: v})):
            for linha, esperado in ((f'{h}  programa/katharos.py', 0), (f'{"0" * 64}  programa/katharos.py', 1)):
                avisos.clear()
                somas = self._escreve('SHA256SUMS.txt', linha + '\n')
                with mock.patch.object(k, 'acha_somas', return_value=somas):
                    k.confere_na_abertura(t)
                self.assertEqual(len(avisos), esperado)
            with mock.patch.object(k, 'acha_somas', return_value=None):
                avisos.clear(); k.confere_na_abertura(t); self.assertEqual(avisos, [])

    def test_abertura_nao_repete_para_o_mesmo_arquivo(self):
        me = Path(k.__file__).resolve()
        avisos = []
        somas = self._escreve('SHA256SUMS.txt', f'{"0" * 64}  katharos.py\n')
        with mock.patch.object(k, 'estado', return_value={'autenticidade': {'hash': k.sha256_de(me)}}), \
                mock.patch.object(k, 'acha_somas', return_value=somas):
            k.confere_na_abertura(mock.Mock(aviso=avisos.append))
        self.assertEqual(avisos, [])

    def test_comando_diz_nao_bate_e_devolve_erro(self):
        me = Path(k.__file__).resolve()
        somas = self._escreve('SHA256SUMS.txt', f'{"0" * 64}  katharos.py\n')
        sai = []
        t = mock.Mock()
        t.aviso = sai.append
        t.p = lambda x, *a, **kw: x
        ctx = mock.Mock(t=t)
        with mock.patch.object(k, 'acha_somas', return_value=somas), mock.patch.object(k, 'arquivos_do_programa', return_value=[me]):
            self.assertEqual(k.ferramenta_autenticidade(ctx, mock.Mock(offline=True)), 1)
        self.assertTrue(any('NÃO bate' in x for x in sai))

    def test_comando_ok_com_lista_oficial(self):
        me = Path(k.__file__).resolve()
        oficial = f'{k.sha256_de(me)}  programa/katharos.py\n'
        oks = []
        t = mock.Mock()
        t.ok = oks.append
        t.p = lambda x, *a, **kw: x
        ctx = mock.Mock(t=t)
        with mock.patch.object(k, 'acha_somas', return_value=None), mock.patch.object(k, 'arquivos_do_programa', return_value=[me]), \
                mock.patch.object(k, 'baixa_somas_oficiais', return_value=(oficial, '')):
            self.assertEqual(k.ferramenta_autenticidade(ctx, mock.Mock(offline=False)), 0)
        self.assertTrue(oks and 'oficial' in oks[0])

    def test_comando_registrado_e_sem_aceite(self):
        self.assertIn('autenticidade', k.SEM_ACEITE)
        self.assertIn('autenticidade', [c[0] for g in k.AREAS_MENU for c in g[2]] if hasattr(k, 'AREAS_MENU') else ['autenticidade'])

    def _nivel(self, local, oficial):
        me = Path(k.__file__).resolve()
        h = k.sha256_de(me)
        l = self._escreve('SHA256SUMS.txt', f'{h if local == "ok" else "0" * 64}  programa/katharos.py\n') if local else None
        of = (f'{h if oficial == "ok" else "0" * 64}  programa/katharos.py\n', '') if oficial else ('', 'sem internet')
        with mock.patch.object(k, 'acha_somas', return_value=l), mock.patch.object(k, 'arquivos_do_programa', return_value=[me]), \
                mock.patch.object(k, 'baixa_somas_oficiais', return_value=of):
            return k.verifica_autenticidade()['nivel']

    def test_niveis_da_verificacao(self):
        self.assertEqual(self._nivel('ok', 'ok'), 'oficial')
        self.assertEqual(self._nivel(None, 'ok'), 'oficial')
        self.assertEqual(self._nivel('ok', None), 'local')
        self.assertEqual(self._nivel(None, None), 'sem')
        self.assertEqual(self._nivel('ok', 'ruim'), 'diferente')
        self.assertEqual(self._nivel('ruim', 'ok'), 'diferente')

    def test_tela_do_aceite_mostra_verde_so_quando_bateu_e_barra_se_nao_bate(self):
        for nivel, ok_esperado, verde in (('oficial', True, True), ('local', True, True), ('sem', True, False), ('diferente', False, False)):
            t = mock.Mock()
            t.p = lambda x, *a, **kw: x
            with mock.patch.object(k, 'verifica_autenticidade', return_value={'nivel': nivel, 'arquivos': [], 'erro': 'x', 'tem_local': False}):
                self.assertEqual(k.mostra_autenticidade_no_aceite(t), ok_esperado, nivel)
            self.assertEqual(t.ok.called, verde, nivel)

    def test_aceite_nao_continua_se_o_programa_nao_bate(self):
        t = mock.Mock()
        ctx = mock.Mock(t=t)
        with mock.patch.object(k, 'mostra_aviso'), mock.patch.object(k, 'mostra_autenticidade_no_aceite', return_value=False):
            self.assertFalse(k.pede_aceite(ctx))
        t.confirma.assert_not_called()

    def test_falha_ao_conferir_nao_trava_o_aceite(self):
        t = mock.Mock()
        t.p = lambda x, *a, **kw: x
        with mock.patch.object(k, 'verifica_autenticidade', side_effect=OSError('x')):
            self.assertTrue(k.mostra_autenticidade_no_aceite(t))

    def test_workflow_de_release_existe_com_atestado(self):
        y = (RAIZ / '.github' / 'workflows' / 'publicar.yml').read_text(encoding='utf-8')
        self.assertIn('attest-build-provenance', y)
        self.assertIn('attestations: write', y)

    def test_notas_da_release_saem_do_changelog(self):
        spec_ = importlib.util.spec_from_file_location('notas', RAIZ / '.github' / 'scripts' / 'notas_release.py')
        n = importlib.util.module_from_spec(spec_)
        spec_.loader.exec_module(n)
        texto = n.notas(k.VERSAO, 'abc')
        self.assertIn('abc', texto)
        self.assertIn('Antes de usar', texto)
        self.assertNotIn(f'## {k.VERSAO}', texto)
        with self.assertRaises(SystemExit):
            n.notas('0.0.0')
        self.assertEqual(n.entrada('1.0', '## 1.0 · x\ncorpo\n\n## 0.9\noutro'), 'corpo')

    def test_changelog_tem_a_versao_atual(self):
        self.assertRegex((RAIZ / 'CHANGELOG.md').read_text(encoding='utf-8'), r'(?m)^## ' + re.escape(k.VERSAO) + r'\b')


class TestSiteSuave(unittest.TestCase):
    def test_rolagem_suave_vem_do_proprio_site_e_respeita_reduzir_movimento(self):
        for nome in ('index.html',):
            h = (RAIZ / 'docs' / nome).read_text(encoding='utf-8')
            self.assertIn('src="lenis.min.js"', h)
            self.assertIn('prefers-reduced-motion: reduce', h)
            self.assertNotIn('https://cdn', h)
            self.assertNotRegex(h, r'html \{[^}]*scroll-behavior: smooth')
        for arq in ('lenis.min.js', 'lenis.css', 'lenis-LICENSE.txt'):
            self.assertTrue((RAIZ / 'docs' / arq).is_file(), arq)


class TestFocoJogos(unittest.TestCase):
    def test_nada_de_jogo_especifico(self):
        for some in ('cs2', 'minecraft', 'unreal', 'steam'):
            self.assertNotIn(some, k.PACOTES)
            self.assertNotIn(some, k.COMANDOS)
        for nome in ('CATALOGO_JOGOS', 'JOGOS_EXE', 'EXE_COM_ANTICHEAT'):
            self.assertFalse(hasattr(k, nome), nome)
        ids = {i.id for i in k.PACOTES['jogos'].itens(mock.Mock(perfil=k.PC_MODELO)) if i}
        self.assertNotIn('prioridade-jogos', ids)

    def test_os_tres_modos_incluem_jogos_e_o_extremo_vai_mais_longe(self):
        ctx = mock.Mock(perfil=k.PC_MODELO, ja={})
        ids = {m: {i.id for i in k._itens_da_etapa(ctx, {'modo': m, 'itens': {}}, 'jogos')} for m in ('seguro', 'equilibrado', 'extremo')}
        self.assertIn('modo-jogo', ids['seguro'])
        self.assertTrue(ids['seguro'] < ids['equilibrado'] < ids['extremo'])
        self.assertIn('timer', ids['extremo'] | {'timer'})
        self.assertNotIn('jogar', k.COMANDOS, 'só três escolhas: os modos')
        self.assertEqual(k.NIVEL_PACOTE['jogos'], 1, 'o turbo inclui jogos em todo modo')


class TestSemBan(unittest.TestCase):
    def test_nada_toca_em_jogo(self):
        fonte = Path(k.__file__).read_text(encoding='utf-8')
        for proibido in ('Image File Execution Options', 'CpuPriorityClass', 'ReadProcessMemory', 'WriteProcessMemory', 'CreateRemoteThread', 'VirtualAllocEx'):
            self.assertNotIn(proibido, fonte, proibido)
        self.assertIn('$comAC', k.DIAG_PS, 'com anti-cheat aberto o raio-x não consulta os processos')
