from __future__ import annotations

from pathlib import Path
import pandas as pd

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

ARQUIVO_BASE          = Path(r"D:\OneDrive\Minc\RAIS\RAIS_py\data\processed\rais_2025_filtrado.csv")
ARQUIVO_CNAE_CRIATIVA = Path(r"E:\Rais\Rais\Auxiliares\CNAE-ibge.xlsx")
ARQUIVO_SAIDA         = Path(r"E:\Rais\Rais\csvs\6.13.csv")

CHUNK_SIZE = 300_000

COL_ANO      = "ano"
COL_RACA     = "Raça Cor - Código"
COL_SALARIO  = "vl_rem_media_nom_deflacionada_2024"
COL_CNAE     = "CNAE 2.0 Subclasse - Código"
COL_CNAE_AUX = "CNAE_IBGE"

ANO_REFERENCIA = "2025"

ORDEM_CATEGORIAS = [
    "Indígena",
    "Branca",
    "Preta/Parda",
    "Amarela",
    "Não identificado",
    "Ignorado",
]

MAPA_RACA = {
    "1":  "Indígena",
    "2":  "Branca",
    "4":  "Preta/Parda",
    "8":  "Preta/Parda",
    "6":  "Amarela",
    "9":  "Não identificado",
    "99": "Não identificado",
    "-1": "Ignorado",
}


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

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


# =============================================================================
# PROCESSAMENTO PRINCIPAL
# =============================================================================

def main() -> None:
    try:
        for caminho in [ARQUIVO_BASE, ARQUIVO_CNAE_CRIATIVA]:
            if not caminho.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

        # Carrega CNAEs da Economia Criativa
        df_cnae = pd.read_excel(ARQUIVO_CNAE_CRIATIVA, usecols=[COL_CNAE_AUX], dtype=str)
        cnaes_criativos = set(normalizar_cnae(df_cnae[COL_CNAE_AUX]).dropna())

        if not cnaes_criativos:
            raise ValueError(
                f"A coluna '{COL_CNAE_AUX}' não contém CNAEs válidos em {ARQUIVO_CNAE_CRIATIVA}."
            )

        print(f"Códigos CNAE da Economia Criativa carregados: {len(cnaes_criativos):,}")
        print(f"\nProcessando arquivo base em chunks de {CHUNK_SIZE:,} linhas...")

        # Acumuladores
        total_vinculos       = {cat: 0   for cat in ORDEM_CATEGORIAS}
        soma_salarios        = {cat: 0.0 for cat in ORDEM_CATEGORIAS}
        qtd_salarios_validos = {cat: 0   for cat in ORDEM_CATEGORIAS}

        leitor = pd.read_csv(
            ARQUIVO_BASE,
            sep=";",
            encoding="utf-8-sig",
            usecols=[COL_ANO, COL_RACA, COL_SALARIO, COL_CNAE],
            dtype=str,
            chunksize=CHUNK_SIZE,
            low_memory=False,
        )

        for i, chunk in enumerate(leitor, 1):
            # Filtra ano de referência
            chunk = chunk[
                chunk[COL_ANO].astype(str).str.strip() == ANO_REFERENCIA
            ].copy()

            if chunk.empty:
                print(f"  Chunk {i}: nenhum registro de {ANO_REFERENCIA}.")
                continue

            # Filtra Economia Criativa
            chunk = chunk[normalizar_cnae(chunk[COL_CNAE]).isin(cnaes_criativos)].copy()

            if chunk.empty:
                print(f"  Chunk {i}: nenhum registro de EC.")
                continue

            # Mapeia raça/cor
            cod_raca = (
                chunk[COL_RACA]
                .astype("string")
                .str.strip()
                .str.replace(r"\.0$", "", regex=True)
            )
            chunk["categoria_raca"] = cod_raca.map(MAPA_RACA)
            chunk = chunk[chunk["categoria_raca"].notna()].copy()

            # Acumula vínculos
            for cat, qtd in chunk["categoria_raca"].value_counts().items():
                total_vinculos[cat] += int(qtd)

            # Acumula salários
            chunk["salario"] = converter_numero_brasileiro(chunk[COL_SALARIO])
            salarios_validos = chunk[chunk["salario"] > 0]

            if not salarios_validos.empty:
                for cat, soma in salarios_validos.groupby("categoria_raca")["salario"].sum().items():
                    soma_salarios[cat] += float(soma)
                for cat, qtd in salarios_validos.groupby("categoria_raca")["salario"].count().items():
                    qtd_salarios_validos[cat] += int(qtd)

            print(f"  Chunk {i} processado.")

        # Monta o DataFrame final
        total_geral = sum(total_vinculos.values())

        if total_geral == 0:
            raise ValueError(
                "Nenhum vínculo encontrado após os filtros. "
                "Verifique os arquivos de entrada."
            )

        registros = []
        for cat in ORDEM_CATEGORIAS:
            vinculos = total_vinculos[cat]
            if vinculos == 0:
                continue

            media_salarial = (
                soma_salarios[cat] / qtd_salarios_validos[cat]
                if qtd_salarios_validos[cat] > 0
                else None
            )

            registros.append({
                "raca_cor":         cat,
                "total_vinculos":   vinculos,
                "participacao_pct": vinculos / total_geral,  # ex: 0,025 = 2,5%
                "media_salarial":   round(media_salarial, 2) if media_salarial else None,
            })

        resultado = pd.DataFrame(registros)

        # Salva o CSV
        ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)

        resultado.to_csv(
            ARQUIVO_SAIDA,
            index=False,
            sep=";",
            decimal=",",
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