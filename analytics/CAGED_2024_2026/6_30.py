from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_DOWN, localcontext
from pathlib import Path

import pandas as pd


# ====
# CONFIGURACAO
# ====

ARQUIVO_ENTRADA = Path(
    r"E:\Rais\CAGED\data\caged_IRCA_final_2016_2026.csv"
)
ARQUIVO_SAIDA = Path(r"E:\Rais\Rais\csvs\6.30.csv")

GRUPO_CULTURA = "Cultura"
ROTULO_ECONOMIA_CRIATIVA = "Economia Criativa"
GRUPO_BRASIL = "Brasil"

ANO_CORTE = 2024
MES_CORTE = 12
CASAS_DECIMAIS_PERCENTUAL = 5

COL_ANO_ORIGEM = "ano"
COL_MES_ORIGEM = "mes"
COL_GRUPO_ORIGEM = "grupo"
COL_IRCA_VINCULOS_ORIGEM = "IRCA_Vinculos"
COL_IRCA_SALARIAL_ORIGEM = "IRCA_Salarial"


# ====
# FUNCOES AUXILIARES
# ====

def converter_decimal(valor) -> Decimal | None:
    """
    Converte um valor numérico para Decimal.

    Aceita ponto ou vírgula decimal. Se houver ambos, interpreta como
    separador decimal o que estiver mais à direita.
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
        texto = texto.replace(",", ".")

    try:
        numero = Decimal(texto)
    except InvalidOperation:
        return None

    return numero if numero.is_finite() else None


def converter_inteiro(valor) -> int | None:
    """Converte ano ou mês para inteiro, retornando None se inválido."""
    numero = converter_decimal(valor)

    if numero is None:
        return None

    if numero != numero.to_integral_value():
        return None

    return int(numero)


def formatar_percentual_truncado(valor: Decimal | None) -> str:
    """Trunca a proporção percentual a até cinco casas decimais."""
    if valor is None:
        return ""

    fator = Decimal(1).scaleb(-CASAS_DECIMAIS_PERCENTUAL)

    with localcontext() as contexto:
        contexto.prec = 50
        valor_truncado = valor.quantize(fator, rounding=ROUND_DOWN)

    texto = format(valor_truncado, "f")

    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")

    return texto


def grupo_contem_rotulo(serie: pd.Series, rotulo: str) -> pd.Series:
    """Faz uma busca tolerante a maiúsculas, minúsculas e espaços."""
    valores = serie.astype("string").str.strip().str.casefold()
    termo = rotulo.strip().casefold()
    return valores.str.contains(termo, regex=False, na=False)


def calcular_variacao(irca: Decimal | None) -> str:
    """Converte um índice em base 100 para proporção de variação."""
    if irca is None:
        return ""

    with localcontext() as contexto:
        contexto.prec = 50
        variacao = (irca - Decimal("100")) / Decimal("100")

    return formatar_percentual_truncado(variacao)


def preparar_grupo(
    df_origem: pd.DataFrame,
    rotulo_origem: str,
    rotulo_saida: str,
) -> list[dict]:
    """Filtra um grupo, calcula variações e aplica o corte temporal."""
    mascara_grupo = grupo_contem_rotulo(
        df_origem[COL_GRUPO_ORIGEM],
        rotulo_origem,
    )
    df_grupo = df_origem.loc[mascara_grupo]

    registros = []

    for _, linha in df_grupo.iterrows():
        ano = converter_inteiro(linha[COL_ANO_ORIGEM])
        mes = converter_inteiro(linha[COL_MES_ORIGEM])

        if ano is None or mes is None or not 1 <= mes <= 12:
            continue

        if (ano, mes) < (ANO_CORTE, MES_CORTE):
            continue

        irca_vinculos = converter_decimal(
            linha[COL_IRCA_VINCULOS_ORIGEM]
        )
        irca_salarial = converter_decimal(
            linha[COL_IRCA_SALARIAL_ORIGEM]
        )

        # Mantém a observação quando ao menos um dos indicadores é válido.
        if irca_vinculos is None and irca_salarial is None:
            continue

        registros.append(
            {
                "ano": ano,
                "mes": mes,
                "grupo": rotulo_saida,
                "pct_variacao_vinculos": calcular_variacao(irca_vinculos),
                "pct_variacao_salarial": calcular_variacao(irca_salarial),
            }
        )

    return registros


# ====
# PROCESSAMENTO PRINCIPAL
# ====

def main() -> None:
    try:
        if not ARQUIVO_ENTRADA.exists():
            raise FileNotFoundError(
                f"Arquivo de entrada não encontrado: {ARQUIVO_ENTRADA}"
            )

        print("Lendo arquivo CAGED...")

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

        colunas_necessarias = {
            COL_ANO_ORIGEM,
            COL_MES_ORIGEM,
            COL_GRUPO_ORIGEM,
            COL_IRCA_VINCULOS_ORIGEM,
            COL_IRCA_SALARIAL_ORIGEM,
        }
        colunas_ausentes = sorted(colunas_necessarias - set(df.columns))

        if colunas_ausentes:
            raise KeyError(
                "Colunas obrigatórias ausentes no arquivo: "
                f"{colunas_ausentes}"
            )

        registros = []
        registros.extend(
            preparar_grupo(
                df,
                GRUPO_CULTURA,
                ROTULO_ECONOMIA_CRIATIVA,
            )
        )
        registros.extend(
            preparar_grupo(
                df,
                GRUPO_BRASIL,
                GRUPO_BRASIL,
            )
        )

        if not any(
            registro["grupo"] == ROTULO_ECONOMIA_CRIATIVA
            for registro in registros
        ):
            raise ValueError(
                "Nenhum registro de Cultura encontrado a partir "
                "de dezembro de 2024."
            )

        if not any(
            registro["grupo"] == GRUPO_BRASIL
            for registro in registros
        ):
            raise ValueError(
                "Nenhum registro de Brasil encontrado a partir "
                "de dezembro de 2024."
            )

        resultado = pd.DataFrame(
            registros,
            columns=[
                "ano",
                "mes",
                "grupo",
                "pct_variacao_vinculos",
                "pct_variacao_salarial",
            ],
        )

        resultado = resultado.sort_values(
            ["ano", "mes", "grupo"],
            kind="stable",
        ).reset_index(drop=True)

        ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
        resultado.to_csv(
            ARQUIVO_SAIDA,
            index=False,
            sep=";",
            encoding="utf-8-sig",
            na_rep="",
        )

        print(f"\nCSV gerado com sucesso: {ARQUIVO_SAIDA}")
        print(f"Registros exportados: {len(resultado):,}")

    except FileNotFoundError as erro:
        print(f"Erro: {erro}")

    except KeyError as erro:
        print(f"Erro de estrutura do arquivo: {erro}")

    except ValueError as erro:
        print(f"Erro de validação: {erro}")

    except Exception as erro:
        print(f"Erro inesperado: {erro}")


if __name__ == "__main__":
    main()