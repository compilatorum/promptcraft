# Template: Passo 4 - Compressão de Sabedoria (Otimização Recursiva)
[DADOS_REQUERIDOS]
  - {PASSO3_OUTPUT} (Resultado do Passo 3 - Simulação e Debug)
[TAREFA]
Comprima os resultados deste ciclo experimental. Transforme os dados brutos analisados em Conhecimento (Regras Inferidas) e Sabedoria (Diretrizes Regenerativas).
Para cada princípio, regra inferida ou diretriz, inclua obrigatoriamente um bloco YAML de metadados contendo a escala de confiança com a chave `confianca` assumindo um dos seguintes valores: `alto`, `medio`, `baixo` ou `especulativo`.
Exemplo:
---
axioma: Nome do Princípio
confianca: alto
---
Descrição do princípio e mecanismo.

Resultados do Passo 3:
{PASSO3_OUTPUT}

