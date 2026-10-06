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
ARQUIVO_CNAE_CRIATIVA = Path(
    r"E:\Rais\Rais\Auxiliares\CNAE-ibge.xlsx"
)
ARQUIVO_SAIDA = Path(r"E:\Rais\Rais\csvs\6.16.csv")

CHUNK_SIZE = 300_000

ANO_REFERENCIA = "2025"
CASAS_DECIMAIS_NOMINAL = 3
CASAS_DECIMAIS_PERCENTUAL = 5

COL_ANO = "ano"
COL_CNAE = "CNAE 2.0 Subclasse - Código"
COL_CNAE_AUX = "CNAE_IBGE"
COL_SALARIO = "vl_rem_media_nom_deflacionada_2024"
COL_DEFICIENCIA = "Ind Portador Defic - Código"

GRUPOS = [
    "Total de trabalhadores",
    "Economia Criativa",
]


# ====
# FUNCOES AUXILIARES
# ====

def normalizar_codigo(serie: pd.Series) -> pd.Series:
    """Normaliza códigos lidos do CSV ou da planilha auxiliar."""
    return (
        serie.astype("string")
        .str.strip()
        .str.replace(r"\.0+$", "", regex=True)
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "null": pd.NA})
    )


def normalizar_cnae(serie: pd.Series) -> pd.Series:
    """Normaliza CNAE para sete dígitos."""
    codigos = (
        normalizar_codigo(serie)
        .str.replace(r"\D", "", regex=True)
        .replace("", pd.NA)
    )
    return codigos.str.zfill(7)


def converter_decimal(valor) -> Decimal | None:
    """Converte número com vírgula ou ponto decimal para Decimal."""
    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    if texto.casefold() in {"", "nan", "none", "null"}:
        return None

    texto = texto.replace(" ", "")

    if "," in texto:
        # Vírgula decimal; pontos são tratados como separadores de milhar.
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


def inicializar_acumuladores() -> dict:
    return {
        grupo: {
            "num_vinculos_validos": 0,
            "num_vinculos_com_deficiencia": 0,
            "soma_salarios_com_deficiencia": Decimal("0"),
            "num_salarios_com_deficiencia": 0,
            "soma_salarios_sem_deficiencia": Decimal("0"),
            "num_salarios_sem_deficiencia": 0,
        }
        for grupo in GRUPOS
    }


def acumular(dados: pd.DataFrame, acumuladores: dict, grupo: str) -> None:
    codigos = normalizar_codigo(dados[COL_DEFICIENCIA])
    mascara_validos = codigos.notna()

    dados_validos = dados.loc[mascara_validos]
    codigos_validos = codigos.loc[mascara_validos]

    acumulador = acumuladores[grupo]
    acumulador["num_vinculos_validos"] += len(dados_validos)

    # Mantém a regra original: código "1" indica deficiência;
    # os demais códigos não ausentes entram como sem deficiência.
    mascara_com_deficiencia = codigos_validos == "1"
    acumulador["num_vinculos_com_deficiencia"] += int(
        mascara_com_deficiencia.sum()
    )

    salarios = dados_validos[COL_SALARIO].map(converter_decimal)

    for codigo, salario in zip(codigos_validos.tolist(), salarios.tolist()):
        if salario is None or salario <= 0:
            continue

        if codigo == "1":
            acumulador["soma_salarios_com_deficiencia"] += salario
            acumulador["num_salarios_com_deficiencia"] += 1
        else:
            acumulador["soma_salarios_sem_deficiencia"] += salario
            acumulador["num_salarios_sem_deficiencia"] += 1


# ====
# PROCESSAMENTO PRINCIPAL
# ====

def main() -> None:
    for caminho in [ARQUIVO_BASE, ARQUIVO_CNAE_CRIATIVA]:
        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    df_cnae = pd.read_excel(
        ARQUIVO_CNAE_CRIATIVA,
        usecols=[COL_CNAE_AUX],
        dtype=str,
    )
    cnaes_criativos = set(
        normalizar_cnae(df_cnae[COL_CNAE_AUX]).dropna()
    )

    if not cnaes_criativos:
        raise ValueError(
            f"A coluna '{COL_CNAE_AUX}' não contém CNAEs válidos em "
            f"{ARQUIVO_CNAE_CRIATIVA}."
        )

    print(f"Códigos CNAE da Economia Criativa carregados: {len(cnaes_criativos)}")
    print(f"Processando a base em chunks de {CHUNK_SIZE} linhas...")

    acumuladores = inicializar_acumuladores()

    leitor = pd.read_csv(
        ARQUIVO_BASE,
        sep=";",
        encoding="utf-8-sig",
        usecols=[
            COL_ANO,
            COL_CNAE,
            COL_SALARIO,
            COL_DEFICIENCIA,
        ],
        dtype=str,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    )

    for numero_chunk, chunk in enumerate(leitor, 1):
        anos = normalizar_codigo(chunk[COL_ANO])
        chunk = chunk.loc[anos == ANO_REFERENCIA].copy()

        if chunk.empty:
            print(
                f"  Chunk {numero_chunk}: "
                f"nenhum registro de {ANO_REFERENCIA}."
            )
            continue

        # Recorte de todos os trabalhadores com indicador de deficiência válido.
        acumular(chunk, acumuladores, "Total de trabalhadores")

        # Recorte da Economia Criativa, usando a planilha local de CNAEs.
        mascara_cnae_criativo = normalizar_cnae(
            chunk[COL_CNAE]
        ).isin(cnaes_criativos)
        chunk_ec = chunk.loc[mascara_cnae_criativo].copy()

        if not chunk_ec.empty:
            acumular(chunk_ec, acumuladores, "Economia Criativa")

        print(f"  Chunk {numero_chunk} processado.")

    registros = []

    for grupo in GRUPOS:
        acumulador = acumuladores[grupo]
        total_validos = acumulador["num_vinculos_validos"]

        if total_validos == 0:
            continue

        quantidade_com_deficiencia = (
            acumulador["num_vinculos_com_deficiencia"]
        )

        with localcontext() as contexto:
            contexto.prec = 50
            participacao = (
                Decimal(quantidade_com_deficiencia)
                / Decimal(total_validos)
            )

        participacao = truncar_casas(
            participacao,
            CASAS_DECIMAIS_PERCENTUAL,
        )

        quantidade_salarios_com = (
            acumulador["num_salarios_com_deficiencia"]
        )
        if quantidade_salarios_com > 0:
            with localcontext() as contexto:
                contexto.prec = 50
                media_com_deficiencia = (
                    acumulador["soma_salarios_com_deficiencia"]
                    / Decimal(quantidade_salarios_com)
                )
            media_com_deficiencia = truncar_casas(
                media_com_deficiencia,
                CASAS_DECIMAIS_NOMINAL,
            )
        else:
            media_com_deficiencia = None

        quantidade_salarios_sem = (
            acumulador["num_salarios_sem_deficiencia"]
        )
        if quantidade_salarios_sem > 0:
            with localcontext() as contexto:
                contexto.prec = 50
                media_sem_deficiencia = (
                    acumulador["soma_salarios_sem_deficiencia"]
                    / Decimal(quantidade_salarios_sem)
                )
            media_sem_deficiencia = truncar_casas(
                media_sem_deficiencia,
                CASAS_DECIMAIS_NOMINAL,
            )
        else:
            media_sem_deficiencia = None

        registros.append(
            {
                "grupo": grupo,
                "num_vinculos_com_deficiencia": quantidade_com_deficiencia,
                "num_vinculos_validos": total_validos,
                "pct_vinculos_com_deficiencia": formatar_decimal(
                    participacao
                ),
                "media_salarial_com_deficiencia_2024": formatar_decimal(
                    media_com_deficiencia
                ),
                "media_salarial_sem_deficiencia_2024": formatar_decimal(
                    media_sem_deficiencia
                ),
            }
        )

    if not registros:
        raise ValueError(
            "Nenhum dado foi encontrado para o ano de referência com "
            "indicador de deficiência válido. Verifique os arquivos de entrada."
        )

    colunas_saida = [
        "grupo",
        "num_vinculos_com_deficiencia",
        "num_vinculos_validos",
        "pct_vinculos_com_deficiencia",
        "media_salarial_com_deficiencia_2024",
        "media_salarial_sem_deficiencia_2024",
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