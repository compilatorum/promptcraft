# -*- coding: utf-8 -*-
"""
===============================================================================
MÓDULO: connectors/links_vault_connector.py
DESCRIÇÃO: Coletor e Cofre de Links / Favoritos (links-vault).
           Parses de bookmarks em formato Netscape HTML, desduplicação de URLs,
           extração de links de arquivos text/markdown e integração com Archive.org.
===============================================================================
"""

import os
import re
from html.parser import HTMLParser
from typing import List, Dict, Any
from core.config import log_info, log_warning

class NetscapeBookmarkParser(HTMLParser):
    """Parser leve para arquivos de Favoritos (exportados do Chrome/Firefox/Safari)."""
    def __init__(self):
        super().__init__()
        self.bookmarks = []
        self.current_title = ""
        self.current_href = ""
        self.current_add_date = ""
        self.in_a_tag = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            self.in_a_tag = True
            self.current_title = ""
            for name, val in attrs:
                if name.lower() == 'href':
                    self.current_href = val
                elif name.lower() == 'add_date':
                    self.current_add_date = val

    def handle_endtag(self, tag):
        if tag.lower() == 'a':
            self.in_a_tag = False
            if self.current_href and not self.current_href.startswith("javascript:"):
                self.bookmarks.append({
                    "title": self.current_title.strip() or self.current_href,
                    "url": self.current_href.strip(),
                    "add_date": self.current_add_date
                })

    def handle_data(self, data):
        if self.in_a_tag:
            self.current_title += data

def parse_bookmarks_html(file_path: str) -> List[Dict[str, Any]]:
    """Lê e extrai todos os links de um arquivo HTML de favoritos."""
    if not os.path.exists(file_path):
        log_warning(f"Arquivo de favoritos não encontrado: {file_path}")
        return []

    log_info(f"Lendo favoritos do arquivo: {file_path}...")
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        html_content = f.read()

    parser = NetscapeBookmarkParser()
    parser.feed(html_content)
    log_info(f"Extraídos {len(parser.bookmarks)} links de favoritos.")
    return parser.bookmarks

def extract_links_from_text(text: str) -> List[str]:
    """Extrai todas as URLs HTTP/HTTPS encontradas em um bloco de texto."""
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    matches = re.findall(url_pattern, text)
    cleaned = list(set([m.rstrip('.,);]') for m in matches]))
    return cleaned
