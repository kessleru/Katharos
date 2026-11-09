"""Testes do Katharos. Rodam em qualquer sistema (Linux no CI): `python -m unittest discover -s tests -v`.
Verificam o que não pode quebrar: cada item é completo, nenhum script mexe nas proteções do Windows, os perfis só
citam itens que existem, o menu só cita comandos que existem e o ZIP bate com os hashes publicados."""
import hashlib
import importlib.util
import re
import sys
import unittest
from pathlib import Path

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


class TestPerfis(unittest.TestCase):
    def test_perfis_citam_so_itens_existentes(self):
        por_pacote = {}
        for nome, i in ITENS:
            por_pacote.setdefault(nome, set()).add(i.id)
        for chave, (nome, desc, sel) in k.PERFIS.items():
            for pac, ids in sel.items():
                self.assertIn(pac, k.PACOTES, f'perfil {chave}: pacote {pac} não existe')
                if isinstance(ids, str):
                    self.assertIn(ids[1:], k.MODOS, f'perfil {chave}: modo {ids}')
                else:
                    falta = set(ids) - por_pacote.get(pac, set())
                    self.assertFalse(falta, f'perfil {chave}/{pac}: itens inexistentes {falta}')

    def test_perfis_tem_nota_e_foco(self):
        for chave in k.PERFIS:
            self.assertIn(chave, k.PERFIL_NOTAS, chave)
            self.assertIn(chave, k.FOCO_PERFIL, chave)
            self.assertTrue(k.itens_do_perfil(chave), f'perfil {chave} ficou vazio')

    def test_perfil_nao_marca_item_de_anticheat_sem_aviso(self):
        for chave in k.PERFIS:
            for pac, its in k.itens_do_perfil(chave):
                for i in its:
                    if 'PerfOptions' in (i.ps or ''):
                        self.assertIn((pac.nome, i.id), k.ALERTA_ITEM, f'{chave}/{i.id}: prioridade por exe sem alerta de anti-cheat')


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
        for chave in k.PERFIS:
            for _, lista in k.itens_do_perfil(chave):
                self.assertNotIn('prioridade-jogos-ac', [i.id for i in lista], chave)

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
        self.assertEqual(set(r), {'cpu', 'cpu_multi', 'ram', 'disco_escrita', 'disco_4k'})
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
                k.roda_ps = lambda t, corpo, *a, **kw: (corpos.__setitem__(f, corpo), type('S', (), {'ok': True, 'erros': []})())[1]
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

    def test_hd_ou_pouca_ram_sugere_pc_fraco(self):
        self.assertEqual(k.sugere_perfil(self.pc(disco={'tipo': 'HDD'}))[0], 'fraco')
        self.assertEqual(k.sugere_perfil(self.pc(ram={'total': 4}))[0], 'fraco')

    def test_pc_de_empresa_sugere_trabalho(self):
        self.assertEqual(k.sugere_perfil(self.pc(pc={'dominio': True}))[0], 'trabalho')

    def test_jogos_com_placa_dedicada(self):
        p = self.pc(gpus=['NVIDIA GeForce RTX 4060'], jogos=['Counter-Strike 2'])
        self.assertEqual(k.sugere_perfil(p)[0], 'jogo')
        self.assertIsNone(k.sugere_perfil(self.pc(jogos=['Counter-Strike 2'])), 'sem placa dedicada não sugere jogo')

    def test_notebook_e_dev(self):
        self.assertEqual(k.sugere_perfil(self.pc(pc={'notebook': True, 'bateria': True}))[0], 'bateria')
        self.assertEqual(k.sugere_perfil(self.pc(tem={'wsl': True}))[0], 'dev')

    def test_nada_se_destaca(self):
        self.assertIsNone(k.sugere_perfil(self.pc()))

    def test_sugestao_sempre_e_perfil_que_existe(self):
        for p in (self.pc(disco={'tipo': 'HDD'}), self.pc(pc={'dominio': True}), self.pc(tem={'docker': True}),
                  self.pc(pc={'notebook': True, 'bateria': True})):
            self.assertIn(k.sugere_perfil(p)[0], k.PERFIS)

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
        n = sum(len(itens) for _, _, itens in k.GRUPOS)
        self.assertIn(f'até o {n}', site, 'rode arte/gera_site.py')
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
