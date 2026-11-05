/* 无浏览器的冒烟测试：用 jsdom 把网页 Demo 从标题页一路点到大结局。
 * 需要：npm i jsdom（只在本地跑，不进游戏包）
 * 用法：node tools/smoke-test.js [选项下标,如 0,0,2,2]
 */
const { JSDOM, VirtualConsole } = require('jsdom');
const fs = require('fs');
const path = require('path');

const DEMO = path.join(__dirname, '..', 'demo');
const DOM_URL = 'http://localhost/demo/?fast=1&nosprite=1';
const wantPath = (process.argv[2] || '').split(',').filter((x) => x !== '').map(Number);

const html = fs.readFileSync(path.join(DEMO, 'index.html'), 'utf8');
const vc = new VirtualConsole();
vc.on('jsdomError', (e) => { console.error('JSDOM ERROR', e.message); });
const dom = new JSDOM(html, { url: DOM_URL, runScripts: 'outside-only', pretendToBeVisual: true, virtualConsole: vc });
const { window } = dom;
const doc = window.document;

const story = fs.readFileSync(path.join(DEMO, 'story.json'), 'utf8');
window.fetch = async () => ({ json: async () => JSON.parse(story) });

// WebAudio 桩
window.AudioContext = function () {
  return new Proxy({}, {
    get: () => () => ({
      connect() {}, start() {}, stop() {},
      gain: { value: 0, cancelScheduledValues() {}, linearRampToValueAtTime() {}, exponentialRampToValueAtTime() {}, setValueAtTime() {} },
      frequency: { value: 0, setValueAtTime() {}, exponentialRampToValueAtTime() {} },
      Q: { value: 0 },
      getChannelData: () => new Float32Array(64),
      buffer: null, loop: false, type: 'sine',
    }),
  });
};
window.requestAnimationFrame = (cb) => setTimeout(() => cb(0), 16);

const errors = [];
window.addEventListener('error', (e) => errors.push(e.message || String(e.error)));
window.addEventListener('unhandledrejection', (e) => errors.push('unhandled: ' + (e.reason && e.reason.message)));

window.eval(fs.readFileSync(path.join(DEMO, 'engine.js'), 'utf8'));

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const click = (n) => n.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
const $ = (id) => doc.getElementById(id);

/* 结构回归检查 —— 血泪教训：
 * 曾经 index.html 多了一个 </div>，把 #box（对白框）挤出了 #stage。
 * 显隐规则是 `#stage.playing #box{opacity:1}`，于是对白框永远是 opacity:0，
 * 玩家看到的就是「黑屏 + 有声音 + 点得动，但没有一个字」，以为卡死了。
 * jsdom 不会真正合成 opacity，但能验证选择器层级，这就够了。
 */
function checkStructure() {
  const problems = [];
  const need = ['stage', 'bg', 'char', 'box', 'who', 'text', 'next', 'choices', 'center', 'title', 'vig', 'grain'];
  for (const id of need) if (!$(id)) problems.push(`缺少元素 #${id}`);

  const stage = $('stage');
  if (stage) {
    // 所有演出层都必须真的在舞台里面，否则 #stage 的后代选择器全部失效
    for (const id of ['bg', 'char', 'vig', 'grain', 'box', 'choices', 'center', 'title']) {
      const e = $(id);
      if (e && !stage.contains(e)) problems.push(`#${id} 掉到 #stage 外面了（检查 index.html 的 <div> 是否配对）`);
    }
    // 模拟开场 + 第一句台词后的状态，确认对白框真的会被点亮
    // （engine 在 typeText 里会摘掉 .empty，只测 .playing 会漏掉这一层）
    stage.classList.add('playing');
    $('box').classList.remove('empty');
    const ok = $('box').matches('#stage.playing #box') && !$('box').classList.contains('empty');
    if (!ok) problems.push('#stage.playing #box 选择器匹配失败 —— 对白框永远不可见');
    stage.classList.remove('playing');
    $('box').classList.add('empty');
  }

  if (problems.length) {
    problems.forEach((p) => console.error('✗ 结构检查: ' + p));
    process.exit(1);
  }
  console.log('结构检查: ✅');
}

(async () => {
  await sleep(400);
  checkStructure();
  click($('startBtn'));
  await sleep(700);

  const transcript = [];
  let choices = [];
  let smellsSeen = 0;
  let steps = 0;
  let last = '';
  let lastCenter = '';

  while (steps++ < 12000) {
    await sleep(12);

    const txt = $('text').textContent.trim();
    if (txt && txt !== last) { transcript.push(txt); last = txt; }

    // 气味交互
    const smell = $('smell');
    if (smell.classList.contains('show')) {
      const spots = [...smell.querySelectorAll('.hotspot')];
      if (spots.length && smellsSeen === 0) {
        spots.forEach((s, i) => { setTimeout(() => click(s), i * 4); });
        await sleep(40);
        smellsSeen = spots.length;
        transcript.push(`[气味面板] ${smell.querySelector('.smellCount').textContent}`);
      }
      const leave = smell.querySelector('.leave');
      if (leave && smellsSeen) { click(leave); await sleep(40); }
      continue;
    }

    // 调味界面（第二章）：先点三样都闻一遍，再按剧本路径放下一样
    if ($('smell').classList.contains('season')) {
      const picks = [...$('smell').querySelectorAll('.seasonPick button')];
      picks.forEach((b) => click(b));
      await sleep(60);
      const putBtns = [...$('smell').querySelectorAll('.seasonPut button')];
      const idx = wantPath.length ? (wantPath[choices.length] ?? 0) : 0;
      if (putBtns.length) {
        choices.push('放下：' + putBtns[Math.min(idx, putBtns.length - 1)].textContent);
        click(putBtns[Math.min(idx, putBtns.length - 1)]);
      }
      await sleep(80);
      continue;
    }

    // 居中独白：它不在 #text 里，得单独记，否则章末/结局名永远抓不到
    const center = $('center');
    if (center.classList.contains('show')) {
      const ct = center.textContent.replace(/\s+/g, ' ').trim();
      if (ct && ct !== lastCenter) { transcript.push('[独白] ' + ct); lastCenter = ct; }
      click($('stage'));
      await sleep(40);
      continue;
    }

    // 选项
    const box = $('choices');
    if (box.classList.contains('show')) {
      const btns = [...box.querySelectorAll('.choice')];
      if (!btns.length) continue;
      const idx = wantPath.length ? (wantPath[choices.length] ?? 0) : (choices.length % btns.length);
      if (idx >= btns.length) { console.error('选项下标越界', idx, btns.length); process.exit(1); }
      choices.push(btns[idx].querySelector('.label').textContent);
      click(btns[idx]);
      await sleep(40);
      continue;
    }

    // 结束判定：任意一章的章末独白出现即停（剧本已进到第二章预告）
    if (transcript.length && steps > 40) {
      const ended = transcript.some((t) =>
        t.includes('第三章 · 完'));
      if (ended) break;
    }

    click($('stage'));
  }

  console.log('错误:', errors.length ? errors : '无');
  console.log('台词行数:', transcript.length);
  console.log('气味:', smellsSeen + '/4');
  console.log('选择:', choices);
  console.log('--- 开场 ---');
  transcript.slice(0, 3).forEach((t) => console.log('  ' + t.slice(0, 70)));
  console.log('--- 结尾 ---');
  transcript.slice(-6).forEach((t) => console.log('  ' + t.slice(0, 78)));
  const ends = transcript.filter((t) => t.includes('结局') || t.includes('· 完') || t.includes('制作中') || t.startsWith('[独白]'));
  console.log('--- 章末 ---');
  ends.slice(-4).forEach((t) => console.log('  ' + t.replace(/\s+/g, ' ').slice(0, 88)));
  process.exit(errors.length ? 1 : 0);
})();
