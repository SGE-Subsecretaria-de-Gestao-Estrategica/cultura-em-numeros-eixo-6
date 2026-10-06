from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_DOWN, localcontext
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
ARQUIVO_SAIDA = Path(r"E:\Rais\Rais\csvs\6.20.csv")

CHUNK_SIZE = 300_000
CASAS_DECIMAIS_NOMINAL = 3

COL_CNAE_BASE = "CNAE 2.0 Subclasse - Código"
COL_CNAE_AUX = "CNAE_IBGE"
COL_DOMINIO = "Domínio Cultural"
COL_SALARIO = "vl_rem_media_nom_deflacionada_2024"
COL_SEXO = "Sexo - Código"

MAPA_SEXO = {
    "1": "Masculino",
    "2": "Feminino",
}


# ====
# FUNCOES AUXILIARES
# ====

def validar_colunas(
    dataframe: pd.DataFrame,
    colunas: list[str],
    caminho: Path,
) -> None:
    """Confere se as colunas necessárias existem."""
    ausentes = [coluna for coluna in colunas if coluna not in dataframe.columns]

    if ausentes:
        raise KeyError(
            f"Colunas ausentes em {caminho}: {ausentes}. "
            f"Colunas disponíveis: {list(dataframe.columns)}"
        )


def normalizar_cnae(serie: pd.Series) -> pd.Series:
    """Padroniza os códigos CNAE em sete dígitos."""
    codigos = (
        serie.astype("string")
        .str.strip()
        .str.replace(r"\.0+$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .replace("", pd.NA)
    )
    return codigos.str.zfill(7)


def normalizar_codigo_sexo(serie: pd.Series) -> pd.Series:
    """Normaliza códigos de sexo, inclusive quando chegam como '1.0' ou '2.0'."""
    return (
        serie.astype("string")
        .str.strip()
        .str.replace(r"\.0+$", "", regex=True)
    )


def converter_decimal(valor) -> Decimal | None:
    """
    Converte valores numéricos para Decimal.

    Aceita, por exemplo, 1234.56, 1.234,56 e 1,234.56.
    Quando há ponto e vírgula, considera como decimal o separador
    que aparece por último.
    """
    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    if texto.casefold() in {"", "nan", "none", "null"}:
        return None

    texto = texto.replace(" ", "").replace("\u00a0", "")
    texto = texto.replace("R$", "")

    tem_ponto = "." in texto
    tem_virgula = "," in texto

    if tem_ponto and tem_virgula:
        if texto.rfind(",") > texto.rfind("."):
            # Formato como 1.234,56
            texto = texto.replace(".", "").replace(",", ".")
        else:
            # Formato como 1,234.56
            texto = texto.replace(",", "")
    elif tem_virgula:
        # Vírgula única é tratada como separador decimal.
        texto = texto.replace(",", ".")

    try:
        numero = Decimal(texto)
    except InvalidOperation:
        return None

    return numero if numero.is_finite() else None


def formatar_decimal(valor: Decimal | None) -> str:
    """Trunca para o limite nominal e formata usando ponto decimal."""
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


def carregar_mapa_dominios() -> dict[str, str]:
    """Carrega a correspondência local entre CNAE e domínio cultural."""
    tabela = pd.read_excel(
        ARQUIVO_CNAE_CRIATIVA,
        usecols=[COL_CNAE_AUX, COL_DOMINIO],
        dtype=str,
    )
    tabela.columns = [
        str(coluna).replace("\ufeff", "").strip()
        for coluna in tabela.columns
    ]

    validar_colunas(
        tabela,
        [COL_CNAE_AUX, COL_DOMINIO],
        ARQUIVO_CNAE_CRIATIVA,
    )

    tabela["cnae_normalizado"] = normalizar_cnae(tabela[COL_CNAE_AUX])
    tabela["dominio_normalizado"] = (
        tabela[COL_DOMINIO]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
    )

    tabela = tabela.dropna(
        subset=["cnae_normalizado", "dominio_normalizado"]
    )

    # Se um CNAE estiver associado a mais de um domínio, interrompe
    # para evitar atribuir registros a um domínio arbitrário.
    dominios_por_cnae = tabela.groupby("cnae_normalizado")[
        "dominio_normalizado"
    ].nunique()
    cnaes_conflitantes = dominios_por_cnae[
        dominios_por_cnae > 1
    ].index.tolist()

    if cnaes_conflitantes:
        raise ValueError(
            "Há códigos CNAE associados a mais de um domínio cultural "
            "na tabela auxiliar. Exemplos: "
            f"{cnaes_conflitantes[:10]}"
        )

    tabela = tabela.drop_duplicates(
        subset=["cnae_normalizado"],
        keep="first",
    )

    mapa = dict(
        zip(
            tabela["cnae_normalizado"],
            tabela["dominio_normalizado"],
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

        mapa_dominio = carregar_mapa_dominios()
        cnaes_criativos = set(mapa_dominio)

        print(
            "CNAEs da Economia Criativa carregados: "
            f"{len(cnaes_criativos):,}"
        )
        print(
            f"Processando arquivo base em chunks de {CHUNK_SIZE:,} linhas..."
        )

        # Acumuladores por domínio cultural e sexo.
        soma: dict[tuple[str, str], Decimal] = {}
        quantidade: dict[tuple[str, str], int] = {}

        leitor = pd.read_csv(
            ARQUIVO_BASE,
            sep=";",
            encoding="utf-8-sig",
            usecols=[
                COL_CNAE_BASE,
                COL_SALARIO,
                COL_SEXO,
            ],
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
                    f"  Chunk {numero_chunk}: nenhum registro de "
                    "Economia Criativa."
                )
                continue

            cnae_normalizado = normalizar_cnae(chunk[COL_CNAE_BASE])
            chunk["dominio_cultural"] = cnae_normalizado.map(mapa_dominio)

            codigos_sexo = normalizar_codigo_sexo(chunk[COL_SEXO])
            chunk["sexo"] = codigos_sexo.map(MAPA_SEXO)

            chunk["salario_decimal"] = chunk[COL_SALARIO].map(
                converter_decimal
            )

            chunk = chunk.loc[
                chunk["dominio_cultural"].notna()
                & chunk["sexo"].notna()
                & chunk["salario_decimal"].map(
                    lambda salario: salario is not None and salario > 0
                )
            ].copy()

            if chunk.empty:
                print(
                    f"  Chunk {numero_chunk}: nenhum registro válido "
                    "após os filtros."
                )
                continue

            with localcontext() as contexto:
                contexto.prec = 50

                for dominio, sexo, salario in zip(
                    chunk["dominio_cultural"],
                    chunk["sexo"],
                    chunk["salario_decimal"],
                ):
                    chave = (str(dominio), str(sexo))
                    soma[chave] = soma.get(chave, Decimal("0")) + salario
                    quantidade[chave] = quantidade.get(chave, 0) + 1

            print(f"  Chunk {numero_chunk} processado.")

        if not soma:
            raise ValueError(
                "Nenhum dado válido foi acumulado após os filtros. "
                "Verifique os arquivos de entrada e os valores de sexo "
                "e salário."
            )

        registros = []

        for (dominio, sexo), soma_salarios in soma.items():
            qtd = quantidade[(dominio, sexo)]

            if qtd == 0:
                media = None
            else:
                with localcontext() as contexto:
                    contexto.prec = 50
                    media = soma_salarios / Decimal(qtd)

            registros.append(
                {
                    "dominio_cultural": dominio,
                    "sexo": sexo,
                    "media_salarial_deflacionada_2024": formatar_decimal(
                        media
                    ),
                }
            )

        resultado = pd.DataFrame(
            registros,
            columns=[
                "dominio_cultural",
                "sexo",
                "media_salarial_deflacionada_2024",
            ],
        )

        resultado = resultado.sort_values(
            ["dominio_cultural", "sexo"],
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
        print(f"Registros exportados: {len(resultado)}")

    except FileNotFoundError as erro:
        print(f"Erro: {erro}")

    except (KeyError, ValueError) as erro:
        print(f"Erro de validação dos dados: {erro}")

    except Exception as erro:
        print(f"Erro inesperado: {erro}")


if __name__ == "__main__":
    main()