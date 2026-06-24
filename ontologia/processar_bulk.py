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
    """Initializes the SQLite database with the exact schema of org-roam v2."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Drop legacy table if it exists
    cursor.execute("DROP TABLE IF EXISTS fontes;")
    
    # Create org-roam v2 compliant tables with composite primary keys to prevent duplication
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        file TEXT UNIQUE PRIMARY KEY,
        title TEXT,
        hash TEXT NOT NULL,
        atime INTEGER NOT NULL,
        mtime INTEGER NOT NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nodes (
        id TEXT NOT NULL PRIMARY KEY,
        file TEXT NOT NULL,
        level INTEGER NOT NULL,
        pos INTEGER NOT NULL,
        todo TEXT,
        priority TEXT,
        scheduled TEXT,
        deadline TEXT,
        title TEXT,
        properties TEXT,
        olp TEXT,
        FOREIGN KEY (file) REFERENCES files (file) ON DELETE CASCADE
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS aliases (
        node_id TEXT NOT NULL,
        alias TEXT,
        PRIMARY KEY (node_id, alias),
        FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS citations (
        node_id TEXT NOT NULL,
        cite_key TEXT NOT NULL,
        pos INTEGER NOT NULL,
        properties TEXT,
        PRIMARY KEY (node_id, cite_key, pos),
        FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS refs (
        node_id TEXT NOT NULL,
        ref TEXT NOT NULL,
        type TEXT NOT NULL,
        PRIMARY KEY (node_id, ref, type),
        FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tags (
        node_id TEXT NOT NULL,
        tag TEXT,
        PRIMARY KEY (node_id, tag),
        FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS links (
        pos INTEGER NOT NULL,
        source TEXT NOT NULL,
        dest TEXT NOT NULL,
        type TEXT NOT NULL,
        properties TEXT NOT NULL,
        PRIMARY KEY (pos, source, dest, type),
        FOREIGN KEY (source) REFERENCES nodes (id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()
    print(f"✅ Banco de dados SQLite inicializado com a estrutura do org-roam v2 em: {DB_PATH}")

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
    print("🚀 Povoando tabelas do org-roam v2 com todas as fontes...")
    insert_count = 0
    now_ts = int(datetime.now().timestamp())
    
    for idx, src in enumerate(sources):
        url_hash = hashlib.sha256(src["url"].encode('utf-8')).hexdigest()[:16]
        category = classify_source(src["title"], src["url"], tags_dict)
        
        # Virtual Denote/Org path
        virtual_file = f"shared-knowledge/{src['source_type']}/{url_hash}__{src['source_type']}.org"
        
        # Insert into 'files'
        cursor.execute("""
        INSERT OR IGNORE INTO files (file, title, hash, atime, mtime)
        VALUES (?, ?, ?, ?, ?);
        """, (virtual_file, src["title"], url_hash, now_ts, now_ts))
        
        # Insert into 'nodes' (storing status & url in properties JSON)
        properties_json = json.dumps({
            "url": src["url"],
            "source_type": src["source_type"],
            "status": "pending",
            "distilled_content": ""
        })
        cursor.execute("""
        INSERT OR IGNORE INTO nodes (id, file, level, pos, title, properties)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (url_hash, virtual_file, 0, 1, src["title"], properties_json))
        
        # Insert into 'refs'
        cursor.execute("""
        INSERT OR IGNORE INTO refs (node_id, ref, type)
        VALUES (?, ?, ?);
        """, (url_hash, src["url"], "url"))
        
        # Insert into 'tags'
        cursor.execute("""
        INSERT OR IGNORE INTO tags (node_id, tag)
        VALUES (?, ?);
        """, (url_hash, category.lower()))
        
        insert_count += 1
            
        if idx > 0 and idx % 5000 == 0:
            conn.commit()
            print(f"   -> {idx}/{len(sources)} fontes processadas...")
            
    conn.commit()
    print(f"✅ Povoamento concluído. {insert_count} fontes mapeadas nas tabelas org-roam.")
    
    # 2. Select a representative sample from each source type to perform a REAL fetch and distillation
    samples = [
        {"source_type": "youtube", "url": "https://www.youtube.com/watch?v=S6xzKM5UuOM", "title": "Vídeo Metacognitivo de Teste"},
        {"source_type": "github", "url": "https://github.com/compilatorum/promptcraft", "title": "Repositório Promptcraft"},
        {"source_type": "snapshot", "url": "https://snapshot.org/#/ens.eth/proposal/0x9ed89cf79760eb92d220fee2da08896bf027317f394aab87863011f964e19453", "title": "[6.45][Social] Renewal of the Security Council"},
        {"source_type": "arxiv", "url": "http://arxiv.org/abs/2304.12345v3", "title": "Non-isometric codes for the black hole interior"},
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
                distilled_content = promptcraft.fetch_url_text(s["url"])
                status = "processed"
            elif s["source_type"] == "github":
                req = urllib.request.Request(
                    "https://api.github.com/repos/compilatorum/promptcraft",
                    headers={"User-Agent": "Mozilla/5.0 promptcraft-cli"}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    repo_data = json.loads(response.read().decode('utf-8'))
                    distilled_content = f"GitHub Starred Repo: {repo_data.get('full_name')}\nDescription: {repo_data.get('description')}\nStars: {repo_data.get('stargazers_count')}\nLanguage: {repo_data.get('language')}"
                status = "processed"
            elif s["source_type"] == "snapshot":
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
                recs = promptcraft.fetch_semantic_scholar_recommendations("2304.12345")
                if recs:
                    distilled_content = f"arXiv Paper Recommendations:\n" + "\n".join([f"- {r['title']} ({r['url']})" for r in recs])
                else:
                    distilled_content = "Nenhuma recomendação adjacente encontrada."
                status = "processed"
            elif s["source_type"] == "bookmarks":
                distilled_content = promptcraft.fetch_url_text(s["url"])
                status = "processed"
                
        except Exception as e:
            err_msg = str(e)
            print(f"   ⚠️ Falha ao processar {s['source_type']}: {err_msg}")
            
        virtual_file = f"shared-knowledge/{s['source_type']}/{url_hash}__{s['source_type']}.org"
        
        # Insert/Update in 'files'
        cursor.execute("""
        INSERT INTO files (file, title, hash, atime, mtime)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(file) DO UPDATE SET
            title = excluded.title,
            mtime = excluded.mtime;
        """, (virtual_file, s["title"], url_hash, now_ts, now_ts))
        
        # Insert/Update in 'nodes' (storing status, error & content in properties JSON)
        properties_json = json.dumps({
            "url": s["url"],
            "source_type": s["source_type"],
            "status": status,
            "error_message": err_msg,
            "distilled_content": distilled_content
        })
        cursor.execute("""
        INSERT INTO nodes (id, file, level, pos, title, properties)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            properties = excluded.properties;
        """, (url_hash, virtual_file, 0, 1, s["title"], properties_json))
        
        # Insert/Update in 'refs'
        cursor.execute("""
        INSERT OR IGNORE INTO refs (node_id, ref, type)
        VALUES (?, ?, ?);
        """, (url_hash, s["url"], "url"))
        
        # Insert/Update in 'tags'
        cursor.execute("""
        INSERT OR IGNORE INTO tags (node_id, tag)
        VALUES (?, ?);
        """, (url_hash, category.lower()))
        
    conn.commit()
    conn.close()
    print("\n✅ Processamento e destilação de amostras concluídos!")
    
    # 3. Analyze results
    analyze_database_results()

def analyze_database_results():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT count(*) FROM files")
    total_files = cursor.fetchone()[0]
    
    cursor.execute("SELECT count(*) FROM nodes")
    total_nodes = cursor.fetchone()[0]
    
    # Parse properties in Python to count status since SQLite doesn't natively parse JSON in older systems
    cursor.execute("SELECT properties FROM nodes")
    rows = cursor.fetchall()
    
    processed = 0
    pending = 0
    failed = 0
    for r in rows:
        props = json.loads(r[0]) if r[0] else {}
        status = props.get("status")
        if status == "processed":
            processed += 1
        elif status == "failed":
            failed += 1
        else:
            pending += 1
            
    print("\n==================================================")
    print("🔬 ANÁLISE DE QUALIDADE E COBERTURA DO BANCO PKM (org-roam v2)")
    print("==================================================")
    print(f"Total de Arquivos Virtuais (files): {total_files}")
    print(f"Total de Nós de Conhecimento (nodes): {total_nodes}")
    print(f"Nós Processados com Sucesso: {processed}")
    print(f"Nós Pendentes na Fila: {pending}")
    print(f"Nós com Falhas de Acesso: {failed}")
    print("--------------------------------------------------")
    
    # Distribution by Tag
    cursor.execute("SELECT tag, count(*) FROM tags GROUP BY tag")
    print("Distribuição por Tag / Categoria Org-Roam:")
    for tag, cnt in cursor.fetchall():
        print(f"  - {tag}: {cnt} nós ({cnt/total_nodes:.2%})")
        
    print("==================================================")
    conn.close()

if __name__ == "__main__":
    process_batch()
