"""Gera planos/catalogo-<versão>.md: todos os itens, o modo que marca cada um, se volta com o Desfazer, o ganho e o custo.
Uso: python3 scripts/catalogo.py (depois de bash scripts/monta.sh)."""
import importlib.util, json, sys
from pathlib import Path
raiz = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('k', raiz / 'programa' / 'katharos.py')
k = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k)
ctx = k.Ctx(k._defaults(k.monta_parser().parse_args([])), k.Terminal(True, True, consulta_fundo=False))
ctx.perfil = json.loads(json.dumps(k.PC_MODELO))
nomes = {0: 'só se marcar', 1: 'seguro', 2: 'equilibrado', 3: 'extremo'}
L, tot = [], 0
for nome, pac in k.PACOTES.items():
    its = [x for x in (pac.itens(ctx) or []) if x]
    if not its:
        continue
    manut = nome in k.PACOTES_RECORRENTES
    L += [f'## {nome}' + (' (manutenção: não vem marcada na janela)' if manut else ''), '',
          '| Item | Vem marcado a partir de | Volta | Ganha | Perde |', '|---|---|---|---|---|']
    for it in its:
        tot += 1
        c = lambda t: str(t or '').replace('|', '/').replace('\n', ' ')
        L.append(f'| {c(it.titulo)} | {"-" if manut else nomes.get(it.nivel, it.nivel)} | {"sim" if it.reverte else "**não**"} | {c(it.ganho)} | {c(it.custo)} |')
    L.append('')
cab = [f'# Catálogo do Katharos {k.VERSAO}', '',
       'Gerado do código por `scripts/catalogo.py` (PC modelo: Windows 11, com jogos). "Vem marcado a partir de" é o primeiro modo que marca o item; '
       '"só se marcar" nunca vem marcado. **Volta** = o Desfazer devolve o valor de antes.', '',
       f'{tot} itens em {len(k.PACOTES)} áreas. Regras (plano 5.0.0, seção 3.4): item sem volta nunca vem marcado (teste '
       '`test_nenhum_item_sem_volta_vem_marcado`); limpeza, reparo e atualização são manutenção e não vêm marcados na janela.', '']
(raiz / 'planos' / f'catalogo-{k.VERSAO}.md').write_text('\n'.join(cab + L), encoding='utf-8')
print(tot, 'itens')
