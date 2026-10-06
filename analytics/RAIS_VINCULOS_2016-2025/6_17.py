from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_DOWN, localcontext
from pathlib import Path
import re

import pandas as pd


# ====
# CONFIGURACAO
# ====

ARQUIVO_BASE = Path(
    r"E:\Rais\Rais\DF1\data\rais_metricas_grupos_2015_2025_com_informalidade.csv"
)
ARQUIVO_SAIDA = Path(r"E:\Rais\Rais\csvs\6.17.csv")

CASAS_DECIMAIS_NOMINAL = 3
ANOS = list(range(2016, 2026))

# Mapeamento: nome do grupo no arquivo-base -> rótulo de saída.
GRUPOS_MAPPING = {
    "Brasil": "Brasil",
    "Cultura": "Economia Criativa",
    "Agricultura, pecuária, produção florestal, pesca e aquicultura": "Agricultura",
    "Indústria extrativa": "Indústria extrativa",
    "Construção": "Construção Civil",
}

COL_GRUPO = "grupo"
COL_ANO = "ano"
COL_MEDIA = "media_def"


# ====
# FUNCOES AUXILIARES
# ====

def normalizar_texto(valor) -> str:
    """Normaliza espaços e maiúsculas/minúsculas para comparar rótulos."""
    if pd.isna(valor):
        return ""

    return re.sub(r"\s+", " ", str(valor).strip()).casefold()


def localizar_grupo(valor) -> str | None:
    """Relaciona o rótulo da base a um grupo de saída."""
    texto = normalizar_texto(valor)

    if not texto:
        return None

    nomes_normalizados = {
        normalizar_texto(nome_base): nome_base
        for nome_base in GRUPOS_MAPPING
    }

    # Prioriza correspondência exata.
    if texto in nomes_normalizados:
        return nomes_normalizados[texto]

    # Permite encontrar o rótulo quando vier acompanhado de texto adicional.
    correspondencias = [
        nome_base
        for nome_base in GRUPOS_MAPPING
        if normalizar_texto(nome_base) in texto
    ]

    if not correspondencias:
        return None

    # Se houver mais de uma possível correspondência, prioriza o nome mais específico.
    return max(correspondencias, key=lambda nome: len(normalizar_texto(nome)))


def converter_decimal(valor) -> Decimal | None:
    """Converte número com ponto ou vírgula decimal para Decimal."""
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
        numero = Decimal(texto)
    except InvalidOperation:
        return None

    if not numero.is_finite():
        return None

    return numero


def truncar_casas(valor: Decimal, casas: int) -> Decimal:
    """Trunca casas decimais excedentes sem arredondar."""
    fator = Decimal(1).scaleb(-casas)

    with localcontext() as contexto:
        contexto.prec = 50
        return valor.quantize(fator, rounding=ROUND_DOWN)


def formatar_decimal(valor: Decimal | None) -> str:
    """Formata o número com ponto decimal, sem zeros finais desnecessários."""
    if valor is None:
        return ""

    texto = format(valor, "f")

    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")

    return texto


def carregar_csv(caminho: Path) -> pd.DataFrame:
    """Lê o CSV tentando os separadores previstos nos arquivos do projeto."""
    colunas_necessarias = {COL_GRUPO, COL_ANO, COL_MEDIA}

    for separador in (";", ","):
        df = pd.read_csv(
            caminho,
            sep=separador,
            encoding="utf-8-sig",
            dtype=str,
            keep_default_na=False,
        )
        df.columns = [
            str(coluna).replace("\ufeff", "").strip()
            for coluna in df.columns
        ]

        if colunas_necessarias.issubset(df.columns):
            return df

    raise KeyError(
        "Não foi possível localizar todas as colunas necessárias "
        f"({COL_GRUPO}, {COL_ANO}, {COL_MEDIA}). "
        f"Colunas encontradas: {list(df.columns)}"
    )


# ====
# PROCESSAMENTO PRINCIPAL
# ====

def main() -> None:
    if not ARQUIVO_BASE.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {ARQUIVO_BASE}"
        )

    df = carregar_csv(ARQUIVO_BASE)

    # Normaliza anos mantendo somente os quatro dígitos do ano.
    anos_texto = (
        df[COL_ANO]
        .astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )
    df[COL_ANO] = pd.to_numeric(anos_texto, errors="coerce")

    df = df.loc[df[COL_ANO].isin(ANOS)].copy()
    df[COL_ANO] = df[COL_ANO].astype(int)

    # Identifica os grupos de interesse.
    df["grupo_base"] = df[COL_GRUPO].map(localizar_grupo)
    df = df.loc[df["grupo_base"].notna()].copy()

    if df.empty:
        raise ValueError(
            "Nenhum dado encontrado para os grupos e anos definidos. "
            "Verifique os rótulos de grupo e o arquivo de entrada."
        )

    df["media_decimal"] = df[COL_MEDIA].map(converter_decimal)

    registros = []

    for grupo_base, grupo_saida in GRUPOS_MAPPING.items():
        subset = df.loc[df["grupo_base"] == grupo_base]

        if subset.empty:
            print(f"Aviso: grupo '{grupo_base}' não localizado no CSV.")
            continue

        for ano in ANOS:
            valores = [
                valor
                for valor in subset.loc[
                    subset[COL_ANO] == ano, "media_decimal"
                ].tolist()
                if valor is not None
            ]

            if valores:
                with localcontext() as contexto:
                    contexto.prec = 50
                    media_anual = sum(
                        valores,
                        start=Decimal("0"),
                    ) / Decimal(len(valores))

                media_anual = truncar_casas(
                    media_anual,
                    CASAS_DECIMAIS_NOMINAL,
                )
            else:
                media_anual = None

            registros.append(
                {
                    "grupo": grupo_saida,
                    "ano": ano,
                    "media_salarial_deflacionada": formatar_decimal(
                        media_anual
                    ),
                }
            )

    if not registros:
        raise ValueError(
            "Nenhum registro foi produzido. Verifique os grupos "
            "e os dados do arquivo de entrada."
        )

    resultado = pd.DataFrame(
        registros,
        columns=[
            "grupo",
            "ano",
            "media_salarial_deflacionada",
        ],
    )

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