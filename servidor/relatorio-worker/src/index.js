// Katharos: recebe o relatório e o feedback que a janela manda e guarda no repositório PRIVADO do dono.
//
//   POST /enviar   corpo: o pacote JSON montado pelo motor (já limpo de dado pessoal no PC, com prévia e consentimento)
//                  resposta: {"ok": true, "codigo": "KTH-XXXXXX"}
//   GET  /         {"ok": true} (para conferir se está no ar)
//
// Este Worker não guarda nada: cada envio vira um arquivo JSON (relatorios/AAAA/MM/KTH-....json) e uma issue no repositório
// privado, com a ficha resumida para triagem. O token do GitHub fica só nos segredos do Worker (GITHUB_TOKEN), com acesso só
// àquele repositório. Limites: tamanho, formato conferido campo a campo e, se a ligação LIMITE existir, envios por IP.
// Arquivo único, sem dependências: dá para colar direto no editor do painel da Cloudflare.

const MAX_BYTES = 256 * 1024;
const TIPOS = ['relatorio', 'feedback', 'ambos'];
const FEEDBACK = ['problema', 'ideia', 'elogio', 'outro'];
const SECOES = ['sistema', 'erros', 'historico', 'eficiencia', 'saude', 'jogos'];
const CHAVES = ['esquema', 'tipo', 'katharos', 'enviado', 'id_pc', 'feedback', 'relatorio', 'secoes', 'encurtado'];

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), { status, headers: { 'content-type': 'application/json; charset=utf-8' } });
}

/** O pacote no formato que o motor monta. Devolve o problema em palavras, ou null se está certo. */
export function valida(p) {
  if (!p || typeof p !== 'object' || Array.isArray(p)) return 'o corpo precisa ser um objeto JSON';
  for (const k of Object.keys(p)) if (!CHAVES.includes(k)) return `campo inesperado: ${k}`.slice(0, 80);
  if (p.esquema !== 1) return 'esquema desconhecido';
  if (!TIPOS.includes(p.tipo)) return 'tipo inválido';
  if (typeof p.katharos !== 'string' || !/^\d+\.\d+\.\d+$/.test(p.katharos)) return 'versão inválida';
  if (typeof p.id_pc !== 'string' || !/^[0-9a-f]{16}$/.test(p.id_pc)) return 'id_pc inválido';
  if (typeof p.enviado !== 'string' || p.enviado.length > 40) return 'data inválida';
  if (p.tipo !== 'relatorio') {
    const f = p.feedback;
    if (!f || typeof f !== 'object' || Array.isArray(f)) return 'falta o feedback';
    if (!FEEDBACK.includes(f.tipo)) return 'tipo de feedback inválido';
    if (typeof f.texto !== 'string' || f.texto.trim().length < 3 || f.texto.length > 5000) return 'texto do feedback inválido';
    if (f.nota !== null && f.nota !== undefined && !(Number.isInteger(f.nota) && f.nota >= 1 && f.nota <= 5)) return 'nota inválida';
    if (f.contato !== null && f.contato !== undefined && (typeof f.contato !== 'string' || f.contato.length > 120)) return 'contato inválido';
  } else if (p.feedback !== undefined) return 'feedback num envio só de relatório';
  if (p.tipo !== 'feedback') {
    if (!p.relatorio || typeof p.relatorio !== 'object' || Array.isArray(p.relatorio)) return 'falta o relatório';
    if (!Array.isArray(p.secoes) || !p.secoes.length || p.secoes.some(s => !SECOES.includes(s))) return 'seções inválidas';
    for (const k of Object.keys(p.relatorio)) if (!SECOES.includes(k)) return 'seção inesperada no relatório';
  } else if (p.relatorio !== undefined) return 'relatório num envio só de feedback';
  return null;
}

/** KTH- e 6 letras e números sem os que se confundem (0/O, 1/I). */
export function novoCodigo() {
  const letras = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  const b = new Uint8Array(6);
  crypto.getRandomValues(b);
  return 'KTH-' + Array.from(b, x => letras[x % letras.length]).join('');
}

function base64(texto) {
  const bytes = new TextEncoder().encode(texto);
  let s = '';
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(s);
}

/** Bloco de código que nenhum texto de dentro consegue fechar (o texto vem do PC de alguém). */
function cerca(texto) {
  const maior = Math.max(2, ...(String(texto).match(/`+/g) || []).map(x => x.length));
  const f = '`'.repeat(maior + 1);
  return `${f}text\n${texto}\n${f}`;
}

/** A ficha da issue: o que dá para triar sem abrir o JSON. */
export function ficha(p, codigo, caminho) {
  const l = [];
  const r = p.relatorio || {};
  const pc = (r.sistema && r.sistema.pc) || {};
  l.push(`**${codigo}** · Katharos ${p.katharos} · ${p.tipo} · PC \`${p.id_pc}\` · ${p.enviado}`);
  if (pc.cpu || pc.windows) l.push(`PC: ${[pc.fabricante, pc.modelo].filter(Boolean).join(' ')} · ${pc.cpu || ''} · ${pc.ram_gb || '?'} GB · ${pc.windows || ''} ${pc.versao || ''} (build ${pc.build || '?'})`);
  if (p.feedback) {
    const f = p.feedback;
    l.push('', `### Feedback: ${f.tipo}${f.nota ? ` · nota ${f.nota}/5` : ''}${f.contato ? ' · quer resposta' : ''}`, cerca(f.texto));
    if (f.contato) l.push(`Contato: ${cerca(f.contato)}`);
  }
  if (r.erros) {
    const e = r.erros;
    const linhas = [...(e.janela || []), ...(e.motor || []), ...(e.segundo_plano || [])];
    l.push('', `### Erros: ${linhas.length} linhas, ${(e.eventos || []).length} eventos ao aplicar`);
    if (linhas.length) l.push(cerca(linhas.slice(-15).join('\n')));
  }
  if (r.eficiencia) {
    const ef = r.eficiencia;
    const resp = Object.values(ef.respostas || {});
    l.push('', `### Eficiência: ${(ef.itens || []).length} itens medidos, ${(ef.rodadas || []).length} rodadas` +
      (resp.length ? `, respostas: ${resp.filter(x => x === 'sim').length} ajudou / ${resp.filter(x => x === 'nao').length} não ajudou` : ''));
  }
  if (r.historico) l.push('', `### Histórico: ${(r.historico.pacotes || []).length} pacotes, ${(r.historico.voltaram_sozinhos || []).length} itens voltaram sozinhos`);
  if (r.saude && r.saude.raiox) l.push('', `### Saúde: raio-x nota ${r.saude.raiox.nota}`);
  if (p.encurtado) l.push('', '_O relatório passou do limite e as listas mais longas foram encurtadas no PC._');
  l.push('', `Arquivo completo: \`${caminho}\``);
  return l.join('\n').slice(0, 60000);
}

async function github(env, metodo, caminho, corpo) {
  const r = await fetch(`https://api.github.com${caminho}`, {
    method: metodo,
    headers: {
      authorization: `Bearer ${env.GITHUB_TOKEN}`, accept: 'application/vnd.github+json', 'x-github-api-version': '2022-11-28',
      'user-agent': 'katharos-relatorios', 'content-type': 'application/json',
    },
    body: JSON.stringify(corpo),
  });
  if (!r.ok) throw new Error(`GitHub ${metodo} ${caminho.split('/').slice(0, 4).join('/')}: ${r.status}`);
  return r.json();
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (req.method === 'GET' && url.pathname === '/') return json({ ok: true, servico: 'katharos-relatorios' });
    if (req.method !== 'POST' || url.pathname !== '/enviar') return json({ ok: false, erro: 'caminho não existe' }, 404);
    if (!env.GITHUB_TOKEN || !env.REPO) return json({ ok: false, erro: 'o servidor ainda não foi configurado' }, 503);

    if (env.LIMITE) {   // ligação de limite da Cloudflare (opcional): poucos envios por minuto de cada IP
      const { success } = await env.LIMITE.limit({ key: req.headers.get('cf-connecting-ip') || 'sem-ip' });
      if (!success) return json({ ok: false, erro: 'muitos envios em pouco tempo; tente daqui a pouco' }, 429);
    }
    if (Number(req.headers.get('content-length') || 0) > MAX_BYTES) return json({ ok: false, erro: 'grande demais' }, 413);
    const texto = await req.text();
    if (new TextEncoder().encode(texto).length > MAX_BYTES) return json({ ok: false, erro: 'grande demais' }, 413);
    let p;
    try { p = JSON.parse(texto); } catch { return json({ ok: false, erro: 'não é JSON' }, 400); }
    const problema = valida(p);
    if (problema) return json({ ok: false, erro: problema }, 400);

    const codigo = novoCodigo();
    const agora = new Date();
    const caminho = `relatorios/${agora.getUTCFullYear()}/${String(agora.getUTCMonth() + 1).padStart(2, '0')}/${codigo}.json`;
    const recebido = { ...p, codigo, recebido: agora.toISOString() };
    try {
      await github(env, 'PUT', `/repos/${env.REPO}/contents/${caminho}`, { message: `${p.tipo} ${codigo} (Katharos ${p.katharos})`, content: base64(JSON.stringify(recebido, null, 1)) });
      const titulo = `${p.tipo === 'feedback' ? 'Feedback' : p.tipo === 'ambos' ? 'Relatório e feedback' : 'Relatório'}` +
        `${p.feedback ? ` (${p.feedback.tipo})` : ''} · ${p.katharos} · ${codigo}`;
      const etiquetas = [p.tipo, `v${p.katharos}`, ...(p.feedback ? [p.feedback.tipo] : []),
        ...(p.relatorio && p.relatorio.erros && ((p.relatorio.erros.janela || []).length + (p.relatorio.erros.motor || []).length) ? ['com erros'] : [])];
      const corpo = { title: titulo, body: ficha(p, codigo, caminho), labels: etiquetas };
      try { await github(env, 'POST', `/repos/${env.REPO}/issues`, corpo); }
      catch { delete corpo.labels; await github(env, 'POST', `/repos/${env.REPO}/issues`, corpo); }   // sem permissão de etiqueta: vai sem
    } catch (e) {
      console.log('falha ao guardar: ' + e.message);
      return json({ ok: false, erro: 'não deu para guardar agora; tente de novo mais tarde' }, 502);
    }
    return json({ ok: true, codigo });
  },
};
