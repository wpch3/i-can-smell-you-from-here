const fs=require('fs');
const story=JSON.parse(fs.readFileSync('/home/user/i-can-smell-you-from-here/demo/story.json','utf8'));

function evalExpr(expr, vars){
  const keys=Object.keys(vars);
  return new Function(...keys,`return (${expr});`)(...keys.map(k=>vars[k]));
}
function runSet(expr, vars){
  let m=expr.match(/^(\w+)\s*\+=\s*(.+)$/);
  if(m){vars[m[1]]=(vars[m[1]]||0)+Number(evalExpr(m[2],vars));return;}
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
    else if(ins.op==='set'){runSet(ins.expr,vars);}
    else if(ins.op==='if'){pc=evalExpr(ins.cond,vars)?ins.pc:ins.else_pc;}
    else if(ins.op==='jump'){ if(ins.label){label=ins.label;pc=0;} else {pc=ins.pc;} }
    else if(ins.op==='menu'){
      const pick = pi<path.length? path[pi++] : 0;
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

// 穷举前 4 个菜单（3^4=81）
const outs={};
let total=0;
for(let a=0;a<3;a++)for(let b=0;b<3;b++)for(let c=0;c<3;c++)for(let d=0;d<3;d++){
  const r=play([a,b,c,d]);
  total++;
  const key=r.end+'/'+(r.vars.chapter_name||'?');
  outs[key]=(outs[key]||0)+1;
  if(r.end!=='end') console.log('BAD',a,b,c,d,r.end,r.label,r.says);
}
console.log('paths:',total);
console.log(outs);

// 列出每个结局的一条代表路径
const seen={};
for(let a=0;a<3;a++)for(let b=0;b<3;b++)for(let c=0;c<3;c++)for(let d=0;d<3;d++){
  const r=play([a,b,c,d]);
  const k=r.vars.chapter_name;
  if(!seen[k]) seen[k]={path:[a,b,c,d],vars:{scent:r.vars.scent,trust:r.vars.trust,doubt:r.vars.doubt},choices:r.choices};
}
for(const k in seen) console.log(k, JSON.stringify(seen[k]));
