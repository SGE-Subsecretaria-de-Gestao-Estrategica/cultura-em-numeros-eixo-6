import os
import re
from decimal import Decimal, InvalidOperation

import numpy as np
import pandas as pd

# Caminhos
CAMINHO_CSV_ENTRADA = (
    r"E:\Rais\Rais\DF1\data\rais_metricas_grupos_2015_2025_com_informalidade.csv"
)
ARQUIVO_SAIDA = r"E:\Rais\Rais\csvs\6.7.csv"

# Mapeamento dos grupos da base para os rótulos exibidos no gráfico
MAPEAMENTO_GRUPOS = {
    "Cultura": "Economia Criativa",
    "Agricultura, pecuária, produção florestal, pesca e aquicultura": "Agricultura",
    "Indústria extrativa": "Indústria extrativa",
    "Construção": "Construção Civil",
}


def parse_num(valor):
    """Converte números em formatos brasileiros e notação científica."""
    if pd.isna(valor):
        return np.nan

    texto = str(valor).strip()

    if texto.lower() in ("", "nan", "none", "na", "n/a", "n/d", "-", "--"):
        return np.nan

    if "e" in texto.lower():
        try:
            return float(texto.replace(",", "."))
        except ValueError:
            return np.nan

    tem_ponto = "." in texto
    tem_virgula = "," in texto

    if tem_ponto and tem_virgula:
        # O separador mais à direita é considerado decimal.
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif tem_virgula:
        if re.fullmatch(r"\d{1,3}(?:,\d{3})+", texto):
            texto = texto.replace(",", "")
        else:
            texto = texto.replace(",", ".")
    elif tem_ponto and re.fullmatch(r"\d{1,3}(?:\.\d{3})+", texto):
        texto = texto.replace(".", "")

    try:
        return float(texto)
    except ValueError:
        return np.nan


def formatar_numero(valor):
    """Formata sem notação científica; inteiros sem casas decimais."""
    if pd.isna(valor):
        return ""

    numero = Decimal(str(valor)).normalize()

    if numero == numero.to_integral_value():
        return str(int(numero))

    return format(numero, "f")


def validar_colunas(df, colunas_esperadas):
    """Verifica se as colunas obrigatórias estão presentes na base."""
    colunas_ausentes = set(colunas_esperadas) - set(df.columns)

    if colunas_ausentes:
        raise ValueError(
            "Colunas obrigatórias ausentes no arquivo de entrada: "
            + ", ".join(sorted(colunas_ausentes))
        )


def main():
    # Leitura como texto para tratar os formatos brasileiros da base
    df = pd.read_csv(CAMINHO_CSV_ENTRADA, sep=";", dtype=str)
    df.columns = [coluna.strip().replace("\ufeff", "") for coluna in df.columns]

    validar_colunas(df, ["grupo", "ano", "total_vinculos_rais"])

    # Mantém apenas os grupos exibidos no gráfico
    resultado = df.loc[
        df["grupo"].astype("string").str.strip().isin(MAPEAMENTO_GRUPOS),
        ["grupo", "ano", "total_vinculos_rais"],
    ].copy()

    if resultado.empty:
        raise ValueError(
            "Nenhum dos grupos definidos foi encontrado no arquivo de entrada."
        )

    # Converte ano e total de vínculos
    resultado["ano"] = resultado["ano"].apply(parse_num)
    resultado["total_vinculos_rais"] = resultado["total_vinculos_rais"].apply(parse_num)

    # Remove apenas linhas sem ano; exige ano inteiro de quatro dígitos
    resultado = resultado.dropna(subset=["ano"]).copy()

    mascara_ano_invalido = resultado["ano"].apply(
        lambda ano: ano != int(ano) or not 1000 <= int(ano) <= 9999
    )

    if mascara_ano_invalido.any():
        raise ValueError(
            "Há valores de ano que não são inteiros de quatro dígitos: "
            f"{resultado.loc[mascara_ano_invalido, 'ano'].tolist()[:10]}"
        )

    resultado["ano"] = resultado["ano"].astype(int)

    # Req. 3: uma linha por grupo e ano; duplicatas não são somadas nem deduplicadas
    duplicados = resultado.duplicated(subset=["grupo", "ano"], keep=False)

    if duplicados.any():
        exemplos = resultado.loc[duplicados, ["grupo", "ano"]].to_dict("records")
        raise ValueError(
            "Há mais de uma linha para o mesmo grupo e ano. "
            f"Exemplos: {exemplos[:10]}"
        )

    # Req. 13: rótulos de categoria iguais aos dos demais arquivos
    resultado["grupo"] = resultado["grupo"].str.strip().map(MAPEAMENTO_GRUPOS)

    resultado = resultado[["grupo", "ano", "total_vinculos_rais"]].sort_values(
        ["grupo", "ano"]
    )

    # Req. 8/12: sem notação científica; faltante como célula vazia
    resultado["total_vinculos_rais"] = resultado["total_vinculos_rais"].apply(formatar_numero)

    os.makedirs(os.path.dirname(ARQUIVO_SAIDA), exist_ok=True)

    resultado.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        sep=";",
        encoding="utf-8-sig",
        na_rep="",
    )

    print(f"CSV gerado com sucesso em: {ARQUIVO_SAIDA}")
    print(f"Total de registros exportados: {len(resultado)}")


if __name__ == "__main__":
    main()