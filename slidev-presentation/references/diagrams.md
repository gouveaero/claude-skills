# Diagrams & Math — Reference

3 sistemas: **Mermaid** (flowchart, sequence, ER, state, gantt — semântico, mais usado), **PlantUML/Kroki** (UML formal, BPMN, ArchiMate), **LaTeX/KaTeX** (fórmulas matemáticas + química via mhchem).

---

## Mermaid — preferido para diagramas padrão

Renderização nativa do Slidev, sintaxe declarativa, mantém o tema do deck.

### Flowchart

````md
```mermaid
flowchart LR
  A[Lead] --> B{Score >= 70?}
  B -->|Sim| C[SQL pipeline]
  B -->|Não| D[Nurture flow]
  C --> E[Sales handoff]
  D --> B
```
````

### Sequence diagram

````md
```mermaid
sequenceDiagram
  Cliente->>API: POST /auth
  API->>DB: SELECT user
  DB-->>API: user{id, role}
  API-->>Cliente: JWT
  Cliente->>API: GET /resource (JWT)
  API->>Cliente: 200 OK
```
````

### State machine

````md
```mermaid
stateDiagram-v2
  [*] --> Idle
  Idle --> Loading: fetch
  Loading --> Success: 200
  Loading --> Error: 4xx/5xx
  Success --> Idle: reset
  Error --> Idle: retry
```
````

### ER diagram

````md
```mermaid
erDiagram
  USER ||--o{ ORDER : places
  ORDER ||--|{ LINE_ITEM : contains
  PRODUCT ||--o{ LINE_ITEM : "ordered in"
```
````

### Configuração inline

````md
```mermaid {theme: 'neutral', scale: 0.8}
flowchart LR
  A --> B
```
````

Opções: `theme` (`default`, `dark`, `forest`, `neutral`), `scale` (multiplicador), `securityLevel`.

### Configuração global (headmatter)

```yaml
mermaid:
  theme: neutral
  themeVariables:
    primaryColor: '#5eead4'
    primaryTextColor: '#0b1020'
```

---

## PlantUML / Kroki — UML formal

Use quando o diagrama precisa ser UML compliant (use case, class, deployment, ArchiMate, BPMN). Renderiza via Kroki online.

````md
```plantuml
@startuml
class Order {
  +id: UUID
  +total: decimal
  +place(): void
}
class LineItem
Order "1" -- "*" LineItem
@enduml
```
````

Mais raro num deck cinematográfico — só use se a audiência (banca, comitê de arquitetura) **espera** UML formal. Caso contrário, Mermaid é mais limpo.

---

## LaTeX / KaTeX — fórmulas matemáticas

### Inline

```md
A velocidade orbital é $v = \sqrt{\mu/r}$ para órbita circular.
```

### Block

```md
$$
\Delta v = v_e \cdot \ln\!\left(\frac{m_0}{m_f}\right)
$$
```

### Staged highlighting

```md
$$ {1|3|all}
\begin{aligned}
a &= b + c \\
&= 2c + d \\
&= 3d
\end{aligned}
$$
```

Cada `|` consome 1 click — primeiro destaca linha 1, depois 3, depois tudo.

### Mhchem (química)

Habilitar no `vite.config.ts` (template já vem com isso quando relevante):

```ts
import 'katex/contrib/mhchem'
```

Uso:

```md
$$
\ce{H2O + CO2 -> H2CO3}
$$
```

---

## Decision tree

| Diagrama é... | Use |
|---|---|
| Fluxo de processo, sistema, decisão | Mermaid `flowchart` |
| Sequência temporal de chamadas | Mermaid `sequenceDiagram` |
| Estados de uma máquina | Mermaid `stateDiagram-v2` |
| Modelo de dados / banco | Mermaid `erDiagram` |
| Roadmap / timeline com datas | Mermaid `gantt` |
| Classes UML, herança, composição | PlantUML ou Mermaid `classDiagram` |
| BPMN / process notation formal | PlantUML/Kroki |
| Fórmula matemática | LaTeX `$$ $$` |
| Equação química | LaTeX + mhchem |
| Diagrama com coordenadas precisas (poucos nós) | `<ArchitectureFlow>` custom |
| Algo fora de tudo isso | HTML + Tailwind direto no slide |
