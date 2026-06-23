# Template: Refatorador Ontológico (Etapa 3)
[DADOS_REQUERIDOS]
  - {ETAPA2_OUTPUT} (Resultado estruturado da Etapa 2)
  - {RESUMO_BASE_EXISTENTE} (Conteúdo do arquivo principios_canonicos.md)
[INPUT] Output da Etapa 2:
{ETAPA2_OUTPUT}

RESUMO_BASE_EXISTENTE:
{RESUMO_BASE_EXISTENTE}

[TAREFA]
  1. Fusão de redundâncias → nova "Constante Canônica" unificada
  2. Resolução de conflitos → substituir dado obsoleto + marcar [ATUALIZADO_{ANO}]
  3. Lacunas de inquérito → listar perguntas abertas geradas pelo novo nó
  4. Sugestão de próxima fonte → onde buscar para fechar a lacuna

[OUTPUT] Diff semântico da base · apenas o que muda · sem reescrever o que permanece
