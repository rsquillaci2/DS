# Tallent Two — Advisory: Branding de Clientes

Repositório de ativos de marca dos clientes de advisory da Tallent Two.
Cada cliente tem sua própria pasta com branding guide, assets visuais e entregáveis produzidos.

---

## Estrutura padrão por cliente

```
advisory/{cliente}/
├── brand/                  ← Branding guide (PDF) + resumo de identidade
│   └── README.md           ← Resumo rápido: cores, tipografia, tom de voz
├── assets/
│   ├── logo/               ← Logos recebidos do cliente (PNG, SVG, AI)
│   └── templates/          ← Templates reutilizáveis (Canva, Figma, PPTX)
└── deliverables/
    ├── cobranding/         ← Logos combinados T2 + cliente, assinatura visual
    ├── presentations/      ← Decks e apresentações entregues
    ├── one-pagers/         ← One-pagers, fichas de produto, sell sheets
    └── social-media/       ← Posts, stories, banners para redes sociais
```

---

## Clientes ativos

| Cliente | Segmento | Status | Branding Guide |
|---------|----------|--------|---------------|
| [Pessoal Saúde](pessoal-saude/) | Operadora de saúde (Medicina de Grupo) | Ativo | v1.0 (Mar 2026) |
| [Vila das Meninas](vila-das-meninas/) | Centro Cultural Gastronômico | Ativo | v1.0 (2026) |

---

## Como adicionar um novo cliente

1. Crie a pasta: `advisory/{slug-do-cliente}/`
2. Copie a estrutura padrão (brand/, assets/, deliverables/)
3. Adicione o branding guide do cliente em `brand/`
4. Crie o `brand/README.md` com o resumo de identidade
5. Atualize a tabela de clientes acima

---

## Convenções

- Nomes de pasta: kebab-case (ex: `pessoal-saude`, `vila-das-meninas`)
- Logos: nomeados como `logo-{variante}.{ext}` (ex: `logo-principal.svg`)
- Entregáveis: prefixar com data `YYYY-MM-{descricao}.{ext}`
- Branding guides: `Branding-Guide-{Cliente}-v{versao}.pdf`

---

> Mantido por: Tallent Two Advisory | GitHub: rsquillaci2
