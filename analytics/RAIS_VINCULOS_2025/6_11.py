import os
import pandas as pd

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

CAMINHO_BASE        = r"D:\OneDrive\Minc\RAIS\RAIS_py\data\processed\rais_2025_filtrado.csv"
CAMINHO_CNAE        = r"E:\Rais\Rais\Auxiliares\CNAE-ibge.xlsx"
CAMINHO_MUNICIPIOS  = r"E:\Rais\Rais\Auxiliares\municipios.xlsx"
ARQUIVO_SAIDA       = r"E:\Rais\Rais\csvs\ec_por_1000_trabalhadores_municipios.csv"

TAMANHO_CHUNK       = 300_000

COL_CNAE_BASE       = "CNAE 2.0 Subclasse - Código"
COL_CNAE_IBGE       = "CNAE_IBGE"
COL_MUN_BASE        = "Município - Código"
COL_MUN_AUX         = "Cod_Município"
COL_MUN_NOME        = "Município"


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def padronizar_cod_municipio_base(serie: pd.Series) -> pd.Series:
    """
    Garante 6 dígitos no código do município vindo do arquivo base:
    - Se vier com 5 dígitos, acrescenta zero à esquerda.
    - Converte para string e remove espaços.
    """
    return (
        serie.astype(str)
        .str.strip()
        .str.zfill(6)
    )


def padronizar_cod_municipio_aux(serie: pd.Series) -> pd.Series:
    """
    Reduz o código de 7 dígitos da tabela auxiliar para 6,
    descartando o último dígito (dígito verificador).
    """
    return (
        serie.astype(str)
        .str.strip()
        .str[:6]
    )


def carregar_codigos_ec(caminho: str) -> set:
    """Carrega os códigos CNAE da Economia Criativa como um conjunto de strings."""
    df = pd.read_excel(caminho, dtype=str)
    df.columns = df.columns.str.strip()

    if COL_CNAE_IBGE not in df.columns:
        raise KeyError(
            f"Coluna '{COL_CNAE_IBGE}' não encontrada em {caminho}. "
            f"Colunas disponíveis: {df.columns.tolist()}"
        )

    codigos = (
        df[COL_CNAE_IBGE]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    print(f"Códigos CNAE da Economia Criativa carregados: {len(codigos)}")
    return set(codigos)


def carregar_municipios(caminho: str) -> pd.DataFrame:
    """
    Carrega a tabela de municípios, retornando um DataFrame com:
    - cod_6: primeiros 6 dígitos do código (chave de join)
    - cod_7: código original de 7 dígitos (para o CSV final)
    - nome_municipio: nome do município
    """
    df = pd.read_excel(caminho, dtype=str)
    df.columns = df.columns.str.strip()

    colunas_necessarias = [COL_MUN_AUX, COL_MUN_NOME]
    ausentes = sorted(set(colunas_necessarias) - set(df.columns))
    if ausentes:
        raise KeyError(
            f"Colunas ausentes em {caminho}: {', '.join(ausentes)}"
        )

    df["cod_7"] = df[COL_MUN_AUX].astype(str).str.strip().str.zfill(7)
    df["cod_6"] = df["cod_7"].str[:6]
    df["nome_municipio"] = df[COL_MUN_NOME].astype(str).str.strip()

    print(f"Municípios carregados: {len(df)}")
    return df[["cod_6", "cod_7", "nome_municipio"]].drop_duplicates(subset="cod_6")


def detectar_separador(caminho: str) -> str:
    """Detecta automaticamente o separador do CSV (ponto e vírgula ou vírgula)."""
    with open(caminho, "r", encoding="utf-8", errors="replace") as f:
        primeira_linha = f.readline()
    return ";" if primeira_linha.count(";") >= primeira_linha.count(",") else ","


# =============================================================================
# PROCESSAMENTO PRINCIPAL
# =============================================================================

def processar_chunks(
    caminho: str,
    codigos_ec: set,
    separador: str,
) -> tuple[pd.Series, pd.Series]:
    """
    Lê o arquivo base em chunks e acumula:
    - contagem_total: total de trabalhadores por município (cod_6)
    - contagem_ec:    trabalhadores da Economia Criativa por município (cod_6)
    """
    contagem_total = pd.Series(dtype="int64")
    contagem_ec    = pd.Series(dtype="int64")

    chunks_lidos = 0

    for chunk in pd.read_csv(
        caminho,
        sep=separador,
        dtype=str,
        chunksize=TAMANHO_CHUNK,
        encoding="utf-8",
        on_bad_lines="skip",
    ):
        chunk.columns = chunk.columns.str.strip()

        colunas_necessarias = [COL_CNAE_BASE, COL_MUN_BASE]
        ausentes = sorted(set(colunas_necessarias) - set(chunk.columns))
        if ausentes:
            raise KeyError(
                f"Colunas ausentes no arquivo base: {', '.join(ausentes)}"
            )

        # Padroniza código do município para 6 dígitos
        chunk["cod_6"] = padronizar_cod_municipio_base(chunk[COL_MUN_BASE])

        # Padroniza código CNAE
        chunk[COL_CNAE_BASE] = chunk[COL_CNAE_BASE].astype(str).str.strip()

        # Acumula total geral por município
        total_chunk = chunk.groupby("cod_6").size()
        contagem_total = contagem_total.add(total_chunk, fill_value=0)

        # Filtra Economia Criativa e acumula por município
        ec_chunk = chunk.loc[chunk[COL_CNAE_BASE].isin(codigos_ec)]
        if not ec_chunk.empty:
            ec_por_mun = ec_chunk.groupby("cod_6").size()
            contagem_ec = contagem_ec.add(ec_por_mun, fill_value=0)

        chunks_lidos += 1
        print(f"  Chunk {chunks_lidos} processado ({len(chunk):,} linhas).")

    return contagem_total.astype(int), contagem_ec.astype(int)


# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================

def main() -> None:
    try:
        for caminho in [CAMINHO_BASE, CAMINHO_CNAE, CAMINHO_MUNICIPIOS]:
            if not os.path.isfile(caminho):
                raise FileNotFoundError(
                    f"Arquivo não encontrado: {caminho}"
                )

        print("Carregando códigos CNAE da Economia Criativa...")
        codigos_ec = carregar_codigos_ec(CAMINHO_CNAE)

        print("\nCarregando tabela de municípios...")
        municipios = carregar_municipios(CAMINHO_MUNICIPIOS)

        print(f"\nProcessando arquivo base em chunks de {TAMANHO_CHUNK:,} linhas...")
        separador = detectar_separador(CAMINHO_BASE)
        contagem_total, contagem_ec = processar_chunks(
            CAMINHO_BASE, codigos_ec, separador
        )

        # Monta o DataFrame de resultados
        resultado = pd.DataFrame({
            "cod_6":            contagem_total.index,
            "total_trabalhadores": contagem_total.values,
        })

        resultado["trabalhadores_ec"] = (
            resultado["cod_6"].map(contagem_ec).fillna(0).astype(int)
        )

        # Calcula a taxa por 1.000 trabalhadores
        resultado["ec_por_1000_trabalhadores"] = (
            resultado["trabalhadores_ec"] / resultado["total_trabalhadores"] * 1_000
        ).round(2)

        # Vincula com a tabela de municípios
        resultado = resultado.merge(municipios, on="cod_6", how="left")

        municipios_sem_nome = resultado["nome_municipio"].isna().sum()
        if municipios_sem_nome > 0:
            print(
                f"\nAviso: {municipios_sem_nome} município(s) sem correspondência "
                "na tabela auxiliar."
            )

        # Monta o CSV final com as colunas solicitadas
        saida = resultado[[
            "cod_7",
            "nome_municipio",
            "ec_por_1000_trabalhadores",
        ]].rename(columns={
            "cod_7":                    "codigo_municipio",
            "nome_municipio":           "nome_municipio",
            "ec_por_1000_trabalhadores": "ec_por_1000_trabalhadores",
        }).sort_values("nome_municipio").reset_index(drop=True)

        os.makedirs(os.path.dirname(ARQUIVO_SAIDA), exist_ok=True)

        saida.to_csv(
            ARQUIVO_SAIDA,
            index=False,
            sep=";",
            decimal=",",
            encoding="utf-8-sig",
        )

        print(f"\nCSV gerado com sucesso: {ARQUIVO_SAIDA}")
        print(f"Total de municípios exportados: {len(saida)}")

    except FileNotFoundError as erro:
        print(f"Erro: {erro}")

    except (KeyError, ValueError) as erro:
        print(f"Erro de validação dos dados: {erro}")

    except Exception as erro:
        print(f"Erro inesperado: {erro}")


if __name__ == "__main__":
    main()