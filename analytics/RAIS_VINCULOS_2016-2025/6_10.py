import os
import re
import numpy as np
import pandas as pd

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

CAMINHO_CSV_ENTRADA = (
    r"E:\Rais\Rais\DF1\data\rais_metricas_grupos_2016_2025_com_informalidade.csv"
)
DIRETORIO_SAIDA = r"E:\Rais\Rais\csvs"

ARQUIVO_SAIDA_CAPITAIS = os.path.join(DIRETORIO_SAIDA, "6.10.1.csv")
ARQUIVO_SAIDA_UFS      = os.path.join(DIRETORIO_SAIDA, "6.10.2.csv")

ANO_REFERENCIA = 2024


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def parse_num(valor):
    """Converte números em formatos brasileiros e notação científica."""
    if pd.isna(valor):
        return np.nan

    s = str(valor).strip()

    if s in ("", "nan", "None"):
        return np.nan

    if "E" in s.upper():
        s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return np.nan

    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", s):
        s = s.replace(".", "")
    else:
        s = s.replace(",", ".")

    try:
        return float(s)
    except ValueError:
        return np.nan


def calcular_participacao(df: pd.DataFrame, prefixo: str) -> pd.DataFrame:
    """
    Para um dado prefixo ('Capital' ou 'UF'), identifica os pares
    Total / Cultura, calcula o total de vínculos (formal + informal)
    e retorna a participação da Economia Criativa por localidade.
    """
    # Filtra apenas as linhas do prefixo e ano de referência
    mascara = (
        df["grupo"].str.startswith(prefixo, na=False)
        & df["ano"].eq(ANO_REFERENCIA)
    )
    recorte = df.loc[mascara].copy()

    if recorte.empty:
        raise ValueError(
            f"Nenhum registro encontrado para prefixo='{prefixo}' "
            f"e ano={ANO_REFERENCIA}."
        )

    # Extrai localidade e tipo (Total / Cultura) a partir da coluna 'grupo'
    # Padrão esperado: "Prefixo - Localidade - Tipo"
    partes = recorte["grupo"].str.extract(
        r"^(?P<prefixo>[^-]+?)\s*-\s*(?P<localidade>.+?)\s*[-–]\s*(?P<tipo>[^-–]+)$"
    )
    recorte = recorte.copy()
    recorte["localidade"] = partes["localidade"].str.strip()
    recorte["tipo"]       = partes["tipo"].str.strip()

    # Calcula total de vínculos: formal + informal estimado
    recorte["total_vinculos_combinado"] = (
        recorte["total_vinculos"].fillna(0)
        + recorte["total_vinculos_informais_estimado"].fillna(0)
    )

    # Separa Total e Cultura
    total_loc = (
        recorte.loc[recorte["tipo"].str.casefold() == "total"]
        .groupby("localidade", as_index=False)["total_vinculos_combinado"]
        .sum()
        .rename(columns={"total_vinculos_combinado": "total_geral"})
    )

    cultura_loc = (
        recorte.loc[recorte["tipo"].str.casefold() == "cultura"]
        .groupby("localidade", as_index=False)["total_vinculos_combinado"]
        .sum()
        .rename(columns={"total_vinculos_combinado": "total_cultura"})
    )

    if total_loc.empty:
        raise ValueError(
            f"Nenhum registro do tipo 'Total' encontrado para prefixo='{prefixo}'."
        )
    if cultura_loc.empty:
        raise ValueError(
            f"Nenhum registro do tipo 'Cultura' encontrado para prefixo='{prefixo}'."
        )

    # Merge e cálculo da participação decimal
    dados = pd.merge(total_loc, cultura_loc, on="localidade", how="inner")
    dados["participacao_ec"] = dados["total_cultura"] / dados["total_geral"]
    dados["ano"] = ANO_REFERENCIA

    return (
        dados[["localidade", "ano", "participacao_ec"]]
        .sort_values("localidade")
        .reset_index(drop=True)
    )


def salvar_csv(df: pd.DataFrame, caminho: str) -> None:
    """Salva o DataFrame em CSV no padrão brasileiro."""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    df.to_csv(
        caminho,
        index=False,
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
    )

    print(f"Arquivo gerado com sucesso: {caminho}")
    print(f"Registros exportados: {len(df)}\n")


# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================

def main() -> None:
    try:
        if not os.path.isfile(CAMINHO_CSV_ENTRADA):
            raise FileNotFoundError(
                f"Arquivo de entrada não encontrado: {CAMINHO_CSV_ENTRADA}"
            )

        # Leitura
        df = pd.read_csv(CAMINHO_CSV_ENTRADA, sep=";", dtype=str)
        df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]

        # Valida colunas obrigatórias
        colunas_necessarias = [
            "grupo", "ano",
            "total_vinculos",
            "total_vinculos_informais_estimado",
        ]
        colunas_ausentes = sorted(set(colunas_necessarias) - set(df.columns))
        if colunas_ausentes:
            raise KeyError(
                "Colunas ausentes no arquivo de origem: "
                + ", ".join(colunas_ausentes)
            )

        # Converte colunas numéricas
        df["ano"] = df["ano"].apply(parse_num).astype("Int64")
        for col in ["total_vinculos", "total_vinculos_informais_estimado"]:
            df[col] = df[col].apply(parse_num)

        # Gera os dois CSVs
        capitais = calcular_participacao(df, prefixo="Capital")
        salvar_csv(capitais, ARQUIVO_SAIDA_CAPITAIS)

        ufs = calcular_participacao(df, prefixo="UF")
        salvar_csv(ufs, ARQUIVO_SAIDA_UFS)

    except FileNotFoundError as erro:
        print(f"Erro: {erro}")

    except (KeyError, ValueError) as erro:
        print(f"Erro de validação dos dados: {erro}")

    except Exception as erro:
        print(f"Erro inesperado: {erro}")


if __name__ == "__main__":
    main()