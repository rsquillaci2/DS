# Meetix — Identidade de Marca
> Engenharia reversa do site meetix.com.br/lp | v2.0 | Produto da Nexd Solution

---

## Identidade

| Atributo | Detalhe |
|----------|---------|
| **Nome** | Meetix |
| **Tagline** | "SDR com IA para WhatsApp" |
| **Proposta** | Qualifique leads automaticamente 24/7, entregue apenas oportunidades prontas para fechar |
| **Site** | [meetix.com.br](https://meetix.com.br) |
| **Produto de** | Nexd Solution (portfólio Tallent Two) |
| **Tipo** | SaaS B2B — CRM com IA conversacional |
| **Stack** | React + Vite + Tailwind CSS + shadcn/ui (Lovable) |

---

## Posicionamento

> "Não é um chatbot genérico. É um sistema de crescimento comercial automatizado que qualifica, organiza e converte no WhatsApp."

- Substitui até 3 SDRs humanos por uma fração do custo
- Resposta instantânea 24/7
- Qualificação com metodologias SPIN/BANT comprovadas
- ROI no 1o mês + garantia de resultado

---

## Público-alvo

| Segmento | Perfil |
|----------|--------|
| Clínicas | Estética e Odontologia |
| Imobiliárias | Corretores e Incorporadoras |
| Cursos | Profissionalizantes e Mentorias |
| Infoprodutores | Lançamentos e Perpétuo |
| Agências | Tráfego e Marketing |
| Franquias | Redes e Unidades |

**Critério:** empresas que investem em tráfego pago e recebem 30+ leads/dia no WhatsApp.

---

## Logotipo

| Asset | Arquivo | Descrição |
|-------|---------|-----------|
| Logo real (original) | `assets/meetix-logo-real.png` | 1264×843px, fundo transparente — extraído direto da LP |
| Logo real (trimmed) | `assets/meetix-logo-trimmed.png` | 861×296px, recortado sem whitespace |
| Favicon | `assets/favicon.png` | Aba do navegador |
| Logo antigo (provisório) | `assets/meetix-logo.png` | ⚠️ Gerado por IA — NÃO é o logo real |

### Descrição do Logo Real

O logo é um **wordmark estilizado** (não um ícone geométrico):

- **"M"** — Azul (`#2078CF` / rgb 32, 120, 207)
- **"ee"** — Verde WhatsApp (`#4CAF50` aprox.)
- **"t"** — Cinza escuro, com um **ícone de telefone/WhatsApp** (verde) saindo do topo como um balão
- **"ix"** — Cinza escuro (`#5A6577` aprox.)

> O logo NÃO é um ícone de cubos 3D. É um wordmark com referência visual ao WhatsApp integrada na letra "t".

---

## Paleta de Cores (CORRIGIDA — extraída da LP real em Jul/2026)

### Cores Principais

| Token | Nome | Hex | HSL | Função |
|-------|------|-----|-----|--------|
| `--primary` | Azul Meetix | `#2078CF` | `210 73% 47%` | Cor dominante — botões CTA, headlines, ring |
| `--accent` | Verde WhatsApp | `#48CF5D` | `127 63% 56%` | Accent, ícones WhatsApp, destaques |
| `--foreground` | Quase-preto | `#020817` | `222.2 84% 4.9%` | Texto principal |
| `--background` | Branco | `#FFFFFF` | `0 0% 100%` | Fundo padrão |

> **CORREÇÃO v2.0:** A cor primária é **azul** (`#2078CF`), não verde. O verde é accent/WhatsApp.

### Cores de Estado

| Token | Nome | Hex | HSL | Função |
|-------|------|-----|-----|--------|
| `--destructive` | Vermelho | `#EF4444` | `0 84.2% 60.2%` | Erros, alertas, seção "Sem a Meetix" |
| `--whatsapp` | Verde WhatsApp | `#25D366` | `142 69% 58%` | Botão flutuante WhatsApp |

### Cores de Suporte

| Token | Hex | HSL | Função |
|-------|-----|-----|--------|
| `--secondary` | `#F0F4F9` | `210 40% 96.1%` | Fundos secundários |
| `--muted` | `#F0F4F9` | `210 40% 96.1%` | Fundos secundários, seções alternadas |
| `--muted-foreground` | `#64748B` | `215.4 16.3% 46.9%` | Texto secundário, descrições |
| `--border` | `#E2E8F0` | `214.3 31.8% 91.4%` | Bordas de cards, divisores |

### Tokens CSS completos (extraídos da LP)

```css
:root {
  --background:           0 0% 100%;
  --foreground:           222.2 84% 4.9%;
  --primary:              210 73% 47%;
  --primary-foreground:   0 0% 100%;
  --secondary:            210 40% 96.1%;
  --secondary-foreground: 219 19% 13%;
  --muted:                210 40% 96.1%;
  --muted-foreground:     215.4 16.3% 46.9%;
  --accent:               127 63% 56%;
  --accent-foreground:    0 0% 100%;
  --destructive:          0 84.2% 60.2%;
  --border:               214.3 31.8% 91.4%;
  --input:                214.3 31.8% 91.4%;
  --ring:                 210 73% 47%;
  --radius:               .75rem;
  --card:                 0 0% 100%;
  --popover:              0 0% 100%;
}
```

---

## Tipografia

| Uso | Fonte | Stack |
|-----|-------|-------|
| Tudo (UI + títulos + corpo) | System UI | `ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` |

> A Meetix usa a fonte do sistema (Tailwind default). Não carrega fontes customizadas.

### Escala tipográfica

| Elemento | Tamanho | Peso |
|----------|---------|------|
| H1 (hero) | `text-4xl` / `text-6xl` (md) = 60px | `font-bold` (700) |
| H2 (seções) | `text-3xl` / `text-4xl` (md) | `font-bold` |
| H3 (cards) | `text-xl` | `font-semibold` |
| Body | `text-base` | `font-normal` |
| Muted / Descrições | `text-sm` / `text-lg` | `text-muted-foreground` |
| Badge / Label | `text-xs` | `font-semibold` |
| Números de impacto | `text-5xl` | `font-bold text-primary` |

### Gradiente do Título (Hero)

```css
h1 {
  background-image: linear-gradient(to right, rgb(32, 120, 207), rgba(32, 120, 207, 0.6));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

---

## Tom de voz

| Atributo | Descrição |
|----------|-----------|
| **Direto e orientado a resultado** | Foca em números, ROI e economia — linguagem de vendas B2B |
| **Provocativo** | Começa com dor: "Pare de perder leads", "Sem contratar mais vendedores" |
| **Comparativo** | Sempre posiciona contra a alternativa (SDR humano = R$ 3.500/mês) |
| **Confiante com prova social** | Depoimentos com nome, foto e resultado concreto |
| **Técnico sem ser complexo** | Menciona SPIN/BANT, Meta API, Twilio — mas explica o benefício |

### Exemplos de copy

| Contexto | Copy |
|----------|------|
| Hero | "Aumente suas vendas no WhatsApp sem contratar mais vendedores" |
| Subhero | "Qualifique leads automaticamente 24/7 e entregue apenas oportunidades prontas para fechar" |
| Badge de urgência | "Pare de perder leads no WhatsApp" |
| Prova de ROI | "-90% tempo de resposta · +3x taxa de conversão · R$ 42k+ economia anual" |
| CTA principal | "Solicitar Diagnóstico Gratuito" |
| CTA secundário | "Agendar Demonstração" |

---

## Componentes visuais

| Componente | Estilo |
|-----------|--------|
| **Botão primário** | bg-primary (`#2078CF`), texto branco, `rounded-[10px]`, `font-medium` |
| **Botão secundário** | bg-white, borda cinza, texto escuro, `rounded-[10px]` |
| **Botão WhatsApp (FAB)** | bg `#25D366`, texto branco, circular, canto inferior direito |
| **Cards** | Borda 2px, hover `border-primary/50`, sombra suave, padding 24px |
| **Badges** | `rounded-full`, borda, `text-xs font-semibold` |
| **Badge de urgência** | Fundo amarelo/laranja, texto escuro, com emoji ⚡ |
| **Ícones** | Lucide Icons, stroke-width 2, dentro de círculos `bg-primary/10` |
| **Gradients** | Hero: `bg-gradient-to-r from-primary to-primary/60` (texto) |
| **Seções alternadas** | Branco / `bg-muted/30` (cinza claro sutil) |
| **Border radius** | `0.75rem` (12px) padrão |

---

## Screenshots da LP (Jul/2026)

| Seção | Arquivo |
|-------|---------|
| Hero + Header | `assets/screenshots/lp-viewport-top.webp` |
| Dashboard + Segmentos + ROI | `assets/screenshots/lp-viewport-scroll1.webp` |
| Comparativo + Features | `assets/screenshots/lp-viewport-scroll2.webp` |

---

## Preços (referência)

| Plano | Preço | SDRs virtuais |
|-------|-------|--------------|
| Starter | R$ 497/mês | Até 3 |
| Pro | R$ 1.297/mês | Até 10 |
| Enterprise | Sob consulta | Ilimitado |

---

## Histórico

| Versão | Data | Descrição |
|--------|------|-----------|
| 1.0 | 2026-04 | Branding extraído via engenharia reversa (sem acesso visual à SPA) |
| 2.0 | 2026-07 | **CORRIGIDO** — Logo real extraído + cores corrigidas (primary = azul, não verde) + screenshots da LP |
