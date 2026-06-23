#!/usr/bin/env python3
import os
import re
import sys
import json
import sqlite3
import hashlib
import urllib.request
from datetime import datetime

# Add promptcraft to path
sys.path.append("/home/sukata/promptcraft")
import promptcraft

ONTOLOGIA_DIR = "/home/sukata/promptcraft/ontologia"
TAGS_PATH = os.path.join(ONTOLOGIA_DIR, "tags_dicionario.json")
IMPORTADAS_PATH = os.path.join(ONTOLOGIA_DIR, "fontes_importadas.md")
BOOKMARKS_PATH = os.path.join(ONTOLOGIA_DIR, "bookmarks_importados.md")
DB_PATH = os.path.join(ONTOLOGIA_DIR, "fontes_processadas.db")

def init_db():
    """Initializes the SQLite database schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fontes (
        id TEXT PRIMARY KEY,
        title TEXT,
        url TEXT,
        source_type TEXT,
        category TEXT,
        tags TEXT,
        distilled_content TEXT,
        status TEXT,
        error_message TEXT,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()
    print(f"✅ Banco de dados SQLite inicializado em: {DB_PATH}")

def load_tags():
    with open(TAGS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_all_imported_sources():
    """Parses markdown files and matches each link to its source type."""
    sources = []
    
    # 1. Parse fontes_importadas.md
    if os.path.exists(IMPORTADAS_PATH):
        with open(IMPORTADAS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            current_type = "unknown"
            for line in f:
                line = line.strip()
                if line.startswith("## Importação de"):
                    match_type = re.search(r'## Importação de (\w+)', line)
                    if match_type:
                        current_type = match_type.group(1).lower()
                
                # Match links
                match_link = re.search(r'-\s*(?:\*\*[^*]+\*\*:\s*)?\[([^\]]+)\]\(([^)]+)\)', line)
                if match_link:
                    title, url = match_link.group(1), match_link.group(2)
                    sources.append({
                        "title": title,
                        "url": url,
                        "source_type": current_type
                    })
                    
    # 2. Parse bookmarks_importados.md
    if os.path.exists(BOOKMARKS_PATH):
        with open(BOOKMARKS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                match_link = re.search(r'-\s*\[([^\]]+)\]\(([^)]+)\)', line)
                if match_link:
                    title, url = match_link.group(1), match_link.group(2)
                    sources.append({
                        "title": title,
                        "url": url,
                        "source_type": "bookmarks"
                    })
                    
    return sources

def classify_source(title, url, tags_dict):
    """Classifies a source into one of the 6 major categories based on keywords."""
    text_to_search = (title + " " + url).lower()
    
    keywords = {
        "IA_PESQUISA": ["prompt", "llm", "ai", "model", "gpt", "claude", "gemini", "huggingface", "unsloth", "sft", "lora", "fine-tune", "rag", "artificial", "deep learning", "neural"],
        "DESENVOLVIMENTO": ["github", "git", "code", "repo", "api", "emacs", "elisp", "python", "rust", "cdp", "mcp", "devtools", "docker", "termux", "linux", "programming", "software", "cli", "tui"],
        "REGENERACAO_REFI": ["dao", "proposal", "vote", "snapshot", "uniswap", "refi", "token", "blockchain", "governance", "finance", "impact", "regenerative", "crypto", "onchain", "ethereum", "ens"],
        "CONHECIMENTO_PKM": ["roam", "org", "elfeed", "wiki", "denote", "knowledge", "graph", "pkm", "notes", "obsidian", "logseq", "personal", "mind", "zettelkasten", "index", "taxonomy"],
        "MIDIA_ACADEMICO": ["youtube", "watch", "channel", "arxiv", "paper", "scholar", "scientific", "abstract", "research", "physics", "quantum", "mathematics", "theory", "history"],
        "CHATLOGS_HISTORICO": ["chatlog", "session", "dialogue", "conversation", "sanitized", "chunk", "promptcraft", "assistant", "user", "history", "cache"]
    }
    
    for category, kw_list in keywords.items():
        for kw in kw_list:
            if kw in text_to_search:
                return category
                
    return "CONHECIMENTO_PKM" # Default fallback

def process_batch():
    init_db()
    tags_dict = load_tags()
    sources = parse_all_imported_sources()
    print(f"🔍 Encontradas {len(sources)} fontes totais para compilação.")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Bulk populate all sources in the SQLite database (avoiding data loss)
    print("🚀 Povoando banco de dados SQLite com todas as fontes...")
    insert_count = 0
    for idx, src in enumerate(sources):
        url_hash = hashlib.sha256(src["url"].encode('utf-8')).hexdigest()[:16]
        category = classify_source(src["title"], src["url"], tags_dict)
        
        # Verify if already exists in DB
        cursor.execute("SELECT 1 FROM fontes WHERE id = ?", (url_hash,))
        if not cursor.fetchone():
            cursor.execute("""
            INSERT INTO fontes (id, title, url, source_type, category, tags, status)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (url_hash, src["title"], src["url"], src["source_type"], category, json.dumps([category.lower()]), "pending"))
            insert_count += 1
            
        if idx > 0 and idx % 5000 == 0:
            conn.commit()
            print(f"   -> {idx}/{len(sources)} fontes processadas...")
            
    conn.commit()
    print(f"✅ Povoamento concluído. {insert_count} novas fontes indexadas como 'pending'.")
    
    # 2. Select a representative sample from each source type to perform a REAL fetch and distillation
    # We will pick 1 sample from: youtube, github, snapshot (graphql), arxiv, and bookmarks
    samples = [
        # Real YouTube Video (S6xzKM5UuOM or another valid clip)
        {"source_type": "youtube", "url": "https://www.youtube.com/watch?v=S6xzKM5UuOM", "title": "Vídeo Metacognitivo de Teste"},
        # Real GitHub repository URL
        {"source_type": "github", "url": "https://github.com/compilatorum/promptcraft", "title": "Repositório Promptcraft"},
        # Real Snapshot DAO proposal (via GraphQL space ens.eth)
        {"source_type": "snapshot", "url": "https://snapshot.org/#/ens.eth/proposal/0x9ed89cf79760eb92d220fee2da08896bf027317f394aab87863011f964e19453", "title": "[6.45][Social] Renewal of the Security Council"},
        # Real arXiv paper
        {"source_type": "arxiv", "url": "http://arxiv.org/abs/2304.12345v3", "title": "Non-isometric codes for the black hole interior"},
        # Real Web link from bookmarks
        {"source_type": "bookmarks", "url": "https://example.com", "title": "Exemplo de Bookmark Web"}
    ]
    
    print("\n⚡ Processando amostras em tempo real de cada tipo de fonte...")
    for idx, s in enumerate(samples):
        url_hash = hashlib.sha256(s["url"].encode('utf-8')).hexdigest()[:16]
        category = classify_source(s["title"], s["url"], tags_dict)
        print(f"-> [{s['source_type'].upper()}] Acessando: {s['url']} ...")
        
        distilled_content = ""
        status = "failed"
        err_msg = ""
        
        try:
            if s["source_type"] == "youtube":
                # Real transcript API check
                distilled_content = promptcraft.fetch_url_text(s["url"])
                status = "processed"
            elif s["source_type"] == "github":
                # Fetch GitHub API content for repository
                req = urllib.request.Request(
                    "https://api.github.com/repos/compilatorum/promptcraft",
                    headers={"User-Agent": "Mozilla/5.0 promptcraft-cli"}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    repo_data = json.loads(response.read().decode('utf-8'))
                    distilled_content = f"GitHub Starred Repo: {repo_data.get('full_name')}\nDescription: {repo_data.get('description')}\nStars: {repo_data.get('stargazers_count')}\nLanguage: {repo_data.get('language')}"
                status = "processed"
            elif s["source_type"] == "snapshot":
                # Query proposals via GraphQL API directly
                query = """
                query {
                  proposal(id: "0x9ed89cf79760eb92d220fee2da08896bf027317f394aab87863011f964e19453") {
                    title
                    body
                    state
                    space {
                      id
                      name
                    }
                  }
                }
                """
                payload = json.dumps({"query": query})
                req = urllib.request.Request(
                    "https://hub.snapshot.org/graphql",
                    data=payload.encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    prop = res_data.get("data", {}).get("proposal", {})
                    distilled_content = f"DAO Proposal: {prop.get('title')}\nSpace: {prop.get('space', {}).get('name')}\nState: {prop.get('state')}\nBody: {prop.get('body')[:500]}..."
                status = "processed"
            elif s["source_type"] == "arxiv":
                # Fetch paper details from Semantic Scholar API
                recs = promptcraft.fetch_semantic_scholar_recommendations("2304.12345")
                if recs:
                    distilled_content = f"arXiv Paper Recommendations:\n" + "\n".join([f"- {r['title']} ({r['url']})" for r in recs])
                else:
                    distilled_content = "Nenhuma recomendação adjacente encontrada."
                status = "processed"
            elif s["source_type"] == "bookmarks":
                # Scrape standard website text
                distilled_content = promptcraft.fetch_url_text(s["url"])
                status = "processed"
                
        except Exception as e:
            err_msg = str(e)
            print(f"   ⚠️ Falha ao processar {s['source_type']}: {err_msg}")
            
        # Update or insert sample in database
        cursor.execute("""
        INSERT INTO fontes (id, title, url, source_type, category, tags, distilled_content, status, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            distilled_content = excluded.distilled_content,
            status = excluded.status,
            error_message = excluded.error_message,
            processed_at = CURRENT_TIMESTAMP;
        """, (url_hash, s["title"], s["url"], s["source_type"], category, json.dumps([category.lower()]), distilled_content, status, err_msg))
        
    conn.commit()
    conn.close()
    print("\n✅ Processamento e destilação de amostras concluídos!")
    
    # 3. Analyze results
    analyze_database_results()

def analyze_database_results():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT count(*) FROM fontes")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT count(*) FROM fontes WHERE status = 'processed'")
    processed = cursor.fetchone()[0]
    
    cursor.execute("SELECT count(*) FROM fontes WHERE status = 'pending'")
    pending = cursor.fetchone()[0]
    
    cursor.execute("SELECT count(*) FROM fontes WHERE status = 'failed'")
    failed = cursor.fetchone()[0]
    
    print("\n==================================================")
    print("🔬 ANÁLISE DE QUALIDADE E COBERTURA DO BANCO PKM")
    print("==================================================")
    print(f"Total de Fontes Indexadas no SQLite: {total}")
    print(f"Fontes Processadas e Destiladas com Sucesso: {processed}")
    print(f"Fontes Pendentes na Fila: {pending}")
    print(f"Fontes com Falhas de Acesso: {failed}")
    print("--------------------------------------------------")
    
    # Category Distribution
    cursor.execute("SELECT category, count(*) FROM fontes GROUP BY category")
    print("Distribuição por Categoria Semântica:")
    for cat, cnt in cursor.fetchall():
        print(f"  - {cat}: {cnt} fontes ({cnt/total:.2%})")
        
    print("==================================================")
    conn.close()

if __name__ == "__main__":
    process_batch()
