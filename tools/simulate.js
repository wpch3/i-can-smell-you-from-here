const fs=require('fs');
const story=JSON.parse(fs.readFileSync('/home/user/i-can-smell-you-from-here/demo/story.json','utf8'));

function evalExpr(expr, vars){
  const keys=Object.keys(vars).filter(k=>/^[A-Za-z_]\w*$/.test(k));
  const env=Object.fromEntries(keys.map(k=>[k,vars[k]]));
  env.persistent = vars.__persistent || {};   // 剧本里的 persistent.xxx 判断
  env._return = vars.__return;
  return new Function('vars',`with(vars){ return (${expr}); }`)(env);
}
function runSet(expr, vars){
  // persistent.foo = True
  let m=expr.match(/^persistent\.(\w+)\s*=\s*(.+)$/);
  if(m){
    if(!vars.__persistent) vars.__persistent={};
    vars.__persistent[m[1]]=evalExpr(m[2],vars);
    return;
  }
  m=expr.match(/^(\w+)\s*\+=\s*(.+)$/);
  if(m){vars[m[1]]=(vars[m[1]]||0)+Number(evalExpr(m[2],vars));return;}
  m=expr.match(/^(\w+)\s*-=\s*(.+)$/);
  if(m){vars[m[1]]=(vars[m[1]]||0)-Number(evalExpr(m[2],vars));return;}
  m=expr.match(/^(\w+)\s*=\s*(.+)$/);
  if(m){vars[m[1]]=evalExpr(m[2],vars);return;}
  throw new Error('set? '+expr);
}
// path 是每个 menu 的选择下标序列
function play(path){
  const vars=JSON.parse(JSON.stringify(story.defaults));
  vars.smells_found=4; vars.smell_line='x';
  let label='start', pc=0, pi=0, says=0, choices=[], steps=0;
  while(steps++<3000){
    const code=story.labels[label];
    if(pc>=code.length){return {end:'fell-off',label,says,choices,vars};}
    const ins=code[pc++];
    if(ins.op==='say'){says++;}
    else if(ins.op==='screen'){
      // 交互界面：调味那一个从 path 里取（0=盐 1=糖 2=那一瓶），
      // 其他（嗅桌子）不产生返回值。
      if(String(ins.name||'').startsWith('seasoning')){
        const pickIdx = pi<path.length ? path[pi++] : 0;
        vars.__return = ['salt','sugar','jar'][Math.min(pickIdx,2)];
      }
    }
    else if(ins.op==='set'){runSet(ins.expr,vars);}
    else if(ins.op==='if'){pc=evalExpr(ins.cond,vars)?ins.pc:ins.else_pc;}
    else if(ins.op==='jump'){ if(ins.label){label=ins.label;pc=0;} else {pc=ins.pc;} }
    else if(ins.op==='menu'){
      let pick = pi<path.length? path[pi++] : 0;
      if (pick >= ins.options.length) pick = ins.options.length - 1;  // 选项数不足时取最后一项
      choices.push(ins.options[pick].text);
      pc=ins.options[pick].pc;
    }
    else if(ins.op==='return'){return {end:'return',label,says,choices,vars};}
    else if(ins.op==='end'){
      // end 之后可能还有代码（占位），视为结束
      return {end:'end',label,says,choices,vars};
    }
  }
  return {end:'loop',label,says,choices,vars};
}

// 穷举前 4 个菜单（3^4=81），然后在 Ch1 用默认选择
const outs={};
let total=0;
for(let a=0;a<3;a++)for(let b=0;b<3;b++)for(let c=0;c<3;c++)for(let d=0;d<3;d++){
  const r=play([a,b,c,d,0,0,0,0]);
  total++;
  const key=r.end+'/'+(r.vars.chapter_name||'?');
  outs[key]=(outs[key]||0)+1;
  if(r.end!=='return' && r.end!=='end') console.log('BAD',a,b,c,d,r.end,r.label,r.says);
}
console.log('paths:',total);
console.log(outs);

// 随机抽样 3000 条完整路径，确认 Ch1 三个结局都可达
let seed = 12345;
const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
function playRandom() {
  const saved = [];
  const n = 24;
  for (let i = 0; i < n; i++) saved.push(Math.floor(rnd() * 3));
  return play(saved);
}
const dist = {};
for (let i = 0; i < 3000; i++) {
  const r = playRandom();
  const k = (r.vars.chapter_name || '?') + ' [' + r.end + ']';
  dist[k] = (dist[k] || 0) + 1;
}
console.log('=== 随机 3000 次 · 结局分布 ===');
Object.entries(dist).sort((a, b) => b[1] - a[1]).forEach(([k, v]) => console.log('  ' + k + ' × ' + v));

// 列出每个结局的一条代表路径（含 Ch1 的 3^4=81 种走法抽样）
const seen={};
const ch1={
  '登门·照做':0,'登门·追问外套':1,'登门·不脱':2,
  '厨房·现在做':0,'厨房·改天':1,'厨房·反悔':2,
  '冰箱·关上门':0,'冰箱·问她':1,'冰箱·拿出来':2,
  '椅子·坐':0,'椅子·反问':1,'椅子·站着':2,
  '天亮·不走':0,'天亮·走':1,'天亮·要钥匙':2,
};
for(let d1=0;d1<3;d1++)for(let d2=0;d2<3;d2++)for(let d3=0;d3<3;d3++)for(let d4=0;d4<3;d4++){
  const r=play([0,0,0,0,d1,d2,d3,d4]);
  const k=r.vars.chapter_name;
  if(!seen[k]) seen[k]={path:[d1,d2,d3,d4],vars:{scent:r.vars.scent,trust:r.vars.trust,doubt:r.vars.doubt},choices:r.choices.slice(5)};
}
for(const k in seen) console.log(k, JSON.stringify(seen[k]));
