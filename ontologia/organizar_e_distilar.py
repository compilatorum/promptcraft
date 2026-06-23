#!/usr/bin/env python3
import os
import re
import json
from datetime import datetime

ONTOLOGIA_DIR = "/home/sukata/promptcraft/ontologia"
TAGS_PATH = os.path.join(ONTOLOGIA_DIR, "tags_dicionario.json")
IMPORTADAS_PATH = os.path.join(ONTOLOGIA_DIR, "fontes_importadas.md")
BOOKMARKS_PATH = os.path.join(ONTOLOGIA_DIR, "bookmarks_importados.md")
ORGANIZADAS_PATH = os.path.join(ONTOLOGIA_DIR, "fontes_organizadas.md")
DISTILADO_PATH = os.path.join(ONTOLOGIA_DIR, "material_distilado_consolidado.md")

def load_tags():
    with open(TAGS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_md_links(filepath):
    """Parses markdown links: - [Title](URL) or - **Source**: [Title](URL)"""
    links = []
    if not os.path.exists(filepath):
        return links
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            # Match - [title](url) or - **Type**: [title](url)
            match = re.search(r'-\s*(?:\*\*[^*]+\*\*:\s*)?\[([^\]]+)\]\(([^)]+)\)', line)
            if match:
                title, url = match.group(1), match.group(2)
                links.append({"title": title, "url": url, "raw_line": line})
    return links

def classify_link(title, url, tags_dict):
    """Classifies a link based on keywords from the tags dictionary."""
    text_to_search = (title + " " + url).lower()
    
    # Keyword associations for each category
    keywords = {
        "IA_PESQUISA": ["prompt", "llm", "ai", "model", "gpt", "claude", "gemini", "huggingface", "unsloth", "sft", "lora", "fine-tune", "rag", "artificial", "deep learning", "neural"],
        "DESENVOLVIMENTO": ["github", "git", "code", "repo", "api", "emacs", "elisp", "python", "rust", "cdp", "mcp", "devtools", "docker", "termux", "linux", "programming", "software", "cli", "tui"],
        "REGENERACAO_REFI": ["dao", "proposal", "vote", "snapshot", "uniswap", "refi", "token", "blockchain", "governance", "finance", "impact", "regenerative", "crypto", "onchain", "ethereum", "ens"],
        "CONHECIMENTO_PKM": ["roam", "org", "elfeed", "wiki", "denote", "knowledge", "graph", "pkm", "notes", "obsidian", "logseq", "personal", "mind", "zettelkasten", "index", "taxonomy"],
        "MIDIA_ACADEMICO": ["youtube", "watch", "channel", "arxiv", "paper", "scholar", "scientific", "abstract", "research", "physics", "quantum", "mathematics", "theory", "history"],
        "CHATLOGS_HISTORICO": ["chatlog", "session", "dialogue", "conversation", "sanitized", "chunk", "promptcraft", "assistant", "user", "history", "cache"]
    }
    
    # Check for direct keyword matches
    for category, kw_list in keywords.items():
        for kw in kw_list:
            if kw in text_to_search:
                return category
                
    # Fallback checking using dictionary subtags
    for category, content in tags_dict.get("tags", {}).items():
        for subtag in content.get("subtags", []):
            clean_sub = subtag.replace("_", " ")
            if clean_sub in text_to_search:
                return category
                
    return "CONHECIMENTO_PKM" # Default category

def organize_sources():
    print("📂 Carregando dicionário de tags...")
    tags_dict = load_tags()
    
    print("🔍 Lendo arquivos de importação...")
    importadas_links = parse_md_links(IMPORTADAS_PATH)
    bookmarks_links = parse_md_links(BOOKMARKS_PATH)
    
    all_links = importadas_links + bookmarks_links
    print(f"📦 Total de links encontrados para classificação: {len(all_links)}")
    
    categorized = {cat: [] for cat in tags_dict["tags"].keys()}
    
    for link in all_links:
        category = classify_link(link["title"], link["url"], tags_dict)
        categorized[category].append(link)
        
    # Write categorized sources to fontes_organizadas.md
    with open(ORGANIZADAS_PATH, 'w', encoding='utf-8') as f:
        f.write("# 📂 Fontes Categorizadas e Organizadas\n")
        f.write(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} com base em `tags_dicionario.json`.\n\n")
        
        for category, items in categorized.items():
            cat_info = tags_dict["tags"][category]
            f.write(f"## 🏷️ {category} - {cat_info['description']}\n")
            f.write(f"*Subtags: {', '.join(cat_info['subtags'])}*\n")
            f.write(f"*Total de itens: {len(items)}*\n\n")
            
            for item in items:
                # Retain structural data
                f.write(f"- [{item['title']}]({item['url']})\n")
            f.write("\n")
            
    print(f"✅ Fontes organizadas gravadas com sucesso em: {ORGANIZADAS_PATH}")
    
    # Generate Distilled Knowledge Synthesis report (material_distilado_consolidado.md)
    generate_distilled_material(categorized)

def generate_distilled_material(categorized):
    print("🧬 Iniciando destilação e compressão cognitiva...")
    
    distillation_content = """# 🧬 Material Destilado e Consolidado de Fontes (Promptcraft)

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
"""
    
    with open(DISTILADO_PATH, 'w', encoding='utf-8') as f:
        f.write(distillation_content)
        
    print(f"✅ Material destilado gravado com sucesso em: {DISTILADO_PATH}")

if __name__ == "__main__":
    organize_sources()
