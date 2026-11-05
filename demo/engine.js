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
    kitchen: '../icancook/game/images/bg_kitchen.jpg',
    genkan: '../icancook/game/images/bg_genkan.jpg',
    morning: '../icancook/game/images/bg_morning.jpg',
    fridge: '../icancook/game/images/bg_fridge.jpg',
    kitchen_close: '../icancook/game/images/bg_kitchen_close.jpg',
    window_dawn: '../icancook/game/images/bg_window_dawn.jpg',
    vig: '../icancook/game/images/vignette.png',
    table_front: '../icancook/game/images/table_front.png',
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
  // 环境音音量：她说话时压低（听觉上的「聚光」），旁白时回来。
  // 这里直接操作 playAmb 建的那条 gain —— 不再另建一套合成底噪。
  const AMB_BASE = 0.32;
  function ambLevel(v, dur) {
    const c = ac(); if (!c || !ambGain) return;
    ambGain.gain.cancelScheduledValues(c.currentTime);
    ambGain.gain.linearRampToValueAtTime(v, c.currentTime + dur);
  }
  function herVoice() { ambLevel(AMB_BASE * 0.42, 0.28); }
  function normalVoice() { ambLevel(AMB_BASE, 0.45); }
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

  // ---------------------------------------------------------------- 真实音频（用 exe 版同一批 wav）
  const AUDIO_DIR = '../icancook/game/audio/';
  const bufCache = {};
  let ambNode = null, ambGain = null, ambTarget = null;

  // 音频永远不能拖住剧本：给整个加载过程设 4 秒上限，超时就当没有这条声音。
  // （真实浏览器里 decodeAudioData 在页面被后台化、或 wav 损坏时可能永不 resolve）
  function withTimeout(p, ms, fallback = null) {
    return Promise.race([p, new Promise((r) => setTimeout(() => r(fallback), ms))]);
  }

  async function loadBuf(name) {
    if (bufCache[name]) return bufCache[name];
    const c = ac(); if (!c) return null;
    try {
      return await withTimeout((async () => {
        const r = await fetch(AUDIO_DIR + name + '.wav');
        const ab = await r.arrayBuffer();
        bufCache[name] = await c.decodeAudioData(ab);
        return bufCache[name];
      })(), 4000);
    } catch (e) {
      console.warn('音频加载失败', name, e);
      return null;
    }
  }

  async function playAmb(name, fade = 2.0) {
    const c = ac(); if (!c) return;
    if (ambTarget === name) return;
    ambTarget = name;
    const buf = await loadBuf(name);
    if (ambTarget !== name) return;          // 加载期间又被切换了
    // 旧的那条淡出
    if (ambNode) {
      const old = ambNode, og = ambGain;
      const t = c.currentTime;
      og.gain.cancelScheduledValues(t);
      og.gain.setValueAtTime(og.gain.value, t);
      og.gain.linearRampToValueAtTime(0.0001, t + fade);
      try { old.stop(t + fade + 0.05); } catch (e) { /* 已停 */ }
    }
    if (!buf) { ambNode = null; ambGain = null; return; }
    const src = c.createBufferSource();
    src.buffer = buf; src.loop = true;
    const g = c.createGain();
    g.gain.setValueAtTime(0.0001, c.currentTime);
    g.gain.linearRampToValueAtTime(AMB_BASE, c.currentTime + fade);
    src.connect(g); g.connect(c.destination);
    src.start();
    ambNode = src; ambGain = g;
  }

  function stopAmb(fade = 2.0) {
    const c = ac(); if (!c || !ambNode) { ambTarget = null; return; }
    const t = c.currentTime;
    ambGain.gain.cancelScheduledValues(t);
    ambGain.gain.setValueAtTime(ambGain.gain.value, t);
    ambGain.gain.linearRampToValueAtTime(0.0001, t + fade);
    try { ambNode.stop(t + fade + 0.05); } catch (e) { /* 已停 */ }
    ambNode = null; ambGain = null; ambTarget = null;
  }

  async function playSfx(name, vol = 0.5) {
    const c = ac(); if (!c) return;
    const buf = await loadBuf(name);
    if (!buf) return;
    const src = c.createBufferSource();
    src.buffer = buf;
    const g = c.createGain(); g.gain.value = vol;
    src.connect(g); g.connect(c.destination);
    src.start();
  }

  // 玩家遇到问题时要能自己确认「拿到的是哪一版」：F12 里会看到这行，标题页角落也有版本号。
  // 之前那个「点进去一片黑」的 bug 有相当概率是浏览器缓存造成的误报，先排除这个变量。
  const VERSION = '0.6.1';
  console.info(`她记住的方式 · 网页 Demo v${VERSION}`);
  const verEl = document.getElementById('ver');
  if (verEl) verEl.textContent = `v${VERSION}`;

  /**
   * 所有静态资源都挂上版本号。
   *
   * 用户反复报"网页版打不开/进去一片黑"，而我在真实 Chromium 里每次都能跑通 ——
   * 这类"我这边好了你那边没好"的十条里有九条是缓存：浏览器死死记住旧的
   * engine.js / story.json / 立绘表，于是新代码永远不生效，玩家却以为坏了。
   * 挂上 VERSION 之后，任何一次发版都会强制重新拉取，症状再也不会因为缓存复发。
   */
  const CACHE_BUST = '?v=' + VERSION;
  const asset = (u) => (u.includes('?') ? u : u + CACHE_BUST);

  const $ = (s) => document.querySelector(s);
  const el = {
    stage: $('#stage'),
    barTop: $('#barTop'),
    barBottom: $('#barBottom'),
    bg: $('#bg'),
    kv: $('#kv'),
    table: $('#table'),
    char: $('#char'),
    charBase: $('#charBase'),
    charBody: $('#charBody'),
    charInner: $('#charInner'),
    lid: $('#lid'),
    layerHair: $('#layerHair'),
    // 刘海层必须和底图里的头发**逐像素对齐**：错一个像素就是双轮廓
    layerHairUnder: $('#layerHairUnder'),
    layerScarf: $('#layerScarf'),
    layerSpec: $('#layerSpec'),
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

  window.__spriteDebug = () => ({ ready: SPRITE.ready, frames: Object.keys(SPRITE.frames || {}), sheet: !!SPRITE.sheet });
  window.__setExpr = (n) => setExpression(n);
  // 调试/汇报用：F12 里可以手动切场景与摆位，方便截图定位构图问题
  window.__scene = (n) => setScene(n);
  window.__layout = (m) => setLayout(m);
  window.__at = (a, d) => applyTransform(a, d);

  function loadSprite() {
    SPRITE.frames = SPRITE.frames || {};
    fetch(asset(SPRITE_DIR + 'sheet.json'))
      .then((r) => r.json())
      .then((m) => {
        SPRITE.cell = m.cell;
        SPRITE.frames = m.frames;
        SPRITE.cols = m.cols || Object.keys(m.frames).length;
        SPRITE.rows = m.rows || 1;
        const sheet = new Image();
        sheet.onload = () => { SPRITE.sheet = sheet; SPRITE.ready = true; };
        sheet.src = asset(SPRITE_DIR + m.image);
        // sheet.json 里 blink_patch 是字符串（"blink_patch.png"）。
        // 旧代码读的是 .file → 请求 idimya/undefined，眨眼图层永远加载不到，
        // 网页版其实从来没眨过眼。这里两种写法都兼容。
        const blinkName = typeof m.blink_patch === 'string'
          ? m.blink_patch : (m.blink_patch && m.blink_patch.file);
        if (blinkName) {
          const bl = new Image();
          bl.onload = () => { SPRITE.blink = bl; };
          bl.src = asset(SPRITE_DIR + blinkName);
        }

        // L2 分层：同一格坐标系，直接叠
        //
        // 刘海要做两层：底层（不动）与上层（微小摆动）用的是**同一张切图**。
        // 切图是从原图复制出来的，原图里那份头发还留在 #charInner 上；
        // 如果只摆动一层，就会看到「双轮廓 / 部件重合」。
        // 底层负责把原图那份盖住，上层再动，重叠处永远是同一张画。
        const bangsUrl = `url("${asset(SPRITE_DIR + 'layers/layer_bangs.png')}")`;
        el.layerHair.style.backgroundImage = bangsUrl;
        if (el.layerHairUnder) el.layerHairUnder.style.backgroundImage = bangsUrl;
        el.layerScarf.style.backgroundImage = `url("${asset(SPRITE_DIR + 'layers/layer_scarf.png')}")`;
        el.layerSpec.style.backgroundImage = `url("${asset(SPRITE_DIR + 'layers/layer_spec.png')}")`;
      })
      .catch((e) => console.warn('立绘表加载失败', e));
  }

  function setExpression(name) {
    if (!SPRITE.frames || !SPRITE.frames[name]) name = 'base/calm';
    SPRITE.name = name;
    paintSprite();
  }

  /* ---------------------------------------------------------------- 摆位
   *
   * 立绘（sheet 的每一格）是**站姿全身**：头顶到膝盖下，1360px 高。
   * 原来引擎只有一种摆法 —— 「底边贴屏幕底、高度 = 舞台 92%」，
   * 结果在 bistro（圆桌、她是坐着的）这一场彻底崩了：
   *   · 她比桌子高一截，腰在桌沿之上，腿穿过整张桌面
   *   · 头顶顶出画面上沿，被切掉
   * 这两条都是用户当场指出来的（「人物超出了屏幕」「人物没有坐下」
   * 「人物超出了背景图层」）。
   *
   * 现在按背景分两种摆法：
   *
   *   seat  —— 她坐在桌后。缩放 / 位置全部从定稿反推，不是估的：
   *            assets/concept/key-visual-official.png 里，脖子处丝巾宽 338px、
   *            立绘里同一处只有 284px → 缩放比 1.190；再把丝巾上沿对齐
   *            （定稿 y=414 / 立绘 y=356）→ 顶端 y≈-46、中心 x≈976。
   *            下沿裁到竖屏也不会露出「截断的腿」的位置，
   *            剩下的交给前景桌面层 #table 遮住。
   *
   *   stand —— 她站在屋里（厨房/玄关/冰箱）。保持「底边贴地」，
   *            但高度改成 1.02 倍舞台高、且允许头顶出画一点点，
   *            因为她是站在离镜头很近的地方 —— 比原来 0.92 更压得住画面。
   */
  const LAYOUT = {
    // top 不是定稿的 -46，而是 120：遮幅有 120px 高，
    // 按定稿贴顶的话，她的头发正好被遮幅吃掉 —— 看起来就是「人物超出屏幕」。
    // 120 = 遮幅高度，等于让她「坐在遮幅下沿」起步，头顶留 70px 余量。
    seat: { zoom: 1.19, top: 44, cx: 976 },
    stand: { zoom: 0.92, bottom: 0, cx: 960 },
  };
  let layoutMode = 'stand';

  /** 切换摆位。座位场景（圆桌）用 seat，其余用 stand。 */
  function setLayout(mode) {
    const changed = layoutMode !== mode;
    layoutMode = mode;
    // 前景桌面只在这类「她坐在桌子后面」的场景出现。
    // 注意这里不能跟着下面的 early return 走：广角镜头（setKv）会把桌面收成 0，
    // 回到近景时必须重新置 1，否则她一直"没有桌子挡着"。
    syncTable();
    if (changed) paintSprite();
  }

  /** 桌面遮挡层的显隐：座位场景 + 不是广角镜头时才显示 */
  function syncTable() {
    if (!el.table) return;
    const on = layoutMode === 'seat' && !kvOn;
    el.table.style.opacity = on ? '1' : '0';
  }

  /** 按背景决定摆位：只有小酒馆是「圆桌 + 坐着」 */
  function layoutFor(sceneName) {
    return sceneName === 'bistro' || sceneName === 'kv' ? 'seat' : 'stand';
  }

  function paintSprite() {
    if (!SPRITE.ready) return;
    // 注意：SPRITE.frames 只有 "造型/表情" 形式的键（base/calm 等），
    // 原来这里兜底写的是 SPRITE.frames.calm —— 那个键不存在，
    // 于是 scene 触发的第一次 paintSprite 直接抛异常，
    // 整段剧本在 start 的第 2 条就停了。
    const f = SPRITE.frames[SPRITE.name] || SPRITE.frames['base/calm'];
    if (!f) return;
    const { w, h } = SPRITE.cell;
    const stageH = el.stage.clientHeight || 1080;
    const stageW = el.stage.clientWidth || 1920;
    const L = LAYOUT[layoutMode] || LAYOUT.stand;

    if (layoutMode === 'seat') {
      // 定稿坐标是 1920x1080 下的像素 → 按舞台高度等比换算
      const k = stageH / 1080;
      const dispH = h * L.zoom;
      const dispW = w * L.zoom;
      const cellScale = (dispH * k) / h;
      el.char.style.height = Math.round(dispH * k) + 'px';
      el.char.style.width = Math.round(dispW * k) + 'px';
      el.char.style.left = Math.round((L.cx - dispW / 2) * k) + 'px';
      el.char.style.top = Math.round(L.top * k) + 'px';
      el.char.style.bottom = 'auto';
      el.char.style.transform = baseTransform();   // 坐姿不用 transform 做位移
      el.charInner.style.width = '100%';
      el.charInner.style.height = '100%';
      el.charInner.style.backgroundImage = `url("${asset(SPRITE_DIR + 'sheet.png')}")`;
      el.charInner.style.backgroundSize =
        `${Math.round(w * SPRITE.cols * cellScale)}px ${Math.round(h * SPRITE.rows * cellScale)}px`;
      el.charInner.style.backgroundPosition =
        `${-Math.round(f[0] * cellScale)}px ${-Math.round(f[1] * cellScale)}px`;
      paintLayers();
      return;
    }

    // stand：底边贴屏幕底，高度 = 舞台 92%（头顶刚好留出遮幅的位置）
    const scale = (stageH * L.zoom) / h;
    el.char.style.width = Math.round(w * scale) + 'px';
    el.char.style.height = Math.round(h * scale) + 'px';
    el.char.style.left = '50%';
    el.char.style.top = 'auto';
    el.char.style.bottom = '0';
    el.char.style.transform = baseTransform();
    el.charInner.style.width = '100%';
    el.charInner.style.height = '100%';
    el.charInner.style.backgroundImage = `url("${asset(SPRITE_DIR + 'sheet.png')}")`;
    el.charInner.style.backgroundSize =
      `${Math.round(w * SPRITE.cols * scale)}px ${Math.round(h * SPRITE.rows * scale)}px`;
    el.charInner.style.backgroundPosition =
      `${-Math.round(f[0] * scale)}px ${-Math.round(f[1] * scale)}px`;
    paintLayers();
  }

  // L2 的三层只从 base/calm 切出来，换到别的造型时必须藏起来，
  // 否则会叠上一层「短发 + 蓝吊带」的刘海和丝巾，比不动还糟。
  function paintLayers() {
    const isBase = SPRITE.name.startsWith('base/');
    el.layerHair.style.display = el.layerScarf.style.display =
      el.layerSpec.style.display = isBase ? 'block' : 'none';
    if (el.layerHairUnder) el.layerHairUnder.style.display = isBase ? 'block' : 'none';
  }

  /* 眨眼：每 1.2~2.7 秒一次，闭上 110ms。
   *
   * 两层坑（都真机复现过）：
   *  ① blink_patch.png 原来是「眼皮横带 + 圆角矩形羽化」，框里还带着
   *     鼻子、脸颊和围巾的一部分 —— 眨眼时脸中央浮出一个方块，
   *     这就是用户看到的"闭眼部件重合"。
   *  ② #lid 是 #char 的直接子元素，而呼吸/视点变换写在 #charInner 上，
   *     所以眼睛在动、眼皮不动，两者永久性地相对漂移。
   *     现在把 #charInner + 三层 + #lid 一起装进 #charBody，
   *     呼吸/视点只动 #charBody —— 所有零件严格同一个坐标系。 */
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

  // 视点跟随 + 呼吸 + L2 分层摆动：合成一个 RAF 循环，避免多条循环互相覆盖 transform
  const gaze = { x: 0, y: 0 };
  function startLive() {
    const t0 = performance.now();
    let cx = 0, cy = 0;

    el.stage.addEventListener('mousemove', (e) => {
      const r = el.stage.getBoundingClientRect();
      gaze.x = ((e.clientX - r.left) / r.width - 0.5) * 2;
      gaze.y = ((e.clientY - r.top) / r.height - 0.5) * 2;
    });

    const loop = () => {
      const t = (performance.now() - t0) / 1000;
      cx += (gaze.x - cx) * 0.05;
      cy += (gaze.y - cy) * 0.05;

      const by = Math.sin(t / 2.6) * 2.4;                    // 呼吸位移
      const bs = 1 + Math.sin(t / 2.6) * 0.0035;             // 呼吸缩放
      // 呼吸 + 视点：整组一起动（立绘 / 刘海 / 丝巾 / 高光 / 眼皮）
      el.charBody.style.transform =
        `translate(${(cx * -1.2).toFixed(2)}%, ${(cy * -0.6 + by).toFixed(2)}%) scale(${bs.toFixed(4)})`;

      /* 刘海 / 丝巾：幅度必须小。
       *
       * 这两层是「从原图上抠下来的复制品」——原图里那份还在下面。
       * 只要位移超过 1~2 像素，就会看到两层错开的轮廓（重影），
       * 用户报的"部件错位"就是它。单靠加大羽化救不回来：
       * 羽化只让边缘变糊，轮廓仍然成双。
       * 所以这里把幅度压到 0.3% / 0.25deg 量级（≈1.5px），
       * 肉眼看不出重影，但能感觉到空气在动。 */
      const hSway = Math.sin(t / 2.7) * 0.30 + Math.sin(t / 1.13) * 0.10;
      const hTilt = Math.sin(t / 3.9) * 0.22;
      el.layerHair.style.transform =
        `translateX(${hSway.toFixed(2)}%) rotate(${hTilt.toFixed(2)}deg)`;

      const sSway = Math.sin((t - 0.6) / 3.4) * 0.55 + Math.sin((t - 0.3) / 1.9) * 0.16;
      const sTilt = Math.sin((t - 0.8) / 4.6) * 0.45;
      el.layerScarf.style.transform =
        `translate(${sSway.toFixed(2)}%, ${(Math.abs(sSway) * 0.10).toFixed(2)}%) rotate(${sTilt.toFixed(2)}deg)`;

      // 高光层：透明度呼吸，模拟烛光扫过
      el.layerSpec.style.opacity =
        (0.13 + Math.sin(t / 1.7) * 0.04 + Math.sin(t / 0.53) * 0.012).toFixed(3);

      // 循环类演出：rack（焦点漂移）与 throb（心跳）
      // Ren'Py 那边是 transform 的 repeat，这里每帧写一次即可。
      if (loopFx === 'rack') {
        const k = 0.5 - 0.5 * Math.cos((t % 4) / 4 * Math.PI * 2);   // 0→1→0
        const light = 0.94 + Math.sin(t / 0.9) * 0.02;   // 保留烛光呼吸
        el.char.style.filter =
          `blur(${(k * 2.2).toFixed(2)}px) brightness(${light.toFixed(3)}) saturate(1.02)`;
        el.char.style.transform = (layoutMode === 'seat'
          ? '' : 'translateX(-50%) ') + `scale(${(1 + k * 0.02).toFixed(4)})`;
      } else if (loopFx === 'throb') {
        const beat = Math.abs(Math.sin(t * Math.PI / 0.85));          // 双峰=心跳
        const dy = -(beat * 2).toFixed(2);
        el.char.style.transform = (layoutMode === 'seat'
          ? '' : 'translateX(-50%) ') + `translateY(${dy}px)`;
        const light = 0.94 + Math.sin(t / 0.9) * 0.02;
        el.char.style.filter = `brightness(${light.toFixed(3)}) saturate(1.02)`;
      }
      requestAnimationFrame(loop);
    };
    loop();
    startBlink();
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
    const keys = Object.keys(S.vars).filter((k) => /^[A-Za-z_]\w*$/.test(k));
    const safe = Object.fromEntries(keys.map((k) => [k, S.vars[k]]));
    // 剧本里的 persistent.xxx 判断（第一章的分支收束）——网页端用 localStorage 顶替
    safe.persistent = loadStore();
    try {
      // 用 with(vars) 而不是把变量名当形参：像 `_return` 这种 renpy 内置名
      // 作为形参名是合法的，但混进 Object.keys 顺序时容易踩到保留字/数字开头。
      // eslint-disable-next-line no-new-func
      return new Function('vars', `with (vars) { return (${expr}); }`)(safe);
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

    setNextHint(false);
    let i = 0;
    let hold = 0;          // 标点停顿：还要等几个 tick 才继续出字
    el.text.textContent = '';
    return new Promise((resolve) => {
      typingResolve = resolve;
      typing = setInterval(() => {
        if (hold > 0) { hold -= 1; return; }   // 停在半句上，像她真的在喘气
        i += 1;
        if (i % 2 === 0 && !skipping) blip(curSpeaker);
        el.text.textContent = full.slice(0, i);
        // 停顿节奏：省略号最长，破折号次之，逗号最短。
        // 这是"她说话慢"最省成本的实现——不要改语速，改停顿。
        const ch = full[i - 1];
        if (!skipping && S.textSpeed > 0) {
          if (ch === '…' || ch === '。') hold = 7;
          else if (ch === '—') hold = 5;
          else if (ch === '，' || ch === '、') hold = 3;
        }
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
  function setNextHint(on) {
    if (!el.next) return;
    el.next.classList.toggle('hide', !on);
  }

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
    // `at sprite_base` 单独出现 = 站着不动。Ren'Py 那边就是 zoom 0.92 常数，
    // 网页这边如果兜底成 push_slow，就会莫名其妙自己慢慢放大。
    none: { dur: 200, scale: 1.0, shiftY: 0 },
    // 循环类（Ren'Py 里是 repeat）：不加 transition，交给 RAF 每帧写。
    // rack = 焦点漂移（模糊呼吸），throb = 心跳位移。
    rack: { dur: 0, scale: 1.0, loop: 'rack' },
    throb: { dur: 0, scale: 1.0, loop: 'throb' },
  };

  /** 当前生效的循环演出（'rack' / 'throb' / null），由 startLive 的 RAF 读取 */
  let loopFx = null;

  /* Ren'Py 里 `show ... at sprite_base, lean_in` 会被原样转成
   * at="sprite_base, lean_in"（整串）。旧代码直接拿整串去查 TRANSFORMS，
   * 永远查不到 → 22 处 lean_in 全部退化成默认的 26 秒 push_slow，
   * 想表现"她凑近"的地方其实一点没动。
   * 这里把整串拆开，取第一个认识的演出名。 */
  function pickTransform(at) {
    if (!at) return 'push_slow';
    const names = String(at).split(',').map((x) => x.trim());
    for (const n of names) {
      const key = n.replace(/\(.*\)$/, '');       // bar_in_top(0.9) → bar_in_top
      if (TRANSFORMS[key]) return key;
    }
    // 只剩摆位锚点（sprite_base / sprite_seat）= 不动
    if (names.some((n) => n.startsWith('sprite_'))) return 'none';
    return 'push_slow';
  }

  function applyTransform(at, dur) {
    const t = TRANSFORMS[pickTransform(at)] || TRANSFORMS.push_slow;
    const e = el.char;
    if (t.loop) {
      loopFx = t.loop;
      e.style.transition = 'transform .6s ease, opacity .8s';
      e.style.transformOrigin = '50% 100%';
      // 循环类不改缩放，只保留底座变换
      e.style.transform = layoutMode === 'seat'
        ? 'none' : 'translateX(-50%) translateY(0%)';
      return;
    }
    loopFx = null;
    e.style.transition =
      `transform ${dur != null ? dur : t.dur / 1000}s cubic-bezier(.22,.61,.36,1), opacity .8s`;
    if (layoutMode === 'seat') {
      // 坐姿：位移由 left/top 决定，这里只叠缩放，且绕底边中心
      e.style.transformOrigin = '50% 100%';
      e.style.transform = `scale(${t.scale})`;
    } else {
      e.style.transformOrigin = '50% 100%';
      e.style.transform = `translateX(-50%) translateY(${t.shiftY || 0}%) scale(${t.scale})`;
    }
  }

  function baseTransform() {
    return layoutMode === 'seat' ? 'none' : 'translateX(-50%)';
  }

  function candleBreath() {
    // 烛光呼吸：轻微明暗起伏。
    // 有循环演出（rack/throb）在跑时让位 —— 两条 RAF 同时写 el.char.style.filter
    // 会互相覆盖，表现得像「眨眼/心跳时亮度乱跳」。
    if (!loopFx) {
      const k = 0.94 + Math.sin(Date.now() / 900) * 0.02;
      el.char.style.filter = `brightness(${k}) saturate(1.02)`;
    }
    requestAnimationFrame(candleBreath);
  }

  // ---------------------------------------------------------------- 剧本执行
  async function runLabel(name, pc = 0) {
    S.label = name;
    S.pc = pc;
    const code = story.labels[name];
    if (!code) { console.error('missing label', name); return; }

    let guard = 0;
    try {
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
          setNextHint(true);          // 文字出完了：告诉玩家"可以点了"
          await waitAdvance();
          setNextHint(false);
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
            // Ren'Py 写法：show idimya <造型> <表情>
            const group = parts[2] ? parts[1] : 'base';
            const face = parts[2] || parts[1] || 'calm';
            setExpression(`${group}/${face}`);
            el.char.style.opacity = '1';
            applyTransform(ins.at, ins.at === 'lean_in' ? 900 : 500);
          } else if (parts[0] === 'kv') {
            // 广角定稿：她坐在桌后，桌子挡住腰。开场先给这个全景。
            setKv(true);
          } else if (parts[0] === 'vig') {
            el.vig.style.opacity = '1';
          } else if (parts[0] === 'bar_top') {
            showBars('top');
          } else if (parts[0] === 'bar_bottom') {
            showBars('bottom');
          }
          break;
        }
        case 'hide': {
          const what = (ins.img || '').split(/\s+/)[0];
          if (what === 'kv') setKv(false);
          if (what === 'idimya') el.char.style.opacity = '0';
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
          if (ins.name && ins.name.startsWith('seasoning')) {
            // Ren'Py 的 `call screen X` 把按钮值放进 _return，
            // 剧本后面用 `if _return == "salt"` 判断，网页端要同样落到 S.vars
            S.vars._return = await openSeasonScreen();
          } else {
            await openSmellScreen();
          }
          break;
        }
        case 'centered': {
          await showCentered(ins.text);
          break;
        }
        case 'play': {
          if (ins.channel === 'ambience') {
            playAmb(ins.target, ins.fade || 2.0);
          } else {
            // sound / voice：一次性音效。Ren'Py 里是 audio.xxx 别名，
            // 转译后只剩 xxx，正好与 audio/xxx.wav 对应。
            const vols = {
              sfx_bell: 0.55, sfx_knife: 0.6, sfx_heartbeat: 0.5,
              sfx_breath_soft: 0.34, sfx_breath_catch: 0.42,
              sfx_cloth: 0.4, sfx_door: 0.5,
            };
            void vols;
            playSfx(ins.target, vols[ins.target] ?? 0.5);
          }
          break;
        }
        case 'stop': {
          if (ins.channel === 'ambience') stopAmb(ins.fade || 1.6);
          break;
        }
        case 'wait': {
          if (!new URLSearchParams(location.search).has('fast')) {
            await wait((ins.sec || 0.4) * 1000);
          }
          break;
        }
        case 'hide': {
          if (ins.img && String(ins.img).startsWith('bar_')) hideBars();
          break;
        }
        case 'unlock': {
          const st = loadStore();
          st[ins.flag] = true;
          saveStore(st);
          break;
        }
        case 'persist': {
          // `$ persistent.ch2_shared = True` 之类
          const st = loadStore();
          try {
            const val = evalExpr(ins.expr);
            st[ins.key] = val;
            saveStore(st);
          } catch (e) { /* 忽略 */ }
          break;
        }
        case 'return':
        case 'end':
        default:
          return;
      }
    }
    } catch (e) {
      // 剧本执行出异常时，绝对不要静默停住 —— 那和"卡死"对玩家来说没区别。
      console.error('剧本执行异常 @', name, S.pc, e && e.stack);
      showFatal(e, `${name} 第 ${S.pc} 条`);
    }
  }

  function showFatal(e, where) {
    let tip = document.getElementById('fatal');
    if (!tip) {
      tip = document.createElement('div');
      tip.id = 'fatal';
      tip.style.cssText = 'position:absolute;left:50%;top:8%;transform:translateX(-50%);'
        + 'max-width:80cqw;padding:1.6cqh 2cqw;z-index:999;'
        + 'background:rgba(40,10,8,.95);border:1px solid #a8443a;'
        + 'color:#e8dcc8;font-size:1.6cqh;line-height:1.7;white-space:pre-wrap';
      document.getElementById('stage').appendChild(tip);
    }
    tip.textContent = `剧本出错了（${where}）：${e && e.message ? e.message : e}\n`
      + '请把这段截给开发者；点这里继续。';
    tip.onclick = () => tip.remove();
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

  /* 广角镜头（key_visual）。
   * 定稿 key_visual 里她已经是「坐在桌后、桌子挡住腰」的完整构图，
   * 开场先播它，观众就先认定她坐下了；之后再切到立绘近景，
   * 只会被读成"镜头推近"，不会再有"她怎么站着"的疑问。
   * 显示广角时必须把立绘和桌面遮挡层都收掉 —— 否则两套"她"会叠在一起。
   */
  let kvOn = false;
  function setKv(on) {
    if (!el.kv) return;
    kvOn = on;
    el.kv.style.opacity = on ? '1' : '0';
    if (on) el.char.style.opacity = '0';
    syncTable();
  }

  function setScene(img) {
    if (img === 'black') {
      el.bg.style.opacity = '0';
      el.char.style.opacity = '0';
      el.vig.style.opacity = '0.9';
      setLayout('stand');
      return;
    }
    el.bg.style.opacity = '1';
    el.vig.style.opacity = '1';
    setKv(false);
    setLayout(layoutFor(img));
    // kv 与 bg 是同一张图：bg 作为静态底，char 承担推近演出
    const url = IMG[img] || IMG.kv;
    if (el.bg.dataset.src !== url) {
      el.bg.dataset.src = url;
      el.bg.style.backgroundImage = `url("${asset(url)}")`;
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
      const text = fillPlaceholders(raw);
      el.center.innerHTML = `<div class="centerText">${renderMarkup(text)}</div>`;
      el.box.classList.add('empty');
      el.center.classList.add('show');

      // 章节标题：自动淡入 → 停留 → 淡出，玩家不需要点。
      // 其他独白（结局名、内心）仍然要点一下才过。
      const isChapter = /第[一二三四五]章|序章/.test(text);
      let done = false;
      const finish = () => {
        if (done) return;
        done = true;
        window.__centerAdvance = null;
        el.center.classList.remove('show');
        el.box.classList.remove('empty');
        resolve();
      };
      window.__centerAdvance = finish;

      if (isChapter) {
        const fast = new URLSearchParams(location.search).has('fast');
        setTimeout(finish, fast ? 260 : 3400);
      }
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

  // ---------------------------------------------------------------- 遮幅（电影画幅）
  function showBars(which) {
    const bars = [el.barTop, el.barBottom];
    if (which === 'top' || which === undefined) {
      el.barTop.classList.add('in');
    }
    if (which === 'bottom' || which === undefined) {
      el.barBottom.classList.add('in');
    }
    return bars;
  }
  function hideBars() {
    el.barTop.classList.remove('in');
    el.barBottom.classList.remove('in');
  }

  const SEASONINGS = {
    salt:  { label: '盐', hint: '咸是诚实。',
             note: '粗粒的，放在一只小陶碟里。没有任何味道，但你会想把它放在舌头上试一下。' },
    sugar: { label: '黄糖', hint: '甜是讨好。',
             note: '结成块，边缘有点黏。有一点焦味，像是熬过头了又被人救回来。' },
    jar:   { label: '没有标签的瓶子', hint: '这一瓶，你不该闻到。', danger: true,
             note: '拔开瓶塞的瞬间，整个厨房的气味都变了。' },
  };

  // 第二章的调味：先闻，再放下。30 秒，放下去不可逆。
  function openSeasonScreen() {
    return new Promise((resolve) => {
      // ?fast=1 时把 30 秒压到 1.5 秒，方便冒烟测试，正常游玩不受影响
      const FAST = new URLSearchParams(location.search).has('fast');
      const SEASON_SECONDS = FAST ? 1.5 : 30;
      const seen = new Set();
      el.smell.innerHTML = '';
      el.smell.classList.add('show', 'season');

      const bar = document.createElement('div');
      bar.className = 'seasonBar';
      const fill = document.createElement('i');
      bar.appendChild(fill);
      el.smell.appendChild(bar);

      const head = document.createElement('div');
      head.className = 'smellHead';
      head.innerHTML = '<div class="t">调 味</div>'
        + '<div class="s">先闻。闻完再决定放什么。放错了也没关系——我会吃完。</div>';
      el.smell.appendChild(head);

      const info = document.createElement('div');
      info.className = 'smellInfo';
      info.innerHTML = '<div class="note"></div><div class="line"></div>';
      el.smell.appendChild(info);

      const pick = document.createElement('div');
      pick.className = 'seasonPick';
      Object.entries(SEASONINGS).forEach(([key, s]) => {
        const b = document.createElement('button');
        if (s.danger) b.className = 'jarbtn';
        b.innerHTML = `<div class="n">${s.label}</div><div class="h">闻一闻</div>`;
        b.addEventListener('click', () => {
          seen.add(key);
          info.querySelector('.note').textContent = s.hint;
          info.querySelector('.line').textContent = s.note;
          info.classList.add('show');
          b.classList.add('seen');
          put.style.visibility = 'visible';
        });
        pick.appendChild(b);
      });
      el.smell.appendChild(pick);

      // 放下去（只在闻过之后可用）
      const put = document.createElement('div');
      put.className = 'seasonPut';
      put.style.visibility = 'hidden';
      [['salt', '放盐'], ['sugar', '放糖'], ['jar', '放那一瓶']].forEach(([k, label]) => {
        const b = document.createElement('button');
        b.textContent = label;
        if (k === 'jar') b.classList.add('jar');
        b.addEventListener('click', () => finish(k));
        put.appendChild(b);
      });
      el.smell.appendChild(put);

      let done = false;
      let left = SEASON_SECONDS;
      const tick = setInterval(() => {
        left = Math.max(0, left - 0.1);
        fill.style.width = `${(left / SEASON_SECONDS) * 100}%`;
        if (left <= 8) fill.classList.add('low');
        if (left <= 0) finish('salt');       // 时间到：默认放盐，她不为难你
      }, 100);

      function finish(k) {
        if (done) return;
        done = true;
        clearInterval(tick);
        el.smell.classList.remove('show', 'season');
        resolve(k);
      }
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
    const res = await fetch(asset('story.json'));
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
    startLive();
    renderEndings();
    requestAnimationFrame(candleBreath);
    setInterval(() => { if (S.running) candleCrackle(); }, 5200 + Math.random() * 4000);
  }

  function renderEndings() {
    const st = loadStore();
    // 按章分组。没拿到的只给一句提示，不剧透名字 —— 让玩家想再走一遍。
    const groups = [
      ['序章', [
        ['endings_lie', 'A · 她记住了你的谎话'],
        ['endings_name', 'B · 她记住了你的名字'],
        ['endings_scent', 'C · 她记住了你的味道'],
      ]],
      ['第一章 · 门铃', [
        ['ch1_stay', '她记住了你留下来'],
        ['ch1_leave', '她记住了你看见了什么'],
        ['ch1_key', '她给了你钥匙'],
      ]],
      ['第二章 · 刀与糖', [
        ['ch2_shared', '她给你留了半盘'],
        ['ch2_taste', '她记住了你放的那一撮'],
        ['ch2_seen', '她已经知道你会回来'],
      ]],
      ['第三章 · 十七个日期', [
        ['ch3_sofa', '她给了你沙发'],
        ['ch3_counted', '她算准了你会回来'],
        ['ch3_same', '她等的从来是同一个人'],
      ]],
    ];
    el.endList.innerHTML = groups.map(([title, items]) => {
      const got = items.filter(([k]) => st[k]).length;
      const rows = items.map(([k, t]) => (st[k]
        ? `<li class="got">◆ ${t}</li>`
        : `<li>◇ <span class="locked">未抵达</span></li>`)).join('');
      return `<li class="grp"><span class="gt">${title}</span>`
        + `<span class="gc">${got}/${items.length}</span></li>${rows}`;
    }).join('');
  }

  // 窗口尺寸变了要重新摆位：seat 用的是 1920x1080 下的绝对像素，换分辨率必须重算
  let resizeTimer = null;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => paintSprite(), 120);
  });

  el.startBtn.addEventListener('click', () => {
    el.title.classList.add('hidden');
    el.stage.classList.add('playing');
    S.running = true;
    // 音频只做「顺手启动」，绝不 await —— 它慢一点不该让玩家看着黑屏等
    try { ac(); } catch (e) { /* 浏览器不支持就算了 */ }
    runLabel('start');
  });

  boot();
})();
