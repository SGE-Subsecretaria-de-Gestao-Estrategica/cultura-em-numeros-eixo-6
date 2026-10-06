"""
6_6.py
====
Lê o CSV base (saída do 02adicionar_informalidade_metricas_2016_2025) e calcula
a participação do setor cultural no emprego total, usando os valores nominais
do IBGE que o arquivo base agora contém — sem estimativa por percentuais.

Colunas utilizadas no novo formato do CSV base:
    total_vinculos_ibge                ← Trabalhadores - Total   (nominal, IBGE)
    total_vinculos_informais_estimado  ← Trabalhadores - Cultura (nominal, IBGE)

Regras:
    - grupo "Brasil"  → usa total_vinculos_ibge (Trabalhadores - Total)
    - grupo "Cultura" → usa total_vinculos_informais_estimado (Trabalhadores - Cultura)
    - pct_participacao = cultura / total, truncado a 5 casas decimais
    - 2025 e anos sem valor nominal ficam em branco
    - Saída: sep=';' e encoding='utf-8-sig'
"""

import os
import re
from decimal import Decimal, InvalidOperation, ROUND_DOWN

import pandas as pd

# Caminhos
CAMINHO_CSV_ENTRADA = (
    r"E:\Rais\Rais\DF1\data\rais_metricas_grupos_2015_2025_com_informalidade.csv"
)
ARQUIVO_SAIDA = r"E:\Rais\Rais\csvs\6.6.csv"

NOME_GRUPO_BRASIL = "Brasil"
NOME_GRUPO_CULTURA = "Cultura"
NOME_GRUPO_EXIBICAO = "Economia Criativa"


def parse_decimal(valor):
    """Converte número em formato brasileiro ou internacional para Decimal."""
    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    if texto.lower() in ("", "nan", "none", "na", "n/a", "n/d", "-", "--"):
        return None

    # Notação científica
    if "e" in texto.lower():
        texto = texto.replace(",", ".")
        try:
            return Decimal(texto)
        except InvalidOperation:
            return None

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
        return Decimal(texto)
    except InvalidOperation:
        return None


def formatar_percentual(valor):
    """Trunca o percentual a no máximo cinco casas decimais, sem notação científica."""
    if valor is None:
        return ""

    valor_truncado = valor.quantize(
        Decimal("0.00001"),
        rounding=ROUND_DOWN,
    )
    texto = format(valor_truncado, "f").rstrip("0").rstrip(".")
    return texto if texto else "0"


def main():
    df = pd.read_csv(CAMINHO_CSV_ENTRADA, sep=";", dtype=str)
    df.columns = [coluna.strip().replace("\ufeff", "") for coluna in df.columns]

    colunas_necessarias = [
        "grupo",
        "ano",
        "total_vinculos_ibge",  # Trabalhadores - Total (nominal, IBGE)
        "total_vinculos_informais_estimado",  # Trabalhadores - Cultura (nominal, IBGE)
    ]
    colunas_ausentes = [
        coluna for coluna in colunas_necessarias if coluna not in df.columns
    ]

    if colunas_ausentes:
        raise KeyError(
            f"Coluna(s) ausente(s) no arquivo de origem: {colunas_ausentes}. "
            f"Colunas disponíveis: {df.columns.tolist()}"
        )

    # Mantém apenas Brasil e Cultura
    df = df.loc[
        df["grupo"].astype("string").str.strip().isin(
            [NOME_GRUPO_BRASIL, NOME_GRUPO_CULTURA]
        ),
        colunas_necessarias,
    ].copy()

    # Converte ano e componentes numéricos
    df["ano_decimal"] = df["ano"].apply(parse_decimal)
    df["total_vinculos_ibge"] = df["total_vinculos_ibge"].apply(parse_decimal)
    df["total_vinculos_informais_estimado"] = (
        df["total_vinculos_informais_estimado"].apply(parse_decimal)
    )

    # Remove apenas linhas sem ano; exige ano inteiro de quatro dígitos
    df = df.loc[df["ano_decimal"].notna()].copy()

    anos_invalidos = df.loc[
        df["ano_decimal"].apply(
            lambda ano: ano != ano.to_integral_value()
            or not 1000 <= int(ano) <= 9999
        )
    ]

    if not anos_invalidos.empty:
        raise ValueError("Há valores de ano que não são inteiros de quatro dígitos.")

    df["ano"] = df["ano_decimal"].astype(int)
    df = df.drop(columns=["ano_decimal"])

    # Evita agregar registros duplicados de grupo e ano
    duplicados = df.duplicated(subset=["grupo", "ano"], keep=False)
    if duplicados.any():
        exemplos = df.loc[duplicados, ["grupo", "ano"]].to_dict("records")
        raise ValueError(
            "Há mais de uma linha para o mesmo grupo e ano; "
            f"não foi feita agregação. Exemplos: {exemplos[:10]}"
        )

    # Usa os valores nominais do IBGE já presentes no arquivo base:
    #   grupo Brasil  → total_vinculos_ibge (Trabalhadores - Total)
    #   grupo Cultura → total_vinculos_informais_estimado (Trabalhadores - Cultura)
    # Não há soma nem estimativa: os valores nominais já incluem formal e informal.
    totais_por_grupo_ano = {}

    for _, linha in df.iterrows():
        grupo = linha["grupo"].strip()

        if grupo == NOME_GRUPO_BRASIL:
            total = linha["total_vinculos_ibge"]
        else:
            total = linha["total_vinculos_informais_estimado"]

        totais_por_grupo_ano[(grupo, linha["ano"])] = total

    linhas_saida = []

    anos = sorted(df["ano"].unique())

    for ano in anos:
        total_brasil = totais_por_grupo_ano.get((NOME_GRUPO_BRASIL, ano))
        total_cultura = totais_por_grupo_ano.get((NOME_GRUPO_CULTURA, ano))

        if (
            total_brasil is None
            or total_cultura is None
            or total_brasil == 0
        ):
            participacao = ""
        else:
            participacao = formatar_percentual(total_cultura / total_brasil)

        linhas_saida.append({
            "grupo": NOME_GRUPO_EXIBICAO,
            "ano": ano,
            "pct_participacao": participacao,
        })

    resultado = pd.DataFrame(
        linhas_saida,
        columns=["grupo", "ano", "pct_participacao"],
    )

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