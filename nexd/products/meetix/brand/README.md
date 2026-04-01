# Meetix — Identidade de Marca
> Engenharia reversa do site meetix.com.br | v1.0 | Produto da Nexd Solution

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
| **Stack** | React + Vite + Tailwind CSS + shadcn/ui |

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

## Paleta de Cores

### Cores Principais

| Token | Nome | Hex | HSL | Função |
|-------|------|-----|-----|--------|
| `--primary` | Verde Meetix | `#006B2B` | `144 100% 21%` | Cor dominante — botões, CTAs, ícones, headlines |
| `--foreground` | Quase-preto | `#020817` | `222.2 84% 4.9%` | Texto principal |
| `--background` | Branco | `#FFFFFF` | `0 0% 100%` | Fundo padrão |

### Cores de Estado

| Token | Nome | Hex | HSL | Função |
|-------|------|-----|-----|--------|
| `--destructive` | Vermelho | `#EF4444` | `0 84.2% 60.2%` | Erros, alertas, seção "Sem a Meetix" |
| `--success` | Verde claro | `#16A34A` | `144 72% 40%` | Confirmações, seção "Com a Meetix" |
| `--warning` | Amarelo | `#F59E0B` | `38 92% 50%` | Avisos, atenção |
| `--info` | Azul | `#0070F3` | `210 100% 52%` | Informativo, links |

### Cores de Suporte

| Token | Hex | Função |
|-------|-----|--------|
| `--muted` | `#F1F5F9` | Fundos secundários, seções alternadas |
| `--muted-foreground` | `#64748B` | Texto secundário, descrições |
| `--border` | `#E2E8F0` | Bordas de cards, divisores |
| `--whatsapp` | `#25D366` | Ícone WhatsApp, badge flutuante |

### Tokens CSS completos

```css
:root {
  --background:           0 0% 100%;
  --foreground:           222.2 84% 4.9%;
  --primary:              144 100% 21%;
  --primary-foreground:   0 0% 100%;
  --secondary:            210 40% 96.1%;
  --secondary-foreground: 222.2 47.4% 11.2%;
  --muted:                210 40% 96.1%;
  --muted-foreground:     215.4 16.3% 46.9%;
  --accent:               210 40% 96.1%;
  --accent-foreground:    222.2 47.4% 11.2%;
  --destructive:          0 84.2% 60.2%;
  --success:              144 72% 40%;
  --warning:              38 92% 50%;
  --info:                 210 100% 52%;
  --border:               214.3 31.8% 91.4%;
  --input:                214.3 31.8% 91.4%;
  --ring:                 222.2 84% 4.9%;
  --radius:               .75rem;
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
| H1 (hero) | `text-4xl` / `text-6xl` (md) | `font-bold` |
| H2 (seções) | `text-3xl` / `text-4xl` (md) | `font-bold` |
| H3 (cards) | `text-xl` | `font-semibold` |
| Body | `text-base` | `font-normal` |
| Muted / Descrições | `text-sm` / `text-lg` | `text-muted-foreground` |
| Badge / Label | `text-xs` | `font-semibold` |
| Números de impacto | `text-5xl` | `font-bold text-primary` |

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
| **Botão primário** | bg-primary (`#006B2B`), texto branco, `rounded-md` (10px), `font-medium` |
| **Botão secundário** | bg-white, borda cinza, texto escuro, `rounded-md` (10px) |
| **Cards** | Borda 2px, hover `border-primary/50`, sombra suave, padding 24px |
| **Badges** | `rounded-full`, borda, `text-xs font-semibold` |
| **Badge de urgência** | Fundo vermelho (`destructive`), texto branco, `animate-pulse` |
| **Ícones** | Lucide Icons, stroke-width 2, dentro de círculos `bg-primary/10` |
| **Gradients** | Hero: `bg-gradient-to-r from-primary to-primary/60` (texto) |
| **Seções alternadas** | Branco / `bg-muted/30` (cinza claro sutil) |

---

## Logotipo

| Asset | Arquivo | Uso |
|-------|---------|-----|
| Logo principal | `assets/meetix-logo.png` | Header, materiais |
| Favicon | `assets/favicon.png` | Aba do navegador |

> O logo é um ícone geométrico verde (cubos 3D) + "meetix" em texto. Formato disponível apenas em PNG.

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
| 1.0 | 2026-04 | Branding extraído via engenharia reversa do site (LP + CSS vars) |
