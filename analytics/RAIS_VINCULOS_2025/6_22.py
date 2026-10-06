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
ARQUIVO_SAIDA = Path(r"E:\Rais\Rais\csvs\6.22.csv")

CHUNK_SIZE = 300_000
CASAS_DECIMAIS_NOMINAL = 3

COL_CNAE_BASE = "CNAE 2.0 Subclasse - Código"
COL_CNAE_AUX = "CNAE_IBGE"
COL_SALARIO = "vl_rem_media_nom_deflacionada_2024"
COL_RACA = "Raça Cor - Código"
COL_SEXO = "Sexo - Código"

MAPA_SEXO = {
    "1": "Masculino",
    "2": "Feminino",
}

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

ORDEM_RACA = [
    "Indígena",
    "Branca",
    "Preta/Parda",
    "Amarela",
    "Não identificado",
    "Ignorado",
]
ORDEM_SEXO = ["Feminino", "Masculino"]


# ====
# FUNCOES AUXILIARES
# ====

def normalizar_cnae(serie: pd.Series) -> pd.Series:
    """Padroniza os códigos CNAE em sete dígitos."""
    codigos = (
        serie.astype("string")
        .str.strip()
        .str.replace(r"\.0+$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .replace("", pd.NA)
    )
    return codigos.str.zfill(7)


def normalizar_codigo_categoria(serie: pd.Series) -> pd.Series:
    """Normaliza códigos categóricos sem alterar códigos negativos."""
    return (
        serie.astype("string")
        .str.strip()
        .str.replace(r"\.0+$", "", regex=True)
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    )


def converter_decimal(valor) -> Decimal | None:
    """
    Converte valores numéricos para Decimal.

    Aceita ponto ou vírgula decimal; quando há ambos, o separador
    que aparece por último é interpretado como separador decimal.
    """
    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    if texto.casefold() in {"", "nan", "none", "null"}:
        return None

    texto = texto.replace(" ", "").replace("\u00a0", "")

    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            # Exemplo: 1.234,56
            texto = texto.replace(".", "").replace(",", ".")
        else:
            # Exemplo: 1,234.56
            texto = texto.replace(",", "")
    elif "," in texto:
        # Vírgula como separador decimal.
        texto = texto.replace(",", ".")

    try:
        numero = Decimal(texto)
    except InvalidOperation:
        return None

    return numero if numero.is_finite() else None


def formatar_decimal_truncado(valor: Decimal | None) -> str:
    """Trunca o valor a três casas decimais e usa ponto como separador."""
    if valor is None:
        return ""

    fator = Decimal(1).scaleb(-CASAS_DECIMAIS_NOMINAL)

    with localcontext() as contexto:
        contexto.prec = 50
        valor_truncado = valor.quantize(fator, rounding=ROUND_DOWN)

    texto = format(valor_truncado, "f")

    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")

    return texto


# ====
# PROCESSAMENTO PRINCIPAL
# ====

def main() -> None:
    try:
        for caminho in [ARQUIVO_BASE, ARQUIVO_CNAE_CRIATIVA]:
            if not caminho.exists():
                raise FileNotFoundError(
                    f"Arquivo não encontrado: {caminho}"
                )

        df_cnae = pd.read_excel(
            ARQUIVO_CNAE_CRIATIVA,
            usecols=[COL_CNAE_AUX],
            dtype=str,
        )
        df_cnae.columns = [
            str(coluna).replace("\ufeff", "").strip()
            for coluna in df_cnae.columns
        ]

        if COL_CNAE_AUX not in df_cnae.columns:
            raise KeyError(
                f"Coluna '{COL_CNAE_AUX}' não encontrada em "
                f"{ARQUIVO_CNAE_CRIATIVA}."
            )

        cnaes_criativos = set(
            normalizar_cnae(df_cnae[COL_CNAE_AUX]).dropna()
        )

        if not cnaes_criativos:
            raise ValueError(
                f"Nenhum CNAE válido encontrado em "
                f"{ARQUIVO_CNAE_CRIATIVA}."
            )

        print(
            "CNAEs da Economia Criativa carregados: "
            f"{len(cnaes_criativos):,}"
        )
        print(
            f"Processando a base em chunks de {CHUNK_SIZE:,} linhas..."
        )

        soma: dict[tuple[str, str], Decimal] = {}
        quantidade: dict[tuple[str, str], int] = {}

        leitor = pd.read_csv(
            ARQUIVO_BASE,
            sep=";",
            encoding="utf-8-sig",
            usecols=[
                COL_CNAE_BASE,
                COL_SALARIO,
                COL_RACA,
                COL_SEXO,
            ],
            dtype=str,
            chunksize=CHUNK_SIZE,
            low_memory=False,
        )

        for numero_chunk, chunk in enumerate(leitor, start=1):
            cnae_normalizado = normalizar_cnae(chunk[COL_CNAE_BASE])
            chunk = chunk.loc[
                cnae_normalizado.isin(cnaes_criativos)
            ].copy()

            if chunk.empty:
                print(
                    f"  Chunk {numero_chunk}: nenhum registro "
                    "de Economia Criativa."
                )
                continue

            chunk["codigo_raca"] = normalizar_codigo_categoria(
                chunk[COL_RACA]
            )
            chunk["codigo_sexo"] = normalizar_codigo_categoria(
                chunk[COL_SEXO]
            )

            chunk["raca_cor"] = chunk["codigo_raca"].map(MAPA_RACA)
            chunk["sexo"] = chunk["codigo_sexo"].map(MAPA_SEXO)
            chunk["salario_decimal"] = chunk[COL_SALARIO].map(
                converter_decimal
            )

            chunk = chunk.loc[
                chunk["raca_cor"].notna()
                & chunk["sexo"].notna()
                & chunk["salario_decimal"].map(
                    lambda valor: valor is not None and valor > 0
                )
            ]

            if chunk.empty:
                print(
                    f"  Chunk {numero_chunk}: nenhum registro válido "
                    "após os filtros."
                )
                continue

            with localcontext() as contexto:
                contexto.prec = 50

                for raca, sexo, salario in zip(
                    chunk["raca_cor"],
                    chunk["sexo"],
                    chunk["salario_decimal"],
                ):
                    chave = (str(raca), str(sexo))
                    soma[chave] = soma.get(chave, Decimal("0")) + salario
                    quantidade[chave] = quantidade.get(chave, 0) + 1

            print(f"  Chunk {numero_chunk} processado.")

        if not soma:
            raise ValueError(
                "Nenhum dado válido foi acumulado após os filtros. "
                "Verifique os arquivos de entrada e os códigos de "
                "raça/cor e sexo."
            )

        registros = []

        for (raca, sexo), soma_salarios in soma.items():
            qtd = quantidade[(raca, sexo)]

            with localcontext() as contexto:
                contexto.prec = 50
                media = soma_salarios / Decimal(qtd)

            registros.append(
                {
                    "raca_cor": raca,
                    "sexo": sexo,
                    "media_salarial_deflacionada_2024":
                        formatar_decimal_truncado(media),
                }
            )

        resultado = pd.DataFrame(
            registros,
            columns=[
                "raca_cor",
                "sexo",
                "media_salarial_deflacionada_2024",
            ],
        )

        resultado["_ordem_raca"] = resultado["raca_cor"].map(
            {valor: indice for indice, valor in enumerate(ORDEM_RACA)}
        )
        resultado["_ordem_sexo"] = resultado["sexo"].map(
            {valor: indice for indice, valor in enumerate(ORDEM_SEXO)}
        )

        resultado = (
            resultado.sort_values(
                ["_ordem_raca", "_ordem_sexo"],
                kind="stable",
            )
            .drop(columns=["_ordem_raca", "_ordem_sexo"])
            .reset_index(drop=True)
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

    except FileNotFoundError as erro:
        print(f"Erro: {erro}")

    except (KeyError, ValueError) as erro:
        print(f"Erro de validação dos dados: {erro}")

    except Exception as erro:
        print(f"Erro inesperado: {erro}")


if __name__ == "__main__":
    main()