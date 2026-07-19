#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
PROMPTCRAFT — CLI Modular & Esteira de Inteligência Multimodal (v2.0)
===============================================================================
Orquestrador modular para ingestão de APIs, coleta por CDP, análise por IA
e persistência com metadados no Lakehouse.

Uso rápido (Termux / Vídeos):
  python3 promptcraft.py youtube "https://www.youtube.com/watch?v=EXEMPLO"
  python3 promptcraft.py summarize --text "Texto longo..."

Uso de APIs & Conectores:
  python3 promptcraft.py cdp "https://site-autenticado.com/dashboard"
  python3 promptcraft.py finance "caminho/extrato.ofx"
  python3 promptcraft.py gdrive
  python3 promptcraft.py defi
  python3 promptcraft.py bookmarks "caminho/favoritos.html"
  python3 promptcraft.py ingest --type arxiv --query "quantum computing"
===============================================================================
"""

import sys
import argparse
import json
from core.config import log_info, log_success, log_warning, log_error
from core.ai_engine import get_generator, direct_summarize_text
from connectors.youtube_connector import fetch_youtube_transcript
from connectors.github_connector import fetch_github_starred
from connectors.arxiv_connector import fetch_arxiv_metadata
from connectors.cdp_collector import fetch_authenticated_url
from connectors.finance_connector import parse_ofx_file, calculate_capital_flow_metrics
from connectors.gdrive_connector import load_gdrive_inventory, summarize_gdrive_distribution
from connectors.defi_cockpit_connector import fetch_defi_cockpit_telemetry
from connectors.links_vault_connector import parse_bookmarks_html
from storage.lakehouse_adapter import LakehouseAdapter
from storage.session_manager import save_session_output, backup_ontology
from analysis.direct_summarizer import process_youtube_summary_simple
from analysis.epistemological_pipeline import run_epistemological_pipeline

def cmd_youtube(args):
    """Comando rápido para transcrição e resumo direto de vídeos do YouTube."""
    generator = get_generator(args.provider, args.model, args.api_key)
    res = process_youtube_summary_simple(args.url, generator)
    
    if res.get("status") == "success":
        print("\n" + "="*80)
        print(res["summary"])
        print("="*80 + "\n")
        
        # Salva a sessão
        save_session_output(res["summary"], session_name=f"yt_{res['video_id']}")
        
        # Ingera no Lakehouse se solicitado
        if args.save_lakehouse:
            adapter = LakehouseAdapter()
            adapter.store_object(
                source=res["url"],
                source_type="video",
                raw_data={"video_id": res["video_id"], "transcript": res["raw_text"]},
                raw_text=res["raw_text"],
                domain="youtube_media",
                custom_metadata={"summary": res["summary"]}
            )
    else:
        log_error(res.get("message"))

def cmd_cdp(args):
    """Comando para coleta de dados de páginas autenticadas via Chrome CDP."""
    log_info(f"Coletando dados da URL autenticada via CDP: {args.url}")
    content = fetch_authenticated_url(args.url, cdp_port=args.port)
    print("\n" + content + "\n")
    
    if args.save_lakehouse:
        adapter = LakehouseAdapter()
        adapter.store_object(
            source=args.url,
            source_type="cdp_authenticated_web",
            raw_data={"url": args.url, "cdp_output": content},
            raw_text=content,
            domain="authenticated_web"
        )

def cmd_finance(args):
    """Comando para ingestão financeira do sovereign-budget (OFX e Métricas VRC/TCR)."""
    txs = parse_ofx_file(args.file)
    metrics = calculate_capital_flow_metrics(
        checking_balance=args.cc_balance,
        survival_monthly_cost=args.cost,
        yields_brl=args.yields,
        active_income_brl=args.income
    )
    print("\n" + "="*60)
    print("📊 MÉTRICAS DE FLUXO DE CAPITAL (SOVEREIGN-BUDGET)")
    print("="*60)
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print("="*60 + "\n")

    if args.save_lakehouse:
        adapter = LakehouseAdapter()
        adapter.store_object(
            source=args.file or "financial_manual_input",
            source_type="personal_finance",
            raw_data={"transactions_count": len(txs), "metrics": metrics},
            raw_text=json.dumps(txs[:10], ensure_ascii=False),
            domain="personal_finance"
        )

def cmd_gdrive(args):
    """Comando para indexação de arquivos no nuvem do gdrive-reorg."""
    items = load_gdrive_inventory(args.inventory)
    stats = summarize_gdrive_distribution(items)
    print("\n" + "="*60)
    print("☁️ DISTRIBUIÇÃO DO GOOGLE DRIVE (GDRIVE-REORG)")
    print("="*60)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    print("="*60 + "\n")

    if args.save_lakehouse:
        adapter = LakehouseAdapter()
        adapter.store_object(
            source=args.inventory,
            source_type="gdrive_inventory",
            raw_data=stats,
            raw_text=f"Total items: {stats['total_items']}, Total size GB: {stats['total_size_gb']}",
            domain="cloud_storage"
        )

def cmd_defi(args):
    """Comando para telemetria DeFi do dfk-pecdoa-postman-cockpit."""
    telemetry = fetch_defi_cockpit_telemetry(args.wallet)
    print("\n" + "="*60)
    print("🎮 TELEMETRIA DEFI & COCKPIT (DFK-PECDOA)")
    print("="*60)
    print(json.dumps(telemetry, indent=2, ensure_ascii=False))
    print("="*60 + "\n")

    if args.save_lakehouse:
        adapter = LakehouseAdapter()
        adapter.store_object(
            source=args.wallet,
            source_type="defi_telemetry",
            raw_data=telemetry,
            raw_text=f"JEWEL Price: ${telemetry['price_usd']}, APY: {telemetry['apy_percent']}%",
            domain="defi_crypto"
        )

def cmd_bookmarks(args):
    """Comando para extração e cofre de links do links-vault."""
    links = parse_bookmarks_html(args.file)
    print(f"\nExtraídos {len(links)} favoritos.")
    for l in links[:5]:
        print(f" • {l['title']} -> {l['url']}")
    if len(links) > 5:
        print(f" ... e mais {len(links)-5} links.")
    print("")

    if args.save_lakehouse:
        adapter = LakehouseAdapter()
        adapter.store_object(
            source=args.file,
            source_type="bookmarks_vault",
            raw_data={"total_links": len(links), "sample": links[:50]},
            raw_text="\n".join([f"{l['title']}: {l['url']}" for l in links]),
            domain="web_bookmarks"
        )

def main():
    parser = argparse.ArgumentParser(
        description="PromptCraft v2.0 — Orquestrador de APIs, CDP, Lakehouse & IA",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando a ser executado")

    # Subcomando: youtube
    yt_parser = subparsers.add_parser("youtube", help="Transcrição e resumo direto de vídeos do YouTube")
    yt_parser.add_argument("url", help="URL ou ID do vídeo do YouTube")
    yt_parser.add_argument("--provider", default="gemini", help="Provedor de IA (gemini, openai, huggingface, local)")
    yt_parser.add_argument("--model", help="Modelo específico do LLM")
    yt_parser.add_argument("--api-key", help="Chave de API do provedor")
    yt_parser.add_argument("--save-lakehouse", action="store_true", help="Salvar resultado e metadados no Lakehouse")

    # Subcomando: cdp
    cdp_parser = subparsers.add_parser("cdp", help="Coleta de dados por Chrome DevTools Protocol (Sites Autenticados)")
    cdp_parser.add_argument("url", help="URL do site autenticado")
    cdp_parser.add_argument("--port", type=int, default=9222, help="Porta de debugging remoto do Chrome")
    cdp_parser.add_argument("--save-lakehouse", action="store_true", help="Salvar no Lakehouse")

    # Subcomando: finance
    fin_parser = subparsers.add_parser("finance", help="Processamento financeiro e VRC (sovereign-budget)")
    fin_parser.add_argument("--file", default="", help="Caminho para arquivo OFX")
    fin_parser.add_argument("--cc-balance", type=float, default=2500.0, help="Saldo atual em conta corrente (BRL)")
    fin_parser.add_argument("--cost", type=float, default=4000.0, help="Custo fixo mensal de existência (BRL)")
    fin_parser.add_argument("--yields", type=float, default=300.0, help="Rendimentos mensais de DeFi/CDB (BRL)")
    fin_parser.add_argument("--income", type=float, default=8000.0, help="Renda ativa salarial (BRL)")
    fin_parser.add_argument("--save-lakehouse", action="store_true", help="Salvar no Lakehouse")

    # Subcomando: gdrive
    gdr_parser = subparsers.add_parser("gdrive", help="Indexação de inventários do GDrive (gdrive-reorg)")
    gdr_parser.add_argument("--inventory", default="/home/sukata/inventory_full.json", help="Caminho do JSON rclone")
    gdr_parser.add_argument("--save-lakehouse", action="store_true", help="Salvar no Lakehouse")

    # Subcomando: defi
    defi_parser = subparsers.add_parser("defi", help="Telemetria e cockpit DeFi (dfk-pecdoa-postman-cockpit)")
    defi_parser.add_argument("--wallet", default="0x71FD508B16d0f442f4Ae44A458259d254058A966", help="Endereço da carteira Web3")
    defi_parser.add_argument("--save-lakehouse", action="store_true", help="Salvar no Lakehouse")

    # Subcomando: bookmarks
    bm_parser = subparsers.add_parser("bookmarks", help="Cofre de links e favoritos (links-vault)")
    bm_parser.add_argument("file", help="Caminho para o HTML de favoritos")
    bm_parser.add_argument("--save-lakehouse", action="store_true", help="Salvar no Lakehouse")

    args = parser.parse_args()

    if args.command == "youtube":
        cmd_youtube(args)
    elif args.command == "cdp":
        cmd_cdp(args)
    elif args.command == "finance":
        cmd_finance(args)
    elif args.command == "gdrive":
        cmd_gdrive(args)
    elif args.command == "defi":
        cmd_defi(args)
    elif args.command == "bookmarks":
        cmd_bookmarks(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
