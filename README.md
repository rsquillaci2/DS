# Design Systems — Tallent Two Portfolio

Repositório central de Design Systems e Identidade de Marca do portfólio **Tallent Two (T2)**.

Cada empresa do portfólio tem sua própria pasta com dois módulos distintos:
- `/brand` → Identidade de marca: missão, valores, logo, cores, tipografia, tom de voz
- `/docs` → Design System técnico: tokens, componentes, templates HTML

---

## Estrutura do repositório

```
DS/
├── legacy-insurtech/     ✅ Brand + DS completos
├── t2-holding/           🔶 Brand completo · DS a construir
├── nexd/                 🔶 A construir
├── legado-ativos/        🔶 A construir
└── README.md
```

---

## Status por empresa

| Empresa | Identidade de Marca | Design System | DS publicado |
|---------|-------------------|---------------|-------------|
| Legacy Insurtech | ✅ Completo | ✅ Completo | ✅ [Ver site](https://corretora-legacy.up.railway.app/) |
| T2 Holding | ✅ Completo (v1.1) | ❌ A construir | ❌ |
| Nexd | ❌ A construir | ❌ A construir | ❌ |
| Legado Ativos Judiciais | ❌ A construir | ❌ A construir | ❌ |

---

## Como usar este repositório

1. Acesse a pasta da empresa desejada
2. Consulte `/brand/README.md` para identidade de marca
3. Consulte `/docs/` para componentes e tokens do DS técnico
4. Para publicar um DS: conecte a pasta da empresa ao Railway ou Vercel

---

## Convenções

- Versionamento semântico: `v1.0`, `v1.1`, `v2.0`
- DS técnico usa build Vite — assets com hash no nome para cache-busting (ex: `main-7Rht7Cvz.css`)
- Tokens de referência documentados no `/brand/README.md` de cada empresa
- Toda alteração de marca passa por revisão do fundador (Ric)

---

> Mantido por: Tallent Two | GitHub: rsquillaci2
