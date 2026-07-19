# -*- coding: utf-8 -*-
"""
===============================================================================
MÓDULO: connectors/gdrive_connector.py
DESCRIÇÃO: Ingestão e Indexação de Arquivos em Nuvem (gdrive-reorg).
           Lê inventários do rclone (JSON), indexa metadados de contas
           Google Drive e envia para tabelas de metadados / Supabase.
===============================================================================
"""

import os
import json
from typing import List, Dict, Any
from core.config import log_info, log_warning

def load_gdrive_inventory(inventory_json_path: str = "/home/sukata/inventory_full.json") -> List[Dict[str, Any]]:
    """
    Carrega o inventário rclone de contas do Google Drive a partir do arquivo JSON.
    """
    if not os.path.exists(inventory_json_path):
        log_warning(f"Inventário do Google Drive não encontrado em: {inventory_json_path}")
        return []

    log_info(f"Lendo inventário do Google Drive: {inventory_json_path}...")
    items = []
    with open(inventory_json_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                items = data
        except Exception:
            f.seek(0)
            for line in f:
                line = line.strip()
                if not line or line in ["[", "]"]:
                    continue
                if line.endswith(","):
                    line = line[:-1]
                try:
                    items.append(json.loads(line))
                except Exception:
                    pass

    log_info(f"Carregados {len(items)} itens do inventário de armazenamento em nuvem.")
    return items

def summarize_gdrive_distribution(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Sintetiza a distribuição por tipos MIME e tamanho total de arquivos no GDrive.
    """
    total_size = 0
    mime_counts = {}
    total_files = 0
    total_dirs = 0

    for item in items:
        if item.get("IsDir", False):
            total_dirs += 1
        else:
            total_files += 1
            size = item.get("Size", 0)
            total_size += size
            mime = item.get("MimeType", "unknown")
            mime_counts[mime] = mime_counts.get(mime, 0) + 1

    return {
        "total_items": len(items),
        "total_files": total_files,
        "total_dirs": total_dirs,
        "total_size_gb": round(total_size / (1024**3), 2),
        "top_mime_types": sorted(mime_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    }
