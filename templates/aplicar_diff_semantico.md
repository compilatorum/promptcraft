# Template: Aplicar Diff Semântico
[ROLE] Integrador de conhecimento sênior

[INPUT]
Base Canônica Atual:
{PRINCIPIOS_CANONICOS}

Diff Semântico (Novidades/Modificações):
{DIFF_SEMANTICO}

[TAREFA]
Aplique as alterações descritas no Diff Semântico à Base Canônica Atual.
Retorne APENAS a nova base de conhecimento completa de `principios_canonicos.md`. Não adicione explicações, preambles ou comentários fora do markdown resultante.
A nova base deve conter os princípios antigos intactos (se não forem modificados) e incorporar as alterações e adições trazidas pelo diff semântico.

[DIRETRIZ DE INCERTEZA]
Todos os axiomas/princípios na base `principios_canonicos.md` devem conter obrigatoriamente metadados de incerteza na forma de um bloco YAML/frontmatter com a chave `confianca` assumindo um dos seguintes valores: `alto`, `medio`, `baixo` ou `especulativo`.
Exemplo:
---
axioma: Nome do Axioma
confianca: alto
---
Descrição do axioma e seu mecanismo causal.

