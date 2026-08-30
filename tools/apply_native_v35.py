import pathlib, re, base64, json, subprocess

VERSION='3.5.0'
p=pathlib.Path('decoded-scripts.html')
src=p.read_text(encoding='utf-8')
marker='''/* =====================================================================
   ESTADO
   ===================================================================== */'''
if marker not in src:
    raise SystemExit('ESTADO marker not found')
if 'FORJA_NATIVE_V35_BEGIN' in src:
    raise SystemExit('native v3.5 patch already present')

patch=r'''
/* FORJA_NATIVE_V35_BEGIN — opções integradas diretamente em QUANDO / SE / ENTÃO */

if (TRIGGERS.interval) TRIGGERS.interval.label = 'A cada intervalo';
if (ACTIONS.cmd) ACTIONS.cmd.label = 'Executar comando';

Object.assign(TRIGGERS, {
  hurtByPlayer: {
    label:'Entidade recebe dano do player', group:'Entidade',
    fields:[{k:'entity',t:'text',label:'Filtrar entidade (id)',ph:'minecraft:zombie'}],
    targets:[{k:'target',label:'quem tomou o dano',expr:'alvo'},{k:'player',label:'o jogador que atacou',expr:'player',isPlayer:true}],
    build(p){
      const h=['world.afterEvents.entityHurt.subscribe((ev) => {','  const alvo = ev.hurtEntity;','  const atacante = ev.damageSource.damagingEntity;','  if (!atacante || atacante.typeId !== "minecraft:player") return;','  const player = atacante;','  const dano = ev.damage;'];
      if(p.entity) h.push(`  if (alvo.typeId !== ${q(p.entity)}) return;`);
      return {head:h,ind:2,close:['});']};
    }
  },
  lookEntity: {
    label:'Jogador olha para entidade', group:'Jogador', loopBody:true,
    fields:[{k:'entity',t:'text',label:'Entidade (id)',ph:'minecraft:zombie'},{k:'range',t:'num',label:'Alcance (blocos)',def:8},{k:'ticks',t:'num',label:'Verificar a cada (ticks)',def:2}],
    targets:[{k:'target',label:'a entidade olhada',expr:'alvo'},{k:'player',label:'o jogador',expr:'player',isPlayer:true}],
    build(p){
      const filtro=p.entity?` && r.entity.typeId === ${q(p.entity)}`:'';
      return {head:['system.runInterval(() => {','  for (const player of world.getAllPlayers()) {',`    const hit = player.getEntitiesFromViewDirection({ maxDistance: ${num(p.range,8)} }).find((r) => r.entity${filtro});`,'    if (!hit?.entity) continue;','    const alvo = hit.entity;'],ind:4,close:['  }',`}, ${num(p.ticks,2)});`],note:'Checagem por tempo usando a direção do olhar'};
    }
  },
  enterCoordinate: {
    label:'Jogador entrou na coordenada', group:'Jogador', loopBody:true,
    fields:[{k:'x',t:'num',label:'X',def:0},{k:'y',t:'num',label:'Y',def:64},{k:'z',t:'num',label:'Z',def:0},{k:'radius',t:'num',label:'Raio (blocos)',def:3},{k:'ticks',t:'num',label:'Verificar a cada (ticks)',def:5}],
    targets:[{k:'player',label:'o jogador',expr:'player',isPlayer:true}],
    build(p,ns,ri){
      const state=`forjaEntrou${ri}`;
      return {head:[`const ${state} = new Map();`,'system.runInterval(() => {','  for (const player of world.getAllPlayers()) {',`    const dentro = Math.hypot(player.location.x-${num(p.x,0)}, player.location.y-${num(p.y,64)}, player.location.z-${num(p.z,0)}) <= ${num(p.radius,3)};`,`    const antes = ${state}.get(player.id);`,`    ${state}.set(player.id, dentro);`,'    if (antes === undefined || !dentro || antes) continue;'],ind:4,close:['  }',`}, ${num(p.ticks,5)});`],note:'Dispara uma vez quando cruza de fora para dentro'};
    }
  },
  leaveCoordinate: {
    label:'Jogador saiu da área', group:'Jogador', loopBody:true,
    fields:[{k:'x',t:'num',label:'X do centro',def:0},{k:'y',t:'num',label:'Y do centro',def:64},{k:'z',t:'num',label:'Z do centro',def:0},{k:'radius',t:'num',label:'Raio (blocos)',def:6},{k:'ticks',t:'num',label:'Verificar a cada (ticks)',def:5}],
    targets:[{k:'player',label:'o jogador',expr:'player',isPlayer:true}],
    build(p,ns,ri){
      const state=`forjaSaiu${ri}`;
      return {head:[`const ${state} = new Map();`,'system.runInterval(() => {','  for (const player of world.getAllPlayers()) {',`    const dentro = Math.hypot(player.location.x-${num(p.x,0)}, player.location.y-${num(p.y,64)}, player.location.z-${num(p.z,0)}) <= ${num(p.radius,6)};`,`    const antes = ${state}.get(player.id);`,`    ${state}.set(player.id, dentro);`,'    if (antes === undefined || dentro || !antes) continue;'],ind:4,close:['  }',`}, ${num(p.ticks,5)});`],note:'Dispara uma vez quando cruza de dentro para fora'};
    }
  },
  touchEntity: {
    label:'Jogador encostou na entidade', group:'Entidade', loopBody:true,
    fields:[{k:'entity',t:'text',label:'Entidade (id)',ph:'minecraft:zombie'},{k:'radius',t:'num',label:'Distância de contato',def:1.25},{k:'ticks',t:'num',label:'Verificar a cada (ticks)',def:2}],
    targets:[{k:'target',label:'a entidade',expr:'alvo'},{k:'player',label:'o jogador',expr:'player',isPlayer:true}],
    build(p){
      const type=p.entity?`type: ${q(p.entity)}, `:'';
      return {head:['system.runInterval(() => {','  for (const player of world.getAllPlayers()) {',`    const alvo = player.dimension.getEntities({ ${type}location: player.location, maxDistance: ${num(p.radius,1.25)} }).find((e) => e.id !== player.id);`,'    if (!alvo) continue;'],ind:4,close:['  }',`}, ${num(p.ticks,2)});`],note:'Contato aproximado por distância'};
    }
  },
  wallEntity: {
    label:'Entidade encosta na parede', group:'Entidade', loopBody:true,
    fields:[{k:'entity',t:'text',label:'Entidade (id, vazio = todas)',ph:'minecraft:zombie'},{k:'dist',t:'num',label:'Distância lateral',def:0.55},{k:'ticks',t:'num',label:'Verificar a cada (ticks)',def:4}],
    targets:[{k:'target',label:'a entidade',expr:'alvo'}],
    build(p){
      const query=p.entity?`{ type: ${q(p.entity)} }`:'{}', d=num(p.dist,0.55);
      return {head:['system.runInterval(() => {','  for (const dim of [world.getDimension("overworld"), world.getDimension("nether"), world.getDimension("the_end")]) {',`    for (const alvo of dim.getEntities(${query})) {`,'      const p = alvo.location; const y = Math.floor(p.y + 0.6);',`      const pts = [[p.x+${d},y,p.z],[p.x-${d},y,p.z],[p.x,y,p.z+${d}],[p.x,y,p.z-${d}]];`,'      const parede = pts.some(([x,y,z]) => { const b=dim.getBlock({x:Math.floor(x),y,z:Math.floor(z)}); return b && b.typeId !== "minecraft:air" && !b.isLiquid; });','      if (!parede) continue;'],ind:6,close:['    }','  }',`}, ${num(p.ticks,4)});`],note:'Detecção aproximada por blocos sólidos laterais'};
    }
  },
  climbingEntity: {
    label:'Entidade está escalando', group:'Entidade', loopBody:true,
    fields:[{k:'entity',t:'text',label:'Entidade (id, vazio = todas)',ph:'minecraft:spider'},{k:'ticks',t:'num',label:'Verificar a cada (ticks)',def:4}],
    targets:[{k:'target',label:'a entidade',expr:'alvo'}],
    build(p){const query=p.entity?`{ type: ${q(p.entity)} }`:'{}';return {head:['system.runInterval(() => {','  for (const dim of [world.getDimension("overworld"), world.getDimension("nether"), world.getDimension("the_end")]) {',`    for (const alvo of dim.getEntities(${query})) {`,'      if (!alvo.isClimbing) continue;'],ind:6,close:['    }','  }',`}, ${num(p.ticks,4)});`]};}
  },
  swimmingEntity: {
    label:'Entidade está nadando', group:'Entidade', loopBody:true,
    fields:[{k:'entity',t:'text',label:'Entidade (id, vazio = todas)',ph:'minecraft:dolphin'},{k:'ticks',t:'num',label:'Verificar a cada (ticks)',def:4}],
    targets:[{k:'target',label:'a entidade',expr:'alvo'}],
    build(p){const query=p.entity?`{ type: ${q(p.entity)} }`:'{}';return {head:['system.runInterval(() => {','  for (const dim of [world.getDimension("overworld"), world.getDimension("nether"), world.getDimension("the_end")]) {',`    for (const alvo of dim.getEntities(${query})) {`,'      if (!alvo.isSwimming) continue;'],ind:6,close:['    }','  }',`}, ${num(p.ticks,4)});`]};}
  }
});

Object.assign(CONDITIONS, {
  lookingEntity:{ label:'Está olhando para entidade', needs:'entity', fields:[{k:'id',t:'text',label:'Entidade (id, vazio = qualquer)',ph:'minecraft:zombie'},{k:'range',t:'num',label:'Alcance',def:8}], code:(T,p)=>{const f=p.id?` && r.entity.typeId === ${q(p.id)}`:'';return `if (!${T}.getEntitiesFromViewDirection({ maxDistance: ${num(p.range,8)} }).some((r) => r.entity${f})) return;`; }},
  touchingEntity:{ label:'Está encostando em entidade', needs:'entity', fields:[{k:'id',t:'text',label:'Entidade (id, vazio = qualquer)',ph:'minecraft:zombie'},{k:'radius',t:'num',label:'Distância',def:1.25}], code:(T,p)=>{const f=p.id?`type: ${q(p.id)}, `:'';return `if (!${T}.dimension.getEntities({ ${f}location: ${T}.location, maxDistance: ${num(p.radius,1.25)} }).some((e) => e.id !== ${T}.id)) return;`; }},
  nearCoordinate:{ label:'Está dentro da coordenada/área', needs:'entity', fields:[{k:'x',t:'num',label:'X',def:0},{k:'y',t:'num',label:'Y',def:64},{k:'z',t:'num',label:'Z',def:0},{k:'radius',t:'num',label:'Raio',def:5}], code:(T,p)=>`if (Math.hypot(${T}.location.x-${num(p.x,0)}, ${T}.location.y-${num(p.y,64)}, ${T}.location.z-${num(p.z,0)}) > ${num(p.radius,5)}) return;`},
  touchingWall:{ label:'Está encostando na parede', needs:'entity', fields:[{k:'dist',t:'num',label:'Distância lateral',def:0.55}], code:(T,p)=>`if (!(() => { const p=${T}.location,d=${T}.dimension,y=Math.floor(p.y+0.6),n=${num(p.dist,0.55)}; return [[p.x+n,y,p.z],[p.x-n,y,p.z],[p.x,y,p.z+n],[p.x,y,p.z-n]].some(([x,y,z])=>{const b=d.getBlock({x:Math.floor(x),y,z:Math.floor(z)});return b&&b.typeId!=="minecraft:air"&&!b.isLiquid;}); })()) return;`},
  climbing:{ label:'Está escalando', needs:'entity', fields:[], code:(T)=>`if (!${T}.isClimbing) return;`},
  swimming:{ label:'Está nadando', needs:'entity', fields:[], code:(T)=>`if (!${T}.isSwimming) return;`}
});

function forjaChestItems(s){
  return String(s||'').split(';').map(x=>x.trim()).filter(Boolean).map(x=>{
    const m=x.match(/^(\d+)\s*=\s*([^,\s]+)\s*(?:,\s*(\d+))?$/); if(!m)return null;
    return {slot:Math.max(0,Math.min(26,Number(m[1]))),id:m[2],qtd:Math.max(1,Math.min(64,Number(m[3]||1)))};
  }).filter(Boolean);
}
function forjaFormRows(s){ return String(s||'').split(';').map(x=>x.trim()).filter(Boolean).map(x=>x.split('|').map(y=>y.trim())); }

Object.assign(ACTIONS, {
  placeBlockNative:{ label:'Colocar bloco', needs:'loc', group:'Bloco', fields:[{k:'id',t:'text',label:'Bloco',def:'minecraft:stone'},{k:'dx',t:'num',label:'Offset X',def:0},{k:'dy',t:'num',label:'Offset Y',def:0},{k:'dz',t:'num',label:'Offset Z',def:0},{k:'air',t:'bool',label:'Só colocar se for ar',def:false}], multi:(c)=>{const p=`pb${c.i}`,b=`bb${c.i}`;return [`const ${p}={x:${c.L}.x+${num(c.p.dx,0)},y:${c.L}.y+${num(c.p.dy,0)},z:${c.L}.z+${num(c.p.dz,0)}};`,`const ${b}=${c.D}.getBlock({x:Math.floor(${p}.x),y:Math.floor(${p}.y),z:Math.floor(${p}.z)});`,c.p.air===true?`if (${b}?.typeId === "minecraft:air") ${b}.setType(${q(c.p.id||'minecraft:stone')});`:`if (${b}) ${b}.setType(${q(c.p.id||'minecraft:stone')});`];}},
  removeBlockNative:{ label:'Remover bloco', needs:'loc', group:'Bloco', fields:[{k:'dx',t:'num',label:'Offset X',def:0},{k:'dy',t:'num',label:'Offset Y',def:0},{k:'dz',t:'num',label:'Offset Z',def:0},{k:'only',t:'text',label:'Só se for este bloco (vazio = qualquer)',ph:'minecraft:stone'}], multi:(c)=>{const p=`pr${c.i}`,b=`br${c.i}`;return [`const ${p}={x:${c.L}.x+${num(c.p.dx,0)},y:${c.L}.y+${num(c.p.dy,0)},z:${c.L}.z+${num(c.p.dz,0)}};`,`const ${b}=${c.D}.getBlock({x:Math.floor(${p}.x),y:Math.floor(${p}.y),z:Math.floor(${p}.z)});`,c.p.only?`if (${b}?.typeId === ${q(c.p.only)}) ${b}.setType("minecraft:air");`:`if (${b}) ${b}.setType("minecraft:air");`];}},
  chestItems:{ label:'Colocar baú com itens', needs:'loc', group:'Bloco', imports:['ItemStack'], fields:[{k:'dx',t:'num',label:'Offset X',def:0},{k:'dy',t:'num',label:'Offset Y',def:0},{k:'dz',t:'num',label:'Offset Z',def:0},{k:'items',t:'text',label:'Itens: slot=id,qtd; ...',def:'0=minecraft:diamond,3; 1=minecraft:apple,5'}], multi:(c)=>{const p=`pc${c.i}`,b=`bc${c.i}`,inv=`inv${c.i}`,it=forjaChestItems(c.p.items);const L=[`const ${p}={x:${c.L}.x+${num(c.p.dx,0)},y:${c.L}.y+${num(c.p.dy,0)},z:${c.L}.z+${num(c.p.dz,0)}};`,`const ${b}=${c.D}.getBlock({x:Math.floor(${p}.x),y:Math.floor(${p}.y),z:Math.floor(${p}.z)});`,`if (${b}) {`,`  ${b}.setType("minecraft:chest");`,`  const ${inv}=${b}.getComponent("minecraft:inventory")?.container;`,`  if (${inv}) {`];for(const x of it)L.push(`    ${inv}.setItem(${x.slot}, new ItemStack(${q(x.id)}, ${x.qtd}));`);L.push('  }','}');return L;}},
  modalForm:{ label:'Adicionar formulário livre', needs:'player', group:'Interface', ui:true, imports:['ModalFormData'], fields:[{k:'title',t:'text',label:'Título',def:'Formulário'},{k:'rows',t:'text',label:'Elementos separados por ;',def:'text|Nome|Digite aqui; toggle|Ativado|true; slider|Nível|0|10|1|5'}], multi:(c)=>{const f=`modal${c.i}`,L=[`const ${f}=new ModalFormData().title(${q(c.p.title||'Formulário')});`];for(const r of forjaFormRows(c.p.rows)){const t=(r[0]||'').toLowerCase();if(t==='header')L.push(`${f}.header(${q(r[1]||'Seção')});`);else if(t==='label')L.push(`${f}.label(${q(r[1]||'Texto')});`);else if(t==='divider')L.push(`${f}.divider();`);else if(t==='toggle')L.push(`${f}.toggle(${q(r[1]||'Ativado')}, { defaultValue: ${String(r[2]).toLowerCase()==='true'} });`);else if(t==='slider')L.push(`${f}.slider(${q(r[1]||'Nível')}, ${Number(r[2]||0)}, ${Number(r[3]||10)}, { valueStep: ${Number(r[4]||1)}, defaultValue: ${Number(r[5]||0)} });`);else if(t==='dropdown'){const opts=(r[2]||'Opção 1,Opção 2').split(',').map(q).join(', ');L.push(`${f}.dropdown(${q(r[1]||'Modo')}, [${opts}], { defaultValueIndex: ${Number(r[3]||0)} });`);}else L.push(`${f}.textField(${q(r[1]||'Texto')}, ${q(r[2]||'Digite aqui')});`);}L.push(`${f}.show(${c.T}).then((res)=>{ if (res.canceled) return; /* res.formValues */ }).catch(()=>{});`);return L;}},
  flashlight:{ label:'Lanterna projetada', needs:'player', group:'Luz', system:true, fields:[{k:'level',t:'num',label:'Nível da luz (1–15)',def:15},{k:'range',t:'num',label:'Alcance',def:8},{k:'spacing',t:'num',label:'Espaçamento',def:1},{k:'ticks',t:'num',label:'Atualizar a cada (ticks)',def:2}], multi:(c)=>{const lv=Math.max(1,Math.min(15,Math.round(cnum(c.p.level,15)))),v=`lanterna${c.i}`,trail=`luzes${c.i}`;return [`const ${v}=${c.T};`,`let ${trail}=[];`,`const loopLanterna${c.i}=system.runInterval(()=>{`,`  try {`,`    for (const p of ${trail}) { const b=p.dimension.getBlock(p.location); if (b?.typeId.startsWith("minecraft:light_block")) b.setType("minecraft:air"); }`,`    ${trail}=[];`,`    const h=${v}.getHeadLocation(); const d=${v}.getViewDirection();`,`    for (let n=${num(c.p.spacing,1)}; n<=${num(c.p.range,8)}; n+=${num(c.p.spacing,1)}) {`,`      const p={x:Math.floor(h.x+d.x*n),y:Math.floor(h.y+d.y*n),z:Math.floor(h.z+d.z*n)}; const b=${v}.dimension.getBlock(p); if(!b)break;`,`      if (b.typeId!=="minecraft:air" && !b.typeId.startsWith("minecraft:light_block")) break;`,`      b.setType("minecraft:light_block_${lv}"); ${trail}.push({dimension:${v}.dimension,location:p});`,`    }`,`  } catch(e){ system.clearRun(loopLanterna${c.i}); }`,`}, ${Math.max(1,cnum(c.p.ticks,2))});`];}},
  lightFollow:{ label:'Luz acompanha jogador', needs:'player', group:'Luz', system:true, fields:[{k:'level',t:'num',label:'Nível da luz (1–15)',def:15},{k:'dx',t:'num',label:'Offset X',def:0},{k:'dy',t:'num',label:'Offset Y',def:1},{k:'dz',t:'num',label:'Offset Z',def:0},{k:'ticks',t:'num',label:'Atualizar a cada (ticks)',def:2}], multi:(c)=>{const lv=Math.max(1,Math.min(15,Math.round(cnum(c.p.level,15)))),pl=`luzPl${c.i}`,old=`luzOld${c.i}`;return [`const ${pl}=${c.T};`,`let ${old}=null;`,`const loopLuz${c.i}=system.runInterval(()=>{`,`  try {`,`    const p={x:Math.floor(${pl}.location.x+${num(c.p.dx,0)}),y:Math.floor(${pl}.location.y+${num(c.p.dy,1)}),z:Math.floor(${pl}.location.z+${num(c.p.dz,0)})};`,`    if (${old} && (${old}.x!==p.x||${old}.y!==p.y||${old}.z!==p.z)) { const b=${pl}.dimension.getBlock(${old}); if(b?.typeId.startsWith("minecraft:light_block"))b.setType("minecraft:air"); }`,`    const b=${pl}.dimension.getBlock(p); if(b && (b.typeId==="minecraft:air"||b.typeId.startsWith("minecraft:light_block"))) b.setType("minecraft:light_block_${lv}");`,`    ${old}=p;`,`  } catch(e){ system.clearRun(loopLuz${c.i}); }`,`}, ${Math.max(1,cnum(c.p.ticks,2))});`];}},
  followBlock:{ label:'Bloco segue jogador', needs:'player', group:'Bloco', system:true, fields:[{k:'id',t:'text',label:'Bloco',def:'minecraft:glass'},{k:'dx',t:'num',label:'Offset X',def:0},{k:'dy',t:'num',label:'Offset Y',def:-1},{k:'dz',t:'num',label:'Offset Z',def:0},{k:'ticks',t:'num',label:'Atualizar a cada (ticks)',def:2}], multi:(c)=>{const pl=`segPl${c.i}`,old=`segOld${c.i}`,id=q(c.p.id||'minecraft:glass');return [`const ${pl}=${c.T};`,`let ${old}=null;`,`const loopSeg${c.i}=system.runInterval(()=>{`,`  try {`,`    const p={x:Math.floor(${pl}.location.x+${num(c.p.dx,0)}),y:Math.floor(${pl}.location.y+${num(c.p.dy,-1)}),z:Math.floor(${pl}.location.z+${num(c.p.dz,0)})};`,`    if (${old} && (${old}.x!==p.x||${old}.y!==p.y||${old}.z!==p.z)) { const b=${pl}.dimension.getBlock(${old}); if(b?.typeId===${id})b.setType("minecraft:air"); }`,`    const b=${pl}.dimension.getBlock(p); if(b?.typeId==="minecraft:air")b.setType(${id});`,`    ${old}=p;`,`  } catch(e){ system.clearRun(loopSeg${c.i}); }`,`}, ${Math.max(1,cnum(c.p.ticks,2))});`];}}
});

/* FORJA_NATIVE_V35_END */

'''

src=src.replace(marker,patch+marker,1)
p.write_text(src,encoding='utf-8')

# Syntax-check every inline script in the decoded editor.
scripts=re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>',src,re.S|re.I)
checked=0
for i,js in enumerate(scripts):
    if not js.strip():
        continue
    f=pathlib.Path(f'/tmp/forja-check-{i}.js')
    f.write_text(js,encoding='utf-8')
    r=subprocess.run(['node','--check',str(f)],capture_output=True,text=True)
    if r.returncode:
        print(r.stdout,r.stderr)
        raise SystemExit(f'JS syntax failed in inline script {i}')
    checked+=1
print('inline scripts syntax OK:',checked)

legacy=pathlib.Path('legacy.html').read_text(encoding='utf-8')
encoded=base64.b64encode(src.encode('utf-8')).decode('ascii')
legacy,n=re.subn(r'(<script type="text/plain" id="src-scripts">).*?(</script>)',lambda m:m.group(1)+encoded+m.group(2),legacy,count=1,flags=re.S)
if n!=1:
    raise SystemExit('failed to repack src-scripts')
legacy=legacy.replace('v3.2.1','v'+VERSION).replace('Forja v3.2.1','Forja v'+VERSION)
pathlib.Path('legacy.html').write_text(legacy,encoding='utf-8')

index=f'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#11131a">
<title>Script Forja v{VERSION}</title>
<style>html,body{{width:100%;height:100%;margin:0;background:#0d0f14;overflow:hidden}}iframe{{display:block;width:100%;height:100%;border:0}}</style>
</head>
<body><iframe src="./legacy.html?v={VERSION}" title="Script Forja v{VERSION}"></iframe></body>
</html>
'''
pathlib.Path('index.html').write_text(index,encoding='utf-8')

report={
  'version':VERSION,
  'triggers':['A cada intervalo','Entidade recebe dano do player','Jogador olha para entidade','Jogador entrou na coordenada','Jogador saiu da área','Jogador encostou na entidade','Entidade encosta na parede','Entidade está escalando','Entidade está nadando'],
  'conditions':['Está olhando para entidade','Está encostando em entidade','Está dentro da coordenada/área','Está encostando na parede','Está escalando','Está nadando'],
  'actions':['Colocar bloco','Remover bloco','Executar comando','Adicionar tag','Colocar baú com itens','Adicionar formulário livre','Lanterna projetada','Luz acompanha jogador','Bloco segue jogador']
}
pathlib.Path('native-v35-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
