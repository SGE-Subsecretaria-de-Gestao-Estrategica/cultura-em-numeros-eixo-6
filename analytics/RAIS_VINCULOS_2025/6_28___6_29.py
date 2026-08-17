from __future__ import annotations

import time
from collections import defaultdict
from pathlib import Path

import pandas as pd

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

FILE_PATH             = Path(r"D:\OneDrive\Minc\RAIS\RAIS_py\data\processed\rais_2025_filtrado.csv")
ARQUIVO_CNAE_CRIATIVA = Path(r"E:\Rais\Rais\Auxiliares\CNAE-ibge.xlsx")
ARQUIVO_SAIDA         = Path(r"E:\Rais\Rais\csvs\6.29_6.30.csv")

CHUNK_SIZE = 300_000

COL_ANO  = "ano"
COL_NJ   = "Natureza Jurídica - Código"
COL_TAM  = "Tamanho Estabelecimento - Código"
COL_SAL  = "vl_rem_media_nom_deflacionada_2024"
COL_CNAE = "CNAE 2.0 Subclasse - Código"
COL_CNAE_AUXILIAR = "CNAE_IBGE"

NJ_EMPRESARIAIS = {
    "2011", "2038", "2046", "2054", "2062", "2070", "2089", "2097",
    "2127", "2135", "2143", "2151", "2160", "2178", "2194", "2216",
    "2224", "2232", "2240", "2259", "2267", "2275", "2283", "2291",
    "2305", "2313", "2321", "2330", "2348", "2356",
}

# Código "1" (0 empregados) descartado intencionalmente
TAM_MAP = {
    "2":  "Microempresa",
    "3":  "Microempresa",
    "4":  "Pequena Empresa",
    "5":  "Pequena Empresa",
    "6":  "Média Empresa",
    "7":  "Grande Empresa",
    "8":  "Grande Empresa",
    "9":  "Grande Empresa",
    "10": "Grande Empresa",
}

ORDEM_TAM = ["Microempresa", "Pequena Empresa", "Média Empresa", "Grande Empresa"]


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def normalizar_cnae(serie: pd.Series) -> pd.Series:
    """Padroniza CNAE em sete posições numéricas."""
    return (
        serie.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .replace("", pd.NA)
        .str.zfill(7)
    )


# =============================================================================
# PROCESSAMENTO PRINCIPAL
# =============================================================================

def main() -> None:
    try:
        if not FILE_PATH.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {FILE_PATH}")
        if not ARQUIVO_CNAE_CRIATIVA.exists():
            raise FileNotFoundError(f"Auxiliar CNAE não encontrado: {ARQUIVO_CNAE_CRIATIVA}")

        # Carrega CNAEs da Economia Criativa
        df_cnae = pd.read_excel(ARQUIVO_CNAE_CRIATIVA, usecols=[COL_CNAE_AUXILIAR], dtype=str)
        cnaes_criativos = set(normalizar_cnae(df_cnae[COL_CNAE_AUXILIAR]).dropna())
        if not cnaes_criativos:
            raise ValueError(f"A coluna '{COL_CNAE_AUXILIAR}' não contém CNAEs válidos.")

        print(f"CNAEs criativos carregados: {len(cnaes_criativos):,}")

        contagem_trabalhadores:    dict[str, int]   = defaultdict(int)
        soma_salarios:             dict[str, float] = defaultdict(float)
        contagem_salarios_validos: dict[str, int]   = defaultdict(int)

        total_lidas       = 0
        total_empresariais = 0
        start_time        = time.time()

        print("Processando arquivo base...")

        leitor = pd.read_csv(
            FILE_PATH,
            sep=";",
            encoding="utf-8-sig",
            dtype=str,
            usecols=[COL_ANO, COL_NJ, COL_TAM, COL_SAL, COL_CNAE],
            chunksize=CHUNK_SIZE,
            low_memory=False,
        )

        for i, chunk in enumerate(leitor, 1):
            total_lidas += len(chunk)

            chunk[COL_ANO] = chunk[COL_ANO].astype(str).str.strip()
            chunk[COL_NJ]  = chunk[COL_NJ].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
            chunk[COL_TAM] = chunk[COL_TAM].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)

            # Filtros: ano 2025 + natureza jurídica empresarial + CNAE criativo
            df_filt = chunk[
                (chunk[COL_ANO] == "2025") &
                (chunk[COL_NJ].isin(NJ_EMPRESARIAIS))
            ].copy()

            if not df_filt.empty:
                df_filt = df_filt[normalizar_cnae(df_filt[COL_CNAE]).isin(cnaes_criativos)].copy()

            if not df_filt.empty:
                total_empresariais += len(df_filt)

                # Salário
                df_filt[COL_SAL] = (
                    df_filt[COL_SAL]
                    .astype(str)
                    .str.replace(",", ".", regex=False)
                )
                df_filt[COL_SAL] = pd.to_numeric(df_filt[COL_SAL], errors="coerce")

                # Porte
                df_filt["tamanho_desc"] = df_filt[COL_TAM].map(TAM_MAP)
                df_filt = df_filt[df_filt["tamanho_desc"].notna()].copy()

                # Contagem de trabalhadores
                for tam, qtd in df_filt["tamanho_desc"].value_counts().items():
                    contagem_trabalhadores[tam] += int(qtd)

                # Soma e contagem de salários válidos
                df_sal = df_filt[df_filt[COL_SAL].notna() & (df_filt[COL_SAL] > 0)]
                if not df_sal.empty:
                    for tam, grp in df_sal.groupby("tamanho_desc")[COL_SAL]:
                        soma_salarios[tam]             += grp.sum()
                        contagem_salarios_validos[tam] += grp.count()

            decorrido = time.time() - start_time
            vel = total_lidas / decorrido if decorrido > 0 else 0
            print(
                f"  Chunk {i} | Lidas: {total_lidas:,} | "
                f"Empresariais criativos: {total_empresariais:,} | Vel: {vel:,.0f} lin/s",
                end="\r",
            )

        print(f"\n\nProcessamento concluído em {time.time() - start_time:.1f}s.")

        if not contagem_trabalhadores:
            raise ValueError(
                "Nenhum vínculo encontrado após os filtros. "
                "Verifique o arquivo de entrada."
            )

        # ── Monta DataFrame final ─────────────────────────────────────────────
        registros = []
        for porte in ORDEM_TAM:
            trab = contagem_trabalhadores.get(porte, 0)
            soma = soma_salarios.get(porte, 0.0)
            qtd  = contagem_salarios_validos.get(porte, 0)
            registros.append({
                "categoria_porte":    porte,
                "total_trabalhadores": trab,
                "salario_medio":      round(soma / qtd, 2) if qtd > 0 else None,
            })

        resultado = pd.DataFrame(registros)

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