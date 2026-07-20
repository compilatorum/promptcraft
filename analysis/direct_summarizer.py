# -*- coding: utf-8 -*-
"""
===============================================================================
MÓDULO: analysis/direct_summarizer.py
DESCRIÇÃO: Processador de Resumo Direto e Transcrição Descomplicada.
           Resolve o problema de saídas excessivamente complexas no Termux,
           fornecendo sintaxe concisa, tópicos ordenados e insights práticos.
===============================================================================
"""

from typing import Callable, Dict, Any
from core.config import log_info, log_warning, log_success
from core.ai_engine import direct_summarize_text
from connectors.youtube_connector import fetch_youtube_transcript

def process_youtube_summary_simple(url_or_id: str, generator: Callable[[str], str], no_llm: bool = False) -> Dict[str, Any]:
    """
    Fluxo simples e direto para vídeo do YouTube:
    1. Busca a transcrição limpa.
    2. Se no_llm=True ou se o LLM falhar (falta de chave, offline), exibe a transcrição completa capturada.
    3. Se o LLM estiver disponível, gera a síntese executiva em Markdown.
    """
    log_info(f"Iniciando síntese direta do vídeo: {url_or_id}...")
    yt_data = fetch_youtube_transcript(url_or_id)
    
    if yt_data.get("status") == "failed" or not yt_data.get("text"):
        return {
            "status": "error",
            "message": f"Não foi possível obter transcrição: {yt_data.get('error')}"
        }

    raw_text = yt_data["text"]
    video_id = yt_data["video_id"]
    url = yt_data["url"]
    
    log_info(f"Transcrição capturada ({len(raw_text)} caracteres).")

    if no_llm:
        log_info("Modo sem LLM ativado (--no-llm). Exibindo transcrição bruta...")
        summary_md = f"## 📜 Transcrição Completa do Vídeo (ID: {video_id})\n\n{raw_text}"
        return {
            "status": "success",
            "video_id": video_id,
            "url": url,
            "summary": summary_md,
            "raw_text": raw_text,
            "llm_used": False
        }

    log_info("Solicitando resumo ao LLM...")

    prompt = (
        "Você é um sintetizador de mídia de alta performance. "
        "Analise a transcrição do vídeo a seguir e apresente uma resposta limpa e bem organizada:\n\n"
        "## 📌 Resumo Executivo\n"
        "(2 a 3 parágrafos diretos sintetizando a mensagem central)\n\n"
        "## 💡 Principais Tópicos & Aprendizados\n"
        "(Lista numerada com os pontos mais importantes)\n\n"
        "## 🎯 Conclusão & Ações Práticas\n"
        "(Principais recomendações ou takeaways)\n\n"
        f"--- TRANSCRIÇÃO DO VÍDEO (ID: {video_id}) ---\n{raw_text[:15000]}\n"
    )

    try:
        summary_md = generator(prompt)
        log_success("Resumo direto concluído com sucesso!")
        return {
            "status": "success",
            "video_id": video_id,
            "url": url,
            "summary": summary_md,
            "raw_text": raw_text,
            "llm_used": True
        }
    except Exception as e:
        log_warning(f"Falha na síntese por LLM ({e}). Exibindo transcrição completa capturada...")
        fallback_md = (
            f"## 📜 Transcrição Completa do Vídeo (ID: {video_id})\n"
            f"> ⚠️ *Nota: A síntese por LLM não pôde ser concluída ({e}). Exibindo transcrição bruta.*\n\n"
            f"{raw_text}"
        )
        return {
            "status": "success",
            "video_id": video_id,
            "url": url,
            "summary": fallback_md,
            "raw_text": raw_text,
            "llm_used": False
        }

