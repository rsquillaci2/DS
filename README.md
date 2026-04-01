# Design Systems — Tallent Two Portfolio

Repositório central de Design Systems e Identidade de Marca do portfólio **Tallent Two (T2)**.

Cada empresa do portfólio tem sua própria pasta com dois módulos distintos:
- `/brand` → Identidade de marca: missão, valores, logo, cores, tipografia, tom de voz
- `/docs` → Design System técnico: tokens, componentes, templates HTML

---

## Estrutura do repositório

```
DS/
├── legacy-insurtech/     ✅ Completo
├── nexd/                 🔶 A construir
├── legado-ativos/        🔶 A construir
├── t2-holding/           🔶 A construir
└── README.md
```

---

## Status por empresa

| Empresa | Identidade de Marca | Design System | DS publicado |
|---------|-------------------|---------------|-------------|
| Legacy Insurtech | ✅ Completo | ✅ Completo | ✅ [Ver site](https://corretora-legacy.up.railway.app/) |
| Nexd | ❓ A verificar | ❌ Ausente | ❌ |
| Legado Ativos Judiciais | ❓ A verificar | ❌ Ausente | ❌ |
| T2 Holding | ❌ A construir | ❌ A construir | ❌ |

---

## Como usar este repositório

1. Acesse a pasta da empresa desejada
2. Consulte `/brand/README.md` para identidade de marca
3. Consulte `/docs/` para componentes e tokens do DS técnico
4. Para publicar um DS: conecte a pasta da empresa ao Railway ou Vercel

---

## Convenções

- Versionamento semântico: `v1.0`, `v1.1`, `v2.0`
- Tokens sempre em `tokens.css` e `tokens.json`
- Toda alteração de marca passa por revisão do fundador (Ric)

---

> Mantido por: Tallent Two | GitHub: rsquillaci2
