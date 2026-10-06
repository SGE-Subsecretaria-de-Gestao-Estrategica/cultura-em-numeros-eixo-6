from __future__ import annotations

import time
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
ARQUIVO_SAIDA = Path(r"E:\Rais\Rais\csvs\6.28_6.29.csv")

CHUNK_SIZE = 300_000
ANO_ANALISE = "2025"
CASAS_DECIMAIS_NOMINAL = 3

COL_ANO = "ano"
COL_NATUREZA_JURIDICA = "Natureza Jurídica - Código"
COL_TAMANHO_ESTABELECIMENTO = "Tamanho Estabelecimento - Código"
COL_SALARIO = "vl_rem_media_nom_deflacionada_2024"
COL_CNAE_BASE = "CNAE 2.0 Subclasse - Código"
COL_CNAE_AUXILIAR = "CNAE_IBGE"

NATUREZAS_JURIDICAS_EMPRESARIAIS = {
    "2011", "2038", "2046", "2054", "2062", "2070", "2089", "2097",
    "2127", "2135", "2143", "2151", "2160", "2178", "2194", "2216",
    "2224", "2232", "2240", "2259", "2267", "2275", "2283", "2291",
    "2305", "2313", "2321", "2330", "2348", "2356",
}

# O código "1" (zero empregados) permanece excluído, como no original.
MAPA_PORTE = {
    "2": "Microempresa",
    "3": "Microempresa",
    "4": "Pequena Empresa",
    "5": "Pequena Empresa",
    "6": "Média Empresa",
    "7": "Grande Empresa",
    "8": "Grande Empresa",
    "9": "Grande Empresa",
    "10": "Grande Empresa",
}

ORDEM_PORTE = [
    "Microempresa",
    "Pequena Empresa",
    "Média Empresa",
    "Grande Empresa",
]


# ====
# FUNCOES AUXILIARES
# ====

def normalizar_codigo(valor) -> str:
    """Normaliza um código numérico lido como texto."""
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()

    if texto.casefold() in {"", "nan", "none", "null"}:
        return ""

    if texto.endswith(".0"):
        texto = texto[:-2]

    return "".join(caractere for caractere in texto if caractere.isdigit())


def normalizar_cnae(serie: pd.Series) -> pd.Series:
    """Normaliza códigos CNAE em sete dígitos."""
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
    Converte valores para Decimal, aceitando formatos como:
    1234.56, 1234,56 e 1.234,56.
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
        # Vírgula como separador decimal.
        texto = texto.replace(",", ".")

    try:
        numero = Decimal(texto)
    except InvalidOperation:
        return None

    return numero if numero.is_finite() else None


def formatar_decimal_truncado(valor: Decimal | None) -> str:
    """Trunca a média salarial a até três casas decimais."""
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


def carregar_cnaes_criativos() -> set[str]:
    """Carrega os códigos CNAE da tabela auxiliar local."""
    df_cnae = pd.read_excel(
        ARQUIVO_CNAE_CRIATIVA,
        usecols=[COL_CNAE_AUXILIAR],
        dtype=str,
    )
    df_cnae.columns = [
        str(coluna).replace("\ufeff", "").strip()
        for coluna in df_cnae.columns
    ]

    if COL_CNAE_AUXILIAR not in df_cnae.columns:
        raise KeyError(
            f"Coluna '{COL_CNAE_AUXILIAR}' não encontrada em "
            f"{ARQUIVO_CNAE_CRIATIVA}."
        )

    cnaes = set(
        normalizar_cnae(df_cnae[COL_CNAE_AUXILIAR]).dropna()
    )

    if not cnaes:
        raise ValueError(
            f"Nenhum CNAE válido encontrado em {ARQUIVO_CNAE_CRIATIVA}."
        )

    return cnaes


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

        cnaes_criativos = carregar_cnaes_criativos()
        print(f"CNAEs criativos carregados: {len(cnaes_criativos):,}")

        num_vinculos_por_porte: dict[str, int] = defaultdict(int)
        soma_salarios_por_porte: dict[str, Decimal] = defaultdict(
            lambda: Decimal("0")
        )
        num_salarios_validos_por_porte: dict[str, int] = defaultdict(int)

        total_lidas = 0
        inicio = time.time()

        print("Processando arquivo base...")

        leitor = pd.read_csv(
            ARQUIVO_BASE,
            sep=";",
            encoding="utf-8-sig",
            dtype=str,
            usecols=[
                COL_ANO,
                COL_NATUREZA_JURIDICA,
                COL_TAMANHO_ESTABELECIMENTO,
                COL_SALARIO,
                COL_CNAE_BASE,
            ],
            chunksize=CHUNK_SIZE,
            low_memory=False,
        )

        for numero_chunk, chunk in enumerate(leitor, start=1):
            total_lidas += len(chunk)

            ano = chunk[COL_ANO].map(normalizar_codigo)
            natureza = chunk[COL_NATUREZA_JURIDICA].map(normalizar_codigo)

            filtrado = chunk.loc[
                ano.eq(ANO_ANALISE)
                & natureza.isin(NATUREZAS_JURIDICAS_EMPRESARIAIS)
            ].copy()

            if filtrado.empty:
                continue

            cnae = normalizar_cnae(filtrado[COL_CNAE_BASE])
            filtrado = filtrado.loc[
                cnae.isin(cnaes_criativos)
            ].copy()

            if filtrado.empty:
                continue

            filtrado["codigo_porte"] = filtrado[
                COL_TAMANHO_ESTABELECIMENTO
            ].map(normalizar_codigo)
            filtrado["categoria_porte"] = filtrado["codigo_porte"].map(
                MAPA_PORTE
            )

            # Desconsidera códigos de porte não mapeados, incluindo "1".
            filtrado = filtrado.dropna(subset=["categoria_porte"])

            if filtrado.empty:
                continue

            # Conta os registros válidos por categoria de porte.
            contagens = filtrado["categoria_porte"].value_counts()
            for porte, quantidade in contagens.items():
                num_vinculos_por_porte[str(porte)] += int(quantidade)

            # Acumula salários positivos e válidos.
            for porte, valor_salario in zip(
                filtrado["categoria_porte"],
                filtrado[COL_SALARIO],
            ):
                salario = converter_decimal(valor_salario)

                if salario is None or salario <= 0:
                    continue

                porte = str(porte)
                soma_salarios_por_porte[porte] += salario
                num_salarios_validos_por_porte[porte] += 1

            decorrido = time.time() - inicio
            velocidade = total_lidas / decorrido if decorrido > 0 else 0

            print(
                f"  Chunk {numero_chunk} | "
                f"Lidas: {total_lidas:,} | "
                f"Velocidade: {velocidade:,.0f} linhas/s",
                end="\r",
            )

        print(f"\n\nProcessamento concluído em {time.time() - inicio:.1f}s.")

        if not num_vinculos_por_porte:
            raise ValueError(
                "Nenhum registro encontrado após os filtros. "
                "Verifique o arquivo de entrada e os filtros aplicados."
            )

        registros = []

        for porte in ORDEM_PORTE:
            quantidade_vinculos = num_vinculos_por_porte.get(porte, 0)
            quantidade_salarios = num_salarios_validos_por_porte.get(
                porte,
                0,
            )

            if quantidade_salarios > 0:
                with localcontext() as contexto:
                    contexto.prec = 50
                    media_salarial = (
                        soma_salarios_por_porte[porte]
                        / Decimal(quantidade_salarios)
                    )
                media_formatada = formatar_decimal_truncado(media_salarial)
            else:
                media_formatada = ""

            registros.append(
                {
                    "ano": int(ANO_ANALISE),
                    "categoria_porte": porte,
                    "num_vinculos": quantidade_vinculos,
                    "media_salarial_deflacionada_2024": media_formatada,
                }
            )

        resultado = pd.DataFrame(
            registros,
            columns=[
                "ano",
                "categoria_porte",
                "num_vinculos",
                "media_salarial_deflacionada_2024",
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
        print(f"Categorias exportadas: {len(resultado)}")

    except FileNotFoundError as erro:
        print(f"Erro: {erro}")

    except (KeyError, ValueError) as erro:
        print(f"Erro de validação dos dados: {erro}")

    except Exception as erro:
        print(f"Erro inesperado: {erro}")


if __name__ == "__main__":
    main()