from __future__ import annotations

from pathlib import Path
import pandas as pd

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

ARQUIVO_BASE          = Path(r"D:\OneDrive\Minc\RAIS\RAIS_py\data\processed\rais_2025_filtrado.csv")
ARQUIVO_CNAE_CRIATIVA = Path(r"E:\Rais\Rais\Auxiliares\CNAE-ibge.xlsx")
ARQUIVO_MUNICIPIOS    = Path(r"E:\Rais\Rais\Auxiliares\municipios.xlsx")
ARQUIVO_SAIDA         = Path(r"E:\Rais\Rais\csvs\6.18.csv")

CHUNK_SIZE = 300_000

COL_CNAE_BASE   = "CNAE 2.0 Subclasse - Código"
COL_CNAE_AUX    = "CNAE_IBGE"
COL_SALARIO     = "vl_rem_media_nom_deflacionada_2024"
COL_MUN_BASE    = "Município - Código"


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def normalizar_cnae(serie: pd.Series) -> pd.Series:
    """Padroniza CNAE em sete posições."""
    return (
        serie.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .replace("", pd.NA)
        .str.zfill(7)
    )


def normalizar_cod_municipio_base(serie: pd.Series) -> pd.Series:
    """
    Normaliza código de município da base RAIS para 6 dígitos:
    - Remove decimais (ex: '110001.0' -> '110001')
    - Se 5 dígitos, adiciona zero à esquerda
    - Mantém apenas os 6 primeiros dígitos
    """
    s = (
        serie.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .replace("", pd.NA)
    )
    # Pad para 6 dígitos se vier com 5
    s = s.str.zfill(6)
    # Garante apenas 6 dígitos
    s = s.str[:6]
    return s


def converter_numero_brasileiro(serie: pd.Series) -> pd.Series:
    """Converte strings no formato brasileiro (1.234,56) para float."""
    texto = (
        serie.astype("string")
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    )
    possui_virgula = texto.str.contains(",", na=False)
    texto = texto.where(
        ~possui_virgula,
        texto.str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
    )
    return pd.to_numeric(texto, errors="coerce")


# =============================================================================
# PROCESSAMENTO PRINCIPAL
# =============================================================================

def main() -> None:
    try:
        for caminho in [ARQUIVO_BASE, ARQUIVO_CNAE_CRIATIVA, ARQUIVO_MUNICIPIOS]:
            if not caminho.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

        # ── CNAEs da Economia Criativa ────────────────────────────────────────
        df_cnae = pd.read_excel(ARQUIVO_CNAE_CRIATIVA, usecols=[COL_CNAE_AUX], dtype=str)
        cnaes_criativos = set(normalizar_cnae(df_cnae[COL_CNAE_AUX]).dropna())

        if not cnaes_criativos:
            raise ValueError(f"Nenhum CNAE válido encontrado em {ARQUIVO_CNAE_CRIATIVA}.")

        print(f"CNAEs da Economia Criativa carregados: {len(cnaes_criativos):,}")

        # ── Tabela de municípios ──────────────────────────────────────────────
        df_mun = pd.read_excel(ARQUIVO_MUNICIPIOS, dtype=str)
        df_mun.columns = [c.strip() for c in df_mun.columns]

        # Normaliza Cod_Município da auxiliar: descarta último dígito (7 -> 6)
        df_mun["cod6"] = df_mun["Cod_Município"].astype("string").str.strip().str[:6]

        # Cod_UF a partir dos dois primeiros dígitos do código de 6
        df_mun["cod_uf2"] = df_mun["cod6"].str[:2]

        # Flag capital
        df_mun["is_capital"] = df_mun["Capital"].astype("string").str.strip() == "1"

        # Colunas que queremos preservar no resultado
        COLUNAS_AUX = ["cod6", "cod_uf2", "Município", "Capital", "is_capital",
                       "Cod_UF", "Macrorregiões", "Abrev_Macrorregiões", "Estado"]
        df_mun = df_mun[COLUNAS_AUX].drop_duplicates(subset=["cod6"])

        # ── Acumuladores: soma e contagem por cod6 ────────────────────────────
        soma_por_mun:  dict[str, float] = {}
        qtd_por_mun:   dict[str, int]   = {}

        print(f"\nProcessando arquivo base em chunks de {CHUNK_SIZE:,} linhas...")

        leitor = pd.read_csv(
            ARQUIVO_BASE,
            sep=";",
            encoding="utf-8-sig",
            usecols=[COL_MUN_BASE, COL_CNAE_BASE, COL_SALARIO],
            dtype=str,
            chunksize=CHUNK_SIZE,
            low_memory=False,
        )

        for i, chunk in enumerate(leitor, 1):
            # Filtra Economia Criativa
            chunk = chunk[
                normalizar_cnae(chunk[COL_CNAE_BASE]).isin(cnaes_criativos)
            ].copy()

            if chunk.empty:
                print(f"  Chunk {i}: nenhum registro de EC.")
                continue

            # Normaliza código de município
            chunk["cod6"] = normalizar_cod_municipio_base(chunk[COL_MUN_BASE])

            # Converte salário e filtra > 0
            chunk["salario"] = converter_numero_brasileiro(chunk[COL_SALARIO])
            chunk = chunk[chunk["salario"] > 0].copy()

            if chunk.empty:
                print(f"  Chunk {i}: nenhum salário válido após filtro.")
                continue

            # Acumula por município
            agrupado = chunk.groupby("cod6")["salario"].agg(["sum", "count"])
            for cod, row in agrupado.iterrows():
                soma_por_mun[cod]  = soma_por_mun.get(cod, 0.0)  + float(row["sum"])
                qtd_por_mun[cod]   = qtd_por_mun.get(cod, 0)     + int(row["count"])

            print(f"  Chunk {i} processado.")

        if not soma_por_mun:
            raise ValueError("Nenhum dado acumulado. Verifique os arquivos de entrada.")

        # ── DataFrame de municípios com salário médio ─────────────────────────
        df_result_mun = pd.DataFrame({
            "cod6":          list(soma_por_mun.keys()),
            "soma_salario":  list(soma_por_mun.values()),
            "qtd_salario":   list(qtd_por_mun.values()),
        })
        df_result_mun["media_salarial"] = (
            df_result_mun["soma_salario"] / df_result_mun["qtd_salario"]
        ).round(2)

        # Junta com tabela auxiliar
        df_result_mun = df_result_mun.merge(df_mun, on="cod6", how="left")

        # ── Salário médio por CAPITAL ─────────────────────────────────────────
        df_capitais = df_result_mun[df_result_mun["is_capital"]].copy()
        df_capitais = df_capitais[[
            "Município", "Cod_UF", "Macrorregiões", "Abrev_Macrorregiões",
            "Estado", "media_salarial"
        ]].rename(columns={"Município": "capital"})
        df_capitais["tipo"] = "Capital"

        # ── Salário médio por UF (média ponderada dos municípios da UF) ───────
        df_uf_agg = (
            df_result_mun
            .dropna(subset=["cod_uf2"])
            .groupby("cod_uf2")
            .apply(
                lambda g: pd.Series({
                    "media_salarial": (
                        (g["soma_salario"].sum() / g["qtd_salario"].sum())
                        if g["qtd_salario"].sum() > 0 else None
                    ),
                    "Cod_UF":              g["Cod_UF"].iloc[0],
                    "Macrorregiões":       g["Macrorregiões"].iloc[0],
                    "Abrev_Macrorregiões": g["Abrev_Macrorregiões"].iloc[0],
                    "Estado":              g["Estado"].iloc[0],
                })
            )
            .reset_index(drop=True)
        )
        df_uf_agg["media_salarial"] = df_uf_agg["media_salarial"].astype(float).round(2)
        df_uf_agg["capital"] = None
        df_uf_agg["tipo"]    = "UF"

        # ── Concatena e ordena ────────────────────────────────────────────────
        colunas_finais = [
            "tipo", "capital", "Cod_UF", "Macrorregiões",
            "Abrev_Macrorregiões", "Estado", "media_salarial"
        ]

        resultado = (
            pd.concat([df_capitais[colunas_finais], df_uf_agg[colunas_finais]], ignore_index=True)
            .sort_values(["tipo", "Estado"])
            .reset_index(drop=True)
        )

        # ── Exporta ───────────────────────────────────────────────────────────
        ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)

        resultado.to_csv(
            ARQUIVO_SAIDA,
            index=False,
            sep=";",
            decimal=".",
            encoding="utf-8-sig",
        )

        print(f"\nCSV gerado com sucesso: {ARQUIVO_SAIDA}")
        print(f"Registros exportados : {len(resultado)}")
        print(f"  Capitais : {(resultado['tipo'] == 'Capital').sum()}")
        print(f"  UFs      : {(resultado['tipo'] == 'UF').sum()}")

    except FileNotFoundError as erro:
        print(f"Erro: {erro}")

    except (KeyError, ValueError) as erro:
        print(f"Erro de validação dos dados: {erro}")

    except Exception as erro:
        print(f"Erro inesperado: {erro}")


if __name__ == "__main__":
    main()