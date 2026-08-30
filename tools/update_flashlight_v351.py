from pathlib import Path
import base64, re

VERSION='3.5.1'
p=Path('decoded-scripts.html')
src=p.read_text(encoding='utf-8')

# Passa o ID único da ação ao gerador. Isso permite que cada lanterna tenha
# seu próprio estado liga/desliga, mesmo quando há várias regras.
old_ctx="ctx:{p:a.p||{},T:Texpr,tpl:makeTpl(rule),i:ai,O:((T.targets||[])[0]||{}).expr||(T.hasBlock?'block':Texpr),isPlayer:!!(tgt&&tgt.isPlayer),D:isList?`${Texpr}.dimension`:dimExprFor(rule,tgt),L:locExprFor(rule,a,tgt)}}"
new_ctx="ctx:{p:a.p||{},actionId:a.id||('action_'+ai),T:Texpr,tpl:makeTpl(rule),i:ai,O:((T.targets||[])[0]||{}).expr||(T.hasBlock?'block':Texpr),isPlayer:!!(tgt&&tgt.isPlayer),D:isList?`${Texpr}.dimension`:dimExprFor(rule,tgt),L:locExprFor(rule,a,tgt)}}"
if old_ctx in src:
    src=src.replace(old_ctx,new_ctx,1)
elif "actionId:a.id||('action_'+ai)" not in src:
    raise SystemExit('makeCtx target not found')

new_flashlight=r'''  flashlight:{
    label:'Lanterna projetada', needs:'player', group:'Luz', system:true,
    fields:[
      {k:'range',t:'num',label:'Alcance total',def:20},
      {k:'nearDistance',t:'num',label:'Faixa próxima (blocos)',def:5},
      {k:'nearLevel',t:'num',label:'Nível perto (1–15)',def:15},
      {k:'farLevel',t:'num',label:'Nível depois da faixa (1–15)',def:7},
      {k:'spacing',t:'num',label:'Espaçamento',def:1},
      {k:'ticks',t:'num',label:'Atualizar a cada (ticks)',def:2}
    ],
    multi:(c)=>{
      const range=Math.max(1,cnum(c.p.range,20));
      const near=Math.max(0,Math.min(range,cnum(c.p.nearDistance,5)));
      const nearLv=Math.max(1,Math.min(15,Math.round(cnum(c.p.nearLevel,15))));
      const farLv=Math.max(1,Math.min(15,Math.round(cnum(c.p.farLevel,7))));
      const spacing=Math.max(0.25,cnum(c.p.spacing,1));
      const ticks=Math.max(1,cnum(c.p.ticks,2));
      const uid=String(c.actionId||('flashlight_'+c.i)).replace(/[^a-zA-Z0-9_]/g,'_');
      const pl=`lanterna_${uid}`;
      const store=`flashStore_${uid}`;
      const key=`flashKey_${uid}`;
      const old=`flashOld_${uid}`;
      const state=`flashState_${uid}`;
      return [
        `const ${pl}=${c.T};`,
        `const ${store}=globalThis.__forjaFlashlights || (globalThis.__forjaFlashlights=new Map());`,
        `const ${key}=${q(String(c.actionId||('flashlight_'+c.i)))} + ':' + ${pl}.id;`,
        `const ${old}=${store}.get(${key});`,
        `if (${old}) {`,
        `  try { system.clearRun(${old}.run); } catch(e) {}`,
        `  for (const p of (${old}.trail||[])) { try { const b=p.dimension.getBlock(p.location); if (b?.typeId.startsWith("minecraft:light_block")) b.setType("minecraft:air"); } catch(e) {} }`,
        `  ${store}.delete(${key});`,
        `} else {`,
        `  const ${state}={trail:[],run:0};`,
        `  ${store}.set(${key},${state});`,
        `  ${state}.run=system.runInterval(()=>{`,
        `    try {`,
        `      for (const p of ${state}.trail) { const b=p.dimension.getBlock(p.location); if (b?.typeId.startsWith("minecraft:light_block")) b.setType("minecraft:air"); }`,
        `      ${state}.trail=[];`,
        `      const h=${pl}.getHeadLocation(); const d=${pl}.getViewDirection();`,
        `      for (let n=${spacing}; n<=${range}; n+=${spacing}) {`,
        `        const p={x:Math.floor(h.x+d.x*n),y:Math.floor(h.y+d.y*n),z:Math.floor(h.z+d.z*n)};`,
        `        const b=${pl}.dimension.getBlock(p); if(!b) break;`,
        `        if (b.typeId!=="minecraft:air" && !b.typeId.startsWith("minecraft:light_block")) break;`,
        `        b.setType(n<=${near} ? "minecraft:light_block_${nearLv}" : "minecraft:light_block_${farLv}");`,
        `        ${state}.trail.push({dimension:${pl}.dimension,location:p});`,
        `      }`,
        `    } catch(e) {`,
        `      try { system.clearRun(${state}.run); } catch(_) {}`,
        `      for (const p of ${state}.trail) { try { const b=p.dimension.getBlock(p.location); if (b?.typeId.startsWith("minecraft:light_block")) b.setType("minecraft:air"); } catch(_) {} }`,
        `      ${store}.delete(${key});`,
        `    }`,
        `  }, ${ticks});`,
        `}`
      ];
    }
  },
'''

pat=r"  flashlight:\{ label:'Lanterna projetada'.*?\}\},\n  lightFollow:"
m=re.search(pat,src,re.S)
if not m:
    # Já pode estar no formato multilinha em uma reexecução.
    pat=r"  flashlight:\{\n    label:'Lanterna projetada'.*?\n  \},\n  lightFollow:"
    m=re.search(pat,src,re.S)
if not m:
    raise SystemExit('flashlight action not found')
src=src[:m.start()]+new_flashlight+'  lightFollow:'+src[m.end():]

# Traduções dos novos campos.
anchor='  "Faixas": "Bands",\n'
translations=(
'  "Alcance total": "Total range",\n'
'  "Faixa próxima (blocos)": "Near range (blocks)",\n'
'  "Nível perto (1–15)": "Near light level (1–15)",\n'
'  "Nível depois da faixa (1–15)": "Light level after near range (1–15)",\n'
)
if '"Faixa próxima (blocos)"' not in src and anchor in src:
    src=src.replace(anchor,anchor+translations,1)

p.write_text(src,encoding='utf-8')

# Reempacota o editor Scripts no shell.
legacy=Path('legacy.html').read_text(encoding='utf-8')
encoded=base64.b64encode(src.encode('utf-8')).decode('ascii')
legacy,n=re.subn(r'(<script type="text/plain" id="src-scripts">).*?(</script>)',lambda m:m.group(1)+encoded+m.group(2),legacy,count=1,flags=re.S)
if n!=1:
    raise SystemExit('failed to repack src-scripts')
legacy=legacy.replace('v3.5.0','v'+VERSION).replace('Forja v3.5.0','Forja v'+VERSION)
Path('legacy.html').write_text(legacy,encoding='utf-8')

index=Path('index.html').read_text(encoding='utf-8')
index=index.replace('v3.5.0','v'+VERSION).replace('3.5.0','3.5.1')
Path('index.html').write_text(index,encoding='utf-8')
