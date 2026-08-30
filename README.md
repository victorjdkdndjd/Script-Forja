# Forja v3.3.0

Versão bilíngue PT-BR / EN do site, preservando a Forja v3.2.1 e adicionando uma extensão de novos geradores para Minecraft Bedrock Script API.

## Novidades v3.3

### Blocos e luz
- Colocar ou remover bloco automaticamente.
- Bloco seguindo a posição do jogador.
- Remover bloco quando o jogador sai de uma área.
- Lanterna dinâmica com `minecraft:light_block_N`.
- Nível de luz configurável de 1 a 15.
- Projeção da luz para frente usando a direção do olhar.

### Player e entidades
- Entidade recebe dano causado por player.
- Entidade encosta na parede (detector por proximidade lateral).
- Jogador olha para uma entidade usando raycast.
- Jogador entrou em coordenada/região.
- Jogador encostou em entidade.
- Estado `isClimbing`.
- Estado `isSwimming`.

### Inventário e interface
- Gerador de baú com inventário.
- HUD visual de 27 slots na própria Forja para escolher a posição dos itens.
- Formulário avançado com `ModalFormData`: cabeçalho, texto, divisor, campo de texto, toggle, slider e dropdown.

## Estrutura
- `index.html`: inicializador da v3.3.
- `legacy.html`: cópia exata da Forja v3.2.1 anterior, mantida para compatibilidade.
- `forja-v3.3.js`: extensão que adiciona os novos geradores à ferramenta Scripts.

## GitHub Pages
Publique a branch `main` em **Settings → Pages**. O arquivo principal continua sendo `index.html`.
