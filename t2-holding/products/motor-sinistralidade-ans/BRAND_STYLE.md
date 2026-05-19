# Brand Style Guide — Motor de Sinistralidade ANS
> Aplicação do Design System Tallent Two (T2 Holding)

---

## Contexto de Uso

O Motor de Sinistralidade é um **produto da Tallent Two Financial Holding**. Portanto:
- **DS principal:** Tallent Two (cores, tipografia, componentes)
- **Marca:** Tallent Two Financial Holding
- **Autoria:** Ricardo Squillaci

---

## Paleta de Cores

| Token | Hex | Uso no Motor |
|-------|-----|-------------|
| `primary` | `#2C3D5B` | Headers, títulos, CTAs, barras de navegação, backgrounds escuros |
| `surface` | `#FFF3DE` | Fundos de cards, backgrounds de seções, superfícies |
| `gold` | `#FFD700` | Destaques premium, indicadores de sucesso, badges de ação |
| `gray` | `#BEBEBE` | Neutralidade, bordas, textos secundários |
| `white` | `#FFFFFF` | Superfícies de cards, fundos de conteúdo |
| `black` | `#000000` | Textos de alto contraste, autoridade |

### Semântica de Sinistralidade
| Faixa | Cor | Significado |
|-------|-----|-------------|
| Saudável (<75%) | `#16A34A` (green) | Operação equilibrada |
| Moderada (75-85%) | `#CA8A04` (amber) | Atenção necessária |
| Crítica (>85%) | `#DC2626` (red) | Risco operacional |

---

## Tipografia

| Família | Uso no Motor | Disponibilidade |
|---------|-------------|-----------------|
| **Dejanire Headline** (Serif) | Títulos de slides, headlines de seção, impacto | Fonte proprietária (.otf no repo) |
| **Roboto** (Sans-serif) | Body, interface, tabelas, dados, textos corridos | Google Fonts |

### Fallback para Web (quando Dejanire não disponível)
```css
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;700;800&family=Roboto:wght@300;400;500;700&display=swap');
```
- **Playfair Display** como fallback para Dejanire Headline (serif display similar)
- **Roboto** disponível diretamente no Google Fonts

### Hierarquia Tipográfica (Slides)
- **Front page:** Dejanire/Playfair 64px Bold
- **Subtítulo:** Roboto 32px Regular
- **Content headline:** Dejanire/Playfair 32px Bold
- **Content subtitle:** Roboto 20px Medium
- **Body:** Roboto 16-18px Regular

---

## Padrões de Dashboard (Streamlit)

### KPI Cards
- Fundo `#FFF3DE` (surface) com borda `#2C3D5B` (primary)
- Ícone em container navy com cor gold
- Label em `#6B7280` (gray-500, 14px)
- Valor em `#2C3D5B` (primary, 24px bold)
- Indicador de tendência: green (positivo) ou red (negativo)

### Gráficos
- Cores primárias: `#2C3D5B`, `#3D5278`, `#5A7099`, `#7D92B3`
- Cor de destaque: `#FFD700`
- Grid lines: `#E5E7EB`
- Labels: `#6B7280`

### Tabelas
- Header: `bg-primary` (#2C3D5B) com texto branco
- Linhas alternadas: branco / `#FFF3DE`
- Bordas: `#BEBEBE`

---

## Tom de Voz (nos materiais)

- **Formal e Profissional** — comunicação direta, séria e objetiva
- **Confiante e Seguro** — transmite estabilidade e segurança
- **Clara e Transparente** — valoriza a clareza nas mensagens
- **Inspirador e Ambicioso** — tom sóbrio com ambição positiva
- Dados sempre com fonte citada

---

## Logo e Assinatura

- Logo Tallent Two (horizontal, versão azul sobre fundo claro / branca sobre fundo escuro)
- Conceito: colunas gregas — força, durabilidade e suporte
- Estilo: Minimalista e elegante. Une tradição e inovação.
- Autor dos relatórios: Ricardo Squillaci
