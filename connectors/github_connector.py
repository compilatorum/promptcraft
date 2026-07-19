# -*- coding: utf-8 -*-
"""
===============================================================================
MÓDULO: connectors/github_connector.py
DESCRIÇÃO: Extração e ingestão de repositórios e estrelas (starred) do GitHub.
===============================================================================
"""

import json
import urllib.request
import urllib.error
from typing import List, Dict, Any
from core.config import log_info, log_warning, resolve_api_key

def fetch_github_starred(username: str = None, token: str = None) -> List[Dict[str, Any]]:
    """
    Busca os repositórios favoritados (starred) de um usuário do GitHub via API REST v3.
    """
    token = resolve_api_key("github", token)
    if not username:
        username = "sukata"  # Usuário padrão do ambiente local

    log_info(f"Buscando repositórios favoritados no GitHub para o usuário: {username}...")
    url = f"https://api.github.com/users/{username}/starred?per_page=100"
    headers = {'User-Agent': 'PromptCraft-Ingestor'}
    if token:
        headers['Authorization'] = f'token {token}'

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            repos = []
            for r in data:
                repos.append({
                    "name": r.get("full_name"),
                    "url": r.get("html_url"),
                    "description": r.get("description", ""),
                    "language": r.get("language", ""),
                    "stars": r.get("stargazers_count", 0),
                    "updated_at": r.get("updated_at")
                })
            log_info(f"Encontrados {len(repos)} repositórios favoritados no GitHub.")
            return repos
    except Exception as e:
        log_warning(f"Erro ao buscar favoritados do GitHub: {e}")
        return []
