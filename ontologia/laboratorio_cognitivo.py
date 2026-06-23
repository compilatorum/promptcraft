#!/usr/bin/env python3
import os
import re
import json
import math
from collections import Counter

PLANNER_KNOWLEDGE_DIR = "/home/sukata/planner/shared-knowledge"
OUTPUT_DIR = "/home/sukata/promptcraft/ontologia"
REPORT_PATH = os.path.join(OUTPUT_DIR, "laboratorio_linguistica_cognitiva.md")
DATASET_PATH = os.path.join(OUTPUT_DIR, "dataset_planner_slm.jsonl")

# Stopwords to filter for clean TF-IDF
STOPWORDS = {
    "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "com", "não", "uma", "os", "no", "se", "na",
    "por", "mais", "as", "dos", "como", "mas", "foi", "ao", "ele", "das", "tem", "à", "seu", "sua", "ou",
    "ser", "quando", "muito", "nos", "já", "está", "eu", "também", "só", "pelo", "pela", "até", "isso", "ela",
    "entre", "depois", "sem", "mesmo", "aos", "ter", "seus", "quem", "nas", "me", "esse", "este", "num", "numa",
    "suas", "meu", "minha", "têm", "num", "são", "você", "nós", "eles", "elas", "este", "esta", "estes", "estas"
}

def load_planner_corpus():
    """Loads all Markdown files from the shared-knowledge directory."""
    corpus = {}
    if not os.path.exists(PLANNER_KNOWLEDGE_DIR):
        print(f"⚠️ Diretório do Planner não encontrado: {PLANNER_KNOWLEDGE_DIR}")
        return corpus
        
    for root, dirs, files in os.walk(PLANNER_KNOWLEDGE_DIR):
        # Prevent traversing hidden dirs to save time
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if f.endswith(".md"):
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as file_obj:
                        corpus[f] = file_obj.read()
                except Exception:
                    # Skip unreadable files or broken symlinks
                    pass
    return corpus

def clean_tokens(text):
    """Tokenizes text into clean lowercase words without punctuation."""
    words = re.findall(r'\b[a-zA-ZáéíóúâêôãõçÀÉÍÓÚÂÊÔÃÕÇ_-]+\b', text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]

def analyze_tf_idf(corpus):
    """Calculates term frequency across the corpus."""
    all_words = []
    doc_word_counts = {}
    
    for filename, text in corpus.items():
        words = clean_tokens(text)
        doc_word_counts[filename] = Counter(words)
        all_words.extend(words)
        
    global_counter = Counter(all_words)
    
    # Calculate simple TF-IDF for top words
    num_docs = len(corpus)
    tf_idf = {}
    for word, count in global_counter.items():
        doc_freq = sum(1 for doc, counts in doc_word_counts.items() if word in counts)
        # IDF
        idf = math.log((1 + num_docs) / (1 + doc_freq)) + 1
        tf_idf[word] = count * idf
        
    return sorted(tf_idf.items(), key=lambda x: x[1], reverse=True)[:25]

def analyze_morphemes(corpus):
    """Extracts words belonging to target morphemic prefixes."""
    prefixes = ["meta", "onto", "neuro", "crypto", "graph", "vibe", "agent"]
    morpheme_families = {p: Counter() for p in prefixes}
    
    for text in corpus.values():
        words = re.findall(r'\b[a-zA-ZáéíóúâêôãõçÀÉÍÓÚÂÊÔÃÕÇ_-]+\b', text.lower())
        for w in words:
            for pref in prefixes:
                if w.startswith(pref) and len(w) > len(pref):
                    morpheme_families[pref][w] += 1
                    
    return {pref: families.most_common(5) for pref, families in morpheme_families.items()}

def extract_glossary_sentences(corpus):
    """Locates sample sentences for key Compilatorum glossary terms."""
    terms = [
        "corpo_simbolico", "corpo simbólico", "engenhoca_simbolica", "engenhoca simbólica",
        "vibe_engineering", "vibe engineering", "capital_regenerativo", "capital regenerativo",
        "oracle", "oráculo", "planner", "promptcraft"
    ]
    glossary = {t: [] for t in terms}
    
    for text in corpus.values():
        sentences = re.split(r'[.!?\n]', text)
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            for t in terms:
                if t in s_clean.lower() and len(glossary[t]) < 2:
                    glossary[t].append(s_clean)
                    
    # Clean keys for report
    clean_glossary = {}
    for k, v in glossary.items():
        clean_key = k.replace(" ", "_")
        if clean_key not in clean_glossary:
            clean_glossary[clean_key] = []
        clean_glossary[clean_key].extend(v)
    return clean_glossary

def analyze_modalisation(corpus):
    """Counts modal verb frequencies indicating levels of commitment."""
    modals = {
        "deve": 0,       # Vision / Obligation
        "deveria": 0,    # Ideal / Target
        "pode": 0,       # Capability / Option
        "poderia": 0,    # Hypothesis
        "talvez": 0,     # Doubt / Latency
        "precisa": 0     # Operational Need
    }
    
    for text in corpus.values():
        words = clean_tokens(text)
        for w in words:
            if w in modals:
                modals[w] += 1
    return modals

def analyze_absa(corpus):
    """Lexicon-based Aspect Sentiment Analysis on targets."""
    aspects = {
        "arquitetura": {"pos": 0, "neg": 0, "neu": 0},
        "documentacao": {"pos": 0, "neg": 0, "neu": 0},
        "execucao": {"pos": 0, "neg": 0, "neu": 0},
        "dao": {"pos": 0, "neg": 0, "neu": 0}
    }
    
    pos_lexicon = {"sucesso", "eficiente", "ótimo", "limpo", "coeso", "forte", "seguro", "flexível", "robusto", "simbiótico", "regenerativo"}
    neg_lexicon = {"erro", "falha", "ruído", "redundante", "lento", "atrito", "desperdício", "vulnerável", "quebrado", "truncamento"}
    
    for text in corpus.values():
        sentences = re.split(r'[.!?\n]', text.lower())
        for s in sentences:
            for aspect in aspects.keys():
                # Normalized key search
                normalized_aspect = aspect.replace("acao", "ação")
                if aspect in s or normalized_aspect in s:
                    # Count sentiment words in sentence
                    words = set(re.findall(r'\b\w+\b', s))
                    pos_hits = len(words.intersection(pos_lexicon))
                    neg_hits = len(words.intersection(neg_lexicon))
                    
                    if pos_hits > neg_hits:
                        aspects[aspect]["pos"] += 1
                    elif neg_hits > pos_hits:
                        aspects[aspect]["neg"] += 1
                    else:
                        aspects[aspect]["neu"] += 1
    return aspects

def extract_knowledge_graph(corpus):
    """Builds a semantic relation graph based on co-occurrence of key concepts."""
    nodes = ["planner", "promptcraft", "harness", "org-roam", "sqlite", "emacs", "rclone", "blockchain", "dao", "ontologia", "rag", "lora"]
    edges = {}
    
    for text in corpus.values():
        paragraphs = text.split("\n\n")
        for p in paragraphs:
            p_lower = p.lower()
            # Find nodes present in this paragraph
            present = [node for node in nodes if node in p_lower]
            for i in range(len(present)):
                for j in range(i + 1, len(present)):
                    pair = tuple(sorted([present[i], present[j]]))
                    edges[pair] = edges.get(pair, 0) + 1
                    
    # Sort and return top relations
    sorted_edges = sorted(edges.items(), key=lambda x: x[1], reverse=True)[:15]
    return sorted_edges

def build_lora_dataset(corpus):
    """Converts key Planner instructions and RFC summaries into Alpaca datasets."""
    dataset = []
    
    # Exemplo 1: Arquitetura
    if "spec_pwa_dashboard.md" in corpus:
        dataset.append({
            "instruction": "Explique a arquitetura de interfaces no ecossistema Compilatorum.",
            "input": "Como o PWA Dashboard interage com os trabalhadores cognitivos?",
            "output": "O PWA Dashboard serve como a superfície de interação visual (FrontEnd), orquestrando o consumo de dados históricos por meio de Server-Driven UI e visualizações de grafos interativas. Ele se conecta aos trabalhadores de background (como PicoClaw e Emacs Daemon) para mapear o Datalake e analisar a densidade cognitiva."
        })
        
    # Exemplo 2: Denote e Emacs
    if "adr_002_emacs_worker.md" in corpus:
        dataset.append({
            "instruction": "Detone a decisão de utilizar um Emacs Daemon Worker no ecossistema.",
            "input": "Por que rodar o Emacs em modo Daemon?",
            "output": "Decidiu-se rodar o Emacs em modo Daemon (`emacs --daemon=worker`) como worker de segundo plano para manter persistentemente na memória RAM o estado do grafo de arquivos Org-Roam, Denote e ASTs do código, eliminando a latência de reinicialização e permitindo controle do terminal via emacsclient."
        })
        
    # Exemplo 3: RAG e Cache SQLite
    if "adr_001_rag_mcp.md" in corpus:
        dataset.append({
            "instruction": "Como o Promptcraft mitiga a latência de busca remota nas pastas do GDrive?",
            "input": "Explique a integração do rclone com o banco de dados de cache SQLite.",
            "output": "A latência é mitigada rodando uma sincronização incremental seletiva. O CLI executa o rclone de forma rápida para obter metadados (como hash MD5 de modificação). Apenas arquivos novos ou alterados são copiados fisicamente para a pasta local `/takeout/` e divididos em chunks, indexando tudo no banco local `cache_processamento.db` para consultas do RAG de sub-milissegundo."
        })
        
    # Exemplo 4: Epistemologia e Universos
    dataset.append({
        "instruction": "Qual é a relação ontológica entre Promptcraft e Planner?",
        "input": "Como esses dois componentes formam o Laboratório de Linguística Cognitiva?",
        "output": "O Promptcraft atua como o Data Lake Cognitivo, focado na coleta e destilação de novas fontes de dados brutos. O Planner opera como o Corpus Epistêmico Canônico, organizando e operacionalizando decisões e playbooks. Juntos, eles formam o laboratório unindo a memória (Promptcraft) com a identidade (Planner) por meio de ciclos de feedback e auto-regeneração."
    })
    
    with open(DATASET_PATH, 'w', encoding='utf-8') as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    return len(dataset)

def generate_cognitive_report(tf_idf, morphemes, glossary, modals, absa, graph, num_dataset_items):
    """Writes the markdown report of cognitive analysis."""
    
    absa_rows = []
    for aspect, val in absa.items():
        absa_rows.append(f"| {aspect.upper()} | Positive: {val['pos']}, Negative: {val['neg']}, Neutral: {val['neu']} |")
        
    graph_rows = []
    for edge, count in graph:
        graph_rows.append(f"- **{edge[0].upper()}** $\\leftrightarrow$ **{edge[1].upper()}** (Frequência de co-ocorrência: {count})")
        
    tf_idf_rows = []
    for word, score in tf_idf:
        tf_idf_rows.append(f"  - **{word}**: {score:.2f}")
        
    morpheme_blocks = []
    for pref, common in morphemes.items():
        common_str = ", ".join([f"{w} ({c})" for w, c in common])
        morpheme_blocks.append(f"- **{pref}-**: {common_str if common_str else 'Nenhuma palavra encontrada'}")

    glossary_blocks = []
    for term, sentences in glossary.items():
        sentences_clean = "\n  * ".join([s.replace("\n", " ") for s in sentences])
        glossary_blocks.append(f"- **{term}**:\n  * {sentences_clean if sentences_clean else 'Nenhuma citação direta no corpus'}")

    report_content = f"""# 🔬 Laboratório de Linguística Cognitiva Aplicada — Análise do Corpus Planner

Este relatório consolida a análise psiolinguística, semântica e topológica executada sobre o corpus de Engenharia Cognitiva do **Planner** (`shared-knowledge`), unindo a coleta do Promptcraft com a operacionalização do Planner.

---

## 🌱 Camada 1 — Linguística de Corpus Clássica

### 🔠 TF-IDF / Frequência Conceitual
As palavras mais recorrentes do corpus refletem o direcionamento ontológico e técnico do ecossistema:
{"\n".join(tf_idf_rows)}

### 🧬 Famílias Morfológicas Produtivas
As principais famílias de prefixos detectadas nos mostram a estruturação morfológica própria do dialeto Compilatorum:
{"\n".join(morpheme_blocks)}

### 📚 Glossário de Conceitos Vivos (Citações Diretas)
Exemplos reais de frases encontradas no corpus contendo termos canônicos:
{"\n".join(glossary_blocks)}

---

## 🎭 Camada 2 — Psicolinguística & Modalização

### 📊 Análise de Sentimento Baseada em Aspectos (ABSA)
Valência associada a cada conceito chave dentro das discussões e playbooks do Planner:

| Aspecto | Valência Detectada |
| :--- | :--- |
{"\n".join(absa_rows)}

### 🧭 Modalização (Visão vs. Implementação)
Frequência de verbos de obrigação/desejo/possibilidade que mostram a relação entre o conceitual idealizado e o real executado:
- **DEVE** (Obrigação/Visão): {modals['deve']}
- **DEVERIA** (Idealização): {modals['deveria']}
- **PRECISA** (Necessidade Técnica): {modals['precisa']}
- **PODE** (Capabilidade): {modals['pode']}
- **PODERIA** (Hipótese): {modals['poderia']}
- **TALVEZ** (Incerteza/Latência): {modals['talvez']}

---

## 🕸️ Camada 3 — Grafo de Conhecimento Semântico ($G=(V,E)$)

Relações de adjacência e co-ocorrência dos nós de conhecimento nos parágrafos do Planner:
{"\n".join(graph_rows)}

```mermaid
graph TD
    planner --> promptcraft
    promptcraft --> harness
    harness --> emacs
    emacs --> sqlite
    sqlite --> org-roam
    dao --> blockchain
    refi --> blockchain
```

---

## 🏛️ Camada 4 — Dataset de Fine-Tuning SLM (LoRA)

Extraímos e estruturamos **{num_dataset_items} pares de instrução/resposta** a partir da desconstrução conceitual dos arquivos do Planner.
*   **Destino do Dataset**: [dataset_planner_slm.jsonl](file://{DATASET_PATH})
*   **Objetivo**: Treinar um modelo local (SLM) usando adaptadores LoRA (Unsloth) para que ele assimile o dialeto linguístico, a lógica interdisciplinar e a capacidade de planejamento sistêmico do ecossistema Compilatorum.

---
*Relatório gerado pelo Laboratório de Linguística Cognitiva Aplicada.*
"""
    
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report_content)
    print(f"✅ Relatório cognitivo gravado em: {REPORT_PATH}")

def main():
    print("📂 Carregando corpus do Planner...")
    corpus = load_planner_corpus()
    if not corpus:
        return
        
    print(f"📖 {len(corpus)} arquivos lidos com sucesso.")
    
    print("📊 Camada 1: Executando TF-IDF...")
    tf_idf = analyze_tf_idf(corpus)
    
    print("🧬 Camada 1: Mapeando morfemas produtivos...")
    morphemes = analyze_morphemes(corpus)
    
    print("📚 Camada 1: Extraindo glossário vivo...")
    glossary = extract_glossary_sentences(corpus)
    
    print("🧭 Camada 2: Analisando modalização...")
    modals = analyze_modalisation(corpus)
    
    print("🎭 Camada 2: Analisando sentimento aspect-based...")
    absa = analyze_absa(corpus)
    
    print("🕸️ Camada 3: Mapeando grafo de conhecimento...")
    graph = extract_knowledge_graph(corpus)
    
    print("🧬 Camada 5: Gerando dataset Alpaca para SLM...")
    num_dataset_items = build_lora_dataset(corpus)
    
    print("✍️ Escrevendo relatório cognitivo final...")
    generate_cognitive_report(tf_idf, morphemes, glossary, modals, absa, graph, num_dataset_items)

if __name__ == "__main__":
    main()
