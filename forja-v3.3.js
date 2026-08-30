(() => {
  'use strict';

  const VERSION = '3.3.0';
  const legacy = document.getElementById('forjaLegacy');
  const boot = document.getElementById('boot');
  const mounted = new WeakSet();

  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const q = (s) => JSON.stringify(String(s ?? ''));
  const num = (v, fallback = 0) => Number.isFinite(Number(v)) ? Number(v) : fallback;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, num(v, a)));

  const FEATURES = [
    {
      id:'auto-block', group:'Blocos & Luz', icon:'🧱', title:'Colocar / remover bloco automaticamente',
      desc:'Coloca ou remove um bloco em uma posição relativa ao jogador a cada intervalo.',
      fields:[
        ['action','Ação','select','colocar',['colocar','remover']],
        ['blockId','Bloco','text','minecraft:stone'],
        ['dx','Offset X','number','0'], ['dy','Offset Y','number','-1'], ['dz','Offset Z','number','0'],
        ['interval','Intervalo (ticks)','number','10']
      ],
      generate:v => `import { world, system, BlockPermutation } from "@minecraft/server";

// Forja v${VERSION} — bloco automático
const CONFIG = {
  acao: ${q(v.action)},
  bloco: ${q(v.blockId)},
  offset: { x: ${num(v.dx)}, y: ${num(v.dy)}, z: ${num(v.dz)} },
  intervalo: ${Math.max(1, num(v.interval, 10))}
};

system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    const p = player.location;
    const pos = {
      x: Math.floor(p.x) + CONFIG.offset.x,
      y: Math.floor(p.y) + CONFIG.offset.y,
      z: Math.floor(p.z) + CONFIG.offset.z
    };
    const block = player.dimension.getBlock(pos);
    if (!block) continue;

    if (CONFIG.acao === "remover") {
      if (block.typeId === CONFIG.bloco) block.setPermutation(BlockPermutation.resolve("minecraft:air"));
    } else if (block.typeId === "minecraft:air") {
      block.setPermutation(BlockPermutation.resolve(CONFIG.bloco));
    }
  }
}, CONFIG.intervalo);`
    },
    {
      id:'flashlight', group:'Blocos & Luz', icon:'🔦', title:'Lanterna — luz projetada para frente',
      desc:'Cria uma sequência de blocos de luz invisíveis na direção em que o jogador olha e remove os antigos.',
      fields:[
        ['level','Nível de luz (1–15)','number','15'],
        ['range','Alcance em blocos','number','6'],
        ['interval','Atualização (ticks)','number','2'],
        ['step','Espaçamento','number','1']
      ],
      generate:v => {
        const level = Math.round(clamp(v.level,1,15));
        const range = Math.max(1, Math.round(num(v.range,6)));
        const interval = Math.max(1, Math.round(num(v.interval,2)));
        const step = Math.max(0.5, num(v.step,1));
        return `import { world, system, BlockPermutation } from "@minecraft/server";

// Forja v${VERSION} — lanterna dinâmica projetada
const LIGHT_ID = "minecraft:light_block_${level}";
const RANGE = ${range};
const STEP = ${step};
const rastros = new Map();

function chave(dim, p) {
  return dim.id + ":" + p.x + ":" + p.y + ":" + p.z;
}

function limpar(lista = []) {
  for (const item of lista) {
    try {
      const b = item.dimension.getBlock(item.location);
      if (b && b.typeId.startsWith("minecraft:light_block")) {
        b.setPermutation(BlockPermutation.resolve("minecraft:air"));
      }
    } catch {}
  }
}

system.runInterval(() => {
  const vivos = new Set();

  for (const player of world.getAllPlayers()) {
    vivos.add(player.id);
    limpar(rastros.get(player.id));

    const head = player.getHeadLocation();
    const dir = player.getViewDirection();
    const novos = [];
    const vistos = new Set();

    for (let d = 1; d <= RANGE; d += STEP) {
      const p = {
        x: Math.floor(head.x + dir.x * d),
        y: Math.floor(head.y + dir.y * d),
        z: Math.floor(head.z + dir.z * d)
      };
      const k = chave(player.dimension, p);
      if (vistos.has(k)) continue;
      vistos.add(k);

      const b = player.dimension.getBlock(p);
      if (!b) continue;
      if (b.typeId === "minecraft:air" || b.typeId.startsWith("minecraft:light_block")) {
        b.setPermutation(BlockPermutation.resolve(LIGHT_ID));
        novos.push({ dimension: player.dimension, location: p });
      } else {
        // Para a projeção quando encontra uma parede/bloco sólido.
        break;
      }
    }
    rastros.set(player.id, novos);
  }

  for (const [id, lista] of rastros) {
    if (!vivos.has(id)) {
      limpar(lista);
      rastros.delete(id);
    }
  }
}, ${interval});`;
      }
    },
    {
      id:'follow-block', group:'Blocos & Luz', icon:'🧲', title:'Bloco seguindo o jogador',
      desc:'Mantém um bloco em um offset do jogador e limpa a posição anterior quando ele se move.',
      fields:[
        ['blockId','Bloco','text','minecraft:glass'],
        ['dx','Offset X','number','0'], ['dy','Offset Y','number','-1'], ['dz','Offset Z','number','0'],
        ['interval','Atualização (ticks)','number','2']
      ],
      generate:v => `import { world, system, BlockPermutation } from "@minecraft/server";

// Forja v${VERSION} — bloco que segue o jogador
const BLOCO = ${q(v.blockId)};
const OFFSET = { x: ${num(v.dx)}, y: ${num(v.dy,-1)}, z: ${num(v.dz)} };
const anterior = new Map();

system.runInterval(() => {
  const ativos = new Set();
  for (const player of world.getAllPlayers()) {
    ativos.add(player.id);
    const p = player.location;
    const atual = {
      x: Math.floor(p.x) + OFFSET.x,
      y: Math.floor(p.y) + OFFSET.y,
      z: Math.floor(p.z) + OFFSET.z
    };
    const old = anterior.get(player.id);

    if (old && (old.x !== atual.x || old.y !== atual.y || old.z !== atual.z)) {
      const oldBlock = player.dimension.getBlock(old);
      if (oldBlock?.typeId === BLOCO) oldBlock.setPermutation(BlockPermutation.resolve("minecraft:air"));
    }

    const block = player.dimension.getBlock(atual);
    if (block && block.typeId === "minecraft:air") block.setPermutation(BlockPermutation.resolve(BLOCO));
    anterior.set(player.id, atual);
  }
}, ${Math.max(1,num(v.interval,2))});`
    },
    {
      id:'leave-area', group:'Blocos & Luz', icon:'📍', title:'Remover bloco ao sair da área',
      desc:'Detecta entrada/saída de uma área e remove um bloco-alvo quando o jogador deixa a região.',
      fields:[
        ['x','Centro X','number','0'], ['y','Centro Y','number','64'], ['z','Centro Z','number','0'],
        ['radius','Raio','number','5'],
        ['bx','Bloco X','number','0'], ['by','Bloco Y','number','64'], ['bz','Bloco Z','number','0'],
        ['blockId','Bloco esperado','text','minecraft:stone']
      ],
      generate:v => `import { world, system, BlockPermutation } from "@minecraft/server";

// Forja v${VERSION} — remove ao sair da área
const AREA = { x:${num(v.x)}, y:${num(v.y,64)}, z:${num(v.z)}, raio:${Math.max(0.5,num(v.radius,5))} };
const ALVO = { x:${num(v.bx)}, y:${num(v.by,64)}, z:${num(v.bz)} };
const BLOCO = ${q(v.blockId)};
const dentro = new Set();

system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    const p = player.location;
    const agora = Math.abs(p.x-AREA.x) <= AREA.raio && Math.abs(p.y-AREA.y) <= AREA.raio && Math.abs(p.z-AREA.z) <= AREA.raio;
    const antes = dentro.has(player.id);

    if (agora && !antes) dentro.add(player.id);
    if (!agora && antes) {
      dentro.delete(player.id);
      const block = player.dimension.getBlock(ALVO);
      if (block?.typeId === BLOCO) block.setPermutation(BlockPermutation.resolve("minecraft:air"));
      // AÇÃO EXTRA AO SAIR DA ÁREA pode ser adicionada aqui.
    }
  }
}, 4);`
    },
    {
      id:'hurt-by-player', group:'Player & Entidade', icon:'⚔️', title:'Entidade recebe dano do player',
      desc:'Evento oficial entityHurt filtrado para dano causado por jogador.',
      fields:[['entityId','ID da entidade (vazio = qualquer)','text','minecraft:zombie']],
      generate:v => `import { world } from "@minecraft/server";

// Forja v${VERSION} — entidade ferida por player
const ENTITY_ID = ${q(v.entityId)};

world.afterEvents.entityHurt.subscribe((event) => {
  const entidade = event.hurtEntity;
  const atacante = event.damageSource.damagingEntity;
  if (!atacante || atacante.typeId !== "minecraft:player") return;
  if (ENTITY_ID && entidade.typeId !== ENTITY_ID) return;

  // AÇÃO: coloque aqui o que acontece quando o player causa dano.
  atacante.sendMessage("Você causou " + event.damage + " de dano em " + entidade.typeId);
});`
    },
    {
      id:'wall-touch', group:'Player & Entidade', icon:'🧱', title:'Entidade encosta na parede',
      desc:'Detector por amostragem dos quatro lados da entidade. Útil como condição de lógica.',
      fields:[
        ['entityId','ID da entidade','text','minecraft:zombie'],
        ['distance','Distância lateral','number','0.6'],
        ['interval','Intervalo (ticks)','number','2']
      ],
      generate:v => `import { world, system } from "@minecraft/server";

// Forja v${VERSION} — aproximação de colisão lateral com parede
const ENTITY_ID = ${q(v.entityId)};
const D = ${Math.max(0.2,num(v.distance,0.6))};
const tocando = new Set();

function blocoSolido(dimension, p) {
  const b = dimension.getBlock({ x: Math.floor(p.x), y: Math.floor(p.y), z: Math.floor(p.z) });
  return !!b && b.typeId !== "minecraft:air" && !b.typeId.includes("water") && !b.typeId.includes("lava");
}

function encostaNaParede(e) {
  const p = e.location;
  const y = p.y + 0.6;
  return blocoSolido(e.dimension,{x:p.x+D,y,z:p.z}) ||
         blocoSolido(e.dimension,{x:p.x-D,y,z:p.z}) ||
         blocoSolido(e.dimension,{x:p.x,y,z:p.z+D}) ||
         blocoSolido(e.dimension,{x:p.x,y,z:p.z-D});
}

system.runInterval(() => {
  for (const dim of [world.getDimension("overworld"), world.getDimension("nether"), world.getDimension("the_end")]) {
    for (const e of dim.getEntities({ type: ENTITY_ID })) {
      const agora = encostaNaParede(e);
      if (agora && !tocando.has(e.id)) {
        tocando.add(e.id);
        // AÇÃO AO ENCOSTAR NA PAREDE
        e.addTag("forja:encostou_parede");
      } else if (!agora && tocando.has(e.id)) {
        tocando.delete(e.id);
        e.removeTag("forja:encostou_parede");
      }
    }
  }
}, ${Math.max(1,num(v.interval,2))});`
    },
    {
      id:'look-entity', group:'Player & Entidade', icon:'👁️', title:'Jogador olha para uma entidade',
      desc:'Usa raycast de visão do player e dispara somente ao começar a olhar para o alvo.',
      fields:[['entityId','ID da entidade','text','minecraft:zombie'],['range','Distância máxima','number','12']],
      generate:v => `import { world, system } from "@minecraft/server";

// Forja v${VERSION} — player olha para entidade
const ENTITY_ID = ${q(v.entityId)};
const olhando = new Map();

system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    let alvo;
    try {
      alvo = player.getEntitiesFromViewDirection({ maxDistance: ${Math.max(1,num(v.range,12))} })
        .find(hit => hit.entity.typeId === ENTITY_ID)?.entity;
    } catch {}

    const old = olhando.get(player.id);
    if (alvo && old !== alvo.id) {
      olhando.set(player.id, alvo.id);
      // AÇÃO AO COMEÇAR A OLHAR
      player.sendMessage("Olhando para: " + alvo.typeId);
    } else if (!alvo) {
      olhando.delete(player.id);
    }
  }
}, 2);`
    },
    {
      id:'enter-coordinate', group:'Player & Entidade', icon:'🧭', title:'Jogador entrou na coordenada',
      desc:'Cria uma região cúbica ao redor de X/Y/Z e dispara uma vez ao entrar.',
      fields:[
        ['x','X','number','0'],['y','Y','number','64'],['z','Z','number','0'],['radius','Raio','number','1']
      ],
      generate:v => `import { world, system } from "@minecraft/server";

// Forja v${VERSION} — player entrou na coordenada/região
const AREA = { x:${num(v.x)}, y:${num(v.y,64)}, z:${num(v.z)}, raio:${Math.max(0.1,num(v.radius,1))} };
const dentro = new Set();

system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    const p = player.location;
    const agora = Math.abs(p.x-AREA.x) <= AREA.raio && Math.abs(p.y-AREA.y) <= AREA.raio && Math.abs(p.z-AREA.z) <= AREA.raio;
    if (agora && !dentro.has(player.id)) {
      dentro.add(player.id);
      // AÇÃO AO ENTRAR
      player.sendMessage("Você entrou na área da Forja.");
    } else if (!agora) {
      dentro.delete(player.id);
    }
  }
}, 2);`
    },
    {
      id:'touch-entity', group:'Player & Entidade', icon:'🤝', title:'Jogador encostou na entidade',
      desc:'Detecta proximidade curta entre player e entidade e dispara uma vez por contato.',
      fields:[['entityId','ID da entidade','text','minecraft:zombie'],['radius','Distância de contato','number','1.1']],
      generate:v => `import { world, system } from "@minecraft/server";

// Forja v${VERSION} — contato player ↔ entidade
const ENTITY_ID = ${q(v.entityId)};
const RAIO = ${Math.max(0.2,num(v.radius,1.1))};
const contatos = new Set();

system.runInterval(() => {
  const atuais = new Set();
  for (const player of world.getAllPlayers()) {
    for (const entidade of player.dimension.getEntities({ type: ENTITY_ID, location: player.location, maxDistance: RAIO })) {
      const key = player.id + ":" + entidade.id;
      atuais.add(key);
      if (!contatos.has(key)) {
        contatos.add(key);
        // AÇÃO AO ENCOSTAR
        player.sendMessage("Encostou em " + entidade.typeId);
      }
    }
  }
  for (const key of [...contatos]) if (!atuais.has(key)) contatos.delete(key);
}, 2);`
    },
    {
      id:'climbing', group:'Player & Entidade', icon:'🪜', title:'Entidade está escalando',
      desc:'Usa a propriedade oficial isClimbing e detecta mudança de estado.',
      fields:[['entityId','ID da entidade','text','minecraft:zombie']],
      generate:v => stateTemplate('isClimbing','escalando','forja:escalando',v.entityId)
    },
    {
      id:'swimming', group:'Player & Entidade', icon:'🏊', title:'Entidade está nadando',
      desc:'Usa a propriedade oficial isSwimming e detecta mudança de estado.',
      fields:[['entityId','ID da entidade','text','minecraft:zombie']],
      generate:v => stateTemplate('isSwimming','nadando','forja:nadando',v.entityId)
    },
    {
      id:'chest', group:'Inventário & Interface', icon:'🧰', title:'Baú com itens — HUD 27 slots',
      desc:'Monte visualmente os 27 slots. O código coloca o baú e preenche cada posição escolhida.',
      special:'chest',
      fields:[
        ['triggerItem','Item que cria o baú','text','minecraft:stick'],
        ['dx','Offset X','number','0'],['dy','Offset Y','number','0'],['dz','Offset Z','number','2']
      ],
      generate:(v,ctx) => chestTemplate(v,ctx.chestSlots)
    },
    {
      id:'form', group:'Inventário & Interface', icon:'🪟', title:'Formulário / Interface avançada',
      desc:'Mistura textos, cabeçalhos, divisores, campos, toggles, sliders e dropdowns em um ModalFormData.',
      fields:[
        ['title','Título','text','Painel da Forja'],
        ['triggerItem','Item que abre','text','minecraft:compass'],
        ['controls','Componentes (um por linha)','textarea','header|Configuração\nlabel|Escolha as opções abaixo\ndivider\ntext|Nome|Digite seu nome\ntoggle|Ativar recurso\nslider|Força|0|100\ndropdown|Modo|Normal,Rápido,Seguro']
      ],
      generate:v => formTemplate(v)
    }
  ];

  function stateTemplate(prop, label, tag, entityId) {
    return `import { world, system } from "@minecraft/server";

// Forja v${VERSION} — entidade está ${label}
const ENTITY_ID = ${q(entityId)};
const ativos = new Set();

system.runInterval(() => {
  for (const dim of [world.getDimension("overworld"), world.getDimension("nether"), world.getDimension("the_end")]) {
    for (const e of dim.getEntities({ type: ENTITY_ID })) {
      const agora = e.${prop};
      if (agora && !ativos.has(e.id)) {
        ativos.add(e.id);
        e.addTag(${q(tag)});
        // AÇÃO AO COMEÇAR
      } else if (!agora && ativos.has(e.id)) {
        ativos.delete(e.id);
        e.removeTag(${q(tag)});
        // AÇÃO AO PARAR
      }
    }
  }
}, 2);`;
  }

  function chestTemplate(v, slots) {
    const filled = [...slots.entries()].sort((a,b)=>a[0]-b[0]);
    const lines = filled.map(([slot,item]) => {
      const [id, amountRaw] = String(item).split(',').map(s=>s.trim());
      const amount = Math.max(1, Math.round(num(amountRaw,1)));
      return `  container.setItem(${slot}, new ItemStack(${q(id || 'minecraft:stone')}, ${amount}));`;
    }).join('\n');
    return `import { world, ItemStack, BlockPermutation } from "@minecraft/server";

// Forja v${VERSION} — baú visual de 27 slots
const ITEM_GATILHO = ${q(v.triggerItem)};
const OFFSET = { x:${num(v.dx)}, y:${num(v.dy)}, z:${num(v.dz,2)} };

function criarBau(player) {
  const p = player.location;
  const pos = { x:Math.floor(p.x)+OFFSET.x, y:Math.floor(p.y)+OFFSET.y, z:Math.floor(p.z)+OFFSET.z };
  const block = player.dimension.getBlock(pos);
  if (!block) return;

  block.setPermutation(BlockPermutation.resolve("minecraft:chest"));
  const inventory = block.getComponent("minecraft:inventory");
  const container = inventory?.container;
  if (!container) return;

  container.clearAll();
${lines || '  // Nenhum item configurado nos slots.'}
}

world.afterEvents.itemUse.subscribe((event) => {
  const player = event.source;
  if (player?.typeId !== "minecraft:player") return;
  if (event.itemStack?.typeId !== ITEM_GATILHO) return;
  criarBau(player);
});`;
  }

  function formTemplate(v) {
    const rows = String(v.controls || '').split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
    const calls = [];
    for (const row of rows) {
      const p = row.split('|').map(s=>s.trim());
      const type = (p.shift() || '').toLowerCase();
      if (type === 'header') calls.push(`  form.header(${q(p[0] || 'Seção')});`);
      else if (type === 'label') calls.push(`  form.label(${q(p[0] || 'Texto')});`);
      else if (type === 'divider') calls.push('  form.divider();');
      else if (type === 'text') calls.push(`  form.textField(${q(p[0] || 'Texto')}, ${q(p[1] || 'Digite aqui')});`);
      else if (type === 'toggle') calls.push(`  form.toggle(${q(p[0] || 'Ativar')});`);
      else if (type === 'slider') calls.push(`  form.slider(${q(p[0] || 'Valor')}, ${num(p[1],0)}, ${num(p[2],100)});`);
      else if (type === 'dropdown') {
        const opts = String(p[1] || 'Opção 1,Opção 2').split(',').map(s=>s.trim()).filter(Boolean);
        calls.push(`  form.dropdown(${q(p[0] || 'Escolha')}, ${JSON.stringify(opts)});`);
      }
    }
    return `import { world } from "@minecraft/server";
import { ModalFormData } from "@minecraft/server-ui";

// Forja v${VERSION} — interface avançada (server-ui 2.x)
const ITEM_GATILHO = ${q(v.triggerItem)};

async function abrirInterface(player) {
  const form = new ModalFormData().title(${q(v.title)});
${calls.join('\n') || '  form.label("Interface vazia — adicione componentes na Forja.");'}
  form.submitButton("Confirmar");

  const resposta = await form.show(player);
  if (resposta.canceled) return;
  const valores = resposta.formValues ?? [];
  // AÇÃO: use os valores dos controles na ordem em que foram adicionados.
  player.sendMessage("Valores: " + JSON.stringify(valores));
}

world.afterEvents.itemUse.subscribe((event) => {
  if (event.source?.typeId !== "minecraft:player") return;
  if (event.itemStack?.typeId !== ITEM_GATILHO) return;
  abrirInterface(event.source).catch(console.warn);
});`;
  }

  function inject(frame) {
    if (!frame || mounted.has(frame)) return;
    const win = frame.contentWindow;
    const doc = frame.contentDocument;
    if (!win || !doc || !doc.body) return;
    mounted.add(frame);

    const style = doc.createElement('style');
    style.textContent = `
      #forja33-btn{position:fixed;right:max(14px,env(safe-area-inset-right));bottom:max(14px,env(safe-area-inset-bottom));z-index:2147483000;border:1px solid rgba(255,255,255,.16);border-radius:16px;padding:11px 14px;background:linear-gradient(135deg,#7c4dff,#4b7cff);color:#fff;font:800 13px system-ui,sans-serif;box-shadow:0 10px 35px #0008;cursor:pointer;letter-spacing:.2px}
      #forja33-btn:hover{filter:brightness(1.08)}
      #forja33-overlay{position:fixed;inset:0;z-index:2147483100;background:#080a0ecc;backdrop-filter:blur(8px);display:none;align-items:center;justify-content:center;padding:12px;box-sizing:border-box;font-family:system-ui,sans-serif;color:#edf1ff}
      #forja33-overlay.open{display:flex}
      #forja33-modal{width:min(1050px,100%);height:min(760px,96vh);background:#121621;border:1px solid #ffffff1c;border-radius:22px;box-shadow:0 28px 80px #000b;overflow:hidden;display:grid;grid-template-rows:auto 1fr}
      .f33-head{display:flex;align-items:center;gap:10px;padding:14px 16px;border-bottom:1px solid #ffffff12;background:#171c29}.f33-head b{font-size:16px}.f33-badge{font-size:11px;padding:4px 7px;border-radius:999px;background:#744cff;color:white}.f33-spacer{flex:1}.f33-x{border:0;background:#ffffff10;color:white;border-radius:10px;width:34px;height:34px;font-size:20px;cursor:pointer}
      .f33-layout{display:grid;grid-template-columns:310px 1fr;min-height:0}.f33-list{overflow:auto;padding:10px;border-right:1px solid #ffffff12;background:#0f131d}.f33-group{font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:1px;color:#8490ad;padding:10px 8px 5px}.f33-card{width:100%;display:grid;grid-template-columns:32px 1fr;gap:8px;text-align:left;border:1px solid transparent;background:transparent;color:#e9edfa;border-radius:13px;padding:9px;margin:2px 0;cursor:pointer}.f33-card:hover{background:#ffffff08}.f33-card.active{background:#6d50ff1f;border-color:#816aff66}.f33-card .ico{font-size:20px}.f33-card strong{display:block;font-size:12px}.f33-card small{display:block;color:#9ba5bc;font-size:10px;margin-top:2px;line-height:1.25}
      .f33-main{overflow:auto;padding:16px}.f33-main h2{margin:0 0 5px;font-size:19px}.f33-main .desc{margin:0 0 16px;color:#a9b2c8;font-size:12px}.f33-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.f33-field{display:flex;flex-direction:column;gap:5px}.f33-field.wide{grid-column:1/-1}.f33-field label{font-size:11px;font-weight:700;color:#b9c2d7}.f33-field input,.f33-field select,.f33-field textarea{width:100%;box-sizing:border-box;background:#0b0e15;border:1px solid #ffffff1a;border-radius:10px;padding:9px 10px;color:#edf1ff;outline:none;font:12px ui-monospace,monospace}.f33-field textarea{min-height:110px;resize:vertical}.f33-field input:focus,.f33-field textarea:focus,.f33-field select:focus{border-color:#8068ff}
      .f33-actions{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}.f33-actions button{border:1px solid #ffffff1c;background:#252c3d;color:#eef2ff;border-radius:10px;padding:9px 12px;font-weight:800;cursor:pointer}.f33-actions button.primary{background:#7054ff;border-color:#8b77ff}.f33-output{width:100%;min-height:230px;box-sizing:border-box;background:#080a0f;border:1px solid #ffffff16;color:#cfe0ff;border-radius:12px;padding:12px;resize:vertical;font:11px/1.45 ui-monospace,SFMono-Regular,Consolas,monospace}
      .f33-slots-wrap{grid-column:1/-1;border:1px solid #ffffff15;border-radius:13px;padding:10px;background:#0c1018}.f33-slots-title{font-size:11px;font-weight:800;margin-bottom:8px;color:#bbc5dc}.f33-slots{display:grid;grid-template-columns:repeat(9,1fr);gap:4px}.f33-slot{aspect-ratio:1;border:1px solid #ffffff1b;border-radius:7px;background:#1c2230;color:#cfd7eb;font:700 9px system-ui;display:grid;place-items:center;cursor:pointer;overflow:hidden;padding:2px}.f33-slot.filled{background:#6048d833;border-color:#8068ff;color:#fff}.f33-note{font-size:10px;color:#8f99b0;margin-top:7px}
      #forja33-toast{position:fixed;left:50%;bottom:70px;z-index:2147483200;transform:translateX(-50%) translateY(8px);background:#222a3a;color:#fff;border:1px solid #ffffff1f;border-radius:10px;padding:9px 12px;font:700 11px system-ui;opacity:0;pointer-events:none;transition:.2s}#forja33-toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
      @media(max-width:720px){#forja33-modal{height:98vh;border-radius:16px}.f33-layout{grid-template-columns:1fr;grid-template-rows:190px 1fr}.f33-list{border-right:0;border-bottom:1px solid #ffffff12}.f33-fields{grid-template-columns:1fr}.f33-card small{display:none}.f33-slot{font-size:8px}.f33-main{padding:12px}}
    `;
    doc.head.appendChild(style);

    const btn = doc.createElement('button');
    btn.id = 'forja33-btn';
    btn.type = 'button';
    btn.textContent = '⚒ Novos blocos v3.3';
    doc.body.appendChild(btn);

    const overlay = doc.createElement('div');
    overlay.id = 'forja33-overlay';
    overlay.innerHTML = `<div id="forja33-modal"><div class="f33-head"><b>⚒ Script Forja</b><span class="f33-badge">v${VERSION}</span><span class="f33-spacer"></span><button class="f33-x" type="button">×</button></div><div class="f33-layout"><div class="f33-list"></div><div class="f33-main"></div></div></div><div id="forja33-toast"></div>`;
    doc.body.appendChild(overlay);

    const list = overlay.querySelector('.f33-list');
    const main = overlay.querySelector('.f33-main');
    const toastEl = overlay.querySelector('#forja33-toast');
    let selected = FEATURES[0];
    const chestSlots = new Map();

    function toast(msg) {
      toastEl.textContent = msg;
      toastEl.classList.add('show');
      win.setTimeout(()=>toastEl.classList.remove('show'),1500);
    }

    function readValues() {
      const out = {};
      main.querySelectorAll('[data-f33-field]').forEach(el => out[el.dataset.f33Field] = el.value);
      return out;
    }

    function generate() {
      const code = selected.generate(readValues(), { chestSlots });
      const output = main.querySelector('.f33-output');
      if (output) output.value = code;
      return code;
    }

    function copyText(text) {
      if (win.navigator.clipboard?.writeText) return win.navigator.clipboard.writeText(text);
      const ta = doc.createElement('textarea');
      ta.value = text; ta.style.position='fixed'; ta.style.opacity='0'; doc.body.appendChild(ta); ta.select();
      doc.execCommand('copy'); ta.remove(); return Promise.resolve();
    }

    function insertIntoExistingEditor(text) {
      try {
        if (win.monaco?.editor?.getModels) {
          const model = win.monaco.editor.getModels()[0];
          if (model) { model.setValue(model.getValue() + '\n\n' + text); return true; }
        }
      } catch {}
      try {
        const cmNode = [...doc.querySelectorAll('.CodeMirror')].find(n => n.CodeMirror);
        if (cmNode?.CodeMirror) { const cm=cmNode.CodeMirror; cm.setValue(cm.getValue()+'\n\n'+text); return true; }
      } catch {}
      try {
        const aceNode = doc.querySelector('.ace_editor');
        if (aceNode && win.ace?.edit) { const ed=win.ace.edit(aceNode); ed.setValue(ed.getValue()+'\n\n'+text,-1); return true; }
      } catch {}
      const textareas = [...doc.querySelectorAll('textarea')].filter(x => !x.classList.contains('f33-output') && !overlay.contains(x));
      if (textareas.length) {
        textareas.sort((a,b)=>(b.value?.length||0)-(a.value?.length||0));
        const ta=textareas[0]; ta.value += (ta.value?'\n\n':'')+text; ta.dispatchEvent(new Event('input',{bubbles:true})); return true;
      }
      const editable = [...doc.querySelectorAll('[contenteditable="true"]')].find(x=>!overlay.contains(x));
      if (editable) { editable.focus(); doc.execCommand('insertText',false,'\n\n'+text); return true; }
      return false;
    }

    function renderList() {
      list.innerHTML = '';
      let group = '';
      for (const f of FEATURES) {
        if (f.group !== group) {
          group = f.group;
          const g=doc.createElement('div'); g.className='f33-group'; g.textContent=group; list.appendChild(g);
        }
        const c=doc.createElement('button'); c.type='button'; c.className='f33-card'+(f.id===selected.id?' active':'');
        c.innerHTML=`<span class="ico">${esc(f.icon)}</span><span><strong>${esc(f.title)}</strong><small>${esc(f.desc)}</small></span>`;
        c.onclick=()=>{ selected=f; renderList(); renderMain(); };
        list.appendChild(c);
      }
    }

    function renderMain() {
      main.innerHTML = `<h2>${esc(selected.icon)} ${esc(selected.title)}</h2><p class="desc">${esc(selected.desc)}</p><div class="f33-fields"></div><div class="f33-actions"><button class="primary" data-act="generate">Gerar código</button><button data-act="copy">Copiar</button><button data-act="insert">Inserir na Forja</button></div><textarea class="f33-output" spellcheck="false" placeholder="O código gerado aparece aqui…"></textarea>`;
      const fields = main.querySelector('.f33-fields');
      for (const [name,label,type,def,options] of selected.fields || []) {
        const wrap=doc.createElement('div'); wrap.className='f33-field'+(type==='textarea'?' wide':'');
        const lab=doc.createElement('label'); lab.textContent=label; wrap.appendChild(lab);
        let input;
        if (type==='select') {
          input=doc.createElement('select');
          for (const o of options||[]) { const op=doc.createElement('option');op.value=o;op.textContent=o;if(o===def)op.selected=true;input.appendChild(op); }
        } else if (type==='textarea') {
          input=doc.createElement('textarea'); input.value=def ?? '';
        } else {
          input=doc.createElement('input'); input.type=type; input.value=def ?? '';
        }
        input.dataset.f33Field=name; wrap.appendChild(input); fields.appendChild(wrap);
      }

      if (selected.special === 'chest') renderChestSlots(fields, chestSlots, doc);
      main.querySelector('[data-act="generate"]').onclick=()=>{generate();toast('Código gerado');};
      main.querySelector('[data-act="copy"]').onclick=()=>copyText(generate()).then(()=>toast('Copiado')); 
      main.querySelector('[data-act="insert"]').onclick=()=>{
        const code=generate();
        if (insertIntoExistingEditor(code)) toast('Código inserido');
        else copyText(code).then(()=>toast('Editor não detectado — código copiado'));
      };
      generate();
    }

    function renderChestSlots(container, slots, d) {
      const wrap=d.createElement('div');wrap.className='f33-slots-wrap';
      wrap.innerHTML='<div class="f33-slots-title">HUD do baú — toque em um slot para definir <code>item,quantidade</code></div><div class="f33-slots"></div><div class="f33-note">Exemplo: <b>minecraft:diamond,32</b>. Deixe vazio para limpar o slot.</div>';
      const grid=wrap.querySelector('.f33-slots');
      for(let i=0;i<27;i++){
        const b=d.createElement('button');b.type='button';b.className='f33-slot'+(slots.has(i)?' filled':'');
        const val=slots.get(i);b.title=val?`Slot ${i}: ${val}`:`Slot ${i}`;b.textContent=val?(String(val).split(',')[0].replace('minecraft:','').slice(0,5)+`\n${i}`):String(i);
        b.onclick=()=>{
          const current=slots.get(i)||'';
          const value=win.prompt(`Slot ${i} — item,quantidade`,current || 'minecraft:diamond,1');
          if(value===null)return;
          if(value.trim())slots.set(i,value.trim());else slots.delete(i);
          renderMain();
        };
        grid.appendChild(b);
      }
      container.appendChild(wrap);
    }

    btn.onclick=()=>{ overlay.classList.add('open'); renderList(); renderMain(); };
    overlay.querySelector('.f33-x').onclick=()=>overlay.classList.remove('open');
    overlay.addEventListener('click',e=>{if(e.target===overlay)overlay.classList.remove('open');});
    doc.addEventListener('keydown',e=>{if(e.key==='Escape')overlay.classList.remove('open');});

    // Sinal discreto para testes/diagnóstico.
    doc.documentElement.dataset.forjaExtension = VERSION;
  }

  function hookLegacy() {
    boot?.classList.add('hide');
    let doc;
    try { doc = legacy.contentDocument; } catch { return; }
    if (!doc) return;
    const host = doc.getElementById('apphost');
    if (!host) return;

    const tryMount = () => {
      const frames = [...host.querySelectorAll('iframe')];
      for (const frame of frames) {
        if ((frame.title || '').toLowerCase().includes('script')) {
          const run=()=>{ try { inject(frame); } catch (e) { console.warn('[Forja v3.3]',e); } };
          frame.addEventListener('load',run,{once:false});
          try { if (frame.contentDocument?.readyState === 'complete') run(); } catch {}
        }
      }
    };
    tryMount();
    new MutationObserver(tryMount).observe(host,{childList:true,subtree:true,attributes:true,attributeFilter:['class','src']});
  }

  legacy.addEventListener('load', hookLegacy);
  if (legacy.contentDocument?.readyState === 'complete') hookLegacy();
})();
