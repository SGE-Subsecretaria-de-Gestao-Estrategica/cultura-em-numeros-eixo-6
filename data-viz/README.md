# Eixo N — Visualização de Dados

Esta pasta reúne os códigos, arquivos de configuração e demais recursos utilizados na produção das visualizações do **eixo N** do projeto **Cultura em Números**.

A documentação deverá permitir que qualquer colaborador consiga identificar os dados utilizados, compreender a estrutura dos códigos, executar as visualizações e atualizar os produtos quando novas bases forem disponibilizadas.

## 1. Estrutura da pasta

A estrutura é:

```text
data-viz/
├── README.md
├── requirements.txt
├── inputs/
│   ├── csv/
│   ├── excel/
│   └── geo/
├── src/
│   ├── app/
│   ├── charts/
│   ├── maps/
│   ├── components/
│   ├── data/
│   └── utils/
├── assets/
├── outputs/
└── tests/
```

### Descrição das pastas

| Pasta             | Finalidade                                            |
| ----------------- | ----------------------------------------------------- |
| `inputs/`         | Arquivos utilizados como entrada pelas visualizações  |
| `inputs/csv/`     | Bases em formato CSV                                  |
| `inputs/excel/`   | Planilhas em formato XLSX ou XLS                      |
| `inputs/geo/`     | Arquivos geográficos, como GeoJSON ou Shapefile       |
| `src/app/`        | Arquivo principal da aplicação ou painel              |
| `src/charts/`     | Códigos responsáveis pela geração de gráficos         |
| `src/maps/`       | Códigos responsáveis pela geração de mapas            |
| `src/components/` | Componentes visuais reutilizáveis                     |
| `src/data/`       | Funções de leitura, validação e preparação dos dados  |
| `src/utils/`      | Funções auxiliares                                    |
| `assets/`         | Imagens, ícones, logotipos e arquivos de estilo       |
| `outputs/`        | Gráficos, mapas, tabelas e outros produtos exportados |
| `tests/`          | Testes e rotinas de validação                         |

A estrutura poderá ser adaptada conforme a tecnologia utilizada. Qualquer alteração deverá ser documentada neste README.

## 2. Tecnologias utilizadas

Preencha esta seção conforme as ferramentas adotadas.

* **Ferramenta principal:** [Power BI, Python, R, JavaScript ou outra]
* **Linguagem:** [Python, R, JavaScript ou outra]
* **Versão:** [versão utilizada]
* **Framework:** [Streamlit, Dash, Shiny, React etc.]
* **Bibliotecas de visualização:** [Plotly, Altair, Matplotlib, D3.js etc.]

## 3. Arquivos de entrada

Os arquivos utilizados pelas visualizações deverão ser armazenados na pasta:

```text
data-viz/inputs/
```

A localização deverá observar o formato do arquivo:

```text
data-viz/inputs/csv/
data-viz/inputs/excel/
data-viz/inputs/geo/
```

Exemplos:

```text
data-viz/inputs/csv/indicadores_eixo_2.csv
data-viz/inputs/excel/tabelas_eixo_2.xlsx
data-viz/inputs/geo/municipios.geojson
```

Os códigos não deverão utilizar arquivos localizados em pastas pessoais, áreas de trabalho ou diretórios de downloads.

Não utilize caminhos absolutos:

```python
df = pd.read_csv(
    "C:/Users/usuario/Desktop/projeto/indicadores.csv"
)
```

Utilize caminhos relativos:

```python
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

input_path = (
    ROOT
    / "inputs"
    / "csv"
    / "indicadores_eixo_2.csv"
)

df = pd.read_csv(input_path)
```

## 4. Catálogo dos arquivos de entrada

Todos os arquivos utilizados deverão ser documentados.

| Arquivo          | Localização                   | Formato | Descrição           | Responsável   |
| ---------------- | ----------------------------- | ------- | ------------------- | ------------- |
| `[arquivo.csv]`  | `inputs/csv/[arquivo.csv]`    | CSV     | [Descrição da base] | [Responsável] |
| `[arquivo.xlsx]` | `inputs/excel/[arquivo.xlsx]` | Excel   | [Descrição da base] | [Responsável] |

Para cada arquivo, informe:

* a fonte original;
* a pessoa ou equipe responsável pela produção;
* o período de referência;
* a periodicidade de atualização;
* a data da última atualização;
* as colunas obrigatórias;
* a unidade de análise;
* as regras de preenchimento;
* as eventuais restrições de uso.

## 5. Estrutura esperada dos arquivos

Cada arquivo de entrada deverá ter suas colunas documentadas.

### Arquivo: `[nome_do_arquivo.csv]`

Localização:

```text
inputs/csv/nome_do_arquivo.csv
```

| Coluna       | Tipo esperado | Obrigatória | Descrição   |
| ------------ | ------------- | ----------- | ----------- |
| `[coluna_1]` | `string`      | Sim         | [Descrição] |
| `[coluna_2]` | `integer`     | Sim         | [Descrição] |
| `[coluna_3]` | `float`       | Não         | [Descrição] |
| `[coluna_4]` | `date`        | Não         | [Descrição] |

Para arquivos CSV, recomenda-se utilizar:

```text
Codificação: UTF-8
Separador: vírgula
Decimal: ponto
Datas: AAAA-MM-DD
Cabeçalho: primeira linha
Índice: não exportar
```

Exemplo:

```csv
codigo_uf,nome_uf,valor_total,quantidade
11,Rondônia,1500000.50,120
12,Acre,980000.00,75
```

## 6. Relação com a pasta `analytics/`

Os tratamentos analíticos deverão ser realizados, preferencialmente, na pasta `analytics/`.

O fluxo recomendado é:

```text
analytics/
    │
    │ processamento e produção dos indicadores
    ▼
analytics/outputs/
    │
    │ exportação dos arquivos finais
    ▼
data-viz/inputs/
    │
    │ leitura dos dados
    ▼
data-viz/src/
```

A pasta `data-viz/` deverá realizar apenas tratamentos necessários à apresentação, como:

* renomear categorias;
* ordenar valores;
* formatar datas;
* formatar valores monetários;
* criar rótulos;
* aplicar filtros de interface;
* adaptar os dados ao formato exigido pelo gráfico.

Cálculos de indicadores e alterações metodológicas deverão ser realizados e documentados em `analytics/`.

## 7. Configuração do ambiente

### Clonar o repositório

```bash
git clone https://github.com/SGE-Subsecretaria-de-Gestao-Estrategica/cultura-em-numeros-eixo-2.git
cd cultura-em-numeros-eixo-2/data-viz
```

### Criar um ambiente virtual

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

### Instalar as dependências

```bash
pip install -r requirements.txt
```

Caso sejam utilizadas outras tecnologias, os comandos correspondentes deverão ser registrados nesta seção.

Exemplo para projetos em JavaScript:

```bash
npm install
```

## 8. Como executar

O comando de execução dependerá da tecnologia utilizada.

### Streamlit

```bash
streamlit run src/app/app.py
```

### Dash ou aplicação Python

```bash
python src/app/app.py
```

### Shiny para R

```r
shiny::runApp()
```

### Aplicação JavaScript

```bash
npm run dev
```

### Geração de gráficos por script

```bash
python src/charts/generate_all_charts.py
```

O comando efetivamente utilizado pelo projeto deverá substituir ou complementar os exemplos acima.

## 9. Ordem de execução

Registre a sequência necessária para executar o produto.

Exemplo:

```text
1. Verificar os arquivos disponíveis em inputs/.
2. Executar a validação dos arquivos de entrada.
3. Executar a preparação dos dados.
4. Gerar os gráficos e mapas.
5. Iniciar a aplicação ou painel.
6. Conferir os arquivos produzidos em outputs/.
```

Exemplo de comandos:

```bash
python src/data/validate_inputs.py
python src/data/prepare_data.py
python src/charts/generate_all_charts.py
streamlit run src/app/app.py
```

## 10. Documentação dos códigos

Cada arquivo deverá apresentar, no início, uma descrição de sua finalidade.

Exemplo:

```python
"""
Gera o gráfico de distribuição dos recursos por unidade da Federação.

Entrada:
    inputs/csv/recursos_por_uf.csv

Colunas utilizadas:
    - uf
    - valor_total
    - percentual_total

Saída:
    outputs/recursos_por_uf.png

Execução:
    python src/charts/recursos_por_uf.py
"""
```

As funções deverão possuir docstrings.

```python
def criar_grafico_recursos_por_uf(df):
    """
    Cria um gráfico de barras com o valor total por UF.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame contendo as colunas `uf` e `valor_total`.

    Returns
    -------
    plotly.graph_objects.Figure
        Figura pronta para exibição ou exportação.
    """
```

Os códigos deverão utilizar:

* nomes claros para arquivos, funções e variáveis;
* caminhos relativos;
* funções reutilizáveis;
* arquivos de configuração centralizados;
* tratamento de erros;
* mensagens claras para arquivos ausentes;
* comentários apenas quando necessários para explicar decisões não evidentes.

## 11. Catálogo das visualizações

Cada gráfico, mapa, tabela ou componente deverá ser registrado.

| Identificador | Título   | Tipo                 | Arquivo de entrada         | Código responsável        |
| ------------- | -------- | -------------------- | -------------------------- | ------------------------- |
| `viz_01`      | [Título] | [Gráfico, mapa etc.] | `inputs/csv/[arquivo.csv]` | `src/charts/[arquivo.py]` |

Para cada visualização, informe:

* o objetivo;
* a pergunta respondida;
* os dados utilizados;
* as colunas utilizadas;
* os filtros aplicados;
* o tipo de agregação;
* a unidade apresentada;
* o arquivo responsável;
* o local da saída.

Modelo:

```text
Identificador: viz_01
Título: [título da visualização]
Objetivo: [objetivo]
Arquivo de entrada: inputs/csv/[arquivo.csv]
Colunas utilizadas: [coluna_1], [coluna_2]
Filtros: [filtros]
Agregação: [soma, média, contagem etc.]
Código: src/charts/[arquivo.py]
Saída: outputs/[arquivo.png]
```

## 12. Validação dos arquivos de entrada

Antes da execução, os códigos deverão verificar:

* se os arquivos obrigatórios existem;
* se estão no diretório correto;
* se as colunas obrigatórias estão presentes;
* se os tipos de dados são válidos;
* se existem duplicidades;
* se existem valores ausentes críticos;
* se o período dos dados está atualizado.

Exemplo:

```python
from pathlib import Path
import pandas as pd

input_path = Path("inputs/csv/indicadores_eixo_2.csv")

if not input_path.exists():
    raise FileNotFoundError(
        f"Arquivo de entrada não encontrado: {input_path}"
    )

df = pd.read_csv(input_path)

required_columns = {
    "categoria",
    "valor",
    "percentual",
}

missing_columns = required_columns.difference(df.columns)

if missing_columns:
    raise ValueError(
        f"Colunas obrigatórias ausentes: {sorted(missing_columns)}"
    )
```

As mensagens de erro deverão indicar claramente o problema e a forma de correção.

## 13. Arquivos de saída

Os arquivos gerados deverão ser armazenados em:

```text
data-viz/outputs/
```

Exemplos:

```text
outputs/grafico_recursos_uf.png
outputs/mapa_municipios.html
outputs/tabela_indicadores.csv
```

Todos os produtos deverão ser documentados.

| Produto   | Arquivo                  | Formato | Código responsável        |
| --------- | ------------------------ | ------- | ------------------------- |
| [Gráfico] | `outputs/[arquivo.png]`  | PNG     | `src/charts/[arquivo.py]` |
| [Mapa]    | `outputs/[arquivo.html]` | HTML    | `src/maps/[arquivo.py]`   |

## 14. Atualização dos dados

Para atualizar uma visualização:

1. identifique o arquivo de entrada utilizado;
2. execute o processo correspondente em `analytics/`;
3. exporte o arquivo atualizado para `data-viz/inputs/`;
4. preserve o nome e as colunas esperadas;
5. valide os dados;
6. execute os códigos de visualização;
7. revise os resultados;
8. compare os totais com os produtos de `analytics/`;
9. atualize o período de referência;
10. atualize este README quando houver mudanças.

Modelo de registro:

```text
Produto: [nome]
Arquivo de entrada: inputs/csv/[arquivo.csv]
Periodicidade: [mensal, anual etc.]
Última atualização: [data]
Período de referência: [período]
Responsável: [nome ou usuário]
Código executado: [caminho]
```

## 15. Segurança

Não deverão ser versionados:

* senhas;
* tokens;
* chaves de API;
* arquivos `.env`;
* dados pessoais identificáveis;
* bases sigilosas;
* arquivos recebidos sob restrição;
* conexões contendo credenciais.

Quando forem necessárias variáveis de ambiente, crie um arquivo `.env.example`:

```text
DATABASE_HOST=
DATABASE_PORT=
DATABASE_NAME=
DATABASE_USER=
DATABASE_PASSWORD=
API_TOKEN=
```

O arquivo `.env` real deverá permanecer no `.gitignore`.

## 16. Checklist para entrega

Antes de concluir uma atividade, confirme:

* [ ] os arquivos de entrada estão documentados;
* [ ] os arquivos estão nas pastas corretas;
* [ ] as colunas obrigatórias foram registradas;
* [ ] os caminhos utilizados são relativos;
* [ ] os códigos possuem descrição e docstrings;
* [ ] a forma de execução está documentada;
* [ ] as visualizações possuem objetivo definido;
* [ ] os filtros e agregações estão descritos;
* [ ] os resultados foram comparados com as bases de `analytics/`;
* [ ] não existem credenciais no repositório;
* [ ] os arquivos temporários foram removidos;
* [ ] o README está atualizado;
* [ ] o produto está pronto para revisão.

## 17. Responsáveis pelo acompanhamento

Para acompanhamento dos produtos de visualização:

* [@gabrielribeirobizerril](https://github.com/gabrielribeirobizerril)
* [@LuizaMaluf](https://github.com/LuizaMaluf)
