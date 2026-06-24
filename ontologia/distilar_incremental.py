#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import hashlib
import time
from datetime import datetime

# Add promptcraft to path
sys.path.append("/home/sukata/promptcraft")
import promptcraft

DB_PATH = "/home/sukata/promptcraft/ontologia/fontes_processadas.db"
BATCH_SIZE = 50  # Number of links to process per run
DELAY_SECONDS = 3.0  # Respectful delay between network requests to avoid rate limits

def distilar_batch():
    if not os.path.exists(DB_PATH):
        print(f"❌ Banco de dados não encontrado em {DB_PATH}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Fetch pending web links
    print(f"🔍 Buscando até {BATCH_SIZE} links pendentes no SQLite...")
    
    cursor.execute("SELECT id, file, title, properties FROM nodes")
    rows = cursor.fetchall()
    
    pending_nodes = []
    for r_id, r_file, r_title, r_props in rows:
        props = json.loads(r_props) if r_props else {}
        status = props.get("status", "pending")
        source_type = props.get("source_type", "")
        url = props.get("url", "")
        
        # We process bookmarks and web links that are pending
        if status == "pending" and source_type in ["bookmarks", "arxiv", "youtube"] and url.startswith("http"):
            pending_nodes.append({
                "id": r_id,
                "file": r_file,
                "title": r_title,
                "url": url,
                "props": props
            })
            if len(pending_nodes) >= BATCH_SIZE:
                break
                
    if not pending_nodes:
        print("🎉 Nenhuma fonte pendente encontrada para processamento!")
        conn.close()
        return
        
    print(f"🚀 Iniciando destilação de {len(pending_nodes)} fontes...")
    processed_count = 0
    failed_count = 0
    
    for idx, node in enumerate(pending_nodes):
        print(f"[{idx+1}/{len(pending_nodes)}] Processando: {node['title']} ({node['url']})")
        
        distilled_content = ""
        status = "failed"
        err_msg = ""
        
        # Polite sleep between fetches
        if idx > 0:
            time.sleep(DELAY_SECONDS)
            
        try:
            # Fetch URL text
            raw_text = promptcraft.fetch_url_text(node["url"])
            if raw_text:
                # Basic token minimization: keep only the most information-dense part
                # e.g., first 5000 characters to save DB space and context windows
                distilled_content = raw_text[:5000]
                status = "processed"
                processed_count += 1
            else:
                err_msg = "Retorno vazio da URL"
                failed_count += 1
        except Exception as e:
            err_msg = str(e)
            print(f"   ⚠️ Falha ao obter URL: {err_msg}")
            failed_count += 1
            
        # Update properties JSON
        node["props"]["status"] = status
        node["props"]["distilled_content"] = distilled_content
        if err_msg:
            node["props"]["error_message"] = err_msg
            
        new_props_json = json.dumps(node["props"])
        
        # Save progress dynamically (commit each to avoid losing work on crash)
        cursor.execute("UPDATE nodes SET properties = ? WHERE id = ?", (new_props_json, node["id"]))
        conn.commit()
        
    conn.close()
    print(f"\n==================================================")
    print(f"📊 Relatório da Rodada:")
    print(f"  - Sucesso (Processed): {processed_count}")
    print(f"  - Falhas (Failed): {failed_count}")
    print(f"==================================================")

if __name__ == "__main__":
    distilar_batch()
