# 🧠 Emacs IDE - Configuração Modular

## 📖 Visão Geral

Esta é uma configuração Emacs **modular**, **pragmática** e **bem documentada**,
inspirada no PDF EmacsIDE.pdf e organizada para facilitar manutenção e compreensão.

### 🎯 Objetivos

1. **Modularidade** - Cada funcionalidade em seu próprio arquivo
2. **Documentação** - Comentários em pt-BR com filosofemas
3. **Pragmatismo** - Do mais simples ao mais complexo
4. **Integridade** - Tudo funcionando de forma coesa

---

## 📁 Estrutura de Arquivos

```
.emacs.d/
├── init.el                      # Arquivo principal (vai carregar todos)
├── lisp/
│   ├── 00-core.el             # 🚀 Core - carrega módulos
│   ├── 01-constants.el        # 🏛️ Constantes e variáveis
│   ├── 02-ui.el               # 🎨 Interface (tema, modeloine, ícones)
│   ├── 03-editing.el          # ✏️ Edição (pares, seleção, formatação)
│   ├── 04-completion.el       # 🤖 Completion (Company, Yasnippet)
│   ├── 05-counsel-ivy.el     # 🔍 Completion UI (Ivy, Counsel, Embark)
│   ├── 06-navagation.el      # 🏃 Navegação (Avy, Ace Jump, Wind Move)
│   ├── 07-project.el          # 📁 Projetos (Projectile, Treemacs)
│   ├── 08-git.el             # 🕐 Git (Magit, Git Gutter, Forge)
│   ├── 09-lsp.el             # 💡 LSP (LSP Mode, Tree-sitter)
│   ├── 10-terminal.el         # 🖥️ Terminal (VTerm, Eshell)
│   ├── 11-org.el             # 📓 Org Mode (Notas, Agenda, Roam)
│   ├── 12-evil.el            # ⚔️ Evil Mode (Vim keybindings)
│   ├── 13-debug.el           # 🐛 Debug (Dape, ERT)
│   └── 14-extras.el          # 📌 Utilitários e extras
├── .workspace_config.yaml     # 🔒 Configuração de segurança
└── secure_workspace.py       # 🐍 Módulo de segurança (Python)
```

---

## 🔧 Instalação

### 1. Pré-requisitos

```bash
# Emacs 28+ recomendado
# Linux/macOS
sudo apt install emacs   # Ubuntu/Debian
brew install --cask emacs  # macOS
```

### 2. Instalar Nerd Fonts (opcional mas recomendado)

```bash
# Clone o repositório
git clone https://github.com/ryanoasis/nerd-fonts.git ~/.nerd-fonts

# Instale JetBrains Mono Nerd Font
~/.nerd-fonts/install.sh JetBrainsMono
```

### 3. Copiar arquivos

```bash
# Backup da config atual
mv ~/.emacs.d ~/.emacs.d.backup

# Clone/clique esta configuração
git clone <repo-url> ~/.emacs.d

# Ou copie manualmente os arquivos
cp -r lisp ~/.emacs.d/
cp init.el ~/.emacs.d/
```

### 4. Reinicie o Emacs

```bash
emacs
```

---

## 📚 Uso dos Módulos

### Carregamento Automático

O `init.el` carrega automaticamente todos os módulos na ordem correta:

```elisp
;; Ordem de carregamento:
;; 1. Constantes (variáveis globais)
;; 2. UI (tema, modeloine)
;; 3. Editing (edição básica)
;; 4. Completion (auto-completar)
;; 5. Counsel-Ivy (interface de completion)
;; 6. Navagation (navegação)
;; 7. Project (projetos)
;; 8. Git (controle de versão)
;; 9. LSP (suporte a linguagens)
;; 10. Terminal (shell integrado)
;; 11. Org (notas e agenda)
;; 12. Evil (emulação Vim)
;; 13. Debug (depuradores)
;; 14. Extras (utilitários)
```

### Carregamento Manual (para teste)

```elisp
;; Carregar um módulo específico
(load "~/.emacs.d/lisp/02-ui.el")

;; Ou usar eval-expression (M-:)
(load "~/.emacs.d/lisp/04-completion.el")
```

---

## ⌨️ Atalhos Principais

### 📦 Geral
| Atalho | Função |
|--------|--------|
| `C-c o` | Menu principal (NeuroCoder) |
| `C-h t` | Tutorial do Emacs |
| `C-c l` | Org Store Link |

### 📁 Navegação de Arquivos
| Atalho | Função |
|--------|--------|
| `C-c d` | Abrir Dired |
| `C-c p p` | Trocar projeto (Projectile) |
| `C-c p f` | Encontrar arquivo no projeto |
| `F8` | Toggle Treemacs |

### 🔍 Busca e Completion
| Atalho | Função |
|--------|--------|
| `C-s` | Swiper (busca incremental) |
| `C-c ;` | Iedit (editar todas ocorrências) |
| `M-/` | Company Complete |
| `M-x` | Counsel-M-x |

### 🏃 Navegação
| Atalho | Função |
|--------|--------|
| `C-;` | Avy (pular para caractere) |
| `M-o` | Ace Window (pular para janela) |
| `C-c <setas>` | Wind Move (navegar janelas) |

### ⚔️ Evil Mode (Vim)
| Atalho | Função |
|--------|--------|
| `SPC` | Leader (atalhos do Evil) |
| `yy` | Yank (copiar) |
| `dd` | Delete (deletar) |
| `yy` | Yank (copiar) |

### 🕐 Git
| Atalho | Função |
|--------|--------|
| `C-x g` | Magit Status |
| `C-x v =` | Git Gutter (mostrar mudanças) |
| `C-c g t` | Git Timemachine |

### 📓 Org Mode
| Atalho | Função |
|--------|--------|
| `C-c c` | Org Capture (captura rápida) |
| `C-c a` | Org Agenda |
| `C-c l` | Org Store Link |

### 🖥️ Terminal
| Atalho | Função |
|--------|--------|
| `C-c t` | Abrir VTerm |
| `C-c e` | Abrir Eshell |

---

## 🎨 Emojis e Nerd Fonts

### Emojis nos Comentários

Usamos emojis para melhorar a legibilidade:

```
🏛️ Constantes       📁 Projetos       🕐 Git
🎨 Interface        📓 Org Mode       ⚔️ Evil Mode
✏️ Edição          💡 LSP             🐛 Debug
🤖 Completion      🖥️ Terminal       📌 Extras
🔍 Counsel-Ivy    🏃 Navegação
```

### Nerd Fonts

Configure no seu terminal e Emacs:

```elisp
;; No init.el
(set-face-attribute 'default nil :font "JetBrainsMono Nerd Font-12")
```

---

## 🔒 Segurança

Incluímos o sistema `secure_workspace` para prevenir erros de criação de arquivos:

### O que ele faz:
- Detecta typos em caminhos (ex: `sukata` vs `sutaka`)
- Bloqueia caminhos do sistema (`/etc`, `/var`)
- Exige confirmação antes de criar arquivos
- Log de todas operações

### Para usar:

```elisp
;; Carregar módulo de segurança
(load "~/.emacs.d/lisp/secure_workspace.py" nil t)
```

---

## 📝 Filosofemas

Cada bloco de código inclui um **filosofema** - uma reflexão sobre o propósito:

| Bloco | Filosofema |
|-------|------------|
| Core | "Ordo est anima" - A ordem é alma |
| Constantes | "Architectura stabilis" - Arquitetura estável |
| UI | "Ars est celare artem" - A arte esconde a arte |
| Editing | "Ars scribendi est ars vivendi" - Escrever é viver |
| Completion | "Completio est opus intelligentiae" - Completar é inteligência |
| Git | "Tempus fugit, git commit" - O tempo foge, mas commit permanece |
| LSP | "Lingua est nexus mentis" - Linguagem é vínculo da mente |
| Org | "Org est organizatio vitae" - Org é organização da vida |
| Evil | "Evil est vinculum dualitatis" - Evil é vínculo da dualidade |

---

## 🐛 Troubleshooting

### Pacote não instala

```bash
# Atualizar lista de pacotes
M-x package-refresh-contents

# Reiniciar Emacs
```

### Tema não carrega

```elisp
;; Forçar carregamento do tema
(load-theme 'doom-gruvbox t)
```

### LSP não funciona

```bash
# Instalar servidor LSP da linguagem
# Python
pip install pyright

# JavaScript/TypeScript
npm install -g typescript-language-server

# Rust
rustup component add rust-analyzer
```

---

## 🚀 Melhorias Futuras

1. **Corporal Mode** - Feedback háptico em terminals
2. **NNC (Neural Network Completion)** - Completion com IA
3. **Memory Graph** - Visualização de memória do projeto
4. **Temporal Navigation** - Navegação por tempo no Git

---

## 📜 Licença

MIT License - Use, modifique e compartilhe!

---

**🎯 Meta:**
> "Construir um Emacs que seja ao mesmo tempo poderoso como uma IDE
> e flexível como um canivete suíço, com documentação clara e
> código elegante."

🌟 **Hacking feliz!** 🧠💻✨
