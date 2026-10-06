import os
import unicodedata
from decimal import Decimal, ROUND_DOWN

import pandas as pd

# Caminhos
CAMINHO_XLSX_ENTRADA = r"E:\Rais\Rais\Informalidade\Informalidade2.xlsx"
ARQUIVO_SAIDA = r"E:\Rais\Rais\csvs\6_8.csv"

# Valores esperados nas colunas de filtro (comparação exata, sem acento, minúsculas)
VALOR_ESCALA = "nacional"
VALOR_RECORTE = "brasil"
ESCOPO_BRASIL = "total"
ESCOPO_EC = "cultura"

# Rótulos de categoria na saída (iguais aos dos demais arquivos)
GRUPO_BRASIL = "Brasil"
GRUPO_EC = "Economia Criativa"


def normalizar_texto(valor):
    """Minúsculas, sem espaços nas pontas e sem acentos, para comparação exata."""
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().casefold()
    texto = unicodedata.normalize("NFKD", texto)

    return "".join(c for c in texto if not unicodedata.combining(c))


def formatar_percentual(valor):
    """Trunca o percentual a no máximo cinco casas decimais, sem notação científica."""
    if pd.isna(valor):
        return ""

    valor_truncado = Decimal(str(valor)).quantize(
        Decimal("0.00001"),
        rounding=ROUND_DOWN,
    )
    texto = format(valor_truncado, "f").rstrip("0").rstrip(".")
    return texto if texto else "0"


def validar_ano(valor):
    """Converte o ano para inteiro; retorna None se ausente ou inválido."""
    if pd.isna(valor):
        return None

    try:
        ano = float(valor)
    except (TypeError, ValueError):
        return None

    if ano != int(ano) or not 1000 <= int(ano) <= 9999:
        raise ValueError(
            f"Ano inválido (esperado inteiro de quatro dígitos): {valor}"
        )

    return int(ano)


def main():
    df = pd.read_excel(CAMINHO_XLSX_ENTRADA)
    df.columns = df.columns.astype(str).str.strip()

    colunas_necessarias = ["Escopo", "Escala", "Recorte", "Ano", "Informal - Total"]
    colunas_ausentes = [
        coluna for coluna in colunas_necessarias if coluna not in df.columns
    ]

    if colunas_ausentes:
        raise KeyError(
            f"Coluna(s) não encontrada(s): {colunas_ausentes}. "
            f"Colunas disponíveis: {df.columns.tolist()}"
        )

    # Normaliza as colunas de filtro para comparação exata
    df["escala_norm"] = df["Escala"].apply(normalizar_texto)
    df["recorte_norm"] = df["Recorte"].apply(normalizar_texto)
    df["escopo_norm"] = df["Escopo"].apply(normalizar_texto)
    df["taxa"] = pd.to_numeric(df["Informal - Total"], errors="coerce")

    filtro_base = (df["escala_norm"] == VALOR_ESCALA) & (
        df["recorte_norm"] == VALOR_RECORTE
    )

    if not filtro_base.any():
        raise ValueError(
            "Nenhuma linha encontrada para os filtros "
            f"Escala='{VALOR_ESCALA}' e Recorte='{VALOR_RECORTE}'. "
            f"Valores disponíveis em Escala: {sorted(df['escala_norm'].unique())}; "
            f"em Recorte: {sorted(df['recorte_norm'].unique())}."
        )

    # Extrai a série (ano -> taxa) de cada grupo
    series_por_grupo = {}

    for valor_escopo, nome_grupo in [
        (ESCOPO_BRASIL, GRUPO_BRASIL),
        (ESCOPO_EC, GRUPO_EC),
    ]:
        selecao = df.loc[
            filtro_base & (df["escopo_norm"] == valor_escopo),
            ["Ano", "taxa"],
        ].copy()

        if selecao.empty:
            raise ValueError(
                f"Nenhuma linha encontrada para Escopo='{valor_escopo}'. "
                f"Valores disponíveis em Escopo: "
                f"{sorted(df.loc[filtro_base, 'escopo_norm'].unique())}."
            )

        selecao["ano"] = selecao["Ano"].apply(validar_ano)
        selecao = selecao.dropna(subset=["ano"])

        if selecao["ano"].duplicated().any():
            duplicados = sorted(
                selecao.loc[selecao["ano"].duplicated(keep=False), "ano"].unique()
            )
            raise ValueError(
                f"Há mais de uma linha para o grupo '{nome_grupo}' nos anos "
                f"{duplicados}; verifique a base de origem."
            )

        series_por_grupo[nome_grupo] = dict(
            zip(selecao["ano"], selecao["taxa"])
        )

    # União dos anos; anos sem dado em um dos grupos ficam com célula vazia
    anos = sorted(
        set(series_por_grupo[GRUPO_BRASIL]) | set(series_por_grupo[GRUPO_EC])
    )

    linhas = []

    for nome_grupo in [GRUPO_BRASIL, GRUPO_EC]:
        for ano in anos:
            taxa = series_por_grupo[nome_grupo].get(ano)
            linhas.append(
                {
                    "grupo": nome_grupo,
                    "ano": ano,
                    "taxa_informalidade": formatar_percentual(taxa),
                }
            )

    resultado = pd.DataFrame(linhas, columns=["grupo", "ano", "taxa_informalidade"])

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