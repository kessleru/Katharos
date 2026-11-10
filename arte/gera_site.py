"""Gera docs/index.html a partir de arte/site.html e dos dados do próprio katharos.py
(grupos do menu e perfis), para o site nunca divergir do programa."""
import html
import importlib.util
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('k', RAIZ / 'programa' / 'katharos.py')
k = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k)
e = html.escape

GH = ('<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .3a12 12 0 0 0-3.8 23.4c.6.1.8-.3.8-.6v-2c-3.3.7-4-1.6-4-1.6-.6-1.4-1.4-1.8-1.4-1.8-1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 1.8 2.8 1.3 3.5 1 0-.8.4-1.3.7-1.6-2.7-.3-5.5-1.3-5.5-6 0-1.2.5-2.3 1.3-3.1-.2-.4-.6-1.6 0-3.2 0 0 1-.3 3.4 1.2a11.5 11.5 0 0 1 6 0C17.3 4.6 18.3 5 18.3 5c.6 1.6.2 2.8.1 3.2.8.8 1.3 1.9 1.3 3.1 0 4.6-2.8 5.6-5.5 5.9.5.4.9 1.1.9 2.2v3.3c0 .3.2.7.8.6A12 12 0 0 0 12 .3"/></svg>')

# ── comandos: só a contagem; a lista completa fica no README e no `katharos ajuda` ──
N_CMD = sum(len(itens) for _, _, itens in k.GRUPOS)

# ── mockup do menu: as mesmas linhas e números do programa ──
def linha_cmd(n, cmd, desc, extra=''):
    return f'    <span class="t-a">{n:>2}</span>  <span class="t-o">{cmd:<9}</span> <span class="t-s">{e(k.corta(desc, 56))}</span>{extra}'

mock = ['<span class="t-o">katharos</span>', '']
for n, (cmd, desc) in enumerate(k.MENU, 1):
    mock.append(linha_cmd(n, cmd, desc))
mock += ['', '<span class="t-m">     0  sair</span>', '', '<span class="t-m">    número ou nome · 0 sai</span>']
mock += ['', '<span class="t-s">o que fazer</span> <span class="t-a">›</span> <span class="digitado">1</span><span class="cursor"></span>']
MOCK = '\n'.join(mock)

# ── modos: o que cada um acrescenta, tirado dos próprios itens ──
class _CM:
    perfil = k.PC_MODELO
NV = {1: ('nv1', 'seguro'), 2: ('nv2', 'equilibrado'), 3: ('nv3', 'extremo'), 0: ('nv0', 'opcional')}
POR_NIVEL = {1: [], 2: [], 3: [], 0: []}   # nível -> [(pacote, [itens])]
for nome_p, pac in k.PACOTES.items():
    try:
        its = [i for i in (pac.itens(_CM) or []) if i]
    except AttributeError:   # pacotes que listam o que este PC tem (programas, apps): a lista depende do PC
        continue
    for nv in POR_NIVEL:
        do_nivel = [i for i in its if (i.nivel if i.nivel in NV else 2) == nv]
        if do_nivel:
            POR_NIVEL[nv].append((pac, do_nivel))
PARA_QUEM = {'seguro': 'PC de trabalho', 'equilibrado': 'o dia a dia (recomendado)', 'extremo': 'tirar tudo o que dá'}
SITE_MODO = {'seguro': 'Só o que não tem contrapartida: telemetria, anúncios e lixo.', 'equilibrado': 'O seguro mais o que quase ninguém usa.', 'extremo': 'Tudo o que ajuda neste PC. Você perde recursos; cada item diz quais.'}
cards = []
acumulado = 0
for nv, (nome_m, cor, texto) in enumerate(k.EXPLICA_MODOS, 1):
    n_novos = sum(len(its) for _, its in POR_NIVEL[nv])
    acumulado += n_novos
    blocos_it = []
    for pac, its in POR_NIVEL[nv]:
        lis = []
        for i in its:
            nota = ' · '.join(x for x in (f'ganha: {i.ganho}' if i.ganho else '', f'perde: {i.custo}' if i.custo else '') if x)
            lis.append(f'<li><span class="nv {NV[nv][0]}">{NV[nv][1]}</span><div><b>{e(i.titulo)}</b><small>{e(nota)}</small></div></li>')
        blocos_it.append(f'<h4>{e(pac.titulo)} <i>{len(its)}</i></h4><ul>{"".join(lis)}</ul>')
    soma = 'itens'
    cards.append(f'''      <article class="perfil">
        <header><div><h3><span class="nv {NV[nv][0]}">{nv}</span> {e(nome_m)}</h3><p class="para">para {e(PARA_QUEM[nome_m])}</p><code>turbo --modo {e(nome_m)}</code></div></header>
        <p class="perde">{e(SITE_MODO[nome_m])}</p>
        <a class="ver-lista" href="#tudo" data-modo="{nv}">Marca {acumulado} {soma}<span>ver a lista</span></a>
      </article>''')
N_OPCIONAIS = sum(len(its) for _, its in POR_NIVEL[0])

# ── a lista inteira: tudo o que o Katharos faz, por área (a ordem do menu), com o nível de cada item ──
NV_NUM = {1: 1, 2: 2, 3: 3, 0: 4}   # 4 = opcional: nenhum modo marca
DEPENDE = {'programas': 'A lista sai do que este PC tem: programas de fábrica, antivírus de teste, atualizadores.',
           'apps': 'A lista sai dos apps da Loja que vieram neste PC.',
           'inicializacao': 'A lista sai do que abre com o Windows neste PC. Antivírus nunca sai.'}
areas, total_itens = [], 0
for titulo_g, expl_g, cmds in k.GRUPOS:
    for cmd, desc, f in cmds:
        if f != 'pacote' or cmd not in k.PACOTES:
            continue
        pac = k.PACOTES[cmd]
        try:
            its = [i for i in (pac.itens(_CM) or []) if i]
        except Exception:
            its = []
        if not its and cmd not in DEPENDE:
            continue
        total_itens += len(its)
        lis = ''.join(
            f'<li data-nv="{NV_NUM.get(i.nivel, 2)}"><span class="nv {NV.get(i.nivel, NV[2])[0]}">{NV.get(i.nivel, NV[2])[1]}</span>'
            f'<div><b>{e(i.titulo)}</b><small>{e(" · ".join(x for x in (("ganha: " + i.ganho) if i.ganho else "", ("perde: " + i.custo) if i.custo else "") if x))}</small></div></li>'
            for i in its)
        corpo = (f'<ul>{lis}</ul>' if lis else '') + (f'<p class="depende">{e(DEPENDE[cmd])}</p>' if cmd in DEPENDE else '')
        areas.append(f'<details class="area" data-total="{len(its)}"><summary><b>{e(pac.titulo)}</b><span>{e(desc)}</span>'
                     f'<i class="conta">{len(its) or "varia"}</i></summary>{corpo}</details>')
TUDO = '\n'.join(areas)

# CSS comum às duas páginas, tirado de site.html: variáveis e grade, cabeçalho de seção
_css = (RAIZ / 'arte' / 'site.html').read_text(encoding='utf-8')
BASE_CSS = (_css.split('<style>\n', 1)[1].split('  /* ── hero ── */', 1)[0]
            + _css.split('  /* ── cabeçalho de seção', 1)[1].split('  /* ── a janela do programa ── */', 1)[0].split('\n', 1)[1])

# ── novidades: as últimas versões, lidas do CHANGELOG.md ──
def md_limpo(t):
    t = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', t)
    return t.replace('`', '')

# resumo escrito à mão para versões cujo changelog é longo demais para cortar sozinho
RESUMO = {
    '3.1.2': [('Menu do ícone', 'só o que se resolve num clique: pausar, ritmo, avisos e iniciar com o Windows')],
    '3.1.1': [('Temperatura da CPU', 'lida do MSI Afterburner, HWiNFO, Core Temp ou AIDA64 abertos, sem driver'),
              ('Painel do ícone', 'ganhou o X para fechar')],
    '3.1.0': [('Katharos.exe', 'clique duas vezes para abrir; o ícone fica perto do relógio'),
              ('Segundo plano ao vivo', 'CPU, placa de vídeo, RAM e temperatura a cada segundo, no ícone'),
              ('Sessões de jogo', 'ele diz o que segurou o FPS e a central de inteligência aprende com isso')],
    '3.0.4': [('Nada elevado na pasta do usuário', 'backup do desfazer, scripts e a tarefa do turbo vão para onde só administradores gravam'),
              ('Só de jogo, só com jogos', 'placa de vídeo, entrada e rede ficam fora do extremo em PC sem jogos')],
}

def novidades(n_versoes=2, por_versao=3):
    texto = (RAIZ / 'CHANGELOG.md').read_text(encoding='utf-8')
    achados = re.findall(r'^## (\d+\.\d+\.\d+) · (.+?)\n(.*?)(?=^## |\Z)', texto, re.S | re.M)
    linhas = []
    for ver, data, corpo in achados[:n_versoes]:
        itens = []
        if ver in RESUMO:
            itens = [f'<li><b>{e(a)}:</b> {e(b)}</li>' for a, b in RESUMO[ver]]
            linhas.append(f'<div class="nov"><div class="nov-v"><b>v{ver}</b><small>{e(data.replace(" de novembro de ", " nov "))}</small></div><ul>{"".join(itens)}</ul></div>')
            continue
        for b in re.findall(r'^- (.+)$', corpo, re.M)[:por_versao]:
            b = md_limpo(b)
            m = re.match(r'\*\*(.+?)\*\*(:?)\s*(.*)', b)
            lead, dois, resto = (m.group(1), m.group(2), m.group(3)) if m else ('', '', b)
            frase = re.split(r'(?<=[.!?])\s', resto, maxsplit=1)[0] if resto else ''
            frase = re.sub(r'\s*\([^)]*\)', '', frase).strip().lstrip(':; ')
            frase = re.split(r'[:;]\s', frase, maxsplit=1)[0].rstrip('.')
            if len(frase) > 72:
                corte = frase[:72].rfind(', ')
                frase = frase[:corte] if corte > 30 else frase[:72].rsplit(' ', 1)[0].rstrip(',') + '…'
            sep = '' if frase[:1] in ',.;' else ' '
            itens.append('<li>' + (f'<b>{e(lead.rstrip("."))}{":" if frase else ""}</b> ' if lead else '') + e(frase) + '</li>')
        linhas.append(f'<div class="nov"><div class="nov-v"><b>v{ver}</b><small>{e(data.replace(" de novembro de ", " nov "))}</small></div><ul>{"".join(itens)}</ul></div>')
    return '\n'.join(linhas)

total = len(re.findall(r'\bItem\(', ''.join(p.read_text(encoding='utf-8') for p in (RAIZ / 'partes').glob('5*.py'))))
mais_de = total // 10 * 10

# Troque para True depois de publicar a tag vX.Y.Z no GitHub (git push origin vX.Y.Z): o botão passa a baixar essa versão exata.
TAG_PUBLICADA = True
ZIP = 'https://github.com/kessleru/Katharos/releases/latest/download/Katharos.zip' if TAG_PUBLICADA else 'https://github.com/kessleru/Katharos/archive/refs/heads/main.zip'

VALORES = {'GH': GH, 'N_ITENS': f'mais de {mais_de}', 'N_CMD': str(N_CMD), 'N_GRUPOS': str(len(k.GRUPOS)),
           'MOCK_MENU': MOCK, 'TUDO': TUDO, 'N_TUDO': str(total_itens), 'MODOS': '\n'.join(cards), 'N_OPCIONAIS': str(N_OPCIONAIS),
           'NOVIDADES': novidades(), 'ZIP': ZIP, 'VERSAO': k.VERSAO, 'DATA_VERSAO': k.DATA_VERSAO}


def monta(modelo, destino):
    out = (RAIZ / 'arte' / modelo).read_text(encoding='utf-8')
    out = out.replace('{{BASE_CSS}}', BASE_CSS)   # primeiro: o CSS não tem marcadores, mas o resto do modelo tem
    for chave, valor in VALORES.items():
        out = out.replace('{{' + chave + '}}', valor)
    assert '{{' not in out, (modelo, re.findall(r'\{\{\w+\}\}', out))
    (RAIZ / 'docs' / destino).write_text(out, encoding='utf-8')


monta('site.html', 'index.html')
print('ok', N_CMD, 'comandos,', len(cards), 'modos,', total, 'itens')
