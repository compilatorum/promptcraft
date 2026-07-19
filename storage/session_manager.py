# -*- coding: utf-8 -*-
"""
===============================================================================
MÓDULO: storage/session_manager.py
DESCRIÇÃO: Gerenciador de Sessões e Backups do PromptCraft.
           Grava transcrições, relatórios e análises em `sessoes/` e cria
           backups incrementais da ontologia em `backups/`.
===============================================================================
"""

import os
import shutil
from datetime import datetime
from core.config import log_info, log_success

def save_session_output(content: str, session_name: str = None, base_dir: str = None) -> str:
    """
    Salva o resultado de uma análise ou resumo na pasta `sessoes/`.
    """
    if not base_dir:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sessoes_dir = os.path.join(base_dir, 'sessoes')
    os.makedirs(sessoes_dir, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    sanitized_name = (session_name or "analise").lower().replace(" ", "_")
    filename = f"{today}_{sanitized_name}.md"
    filepath = os.path.join(sessoes_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    log_success(f"Sessão salva com sucesso em: {filepath}")
    return filepath

def backup_ontology(base_dir: str = None) -> str:
    """
    Cria uma cópia de segurança da pasta `ontologia/` antes de atualizações.
    """
    if not base_dir:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ontologia_dir = os.path.join(base_dir, 'ontologia')
    backups_dir = os.path.join(base_dir, 'backups')
    os.makedirs(backups_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_backup = os.path.join(backups_dir, f"ontologia_backup_{timestamp}")

    if os.path.exists(ontologia_dir):
        shutil.copytree(ontologia_dir, target_backup)
        log_info(f"Backup da ontologia criado em: {target_backup}")
        return target_backup
    return ""
