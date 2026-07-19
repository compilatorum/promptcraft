# -*- coding: utf-8 -*-
"""
===============================================================================
MÓDULO: connectors/youtube_connector.py
DESCRIÇÃO: Conector especializado para extração de transcrições e metadados
           de vídeos e shorts do YouTube.
===============================================================================
"""

import re
import urllib.parse
from typing import Dict, Any, Optional
from core.config import log_info, log_warning, log_error

def extract_youtube_video_id(url: str) -> Optional[str]:
    """
    Extrai o ID único do vídeo a partir de URLs do YouTube (watch, shorts ou youtu.be).
    """
    if not url:
        return None
    url_str = str(url).strip()
    
    if "youtu.be" in url_str.lower():
        return url_str.split('/')[-1].split('?')[0]
    
    parsed = urllib.parse.urlparse(url_str)
    queries = urllib.parse.parse_qs(parsed.query)
    if "v" in queries:
        return queries["v"][0]
    elif "/shorts/" in parsed.path:
        return parsed.path.split('/shorts/')[1].split('/')[0]
    
    # Fallback regex para extrair ID de 11 caracteres
    match = re.search(r'(?:v=|\/([0-9A-Za-z_-]{11}))', url_str)
    if match:
        return match.group(1) or match.group(0)
    
    return None

def fetch_youtube_transcript(url_or_id: str, languages=['pt', 'en', 'es']) -> Dict[str, Any]:
    """
    Busca e formata a transcrição completa de um vídeo do YouTube.
    Retorna um dicionário estruturado com metadados e o texto limpo da transcrição.
    """
    video_id = extract_youtube_video_id(url_or_id) if "http" in url_or_id else url_or_id
    if not video_id:
        raise ValueError(f"URL ou ID do YouTube inválido: {url_or_id}")

    log_info(f"Conectando à API de Transcrição do YouTube para o vídeo ID: {video_id}...")
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        # Tenta buscar a transcrição nos idiomas preferenciais
        transcript_list = YouTubeTranscriptApi().fetch(video_id, languages=languages)
        full_text = " ".join([item.get('text', item.text if hasattr(item, 'text') else '') for item in transcript_list])
        
        return {
            "source_type": "youtube",
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "text": full_text,
            "item_count": len(transcript_list),
            "status": "success"
        }
    except Exception as e:
        log_warning(f"Falha ao extrair transcrição oficial ({e}). Verifique se o vídeo possui legendas desativadas.")
        return {
            "source_type": "youtube",
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "text": "",
            "error": str(e),
            "status": "failed"
        }
