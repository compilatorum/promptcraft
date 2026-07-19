# -*- coding: utf-8 -*-
"""
===============================================================================
MÓDULO: connectors/finance_connector.py
DESCRIÇÃO: Ingestão de Dados Financeiros e Métricas de Fluxo (sovereign-budget).
           Processa OFX, CSV bancários, Beancount e calcula métricas como VRC
           (Velocidade de Retenção de Capital) e TCR (Taxa de Conversão de Renda).
===============================================================================
"""

import os
import re
import csv
from typing import Dict, Any, List
from core.config import log_info, log_warning

def parse_ofx_file(filepath: str) -> List[Dict[str, Any]]:
    """
    Realiza o parse de arquivos bancários OFX locais sem dependências externas.
    Extrai data, valor, memo/descrição e ID da transação.
    """
    if not os.path.exists(filepath):
        log_warning(f"Arquivo OFX não encontrado: {filepath}")
        return []

    log_info(f"Processando extrato bancário OFX: {filepath}...")
    transactions = []
    with open(filepath, 'r', encoding='latin-1', errors='ignore') as f:
        content = f.read()

    # Regex para capturar blocos STMTTRN
    raw_txs = re.findall(r'<STMTTRN>(.*?)</STMTTRN>', content, re.DOTALL)
    for raw in raw_txs:
        amount_match = re.search(r'<TRNAMT>([\d\.\-]+)', raw)
        memo_match = re.search(r'<MEMO>(.*?)\n', raw) or re.search(r'<NAME>(.*?)\n', raw)
        date_match = re.search(r'<DTPOSTED>(\d{8})', raw)
        fitid_match = re.search(r'<FITID>(.*?)\n', raw)

        amount = float(amount_match.group(1)) if amount_match else 0.0
        memo = memo_match.group(1).strip() if memo_match else "Sem Descrição"
        dt = date_match.group(1) if date_match else "19700101"
        fitid = fitid_match.group(1).strip() if fitid_match else ""

        transactions.append({
            "fitid": fitid,
            "date": f"{dt[:4]}-{dt[4:6]}-{dt[6:8]}",
            "amount": amount,
            "memo": memo,
            "currency": "BRL"
        })

    log_info(f"Extraídas {len(transactions)} transações do arquivo OFX.")
    return transactions

def calculate_capital_flow_metrics(checking_balance: float, survival_monthly_cost: float, yields_brl: float, active_income_brl: float) -> Dict[str, Any]:
    """
    Calcula as métricas de fluxo financeiro do sovereign-budget:
    - VRC (Velocidade de Retenção de Capital): Tempo que o excedente rende antes de custear passivos.
    - TCR (Taxa de Conversão de Renda): Proporção de renda gerada por yields passivos.
    - Buffer 15d: Verificação de reserva fiduciária de 15 dias no caixa.
    """
    buffer_required_15d = (survival_monthly_cost / 30.0) * 15.0
    buffer_ok = checking_balance >= buffer_required_15d
    
    total_income = active_income_brl + yields_brl
    tcr = (yields_brl / total_income) if total_income > 0 else 0.0

    return {
        "checking_balance": checking_balance,
        "buffer_required_15d": buffer_required_15d,
        "buffer_healthy": buffer_ok,
        "yields_brl": yields_brl,
        "active_income_brl": active_income_brl,
        "tcr_taxa_conversao_renda": round(tcr, 4),
        "alert": None if buffer_ok else "🚨 ALERTA: Saldo em CC abaixo do buffer mínimo de 15 dias de existência!"
    }
