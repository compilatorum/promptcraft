# 🧬 promptcraft: Motor de Destilação de Conhecimento

Este repositório implementa o **Motor Nexialista de Destilação de Conhecimento** conforme especificado em `EpistemoAutomatic_PromptEngSpec.md`. O objetivo deste sistema é extrair os axiomas fundamentais de fontes de conhecimento bruto, integrando-os de forma iterativa e auto-regenerativa em uma ontologia viva.

---

## 🔮 Planejamento de Escala e Integração Epistêmica

O Promptcraft foi arquitetado para ir além da triagem e ingestão local. Para ver os planos detalhados de expansão, especificações de engenharia e modelagem de conectores para dados heterogêneos (YouTube, GitHub Starred, Reddit, NotebookLM, Google Drive via rclone, Bookmarks, Semantic Scholar, CDP/GPT chatlogs, Lightpanda e dados Web3/DAOs) em um grafo de conhecimento unificado (PKM), consulte as especificações:

👉 **[Planejamento de Escala Epistêmica](file:///home/sukata/promptcraft/ontologia/planejamento_escala.md)**
👉 **[Conectores de Ingestão e Estrutura de Grafo PKM](file:///home/sukata/promptcraft/ontologia/integracao_fontes_pkm.md)**

---

## 🗺️ Estrutura do Repositório

```text
/promptcraft/
  /templates/
    desconstrutor_atomico.md       → Etapa 1: Extração de Mecanismos e Constantes
    tecelao_nexialista.md          → Etapa 2: Isomorfismos e Impacto Cruzado
    refatorador_ontologico.md      → Etapa 3: Resolução de Conflitos e Gaps
    triagem_continua.md            → Filtro P1-P3 de Triagem Epistemológica
    auditoria_socrática.md         → Auditoria de Premissas do Framework
    refatorador_ciclo.md           → Prompt de Loop de Auto-Regeneração
    aplicar_diff_semantico.md      → Prompt auxiliar para aplicar o Diff Ontológico
  /ontologia/
    principios_canonicos.md        → Base viva de axiomas (principais ensinamentos)
    lacunas_abertas.md             → Perguntas sem resposta geradas pelo sistema
    log_refatoracoes.md            → Histórico de modificações e ciclos de refatoração
  /sessoes/
    {AAAA-MM-DD}_{dominio}.md      → Logs de cada ciclo de processamento individual
  /backups/
    *                              → Backups automáticos criados antes de atualizações
  config.json                      → Configuração de LLM e chaves de API
  promptcraft.py                   → Ferramenta CLI principal
```

---

## 🛠️ Instalação e Configuração

### 1. Pré-requisitos
Certifique-se de que os pacotes do provedor que você deseja utilizar estão instalados:
```bash
# Para usar OpenAI
pip install openai

# Para usar Anthropic (Claude)
pip install anthropic

# Para usar Gemini
pip install google-generativeai
```

### 2. Configurando Chaves de API
Você pode configurar as chaves de API de três formas diferentes (em ordem de precedência):

1. **Variáveis de Ambiente**:
   ```bash
   export OPENAI_API_KEY="sua-chave-aqui"
   export ANTHROPIC_API_KEY="sua-chave-aqui"
   export GEMINI_API_KEY="sua-chave-aqui" # ou GOOGLE_API_KEY
   ```

2. **Arquivo `.env`**:
   Crie um arquivo `.env` na raiz da pasta `promptcraft` ou no diretório de execução atual:
   ```env
   OPENAI_API_KEY=sua-chave-aqui
   ANTHROPIC_API_KEY=sua-chave-aqui
   GEMINI_API_KEY=sua-chave-aqui
   ```

3. **Arquivo de Configuração (`config.json`)**:
   Edite o arquivo `/home/sukata/promptcraft/config.json` e adicione a chave do provedor escolhido, definindo também o `provider` e o `model` de preferência:
   ```json
   {
       "provider": "gemini",
       "model": "gemini-1.5-flash",
       "openai_api_key": "",
       "anthropic_api_key": "",
       "gemini_api_key": "sua-chave-gemini-aqui",
       "temperature": 0.2
   }
   ```

---

## 🚀 Comandos Operacionais da CLI

A ferramenta CLI `promptcraft.py` pode ser executada a partir de qualquer local. Abaixo estão os principais comandos e parâmetros de uso.

### 1. Inicializar Diretórios e Configurações
Garante que todas as pastas e arquivos de configuração padrão necessários estejam criados.
```bash
python3 promptcraft.py init
```

### 2. Triagem Epistemológica (Filtro P1-P3)
Verifica se um determinado conteúdo oferece mecanismos causais novos, constantes ou gaps, classificando-o sem rodar o pipeline completo.
```bash
# Via texto direto
python3 promptcraft.py triar --text "O aumento da entropia em sistemas fechados segue a lei..."

# Via arquivo de texto local
python3 promptcraft.py triar --file caminho/para/arquivo.txt

# Via URL externa (extração automática do corpo da página)
python3 promptcraft.py triar --url "https://exemplo.com/artigo-tecnico"
```

### 3. Executar o Pipeline de Destilação Completo
Executa a **Triagem**, **Etapa 1 (Desconstrutor)**, **Etapa 2 (Tecelão)** e **Etapa 3 (Refatorador)**. Se aprovado pela triagem, atualiza automaticamente a ontologia viva (`principios_canonicos.md` e `lacunas_abertas.md`) e gera um arquivo de log na pasta `sessoes/`.
```bash
# Processar uma URL especificando domínio e tipo da fonte
python3 promptcraft.py processar \
  --url "https://github.com/exemplo/projeto" \
  --source-type code \
  --source-ref "github/projeto" \
  --domain "hard-tech"

# Processar um arquivo local forçando a execução mesmo se a triagem reprovar
python3 promptcraft.py processar \
  --file "artigo.txt" \
  --source-type document \
  --source-ref "Artigo Inovação" \
  --domain "fronteiras-teoricas" \
  --force
```
*Dica para repositórios de código:* Se você selecionar `--source-type code` e passar um diretório local para `--file`, a CLI lerá automaticamente os arquivos `README.md` e `CHANGELOG.md` presentes na pasta!

### 4. Ciclo de Refatoração (Auto-Regeneração)
Faz a varredura na base de dados em busca de redundâncias, conflitos, contradições e nós isolados. Consolida tudo em constantes canônicas e gera um relatório completo de modificações em `log_refatoracoes.md`, além de atualizar `principios_canonicos.md` e `lacunas_abertas.md`.
```bash
python3 promptcraft.py refatorar
```

### 5. Auditoria Socrática
Executa o prompt socrático que audita a arquitetura conceitual e premissas implícitas do framework, salvando o relatório na pasta `sessoes/`.
```bash
python3 promptcraft.py auditar
```

### 6. Importação de Fontes Externas (Takeout / APIs)
Importa e unifica links de fontes externas como inscrições de YouTube (Takeout CSV), repositórios de código favoritos do GitHub, posts do Reddit e artigos acadêmicos do arXiv. Salva de forma incremental em `ontologia/fontes_importadas.md`.
```bash
# Inscrições do YouTube (Google Takeout CSV)
python3 promptcraft.py importar --type youtube --file caminho/para/subscriptions.csv

# Repositórios Favoritados do GitHub de um usuário
python3 promptcraft.py importar --type github --user "nome-usuario-github"

# Posts Salvos do Reddit (JSON ou CSV)
python3 promptcraft.py importar --type reddit --file posts_reddit.json

# Artigos Científicos do arXiv (Busca ou IDs específicos)
python3 promptcraft.py importar --type arxiv --query "2304.12345,2211.02350"
python3 promptcraft.py importar --type arxiv --query "quantum computing"
```

### 7. Pesquisa Sistemática (Loop Metacognitivo de 4 Etapas)
Executa a esteira de pesquisa do Manifesto Oms-Sistêmico. Passa sequencialmente pelo Passo 1 (Gnosio-Logística / Inquérito), Passo 2 (Mapeamento de Frameworks), Passo 3 (Simulação/Debug Coorte) e Passo 4 (Compressão de Sabedoria), atualizando a ontologia viva com as novas diretrizes éticas e lacunas identificadas.
```bash
python3 promptcraft.py pesquisar \
  --url "https://arxiv.org/abs/2304.12345" \
  --line "Computação Quântica e Holografia"
```

---

## ⚙️ Parâmetros Adicionais Comuns

* `--provider`: Define o provedor do LLM (`openai`, `anthropic`, `gemini`, `huggingface`, `agent`, `antigravity`). Se não informado, tenta detectar automaticamente a partir das chaves configuradas.
* `--model`: Permite usar um modelo de LLM personalizado.
* `--temperature`: Controla a criatividade e rigor factual do LLM (default: `0.2`).
* `--api-key`: Permite passar a chave diretamente via comando.

---

## 🤖 Integração do Provedor de Agente Autônomo (`agent`)

O Motor Promptcraft agora possui suporte nativo ao provedor `"agent"` (ou `"antigravity"`), permitindo que **o próprio agente executor (Antigravity)** funcione como backend do LLM sem necessidade de chaves de API externas.

### Como funciona
1. Quando o `--provider agent` é selecionado, o motor escreve o prompt no terminal envolto por marcadores delimitadores:
   ```text
   === AGENT_PROMPT_START ===
   [conteúdo do prompt]
   === AGENT_PROMPT_END ===
   ```
2. O CLI entra em suspensão e aguarda a entrada do agente no `stdin`.
3. O agente processa a requisição usando sua própria inteligência cognitiva e envia o resultado no terminal de fundo, finalizando com a linha:
   ```text
   === AGENT_RESPONSE_END ===
   ```
4. O CLI detecta a quebra de linha do delimitador, assimila a resposta e avança no pipeline.

Este ciclo de interações em loop fecha o círculo de **sistemas de segunda ordem**, onde o agente opera a ferramenta que o invoca.

---

## 🔮 Roadmap de Extensibilidade para Novas Fontes de Dados

Para evoluir a esteira de ingestão e abranger o espectro completo do Manifesto Oms-Sistêmico, o Promptcraft deve expandir sua infraestrutura de coletores para os seguintes formatos:

### 🌐 1. Hiperlinks e Web Links em Geral
* **Arquitetura de Ingestão**: Web scrapers com suporte a renderização de Single Page Applications (SPAs) e extração de metadados semânticos.
* **Metodologia de Destilação**: Algoritmos de limpeza para remoção de menus (`<nav>`), propagandas e rodapés, convertendo o conteúdo útil em Markdown estruturado que preserva apenas os links internos/externos relevantes para mapeamento topológico.

### 💻 2. Repositórios do GitHub (Bookmarks & Código)
* **Arquitetura de Ingestão**: Consumo incremental da API de Stars do GitHub.
* **Metodologia de Destilação**: Varredura recursiva de arquivos `README.md`, `ARCHITECTURE.md` e tags de tópicos do repositório para mapeamento de isomorfismos arquiteturais e agregação de padrões em clusters no `principios_canonicos.md`.

### 🔬 3. Árvore de Citações de Artigos Científicos (arXiv / Scholar)
* **Arquitetura de Ingestão**: Integração com a API do Semantic Scholar (`api.semanticscholar.org`).
* **Metodologia de Destilação**: Coleta dos grafos de citações e referências dos artigos ingeridos. Nós com alta centralidade de co-citação são promovidos como axiomas pilares, enquanto conflitos conceituais na literatura são exportados como novas perguntas abertas em `lacunas_abertas.md`.

### 📓 4. Compartilhamento de Cadernos (NotebookLM / Jupyter / Colab)
* **Arquitetura de Ingestão**: Extração de células de notebooks (arquivos `.ipynb`) e transcrições geradas pelo NotebookLM (MP3/PDF).
* **Metodologia de Destilação**: Processamento diferenciado de código (execução lógica), comentários (intenção metodológica) e logs de saída. Casos de uso de código que validam premissas teóricas alimentam as asserções de invariante do sistema.

### 📊 5. Monitoramento de Dados Quantitativos e Métricas Financeiras
* **Arquitetura de Ingestão**: Integração de cronjobs (via agendador do agy) que consultam feeds estruturados JSON/CSV de dados de mercado (ex: inflação, volatilidade de ativos).
* **Metodologia de Destilação**: Conversão de séries temporais em métricas matemáticas de controle de risco, atualizadas dinamicamente via frontmatter YAML na base de axiomas.

### 👥 6. Comunidades e Redes Sociais (Reddit / Twitter / Farcaster)
* **Arquitetura de Ingestão**: Parsers de discussões em threads utilizando APIs de redes descentralizadas ou arquivos de exportação.
* **Metodologia de Destilação**: Agrupamento semântico de discussões para detecção de consensos de comunidade, tendências emergentes e refutação de boatos (ruído semântico).

### 🏛️ 7. Governança e Processos em DAOs
* **Arquitetura de Ingestão**: Consumo da API do Snapshot (votações de propostas) e governança em redes EVM.
* **Metodologia de Destilação**: Rastreamento de propostas aprovadas e discussões em fóruns (Discourse) para alimentar a ontologia com regras pragmáticas de governança descentralizada e lições aprendidas de incentivo/conflito de agentes.


