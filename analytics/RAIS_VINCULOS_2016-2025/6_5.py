import os
import re
import numpy as np
import pandas as pd

# Configurações de caminhos
CAMINHO_CSV_ENTRADA = (
    r"E:\Rais\Rais\DF1\data\rais_metricas_grupos_2015_2024_com_informalidade.csv"
)
ARQUIVO_SAIDA = r"E:\Rais\Rais\csvs\6_5.csv"

NOME_GRUPO_ARQUIVO = "Cultura"
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
        # Leitura como texto para preservar a estrutura original do CSV
        df = pd.read_csv(CAMINHO_CSV_ENTRADA, sep=";", dtype=str)
        df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]

        # Filtra somente o grupo de Cultura
        mask = df["grupo"].astype(str).str.strip().eq(NOME_GRUPO_ARQUIVO)
        ec = df.loc[mask].copy()

        if ec.empty:
            raise ValueError(
                f"Nenhuma linha com grupo '{NOME_GRUPO_ARQUIVO}' foi encontrada."
            )

        # Converte colunas numéricas
        for col in ["ano", "total_vinculos", "total_vinculos_informais_estimado"]:
            if col not in ec.columns:
                raise KeyError(
                    f"Coluna '{col}' não encontrada. "
                    f"Colunas disponíveis: {df.columns.tolist()}"
                )
            ec[col] = ec[col].apply(parse_num)

        ec = ec.sort_values("ano").reset_index(drop=True)
        ec["ano"] = ec["ano"].astype(int)

        # Colunas derivadas — as mesmas usadas no gráfico
        ec["total_vinculos_formal_informal"] = (
            ec["total_vinculos"].fillna(0)
            + ec["total_vinculos_informais_estimado"].fillna(0)
        )

        ec["variacao_yoy_pct"] = ec["total_vinculos_formal_informal"].pct_change()

        # Monta o DataFrame de saída
        resultado = ec[[
            "ano",
            "total_vinculos_formal_informal",
            "variacao_yoy_pct",
        ]].copy()

        resultado.insert(0, "grupo", NOME_GRUPO_EXIBICAO)

        # Cria o diretório de saída, se necessário
        os.makedirs(os.path.dirname(ARQUIVO_SAIDA), exist_ok=True)

        resultado.to_csv(
            ARQUIVO_SAIDA,
            index=False,
            sep=";",
            decimal=",",
            encoding="utf-8-sig"
        )

        print(f"CSV gerado com sucesso em: {ARQUIVO_SAIDA}")
        print(f"Total de registros exportados: {len(resultado)}")

    except FileNotFoundError:
        print(f"Erro: arquivo de entrada não encontrado: {CAMINHO_CSV_ENTRADA}")

    except Exception as erro:
        print(f"Erro ao gerar o CSV: {erro}")


if __name__ == "__main__":
    main()