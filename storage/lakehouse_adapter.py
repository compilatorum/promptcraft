# -*- coding: utf-8 -*-
"""
===============================================================================
MÓDULO: storage/lakehouse_adapter.py
DESCRIÇÃO: Adaptador de Armazenamento para Compatibilidade com o Repositório Lakehouse.
           Persiste documentos e objetos coletados nas Camadas Bronze/Prata do Lakehouse
           (PostgreSQL ou SQLite fallback) garantindo metadados ricos e controle de versão.
===============================================================================
"""

import os
import json
import sqlite3
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from core.config import log_info, log_warning, log_success, VOLATILITY_SCORES

class LakehouseAdapter:
    """
    Interface de persistência compatível com a camada de Ingestão do Lakehouse.
    Grava objetos brutos com checksum SHA-256 e metadados estruturados.
    """
    def __init__(self, db_path: str = None, dsn: str = None):
        self.dsn = dsn or os.environ.get("LAKEHOUSE_POSTGRES_DSN")
        if not db_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(base_dir, "lakehouse_local.db")
        else:
            self.db_path = db_path

        # Inicializa o banco de dados SQLite local caso o PostgreSQL não esteja configurado
        if not self.dsn:
            self._init_sqlite_db()

    def _init_sqlite_db(self):
        """Cria as tabelas bronze_data e metadata no SQLite local se não existirem."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bronze_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                source_type TEXT NOT NULL,
                raw_data TEXT NOT NULL,
                raw_text TEXT,
                metadata TEXT,
                checksum TEXT UNIQUE,
                volatility_score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()

    @staticmethod
    def compute_checksum(data: Any) -> str:
        """Gera hash SHA-256 único para garantir idempotência e desduplicação."""
        if isinstance(data, dict) or isinstance(data, list):
            raw = json.dumps(data, sort_keys=True, ensure_ascii=False)
        else:
            raw = str(data)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def store_object(self, source: str, source_type: str, raw_data: Any, raw_text: str = "", domain: str = "general", custom_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Armazena um documento/objeto coletado pelo PromptCraft no Lakehouse.
        Calcula a volatilidade e anexa metadados ricos (timestamp, checksum, tags).
        """
        checksum = self.compute_checksum(raw_data)
        volatility = VOLATILITY_SCORES.get(source_type.lower(), 5)
        
        meta = {
            "ingested_by": "PromptCraft-Upgrade-Pipeline",
            "domain": domain,
            "volatility_score": volatility,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "has_raw_text": bool(raw_text)
        }
        if custom_metadata:
            meta.update(custom_metadata)

        raw_data_json = json.dumps(raw_data, ensure_ascii=False)
        metadata_json = json.dumps(meta, ensure_ascii=False)

        log_info(f"Persistindo objeto ({source_type}) no Lakehouse. Checksum: {checksum[:8]}...")

        # Tenta persitir via PostgreSQL se DSN estiver presente
        if self.dsn:
            try:
                import psycopg2
                import psycopg2.extras
                query = """
                    INSERT INTO bronze_data (source, source_type, raw_data, raw_text, metadata, checksum)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (checksum) DO UPDATE SET metadata = EXCLUDED.metadata
                    RETURNING id;
                """
                with psycopg2.connect(self.dsn) as conn:
                    with conn.cursor() as cur:
                        cur.execute(query, (source, source_type, psycopg2.extras.Json(raw_data), raw_text, psycopg2.extras.Json(meta), checksum))
                        record_id = cur.fetchone()[0]
                log_success(f"Objeto salvo com sucesso no PostgreSQL Lakehouse (ID: {record_id}).")
                return {"status": "saved", "backend": "postgresql", "id": record_id, "checksum": checksum}
            except Exception as e:
                log_warning(f"Falha na conexão PostgreSQL Lakehouse ({e}). Utilizando fallback SQLite local...")

        # Fallback para SQLite local
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO bronze_data (source, source_type, raw_data, raw_text, metadata, checksum, volatility_score)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (source, source_type, raw_data_json, raw_text, metadata_json, checksum, volatility))
        record_id = cur.lastrowid
        conn.commit()
        conn.close()

        log_success(f"Objeto gravado no SQLite Lakehouse local (ID: {record_id}, arquivo: {os.path.basename(self.db_path)}).")
        return {"status": "saved", "backend": "sqlite", "id": record_id, "checksum": checksum}
