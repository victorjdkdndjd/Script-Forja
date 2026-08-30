from pathlib import Path
import base64, re

VERSION='3.6.0'
p=Path('decoded-scripts.html')
src=p.read_text(encoding='utf-8')

BEGIN='/* FORJA_SYSTEMS_V360_BEGIN */'
END='/* FORJA_SYSTEMS_V360_END */'
if BEGIN in src and END in src:
    src=re.sub(re.escape(BEGIN)+r'.*?'+re.escape(END)+r'\n?', '', src, flags=re.S)

block=r'''
/* FORJA_SYSTEMS_V360_BEGIN */
function forjaSysUid(c,prefix='sys'){
  return (prefix+'_'+String(c.actionId||c.i||'x')).replace(/[^a-zA-Z0-9_]/g,'_');
}
function forjaSysId(v,def='forja'){
  const s=String(v||def).replace(/[^a-zA-Z0-9_.-]/g,'_');
  return s||def;
}
function forjaSysKey(v,def='dado'){
  const s=String(v||def).replace(/[^a-zA-Z0-9_.:-]/g,'_');
  return s||def;
}
Object.assign(ACTIONS, {
  sysTimer:{ label:'Sistema de cronômetro', needs:'player', group:'Sistema', system:true,
    fields:[{k:'name',t:'text',label:'Nome',def:'principal'},{k:'mode',t:'select',label:'Ação',def:'toggle',opts:[['toggle','Ligar / desligar'],['start','Iniciar / reiniciar'],['stop','Parar']]},{k:'show',t:'bool',label:'Mostrar no actionbar',def:true}],
    multi:(c)=>{const u=forjaSysUid(c,'timer'),name=forjaSysKey(c.p.name,'principal'),mode=c.p.mode||'toggle';const L=[`const __pl_${u}=${c.T};`,`const __timers_${u}=globalThis.__forjaTimers||(globalThis.__forjaTimers=new Map());`,`const __tk_${u}=${q(name)}+":"+__pl_${u}.id;`,`const __old_${u}=__timers_${u}.get(__tk_${u});`];if(mode==='stop'||mode==='toggle')L.push(`if (__old_${u}) { try{system.clearRun(__old_${u}.run)}catch(e){} __timers_${u}.delete(__tk_${u}); ${c.p.show!==false?`try{__pl_${u}.onScreenDisplay.setActionBar("§7Cronômetro parado: §f"+__old_${u}.sec+"s")}catch(e){}`:''} }`);if(mode==='stop')return L;if(mode==='toggle')L.push(`else {`);else L.push(`{ if(__old_${u}){try{system.clearRun(__old_${u}.run)}catch(e){}}`);L.push(`  const __st_${u}={sec:0,run:0};`,`  __timers_${u}.set(__tk_${u},__st_${u});`,`  __st_${u}.run=system.runInterval(()=>{ __st_${u}.sec++; ${c.p.show!==false?`try{__pl_${u}.onScreenDisplay.setActionBar("§e${name}: §f"+__st_${u}.sec+"s")}catch(e){}`:''} },20);`,`}`);return L;}},

  sysCountdown:{ label:'Sistema de contagem regressiva', needs:'player', group:'Sistema', system:true,
    fields:[{k:'seconds',t:'num',label:'Segundos',def:10},{k:'end',t:'text',label:'Mensagem ao terminar',def:'§aTempo encerrado!'},{k:'toggle',t:'bool',label:'Segunda execução desliga',def:true}],
    multi:(c)=>{const u=forjaSysUid(c,'count'),sec=Math.max(1,Math.round(cnum(c.p.seconds,10)));return [`const __pl_${u}=${c.T};`,`const __counts_${u}=globalThis.__forjaCountdowns||(globalThis.__forjaCountdowns=new Map());`,`const __ck_${u}=${q(String(c.actionId||u))}+":"+__pl_${u}.id;`,`const __co_${u}=__counts_${u}.get(__ck_${u});`,`if (__co_${u}${c.p.toggle===false?' && false':''}) { try{system.clearRun(__co_${u}.run)}catch(e){} __counts_${u}.delete(__ck_${u}); try{__pl_${u}.onScreenDisplay.setActionBar("§7Contagem cancelada")}catch(e){} } else {`,`  const __st_${u}={left:${sec},run:0}; __counts_${u}.set(__ck_${u},__st_${u});`,`  try{__pl_${u}.onScreenDisplay.setActionBar("§e"+__st_${u}.left+"s")}catch(e){}` ,`  __st_${u}.run=system.runInterval(()=>{ __st_${u}.left--; if(__st_${u}.left<=0){ try{system.clearRun(__st_${u}.run)}catch(e){} __counts_${u}.delete(__ck_${u}); try{__pl_${u}.sendMessage(${q(c.p.end||'§aTempo encerrado!')})}catch(e){} return;} try{__pl_${u}.onScreenDisplay.setActionBar("§e"+__st_${u}.left+"s")}catch(e){} },20);`,`}`];}},

  sysCooldown:{ label:'Sistema de cooldown', needs:'player', group:'Sistema', system:true,
    fields:[{k:'key',t:'text',label:'ID do cooldown',def:'habilidade'},{k:'seconds',t:'num',label:'Segundos',def:5},{k:'mode',t:'select',label:'Ação',def:'set',opts:[['set','Aplicar / reiniciar'],['clear','Remover']]},{k:'msg',t:'bool',label:'Mostrar tempo',def:true}],
    multi:(c)=>{const k='forja:cooldown_'+forjaSysKey(c.p.key,'habilidade'),ticks=Math.max(1,Math.round(cnum(c.p.seconds,5)*20));if(c.p.mode==='clear')return [`try{${c.T}.setDynamicProperty(${q(k)},0)}catch(e){}`];return [`const __cdEnd=system.currentTick+${ticks};`,`try{${c.T}.setDynamicProperty(${q(k)},__cdEnd)}catch(e){}`,c.p.msg!==false?`try{${c.T}.sendMessage("§7Cooldown: §f${Math.round(ticks/20)}s")}catch(e){}`:''];}},

  sysTask:{ label:'Sistema de tarefas', needs:'player', group:'Sistema',
    fields:[{k:'id',t:'text',label:'ID da tarefa',def:'tarefa1'},{k:'text',t:'text',label:'Descrição',def:'Encontre o objetivo'},{k:'progress',t:'num',label:'Progresso',def:0},{k:'status',t:'select',label:'Estado',def:'ativa',opts:[['ativa','Ativa'],['concluida','Concluída'],['falhou','Falhou']]}],
    multi:(c)=>{const k=forjaSysKey(c.p.id,'tarefa1');return [`try{${c.T}.setDynamicProperty(${q('forja:task_'+k+'_text')},${q(c.p.text||'')});${c.T}.setDynamicProperty(${q('forja:task_'+k+'_progress')},${num(c.p.progress,0)});${c.T}.setDynamicProperty(${q('forja:task_'+k+'_status')},${q(c.p.status||'ativa')});}catch(e){}`];}},

  sysObjective:{ label:'Sistema de objetivos', needs:'player', group:'Sistema',
    fields:[{k:'id',t:'text',label:'Objetivo / scoreboard',def:'objetivos'},{k:'display',t:'select',label:'Mostrar em',def:'none',opts:[['none','Não mostrar'],['sidebar','Lateral'],['list','Lista'],['belowname','Abaixo do nome']]}],
    multi:(c)=>{const id=forjaSysId(c.p.id,'objetivos'),L=[`let __obj=world.scoreboard.getObjective(${q(id)}); if(!__obj) try{__obj=world.scoreboard.addObjective(${q(id)},${q(id)})}catch(e){}`];if(c.p.display&&c.p.display!=='none')L.push(`try{${c.T}.runCommand(${q('scoreboard objectives setdisplay '+c.p.display+' '+id)})}catch(e){}`);return L;}},

  sysPoints:{ label:'Sistema de pontos', needs:'player', group:'Sistema',
    fields:[{k:'id',t:'text',label:'Placar',def:'pontos'},{k:'amount',t:'num',label:'Somar',def:1}], multi:(c)=>{const id=forjaSysId(c.p.id,'pontos');return [`let __o=world.scoreboard.getObjective(${q(id)});if(!__o)try{__o=world.scoreboard.addObjective(${q(id)},${q(id)})}catch(e){}`,`try{__o?.addScore(${c.T},${num(c.p.amount,1)})}catch(e){}`];}},
  sysCoins:{ label:'Sistema de moedas', needs:'player', group:'Sistema',
    fields:[{k:'id',t:'text',label:'Placar de moedas',def:'moedas'},{k:'amount',t:'num',label:'Somar (negativo tira)',def:1}], multi:(c)=>{const id=forjaSysId(c.p.id,'moedas');return [`let __o=world.scoreboard.getObjective(${q(id)});if(!__o)try{__o=world.scoreboard.addObjective(${q(id)},${q(id)})}catch(e){}`,`try{__o?.addScore(${c.T},${num(c.p.amount,1)})}catch(e){}`];}},
  sysLevels:{ label:'Sistema de níveis', needs:'player', group:'Sistema',
    fields:[{k:'id',t:'text',label:'Placar de nível',def:'nivel'},{k:'amount',t:'num',label:'Somar níveis',def:1}], multi:(c)=>{const id=forjaSysId(c.p.id,'nivel');return [`let __o=world.scoreboard.getObjective(${q(id)});if(!__o)try{__o=world.scoreboard.addObjective(${q(id)},${q(id)})}catch(e){}`,`try{__o?.addScore(${c.T},${num(c.p.amount,1)})}catch(e){}`];}},
  sysCustomXp:{ label:'Sistema de XP personalizado', needs:'player', group:'Sistema',
    fields:[{k:'xp',t:'text',label:'Placar XP',def:'xp_custom'},{k:'level',t:'text',label:'Placar nível',def:'nivel_custom'},{k:'amount',t:'num',label:'Ganhar XP',def:10},{k:'need',t:'num',label:'XP por nível',def:100}],
    multi:(c)=>{const xp=forjaSysId(c.p.xp,'xp_custom'),lv=forjaSysId(c.p.level,'nivel_custom'),need=Math.max(1,cnum(c.p.need,100));return [`let __xp=world.scoreboard.getObjective(${q(xp)});if(!__xp)try{__xp=world.scoreboard.addObjective(${q(xp)},${q(xp)})}catch(e){}`,`let __lv=world.scoreboard.getObjective(${q(lv)});if(!__lv)try{__lv=world.scoreboard.addObjective(${q(lv)},${q(lv)})}catch(e){}`,`try{__xp?.addScore(${c.T},${num(c.p.amount,10)});let __v=__xp?.getScore(${c.T})||0;while(__v>=${need}){__xp.setScore(${c.T},__v-${need});__lv?.addScore(${c.T},1);__v-= ${need};}}catch(e){}`];}},
  sysRanking:{ label:'Sistema de ranking', needs:'player', group:'Sistema',
    fields:[{k:'id',t:'text',label:'Placar',def:'pontos'},{k:'slot',t:'select',label:'Mostrar em',def:'sidebar',opts:[['sidebar','Lateral'],['list','Lista'],['belowname','Abaixo do nome']]}], code:(c)=>`${c.T}.runCommand(${q('scoreboard objectives setdisplay '+(c.p.slot||'sidebar')+' '+forjaSysId(c.p.id,'pontos'))});`},

  sysTeam:{ label:'Sistema de equipes', needs:'player', group:'Sistema',
    fields:[{k:'team',t:'text',label:'Equipe',def:'azul'},{k:'mode',t:'select',label:'Ação',def:'join',opts:[['join','Entrar'],['leave','Sair']]}],
    multi:(c)=>{const tag='team_'+forjaSysKey(c.p.team,'azul');if(c.p.mode==='leave')return [`try{${c.T}.removeTag(${q(tag)})}catch(e){}`];return [`try{for(const __t of ${c.T}.getTags())if(__t.startsWith("team_"))${c.T}.removeTag(__t);${c.T}.addTag(${q(tag)})}catch(e){}`];}},
  sysMatch:{ label:'Sistema de partidas', needs:'player', group:'Sistema',
    fields:[{k:'state',t:'select',label:'Estado da partida',def:'aguardando',opts:[['aguardando','Aguardando'],['iniciando','Iniciando'],['rodando','Em andamento'],['finalizada','Finalizada']]}], code:(c)=>`world.setDynamicProperty("forja:partida_estado",${q(c.p.state||'aguardando')});`},
  sysLobby:{ label:'Sistema de lobby', needs:'player', group:'Sistema',
    fields:[{k:'x',t:'num',label:'X',def:0},{k:'y',t:'num',label:'Y',def:80},{k:'z',t:'num',label:'Z',def:0},{k:'dim',t:'select',label:'Dimensão',def:'overworld',opts:[['overworld','Overworld'],['nether','Nether'],['the_end','The End']]}], code:(c)=>`${c.T}.teleport({x:${num(c.p.x,0)},y:${num(c.p.y,80)},z:${num(c.p.z,0)}},{dimension:world.getDimension(${q(c.p.dim||'overworld')})});`},
  sysQueue:{ label:'Sistema de fila de jogadores', needs:'player', group:'Sistema',
    fields:[{k:'name',t:'text',label:'Nome da fila',def:'principal'},{k:'mode',t:'select',label:'Ação',def:'toggle',opts:[['toggle','Entrar / sair'],['join','Entrar'],['leave','Sair']]}],
    multi:(c)=>{const u=forjaSysUid(c,'queue'),name=forjaSysKey(c.p.name,'principal'),mode=c.p.mode||'toggle';return [`const __qs_${u}=globalThis.__forjaQueues||(globalThis.__forjaQueues=new Map());`,`const __qn_${u}=${q(name)};let __q_${u}=__qs_${u}.get(__qn_${u});if(!__q_${u}){__q_${u}=[];__qs_${u}.set(__qn_${u},__q_${u});}`,`const __qi_${u}=__q_${u}.indexOf(${c.T}.id);`,`if (${q(mode)}==="leave" || (${q(mode)}==="toggle"&&__qi_${u}>=0)) {if(__qi_${u}>=0)__q_${u}.splice(__qi_${u},1);try{${c.T}.sendMessage("§7Saiu da fila") }catch(e){}} else {if(__qi_${u}<0)__q_${u}.push(${c.T}.id);try{${c.T}.sendMessage("§ePosição na fila: §f"+(__q_${u}.indexOf(${c.T}.id)+1))}catch(e){}}`];}},
  sysDraw:{ label:'Sistema de sorteio', needs:'player', group:'Sistema',
    fields:[{k:'min',t:'num',label:'Mínimo',def:1},{k:'max',t:'num',label:'Máximo',def:100},{k:'key',t:'text',label:'Salvar em',def:'sorteio'}], multi:(c)=>{const a=cnum(c.p.min,1),b=cnum(c.p.max,100),k='forja:'+forjaSysKey(c.p.key,'sorteio');return [`const __r=${Math.min(a,b)}+Math.floor(Math.random()*${Math.max(1,Math.abs(b-a)+1)});`,`try{${c.T}.setDynamicProperty(${q(k)},__r);${c.T}.sendMessage("§eSorteio: §f"+__r)}catch(e){}`];}},
  sysVote:{ label:'Sistema de votação', needs:'player', group:'Sistema',
    fields:[{k:'poll',t:'text',label:'ID da votação',def:'votacao1'},{k:'option',t:'text',label:'Opção',def:'sim'}], multi:(c)=>{const k='forja:voto_'+forjaSysKey(c.p.poll,'votacao1')+'_'+forjaSysKey(c.p.option,'sim');return [`const __v=Number(world.getDynamicProperty(${q(k)})||0)+1;`,`world.setDynamicProperty(${q(k)},__v);`,`try{${c.T}.sendMessage("§aVoto registrado: §f${String(c.p.option||'sim').replace(/"/g,'\\"')}")}catch(e){}`];}},

  sysCheckpoint:{ label:'Sistema de checkpoints', needs:'player', group:'Sistema',
    fields:[{k:'id',t:'text',label:'ID do checkpoint',def:'principal'},{k:'mode',t:'select',label:'Ação',def:'save',opts:[['save','Salvar posição'],['load','Voltar ao checkpoint']]}],
    multi:(c)=>{const k='forja:cp_'+forjaSysKey(c.p.id,'principal');if(c.p.mode==='load')return [`try{const __x=${c.T}.getDynamicProperty(${q(k+'_x')}),__y=${c.T}.getDynamicProperty(${q(k+'_y')}),__z=${c.T}.getDynamicProperty(${q(k+'_z')}),__d=${c.T}.getDynamicProperty(${q(k+'_dim')});if(__x!==undefined&&__y!==undefined&&__z!==undefined)${c.T}.teleport({x:Number(__x),y:Number(__y),z:Number(__z)},{dimension:world.getDimension(String(__d||"overworld"))});}catch(e){}`];return [`try{const __l=${c.T}.location;${c.T}.setDynamicProperty(${q(k+'_x')},__l.x);${c.T}.setDynamicProperty(${q(k+'_y')},__l.y);${c.T}.setDynamicProperty(${q(k+'_z')},__l.z);${c.T}.setDynamicProperty(${q(k+'_dim')},${c.T}.dimension.id.replace("minecraft:",""));${c.T}.sendMessage("§aCheckpoint salvo") }catch(e){}`];}},
  sysSpawn:{ label:'Sistema de spawn personalizado', needs:'player', group:'Sistema',
    fields:[{k:'x',t:'num',label:'X',def:0},{k:'y',t:'num',label:'Y',def:80},{k:'z',t:'num',label:'Z',def:0}], code:(c)=>`${c.T}.runCommand(${q('spawnpoint @s '+cnum(c.p.x,0)+' '+cnum(c.p.y,80)+' '+cnum(c.p.z,0))});`},
  sysRespawn:{ label:'Sistema de respawn', needs:'player', group:'Sistema',
    fields:[{k:'x',t:'num',label:'X',def:0},{k:'y',t:'num',label:'Y',def:80},{k:'z',t:'num',label:'Z',def:0},{k:'dim',t:'select',label:'Dimensão',def:'overworld',opts:[['overworld','Overworld'],['nether','Nether'],['the_end','The End']]}], multi:(c)=>[`try{${c.T}.teleport({x:${num(c.p.x,0)},y:${num(c.p.y,80)},z:${num(c.p.z,0)}},{dimension:world.getDimension(${q(c.p.dim||'overworld')})});}catch(e){}`,`try{${c.T}.runCommand(${q('spawnpoint @s '+cnum(c.p.x,0)+' '+cnum(c.p.y,80)+' '+cnum(c.p.z,0))})}catch(e){}`]},
  sysRegion:{ label:'Sistema de regiões', needs:'player', group:'Sistema', fields:[{k:'name',t:'text',label:'Região',def:'spawn'}], code:(c)=>`${c.T}.setDynamicProperty("forja:regiao",${q(c.p.name||'spawn')});`},
  sysZone:{ label:'Sistema de zonas', needs:'player', group:'Sistema', fields:[{k:'name',t:'text',label:'Zona',def:'segura'}], code:(c)=>`${c.T}.setDynamicProperty("forja:zona",${q(c.p.name||'segura')});`},
  sysArea:{ label:'Sistema de áreas', needs:'player', group:'Sistema', fields:[{k:'name',t:'text',label:'Área',def:'principal'}], code:(c)=>`${c.T}.setDynamicProperty("forja:area",${q(c.p.name||'principal')});`},

  sysScheduled:{ label:'Sistema de eventos programados', needs:'player', group:'Sistema', system:true,
    fields:[{k:'seconds',t:'num',label:'Executar depois de (s)',def:5},{k:'cmd',t:'text',label:'Comando',def:'say Evento programado'}], code:(c)=>`system.runTimeout(()=>{try{${c.T}.runCommand(${q(c.p.cmd||'say Evento programado')})}catch(e){}},${Math.max(1,Math.round(cnum(c.p.seconds,5)*20))});`},
  sysWeather:{ label:'Sistema de clima automático', needs:'player', group:'Sistema', system:true,
    fields:[{k:'seconds',t:'num',label:'Trocar a cada (s)',def:60},{k:'mode',t:'select',label:'Modo',def:'cycle',opts:[['cycle','Ciclo clear/rain/thunder'],['random','Aleatório']]}],
    multi:(c)=>{const u=forjaSysUid(c,'weather'),iv=Math.max(20,Math.round(cnum(c.p.seconds,60)*20));return [`const __ws_${u}=globalThis.__forjaWeather||(globalThis.__forjaWeather=new Map());`,`const __wk_${u}=${q(String(c.actionId||u))};const __wo_${u}=__ws_${u}.get(__wk_${u});`,`if(__wo_${u}){try{system.clearRun(__wo_${u})}catch(e){}__ws_${u}.delete(__wk_${u});}else{let __wi_${u}=0;const __wr_${u}=system.runInterval(()=>{const __a=["clear","rain","thunder"];const __w=${q(c.p.mode||'cycle')}==="random"?__a[Math.floor(Math.random()*3)]:__a[(__wi_${u}++)%3];try{world.getDimension("overworld").runCommand("weather "+__w)}catch(e){}},${iv});__ws_${u}.set(__wk_${u},__wr_${u});}`];}},
  sysDayNight:{ label:'Sistema de ciclo dia/noite', needs:'player', group:'Sistema', system:true,
    fields:[{k:'step',t:'num',label:'Avançar tempo',def:20},{k:'ticks',t:'num',label:'A cada ticks',def:20}],
    multi:(c)=>{const u=forjaSysUid(c,'day'),iv=Math.max(1,cnum(c.p.ticks,20));return [`const __ds_${u}=globalThis.__forjaDayCycles||(globalThis.__forjaDayCycles=new Map());const __dk_${u}=${q(String(c.actionId||u))};const __do_${u}=__ds_${u}.get(__dk_${u});`,`if(__do_${u}){try{system.clearRun(__do_${u})}catch(e){}__ds_${u}.delete(__dk_${u});}else{const __dr_${u}=system.runInterval(()=>{try{world.setTimeOfDay((world.getTimeOfDay()+${num(c.p.step,20)})%24000)}catch(e){}},${iv});__ds_${u}.set(__dk_${u},__dr_${u});}`];}},
  sysAutoMessage:{ label:'Sistema de mensagens automáticas', needs:'player', group:'Sistema', system:true,
    fields:[{k:'text',t:'text',label:'Mensagem',def:'§eMensagem automática'},{k:'seconds',t:'num',label:'A cada (s)',def:30},{k:'all',t:'bool',label:'Enviar para todos',def:true}],
    multi:(c)=>{const u=forjaSysUid(c,'msg'),iv=Math.max(20,Math.round(cnum(c.p.seconds,30)*20));return [`const __ms_${u}=globalThis.__forjaAutoMessages||(globalThis.__forjaAutoMessages=new Map());const __mk_${u}=${q(String(c.actionId||u))}+":"+${c.T}.id;const __mo_${u}=__ms_${u}.get(__mk_${u});`,`if(__mo_${u}){try{system.clearRun(__mo_${u})}catch(e){}__ms_${u}.delete(__mk_${u});}else{const __mr_${u}=system.runInterval(()=>{try{${c.p.all===false?`${c.T}.sendMessage(${q(c.p.text||'§eMensagem automática')})`:`world.sendMessage(${q(c.p.text||'§eMensagem automática')})`}}catch(e){}},${iv});__ms_${u}.set(__mk_${u},__mr_${u});}`];}},
  sysNotification:{ label:'Sistema de notificações', needs:'player', group:'Sistema',
    fields:[{k:'text',t:'text',label:'Texto',def:'Nova notificação!'},{k:'mode',t:'select',label:'Mostrar como',def:'actionbar',opts:[['actionbar','Actionbar'],['title','Título'],['chat','Chat']]}],
    multi:(c)=>c.p.mode==='title'?[`try{${c.T}.onScreenDisplay.setTitle(${q(c.p.text||'Nova notificação!')})}catch(e){}`]:c.p.mode==='chat'?[`try{${c.T}.sendMessage(${q(c.p.text||'Nova notificação!')})}catch(e){}`]:[`try{${c.T}.onScreenDisplay.setActionBar(${q(c.p.text||'Nova notificação!')})}catch(e){}`]},

  sysPersistent:{ label:'Sistema de dados persistentes', needs:'player', group:'Sistema',
    fields:[{k:'scope',t:'select',label:'Salvar em',def:'player',opts:[['player','Jogador'],['world','Mundo']]},{k:'key',t:'text',label:'Chave',def:'dado'},{k:'value',t:'text',label:'Valor',def:'1'}],
    code:(c)=>`${c.p.scope==='world'?'world':c.T}.setDynamicProperty(${q('forja:'+forjaSysKey(c.p.key,'dado'))},${q(String(c.p.value??''))});`},
  sysAutoSave:{ label:'Sistema de salvamento automático', needs:'player', group:'Sistema', system:true,
    fields:[{k:'seconds',t:'num',label:'Salvar a cada (s)',def:30}],
    multi:(c)=>{const u=forjaSysUid(c,'save'),iv=Math.max(20,Math.round(cnum(c.p.seconds,30)*20));return [`const __ss_${u}=globalThis.__forjaAutoSaves||(globalThis.__forjaAutoSaves=new Map());const __sk_${u}=${q(String(c.actionId||u))}+":"+${c.T}.id;const __so_${u}=__ss_${u}.get(__sk_${u});`,`if(__so_${u}){try{system.clearRun(__so_${u})}catch(e){}__ss_${u}.delete(__sk_${u});}else{const __sr_${u}=system.runInterval(()=>{try{const l=${c.T}.location;${c.T}.setDynamicProperty("forja:autosave_x",l.x);${c.T}.setDynamicProperty("forja:autosave_y",l.y);${c.T}.setDynamicProperty("forja:autosave_z",l.z);${c.T}.setDynamicProperty("forja:autosave_dim",${c.T}.dimension.id.replace("minecraft:",""));${c.T}.setDynamicProperty("forja:autosave_tick",system.currentTick)}catch(e){}},${iv});__ss_${u}.set(__sk_${u},__sr_${u});}`];}},
  sysRestore:{ label:'Sistema de recuperação de dados', needs:'player', group:'Sistema',
    fields:[{k:'teleport',t:'bool',label:'Voltar para posição salva',def:true}], multi:(c)=>c.p.teleport===false?[`try{${c.T}.sendMessage("§7Último save: §f"+String(${c.T}.getDynamicProperty("forja:autosave_tick")??"nenhum"))}catch(e){}`]:[`try{const x=${c.T}.getDynamicProperty("forja:autosave_x"),y=${c.T}.getDynamicProperty("forja:autosave_y"),z=${c.T}.getDynamicProperty("forja:autosave_z"),d=${c.T}.getDynamicProperty("forja:autosave_dim");if(x!==undefined&&y!==undefined&&z!==undefined)${c.T}.teleport({x:Number(x),y:Number(y),z:Number(z)},{dimension:world.getDimension(String(d||"overworld"))});}catch(e){}`]},
  sysPermission:{ label:'Sistema de permissões', needs:'player', group:'Sistema',
    fields:[{k:'permission',t:'text',label:'Permissão',def:'admin'},{k:'mode',t:'select',label:'Ação',def:'give',opts:[['give','Conceder'],['remove','Remover']]}], code:(c)=>`${c.T}.${c.p.mode==='remove'?'removeTag':'addTag'}(${q('perm_'+forjaSysKey(c.p.permission,'admin'))});`},
  sysLog:{ label:'Sistema de logs', needs:'player', group:'Sistema',
    fields:[{k:'text',t:'text',label:'Log',def:'Ação executada'},{k:'announce',t:'bool',label:'Mostrar no chat',def:false}], multi:(c)=>[`world.setDynamicProperty("forja:last_log",${q(c.p.text||'Ação executada')});`,c.p.announce===true?`world.sendMessage("§8[LOG] §7"+${q(c.p.text||'Ação executada')});`:``]},
  sysAfk:{ label:'Sistema de AFK / inatividade', needs:'player', group:'Sistema', system:true,
    fields:[{k:'seconds',t:'num',label:'Segundos parado',def:60},{k:'tag',t:'text',label:'Tag AFK',def:'afk'}],
    multi:(c)=>{const u=forjaSysUid(c,'afk'),ticks=Math.max(20,Math.round(cnum(c.p.seconds,60)*20)),tag=forjaSysKey(c.p.tag,'afk');return [`const __as_${u}=globalThis.__forjaAfk||(globalThis.__forjaAfk=new Map());const __ak_${u}=${q(String(c.actionId||u))}+":"+${c.T}.id;const __ao_${u}=__as_${u}.get(__ak_${u});`,`if(__ao_${u}){try{system.clearRun(__ao_${u}.run)}catch(e){}__as_${u}.delete(__ak_${u});try{${c.T}.removeTag(${q(tag)})}catch(e){}}else{const __st_${u}={x:${c.T}.location.x,y:${c.T}.location.y,z:${c.T}.location.z,last:system.currentTick,run:0};__st_${u}.run=system.runInterval(()=>{try{const l=${c.T}.location;const moved=Math.hypot(l.x-__st_${u}.x,l.y-__st_${u}.y,l.z-__st_${u}.z)>.15;if(moved){__st_${u}.x=l.x;__st_${u}.y=l.y;__st_${u}.z=l.z;__st_${u}.last=system.currentTick;${c.T}.removeTag(${q(tag)});}else if(system.currentTick-__st_${u}.last>=${ticks})${c.T}.addTag(${q(tag)});}catch(e){}},20);__as_${u}.set(__ak_${u},__st_${u});}`];}},

  sysReward:{ label:'Sistema de recompensas', needs:'player', group:'Sistema', imports:['ItemStack'],
    fields:[{k:'item',t:'text',label:'Item',def:'minecraft:diamond'},{k:'qty',t:'num',label:'Quantidade',def:1},{k:'coins',t:'num',label:'Moedas extras',def:0},{k:'obj',t:'text',label:'Placar de moedas',def:'moedas'}],
    multi:(c)=>{const id=forjaSysId(c.p.obj,'moedas');return [`try{${c.T}.getComponent("minecraft:inventory")?.container?.addItem(new ItemStack(${q(c.p.item||'minecraft:diamond')},Math.max(1,Math.min(64,${num(c.p.qty,1)}))))}catch(e){}`,`let __rw=world.scoreboard.getObjective(${q(id)});if(!__rw)try{__rw=world.scoreboard.addObjective(${q(id)},${q(id)})}catch(e){}`,`if(${num(c.p.coins,0)}!==0)try{__rw?.addScore(${c.T},${num(c.p.coins,0)})}catch(e){}`];}},
  sysShop:{ label:'Sistema de loja / compra', needs:'player', group:'Sistema', imports:['ItemStack'],
    fields:[{k:'item',t:'text',label:'Item',def:'minecraft:apple'},{k:'qty',t:'num',label:'Quantidade',def:1},{k:'price',t:'num',label:'Preço',def:10},{k:'obj',t:'text',label:'Placar de moedas',def:'moedas'}],
    multi:(c)=>{const id=forjaSysId(c.p.obj,'moedas');return [`let __sh=world.scoreboard.getObjective(${q(id)});if(!__sh)try{__sh=world.scoreboard.addObjective(${q(id)},${q(id)})}catch(e){}`,`try{const __money=__sh?.getScore(${c.T})||0;if(__money>=${num(c.p.price,10)}){__sh.setScore(${c.T},__money-${num(c.p.price,10)});${c.T}.getComponent("minecraft:inventory")?.container?.addItem(new ItemStack(${q(c.p.item||'minecraft:apple')},Math.max(1,Math.min(64,${num(c.p.qty,1)}))));${c.T}.sendMessage("§aCompra realizada");}else ${c.T}.sendMessage("§cMoedas insuficientes");}catch(e){}`];}},
  sysState:{ label:'Sistema de máquina de estados', needs:'entity', group:'Sistema',
    fields:[{k:'machine',t:'text',label:'Máquina',def:'principal'},{k:'state',t:'text',label:'Estado',def:'idle'}], code:(c)=>`${c.T}.setDynamicProperty(${q('forja:state_'+forjaSysKey(c.p.machine,'principal'))},${q(c.p.state||'idle')});`},
  sysEntityManager:{ label:'Sistema de gerenciamento de entidades', needs:'entity', group:'Sistema',
    fields:[{k:'mode',t:'select',label:'Ação',def:'tag',opts:[['tag','Adicionar tag'],['kill','Matar'],['event','Disparar evento']]},{k:'value',t:'text',label:'Tag / evento',def:'gerenciado'}], multi:(c)=>c.p.mode==='kill'?[`try{${c.T}.kill()}catch(e){}`]:c.p.mode==='event'?[`try{${c.T}.triggerEvent(${q(c.p.value||'minecraft:entity_born')})}catch(e){}`]:[`try{${c.T}.addTag(${q(c.p.value||'gerenciado')})}catch(e){}`]},
  sysSequence:{ label:'Sistema de sequência de eventos', needs:'player', group:'Sistema', system:true,
    fields:[{k:'commands',t:'text',label:'Comandos separados por ;',def:'say Etapa 1;say Etapa 2;say Etapa 3'},{k:'ticks',t:'num',label:'Intervalo entre etapas',def:20}], multi:(c)=>{const arr=String(c.p.commands||'').split(';').map(x=>x.trim()).filter(Boolean),iv=Math.max(1,cnum(c.p.ticks,20)),u=forjaSysUid(c,'seq');const L=[];arr.forEach((cmd,i)=>L.push(`system.runTimeout(()=>{try{${c.T}.runCommand(${q(cmd)})}catch(e){}},${i*iv});`));return L;}},
  sysTempBlock:{ label:'Sistema de blocos temporários', needs:'loc', group:'Sistema', system:true,
    fields:[{k:'block',t:'text',label:'Bloco temporário',def:'minecraft:glass'},{k:'seconds',t:'num',label:'Duração (s)',def:5}], multi:(c)=>{const u=forjaSysUid(c,'tmp');return [`const __p_${u}={x:Math.floor(${c.L}.x),y:Math.floor(${c.L}.y),z:Math.floor(${c.L}.z)};const __b_${u}=${c.D}.getBlock(__p_${u});const __old_${u}=__b_${u}?.typeId||"minecraft:air";`,`try{__b_${u}?.setType(${q(c.p.block||'minecraft:glass')})}catch(e){}`,`system.runTimeout(()=>{try{${c.D}.getBlock(__p_${u})?.setType(__old_${u})}catch(e){}},${Math.max(1,Math.round(cnum(c.p.seconds,5)*20))});`];}},
  sysIntervalAction:{ label:'Sistema de execução por intervalo', needs:'player', group:'Sistema', system:true,
    fields:[{k:'cmd',t:'text',label:'Comando',def:'say intervalo'},{k:'ticks',t:'num',label:'Intervalo (ticks)',def:20}], multi:(c)=>{const u=forjaSysUid(c,'int'),iv=Math.max(1,cnum(c.p.ticks,20));return [`const __is_${u}=globalThis.__forjaIntervals||(globalThis.__forjaIntervals=new Map());const __ik_${u}=${q(String(c.actionId||u))}+":"+${c.T}.id;const __io_${u}=__is_${u}.get(__ik_${u});`,`if(__io_${u}){try{system.clearRun(__io_${u})}catch(e){}__is_${u}.delete(__ik_${u});}else{const __ir_${u}=system.runInterval(()=>{try{${c.T}.runCommand(${q(c.p.cmd||'say intervalo')})}catch(e){}},${iv});__is_${u}.set(__ik_${u},__ir_${u});}`];}},
  sysTickAction:{ label:'Sistema de execução por tick', needs:'player', group:'Sistema', system:true,
    fields:[{k:'cmd',t:'text',label:'Comando',def:'effect @s speed 1 0 true'}], multi:(c)=>{const u=forjaSysUid(c,'tick');return [`const __ts_${u}=globalThis.__forjaTicks||(globalThis.__forjaTicks=new Map());const __tk_${u}=${q(String(c.actionId||u))}+":"+${c.T}.id;const __to_${u}=__ts_${u}.get(__tk_${u});`,`if(__to_${u}){try{system.clearRun(__to_${u})}catch(e){}__ts_${u}.delete(__tk_${u});}else{const __tr_${u}=system.runInterval(()=>{try{${c.T}.runCommand(${q(c.p.cmd||'effect @s speed 1 0 true')})}catch(e){}},1);__ts_${u}.set(__tk_${u},__tr_${u});}`];}},
  sysPlayerState:{ label:'Sistema de estados do jogador', needs:'player', group:'Sistema', fields:[{k:'key',t:'text',label:'Estado',def:'modo'},{k:'value',t:'text',label:'Valor',def:'ativo'}], code:(c)=>`${c.T}.setDynamicProperty(${q('forja:player_state_'+forjaSysKey(c.p.key,'modo'))},${q(c.p.value||'ativo')});`},
  sysEntityState:{ label:'Sistema de estados da entidade', needs:'entity', group:'Sistema', fields:[{k:'key',t:'text',label:'Estado',def:'fase'},{k:'value',t:'text',label:'Valor',def:'1'}], code:(c)=>`${c.T}.setDynamicProperty(${q('forja:entity_state_'+forjaSysKey(c.p.key,'fase'))},${q(c.p.value||'1')});`},
  sysLoading:{ label:'Carregamento com tempo definido', needs:'player', group:'Sistema', system:true,
    fields:[{k:'seconds',t:'num',label:'Tempo (s)',def:5},{k:'text',t:'text',label:'Texto',def:'Carregando'},{k:'cmd',t:'text',label:'Comando ao terminar',def:'say Pronto'}], multi:(c)=>{const u=forjaSysUid(c,'load'),sec=Math.max(1,Math.round(cnum(c.p.seconds,5)));return [`let __left_${u}=${sec};try{${c.T}.onScreenDisplay.setActionBar(${q((c.p.text||'Carregando')+': ')}+__left_${u}+"s")}catch(e){}`,`const __lr_${u}=system.runInterval(()=>{__left_${u}--;if(__left_${u}<=0){try{system.clearRun(__lr_${u});${c.T}.runCommand(${q(c.p.cmd||'say Pronto')})}catch(e){}return;}try{${c.T}.onScreenDisplay.setActionBar(${q((c.p.text||'Carregando')+': ')}+__left_${u}+"s")}catch(e){}},20);`];}},
  sysPlayerCount:{ label:'Quantidade de jogadores', needs:'player', group:'Sistema',
    fields:[{k:'count',t:'num',label:'Jogadores necessários',def:2},{k:'cmd',t:'text',label:'Comando quando atingir',def:'say Jogadores suficientes!'}], code:(c)=>`if(world.getAllPlayers().length>=${Math.max(1,cnum(c.p.count,2))})try{${c.T}.runCommand(${q(c.p.cmd||'say Jogadores suficientes!')})}catch(e){}`}
});
/* FORJA_SYSTEMS_V360_END */
'''

anchor='/* =====================================================================\n   GERAÇÃO DE CÓDIGO\n   ===================================================================== */'
if anchor not in src:
    raise SystemExit('generation anchor not found')
src=src.replace(anchor,block+'\n'+anchor,1)

# Pequenas traduções dos nomes principais da nova categoria.
translations={
  'Sistema de cronômetro':'Timer system','Sistema de contagem regressiva':'Countdown system','Sistema de cooldown':'Cooldown system',
  'Sistema de tarefas':'Task system','Sistema de objetivos':'Objective system','Sistema de pontos':'Points system','Sistema de moedas':'Currency system',
  'Sistema de níveis':'Level system','Sistema de XP personalizado':'Custom XP system','Sistema de ranking':'Ranking system','Sistema de equipes':'Team system',
  'Sistema de partidas':'Match system','Sistema de lobby':'Lobby system','Sistema de fila de jogadores':'Player queue system','Sistema de sorteio':'Draw system',
  'Sistema de votação':'Voting system','Sistema de checkpoints':'Checkpoint system','Sistema de spawn personalizado':'Custom spawn system','Sistema de respawn':'Respawn system',
  'Sistema de regiões':'Region system','Sistema de zonas':'Zone system','Sistema de áreas':'Area system','Sistema de eventos programados':'Scheduled events system',
  'Sistema de clima automático':'Automatic weather system','Sistema de ciclo dia/noite':'Day/night cycle system','Sistema de mensagens automáticas':'Automatic messages system',
  'Sistema de notificações':'Notification system','Sistema de dados persistentes':'Persistent data system','Sistema de salvamento automático':'Autosave system',
  'Sistema de recuperação de dados':'Data recovery system','Sistema de permissões':'Permission system','Sistema de logs':'Log system','Sistema de AFK / inatividade':'AFK / inactivity system',
  'Sistema de recompensas':'Reward system','Sistema de loja / compra':'Shop / purchase system','Sistema de máquina de estados':'State machine system',
  'Sistema de gerenciamento de entidades':'Entity management system','Sistema de sequência de eventos':'Event sequence system','Sistema de blocos temporários':'Temporary block system',
  'Sistema de execução por intervalo':'Interval execution system','Sistema de execução por tick':'Tick execution system','Sistema de estados do jogador':'Player state system',
  'Sistema de estados da entidade':'Entity state system','Carregamento com tempo definido':'Timed loading','Quantidade de jogadores':'Player count','Sistema':'System'
}
# Injeta no DICT apenas se houver um dicionário PT/EN localizável.
dict_anchor='  "Ação": "Action",\n'
if dict_anchor in src:
    add=''.join(f'  {k!r}: {v!r},\n'.replace("'",'"') for k,v in translations.items())
    src=src.replace(dict_anchor,dict_anchor+add,1)

p.write_text(src,encoding='utf-8')

# Reempacota a aba Scripts dentro do shell legado.
legacy=Path('legacy.html').read_text(encoding='utf-8')
encoded=base64.b64encode(src.encode('utf-8')).decode('ascii')
legacy,n=re.subn(r'(<script type="text/plain" id="src-scripts">).*?(</script>)',lambda m:m.group(1)+encoded+m.group(2),legacy,count=1,flags=re.S)
if n!=1:
    raise SystemExit('failed to repack src-scripts')
legacy=legacy.replace('v3.5.1','v'+VERSION).replace('3.5.1',VERSION)
Path('legacy.html').write_text(legacy,encoding='utf-8')

index=Path('index.html').read_text(encoding='utf-8')
index=index.replace('v3.5.1','v'+VERSION).replace('3.5.1',VERSION)
Path('index.html').write_text(index,encoding='utf-8')

print('Forja',VERSION,'systems added:',src.count("group:'Sistema'"))
