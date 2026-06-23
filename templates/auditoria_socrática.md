# Template: Auditoria Socrática
[DADOS_REQUERIDOS]
  - {RESUMO_BASE_EXISTENTE} (Conteúdo do arquivo principios_canonicos.md)

[ROLE] Auditor socrático do sistema de conhecimento

RESUMO_BASE_EXISTENTE:
{RESUMO_BASE_EXISTENTE}

[TAREFA] Responda às três perguntas de sombra:
  1. Que pressupostos não questionados esta arquitetura reproduz?
  2. Onde o filtro de "impact washing" pode estar rejeitando sinal real?
  3. Que tipo de conhecimento este sistema é estruturalmente incapaz de capturar?

[OUTPUT]
Retorne um objeto JSON contendo uma lista de propostas estruturadas exatamente no seguinte formato. Não adicione preamble, markdown code blocks ou explicações fora do JSON.
[
  {
    "problema": "Descrição do problema/sombra identificada na auditoria",
    "proposta": "Proposta de melhoria conceitual para mitigar o problema",
    "experimento": "Experimento prático concreto para testar a proposta"
  },
  ... (exatamente 3 propostas)
]
