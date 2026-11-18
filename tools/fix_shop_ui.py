"""Атомарно ставит магазинный билдер в index.html: блок cs-full и JS билдера."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
p = ROOT / "static" / "index.html"
s = p.read_text(encoding="utf-8")

HTML = '''<div id="cs-full" class="hidden">
          <div class="row">
            <select id="cb-method" onchange="cbLoad()">
              <option value="complete_package">Complete Package — 62 STAT + 86 Skill</option>
              <option value="edgerunner">Edgerunner — бросок STAT + 86 Skill</option>
              <option value="streetrat">Streetrat — шаблон</option>
            </select>
            <select id="cb-role" onchange="cbLoad()"></select>
          </div>
          <div id="cb-method-note" class="book-note"></div>
          <div class="turnbar" style="font-size:0.95em">
            <span>Бюджет: <b id="cb-budget">0</b> eb</span>
            <span>Потрачено: <b id="cb-spent">0</b> eb</span>
            <span>Остаток: <b id="cb-left">0</b> eb</span>
          </div>
          <div class="panel-section">Статы (пул <span id="cb-stat-pool"></span>)</div>
          <div id="cb-stats" class="panel-small"></div>
          <div class="panel-section">Навыки — прирост поверх шаблона (осталось <span id="cb-skill-pool"></span>)</div>
          <div id="cb-skills" class="panel-small" style="max-height:220px;overflow-y:auto"></div>
          <div class="panel-section">Боевые искусства</div>
          <div id="cb-martial" class="panel-small"></div>
          <div class="panel-section">Пакет роли (бесплатно)</div>
          <div id="cb-package" class="panel-small"></div>
          <div class="panel-section">Магазин</div>
          <div class="row" id="cb-tabs"></div>
          <div id="cb-shop" class="panel-small" style="max-height:260px;overflow-y:auto"></div>
          <div class="panel-section">Куплено</div>
          <div id="cb-cart" class="panel-small"></div>
          <div class="panel-section">Экипировать</div>
          <div class="row"><select id="cb-weapon"></select><select id="cb-armor"></select></div>
          <div class="row"><button onclick="cbBuild()">Собрать персонажа</button></div>
        </div>

        '''

JS = '''let CB_CAT = 'weapon';
const CAT_RU = {weapon:'Оружие', armor:'Броня', gear:'Снаряжение',
                cyberware:'Импланты', drug:'Препараты', program:'Программы'};

async function cbLoad() {
  const role = document.getElementById('cb-role').value || '';
  const method = document.getElementById('cb-method').value || 'complete_package';
  const qs = new URLSearchParams({method});
  if (role) qs.set('role', role);
  const r = await fetch('/creation/options?' + qs.toString());
  if (!r.ok) { alert('Не удалось загрузить опции создания'); return; }
  CB = await r.json();
  CB.spec = {role: CB.role, method: CB.method,
    stats: Object.assign({}, CB.template_stats), skills: {},
    purchases: [], martial_form: null,
    weapon: CB.preset.weapon, armor: CB.preset.armor};
  CB.skills.forEach(x => { if (x.baseline) CB.spec.skills[x.key] = x.baseline; });
  document.getElementById('cb-method-note').textContent =
    ((typeof METHOD_NOTE !== 'undefined' && METHOD_NOTE[CB.method]) || '') +
    ' Очки навыков тратятся на прирост поверх шаблона.';
  document.getElementById('cb-tabs').innerHTML = Object.entries(CAT_RU).map(([k, v]) =>
    `<button class="secondary mini" onclick="cbTab('${k}')">${v}</button>`).join('');
  cbRender();
}

function cbTab(c) { CB_CAT = c; cbRender(); }

function cbOwned() { return Array.from(new Set([...(CB.package || []), ...CB.spec.purchases])); }
function cbSpent() {
  const m = {}; CB.catalog.forEach(i => m[i.key] = i.price);
  return CB.spec.purchases.reduce((a, k) => a + (m[k] || 0), 0);
}
function cbDelta() {
  let d = 0;
  CB.skills.forEach(s => { d += Math.max(0, (CB.spec.skills[s.key] || 0) - s.baseline); });
  return d;
}
function cbMartial() {
  const lvl = CB.spec.skills['martial_arts'] || 0;
  return {required: lvl >= 1, forms: (CB.martial && CB.martial.forms) || [],
          moves: [{key:'sweep',min_level:1},{key:'disarm',min_level:3},{key:'throw',min_level:5}]
                 .filter(m => lvl >= m.min_level)};
}

function cbRender() {
  if (!CB) return;
  const s = CB.spec, spent = cbSpent();
  document.getElementById('cb-budget').textContent = CB.budget;
  document.getElementById('cb-spent').textContent = spent;
  document.getElementById('cb-left').textContent = CB.budget - spent;

  if (CB.stat_pool === null || CB.stat_pool === undefined) {
    document.getElementById('cb-stat-pool').textContent =
      CB.method === 'streetrat' ? 'шаблон' : 'бросок 1d10';
    document.getElementById('cb-stats').innerHTML =
      CB.stats.map(k => `<span class="stat-chip"><b>${k}</b> ${s.stats[k]}</span>`).join('') +
      (CB.method === 'edgerunner'
        ? `<button class="secondary mini" onclick="cbRollStats()">🎲 Бросить STAT</button>` : '');
  } else {
    const used = Object.values(s.stats).reduce((a,b)=>a+b,0);
    document.getElementById('cb-stat-pool').textContent = CB.stat_pool - used;
    document.getElementById('cb-stats').innerHTML = CB.stats.map(k =>
      `<span class="stat-chip"><b>${k}</b> ${s.stats[k]}
        <button class="secondary mini" onclick="cbStat('${k}',-1)">−</button>
        <button class="secondary mini" onclick="cbStat('${k}',1)">+</button></span>`).join('');
  }

  if (CB.skill_pool === null || CB.skill_pool === undefined) {
    document.getElementById('cb-skill-pool').textContent = 'шаблон';
    document.getElementById('cb-skills').innerHTML = CB.skills
      .filter(x => s.skills[x.key])
      .map(x => `<span class="stat-chip"><b>${x.key}</b> ${s.skills[x.key]}</span>`).join('');
  } else {
    document.getElementById('cb-skill-pool').textContent = CB.skill_pool - cbDelta();
    document.getElementById('cb-skills').innerHTML = CB.skills.map(x =>
      `<span class="stat-chip"><b>${x.key}</b> [${x.stat}] ${s.skills[x.key]||0}
        <span style="color:#666">база ${x.baseline}</span>
        <button class="secondary mini" onclick="cbSkill('${x.key}',-1)">−</button>
        <button class="secondary mini" onclick="cbSkill('${x.key}',1)">+</button></span>`).join('');
  }

  const ma = cbMartial();
  document.getElementById('cb-martial').innerHTML = !ma.required
    ? '<span style="color:#888">martial_arts = 0 — форма не требуется</span>'
    : `<select onchange="CB.spec.martial_form=this.value">
         <option value="">— выбрать форму —</option>
         ${ma.forms.map(f => `<option ${s.martial_form===f?'selected':''}>${f}</option>`).join('')}
       </select>
       <div style="margin-top:6px;color:#7fbf7f">Приёмы: ${ma.moves.map(m=>m.key).join(', ') || '—'}</div>`;

  document.getElementById('cb-package').innerHTML =
    (CB.package || []).map(k => `<span class="stat-chip">${k}</span>`).join('');

  const owned = cbOwned();
  document.getElementById('cb-shop').innerHTML = CB.catalog
    .filter(i => i.category === CB_CAT && !owned.includes(i.key))
    .map(i => `<div style="display:flex;gap:8px;align-items:center;margin:3px 0">
        <span style="flex:1">${i.name}${i.damage?' · '+i.damage:''}${i.sp?' · SP'+i.sp:''}${i.hl?' · HL'+i.hl:''}</span>
        <span style="color:${i.source==='book'?'#7fbf7f':'#c9a227'}">${i.price} eb</span>
        <button class="secondary mini" onclick="cbBuy('${i.key}')">Купить</button>
      </div>`).join('') || '<span style="color:#888">Всё куплено</span>';

  document.getElementById('cb-cart').innerHTML = s.purchases.length
    ? s.purchases.map(k => `<span class="stat-chip">${k}
        <button class="secondary mini" onclick="cbSell('${k}')">×</button></span>`).join('')
    : '<span style="color:#888">Ничего не куплено</span>';

  const cat = k => (CB.catalog.find(i => i.key === k) || {}).category;
  document.getElementById('cb-weapon').innerHTML =
    owned.filter(k => cat(k) === 'weapon').map(w => `<option ${w===s.weapon?'selected':''}>${w}</option>`).join('');
  document.getElementById('cb-armor').innerHTML =
    owned.filter(k => cat(k) === 'armor').map(a => `<option ${a===s.armor?'selected':''}>${a}</option>`).join('');
}

function cbBuy(k) {
  const item = CB.catalog.find(i => i.key === k);
  if (!item) return;
  if (cbSpent() + item.price > CB.budget) { alert('Не хватает eb'); return; }
  CB.spec.purchases.push(k); cbRender();
}
function cbSell(k) { CB.spec.purchases = CB.spec.purchases.filter(x => x !== k); cbRender(); }

async function cbRollStats() {
  const r = await fetch('/creation/roll_stats', {method:'POST'});
  if (r.ok) { CB.spec.stats = await r.json(); cbRender(); }
}

function cbStat(k, d) {
  if (CB.stat_pool === null || CB.stat_pool === undefined) return;
  const s = CB.spec.stats, used = Object.values(s).reduce((a,b)=>a+b,0);
  const nv = (s[k]||0) + d;
  if (nv < CB.stat_min || nv > CB.stat_max) return;
  if (d > 0 && used >= CB.stat_pool) return;
  s[k] = nv; cbRender();
}

function cbSkill(k, d) {
  if (CB.skill_pool === null || CB.skill_pool === undefined) return;
  const base = (CB.skills.find(x => x.key === k) || {}).baseline || 0;
  const nv = (CB.spec.skills[k] || 0) + d;
  if (nv < base || nv > CB.skill_max) return;
  if (d > 0 && cbDelta() >= CB.skill_pool) return;
  CB.spec.skills[k] = nv; cbRender();
}

async function cbBuild() {
  if (!CB) return;
  CB.spec.weapon = document.getElementById('cb-weapon').value || CB.spec.weapon;
  CB.spec.armor = document.getElementById('cb-armor').value || CB.spec.armor;
  CB.spec.name = document.getElementById('cs-name').textContent;
  CB.spec.method = CB.method;
  const r = await fetch('/creation/build', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify(CB.spec)});
  if (!r.ok) { const e = await r.json().catch(()=>({})); alert(e.detail || 'Ошибка сборки'); return; }
  pendingChar = await r.json();
  renderCharPreview();
}

'''

a = s.find('<div id="cs-full"')
b = s.find('<div id="cs-preview"')
assert a > 0 and b > a, "не найден блок cs-full / cs-preview"
s = s[:a] + HTML + s[b:]
print("index.html: блок cs-full заменён")

a = s.find('async function cbLoad()')
b = s.find('function renderCharPreview()')
assert a > 0 and b > a, "не найден JS-регион билдера"
s = s[:a] + JS + s[b:]
print("index.html: JS билдера заменён")

if 'button.mini' not in s:
    s = s.replace('  .row { display: flex;',
                  '  button.mini { padding: 0 7px; font-size: 0.9em; }\n'
                  '  .book-note { color: #7fbf7f; font-size: 0.78em; margin: 4px 0; }\n'
                  '  .row { display: flex;')
    print("index.html: +стили mini/book-note")

p.write_text(s, encoding="utf-8")