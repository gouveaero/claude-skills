# Mode C — Auto Brand Guide

When no reference is provided, propose a palette + typography from the content's tone.

---

## Step 1 — Classify content tone

Read the content and pick the closest category:

| Category | Signals |
|---|---|
| **Editorial / B2B** | Legal, finance, consulting, tax, healthcare. Formal language, long sentences, authoritative. |
| **Tech / SaaS** | Product screenshots, feature lists, metrics, developer audience. Clean, functional. |
| **Lifestyle / Consumer** | Food, fashion, travel, wellness. Warm, personal, aspirational. |
| **Playful / Bold** | Entertainment, youth brand, sports, streetwear. High energy, irreverent. |
| **Corporate / Institutional** | Government, enterprise, NGO. Conservative, trust-focused. |

---

## Step 2 — Palette proposals (2 options)

### Editorial / B2B
**Option A — Warm Earth (TriboTax style)**
```
bg:        #F5EFE4  bg_alt:    #EBE2D0  bg_deep:   #18231C
fg:        #141410  fg_muted:  #5A5850  fg_on_deep:#E0D8C6
accent:    #8B3A2C  accent_alt:#B87060
fonts: Cormorant Garamond + Inter Tight + JetBrains Mono
```

**Option B — Cool Slate**
```
bg:        #F3F4F6  bg_alt:    #E8EAF0  bg_deep:   #1E2433
fg:        #111827  fg_muted:  #6B7280  fg_on_deep:#D1D5DB
accent:    #3B5BDB  accent_alt:#74C0FC
fonts: Playfair Display + Inter + JetBrains Mono
```

### Tech / SaaS
**Option A — Clean Minimal**
```
bg:        #FFFFFF  bg_alt:    #F8FAFC  bg_deep:   #0F172A
fg:        #0F172A  fg_muted:  #64748B  fg_on_deep:#E2E8F0
accent:    #7C3AED  accent_alt:#A78BFA
fonts: Inter + Inter + Fira Code
```

**Option B — Dark Primary**
```
bg:        #0F0F0F  bg_alt:    #1A1A1A  bg_deep:   #000000
fg:        #F5F5F5  fg_muted:  #888888  fg_on_deep:#CCCCCC
accent:    #22D3EE  accent_alt:#67E8F9
fonts: Space Grotesk + Inter + JetBrains Mono
```

### Lifestyle / Consumer
**Option A — Warm Cream**
```
bg:        #FEFAF5  bg_alt:    #F5EDE0  bg_deep:   #2D1F14
fg:        #1A1109  fg_muted:  #7A6A5A  fg_on_deep:#EDE0D0
accent:    #D4703B  accent_alt:#E89B70
fonts: Playfair Display + Lato + -
```

**Option B — Soft Blush**
```
bg:        #FFF5F7  bg_alt:    #FFE8EC  bg_deep:   #1A1018
fg:        #1A0D14  fg_muted:  #7C6070  fg_on_deep:#F0D8E0
accent:    #E0446A  accent_alt:#F07090
fonts: Cormorant Garamond + DM Sans + -
```

### Playful / Bold
**Option A — High Contrast**
```
bg:        #FFFFFF  bg_alt:    #F0F0F0  bg_deep:   #0A0A0A
fg:        #0A0A0A  fg_muted:  #666666  fg_on_deep:#F0F0F0
accent:    #FF2D55  accent_alt:#FF6B87
fonts: Syne + Inter + IBM Plex Mono
```

**Option B — Vibrant Yellow**
```
bg:        #FFFDE7  bg_alt:    #FFF9C4  bg_deep:   #1A1600
fg:        #1A1600  fg_muted:  #665C00  fg_on_deep:#FFF9C4
accent:    #F59E0B  accent_alt:#FCD34D
fonts: Space Grotesk + DM Sans + -
```

### Corporate / Institutional
**Option A — Navy Trust**
```
bg:        #F8F9FA  bg_alt:    #E9ECEF  bg_deep:   #0D1B2A
fg:        #0D1B2A  fg_muted:  #5C677D  fg_on_deep:#D8E2EF
accent:    #1B4F8A  accent_alt:#4A90D9
fonts: Merriweather + Source Sans 3 + Source Code Pro
```

---

## Step 3 — Present proposals

Show 2 options with AskUserQuestion using the `preview` field to visually describe each. Example option labels:

- "Opção A — [name]: [one-line description]"
- "Opção B — [name]: [one-line description]"

After selection, save to `brand-configs/<slug>.brand.json`.

---

## Google Fonts URLs

Pre-built URLs for common combinations:

| Pair | URL |
|---|---|
| Cormorant + Inter Tight + JetBrains | `https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter+Tight:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap` |
| Playfair + Inter | `https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500;600&display=swap` |
| Space Grotesk + Inter | `https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Inter:wght@400;500&display=swap` |
| Syne + Inter | `https://fonts.googleapis.com/css2?family=Syne:wght@400;600;800&family=Inter:wght@400;500&display=swap` |
| Merriweather + Source Sans | `https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,400;0,700;1,400&family=Source+Sans+3:wght@400;600&display=swap` |
