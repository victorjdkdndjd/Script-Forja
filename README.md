# Forja — Scripts e Componentes

Site estático pronto para publicar no GitHub Pages.

## Publicar no GitHub Pages

1. Crie um repositório novo no GitHub, por exemplo `forja`.
2. Envie `index.html` e `.nojekyll` para a raiz do repositório.
3. Abra **Settings → Pages**.
4. Em **Build and deployment**, escolha **Deploy from a branch**.
5. Selecione a branch **main** e a pasta **/(root)** e salve.
6. Depois da publicação, o endereço normalmente será:
   `https://SEU-USUARIO.github.io/forja/`

## Arquivos

- `index.html` — site completo.
- `.nojekyll` — evita processamento desnecessário pelo Jekyll.

O site usa recursos externos via HTTPS, incluindo JSZip e, na área de Scripts, Google Fonts/documentação externa.
