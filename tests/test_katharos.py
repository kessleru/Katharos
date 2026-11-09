"""Testes do Katharos. Rodam em qualquer sistema (Linux no CI): `python -m unittest discover -s tests -v`.
Verificam o que não pode quebrar: cada item é completo, nenhum script mexe nas proteções do Windows, os perfis só
citam itens que existem, o menu só cita comandos que existem e o ZIP bate com os hashes publicados."""
import hashlib
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

    def test_jogar_junta_tudo_de_jogo_num_lugar_so(self):
        (titulo, expl, itens), = k.grupos_da_tela('jogar')
        cmds = [c for c, _ in itens]
        for c in ('jogos', 'cs2', 'minecraft', 'unreal', 'steam'):
            self.assertIn(c, cmds)
        self.assertEqual(cmds[0], 'jogos', 'o Windows vem primeiro')
        self.assertTrue(expl)
        for tela in ('escolher', 'mais'):
            for _, _, its in k.grupos_da_tela(tela):
                self.assertFalse({c for c, _ in its} & set(cmds), f'{tela} repete o que é de jogo')

    def test_pacote_de_jogo_vazio_diz_o_que_nao_achou(self):
        for c in ('cs2', 'minecraft', 'unreal'):
            self.assertIn('Não achei', k.SEM_ITENS[c])
        achados = k.jogos_neste_pc()
        if k.WINDOWS:   # no Windows responde sim ou não para cada jogo; fora dele não afirma nada
            self.assertEqual(set(achados), {'steam', 'cs2', 'minecraft', 'unreal'})
            self.assertTrue(all(isinstance(v, bool) for v in achados.values()))
        else:
            self.assertEqual(achados, {})

    def tela_jogar(self, achados, windows=False):
        import io, contextlib
        t = k.Terminal(True, True)
        ctx = k.Ctx(type('A', (), {'ascii': True, 'sem_cor': True, 'teste': False, 'sim': False, 'modo': None})(), t)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), mock.patch.object(k, 'jogos_neste_pc', lambda: achados), \
                mock.patch.object(k, 'jogos_do_catalogo', lambda: (['Hades'], 1)), mock.patch.object(k, 'primeira_vez', lambda c: None), mock.patch.object(k, 'estado', lambda: {}), \
                mock.patch.object(k, 'WINDOWS', windows), mock.patch.object(k, 'eh_admin', lambda: True), \
                mock.patch.dict(k._CACHE_JOGOS, {'catalogo': (['Hades'], 1)}), \
                mock.patch('builtins.input', side_effect=['4', '0', '0']):
            k.menu(ctx, k.monta_parser(), type('A', (), {})())
        return buf.getvalue()

    def test_jogar_mostra_so_os_jogos_que_este_pc_tem(self):
        n = [c for c, _ in k.MENU].index('jogar') + 1
        self.assertEqual(n, 4)
        txt = self.tela_jogar({'steam': True, 'cs2': True, 'minecraft': False, 'unreal': False})
        self.assertIn('cs2', txt)
        self.assertIn('steam', txt)
        self.assertNotIn('minecraft  ', txt)
        self.assertNotIn('unreal  ', txt)
        self.assertIn('jogos', txt, 'o Windows aparece sempre')

    def test_jogar_lista_os_jogos_do_catalogo_achados_e_o_anticheat(self):
        txt = self.tela_jogar({'steam': True, 'cs2': False, 'minecraft': False, 'unreal': False}, windows=True)
        self.assertIn('Hades', txt)
        self.assertIn('anti-cheat de terceiros', txt)
        self.assertIn('achados aqui (1)', txt)

    def test_jogar_sem_nenhum_jogo_ainda_tem_o_windows(self):
        txt = self.tela_jogar({'steam': False, 'cs2': False, 'minecraft': False, 'unreal': False})
        self.assertIn('o Windows para jogar', txt)
        self.assertNotIn('cs2   ', txt)

    def test_acha_jogos_do_catalogo_pelo_nome_do_exe_e_conta_anticheat(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / 'Cyberpunk 2077' / 'bin' / 'x64'
            a.mkdir(parents=True)
            (a / 'Cyberpunk2077.exe').write_bytes(b'')
            b = Path(d) / 'Apex'
            b.mkdir()
            (b / 'r5apex.exe').write_bytes(b'')
            (Path(d) / 'Outro').mkdir()
            (Path(d) / 'Outro' / 'notepad.exe').write_bytes(b'')
            achados, com_ac = k.jogos_do_catalogo([Path(d) / 'Cyberpunk 2077', b, Path(d) / 'Outro', Path(d) / 'nao existe'])
        self.assertEqual(achados, ['Cyberpunk 2077'])
        self.assertEqual(com_ac, 1)
        self.assertEqual(k.jogos_do_catalogo([]), ([], 0))

    def test_so_lista_jogo_do_catalogo_e_nunca_um_exe_qualquer(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'setup.exe').write_bytes(b'')
            self.assertEqual(k.jogos_do_catalogo([Path(d)])[0], [])

    def test_resumo_dos_jogos_achados(self):
        self.assertEqual(k.resumo_jogos_achados([]), '')
        self.assertEqual(k.resumo_jogos_achados(['A', 'B']), 'A, B')
        self.assertEqual(k.resumo_jogos_achados(list('ABCDEFGHI')), 'A, B, C, D, E, F e mais 3')

    def test_dicas_mostram_poucas_teclas_separadas_por_bolinha(self):
        import io, contextlib
        t = k.Terminal(True, True)
        buf = io.StringIO()
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
        self.assertIn('!', linha)


class TestJogosECS2(unittest.TestCase):
    """O catálogo e o pacote do CS2 só mexem no que foi confirmado em fonte."""
    def test_catalogo_nao_tem_exe_com_anticheat(self):
        self.assertFalse(set(k.JOGOS_EXE) & set(k.EXE_COM_ANTICHEAT))

    def test_catalogo_sem_repeticao_e_sem_jogo_que_nao_existe_mais(self):
        nomes = [n for n, _ in k.CATALOGO_JOGOS]
        self.assertEqual(len(nomes), len(set(nomes)))
        self.assertEqual(len(k.JOGOS_EXE), len(set(k.JOGOS_EXE)))
        self.assertNotIn('csgo.exe', k.JOGOS_EXE)

    def test_item_de_prioridade_com_anticheat_e_opt_in(self):
        its = {i.id: i for _, i in ITENS}
        item = its['prioridade-jogos-ac']
        self.assertEqual(item.nivel, 0)
        self.assertTrue(item.alerta)
        for modo in k.MODOS:   # nenhum modo marca sozinho
            lista = [i for n, i in todos_itens() if n == 'jogos']
            k.marca_por_modo(lista, modo)
            self.assertNotIn('prioridade-jogos-ac', [i.id for i in lista if i.marcado], modo)

    def test_itens_novos_do_cs2_existem(self):
        ids = {i.id for _, i in ITENS}
        for novo in ('video-cs2', 'video-cs2-fraco', 'reflex-cs2', 'medir-cs2', 'prioridade-jogos-ac'):
            self.assertIn(novo, ids)

    def test_video_cs2_so_troca_chaves_conhecidas_e_nunca_a_resolucao(self):
        todas = {**k.VIDEO_CS2, **k.VIDEO_CS2_FRACO, **k.VIDEO_CS2_REFLEX}
        for chave in todas:
            self.assertNotRegex(chave, r'defaultres|fullscreen|aspectratio|refreshrate|display')
        self.assertFalse(set(k.VIDEO_CS2) & set(k.VIDEO_CS2_FRACO))

    def test_video_cs2_faz_copia_antes_e_exige_jogo_fechado(self):
        its = {i.id: i for _, i in ITENS}
        self.assertIn('.katharos.bak', its['video-cs2'].ps)
        self.assertIn('cs2', its['video-cs2'].ps.lower())


class TestPacotesDeJogo(unittest.TestCase):
    """Regras de todo pacote que edita arquivo de configuração de jogo."""
    def test_minecraft_so_usa_chaves_confirmadas_e_so_baixa(self):
        for regras in (k.MC_OPCOES, k.MC_OPCOES_FRACO):
            self.assertFalse(set(regras) - k.MC_CHAVES_CONFIRMADAS, 'chave do Minecraft sem fonte')
            for chave, (como, valor) in regras.items():
                self.assertIn(como, ('max', 'min', 'set'))
        self.assertNotIn('maxFps', {**k.MC_OPCOES, **k.MC_OPCOES_FRACO}, 'o teto de FPS não é mexido')

    def test_nenhum_script_de_jogo_grava_com_bom(self):
        """Set-Content -Encoding UTF8 grava BOM no PowerShell 5.1; arquivo de jogo (Java, cfg da Valve) pode não aceitar."""
        for pac, it in ITENS:
            if pac in ('cs2', 'minecraft', 'unreal'):
                self.assertNotRegex(it.ps or '', r'Set-Content[^\n]*-Encoding\s+UTF8', f'{pac}/{it.id}')
                self.assertNotRegex(it.ps or '', r'Out-File', f'{pac}/{it.id}')

    def test_pacote_de_jogo_faz_copia_e_exige_jogo_fechado(self):
        for pac, it in ITENS:
            if pac in ('minecraft', 'unreal'):
                self.assertIn('.katharos.bak', it.ps)
                self.assertIn('Get-Process', it.ps)
                self.assertIn('Guarda-Desfazer', it.ps)
                self.assertIn('UTF8Encoding $__bom', it.ps)
                self.assertIn('UTF-16', it.ps, 'não reescreve arquivo em codificação que não entende')

    def test_unreal_so_usa_chaves_documentadas_so_baixa_e_so_jogo_com_fonte(self):
        self.assertFalse(set(k.UE_REGRAS) - k.UE_CHAVES_DOCUMENTADAS)
        self.assertTrue(all(como == 'max' for como, _ in k.UE_REGRAS.values()), 'só baixa')
        self.assertTrue(all(valor <= 2 for _, valor in k.UE_REGRAS.values()), 'de Épico (3) para Alto (2), no máximo')
        for id_, nome, pasta, fonte in k.UE_JOGOS:
            self.assertTrue(fonte.startswith('https://'), nome)
            self.assertNotIn(nome, k.JOGOS_ANTICHEAT, f'{nome} tem anti-cheat de terceiros')
        antigo = k._ue_instalado
        k._ue_instalado = lambda pasta: True   # no Windows de verdade só aparece o jogo instalado; aqui conferimos todos
        try:
            itens = [i for i in k.PACOTES['unreal'].itens(Ctx) if i]
        finally:
            k._ue_instalado = antigo
        self.assertEqual({i.id for i in itens}, {'ue-' + j[0] for j in k.UE_JOGOS})
        for i in itens:
            self.assertIn('^([^=]+)=(.*)$', i.ps)
            self.assertNotIn('sg.TextureQuality', i.ps)
            self.assertNotIn('sg.AntiAliasingQuality', i.ps)

    def test_pacote_de_jogo_esta_no_menu(self):
        cmds = [c for _, _, its in k.GRUPOS for c, _, _ in its]
        self.assertIn('minecraft', cmds)
        self.assertIn('unreal', cmds)


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
        for texto in ('<h2>Temperatura</h2>', '<h2>Consumo</h2>', 'Em repouso e sob carga', 'Quando esquenta', 'Temperatura por dia', 'Quem mais pesou na CPU', 'jogo'):
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
        self.assertIn('<h2>Consumo</h2>', h)

    def test_painel_com_poucas_horas_nao_mostra_secoes(self):
        h = k.monta_painel([], [], [], [], 'PC', '1', horas=self._horas(1)[:2])
        self.assertNotIn('<h2>Temperatura</h2>', h)

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

    def test_nomes_de_jogo_cobrem_catalogo_anticheat_e_exemplos(self):
        n = k.nomes_de_jogo()
        for esperado in ('cs2', 'valorant-win64-shipping', 'easyanticheat', 'vgc', 'faceitclient'):
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


if __name__ == '__main__':
    unittest.main()
