# 📋 SPEC: Plano de Upgrade Integrado — Knowledge Pipeline × NLaC-OS

**Versão:** 2.0.0
**Data:** 2026-04-22
**Autor:** MiniMax Agent

---

## 🧭 FILOSOFIAS E PRINCIPÍOS FUNDANTES

### 📜 Philosophemes Nucleares

| # | Philosopheme | Rationale |
|---|-------------|-----------|
| φ₁ | *"Não armazene, processe"* | Dados brutos são passivos; conhecimento processado é ativo (capital intelectual) |
| φ₂ | *"Baixa fricção, alta densidade"* | Interfaces devem exigir mínimo de ação cognitiva (incremental search) |
| φ₃ | *"O todo é maior que a soma"* | Integração sistêmica > funcionalidades isoladas |
| φ₄ | *"Loop fechado: captura → processamento → recuperação"* | Ciclo virtuoso do conhecimento |
| φ₅ | *"Offline-first, cloud-ready"* | Privacidade como padrão, escalabilidade como opção |
| φ₆ | *"Formalismo serve à semântica, não o contrário"* | Estruturas devem emergir do conteúdo, não impostas a priori |

### 🔱 Axiomas de Design

```
AXIOM_01: ∀ sistema ∈ [Pipeline, NLaC-OS] → deve_expor_api_unificada()
AXIOM_02: ∀ entrada → deve_gerar_chunk_atômico()
AXIOM_03: ∀ chunk → deve_ter_id único ∧ deve_ter_embedding vetorial
AXIOM_04: ∀ arquivo_org → deve_ser_parsável_por_org_element()
AXIOM_05: ∃ fallback_hierárquico: HF → Groq → Ollama → Regex
```

---

## 🎯 ESCOPO DA INTEGRAÇÃO

### Sistemas Alvo

| Sistema | Componentes | Status Atual |
|---------|-------------|--------------|
| **Knowledge Pipeline** | Extractor, Enricher, Token Pool, Cache, Storage, CodeGraph, OrgExport | ✅ Implementado |
| **NLaC-OS** | Dashboard, Ingest Agent, Deep Search, Org-brain Integration | ⏳ A implementar |
| **Emacs Integration** | gptel, ellama, org-roam, consult | 🔲 Dependência externa |

---

## 📐 ARQUITETURA INTEGRADA

### 🔷 Formalismo: Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NLaC-OS CORE (Unified Knowledge OS)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────────────┐    │
│  │  INGESTÃO     │    │ PROCESSAMENTO │    │   RECUPERAÇÃO         │    │
│  │               │    │               │    │                       │    │
│  │ • ripgrep     │───▶│ • HF API      │───▶│ • Keyword Search      │    │
│  │ • crawler     │    │ • Ollama      │    │ • Vector Search       │    │
│  │ • Emacs sel   │    │ • CodeBERT    │    │ • Graph Traversal     │    │
│  │ • Chatlogs    │    │ • BART-MNLI   │    │ • Hybrid Query       │    │
│  └───────────────┘    └───────────────┘    └───────────────────────┘    │
│         │                     │                      │                      │
│         ▼                     ▼                      ▼                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    CACHE LAYER (Multi-tier)                         │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐              │   │
│  │  │ L1:RAM  │  │ L2:SQLite│  │ L3:FS   │  │ L4:PGVec│              │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                       │
│         ┌─────────────────────────┼─────────────────────────┐            │
│         ▼                         ▼                         ▼            │
│  ┌─────────────┐         ┌─────────────┐         ┌─────────────┐      │
│  │ ORG-ROAM    │         │ ORG-BRAIN  │         │ CODE-GRAPH  │      │
│  │ (Grafo)     │         │ (Ontologia) │         │ (Dependências│      │
│  └─────────────┘         └─────────────┘         └─────────────┘      │
│                                    │                                       │
│                                    ▼                                       │
│                    ┌───────────────────────────────┐                     │
│                    │       ORG-FILES (.org)        │                     │
│                    │  /zettel  /prompts           │                     │
│                    │  /snippets /brain              │                     │
│                    └───────────────────────────────┘                     │
│                                    │                                       │
│                                    ▼                                       │
│                    ┌───────────────────────────────┐                     │
│                    │       DASHBOARD (Web/CLI)     │                     │
│                    │  • Estatísticas              │                     │
│                    │  • Visualização do Grafo     │                     │
│                    │  • Quick Actions             │                     │
│                    └───────────────────────────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 MÓDULOS E FUNCIONALIDADES

### 📦 Módulo 1: INGESTÃO UNIFICADA

| # | Feature | Emoji | Descrição | Status |
|---|---------|-------|-----------|--------|
| 1.1.1 | **Ripgrep Extractor** | 🔍 | Extração via ripgrep com regex customizável | ✅ |
| 1.1.2 | **Crawl4AI Integration** | 🕷️ | Crawling de páginas web para Markdown | ⏳ |
| 1.1.3 | **Emacs Region Capture** | 📝 | Captura de seleção via gptel/org-mode | 🔲 |
| 1.1.4 | **Chatlog Parser** | 💬 | Extração de prompts/respostas de logs | ✅ |
| 1.1.5 | **File Watcher** | 👁️ | Auto-ingestão via filesystem events | 🔲 |

### 📦 Módulo 2: ENRIQUECIMENTO MULTI-TIER

| # | Feature | Emoji | Descrição | Status |
|---|---------|-------|-----------|--------|
| 2.1.1 | **HF Token Pool** | 🔄 | Round-robin entre 4 contas HF | ✅ |
| 2.1.2 | **Zero-shot Classification** | 🏷️ | BART-MNLI para tags customizadas | ✅ |
| 2.1.3 | **Summarization** | 📝 | BART-CNN para resumos | ✅ |
| 2.1.4 | **NER Extraction** | 🧠 | BERT-NER para entidades | ✅ |
| 2.1.5 | **Embeddings** | 🔢 | Sentence-BERT para vetores | ✅ |
| 2.1.6 | **Code Intelligence** | 💻 | CodeBERT para snippets | ✅ |
| 2.1.7 | **Agentic Chunking** | 🧩 | Fragmentação semântica via LLM | ⏳ |

### 📦 Módulo 3: ARMAZENAMENTO HÍBRIDO

| # | Feature | Emoji | Descrição | Status |
|---|---------|-------|-----------|--------|
| 3.1.1 | **SQLite Storage** | 🗄️ | Cache leve para dev/testes | ✅ |
| 3.1.2 | **PostgreSQL + pgvector** | 🐘 | Storage prod com busca vetorial | ✅ |
| 3.1.3 | **Full-text Search** | 🔤 | FTS nativo (portuguese/english) | ✅ |
| 3.1.4 | **Org-roam DB Sync** | 🔗 | Sincronização bidirecional com org-roam.db | ⏳ |
| 3.1.5 | **Graph Storage** | 🕸️ | Apache AGE para grafos relacionais | 🔲 |

### 📦 Módulo 4: CODE INTELLIGENCE

| # | Feature | Emoji | Descrição | Status |
|---|---------|-------|-----------|--------|
| 4.1.1 | **Code Graph Builder** | 🕸️ | Mapeamento de dependências | ✅ |
| 4.1.2 | **Function Extractor** | 🔎 | Extração de funções via regex | ✅ |
| 4.1.3 | **Import Resolver** | 📦 | Resolução de imports/módulos | ✅ |
| 4.1.4 | **Semantic Clustering** | 📊 | Clusterização por similaridade | ✅ |
| 4.1.5 | **AST Parsing** | 🌳 | Parsing real via tree-sitter | 🔲 |

### 📦 Módulo 5: ORG-MODE INTEGRATION

| # | Feature | Emoji | Descrição | Status |
|---|---------|-------|-----------|--------|
| 5.1.1 | **Org-mode Exporter** | 📄 | Geração de arquivos .org | ✅ |
| 5.1.2 | **Org-roam Templates** | 📋 | Templates Zettelkasten | ⏳ |
| 5.1.3 | **Org-brain Relations** | 🧠 | Propriedades BRAIN_PARENTS | ⏳ |
| 5.1.4 | **ID Generation** | 🆔 | UUID para cada nó | ✅ |

### 📦 Módulo 6: RECUPERAÇÃO E BUSCA

| # | Feature | Emoji | Descrição | Status |
|---|---------|-------|-----------|--------|
| 6.1.1 | **Keyword Search** | 🔤 | Busca exata via ripgrep | ✅ |
| 6.1.2 | **Vector Search** | 🔢 | Busca semântica via embeddings | ✅ |
| 6.1.3 | **Hybrid Query** | 🔀 | Combinação keyword + vector | ⏳ |
| 6.1.4 | **Deep Search** | 🔍 | Busca dentro de blocos de código | ⏳ |

### 📦 Módulo 7: INTERFACE E VIZUALIZAÇÃO

| # | Feature | Emoji | Descrição | Status |
|---|---------|-------|-----------|--------|
| 7.1.1 | **CLI Unificada** | 💻 | Interface de linha de comando | ✅ |
| 7.1.2 | **Makefile** | 🔧 | Orquestração via make | ✅ |
| 7.1.3 | **Dashboard Web** | 📊 | Interface web com estatísticas | 🔲 |
| 7.1.4 | **Graph Visualizer** | 🕸️ | Visualização do grafo (D3/Cytoscape) | ⏳ |
| 7.1.5 | **Emacs Dashboard** | 📟 | Dashboard.el com atalhos | 🔲 |

---

## 🔧 ROADMAP DE IMPLEMENTAÇÃO

### Fase 1: Foundation (Semanas 1-2) ✅ IMPLEMENTADO

```
📦 M1: Integração Emacs ✅
  ├── [x] Hook org-mode para auto-save
  ├── [x] Integração com org-roam-db-sync
  └── [x] gptel integration para ingest

📦 M2: Pipeline Enhancement ✅
  ├── [x] Agentic Chunking via Ollama
  ├── [x] Crawl4AI integration
  └── [x] Retry logic com backoff

📦 M3: Storage Enhancement ✅
  ├── [x] Sync bidirecional org-roam.db
  ├── [x] Graph storage (Apache AGE)
  └── [x] Backup automation
```

### Fase 2: Intelligence (Semanas 3-4) 🔲 BACKLOG

```
📦 M4: Code Intelligence
  ├── [ ] AST parsing (tree-sitter)
  ├── [ ] Call graph builder
  └── [ ] Code similarity search

📦 M5: Semantic Layer
  ├── [ ] Ollama embeddings (nomic-embed-text)
  ├── [ ] Hybrid retrieval
  └── [ ] Reranking logic
```

### Fase 3: Interface (Semanas 5-6) 🔲 BACKLOG

```
📦 M6: Dashboard & Visualization
  ├── [ ] Web dashboard
  ├── [ ] Graph visualizer (D3)
  └── [ ] Emacs dashboard.el

📦 M7: Workflow Automation
  ├── [ ] Auto-dispatch chunks
  ├── [ ] Redundancy detection
  └── [ ] Git auto-commit
```

---

## ✅ CHECKLIST DE REQUISITOS

### Requisitos Funcionais

- [ ] RF_01: Sistema deve processar documentos de múltiplas fontes (files, URLs, chatlogs)
- [ ] RF_02: Sistema deve gerar embeddings vetoriais para todos os chunks
- [ ] RF_03: Sistema deve suportar busca híbrida (keyword + vector + graph)
- [ ] RF_04: Sistema deve exportar para Org-mode compatível com org-roam
- [ ] RF_05: Sistema deve manter cache para evitar chamadas redundantes
- [ ] RF_06: Sistema deve implementar fallback hierárquico (HF → Ollama → Regex)

### Requisitos Não-Funcionais

- [ ] RNF_01: Latência < 100ms para queries de busca
- [ ] RNF_02: Throughput > 100 documentos/minuto em batch
- [ ] RNF_03: Cache hit rate > 80% para queries similares
- [ ] RNF_04: 100% offline operation (via Ollama)

---

## 📊 MATRIZ DE DEPENDÊNCIAS

```
Feature              Depende de          Prioridade
─────────────────────────────────────────────────────
Ingestão             —                   P0
HF Token Pool        —                   P0
Enriquecimento       Ingestão            P0
SQLite Storage       —                   P0
Org Export           Enrichment          P1
PostgreSQL/pgvector  SQLite             P1
Code Graph           Org Export          P2
Ollama Fallback      HF Token Pool       P1
Hybrid Search        Vector Search       P2
Emacs Integration    Org Export          P2
Dashboard            All                 P3
```

---

## 📚 GLOSSÁRIO

| Termo | Definição |
|-------|-----------|
| **Chunk** | Unidade atômica de conhecimento (equivalente a Zettel) |
| **Embedding** | Representação vetorial densa de texto |
| **Fallback** | Estratégia de contingência quando serviço primário falha |
| **Grafo de Conhecimento** | Estrutura de nós (documentos) e arestas (relações) |
| **Hybrid Search** | Busca que combina múltiplas estratégias (keyword + vector) |
| **Ontologia** | Hierarquia de conceitos (pai-filho via Org-brain) |
| **Token Pool** | Conjunto rotativo de credenciais API |

---

**Documento gerado por MiniMax Agent**
*Last updated: 2026-04-22*
