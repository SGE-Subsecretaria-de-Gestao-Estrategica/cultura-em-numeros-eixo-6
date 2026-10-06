from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_DOWN, localcontext
from pathlib import Path

import pandas as pd


# ====
# CONFIGURACAO
# ====

ARQUIVO_BASE = Path(
    r"D:\OneDrive\Minc\RAIS\RAIS_py\data\processed\rais_2025_filtrado.csv"
)
ARQUIVO_CNAE_CRIATIVA = Path(
    r"E:\Rais\Rais\Auxiliares\CNAE-ibge.xlsx"
)
ARQUIVO_SAIDA = Path(r"E:\Rais\Rais\csvs\6.25_6.26.csv")

CHUNK_SIZE = 300_000
CASAS_DECIMAIS_NOMINAL = 3

COL_CNAE_BASE = "CNAE 2.0 Subclasse - Código"
COL_CNAE_AUX = "CNAE_IBGE"
COL_DOMINIO = "Domínio Cultural"
COL_SALARIO = "vl_rem_media_nom_deflacionada_2024"


# ====
# FUNCOES AUXILIARES
# ====

def validar_colunas(
    dataframe: pd.DataFrame,
    colunas: list[str],
    caminho: Path,
) -> None:
    """Verifica se as colunas necessárias existem."""
    ausentes = [coluna for coluna in colunas if coluna not in dataframe.columns]

    if ausentes:
        raise KeyError(
            f"Colunas ausentes em {caminho}: {ausentes}. "
            f"Colunas disponíveis: {list(dataframe.columns)}"
        )


def normalizar_cnae(serie: pd.Series) -> pd.Series:
    """Normaliza os códigos CNAE em sete dígitos."""
    codigos = (
        serie.astype("string")
        .str.strip()
        .str.replace(r"\.0+$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .replace("", pd.NA)
    )
    return codigos.str.zfill(7)


def converter_decimal(valor) -> Decimal | None:
    """
    Converte valores numéricos para Decimal.

    Aceita ponto ou vírgula decimal. Quando ambos aparecem, considera
    decimal o separador que estiver mais à direita.
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
        # Vírgula decimal.
        texto = texto.replace(",", ".")

    try:
        numero = Decimal(texto)
    except InvalidOperation:
        return None

    return numero if numero.is_finite() else None


def formatar_decimal_truncado(valor: Decimal | None) -> str:
    """Trunca o valor a até três casas decimais e formata com ponto."""
    if valor is None:
        return ""

    fator = Decimal(1).scaleb(-CASAS_DECIMAIS_NOMINAL)

    with localcontext() as contexto:
        contexto.prec = 50
        valor_truncado = valor.quantize(fator, rounding=ROUND_DOWN)

    texto = format(valor_truncado, "f")

    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")

    return texto


def carregar_mapa_cnae_dominio() -> dict[str, str]:
    """Carrega a correspondência local entre CNAE e domínio cultural."""
    df_aux = pd.read_excel(
        ARQUIVO_CNAE_CRIATIVA,
        usecols=[COL_CNAE_AUX, COL_DOMINIO],
        dtype=str,
    )
    df_aux.columns = [
        str(coluna).replace("\ufeff", "").strip()
        for coluna in df_aux.columns
    ]

    validar_colunas(
        df_aux,
        [COL_CNAE_AUX, COL_DOMINIO],
        ARQUIVO_CNAE_CRIATIVA,
    )

    df_aux["cnae_normalizado"] = normalizar_cnae(df_aux[COL_CNAE_AUX])
    df_aux["dominio_cultural"] = (
        df_aux[COL_DOMINIO]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
    )

    df_aux = df_aux.dropna(
        subset=["cnae_normalizado", "dominio_cultural"]
    )

    # Evita escolher silenciosamente um domínio caso um CNAE esteja
    # associado a mais de um domínio na tabela auxiliar.
    dominios_por_cnae = df_aux.groupby("cnae_normalizado")[
        "dominio_cultural"
    ].nunique()
    cnaes_conflitantes = dominios_por_cnae[
        dominios_por_cnae > 1
    ].index.tolist()

    if cnaes_conflitantes:
        raise ValueError(
            "Há CNAEs associados a mais de um domínio cultural na tabela "
            "auxiliar. Exemplos: "
            f"{cnaes_conflitantes[:10]}"
        )

    df_aux = df_aux.drop_duplicates(
        subset=["cnae_normalizado"],
        keep="first",
    )

    mapa = dict(
        zip(
            df_aux["cnae_normalizado"],
            df_aux["dominio_cultural"],
        )
    )

    if not mapa:
        raise ValueError(
            f"Nenhum CNAE válido encontrado em {ARQUIVO_CNAE_CRIATIVA}."
        )

    return mapa


# ====
# PROCESSAMENTO PRINCIPAL
# ====

def main() -> None:
    try:
        for caminho in [ARQUIVO_BASE, ARQUIVO_CNAE_CRIATIVA]:
            if not caminho.exists():
                raise FileNotFoundError(
                    f"Arquivo não encontrado: {caminho}"
                )

        mapa_cnae_dominio = carregar_mapa_cnae_dominio()
        cnaes_criativos = set(mapa_cnae_dominio)

        print(
            "CNAEs da Economia Criativa carregados: "
            f"{len(cnaes_criativos):,}"
        )
        print(
            f"Processando a base em chunks de {CHUNK_SIZE:,} linhas..."
        )

        # Conta todos os vínculos identificados como Economia Criativa.
        num_vinculos_por_dominio: dict[str, int] = defaultdict(int)

        # Salários positivos válidos usados no cálculo da média.
        soma_salarios_por_dominio: dict[str, Decimal] = defaultdict(
            lambda: Decimal("0")
        )
        num_salarios_validos_por_dominio: dict[str, int] = defaultdict(int)

        leitor = pd.read_csv(
            ARQUIVO_BASE,
            sep=";",
            encoding="utf-8-sig",
            usecols=[COL_CNAE_BASE, COL_SALARIO],
            dtype=str,
            chunksize=CHUNK_SIZE,
            low_memory=False,
        )

        for numero_chunk, chunk in enumerate(leitor, start=1):
            cnae_normalizado = normalizar_cnae(chunk[COL_CNAE_BASE])
            chunk = chunk.loc[
                cnae_normalizado.isin(cnaes_criativos)
            ].copy()

            if chunk.empty:
                print(
                    f"  Chunk {numero_chunk}: nenhum registro "
                    "de Economia Criativa."
                )
                continue

            cnae_normalizado = normalizar_cnae(chunk[COL_CNAE_BASE])
            chunk["dominio_cultural"] = cnae_normalizado.map(
                mapa_cnae_dominio
            )
            chunk = chunk.dropna(subset=["dominio_cultural"])

            if chunk.empty:
                print(
                    f"  Chunk {numero_chunk}: nenhum domínio "
                    "cultural correspondente."
                )
                continue

            # Conta vínculos independentemente da disponibilidade do salário.
            contagens = chunk["dominio_cultural"].value_counts()
            for dominio, quantidade in contagens.items():
                num_vinculos_por_dominio[str(dominio)] += int(quantidade)

            # Soma somente salários positivos e válidos.
            for dominio, valor_salario in zip(
                chunk["dominio_cultural"],
                chunk[COL_SALARIO],
            ):
                salario = converter_decimal(valor_salario)

                if salario is None or salario <= 0:
                    continue

                dominio = str(dominio)
                soma_salarios_por_dominio[dominio] += salario
                num_salarios_validos_por_dominio[dominio] += 1

            print(f"  Chunk {numero_chunk} processado.")

        if not num_vinculos_por_dominio:
            raise ValueError(
                "Nenhum vínculo encontrado após os filtros. "
                "Verifique os arquivos e os códigos CNAE."
            )

        registros = []

        for dominio, num_vinculos in num_vinculos_por_dominio.items():
            quantidade_salarios = num_salarios_validos_por_dominio.get(
                dominio,
                0,
            )

            if quantidade_salarios:
                with localcontext() as contexto:
                    contexto.prec = 50
                    media = (
                        soma_salarios_por_dominio[dominio]
                        / Decimal(quantidade_salarios)
                    )
                media_formatada = formatar_decimal_truncado(media)
            else:
                media_formatada = ""

            registros.append(
                {
                    "dominio_cultural": dominio,
                    "num_vinculos": num_vinculos,
                    "media_salarial_deflacionada_2024": media_formatada,
                }
            )

        resultado = pd.DataFrame(
            registros,
            columns=[
                "dominio_cultural",
                "num_vinculos",
                "media_salarial_deflacionada_2024",
            ],
        )

        resultado = resultado.sort_values(
            "num_vinculos",
            ascending=False,
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
        print(f"Domínios exportados: {len(resultado)}")

    except FileNotFoundError as erro:
        print(f"Erro: {erro}")

    except (KeyError, ValueError) as erro:
        print(f"Erro de validação dos dados: {erro}")

    except Exception as erro:
        print(f"Erro inesperado: {erro}")


if __name__ == "__main__":
    main()