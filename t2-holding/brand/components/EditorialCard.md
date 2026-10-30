# EditorialCard

> Card de matéria/insight no estilo jornal premium. Padrão: **eyebrow bordeaux** + **título display** + meta + lead.

## Anatomia

```
┌────────────────────────────────────────────┐
│ MARKETS                              ← eyebrow (uppercase, bordeaux)
│                                          
│ Brazil's Market Just Repriced the    ← título (Dejanire Headline, h1/h2)
│ Easing Cycle                             "Repriced" pode receber italic-accent
│                                          (Dejanire Italic + bordeaux)
│ By Iolanda Fonseca · May 18, 2026     ← meta (caption, gray-600)
│ · 5 min read                              tag pill em surface.cream
│                                          
│ Lead opcional em itálico (Dejanire   ← lead (text italic, 20px)
│ Text), 2–3 linhas no máximo.
└────────────────────────────────────────────┘
```

## Tokens

| Slot      | Token                          |
|-----------|--------------------------------|
| eyebrow   | `typography.eyebrow` + `accent.bordeaux` |
| title     | `typography.h1` ou `h2`        |
| accent    | `accent.bordeaux` (em itálico) |
| meta      | `typography.caption` + `neutral.gray-600` |
| lead      | `typography.lead`              |
| bg        | `surface.pure` ou `surface.paper` |
| divider   | `border.hair` (1px gray-100)   |
| padding   | `spacing.card-padding` (24px)  |

## Variantes

- **Default** — fundo `surface.pure`, sem moldura, separado do próximo card por `divider.hair`.
- **Premium** — fundo `surface.cream`, padding-lg, usado em destaques institucionais.
- **Compact** — sem lead; apenas eyebrow + título + meta.

## Regras

1. Eyebrow **sempre** precede o título, **nunca** após.
2. Italic-accent permitido apenas em **uma** palavra-âncora do título.
3. Lead máximo de 3 linhas; além disso, usar `body`.
4. Cards adjacentes separados por `divider.hair`, nunca por sombra.

## Inspiração

Layout editorial de The Rio Times (capa de matéria) — hierarquia tipográfica forte com mínimo ruído visual.
