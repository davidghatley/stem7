// Stem 7 site: every figure is drawn from site/data/glyphs.json, which tools/export_site.py writes from the .s7 sources.
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const NS = 'http://www.w3.org/2000/svg';
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

const data = await fetch(new URL('data/glyphs.json', import.meta.url)).then(r => r.json());
await Promise.all(['400 32px "Stem 7"', '700 32px "Stem 7"', '400 48px "Stem 7 Grid"'].map(f => document.fonts.load(f).catch(() => {})));

const byName = { regular: {}, bold: {} };
for (const st of ['regular', 'bold']) for (const g of data[st]) byName[st][g.n] = g;
const nameOf = {};
for (const g of data.regular) for (const u of g.u) nameOf[String.fromCodePoint(parseInt(u, 16))] = g.n;
const rows9 = r => r.length >= 9 ? r : [...r, ...Array(9 - r.length).fill('.'.repeat((r[0] || '').length))];
const ink = 'fill:var(--ink)', faint = 'stroke:var(--rule-faint)', rule = 'stroke:var(--rule)';

// A glyph (or several, placed by x offset in cells) drawn as cells on a grid, at a fixed pixel size.
function cellsSVG(parts, { cell = 12, cols, grid = true, guides = false, extra = '' } = {}) {
  const W = cols ?? Math.max(...parts.map(p => p.x + (p.rows[0] || '').length)), H = 9;
  let s = `<svg xmlns="${NS}" width="${W * cell}" height="${H * cell}" viewBox="0 0 ${W * cell} ${H * cell}" shape-rendering="crispEdges" aria-hidden="true">`;
  s += extra;
  if (grid) {
    for (let x = 0; x <= W; x++) s += `<line x1="${x * cell + .5}" y1="0" x2="${x * cell + .5}" y2="${H * cell}" style="${faint}"/>`;
    for (let y = 0; y <= H; y++) s += `<line x1="0" y1="${y * cell + .5}" x2="${W * cell}" y2="${y * cell + .5}" style="${faint}"/>`;
  }
  for (const p of parts) p.rows.forEach((r, y) => [...r].forEach((c, x) => {
    if (c === 'X') s += `<rect x="${(p.x + x) * cell}" y="${y * cell}" width="${cell}" height="${cell}" style="${p.style || ink}"/>`;
  }));
  if (guides) for (const y of [0, 3, 7]) s += `<line x1="0" y1="${y * cell + .5}" x2="${W * cell}" y2="${y * cell + .5}" style="stroke:var(--cobalt);stroke-width:1"/>`;
  return s + '</svg>';
}
const glyphParts = (g, x = 0, style) => ({ x: x + (g.l || 0), rows: rows9(g.r), style });
const adv = g => g.w ?? (g.l + (g.r[0] || '').length + g.rs);

// 00 hero grid: 1px lines on the font's own cell, aligned with the h1's cap line
function heroGrid() {
  const svg = $('.hero__grid'), c = innerWidth <= 640 ? 9 : 15;
  svg.innerHTML = `<defs><pattern id="hg" width="${c}" height="${c}" patternUnits="userSpaceOnUse"><rect width="${c}" height="1" fill="currentColor"/><rect width="1" height="${c}" fill="currentColor"/></pattern></defs><rect width="100%" height="100%" fill="url(#hg)"/>`;
}
heroGrid(); addEventListener('resize', heroGrid);

// segmented radios
function seg(el, on) {
  el.addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; set(b); });
  el.addEventListener('keydown', e => {
    if (!['ArrowLeft', 'ArrowRight'].includes(e.key)) return;
    const bs = $$('button', el), i = bs.findIndex(b => b.getAttribute('aria-checked') === 'true');
    const n = bs[(i + (e.key === 'ArrowRight' ? 1 : bs.length - 1)) % bs.length]; set(n); n.focus(); e.preventDefault();
  });
  function set(b) { $$('button', el).forEach(x => { x.setAttribute('aria-checked', x === b); x.tabIndex = x === b ? 0 : -1; }); on(b.dataset.v); }
  $$('button', el).forEach(x => x.tabIndex = x.getAttribute('aria-checked') === 'true' ? 0 : -1);
}

// 00 tester
{
  const out = $('[data-tester]'), note = $('[data-note]');
  let size = 48, style = 'regular';
  const NOTES = {
    16: '16 px · 2 px cells · caps and figures only, so it sets them in caps',
    32: '32 px · 4 px cells · the smallest size for lowercase',
    48: '48 px · 6 px cells · click the text to edit it',
    72: '72 px · 9 px cells',
    120: '120 px · 15 px cells · go on, zoom in',
    20: '20 px · 2.5 px cells · that soft edge is half a pixel. You were warned',
  };
  const draw = () => {
    out.style.fontSize = size + 'px';
    out.style.textTransform = size === 16 ? 'uppercase' : '';
    out.classList.toggle('is-bold', style === 'bold');
    out.classList.toggle('is-grid', style === 'grid');
    note.textContent = NOTES[size] + (style === 'grid' && size < 48 ? ' · Grid reads best from 48 px' : '');
    note.classList.toggle('is-bad', size === 20);
  };
  seg($('[data-size]'), v => { size = +v; draw(); });
  seg($('[data-style]'), v => { style = v; draw(); });
  if (!('contentEditable' in out) || out.contentEditable !== 'plaintext-only') out.contentEditable = 'true';
}

// 01 the mark, and H x g on the same grid with labelled guide lines
{
  const mark = byName.regular['dh.mark'];
  $('[data-fig="mark"]').outerHTML = cellsSVG([{ x: 0, rows: mark.r }], { cell: 20 });
  const parts = []; let x = 1;
  for (const n of ['H', 'x', 'g', 'dh.mark']) { const g = byName.regular[n]; parts.push(glyphParts(g, x)); x += adv(g) + 1; }
  const cell = innerWidth <= 640 ? 10 : 20, W = x;
  const wrap = document.createElement('div'); wrap.className = 'guides';
  wrap.style.cssText = `position:relative;max-width:100%;overflow-x:auto;padding:8px 0`;
  wrap.innerHTML = `<div style="position:relative;width:${W * cell + 128}px">${cellsSVG(parts, { cell, cols: W, guides: true, extra: `<rect x="0" y="${7 * cell}" width="${W * cell}" height="${2 * cell}" style="fill:var(--cobalt-tint)"/>` })}` +
    [['Cap · 7', 0], ['x-height · 4', 3], ['Baseline', 7], ['Descender · 2', 9]].map(([t, y]) => `<span class="ss-label" style="position:absolute;left:${W * cell + 12}px;top:${y * cell - 8}px">${t}</span>`).join('') + '</div>';
  $('[data-fig="guides"]').replaceWith(wrap);
}

// 02 source
{
  const picks = [['a', 'a'], ['g', 'g'], ['2', 'two'], ['&', 'ampersand'], ['@', 'at'], ['N', 'N']];
  const host = $('[data-pick="src"]');
  const show = n => {
    const g = byName.regular[n];
    const note = g.note ? g.note.split('\n').flatMap(l => wrapText(l, 46)).map(l => '# ' + l) : [];
    const lab = { 0: 'cap', 3: 'x-height', 6: 'baseline', 8: 'descender' };
    const head = `glyph ${g.n} ${g.u.map(u => 'U+' + u).join(',')}${g.l ? ' lsb=' + g.l : ''}${g.rs !== 1 ? ' rsb=' + g.rs : ''}`;
    $('[data-src]').innerHTML = [...note.map(l => `<span class="c">${esc(l)}</span>`), esc(head),
      ...rows9(g.r).map((r, i) => esc(r) + (lab[i] ? `   <span class="c"># ${lab[i]}</span>` : ''))].join('\n');
    $('[data-fig="src"]').outerHTML = cellsSVG([glyphParts(g, 1)], { cell: 14, cols: adv(g) + 2, guides: true }).replace('<svg ', '<svg data-fig="src" ');
    $('[data-src-real]').textContent = String.fromCodePoint(parseInt(g.u[0], 16));
    $$('button', host).forEach(b => b.setAttribute('aria-pressed', b.dataset.n === n));
  };
  host.innerHTML = picks.map(([c, n]) => `<button type="button" data-n="${n}" aria-label="Show ${n}">${esc(c)}</button>`).join('');
  host.addEventListener('click', e => { const b = e.target.closest('button'); if (b) show(b.dataset.n); });
  show('a');
}
// source notes are comment lines; a line without closing punctuation ends its sentence
function tidy(t) { return t.split('\n').map(l => l.trim()).filter(Boolean).map(l => l[0].toUpperCase() + l.slice(1)).map(l => /[.!?:;)]$/.test(l) ? l : l + '.').join(' '); }
function wrapText(t, w) { const out = []; let l = ''; for (const word of t.split(/\s+/)) { if ((l + ' ' + word).trim().length > w) { out.push(l); l = word; } else l = (l + ' ' + word).trim(); } if (l) out.push(l); return out; }

// 03 the ladder: H at true size for each step, its cells drawn as cells
{
  const H = byName.regular.H;
  $('[data-fig="ladder"]').innerHTML = [16, 32, 48, 72, 120].map(s => {
    const c = s / 8;
    return `<div class="rung">${cellsSVG([glyphParts(H, 0)], { cell: c, grid: c >= 6 })}<b>${s} px</b><span>${c} px cells</span></div>`;
  }).join('');
}

// 04 the loupe: render with canvas in this browser, count pixels that are neither ink nor paper
{
  const cv = $('[data-loupe]'), n = $('[data-loupe-n]'), l = $('[data-loupe-l]');
  const off = document.createElement('canvas'), ox = off.getContext('2d', { willReadFrequently: true });
  const draw = s => {
    const text = 'Stem 7';
    ox.font = `400 ${s}px "Stem 7"`;
    const w = Math.ceil(ox.measureText(text).width) + 4, h = Math.ceil(s * 1.25) + 4;
    off.width = w; off.height = h;
    ox.font = `400 ${s}px "Stem 7"`; ox.textBaseline = 'alphabetic'; ox.fillStyle = '#000';
    ox.fillText(text, 2, 2 + Math.round(s * 7 / 8));
    const px = ox.getImageData(0, 0, w, h).data;
    let grey = 0, solid = 0;
    const cs = getComputedStyle(document.body);
    const col = { ink: cs.getPropertyValue('--ink').trim(), bad: cs.getPropertyValue('--vermilion').trim(), line: cs.getPropertyValue('--rule-faint').trim() };
    const z = Math.max(2, Math.min(14, Math.floor(720 / w)));
    cv.width = w * z; cv.height = h * z;
    const c = cv.getContext('2d');
    c.clearRect(0, 0, cv.width, cv.height);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const a = px[(y * w + x) * 4 + 3];
      if (!a) continue;
      if (a === 255) { solid++; c.fillStyle = col.ink; } else { grey++; c.fillStyle = col.bad; }
      c.fillRect(x * z, y * z, z, z);
    }
    if (z >= 6) { c.fillStyle = col.line; for (let x = 0; x <= w; x++) c.fillRect(x * z, 0, 1, cv.height); for (let y = 0; y <= h; y++) c.fillRect(0, y * z, cv.width, 1); }
    n.textContent = grey.toLocaleString();
    n.classList.toggle('is-bad', grey > 0);
    l.textContent = `grey pixels · ${solid.toLocaleString()} solid ink · ${s} px`;
  };
  let cur = 32;
  seg($('[data-loupe-size]'), v => draw(cur = +v));
  draw(cur);
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => draw(cur));
}

// 05 Grid gaps: one 3x3 patch per size, zoomed so a cell is 48px, with the device pixels ruled
{
  $('[data-fig="gaps"]').innerHTML = [16, 32, 48, 72, 120].map(s => {
    const c = s / 8, gap = s <= 40 ? c / 2 : c / 3, z = 48 / c, n = 3, W = n * c * z;
    let r = `<svg width="${W}" height="${W}" viewBox="0 0 ${W} ${W}" shape-rendering="crispEdges" aria-hidden="true">`;
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) r += `<rect x="${x * c * z}" y="${(y * c + gap) * z}" width="${(c - gap) * z}" height="${(c - gap) * z}" style="${ink}"/>`;
    for (let i = 0; i <= n * c; i++) r += `<line x1="${i * z + .5}" y1="0" x2="${i * z + .5}" y2="${W}" style="${rule};stroke-opacity:.6"/><line x1="0" y1="${i * z + .5}" x2="${W}" y2="${i * z + .5}" style="${rule};stroke-opacity:.6"/>`;
    return `<div class="gap">${r}</svg><b>${s} px · gap ${gap} px</b><span>${c} px cells</span></div>`;
  }).join('');
}

// 06 revisions: round 0 next to 1.001
{
  const revs = [
    ['a', 'a', 'Was a cut-corner bowl that read as o. Now it is the mark\'s square bowl with a spur.'],
    ['e', 'e', 'The bar stops short, which opens a 2-cell aperture.'],
    ['s', 's', 'Corners cut like S, so it stops reading as bold.'],
    ['t', 't', 'Starts a row lower, so t and l stop sharing a height.'],
    ['0', 'zero', 'The slash read as Ø at 120 px. Now it has a centre dot.'],
    ['2', 'two', 'Was a mirrored S. Now a hooked top and one step per row.'],
    ['7', 'seven', 'The 2-1-3 staircase looked broken. Now it steps evenly.'],
    ['N', 'N', 'One diagonal cell per row. The old 2-cell steps knotted at the stem.'],
  ];
  $('[data-fig="revs"]').innerHTML = revs.filter(([k]) => data.round0[k]).map(([k, n, why]) => {
    const g = byName.regular[n], old = rows9(data.round0[k]);
    return `<div class="rev"><div class="rev__pair">${cellsSVG([{ x: 0, rows: old, style: 'fill:var(--ink-muted)' }], { cell: 6, grid: false }).replace('<svg ', '<svg class="old" ')}<i>→</i>${cellsSVG([{ x: 0, rows: rows9(g.r) }], { cell: 6, grid: false })}</div><p>${esc(why)}</p></div>`;
  }).join('');
}

// 07 bold: auto-bold draft next to the drawn glyph, changed cells in cobalt
{
  const want = ['K', 'N', 'S', 's', 'f', 'two', 'seven', 'ampersand', 'at', 'dollar', 'question', 'asterisk'];
  const pick = want.filter(n => data.drafts[n] && byName.bold[n]);
  $('[data-nredrawn]').textContent = Object.keys(data.drafts).length;
  $('[data-fig="bolds"]').innerHTML = pick.map(n => {
    const d = rows9(data.drafts[n]), f = rows9(byName.bold[n].r);
    const same = f.map((r, y) => [...r].map((c, x) => c === 'X' && d[y] && d[y][x] === 'X' ? 'X' : '.').join(''));
    const diff = f.map((r, y) => [...r].map((c, x) => c === 'X' && !(d[y] && d[y][x] === 'X') ? 'X' : '.').join(''));
    const label = String.fromCodePoint(parseInt(byName.regular[n].u[0], 16));
    return `<div class="bold"><div class="bold__pair">${cellsSVG([{ x: 0, rows: d, style: 'fill:var(--ink-muted)' }], { cell: 5, grid: false })}<i>→</i>${cellsSVG([{ x: 0, rows: same }, { x: 0, rows: diff, style: 'fill:var(--cobalt)' }], { cell: 5, grid: false })}</div><span>${esc(label)}</span></div>`;
  }).join('');
}

// 08 kerning: a pair drawn with kerning off and on, the facing gap on each shared row shaded
{
  const pairs = [['F', 'a'], ['L', 'T'], ['T', 'o'], ['P', 'period']];
  const host = $('[data-pick="kern"]');
  const draw = ([a, b]) => {
    const A = byName.regular[a], B = byName.regular[b], k = data.kern[`${a} ${b}`] || [0, null];
    const ra = rows9(A.r), rb = rows9(B.r);
    const fig = kern => {
      const xb = adv(A) + kern;
      const gap = [];
      for (let y = 0; y < 9; y++) {
        const ia = ra[y].lastIndexOf('X'), ib = rb[y].indexOf('X');
        if (ia < 0 || ib < 0) continue;
        const from = A.l + ia + 1, to = xb + B.l + ib;
        if (to > from) gap.push(`<rect x="${from * 14}" y="${y * 14}" width="${(to - from) * 14}" height="14" style="fill:var(--cobalt-tint)"/>`);
      }
      return cellsSVG([glyphParts(A, 0), glyphParts(B, xb)], { cell: 14, cols: xb + adv(B), extra: gap.join('') });
    };
    const lbl = c => String.fromCodePoint(parseInt(byName.regular[c].u[0], 16));
    $('[data-fig="kern"]').innerHTML = `<figure>${fig(0)}<figcaption>Kerning off</figcaption></figure><figure>${fig(k[0])}<figcaption>Kerning on · <b>${k[0] ? (k[0] > 0 ? '+' : '−') + Math.abs(k[0]) + ' cell' + (Math.abs(k[0]) > 1 ? 's' : '') : 'none'}</b></figcaption></figure>`;
    $('[data-kern-cap]').textContent = (k[1] != null ? `${lbl(a)}${lbl(b)}: the average gap over the rows they share is ${k[1]} cells, so it pulls in ${Math.abs(k[0])}.` : '') +
      (a === 'F' && b === 'a' ? ' This is one of the 11 pairs that 1.001 fixed.' : '');
    $$('button', host).forEach(x => x.setAttribute('aria-pressed', x.dataset.p === a + ' ' + b));
  };
  host.innerHTML = pairs.map(([a, b]) => `<button type="button" data-p="${a} ${b}">${esc(String.fromCodePoint(parseInt(byName.regular[a].u[0], 16)) + String.fromCodePoint(parseInt(byName.regular[b].u[0], 16)))}</button>`).join('');
  host.addEventListener('click', e => { const x = e.target.closest('button'); if (x) draw(x.dataset.p.split(' ')); });
  draw(pairs[0]);
}

// 09 every character + inspector
{
  const grid = $('[data-grid]'), insp = $('[data-insp]');
  let style = 'regular', cur = 'a';
  const list = () => data[style].filter(g => g.r.length || g.w);
  const ch = g => String.fromCodePoint(parseInt(g.u[0], 16));
  const render = () => {
    grid.innerHTML = list().map(g => `<button type="button" class="gtile${style === 'bold' ? ' is-bold' : ''}" data-n="${esc(g.n)}" aria-pressed="${g.n === cur}" aria-label="${esc(g.n)}">${!g.r.length ? `<span class="ss-label">${g.n === 'space' ? 'SP' : 'FIG'}</span>` : esc(ch(g))}</button>`).join('');
    inspect(cur);
  };
  const inspect = n => {
    const g = byName[style][n] || byName.regular[n]; cur = n;
    $$('.gtile', grid).forEach(b => b.setAttribute('aria-pressed', b.dataset.n === n));
    const w = (g.r[0] || '').length;
    insp.innerHTML = `<div class="insp__head"><b>${esc(g.n)}</b><span class="ss-label">${g.u.map(u => 'U+' + u).join(' · ')}</span></div>` +
      (g.r.length ? cellsSVG([glyphParts(g, 1)], { cell: 16, cols: adv(g) + 2, guides: true }) : '<p>An empty glyph. Very restful.</p>') +
      `<dl><dt>Advance</dt><dd>${adv(g)} cells</dd><dt>Drawing</dt><dd>${w} × ${g.r.length ? 9 : 0}</dd><dt>Bearings</dt><dd>${g.l} left · ${g.rs} right</dd>${g.t ? '<dt>Figure</dt><dd>tabular</dd>' : ''}</dl>` +
      (g.note ? `<p>${esc(tidy(g.note.replace(/^[^:\n]+:\s*/, '')))}</p>` : '');
  };
  grid.addEventListener('click', e => { const b = e.target.closest('.gtile'); if (b) inspect(b.dataset.n); });
  seg($('[data-gstyle]'), v => { style = v; render(); });
  render();
}

// 10 in use: a live clock (paused offscreen) and the seed strip
{
  const el = $('[data-clock]'); let t = 0, on = false;
  const tick = () => { const d = new Date(); el.textContent = [d.getHours(), d.getMinutes(), d.getSeconds()].map(v => String(v).padStart(2, '0')).join(':'); };
  tick();
  if (!reduced) new IntersectionObserver(([e]) => { on = e.isIntersecting; clearInterval(t); if (on) t = setInterval(tick, 1000); }).observe(el);
  const s = $('[data-seed]'), v = +s.dataset.seed;
  s.innerHTML = [...Array(16)].map((_, i) => `<i class="${(v >> (15 - i)) & 1 ? 'on' : ''}"></i>`).join('');
}

// 11 tabs and copy buttons
{
  const tabs = $$('[role="tab"]');
  const sel = t => { tabs.forEach(x => { const on = x === t; x.setAttribute('aria-selected', on); x.tabIndex = on ? 0 : -1; $('#' + x.getAttribute('aria-controls')).hidden = !on; }); };
  tabs.forEach((t, i) => {
    t.addEventListener('click', () => sel(t));
    t.addEventListener('keydown', e => {
      const d = { ArrowRight: 1, ArrowLeft: -1, Home: -i, End: tabs.length - 1 - i }[e.key];
      if (d === undefined) return;
      const n = tabs[(i + d + tabs.length) % tabs.length]; sel(n); n.focus(); e.preventDefault();
    });
  });
  if (location.hash === '#npm') sel($('#tab-npm'));
  $$('[data-copy]').forEach(b => b.addEventListener('click', async () => {
    const text = b.closest('.ss-code').querySelector('pre').textContent;
    try { await navigator.clipboard.writeText(text); b.textContent = 'Copied'; } catch { b.textContent = 'Select and copy'; }
    setTimeout(() => b.textContent = 'Copy', 1600);
  }));
}
