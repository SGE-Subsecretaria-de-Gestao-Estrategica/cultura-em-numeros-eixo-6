# Eixo N — Documentação técnica de dados e análises

Este documento descreve a organização, a configuração e a execução dos códigos mantidos na pasta `analytics/` do repositório **cultura-em-numeros-eixo-2**.

Como a arquitetura técnica do eixo ainda está em definição, este README funciona como um modelo inicial. As seções deverão ser atualizadas à medida que scripts, notebooks, fontes de dados e produtos analíticos forem incorporados.

> **Atenção:** substitua os campos entre colchetes pelas informações específicas do projeto.

## 1. Finalidade da pasta

A pasta `analytics/` deverá concentrar os trabalhos da equipe de dados, incluindo:

* extração de dados;
* transformação e padronização;
* validação e controle de qualidade;
* integração entre fontes;
* análises exploratórias;
* produção de indicadores;
* análises estatísticas;
* exportação de bases derivadas;
* documentação técnica dos processos.

## 2. Estrutura recomendada

A estrutura poderá ser adaptada conforme a complexidade do eixo.

```text
analytics/
├── README.md
├── requirements.txt
├── .env.example
├── notebooks/
├── src/
│   ├── extraction/
│   ├── transformation/
│   ├── analysis/
│   └── utils/
├── data/
│   ├── external/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── outputs/
│   ├── tables/
│   ├── charts/
│   └── reports/
├── tests/
└── config/
```

### Descrição das pastas

| Pasta                 | Finalidade                                    |
| --------------------- | --------------------------------------------- |
| `notebooks/`          | Exploração, testes analíticos e demonstrações |
| `src/extraction/`     | Rotinas de extração e coleta                  |
| `src/transformation/` | Limpeza, padronização e integração            |
| `src/analysis/`       | Indicadores, estatísticas e análises          |
| `src/utils/`          | Funções auxiliares compartilhadas             |
| `data/raw/`           | Dados brutos, quando puderem ser versionados  |
| `data/interim/`       | Dados intermediários                          |
| `data/processed/`     | Dados tratados e prontos para análise         |
| `outputs/tables/`     | Tabelas produzidas                            |
| `outputs/charts/`     | Gráficos produzidos pela equipe de dados      |
| `outputs/reports/`    | Relatórios ou arquivos analíticos             |
| `tests/`              | Testes automatizados                          |
| `config/`             | Arquivos de configuração sem credenciais      |

A inclusão de dados no GitHub deverá respeitar as regras de sigilo, proteção de dados, licenciamento e limite de tamanho dos arquivos.

## 3. Tecnologias utilizadas

Preencha esta seção conforme o ambiente adotado.

* **Linguagem principal:** [Python, R ou outra]
* **Versão:** [versão da linguagem]
* **Gerenciador de dependências:** [pip, Poetry, Conda etc.]
* **Banco de dados:** [PostgreSQL, DuckDB, SQLite etc.]
* **Ferramentas adicionais:** [Jupyter, VS Code, Docker etc.]

## 4. Configuração do ambiente

### 4.1 Clonar o repositório

```bash
git clone https://github.com/SGE-Subsecretaria-de-Gestao-Estrategica/cultura-em-numeros-eixo-2.git
cd cultura-em-numeros-eixo-2/analytics
```

### 4.2 Criar um ambiente virtual

Exemplo com `venv`:

```bash
python -m venv .venv
```

Ativação no Linux ou macOS:

```bash
source .venv/bin/activate
```

Ativação no Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 4.3 Instalar as dependências

```bash
pip install -r requirements.txt
```

Caso o projeto utilize outra ferramenta, substitua essa instrução pelo comando correspondente.

## 5. Dependências

Todas as dependências necessárias deverão ser registradas em um arquivo próprio, como:

```text
requirements.txt
```

Exemplo:

```text
pandas
numpy
pyarrow
requests
openpyxl
jupyter
```

As versões deverão ser fixadas quando isso for necessário para garantir a reprodução dos resultados.

Exemplo:

```text
pandas==2.3.0
numpy==2.3.1
```

## 6. Variáveis de ambiente

Credenciais, senhas, tokens e chaves de acesso não deverão ser incluídos no GitHub.

Quando o projeto utilizar variáveis de ambiente, deverá existir um arquivo `.env.example` contendo apenas os nomes das variáveis:

```text
DATABASE_HOST=
DATABASE_PORT=
DATABASE_NAME=
DATABASE_USER=
DATABASE_PASSWORD=
API_TOKEN=
```

O arquivo `.env` real deverá ser incluído no `.gitignore`.

## 7. Fontes e entradas de dados

Registre todas as fontes utilizadas.

| Identificador | Fonte           | Arquivo ou acesso      | Período   | Responsável   | Observações   |
| ------------- | --------------- | ---------------------- | --------- | ------------- | ------------- |
| `[fonte_1]`   | [Nome da fonte] | [API, CSV, banco etc.] | [Período] | [Responsável] | [Observações] |

Para cada entrada, informe:

* a origem;
* a data de extração;
* o período de referência;
* o formato;
* a codificação;
* as variáveis principais;
* as restrições de uso;
* o procedimento de atualização.

## 8. Ordem de execução

Registre a sequência necessária para reprodução do processo.

Exemplo:

```text
1. src/extraction/01_extract_source_a.py
2. src/extraction/02_extract_source_b.py
3. src/transformation/01_clean_source_a.py
4. src/transformation/02_merge_sources.py
5. src/analysis/01_generate_indicators.py
6. src/analysis/02_export_outputs.py
```

Comandos de exemplo:

```bash
python src/extraction/01_extract_source_a.py
python src/transformation/01_clean_source_a.py
python src/analysis/01_generate_indicators.py
```

Quando houver notebooks, informe se eles são obrigatórios ou apenas exploratórios. Processos de produção deverão, preferencialmente, ser executáveis por scripts ou pipelines reproduzíveis.

## 9. Descrição dos códigos

Cada arquivo relevante deverá ser registrado na tabela abaixo.

| Arquivo        | Finalidade  | Entrada   | Saída   | Execução obrigatória |
| -------------- | ----------- | --------- | ------- | -------------------- |
| `[arquivo.py]` | [Descrição] | [Entrada] | [Saída] | Sim/Não              |

Funções complexas deverão possuir docstrings contendo:

* finalidade;
* parâmetros;
* tipos dos parâmetros;
* retorno;
* exceções relevantes;
* exemplo de uso, quando necessário.

## 10. Entradas e saídas

### Entradas

| Arquivo ou tabela | Localização | Descrição   |
| ----------------- | ----------- | ----------- |
| [entrada]         | [caminho]   | [descrição] |

### Saídas

| Arquivo ou tabela | Localização | Descrição   |
| ----------------- | ----------- | ----------- |
| [saída]           | [caminho]   | [descrição] |

Os arquivos gerados deverão possuir nomes claros e, quando pertinente, data ou versão.

Exemplo:

```text
indicadores_eixo_2__2026-07-20.csv
```

## 11. Convenções de código

Os colaboradores deverão observar as seguintes convenções:

* utilizar nomes claros para variáveis, funções e arquivos;
* evitar código duplicado;
* transformar trechos reutilizáveis em funções;
* utilizar caminhos relativos;
* registrar parâmetros em arquivos de configuração quando apropriado;
* evitar alterações manuais não documentadas nas bases;
* incluir tratamento de erros nas etapas críticas;
* preservar a rastreabilidade entre fonte, transformação e resultado;
* remover células temporárias e códigos de teste antes da entrega;
* manter notebooks organizados e executáveis do início ao fim.

## 12. Qualidade e validação

Cada pipeline deverá incluir verificações compatíveis com o tipo de dado processado.

Exemplos:

* quantidade de linhas antes e depois das transformações;
* identificação de duplicidades;
* validação de chaves;
* análise de valores ausentes;
* validação de tipos;
* conferência de totais;
* verificação de intervalos válidos;
* comparação com fontes oficiais;
* registro de perdas decorrentes de filtros ou junções.

As validações relevantes deverão ser documentadas no código ou em arquivo específico.

## 13. Testes

Quando houver testes automatizados, execute:

```bash
pytest
```

Os testes poderão abranger:

* funções de transformação;
* regras de classificação;
* cálculos de indicadores;
* validação de esquemas;
* tratamento de casos extremos;
* integridade das saídas.

## 14. Atualização das bases

Para cada fonte, documente:

1. onde obter os dados;
2. quais credenciais são necessárias;
3. qual período deverá ser extraído;
4. quais arquivos deverão ser substituídos;
5. quais scripts deverão ser executados;
6. quais validações deverão ser realizadas;
7. quais produtos deverão ser atualizados.

Modelo:

```text
Fonte: [nome]
Periodicidade: [mensal, anual etc.]
Última atualização: [data]
Responsável: [nome ou usuário]
Procedimento: [descrição]
```

## 15. Proteção de dados e segurança

Não deverão ser versionados:

* senhas;
* tokens;
* chaves de API;
* arquivos `.env`;
* dados pessoais identificáveis;
* bases sigilosas;
* arquivos recebidos sob restrição;
* informações protegidas por acordo institucional.

Antes de enviar alterações, execute:

```bash
git status
```

Revise todos os arquivos listados e confirme que nenhum conteúdo restrito será publicado.

## 16. Problemas conhecidos

| Problema   | Causa provável | Solução   |
| ---------- | -------------- | --------- |
| [Problema] | [Causa]        | [Solução] |

Inclua nesta seção erros recorrentes, incompatibilidades de versão, limitações das fontes e procedimentos alternativos.

## 17. Como contribuir

Antes de alterar os códigos:

1. atualize sua branch principal;
2. crie uma branch para a atividade;
3. consulte este README;
4. verifique as dependências;
5. preserve a estrutura existente;
6. documente novos scripts e saídas;
7. abra um pull request ao concluir.

Exemplos de branches:

```text
feature/pipeline-fonte-a
fix/correcao-classificacao
docs/documentacao-execucao
refactor/padronizacao-funcoes
```

## 18. Checklist para entrega

Antes de concluir uma atividade, confirme:

* [ ] o código executa sem erros;
* [ ] as dependências foram atualizadas;
* [ ] não há caminhos absolutos pessoais;
* [ ] não há credenciais no repositório;
* [ ] os arquivos temporários foram removidos;
* [ ] as entradas e saídas estão documentadas;
* [ ] a ordem de execução está atualizada;
* [ ] as validações foram realizadas;
* [ ] o README foi atualizado;
* [ ] o pull request está pronto para revisão.

## 19. Responsáveis pelo acompanhamento

Para acompanhamento técnico:

* [@gabrielribeirobizerril](https://github.com/gabrielribeirobizerril)
* [@LuizaMaluf](https://github.com/LuizaMaluf)
  ::: 
