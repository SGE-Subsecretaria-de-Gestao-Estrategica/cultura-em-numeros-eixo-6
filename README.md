# Cultura em Números — Eixo 6

Documentação técnica dos scripts de tratamento, integração e produção de indicadores do **Eixo 6** do projeto **Cultura em Números**. O repositório reúne rotinas para análise do mercado de trabalho cultural e da Economia Criativa a partir de microdados da RAIS, do Novo CAGED e de indicadores de formalidade e informalidade do IBGE.

Este README descreve a finalidade dos grupos de scripts, fontes e arquivos auxiliares, encadeamento das etapas, produtos gerados, regras metodológicas observadas e pontos que devem ser conferidos ao atualizar as bases. Os caminhos absolutos indicados são os que aparecem nos scripts ou foram informados durante a revisão; eles refletem ambientes locais e podem precisar de ajuste em outra máquina.

## 1. Finalidade

Os códigos do Eixo 6 permitem:

- extrair e estruturar indicadores de formalidade e informalidade do setor cultural;
- calcular métricas anuais da RAIS e mensais do Novo CAGED;
- estimar vínculos e fluxos totais a partir de medidas de informalidade, quando previsto pelo respectivo pipeline;
- calcular índices de acompanhamento de vínculos e de remuneração;
- processar estabelecimentos da RAIS por natureza jurídica e porte;
- produzir perfis de trabalhadores da Economia Criativa por sexo, raça/cor, escolaridade, idade, deficiência, domínio cultural, porte e localização;
- exportar tabelas finais para análise, visualização e publicação, conforme autorização institucional.

Os grupos atualmente documentados são:

1. `INFORMALIDADE`
2. `RAIS_VINCULOS_2016-2025`
3. `RAIS_ESTABELECIMENTOS_2025`
4. `CAGED_2024_2026`
5. `RAIS_VINCULOS_2025`

## 2. Estrutura de pastas e arquivos

A estrutura abaixo representa a organização lógica dos grupos e uma proposta para organizar dados e saídas. Ela não significa que todos os scripts já utilizem caminhos relativos: muitos ainda contêm caminhos absolutos próprios.

```text
analytics/
├── README.md
├── requirements.txt
├── config/
├── CAGED_2024_2026/
├── INFORMALIDADE/
├── RAIS_ESTABELECIMENTOS_2025/
├── RAIS_VINCULOS_2016-2025/
├── RAIS_VINCULOS_2025/
├── data/
│   ├── raw/             # microdados e planilhas de origem
│   ├── external/        # CNAE, municípios, IPCA e outras tabelas auxiliares
│   └── processed/       # bases intermediárias
└── outputs/
    └── tables/          # tabelas finais, quando configuradas nesse local
```

| Componente | Função |
|---|---|
| `INFORMALIDADE/` | Extração e exportação de taxas e contagens de trabalhadores do IBGE. |
| `RAIS_VINCULOS_2016-2025/` | Métricas históricas anuais, integração com informações do IBGE e índices de acompanhamento. |
| `RAIS_ESTABELECIMENTOS_2025/` | Tratamento dos estabelecimentos e consolidações por natureza jurídica e porte. |
| `CAGED_2024_2026/` | Métricas mensais, integração de informalidade e cálculo do IRCA do CAGED. |
| `RAIS_VINCULOS_2025/` | Preparação da base de vínculos de 2025 e tabelas de perfil da força de trabalho. |
| `data/raw/` | Dados brutos recebidos ou baixados das fontes. |
| `data/external/` | Arquivos auxiliares usados em classificações e cruzamentos. |
| `data/processed/` | Bases intermediárias consumidas por etapas posteriores. |
| `outputs/tables/` | Diretório recomendado para os produtos finais; nos scripts revisados, diversos CSVs são gravados em `E:\Rais\Rais\csvs\`. |

> Microdados, arquivos intermediários extensos e arquivos sujeitos a restrições de uso não devem ser versionados sem autorização. A publicação de produtos finais também depende da verificação de sigilo, licenciamento e regras institucionais.

## 3. Tecnologias e dependências

Os scripts são escritos em Python e utilizam principalmente:

```text
pandas
numpy
openpyxl
xlrd
```

A necessidade de `openpyxl` e `xlrd` varia de acordo com o formato das planilhas lidas. As dependências e versões devem ser mantidas em `requirements.txt` para facilitar a reprodução. Exemplo de instalação:

```bash
pip install pandas numpy openpyxl xlrd
```

## 4. Ambiente, caminhos e configuração

### 4.1 Ambiente virtual

```bash
git clone https://github.com/SGE-Subsecretaria-de-Gestao-Estrategica/cultura-em-numeros-eixo-6.git
cd cultura-em-numeros-eixo-6/analytics
```

Ativação no Linux/macOS:

```bash
source .venv/bin/activate
```

Ativação no Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Instalação, caso exista um arquivo de dependências:

```bash
pip install -r requirements.txt
```

### 4.2 Caminhos locais observados

Os scripts usam caminhos de mais de um ambiente, entre eles:

- `E:\Rais\Rais\csvs\` para diversos CSVs finais;
- `E:\Rais\DF2\data` para bases intermediárias do processamento de estabelecimentos;
- `E:\Rais\DF5_DF6\data` para a base filtrada de vínculos RAIS 2025;
- `E:\Rais\CAGED\data` para bases intermediárias do CAGED;
- `D:\OneDrive\Minc\RAIS\RAIS_py\data\processed\` como caminho declarado por scripts analíticos da RAIS 2025.

Esses caminhos precisam existir e ser compatíveis entre as etapas. Em particular, a base filtrada de 2025 é gravada por `01_Filtro_2025.py` em um local diferente daquele declarado como entrada por vários scripts analíticos. Antes da execução em outro ambiente, alinhe explicitamente os caminhos de entrada e saída — não basta copiar o README ou criar diretórios vazios.

Como melhoria de manutenção, recomenda-se centralizar os caminhos em um arquivo local de configuração (não versionar dados pessoais ou credenciais) e substituir caminhos absolutos por `pathlib.Path` relativo ao projeto ou por variáveis de ambiente.

## 5. Fontes e entradas de dados

### 5.1 Fontes oficiais e auxiliares

| Identificador | Fonte | Acesso | Arquivos utilizados | Uso no pipeline |
| --- | --- | --- | --- | --- |
| `RAIS_VINCULOS` | Relação Anual de Informações Sociais — RAIS | [FTP do Ministério do Trabalho e Emprego](ftp://ftp.mtps.gov.br/pdet/microdados/) | Arquivos anuais de vínculos, incluindo arquivos `.txt` e `.COMT` | Métricas de emprego formal, massa salarial, perfis dos trabalhadores e indicadores da Economia Criativa |
| `RAIS_ESTABELECIMENTOS` | Relação Anual de Informações Sociais — RAIS | [FTP do Ministério do Trabalho e Emprego](ftp://ftp.mtps.gov.br/pdet/microdados/) | Arquivos anuais de estabelecimentos, incluindo `Estb2025ID.COMT` | Indicadores de estabelecimentos culturais por natureza jurídica e porte |
| `CAGED` | Novo CAGED | [FTP do Ministério do Trabalho e Emprego](ftp://ftp.mtps.gov.br/pdet/microdados/) | Arquivos mensais `CAGEDMOV`, `CAGEDFOR` e `CAGEDEXC` | Movimentações, fluxo salarial e índices mensais de acompanhamento |
| `INFORMALIDADE` | IBGE — Indicadores culturais | [Indicadores culturais do IBGE](https://www.ibge.gov.br/estatisticas/multidominio/cultura-recreacao-e-esporte/9388-indicadores-culturais.html) | Tabela 6.4 — *Ocupação no setor cultural (formal e informal)* | Taxas de formalidade e informalidade para estimativas de vínculos e fluxos totais |
| `CNAE_CULTURA` | Arquivo auxiliar do projeto | Arquivo local definido pelo usuário | `CNAE-ibge.xlsx` | Classificação de atividades da Economia Criativa e domínios culturais |
| `MUNICIPIOS` | Arquivo auxiliar do projeto | Arquivo local definido pelo usuário | `municipios.xlsx` | Associação entre códigos de municípios, UF, região e indicação de capital |
| `IPCA` | Arquivo auxiliar do projeto | Arquivo local definido pelo usuário | `IPCA_mensal.xls` | Deflação de valores salariais |

A tabela CNAE e a tabela de municípios são arquivos auxiliares locais. Não se deve presumir que todos os grupos usam a mesma versão ou a mesma estratégia de mapeamento: os detalhes abaixo distinguem as implementações verificadas.

### 5.2 Organização local sugerida dos dados

```text
data/
├── raw/
│   ├── rais/
│   │   ├── vinculos/
│   │   │   ├── 2016/
│   │   │   ├── 2017/
│   │   │   ├── 2018/
│   │   │   ├── 2019/
│   │   │   ├── 2020/
│   │   │   ├── 2021/
│   │   │   ├── 2022/
│   │   │   ├── 2023/
│   │   │   ├── 2024/
│   │   │   └── 2025/
│   │   └── estabelecimentos/
│   │       └── 2025/
│   ├── caged/
│   │   ├── 2024/
│   │   ├── 2025/
│   │   └── 2026/
│   └── informalidade/
│       └── Tabela 6.4.xlsx
├── external/
│   ├── CNAE-ibge.xlsx
│   ├── municipios.xlsx
│   └── IPCA_mensal.xls
└── processed/
```

## 6. Padrão dos arquivos finais

Para os CSVs finais, adota-se como padrão do projeto:

- separador de campos `;`;
- codificação `utf-8-sig`;
- ponto como separador decimal;
- ausência de notação científica;
- células vazias para valores ausentes;
- proporções percentuais na escala de 0 a 1, salvo indicação expressa de outra unidade, como taxa por mil trabalhadores;
- formato longo sempre que aplicável, com uma observação por linha e dimensões em colunas.

Os arquivos intermediários podem ter convenções diferentes, por exemplo, vírgula decimal em saídas de processamento histórico. Consulte a configuração do script antes de reutilizar um intermediário como se fosse um CSV final. Também há scripts que truncam casas decimais e outros que arredondam; o método específico é indicado nas seções do grupo.

## 7. Fluxo geral de execução

A ordem lógica recomendada, considerando as dependências entre bases, é:

```text
A. Preparar a base auxiliar de informalidade
   INFORMALIDADE/01_extrai_informalidade.py
   INFORMALIDADE/6_8.py e INFORMALIDADE/6_9.py

B. RAIS Vínculos 2025
   RAIS_VINCULOS_2025/01_Filtro_2025.py
   scripts analíticos 6.x (independentes entre si após a base filtrada)

C. RAIS Estabelecimentos 2025
   RAIS_ESTABELECIMENTOS_2025/02_estabelecimentos_2025.py
   RAIS_ESTABELECIMENTOS_2025/6_27.py

D. RAIS Vínculos 2016–2025
   01.2rais_metricas_grupos_2016-2025.py
   02adicionar_informalidade_metricas_2015_2025.py
   04_rais_IRCA_frentes.py
   scripts finais 6_5.py, 6_6.py, 6_7.py, 6_10.py e 6_17.py

E. CAGED 2024–2026
   01_caged_metricas_grupos_salario1M.py
   02_caged_adicionar_informalidade_1M.py
   03_caged_IRCA_frentes.py
   6_30.py
```

A ordem é por dependência de bases, não necessariamente por número de tabela. Antes de rodar uma etapa, confira os nomes de entrada configurados no próprio script, a disponibilidade da base anterior e os diretórios de saída. Os scripts `6.x` que partem da mesma base filtrada costumam ser independentes entre si.

## 8. Grupo `INFORMALIDADE`

### 8.1 Objetivo, período e unidade

O grupo extrai e organiza a Tabela 6.4 do IBGE para gerar uma base auxiliar de formalidade/informalidade e tabelas finais de série nacional, estados e municípios. A série utilizada cobre **2015–2024**; o ano 2014 é excluído. Grandes Regiões são ignoradas na estrutura usada pelo pipeline. Os recortes incluem `Total` e `Economia Criativa` e escalas nacional, estadual e municipal, conforme disponibilidade na fonte.

### 8.2 Scripts e produtos

| Script | Entrada | Operação | Produto |
|---|---|---|---|
| `01_extrai_informalidade.py` | Planilha da Tabela 6.4 do IBGE | Lê abas anuais, classifica escopo/escala/localidade e estrutura proporções e contagens. | `Informalidade2.xlsx` (base auxiliar). |
| `6_8.py` | `Informalidade2.xlsx` | Exporta a série nacional de taxa de informalidade para Brasil e Economia Criativa. | `6_8.csv`. |
| `6_9.py` | `Informalidade2.xlsx` | Exporta recortes de Economia Criativa para estados e municípios no ano de referência 2024. | `6.9.1.csv` (estadual) e `6.9.2.csv` (municipal). |

Os scripts finais de informalidade gravam em `E:\Rais\Rais\csvs\` no ambiente configurado.

### 8.3 Estrutura da base auxiliar

A saída estruturada `Informalidade2.xlsx` contém, além das dimensões, campos de proporção e contagem. Entre as colunas registradas estão:

| Campo | Significado |
|---|---|
| `Escopo` | Total ou Cultura/Economia Criativa, conforme o rótulo na origem. |
| `Escala` | Nacional, Estadual ou Municipal. |
| `Recorte` | Brasil, UF ou município. |
| `Formal - Total` | Proporção formal, em escala 0–1. |
| `Informal - Total` | Proporção informal, em escala 0–1. |
| `Trabalhadores - Total` | Contagem de trabalhadores totais; valores da fonte em milhares são convertidos para unidades. |
| `Trabalhadores - Cultura` | Contagem de trabalhadores da Cultura; valores da fonte em milhares são convertidos para unidades. |
| `Ano` | Ano de referência. |

Os nomes exatos devem ser preservados nos cruzamentos porque são usados por scripts posteriores. A planilha é ordenada por escopo, escala, recorte e ano decrescente.

### 8.4 Regras e mapeamentos

- Percentuais da tabela de origem são convertidos para proporções (0–1).
- As contagens apresentadas em milhares são multiplicadas por 1.000.
- Abas de coeficiente de variação e observações fora do período definido são descartadas.
- Quando “Rio de Janeiro” e “São Paulo” aparecem em mais de uma escala na planilha, a primeira ocorrência é interpretada como estadual e a segunda como municipal, conforme a lógica do extrator.
- `6_9.py` usa dicionários locais de códigos de UF e município para compor identificadores, não `municipios.xlsx`.
- Em `6_9.py`, o rótulo Cultura da origem é apresentado como `Economia Criativa`; os percentuais são exportados como proporções.

### 8.5 Colunas dos CSVs finais

- `6_8.csv`: `grupo`, `ano`, `taxa_informalidade`.
- `6.9.1.csv`: `grupo`, `uf`, `ano`, `pct_formal`, `pct_informal`.
- `6.9.2.csv`: `grupo`, `cod_ibge`, `ano`, `pct_formal`, `pct_informal`.

## 9. Grupo `RAIS_VINCULOS_2016-2025`

### 9.1 Objetivo e abrangência

Este grupo produz métricas históricas anuais de vínculos e remuneração, incorpora informações absolutas de trabalhadores do IBGE e calcula índices de acompanhamento. A série preparada começa em **2015** na etapa que integra os dados de informalidade; os arquivos RAIS e os períodos efetivamente disponíveis seguem os layouts e a configuração do processamento.

A deflação é referenciada a **2024**. No script de métricas, o IPCA anual é incorporado em um dicionário no próprio código, com 2024 como base 1,0; essa etapa não depende do arquivo `IPCA_mensal.xls` indicado em versões anteriores da documentação.

### 9.2 Scripts, entradas e saídas

| Script | Função | Entrada principal | Saída principal |
|---|---|---|---|
| `01.2rais_metricas_grupos_2016-2025.py` | Processa arquivos anuais, filtra vínculos ativos, cria recortes econômicos e geográficos e calcula contagens, massas e médias. | RAIS Vínculos anual; `CNAE-ibge.xlsx` quando previsto pela configuração. | `rais_metricas_grupos_2016_2025.csv` (base intermediária, caminho local definido no script). |
| `02adicionar_informalidade_metricas_2015_2025.py` | Integra as contagens absolutas do IBGE à base RAIS; renomeia a contagem RAIS e acrescenta totais IBGE. | Base de métricas RAIS; `Informalidade2.xlsx`. | `rais_metricas_grupos_2015_2025_com_informalidade.csv`. |
| `04_rais_IRCA_frentes.py` | Calcula índices de acompanhamento salarial e de vínculos e produz arquivo tabular e planilha com abas de recorte. | Base integrada `rais_metricas_grupos_2015_2025_com_informalidade.csv`. | `rais_IRCA_frentes.csv` e `rais_IRCA_frentes.xlsx`. |
| `6_5.py` | Série da Economia Criativa com total de vínculos baseado na contagem do IBGE e variação anual. | Base integrada/índice conforme configuração atual. | `6.5.csv`. |
| `6_6.py` | Participação da Economia Criativa no total de vínculos, usando valores de referência do IBGE. | Base integrada. | `6.6.csv`. |
| `6_7.py` | Série de vínculos RAIS para Economia Criativa, Agricultura, Indústria Extrativa e Construção Civil. | Base integrada. | `6.7.csv`. |
| `6_10.py` | Participação da Economia Criativa por capital e por UF no ano de referência. | Base integrada. | `6.10.1.csv` (capitais) e `6.10.2.csv` (UFs). |
| `6_17.py` | Série histórica de remuneração média deflacionada para grupos selecionados. | Base integrada de 2015–2025, conforme ajuste informado. | `6.17.csv`. |

Os arquivos finais são gravados no diretório configurado pelo script, observado como `E:\Rais\Rais\csvs\` para os produtos tabulares. As bases intermediárias e os produtos de índices podem estar em diretórios diferentes.

### 9.3 Métricas e recortes

A base de métricas contém, entre outros campos documentados, grupo, ano, total de vínculos, massa salarial nominal e deflacionada e remuneração média nominal e deflacionada. As médias são calculadas apenas quando a remuneração nominal é positiva. Os recortes incluem Brasil, Economia Criativa e grupos econômicos selecionados, além de UFs e capitais em recortes Total e Cultura/Economia Criativa.

A UF e a capital são derivadas de códigos municipais por dicionários internos (`UF_MAP` e `CAPITAIS`) nessa etapa; `municipios.xlsx` não é usado pelo script de métricas históricas descrito.

### 9.4 Integração de informalidade e IRCA

A versão atual da etapa de integração utiliza os **valores absolutos** do arquivo `Informalidade2.xlsx`:

- `Trabalhadores - Cultura` alimenta `total_vinculos_informais_estimado`;
- `Trabalhadores - Total` alimenta `total_vinculos_ibge`;
- `total_vinculos` da RAIS passa a ser identificado como `total_vinculos_rais`.

Portanto, não se deve descrever essa etapa como uma simples aplicação de percentuais para estimar informais. Também não se deve presumir que os valores de informalidade de 2024 sejam replicados para 2025: a versão registrada mantém 2025 sem esse preenchimento quando não há valor do IBGE correspondente.

O `04_rais_IRCA_frentes.py` produz os índices `IRCA_Salarial` e `IRCA_Vinculos`, com base **2024 = 1,0**, e calcula TF a partir da relação entre vínculos formais e formais mais informais estimados. Também gera uma planilha Excel com abas de recortes e resumo.

### 9.5 Produtos finais e unidades

- `6.5.csv`: série e variação anual de vínculos da Economia Criativa; proporções de variação em escala 0–1.
- `6.6.csv`: participação da Economia Criativa no total de vínculos; proporção em escala 0–1.
- `6.7.csv`: série por grupo econômico selecionado, baseada em `total_vinculos_rais`.
- `6.10.1.csv` e `6.10.2.csv`: participações geográficas, com código IBGE para capitais e sigla da UF para estados; participação em escala 0–1.
- `6.17.csv`: remuneração média deflacionada, com até três casas decimais na exportação conforme a implementação do script.

### 9.6 Observações operacionais

- `04_rais_IRCA_frentes.py` e `6_17.py` devem ler a base de 2015–2025, conforme correção informada durante a revisão.
- O nome do script de integração passou a usar o intervalo 2015–2025: `02adicionar_informalidade_metricas_2015_2025.py`.
- A base monetária é 2024; não confundir o índice com base 1,0 com séries percentuais.
- A série das variáveis do IBGE e a série da RAIS têm origens diferentes e devem ser identificadas separadamente na interpretação.
- Os códigos geográficos são tratados por dicionários internos neste grupo; essa regra não é automaticamente compartilhada por todos os demais scripts.

## 10. Grupo `RAIS_ESTABELECIMENTOS_2025`

### 10.1 Objetivo e fonte

Processa estabelecimentos da RAIS 2025 a partir de `Estb2025ID.COMT` e da tabela auxiliar `CNAE-ibge.xlsx`. O arquivo é lido em blocos de 300.000 linhas, com configuração de separador por vírgula e codificação `latin1` no script analisado. O filtro de RAIS negativa igual a `0` é aplicado às saídas do processamento.

### 10.2 Scripts e produtos

| Script | Função | Entrada | Saída |
|---|---|---|---|
| `02_estabelecimentos_2025.py` | Filtra registros válidos, identifica CNAEs culturais, normaliza códigos e gera bases por Cultura, natureza jurídica e porte do estabelecimento. | `Estb2025ID.COMT`; `CNAE-ibge.xlsx`. | `saida_1_estab_cultura_2025_base.csv`; `saida_2_brasil_natureza_juridica_categoria.csv`; `saida_3_brasil_tamanho_estabelecimento_categoria.csv`. |
| `6_27.py` | Usa a base indicada na configuração do próprio script, filtra 2025 e naturezas jurídicas empresariais, agrega porte e calcula participação. | `saida_1_estab_cultura_2016_2025_base.csv` (arquivo de entrada informado como já ajustado). | `6.27.csv`. |

As saídas intermediárias do script-base foram configuradas em `E:\Rais\DF2\data`; o produto `6.27.csv` é gravado em `E:\Rais\Rais\csvs\`.

> A base que `6_27.py` lê é a `saida_1_estab_cultura_2016_2025_base.csv`, conforme ajuste informado pelo usuário. Ela não deve ser confundida com a base 2025 que `02_estabelecimentos_2025.py` gera. Garanta que a base efetivamente lida exista e corresponda ao conteúdo que se deseja resumir.

### 10.3 Categorias

O script-base gera categorias de natureza jurídica, entre elas Administração Pública, Entidades Empresariais, Entidades sem Fins Lucrativos, Pessoas Físicas, Organizações Internacionais/Outras Instituições Extraterritoriais e Outros. A classificação é baseada nos códigos processados pelo script.

Para o porte original, os códigos representam faixas desde zero empregados até 1.000 ou mais. No produto final `6_27.py`, os códigos são agrupados em:

| Categoria do produto final | Códigos de porte considerados |
|---|---|
| Microempresa | 2–3 |
| Pequena Empresa | 4–5 |
| Média Empresa | 6 |
| Grande Empresa | 7–10 |

O código `1`, correspondente a zero empregados, é excluído da agregação final. `pct_participacao` é exportado como proporção 0–1; quando o denominador é zero, a célula fica vazia. O script utiliza truncamento decimal (ROUND_DOWN) para a participação, até cinco casas.

## 11. Grupo `CAGED_2024_2026`

### 11.1 Objetivo e período

O grupo calcula métricas mensais do Novo CAGED, integra estimativas de informalidade, reconstrói estoques e produz índices de acompanhamento para Brasil, Cultura/Economia Criativa, grupos econômicos e recortes geográficos configurados.

Embora alguns nomes de arquivos intermediários contenham `2016_2026`, a configuração analisada processa competências de **2024 a 2026**. O código inclui funções relacionadas ao CAGED legado, mas os anos 2016–2019 não fazem parte da lista configurada nessa execução.

A referência de deflação salarial é dezembro de 2024. A fonte e o caminho do IPCA devem ser conferidos na configuração ativa do script, pois o comentário/cabeçalho e o caminho definido podem divergir.

### 11.2 Scripts, entradas e saídas

| Script | Função | Entradas principais | Saída principal |
|---|---|---|---|
| `01_caged_metricas_grupos_salario1M.py` | Lê arquivos mensais MOV/FOR/EXC, calcula movimentações líquidas e métricas salariais por grupo e recorte. | Arquivos mensais do Novo CAGED; `CNAE-ibge.xlsx`; configuração/série IPCA. | `caged_metricas_grupos_2016_2026_salario1M.csv`. |
| `02_caged_adicionar_informalidade_1M.py` | Integra informações de informalidade e estima fluxo salarial total. | Base de métricas CAGED; `Informalidade2.xlsx`. | `caged_com_informalidade_2016_2026.csv`. |
| `03_caged_IRCA_frentes.py` | Reconstrói estoques e calcula IRCA de Vínculos e Salarial com dezembro de 2024 como referência. | Base CAGED com informalidade; dados de âncora RAIS e informalidade. | `caged_IRCA_final_2016_2026.csv`. |
| `6_30.py` | Seleciona Brasil e Cultura/Economia Criativa e exporta variações dos indicadores a partir de dezembro de 2024. | Base final do IRCA CAGED. | `6.30.csv`. |

As bases intermediárias são gravadas em `E:\Rais\CAGED\data`; `6.30.csv` é exportado em `E:\Rais\Rais\csvs\`.

### 11.3 Grupos e recortes

Os grupos nacionais configurados incluem Brasil, Cultura/Economia Criativa, Agricultura, Indústria Extrativa e Construção. Também são produzidos recortes de UFs e capitais, para Total e Cultura, de acordo com a seleção existente no código. A classificação de UF e capital usa mapeamentos internos.

### 11.4 Regras metodológicas

- Os arquivos de desligamento/EXC são incorporados com inversão de sinal para formar movimentações líquidas, conforme a lógica do script.
- Movimentações acima do limite salarial de R$ 1 milhão são mantidas na contagem de movimentações líquidas, mas excluídas dos cálculos de fluxo salarial e salário médio.
- O fluxo salarial é calculado a partir dos valores salariais e das movimentações; o script produz versões nominal e deflacionada.
- A etapa de informalidade replica os dados de 2024 para 2025 e 2026. Quando não há correspondência de informalidade, o fluxo formal é mantido como estimativa total.
- O `03_caged_IRCA_frentes.py` reconstrói estoques a partir das movimentações acumuladas e das âncoras da RAIS e usa a taxa de formalidade nacional da Cultura no ajuste descrito no código.
- `6_30.py` conserva observações a partir de dezembro de 2024. A variação é exportada como proporção 0–1, embora os nomes das colunas contenham `pct_`.

### 11.5 Campos produzidos

Entre os campos documentados nas bases intermediárias estão `grupo`, `ano`, `mes`, `competencia`, `movimentacoes_liquidas`, fluxo salarial nominal/deflacionado e salário médio de admissões nominal/deflacionado. A integração adiciona estimativas de fluxo total; o estágio de IRCA inclui estoques formais/estimados e índices de vínculos e salário. Verifique o cabeçalho efetivo do CSV antes de consumir ou renomear campos.

## 12. Grupo `RAIS_VINCULOS_2025`

### 12.1 Objetivo, fonte e preparação

Este grupo parte dos microdados de vínculos da RAIS 2025 para gerar uma base analítica e perfis de trabalhadores. O filtro lê seis arquivos regionais `.COMT`, em blocos de 300.000 linhas, seleciona vínculos ativos em 31/12 e prepara variáveis salariais e categóricas.

Arquivos regionais mencionados pelo pipeline:

- `RAIS_VINC_ID_CENTRO_OESTE_2025.COMT`
- `RAIS_VINC_ID_MG_ES_RJ_2025.COMT`
- `RAIS_VINC_ID_NORDESTE_2025.COMT`
- `RAIS_VINC_ID_NORTE_2025.COMT`
- `RAIS_VINC_ID_SP_2025.COMT`
- `RAIS_VINC_ID_SUL_2025.COMT`

### 12.2 Preparação da base: `01_Filtro_2025.py`

| Entrada | Operação | Saída |
|---|---|---|
| Seis arquivos regionais RAIS 2025 (`.COMT`). | Filtra vínculos ativos em 31/12, normaliza campos, calcula remuneração e massa salarial, cria variáveis deflacionadas e remove campos mensais que não serão usados nas análises. | `rais_2025_filtrado.csv`. |

O CNAE é normalizado para classe de cinco dígitos nessa etapa. A massa salarial nominal combina remunerações de janeiro a novembro (sem 13º) e dezembro nominal; a quantidade de meses com salário positivo também é calculada. A deflação de 2025 para preços de 2024 utiliza a taxa configurada de 4,26%. A base contém, entre outros, `massa_salarial`, `meses_com_salario`, `massa_salarial_deflacionada_2024` e `vl_rem_media_nom_deflacionada_2024`.

A saída é configurada em `E:\Rais\DF5_DF6\data`, com separador `;`, codificação `utf-8-sig` e configuração decimal própria do script. Vários scripts analíticos, por sua vez, declaram como entrada um caminho em `D:\OneDrive\Minc\RAIS\RAIS_py\data\processed\`. Esse desencontro de diretórios precisa ser resolvido na configuração antes da execução.

### 12.3 Inventário dos scripts e produtos

Os scripts de análise leem a base filtrada em blocos (em geral 300.000 linhas). Quando aplicável, usam `CNAE-ibge.xlsx` para selecionar CNAEs da Economia Criativa; os scripts por domínio também usam a coluna de domínio cultural. As saídas observadas são:

| Script | Recorte e operação | Saída final |
|---|---|---|
| `6_11.py` | Vínculos da Economia Criativa por 1.000 vínculos totais em cada município; usa CNAE e metadados municipais. | `6.11.csv`. |
| `6_12___6_19.py` | Economia Criativa por sexo: vínculos, participação e média salarial deflacionada. | `6.12.csv`. |
| `6_12B____6_19B.py` | Economia Total por sexo, sem filtro de CNAE criativo. | `6.12B_6.19B.csv`. |
| `6_13___6_21.py` | Economia Criativa por raça/cor: vínculos, participação e média salarial deflacionada. | `6.13.csv`. |
| `6_13B____6_21B.py` | Economia Total por raça/cor, sem filtro de CNAE criativo. | `6.13B_6.21B.csv`. |
| `6_14___6_23.py` | Economia Criativa por escolaridade. | `6.14.csv`. |
| `6_14B____6_23B.py` | Economia Total por escolaridade, sem filtro de CNAE criativo. | `6.14B_6.23B.csv`. |
| `6_15___6_24.py` | Economia Criativa por faixa etária. | `6.15.csv`. |
| `6_15B___6_24B.py` | Economia Total por faixa etária, sem filtro de CNAE criativo. | `6.15B_6.24B.csv`. |
| `6_16.py` | Participação/quantidade de vínculos com deficiência e médias salariais com/sem deficiência, em recortes Total e Economia Criativa. | `6.16.csv`. |
| `6_18.py` | Média salarial da Economia Criativa por UF e capital; inclui metadados regionais. | `6.18.csv`. |
| `6_20.py` | Média salarial da Economia Criativa por domínio cultural e sexo. | `6.20.csv`. |
| `6_22.py` | Média salarial da Economia Criativa por raça/cor e sexo. | `6.22.csv`. |
| `6_25___6_26.py` | Quantidade de vínculos e média salarial por domínio cultural. | `6.25_6.26.csv`. |
| `6_28___6_29.py` | Vínculos e média salarial por porte, em CNAEs criativos e naturezas jurídicas empresariais. | `6.28_6.29.csv`. |

Os nomes dos arquivos de saída acima refletem os nomes configurados nos scripts analisados. Os arquivos finais são gravados em `E:\Rais\Rais\csvs\`, salvo configuração local divergente.

### 12.4 Regras de classificação

#### Sexo

| Código | Categoria |
|---|---|
| 1 | Masculino |
| 2 | Feminino |

#### Raça/cor

| Código | Categoria |
|---|---|
| 1 | Indígena |
| 2 | Branca |
| 4 e 8 | Preta/Parda |
| 6 | Amarela |
| 9 e 99 | Não identificado |
| -1 | Ignorado |

Os scripts que fazem cruzamento por raça/cor e sexo exigem que as categorias estejam mapeadas; em `6_22.py`, a média utiliza salários positivos e válidos.

#### Escolaridade

O mapeamento em seis níveis agrupa os códigos da seguinte forma, conforme scripts de perfil:

| Código(s) | Categoria resumida |
|---|---|
| 1–4 | Sem instrução / Fundamental incompleto |
| 5–6 | Fundamental completo / Médio incompleto |
| 7–8 | Médio completo / Superior incompleto |
| 9 | Superior completo |
| 10–11 | Pós-graduação |
| -1 | Ignorado |

#### Faixa etária

| Faixa | Idade |
|---|---|
| Jovem | 15–29 |
| Adulto I | 30–44 |
| Adulto II | 45–59 |
| Idoso | 60 anos ou mais |

#### Porte nos vínculos

Em `6_28___6_29.py`, os códigos `2–3` formam Microempresa; `4–5`, Pequena Empresa; `6`, Média Empresa; `7–10`, Grande Empresa. O código `1` (zero empregados) é excluído. O script restringe o ano a 2025 e usa uma lista definida no próprio código para naturezas jurídicas empresariais.

### 12.5 Regras de cálculo e particularidades

- As médias dos scripts de perfil usam `vl_rem_media_nom_deflacionada_2024`, isto é, salários em preços de 2024, e geralmente consideram salários estritamente positivos.
- Algumas saídas de perfil agregam contagem de vínculos e participação; os scripts pares com `B` representam a Economia Total e os sem `B`, a Economia Criativa.
- Os scripts não têm todos o mesmo método de casas decimais: há implementações com arredondamento e outras com truncamento. A documentação não deve converter essa diferença em uma regra única.
- `6_16.py` trata como válidos registros com código de deficiência preenchido; código `1` é “com deficiência” e os demais códigos preenchidos entram como “sem deficiência”. O percentual usa os registros com código válido; médias consideram salários positivos.
- `6_18.py` possui mapas internos de prefixos de UF e capitais e também consulta `municipios.xlsx` para metadados. Não é a mesma implementação geográfica do grupo histórico, que deriva UF/capital por dicionários internos.
- `6_20.py` calcula remuneração por domínio cultural e sexo para categorias de sexo mapeadas.
- `6_22.py` usa as categorias de raça/cor e sexo indicadas acima e salários positivos válidos.
- `6_25___6_26.py` conta todos os vínculos atribuídos ao domínio, independentemente do salário; a média considera salários positivos. O script valida se cada CNAE corresponde a um único domínio e interrompe o processamento quando encontra associação conflitante.
- `6_28___6_29.py` conta registros após os filtros de ano, natureza jurídica, CNAE e porte; as médias salariais usam valores positivos.
- Os CNAEs são tratados em níveis de normalização diferentes conforme a etapa: o filtro principal trabalha com classe de cinco dígitos e scripts de perfil podem normalizar a comparação para sete dígitos. Confirme que os códigos usados nos cruzamentos são compatíveis com a tabela auxiliar vigente.

### 12.6 Metadados geográficos

`6_11.py` produz identificador municipal e taxa por mil trabalhadores, usando a classificação CNAE e `municipios.xlsx`; o código municipal é tratado em formato IBGE de sete dígitos quando disponível. `6_18.py` combina mapas próprios de capitais/UFs com consulta aos metadados municipais. Os scripts históricos e os scripts de informalidade, por outro lado, têm dicionários próprios para alguns recortes. Não substitua essas implementações por uma única tabela sem validar equivalência de códigos e cobertura.

## 13. Inventário consolidado de produtos finais

Os produtos finais identificados nesta documentação são:

| Grupo | Arquivos finais |
|---|---|
| `INFORMALIDADE` | `6_8.csv`, `6.9.1.csv`, `6.9.2.csv` |
| `RAIS_VINCULOS_2016-2025` | `6.5.csv`, `6.6.csv`, `6.7.csv`, `6.10.1.csv`, `6.10.2.csv`, `6.17.csv` |
| `RAIS_ESTABELECIMENTOS_2025` | `6.27.csv` |
| `CAGED_2024_2026` | `6.30.csv` |
| `RAIS_VINCULOS_2025` | `6.11.csv`, `6.12.csv`, `6.12B_6.19B.csv`, `6.13.csv`, `6.13B_6.21B.csv`, `6.14.csv`, `6.14B_6.23B.csv`, `6.15.csv`, `6.15B_6.24B.csv`, `6.16.csv`, `6.18.csv`, `6.20.csv`, `6.22.csv`, `6.25_6.26.csv`, `6.28_6.29.csv` |

Bases intermediárias relevantes incluem `Informalidade2.xlsx`, `rais_2025_filtrado.csv`, `rais_metricas_grupos_2015_2025_com_informalidade.csv`, `rais_IRCA_frentes.csv`, `rais_IRCA_frentes.xlsx`, bases de métricas e IRCA do CAGED e as três bases de estabelecimentos. A localização de cada uma é definida no script correspondente.

> O inventário descreve nomes configurados e informados durante a análise. Antes de uma publicação ou execução, valide no código se nome, local, cabeçalho e conteúdo continuam iguais à versão documentada.

## 14. Qualidade, validação e reprodução

Os scripts incluem, em graus diferentes, verificações de existência de arquivos, colunas obrigatórias, CNAEs sem correspondência, bases vazias e processamento em blocos. A execução em si não substitui a validação dos resultados. Recomenda-se registrar, para cada atualização:

- número de linhas lidas e mantidas em cada filtro;
- ano e período de referência efetivamente processados;
- contagem de CNAEs e municípios sem correspondência;
- contagens antes/depois de joins e filtros;
- duplicidades nas chaves de agregação;
- denominadores de percentuais e tratamento de denominador zero;
- conferência de totais com a fonte original;
- esquema e tipo das colunas das saídas;
- unidade dos salários e se os valores estão nominais ou deflacionados;
- convenção de decimal, separador e codificação do CSV final.

Nos arquivos de domínio cultural, confirme a unicidade da relação CNAE-domínio. Nos arquivos de municípios, confira códigos IBGE, UF e capital. Nos produtos de informalidade, valide separadamente proporções e contagens, pois têm unidades distintas.

## 15. Problemas conhecidos e cuidados de manutenção

| Ponto | Situação documentada | Ação antes da execução/publicação |
|---|---|---|
| Caminhos absolutos | Os grupos usam diretórios locais distintos em `E:\` e `D:\`. | Ajustar entradas e saídas no ambiente de execução; preferir configuração centralizada. |
| Informalidade histórica | A versão atual usa valores absolutos do IBGE em alguns produtos; lógica anterior baseada só em proporções não descreve a versão revisada. | Distinguir contagem IBGE, vínculo RAIS e estimativa de informalidade ao interpretar os campos. |
| CAGED | Nomes intermediários incluem 2016–2026, enquanto a lista de anos atual é 2024–2026. | Conferir a lista configurada e registrar as competências realmente processadas. |
| IPCA no CAGED | O comentário do script e o caminho efetivo da série podem divergir. | Conferir a configuração ativa e a referência de deflação. |
| CNAE | Há normalizações para cinco e sete dígitos conforme o grupo/script. | Validar chaves e nível de agregação antes de cruzar com a planilha auxiliar. |
| Mapas regionais | Alguns scripts usam dicionários internos; outros consultam `municipios.xlsx` ou combinam os dois. | Não assumir equivalência sem validar códigos, nomes e cobertura. |
| Casas decimais | Há saídas com truncamento e outras com arredondamento. | Preservar o comportamento específico do script e documentar alterações. |
| Dependência temporal | Scripts analíticos dependem das bases intermediárias das etapas anteriores. | Executar primeiro a etapa produtora e conferir data, período e caminho da base. |

As inconsistências de leitura dos arquivos 2015–2025 em `04_rais_IRCA_frentes.py` e `6_17.py` foram informadas como corrigidas. A leitura ajustada de `6_27.py` também foi informada. Esses pontos são registrados como resolvidos no código do usuário, sem dispensar a conferência da versão atualmente armazenada no repositório.

## 16. Recomendações de manutenção

- manter uma configuração única para diretórios e arquivos de entrada/saída;
- preservar a distinção entre bases brutas, intermediárias e produtos finais;
- parametrizar ano, período, diretório e versão de saída quando pertinente;
- manter um dicionário de dados para cada produto final;
- registrar em cada saída a unidade, período e referência monetária;
- padronizar identificadores geográficos e CNAE apenas depois de validar compatibilidade entre fontes;
- evitar edição manual de bases intermediárias sem rastreabilidade;
- documentar novas tabelas, filtros e mudanças metodológicas no mesmo ciclo da alteração do código;
- manter os CSVs finais em formato longo quando adequado à análise;
- não tratar `Cultura` e `Economia Criativa` como rótulos diferentes quando forem apenas a renomeação do mesmo escopo na saída — registrar explicitamente o caso.

## 17. Atualização das bases

### RAIS Vínculos

1. Obter os arquivos anuais ou regionais correspondentes ao período e layout desejados.
2. Armazenar os arquivos no diretório local configurado.
3. Atualizar/validar `CNAE-ibge.xlsx` e, nos scripts que usam, `municipios.xlsx`.
4. Executar o filtro ou processamento anual aplicável.
5. Executar a integração com informalidade e/ou índices apenas depois de conferir a base intermediária.
6. Executar os produtos `6.x` dependentes da série.
7. Conferir período, contagens, remuneração e padrões dos CSVs.

### RAIS Estabelecimentos

1. Disponibilizar `Estb2025ID.COMT` e a tabela CNAE no caminho configurado.
2. Executar `02_estabelecimentos_2025.py`.
3. Conferir as três bases intermediárias geradas.
4. Confirmar a base específica lida por `6_27.py` — `saida_1_estab_cultura_2016_2025_base.csv` na configuração informada.
5. Executar `6_27.py` e validar denominador e participação por porte.

### CAGED

1. Disponibilizar os arquivos mensais MOV/FOR/EXC do período configurado.
2. Confirmar o intervalo de competências ativo no script; a configuração revisada é 2024–2026.
3. Conferir a tabela CNAE, a série/caminho do IPCA e os arquivos de informalidade/âncora RAIS.
4. Executar os três estágios do pipeline em sequência.
5. Executar `6_30.py` e conferir a referência dezembro de 2024 e os recortes exportados.

### Informalidade

1. Obter a versão atualizada da Tabela 6.4 do IBGE.
2. Conferir abas, anos e posição das colunas esperadas pelo extrator.
3. Executar `01_extrai_informalidade.py`.
4. Validar proporções (0–1), contagens convertidas para unidades e classificação de escalas.
5. Executar `6_8.py` e `6_9.py` e validar os recortes nacional, estadual e municipal.

## 18. Proteção de dados e publicação

Antes de versionar arquivos, verificar:

- restrições de publicação dos microdados brutos;
- existência de dados pessoais ou identificáveis;
- licenças e termos de uso das fontes;
- tamanho e conteúdo das bases intermediárias;
- autorização para publicar os produtos finais.

Não versionar, salvo autorização expressa, microdados restritos, arquivos locais de configuração, credenciais ou bases intermediárias extensas. Revisar os arquivos efetivamente staged antes de cada commit.

## 19. Checklist de atualização

- [ ] O período processado está explícito e corresponde à configuração do script.
- [ ] Os arquivos brutos e auxiliares necessários estão disponíveis.
- [ ] Os caminhos de entrada e saída entre etapas estão alinhados.
- [ ] Os nomes e esquemas das colunas foram conferidos.
- [ ] Os filtros e regras de classificação foram documentados.
- [ ] A unidade dos percentuais, contagens e salários está identificada.
- [ ] A base monetária e o método de deflação foram conferidos.
- [ ] Os códigos CNAE e geográficos foram validados nos cruzamentos.
- [ ] Totais, denominadores, ausências e duplicidades foram revisados.
- [ ] Os CSVs seguem o padrão de saída do projeto.
- [ ] Os arquivos restritos não foram incluídos no versionamento.
- [ ] Este README foi atualizado junto com o código.

## 20. Responsáveis pelo acompanhamento

- [@gabrielribeirobizerril](https://github.com/gabrielribeirobizerril)
- [@LuizaMaluf](https://github.com/LuizaMaluf)
