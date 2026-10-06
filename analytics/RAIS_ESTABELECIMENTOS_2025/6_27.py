from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, localcontext
from pathlib import Path

import pandas as pd


# ====
# CONFIGURACAO
# ====

ARQUIVO_ENTRADA = Path(
    r"E:\Rais\DF2\data\saida_1_estab_cultura_2016_2025_base.csv"
)
ARQUIVO_SAIDA = Path(r"E:\Rais\Rais\csvs\6.27.csv")

ANO_ANALISE = "2025"
CASAS_DECIMAIS_PERCENTUAL = 5

COL_ANO = "ano"
COL_TAMANHO = "tam_estab"
COL_NATUREZA_JURIDICA = "natureza_juridica"

NATUREZAS_JURIDICAS_EMPRESARIAIS = {
    "2011", "2038", "2046", "2054", "2062", "2070", "2089", "2097",
    "2127", "2135", "2143", "2151", "2160", "2178", "2194", "2216",
    "2224", "2232", "2240", "2259", "2267", "2275", "2283", "2291",
    "2305", "2313", "2321", "2330", "2348", "2356",
}

MAPA_PORTE = {
    "1": "Microempresa (Até 9)",
    "2": "Microempresa (Até 9)",
    "3": "Microempresa (Até 9)",
    "4": "Pequena Empresa (10 a 49)",
    "5": "Pequena Empresa (10 a 49)",
    "6": "Média Empresa (50 a 99)",
    "7": "Grande Empresa (100 ou mais)",
    "8": "Grande Empresa (100 ou mais)",
    "9": "Grande Empresa (100 ou mais)",
    "10": "Grande Empresa (100 ou mais)",
}

ORDEM_PORTE = [
    "Microempresa (Até 9)",
    "Pequena Empresa (10 a 49)",
    "Média Empresa (50 a 99)",
    "Grande Empresa (100 ou mais)",
]


# ====
# FUNCOES AUXILIARES
# ====

def normalizar_codigo(valor) -> str:
    """Normaliza códigos lidos como texto, inteiro ou número terminado em .0."""
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()

    if texto.casefold() in {"", "nan", "none", "null"}:
        return ""

    if texto.endswith(".0"):
        texto = texto[:-2]

    digitos = "".join(caractere for caractere in texto if caractere.isdigit())

    if not digitos:
        return ""

    codigo = digitos.lstrip("0")
    return codigo or "0"


def truncar_percentual(numerador: int, denominador: int) -> str:
    """Calcula e trunca a proporção a até cinco casas decimais."""
    if denominador == 0:
        return ""

    fator = Decimal(1).scaleb(-CASAS_DECIMAIS_PERCENTUAL)

    with localcontext() as contexto:
        contexto.prec = 50
        proporcao = Decimal(numerador) / Decimal(denominador)
        proporcao = proporcao.quantize(fator, rounding=ROUND_DOWN)

    texto = format(proporcao, "f")

    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")

    return texto


def validar_colunas(dataframe: pd.DataFrame) -> None:
    """Verifica as colunas necessárias no arquivo de entrada."""
    obrigatorias = {
        COL_ANO,
        COL_TAMANHO,
        COL_NATUREZA_JURIDICA,
    }
    ausentes = sorted(obrigatorias - set(dataframe.columns))

    if ausentes:
        raise KeyError(
            "Colunas obrigatórias não encontradas no arquivo: "
            f"{ausentes}. Colunas disponíveis: {list(dataframe.columns)}"
        )


# ====
# PROCESSAMENTO PRINCIPAL
# ====

def main() -> None:
    try:
        if not ARQUIVO_ENTRADA.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {ARQUIVO_ENTRADA}"
            )

        print("Lendo arquivo de entrada...")

        df = pd.read_csv(
            ARQUIVO_ENTRADA,
            sep=";",
            encoding="utf-8-sig",
            dtype=str,
            low_memory=False,
        )

        df.columns = [
            str(coluna).replace("\ufeff", "").strip()
            for coluna in df.columns
        ]
        validar_colunas(df)

        df["ano_normalizado"] = df[COL_ANO].map(normalizar_codigo)
        df["natureza_juridica_normalizada"] = df[
            COL_NATUREZA_JURIDICA
        ].map(normalizar_codigo)
        df["porte_codigo"] = df[COL_TAMANHO].map(normalizar_codigo)

        # Filtra pelo ano de análise e pelas naturezas jurídicas previstas.
        df_filtrado = df.loc[
            df["ano_normalizado"].eq(ANO_ANALISE)
            & df["natureza_juridica_normalizada"].isin(
                NATUREZAS_JURIDICAS_EMPRESARIAIS
            )
        ].copy()

        if df_filtrado.empty:
            raise ValueError(
                f"Nenhum registro encontrado para o ano {ANO_ANALISE} "
                "com os filtros de natureza jurídica aplicados."
            )

        df_filtrado["categoria_porte"] = df_filtrado[
            "porte_codigo"
        ].map(MAPA_PORTE)
        df_filtrado = df_filtrado.dropna(subset=["categoria_porte"])

        if df_filtrado.empty:
            raise ValueError(
                "Nenhum registro possui código de porte reconhecido."
            )

        contagens = df_filtrado["categoria_porte"].value_counts()
        total_registros_classificados = int(contagens.sum())

        registros = []

        for porte in ORDEM_PORTE:
            quantidade = int(contagens.get(porte, 0))
            registros.append(
                {
                    "ano": int(ANO_ANALISE),
                    "categoria_porte": porte,
                    "num_estabelecimentos": quantidade,
                    "pct_participacao": truncar_percentual(
                        quantidade,
                        total_registros_classificados,
                    ),
                }
            )

        resultado = pd.DataFrame(
            registros,
            columns=[
                "ano",
                "categoria_porte",
                "num_estabelecimentos",
                "pct_participacao",
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
        print(f"Categorias exportadas: {len(resultado)}")
        print(
            "Registros classificados usados no cálculo: "
            f"{total_registros_classificados:,}"
        )

    except FileNotFoundError as erro:
        print(f"Erro: {erro}")

    except (KeyError, ValueError) as erro:
        print(f"Erro de validação dos dados: {erro}")

    except Exception as erro:
        print(f"Erro inesperado: {erro}")


if __name__ == "__main__":
    main()