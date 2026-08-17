# Cultura em Números — Eixo 6 

Este repositório reúne os trabalhos desenvolvidos no **Eixo 6** do projeto **Cultura em Números**.

Este repositório reúne scripts para tratamento, integração e produção de indicadores derivados de bases administrativas e pesquisas sobre mercado de trabalho, com foco na Economia Criativa.

Os códigos estão organizados em cinco grupos:

1. `CAGED_2024_2026`
2. `INFORMALIDADE`
3. `RAIS_ESTABELECIMENTOS_2025`
4. `RAIS_VINCULOS_2016-2025`
5. `RAIS_VINCULOS_2025`

Este README documenta as fontes, a lógica de processamento, a ordem de execução, os arquivos de entrada e saída e as observações relevantes para reprodução dos resultados.

## 1. Finalidade

Os scripts do repositório permitem:

- processar microdados do CAGED;
- calcular métricas de movimentação e fluxo salarial;
- aplicar deflação monetária com base no IPCA;
- extrair e estruturar taxas de formalidade e informalidade;
- incorporar estimativas de informalidade ao pipeline do CAGED e da RAIS;
- reconstruir estoques de vínculos e massa salarial;
- calcular o índice de acompanhamento salarial e de vínculos;
- processar dados de estabelecimentos da RAIS por natureza jurídica e porte;
- produzir perfis de vínculos da Economia Criativa por sexo, raça/cor, escolaridade, faixa etária, deficiência, porte, domínio cultural e geografia;
- exportar CSVs finais para uso em tabelas, painéis, relatórios e visualizações.

## 2. Estrutura de pastas e arquivos

A estrutura abaixo é uma sugestão de organização do repositório e dos dados locais. Os scripts atualmente possuem caminhos absolutos do ambiente original de desenvolvimento, mas recomenda-se fortemente a adoção de caminhos configuráveis.

```text
analytics/
├── README.md
├── requirements.txt
├── .gitignore
├── config/
│   └── paths.example.py
├── CAGED_2024_2026/
│   ├── 01_caged_metricas_grupos_salario1M.py
│   ├── 02_caged_adicionar_informalidade_1M.py
│   ├── 03_caged_IRCA_frentes.py
│   └── 6_30.py
├── INFORMALIDADE/
│   ├── 01_extrai_informalidade.py
│   ├── 6_8.py
│   └── 6_9.py
├── RAIS_ESTABELECIMENTOS_2025/
│   ├── 02_estabelecimentos_2025.py
│   └── 6_27.py
├── RAIS_VINCULOS_2016-2025/
│   ├── 01.2rais_metricas_grupos_2016-2025.py
│   ├── 02adicionar_informalidade_metricas_2016_2025.py.py
│   ├── 04_rais_IRCA_frentes.py
│   ├── 6_5.py
│   ├── 6_6.py
│   ├── 6_7.py
│   ├── 6_10.py
│   └── 6_17.py
├── RAIS_VINCULOS_2025/
│   ├── 01_Filtro_2025.py
│   ├── 6_11.py
│   ├── 6_12___6_19.py
│   ├── 6_13___6_21.py
│   ├── 6_14___6_23.py
│   ├── 6_15___6_24.py
│   ├── 6_16.py
│   ├── 6_18.py
│   ├── 6_20.py
│   ├── 6_22.py
│   ├── 6_25___6_26.py
│   └── 6_28___6_29.py
├── data/
│   ├── raw/
│   │   ├── rais/
│   │   │   ├── vinculos/
│   │   │   └── estabelecimentos/
│   │   ├── caged/
│   │   └── informalidade/
│   ├── external/
│   │   ├── CNAE-ibge.xlsx
│   │   ├── municipios.xlsx
│   │   └── IPCA_mensal.xls
│   └── processed/
│       ├── rais_2025_filtrado.csv
│       ├── rais_metricas_grupos_2016_2025.csv
│       ├── rais_metricas_grupos_2016_2025_com_informalidade.csv
│       ├── rais_IRCA_frentes.csv
│       ├── caged_metricas_grupos_2016_2026_salario1M.csv
│       ├── caged_com_informalidade_2016_2026.csv
│       ├── caged_indice_final_2016_2026.csv
│       └── [demais bases intermediárias]
└── outputs/
    └── tables/
        ├── 6_5.csv
        ├── 6_6.csv
        ├── 6.7.csv
        ├── 6_8.csv
        ├── 6.9.1.csv
        ├── 6.9.2.csv
        ├── 6.10.1.csv
        ├── 6.10.2.csv
        ├── 6.12.csv
        ├── 6.13.csv
        ├── 6.14.csv
        ├── 6.15.csv
        ├── 6.16.csv
        ├── 6.17.csv
        ├── 6.18.csv
        ├── 6.20.csv
        ├── 6.23.csv
        ├── 6.26.csv
        ├── 6.28.csv
        ├── 6.29_6.30.csv
        ├── 6.31.csv
        └── ec_por_1000_trabalhadores_municipios.csv
```

### Descrição das pastas

| Pasta | Finalidade |
| --- | --- |
| `CAGED_2024_2026/` | Scripts de processamento e indicadores mensais do CAGED |
| `INFORMALIDADE/` | Scripts de extração e exportação das taxas de formalidade e informalidade |
| `RAIS_ESTABELECIMENTOS_2025/` | Scripts de processamento dos estabelecimentos da RAIS 2025 |
| `RAIS_VINCULOS_2016-2025/` | Scripts de métricas históricas anuais da RAIS e índices de acompanhamento |
| `RAIS_VINCULOS_2025/` | Scripts de filtragem e perfis analíticos dos vínculos RAIS 2025 |
| `data/raw/` | Dados brutos baixados das fontes oficiais |
| `data/external/` | Arquivos auxiliares locais usados nos cruzamentos e classificações |
| `data/processed/` | Bases intermediárias geradas pelos scripts |
| `outputs/tables/` | CSVs finais gerados pelos scripts `6.x`, passíveis de versionamento no GitHub |
| `config/` | Arquivos-modelo de configuração de caminhos locais |

> Recomenda-se que `data/raw/` e `data/processed/` não sejam versionados quando contiverem microdados, arquivos grandes ou material sujeito a restrições de uso. Os produtos finais em `outputs/tables/` podem ser publicados quando autorizados.

## 3. Tecnologias e dependências

Os scripts documentados utilizam Python e as bibliotecas abaixo:

```text
pandas
numpy
openpyxl
xlrd
```

Exemplo de instalação:

```bash
pip install pandas numpy openpyxl xlrd
```

As versões podem ser fixadas no `requirements.txt` quando necessário para garantir reprodutibilidade.

## 4. Configuração do ambiente

### 4.1 Clonar o repositório

```bash
git clone https://github.com/SGE-Subsecretaria-de-Gestao-Estrategica/cultura-em-numeros-eixo-6.git
cd cultura-em-numeros-eixo-6/analytics
```

### 4.2 Criar um ambiente virtual

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

### 4.3 Instalar dependências

```bash
pip install -r requirements.txt
```

## 5. Caminhos configuráveis

Os scripts, na forma atual, utilizam caminhos absolutos do ambiente original de desenvolvimento. Para tornar o projeto reproduzível em outros computadores, recomenda-se substituir esses caminhos por variáveis de configuração locais.

Exemplo de arquivo de configuração:

```python
from pathlib import Path

DATA_DIR = Path("C:/caminho/local/para/dados")

RAIS_VINCULOS_DIR = DATA_DIR / "raw" / "rais" / "vinculos"
RAIS_ESTABELECIMENTOS_DIR = DATA_DIR / "raw" / "rais" / "estabelecimentos"
CAGED_DIR = DATA_DIR / "raw" / "caged"
INFORMALIDADE_DIR = DATA_DIR / "raw" / "informalidade"

EXTERNAL_DIR = DATA_DIR / "external"
CNAE_PATH = EXTERNAL_DIR / "CNAE-ibge.xlsx"
MUNICIPIOS_PATH = EXTERNAL_DIR / "municipios.xlsx"
IPCA_PATH = EXTERNAL_DIR / "IPCA_mensal.xls"

PROCESSED_DIR = Path("data/processed")
OUTPUTS_DIR = Path("outputs/tables")
```

Recomenda-se manter no repositório apenas um arquivo-modelo, como `config/paths.example.py`, e ignorar o arquivo local real no `.gitignore`.

## 6. Fontes e entradas de dados

### 6.1 Fontes oficiais e auxiliares

| Identificador | Fonte | Acesso | Arquivos utilizados | Uso no pipeline |
| --- | --- | --- | --- | --- |
| `RAIS_VINCULOS` | Relação Anual de Informações Sociais — RAIS | [FTP do Ministério do Trabalho e Emprego](ftp://ftp.mtps.gov.br/pdet/microdados/) | Arquivos anuais de vínculos, incluindo arquivos `.txt` e `.COMT` | Métricas de emprego formal, massa salarial, perfis dos trabalhadores e indicadores da Economia Criativa |
| `RAIS_ESTABELECIMENTOS` | Relação Anual de Informações Sociais — RAIS | [FTP do Ministério do Trabalho e Emprego](ftp://ftp.mtps.gov.br/pdet/microdados/) | Arquivos anuais de estabelecimentos, incluindo `Estb2025ID.COMT` | Indicadores de estabelecimentos culturais por natureza jurídica e porte |
| `CAGED` | Novo CAGED | [FTP do Ministério do Trabalho e Emprego](ftp://ftp.mtps.gov.br/pdet/microdados/) | Arquivos mensais `CAGEDMOV`, `CAGEDFOR` e `CAGEDEXC` | Movimentações, fluxo salarial e índices mensais de acompanhamento |
| `INFORMALIDADE` | IBGE — Indicadores culturais | [Indicadores culturais do IBGE](https://www.ibge.gov.br/estatisticas/multidominio/cultura-recreacao-e-esporte/9388-indicadores-culturais.html) | Tabela 6.4 — *Ocupação no setor cultural (formal e informal)* | Taxas de formalidade e informalidade para estimativas de vínculos e fluxos totais |
| `CNAE_CULTURA` | Arquivo auxiliar do projeto | Arquivo local definido pelo usuário | `CNAE-ibge.xlsx` | Classificação de atividades da Economia Criativa e domínios culturais |
| `MUNICIPIOS` | Arquivo auxiliar do projeto | Arquivo local definido pelo usuário | `municipios.xlsx` | Associação entre códigos de municípios, UF, região e indicação de capital |
| `IPCA` | Arquivo auxiliar do projeto | Arquivo local definido pelo usuário | `IPCA_mensal.xls` | Deflação de valores salariais |

### 6.2 Organização local sugerida dos dados

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

## 7. Ordem geral de execução

A execução recomendada do repositório é:

```text
1. INFORMALIDADE/01_extrai_informalidade.py
2. INFORMALIDADE/6_8.py
3. INFORMALIDADE/6_9.py

4. RAIS_VINCULOS_2025/01_Filtro_2025.py
5. RAIS_VINCULOS_2025/[scripts 6_x]

6. RAIS_ESTABELECIMENTOS_2025/02_estabelecimentos_2025.py
7. RAIS_ESTABELECIMENTOS_2025/6_27.py

8. RAIS_VINCULOS_2016-2025/01.2rais_metricas_grupos_2016-2025.py
9. RAIS_VINCULOS_2016-2025/02adicionar_informalidade_metricas_2016_2025.py.py
10. RAIS_VINCULOS_2016-2025/04_rais_IRCA_frentes.py
11. RAIS_VINCULOS_2016-2025/[scripts 6_x]

12. CAGED_2024_2026/01_caged_metricas_grupos_salario1M.py
13. CAGED_2024_2026/02_caged_adicionar_informalidade_1M.py
14. CAGED_2024_2026/03_caged_IRCA_frentes.py
15. CAGED_2024_2026/6_30.py
```

> Alguns scripts `6.x` são independentes entre si, desde que o arquivo-base intermediário já tenha sido gerado.

## 8. Entradas e saídas

### 8.1 Entradas

| Tipo | Diretório sugerido | Conteúdo |
| --- | --- | --- |
| Dados brutos | `data/raw/` | Microdados de RAIS, CAGED e planilha de informalidade baixados das fontes oficiais |
| Dados auxiliares | `data/external/` | CNAEs culturais, municípios e IPCA |
| Dados intermediários | `data/processed/` | Bases tratadas produzidas por etapas anteriores |

### 8.2 Saídas

| Tipo | Diretório sugerido | Conteúdo | Versionamento |
| --- | --- | --- | --- |
| Bases intermediárias | `data/processed/` | CSVs e planilhas utilizados por scripts subsequentes | Em geral, não recomendado |
| Produtos finais | `outputs/tables/` | CSVs analíticos produzidos pelos scripts `6.x` | Sim, quando autorizada a publicação |

Os CSVs finais esperados incluem:

```text
6_5.csv
6_6.csv
6.7.csv
6_8.csv
6.9.1.csv
6.9.2.csv
6.10.1.csv
6.10.2.csv
6.12.csv
6.13.csv
6.14.csv
6.15.csv
6.16.csv
6.17.csv
6.18.csv
6.20.csv
6.23.csv
6.26.csv
6.28.csv
6.29_6.30.csv
6.31.csv
ec_por_1000_trabalhadores_municipios.csv
```

## 9. Grupo `CAGED_2024_2026`

### 9.1 Finalidade

Este grupo processa dados mensais do Novo CAGED para gerar métricas de movimentação, fluxo salarial e índices de acompanhamento para o Brasil, a Economia Criativa, Unidades da Federação e capitais.

O pipeline executa quatro etapas:

1. consolidação das métricas do CAGED por grupo;
2. aplicação de fatores de expansão associados à informalidade;
3. cálculo do índice de acompanhamento salarial e de vínculos;
4. exportação de variações percentuais para Brasil e Economia Criativa.

### 9.2 Fontes de dados

| Fonte | Arquivo ou estrutura esperada | Uso no processo |
| --- | --- | --- |
| Novo CAGED | Arquivos mensais `CAGEDMOVAAAAMM`, `CAGEDFORAAAAMM` e `CAGEDEXCAAAAMM` | Movimentações mensais de vínculos e salários |
| CNAEs da cultura | `CNAE-ibge.xlsx` | Identificação das atividades classificadas como Cultura |
| IPCA mensal | `IPCA_mensal.xls` | Deflação dos valores salariais |
| Informalidade | `Informalidade2.xlsx` | Estimativa de fluxos e estoques totais a partir da formalidade |
| RAIS 2024 | `rais_cultura_uf_capitais_2024.csv` | Âncoras de estoque de vínculos e massa salarial em dezembro de 2024 |

### 9.3 Período processado

A configuração atual processa competências mensais entre **janeiro de 2024 e dezembro de 2026**, conforme disponibilidade dos arquivos de origem.

A base monetária para deflação é **dezembro de 2024**.

### 9.4 Grupos e recortes gerados

O processamento gera métricas para os seguintes grupos nacionais:

- `Brasil`;
- `Economia Criativa`;
- `Agricultura, pecuária, produção florestal, pesca e aquicultura`;
- `Indústria extrativa`;
- `Construção`.

Também são produzidos recortes para:

- todas as Unidades da Federação, para `Total` e `Economia Criativa`;
- todas as capitais estaduais e o Distrito Federal, para `Total` e `Economia Criativa`.

### 9.5 Ordem de execução

```text
1. 01_caged_metricas_grupos_salario1M.py
2. 02_caged_adicionar_informalidade_1M.py
3. 03_caged_IRCA_frentes.py
4. 6_30.py
```

### 9.6 Descrição dos scripts

| Arquivo | Finalidade | Entradas principais | Saída |
| --- | --- | --- | --- |
| `01_caged_metricas_grupos_salario1M.py` | Lê os arquivos mensais do CAGED, classifica registros por grupos econômicos e geográficos e calcula movimentações líquidas, fluxo salarial e salário médio de admissão. | Arquivos mensais do CAGED; `CNAE-ibge.xlsx`; `IPCA_mensal.xls` | `data/processed/caged_metricas_grupos_2016_2026_salario1M.csv` |
| `02_caged_adicionar_informalidade_1M.py` | Integra percentuais de formalidade e informalidade às métricas do CAGED e estima o fluxo salarial total. | `caged_metricas_grupos_2016_2026_salario1M.csv`; `Informalidade2.xlsx` | `data/processed/caged_com_informalidade_2016_2026.csv` |
| `03_caged_IRCA_frentes.py` | Reconstrói estoques formais, estima vínculos totais e calcula o índice de acompanhamento de vínculos e salarial, com base 100 em dezembro de 2024. | `caged_com_informalidade_2016_2026.csv`; `rais_cultura_uf_capitais_2024.csv`; `Informalidade2.xlsx` | `data/processed/caged_indice_final_2016_2026.csv` |
| `6_30.py` | Seleciona Brasil e Cultura, renomeia Cultura como Economia Criativa e exporta as variações percentuais dos índices a partir de dezembro de 2024. | `caged_indice_final_2016_2026.csv` | `outputs/tables/6.31.csv` |

### 9.7 Fluxo de dados

```text
Arquivos mensais do CAGED
        │
        ├── CNAE-ibge.xlsx
        ├── IPCA_mensal.xls
        │
        ▼
caged_metricas_grupos_2016_2026_salario1M.csv
        │
        ├── Informalidade2.xlsx
        │
        ▼
caged_com_informalidade_2016_2026.csv
        │
        ├── rais_cultura_uf_capitais_2024.csv
        ├── Informalidade2.xlsx
        │
        ▼
caged_indice_final_2016_2026.csv
        │
        ▼
outputs/tables/6.31.csv
```

### 9.8 Métricas produzidas

| Variável | Descrição |
| --- | --- |
| `grupo` | Grupo econômico ou recorte geográfico analisado |
| `ano` | Ano da competência |
| `mes` | Mês da competência |
| `competencia` | Identificador no formato `AAAAMM` |
| `movimentacoes_liquidas` | Saldo líquido de movimentações |
| `fluxo_salarial_nom` | Soma nominal de salário multiplicado pelo saldo de movimentação |
| `fluxo_salarial_def` | Fluxo salarial deflacionado |
| `salario_medio_adm_nom` | Salário médio nominal das admissões |
| `salario_medio_adm_def` | Salário médio das admissões deflacionado |

O segundo script adiciona:

| Variável | Descrição |
| --- | --- |
| `fluxo_salarial_nom_total` | Estimativa do fluxo salarial nominal total |
| `fluxo_salarial_def_total` | Estimativa do fluxo salarial total deflacionado |

O terceiro script produz adicionalmente:

| Variável | Descrição |
| --- | --- |
| `estoque_vin_formal` | Estoque formal estimado de vínculos |
| `vinculos_total_estimado` | Estoque total estimado de vínculos |
| `indice_vinculos` | Índice de acompanhamento de vínculos |
| `estoque_sal_formal` | Estoque formal estimado de massa salarial |
| `massa_ajustada` | Massa salarial ajustada |
| `indice_salarial` | Índice de acompanhamento salarial |

### 9.9 Regras de cálculo relevantes

#### Deflação

Os valores salariais são deflacionados com base na série de IPCA e têm como referência dezembro de 2024.

#### Informalidade

O fator de expansão utilizado é:

$$
\text{fator de informalidade} = \frac{\text{percentual formal} + \text{percentual informal}}{\text{percentual formal}}
$$

#### Índice de acompanhamento

O índice de acompanhamento utiliza dezembro de 2024 como referência, com valor igual a 100 nessa competência.

### 9.10 Validações e observações

- verificação da existência de arquivos e pastas de entrada;
- identificação flexível de nomes de colunas;
- tentativa alternativa de codificação entre UTF-8 e Latin-1;
- processamento em blocos;
- avisos para arquivos mensais ausentes;
- dependência do arquivo `rais_cultura_uf_capitais_2024.csv`, produzido no pipeline de RAIS 2025;
- replicação das taxas de informalidade de 2024 para 2025 e 2026.

## 10. Grupo `INFORMALIDADE`

### 10.1 Finalidade

Este grupo extrai e estrutura taxas de formalidade e informalidade a partir da **Tabela 6.4** do IBGE e produz arquivos auxiliares utilizados nos pipelines do CAGED e da RAIS, além de CSVs finais para visualização.

### 10.2 Fontes de dados

| Fonte | Arquivo | Uso |
| --- | --- | --- |
| IBGE — Tabela 6.4 | `Tabela 6.4.xlsx` | Taxas de formalidade e informalidade por localidade e setor, 2015–2024 |

### 10.3 Período processado

Os dados cobrem o período de **2015 a 2024**. O ano de referência dos recortes exportados em `6_9.py` é **2024**.

### 10.4 Escalas e escopos

Cada localidade é classificada em uma das escalas:

- `Nacional`
- `Estadual`
- `Municipal`

Cada localidade gera dois escopos:

- `Total`
- `Economia Criativa`

### 10.5 Ordem de execução

```text
1. 01_extrai_informalidade.py
2. 6_8.py
3. 6_9.py
```

### 10.6 Descrição dos scripts

| Arquivo | Finalidade | Entrada | Saída |
| --- | --- | --- | --- |
| `01_extrai_informalidade.py` | Lê as abas anuais da Tabela 6.4, classifica as localidades por escala e escopo e gera o arquivo estruturado de informalidade. | `Tabela 6.4.xlsx` | `data/processed/Informalidade2.xlsx` |
| `6_8.py` | Extrai a série histórica nacional de taxas de informalidade para Brasil e Economia Criativa. | `Informalidade2.xlsx` | `outputs/tables/6_8.csv` |
| `6_9.py` | Extrai os dados de Economia Criativa do ano de referência para os recortes estadual e municipal. | `Informalidade2.xlsx` | `outputs/tables/6.9.1.csv` e `outputs/tables/6.9.2.csv` |

### 10.7 Estrutura do arquivo `Informalidade2.xlsx`

| Coluna | Descrição |
| --- | --- |
| `Escopo` | `Total` ou `Economia Criativa` |
| `Escala` | `Nacional`, `Estadual` ou `Municipal` |
| `Recorte` | Nome da localidade |
| `Formal - Total` | Proporção de trabalhadores formais |
| `Informal - Total` | Proporção de trabalhadores informais |
| `Ano` | Ano de referência |

### 10.8 Validações e observações

- abas com coeficiente de variação e anos fora do intervalo são ignoradas;
- linhas sem dados numéricos válidos são descartadas;
- o script depende da posição fixa de colunas na planilha do IBGE;
- o arquivo `Informalidade2.xlsx` serve como base auxiliar para outros grupos.

## 11. Grupo `RAIS_ESTABELECIMENTOS_2025`

### 11.1 Finalidade

Este grupo processa o arquivo de estabelecimentos da RAIS 2025 para produzir:

- uma base detalhada dos estabelecimentos culturais;
- uma síntese nacional por natureza jurídica;
- uma síntese nacional por porte de estabelecimento;
- um CSV final com empresas da Economia Criativa por porte.

### 11.2 Fontes de dados

| Fonte | Arquivo | Uso |
| --- | --- | --- |
| RAIS Estabelecimentos 2025 | `Estb2025ID.COMT` | Microdados de estabelecimentos |
| CNAEs da cultura | `CNAE-ibge.xlsx` | Identificação de estabelecimentos culturais |

### 11.3 Período processado

Ano-base **2025**.

### 11.4 Filtros aplicados

- apenas registros com RAIS negativa igual a `0`;
- apenas CNAEs culturais para a base temática;
- apenas natureza jurídica empresarial para o produto final `6.28.csv`.

### 11.5 Ordem de execução

```text
1. 02_estabelecimentos_2025.py
2. 6_27.py
```

### 11.6 Descrição dos scripts

| Arquivo | Finalidade | Entradas principais | Saída |
| --- | --- | --- | --- |
| `02_estabelecimentos_2025.py` | Lê o arquivo de estabelecimentos da RAIS 2025, filtra registros válidos, classifica por CNAE cultural, natureza jurídica e porte, e gera três bases analíticas. | `Estb2025ID.COMT`; `CNAE-ibge.xlsx` | `data/processed/saida_1_estab_cultura_2025_base.csv`; `data/processed/saida_2_brasil_natureza_juridica_categoria.csv`; `data/processed/saida_3_brasil_tamanho_estabelecimento_categoria.csv` |
| `6_27.py` | Lê a base cultural, filtra por natureza jurídica empresarial e ano de análise, agrupa por categoria de porte e calcula participação percentual. | Base cultural intermediária | `outputs/tables/6.28.csv` |

### 11.7 Categorização

#### Natureza jurídica

- `Administração Pública`
- `Entidades Empresariais`
- `Entidades sem Fins Lucrativos`
- `Pessoas Físicas`
- `Organizações Internacionais e Outras Instituições Extraterritoriais`
- `Outros`

#### Porte

No script base:

- `1`: 0 empregados
- `2`: 1 a 4
- `3`: 5 a 9
- `4`: 10 a 19
- `5`: 20 a 49
- `6`: 50 a 99
- `7`: 100 a 249
- `8`: 250 a 499
- `9`: 500 a 999
- `10`: 1.000 ou mais

No produto final:

- `Microempresa (Até 9)`
- `Pequena Empresa (10 a 49)`
- `Média Empresa (50 a 99)`
- `Grande Empresa (100 ou mais)`

### 11.8 Validações e observações

- processamento em blocos de 300.000 linhas;
- descarte de linhas malformadas;
- verificação de existência dos arquivos de entrada;
- possível divergência entre o nome da base gerada e o nome da base lida por `6_27.py`, ponto que deve ser verificado.

## 12. Grupo `RAIS_VINCULOS_2016-2025`

### 12.1 Finalidade

Este grupo processa os microdados de vínculos da RAIS de 2016 a 2025, gerando métricas anuais de vínculos, massa salarial e remuneração média por grupo econômico e recorte geográfico. Em seguida, incorpora estimativas de informalidade, calcula índices de acompanhamento e exporta produtos finais.

### 12.2 Fontes de dados

| Fonte | Arquivo ou estrutura | Uso |
| --- | --- | --- |
| RAIS Vínculos | Arquivos anuais por UF | Microdados de vínculos ativos com CNAE, município e remuneração |
| CNAEs da cultura | `CNAE-ibge.xlsx` | Identificação das atividades classificadas como Cultura |
| Informalidade | `Informalidade2.xlsx` | Estimativa de vínculos informais e ajuste dos índices |

### 12.3 Período processado

Os dados cobrem **2016 a 2025**. As taxas de informalidade de 2024 são replicadas para 2025.

A base monetária é **2024**.

### 12.4 Grupos e recortes gerados

Grupos nacionais:

- `Brasil`
- `Economia Criativa`
- `Agricultura, pecuária, produção florestal, pesca e aquicultura`
- `Indústria extrativa`
- `Construção`

Recortes adicionais:

- UFs, para `Total` e `Economia Criativa`
- capitais, para `Total` e `Economia Criativa`

### 12.5 Ordem de execução

```text
1. 01.2rais_metricas_grupos_2016-2025.py
2. 02adicionar_informalidade_metricas_2016_2025.py.py
3. 04_rais_IRCA_frentes.py
4. 6_5.py, 6_6.py, 6_7.py, 6_10.py, 6_17.py
```

### 12.6 Descrição dos scripts

| Arquivo | Finalidade | Entradas principais | Saída |
| --- | --- | --- | --- |
| `01.2rais_metricas_grupos_2016-2025.py` | Lê os arquivos anuais da RAIS Vínculos, filtra vínculos ativos, classifica registros por grupo econômico e recorte geográfico e calcula vínculos, massa salarial e remuneração média. | Arquivos anuais da RAIS; `CNAE-ibge.xlsx` | `data/processed/rais_metricas_grupos_2016_2025.csv` |
| `02adicionar_informalidade_metricas_2016_2025.py.py` | Cruza as métricas da RAIS com a base de informalidade e adiciona a estimativa de vínculos informais. | `rais_metricas_grupos_2016_2025.csv`; `Informalidade2.xlsx` | `data/processed/rais_metricas_grupos_2016_2025_com_informalidade.csv` |
| `04_rais_IRCA_frentes.py` | Calcula os índices de acompanhamento salarial e de vínculos com base 2024. | `rais_metricas_grupos_2016_2025_com_informalidade.csv` | `data/processed/rais_IRCA_frentes.csv` e `data/processed/rais_IRCA_frentes.xlsx` |
| `6_5.py` | Extrai a série histórica de vínculos totais da Economia Criativa e calcula a variação anual percentual. | Base com informalidade | `outputs/tables/6_5.csv` |
| `6_6.py` | Calcula a participação da Economia Criativa no total de vínculos do Brasil. | Base com informalidade | `outputs/tables/6_6.csv` |
| `6_7.py` | Extrai a série histórica de vínculos formais para Economia Criativa, Agricultura, Indústria extrativa e Construção. | Base com informalidade | `outputs/tables/6.7.csv` |
| `6_10.py` | Calcula a participação da Economia Criativa no total de vínculos por capital e por UF em 2024. | Base com informalidade | `outputs/tables/6.10.1.csv` e `outputs/tables/6.10.2.csv` |
| `6_17.py` | Extrai a série histórica de remuneração média deflacionada para grupos selecionados. | Base com informalidade | `outputs/tables/6.17.csv` |

### 12.7 Métricas produzidas

| Variável | Descrição |
| --- | --- |
| `grupo` | Grupo econômico ou recorte geográfico |
| `ano` | Ano de referência |
| `total_vinculos` | Total de vínculos ativos em 31/12 |
| `massa_salarial_nom` | Massa salarial nominal |
| `massa_salarial_def` | Massa salarial deflacionada |
| `media_nom` | Remuneração média nominal |
| `media_def` | Remuneração média deflacionada |

Variáveis adicionais:

| Variável | Descrição |
| --- | --- |
| `total_vinculos_informais_estimado` | Estimativa de vínculos informais |
| `TF` | Taxa de formalidade |
| `fator_TF` | Razão entre taxa de formalidade de 2024 e do ano corrente |
| `massa_ajustada` | Massa salarial ajustada |
| `indice_salarial` | Índice de acompanhamento salarial |
| `vinculos_ajustados` | Vínculos formais ajustados |
| `indice_vinculos` | Índice de acompanhamento de vínculos |

### 12.8 Regras de cálculo relevantes

A estimativa de vínculos informais segue a fórmula:

$$
\text{informais estimados} = \text{formais} \times \left(\frac{\text{pct informal}}{\text{pct formal}}\right)
$$

Os índices são normalizados para 2024.

### 12.9 Validações e observações

- leitura diferenciada por período devido a mudanças de layout dos arquivos;
- processamento em blocos de 300.000 linhas;
- verificação de colunas obrigatórias;
- replicação das taxas de informalidade de 2024 para 2025;
- alguns scripts usam nomes de arquivos históricos ligeiramente diferentes, o que deve ser conferido.

## 13. Grupo `RAIS_VINCULOS_2025`

### 13.1 Finalidade

Este grupo processa os microdados de vínculos da RAIS 2025 para produzir perfis detalhados dos trabalhadores da Economia Criativa. A partir de um arquivo filtrado e padronizado gerado pelo script inicial, os demais scripts calculam indicadores por sexo, raça/cor, escolaridade, faixa etária, deficiência, domínio cultural, porte do estabelecimento e recorte geográfico.

### 13.2 Fontes de dados

| Fonte | Arquivo ou estrutura esperada | Uso |
| --- | --- | --- |
| RAIS Vínculos 2025 | Seis arquivos `.COMT` regionais | Microdados de vínculos ativos com atributos individuais e salariais |
| CNAEs da cultura | `CNAE-ibge.xlsx` | Identificação da Economia Criativa e mapeamento de domínios culturais |
| Municípios | `municipios.xlsx` | Código, nome, UF, macrorregião e identificação de capital |

### 13.3 Arquivos regionais da RAIS 2025

- `RAIS_VINC_ID_CENTRO_OESTE_2025.COMT`
- `RAIS_VINC_ID_MG_ES_RJ_2025.COMT`
- `RAIS_VINC_ID_NORDESTE_2025.COMT`
- `RAIS_VINC_ID_NORTE_2025.COMT`
- `RAIS_VINC_ID_SP_2025.COMT`
- `RAIS_VINC_ID_SUL_2025.COMT`

### 13.4 Período processado e deflação

Os dados correspondem ao ano-base **2025**. Os valores salariais são deflacionados para preços de **2024**.

### 13.5 Colunas do arquivo filtrado

O script `01_Filtro_2025.py` produz um CSV com colunas como:

| Coluna | Descrição |
| --- | --- |
| `CBO 2002 Ocupação - Código` | Código da ocupação |
| `CNAE 2.0 Subclasse - Código` | Código CNAE normalizado |
| `Escolaridade Após 2005 - Código` | Código de escolaridade |
| `Ind Portador Defic - Código` | Indicador de deficiência |
| `Ind Trabalho Intermitente - Código` | Indicador de trabalho intermitente |
| `Município - Código` | Código do município |
| `Natureza Jurídica - Código` | Código de natureza jurídica |
| `Raça Cor - Código` | Código de raça/cor |
| `Sexo - Código` | Código de sexo |
| `Tamanho Estabelecimento - Código` | Código de porte |
| `Idade` | Idade do trabalhador |
| `Vl Rem Média Nom` | Remuneração média nominal |
| `massa_salarial` | Soma das remunerações mensais |
| `meses_com_salario` | Número de meses com remuneração positiva |
| `massa_salarial_deflacionada_2024` | Massa salarial deflacionada |
| `vl_rem_media_nom_deflacionada_2024` | Remuneração média deflacionada |
| `ano` | Ano de referência |

### 13.6 Ordem de execução

```text
1. 01_Filtro_2025.py
2. 6_11.py
3. 6_12___6_19.py
4. 6_13___6_21.py
5. 6_14___6_23.py
6. 6_15___6_24.py
7. 6_16.py
8. 6_18.py
9. 6_20.py
10. 6_22.py
11. 6_25___6_26.py
12. 6_28___6_29.py
```

Após a geração do arquivo filtrado, os scripts analíticos são independentes entre si.

### 13.7 Descrição dos scripts

| Arquivo | Finalidade | Entradas principais | Saída |
| --- | --- | --- | --- |
| `01_Filtro_2025.py` | Lê os seis arquivos regionais da RAIS 2025, filtra vínculos ativos em 31/12, padroniza campos, calcula massa salarial e deflaciona os valores para preços de 2024. | Arquivos `.COMT` regionais | `data/processed/rais_2025_filtrado.csv` |
| `6_11.py` | Calcula a taxa de trabalhadores da Economia Criativa por 1.000 trabalhadores totais por município. | `rais_2025_filtrado.csv`; `CNAE-ibge.xlsx`; `municipios.xlsx` | `outputs/tables/ec_por_1000_trabalhadores_municipios.csv` |
| `6_12___6_19.py` | Calcula total de vínculos, participação percentual e remuneração média deflacionada da Economia Criativa por sexo. | `rais_2025_filtrado.csv`; `CNAE-ibge.xlsx` | `outputs/tables/6.12.csv` |
| `6_13___6_21.py` | Calcula total de vínculos, participação percentual e remuneração média deflacionada da Economia Criativa por raça/cor. | `rais_2025_filtrado.csv`; `CNAE-ibge.xlsx` | `outputs/tables/6.13.csv` |
| `6_14___6_23.py` | Calcula total de vínculos, participação percentual e remuneração média deflacionada da Economia Criativa por escolaridade. | `rais_2025_filtrado.csv`; `CNAE-ibge.xlsx` | `outputs/tables/6.14.csv` |
| `6_15___6_24.py` | Calcula total de vínculos, participação percentual e remuneração média deflacionada da Economia Criativa por faixa etária. | `rais_2025_filtrado.csv`; `CNAE-ibge.xlsx` | `outputs/tables/6.15.csv` |
| `6_16.py` | Calcula total de vínculos com deficiência, participação percentual e remuneração média deflacionada com e sem deficiência, para total e Economia Criativa. | `rais_2025_filtrado.csv`; `CNAE-ibge.xlsx` | `outputs/tables/6.16.csv` |
| `6_18.py` | Calcula a remuneração média deflacionada da Economia Criativa por capital e por UF. | `rais_2025_filtrado.csv`; `CNAE-ibge.xlsx`; `municipios.xlsx` | `outputs/tables/6.18.csv` |
| `6_20.py` | Calcula a remuneração média deflacionada da Economia Criativa por domínio cultural e sexo. | `rais_2025_filtrado.csv`; `CNAE-ibge.xlsx` | `outputs/tables/6.20.csv` |
| `6_22.py` | Calcula a remuneração média deflacionada da Economia Criativa por raça/cor e sexo. | `rais_2025_filtrado.csv`; `CNAE-ibge.xlsx` | `outputs/tables/6.23.csv` |
| `6_25___6_26.py` | Filtra vínculos da Economia Criativa, associa cada atividade ao respectivo domínio cultural e calcula, por domínio, o total de vínculos e a remuneração média deflacionada. | `rais_2025_filtrado.csv`; `CNAE-ibge.xlsx` | `outputs/tables/6.26.csv` |
| `6_28___6_29.py` | Filtra vínculos criativos em entidades empresariais, classifica os registros por porte do estabelecimento e calcula total de trabalhadores e salário médio por porte. | `rais_2025_filtrado.csv`; `CNAE-ibge.xlsx` | `outputs/tables/6.29_6.30.csv` |

### 13.8 Categorias utilizadas

#### Sexo

| Código | Categoria |
| --- | --- |
| 1 | Masculino |
| 2 | Feminino |

#### Raça/cor

| Código | Categoria |
| --- | --- |
| 1 | Indígena |
| 2 | Branca |
| 4 | Preta/Parda |
| 8 | Preta/Parda |
| 6 | Amarela |
| 9 | Não identificado |
| 99 | Não identificado |
| -1 | Ignorado |

#### Escolaridade

| Códigos | Categoria |
| --- | --- |
| 1, 2, 3, 4 | Sem instrução / Fund. Incompleto |
| 5, 6 | Fund. Completo / Médio Incompleto |
| 7, 8 | Médio Completo / Sup. Incompleto |
| 9 | Superior Completo |
| 10, 11 | Pós-graduação |
| -1 | Ignorado |

#### Faixa etária

| Faixa | Intervalo |
| --- | --- |
| Jovem (15–29) | 15 a 29 anos |
| Adulto I (30–44) | 30 a 44 anos |
| Adulto II (45–59) | 45 a 59 anos |
| Idoso (60+) | 60 anos ou mais |

### 13.9 Fluxo de dados

```text
Arquivos regionais RAIS 2025 (.COMT)
        │
        ▼
rais_2025_filtrado.csv
        │
        ├── CNAE-ibge.xlsx
        ├── municipios.xlsx
        │
        ├──► 6_11.py         ──► outputs/tables/ec_por_1000_trabalhadores_municipios.csv
        ├──► 6_12___6_19.py  ──► outputs/tables/6.12.csv
        ├──► 6_13___6_21.py  ──► outputs/tables/6.13.csv
        ├──► 6_14___6_23.py  ──► outputs/tables/6.14.csv
        ├──► 6_15___6_24.py  ──► outputs/tables/6.15.csv
        ├──► 6_16.py         ──► outputs/tables/6.16.csv
        ├──► 6_18.py         ──► outputs/tables/6.18.csv
        ├──► 6_20.py         ──► outputs/tables/6.20.csv
        ├──► 6_22.py         ──► outputs/tables/6.23.csv
        ├──► 6_25___6_26.py  ──► outputs/tables/6.26.csv
        └──► 6_28___6_29.py  ──► outputs/tables/6.29_6.30.csv
```

### 13.10 Validações e observações

- verificação da existência de todos os arquivos de entrada;
- processamento em blocos de 300.000 linhas;
- descarte de linhas malformadas;
- detecção de separador do CSV de entrada em alguns scripts de análise;
- avisos para municípios sem correspondência nas tabelas auxiliares;
- os scripts com dupla numeração no nome dependem de configuração manual de constantes para gerar produtos alternativos;
- `6_28___6_29.py`, na versão analisada, contém um problema de indentação no trecho de agrupamento salarial;
- a compatibilidade entre o nível de agregação do CNAE no arquivo filtrado e nos arquivos auxiliares deve ser validada.

## 14. Convenções de código e recomendações

Recomenda-se que a manutenção futura observe as seguintes práticas:

- substituir caminhos absolutos por caminhos configuráveis;
- centralizar parâmetros locais em arquivo de configuração;
- evitar divergência entre o nome do script e o nome do arquivo final gerado;
- parametrizar ano de referência e nome de saída via linha de comando;
- manter funções reutilizáveis com docstrings;
- padronizar nomes de arquivos intermediários;
- incluir validações explícitas de integridade e consistência entre chaves de cruzamento;
- registrar no README qualquer nova saída analítica adicionada ao pipeline.

## 15. Qualidade e validação

Os pipelines já incluem, em diferentes graus, validações como:

- verificação de existência de arquivos e diretórios;
- conferência de colunas obrigatórias;
- normalização de codificação e nomes de colunas;
- descarte de linhas malformadas;
- processamento em blocos para controle de memória;
- checagem de filtros sem resultado;
- avisos e erros explícitos para bases vazias ou inconsistentes.

Recomenda-se complementar com:

- contagem de linhas antes e depois dos filtros;
- validação de chaves de merge;
- verificação de duplicidades;
- conferência de totais com fontes oficiais;
- testes de consistência entre saídas históricas e novas atualizações.

## 16. Problemas conhecidos

| Problema | Causa provável | Observação |
| --- | --- | --- |
| Caminhos absolutos pessoais nos scripts | Desenvolvimento local original | Devem ser substituídos por caminhos configuráveis |
| Nomes de scripts e nomes de saídas nem sempre coincidem | Convenção de trabalho acumulada | Recomenda-se padronização |
| Scripts com dupla numeração dependem de edição manual | Parâmetros embutidos no código | Recomenda-se parametrização |
| Divergências entre nomes de arquivos intermediários | Evolução incremental do pipeline | Deve ser revisado antes da automação |
| Problema de indentação em `6_28___6_29.py` | Erro de formatação do código | Requer correção antes da execução |

## 17. Atualização das bases

### RAIS Vínculos

1. baixar os microdados anuais no [FTP do Ministério do Trabalho e Emprego](ftp://ftp.mtps.gov.br/pdet/microdados/);
2. armazenar localmente em `data/raw/rais/vinculos/`;
3. atualizar arquivos auxiliares, se necessário;
4. executar os pipelines históricos e/ou anuais correspondentes;
5. validar totais, colunas e saídas.

### RAIS Estabelecimentos

1. baixar os microdados anuais no [FTP do Ministério do Trabalho e Emprego](ftp://ftp.mtps.gov.br/pdet/microdados/);
2. armazenar localmente em `data/raw/rais/estabelecimentos/`;
3. executar os scripts do grupo `RAIS_ESTABELECIMENTOS_2025`;
4. validar categorias e saídas finais.

### CAGED

1. baixar os arquivos mensais no [FTP do Ministério do Trabalho e Emprego](ftp://ftp.mtps.gov.br/pdet/microdados/);
2. armazenar localmente em `data/raw/caged/`;
3. atualizar IPCA, se necessário;
4. executar o pipeline `CAGED_2024_2026`;
5. validar índices e variações percentuais exportadas.

### Informalidade

1. acessar a página de [Indicadores culturais do IBGE](https://www.ibge.gov.br/estatisticas/multidominio/cultura-recreacao-e-esporte/9388-indicadores-culturais.html);
2. localizar a Tabela 6.4 de *Ocupação no setor cultural (formal e informal)*;
3. salvar o arquivo localmente em `data/raw/informalidade/`;
4. executar os scripts do grupo `INFORMALIDADE`;
5. validar a estrutura de `Informalidade2.xlsx`.

## 18. Proteção de dados e publicação

Antes de versionar arquivos no GitHub, verificar:

- se os microdados brutos podem ser publicados;
- se há restrições de sigilo, tamanho ou licenciamento;
- se os dados intermediários contêm informações sensíveis;
- se apenas os produtos finais autorizados serão incluídos em `outputs/tables/`.

Não devem ser versionados, salvo autorização explícita:

- microdados brutos;
- arquivos locais de configuração;
- bases intermediárias extensas;
- dados protegidos por restrições institucionais.

## 19. Checklist para entrega

Antes de concluir uma atualização, confirmar:

- [ ] o código executa sem erros;
- [ ] os caminhos locais foram configurados;
- [ ] não há caminhos absolutos pessoais a publicar;
- [ ] não há credenciais nem arquivos sensíveis no repositório;
- [ ] as entradas e saídas estão documentadas;
- [ ] os arquivos finais em `outputs/tables/` foram conferidos;
- [ ] a ordem de execução está atualizada;
- [ ] as validações foram realizadas;
- [ ] o README foi atualizado.

## 20. Responsáveis pelo acompanhamento

Para acompanhamento técnico:

- [@gabrielribeirobizerril](https://github.com/gabrielribeirobizerril)
- [@LuizaMaluf](https://github.com/LuizaMaluf)
