from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_DOWN, localcontext
from pathlib import Path

import pandas as pd


# ====
# CONFIGURACAO
# ====

ARQUIVO_BASE = Path(
    r"D:\OneDrive\Minc\RAIS\RAIS_py\data\processed\rais_2025_filtrado.csv"
)
ARQUIVO_SAIDA = Path(r"E:\Rais\Rais\csvs\6.15B_6.24B.csv")

CHUNK_SIZE = 300_000

CASAS_DECIMAIS_NOMINAL = 3
CASAS_DECIMAIS_PERCENTUAL = 5

COL_IDADE = "Idade"
COL_SALARIO = "vl_rem_media_nom_deflacionada_2024"

ORDEM_FAIXAS = [
    "Jovem (15 – 29)",
    "Adulto I (30 – 44)",
    "Adulto II (45 – 59)",
    "Idoso (60+)",
]


# ====
# FUNCOES AUXILIARES
# ====

def converter_idade(valor) -> int | None:
    """Converte idade inteira; retorna None para valor ausente ou inválido."""
    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    if texto.casefold() in {"", "nan", "none", "null"}:
        return None

    try:
        idade_decimal = Decimal(texto)
    except InvalidOperation:
        return None

    if idade_decimal != idade_decimal.to_integral_value():
        return None

    return int(idade_decimal)


def classificar_idade(idade: int) -> str | None:
    """Retorna a faixa etária ou None se estiver fora do escopo."""
    if 15 <= idade <= 29:
        return "Jovem (15 – 29)"
    if 30 <= idade <= 44:
        return "Adulto I (30 – 44)"
    if 45 <= idade <= 59:
        return "Adulto II (45 – 59)"
    if idade >= 60:
        return "Idoso (60+)"
    return None


def converter_decimal(valor) -> Decimal | None:
    """Converte valores com vírgula ou ponto decimal para Decimal."""
    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    if texto.casefold() in {"", "nan", "none", "null"}:
        return None

    texto = texto.replace(" ", "")

    if "," in texto:
        # Se há vírgula, trata-a como separador decimal
        # e remove pontos usados como separadores de milhar.
        texto = texto.replace(".", "").replace(",", ".")

    try:
        return Decimal(texto)
    except InvalidOperation:
        return None


def truncar_casas(valor: Decimal | None, casas: int) -> Decimal | None:
    """Trunca casas decimais excedentes, sem arredondar."""
    if valor is None:
        return None

    fator = Decimal(1).scaleb(-casas)

    with localcontext() as contexto:
        contexto.prec = 50
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

    total_vinculos = {faixa: 0 for faixa in ORDEM_FAIXAS}
    soma_salarios = {
        faixa: Decimal("0") for faixa in ORDEM_FAIXAS
    }
    qtd_salarios_validos = {faixa: 0 for faixa in ORDEM_FAIXAS}

    print("Processando faixas etárias — Economia Total...")
    print(f"Arquivo-base: {ARQUIVO_BASE}")
    print(f"Chunks de {CHUNK_SIZE} linhas")
    print(f"Saída CSV: {ARQUIVO_SAIDA}\n")

    leitor = pd.read_csv(
        ARQUIVO_BASE,
        sep=";",
        encoding="utf-8-sig",
        usecols=[COL_IDADE, COL_SALARIO],
        dtype=str,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    )

    for numero_chunk, chunk in enumerate(leitor, 1):
        # Classifica as idades válidas.
        idades = chunk[COL_IDADE].map(converter_idade)
        chunk["faixa_etaria"] = idades.map(
            lambda idade: (
                classificar_idade(idade)
                if idade is not None
                else None
            )
        )
        chunk = chunk.loc[chunk["faixa_etaria"].notna()].copy()

        if chunk.empty:
            print(
                f"  Chunk {numero_chunk}: "
                "nenhum registro em faixa etária válida."
            )
            continue

        # Conta vínculos por faixa etária.
        contagens = chunk["faixa_etaria"].value_counts()
        for faixa, quantidade in contagens.items():
            total_vinculos[faixa] += int(quantidade)

        # Acumula salários válidos por faixa etária.
        for faixa in ORDEM_FAIXAS:
            valores = chunk.loc[
                chunk["faixa_etaria"] == faixa,
                COL_SALARIO,
            ].map(converter_decimal)

            salarios_validos = [
                valor
                for valor in valores
                if valor is not None and valor > 0
            ]

            soma_salarios[faixa] += sum(
                salarios_validos,
                start=Decimal("0"),
            )
            qtd_salarios_validos[faixa] += len(salarios_validos)

        print(f"  Chunk {numero_chunk} processado.")

    total_geral = sum(total_vinculos.values())

    if total_geral == 0:
        raise ValueError(
            "Nenhum vínculo foi encontrado em faixas etárias válidas. "
            "Verifique os dados de entrada."
        )

    registros = []

    for faixa in ORDEM_FAIXAS:
        quantidade_vinculos = total_vinculos[faixa]

        # Não exporta faixas sem observações.
        if quantidade_vinculos == 0:
            continue

        quantidade_salarios = qtd_salarios_validos[faixa]

        if quantidade_salarios > 0:
            with localcontext() as contexto:
                contexto.prec = 50
                media_salarial = (
                    soma_salarios[faixa] / Decimal(quantidade_salarios)
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
                Decimal(quantidade_vinculos) / Decimal(total_geral)
            )

        participacao = truncar_casas(
            participacao,
            CASAS_DECIMAIS_PERCENTUAL,
        )

        registros.append(
            {
                "faixa_etaria": faixa,
                "num_vinculos": quantidade_vinculos,
                "pct_participacao": formatar_decimal(participacao),
                "media_salarial_deflacionada_2024": formatar_decimal(
                    media_salarial
                ),
            }
        )

    colunas_saida = [
        "faixa_etaria",
        "num_vinculos",
        "pct_participacao",
        "media_salarial_deflacionada_2024",
    ]
    resultado = pd.DataFrame(registros, columns=colunas_saida)

    ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        sep=";",
        encoding="utf-8-sig",
        na_rep="",
    )

    print(f"\nCSV gerado com sucesso: {ARQUIVO_SAIDA}")
    print(f"Registros exportados: {len(resultado)}")


if __name__ == "__main__":
    main()