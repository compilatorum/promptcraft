# -*- coding: utf-8 -*-
"""
===============================================================================
MÓDULO: connectors/arxiv_connector.py
DESCRIÇÃO: Consulta e extração de artigos científicos do arXiv e citações
           do Semantic Scholar.
===============================================================================
"""

import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from core.config import log_info, log_warning

def fetch_arxiv_metadata(query_or_ids: str) -> List[Dict[str, Any]]:
    """
    Busca metadados e resumos de artigos no ArXiv por palavras-chave ou IDs.
    """
    log_info(f"Consultando API do arXiv para a busca: '{query_or_ids}'...")
    base_url = "http://export.arxiv.org/api/query?"
    if any(char.isdigit() for char in query_or_ids) and "." in query_or_ids:
        params = {"id_list": query_or_ids.strip()}
    else:
        params = {"search_query": f"all:{query_or_ids.strip()}", "start": 0, "max_results": 10}

    url = base_url + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'PromptCraft/2.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_data = resp.read().decode('utf-8')

        root = ET.fromstring(xml_data)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        results = []
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
            arxiv_id = entry.find('atom:id', ns).text.split('/abs/')[-1]
            published = entry.find('atom:published', ns).text
            authors = [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)]
            
            results.append({
                "source_type": "arxiv",
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors,
                "summary": summary,
                "published": published,
                "url": f"https://arxiv.org/abs/{arxiv_id}"
            })
        return results
    except Exception as e:
        log_warning(f"Erro ao consultar o arXiv: {e}")
        return []

def fetch_semantic_scholar_recommendations(arxiv_id: str) -> List[Dict[str, Any]]:
    """
    Busca recomendações de artigos e citações relacionadas via API do Semantic Scholar.
    """
    url = f"https://api.semanticscholar.org/graph/v1/paper/ARXIV:{arxiv_id}?fields=title,authors,citations,references,abstract"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'PromptCraft/2.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data.get('references', [])[:5]
    except Exception as e:
        log_warning(f"Não foi possível obter recomendações do Semantic Scholar para {arxiv_id}: {e}")
        return []
