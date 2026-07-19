# -*- coding: utf-8 -*-
"""
===============================================================================
MÓDULO: core/config.py
DESCRIÇÃO: Gerenciamento unificado de configurações, chaves de API, variáveis
           de ambiente e utilitários de log colorido para o PromptCraft.
AUTOR: Equipe Antigravity / PromptCraft Core
===============================================================================
"""

import os
import sys
import json

# Pontuação de volatilidade para classificação ontológica de dados
VOLATILITY_SCORES = {
    "video": 5,        # Transcrição de vídeo (Média volatilidade)
    "document": 2,     # Documentos estáticos/PDF (Baixa volatilidade)
    "code": 8,         # Repositórios de código (Alta volatilidade)
    "feed": 9,         # Feeds e redes sociais (Alta volatilidade)
    "data": 10,        # Dados quantitativos/financeiros (Muito alta)
    "personal": 6,     # Arquivos pessoais / Beancount (Variável)
    "bookmark": 4,     # Favoritos/Web links (Média volatilidade)
    "gdrive": 3        # Inventário de arquivos em nuvem (Baixa/Média)
}

# Cores ANSI para saída limpa e amigável no terminal (inclusive Termux)
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def log_info(msg: str):
    """Exibe mensagem informativa estilizada em azul."""
    print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {msg}")

def log_success(msg: str):
    """Exibe mensagem de sucesso estilizada em verde com marcação."""
    print(f"{Colors.GREEN}[✓]{Colors.ENDC} {msg}")

def log_warning(msg: str):
    """Exibe mensagem de alerta em amarelo."""
    print(f"{Colors.WARNING}[⚠️ AVISO]{Colors.ENDC} {msg}")

def log_error(msg: str):
    """Exibe mensagem de erro em vermelho no stderr."""
    print(f"{Colors.FAIL}[✗ ERRO]{Colors.ENDC} {msg}", file=sys.stderr)

def load_config(base_dir: str = None) -> dict:
    """
    Carrega as configurações locais do arquivo `config.json` se existente.
    Procura na raiz do projeto ou no diretório base especificado.
    """
    if not base_dir:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log_warning(f"Erro ao ler config.json: {e}")
    return {}

def resolve_api_key(provider: str, cli_key: str = None, base_dir: str = None) -> str:
    """
    Resolve a chave de API para um provedor específico.
    Ordem de prioridade:
      1. Argumento via CLI (--api-key)
      2. Variáveis de ambiente específicas (ex: GEMINI_API_KEY, OPENAI_API_KEY)
      3. Arquivo local `.env`
      4. Arquivo de configuração `config.json`
    """
    if cli_key:
        return cli_key

    env_vars = {
        "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "openai": ["OPENAI_API_KEY"],
        "anthropic": ["ANTHROPIC_API_KEY", "CLAUDE_API_KEY"],
        "huggingface": ["HUGGINGFACE_TOKEN", "HF_TOKEN", "HF_API_KEY"],
        "ollama": ["OLLAMA_HOST"],
        "supabase": ["SUPABASE_KEY", "SUPABASE_SERVICE_ROLE_KEY"]
    }

    # 1. Tentar variáveis de ambiente do SO
    for var in env_vars.get(provider.lower(), []):
        val = os.environ.get(var)
        if val:
            return val

    # 2. Carregar do arquivo config.json
    config = load_config(base_dir)
    cfg_key = config.get("api_keys", {}).get(provider.lower())
    if cfg_key:
        return cfg_key

    return ""
