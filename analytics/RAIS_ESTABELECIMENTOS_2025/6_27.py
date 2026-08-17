from __future__ import annotations

from pathlib import Path

import pandas as pd

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

ARQUIVO_ENTRADA = Path(r"E:\Rais\DF2\data\saida_1_estab_cultura_2016_2025_base.csv")
ARQUIVO_SAIDA   = Path(r"E:\Rais\Rais\csvs\6.28.csv")

ANO_ANALISE = 2025

NJ_EMPRESARIAIS = {
    "2011", "2038", "2046", "2054", "2062", "2070", "2089", "2097",
    "2127", "2135", "2143", "2151", "2160", "2178", "2194", "2216",
    "2224", "2232", "2240", "2259", "2267", "2275", "2283", "2291",
    "2305", "2313", "2321", "2330", "2348", "2356",
}

TAM_MAP = {
    "1":  "Microempresa (Até 9)",
    "2":  "Microempresa (Até 9)",
    "3":  "Microempresa (Até 9)",
    "4":  "Pequena Empresa (10 a 49)",
    "5":  "Pequena Empresa (10 a 49)",
    "6":  "Média Empresa (50 a 99)",
    "7":  "Grande Empresa (100 ou mais)",
    "8":  "Grande Empresa (100 ou mais)",
    "9":  "Grande Empresa (100 ou mais)",
    "10": "Grande Empresa (100 ou mais)",
}

ORDEM_TAM = [
    "Microempresa (Até 9)",
    "Pequena Empresa (10 a 49)",
    "Média Empresa (50 a 99)",
    "Grande Empresa (100 ou mais)",
]


# =============================================================================
# PROCESSAMENTO PRINCIPAL
# =============================================================================

def main() -> None:
    try:
        if not ARQUIVO_ENTRADA.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_ENTRADA}")

        print("Lendo arquivo de entrada...")

        df = pd.read_csv(
            ARQUIVO_ENTRADA,
            sep=";",
            encoding="utf-8-sig",
            dtype={"ano": "Int64", "tam_estab": str, "natureza_juridica": str},
        )

        # Padronizar strings
        df["natureza_juridica"] = df["natureza_juridica"].astype(str).str.strip()
        df["tam_estab"] = (
            df["tam_estab"]
            .astype(str)
            .str.replace(r"\D", "", regex=True)
            .str.lstrip("0")
        )

        # Filtros: ano e natureza jurídica empresarial
        df_filt = df[
            (df["ano"] == ANO_ANALISE) &
            (df["natureza_juridica"].isin(NJ_EMPRESARIAIS))
        ].copy()

        if df_filt.empty:
            raise ValueError(
                f"Nenhum dado encontrado para o ano {ANO_ANALISE} "
                "com os filtros de natureza jurídica aplicados."
            )

        print(f"Registros após filtros: {len(df_filt):,}")

        # Mapear categoria de porte
        df_filt["categoria_porte"] = df_filt["tam_estab"].map(TAM_MAP)
        df_filt = df_filt.dropna(subset=["categoria_porte"])

        # Contagem por porte
        contagem = df_filt["categoria_porte"].value_counts()
        total_geral = contagem.sum()

        # Monta DataFrame final na ordem definida
        registros = []
        for porte in ORDEM_TAM:
            qtd = int(contagem.get(porte, 0))
            registros.append({
                "categoria_porte":  porte,
                "total_empresas":   qtd,
                "participacao_pct": round(qtd / total_geral, 6) if total_geral > 0 else None,
            })

        resultado = pd.DataFrame(registros)

        # Exporta
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