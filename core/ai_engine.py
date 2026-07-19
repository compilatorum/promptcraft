# -*- coding: utf-8 -*-
"""
===============================================================================
MÓDULO: core/ai_engine.py
DESCRIÇÃO: Motor Unificado de Inteligência Artificial para o PromptCraft.
           Gerencia geradores de LLM (Gemini, OpenAI, Anthropic, Hugging Face,
           Ollama/Qwen) e fornece métodos diretos de inferência e resumo.
AUTOR: Equipe Antigravity / PromptCraft Core
===============================================================================
"""

import urllib.request
import urllib.error
import json
from typing import Callable, Optional
from core.config import log_info, log_warning, log_error, resolve_api_key

def get_generator(provider: str, model_name: str = None, api_key: str = None, temperature: float = 0.2) -> Callable[[str], str]:
    """
    Retorna uma função geradora `generate(prompt: str) -> str` configurada para
    o provedor e modelo solicitados. Suporta fallbacks limpos e APIs REST nativas.
    """
    provider = (provider or "gemini").lower()
    resolved_key = resolve_api_key(provider, api_key)

    # -------------------------------------------------------------------------
    # PROVEDOR: GEMINI (Google Generative AI)
    # -------------------------------------------------------------------------
    if provider == "gemini":
        model_target = model_name or "gemini-1.5-flash"
        if not resolved_key:
            log_warning("Chave do Gemini não encontrada. Tentando fallback para Hugging Face / Ollama local...")
            return get_generator("huggingface", model_name, api_key, temperature)

        def generate_gemini(prompt: str) -> str:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_target}:generateContent?key={resolved_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature}
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                res_data = json.loads(resp.read().decode('utf-8'))
                return res_data['candidates'][0]['content']['parts'][0]['text']

        return generate_gemini

    # -------------------------------------------------------------------------
    # PROVEDOR: OPENAI (GPT-4o, GPT-3.5-turbo, etc.)
    # -------------------------------------------------------------------------
    elif provider == "openai":
        model_target = model_name or "gpt-4o-mini"
        if not resolved_key:
            raise ValueError("Chave de API OpenAI não informada ou não configurada.")

        def generate_openai(prompt: str) -> str:
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": model_target,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {resolved_key}'
                }
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                res_data = json.loads(resp.read().decode('utf-8'))
                return res_data['choices'][0]['message']['content']

        return generate_openai

    # -------------------------------------------------------------------------
    # PROVEDOR: HUGGING FACE (Serverless Inference API)
    # -------------------------------------------------------------------------
    elif provider in ["huggingface", "hf"]:
        model_target = model_name or "meta-llama/Llama-3.3-70B-Instruct"
        def generate_hf(prompt: str) -> str:
            url = f"https://api-inference.huggingface.co/models/{model_target}/v1/chat/completions"
            headers = {'Content-Type': 'application/json'}
            if resolved_key:
                headers['Authorization'] = f'Bearer {resolved_key}'
            payload = {
                "model": model_target,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": 2048
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                res_data = json.loads(resp.read().decode('utf-8'))
                return res_data['choices'][0]['message']['content']

        return generate_hf

    # -------------------------------------------------------------------------
    # PROVEDOR: OLLAMA / LOCAL (Qwen, Llama local no Termux/PC)
    # -------------------------------------------------------------------------
    elif provider in ["ollama", "local"]:
        host = resolved_key or "http://localhost:11434"
        model_target = model_name or "qwen2.5-coder"
        def generate_ollama(prompt: str) -> str:
            url = f"{host}/api/generate"
            payload = {"model": model_target, "prompt": prompt, "stream": False}
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=120) as resp:
                res_data = json.loads(resp.read().decode('utf-8'))
                return res_data.get('response', '')

        return generate_ollama

    else:
        raise ValueError(f"Provedor de IA desconhecido ou não suportado: {provider}")

def direct_summarize_text(text: str, generator: Callable[[str], str], custom_prompt: str = None) -> str:
    """
    Executa um resumo direto e descomplicado sobre o texto fornecido.
    Evita meta-prompts pesados quando o usuário só precisa de uma transcrição/resumo limpo no Termux.
    """
    if not custom_prompt:
        custom_prompt = (
            "Você é um assistente conciso e prático. Sintetize o conteúdo a seguir em tópicos claros em português.\n"
            "Destaque: 1) Ideias principais, 2) Pontos de ação/insights, 3) Conclusão.\n"
            "Mantenha uma linguagem direta e evite jargões desnecessários.\n\n"
            f"--- CONTEÚDO ---\n{text}\n"
        )
    return generator(custom_prompt)
