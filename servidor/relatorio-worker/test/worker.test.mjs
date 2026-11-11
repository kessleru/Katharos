// node --test servidor/relatorio-worker/test   (sem dependências: o fetch do GitHub é trocado por um falso)
import test from 'node:test';
import assert from 'node:assert/strict';
import worker, { valida, ficha, novoCodigo } from '../src/index.js';

const env = { GITHUB_TOKEN: 'x', REPO: 'kessleru/katharos-relatorios' };
const base = () => ({
  esquema: 1, tipo: 'ambos', katharos: '4.2.0', enviado: '2026-11-11T15:00:00', id_pc: '0123456789abcdef', secoes: ['erros'],
  feedback: { tipo: 'problema', texto: 'travou ao ligar ```\n## injeção', nota: 4, contato: 'eu@exemplo.com' },
  relatorio: { erros: { janela: ['erro 1'], motor: [], segundo_plano: [], eventos: [] } },
});
const pede = (corpo, cab = {}) => new Request('https://w/enviar', { method: 'POST', body: typeof corpo === 'string' ? corpo : JSON.stringify(corpo), headers: cab });

function githubFalso(falhaEm = null) {
  const chamadas = [];
  globalThis.fetch = async (url, op) => {
    chamadas.push({ url, op, corpo: JSON.parse(op.body) });
    if (falhaEm && url.includes(falhaEm)) return new Response('{}', { status: 500 });
    return new Response('{}', { status: 201 });
  };
  return chamadas;
}

test('valida o formato do motor', () => {
  assert.equal(valida(base()), null);
  assert.match(valida({ ...base(), extra: 1 }), /inesperado/);
  assert.match(valida({ ...base(), esquema: 2 }), /esquema/);
  assert.match(valida({ ...base(), id_pc: 'abc' }), /id_pc/);
  assert.match(valida({ ...base(), feedback: { ...base().feedback, nota: 7 } }), /nota/);
  assert.match(valida({ ...base(), feedback: { ...base().feedback, texto: ' ' } }), /texto/);
  assert.match(valida({ ...base(), secoes: ['portas'] }), /seções/);
  assert.match(valida({ ...base(), relatorio: { portas: {} } }), /seção/);
  const so = base(); so.tipo = 'feedback';
  assert.match(valida(so), /relatório num envio só de feedback/);
  delete so.relatorio; delete so.secoes;
  assert.equal(valida(so), null);
});

test('guarda o arquivo e abre a issue, devolvendo o código', async () => {
  const ch = githubFalso();
  const r = await worker.fetch(pede(base()), env);
  const d = await r.json();
  assert.equal(r.status, 200);
  assert.match(d.codigo, /^KTH-[A-HJ-NP-Z2-9]{6}$/);
  assert.equal(ch.length, 2);
  assert.match(ch[0].url, /\/repos\/kessleru\/katharos-relatorios\/contents\/relatorios\/\d{4}\/\d{2}\/KTH-/);
  const salvo = JSON.parse(Buffer.from(ch[0].corpo.content, 'base64').toString('utf8'));
  assert.equal(salvo.codigo, d.codigo);
  assert.equal(salvo.feedback.texto, base().feedback.texto, 'acentos e texto chegam iguais');
  assert.match(ch[1].url, /\/issues$/);
  assert.ok(ch[1].corpo.labels.includes('com erros'));
  // o texto de quem mandou não fecha o bloco de código nem vira título na issue
  assert.ok(ch[1].corpo.body.includes('````text\ntravou ao ligar ```\n## injeção\n````'));
});

test('recusa o que não serve', async () => {
  githubFalso();
  assert.equal((await worker.fetch(pede('não é json'), env)).status, 400);
  assert.equal((await worker.fetch(pede({ ...base(), tipo: 'x' }), env)).status, 400);
  assert.equal((await worker.fetch(pede('x'.repeat(300 * 1024)), env)).status, 413);
  assert.equal((await worker.fetch(new Request('https://w/outro', { method: 'POST', body: '{}' }), env)).status, 404);
  assert.equal((await worker.fetch(pede(base()), {})).status, 503);
  const limite = { ...env, LIMITE: { limit: async () => ({ success: false }) } };
  assert.equal((await worker.fetch(pede(base()), limite)).status, 429);
});

test('issue sem etiqueta se a etiqueta falhar; erro do GitHub vira 502', async () => {
  let n = 0;
  globalThis.fetch = async (url, op) => { n++; return new Response('{}', { status: url.includes('/issues') && JSON.parse(op.body).labels ? 422 : 201 }); };
  assert.equal((await worker.fetch(pede(base()), env)).status, 200);
  assert.equal(n, 3);
  githubFalso('/contents/');
  assert.equal((await worker.fetch(pede(base()), env)).status, 502);
});

test('código e ficha', () => {
  const cs = new Set(Array.from({ length: 200 }, novoCodigo));
  assert.equal(cs.size, 200);
  const f = ficha(base(), 'KTH-ABCDEF', 'relatorios/x.json');
  assert.match(f, /KTH-ABCDEF/);
  assert.match(f, /nota 4\/5/);
  assert.ok(f.length <= 60000);
});
