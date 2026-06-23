# Template: Triagem Contínua (Filtro P1-P3)
[DADOS_REQUERIDOS]
  - {CONTEUDO} (Conteúdo bruto da fonte)
  - {RESUMO_BASE_EXISTENTE} (Conteúdo do arquivo principios_canonicos.md)
[TAREFA]
Avalie o seguinte conteúdo sob os seguintes critérios:

P1: Este conteúdo apresenta um mecanismo causal novo ou uma constante quantificável?
    Se não, classifique como [RUÍDO-DE-BAIXA-DENSIDADE].

P2: Este conteúdo contradiz, expande ou refina algo já na base?
    Se não, classifique como [REDUNDANTE-CONFIRMATIVO].

P3: Este conteúdo abre uma lacuna de inquérito não mapeada?
    Se sim, classifique como [NÓ-NOVO-DE-CONHECIMENTO].
    Se não, classifique como [CONFIRMAÇÃO-DE-AXIOMA].

Resumo da base existente para comparação:
{RESUMO_BASE_EXISTENTE}

Conteúdo a avaliar:
{CONTEUDO}

[OUTPUT]
Sua resposta deve conter apenas uma linha com a classificação final entre colchetes, seguido por uma justificativa concisa baseada em P1, P2 e P3.
Exemplo:
[NÓ-NOVO-DE-CONHECIMENTO] Apresenta mecanismo causal de tolerância a falhas via termodinâmica que não consta na base.
