# Design Systems — Tallent Two Portfolio

Repositório central de Design Systems, Identidade de Marca e Branding do portfólio **Tallent Two (T2)**.

Cada empresa do portfólio tem sua própria pasta com módulos distintos:
- `/brand` → Identidade de marca: missão, valores, logo, cores, tipografia, tom de voz
- `/docs` → Design System técnico: tokens, componentes, templates HTML
- `/products` → Marcas/plataformas que não são empresas separadas (ex: SaaS da Nexd)
- `/advisory` → Branding de clientes de advisory (dentro da T2)

---

## Estrutura do repositório

```
DS/
├── legacy-insurtech/         ✅ Brand + DS completos
│   ├── brand/
│   └── docs/
├── t2-holding/               🔶 Brand completo · DS a construir
│   ├── brand/                ✅ Identidade + assets (42 arquivos)
│   └── advisory/             ✅ Branding de clientes de advisory
│       ├── pessoal-saude/
│       └── vila-das-meninas/
├── nexd/                     🔶 Brand em construção
│   ├── brand/                🔶 Identidade institucional (pendente)
│   └── products/
│       └── meetix/           ✅ Branding completo (engenharia reversa)
├── legado-ativos/            🔶 A construir
└── README.md
```

---

## Status por empresa

| Empresa | Identidade de Marca | Design System | DS publicado |
|---------|-------------------|---------------|-------------|
| Legacy Insurtech | ✅ Completo | ✅ Completo | ✅ [Ver site](https://corretora-legacy.up.railway.app/) |
| T2 Holding | ✅ Completo (v1.2) | ❌ A construir | ❌ |
| Nexd Solution | 🔶 Em construção | ❌ A construir | ❌ |
| Legado Ativos Judiciais | ❌ A construir | ❌ A construir | ❌ |

## Produtos / Marcas (não são empresas)

| Marca | Empresa-mãe | Descrição | Branding |
|-------|------------|-----------|----------|
| [Meetix](nexd/products/meetix/) | Nexd Solution | SDR com IA para WhatsApp | ✅ v1.0 |

## Clientes de Advisory (T2)

| Cliente | Segmento | Branding Guide |
|---------|----------|---------------|
| [Pessoal Saúde](t2-holding/advisory/pessoal-saude/) | Operadora de saúde | ✅ v1.0 |
| [Vila das Meninas](t2-holding/advisory/vila-das-meninas/) | Centro Cultural Gastronômico | ✅ v1.0 |

---

## Como usar este repositório

1. Acesse a pasta da empresa desejada
2. Consulte `/brand/README.md` para identidade de marca
3. Consulte `/docs/` para componentes e tokens do DS técnico
4. Para produtos: consulte `{empresa}/products/{produto}/brand/`
5. Para clientes de advisory: consulte `t2-holding/advisory/`
6. Para publicar um DS: conecte a pasta ao Railway ou Vercel

---

## Convenções

- Versionamento semântico: `v1.0`, `v1.1`, `v2.0`
- DS técnico usa build Vite — assets com hash para cache-busting
- Tokens de referência documentados no `/brand/README.md` de cada entidade
- Toda alteração de marca passa por revisão do fundador (Ric)
- Produtos usam `/products/{slug}/` dentro da empresa-mãe
- Clientes de advisory usam `/advisory/{slug}/` dentro da T2

---

> Mantido por: Tallent Two | GitHub: rsquillaci2
