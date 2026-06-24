# 🗺️ Manual de Instruções — Banco de Dados Cognitivo Unificado & Mapeamento PKM

> **Filosofema**: *"O conhecimento sem estrutura é ruído de fundo; o conhecimento estruturado em grafo relacional é a base do exocérebro digital."*

---

## 📂 1. MAPEAMENTO DA ESTRUTURA DO PROJETO

Abaixo está o mapeamento detalhado da raiz `~/promptcraft` e do diretório `~/promptcraft/ontologia`, com resumos funcionais de cada arquivo e pasta.

### 🧭 1.1 Diretório Raiz (`~/promptcraft`)

*   📁 **`.agents/`**: Configurações de agentes de desenvolvimento, regras do projeto e sidecars locais.
*   📁 **`backups/`**: Cópias de segurança de versões legadas do banco de dados e arquivos de configuração.
*   📁 **`takeout/`**: Biblioteca de documentos baixados (PDFs, DOCX, Markdown, ORG) oriundos da sincronização via Rclone do Google Drive.
    *   *Exemplos notáveis*:
        *   `HT-F02_Advanced-Smart-Contract-Hacking-FINAL.pdf`: Material avançado de segurança em Solidity.
        *   `The_Sickness_of_Becoming_Great_Creativit.docx`: Estudo sobre criatividade e psicologia.
*   📁 **`templates/`**: Templates de prompts em Markdown e formatos XML para injeção de contexto estruturado.
*   📄 **`promptcraft.py`**: O CLI central do ecossistema. Contém comandos para:
    *   Sincronização incremental do Google Drive via Rclone (`importar --type gdrive`).
    *   Extração inteligente de conteúdo em múltiplos formatos (fitz para PDFs, docx para Word, markdown nativo).
    *   Indexação direta e estruturada na base relacional SQLite.
*   📄 **`config.json`**: Configuração central do ecossistema. Define:
    *   Modelos de LLM utilizados (Llama 3.3, Claude).
    *   Chaves de API das provedoras (OpenAI, Anthropic, Gemini, HuggingFace).
    *   Parâmetros de volatilidade semântica para diferentes tipos de fontes (vídeo, artigo, bookmark, etc.).
*   📄 **`org-roam.db`**: Banco de dados cache local do Org-Roam em Emacs (tabelas clássicas de nós, aliases, tags).
*   📄 **`chatlog_d43ca8ed.jsonl` / `_full.jsonl`**: Histórico completo consolidado da sessão de chat com a IA Antigravity, servindo como base para geração de datasets.
*   📄 **`favoritos_23_06_2026.html`**: Exportação HTML crua de favoritos do navegador (~32k URLs) que serve como input inicial da esteira de ingestão.

### 🧠 1.2 Diretório de Ontologia (`~/promptcraft/ontologia`)

*   📄 **`fontes_processadas.db`**: O banco de dados SQLite unificado. Contém as tabelas do Org-Roam v2 em coexistência com os 7 lobos cerebrais da arquitetura **IPMO** (ver seção 2).
*   📄 **`tags_dicionario.json`**: Dicionário taxonômico dinâmico. Define:
    *   *Marcadores Léxicos*: Termos epistêmicos, semânticos, sintáticos e cognitivos.
    *   *Mapeamento de Domínios*: Regras de regex para catalogar URLs (Wikipedia, buscas, artigos, web3, etc.).
    *   *Hierarquia de Tags*: Categorias fundamentais (`IA_PESQUISA`, `DESENVOLVIMENTO`, `REGENERACAO_REFI`, `NEURO_COGNICAO`, etc.) e suas subtags para classificação automatizada.
*   📄 **`processar_bulk.py`**: Script de inicialização do banco de dados e ingestão em lote.
    *   Configura e cria as 38 tabelas, 108 índices, 6 triggers e 5 views.
    *   Realiza a leitura de `fontes_importadas.md` e `bookmarks_importados.md` para criar a base relacional.
    *   Roda testes de API em tempo real (YouTube, GitHub, GraphQL Snapshot, Semantic Scholar).
*   📄 **`distilar_incremental.py`**: Crawler progressivo rodando em lotes parametrizáveis.
    *   Acessa URLs pendentes em segundo plano com delay amigável (3 segundos).
    *   Extrai os primeiros 5.000 caracteres das páginas, otimizando o buffer de armazenamento e tokens.
*   📄 **`importar_github_starred.py`**: Integrador automatizado com a API do GitHub.
    *   Recupera todos os starred repos de `@compilatorum`.
    *   Constrói metadados estruturados (linguagem, estrelas, tópicos, issues) e os destila como nós de conhecimento.
    *   Mapeia tópicos do repositório para a taxonomia complexa em `tags_dicionario.json`.
*   📄 **`laboratorio_cognitivo.py`**: Motor de análise linguística clássica do Planner.
    *   Analisa frequências de tokens, TF-IDF, riqueza de vocabulário e exporta dados no formato Alpaca JSONL para sintonia fina de modelos (LoRA/SFT).
*   📄 **`todo_list.md`**: Plano de ação atomizado contendo tarefas em progresso de infraestrutura, sincronização e correções técnicas para Termux Android.

---

## 🗄️ 2. A ARQUITETURA DO BANCO DE DADOS COGNITIVO UNIFICADO

O banco `fontes_processadas.db` une a estrutura relacional do **Org-Roam v2** (Emacs) à arquitetura **IPMO** de forma adaptiva para evitar colisões.

```
┌──────────────────────────────────────────────────────────┐
│  📑 ORG-ROAM V2 COMPATIBLE                               │
│     files, nodes, aliases, citations, refs, tags, links  │
├──────────────────────────────────────────────────────────┤
│  🧠 CORE (Sistema Central)                               │
│     sessions, messages, agents, tools, events            │
├──────────────────────────────────────────────────────────┤
│  💾 MEMORY (Memory Bank)                                 │
│     memory_items, knowledge_patches, adrs, snapshots    │
├──────────────────────────────────────────────────────────┤
│  📋 TASKS (iPMO Planner)                                 │
│     tasks, dags, task_dependencies, workflows            │
├──────────────────────────────────────────────────────────┤
│  📚 KNOWLEDGE (RAG + Graph)                              │
│     documents, document_chunks, symbols, graph_links     │
├──────────────────────────────────────────────────────────┤
│  🔧 CODE (Code Intelligence)                             │
│     code_chunks, git_commits, git_branches, git_diffs    │
├──────────────────────────────────────────────────────────┤
│  📊 METRICS (Observabilidade)                            │
│     metrics, drift_scores, reliability_scores, alerts    │
├──────────────────────────────────────────────────────────┤
│  ⚙️ CONFIG (Configuração)                                │
│     settings, prompt_templates, agent_configs            │
└──────────────────────────────────────────────────────────┘
```

### ⚡ 2.1 Triggers de Automação Implementados
Os triggers no SQLite atuam como reflexos reflexivos do ecossistema, mantendo estados consistentes:
1.  `update_sessions_timestamp`: Sincroniza `updated_at` a cada alteração em `sessions`.
2.  `update_messages_timestamp`: Mantém o histórico temporal de `messages` ativo.
3.  `update_tasks_timestamp`: Registra alterações em tarefas em tempo real.
4.  `update_session_steps`: Sempre que o `role = 'assistant'` insere uma mensagem, a sessão associada incrementa `step_current` e atualiza seu timestamp de atividade.
5.  `log_drift_change`: Monitora alterações no `drift_score` das sessões e grava um registro de evento no histórico `events` estruturado em JSON com a variação (`delta`).
6.  `alert_on_high_drift`: Dispara automaticamente alertas críticos (`drift_critical` ou `drift_warning`) na tabela `alerts` caso o `drift_score` da sessão activa ultrapasse `0.35`.

### 📊 2.2 Views de Observabilidade
1.  `v_session_summary`: Sumariza sessões, com número de mensagens do usuário/assistente, confiança média e drifts correntes.
2.  `v_task_progress`: Calcula dinamicamente o progresso em percentual (0%, 25%, 50%, 100%) baseado no status do Planner (`todo`, `blocked`, `in_progress`, `done`).
3.  `v_active_alerts`: Filtra e prioriza todos os alertas pendentes com rótulos visuais (🚨 CRÍTICO, ⚠️ ALTO, 📌 MÉDIO).
4.  `v_knowledge_graph`: Consolida links bi-direcionais entre documentos, tarefas e ADRs de forma descritiva.
5.  `v_file_statistics`: Retorna estatísticas de arquivos do workspace agrupados por linguagem de programação (total de linhas, tamanho e número de arquivos).

---

## 🔍 3. MANUAL DE QUERIES E DIAGNÓSTICO (SQL)

### 📈 3.1 Consulta de Progresso do Planner por DAG
```sql
SELECT 
    dag_name,
    COUNT(id) AS total_tasks,
    SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS completed_tasks,
    ROUND(AVG(progress_percent), 2) AS avg_progress_percentage
FROM v_task_progress
GROUP BY dag_name;
```

### 🚨 3.2 Listar Alertas Ativos de Desvio Cognitivo
```sql
SELECT title, message, severity_label, session_title, created_at
FROM v_active_alerts
WHERE alert_type LIKE 'drift%'
ORDER BY severity ASC;
```

### 🏷️ 3.3 Buscar Nós Destilados que contenham uma Subtag Específica
```sql
SELECT n.title, json_extract(n.properties, '$.url') AS url, t.tag
FROM nodes n
JOIN tags t ON n.id = t.node_id
WHERE t.tag = 'mcp_protocol' AND json_extract(n.properties, '$.status') = 'processed';
```

### 📊 3.4 Estatísticas de Linguagens nos Starred Favoritos
```sql
SELECT 
    language,
    COUNT(*) AS total_repos,
    SUM(size_bytes) AS total_distilled_chars,
    ROUND(AVG(line_count), 1) AS avg_lines_per_repo
FROM files
WHERE file LIKE 'shared-knowledge/github/%'
GROUP BY language
ORDER BY total_repos DESC;
```

---

## 🚀 4. INTEGRAÇÃO COM OUTROS PROJETOS (PRÓXIMOS PASSOS)

Para integrar totalmente a base cognitiva aos seus outros repositórios e ecossistema, siga estas rotas de conexão técnica:

### ⚙️ 4.1 Integração com Emacs / Denote (`pkm-bootstrap.el`)
Podemos ler os nós processados na base SQLite `fontes_processadas.db` e escrever diretamente notas `.org` válidas na pasta do Denote.
*   **Estrutura do Script de Exportação (Elisp)**:
    ```elisp
    (defun pkm/sync-db-to-denote ()
      "Lê nós do fontes_processadas.db com status 'processed' e cria arquivos Denote."
      (interactive)
      (let* ((db-path "/home/sukata/promptcraft/ontologia/fontes_processadas.db")
             (nodes (sqlite-select db-path "SELECT id, title, properties FROM nodes WHERE json_extract(properties, '$.status') = 'processed'")))
        (dolist (node nodes)
          (let* ((id (car node))
                 (title (cadr node))
                 (props (json-read-from-string (caddr node)))
                 (content (cdr (assoc 'distilled_content props)))
                 (url (cdr (assoc 'url props)))
                 (tags (sqlite-select db-path "SELECT tag FROM tags WHERE node_id = ?" (list id)))
                 (denote-tags (mapcar #'car tags)))
            ;; Chama denote-create ou escreve arquivo org com front-matter do denote
            (pkm/write-denote-file title content url denote-tags)))))
    ```

### 🗄️ 4.2 Integração com Lakehouse de Dados (DuckDB + Parquet)
Para análises estatísticas em larga escala sem sobrecarregar o SQLite do ambiente de desenvolvimento local, podemos ler as tabelas relacionais do banco cognitivo e sincronizá-las para tabelas Parquet num Lakehouse usando **DuckDB**:
1.  **Script de Extração (Python + DuckDB)**:
    ```python
    import duckdb
    # Conecta ao duckdb
    con = duckdb.connect("lakehouse.db")
    # Copia dados direto do SQLite em formato Parquet para o Lakehouse
    con.execute("INSTALL sqlite; LOAD sqlite;")
    con.execute("CALL sqlite_attach('/home/sukata/promptcraft/ontologia/fontes_processadas.db', 'pkm_db');")
    con.execute("COPY pkm_db.nodes TO 'lakehouse/nodes.parquet' (FORMAT PARQUET);")
    con.execute("COPY pkm_db.tags TO 'lakehouse/tags.parquet' (FORMAT PARQUET);")
    ```

### 🧠 4.3 Fine-Tuning de Modelos Locais (SLMs via Unsloth)
Podemos construir conjuntos de dados de treinamento baseados em nossa base relacional. As 501 fontes já destiladas e processadas (incluindo repositórios GitHub do compilatorum, chatlogs sanitizados e GDrive PDFs) podem ser extraídas diretamente para formato Alpaca:
1.  **Pipeline de dataset**:
    *   *Input*: `SELECT title, json_extract(properties, '$.distilled_content') FROM nodes WHERE json_extract(properties, '$.status') = 'processed';`
    *   *Formatação*: Gerar um arquivo `dataset_train.jsonl` contendo:
        ```json
        {"instruction": "Resuma e extraia as principais tags de ontologia do seguinte repositório/documento:", "input": "<distilled_content>", "output": "<title> - Focado em <tags>"}
        ```
    *   *Execução*: Importar este arquivo JSONL em um notebook de treino Unsloth para fazer o ajuste fino de um Llama-3-8B local especializado em sua taxonomia pessoal de projetos.

### 🌐 4.4 Ingestão de Fontes Dinâmicas e Alinhamento com DAM (Reddit/PRAW, Busca Acadêmica, GraphQL)
A expansão da base de conhecimento integra fluxos de dados em tempo real. No ecossistema Web3, essa Ingestão subsidia sistemas de **DAM (Decentralized Asset Management / Decentralized Autonomous Machine)**, onde agentes analisam dados on-chain para governança e tomadas de decisão financeiras automatizadas.

1. **Reddit & PRAW (canais, notificações, favoritos)**:
   - *Finalidade*: Monitorar subreddits específicos (ex: `r/emacs`, `r/Refi`), capturar postagens salvas (favorites) do usuário e rastrear mensagens/notificações da caixa de entrada.
   - *Fluxo Relacional*: Postagens salvas são indexadas como nós de conhecimento com tag `bookmarks_curated`, enquanto notificações alimentam a tabela `events` para rastreamento comportamental de agentes.
   - *Código de Ingestão*:
     ```python
     import praw
     reddit = praw.Reddit(
         client_id="YOUR_CLIENT_ID",
         client_secret="YOUR_CLIENT_SECRET",
         user_agent="pkm-agent:v1.0",
         username="YOUR_USERNAME",
         password="YOUR_PASSWORD"
     )
     # Ingerir salvos do usuário
     for item in reddit.user.me().saved(limit=50):
         # Mapear título, subreddit e corpo do post para distilled_content
         pass
     ```

2. **Busca Acadêmica Semântica (Semantic Scholar vs. Google Scholar)**:
   - *Recomendação*: **Semantic Scholar API** (`api.semanticscholar.org/v1/paper`). 
   - *Motivo*: O Google Scholar não possui API aberta estável e realiza bloqueios agressivos por CAPTCHA. O Semantic Scholar fornece acesso aberto a resumos, contagem de citações, referências e adjacências semânticas estruturadas (ideais para grafos de RAG) e integra-se perfeitamente com metadados do arXiv.
   - *Fluxo Relacional*: Artigos baixados são salvos em `takeout/` e indexados na tabela `documents` com fragmentos no `document_chunks`. As conexões de referências alimentam a tabela `graph_links` com tipo `references`.

3. **GraphQL & Dados Web3 (DAM - Decentralized Asset Management)**:
   - *Finalidade*: Consultar métricas financeiras de DeFi (Uniswap, Curve) e propostas de governança de DAOs (Snapshot GraphQL).
   - *Alinhamento DAM*: Em sistemas de gerenciamento descentralizado de ativos (DeFi), o agente precisa capturar propostas on-chain para participar de decisões de portfólio. As propostas entram na tabela `tasks` (dentro de um DAG de governança) e os resultados financeiros retroalimentam a tabela `metrics` e `reliability_scores`.
   - *Exemplo de Query GraphQL (Uniswap Subgraph)*:
     ```graphql
     query {
       pools(orderBy: totalValueLockedUSD, orderDirection: desc, first: 5) {
         id
         token0 { symbol }
         token1 { symbol }
         totalValueLockedUSD
       }
     }
     ```

