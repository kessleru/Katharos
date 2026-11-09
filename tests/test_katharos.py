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
            if pac in ('cs2', 'minecraft'):
                self.assertNotRegex(it.ps or '', r'Set-Content[^\n]*-Encoding\s+UTF8', f'{pac}/{it.id}')
                self.assertNotRegex(it.ps or '', r'Out-File', f'{pac}/{it.id}')

    def test_pacote_de_jogo_faz_copia_e_exige_jogo_fechado(self):
        for pac, it in ITENS:
            if pac == 'minecraft':
                self.assertIn('.katharos.bak', it.ps)
                self.assertIn('Get-Process', it.ps)
                self.assertIn('Guarda-Desfazer', it.ps)
                self.assertIn('UTF8Encoding $false', it.ps)

    def test_pacote_de_jogo_esta_no_menu(self):
        cmds = [c for _, _, its in k.GRUPOS for c, _, _ in its]
        self.assertIn('minecraft', cmds)


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

    def test_benchmark_apaga_o_arquivo_temporario(self):
        import tempfile
        d = Path(tempfile.mkdtemp())
        class T:
            def __getattr__(self, n):
                return lambda *a, **kw: ''
        k.Progresso = type('P', (), {'__init__': lambda s, *a, **kw: None, '__enter__': lambda s: s, '__exit__': lambda s, *a: False})
        r = k.roda_bench(T(), rapido=True, leve=True, pasta_tmp=d)
        self.assertEqual(set(r), {'cpu', 'ram', 'disco_escrita', 'disco_4k'})
        self.assertTrue(all(v['mediana'] > 0 for v in r.values()))
        self.assertEqual(list(d.glob('*')), [], 'o arquivo de teste tem de ser apagado')


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

if __name__ == '__main__':
    unittest.main()
