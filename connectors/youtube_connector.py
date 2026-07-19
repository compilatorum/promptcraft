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
    r"""
    Extrai o ID único do vídeo a partir de URLs do YouTube (watch, shorts ou youtu.be).
    Suporta higienização de contrabarras de escape enviadas pelo shell (\?, \&, \=).
    """
    if not url:
        return None
    url_str = str(url).strip().replace('\\', '')
    
    # 1. Busca por v=ID na query string (em qualquer posição da URL)
    match_v = re.search(r'[?&]v=([0-9A-Za-z_-]{11})', url_str)
    if match_v:
        return match_v.group(1)
    
    # 2. Busca por caminhos comuns: youtu.be/ID, shorts/ID, embed/ID, v/ID
    match_path = re.search(r'(?:youtu\.be\/|shorts\/|embed\/|v\/)([0-9A-Za-z_-]{11})', url_str)
    if match_path:
        return match_path.group(1)
    
    # 3. Se for diretamente um ID de 11 caracteres isolado
    if re.fullmatch(r'[0-9A-Za-z_-]{11}', url_str):
        return url_str
    
    # 4. Fallback genérico para qualquer padrão de 11 caracteres parecidos com ID de vídeo
    match_gen = re.search(r'([0-9A-Za-z_-]{11})', url_str)
    if match_gen:
        return match_gen.group(1)
    
    return None

def fetch_youtube_transcript(url_or_id: str, languages=['pt', 'pt-BR', 'en', 'es']) -> Dict[str, Any]:
    """
    Busca e formata a transcrição completa de um vídeo do YouTube.
    Retorna um dicionário estruturado com metadados e o texto limpo da transcrição.
    """
    video_id = extract_youtube_video_id(url_or_id)
    if not video_id:
        raise ValueError(f"URL ou ID do YouTube inválido: {url_or_id}")

    log_info(f"Conectando à API de Transcrição do YouTube para o vídeo ID: {video_id}...")
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        
        try:
            transcript_list = api.fetch(video_id, languages=languages)
        except Exception:
            # Fallback inteligente: lista as transcrições disponíveis e obtém a primeira existente
            transcript_metadata = api.list(video_id)
            first_transcript = next(iter(transcript_metadata))
            transcript_list = first_transcript.fetch()

        full_text = " ".join([
            item.get('text', getattr(item, 'text', '')) if isinstance(item, dict) else getattr(item, 'text', str(item))
            for item in transcript_list
        ])
        
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

