# 📋 Plano de Implementação & Testes

## 📁 Projetos
- 🟢 **Kimi_Export** - TribaLab Cognitive Infrastructure
- 🔵 **ECC v2.0** - Hypervisor Architecture  
- 🟣 **PromptOS** - Promptcraft e Engenharia Cognitiva

---

## 📂 Kimi_Export - TribaLab Cognitive Infrastructure

### 🧪 Fase 1: Testes do Projeto Existente

#### 1.1 Frontend (`/home/sukata/app`)

```bash
cd /home/sukata/app
npm install
npm run dev
```

| Teste | Descrição | Prioridade |
|-------|-----------|------------|
| 🔍 Unit Tests | Componentes React | Alta |
| 🔧 Build | `npm run build` | Alta |
| 🎨 UI/UX | Verificar renderização | Média |

**Estrutura:**
```
app/
├── src/
│   ├── components/ui/     # 40+ componentes shadcn
│   ├── sections/          # HeroSection, PlaygroundSection
│   └── hooks/
├── dist/                  # Build production
└── package.json
```

#### 1.2 Backend (`/home/sukata/tribalab-infrastructure`)

| Teste | Descrição | Ferramenta |
|-------|-----------|------------|
| 🐍 Unit Tests | Testes em `tests/unit/` | pytest |
| 🔗 Integration | API endpoints | pytest |
| 🏃 E2E | User journey | pytest |
| ⚙️ Lint | Code quality | flake8 |

**Execução:**
```bash
cd /home/sukata/tribalab-infrastructure
pytest tests/ -v
```

**Endpoints API a testar:**
- `GET /agents` - Listar agentes
- `POST /knowledge/rag` - Graph RAG
- `GET /datasets` - Listar datasets
- `POST /simulations/{id}/runs` - Executar simulação

---

### 🚀 Fase 2: Deploy & Integração

```bash
# 1. Iniciar infraestrutura Docker
cd tribalab-infrastructure/docker
docker-compose up -d

# 2. Verificar serviços
# - API: http://localhost:8000
# - Airflow: http://localhost:8080
# - pgAdmin: http://localhost:5050
# - MinIO: http://localhost:9001
# - MLflow: http://localhost:5000

# 3. Executar migrations
docker-compose exec postgres psql -U tribalab -d tribalab -f /docker-entrypoint-initdb.d/*.sql

# 4. Testar API
curl http://localhost:8000/health
```

---

## 🔵 ECC v2.0 Hypervisor Architecture

### 🧪 Fase 1: Validação da Arquitetura

#### 1.1 Estrutura
```
ecc-architecture/
├── .hypervisor.json          # Manifesto mestre
├── hypervisor/
│   └── hypervisor.js         # Core
├── adapters/                  # 9 adaptadores
│   ├── adapter-claude.js
│   ├── adapter-opencode.js
│   ├── adapter-codex.js
│   ├── adapter-gemini.js
│   ├── adapter-cursor.js
│   ├── adapter-kiro.js
│   ├── adapter-trae.js
│   └── adapter-codebuddy.js
└── scripts-unified/
    ├── build-index.js
    ├── compress-metadata.js
    └── validate-artifacts.js
```

#### 1.2 Testes Manuais
```bash
# Detectar harness
node hypervisor/hypervisor.js --detect

# Ver status
node hypervisor/hypervisor.js --status

# Listar agentes
node hypervisor/hypervisor.js --list-agents

# Busca fuzzy
node hypervisor/hypervisor.js --search agent
```

#### 1.3 Matriz de Adaptadores

| Harness | Arquivo | Status | Teste |
|---------|---------|--------|-------|
| Claude Code | `adapter-claude.js` | ✅ | Manual |
| OpenCode | `adapter-opencode.js` | ✅ | Manual |
| Codex | `adapter-codex.js` | ✅ | Manual |
| Gemini | `adapter-gemini.js` | ✅ | Manual |
| Cursor | `adapter-cursor.js` | ✅ | Manual |
| Kiro | `adapter-kiro.js` | ✅ | Manual |
| Trae | `adapter-trae.js` | ✅ | Manual |
| CodeBuddy | `adapter-codebuddy.js` | ✅ | Manual |

---

### 🔧 Fase 2: Integração com Harnesses

#### 2.1 Claude Code
```bash
cp .hypervisor.json ~/.claude/
cp -r hypervisor ~/.claude/
cp -r adapters ~/.claude/
```

#### 2.2 Scripts de Validação
```bash
# Validar artefatos
node scripts-unified/validate-artifacts.js

# Build índice
node scripts-unified/build-index.js

# Comprimir metadados
node scripts-unified/compress-metadata.js
```

---

## 🟣 PromptOS - Promptcraft e Engenharia Cognitiva

### 📖 Entendimento do Documento

O PDF define um **Sistema Operacional de Promptcraft** com:

| Componente | Função |
|------------|--------|
| 🧠 **Prompt Kernel** | Núcleo ontológico, identidade do Self |
| 🌐 **Prompt Graph** | Estrutura cognitiva, relações entre prompts |
| 🔎 **Prompt Index** | Sistema de recuperação contextual |
| ⚙️ **Prompt Compiler** | Transforma prompts em representações executáveis |
| 🎨 **Prompt Renderer** | Projeta sistema em forma humana |
| 🖥️ **Prompt IDE** | Ambiente cognitivo (Emacs) |

### 🏗️ Arquitetura Neurosimbólica

```
┌─────────────────────────────────────────────────────┐
│                   PromptOS                          │
├─────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│  │ Camada  │  │ Camada  │  │ Camada  │             │
│  │Simbólica│  │Vetorial │  │Temporal │             │
│  │   𝓢     │  │   𝓥     │  │   𝓣     │             │
│  └────┬────┘  └────┬────┘  └────┬────┘             │
│       │             │             │                  │
│  ┌────┴─────────────┴─────────────┴────┐            │
│  │         Camada Latente (𝓩)          │            │
│  │    Self ⊂ Z ⊂ ℝⁿ  (Embeddings)     │            │
│  └────────────────┬────────────────────┘            │
│                   │                                 │
│  ┌────────────────┴────────────────────┐            │
│  │           LoRA Genesis              │            │
│  │   ΔW = f(Self_latent) → AᵀB        │            │
│  └─────────────────────────────────────┘            │
└─────────────────────────────────────────────────────┘
```

### 📦 Stack Tecnológica Proposta

| Camada | Tecnologia |
|--------|------------|
| **IDE** | Emacs + Org-mode + Org-roam |
| **Database** | PostgreSQL + pgvector + Apache AGE |
| **Datalake** | Bronze/Silver/Gold layers |
| **Graph** | Org-roam + NetworkX + Neo4j |
| **Embeddings** | Chroma/FAISS |
| **LLM Ops** | DSPy + LangChain |
| **Models** | LoRA + SLM fine-tuning |

---

## 📋 Plano de Implementação Sequencial

### Sprint 1: Kimi_Export ✅
- [ ] Setup frontend (`npm install && npm run dev`)
- [ ] Setup infraestrutura Docker
- [ ] Executar migrations
- [ ] Testar API endpoints
- [ ] Executar pytest suite
- [ ] Validar pipelines Airflow

### Sprint 2: ECC v2.0
- [ ] Validar estrutura de arquivos
- [ ] Testar hypervisor core
- [ ] Testar cada adaptador
- [ ] Executar scripts de validação
- [ ] Integrar com Claude Code

### Sprint 3: PromptOS
- [ ] Especificar schema Org-mode
- [ ] Especificar schema PostgreSQL
- [ ] Criar pipeline Org → Postgres
- [ ] Implementar embedding pipeline
- [ ] Construir Prompt Graph
- [ ] Implementar Prompt Compiler
- [ ] Configurar Emacs como Prompt IDE

---

## 🧪 Cobertura de Testes

### Kimi_Export
```
tests/
├── unit/           # Agentes, Grafo, Simulações
├── integration/    # API endpoints
├── e2e/            # User journey
└── doubles/        # Mocks e fakes
```

### ECC v2.0
```
tests/
├── lib/
│   ├── hypervisor.test.js
│   └── adapter-factory.test.js
└── adapters/
    └── [cada adaptador]
```

---

## 📊 Métricas de Sucesso

| Projeto | Testes | Cobertura | Build |
|---------|--------|-----------|-------|
| Kimi_Export | pytest | 80%+ | ✅ |
| ECC v2.0 | node test | 80%+ | ✅ |
| PromptOS | Manual + Auto | TBD | TBD |

---

## 🎯 Prioridades

1. 🔴 **Alta** - Kimi_Export: setup completo + testes passando
2. 🟠 **Média** - ECC v2.0: validação + integração Claude Code
3. 🟡 **Baixa** - PromptOS: especificação + protótipo inicial
