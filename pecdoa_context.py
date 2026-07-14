# -*- coding: utf-8 -*-
"""
🧠 PECDOA-DFK Context Engine (promptcraft)
Responsável pelas camadas de Busca Vetorial Semântica (Embeddings) e Compactação de Mensagens (Context Manager).
"""

import os
import json
import numpy as np

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_DIR = os.path.join(BASE_DIR, "promptcraft", "templates")
LOGS_DIR = os.path.join(BASE_DIR, "promptcraft", "logs")

os.makedirs(PROMPTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)


class PECDOAVectorStore:
    """Busca Semântica de Prompts e Logs usando Embeddings Local (com fallback offline)"""
    def __init__(self):
        self.encoder = None
        self.dimension = 384
        self.try_load_encoder()

    def try_load_encoder(self):
        try:
            # Tenta carregar sentence_transformers localmente
            from sentence_transformers import SentenceTransformer
            # Carrega o modelo local/cached sem bater na internet se possível
            self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
            print("[VectorStore] SentenceTransformer carregado com sucesso.")
        except Exception:
            print("[VectorStore] SentenceTransformer não disponível. Usando HashVectorizer determinístico 100% offline.")

    def get_embedding(self, text: str) -> list:
        if self.encoder:
            try:
                emb = self.encoder.encode(text)
                return list(emb.astype(float))
            except Exception:
                pass
        
        # Fallback: HashVectorizer de 384 dimensões
        h = hash(text)
        np.random.seed(h % 2**32)
        vec = np.random.randn(self.dimension)
        # Normalização do vetor
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return list(vec.astype(float))

    def calculate_similarity(self, vec1: list, vec2: list) -> float:
        v1, v2 = np.array(vec1), np.array(vec2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    def search_prompts(self, query: str, top_k=2) -> list:
        query_vec = self.get_embedding(query)
        
        results = []
        # Percorre a pasta de templates/prompts para encontrar o mais similar semanticamente
        if os.path.exists(PROMPTS_DIR):
            for filename in os.listdir(PROMPTS_DIR):
                if filename.endswith(".md") or filename.endswith(".jinja"):
                    path = os.path.join(PROMPTS_DIR, filename)
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Gera embedding do conteúdo
                    content_vec = self.get_embedding(content)
                    similarity = self.calculate_similarity(query_vec, content_vec)
                    results.append({
                        "file": filename,
                        "similarity": similarity,
                        "content": content
                    })
        
        results.sort(key=lambda x: -x["similarity"])
        return results[:top_k]


class PECDOAContextManager:
    """Compactação e Compressão de Mensagens para Controle de Janela de Contexto de LLM"""
    def __init__(self):
        pass

    def compact_history(self, messages: list, max_recent=5) -> dict:
        """Sumariza mensagens anteriores e mantém as últimas 'max_recent' mensagens intactas"""
        if len(messages) <= max_recent:
            return {
                "summary": "",
                "recent_messages": messages
            }

        # Divide o histórico em antigas e recentes
        old_messages = messages[:-max_recent]
        recent_messages = messages[-max_recent:]
        
        # Sumarização heurística simples (BART mock / Regras de extração de pontos-chave)
        summary_points = []
        for msg in old_messages:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            # Pega as primeiras palavras chave ou sentenças principais
            summary_points.append(f"[{role}] {content[:100]}...")
            
        summary = "RESUMO DE TURNOS ANTERIORES:\n" + "\n".join(summary_points)
        
        print(f"[ContextManager] {len(old_messages)} mensagens antigas compactadas em um único resumo de {len(summary)} bytes.")
        return {
            "summary": summary,
            "recent_messages": recent_messages
        }
