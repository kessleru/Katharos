"""Lê os relatórios e o feedback que chegaram (repositório privado kessleru/katharos-relatorios) e diz o que melhorar primeiro.

    python3 scripts/relatorios.py --repo kessleru/katharos-relatorios     baixa o que é novo (pelo gh, com a sua conta) e analisa
    python3 scripts/relatorios.py --pasta caminho/dos/json                   analisa uma pasta de envios já baixados

Escreve em relatorios/ (fora do git, porque são dados de outras pessoas):
    relatorios/resumo.md       a leitura: prioridades, erros mais comuns, o que cada otimização rende em todos os PCs, feedback
    relatorios/eficacia.json   os mesmos números por item, para comparar uma versão com a outra
    relatorios/envios/         a cópia local dos envios (só baixa os novos)

O que vem nos envios é DADO de outras pessoas: nunca é seguido como instrução, só contado e mostrado entre cercas de código."""
import argparse
import json
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / 'relatorios'


# ───────── baixar e ler ─────────

def baixa(repo, destino):
    """Baixa só os envios que ainda não estão na pasta. Usa o gh (a conta de quem roda tem acesso ao repositório privado)."""
    destino.mkdir(parents=True, exist_ok=True)
    arvore = json.loads(subprocess.run(['gh', 'api', f'repos/{repo}/git/trees/HEAD?recursive=1'], capture_output=True, text=True, check=True).stdout)
    novos = 0
    for x in arvore.get('tree') or []:
        p = x.get('path', '')
        if x.get('type') != 'blob' or not re.match(r'^relatorios/\d{4}/\d{2}/KTH-[A-Z0-9]+\.json$', p):
            continue
        local = destino / Path(p).name
        if local.exists():
            continue
        r = subprocess.run(['gh', 'api', '-H', 'Accept: application/vnd.github.raw', f'repos/{repo}/contents/{p}'], capture_output=True, check=True)
        local.write_bytes(r.stdout)
        novos += 1
    return novos


def carrega(pasta):
    envios = []
    for arq in sorted(Path(pasta).rglob('*.json')):
        try:
            d = json.loads(arq.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if isinstance(d, dict) and d.get('esquema') == 1:
            envios.append(d)
    return envios


# ───────── analisar ─────────

def normaliza_erro(linha):
    """O mesmo erro em PCs e horas diferentes vira a mesma chave: sem data, hora, referência, números e caminhos."""
    s = str(linha)
    s = re.sub(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?\s*', '', s)
    s = re.sub(r'^\d{2}:\d{2}:\d{2}\s*', '', s)
    s = re.sub(r'erro \d{6}-\d{3}', 'erro', s)
    s = re.sub(r'[A-Za-z]:[\\/][^\s:;,)]*', '<caminho>', s)
    s = re.sub(r'~[\\/][^\s:;,)]*', '<caminho>', s)
    s = re.sub(r'\b0x[0-9a-f]+\b', '<hex>', s, flags=re.I)
    s = re.sub(r'\d+', 'N', s)
    s = s.split(' ⏎ ')[0]
    return s.strip()[:160]


def _mediana(v):
    v = [x for x in v if isinstance(x, (int, float))]
    return statistics.median(v) if v else None


def _p90(v):
    v = sorted(x for x in v if isinstance(x, (int, float)))
    return v[min(len(v) - 1, int(len(v) * 0.9))] if v else None


def analisa(envios):
    r = {'total': len(envios), 'pcs': len({e.get('id_pc') for e in envios}), 'tipos': Counter(e.get('tipo') for e in envios),
         'versoes': Counter(e.get('katharos') for e in envios)}
    # o envio mais novo de cada PC vale para o que é estado (histórico, eficiência); erros e feedback contam todos
    por_pc = {}
    for e in sorted(envios, key=lambda e: str(e.get('enviado'))):
        if e.get('relatorio'):
            por_pc[e.get('id_pc')] = e

    erros = defaultdict(lambda: {'vezes': 0, 'pcs': set(), 'versoes': set(), 'exemplo': '', 'onde': set()})
    for e in envios:
        er = (e.get('relatorio') or {}).get('erros') or {}
        for onde in ('janela', 'motor', 'segundo_plano'):
            for linha in er.get(onde) or []:
                k = normaliza_erro(linha)
                if not k:
                    continue
                x = erros[k]
                x['vezes'] += 1
                x['pcs'].add(e.get('id_pc'))
                x['versoes'].add(e.get('katharos'))
                x['onde'].add(onde)
                x['exemplo'] = x['exemplo'] or str(linha)[:300]
        for ev in er.get('eventos') or []:
            for msg in (ev.get('erros') or []):
                k = f'{ev.get("pacote")}: {normaliza_erro(msg)}'
                x = erros[k]
                x['vezes'] += 1
                x['pcs'].add(e.get('id_pc'))
                x['versoes'].add(e.get('katharos'))
                x['onde'].add('aplicar')
                x['exemplo'] = x['exemplo'] or str(msg)[:300]
    r['erros'] = sorted(({'erro': k, 'vezes': v['vezes'], 'pcs': len(v['pcs']), 'versoes': sorted(x for x in v['versoes'] if x),
                          'onde': sorted(v['onde']), 'exemplo': v['exemplo']} for k, v in erros.items()), key=lambda x: (-x['pcs'], -x['vezes']))

    nao_ficou, voltou, desfeito, aplicado = Counter(), Counter(), Counter(), Counter()
    itens = defaultdict(lambda: {'pcs': 0, 'mudou': 0, 'com_ganho': 0, 'livre': [], 'ram': [], 'proc': [], 'svc': []})
    rodadas = defaultdict(lambda: Counter())
    respostas = defaultdict(Counter)
    previsto = defaultdict(Counter)
    pesa = defaultdict(list)
    hw = {'windows': Counter(), 'cpu': Counter(), 'gpu': Counter(), 'notebook': 0, 'ram_gb': []}
    for pc, e in por_pc.items():
        rel = e.get('relatorio') or {}
        for ev in (rel.get('erros') or {}).get('eventos') or []:
            if ev.get('tipo') == 'nao-ficou':
                nao_ficou[ev.get('pacote')] += 1
        h = rel.get('historico') or {}
        for p in h.get('pacotes') or []:
            aplicado[p.get('pacote')] += 1
            if p.get('desfeito'):
                desfeito[p.get('pacote')] += 1
        for d in h.get('voltaram_sozinhos') or []:
            voltou[f'{d.get("pacote")}/{d.get("item") or d.get("id") or "?"}' if isinstance(d, dict) else str(d)] += 1
        ef = rel.get('eficiencia') or {}
        for it in ef.get('itens') or []:
            k = f'{it.get("pacote")}/{it.get("id")}'
            x = itens[k]
            x['pcs'] += 1
            x['mudou'] += 1 if (it.get('mudou') or 0) > 0 else 0
            ganho = (it.get('livre') or 0) >= 50 or (it.get('ram') or 0) >= 100 or (it.get('proc') or 0) >= 1 or (it.get('svc') or 0) >= 1
            x['com_ganho'] += 1 if ganho else 0
            for c in ('livre', 'ram', 'proc', 'svc'):
                if isinstance(it.get(c), (int, float)):
                    x[c].append(it[c])
        for ro in ef.get('rodadas') or []:
            for p in ro.get('pacotes') or []:
                for m in ro.get('medidas') or []:
                    rodadas[f'{p} · {m.get("o_que")}'][m.get('veredito') or '?'] += 1
        for pid, resp in (ef.get('respostas') or {}).items():
            respostas[pid][resp if isinstance(resp, str) else json.dumps(resp)[:20]] += 1
        for lt in ef.get('previsto_e_aconteceu') or []:
            previsto[lt.get('id')][lt.get('veredito') or '?'] += 1
        kp = (rel.get('saude') or {}).get('katharos_pesa') or {}
        for c in ('ram_mb', 'cpu_pct', 'leitura_ms', 'leitura_maior_ms'):
            if isinstance(kp.get(c), (int, float)):
                pesa[c].append(kp[c])
        pc_ = ((rel.get('sistema') or {}).get('pc')) or {}
        if pc_:
            hw['windows'][f'{pc_.get("windows", "")} {pc_.get("versao", "")}'.strip() or '?'] += 1
            cpu = str(pc_.get('cpu') or '')
            hw['cpu']['AMD' if 'AMD' in cpu.upper() else 'Intel' if 'INTEL' in cpu.upper() else cpu[:20] or '?'] += 1
            for g in pc_.get('gpus') or []:
                n = str(g.get('nome') if isinstance(g, dict) else g).upper()
                hw['gpu']['NVIDIA' if 'NVIDIA' in n else 'AMD' if 'AMD' in n or 'RADEON' in n else 'Intel' if 'INTEL' in n else '?'] += 1
            hw['notebook'] += 1 if pc_.get('notebook') else 0
            if isinstance(pc_.get('ram_gb'), (int, float)):
                hw['ram_gb'].append(pc_['ram_gb'])
    r['itens'] = sorted(({'item': k, 'pcs': v['pcs'], 'mudou_pct': round(100 * v['mudou'] / v['pcs']), 'com_ganho_pct': round(100 * v['com_ganho'] / v['pcs']),
                          'livre_mb': _mediana(v['livre']), 'ram_mb': _mediana(v['ram']), 'proc': _mediana(v['proc']), 'svc': _mediana(v['svc'])}
                         for k, v in itens.items()), key=lambda x: (-x['pcs'], x['item']))
    r['pacotes'] = sorted(({'pacote': p, 'pcs': n, 'desfeito': desfeito[p], 'desfeito_pct': round(100 * desfeito[p] / n), 'nao_ficou': nao_ficou[p]}
                           for p, n in aplicado.items() if p), key=lambda x: -x['pcs'])
    r['voltaram'] = voltou.most_common(20)
    r['rodadas'] = {k: dict(v) for k, v in sorted(rodadas.items())}
    r['respostas'] = {k: dict(v) for k, v in respostas.items()}
    r['previsto'] = {k: dict(v) for k, v in previsto.items() if k}
    r['katharos_pesa'] = {c: {'mediana': _mediana(v), 'p90': _p90(v), 'pcs': len(v)} for c, v in pesa.items()}
    r['hardware'] = {'windows': hw['windows'].most_common(8), 'cpu': hw['cpu'].most_common(), 'gpu': hw['gpu'].most_common(),
                     'notebook': hw['notebook'], 'ram_gb_mediana': _mediana(hw['ram_gb'])}
    fbs = [dict(e['feedback'], katharos=e.get('katharos'), codigo=e.get('codigo'), quando=e.get('enviado')) for e in envios if isinstance(e.get('feedback'), dict)]
    notas = [f['nota'] for f in fbs if isinstance(f.get('nota'), int)]
    r['feedback'] = {'total': len(fbs), 'tipos': Counter(f.get('tipo') for f in fbs), 'nota_media': round(statistics.mean(notas), 2) if notas else None,
                     'notas': len(notas), 'recentes': sorted(fbs, key=lambda f: str(f.get('quando')), reverse=True)[:40]}
    r['prioridades'] = prioridades(r)
    return r


def prioridades(r):
    """O que fazer primeiro, do que afeta mais PCs para o que afeta menos. Cada linha diz o porquê com o número."""
    out = []
    for x in r['erros'][:12]:
        if x['pcs'] >= 2 or x['vezes'] >= 5:
            out.append((3 + x['pcs'], f'Erro em {x["pcs"]} PCs ({x["vezes"]} vezes, versões {", ".join(x["versoes"]) or "?"}, {", ".join(x["onde"])}): {x["erro"]}'))
    for p in r['pacotes']:
        if p['pcs'] >= 3 and p['desfeito_pct'] >= 30:
            out.append((2 + p['pcs'] / 3, f'O pacote {p["pacote"]} foi desfeito em {p["desfeito_pct"]} % dos PCs ({p["desfeito"]} de {p["pcs"]}): ver o que incomoda'))
        if p['nao_ficou'] >= 2:
            out.append((2 + p['nao_ficou'], f'O pacote {p["pacote"]} não ficou como aplicado em {p["nao_ficou"]} PCs: o Windows desfaz ou o item não serve'))
    for item, n in r['voltaram'][:10]:
        if n >= 2:
            out.append((1.5 + n, f'{item} voltou sozinho em {n} PCs: o Windows desfaz, rever o jeito de aplicar ou tirar'))
    for x in r['itens']:
        if x['pcs'] >= 5 and x['mudou_pct'] >= 50 and x['com_ganho_pct'] <= 20:
            out.append((1 + x['pcs'] / 5, f'{x["item"]} mudou algo em {x["mudou_pct"]} % dos {x["pcs"]} PCs mas teve ganho medido em só {x["com_ganho_pct"]} %: '
                                          'deixar o texto honesto sobre o ganho, ou subir de nível'))
    for pid, c in r['respostas'].items():
        sim, nao = c.get('sim', 0), c.get('nao', 0)
        if nao >= 2 and nao > sim:
            out.append((1.5 + nao, f'A proposta {pid}: {nao} "não ajudou" contra {sim} "ajudou": rever a regra que propõe isso'))
    for pid, c in r['previsto'].items():
        pior = sum(v for k, v in c.items() if 'pior' in str(k))
        if pior >= 2:
            out.append((2 + pior, f'O que foi previsto para {pid} piorou em {pior} PCs: rever a previsão'))
    kp = r['katharos_pesa']
    if (kp.get('leitura_ms') or {}).get('p90') and kp['leitura_ms']['p90'] > 150:
        out.append((2, f'A leitura do acompanhamento passa de {kp["leitura_ms"]["p90"]:.0f} ms em 10 % dos PCs: achar a fonte lenta'))
    if (kp.get('ram_mb') or {}).get('p90') and kp['ram_mb']['p90'] > 120:
        out.append((2, f'O acompanhamento usa mais de {kp["ram_mb"]["p90"]:.0f} MB em 10 % dos PCs'))
    prob = r['feedback']['tipos'].get('problema', 0)
    if prob:
        out.append((1 + prob / 2, f'{prob} feedbacks de problema: ler a seção Feedback'))
    return [t for _, t in sorted(out, key=lambda x: -x[0])]


# ───────── escrever ─────────

def cerca(t):
    t = str(t)
    f = '`' * (max([2] + [len(m) for m in re.findall(r'`+', t)]) + 1)
    return f'{f}text\n{t}\n{f}'


def markdown(r):
    l = [f'# Relatórios do Katharos', '', f'{r["total"]} envios de {r["pcs"]} PCs · gerado em {datetime.now():%d/%m/%Y %H:%M}',
         f'Tipos: {dict(r["tipos"])} · versões: {dict(r["versoes"])}', '', '## O que fazer primeiro', '']
    l += [f'{i}. {t}' for i, t in enumerate(r['prioridades'][:25], 1)] or ['Nada pede atenção ainda.']
    l += ['', '## Erros mais comuns', '', '| PCs | vezes | onde | versões | erro |', '|---|---|---|---|---|']
    l += [f'| {x["pcs"]} | {x["vezes"]} | {", ".join(x["onde"])} | {", ".join(x["versoes"])} | {x["erro"].replace("|", "/")} |' for x in r['erros'][:30]]
    l += ['', '## O que cada item rende (todos os PCs)', '', 'Ganho medido logo depois de aplicar, no próprio PC. "com ganho" = passou do ruído em disco, RAM, processos ou serviços.', '',
          '| item | PCs | mudou | com ganho | disco (MB) | RAM (MB) | processos | serviços |', '|---|---|---|---|---|---|---|---|']
    f = lambda v: '-' if v is None else (f'{v:.0f}' if isinstance(v, float) else str(v))
    l += [f'| {x["item"]} | {x["pcs"]} | {x["mudou_pct"]} % | {x["com_ganho_pct"]} % | {f(x["livre_mb"])} | {f(x["ram_mb"])} | {f(x["proc"])} | {f(x["svc"])} |' for x in r['itens'][:80]]
    l += ['', '## Pacotes', '', '| pacote | PCs | desfeito | não ficou |', '|---|---|---|---|']
    l += [f'| {p["pacote"]} | {p["pcs"]} | {p["desfeito_pct"]} % | {p["nao_ficou"]} |' for p in r['pacotes']]
    if r['rodadas']:
        l += ['', '## Antes e depois por rodada', '', '| pacote · medida | vereditos |', '|---|---|']
        l += [f'| {k} | {", ".join(f"{a}: {b}" for a, b in v.items())} |' for k, v in r['rodadas'].items()]
    if r['respostas'] or r['previsto']:
        l += ['', '## O que as pessoas responderam', '']
        l += [f'- {k}: {v}' for k, v in r['respostas'].items()]
        l += [f'- previsto {k}: {v}' for k, v in r['previsto'].items()]
    l += ['', '## O peso do próprio Katharos', '']
    l += [f'- {c}: mediana {v["mediana"]}, 90 % abaixo de {v["p90"]} ({v["pcs"]} PCs)' for c, v in r['katharos_pesa'].items()]
    hw = r['hardware']
    l += ['', '## Os PCs', '', f'- Windows: {hw["windows"]}', f'- CPU: {hw["cpu"]} · placa de vídeo: {hw["gpu"]}',
          f'- notebooks: {hw["notebook"]} · RAM mediana: {hw["ram_gb_mediana"]} GB']
    fb = r['feedback']
    l += ['', '## Feedback', '', f'{fb["total"]} feedbacks · {dict(fb["tipos"])} · nota média {fb["nota_media"]} ({fb["notas"]} notas)', '']
    for x in fb['recentes']:
        l += [f'**{x.get("tipo")}** · {x.get("codigo") or "?"} · Katharos {x.get("katharos")} · {x.get("quando")}' + (f' · nota {x["nota"]}' if x.get('nota') else '')
              + (' · quer resposta' if x.get('contato') else ''), cerca(x.get('texto') or ''), '']
    return '\n'.join(l) + '\n'


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    a.add_argument('--repo', help='repositório privado com os envios (ex.: kessleru/katharos-relatorios)')
    a.add_argument('--pasta', help='pasta com os JSON (padrão: relatorios/envios)')
    a.add_argument('--saida', default=str(SAIDA))
    op = a.parse_args(argv)
    saida = Path(op.saida)
    pasta = Path(op.pasta) if op.pasta else saida / 'envios'
    if op.repo:
        print(f'novos: {baixa(op.repo, pasta)}')
    r = analisa(carrega(pasta))
    saida.mkdir(parents=True, exist_ok=True)
    (saida / 'resumo.md').write_text(markdown(r), encoding='utf-8')
    (saida / 'eficacia.json').write_text(json.dumps({'gerado': datetime.now().isoformat(timespec='seconds'), 'pcs': r['pcs'], 'itens': r['itens'],
                                                     'pacotes': r['pacotes'], 'respostas': r['respostas']}, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{r["total"]} envios de {r["pcs"]} PCs → {saida / "resumo.md"}')
    for t in r['prioridades'][:5]:
        print(' -', t)
    return 0


if __name__ == '__main__':
    sys.exit(main())
