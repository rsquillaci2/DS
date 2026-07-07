# TickerBar

> Faixa superior preta com tickers financeiros em fluxo contínuo. Referência: Bloomberg / The Rio Times.

## Anatomia

```
█ FLRY3 15.80 ▲ 3.13%   SMTO3 18.07 ▼ 1.53%   UGPA3 29.02 ▲ 2.29%   VBBR3 33.34 ▲ 2.05% █
```

## Tokens

| Slot      | Token                                |
|-----------|--------------------------------------|
| bg        | `neutral.black` (#000000)            |
| text      | `surface.cream` ou `surface.pure`    |
| symbol    | `typography.ticker` (uppercase, mono)|
| value     | `typography.ticker`                  |
| up-arrow  | `accent.gold` ou verde semântico     |
| down-arrow| `accent.bordeaux` ou vermelho semântico |
| padding   | `spacing.inline-md` (12px lateral)   |
| height    | 32px                                 |

## Comportamento

- **Scroll horizontal automático** (`marquee`) com velocidade ~60s/loop.
- **Pausa no hover.**
- **Atualização real-time** via WebSocket / polling 30s.
- **Acessibilidade:** respeitar `prefers-reduced-motion` (pausar animação).

## Variantes

- **Default** — fixed top, 32px.
- **Minimal** — sem setas, apenas símbolo + %.
- **Embedded** — dentro de dashboard, sem scroll, estático.

## Regras

1. **Nunca** sobrepor TickerBar a navegação principal — fica acima.
2. Máximo de 12 tickers visíveis em desktop / 5 em mobile.
3. Em mobile, considerar variante **Minimal**.
