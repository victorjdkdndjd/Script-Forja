(() => {
  'use strict';

  const VERSION = '3.4.0';
  const outer = document.getElementById('forjaLegacy');
  const mounted = new WeakSet();
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const q = s => JSON.stringify(String(s ?? ''));
  const n = (v,d=0) => Number.isFinite(Number(v)) ? Number(v) : d;
  const clamp = (v,a,b) => Math.max(a,Math.min(b,n(v,a)));
  const uid = () => 'b' + Math.random().toString(36).slice(2,9);
  const safe = s => String(s).replace(/[^a-zA-Z0-9_]/g,'_');

  const BLOCKS = [
    {id:'tick_players',kind:'trigger',group:'Eventos',icon:'⏱️',title:'A cada intervalo',desc:'Executa as ações para cada jogador conectado.',fields:[['interval','Intervalo (ticks)','number','20']]},
    {id:'hurt_player',kind:'trigger',group:'Eventos',icon:'⚔️',title:'Entidade recebe dano do player',desc:'Dispara quando um jogador causa dano em uma entidade.',fields:[['entityId','Entidade (vazio = qualquer)','text','minecraft:zombie']]},
    {id:'look_entity',kind:'trigger',group:'Eventos',icon:'👁️',title:'Jogador olha para entidade',desc:'Raycast na direção do olhar; dispara quando começa a mirar no alvo.',fields:[['entityId','Entidade','text','minecraft:zombie'],['range','Alcance','number','12']]},
    {id:'enter_area',kind:'trigger',group:'Eventos',icon:'🧭',title:'Jogador entrou na coordenada',desc:'Dispara uma vez ao entrar numa região cúbica.',fields:[['x','X','number','0'],['y','Y','number','64'],['z','Z','number','0'],['radius','Raio','number','1']]},
    {id:'leave_area',kind:'trigger',group:'Eventos',icon:'📍',title:'Jogador saiu da área',desc:'Ideal para encaixar “Remover bloco” quando o jogador sair.',fields:[['x','X','number','0'],['y','Y','number','64'],['z','Z','number','0'],['radius','Raio','number','5']]},
    {id:'touch_entity',kind:'trigger',group:'Eventos',icon:'🤝',title:'Jogador encostou na entidade',desc:'Detecta proximidade e dispara ao começar o contato.',fields:[['entityId','Entidade','text','minecraft:zombie'],['radius','Distância','number','1.15']]},
    {id:'wall_entity',kind:'trigger',group:'Eventos',icon:'🧱',title:'Entidade encosta na parede',desc:'Amostra blocos sólidos ao redor da entidade.',fields:[['entityId','Entidade','text','minecraft:zombie'],['distance','Distância lateral','number','0.65'],['interval','Intervalo','number','2']]},
    {id:'climbing',kind:'trigger',group:'Estados',icon:'🪜',title:'Entidade está escalando',desc:'Dispara quando isClimbing passa a verdadeiro.',fields:[['entityId','Entidade','text','minecraft:zombie'],['interval','Intervalo','number','2']]},
    {id:'swimming',kind:'trigger',group:'Estados',icon:'🏊',title:'Entidade está nadando',desc:'Dispara quando isSwimming passa a verdadeiro.',fields:[['entityId','Entidade','text','minecraft:zombie'],['interval','Intervalo','number','2']]},

    {id:'place_block',kind:'action',group:'Blocos',icon:'➕',title:'Colocar bloco',desc:'Coloca um bloco relativo ao jogador/entidade do evento.',fields:[['blockId','Bloco','text','minecraft:stone'],['dx','Offset X','number','0'],['dy','Offset Y','number','-1'],['dz','Offset Z','number','0'],['onlyAir','Somente se for ar','select','sim',['sim','não']]]},
    {id:'remove_block',kind:'action',group:'Blocos',icon:'➖',title:'Remover bloco',desc:'Remove o bloco na posição relativa ao contexto.',fields:[['dx','Offset X','number','0'],['dy','Offset Y','number','-1'],['dz','Offset Z','number','0'],['expected','Somente este ID (vazio = qualquer)','text','']]},
    {id:'command',kind:'action',group:'Ações',icon:'⌨️',title:'Executar comando',desc:'Executa um comando na dimensão do jogador/entidade.',fields:[['command','Comando sem /','text','say Forja 3.4']]},
    {id:'message',kind:'action',group:'Ações',icon:'💬',title:'Enviar mensagem ao jogador',desc:'Envia uma mensagem ao player disponível no evento.',fields:[['text','Mensagem','text','Ação executada!']]},
    {id:'tag',kind:'action',group:'Ações',icon:'🏷️',title:'Adicionar tag',desc:'Adiciona uma tag ao alvo do evento.',fields:[['tag','Tag','text','forja:ativo']]},
    {id:'chest',kind:'action',group:'Inventário',icon:'🧰',title:'Colocar baú com itens',desc:'Baú visual de 27 slots; cada posição vira Container.setItem.',fields:[['dx','Offset X','number','0'],['dy','Offset Y','number','0'],['dz','Offset Z','number','1']],special:'chest'},
    {id:'form',kind:'action',group:'Interface',icon:'🪟',title:'Adicionar formulário livre',desc:'ModalFormData com texto, campos e controles misturados.',fields:[['title','Título','text','Minha Interface'],['elements','Elementos (um por linha)','textarea','header|Título da seção\nlabel|Texto livre\ndivider\ntext|Nome|Digite aqui\ntoggle|Ativado|true\nslider|Nível|0|10|1|5\ndropdown|Modo|Fácil,Médio,Difícil|0']]},

    {id:'flashlight',kind:'service',group:'Luz & Seguidores',icon:'🔦',title:'Lanterna projetada',desc:'Blocos de luz invisíveis seguem a direção do olhar e param em paredes.',fields:[['level','Luz 1–15','number','15'],['range','Alcance','number','7'],['step','Espaçamento','number','1'],['interval','Atualização','number','2']]},
    {id:'light_follow',kind:'service',group:'Luz & Seguidores',icon:'💡',title:'Luz acompanha jogador',desc:'Um bloco de luz invisível acompanha a posição do jogador.',fields:[['level','Luz 1–15','number','15'],['dx','Offset X','number','0'],['dy','Offset Y','number','1'],['dz','Offset Z','number','0'],['interval','Atualização','number','2']]},
    {id:'follow_block',kind:'service',group:'Luz & Seguidores',icon:'🧲',title:'Bloco segue jogador',desc:'Move um bloco junto do jogador e limpa a posição anterior.',fields:[['blockId','Bloco','text','minecraft:glass'],['dx','Offset X','number','0'],['dy','Offset Y','number','-1'],['dz','Offset Z','number','0'],['interval','Atualização','number','2']]}
  ];
  const byId = Object.fromEntries(BLOCKS.map(b => [b.id,b]));

  function defaults(def){
    const values={};
    for(const f of def.fields||[]) values[f[0]]=f[3] ?? '';
    if(def.special==='chest') values.slots={};
    return values;
  }

  function compileAction(node,ctx,b){
    const v=node.values, src=ctx.source || 'player';
    if(node.type==='place_block'){
      b.imports.add('BlockPermutation');
      return `{
  const __src = ${src};
  if (__src) {
    const __p = __src.location;
    const __pos = { x: Math.floor(__p.x)+${n(v.dx)}, y: Math.floor(__p.y)+${n(v.dy,-1)}, z: Math.floor(__p.z)+${n(v.dz)} };
    const __block = __src.dimension.getBlock(__pos);
    if (__block${v.onlyAir==='sim'?' && __block.typeId === "minecraft:air"':''}) __block.setPermutation(BlockPermutation.resolve(${q(v.blockId)}));
  }
}`;
    }
    if(node.type==='remove_block'){
      b.imports.add('BlockPermutation');
      const check=String(v.expected||'').trim()?`__block.typeId === ${q(v.expected)}`:'__block.typeId !== "minecraft:air"';
      return `{
  const __src = ${src};
  if (__src) {
    const __p = __src.location;
    const __block = __src.dimension.getBlock({ x:Math.floor(__p.x)+${n(v.dx)}, y:Math.floor(__p.y)+${n(v.dy,-1)}, z:Math.floor(__p.z)+${n(v.dz)} });
    if (__block && ${check}) __block.setPermutation(BlockPermutation.resolve("minecraft:air"));
  }
}`;
    }
    if(node.type==='command') return `try { (${src})?.dimension.runCommand(${q(v.command)}); } catch {}`;
    if(node.type==='message') return `try { ${ctx.player||'player'}?.sendMessage(${q(v.text)}); } catch {}`;
    if(node.type==='tag') return `try { (${ctx.entity||src})?.addTag(${q(v.tag)}); } catch {}`;
    if(node.type==='chest'){
      b.imports.add('BlockPermutation'); b.imports.add('ItemStack');
      const lines=Object.entries(v.slots||{}).sort((a,c)=>Number(a[0])-Number(c[0])).map(([slot,val])=>{
        const [item,amtRaw]=String(val).split(',');
        const amt=Math.max(1,Math.min(64,Math.round(n(amtRaw,1))));
        return `      __container?.setItem(${Number(slot)}, new ItemStack(${q((item||'minecraft:stone').trim())}, ${amt}));`;
      }).join('\n');
      return `{
  const __src = ${src};
  if (__src) {
    const __p=__src.location;
    const __chest=__src.dimension.getBlock({x:Math.floor(__p.x)+${n(v.dx)},y:Math.floor(__p.y)+${n(v.dy)},z:Math.floor(__p.z)+${n(v.dz,1)}});
    if (__chest) {
      __chest.setPermutation(BlockPermutation.resolve("minecraft:chest"));
      const __container=__chest.getComponent("minecraft:inventory")?.container;
${lines || '      // Nenhum item configurado no HUD do baú.'}
    }
  }
}`;
    }
    if(node.type==='form'){
      b.ui=true;
      const lines=String(v.elements||'').split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
      let body=`const __form = new ModalFormData().title(${q(v.title)});`;
      for(const line of lines){
        const p=line.split('|'), t=(p.shift()||'').toLowerCase();
        if(t==='header') body+=`\n__form.header(${q(p.join('|'))});`;
        else if(t==='label') body+=`\n__form.label(${q(p.join('|'))});`;
        else if(t==='divider') body+=`\n__form.divider();`;
        else if(t==='text') body+=`\n__form.textField(${q(p[0]||'Campo')}, ${q(p[1]||'')});`;
        else if(t==='toggle') body+=`\n__form.toggle(${q(p[0]||'Opção')}, { defaultValue: ${String(p[1]).toLowerCase()==='true'} });`;
        else if(t==='slider') body+=`\n__form.slider(${q(p[0]||'Valor')}, ${n(p[1])}, ${n(p[2],10)}, { valueStep: ${n(p[3],1)}, defaultValue: ${n(p[4])} });`;
        else if(t==='dropdown'){
          const opts=(p[1]||'Opção 1,Opção 2').split(',').map(s=>q(s.trim())).join(', ');
          body+=`\n__form.dropdown(${q(p[0]||'Lista')}, [${opts}], { defaultValueIndex: ${Math.max(0,Math.round(n(p[2])))} });`;
        }
      }
      return `if (${ctx.player||'player'}) {
  try {
    ${body.replace(/\n/g,'\n    ')}
    __form.show(${ctx.player||'player'}).then(__result => {
      if (__result.canceled) return;
      // __result.formValues contém os valores dos controles na ordem adicionada.
    });
  } catch (__e) { console.warn("[Forja] formulário:", __e); }
}`;
    }
    return '// bloco sem compilador';
  }

  function compileChildren(children,ctx,b,indent='  '){
    const out=[];
    for(const child of children||[]){
      const code=compileAction(child,ctx,b);
      out.push(code.split('\n').map(x=>indent+x).join('\n'));
    }
    return out.join('\n');
  }

  function compileTrigger(node,b){
    const v=node.values, s=safe(node.uid);
    b.imports.add('world');
    const actions=(ctx,indent='  ')=>compileChildren(node.children,ctx,b,indent) || `${indent}// Encaixe uma ação aqui.`;
    if(node.type==='tick_players'){
      b.imports.add('system');
      return `system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
${actions({player:'player',source:'player',entity:'player'},'    ')}
  }
}, ${Math.max(1,Math.round(n(v.interval,20)))});`;
    }
    if(node.type==='hurt_player'){
      return `world.afterEvents.entityHurt.subscribe((event) => {
  const entity = event.hurtEntity;
  const player = event.damageSource.damagingEntity;
  if (!player || player.typeId !== "minecraft:player") return;
  if (${q(v.entityId)} && entity.typeId !== ${q(v.entityId)}) return;
${actions({player:'player',entity:'entity',source:'entity'},'  ')}
});`;
    }
    if(node.type==='look_entity'){
      b.imports.add('system');
      return `const looking_${s} = new Map();
system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    const hit = player.getEntitiesFromViewDirection({ maxDistance: ${Math.max(1,n(v.range,12))} }).find(h => h.entity.typeId === ${q(v.entityId)});
    const entity = hit?.entity;
    const before = looking_${s}.get(player.id);
    if (entity && before !== entity.id) {
      looking_${s}.set(player.id, entity.id);
${actions({player:'player',entity:'entity',source:'player'},'      ')}
    } else if (!entity) looking_${s}.delete(player.id);
  }
}, 2);`;
    }
    if(node.type==='enter_area' || node.type==='leave_area'){
      b.imports.add('system');
      const leave=node.type==='leave_area';
      return `const inside_${s}=new Set();
system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    const p=player.location;
    const now=Math.abs(p.x-${n(v.x)})<=${Math.max(.1,n(v.radius,1))} && Math.abs(p.y-${n(v.y,64)})<=${Math.max(.1,n(v.radius,1))} && Math.abs(p.z-${n(v.z)})<=${Math.max(.1,n(v.radius,1))};
    const before=inside_${s}.has(player.id);
    if (now && !before) {
      inside_${s}.add(player.id);${leave?'':`\n${actions({player:'player',entity:'player',source:'player'},'      ')}`}
    } else if (!now && before) {
      inside_${s}.delete(player.id);${leave?`\n${actions({player:'player',entity:'player',source:'player'},'      ')}`:''}
    }
  }
}, 2);`;
    }
    if(node.type==='touch_entity'){
      b.imports.add('system');
      return `const touching_${s}=new Map();
system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    const entity=player.dimension.getEntities({ type:${q(v.entityId)}, location:player.location, maxDistance:${Math.max(.2,n(v.radius,1.15))} }).find(e=>e.id!==player.id);
    const before=touching_${s}.get(player.id);
    if (entity && before!==entity.id) {
      touching_${s}.set(player.id,entity.id);
${actions({player:'player',entity:'entity',source:'player'},'      ')}
    } else if (!entity) touching_${s}.delete(player.id);
  }
}, 2);`;
    }
    if(node.type==='wall_entity'){
      b.imports.add('system');
      const d=Math.max(.2,n(v.distance,.65));
      return `const wall_${s}=new Set();
function solid_${s}(dim,p){const x=dim.getBlock({x:Math.floor(p.x),y:Math.floor(p.y),z:Math.floor(p.z)});return !!x&&x.typeId!=="minecraft:air"&&!x.typeId.includes("water")&&!x.typeId.includes("lava");}
system.runInterval(() => {
  for (const dim of [world.getDimension("overworld"),world.getDimension("nether"),world.getDimension("the_end")]) {
    for (const entity of dim.getEntities({type:${q(v.entityId)}})) {
      const p=entity.location,y=p.y+.6;
      const now=solid_${s}(dim,{x:p.x+${d},y,z:p.z})||solid_${s}(dim,{x:p.x-${d},y,z:p.z})||solid_${s}(dim,{x:p.x,y,z:p.z+${d}})||solid_${s}(dim,{x:p.x,y,z:p.z-${d}});
      if(now&&!wall_${s}.has(entity.id)) { wall_${s}.add(entity.id);
${actions({player:'undefined',entity:'entity',source:'entity'},'        ')}
      } else if(!now) wall_${s}.delete(entity.id);
    }
  }
}, ${Math.max(1,Math.round(n(v.interval,2)))});`;
    }
    if(node.type==='climbing' || node.type==='swimming'){
      b.imports.add('system');
      const prop=node.type==='climbing'?'isClimbing':'isSwimming';
      return `const state_${s}=new Set();
system.runInterval(() => {
  for (const dim of [world.getDimension("overworld"),world.getDimension("nether"),world.getDimension("the_end")]) {
    for (const entity of dim.getEntities({type:${q(v.entityId)}})) {
      const now=!!entity.${prop};
      if(now&&!state_${s}.has(entity.id)) { state_${s}.add(entity.id);
${actions({player:'undefined',entity:'entity',source:'entity'},'        ')}
      } else if(!now) state_${s}.delete(entity.id);
    }
  }
}, ${Math.max(1,Math.round(n(v.interval,2)))});`;
    }
    return '// evento desconhecido';
  }

  function compileService(node,b){
    const v=node.values,s=safe(node.uid); b.imports.add('world'); b.imports.add('system'); b.imports.add('BlockPermutation');
    if(node.type==='flashlight'){
      const level=Math.round(clamp(v.level,1,15)),range=Math.max(1,n(v.range,7)),step=Math.max(.5,n(v.step,1));
      return `const trail_${s}=new Map();
function clear_${s}(list=[]){for(const it of list){try{const x=it.dimension.getBlock(it.location);if(x?.typeId.startsWith("minecraft:light_block"))x.setPermutation(BlockPermutation.resolve("minecraft:air"));}catch{}}}
system.runInterval(() => {
  const alive=new Set();
  for(const player of world.getAllPlayers()){
    alive.add(player.id); clear_${s}(trail_${s}.get(player.id));
    const h=player.getHeadLocation(),d=player.getViewDirection(),next=[],seen=new Set();
    for(let dist=1;dist<=${range};dist+=${step}){
      const p={x:Math.floor(h.x+d.x*dist),y:Math.floor(h.y+d.y*dist),z:Math.floor(h.z+d.z*dist)};
      const k=p.x+":"+p.y+":"+p.z;if(seen.has(k))continue;seen.add(k);
      const x=player.dimension.getBlock(p);if(!x)continue;
      if(x.typeId==="minecraft:air"||x.typeId.startsWith("minecraft:light_block")){x.setPermutation(BlockPermutation.resolve("minecraft:light_block_${level}"));next.push({dimension:player.dimension,location:p});}else break;
    }
    trail_${s}.set(player.id,next);
  }
  for(const [id,list] of trail_${s})if(!alive.has(id)){clear_${s}(list);trail_${s}.delete(id);}
}, ${Math.max(1,Math.round(n(v.interval,2)))});`;
    }
    if(node.type==='light_follow' || node.type==='follow_block'){
      const id=node.type==='light_follow'?`minecraft:light_block_${Math.round(clamp(v.level,1,15))}`:String(v.blockId||'minecraft:glass');
      return `const previous_${s}=new Map();
system.runInterval(() => {
  const alive=new Set();
  for(const player of world.getAllPlayers()){
    alive.add(player.id);const p=player.location;
    const now={x:Math.floor(p.x)+${n(v.dx)},y:Math.floor(p.y)+${n(v.dy,node.type==='light_follow'?1:-1)},z:Math.floor(p.z)+${n(v.dz)}};
    const old=previous_${s}.get(player.id);
    if(old&&(old.x!==now.x||old.y!==now.y||old.z!==now.z)){const x=player.dimension.getBlock(old);if(x?.typeId===${q(id)})x.setPermutation(BlockPermutation.resolve("minecraft:air"));}
    const x=player.dimension.getBlock(now);if(x&&(x.typeId==="minecraft:air"||x.typeId.startsWith("minecraft:light_block")))x.setPermutation(BlockPermutation.resolve(${q(id)}));
    previous_${s}.set(player.id,now);
  }
}, ${Math.max(1,Math.round(n(v.interval,2)))});`;
    }
    return '// serviço desconhecido';
  }

  function compileWorkspace(nodes){
    const b={imports:new Set(),ui:false};
    const sections=[];
    for(const node of nodes){
      const def=byId[node.type]; if(!def) continue;
      if(def.kind==='trigger') sections.push(compileTrigger(node,b));
      else if(def.kind==='service') sections.push(compileService(node,b));
    }
    if(!sections.length) return '// Adicione eventos ou serviços ao workspace visual da Forja.';
    const server=[...b.imports].filter(x=>x!=='ModalFormData').sort();
    let head=server.length?`import { ${server.join(', ')} } from "@minecraft/server";\n`:'';
    if(b.ui) head+='import { ModalFormData } from "@minecraft/server-ui";\n';
    return `${head}\n// Script Forja v${VERSION} — gerado pelo workspace visual\n\n${sections.join('\n\n')}`;
  }

  function mount(win){
    const doc=win.document;if(mounted.has(doc))return;mounted.add(doc);
    const old=doc.getElementById('forja33-btn'); if(old) old.style.display='none';
    const style=doc.createElement('style');
    style.textContent=`
      #forja34-open{position:fixed;right:12px;bottom:12px;z-index:2147483000;border:2px solid #2a2317;background:#b32e28;color:#fff;border-radius:8px;padding:10px 13px;font:800 12px ui-monospace,monospace;box-shadow:3px 3px 0 #2a2317;cursor:pointer}
      #forja34{position:fixed;inset:0;z-index:2147483100;background:#15161b;color:#ede3ce;display:none;font:13px system-ui,sans-serif}#forja34.open{display:grid;grid-template-rows:50px 1fr}
      .f34top{display:flex;align-items:center;gap:8px;padding:7px 10px;background:#2a2317;border-bottom:2px solid #000}.f34top b{font:700 14px ui-monospace,monospace}.f34top .sp{flex:1}.f34top button{border:1px solid #8c7955;background:#dccdad;color:#2a2317;border-radius:6px;padding:7px 9px;font-weight:800;cursor:pointer}.f34top button.hot{background:#b32e28;color:white;border-color:#e76a62}
      .f34grid{min-height:0;display:grid;grid-template-columns:240px minmax(300px,1fr) 330px}.f34palette,.f34inspector{overflow:auto;background:#ede3ce;color:#2a2317}.f34palette{border-right:3px solid #000;padding:8px}.f34inspector{border-left:3px solid #000;padding:10px}.f34work{overflow:auto;padding:18px;background-color:#dccdad;background-image:linear-gradient(#00000008 1px,transparent 1px),linear-gradient(90deg,#00000008 1px,transparent 1px);background-size:20px 20px}
      .f34group{font:800 10px ui-monospace,monospace;text-transform:uppercase;letter-spacing:1px;color:#6b5c40;margin:9px 4px 4px}.f34pal{width:100%;display:flex;gap:7px;align-items:center;text-align:left;margin:4px 0;padding:8px;border:2px solid #7d6d4e;border-radius:6px;background:#f7eedb;color:#2a2317;box-shadow:2px 2px 0 #a08e68;cursor:pointer}.f34pal[data-kind=trigger]{border-left:8px solid #b32e28}.f34pal[data-kind=action]{border-left:8px solid #1e5aa8}.f34pal[data-kind=service]{border-left:8px solid #2e7d46}.f34pal small{display:block;color:#6b5c40;font-size:9px}.f34pal strong{font-size:11px}
      .f34empty{border:2px dashed #8d7a56;border-radius:8px;padding:30px;text-align:center;color:#6b5c40}.f34root{margin:0 0 13px;position:relative}.f34block{position:relative;background:#f4ead4;color:#2a2317;border:2px solid #2a2317;border-radius:7px;box-shadow:3px 3px 0 #8c7955;min-width:230px}.f34block.sel{outline:3px solid #1e5aa8;outline-offset:2px}.f34block.trigger{border-top:8px solid #b32e28}.f34block.service{border-top:8px solid #2e7d46}.f34block.action{border-left:8px solid #1e5aa8;box-shadow:2px 2px 0 #8c7955}.f34head{display:flex;gap:7px;align-items:center;padding:8px;cursor:pointer}.f34head .grow{flex:1}.f34head strong{display:block;font-size:12px}.f34head small{display:block;font-size:9px;color:#6b5c40}.f34mini{border:0;background:#dccdad;color:#2a2317;border-radius:4px;width:25px;height:25px;cursor:pointer;font-weight:900}.f34children{margin:0 9px 10px 24px;border-left:4px solid #b32e28;padding:4px 0 4px 11px;min-height:45px}.f34drop{border:2px dashed #a08e68;border-radius:6px;padding:9px;color:#7a6848;font-size:10px;margin-top:5px}.f34child{margin:5px 0}.f34child .f34head{padding:6px}.f34connector{width:22px;height:7px;background:#1e5aa8;margin:-2px 0 -4px 22px;border:2px solid #2a2317;border-radius:0 0 5px 5px}
      .f34inspector h3{margin:2px 0 3px;font:800 14px ui-monospace,monospace}.f34inspector p{font-size:10px;color:#6b5c40}.f34field{margin:9px 0}.f34field label{display:block;font:700 10px ui-monospace,monospace;margin-bottom:3px}.f34field input,.f34field select,.f34field textarea{width:100%;box-sizing:border-box;border:2px solid #8d7a56;border-radius:5px;background:#fff8e8;padding:7px;color:#2a2317;font:11px ui-monospace,monospace}.f34field textarea{min-height:130px;resize:vertical}.f34code{width:100%;min-height:210px;box-sizing:border-box;background:#15161b;color:#d6d9e0;border:2px solid #000;border-radius:6px;padding:8px;font:10px/1.4 ui-monospace,monospace;resize:vertical}.f34actions{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}.f34actions button{border:2px solid #2a2317;background:#dccdad;color:#2a2317;border-radius:5px;padding:6px 8px;font-size:10px;font-weight:800;cursor:pointer}
      .f34slots{display:grid;grid-template-columns:repeat(9,1fr);gap:3px;margin:8px 0}.f34slot{aspect-ratio:1;border:2px solid #756542;background:#c7b48c;color:#2a2317;padding:0;font-size:8px;font-weight:800;overflow:hidden}.f34slot.filled{background:#e8b96a;border-color:#b32e28}
      #f34toast{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);background:#2a2317;color:#fff;padding:8px 12px;border-radius:6px;opacity:0;pointer-events:none;transition:.15s;z-index:2147483200}#f34toast.on{opacity:1}
      @media(max-width:850px){.f34grid{grid-template-columns:170px 1fr}.f34inspector{position:absolute;right:0;top:50px;bottom:0;width:min(330px,88vw);z-index:5;transform:translateX(100%);transition:.2s}.f34inspector.mobile-open{transform:none}.f34palette{font-size:10px}.f34pal small{display:none}}
      @media(max-width:520px){.f34grid{grid-template-columns:130px 1fr}.f34palette{padding:5px}.f34pal{padding:6px 4px}.f34pal strong{font-size:9px}.f34work{padding:10px}.f34block{min-width:200px}.f34top b{font-size:11px}.f34top button{padding:6px;font-size:10px}}
    `;doc.head.appendChild(style);

    const btn=doc.createElement('button');btn.id='forja34-open';btn.textContent='🧩 Blocos v3.4';doc.body.appendChild(btn);
    const ui=doc.createElement('div');ui.id='forja34';ui.innerHTML=`<div class="f34top"><b>🧩 Script Forja <span style="color:#e76a62">v${VERSION}</span></b><button data-a="clear">Limpar</button><button data-a="example">Exemplo</button><span class="sp"></span><button class="hot" data-a="code">Gerar código</button><button data-a="close">✕</button></div><div class="f34grid"><aside class="f34palette"></aside><main class="f34work"></main><aside class="f34inspector"></aside></div><div id="f34toast"></div>`;doc.body.appendChild(ui);
    const palette=ui.querySelector('.f34palette'),work=ui.querySelector('.f34work'),inspector=ui.querySelector('.f34inspector'),toastEl=ui.querySelector('#f34toast');
    let nodes=[],selected=null,dragPayload=null;
    const toast=t=>{toastEl.textContent=t;toastEl.classList.add('on');win.setTimeout(()=>toastEl.classList.remove('on'),1300)};
    const findNode=id=>{for(const r of nodes){if(r.uid===id)return r;for(const c of r.children||[])if(c.uid===id)return c;}return null};
    const findParent=id=>nodes.find(r=>(r.children||[]).some(c=>c.uid===id));

    function add(type,parentId=null){const def=byId[type];if(!def)return;const node={uid:uid(),type,values:defaults(def),children:def.kind==='trigger'?[]:undefined};if(def.kind==='action'){
        let parent=parentId?findNode(parentId):findNode(selected);if(!parent||byId[parent.type]?.kind!=='trigger'){toast('Selecione um bloco de evento para encaixar a ação');return;}parent.children.push(node);
      } else nodes.push(node);selected=node.uid;render();}
    function remove(id){const p=findParent(id);if(p)p.children=p.children.filter(x=>x.uid!==id);else nodes=nodes.filter(x=>x.uid!==id);if(selected===id)selected=null;render();}
    function moveChild(id,delta){const p=findParent(id);if(!p)return;const i=p.children.findIndex(x=>x.uid===id),j=i+delta;if(j<0||j>=p.children.length)return;[p.children[i],p.children[j]]=[p.children[j],p.children[i]];render();}

    function renderPalette(){palette.innerHTML='';let g='';for(const def of BLOCKS){if(def.group!==g){g=def.group;palette.insertAdjacentHTML('beforeend',`<div class="f34group">${esc(g)}</div>`)}const x=doc.createElement('button');x.className='f34pal';x.dataset.kind=def.kind;x.draggable=true;x.innerHTML=`<span>${def.icon}</span><span><strong>${esc(def.title)}</strong><small>${esc(def.desc)}</small></span>`;x.onclick=()=>add(def.id);x.ondragstart=e=>{dragPayload={type:def.id};e.dataTransfer?.setData('text/plain',def.id)};palette.appendChild(x)}}
    function blockHTML(node,child=false){const d=byId[node.type],sel=node.uid===selected?' sel':'';return `<div class="f34block ${d.kind}${sel}" data-uid="${node.uid}"><div class="f34head" data-select="${node.uid}"><span>${d.icon}</span><span class="grow"><strong>${esc(d.title)}</strong><small>${esc(d.kind==='trigger'?'EVENTO':d.kind==='service'?'SERVIÇO':'AÇÃO')}</small></span>${child?'<button class="f34mini" data-up="'+node.uid+'">↑</button><button class="f34mini" data-down="'+node.uid+'">↓</button>':''}<button class="f34mini" data-del="${node.uid}">×</button></div></div>`}
    function renderWork(){if(!nodes.length){work.innerHTML='<div class="f34empty">Arraste um bloco para cá ou toque nele na paleta.<br><br>Eventos recebem ações encaixadas dentro deles.</div>';return}work.innerHTML='';for(const r of nodes){const wrap=doc.createElement('div');wrap.className='f34root';wrap.innerHTML=blockHTML(r);if(byId[r.type].kind==='trigger'){const ch=doc.createElement('div');ch.className='f34children';ch.dataset.parent=r.uid;for(const c of r.children||[]){const z=doc.createElement('div');z.className='f34child';z.draggable=true;z.dataset.draguid=c.uid;z.innerHTML=blockHTML(c,true)+'<div class="f34connector"></div>';ch.appendChild(z)}ch.insertAdjacentHTML('beforeend','<div class="f34drop">encaixe ações aqui</div>');wrap.appendChild(ch)}work.appendChild(wrap)}
      work.querySelectorAll('[data-select]').forEach(x=>x.onclick=e=>{if(e.target.closest('button'))return;selected=x.dataset.select;render()});work.querySelectorAll('[data-del]').forEach(x=>x.onclick=e=>{e.stopPropagation();remove(x.dataset.del)});work.querySelectorAll('[data-up]').forEach(x=>x.onclick=e=>{e.stopPropagation();moveChild(x.dataset.up,-1)});work.querySelectorAll('[data-down]').forEach(x=>x.onclick=e=>{e.stopPropagation();moveChild(x.dataset.down,1)});
      work.querySelectorAll('[data-draguid]').forEach(x=>x.ondragstart=e=>{dragPayload={uid:x.dataset.draguid};e.dataTransfer?.setData('text/plain',x.dataset.draguid)});
      work.querySelectorAll('.f34children').forEach(z=>{z.ondragover=e=>e.preventDefault();z.ondrop=e=>{e.preventDefault();const p=findNode(z.dataset.parent);if(!p)return;if(dragPayload?.type&&byId[dragPayload.type]?.kind==='action'){add(dragPayload.type,p.uid)}else if(dragPayload?.uid){const c=findNode(dragPayload.uid);const old=findParent(dragPayload.uid);if(c&&byId[c.type]?.kind==='action'){if(old)old.children=old.children.filter(x=>x.uid!==c.uid);p.children.push(c);selected=c.uid;render()}}dragPayload=null}})}

    function renderInspector(){const node=findNode(selected);if(!node){inspector.innerHTML='<h3>Inspector</h3><p>Selecione um bloco para configurar.</p><div class="f34actions"><button data-gen>Gerar código</button></div><textarea class="f34code" readonly></textarea>';wireInspector();return}const def=byId[node.type];let html=`<h3>${def.icon} ${esc(def.title)}</h3><p>${esc(def.desc)}</p>`;for(const [name,label,type,_d,opts] of def.fields||[]){html+=`<div class="f34field"><label>${esc(label)}</label>`;if(type==='select')html+=`<select data-field="${name}">${opts.map(o=>`<option${String(node.values[name])===String(o)?' selected':''}>${esc(o)}</option>`).join('')}</select>`;else if(type==='textarea')html+=`<textarea data-field="${name}">${esc(node.values[name])}</textarea>`;else html+=`<input data-field="${name}" type="${type}" value="${esc(node.values[name])}">`;html+='</div>'}
      if(def.special==='chest'){html+='<div class="f34field"><label>HUD do baú — toque no slot</label><div class="f34slots">';for(let i=0;i<27;i++){const val=node.values.slots?.[i];html+=`<button class="f34slot${val?' filled':''}" data-slot="${i}" title="${esc(val||'')}">${val?esc(String(val).split(',')[0].replace('minecraft:','').slice(0,4)):i}</button>`}html+='</div><small>Formato: minecraft:item,quantidade</small></div>'}
      html+=`<div class="f34actions"><button data-gen>Gerar código</button><button data-copy>Copiar</button><button data-insert>Inserir na Forja</button></div><textarea class="f34code" readonly></textarea>`;inspector.innerHTML=html;wireInspector();}
    function wireInspector(){inspector.querySelectorAll('[data-field]').forEach(x=>x.oninput=()=>{const node=findNode(selected);if(node)node.values[x.dataset.field]=x.value});inspector.querySelectorAll('[data-slot]').forEach(x=>x.onclick=()=>{const node=findNode(selected);if(!node)return;const i=x.dataset.slot,cur=node.values.slots?.[i]||'';const val=win.prompt(`Slot ${i} — item,quantidade`,cur||'minecraft:diamond,1');if(val===null)return;if(!node.values.slots)node.values.slots={};if(val.trim())node.values.slots[i]=val.trim();else delete node.values.slots[i];renderInspector()});const code=()=>{const c=compileWorkspace(nodes),ta=inspector.querySelector('.f34code');if(ta)ta.value=c;return c};inspector.querySelectorAll('[data-gen]').forEach(x=>x.onclick=()=>{code();toast('Código atualizado')});inspector.querySelectorAll('[data-copy]').forEach(x=>x.onclick=async()=>{const c=code();try{await win.navigator.clipboard.writeText(c);toast('Copiado')}catch{toast('Não foi possível copiar')}});inspector.querySelectorAll('[data-insert]').forEach(x=>x.onclick=()=>{const c=code();let ok=false;try{if(win.monaco?.editor?.getModels){const m=win.monaco.editor.getModels()[0];if(m){m.setValue(m.getValue()+'\n\n'+c);ok=true}}}catch{}if(!ok){const tas=[...doc.querySelectorAll('textarea')].filter(t=>!ui.contains(t));if(tas.length){tas.sort((a,b)=>(b.value?.length||0)-(a.value?.length||0));tas[0].value+=(tas[0].value?'\n\n':'')+c;tas[0].dispatchEvent(new Event('input',{bubbles:true}));ok=true}}toast(ok?'Inserido na Forja':'Editor não detectado')})}
    function render(){renderWork();renderInspector()}

    work.ondragover=e=>e.preventDefault();work.ondrop=e=>{if(e.target.closest('.f34children'))return;e.preventDefault();if(dragPayload?.type&&byId[dragPayload.type]?.kind!=='action')add(dragPayload.type);dragPayload=null};
    ui.querySelector('[data-a=close]').onclick=()=>ui.classList.remove('open');ui.querySelector('[data-a=code]').onclick=()=>{const c=compileWorkspace(nodes);const ta=inspector.querySelector('.f34code');if(ta)ta.value=c;inspector.classList.add('mobile-open');toast('Código gerado')};ui.querySelector('[data-a=clear]').onclick=()=>{nodes=[];selected=null;render()};ui.querySelector('[data-a=example]').onclick=()=>{const trig={uid:uid(),type:'look_entity',values:{entityId:'minecraft:zombie',range:'12'},children:[]};trig.children.push({uid:uid(),type:'place_block',values:{blockId:'minecraft:light_block_15',dx:'0',dy:'1',dz:'0',onlyAir:'sim'}});nodes=[{uid:uid(),type:'flashlight',values:{level:'15',range:'7',step:'1',interval:'2'}},trig];selected=trig.uid;render();toast('Exemplo carregado')};btn.onclick=()=>{ui.classList.add('open');render()};
    renderPalette();render();doc.documentElement.dataset.forjaVisual=VERSION;
  }

  function hook(){let doc;try{doc=outer.contentDocument}catch{return}if(!doc)return;const host=doc.getElementById('apphost');if(!host)return;const scan=()=>{for(const frame of host.querySelectorAll('iframe')){if((frame.title||'').toLowerCase().includes('script')){const go=()=>{try{if(frame.contentWindow?.document?.body)mount(frame.contentWindow)}catch(e){console.warn('[Forja 3.4]',e)}};frame.addEventListener('load',go);try{if(frame.contentDocument?.readyState==='complete')go()}catch{}}}};scan();new MutationObserver(scan).observe(host,{childList:true,subtree:true,attributes:true})}
  outer?.addEventListener('load',hook);try{if(outer?.contentDocument?.readyState==='complete')hook()}catch{}
})();
