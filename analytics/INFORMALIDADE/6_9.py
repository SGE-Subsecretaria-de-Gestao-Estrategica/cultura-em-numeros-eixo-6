import os
import pandas as pd

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

CAMINHO_XLSX_ENTRADA = r"E:\Rais\Rais\Informalidade\Informalidade2.xlsx"
DIRETORIO_SAIDA = r"E:\Rais\Rais\csvs"

ARQUIVO_SAIDA_ESTADUAL = os.path.join(DIRETORIO_SAIDA, "6.9.1.csv")
ARQUIVO_SAIDA_MUNICIPAL = os.path.join(DIRETORIO_SAIDA, "6.9.2.csv")

ANO_REFERENCIA = 2024
ESCOPO_ORIGEM = "Cultura"
NOME_GRUPO_SAIDA = "Economia Criativa"

COLUNAS_OBRIGATORIAS = [
    "Escopo",
    "Escala",
    "Recorte",
    "Ano",
    "Formal - Total",
    "Informal - Total",
]

COLUNAS_SAIDA = [
    "grupo",
    "Escala",
    "Recorte",
    "Ano",
    "Formal - Total",
    "Informal - Total",
]


# =============================================================================
# FUNÇÕES
# =============================================================================

def validar_colunas(df: pd.DataFrame) -> None:
    """Verifica se todas as colunas necessárias existem no arquivo de origem."""
    colunas_ausentes = sorted(
        set(COLUNAS_OBRIGATORIAS) - set(df.columns)
    )

    if colunas_ausentes:
        raise KeyError(
            "As seguintes colunas obrigatórias não foram encontradas no "
            f"arquivo de origem: {', '.join(colunas_ausentes)}."
        )


def padronizar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza os nomes das colunas, textos e tipos numéricos."""
    df = df.copy()

    df.columns = df.columns.astype(str).str.strip()
    validar_colunas(df)

    for coluna in ["Escopo", "Escala", "Recorte"]:
        df[coluna] = df[coluna].fillna("").astype(str).str.strip()

    for coluna in ["Ano", "Formal - Total", "Informal - Total"]:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    return df


def gerar_csv_por_escala(
    df: pd.DataFrame,
    escala: str,
    caminho_saida: str,
) -> None:
    """
    Filtra os dados de Economia Criativa para o ano de referência e uma
    escala geográfica específica, salvando o resultado em CSV.
    """
    filtro = (
        df["Escopo"].str.casefold().eq(ESCOPO_ORIGEM.casefold())
        & df["Escala"].str.casefold().eq(escala.casefold())
        & df["Ano"].eq(ANO_REFERENCIA)
    )

    resultado = df.loc[
        filtro,
        ["Escala", "Recorte", "Ano", "Formal - Total", "Informal - Total"],
    ].copy()

    if resultado.empty:
        raise ValueError(
            f"Nenhum registro encontrado para Escopo='{ESCOPO_ORIGEM}', "
            f"Escala='{escala}' e Ano={ANO_REFERENCIA}."
        )

    resultado.insert(0, "grupo", NOME_GRUPO_SAIDA)

    resultado["Ano"] = resultado["Ano"].astype(int)

    resultado = resultado.sort_values(
        by=["Recorte", "Ano"],
        ascending=[True, True],
        kind="stable",
    ).reset_index(drop=True)

    resultado = resultado[COLUNAS_SAIDA]

    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)

    resultado.to_csv(
        caminho_saida,
        index=False,
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
    )

    print(f"Arquivo gerado com sucesso: {caminho_saida}")
    print(f"Registros exportados: {len(resultado)}")


# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================

def main() -> None:
    """Executa a leitura, o tratamento e a exportação dos dois arquivos CSV."""
    try:
        if not os.path.isfile(CAMINHO_XLSX_ENTRADA):
            raise FileNotFoundError(
                f"Arquivo de entrada não encontrado: {CAMINHO_XLSX_ENTRADA}"
            )

        df = pd.read_excel(CAMINHO_XLSX_ENTRADA)
        df = padronizar_dados(df)

        gerar_csv_por_escala(
            df=df,
            escala="Estadual",
            caminho_saida=ARQUIVO_SAIDA_ESTADUAL,
        )

        gerar_csv_por_escala(
            df=df,
            escala="Municipal",
            caminho_saida=ARQUIVO_SAIDA_MUNICIPAL,
        )

    except FileNotFoundError as erro:
        print(f"Erro: {erro}")

    except (KeyError, ValueError) as erro:
        print(f"Erro de validação dos dados: {erro}")

    except Exception as erro:
        print(f"Erro inesperado ao processar os arquivos: {erro}")


if __name__ == "__main__":
    main()