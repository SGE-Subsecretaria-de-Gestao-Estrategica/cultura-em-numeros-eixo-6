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
ARQUIVO_SAIDA = Path(r"E:\Rais\Rais\csvs\6.14B_6.23B.csv")

CHUNK_SIZE = 300_000

ANO_REFERENCIA = "2025"
CASAS_DECIMAIS_NOMINAL = 3
CASAS_DECIMAIS_PERCENTUAL = 5

COL_ANO = "ano"
COL_ESCOLARIDADE = "Escolaridade Após 2005 - Código"
COL_SALARIO = "vl_rem_media_nom_deflacionada_2024"

ORDEM_CATEGORIAS = [
    "Sem instrução / Fund. Incompleto",
    "Fund. Completo / Médio Incompleto",
    "Médio Completo / Sup. Incompleto",
    "Superior Completo",
    "Pós-graduação",
    "Ignorado",
]

MAPA_ESCOLARIDADE = {
    "1": "Sem instrução / Fund. Incompleto",
    "2": "Sem instrução / Fund. Incompleto",
    "3": "Sem instrução / Fund. Incompleto",
    "4": "Sem instrução / Fund. Incompleto",
    "5": "Fund. Completo / Médio Incompleto",
    "6": "Fund. Completo / Médio Incompleto",
    "7": "Médio Completo / Sup. Incompleto",
    "8": "Médio Completo / Sup. Incompleto",
    "9": "Superior Completo",
    "10": "Pós-graduação",
    "11": "Pós-graduação",
    "-1": "Ignorado",
}


# ====
# FUNCOES AUXILIARES
# ====

def converter_decimal(valor) -> Decimal | None:
    """Converte números com vírgula ou ponto decimal para Decimal."""
    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    if texto.casefold() in {"", "nan", "none", "null"}:
        return None

    texto = texto.replace(" ", "")

    if "," in texto:
        # Vírgula como separador decimal; pontos são tratados como milhares.
        texto = texto.replace(".", "").replace(",", ".")

    try:
        return Decimal(texto)
    except InvalidOperation:
        return None


def normalizar_codigo(valor) -> str | None:
    """Normaliza códigos categóricos lidos do CSV."""
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

    colunas_necessarias = [
        COL_ANO,
        COL_ESCOLARIDADE,
        COL_SALARIO,
    ]

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
    total_linhas_escolaridade_mapeada = 0
    total_salarios_validos = 0

    print("Processando escolaridade — Economia Total, RAIS 2025...")
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

        # Mantém registros que contenham o ano de referência.
        anos = (
            chunk[COL_ANO]
            .astype("string")
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
        )
        chunk = chunk.loc[
            anos.str.contains(ANO_REFERENCIA, regex=False, na=False)
        ].copy()
        total_linhas_ano += len(chunk)

        if not chunk.empty:
            # Mapeia as categorias de escolaridade.
            codigos = chunk[COL_ESCOLARIDADE].map(normalizar_codigo)
            chunk["escolaridade"] = codigos.map(MAPA_ESCOLARIDADE)
            chunk = chunk.loc[chunk["escolaridade"].notna()].copy()
            total_linhas_escolaridade_mapeada += len(chunk)

            if not chunk.empty:
                # Conta vínculos por categoria.
                contagens = chunk["escolaridade"].value_counts()
                for categoria, quantidade in contagens.items():
                    total_vinculos[categoria] += int(quantidade)

                # Acumula salários válidos por categoria.
                for categoria in ORDEM_CATEGORIAS:
                    valores = chunk.loc[
                        chunk["escolaridade"] == categoria,
                        COL_SALARIO,
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
                    qtd_salarios_validos[categoria] += len(
                        salarios_validos
                    )
                    total_salarios_validos += len(salarios_validos)

        print(
            f"Chunk {numero_chunk:>4} | "
            f"lidas: {total_linhas_lidas:>15,} | "
            f"ano de referência: {total_linhas_ano:>15,} | "
            f"escolaridade mapeada: "
            f"{total_linhas_escolaridade_mapeada:>15,} | "
            f"salários válidos: {total_salarios_validos:>15,}"
        )

    total_geral_vinculos = sum(total_vinculos.values())

    if total_geral_vinculos == 0:
        raise ValueError(
            "Nenhum vínculo do ano de referência com escolaridade mapeada "
            "foi encontrado. Verifique os dados de entrada."
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
                "escolaridade": categoria,
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
        "escolaridade",
        "num_vinculos",
        "pct_participacao",
        "media_salarial_deflacionada_2024",
        "num_salarios_validos",
    ]
    resultado = pd.DataFrame(registros, columns=colunas_saida)

    resultado.to_csv(
        ARQUIVO_SAIDA,
        sep=";",
        index=False,
        encoding="utf-8-sig",
        na_rep="",
    )

    print("\nProcessamento concluído.")
    print(f"Linhas lidas: {total_linhas_lidas:,}")
    print(f"Registros do ano de referência: {total_linhas_ano:,}")
    print(
        "Registros com escolaridade mapeada: "
        f"{total_linhas_escolaridade_mapeada:,}"
    )
    print(f"Salários válidos (> 0): {total_salarios_validos:,}")
    print(f"CSV salvo em: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()