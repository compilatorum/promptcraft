# 🧬 Material Destilado e Consolidado de Fontes (Promptcraft)

Este documento representa o núcleo cognitivo consolidado de todas as fontes importadas (YouTube, Reddit/PRAW, GitHub Stars, GDrive/Rclone, Web3/GraphQL, Bookmarks, CDP, Chatlogs e Scholar).

---

## 🧠 1. Destilação e Síntese de Conteúdo por Categoria

### 🧠 1.1. IA & Pesquisa (IA_PESQUISA)
*   **Axiomas Principais**: A engenharia de prompts e contexto evolui de meras instruções textuais para sistemas de restrições neurosimbólicas. Os invariantes são expressos sob a forma de formalismos matemáticos (ex: $A' = R(A \oplus a_i)$).
*   **Ajuste Fino vs. RAG**: O RAG atua na recuperação dinâmica de blocos de contexto curto (latência sub-100ms) a partir de tabelas estruturadas de cache SQLite, enquanto o Fine-Tuning LoRA (gerado via Alpaca em `train.jsonl` com Unsloth) recondiciona a distribuição de probabilidade de tokens do modelo para responder usando a ontologia do usuário.

### 🛠️ 1.2. Engenharia & Código (DESENVOLVIMENTO)
*   **O Emacs Daemon Worker**: O ambiente Emacs mantido persistente (`emacs --daemon=worker`) atua como o servidor de memória de ASTs do workspace.
*   **CDP (Chrome DevTools Protocol)**: Uso de automação local para controle de sessões e extração de chatlogs brutos sem barreiras de APIs restritivas ou proxies.

### 🏛️ 1.3. Web3 & Governança (REGENERACAO_REFI)
*   **Snapshot GraphQL**: Ingestão contínua de propostas fechadas (ex: `ens.eth`) para identificar padrões de tomadas de decisão e propostas de finanças regenerativas (ReFI).
*   **Métricas On-chain**: Integração sistemática de TVL, liquidez e volumes estruturados no grafo relacional do PKM.

### 📂 1.4. Gestão de Conhecimento Pessoal (CONHECIMENTO_PKM)
*   **Org-Roam v2 & Elfeed**: Integração de feeds RSS e notas de denote em uma estrutura org com indexação via banco de dados SQLite nativo do `org-roam`. O banco relacional do Org-Roam fornece a velocidade necessária para mapear arcos nexiais entre nós.
*   **Graphify & LLM-Wiki v2**: Prevenção de leituras de arquivo cegas (mass-grepping). Navegação baseada em grafos direcionados para conservação do escopo do contexto.

---

## 🔬 2. Análise Metodológica Geral & Próximos Passos

### 🔴 Auditoria de Lacunas Científicas
1.  **Excesso de Ruído Semântico**: Favoritos extensos (como os 31.820 links) contêm cerca de 45% de redundâncias que devem ser eliminadas por um loop de deduplicação semântica baseado em similaridade de cosseno.
2.  **HITL (Human-in-the-Loop) Gate**: A automação total gera "drift epistêmico". A validação humana deve ser mantida como o selador de commits no Git.

### 🟢 Plano de Ação Imediato
1.  **Cron de Sincronização**: Automatizar a execução diária de `manage_chatlogs.py` e `organizar_e_distilar.py` usando timers locais `/schedule`.
2.  **Mapeador Org-Roam**: Desenvolver um script em Elisp (`pkm-bootstrap.el`) para ler `fontes_organizadas.md` e gerar nós `.org` Denote associados ao banco SQLite do `org-roam`.
