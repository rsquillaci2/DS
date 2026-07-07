# RankedList

> Lista ordenada com numeração display gigante em cinza-claro. Inspirado em "Most Viewed Today" do The Rio Times.

## Anatomia

```
MOST VIEWED — TODAY                          ← eyebrow (bordeaux)
──────────────────────────────────────────
01   Working Remotely from Brazil…         ← numeric-xl + body link
02   Chile's Economy Shrinks in Q1…
03   Brazilian Police Arrest Banker…
04   Brazil's Copasa Privatization…
05   Argentina Picks Operator…
```

## Tokens

| Slot     | Token                                    |
|----------|------------------------------------------|
| eyebrow  | `typography.eyebrow` + `accent.bordeaux` |
| number   | `typography.numeric-xl` + `neutral.gray-300` |
| title    | `typography.body` (link: `accent.bordeaux` hover) |
| divider  | `border.hair` entre itens                |
| spacing  | `spacing.stack-md` entre itens           |

## Variantes

- **Editorial** — numeração gigante 48px (default).
- **Compact** — numeração 24px, item em uma linha.
- **Boxed** — dentro de `surface.paper` com `radius.lg`.

## Regras

1. Máximo de **7 itens** por lista (regra 7±2).
2. Numeração sempre com dois dígitos (`01`, `02`…) para alinhamento visual.
3. Títulos truncados em 2 linhas com `text-overflow: ellipsis`.
