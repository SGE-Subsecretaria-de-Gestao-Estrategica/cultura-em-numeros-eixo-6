import os
import re
import numpy as np
import pandas as pd

# Configurações de caminhos
CAMINHO_CSV_ENTRADA = (
    r"E:\Rais\Rais\DF1\data\rais_metricas_grupos_2015_2024_com_informalidade.csv"
)
ARQUIVO_SAIDA = r"E:\Rais\Rais\csvs\6_6.csv"

NOME_GRUPO_EXIBICAO = "Economia Criativa"


def parse_num(valor):
    """Converte números em formatos brasileiros e notação científica."""
    if pd.isna(valor):
        return np.nan

    s = str(valor).strip()

    if s in ("", "nan", "None"):
        return np.nan

    if "E" in s.upper():
        s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return np.nan

    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", s):
        s = s.replace(".", "")
    else:
        s = s.replace(",", ".")

    try:
        return float(s)
    except ValueError:
        return np.nan


def main():
    try:
        # Leitura como texto para lidar corretamente com formatos brasileiros
        df = pd.read_csv(CAMINHO_CSV_ENTRADA, sep=";", dtype=str)
        df.columns = [coluna.strip().replace("\ufeff", "") for coluna in df.columns]

        # Valida as colunas necessárias
        colunas_necessarias = [
            "grupo",
            "ano",
            "total_vinculos",
            "total_vinculos_informais_estimado",
        ]
        colunas_ausentes = set(colunas_necessarias) - set(df.columns)

        if colunas_ausentes:
            raise KeyError(
                "Colunas ausentes no arquivo de origem: "
                + ", ".join(sorted(colunas_ausentes))
            )

        # Converte as colunas numéricas utilizadas no cálculo do gráfico
        for coluna in [
            "ano",
            "total_vinculos",
            "total_vinculos_informais_estimado",
        ]:
            df[coluna] = df[coluna].apply(parse_num)

        # Filtra os grupos usados no cálculo da participação
        brasil = df.loc[
            df["grupo"].astype(str).str.strip().eq("Brasil")
        ].copy()

        cultura = df.loc[
            df["grupo"].astype(str).str.strip().eq("Cultura")
        ].copy()

        if brasil.empty:
            raise ValueError("Nenhuma linha com grupo 'Brasil' foi encontrada.")

        if cultura.empty:
            raise ValueError("Nenhuma linha com grupo 'Cultura' foi encontrada.")

        # Calcula total de vínculos: formais + informais estimados
        brasil["total"] = (
            brasil["total_vinculos"].fillna(0)
            + brasil["total_vinculos_informais_estimado"].fillna(0)
        )

        cultura["total"] = (
            cultura["total_vinculos"].fillna(0)
            + cultura["total_vinculos_informais_estimado"].fillna(0)
        )

        # Agrega por ano para reproduzir exatamente a base do gráfico
        brasil_por_ano = brasil.groupby("ano", as_index=False)["total"].sum()
        cultura_por_ano = cultura.groupby("ano", as_index=False)["total"].sum()

        dados_grafico = pd.merge(
            brasil_por_ano,
            cultura_por_ano,
            on="ano",
            suffixes=("_brasil", "_cultura"),
            how="inner",
        ).sort_values("ano")

        # Participação em proporção decimal:
        # 0,025 equivale a 2,5%
        dados_grafico["participacao_pct"] = (
            dados_grafico["total_cultura"] / dados_grafico["total_brasil"]
        )

        # Mantém exclusivamente os dados efetivamente plotados no gráfico
        resultado = dados_grafico[["ano", "participacao_pct"]].copy()
        resultado["ano"] = resultado["ano"].astype(int)
        resultado.insert(0, "grupo", NOME_GRUPO_EXIBICAO)

        # Cria a pasta de destino, se necessário
        os.makedirs(os.path.dirname(ARQUIVO_SAIDA), exist_ok=True)

        # Salva o CSV no padrão brasileiro
        resultado.to_csv(
            ARQUIVO_SAIDA,
            index=False,
            sep=";",
            decimal=",",
            encoding="utf-8-sig",
        )

        print(f"CSV gerado com sucesso em: {ARQUIVO_SAIDA}")
        print(f"Total de registros exportados: {len(resultado)}")

    except FileNotFoundError:
        print(f"Erro: arquivo de entrada não encontrado: {CAMINHO_CSV_ENTRADA}")

    except Exception as erro:
        print(f"Erro ao gerar o CSV: {erro}")


if __name__ == "__main__":
    main()