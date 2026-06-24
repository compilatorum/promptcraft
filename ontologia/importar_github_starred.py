#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import hashlib
import subprocess
from datetime import datetime

# Add promptcraft to path
sys.path.append("/home/sukata/promptcraft")
sys.path.append("/home/sukata/promptcraft/ontologia")
import promptcraft
import processar_bulk

DB_PATH = "/home/sukata/promptcraft/ontologia/fontes_processadas.db"
TAGS_PATH = "/home/sukata/promptcraft/ontologia/tags_dicionario.json"

def get_github_token():
    try:
        # Retrieve token from gh CLI helper
        return subprocess.check_output(["gh", "auth", "token"]).decode().strip()
    except Exception as e:
        print(f"⚠️ Erro ao obter token do gh CLI: {e}")
        return None

def fetch_starred_repos(token):
    import urllib.request
    headers = {
        "User-Agent": "promptcraft-cli",
        "Accept": "application/vnd.github+json"
    }
    if token:
        headers["Authorization"] = f"token {token}"
        
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/compilatorum/starred?per_page=100&page={page}"
        print(f"🔄 Buscando página {page} de repositórios favoritos...")
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
                if not data:
                    break
                repos.extend(data)
                if len(data) < 100:
                    break
                page += 1
        except Exception as e:
            print(f"❌ Erro ao buscar página {page}: {e}")
            break
    return repos

def import_and_process():
    print("🚀 Iniciando importação e destilação de favoritos do GitHub para compilatorum...")
    
    token = get_github_token()
    if not token:
        print("❌ Não foi possível recuperar o token de autenticação do GitHub.")
        sys.exit(1)
        
    repos = fetch_starred_repos(token)
    print(f"✅ Recupeados {len(repos)} repositórios favoritados de compilatorum.")
    
    if not repos:
        print("🎉 Nenhum repositório favoritado encontrado para importar.")
        return
        
    # Reinitialize/ensure DB tables exist
    processar_bulk.init_db()
    tags_dict = processar_bulk.load_tags()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now_ts = int(datetime.now().timestamp())
    inserted_count = 0
    updated_count = 0
    
    for idx, repo in enumerate(repos):
        repo_name = repo.get("full_name", "")
        repo_url = repo.get("html_url", "")
        description = repo.get("description") or ""
        primary_lang = repo.get("language") or "Markdown"
        stars = repo.get("stargazers_count", 0)
        open_issues = repo.get("open_issues_count", 0)
        topics = repo.get("topics", [])
        license_name = (repo.get("license") or {}).get("name") if repo.get("license") else "N/A"
        homepage = repo.get("homepage") or ""
        updated_at = repo.get("updated_at") or ""
        owner = (repo.get("owner") or {}).get("login") or ""
        
        # 1. Distill content
        distilled_content = (
            f"GitHub Starred Repo: {repo_name}\n"
            f"Owner: {owner}\n"
            f"URL: {repo_url}\n"
            f"Homepage: {homepage}\n"
            f"Description: {description}\n"
            f"Primary Language: {primary_lang}\n"
            f"License: {license_name}\n"
            f"Stars: {stars}\n"
            f"Open Issues: {open_issues}\n"
            f"Topics: {', '.join(topics) if topics else 'N/A'}\n"
            f"Last Updated: {updated_at}\n"
        )
        
        url_hash = hashlib.sha256(repo_url.encode('utf-8')).hexdigest()[:16]
        virtual_file = f"shared-knowledge/github/{url_hash}__github.org"
        
        # 2. Classify source category & domain
        category = processar_bulk.classify_source(repo_name + " " + description, repo_url, tags_dict)
        domain_tag = processar_bulk.classify_domain(repo_url, tags_dict.get("domains", {}))
        
        properties_json = json.dumps({
            "url": repo_url,
            "source_type": "github",
            "status": "processed",
            "distilled_content": distilled_content
        })
        
        # Check if node already exists
        cursor.execute("SELECT id FROM nodes WHERE id = ?", (url_hash,))
        exists = cursor.fetchone()
        
        # 3. Insert or update files table
        cursor.execute("""
        INSERT INTO files (file, title, hash, atime, mtime, filename, extension, language, size_bytes, line_count, git_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(file) DO UPDATE SET
            title = excluded.title,
            hash = excluded.hash,
            mtime = excluded.mtime,
            language = excluded.language,
            size_bytes = excluded.size_bytes,
            line_count = excluded.line_count;
        """, (
            virtual_file, repo_name, url_hash, now_ts, now_ts,
            f"{url_hash}__github.org", "org", primary_lang.lower(),
            len(distilled_content), len(distilled_content.splitlines()), "clean"
        ))
        
        # 4. Insert or replace nodes table
        cursor.execute("""
        INSERT OR REPLACE INTO nodes (id, file, level, pos, title, properties)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (url_hash, virtual_file, 0, 1, repo_name, properties_json))
        
        # 5. Insert refs
        cursor.execute("""
        INSERT OR IGNORE INTO refs (node_id, ref, type)
        VALUES (?, ?, ?);
        """, (url_hash, repo_url, "url"))
        
        # 6. Insert primary tag
        cursor.execute("""
        INSERT OR IGNORE INTO tags (node_id, tag)
        VALUES (?, ?);
        """, (url_hash, category.lower()))
        
        # 7. Insert domain tag
        if domain_tag:
            cursor.execute("""
            INSERT OR IGNORE INTO tags (node_id, tag)
            VALUES (?, ?);
            """, (url_hash, domain_tag))
            
        # 8. Map topics to taxonomy subtags
        taxonomy_tags = ["github_starred"]
        for t in topics:
            t_clean = t.lower().replace("-", "_")
            for cat, cat_info in tags_dict.get("tags", {}).items():
                for subtag in cat_info.get("subtags", []):
                    if t_clean in subtag or subtag in t_clean:
                        taxonomy_tags.append(subtag)
                        
        for tag in set(taxonomy_tags):
            cursor.execute("""
            INSERT OR IGNORE INTO tags (node_id, tag)
            VALUES (?, ?);
            """, (url_hash, tag))
            
        if exists:
            updated_count += 1
        else:
            inserted_count += 1
            
        if idx > 0 and idx % 50 == 0:
            conn.commit()
            print(f"   -> {idx}/{len(repos)} repositórios processados...")
            
    conn.commit()
    conn.close()
    
    print("\n==================================================")
    print("📊 Importação e Processamento Concluídos!")
    print(f"  - Repositórios Starred Novos (Inseridos): {inserted_count}")
    print(f"  - Repositórios Starred Atualizados: {updated_count}")
    print(f"  - Total Geral Processado: {inserted_count + updated_count}")
    print("==================================================")

if __name__ == "__main__":
    import_and_process()
