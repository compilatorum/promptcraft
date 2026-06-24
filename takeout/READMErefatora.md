# CSO - Cognitive Search Orchestrator

Sistema de análise cognitiva de repositórios de código com capacidades de busca semântica, insights automatizados e relatórios detalhados.

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

### Analisar um repositório

```bash
python main.py analyze /path/to/repo --deep
```

### Buscar código

```bash
python main.py search "função de autenticação" --repo /path/to/repo
```

### Chat interativo

```bash
python main.py chat --repo /path/to/repo
```

### Gerar relatório

```bash
python main.py report analysis_result.json --type technical --output report.md
```

### Dashboard

```bash
python main.py dashboard --repo /path/to/repo
```

## Configuração

Edite `config.yaml` para personalizar:
- Modelos de IA (OpenAI, Ollama)
- Padrões de análise de código
- Limites e thresholds
- Formatos de saída

## Estrutura do Projeto

```
cso/
├── cso_core/          # Core do orquestrador
├── cso_analyzers/     # Analisadores de código, repositório, dependências
├── cso_insights/      # Geração e visualização de insights
├── cso_chat/           # Chat interativo
├── cso_reports/        # Geração de relatórios
└── cso_gap/            # Análise de gaps
```

## Licença

MIT
