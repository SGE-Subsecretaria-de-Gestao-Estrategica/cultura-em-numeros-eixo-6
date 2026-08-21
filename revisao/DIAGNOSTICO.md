# Pontos de melhoria — pipeline `analytics/` (Eixo 6)

Lista de ajustes para deixar o pipeline executável por qualquer pessoa que clonar o repositório, sem precisar editar os scripts manualmente. A documentação em si (`analytics/README.md`) já está muito completa — os pontos abaixo são sobre o código e a nomenclatura dos arquivos.

## Bloqueante (impede a execução em outra máquina)

1. **`csv.field_size_limit(sys.maxsize)` quebra em qualquer instalação Windows.**
   Em `RAIS_ESTABELECIMENTOS_2025/02_estabelecimentos_2025.py`, linha 27. `sys.maxsize` é um inteiro de 64 bits, mas essa função espera um C `long` (32 bits no Windows) — a chamada sempre lança `OverflowError`, independente de path ou dado de entrada.
   **Sugestão testada:**
   ```diff
   - csv.field_size_limit(sys.maxsize)
   + csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
   ```

## Observação sobre os caminhos absolutos (não é um bug)

Os scripts leem e gravam diretamente em `D:\OneDrive\Minc\RAIS\...`, `E:\Rais\...` etc. — caminhos absolutos do ambiente de quem escreveu o script. Isso é intencional: as bases da RAIS são grandes demais para ficarem dentro do repositório, então o pipeline sempre vai puxar os dados de um local externo (OneDrive, disco externo), não do próprio repo. Não é um problema a corrigir.

O único ponto que ainda vale considerar, sem mudar onde os dados ficam: como o caminho é uma constante fixa por script, quem for rodar em outra máquina (outro drive, outra pasta de OneDrive) precisa editar cada script manualmente para apontar pro lugar certo. Isso já é simples hoje, porque cada script usa `pathlib.Path` numa constante clara no topo do arquivo — é só trocar o valor. Se um dia isso incomodar, a alternativa seria centralizar essas constantes em `analytics/config/paths.py` (o template já existe em `config/`), editando um arquivo só em vez de cada script — mas isso é opcional, não uma correção necessária.

## Nomenclatura de arquivos (extensão `.txt` sobrando)

Alguns arquivos tinham uma extensão extra, o que fazia o Git/pip não reconhecê-los como deveriam:

| Arquivo atual | Deveria ser | Por quê | Status |
|---|---|---|---|
| `analytics/requirements.txt.txt` | `analytics/requirements.txt` | `pip install -r requirements.txt` não encontrava o arquivo | ✅ Corrigido — regerado com `pipreqs` (ver passo a passo abaixo) |
| `analytics/.gitignore.txt` | `analytics/.gitignore` | O Git não aplicava essas regras (risco de versionar `data/raw/`, `config/paths.py` etc. por engano) | ✅ Corrigido |
| `analytics/config/paths.example.py.txt` | `analytics/config/paths.example.py` | Não é reconhecido como módulo Python | ✅ Corrigido |

O `.gitignore` da raiz do repositório estava vazio — ✅ preenchido com `.venv/`, `__pycache__/`, `.env` e arquivos de sistema/editor.

## Como gerar o `requirements.txt` (passo a passo)

O `analytics/requirements.txt` foi regerado com a ferramenta `pipreqs`, que escaneia os `imports` de fato usados no código (em vez de listar tudo que está instalado no ambiente, como faz `pip freeze`). Passo a passo para reproduzir ou atualizar:

1. Instalar a ferramenta:
   ```bash
   pip install pipreqs
   ```
2. Rodar apontando para a pasta do projeto (a partir da raiz do repositório):
   ```bash
   cd analytics
   pipreqs . --force
   ```
   `--force` sobrescreve o `requirements.txt` existente. Sem o `--force`, o comando falha se o arquivo já existir.
3. **Revisar manualmente o resultado.** O `pipreqs` só detecta pacotes que aparecem em `import`/`from` no código — ele não pega dependências usadas indiretamente. Neste projeto, isso significa que `xlrd` (necessário para o pandas ler arquivos `.xls` antigos, como `IPCA_mensal.xls`) não aparece automaticamente e precisa ser adicionado à mão.
4. Resultado atual (`analytics/requirements.txt`):
   ```text
   numpy==2.5.2
   openpyxl==3.1.5
   pandas==3.0.5
   xlrd==2.0.2
   ```
5. Testar a instalação em um ambiente limpo antes de considerar concluído:
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

Sempre que um script novo passar a importar uma biblioteca nova, repita os passos 2–3 para manter o arquivo atualizado.