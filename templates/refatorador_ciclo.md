# Template: Loop de Auto-Regeneração (Refatoração de Ciclo)
[ROLE] Engenheiro de conhecimento sênior · refatorador ontológico

[INPUT]
Princípios Canônicos Atuais:
{PRINCIPIOS_CANONICOS}

Lacunas Abertas Atuais:
{LACUNAS_ABERTAS}

[TAREFA]
Realize o ciclo de auto-regeneração sobre a base de conhecimento acima:
1. Identifique redundâncias entre os princípios e funda-os em "Constantes Canônicas" unificadas.
2. Resolva contradições, atualizando para as versões corretas/mais refinadas e marcando [ATUALIZADO_{ANO}] (onde {ANO} é o ano atual).
3. Comprima os princípios: remova descrições prolixas e exemplos redundantes, mantendo apenas fórmulas, mecanismos causais puros e regras compactas.
4. Identifique nós isolados (sem arcos nexialistas ou relações) e avalie se devem ser arquivados como [RUÍDO] ou transformados em [LACUNA].
5. Atualize as "Lacunas Abertas", removendo as perguntas que foram respondidas e adicionando novas.
6. Certifique-se de que todos os axiomas/princípios na base resultante `principios_canonicos.md` possuam um bloco de metadados YAML/frontmatter estruturado contendo: `confianca` (`alto`, `medio`, `baixo`, `especulativo`), `evidencias_qtd` (inteiro), `contradicoes_qtd` (inteiro) e `referencias` (lista de strings com IDs de referência).

[OUTPUT]
Sua resposta deve conter três seções principais separadas exatamente por `=== DIVIDER ===`:

1. Novo conteúdo para `principios_canonicos.md` (onde cada axioma/princípio tem seu respectivo frontmatter YAML com `confianca`, `evidencias_qtd`, `contradicoes_qtd` e `referencias`)
=== DIVIDER ===
2. Novo conteúdo para `lacunas_abertas.md`
=== DIVIDER ===
3. Relatório de modificações (o que mudou, o que foi fundido, resolvido ou removido).
