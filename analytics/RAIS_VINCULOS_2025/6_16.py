from __future__ import annotations

from pathlib import Path
import pandas as pd

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

ARQUIVO_BASE          = Path(r"D:\OneDrive\Minc\RAIS\RAIS_py\data\processed\rais_2025_filtrado.csv")
ARQUIVO_CNAE_CRIATIVA = Path(r"E:\Rais\Rais\Auxiliares\CNAE-ibge.xlsx")
ARQUIVO_SAIDA         = Path(r"E:\Rais\Rais\csvs\6.16.csv")

CHUNK_SIZE = 300_000

COL_ANO         = "ano"
COL_CNAE        = "CNAE 2.0 Subclasse - Código"
COL_CNAE_AUX    = "CNAE_IBGE"
COL_SALARIO     = "vl_rem_media_nom_deflacionada_2024"
COL_DEFICIENCIA = "Ind Portador Defic - Código"

ANO_REFERENCIA  = "2025"
GRUPOS          = ["Total de trabalhadores", "Economia Criativa"]


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def converter_numero_brasileiro(serie: pd.Series) -> pd.Series:
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


def normalizar_cnae(serie: pd.Series) -> pd.Series:
    return (
        serie.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .replace("", pd.NA)
        .str.zfill(7)
    )


def normalizar_indicador(serie: pd.Series) -> pd.Series:
    return (
        serie.astype("string")
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
        .str.replace(r"\.0$", "", regex=True)
    )


def inicializar_acumuladores() -> dict:
    return {
        grupo: {
            "total_validos":  0,
            "total_sim":      0,
            "soma_sal_sim":   0.0,
            "qtd_sal_sim":    0,
            "soma_sal_nao":   0.0,
            "qtd_sal_nao":    0,
        }
        for grupo in GRUPOS
    }


def acumular(dados: pd.DataFrame, acumuladores: dict, grupo: str) -> None:
    codigo = normalizar_indicador(dados[COL_DEFICIENCIA])
    validos = dados[codigo.notna()].copy()
    cod_validos = codigo.loc[validos.index]

    acumuladores[grupo]["total_validos"] += len(validos)

    sim = validos[cod_validos == "1"].copy()
    acumuladores[grupo]["total_sim"] += len(sim)

    sal_sim = sim[sim["salario"] > 0]
    acumuladores[grupo]["soma_sal_sim"] += float(sal_sim["salario"].sum())
    acumuladores[grupo]["qtd_sal_sim"]  += len(sal_sim)

    nao = validos[cod_validos != "1"].copy()
    sal_nao = nao[nao["salario"] > 0]
    acumuladores[grupo]["soma_sal_nao"] += float(sal_nao["salario"].sum())
    acumuladores[grupo]["qtd_sal_nao"]  += len(sal_nao)


# =============================================================================
# PROCESSAMENTO PRINCIPAL
# =============================================================================

def main() -> None:
    try:
        for caminho in [ARQUIVO_BASE, ARQUIVO_CNAE_CRIATIVA]:
            if not caminho.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

        df_cnae = pd.read_excel(ARQUIVO_CNAE_CRIATIVA, usecols=[COL_CNAE_AUX], dtype=str)
        cnaes_criativos = set(normalizar_cnae(df_cnae[COL_CNAE_AUX]).dropna())

        if not cnaes_criativos:
            raise ValueError(
                f"A coluna '{COL_CNAE_AUX}' não contém CNAEs válidos em {ARQUIVO_CNAE_CRIATIVA}."
            )

        print(f"Códigos CNAE da Economia Criativa carregados: {len(cnaes_criativos):,}")
        print(f"\nProcessando arquivo base em chunks de {CHUNK_SIZE:,} linhas...")

        acumuladores = inicializar_acumuladores()

        leitor = pd.read_csv(
            ARQUIVO_BASE,
            sep=";",
            encoding="utf-8-sig",
            usecols=[COL_ANO, COL_CNAE, COL_SALARIO, COL_DEFICIENCIA],
            dtype=str,
            chunksize=CHUNK_SIZE,
            low_memory=False,
        )

        for i, chunk in enumerate(leitor, 1):
            chunk = chunk[
                chunk[COL_ANO].astype("string").str.strip() == ANO_REFERENCIA
            ].copy()

            if chunk.empty:
                print(f"  Chunk {i}: nenhum registro de {ANO_REFERENCIA}.")
                continue

            chunk["salario"] = converter_numero_brasileiro(chunk[COL_SALARIO])

            acumular(chunk, acumuladores, "Total de trabalhadores")

            chunk_ec = chunk[normalizar_cnae(chunk[COL_CNAE]).isin(cnaes_criativos)].copy()
            if not chunk_ec.empty:
                acumular(chunk_ec, acumuladores, "Economia Criativa")

            print(f"  Chunk {i} processado.")

        # =====================================================================
        # Monta o CSV final — 1 linha por grupo, com todas as métricas
        # =====================================================================
        registros = []

        for grupo in GRUPOS:
            acc = acumuladores[grupo]
            total_validos = acc["total_validos"]
            total_sim     = acc["total_sim"]

            if total_validos == 0:
                continue

            media_sal_sim = (
                round(acc["soma_sal_sim"] / acc["qtd_sal_sim"], 2)
                if acc["qtd_sal_sim"] > 0 else None
            )
            media_sal_nao = (
                round(acc["soma_sal_nao"] / acc["qtd_sal_nao"], 2)
                if acc["qtd_sal_nao"] > 0 else None
            )

            registros.append({
                "grupo":                    grupo,
                "total_vinculos_defic":     total_sim,
                "total_vinculos_validos":   total_validos,
                "participacao_pct":         total_sim / total_validos,
                "media_salarial_com_defic": media_sal_sim,
                "media_salarial_sem_defic": media_sal_nao,
            })

        if not registros:
            raise ValueError(
                "Nenhum dado encontrado após os filtros. "
                "Verifique os arquivos de entrada."
            )

        resultado = pd.DataFrame(registros)

        ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)

        resultado.to_csv(
            ARQUIVO_SAIDA,
            index=False,
            sep=";",
            decimal=".",
            encoding="utf-8-sig",
        )

        print(f"\nCSV gerado com sucesso: {ARQUIVO_SAIDA}")
        print(f"Registros exportados: {len(resultado)}")

    except FileNotFoundError as erro:
        print(f"Erro: {erro}")

    except (KeyError, ValueError) as erro:
        print(f"Erro de validação dos dados: {erro}")

    except Exception as erro:
        print(f"Erro inesperado: {erro}")


if __name__ == "__main__":
    main()