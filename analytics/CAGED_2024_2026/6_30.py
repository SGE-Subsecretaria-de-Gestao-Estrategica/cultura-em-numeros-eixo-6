from __future__ import annotations

from pathlib import Path

import pandas as pd

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

ARQUIVO_ENTRADA = Path(r"E:\Rais\CAGED\data\caged_IRCA_final_2016_2026.csv")
ARQUIVO_SAIDA = Path(r"E:\Rais\Rais\csvs\6.31.csv")

GRUPO_CULTURA = "Cultura"
ROTULO_ECONOMIA_CRIATIVA = "Economia Criativa"
GRUPO_BRASIL = "Brasil"
DATA_CORTE = pd.Timestamp("2024-12-01")

COL_ANO = "ano"
COL_MES = "mes"
COL_GRUPO = "grupo"
COL_IRCA_VINCULOS = "IRCA_Vinculos"
COL_IRCA_SALARIAL = "IRCA_Salarial"


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def preparar_dados(df_origem: pd.DataFrame, grupo: str) -> pd.DataFrame:
    """
    Filtra os dados de um grupo e calcula as variações em relação
    à base 100 de dezembro de 2024.

    A saída adota o padrão decimal:
    0.025 representa 2,5%.
    """
    df_grupo = df_origem[
        df_origem[COL_GRUPO]
        .astype(str)
        .str.strip()
        .str.lower() == grupo.lower()
    ].copy()

    if df_grupo.empty:
        return df_grupo

    df_grupo[COL_ANO] = pd.to_numeric(df_grupo[COL_ANO], errors="coerce")
    df_grupo[COL_MES] = pd.to_numeric(df_grupo[COL_MES], errors="coerce")

    df_grupo["data"] = pd.to_datetime(
        {
            "year": df_grupo[COL_ANO],
            "month": df_grupo[COL_MES],
            "day": 1,
        },
        errors="coerce",
    )

    df_grupo[COL_IRCA_VINCULOS] = pd.to_numeric(
        df_grupo[COL_IRCA_VINCULOS],
        errors="coerce",
    )
    df_grupo[COL_IRCA_SALARIAL] = pd.to_numeric(
        df_grupo[COL_IRCA_SALARIAL],
        errors="coerce",
    )

    df_grupo = (
        df_grupo
        .dropna(subset=["data", COL_IRCA_VINCULOS, COL_IRCA_SALARIAL])
        .sort_values("data")
        .reset_index(drop=True)
    )

    # O IRCA está em base 100.
    # Exemplo: IRCA de 102,5 corresponde à variação de 2,5%,
    # exportada como 0.025 no padrão decimal.
    df_grupo["variacao_vinculos_pct"] = (
        (df_grupo[COL_IRCA_VINCULOS] - 100) / 100
    ).round(6)

    df_grupo["variacao_salarial_pct"] = (
        (df_grupo[COL_IRCA_SALARIAL] - 100) / 100
    ).round(6)

    return df_grupo


# =============================================================================
# PROCESSAMENTO PRINCIPAL
# =============================================================================

def main() -> None:
    try:
        if not ARQUIVO_ENTRADA.exists():
            raise FileNotFoundError(
                f"Arquivo de entrada não encontrado: {ARQUIVO_ENTRADA}"
            )

        print("Lendo arquivo CAGED...")

        df = pd.read_csv(
            ARQUIVO_ENTRADA,
            sep=";",
            decimal=",",
            encoding="utf-8-sig",
        )

        colunas_necessarias = {
            COL_ANO,
            COL_MES,
            COL_GRUPO,
            COL_IRCA_VINCULOS,
            COL_IRCA_SALARIAL,
        }

        colunas_ausentes = colunas_necessarias - set(df.columns)
        if colunas_ausentes:
            raise KeyError(
                f"Colunas obrigatórias ausentes no arquivo: {sorted(colunas_ausentes)}"
            )

        print("Preparando dados da Economia Criativa...")
        df_cultura = preparar_dados(df, GRUPO_CULTURA)

        print("Preparando dados do Brasil...")
        df_brasil = preparar_dados(df, GRUPO_BRASIL)

        # Atualizar rótulo para Economia Criativa
        df_cultura[COL_GRUPO] = ROTULO_ECONOMIA_CRIATIVA

        # Manter somente o período representado no gráfico.
        df_cultura = df_cultura[
            df_cultura["data"] >= DATA_CORTE
        ].copy()

        df_brasil = df_brasil[
            df_brasil["data"] >= DATA_CORTE
        ].copy()

        if df_cultura.empty:
            raise ValueError(
                f"Nenhum registro encontrado para {ROTULO_ECONOMIA_CRIATIVA} a partir de dezembro de 2024."
            )

        if df_brasil.empty:
            raise ValueError(
                "Nenhum registro encontrado para Brasil a partir de dezembro de 2024."
            )

        colunas_saida = [
            COL_ANO,
            COL_MES,
            COL_GRUPO,
            "variacao_vinculos_pct",
            "variacao_salarial_pct",
        ]

        resultado = pd.concat(
            [
                df_cultura[colunas_saida],
                df_brasil[colunas_saida],
            ],
            ignore_index=True,
        )

        resultado = (
            resultado
            .sort_values([COL_ANO, COL_MES, COL_GRUPO])
            .reset_index(drop=True)
        )

        ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)

        resultado.to_csv(
            ARQUIVO_SAIDA,
            index=False,
            sep=";",
            decimal=".",
            encoding="utf-8-sig",
        )

        print(f"\nCSV gerado com sucesso: {ARQUIVO_SAIDA}")
        print(f"Total de registros exportados: {len(resultado):,}")

    except FileNotFoundError as erro:
        print(f"Erro: {erro}")

    except KeyError as erro:
        print(f"Erro de estrutura do arquivo: {erro}")

    except ValueError as erro:
        print(f"Erro de validação: {erro}")

    except Exception as erro:
        print(f"Erro inesperado: {erro}")


if __name__ == "__main__":
    main()