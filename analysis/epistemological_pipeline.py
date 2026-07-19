# -*- coding: utf-8 -*-
"""
===============================================================================
MÓDULO: analysis/epistemological_pipeline.py
DESCRIÇÃO: Esteira Metacognitiva Avançada de Destilação Ontológica (3 Etapas).
           Executa a Desconstrução Atômica, Tecelagem Nexialista e Refatoração
           Ontológica para pesquisas profundas e atualização da base viva.
===============================================================================
"""

import os
from typing import Callable, Dict, Any
from core.config import log_info, log_success

def load_template(template_name: str, base_dir: str = None) -> str:
    """Carrega o conteúdo do template Markdown a partir de templates/."""
    if not base_dir:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, 'templates', template_name)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def run_epistemological_pipeline(content: str, source_ref: str, domain: str, generator: Callable[[str], str]) -> Dict[str, Any]:
    """
    Executa o pipeline metacognitivo completo de 3 etapas sobre um documento ou URL.
    """
    log_info(f"Iniciando Pipeline Metacognitivo Avançado para [{source_ref}] no domínio [{domain}]...")

    # Etapa 1: Desconstrutor Atômico
    log_info("Etapa 1/3: Executando Desconstrutor Atômico...")
    t1 = load_template("desconstrutor_atomico.md")
    p1 = f"{t1}\n\n[CONTEÚDO BRUTO]\n{content[:20000]}" if t1 else f"Desconstrua os axiomas principais do conteúdo:\n{content[:20000]}"
    res1 = generator(p1)

    # Etapa 2: Tecelão Nexialista
    log_info("Etapa 2/3: Executando Tecelão Nexialista...")
    t2 = load_template("tecelao_nexialista.md")
    p2 = f"{t2}\n\n[SÍNTESE ATÔMICA ETAPA 1]\n{res1}" if t2 else f"Mapeie isomorfismos e conexões causais:\n{res1}"
    res2 = generator(p2)

    # Etapa 3: Refatorador Ontológico
    log_info("Etapa 3/3: Executando Refatorador Ontológico...")
    t3 = load_template("refatorador_ontologico.md")
    p3 = f"{t3}\n\n[TECELAGEM ETAPA 2]\n{res2}" if t3 else f"Gere o Diff Semântico e mutação de princípios:\n{res2}"
    res3 = generator(p3)

    log_success("Pipeline Metacognitivo concluído!")

    full_report = (
        f"# 🧬 Relatório de Destilação Epistemológica — {source_ref}\n"
        f"**Domínio**: {domain}  \n\n"
        f"--- \n\n## ⚛️ 1. Desconstrução Atômica\n{res1}\n\n"
        f"--- \n\n## 🕸️ 2. Tecelagem Nexialista\n{res2}\n\n"
        f"--- \n\n## 🔄 3. Diff Semântico e Refatoração\n{res3}\n"
    )

    return {
        "status": "success",
        "source_ref": source_ref,
        "domain": domain,
        "desconstrucao": res1,
        "tecelagem": res2,
        "refatoracao": res3,
        "full_report": full_report
    }
