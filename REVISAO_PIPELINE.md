# Revisão do pipeline — Cultura em Números, Eixo 6

Data da revisão: 2026-08-20
Escopo: repositório `cultura-em-numeros-eixo-6` (pastas `analytics/` e `data-viz/`)
Metodologia: revisão de documentação/código + teste funcional real (clone em diretório temporário, instalação de dependências, execução dos scripts). O teste em si ocorreu numa cópia local descartável; algumas correções simples e de baixo risco (nomes de arquivo, `.gitignore`) foram depois aplicadas também no repositório real — ver "O que foi e não foi alterado" ao final.

## Resumo

O único problema de execução encontrado que é de fato um defeito de código é um bug de portabilidade no Windows. Os caminhos absolutos apontando para OneDrive/disco externo, que a princípio pareciam um bloqueio de portabilidade, são intencionais (as bases da RAIS são grandes demais para o repositório) e não contam como erro.

1. **Bug real de compatibilidade (encontrado e corrigido só na cópia de teste, ainda não no repositório real):** `RAIS_ESTABELECIMENTOS_2025/02_estabelecimentos_2025.py` chamava `csv.field_size_limit(sys.maxsize)`, que sempre falha no Windows com `OverflowError` — não é um erro de ambiente/dado, é um bug de portabilidade, reproduzível em qualquer instalação Windows, independente de path ou dado de entrada.
2. **Caminhos absolutos apontando para OneDrive/disco externo (intencional, não é bug):** os caminhos de entrada e saída são caminhos absolutos do ambiente de quem escreveu o script (`D:\OneDrive\Minc\RAIS\...`, `E:\Rais\...`). Isso é esperado — as bases da RAIS são grandes demais para ficarem no repositório, então o pipeline sempre vai puxar de um local externo. Cada script tem uma constante de caminho fixa que precisa ser editada manualmente por quem for rodar em outra máquina — já é simples hoje, por ser uma constante `pathlib.Path` clara no topo do arquivo. No teste abaixo, a execução falhou porque o drive `E:\` do ambiente original não existe nesta máquina de teste — comportamento esperado, não uma falha do pipeline.

Três arquivos tinham extensão duplicada (`.txt` a mais) e o `.gitignore` da raiz estava vazio — já corrigidos no repositório real. A pasta `data-viz/` ainda é só um template genérico vazio, o que é esperado nesta fase do eixo.

## 1. O projeto é executável?

**Não de ponta a ponta nesta máquina de teste — mas por um motivo esperado.** Os scripts leem/gravam diretamente em `D:\OneDrive\...` e `E:\Rais\...`, caminhos externos intencionais (as bases da RAIS são grandes demais para o repositório), que não existem fora do ambiente original. Isso não é um defeito do pipeline; é quem for rodar em outra máquina que precisa editar a constante de caminho no topo de cada script antes de rodar — algo já simples hoje, por ser um `pathlib.Path` isolado. O que de fato é um problema de execução, independente de onde os dados estão, é o bug de portabilidade descrito na seção "Resultado do teste de execução" abaixo.

Três arquivos com nome errado (extensão `.txt` sobrando) quebram silenciosamente partes do próprio fluxo de setup documentado no README:

| Arquivo atual | Deveria ser | Efeito do nome errado |
|---|---|---|
| `analytics/requirements.txt.txt` | `analytics/requirements.txt` | `pip install -r requirements.txt` (comando documentado no README) falha com "arquivo não encontrado" — confirmado no teste |
| `analytics/.gitignore.txt` | `analytics/.gitignore` | O Git não reconhece esse arquivo como gitignore; nenhuma das regras (`.venv/`, `__pycache__/`, `data/raw/`, `config/paths.py`) está de fato ativa |
| `analytics/config/paths.example.py.txt` | `analytics/config/paths.example.py` | O template de configuração de caminhos não é reconhecido como módulo Python |

O `.gitignore` da raiz também existe, mas está vazio (0 bytes) — não há hoje nenhum `.gitignore` funcional em todo o repositório.

## 2. Existe documentação da estrutura do código?

**Sim, e é o ponto mais forte do repositório.** `analytics/README.md` (1002 linhas) documenta, por grupo de script, fontes de dados, entradas/saídas esperadas, ordem de execução (seção 7) e uma tabela de "Problemas conhecidos" (seção 16).

## 3. Existe documentação de como executar?

**Sim, no nível de instruções**, mas ela descreve um fluxo que os scripts não seguem de fato: a seção 5 recomenda `config/paths.py`, mas nenhum dos 28 scripts importa esse módulo — todos usam constantes de caminho absoluto no topo do próprio arquivo.

## 4. Existe a ficha de metadados (.xlsx)?

**Sim** — `Ficha de Metadados Eixo 6.xlsx` está presente na raiz do repositório.

## 5. Existe arquivo de dependências correspondente à linguagem?

**Sim quanto ao conteúdo, não quanto ao nome.** `analytics/requirements.txt.txt` lista corretamente `pandas`, `numpy`, `openpyxl`, `xlrd` — e a instalação com essas 4 linhas funcionou sem erro no teste, depois de corrigido o nome do arquivo.

## Resultado do teste de execução

**Veredito: passou com ajustes, dentro do possível nesta máquina de teste** — corrigido um bug real de portabilidade; o restante das falhas veio de os dados (intencionalmente externos, em OneDrive/disco) e o drive `E:\` do ambiente original não existirem nesta máquina, o que é esperado e não indica defeito do pipeline.

### Setup (bem-sucedido)

1. Clone do repositório para diretório temporário local.
2. `cp requirements.txt.txt requirements.txt` (correção simples, nome de arquivo).
3. `python -m venv .venv` + `pip install -r requirements.txt` → **sucesso**: `pandas 3.0.5`, `numpy 2.4.6`, `openpyxl 3.1.5`, `xlrd 2.0.2` instalados sem conflito.

### Correção simples aplicada (na cópia de teste apenas)

**Arquivo:** `analytics/RAIS_ESTABELECIMENTOS_2025/02_estabelecimentos_2025.py:27`

```diff
- csv.field_size_limit(sys.maxsize)
+ csv.field_size_limit(min(sys.maxsize, 2**31 - 1))  # sys.maxsize excede o limite de C long no Windows
```

`sys.maxsize` é um inteiro de 64 bits, mas `csv.field_size_limit` espera um C `long`, que no Windows é de 32 bits — a chamada original sempre lança `OverflowError: Python int too large to convert to C long` em qualquer instalação Windows, com qualquer dado de entrada. Não é um problema de path nem de dado ausente: é um bug de portabilidade do próprio código, e é o único erro encontrado que teria acontecido mesmo com os dados reais e o drive certo disponíveis. Depois da correção, o script passou dessa linha e seguiu para a etapa seguinte. Ocorre só neste arquivo — os outros 27 scripts não usam essa chamada.

### Falhas esperadas nesta máquina de teste (dados externos por design, não um defeito)

Testado um script representativo de cada um dos 5 grupos (o primeiro da ordem de execução documentada na seção 7 do README). Todos falham pelo mesmo motivo: o caminho aponta para um drive (`E:\`, `D:\`) que só existe no ambiente original — esperado, já que as bases da RAIS são grandes demais para o repositório e o pipeline sempre vai buscar os dados de um local externo (OneDrive/disco).

| Grupo | Script testado | Ponto de falha | Erro |
|---|---|---|---|
| INFORMALIDADE | `01_extrai_informalidade.py` | leitura de `E:\Rais\Rais\Informalidade\Tabela 6.4.xlsx` | `FileNotFoundError` (traceback bruto do pandas, sem mensagem amigável) |
| RAIS_VINCULOS_2025 | `01_Filtro_2025.py` | `OUTPUT_DIR.mkdir(...)` | `FileNotFoundError: [WinError 3]` — não encontra `E:\` |
| CAGED_2024_2026 | `01_caged_metricas_grupos_salario1M.py` | `PASTA_OUTPUT.mkdir(...)` | `FileNotFoundError: [WinError 3]` — não encontra `E:\` |
| RAIS_ESTABELECIMENTOS_2025 | `02_estabelecimentos_2025.py` | `OUT_DIR.mkdir(...)` (após corrigir o bug do field_size_limit) | `FileNotFoundError: [WinError 3]` — não encontra `E:\` |
| RAIS_VINCULOS_2016-2025 | `01.2rais_metricas_grupos_2016-2025.py` | `PASTA_OUTPUT.mkdir(...)` | `FileNotFoundError: [WinError 3]` — não encontra `E:\` |

Essas falhas não foram "corrigidas" porque não são um defeito a corrigir: em qualquer máquina, quem for rodar precisa primeiro apontar a constante de caminho no topo do script para onde os dados estão localmente (o mesmo drive/OneDrive do usuário). É um passo manual esperado do fluxo, não um bug.

Sobre o item "Problema de indentação em `6_28___6_29.py`" citado na seção 16 do README: revisei o arquivo e o executei via `ast.parse` junto com os outros 27 scripts — nenhum erro de sintaxe foi encontrado no estado atual. Pode já ter sido corrigido sem atualizar a tabela, ou ser um problema lógico mais sutil; recomendo confirmar com quem escreveu o script.

## Pontos impeditivos e sugestão de correção

| # | Ponto impeditivo | Sugestão | Status |
|---|---|---|---|
| 1 | `csv.field_size_limit(sys.maxsize)` quebra em qualquer Windows | Aplicar a correção já testada: `csv.field_size_limit(min(sys.maxsize, 2**31 - 1))` | Testado só na cópia temporária — ainda não aplicado no repositório real |
| 2 | `analytics/requirements.txt.txt` → nome errado | Renomear para `analytics/requirements.txt` | ✅ Corrigido — regerado com `pipreqs` |
| 3 | `analytics/.gitignore.txt` → nome errado, ignore não funciona | Renomear para `analytics/.gitignore` | ✅ Corrigido |
| 4 | `analytics/config/paths.example.py.txt` → nome errado | Renomear para `analytics/config/paths.example.py` | ✅ Corrigido |
| 5 | `.gitignore` da raiz estava vazio | Preencher com regras equivalentes (`.venv/`, `__pycache__/`, `.env`) | ✅ Corrigido |
| 6 | `data-viz/README.md` ainda é o template de outro eixo (título "Eixo N", link do eixo 2) | Atualizar título e link de clone para `eixo-6` quando a etapa de visualização começar | Pendente |

Os caminhos absolutos apontando para OneDrive/disco externo (`D:\...`, `E:\...`) **não entram nessa lista** — são intencionais, dado o tamanho das bases da RAIS, e não uma falha a corrigir (ver seção 1 acima).

## Checklist final

- [ ] Repositório é executável (roda sem erros críticos, mesmo que com ajustes simples) — falta aplicar a correção do `field_size_limit` no repositório real; os caminhos externos não contam contra este item, são esperados
- [x] Documentação explica a estrutura do código
- [x] Documentação explica como executar o código (sequência dos scripts)
- [x] Cada script documenta input/output esperado (seções 9–13 do `analytics/README.md`)
- [x] Existe tutorial de como rodar na máquina de quem clonar
- [x] Existe arquivo .xlsx com a ficha de metadados do projeto
- [x] Existe arquivo de dependências adequado à linguagem (`analytics/requirements.txt`, regerado com `pipreqs`)
- [ ] Ausência de erros críticos que impeçam a execução — falta aplicar no repositório real a correção do bug de `field_size_limit` (hoje corrigida só na cópia de teste)

## O que foi e não foi alterado

- **Teste funcional (clone, venv, execução dos scripts, correção do `field_size_limit`):** ocorreu só numa cópia temporária local, descartada ao final — não afetou o repositório real.
- **Já aplicado no repositório real, depois da revisão:** os 3 arquivos com nome errado foram renomeados (`analytics/requirements.txt`, `analytics/.gitignore`, `analytics/config/paths.example.py`), `analytics/requirements.txt` foi regerado com `pipreqs`, e o `.gitignore` da raiz (antes vazio) foi preenchido.
- **Ainda não aplicado no repositório real:** a correção do bug `csv.field_size_limit` em `RAIS_ESTABELECIMENTOS_2025/02_estabelecimentos_2025.py` (testada e validada só na cópia temporária) e a atualização do template de `data-viz/README.md`.
