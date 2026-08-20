---
name: review-pipelines-cultura-em-numeros
description: "Com base em um repositório do github do projeto Cultura em Números, revisar documentação e código, rodar um teste funcional real do pipeline (clonando o repositório, instalando dependências e executando os scripts, corrigindo erros simples quando possível), e gerar um relatório markdown mostrando se o projeto está rodando, quais são as falhas críticas, o que precisa ser melhorado, e um checklist final com os itens imprescindíveis para a execução. Use esta skill sempre que o usuário pedir para revisar, auditar, testar ou validar um repositório/pipeline do Cultura em Números."
---

O projeto cultura em números é dividido em eixos:
Para cada eixo tem um repositório no github;
Cada repositório possui um pipeline de dados que extrai e transforma dados dando outputs para a uma pesquisa

- Precisamos revisar o repositório e entender se ele é executável;
- Se possui documentação explicando a estrutura do código;
- Se possui documentação explicando como executar o código;
- Se possui erros críticos;
- Se possui um arquivo .xlsx contendo a ficha de metadados do projeto;
- Se possui um arquivo de dependências correspondente à linguagem do projeto: `requirements.txt` (ou `pyproject.toml`/`Pipfile`) para projetos em Python, ou `renv.lock` (projeto usando `renv`) para projetos em R;
- A ideia não é mudar substancialmente o código da pessoa;
- A ideia, a priori não é fazer qualquer alteração no código no repositório original, apenas se for pedido (a exceção é o teste funcional descrito abaixo, que roda sobre uma cópia local/temporária do repositório);
- Critérios mínimos que devem estar na documentação:
   - explicação de como funciona os scripts (como rodar, qual a sequência que devem ser rodados, o que cada um recebe de input e devolve de output e um pequeno tutorial explicando como rodar na máquina da pessoa que a clonar);

## Teste funcional do pipeline

Além da revisão de documentação e código, é preciso efetivamente tentar rodar o pipeline:

1. Clonar o repositório para um diretório temporário local (nunca alterar o repositório remoto/original).
2. Tentar identificar e instalar as dependências (ex: `requirements.txt`, `pyproject.toml`, `Pipfile` para Python; `renv.lock` para R; `package.json` para JS/Node; etc.).
3. Executar os scripts na sequência indicada pela documentação (ou, se não houver documentação clara, na ordem que parecer lógica pelos nomes/estrutura dos arquivos).
4. Se a execução falhar por um erro simples e de baixo risco (ex: dependência faltando, versão de biblioteca incompatível, variável de ambiente ou caminho de arquivo não configurado), tentar corrigir esse erro pontual na cópia local e rodar novamente. Cada correção feita deve ser registrada.
5. Se o erro não for simples (ex: exige entendimento profundo da lógica de negócio, dados de entrada ausentes que não podem ser criados, decisões de arquitetura), não tentar corrigir — apenas documentar o erro e onde ele ocorreu.
6. Repetir o processo até o pipeline rodar de ponta a ponta ou até esgotar as tentativas razoáveis de correção simples.

Esse teste gera um veredito: **passou** (rodou sem erros), **passou com ajustes** (precisou de correções simples, listadas), ou **falhou** (erro que não foi possível contornar).

## Relatório final

Ao fim, gerar um relatório markdown contendo:

1. **Resumo** — pontos que são impeditivos e sugestão de como mudar cada ponto para que o pipeline de fato funcione.
2. **Resultado do teste de execução** — veredito (passou / passou com ajustes / falhou), lista de correções simples aplicadas (se houver) e os erros encontrados (com trecho relevante do log/stack trace), incluindo os que não puderam ser corrigidos.
3. **Checklist de itens imprescindíveis para execução** — usando `[x]` para itens atendidos e `[ ]` para itens pendentes:
   - [ ] Repositório é executável (roda sem erros críticos, mesmo que com ajustes simples)
   - [ ] Documentação explica a estrutura do código
   - [ ] Documentação explica como executar o código (sequência dos scripts)
   - [ ] Cada script documenta input/output esperado
   - [ ] Existe tutorial de como rodar na máquina de quem clonar
   - [ ] Existe arquivo .xlsx com a ficha de metadados do projeto
   - [ ] Existe arquivo de dependências adequado à linguagem (`requirements.txt`/`pyproject.toml`/`Pipfile` para Python, ou `renv.lock` para R)
   - [ ] Ausência de erros críticos que impeçam a execução
