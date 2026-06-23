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

[DIRETRIZ DE RASTREABILIDADE E INCERTEZA]
Todos os axiomas/princípios na base `principios_canonicos.md` devem conter obrigatoriamente metadados estruturados na forma de um bloco YAML/frontmatter com as seguintes chaves:
  - `confianca`: `alto`, `medio`, `baixo` ou `especulativo`
  - `evidencias_qtd`: número de fontes independentes que suportam este axioma (inteiro)
  - `contradicoes_qtd`: número de fontes independentes que contradizem ou limitam este axioma (inteiro)
  - `referencias`: lista de strings de IDs de referência das fontes de suporte (ex: `doc:manual-input`, `video:UC-1BAmCv...`)

Exemplo:
---
axioma: Nome do Axioma
confianca: alto
evidencias_qtd: 2
contradicoes_qtd: 0
referencias:
  - doc:manual-input
  - video:UC-1BAmCv...
---
Descrição do axioma e seu mecanismo causal.

