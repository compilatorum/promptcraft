#!/usr/bin/env python3
import os
import re
import sys
import json
import sqlite3
import hashlib
import urllib.request
from datetime import datetime

# Add promptcraft to path
sys.path.append("/home/sukata/promptcraft")
import promptcraft

ONTOLOGIA_DIR = "/home/sukata/promptcraft/ontologia"
TAGS_PATH = os.path.join(ONTOLOGIA_DIR, "tags_dicionario.json")
IMPORTADAS_PATH = os.path.join(ONTOLOGIA_DIR, "fontes_importadas.md")
BOOKMARKS_PATH = os.path.join(ONTOLOGIA_DIR, "bookmarks_importados.md")
DB_PATH = os.path.join(ONTOLOGIA_DIR, "fontes_processadas.db")

def init_db():
    """Initializes the SQLite database with the unified schema, merging org-roam v2 and IPMO modules."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Drop legacy table if it exists
    cursor.execute("DROP TABLE IF EXISTS fontes;")
    
    # 1. ORG-ROAM V2 COMPLIANT TABLES (with merged unified fields where applicable)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        file TEXT UNIQUE PRIMARY KEY,          -- Matches 'path' in unified
        title TEXT,
        hash TEXT NOT NULL,                    -- Matches 'content_hash'
        atime INTEGER NOT NULL,
        mtime INTEGER NOT NULL,
        filename TEXT,
        extension TEXT,
        language TEXT,
        size_bytes INTEGER,
        line_count INTEGER,
        git_status TEXT,
        last_commit_hash TEXT,
        is_ignored BOOLEAN DEFAULT 0,
        is_binary BOOLEAN DEFAULT 0
    );
    """)
    
    # Dynamic migration to add missing columns to existing 'files' table if it was created in a legacy schema version
    cursor.execute("PRAGMA table_info(files);")
    existing_files_cols = {row[1] for row in cursor.fetchall()}
    expected_files_cols = {
        "filename": "TEXT",
        "extension": "TEXT",
        "language": "TEXT",
        "size_bytes": "INTEGER",
        "line_count": "INTEGER",
        "git_status": "TEXT",
        "last_commit_hash": "TEXT",
        "is_ignored": "BOOLEAN DEFAULT 0",
        "is_binary": "BOOLEAN DEFAULT 0"
    }
    for col_name, col_type in expected_files_cols.items():
        if col_name not in existing_files_cols:
            cursor.execute(f"ALTER TABLE files ADD COLUMN {col_name} {col_type};")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nodes (
        id TEXT NOT NULL PRIMARY KEY,
        file TEXT NOT NULL,
        level INTEGER NOT NULL,
        pos INTEGER NOT NULL,
        todo TEXT,
        priority TEXT,
        scheduled TEXT,
        deadline TEXT,
        title TEXT,
        properties TEXT,
        olp TEXT,
        FOREIGN KEY (file) REFERENCES files (file) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS aliases (
        node_id TEXT NOT NULL,
        alias TEXT,
        PRIMARY KEY (node_id, alias),
        FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS citations (
        node_id TEXT NOT NULL,
        cite_key TEXT NOT NULL,
        pos INTEGER NOT NULL,
        properties TEXT,
        PRIMARY KEY (node_id, cite_key, pos),
        FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS refs (
        node_id TEXT NOT NULL,
        ref TEXT NOT NULL,
        type TEXT NOT NULL,
        PRIMARY KEY (node_id, ref, type),
        FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tags (
        node_id TEXT NOT NULL,
        tag TEXT,
        PRIMARY KEY (node_id, tag),
        FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS links (
        pos INTEGER NOT NULL,
        source TEXT NOT NULL,
        dest TEXT NOT NULL,
        type TEXT NOT NULL,
        properties TEXT NOT NULL,
        PRIMARY KEY (pos, source, dest, type),
        FOREIGN KEY (source) REFERENCES nodes (id) ON DELETE CASCADE
    );
    """)

    # 2. CORE MODULE TABLES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        title TEXT,
        agent_id TEXT,
        habitat TEXT CHECK(habitat IN ('edge', 'core', 'archive')),
        status TEXT DEFAULT 'active' CHECK(status IN ('active', 'paused', 'completed', 'aborted')),
        drift_score REAL DEFAULT 0.0,
        reliability_score REAL DEFAULT 1.0,
        step_current INTEGER DEFAULT 0,
        step_total INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME,
        initial_intent TEXT,
        final_outcome TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system', 'tool')),
        content TEXT NOT NULL,
        token_count INTEGER,
        model TEXT,
        temperature REAL,
        facts_used TEXT,
        assumptions TEXT,
        open_questions TEXT,
        confidence REAL,
        drift_delta REAL DEFAULT 0.0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        system_prompt TEXT,
        model TEXT DEFAULT 'claude-sonnet-4',
        temperature REAL DEFAULT 0.7,
        max_tokens INTEGER DEFAULT 4096,
        tools_enabled TEXT,
        hypostases TEXT,
        is_active BOOLEAN DEFAULT 1,
        last_used_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tools (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        mcp_server TEXT,
        tool_schema TEXT,
        is_enabled BOOLEAN DEFAULT 1,
        call_count INTEGER DEFAULT 0,
        avg_latency_ms REAL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        payload TEXT,
        session_id TEXT,
        agent_id TEXT,
        tool_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions(id),
        FOREIGN KEY (agent_id) REFERENCES agents(id),
        FOREIGN KEY (tool_id) REFERENCES tools(id)
    );
    """)

    # 3. MEMORY MODULE TABLES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory_items (
        id TEXT PRIMARY KEY,
        item_type TEXT NOT NULL CHECK(item_type IN (
            'projectBrief', 'activeContext', 'progressLog', 
            'ontology', 'systemPatterns', 'decisionLog'
        )),
        title TEXT,
        content TEXT NOT NULL,
        privacy_layer INTEGER DEFAULT 0 CHECK(privacy_layer BETWEEN 0 AND 4),
        is_pinned BOOLEAN DEFAULT 0,
        version INTEGER DEFAULT 1,
        previous_version_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (previous_version_id) REFERENCES memory_items(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_patches (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        principle TEXT,
        cases TEXT,
        anti_patterns TEXT,
        source_session_id TEXT,
        source_message_id TEXT,
        is_compressed BOOLEAN DEFAULT 0,
        compressed_from TEXT,
        tags TEXT,
        usage_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_session_id) REFERENCES sessions(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS adrs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number INTEGER NOT NULL UNIQUE,
        title TEXT NOT NULL,
        status TEXT DEFAULT 'proposed' CHECK(status IN ('proposed', 'accepted', 'deprecated', 'superseded')),
        context TEXT,
        decision TEXT,
        consequences TEXT,
        hypostasis TEXT CHECK(hypostasis IN ('project', 'product', 'program', 'policy', 'plan', 'process')),
        tags TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        accepted_at DATETIME
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS context_snapshots (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        state_tracker TEXT NOT NULL,
        verified_facts TEXT,
        assumptions TEXT,
        open_questions TEXT,
        step_number INTEGER,
        drift_score REAL,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
    );
    """)

    # 4. TASKS MODULE TABLES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        hypostasis TEXT NOT NULL CHECK(hypostasis IN (
            'project', 'product', 'program', 'policy', 'plan', 'process'
        )),
        node_type TEXT CHECK(node_type IN (
            'habitat_provision', 'protocol_bridge', 'knowledge_distillation',
            'capability_routing', 'self_modeling'
        )),
        status TEXT DEFAULT 'todo' CHECK(status IN (
            'todo', 'in_progress', 'blocked', 'done', 'cancelled'
        )),
        priority INTEGER DEFAULT 3 CHECK(priority BETWEEN 1 AND 5),
        dag_id TEXT,
        parent_task_id TEXT,
        order_index INTEGER DEFAULT 0,
        assigned_to TEXT,
        estimated_hours REAL,
        actual_hours REAL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        started_at DATETIME,
        completed_at DATETIME,
        due_date DATETIME,
        FOREIGN KEY (dag_id) REFERENCES dags(id),
        FOREIGN KEY (parent_task_id) REFERENCES tasks(id),
        FOREIGN KEY (assigned_to) REFERENCES agents(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dags (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        definition TEXT,
        nodes_count INTEGER DEFAULT 0,
        edges_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'draft' CHECK(status IN (
            'draft', 'active', 'completed', 'failed', 'cancelled'
        )),
        execution_order TEXT,
        created_by TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        started_at DATETIME,
        completed_at DATETIME,
        FOREIGN KEY (created_by) REFERENCES agents(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS task_dependencies (
        id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        depends_on_task_id TEXT NOT NULL,
        dependency_type TEXT DEFAULT 'finish_to_start' CHECK(dependency_type IN (
            'finish_to_start', 'start_to_start', 'finish_to_finish', 'start_to_finish'
        )),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
        FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id) ON DELETE CASCADE,
        UNIQUE(task_id, depends_on_task_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workflows (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        workflow_type TEXT CHECK(workflow_type IN (
            'knowledge_distillation', 'protocol_bridge', 'habitat_provision',
            'capability_routing', 'self_modeling'
        )),
        steps TEXT NOT NULL,
        status TEXT DEFAULT 'pending' CHECK(status IN (
            'pending', 'running', 'completed', 'failed', 'cancelled'
        )),
        current_step INTEGER DEFAULT 0,
        triggered_by TEXT,
        result TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        started_at DATETIME,
        completed_at DATETIME
    );
    """)

    # 5. KNOWLEDGE MODULE ADDITIONAL TABLES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        title TEXT,
        content TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        source_type TEXT CHECK(source_type IN (
            'file', 'url', 'chatlog', 'code', 'manual'
        )),
        source_path TEXT,
        file_format TEXT,
        chunk_count INTEGER DEFAULT 0,
        is_processed BOOLEAN DEFAULT 0,
        tags TEXT,
        metadata TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(content_hash)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_chunks (
        id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL,
        content TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        start_char INTEGER,
        end_char INTEGER,
        token_count INTEGER,
        embedding BLOB,
        embedding_model TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        UNIQUE(document_id, chunk_index)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS symbols (
        id TEXT PRIMARY KEY,
        file_id TEXT NOT NULL,
        name TEXT NOT NULL,
        symbol_type TEXT NOT NULL CHECK(symbol_type IN (
            'function', 'class', 'method', 'variable', 'constant',
            'interface', 'type', 'enum', 'module'
        )),
        line_start INTEGER,
        line_end INTEGER,
        column_start INTEGER,
        column_end INTEGER,
        signature TEXT,
        documentation TEXT,
        is_exported BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (file_id) REFERENCES files(file) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS graph_links (
        id TEXT PRIMARY KEY,
        source_type TEXT NOT NULL,
        source_id TEXT NOT NULL,
        target_type TEXT NOT NULL,
        target_id TEXT NOT NULL,
        link_type TEXT NOT NULL CHECK(link_type IN (
            'references', 'depends_on', 'implements', 'extends',
            'uses', 'related_to', 'backlink'
        )),
        context TEXT,
        confidence REAL DEFAULT 1.0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(source_type, source_id, target_type, target_id, link_type)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tags_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        color TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entity_tags (
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (entity_type, entity_id, tag_id),
        FOREIGN KEY (tag_id) REFERENCES tags_config(id) ON DELETE CASCADE
    );
    """)

    # 6. CODE MODULE ADDITIONAL TABLES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS code_chunks (
        id TEXT PRIMARY KEY,
        file_id TEXT NOT NULL,
        content TEXT NOT NULL,
        start_line INTEGER NOT NULL,
        end_line INTEGER NOT NULL,
        chunk_type TEXT CHECK(chunk_type IN (
            'function', 'class', 'method', 'block', 'file'
        )),
        token_count INTEGER,
        embedding BLOB,
        embedding_model TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (file_id) REFERENCES files(file) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS git_commits (
        hash TEXT PRIMARY KEY,
        parent_hash TEXT,
        message TEXT NOT NULL,
        author_name TEXT,
        author_email TEXT,
        hypostasis TEXT CHECK(hypostasis IN (
            'project', 'product', 'program', 'policy', 'plan', 'process'
        )),
        committed_at DATETIME NOT NULL,
        scanned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        files_changed INTEGER DEFAULT 0,
        insertions INTEGER DEFAULT 0,
        deletions INTEGER DEFAULT 0,
        FOREIGN KEY (parent_hash) REFERENCES git_commits(hash)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS git_branches (
        name TEXT PRIMARY KEY,
        commit_hash TEXT NOT NULL,
        is_current BOOLEAN DEFAULT 0,
        is_remote BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (commit_hash) REFERENCES git_commits(hash)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS git_diffs (
        id TEXT PRIMARY KEY,
        commit_hash TEXT NOT NULL,
        file_path TEXT NOT NULL,
        diff_content TEXT NOT NULL,
        change_type TEXT CHECK(change_type IN ('added', 'modified', 'deleted', 'renamed')),
        lines_added INTEGER DEFAULT 0,
        lines_deleted INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (commit_hash) REFERENCES git_commits(hash) ON DELETE CASCADE
    );
    """)

    # 7. METRICS MODULE TABLES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metrics (
        id TEXT PRIMARY KEY,
        metric_name TEXT NOT NULL,
        value REAL NOT NULL,
        unit TEXT,
        session_id TEXT,
        agent_id TEXT,
        tool_id TEXT,
        tags TEXT,
        metadata TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions(id),
        FOREIGN KEY (agent_id) REFERENCES agents(id),
        FOREIGN KEY (tool_id) REFERENCES tools(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS drift_scores (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        drift_score REAL NOT NULL CHECK(drift_score BETWEEN 0.0 AND 1.0),
        step_number INTEGER,
        verified_facts_count INTEGER,
        assumptions_count INTEGER,
        open_questions_count INTEGER,
        trigger_code TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reliability_scores (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        reliability_score REAL NOT NULL CHECK(reliability_score BETWEEN 0.0 AND 1.0),
        completeness REAL,
        verification REAL,
        consistency REAL,
        step_number INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id TEXT PRIMARY KEY,
        alert_type TEXT NOT NULL CHECK(alert_type IN (
            'drift_warning', 'drift_critical', 'reliability_low',
            'tool_failure', 'schema_violation', 'constraint_breach'
        )),
        severity INTEGER NOT NULL CHECK(severity BETWEEN 1 AND 4),
        title TEXT NOT NULL,
        message TEXT,
        session_id TEXT,
        agent_id TEXT,
        metric_value REAL,
        threshold REAL,
        status TEXT DEFAULT 'active' CHECK(status IN ('active', 'acknowledged', 'resolved')),
        acknowledged_at DATETIME,
        resolved_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions(id),
        FOREIGN KEY (agent_id) REFERENCES agents(id)
    );
    """)

    # 8. CONFIG MODULE TABLES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        category TEXT,
        description TEXT,
        is_secret BOOLEAN DEFAULT 0,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prompt_templates (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        template TEXT NOT NULL,
        description TEXT,
        category TEXT,
        variables TEXT,
        usage_count INTEGER DEFAULT 0,
        avg_rating REAL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_configs (
        id TEXT PRIMARY KEY,
        agent_id TEXT NOT NULL,
        config_key TEXT NOT NULL,
        config_value TEXT NOT NULL,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
        UNIQUE(agent_id, config_key)
    );
    """)

    # 9. VIEWS
    cursor.execute("DROP VIEW IF EXISTS v_session_summary;")
    cursor.execute("""
    CREATE VIEW v_session_summary AS
    SELECT 
        s.id, s.title, s.status, s.habitat, s.drift_score, s.reliability_score, s.step_current, s.step_total,
        a.name AS agent_name, COUNT(m.id) AS message_count,
        SUM(CASE WHEN m.role = 'user' THEN 1 ELSE 0 END) AS user_messages,
        SUM(CASE WHEN m.role = 'assistant' THEN 1 ELSE 0 END) AS assistant_messages,
        AVG(m.confidence) AS avg_confidence, s.created_at, s.updated_at
    FROM sessions s
    LEFT JOIN agents a ON s.agent_id = a.id
    LEFT JOIN messages m ON s.id = m.session_id
    GROUP BY s.id;
    """)

    cursor.execute("DROP VIEW IF EXISTS v_task_progress;")
    cursor.execute("""
    CREATE VIEW v_task_progress AS
    SELECT 
        t.id, t.title, t.hypostasis, t.node_type, t.status, t.priority,
        d.name AS dag_name, COUNT(td.depends_on_task_id) AS dependency_count,
        CASE 
            WHEN t.status = 'done' THEN 100
            WHEN t.status = 'in_progress' THEN 50
            WHEN t.status = 'blocked' THEN 25
            ELSE 0
        END AS progress_percent, t.created_at, t.due_date
    FROM tasks t
    LEFT JOIN dags d ON t.dag_id = d.id
    LEFT JOIN task_dependencies td ON t.id = td.task_id
    GROUP BY t.id;
    """)

    cursor.execute("DROP VIEW IF EXISTS v_active_alerts;")
    cursor.execute("""
    CREATE VIEW v_active_alerts AS
    SELECT 
        al.id, al.alert_type, al.severity, al.title, al.message, al.metric_value, al.threshold,
        s.title AS session_title, ag.name AS agent_name, al.created_at,
        CASE al.severity
            WHEN 1 THEN '🚨 CRÍTICO'
            WHEN 2 THEN '⚠️ ALTO'
            WHEN 3 THEN '📌 MÉDIO'
            WHEN 4 THEN 'ℹ️ INFO'
        END AS severity_label
    FROM alerts al
    LEFT JOIN sessions s ON al.session_id = s.id
    LEFT JOIN agents ag ON al.agent_id = ag.id
    WHERE al.status = 'active';
    """)

    cursor.execute("DROP VIEW IF EXISTS v_knowledge_graph;")
    cursor.execute("""
    CREATE VIEW v_knowledge_graph AS
    SELECT 
        gl.id AS link_id, gl.source_type, gl.source_id, gl.target_type, gl.target_id, gl.link_type, gl.confidence,
        CASE gl.source_type
            WHEN 'document' THEN (SELECT title FROM documents WHERE id = gl.source_id)
            WHEN 'task' THEN (SELECT title FROM tasks WHERE id = gl.source_id)
            WHEN 'adr' THEN (SELECT title FROM adrs WHERE id = gl.source_id)
            ELSE 'Unknown'
        END AS source_title,
        CASE gl.target_type
            WHEN 'document' THEN (SELECT title FROM documents WHERE id = gl.target_id)
            WHEN 'task' THEN (SELECT title FROM tasks WHERE id = gl.target_id)
            WHEN 'adr' THEN (SELECT title FROM adrs WHERE id = gl.target_id)
            ELSE 'Unknown'
        END AS target_title
    FROM graph_links gl;
    """)

    cursor.execute("DROP VIEW IF EXISTS v_file_statistics;")
    cursor.execute("""
    CREATE VIEW v_file_statistics AS
    SELECT 
        f.language,
        COUNT(*) AS file_count,
        SUM(f.size_bytes) AS total_bytes,
        SUM(f.line_count) AS total_lines
    FROM files f
    GROUP BY f.language;
    """)

    # 10. INDEXES
    # Sessions
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_agent ON sessions(agent_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at DESC);")
    
    # Messages
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);")
    
    # Agents
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_agents_active ON agents(is_active);")
    
    # Events
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at DESC);")
    
    # Memory Items
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_items(item_type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_pinned ON memory_items(is_pinned);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_privacy ON memory_items(privacy_layer);")
    
    # Knowledge Patches
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_patches_compressed ON knowledge_patches(is_compressed);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_patches_tags ON knowledge_patches(tags);")
    
    # ADRs
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_adrs_status ON adrs(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_adrs_hypostasis ON adrs(hypostasis);")
    
    # Context Snapshots
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_session ON context_snapshots(session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_created ON context_snapshots(created_at DESC);")
    
    # Tasks
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_hypostasis ON tasks(hypostasis);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_dag ON tasks(dag_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);")
    
    # DAGs
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dags_status ON dags(status);")
    
    # Task Dependencies
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deps_task ON task_dependencies(task_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deps_depends ON task_dependencies(depends_on_task_id);")
    
    # Workflows
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflows_type ON workflows(workflow_type);")
    
    # Documents
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_docs_source ON documents(source_type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_docs_processed ON documents(is_processed);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_docs_hash ON documents(content_hash);")
    
    # Document Chunks
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_index ON document_chunks(chunk_index);")
    
    # Symbols
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(symbol_type);")
    
    # Graph Links (IPMO's links table)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_graph_links_source ON graph_links(source_type, source_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_graph_links_target ON graph_links(target_type, target_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_graph_links_type ON graph_links(link_type);")
    
    # Entity Tags
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_tags_tag ON entity_tags(tag_id);")
    
    # Files
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_path ON files(file);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_extension ON files(extension);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_language ON files(language);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_git ON files(git_status);")
    
    # Code Chunks
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_code_chunks_file ON code_chunks(file_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_code_chunks_type ON code_chunks(chunk_type);")
    
    # Git Commits
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commits_parent ON git_commits(parent_hash);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commits_date ON git_commits(committed_at DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commits_hypostasis ON git_commits(hypostasis);")
    
    # Git Branches
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_branches_current ON git_branches(is_current);")
    
    # Git Diffs
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_diffs_commit ON git_diffs(commit_hash);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_diffs_file ON git_diffs(file_path);")
    
    # Metrics
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_session ON metrics(session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_created ON metrics(created_at DESC);")
    
    # Drift Scores
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_drift_session ON drift_scores(session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_drift_score ON drift_scores(drift_score);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_drift_created ON drift_scores(created_at DESC);")
    
    # Reliability Scores
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reliability_session ON reliability_scores(session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reliability_score ON reliability_scores(reliability_score);")
    
    # Alerts
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at DESC);")
    
    # Settings
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_settings_category ON settings(category);")
    
    # Prompt Templates
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prompts_category ON prompt_templates(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prompts_usage ON prompt_templates(usage_count DESC);")
    
    # Agent Configs
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_configs_agent ON agent_configs(agent_id);")

    # 11. TRIGGERS
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS update_sessions_timestamp AFTER UPDATE ON sessions
    BEGIN
        UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS update_messages_timestamp AFTER UPDATE ON messages
    BEGIN
        UPDATE messages SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS update_tasks_timestamp AFTER UPDATE ON tasks
    BEGIN
        UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS update_session_steps AFTER INSERT ON messages
    WHEN NEW.role = 'assistant'
    BEGIN
        UPDATE sessions 
        SET step_current = step_current + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.session_id;
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS log_drift_change AFTER UPDATE ON sessions
    WHEN NEW.drift_score != OLD.drift_score
    BEGIN
        INSERT INTO events (id, event_type, payload, session_id, created_at)
        VALUES (
            lower(hex(randomblob(16))),
            'drift_score_changed',
            json_object(
                'old_value', OLD.drift_score,
                'new_value', NEW.drift_score,
                'delta', NEW.drift_score - OLD.drift_score
            ),
            NEW.id,
            CURRENT_TIMESTAMP
        );
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS alert_on_high_drift AFTER UPDATE ON sessions
    WHEN NEW.drift_score > 0.35 AND OLD.drift_score <= 0.35
    BEGIN
        INSERT INTO alerts (id, alert_type, severity, title, message, session_id, metric_value, threshold, created_at)
        VALUES (
            lower(hex(randomblob(16))),
            CASE WHEN NEW.drift_score > 0.6 THEN 'drift_critical' ELSE 'drift_warning' END,
            CASE WHEN NEW.drift_score > 0.6 THEN 1 ELSE 2 END,
            'Drift Score Alto Detectado',
            'Drift score atingiu ' || NEW.drift_score || '. Considerar ativação de damping.',
            NEW.id,
            NEW.drift_score,
            0.35,
            CURRENT_TIMESTAMP
        );
    END;
    """)

    conn.commit()
    conn.close()
    print(f"✅ Banco de dados SQLite inicializado com a estrutura do org-roam v2 e IPMO em: {DB_PATH}")

def load_tags():
    with open(TAGS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_all_imported_sources():
    """Parses markdown files and matches each link to its source type."""
    sources = []
    
    # 1. Parse fontes_importadas.md
    if os.path.exists(IMPORTADAS_PATH):
        with open(IMPORTADAS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            current_type = "unknown"
            for line in f:
                line = line.strip()
                if line.startswith("## Importação de"):
                    match_type = re.search(r'## Importação de (\w+)', line)
                    if match_type:
                        current_type = match_type.group(1).lower()
                
                # Match links
                match_link = re.search(r'-\s*(?:\*\*[^*]+\*\*:\s*)?\[([^\]]+)\]\(([^)]+)\)', line)
                if match_link:
                    title, url = match_link.group(1), match_link.group(2)
                    sources.append({
                        "title": title,
                        "url": url,
                        "source_type": current_type
                    })
                    
    # 2. Parse bookmarks_importados.md
    if os.path.exists(BOOKMARKS_PATH):
        with open(BOOKMARKS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                match_link = re.search(r'-\s*\[([^\]]+)\]\(([^)]+)\)', line)
                if match_link:
                    title, url = match_link.group(1), match_link.group(2)
                    sources.append({
                        "title": title,
                        "url": url,
                        "source_type": "bookmarks"
                    })
                    
    return sources

def classify_source(title, url, tags_dict):
    """Classifies a source into one of the 6 major categories based on keywords."""
    text_to_search = (title + " " + url).lower()
    
    keywords = {
        "IA_PESQUISA": ["prompt", "llm", "ai", "model", "gpt", "claude", "gemini", "huggingface", "unsloth", "sft", "lora", "fine-tune", "rag", "artificial", "deep learning", "neural"],
        "DESENVOLVIMENTO": ["github", "git", "code", "repo", "api", "emacs", "elisp", "python", "rust", "cdp", "mcp", "devtools", "docker", "termux", "linux", "programming", "software", "cli", "tui"],
        "REGENERACAO_REFI": ["dao", "proposal", "vote", "snapshot", "uniswap", "refi", "token", "blockchain", "governance", "finance", "impact", "regenerative", "crypto", "onchain", "ethereum", "ens"],
        "CONHECIMENTO_PKM": ["roam", "org", "elfeed", "wiki", "denote", "knowledge", "graph", "pkm", "notes", "obsidian", "logseq", "personal", "mind", "zettelkasten", "index", "taxonomy"],
        "MIDIA_ACADEMICO": ["youtube", "watch", "channel", "arxiv", "paper", "scholar", "scientific", "abstract", "research", "physics", "quantum", "mathematics", "theory", "history"],
        "CHATLOGS_HISTORICO": ["chatlog", "session", "dialogue", "conversation", "sanitized", "chunk", "promptcraft", "assistant", "user", "history", "cache"]
    }
    
    for category, kw_list in keywords.items():
        for kw in kw_list:
            if kw in text_to_search:
                return category
                
    return "CONHECIMENTO_PKM" # Default fallback

def classify_domain(url, domains_dict):
    """Classifies a URL into a domain group based on patterns in domains_dict."""
    url_lower = url.lower()
    for domain_group, patterns in domains_dict.items():
        for pattern in patterns:
            if pattern in url_lower:
                return f"domain_{domain_group.lower()}"
    return None

def process_batch():
    init_db()
    tags_dict = load_tags()
    sources = parse_all_imported_sources()
    print(f"🔍 Encontradas {len(sources)} fontes totais para compilação.")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Bulk populate all sources in the SQLite database (avoiding data loss)
    print("🚀 Povoando tabelas do org-roam v2 com todas as fontes...")
    insert_count = 0
    now_ts = int(datetime.now().timestamp())
    
    for idx, src in enumerate(sources):
        url_hash = hashlib.sha256(src["url"].encode('utf-8')).hexdigest()[:16]
        category = classify_source(src["title"], src["url"], tags_dict)
        
        # Virtual Denote/Org path
        virtual_file = f"shared-knowledge/{src['source_type']}/{url_hash}__{src['source_type']}.org"
        
        # Determine status and extract distilled content if the file is local
        status = "pending"
        distilled_content = ""
        actual_file = virtual_file
        
        if src["url"].startswith("file:///"):
            local_path = src["url"].replace("file://", "")
            if os.path.exists(local_path):
                actual_file = local_path
                distilled_content = promptcraft.extract_file_content(local_path)
                status = "processed"
        
        # Insert into 'files'
        cursor.execute("""
        INSERT OR IGNORE INTO files (file, title, hash, atime, mtime)
        VALUES (?, ?, ?, ?, ?);
        """, (actual_file, src["title"], url_hash, now_ts, now_ts))
        
        # Insert into 'nodes' (storing status & url in properties JSON)
        properties_json = json.dumps({
            "url": src["url"],
            "source_type": src["source_type"],
            "status": status,
            "distilled_content": distilled_content
        })
        cursor.execute("""
        INSERT OR REPLACE INTO nodes (id, file, level, pos, title, properties)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (url_hash, actual_file, 0, 1, src["title"], properties_json))
        
        # Insert into 'refs'
        cursor.execute("""
        INSERT OR IGNORE INTO refs (node_id, ref, type)
        VALUES (?, ?, ?);
        """, (url_hash, src["url"], "url"))
        
        # Insert into 'tags'
        cursor.execute("""
        INSERT OR IGNORE INTO tags (node_id, tag)
        VALUES (?, ?);
        """, (url_hash, category.lower()))
        
        # Classify and insert domain tag
        domain_tag = classify_domain(src["url"], tags_dict.get("domains", {}))
        if domain_tag:
            cursor.execute("""
            INSERT OR IGNORE INTO tags (node_id, tag)
            VALUES (?, ?);
            """, (url_hash, domain_tag))
        
        insert_count += 1
            
        if idx > 0 and idx % 5000 == 0:
            conn.commit()
            print(f"   -> {idx}/{len(sources)} fontes processadas...")
            
    # Add chatlogs import from /home/sukata/chatlogs/sanitized
    chatlogs_dir = "/home/sukata/chatlogs/sanitized"
    if os.path.exists(chatlogs_dir):
        print("💬 Importando e indexando chatlogs sanitizados...")
        chatlog_count = 0
        for filename in os.listdir(chatlogs_dir):
            if not filename.endswith(".md"):
                continue
            local_filepath = os.path.join(chatlogs_dir, filename)
            url_hash = hashlib.sha256(f"file://{local_filepath}".encode('utf-8')).hexdigest()[:16]
            title = filename
            
            distilled_content = promptcraft.extract_file_content(local_filepath)
            
            properties_json = json.dumps({
                "url": f"file://{local_filepath}",
                "source_type": "chatlogs",
                "status": "processed",
                "distilled_content": distilled_content
            })
            
            # Insert into 'files'
            cursor.execute("""
            INSERT OR IGNORE INTO files (file, title, hash, atime, mtime)
            VALUES (?, ?, ?, ?, ?);
            """, (local_filepath, title, url_hash, now_ts, now_ts))
            
            # Insert into 'nodes'
            cursor.execute("""
            INSERT OR REPLACE INTO nodes (id, file, level, pos, title, properties)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (url_hash, local_filepath, 0, 1, title, properties_json))
            
            # Insert into 'refs'
            cursor.execute("""
            INSERT OR IGNORE INTO refs (node_id, ref, type)
            VALUES (?, ?, ?);
            """, (url_hash, f"file://{local_filepath}", "url"))
            
            # Insert into 'tags'
            cursor.execute("""
            INSERT OR IGNORE INTO tags (node_id, tag)
            VALUES (?, ?);
            """, (url_hash, "chatlogs_historico"))
            
            chatlog_count += 1
            insert_count += 1
        print(f"✅ {chatlog_count} chatlogs indexados com sucesso no SQLite.")
            
    conn.commit()
    print(f"✅ Povoamento concluído. {insert_count} fontes mapeadas nas tabelas org-roam.")
    
    # 2. Select a representative sample from each source type to perform a REAL fetch and distillation
    samples = [
        {"source_type": "youtube", "url": "https://www.youtube.com/watch?v=S6xzKM5UuOM", "title": "Vídeo Metacognitivo de Teste"},
        {"source_type": "github", "url": "https://github.com/compilatorum/promptcraft", "title": "Repositório Promptcraft"},
        {"source_type": "snapshot", "url": "https://snapshot.org/#/ens.eth/proposal/0x9ed89cf79760eb92d220fee2da08896bf027317f394aab87863011f964e19453", "title": "[6.45][Social] Renewal of the Security Council"},
        {"source_type": "arxiv", "url": "http://arxiv.org/abs/2304.12345v3", "title": "Non-isometric codes for the black hole interior"},
        {"source_type": "bookmarks", "url": "https://example.com", "title": "Exemplo de Bookmark Web"}
    ]
    
    print("\n⚡ Processando amostras em tempo real de cada tipo de fonte...")
    for idx, s in enumerate(samples):
        url_hash = hashlib.sha256(s["url"].encode('utf-8')).hexdigest()[:16]
        category = classify_source(s["title"], s["url"], tags_dict)
        print(f"-> [{s['source_type'].upper()}] Acessando: {s['url']} ...")
        
        distilled_content = ""
        status = "failed"
        err_msg = ""
        
        try:
            if s["source_type"] == "youtube":
                distilled_content = promptcraft.fetch_url_text(s["url"])
                status = "processed"
            elif s["source_type"] == "github":
                req = urllib.request.Request(
                    "https://api.github.com/repos/compilatorum/promptcraft",
                    headers={"User-Agent": "Mozilla/5.0 promptcraft-cli"}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    repo_data = json.loads(response.read().decode('utf-8'))
                    distilled_content = f"GitHub Starred Repo: {repo_data.get('full_name')}\nDescription: {repo_data.get('description')}\nStars: {repo_data.get('stargazers_count')}\nLanguage: {repo_data.get('language')}"
                status = "processed"
            elif s["source_type"] == "snapshot":
                query = """
                query {
                  proposal(id: "0x9ed89cf79760eb92d220fee2da08896bf027317f394aab87863011f964e19453") {
                    title
                    body
                    state
                    space {
                      id
                      name
                    }
                  }
                }
                """
                payload = json.dumps({"query": query})
                req = urllib.request.Request(
                    "https://hub.snapshot.org/graphql",
                    data=payload.encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    prop = res_data.get("data", {}).get("proposal", {})
                    distilled_content = f"DAO Proposal: {prop.get('title')}\nSpace: {prop.get('space', {}).get('name')}\nState: {prop.get('state')}\nBody: {prop.get('body')[:500]}..."
                status = "processed"
            elif s["source_type"] == "arxiv":
                recs = promptcraft.fetch_semantic_scholar_recommendations("2304.12345")
                if recs:
                    distilled_content = f"arXiv Paper Recommendations:\n" + "\n".join([f"- {r['title']} ({r['url']})" for r in recs])
                else:
                    distilled_content = "Nenhuma recomendação adjacente encontrada."
                status = "processed"
            elif s["source_type"] == "bookmarks":
                distilled_content = promptcraft.fetch_url_text(s["url"])
                status = "processed"
                
        except Exception as e:
            err_msg = str(e)
            print(f"   ⚠️ Falha ao processar {s['source_type']}: {err_msg}")
            
        virtual_file = f"shared-knowledge/{s['source_type']}/{url_hash}__{s['source_type']}.org"
        
        # Insert/Update in 'files'
        cursor.execute("""
        INSERT INTO files (file, title, hash, atime, mtime)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(file) DO UPDATE SET
            title = excluded.title,
            mtime = excluded.mtime;
        """, (virtual_file, s["title"], url_hash, now_ts, now_ts))
        
        # Insert/Update in 'nodes' (storing status, error & content in properties JSON)
        properties_json = json.dumps({
            "url": s["url"],
            "source_type": s["source_type"],
            "status": status,
            "error_message": err_msg,
            "distilled_content": distilled_content
        })
        cursor.execute("""
        INSERT INTO nodes (id, file, level, pos, title, properties)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            properties = excluded.properties;
        """, (url_hash, virtual_file, 0, 1, s["title"], properties_json))
        
        # Insert/Update in 'refs'
        cursor.execute("""
        INSERT OR IGNORE INTO refs (node_id, ref, type)
        VALUES (?, ?, ?);
        """, (url_hash, s["url"], "url"))
        
        # Insert/Update in 'tags'
        cursor.execute("""
        INSERT OR IGNORE INTO tags (node_id, tag)
        VALUES (?, ?);
        """, (url_hash, category.lower()))
        
        domain_tag = classify_domain(s["url"], tags_dict.get("domains", {}))
        if domain_tag:
            cursor.execute("""
            INSERT OR IGNORE INTO tags (node_id, tag)
            VALUES (?, ?);
            """, (url_hash, domain_tag))
        
    conn.commit()
    conn.close()
    print("\n✅ Processamento e destilação de amostras concluídos!")
    
    # 3. Analyze results
    analyze_database_results()

def analyze_database_results():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT count(*) FROM files")
    total_files = cursor.fetchone()[0]
    
    cursor.execute("SELECT count(*) FROM nodes")
    total_nodes = cursor.fetchone()[0]
    
    # Parse properties in Python to count status since SQLite doesn't natively parse JSON in older systems
    cursor.execute("SELECT properties FROM nodes")
    rows = cursor.fetchall()
    
    processed = 0
    pending = 0
    failed = 0
    for r in rows:
        props = json.loads(r[0]) if r[0] else {}
        status = props.get("status")
        if status == "processed":
            processed += 1
        elif status == "failed":
            failed += 1
        else:
            pending += 1
            
    print("\n==================================================")
    print("🔬 ANÁLISE DE QUALIDADE E COBERTURA DO BANCO PKM (org-roam v2)")
    print("==================================================")
    print(f"Total de Arquivos Virtuais (files): {total_files}")
    print(f"Total de Nós de Conhecimento (nodes): {total_nodes}")
    print(f"Nós Processados com Sucesso: {processed}")
    print(f"Nós Pendentes na Fila: {pending}")
    print(f"Nós com Falhas de Acesso: {failed}")
    print("--------------------------------------------------")
    
    # Distribution by Tag
    cursor.execute("SELECT tag, count(*) FROM tags GROUP BY tag")
    print("Distribuição por Tag / Categoria Org-Roam:")
    for tag, cnt in cursor.fetchall():
        print(f"  - {tag}: {cnt} nós ({cnt/total_nodes:.2%})")
        
    print("==================================================")
    conn.close()

if __name__ == "__main__":
    process_batch()
