from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pandas as pd

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

ARQUIVO_BASE          = Path(r"D:\OneDrive\Minc\RAIS\RAIS_py\data\processed\rais_2025_filtrado.csv")
ARQUIVO_CNAE_CRIATIVA = Path(r"E:\Rais\Rais\Auxiliares\CNAE-ibge.xlsx")
ARQUIVO_SAIDA         = Path(r"E:\Rais\Rais\csvs\6.26.csv")

CHUNK_SIZE = 300_000

COL_CNAE      = "CNAE 2.0 Subclasse - Código"
COL_CNAE_AUX  = "CNAE_IBGE"
COL_DOMINIO   = "Domínio Cultural"
COL_SALARIO   = "vl_rem_media_nom_deflacionada_2024"


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
        df_aux = pd.read_excel(
            ARQUIVO_CNAE_CRIATIVA,
            usecols=[COL_CNAE_AUX, COL_DOMINIO],
            dtype=str,
        )
        df_aux.columns = [c.strip() for c in df_aux.columns]
        df_aux[COL_CNAE_AUX] = normalizar_cnae(df_aux[COL_CNAE_AUX])
        df_aux[COL_DOMINIO]  = df_aux[COL_DOMINIO].astype("string").str.strip()
        df_aux = df_aux.dropna(subset=[COL_CNAE_AUX, COL_DOMINIO]).drop_duplicates(subset=[COL_CNAE_AUX])

        mapa_cnae_dominio = dict(zip(df_aux[COL_CNAE_AUX], df_aux[COL_DOMINIO]))
        cnaes_criativos   = set(mapa_cnae_dominio.keys())

        if not cnaes_criativos:
            raise ValueError(f"Nenhum CNAE válido encontrado em {ARQUIVO_CNAE_CRIATIVA}.")

        print(f"CNAEs da Economia Criativa carregados: {len(cnaes_criativos):,}")
        print(f"\nProcessando arquivo base em chunks de {CHUNK_SIZE:,} linhas...")

        # ── Acumuladores: domínio -> vínculos, soma salarial e quantidade ────
        acumulador_vinculos: dict[str, int] = defaultdict(int)
        soma_salarios: dict[str, float] = defaultdict(float)
        qtd_salarios_validos: dict[str, int] = defaultdict(int)

        leitor = pd.read_csv(
            ARQUIVO_BASE,
            sep=";",
            encoding="utf-8-sig",
            usecols=[COL_CNAE, COL_SALARIO],
            dtype=str,
            chunksize=CHUNK_SIZE,
            low_memory=False,
        )

        for i, chunk in enumerate(leitor, 1):
            cnae_norm = normalizar_cnae(chunk[COL_CNAE])
            chunk = chunk[cnae_norm.isin(cnaes_criativos)].copy()
            cnae_norm = normalizar_cnae(chunk[COL_CNAE])

            if chunk.empty:
                print(f"  Chunk {i}: nenhum registro de EC.")
                continue

            chunk["dominio"] = cnae_norm.map(mapa_cnae_dominio)
            chunk = chunk.dropna(subset=["dominio"])

            for dominio, qtd in chunk["dominio"].value_counts().items():
                acumulador_vinculos[dominio] += int(qtd)

            # Calcula salário médio usando somente valores positivos.
            chunk["salario"] = converter_numero_brasileiro(chunk[COL_SALARIO])
            salarios_validos = chunk[chunk["salario"] > 0]

            if not salarios_validos.empty:
                agrupado_salarios = salarios_validos.groupby("dominio")["salario"].agg(["sum", "count"])
                for dominio, linha in agrupado_salarios.iterrows():
                    soma_salarios[dominio] += float(linha["sum"])
                    qtd_salarios_validos[dominio] += int(linha["count"])

            print(f"  Chunk {i} processado.")

        if not acumulador_vinculos:
            raise ValueError(
                "Nenhum vínculo encontrado após os filtros. "
                "Verifique os arquivos de entrada."
            )

        # ── Monta DataFrame final ─────────────────────────────────────────────
        resultado = (
            pd.DataFrame([
                {
                    "dominio_cultural": dominio,
                    "total_vinculos": qtd,
                    "media_salarial": round(
                        soma_salarios[dominio] / qtd_salarios_validos[dominio], 2
                    ) if qtd_salarios_validos[dominio] > 0 else None,
                }
                for dominio, qtd in acumulador_vinculos.items()
            ])
            .sort_values("total_vinculos", ascending=False)
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