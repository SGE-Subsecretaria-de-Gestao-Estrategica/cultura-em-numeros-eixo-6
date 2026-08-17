from __future__ import annotations

from pathlib import Path
import pandas as pd

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

ARQUIVO_BASE          = Path(r"D:\OneDrive\Minc\RAIS\RAIS_py\data\processed\rais_2025_filtrado.csv")
ARQUIVO_CNAE_CRIATIVA = Path(r"E:\Rais\Rais\Auxiliares\CNAE-ibge.xlsx")
ARQUIVO_SAIDA         = Path(r"E:\Rais\Rais\csvs\6.20.csv")

CHUNK_SIZE = 300_000

COL_CNAE_BASE   = "CNAE 2.0 Subclasse - Código"
COL_CNAE_AUX    = "CNAE_IBGE"
COL_DOMINIO     = "Domínio Cultural"
COL_SALARIO     = "vl_rem_media_nom_deflacionada_2024"
COL_SEXO        = "Sexo - Código"

MAPA_SEXO = {"1": "Masculino", "2": "Feminino"}


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
        for caminho in [ARQUIVO_BASE, ARQUIVO_CNAE_CRIATIVA]:
            if not caminho.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

        # ── Tabela auxiliar CNAE → Domínio Cultural ───────────────────────────
        df_cnae = pd.read_excel(
            ARQUIVO_CNAE_CRIATIVA,
            usecols=[COL_CNAE_AUX, COL_DOMINIO],
            dtype=str,
        )
        df_cnae.columns = [c.strip() for c in df_cnae.columns]
        df_cnae["cnae_norm"] = normalizar_cnae(df_cnae[COL_CNAE_AUX])
        df_cnae[COL_DOMINIO] = df_cnae[COL_DOMINIO].astype("string").str.strip()
        df_cnae = df_cnae.dropna(subset=["cnae_norm", COL_DOMINIO])
        df_cnae = df_cnae[["cnae_norm", COL_DOMINIO]].drop_duplicates(subset=["cnae_norm"])

        cnaes_criativos = set(df_cnae["cnae_norm"])

        if not cnaes_criativos:
            raise ValueError(f"Nenhum CNAE válido encontrado em {ARQUIVO_CNAE_CRIATIVA}.")

        # Dicionário cnae -> domínio para lookup rápido
        mapa_dominio: dict[str, str] = dict(
            zip(df_cnae["cnae_norm"], df_cnae[COL_DOMINIO])
        )

        print(f"CNAEs da Economia Criativa carregados: {len(cnaes_criativos):,}")
        print(f"\nProcessando arquivo base em chunks de {CHUNK_SIZE:,} linhas...")

        # ── Acumuladores: (domínio, sexo) -> soma e contagem ─────────────────
        soma:  dict[tuple[str, str], float] = {}
        qtd:   dict[tuple[str, str], int]   = {}

        leitor = pd.read_csv(
            ARQUIVO_BASE,
            sep=";",
            encoding="utf-8-sig",
            usecols=[COL_CNAE_BASE, COL_SALARIO, COL_SEXO],
            dtype=str,
            chunksize=CHUNK_SIZE,
            low_memory=False,
        )

        for i, chunk in enumerate(leitor, 1):
            # Filtra Economia Criativa
            cnae_norm = normalizar_cnae(chunk[COL_CNAE_BASE])
            chunk = chunk[cnae_norm.isin(cnaes_criativos)].copy()
            cnae_norm = normalizar_cnae(chunk[COL_CNAE_BASE])

            if chunk.empty:
                print(f"  Chunk {i}: nenhum registro de EC.")
                continue

            # Mapeia domínio cultural
            chunk["dominio"] = cnae_norm.map(mapa_dominio)

            # Normaliza sexo
            chunk["sexo_cod"] = (
                chunk[COL_SEXO].astype("string")
                .str.strip()
                .str.replace(r"\.0$", "", regex=True)
            )
            chunk["sexo"] = chunk["sexo_cod"].map(MAPA_SEXO)

            # Converte salário e filtra > 0
            chunk["salario"] = converter_numero_brasileiro(chunk[COL_SALARIO])
            chunk = chunk[
                (chunk["salario"] > 0) &
                chunk["dominio"].notna() &
                chunk["sexo"].notna()
            ].copy()

            if chunk.empty:
                print(f"  Chunk {i}: nenhum registro válido após filtros.")
                continue

            # Acumula por (domínio, sexo)
            agrupado = chunk.groupby(["dominio", "sexo"])["salario"].agg(["sum", "count"])
            for (dominio, sexo), row in agrupado.iterrows():
                chave = (dominio, sexo)
                soma[chave] = soma.get(chave, 0.0) + float(row["sum"])
                qtd[chave]  = qtd.get(chave, 0)   + int(row["count"])

            print(f"  Chunk {i} processado.")

        if not soma:
            raise ValueError(
                "Nenhum dado acumulado após os filtros. "
                "Verifique os arquivos de entrada."
            )

        # ── Monta DataFrame final ─────────────────────────────────────────────
        registros = []
        for (dominio, sexo), soma_val in soma.items():
            qtd_val = qtd[(dominio, sexo)]
            registros.append({
                "dominio_cultural": dominio,
                "sexo":             sexo,
                "media_salarial":   round(soma_val / qtd_val, 2) if qtd_val > 0 else None,
            })

        resultado = (
            pd.DataFrame(registros)
            .sort_values(["dominio_cultural", "sexo"])
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

    except FileNotFoundError as erro:
        print(f"Erro: {erro}")

    except (KeyError, ValueError) as erro:
        print(f"Erro de validação dos dados: {erro}")

    except Exception as erro:
        print(f"Erro inesperado: {erro}")


if __name__ == "__main__":
    main()