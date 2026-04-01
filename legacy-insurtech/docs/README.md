# Legacy Insurtech — Design System Técnico
> Versão: 1.0 | Publicado em: https://corretora-legacy.up.railway.app/

---

## Estrutura

```
/docs/
  index.html          ← Página principal
  tokens.html         ← Cores, tipografia, espaçamentos
  buttons.html        ← Variantes de botões
  forms.html          ← Campos, selects, checkboxes
  cards.html          ← Padrões de card
  navigation.html     ← Menus, tabs, breadcrumbs
  feedback.html       ← Alertas, toasts, modais, badges
  tables.html         ← Tabelas de dados
  layout.html         ← Grid e espaçamentos
  dashboard.html      ← KPIs, gráficos, painéis
  templates.html      ← Páginas-modelo prontas
  /assets/
    /css/             ← Estilos globais e tokens CSS
    /fonts/           ← Fontes locais (se houver)
    /icons/           ← Ícones e SVGs
```

---

## Tokens principais (CSS)

```css
:root {
  /* Cores */
  --color-primary:   #284DA4;
  --color-accent:    #9BDF1A;
  --color-surface:   #E4EAF8;
  --color-success:   #16A34A;
  --color-warning:   #CA8A04;
  --color-error:     #DC2626;

  /* Tipografia */
  --font-display: 'Kaisei Tokumin', serif;
  --font-body:    'Roboto', sans-serif;
}
```

---

## Como rodar localmente

Por ser HTML estático, basta abrir o `index.html` no navegador ou usar um servidor local:

```bash
# Com Python
python3 -m http.server 8080

# Com Node
npx serve .
```

---

## Como publicar

O DS está conectado ao Railway via deploy automático do GitHub.
Qualquer push na branch `main` desta pasta atualiza o site publicado.

**URL atual:** https://corretora-legacy.up.railway.app/

---

## Referência de marca

Consulte `/brand/README.md` para tokens de identidade (cores, tipografia, valores).
O DS técnico deve sempre estar em sincronia com o brand guide.
