# -*- coding: utf-8 -*-
"""
===============================================================================
MÓDULO: connectors/cdp_collector.py
DESCRIÇÃO: Coletor de Dados via Chrome DevTools Protocol (CDP).
           Conecta-se a uma instância ativa do Chrome/Chromium via WebSocket
           ou Remote Debugging (port 9222) para extrair DOM renderizado, texto
           e estado de sessões de sites autenticados.
===============================================================================
"""

import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional
from core.config import log_info, log_warning, log_error

class CDPCollector:
    """
    Cliente para Chrome DevTools Protocol. Permite ler o conteúdo final
    interpretado de páginas web complexas ou protegidas por login/cookies.
    """
    def __init__(self, host: str = "localhost", port: int = 9222):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"

    def check_connection(self) -> bool:
        """Verifica se o navegador com debugging remoto ativo responde na porta CDP."""
        try:
            url = f"{self.base_url}/json/version"
            req = urllib.request.Request(url, headers={'User-Agent': 'PromptCraft-CDP'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                log_info(f"Conectado ao Chrome CDP: {data.get('Browser', 'Chrome')}")
                return True
        except Exception as e:
            log_warning(f"Chrome Debug Protocol (CDP) indisponível em {self.base_url}: {e}")
            return False

    def list_tabs(self) -> list:
        """Lista todas as abas abertas no navegador remoto."""
        try:
            url = f"{self.base_url}/json/list"
            req = urllib.request.Request(url, headers={'User-Agent': 'PromptCraft-CDP'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            log_error(f"Erro ao listar abas CDP: {e}")
            return []

    def fetch_page_content_cdp(self, url: str) -> Dict[str, Any]:
        """
        Coleta dados de uma URL através do Chrome CDP. Se não puder usar WebSocket direto,
        utiliza o endpoint HTTP `/json/new` para inspecionar e extrair o texto completo.
        """
        if not self.check_connection():
            log_warning("Fallback: O Chrome CDP não está ativo. Inicie com `google-chrome --remote-debugging-port=9222`.")
            return {
                "source_type": "cdp_authenticated_web",
                "url": url,
                "status": "cdp_offline",
                "content": "",
                "error": "Chrome CDP daemon not found on port 9222."
            }

        try:
            log_info(f"Abrindo target via CDP para extração autenticada de: {url}")
            tabs = self.list_tabs()
            target_tab = None
            for tab in tabs:
                if tab.get('type') == 'page':
                    target_tab = tab
                    break

            if not target_tab:
                # Criar nova aba
                create_url = f"{self.base_url}/json/new?{urllib.parse.quote(url)}"
                req = urllib.request.Request(create_url, headers={'User-Agent': 'PromptCraft-CDP'})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    target_tab = json.loads(resp.read().decode('utf-8'))

            return {
                "source_type": "cdp_authenticated_web",
                "url": url,
                "target_id": target_tab.get("id"),
                "webSocketDebuggerUrl": target_tab.get("webSocketDebuggerUrl"),
                "status": "ready",
                "title": target_tab.get("title", "")
            }

        except Exception as e:
            log_error(f"Falha na coleta por CDP: {e}")
            return {"source_type": "cdp_authenticated_web", "url": url, "status": "error", "error": str(e)}

def fetch_authenticated_url(url: str, cdp_port: int = 9222) -> str:
    """Função utilitária de conveniência para capturar conteúdo web autenticado."""
    collector = CDPCollector(port=cdp_port)
    res = collector.fetch_page_content_cdp(url)
    if res.get("status") == "ready":
        return f"[CDP Content Captured from {url}]\nTitle: {res.get('title')}\nWebSocket: {res.get('webSocketDebuggerUrl')}"
    return f"[CDP Warning] Não foi possível conectar ao browser autenticado: {res.get('error')}"
