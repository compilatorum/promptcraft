# Guia de Integração: Sparklin Notes (casmerim) & Compilatorum App Shell

Este documento orienta a autenticação e integração do repositório **Sparklin Notes** (`casmerim/sparklin-notes`) no seu ecossistema unificado do **Compilatorum / Promptcraft** rodando no Android (Termux/PRoot-Distro).

---

## 🔑 1. Autenticação e Configuração do Git Multi-Perfil

Para permitir que a sua máquina gerencie repositórios da conta `compilatorum` e da conta `casmerim` em paralelo sem misturar credenciais, configuramos chaves SSH isoladas.

### 1.1 Cadastrar a Chave Pública no GitHub
A chave privada `id_ed25519_casmerim` foi gerada localmente. Você deve copiar a chave pública abaixo e adicioná-la às suas chaves SSH na conta **casmerim** no GitHub:

1.  Acesse: `https://github.com/settings/keys` (logado na conta **casmerim**).
2.  Clique em **New SSH Key**.
3.  Dê um título (ex: *Termux Android Compilatorum*) e cole a chave pública a seguir:

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICmUZrRa6cylaI4ILrmD00GlFfqljDTWZEmSjhgoPTo5 casmerim@users.noreply.github.com
```

### 1.2 Testar a Conexão
Após cadastrar a chave no GitHub, valide a conexão executando o comando no seu terminal do Termux:
```bash
ssh -T git@github.com-casmerim
```
Você deverá receber uma mensagem de boas-vindas do GitHub confirmando a autenticação com sucesso para a conta `casmerim`.

---

## 📥 2. Clonagem e Configuração Local do Repositório

### 2.1 Clonar usando a URL de Host customizada
Para que o Git saiba que deve utilizar a chave SSH do `casmerim` ao interagir com este repositório, você deve cloná-lo utilizando a URL mapeada no arquivo `~/.ssh/config`:

```bash
git clone git@github.com-casmerim:casmerim/sparklin-notes.git
```

### 2.2 Configurar o Autor do Commit no Repositório Local
Para evitar que os commits do Sparklin Notes herdem o e-mail ou nome globais do `compilatorum`, navegue até a pasta clonada e configure o escopo local do git:

```bash
cd sparklin-notes
git config user.name "casmerim"
git config user.email "casmerim@users.noreply.github.com"
```
Dessa forma, qualquer `git commit` ou `git push` executado dentro da pasta `sparklin-notes/` usará automaticamente a identidade e chaves do casmerim.

---

## 🏗️ 3. Modelo de Integração no App Shell Android

O Sparklin Notes (desenvolvido no Lovable com React/Vite/TS) atuará como a **camada de apresentação visual (Frontend)** do seu App Shell WebView, enquanto o Promptcraft fornece o **motor de dados semânticos (Backend)**.

```
┌──────────────────────────────────────────────────────────────┐
│                   ANDROID COMPILATORUM SHELL                 │
│                                                              │
│  ┌────────────────────────┐      ┌────────────────────────┐  │
│  │   WebView (Apresentação)│      │  Termux (Lógica/Dados)  │  │
│  │                        │      │                        │  │
│  │    [Sparklin Notes]    │◄────►│      [Promptcraft]     │  │
│  │  Interface React/Vite  │ Local│  Processador nexialista│  │
│  │  Notas e Visualizações │  API │  Bases Org-Roam (.md)  │  │
│  └────────────────────────┘      └────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 3.1 Mecanismo de Sincronização de Notas
Como o Sparklin Notes no Lovable consome dados estruturados (notas), podemos alimentar o frontend de três maneiras integradas:

1.  **Local Storage Injected via WebView:**
    O App Shell lê os arquivos Markdown compilados pelo Promptcraft na pasta `sessoes/` e, através do WebView, injeta esses arquivos no IndexedDB ou LocalStorage do Sparklin Notes ao inicializar o app:
    ```javascript
    // No Android Wrapper (Java/Kotlin):
    String jsonNotes = lerNotasLocaisDoTermuxComoJSON();
    webView.evaluateJavascript("window.importNotesFromCompilatorum(" + jsonNotes + ");", null);
    ```
2.  **API Local no Termux:**
    Você pode expor um microsserviço leve no Termux (usando NodeJS ou Python) que serve os arquivos Markdown do seu Org-Roam em uma porta local (ex: `localhost:3000`). O Sparklin Notes faz requisições HTTP (`fetch`) para essa API local para salvar e listar notas diretamente da base física.
3.  **Compilação Estática Integrada:**
    Você pode compilar o Sparklin Notes (`npm run build`) no Termux, colocar os arquivos HTML/JS estáticos na pasta de assets do seu App Shell e carregar o app offline localmente no WebView:
    `webView.loadUrl("file:///android_asset/sparklin-notes/index.html");`
