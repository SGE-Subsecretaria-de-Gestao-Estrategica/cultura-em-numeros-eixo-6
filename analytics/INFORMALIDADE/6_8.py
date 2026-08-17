import os
import pandas as pd

# Configurações de caminhos
CAMINHO_XLSX_ENTRADA = r"E:\Rais\Rais\Auxiliares\Informalidade2.xlsx"
ARQUIVO_SAIDA = r"E:\Rais\Rais\csvs\6_8.csv"


def main():
    try:
        # Leitura do arquivo de origem
        df = pd.read_excel(CAMINHO_XLSX_ENTRADA)
        df.columns = df.columns.astype(str).str.strip()

        for coluna in ["Escopo", "Escala", "Recorte"]:
            df[coluna] = df[coluna].astype(str).str.strip()

        for coluna in ["Formal - Total", "Informal - Total", "Ano"]:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

        # Filtro base: dados nacionais do Brasil
        filtro_base = (
            df["Escala"].str.contains("Nacional", case=False, na=False)
            & df["Recorte"].str.contains("Brasil", case=False, na=False)
        )

        # Brasil: Escopo Total
        brasil = df[
            filtro_base
            & df["Escopo"].str.contains("Total", case=False, na=False)
        ][["Ano", "Informal - Total"]].rename(
            columns={"Informal - Total": "taxa_informalidade_brasil"}
        )

        # Economia Criativa: Escopo Cultura
        economia_criativa = df[
            filtro_base
            & df["Escopo"].str.contains("Cultura", case=False, na=False)
        ][["Ano", "Informal - Total"]].rename(
            columns={"Informal - Total": "taxa_informalidade_ec"}
        )

        if brasil.empty:
            raise ValueError("Nenhum dado encontrado para 'Brasil' no arquivo.")
        if economia_criativa.empty:
            raise ValueError("Nenhum dado encontrado para 'Cultura' no arquivo.")

        # Merge e ordenação — reproduz exatamente a base do gráfico
        dados = pd.merge(brasil, economia_criativa, on="Ano", how="inner")
        dados = dados.sort_values("Ano").reset_index(drop=True)
        dados["Ano"] = dados["Ano"].astype(int)

        if dados[["taxa_informalidade_brasil", "taxa_informalidade_ec"]].isna().any().any():
            raise ValueError(
                "Há valores ausentes nas taxas de informalidade. "
                "Confira a coluna 'Informal - Total' no arquivo."
            )

        # Monta o DataFrame de saída com apenas os dados plotados
        resultado = dados.rename(columns={"Ano": "ano"}).copy()
        resultado.insert(0, "grupo", "Economia Criativa")

        # Cria o diretório de saída, se necessário
        os.makedirs(os.path.dirname(ARQUIVO_SAIDA), exist_ok=True)

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
        print(f"Erro: arquivo de entrada não encontrado: {CAMINHO_XLSX_ENTRADA}")

    except Exception as erro:
        print(f"Erro ao gerar o CSV: {erro}")


if __name__ == "__main__":
    main()