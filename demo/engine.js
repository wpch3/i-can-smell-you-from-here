/* 我在这儿就能为你下厨了 — 网页 Demo 内核
 * 读取 tools/rpy2json.py 从 exe 版剧本转出的 story.json，
 * 因此两边的内容、分支、变量完全一致。
 */
(() => {
  'use strict';

  // ---------------------------------------------------------------- 资源
  const IMG = {
    kv: '../icancook/game/images/key_visual.jpg',
    bistro: '../icancook/game/images/bg_bistro.jpg',
    vig: '../icancook/game/images/vignette.png',
  };
  const SPRITE_DIR = '../icancook/game/images/idimya/';

  // ---------------------------------------------------------------- 音效
  // 没有音频素材，用 WebAudio 合成；她的声音与旁白用不同滤波，产生「她在场」的听觉差异
  let AC = null;
  function ac() {
    if (!AC) {
      const C = window.AudioContext || window.webkitAudioContext;
      if (!C) return null;
      AC = new C();
    }
    if (AC.state === 'suspended') AC.resume();
    return AC;
  }
  function ambience() {
    const c = ac(); if (!c) return;
    // 房间底噪：低通白噪
    const buf = c.createBuffer(1, c.sampleRate * 4, c.sampleRate);
    const d = buf.getChannelData(0);
    let last = 0;
    for (let i = 0; i < d.length; i++) {
      const w = Math.random() * 2 - 1;
      last = (last + 0.02 * w) / 1.02;
      d[i] = last * 3.2;
    }
    const src = c.createBufferSource(); src.buffer = buf; src.loop = true;
    const lp = c.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 420;
    const g = c.createGain(); g.gain.value = 0.05;
    src.connect(lp); lp.connect(g); g.connect(c.destination);
    src.start();
    window.__amb = { g, lp };
  }
  function herVoice() {
    // 她说话时：环境音压低（听觉上的「聚光」）
    const a = window.__amb; if (!a) return;
    a.g.gain.cancelScheduledValues(a.g.currentTime);
    a.g.gain.linearRampToValueAtTime(0.018, a.g.currentTime + 0.25);
  }
  function normalVoice() {
    const a = window.__amb; if (!a) return;
    a.g.gain.cancelScheduledValues(a.g.currentTime);
    a.g.gain.linearRampToValueAtTime(0.05, a.g.currentTime + 0.4);
  }
  function blip(kind) {
    const c = ac(); if (!c) return;
    const t = c.currentTime;
    const o = c.createOscillator();
    const g = c.createGain();
    o.type = 'sine';
    const f = kind === 'idimya' ? 320 : kind === 'note' ? 150 : 200;
    o.frequency.setValueAtTime(f, t);
    o.frequency.exponentialRampToValueAtTime(f * 0.72, t + 0.12);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.055, t + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.16);
    o.connect(g); g.connect(c.destination);
    o.start(t); o.stop(t + 0.18);
  }
  function candleCrackle() {
    const c = ac(); if (!c) return;
    const t = c.currentTime;
    const buf = c.createBuffer(1, 900, c.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / 900, 6);
    const src = c.createBufferSource(); src.buffer = buf;
    const bp = c.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 1800; bp.Q.value = 1.4;
    const g = c.createGain(); g.gain.value = 0.09;
    src.connect(bp); bp.connect(g); g.connect(c.destination);
    src.start(t);
  }

  const $ = (s) => document.querySelector(s);
  const el = {
    stage: $('#stage'),
    bg: $('#bg'),
    char: $('#char'),
    charInner: $('#charInner'),
    lid: $('#lid'),
    vig: $('#vig'),
    box: $('#box'),
    who: $('#who'),
    text: $('#text'),
    next: $('#next'),
    choices: $('#choices'),
    center: $('#center'),
    smell: $('#smell'),
    title: $('#title'),
    startBtn: $('#startBtn'),
    endList: $('#endList'),
    history: $('#history'),
    historyList: $('#historyList'),
    closeHistory: $('#closeHistory'),
    quick: $('#quick'),
  };

  const SPRITE = {
    ready: false,
    sheet: null,          // Image
    cell: { w: 584, h: 1304 },
    frames: {},           // name -> [x,y,w,h]
    blink: null,          // Image
    name: 'calm',
    blinkTimer: null,
    blinkUntil: 0,
  };

  window.__spriteDebug = () => ({ ready: SPRITE.ready, frames: Object.keys(SPRITE.frames||{}), sheet: !!SPRITE.sheet });

  function loadSprite() {
    SPRITE.frames = SPRITE.frames || {};
    fetch(SPRITE_DIR + 'sheet.json')
      .then((r) => r.json())
      .then((m) => {
        SPRITE.cell = m.cell;
        SPRITE.frames = m.frames;
        const sheet = new Image();
        sheet.onload = () => { SPRITE.sheet = sheet; SPRITE.ready = true; };
        sheet.src = SPRITE_DIR + m.image;
        const bl = new Image();
        bl.onload = () => { SPRITE.blink = bl; };
        bl.src = SPRITE_DIR + m.blink_patch.file;
      })
      .catch((e) => console.warn('立绘表加载失败', e));
  }

  function setExpression(name) {
    if (!SPRITE.frames || !SPRITE.frames[name]) name = 'calm';
    SPRITE.name = name;
    paintSprite();
  }

  function paintSprite() {
    if (!SPRITE.ready) return;
    const f = SPRITE.frames[SPRITE.name] || SPRITE.frames.calm;
    const { w, h } = SPRITE.cell;
    // 用舞台高度的比例定尺寸：立绘高度 ≈ 舞台 92%
    const stageH = el.stage.clientHeight || 1080;
    const scale = (stageH * 0.92) / h;
    el.char.style.width = Math.round(w * scale) + 'px';
    el.char.style.height = Math.round(stageH * 0.92) + 'px';
    el.charInner.style.width = '100%';
    el.charInner.style.height = '100%';
    el.charInner.style.backgroundImage = `url("${SPRITE_DIR}sheet.png")`;
    el.charInner.style.backgroundSize =
      `${Math.round(w * Object.keys(SPRITE.frames).length * scale)}px ${Math.round(h * scale)}px`;
    el.charInner.style.backgroundPosition =
      `${-Math.round(f[0] * scale)}px ${-Math.round(f[1] * scale)}px`;
  }

  // 眨眼：每 3~7 秒一次，闭上 110ms
  function startBlink() {
    clearInterval(SPRITE.blinkTimer);
    SPRITE.blinkTimer = setInterval(() => {
      if (!SPRITE.ready || !SPRITE.blink) return;
      const now = performance.now();
      if (now < SPRITE.blinkUntil) return;
      SPRITE.blinkUntil = now + 110;
      el.lid.classList.add('closed');
      setTimeout(() => el.lid.classList.remove('closed'), 110);
    }, 1200 + Math.random() * 1500);
  }

  // 呼吸：极慢的上下浮动 + 极轻微缩放
  function startBreath() {
    const t0 = performance.now();
    const loop = () => {
      const t = (performance.now() - t0) / 1000;
      const y = Math.sin(t / 2.6) * 2.4;
      const sc = 1 + Math.sin(t / 2.6) * 0.0035;
      el.charInner.style.transform = `translateY(${y}px) scale(${sc})`;
      requestAnimationFrame(loop);
    };
    loop();
  }

  let story = null;
  let S = null;            // 运行时状态
  let typing = null;       // 打字机计时器
  let typingResolve = null;// 被打断时用来兑现 typeText 的 promise
  let full = '';           // 当前台词全文
  let waiting = null;      // 等待玩家点击的 resolve
  let autoTimer = null;
  let skipping = false;

  const SAVE_KEY = 'icancook.demo.v1';

  // ---------------------------------------------------------------- 工具
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));

  function loadStore() {
    try { return JSON.parse(localStorage.getItem(SAVE_KEY)) || {}; }
    catch { return {}; }
  }
  function saveStore(o) {
    try { localStorage.setItem(SAVE_KEY, JSON.stringify(o)); } catch {}
  }

  /** Ren'Py 风格的小标记：{color=#xxx} {size=NN} {/color} {/size} \n */
  function renderMarkup(s) {
    let out = s
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/\\n/g, '<br>')
      .replace(/\n/g, '<br>');
    out = out.replace(/\{color=([^}]+)\}/g, '<span style="color:$1">')
             .replace(/\{\/color\}/g, '</span>')
             .replace(/\{size=(\d+)\}/g, '<span style="font-size:$1px">')
             .replace(/\{\/size\}/g, '</span>')
             .replace(/\{b\}/g, '<b>').replace(/\{\/b\}/g, '</b>');
    return out;
  }

  /** 变量取值 / 赋值（把 .rpy 里的 Python 片段当 JS 跑） */
  function evalExpr(expr) {
    const keys = Object.keys(S.vars);
    try {
      // eslint-disable-next-line no-new-func
      return new Function(...keys, `return (${expr});`)(...keys.map((k) => S.vars[k]));
    } catch (e) {
      console.warn('expr failed:', expr, e);
      return undefined;
    }
  }

  function runSet(expr) {
    let m = expr.match(/^(\w+)\s*\+=\s*(.+)$/);
    if (m) { S.vars[m[1]] = (S.vars[m[1]] || 0) + Number(evalExpr(m[2])); return; }
    m = expr.match(/^(\w+)\s*-=\s*(.+)$/);
    if (m) { S.vars[m[1]] = (S.vars[m[1]] || 0) - Number(evalExpr(m[2])); return; }
    m = expr.match(/^(\w+)\s*=\s*(.+)$/);
    if (m) { S.vars[m[1]] = evalExpr(m[2]); return; }
    console.warn('unhandled set:', expr);
  }

  function fillPlaceholders(s) {
    return s.replace(/\[(\w+)\]/g, (_, k) => (S.vars[k] == null ? '' : String(S.vars[k])));
  }

  // ---------------------------------------------------------------- 打字机
  function typeText(raw) {
    full = fillPlaceholders(raw);
    el.box.classList.remove('empty');
    if (typing) { clearInterval(typing); typing = null; }
    if (typingResolve) { const r = typingResolve; typingResolve = null; r(); }

    const html = renderMarkup(full);
    const hasMarkup = html.includes('<span') || html.includes('<br');

    // 含样式标记的台词整段显示，避免拆坏标签
    if (hasMarkup || S.textSpeed <= 0) {
      el.text.innerHTML = html;
      return Promise.resolve();
    }

    let i = 0;
    el.text.textContent = '';
    return new Promise((resolve) => {
      typingResolve = resolve;
      typing = setInterval(() => {
        i += 1;
        if (i % 2 === 0 && !skipping) blip(curSpeaker);
        el.text.textContent = full.slice(0, i);
        if (i >= full.length) {
          clearInterval(typing); typing = null;
          typingResolve = null;
          resolve();
        }
      }, S.textSpeed);
    });
  }

  /** 玩家在打字过程中点击：立刻补完，并且必须兑现 promise（否则剧本会卡住） */
  function finishTyping() {
    if (!typing) return false;
    clearInterval(typing);
    typing = null;
    el.text.textContent = full;
    if (typingResolve) { const r = typingResolve; typingResolve = null; r(); }
    return true;
  }

  // ---------------------------------------------------------------- 等待推进
  function waitAdvance() {
    return new Promise((resolve) => { waiting = resolve; });
  }

  function advance() {
    if (waiting) { const w = waiting; waiting = null; w(); }
  }

  // ---------------------------------------------------------------- 演出
  const TRANSFORMS = {
    push_slow: { dur: 26000, scale: 1.05 },
    lean_in: { dur: 1600, scale: 1.12, shiftY: 0 },
    lean_back: { dur: 900, scale: 1.0, shiftY: 0 },
  };

  function applyTransform(name, dur) {
    const t = TRANSFORMS[name] || TRANSFORMS.push_slow;
    const e = el.char;
    e.style.transition =
      `transform ${dur != null ? dur : t.dur / 1000}s cubic-bezier(.22,.61,.36,1), opacity .8s`;
    e.style.transformOrigin = '50% 100%';
    e.style.transform = `translate(-50%, ${t.shiftY || 0}%) scale(${t.scale})`;
  }

  function candleBreath() {
    // 烛光呼吸：轻微明暗起伏
    const k = 0.94 + Math.sin(Date.now() / 900) * 0.02;
    el.char.style.filter = `brightness(${k}) saturate(1.02)`;
    requestAnimationFrame(candleBreath);
  }

  // ---------------------------------------------------------------- 剧本执行
  async function runLabel(name, pc = 0) {
    S.label = name;
    S.pc = pc;
    const code = story.labels[name];
    if (!code) { console.error('missing label', name); return; }

    let guard = 0;
    while (S.pc < code.length) {
      if (++guard > 5000) { console.error('infinite loop at', name, S.pc); return; }
      const ins = code[S.pc];
      S.pc += 1;
      if (window.__debug) console.log(`[${name}:${S.pc - 1}]`, ins.op, (ins.text || ins.cond || ins.expr || ins.label || ins.name || '').toString().slice(0, 40));

      switch (ins.op) {
        case 'say': {
          if (skipping) { await wait(30); break; }
          showSpeaker(ins.who);
          const done = typeText(ins.text);
          await done;
          pushHistory(ins.who, fillPlaceholders(ins.text));
          await waitAdvance();
          break;
        }
        case 'scene': {
          if (ins.img === 'black') {
            el.bg.style.filter = 'brightness(.35) saturate(.7)';
          } else {
            el.bg.style.filter = 'none';
            setScene(ins.img);
          }
          break;
        }
        case 'show': {
          const parts = (ins.img || '').split(/\s+/);
          if (parts[0] === 'idimya') {
            setExpression(parts[1] || 'calm');
            el.char.style.opacity = '1';
            applyTransform(ins.at, ins.at === 'lean_in' ? 900 : 500);
          } else if (parts[0] === 'vig') {
            el.vig.style.opacity = '1';
          }
          break;
        }
        case 'with': {
          await wait(Math.min(ins.dur, 1.2) * 1000);
          break;
        }
        case 'set': {
          runSet(ins.expr);
          break;
        }
        case 'if': {
          const ok = evalExpr(ins.cond);
          S.pc = ok ? ins.pc : ins.else_pc;
          break;
        }
        case 'jump': {
          if (ins.label) { return runLabel(ins.label); }
          S.pc = ins.pc;
          break;
        }
        case 'menu': {
          const choice = await showChoices(ins.options);
          S.pc = choice;
          break;
        }
        case 'screen': {
          await openSmellScreen();
          break;
        }
        case 'centered': {
          await showCentered(ins.text);
          break;
        }
        case 'unlock': {
          const st = loadStore();
          st[ins.flag] = true;
          saveStore(st);
          break;
        }
        case 'return':
        case 'end':
        default:
          return;
      }
    }
  }

  // ---------------------------------------------------------------- UI
  const SPEAKERS = {
    idimya: { name: '伊迪米娅', cls: 'idimya' },
    n: { name: '', cls: 'you' },
    note: { name: '', cls: 'note' },
  };

  let curSpeaker = 'note';

  function showSpeaker(who) {
    curSpeaker = who;
    if (who === 'idimya') herVoice(); else normalVoice();
    const sp = SPEAKERS[who] || { name: '', cls: 'note' };
    el.who.textContent = sp.name;
    el.who.className = sp.name ? 'who ' + sp.cls : 'who';
    el.text.className = 'text ' + sp.cls;
  }

  function checkImage(url) {
    const im = new Image();
    im.onerror = () => {
      console.error('背景图加载失败:', url);
      const tip = document.createElement('div');
      tip.style.cssText = 'position:absolute;left:50%;top:12%;transform:translateX(-50%);' +
        'font-size:1.6cqh;color:#d9a05f;background:rgba(10,7,4,.9);padding:1cqh 1.6cqw;z-index:99';
      tip.textContent = '背景图没取到：' + url + '（请用仓库根目录起 http 服务，或直接访问 /demo/）';
      el.stage.appendChild(tip);
    };
    im.src = url;
  }

  function setScene(img) {
    if (img === 'black') {
      el.bg.style.opacity = '0';
      el.char.style.opacity = '0';
      el.vig.style.opacity = '0.9';
      return;
    }
    el.bg.style.opacity = '1';
    el.vig.style.opacity = '1';
    // kv 与 bg 是同一张图：bg 作为静态底，char 承担推近演出
    const url = IMG[img] || IMG.kv;
    if (el.bg.dataset.src !== url) {
      el.bg.dataset.src = url;
      el.bg.style.backgroundImage = `url("${url}")`;
      checkImage(url);
    }
  }

  function showChoices(options) {
    return new Promise((resolve) => {
      el.choices.innerHTML = '';
      el.choices.classList.add('show');
      el.next.classList.add('hide');
      options.forEach((o, i) => {
        const b = document.createElement('button');
        b.className = 'choice';
        b.style.animationDelay = `${i * 90}ms`;
        b.innerHTML = `<span class="bar"></span><span class="label">${renderMarkup(fillPlaceholders(o.text))}</span>`;
        b.addEventListener('click', () => {
          el.choices.classList.remove('show');
          el.choices.innerHTML = '';
          el.next.classList.remove('hide');
          resolve(o.pc);
        });
        el.choices.appendChild(b);
      });
    });
  }

  function showCentered(raw) {
    return new Promise((resolve) => {
      el.center.innerHTML = `<div class="centerText">${renderMarkup(fillPlaceholders(raw))}</div>`;
      el.box.classList.add('empty');
      el.center.classList.add('show');
      window.__centerAdvance = () => {
        window.__centerAdvance = null;
        el.center.classList.remove('show');
        el.box.classList.remove('empty');
        resolve();
      };
    });
  }

  function pushHistory(who, text) {
    const sp = SPEAKERS[who];
    const name = sp && sp.name ? sp.name : '';
    S.history.push({ name, text });
    if (S.history.length > 200) S.history.shift();
    renderHistory();
  }

  function renderHistory() {
    el.historyList.innerHTML = S.history
      .map((h) => `<div class="hrow"><div class="hname">${h.name}</div><div class="htext">${renderMarkup(h.text)}</div></div>`)
      .join('');
    el.historyList.scrollTop = el.historyList.scrollHeight;
  }

  // ---------------------------------------------------------------- 嗅觉交互
  const SMELLS = {
    candle: {
      x: 0.40, y: 0.80, w: 0.1, h: 0.2,
      label: '烛台',
      note: '蜡油、旧火、还有一点铁。',
      line: '蜡油。烧过很多次了，每次都是同一支。她大概从来不换。',
    },
    notebook: {
      x: 0.66, y: 0.88, w: 0.12, h: 0.12,
      label: '笔记本',
      note: '皮革、纸、干了很久的甜。',
      line: '皮面的本子，压着一股很淡的甜味。翻过很多次，边角是软的。',
    },
    hand: {
      x: 0.50, y: 0.70, w: 0.14, h: 0.14,
      label: '她的手',
      note: '体温、皂、干净的皮肤。',
      line: '她的手腕上没有香水。只有体温，和一点洗涤剂的味道。',
    },
    air: {
      x: 0.06, y: 0.18, w: 0.1, h: 0.14,
      label: '空气',
      note: '铁锈。很新鲜的那种铁锈。',
      line: '空气里有别的东西。不是这桌的。是走廊深处飘过来的。',
    },
  };

  function openSmellScreen() {
    return new Promise((resolve) => {
      const seen = new Set();
      el.smell.innerHTML = '';
      el.smell.classList.add('show');

      const head = document.createElement('div');
      head.className = 'smellHead';
      head.innerHTML = '<div class="t">嗅</div><div class="s">把光标移到桌上的东西上，点一下，直到气味浮上来。</div>';
      el.smell.appendChild(head);

      const info = document.createElement('div');
      info.className = 'smellInfo';
      info.innerHTML = '<div class="note"></div><div class="line"></div>';
      el.smell.appendChild(info);

      const counter = document.createElement('div');
      counter.className = 'smellCount';
      counter.textContent = '闻到 0 / 4';
      el.smell.appendChild(counter);

      Object.entries(SMELLS).forEach(([key, s]) => {
        const b = document.createElement('button');
        b.className = 'hotspot';
        b.style.left = `${s.x * 100}%`;
        b.style.top = `${s.y * 100}%`;
        b.style.width = `${s.w * 100}%`;
        b.style.height = `${s.h * 100}%`;
        b.innerHTML = `<span>${s.label}</span>`;
        b.addEventListener('click', () => {
          seen.add(key);
          info.querySelector('.note').textContent = s.note;
          info.querySelector('.line').textContent = s.line;
          info.classList.add('show');
          b.classList.add('seen');
          counter.textContent = `闻到 ${seen.size} / 4`;
          if (seen.size === 4) {
            counter.textContent = '闻到 4 / 4 · 你已经知道得够多了';
            counter.classList.add('full');
          }
          // 同步给剧本变量，让 [smell_line] 与 if smells_found >= 3 生效
          S.vars.smells_found = seen.size;
          S.vars.smell_line = s.line;
        });
        el.smell.appendChild(b);
      });

      const leave = document.createElement('button');
      leave.className = 'leave';
      leave.textContent = '起身';
      leave.addEventListener('click', () => {
        el.smell.classList.remove('show');
        if (S.vars.smells_found == null) S.vars.smells_found = seen.size;
        if (!S.vars.smell_line) S.vars.smell_line = '桌面只是桌面。';
        resolve();
      });
      el.smell.appendChild(leave);
    });
  }

  // ---------------------------------------------------------------- 输入
  function onAdvanceInput(e) {
    if (el.smell.classList.contains('show')) return;
    if (el.choices.classList.contains('show')) return;
    if (el.history.classList.contains('show')) return;
    if (window.__centerAdvance) { window.__centerAdvance(); return; }
    if (finishTyping()) return;   // 先补完当前句
    advance();
  }

  el.stage.addEventListener('click', onAdvanceInput);
  window.addEventListener('keydown', (e) => {
    if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); onAdvanceInput(e); }
    if (e.key === 'Control') { skipping = true; }
    if (e.key === 'h' || e.key === 'H') toggleHistory();
    if (e.key === 'Escape') el.history.classList.remove('show');
  });
  window.addEventListener('keyup', (e) => { if (e.key === 'Control') skipping = false; });

  function toggleHistory() {
    el.history.classList.toggle('show');
    if (el.history.classList.contains('show')) renderHistory();
  }
  el.quick.addEventListener('click', (e) => {
    const act = e.target.dataset.act;
    if (act === 'history') toggleHistory();
    if (act === 'skip') skipping = !skipping;
    if (act === 'restart') { if (confirm('重新开始？')) location.reload(); }
  });
  el.closeHistory.addEventListener('click', () => el.history.classList.remove('show'));

  // ---------------------------------------------------------------- 启动
  async function boot() {
    const res = await fetch('story.json');
    story = await res.json();

    S = {
      vars: JSON.parse(JSON.stringify(story.defaults)),
      history: [],
      label: 'start',
      pc: 0,
      textSpeed: new URLSearchParams(location.search).has('fast') ? 4 : 26,
      running: false,
    };
    S.vars.smells_found = 0;
    S.vars.smell_line = '';

    if (!new URLSearchParams(location.search).has('nosprite')) loadSprite();
    startBlink();
    startBreath();
    renderEndings();
    requestAnimationFrame(candleBreath);
    setInterval(() => { if (S.running) candleCrackle(); }, 5200 + Math.random() * 4000);
  }

  function renderEndings() {
    const st = loadStore();
    const list = [
      ['endings_lie', 'A · 她记住了你的谎话'],
      ['endings_name', 'B · 她记住了你的名字'],
      ['endings_scent', 'C · 她记住了你的味道'],
    ];
    el.endList.innerHTML = list
      .map(([k, t]) => `<li class="${st[k] ? 'got' : ''}">${st[k] ? '◆' : '◇'} ${t}</li>`)
      .join('');
  }

  el.startBtn.addEventListener('click', async () => {
    el.title.classList.add('hidden');
    await wait(400);
    el.stage.classList.add('playing');
    ambience();
    S.running = true;
    runLabel('start');
  });

  boot();
})();
