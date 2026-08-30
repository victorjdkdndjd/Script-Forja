# Forja v3.4.0

Forja de scripts para Minecraft Bedrock com workspace visual encaixável, preservando integralmente a Forja v3.2.1 em `legacy.html` e mantendo os geradores da v3.3 como camada de compatibilidade.

## Novidades v3.4 — blocos visuais

Agora as sugestões da v3.3 podem ser usadas em um **workspace visual**. Eventos recebem ações encaixadas dentro deles, permitindo montar fluxos como:

`Jogador olha para entidade` → `Colocar bloco` → `Executar comando`

ou:

`Jogador saiu da área` → `Remover bloco`

### Eventos e estados
- A cada intervalo.
- Entidade recebe dano do player.
- Jogador olha para uma entidade.
- Jogador entrou em coordenada/região.
- Jogador saiu da área.
- Jogador encostou em entidade.
- Entidade encostou na parede.
- Entidade está escalando (`isClimbing`).
- Entidade está nadando (`isSwimming`).

### Ações encaixáveis
- Colocar bloco.
- Remover bloco.
- Executar comando.
- Enviar mensagem ao jogador.
- Adicionar tag.
- Colocar baú com itens.
- Abrir formulário livre.

### Luz e seguidores
- Lanterna dinâmica projetada na direção do olhar.
- Nível de luz configurável de 1 a 15.
- Luz invisível acompanhando o jogador.
- Bloco comum seguindo o jogador.
- Limpeza da posição anterior ao mover.

### Baú visual
O bloco **Colocar baú com itens** possui um HUD de 27 slots. Cada slot aceita `minecraft:item,quantidade` e o código gerado usa a posição correspondente do container.

### Formulário livre
O bloco de formulário aceita uma lista de elementos mistos, por exemplo:

```text
header|Título
label|Texto livre
divider
text|Nome|Digite aqui
toggle|Ativado|true
slider|Nível|0|10|1|5
dropdown|Modo|Fácil,Médio,Difícil|0
```

### Uso no celular
- Toque em um evento ou serviço para adicionar ao workspace.
- Selecione um evento e toque em uma ação para encaixá-la.
- Também é possível arrastar ações para a área interna do evento em navegadores compatíveis.
- Use ↑ e ↓ para reorganizar ações.
- O inspector permite editar os parâmetros do bloco selecionado.

## Estrutura
- `index.html`: inicializador da v3.4.
- `legacy.html`: Forja v3.2.1 preservada.
- `forja-v3.3.js`: geradores individuais da v3.3, mantidos por compatibilidade.
- `forja-v3.4.js`: workspace visual, blocos encaixáveis e compilador de fluxo.

## GitHub Pages
Publique a branch `main` em **Settings → Pages**. O arquivo principal continua sendo `index.html`.
