import os
import pandas as pd

# Configurações de caminhos
CAMINHO_CSV_ENTRADA = (
    r"E:\Rais\Rais\DF1\data\rais_metricas_grupos_2016_2025_com_informalidade.csv"
)
ARQUIVO_SAIDA = r"E:\Rais\Rais\csvs\6.7.csv"

# Mapeamento dos grupos presentes na base para os nomes exibidos no gráfico
MAPEAMENTO_GRUPOS = {
    "Cultura": "Economia Criativa",
    "Agricultura, pecuária, produção florestal, pesca e aquicultura": "Agricultura",
    "Indústria extrativa": "Indústria extrativa",
    "Construção": "Construção Civil",
}


def validar_colunas(df, colunas_esperadas):
    """Verifica se as colunas obrigatórias estão presentes na base."""
    colunas_ausentes = set(colunas_esperadas) - set(df.columns)

    if colunas_ausentes:
        raise ValueError(
            "Colunas obrigatórias ausentes no arquivo de entrada: "
            + ", ".join(sorted(colunas_ausentes))
        )


def main():
    try:
        # Lê a base original usando o mesmo padrão do script do gráfico
        df = pd.read_csv(
            CAMINHO_CSV_ENTRADA,
            sep=";",
            decimal=","
        )

        validar_colunas(df, ["grupo", "ano", "total_vinculos"])

        # Mantém apenas os grupos exibidos no gráfico
        resultado = df.loc[
            df["grupo"].isin(MAPEAMENTO_GRUPOS.keys()),
            ["grupo", "ano", "total_vinculos"]
        ].copy()

        if resultado.empty:
            raise ValueError(
                "Nenhum dos grupos definidos foi encontrado no arquivo de entrada."
            )

        # Renomeia os grupos conforme a legenda do gráfico
        resultado["grupo_original"] = resultado["grupo"]
        resultado["grupo"] = resultado["grupo"].map(MAPEAMENTO_GRUPOS)

        # Organiza as colunas e os registros
        resultado = resultado[
            ["grupo_original", "grupo", "ano", "total_vinculos"]
        ].sort_values(["grupo", "ano"])

        # Cria a pasta de saída caso não exista
        os.makedirs(os.path.dirname(ARQUIVO_SAIDA), exist_ok=True)

        # Salva os dados brutos que alimentam o gráfico
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