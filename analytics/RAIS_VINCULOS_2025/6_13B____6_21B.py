from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation, ROUND_DOWN, localcontext
from pathlib import Path

import pandas as pd


# ====
# CONFIGURACAO
# ====

ARQUIVO_BASE = Path(
    r"D:\OneDrive\Minc\RAIS\RAIS_py\data\processed\rais_2025_filtrado.csv"
)
ARQUIVO_SAIDA = Path(r"E:\Rais\Rais\csvs\6.13B_6.21B.csv")

CHUNK_SIZE = 300_000

ANO_REFERENCIA = "2025"
CASAS_DECIMAIS_NOMINAL = 3
CASAS_DECIMAIS_PERCENTUAL = 5

COL_ANO = "ano"
COL_RACA = "Raça Cor - Código"
COL_SALARIO = "vl_rem_media_nom_deflacionada_2024"

ORDEM_CATEGORIAS = [
    "Indígena",
    "Branca",
    "Preta/Parda",
    "Amarela",
    "Não identificado",
    "Ignorado",
]

MAPA_RACA = {
    "1": "Indígena",
    "2": "Branca",
    "4": "Preta/Parda",
    "8": "Preta/Parda",
    "6": "Amarela",
    "9": "Não identificado",
    "99": "Não identificado",
    "-1": "Ignorado",
}


# ====
# FUNCOES AUXILIARES
# ====

def converter_decimal(valor) -> Decimal | None:
    """Converte valores numéricos com vírgula ou ponto decimal para Decimal."""
    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    if texto.casefold() in {"", "nan", "none", "null"}:
        return None

    texto = texto.replace(" ", "")

    if "," in texto:
        # Se há vírgula, trata-a como separador decimal e remove pontos de milhar.
        texto = texto.replace(".", "").replace(",", ".")
    # Sem vírgula, mantém o ponto como separador decimal.

    try:
        return Decimal(texto)
    except InvalidOperation:
        return None


def normalizar_codigo_categoria(valor) -> str | None:
    """Normaliza o código de raça/cor para consulta no mapa."""
    if pd.isna(valor):
        return None

    texto = str(valor).strip()
    texto = re.sub(r"\.0+$", "", texto)

    if texto.casefold() in {"", "nan", "none", "null"}:
        return None

    return texto


def truncar_casas(valor: Decimal | None, casas: int) -> Decimal | None:
    """Trunca casas decimais excedentes, sem arredondar."""
    if valor is None:
        return None

    fator = Decimal(1).scaleb(-casas)
    return valor.quantize(fator, rounding=ROUND_DOWN)


def formatar_decimal(valor: Decimal | None) -> str:
    """Formata com ponto decimal e remove zeros finais."""
    if valor is None:
        return ""

    texto = format(valor, "f")

    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")

    return texto


# ====
# PROCESSAMENTO
# ====

def main() -> None:
    if not ARQUIVO_BASE.exists():
        raise FileNotFoundError(
            f"Arquivo-base não encontrado:\n{ARQUIVO_BASE}"
        )

    ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)

    colunas_necessarias = [COL_ANO, COL_RACA, COL_SALARIO]

    total_vinculos = {
        categoria: 0 for categoria in ORDEM_CATEGORIAS
    }
    soma_salarios = {
        categoria: Decimal("0") for categoria in ORDEM_CATEGORIAS
    }
    qtd_salarios_validos = {
        categoria: 0 for categoria in ORDEM_CATEGORIAS
    }

    total_linhas_lidas = 0
    total_linhas_ano = 0
    total_linhas_raca_mapeada = 0

    print("Iniciando processamento — Economia Total, RAIS 2025...")
    print(f"Arquivo-base: {ARQUIVO_BASE}")
    print(f"Chunks de {CHUNK_SIZE} linhas")
    print(f"Saída CSV: {ARQUIVO_SAIDA}\n")

    leitor = pd.read_csv(
        ARQUIVO_BASE,
        sep=";",
        encoding="utf-8-sig",
        usecols=colunas_necessarias,
        dtype=str,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    )

    for numero_chunk, chunk in enumerate(leitor, start=1):
        total_linhas_lidas += len(chunk)

        # Mantém somente os registros de 2025.
        mascara_ano = (
            chunk[COL_ANO]
            .astype("string")
            .str.strip()
            .str.contains(ANO_REFERENCIA, regex=False, na=False)
        )
        chunk = chunk.loc[mascara_ano].copy()
        total_linhas_ano += len(chunk)

        if not chunk.empty:
            codigo_raca = chunk[COL_RACA].map(
                normalizar_codigo_categoria
            )
            chunk["raca_cor"] = codigo_raca.map(MAPA_RACA)
            chunk = chunk.loc[chunk["raca_cor"].notna()].copy()
            total_linhas_raca_mapeada += len(chunk)

            # Vínculos: contagem de registros mapeados.
            contagens = chunk["raca_cor"].value_counts()
            for categoria, quantidade in contagens.items():
                total_vinculos[categoria] += int(quantidade)

            # Salários válidos: valores maiores que zero.
            for categoria in ORDEM_CATEGORIAS:
                valores = chunk.loc[
                    chunk["raca_cor"] == categoria, COL_SALARIO
                ].map(converter_decimal)

                salarios_validos = [
                    valor
                    for valor in valores
                    if valor is not None and valor > 0
                ]

                soma_salarios[categoria] += sum(
                    salarios_validos,
                    start=Decimal("0"),
                )
                qtd_salarios_validos[categoria] += len(salarios_validos)

        print(
            f"Chunk {numero_chunk:>4} | "
            f"lidas: {total_linhas_lidas:>15,} | "
            f"ano de referência: {total_linhas_ano:>15,} | "
            f"raça/cor mapeada: {total_linhas_raca_mapeada:>15,}"
        )

    total_geral_vinculos = sum(total_vinculos.values())

    if total_geral_vinculos == 0:
        raise ValueError(
            "Nenhum vínculo de 2025 com raça/cor mapeada foi encontrado. "
            "Verifique os dados de entrada."
        )

    registros = []

    for categoria in ORDEM_CATEGORIAS:
        quantidade_vinculos = total_vinculos[categoria]

        # Não exporta categorias sem observações.
        if quantidade_vinculos == 0:
            continue

        quantidade_salarios = qtd_salarios_validos[categoria]

        if quantidade_salarios > 0:
            with localcontext() as contexto:
                contexto.prec = 50
                media_salarial = (
                    soma_salarios[categoria]
                    / Decimal(quantidade_salarios)
                )
            media_salarial = truncar_casas(
                media_salarial,
                CASAS_DECIMAIS_NOMINAL,
            )
        else:
            media_salarial = None

        with localcontext() as contexto:
            contexto.prec = 50
            participacao = (
                Decimal(quantidade_vinculos)
                / Decimal(total_geral_vinculos)
            )
        participacao = truncar_casas(
            participacao,
            CASAS_DECIMAIS_PERCENTUAL,
        )

        registros.append(
            {
                "ano": int(ANO_REFERENCIA),
                "raca_cor": categoria,
                "num_vinculos": quantidade_vinculos,
                "pct_participacao": formatar_decimal(participacao),
                "media_salarial_deflacionada_2024": formatar_decimal(
                    media_salarial
                ),
                "num_salarios_validos": quantidade_salarios,
            }
        )

    colunas_saida = [
        "ano",
        "raca_cor",
        "num_vinculos",
        "pct_participacao",
        "media_salarial_deflacionada_2024",
        "num_salarios_validos",
    ]
    df_saida = pd.DataFrame(registros, columns=colunas_saida)

    df_saida.to_csv(
        ARQUIVO_SAIDA,
        sep=";",
        index=False,
        encoding="utf-8-sig",
        na_rep="",
    )

    print("\nProcessamento concluído.")
    print(f"Linhas lidas: {total_linhas_lidas:,}")
    print(f"Registros de 2025: {total_linhas_ano:,}")
    print(f"Registros com raça/cor mapeada: {total_linhas_raca_mapeada:,}")
    print(f"CSV salvo em: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()