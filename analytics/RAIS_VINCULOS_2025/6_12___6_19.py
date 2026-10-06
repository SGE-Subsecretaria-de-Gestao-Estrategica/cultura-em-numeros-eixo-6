from __future__ import annotations

import os
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from pathlib import Path

import pandas as pd


# ====
# CONFIGURACOES
# ====

ARQUIVO_BASE = Path(
    r"D:\OneDrive\Minc\RAIS\RAIS_py\data\processed\rais_2025_filtrado.csv"
)
ARQUIVO_CNAE_CRIATIVA = Path(
    r"E:\Rais\Rais\Auxiliares\CNAE-ibge.xlsx"
)
ARQUIVO_SAIDA = Path(r"E:\Rais\Rais\csvs\6.12.csv")

CHUNK_SIZE = 300_000

CASAS_DECIMAIS_NOMINAL = 3
CASAS_DECIMAIS_PERCENTUAL = 5

COL_SEXO = "Sexo - Código"
COL_SALARIO = "vl_rem_media_nom_deflacionada_2024"
COL_CNAE = "CNAE 2.0 Subclasse - Código"
COL_CNAE_AUX = "CNAE_IBGE"

MAPA_SEXO = {
    "1": "Masculino",
    "2": "Feminino",
}
ORDEM_CATEGORIAS = ["Masculino", "Feminino"]


# ====
# FUNCOES AUXILIARES
# ====

def converter_decimal(valor) -> Decimal | None:
    """Converte números com vírgula ou ponto decimal para Decimal."""
    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    if texto.casefold() in {"", "nan", "none", "null"}:
        return None

    texto = texto.replace(" ", "")

    if "," in texto and "." in texto:
        # O separador mais à direita é tratado como decimal.
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", texto):
        # Ex.: 1.234 interpretado como milhar.
        texto = texto.replace(".", "")

    try:
        return Decimal(texto)
    except InvalidOperation:
        return None


def normalizar_cnae(serie: pd.Series) -> pd.Series:
    """Padroniza os códigos CNAE para comparação."""
    codigos = (
        serie.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .replace("", pd.NA)
    )
    return codigos.str.zfill(7)


def limitar_casas(valor: Decimal | None, casas: int) -> Decimal | None:
    """Limita o número de casas decimais, sem zeros à direita."""
    if valor is None:
        return None

    fator = Decimal(1).scaleb(-casas)
    return valor.quantize(fator, rounding=ROUND_HALF_UP)


def formatar_decimal(valor: Decimal | None) -> str:
    """Converte Decimal em texto com ponto decimal e sem zeros finais."""
    if valor is None:
        return ""

    texto = format(valor, "f")

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
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

        # Carrega os CNAEs da Economia Criativa.
        df_cnae_aux = pd.read_excel(
            ARQUIVO_CNAE_CRIATIVA,
            usecols=[COL_CNAE_AUX],
            dtype=str,
        )

        cnaes_criativos = set(
            normalizar_cnae(df_cnae_aux[COL_CNAE_AUX]).dropna()
        )

        if not cnaes_criativos:
            raise ValueError(
                "Nenhum código CNAE válido foi encontrado na planilha auxiliar."
            )

        print(
            "Códigos CNAE da Economia Criativa carregados: "
            f"{len(cnaes_criativos)}"
        )

        total_vinculos = {categoria: 0 for categoria in ORDEM_CATEGORIAS}
        soma_salarios = {
            categoria: Decimal("0") for categoria in ORDEM_CATEGORIAS
        }
        qtd_salarios_validos = {
            categoria: 0 for categoria in ORDEM_CATEGORIAS
        }

        print(f"\nProcessando arquivo-base em chunks de {CHUNK_SIZE} linhas...")

        leitor = pd.read_csv(
            ARQUIVO_BASE,
            sep=";",
            encoding="utf-8-sig",
            usecols=[COL_SEXO, COL_SALARIO, COL_CNAE],
            dtype=str,
            chunksize=CHUNK_SIZE,
            low_memory=False,
        )

        for numero_chunk, chunk in enumerate(leitor, 1):
            # Filtra os registros da Economia Criativa.
            mascara_ec = normalizar_cnae(chunk[COL_CNAE]).isin(
                cnaes_criativos
            )
            chunk = chunk.loc[mascara_ec].copy()

            if chunk.empty:
                print(f"  Chunk {numero_chunk}: nenhum registro de EC.")
                continue

            # Padroniza e mapeia as categorias de sexo.
            cod_sexo = (
                chunk[COL_SEXO]
                .astype("string")
                .str.strip()
                .str.replace(r"\.0$", "", regex=True)
            )
            chunk["sexo"] = cod_sexo.map(MAPA_SEXO)
            chunk = chunk.loc[chunk["sexo"].notna()].copy()

            # Conta vínculos por categoria.
            contagens = chunk["sexo"].value_counts()
            for categoria, quantidade in contagens.items():
                total_vinculos[categoria] += int(quantidade)

            # Soma salários válidos por categoria.
            for categoria in ORDEM_CATEGORIAS:
                salarios = chunk.loc[
                    chunk["sexo"] == categoria, COL_SALARIO
                ].map(converter_decimal)

                salarios_validos = [
                    salario
                    for salario in salarios
                    if salario is not None and salario > 0
                ]

                soma_salarios[categoria] += sum(
                    salarios_validos,
                    start=Decimal("0"),
                )
                qtd_salarios_validos[categoria] += len(salarios_validos)

            print(f"  Chunk {numero_chunk} processado.")

        total_geral = sum(total_vinculos.values())

        if total_geral == 0:
            raise ValueError(
                "Nenhum vínculo foi encontrado após os filtros. "
                "Verifique os arquivos de entrada."
            )

        registros = []

        for categoria in ORDEM_CATEGORIAS:
            quantidade = total_vinculos[categoria]

            # Não cria uma linha para categoria sem observações.
            if quantidade == 0:
                continue

            qtd_salarios = qtd_salarios_validos[categoria]

            if qtd_salarios:
                with localcontext() as contexto:
                    contexto.prec = 50
                    media_salarial = (
                        soma_salarios[categoria] / Decimal(qtd_salarios)
                    )
                media_salarial = limitar_casas(
                    media_salarial, CASAS_DECIMAIS_NOMINAL
                )
            else:
                media_salarial = None

            with localcontext() as contexto:
                contexto.prec = 50
                participacao = Decimal(quantidade) / Decimal(total_geral)

            participacao = limitar_casas(
                participacao, CASAS_DECIMAIS_PERCENTUAL
            )

            registros.append(
                {
                    "sexo": categoria,
                    "num_vinculos": quantidade,
                    "pct_participacao": formatar_decimal(participacao),
                    "media_salarial": formatar_decimal(media_salarial),
                }
            )

        resultado = pd.DataFrame(
            registros,
            columns=[
                "sexo",
                "num_vinculos",
                "pct_participacao",
                "media_salarial",
            ],
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