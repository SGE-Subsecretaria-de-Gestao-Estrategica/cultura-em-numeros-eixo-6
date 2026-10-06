import os
import re
from decimal import Decimal

import numpy as np
import pandas as pd

# Caminhos
CAMINHO_CSV_ENTRADA = (
    r"E:\Rais\Rais\DF1\data\rais_metricas_grupos_2015_2025_com_informalidade.csv"
)
ARQUIVO_SAIDA = r"E:\Rais\Rais\csvs\6.5.csv"

NOME_GRUPO_ARQUIVO = "Cultura"
NOME_GRUPO_EXIBICAO = "Economia Criativa"


def parse_num(valor):
    """Converte valores numéricos com separadores brasileiros ou internacionais."""
    if pd.isna(valor):
        return np.nan

    texto = str(valor).strip()

    if texto.lower() in ("", "nan", "none", "na", "n/a", "n/d", "-", "--"):
        return np.nan

    # Notação científica
    if "e" in texto.lower():
        try:
            return float(texto.replace(",", "."))
        except ValueError:
            return np.nan

    tem_ponto = "." in texto
    tem_virgula = "," in texto

    if tem_ponto and tem_virgula:
        # O separador mais à direita é tratado como decimal.
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


def formato_sem_notacao_cientifica(valor):
    """Formata números sem notação científica e sem zeros decimais desnecessários."""
    if pd.isna(valor):
        return ""

    numero = Decimal(str(valor)).normalize()
    return format(numero, "f")


def main():
    df = pd.read_csv(CAMINHO_CSV_ENTRADA, sep=";", dtype=str)
    df.columns = [coluna.strip().replace("\ufeff", "") for coluna in df.columns]

    colunas_necessarias = [
        "grupo",
        "ano",
        "total_vinculos_informais_estimado",
    ]
    colunas_ausentes = [
        coluna for coluna in colunas_necessarias if coluna not in df.columns
    ]

    if colunas_ausentes:
        raise KeyError(
            f"Coluna(s) não encontrada(s): {colunas_ausentes}. "
            f"Colunas disponíveis: {df.columns.tolist()}"
        )

    # Filtra o grupo de interesse
    mascara = (
        df["grupo"]
        .astype("string")
        .str.strip()
        .eq(NOME_GRUPO_ARQUIVO)
    )
    resultado = df.loc[mascara, colunas_necessarias].copy()

    if resultado.empty:
        raise ValueError(
            f"Nenhuma linha com grupo '{NOME_GRUPO_ARQUIVO}' foi encontrada."
        )

    # Converte os campos numéricos
    for coluna in [
        "ano",
        "total_vinculos_informais_estimado",
    ]:
        resultado[coluna] = resultado[coluna].apply(parse_num)

    # Remove linhas sem ano e converte anos válidos para inteiro
    resultado = resultado.dropna(subset=["ano"]).copy()
    resultado["ano"] = resultado["ano"].astype(int)

    # Valor vem diretamente da coluna de referência total_vinculos_informais_estimado,
    # sem soma com a RAIS; a variação anual é calculada a partir dele.
    resultado["total_vinculos_informais_estimado"] = resultado[
        "total_vinculos_informais_estimado"
    ]

    # Variação anual na escala 0–1; ausências não são preenchidas artificialmente
    resultado = resultado.sort_values("ano").reset_index(drop=True)
    resultado["pct_variacao_anual"] = resultado[
        "total_vinculos_informais_estimado"
    ].pct_change(fill_method=None)

    # Valores infinitos podem surgir se o valor do ano anterior for zero;
    # nesse caso, a variação fica como dado faltante.
    resultado["pct_variacao_anual"] = resultado[
        "pct_variacao_anual"
    ].replace([np.inf, -np.inf], np.nan)

    # Monta a saída com nomes de coluna padronizados
    saida = resultado[
        ["ano", "total_vinculos_informais_estimado", "pct_variacao_anual"]
    ].copy()
    saida.insert(0, "grupo", NOME_GRUPO_EXIBICAO)

    # Formata os campos numéricos sem notação científica
    for coluna in [
        "total_vinculos_informais_estimado",
        "pct_variacao_anual",
    ]:
        saida[coluna] = saida[coluna].apply(formato_sem_notacao_cientifica)

    os.makedirs(os.path.dirname(ARQUIVO_SAIDA), exist_ok=True)

    saida.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        sep=";",
        decimal=".",
        encoding="utf-8-sig",
        na_rep="",
    )

    print(f"CSV gerado com sucesso em: {ARQUIVO_SAIDA}")
    print(f"Total de registros exportados: {len(saida)}")


if __name__ == "__main__":
    main()