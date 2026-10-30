# DarkCTA

> Bloco escuro de chamada institucional / conversion. Inspirado no card "Full Access" do The Rio Times.

## Anatomia

```
┌──────────────────────────────────────┐   navy-deep #1B2740
│ FULL ACCESS                          │   eyebrow cream
│                                      │
│ All articles, market reports,        │   body-ui cream
│ intelligence briefs.                 │
│                                      │
│ $8.99 /mo                            │   numeric-xl + caption
│ Cancel anytime. 7-day free trial.    │
│                                      │
│ [   START FREE TRIAL   ]             │   botão premium (gold) ou accent (bordeaux)
└──────────────────────────────────────┘
```

## Tokens

| Slot     | Token                                    |
|----------|------------------------------------------|
| bg       | `primary.navy-deep` (#1B2740)            |
| eyebrow  | `typography.eyebrow` + `surface.cream`   |
| title    | `typography.h2` + `surface.cream`        |
| body     | `typography.body-ui` + `surface.cream`   |
| price    | `typography.numeric-xl` + `accent.gold`  |
| button   | `cta.premium-bg` (gold) ou `cta.accent-bg` (bordeaux) |
| padding  | `spacing.card-padding-lg` (32px)         |
| radius   | `radius.md`                              |

## Variantes

- **Premium** — botão gold, para ofertas institucionais.
- **Accent** — botão bordeaux, para CTAs editoriais.
- **Subtle** — sem preço destacado; apenas eyebrow + título + botão.

## Acessibilidade

- Contraste cream sobre navy-deep: **12.8:1** — WCAG AAA.
- Botão gold sobre navy-deep: **8.6:1** — AAA para texto navy-ink dentro do botão.
- Foco visível: outline `accent.gold` 2px.

## Regras

1. Usar no máximo **um DarkCTA por viewport** — evita ruído competitivo.
2. Nunca colocar dois DarkCTA lado a lado.
3. Título curto (≤7 palavras).
