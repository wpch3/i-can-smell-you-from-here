/* 无浏览器的冒烟测试：用 jsdom 把网页 Demo 从标题页一路点到大结局。
 * 需要：npm i jsdom（只在本地跑，不进游戏包）
 * 用法：node tools/smoke-test.js [选项下标,如 0,0,2,2]
 */
const { JSDOM, VirtualConsole } = require('jsdom');
const fs = require('fs');
const path = require('path');

const DEMO = path.join(__dirname, '..', 'demo');
const DOM_URL = 'http://localhost/demo/?fast=1';
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

(async () => {
  await sleep(400);
  click($('startBtn'));
  await sleep(700);

  const transcript = [];
  let choices = [];
  let smellsSeen = 0;
  let steps = 0;
  let last = '';

  while (steps++ < 4000) {
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

    // 居中独白
    if ($('center').classList.contains('show')) { click($('stage')); await sleep(40); continue; }

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

    // 结束判定：回到标题或长时间无变化
    if (transcript.length && $('box').classList.contains('empty') && steps > 40) {
      const ended = transcript.some((t) => t.includes('序章 · 完'));
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
  transcript.slice(-4).forEach((t) => console.log('  ' + t.slice(0, 70)));
  process.exit(errors.length ? 1 : 0);
})();
