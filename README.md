# Cultura em Números — Eixo N 

Este repositório reúne os trabalhos desenvolvidos no **Eixo N** do projeto **Cultura em Números**.

Como o escopo temático e os produtos principais deste eixo ainda estão em definição, este documento apresenta a estrutura inicial do repositório, as responsabilidades das equipes e as regras de documentação, desenvolvimento e versionamento que deverão ser seguidas pelos colaboradores.

> **Atenção:** os campos indicados entre colchetes deverão ser atualizados quando o escopo do eixo for consolidado.

## 1. Identificação do eixo

* **Projeto:** Cultura em Números
* **Eixo:** Eixo N
* **Tema:** [inserir tema do eixo]
* **Objetivo geral:** [inserir objetivo geral]
* **Coordenação:** [inserir responsáveis]
* **Situação atual:** planejamento e definição do escopo
* **Versão mais recente:** ainda não publicada

## 2. Contexto

O projeto **Cultura em Números** está organizado em oito eixos temáticos, cada um desenvolvido em um repositório próprio.

O eixo N deverá reunir análises, bases derivadas, códigos, visualizações e demais produtos relacionados ao seu tema específico. Este repositório também deverá preservar a documentação necessária para que os trabalhos possam ser compreendidos, revisados, atualizados e reproduzidos por outros colaboradores.

Quando o escopo estiver definido, esta seção deverá apresentar:

* o problema ou tema investigado;
* a justificativa do eixo;
* as perguntas que orientam o trabalho;
* os públicos aos quais os produtos se destinam;
* a relação do eixo com os demais componentes do projeto Cultura em Números.

## 3. Objetivos

### Objetivo geral

[Descrever o principal objetivo do eixo N.]

### Objetivos específicos

* [Objetivo específico 1];
* [Objetivo específico 2];
* [Objetivo específico 3].

## 4. Fontes de dados

As fontes utilizadas deverão ser registradas nesta seção conforme forem definidas.

| Fonte           | Instituição responsável | Período de referência | Forma de acesso              | Observações   |
| --------------- | ----------------------- | --------------------- | ---------------------------- | ------------- |
| [Nome da fonte] | [Instituição]           | [Período]             | [API, arquivo, sistema etc.] | [Observações] |

Dados sigilosos, informações pessoais, credenciais, chaves de acesso e arquivos com restrição de publicação não deverão ser incluídos neste repositório.

## 5. Metodologia

A metodologia do eixo deverá ser descrita de forma geral nesta seção. A documentação detalhada dos códigos deverá permanecer no arquivo [`analytics/README.md`](analytics/README.md).

A descrição metodológica deverá informar, conforme aplicável:

* a unidade de análise;
* o período analisado;
* os critérios de seleção e exclusão;
* os procedimentos de tratamento dos dados;
* os indicadores produzidos;
* os métodos estatísticos ou analíticos empregados;
* as limitações conhecidas.

## 6. Estrutura do repositório

```text
cultura-em-numeros-eixo-n/
├── README.md
├── analytics/
│   └── README.md
└── data-viz/
    └── README.md
```

### `analytics/`

A pasta `analytics/` concentra os trabalhos da equipe de dados, incluindo:

* scripts de extração, transformação e carga;
* notebooks de exploração e análise;
* rotinas de limpeza e padronização;
* consultas;
* modelos analíticos;
* arquivos de configuração;
* documentação técnica;
* arquivos auxiliares necessários à reprodução das análises.

As instruções técnicas para configuração do ambiente, execução dos códigos e atualização dos dados deverão ser mantidas em [`analytics/README.md`](analytics/README.md).

### `data-viz/`

A pasta `data-viz/` concentra os trabalhos da equipe de visualização, incluindo:

* arquivos de painéis;
* códigos de aplicações;
* gráficos e elementos visuais;
* protótipos;
* arquivos de configuração;
* documentação de identidade visual;
* instruções de publicação e atualização;
* produtos finais destinados à apresentação dos resultados.

Quando houver códigos, aplicações ou procedimentos específicos de execução, a pasta deverá possuir seu próprio `README.md`.

## 7. Produtos previstos

Os produtos principais do Eixo n ainda não foram definidos. Quando houver definição, deverão ser registrados nesta seção.

Exemplos de produtos possíveis:

* bases de dados tratadas ou agregadas;
* indicadores;
* notas técnicas;
* relatórios analíticos;
* painéis de visualização;
* gráficos;
* mapas;
* aplicações;
* documentação metodológica.

## 8. Orientações para colaboradores

Antes de iniciar uma atividade:

1. consulte este `README.md`;
2. consulte o README técnico da pasta em que trabalhará;
3. verifique se já existe código, análise ou arquivo com a mesma finalidade;
4. confirme em qual branch a atividade deverá ser desenvolvida;
5. não inclua credenciais, dados sigilosos ou arquivos pessoais no repositório.

Durante o desenvolvimento:

* utilize nomes claros para arquivos, funções e variáveis;
* mantenha os códigos organizados por etapa ou finalidade;
* registre dependências e alterações relevantes;
* evite caminhos absolutos vinculados ao computador de uma pessoa;
* atualize a documentação sempre que alterar a estrutura ou o funcionamento do projeto;
* remova arquivos temporários antes de enviar alterações;
* preserve a rastreabilidade das fontes e das transformações realizadas.

## 9. Fluxo de contribuição

O fluxo recomendado de trabalho é:

1. atualizar a branch principal local;
2. criar uma branch específica para a atividade;
3. realizar as alterações;
4. revisar os arquivos modificados;
5. registrar um commit com mensagem clara;
6. enviar a branch ao GitHub;
7. abrir um pull request;
8. solicitar revisão;
9. incorporar as alterações após aprovação.

Exemplos de nomes de branches:

```text
feature/nova-analise
fix/correcao-indicador
docs/atualizacao-readme
refactor/reorganizacao-pipeline
```

Exemplos de mensagens de commit:

```text
feat: adiciona cálculo do indicador
fix: corrige filtro da base municipal
docs: atualiza instruções de execução
refactor: reorganiza pipeline de tratamento
```

## 10. Releases

Uma release deverá ser criada sempre que for concluída uma entrega utilizável, revisada e identificável do eixo N.

As versões deverão seguir o padrão:

```text
vMAJOR.MINOR.PATCH
```

Exemplos:

* `v1.0.0`: primeira entrega completa e estável;
* `v1.0.1`: correção pontual;
* `v1.1.0`: inclusão de nova análise ou funcionalidade;
* `v2.0.0`: alteração estrutural ou incompatível com versões anteriores.

Antes de publicar uma release, verifique se:

* as alterações foram incorporadas à branch principal;
* os códigos necessários estão versionados;
* os READMEs estão atualizados;
* os arquivos temporários e as credenciais foram removidos;
* a entrega foi revisada;
* a versão escolhida ainda não foi utilizada.

A descrição da release deverá informar:

* o objetivo da entrega;
* as principais alterações;
* os produtos incluídos;
* as orientações de reprodução e uso;
* as limitações e pendências;
* a versão anterior, quando houver.

A descrição deverá mencionar:

* [@gabrielribeirobizerril](https://github.com/gabrielribeirobizerril)
* [@LuizaMaluf](https://github.com/LuizaMaluf)

## 11. Limitações e pendências

* O tema específico do eixo N ainda deverá ser documentado;
* os objetivos gerais e específicos ainda deverão ser definidos;
* as fontes de dados ainda deverão ser registradas;
* os produtos principais ainda deverão ser estabelecidos;
* os responsáveis por cada frente de trabalho ainda deverão ser identificados.

## 12. Responsáveis pelo acompanhamento

Para acompanhamento do repositório:

* [@gabrielribeirobizerril](https://github.com/gabrielribeirobizerril)
* [@LuizaMaluf](https://github.com/LuizaMaluf)
