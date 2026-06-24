# 🏠 Ambiente Termux + Proot-Distro Ubuntu

## Diagnóstico Completo do Sistema

---

## 📊 1. Estado Atual do Ambiente

### 1.1 Sistema Operacional
```
┌─────────────────────────────────────────────────────────┐
│  🖥️  Termux (Android) + Proot-Distro Ubuntu           │
│  👤  Usuário: sukata                                  │
│  🏠  Home: /home/sukata                               │
│  💾  Armazenamento: 225GB (67% usado)                 │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Variáveis de Ambiente Críticas

| Variável | Valor | Status |
|----------|-------|--------|
| `HOME` | `/home/sukata` | ✅ OK |
| `SHELL` | `/usr/bin/zsh` | ✅ ZSH |
| `PYTHONPATH` | Não definido | ⚠️ FALTA |
| `NVM_DIR` | `/home/sukata/.nvm` | ✅ Instalado |
| `NODE_PATH` | Não definido | ⚠️ FALTA |
| `PATH` | Fragmentado | ⚠️ REVISAR |

### 1.3 Stack de Linguagens

| Linguagem | Versão | Status | Manager |
|-----------|--------|--------|---------|
| **Python** | 3.13.7 | ✅ | pip (não pypi local) |
| **Python** | 3.13.12 | ✅ | Termux |
| **Node.js** | v24.13.0 | ✅ | npm nativo |
| **Java** | OpenJDK 21 | ✅ | apt |
| **Emacs** | 30.1 | ✅ | apt |
| **Go** | ❌ Ausente | ⚠️ | - |
| **Rust** | ❌ Ausente | ⚠️ | - |

---

## 📦 2. Análise de Projetos

### 2.1 Estrutura Atual
```
/home/sukata/
├── 📂 neurocoder/           # Python CLI (typer, networkx, tree-sitter)
├── 📂 neurocoder-pwa/       # React PWA
├── 📂 monorepo/             # Brainstorm, libs, apps, scripts
├── 📂 molora/               # Python ML (PyTorch, transformers, PEFT)
├── 📂 tribalab-infrastructure/  # FastAPI + Airflow + Docker
├── 📂 app/                  # React Frontend (shadcn/ui)
├── 📂 everything-claude-code/    # ECC v2.0 Hypervisor
├── 📂 hypervisor/           # ECC extractions
├── 📂 adapters/             # ECC adapters
├── 📂 scripts-unified/      # ECC scripts
├── 📂 antigravity/          # Legacy
├── 📂 emacs/                # Configurações emacs
├── 📂 organizar/            # Scripts utilitários
├── 📂 KimiDocs/             # Documentações exportadas
├── 📂 virt/                 # Virtualização
└── 📄 *.md, *.pdf          # Documentações
```

### 2.2 Dependências Python por Projeto

| Projeto | Python | Dependências Principais |
|---------|--------|--------------------------|
| `neurocoder` | ≥3.11 | typer, rich, anthropic, networkx |
| `molora` | ≥3.8 | torch, transformers, peft, accelerate |
| `tribalab-infrastructure/api` | ≥3.10 | fastapi, sqlalchemy, pydantic |
| `user_input_files/emacs` | - | requirements.txt genérico |

### 2.3 Dependências Node por Projeto

| Projeto | Framework | Dependências |
|---------|-----------|--------------|
| `app` | React + Vite | shadcn/ui, tailwind |
| `neurocoder-pwa` | PWA | - |
| `everything-claude-code` | Vanilla | - |

---

## 🔧 3. Problemas Identificados

### 3.1 Gestão de Pacotes
```
❌ Pip global poluído (130+ pacotes)
❌ Conflitos entre versões Python
❌ Sem virtualenvs por projeto
❌ Sem Poetry ou PDM para lock
```

### 3.2 Estrutura de Pastas
```
❌ Documentos soltos na home (MD, PDF, TXT)
❌ Logs dispersos
❌ Arquivos extraídos sem organização
❌ Projetos duplicados ou redundantes
```

### 3.3 Ambiente
```
❌ NVM não carregado automaticamente
❌ PATH fragmentado
❌ JAVA_HOME não definido
❌ Sem .local/bin no PATH
```

---

## 🗂️ 4. Plano de Reorganização

### 4.1 Nova Estrutura de Pastas
```
/home/sukata/
│
├── 📁 projects/                    # Todos os projetos
│   ├── 📁 python/                 # Projetos Python
│   │   ├── neurocoder/
│   │   ├── molora/
│   │   └── tribalab-infrastructure/
│   │
│   ├── 📁 javascript/             # Projetos JS/TS
│   │   ├── app/                   # React frontend
│   │   ├── neurocoder-pwa/
│   │   └── everything-claude-code/
│   │
│   └── 📁 infrastructure/         # Docker/Deploy
│       └── tribalab-infrastructure/
│
├── 📁 workspace/                   # Working directory
│   ├── 📁 downloads/
│   ├── 📁 temp/
│   └── 📁 extractions/
│
├── 📁 docs/                        # Documentações organizadas
│   ├── 📁 projetos/
│   ├── 📁 papers/
│   └── 📁 logs/
│
├── 📁 config/                      # Configurações globais
│   ├── emacs/
│   ├── git/
│   └── shell/
│
├── 📁 data/                        # Dados persistentes
│   ├── 📁 databases/
│   ├── 📁 models/
│   └── 📁 datasets/
│
├── 📁 venvs/                       # Virtualenvs Python
│   ├── neurocoder/
│   ├── molora/
│   └── tribalab/
│
├── 📁 tools/                       # Ferramentas globais
│   └── scripts/
│
└── 📄 README.md                    # Entrada principal
```

### 4.2 Migração de Arquivos
```bash
# Mover projetos para estrutura
mkdir -p projects/{python,javascript,infrastructure}
mv neurocoder/ projects/python/
mv molora/ projects/python/
mv app/ projects/javascript/
mv tribalab-infrastructure/ projects/infrastructure/
# etc.

# Mover documentações
mkdir -p docs/{projetos,papers,logs}
mv *.md docs/projetos/
mv *.pdf docs/papers/
mv *log*.md docs/logs/
```

---

## 🐍 5. Gestão Python - Poetry vs Pip

### 5.1 Recomendação: Poetry

| Critério | Poetry | Pip + venv |
|----------|--------|------------|
| Lock de dependências | ✅ Sim | ⚠️ Manual |
| Virtualenv automático | ✅ Sim | ⚠️ Manual |
| Monorepo | ✅ Workspaces | ❌ Não |
| Velocidade | ✅ Rápido | ✅ Rápido |
| No Android/Termux | ✅ Testado | ✅ OK |

### 5.2 Instalação
```bash
# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Ou via pipx
pipx install poetry

# Adicionar ao PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 5.3 Configuração por Projeto
```toml
# pyproject.toml (já existe em neurocoder)
[tool.poetry]
name = "neurocoder"
version = "0.1.0"
python = "^3.11"

[tool.poetry.dependencies]
python = "^3.11"
typer = "^0.12.0"
rich = "^13.7.0"
anthropic = "^0.25.0"
networkx = "^3.2.1"

[tool.poetry.dev-dependencies]
pytest = "^8.0.0"
ruff = "^0.3.0"

[tool.poetry.scripts]
neurocoder = "neurocoder.cli:main"
```

### 5.4 Comandos Essenciais
```bash
# Inicializar projeto
poetry new project-name
poetry init

# Instalar dependências
poetry install

# Ativar ambiente
poetry shell

# Adicionar dependência
poetry add requests
poetry add --group dev pytest

# Build
poetry build

# Lock
poetry lock
```

---

## 📦 6. Instalação de Pacotes APT

### 6.1 Pacotes Essenciais
```bash
# Desenvolvimento
sudo apt install -y \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    zip \
    unzip \
    tar \
    gzip

# Python
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-full

# Node
sudo apt install -y nodejs npm

# Data Science (se necessário)
sudo apt install -y \
    python3-numpy \
    python3-scipy \
    python3-matplotlib

# PostgreSQL (para tribalab)
sudo apt install -y \
    postgresql \
    postgresql-contrib \
    postgresql-16 \
    postgresql-client-16

# Docker (se suportado)
sudo apt install -y docker.io docker-compose

# Misc
sudo apt install -y \
    htop \
    tmux \
    vim \
    jq \
    tree
```

### 6.2 Pacotes Opcionais
```bash
# Go
sudo apt install -y golang-go

# Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Flutter (se quiser)
# Requer download manual
```

---

## 🟢 7. Node.js - NVM e Gestão

### 7.1 Problema Atual
```
NVM está em /home/sukata/.nvm mas não está carregado
Node.js é nativo do Termux (v24)
```

### 7.2 Solução: Manter Node Nativo
```bash
# Para Termux + proot-distro, Node nativo é melhor
# Verificar versão
node --version  # v24.13.0

# Adicionar npm global bins
echo 'export PATH="$PATH:$(npm config get prefix)/bin"' >> ~/.zshrc
```

### 7.3 Se Precisar de NVM
```bash
# Instalar NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Adicionar ao .zshrc
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Comandos
nvm install 20
nvm use 20
nvm alias default 20
```

### 7.4 Alternativa: fnm (mais rápido)
```bash
curl -fsSL https://fnm.vercel.app/install | bash
fnm install 20
fnm use 20
```

---

## 🔧 8. Configuração do Ambiente

### 8.1 .zshrc Atualizado
```zsh
# ========== AMBIENTE SUKATA ==========

# Meta
export EDITOR="vim"
export VISUAL="emacsclient -c -a emacs"
export BROWSER="termux-open"

# NVM (se instalado)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Poetry
export PATH="$HOME/.local/bin:$PATH"

# Python
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUSERBASE="$HOME/.local"
export PIP_USER=1

# Node
export PATH="$PATH:$(npm config get prefix 2>/dev/null)/bin"

# Projetos
export PROJECTS_DIR="$HOME/projects"
export WORKSPACE="$HOME/workspace"

# TribaLab
export PGDATA="$HOME/data/databases/postgres"
export DOCKER_HOST="unix:///var/run/docker.sock"

# Java
export JAVA_HOME="/usr/lib/jvm/java-21-openjdk-arm64"
export PATH="$JAVA_HOME/bin:$PATH"

# Go
export GOPATH="$HOME/go"
export PATH="$GOPATH/bin:$PATH"

# Rust
export CARGO_HOME="$HOME/.cargo"
export RUSTUP_HOME="$HOME/.rustup"
export PATH="$CARGO_HOME/bin:$PATH"

# Aliases
alias p="poetry"
alias pa="poetry run python"
alias pn="poetry run npm"
alias pi="poetry add"
alias pid="poetry add --group dev"

# Projetos
alias projects="cd $PROJECTS_DIR"
alias ws="cd $WORKSPACE"
alias neurocoder="cd $PROJECTS_DIR/python/neurocoder"

# Emacs
export ALTERNATE_EDITOR=""

# LLM Providers
export OPENAI_API_KEY=""
export ANTHROPIC_API_KEY=""
export GOOGLE_API_KEY=""
```

### 8.2 pyproject.toml Base para Neurocoder
```toml
[tool.poetry]
name = "neurocoder"
version = "0.1.0"
description = "Pipeline de Geração Aumentada com Memory Bank e Code Graph"
authors = ["João Sukata"]
readme = "README.md"
packages = [{include = "neurocoder"}]
python = "^3.11"

[tool.poetry.dependencies]
python = "^3.11"
typer = "^0.12"
rich = "^13.7"
pyyaml = "^6.0"
jinja2 = "^3.1"
httpx = "^0.27"
anthropic = "^0.25"
openai = "^1.12"
numpy = "^1.26"
networkx = "^3.2"
tree-sitter = "^0.21"
tree-sitter-languages = "^1.10"
python-dotenv = "^1.0"
watchdog = "^4.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-asyncio = "^0.23"
pytest-mock = "^3.12"
ruff = "^0.3"
mypy = "^1.8"

[tool.poetry.scripts]
neurocoder = "neurocoder.cli:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

---

## 🧪 9. Testes e Validação

### 9.1 Checklist de Verificação
```bash
# Python
python3 --version          # 3.13.7
poetry --version          # Poetry 2.x
poetry env info           # Ver ambiente

# Node
node --version            # v24.13.0
npm --version             # 11.11.0

# Java
java -version             # 21

# Emacs
emacs --version           # 30.1

# Git
git --version             # 2.51.0
```

### 9.2 Testar Neurocoder
```bash
cd $PROJECTS_DIR/python/neurocoder
poetry install
poetry run neurocoder --help
```

### 9.3 Testar Molora
```bash
cd $PROJECTS_DIR/python/molora
poetry install
poetry run python -c "import torch; print(torch.__version__)"
```

### 9.4 Testar Frontend
```bash
cd $PROJECTS_DIR/javascript/app
npm install
npm run dev
```

---

## 📋 10. Plano de Execução

### Fase 1: Limpeza e Migração
- [ ] Criar nova estrutura de pastas
- [ ] Mover projetos para `projects/`
- [ ] Mover docs para `docs/`
- [ ] Limpar arquivos soltos na home
- [ ] Configurar `.zshrc` atualizado

### Fase 2: Python
- [ ] Instalar Poetry
- [ ] Configurar `pyproject.toml` para cada projeto
- [ ] Migrar para Poetry (evitar pip global)
- [ ] Criar virtualenvs em `venvs/`
- [ ] Testar cada projeto

### Fase 3: Node.js
- [ ] Verificar npm global
- [ ] Testar projetos React
- [ ] Configurar aliases

### Fase 4: TribaLab
- [ ] Configurar PostgreSQL
- [ ] Configurar Docker
- [ ] Testar docker-compose

### Fase 5: Integração
- [ ] Emacs + Org-mode
- [ ] Org-roam
- [ ] PromptOS

---

## 🎯 11. Priorização

| Prioridade | Tarefa | Tempo Estimado |
|------------|--------|----------------|
| 🔴 Alta | Organizar estrutura de pastas | 30 min |
| 🔴 Alta | Configurar Poetry + Neurocoder | 1h |
| 🟠 Média | Configurar Molora + Poetry | 1h |
| 🟠 Média | Setup TribaLab Infra | 2h |
| 🟡 Baixa | Emacs + Org integration | 4h |
| 🟡 Baixa | PromptOS spec | 2h |

---

## 📝 12. Scripts de Automação

### 12.1 Setup Completo
```bash
#!/bin/bash
set -e

echo "🔧 Configurando ambiente sukata..."

# 1. Estrutura de pastas
mkdir -p ~/projects/{python,javascript,infrastructure}
mkdir -p ~/workspace/{downloads,temp,extractions}
mkdir -p ~/docs/{projetos,papers,logs}
mkdir -p ~/config/{emacs,git,shell}
mkdir -p ~/data/{databases,models,datasets}
mkdir -p ~/venvs
mkdir -p ~/tools/scripts

# 2. Mover projetos (se existirem na home)
[ -d ~/neurocoder ] && mv ~/neurocoder ~/projects/python/
[ -d ~/molora ] && mv ~/molora ~/projects/python/
[ -d ~/app ] && mv ~/app ~/projects/javascript/
[ -d ~/tribalab-infrastructure ] && mv ~/tribalab-infrastructure ~/projects/infrastructure/

# 3. Instalar Poetry
if ! command -v poetry &> /dev/null; then
    curl -sSL https://install.python-poetry.org | python3 -
fi

# 4. Atualizar .zshrc
cat >> ~/.zshrc << 'EOF'
# === SUKATA ENVIRONMENT ===
export PROJECTS_DIR="$HOME/projects"
export WORKSPACE="$HOME/workspace"
export PYTHONDONTWRITEBYTECODE=1
alias projects="cd $PROJECTS_DIR"
alias ws="cd $WORKSPACE"
EOF

echo "✅ Setup completo!"
echo "Execute: source ~/.zshrc"
```

---

## 🔗 13. Referências

- [Poetry Docs](https://python-poetry.org/docs/)
- [Termux Wiki](https://wiki.termux.com/wiki/Main_Page)
- [Emacs Org-mode](https://orgmode.org/)

---

**Última atualização:** 2026-04-08
